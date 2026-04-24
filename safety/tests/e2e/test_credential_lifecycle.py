"""E2E scenario 4 — credential lifecycle (v0.1.4 WS-E).

Scenario: creds present → live sync writes a successful row to
sync_run_log → user rotates keys / wipes keychain → ``hai stats``
reports ``stale_credentials`` without waiting for the next pull
attempt to fail.

This validates D4 #5 end-to-end: the cred-aware stats surface joins
the successful sync history against *current* credential state, so
the user sees the problem before ``hai daily`` hangs trying to
re-authenticate.

The sync history is seeded via ``begin_sync`` / ``complete_sync``
rather than an actual live pull — we're testing the stats
downgrade, not the adapter. Credential status is toggled via a fake
keyring backend so this test never touches the real OS keyring.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from .conftest import E2EEnv


class _FakeKeyring:
    def __init__(self):
        self._data: dict[tuple[str, str], str] = {}

    def get_password(self, service, username):
        return self._data.get((service, username))

    def set_password(self, service, username, password):
        self._data[(service, username)] = password

    def delete_password(self, service, username):
        self._data.pop((service, username), None)


USER_ID = "u_local_1"
AS_OF = date(2026, 4, 22)


def _seed_live_sync(env: E2EEnv, *, source: str) -> None:
    from health_agent_infra.core.state import (
        begin_sync,
        complete_sync,
        open_connection,
    )
    conn = open_connection(env.db_path)
    try:
        sid = begin_sync(
            conn, source=source, user_id=USER_ID,
            mode="live", for_date=AS_OF,
        )
        complete_sync(
            conn, sid, rows_pulled=1, rows_accepted=1,
            duplicates_skipped=0, status="ok",
        )
    finally:
        conn.close()


def test_stats_downgrades_status_after_credentials_removed(
    e2e_env: E2EEnv, monkeypatch,
) -> None:
    """Full lifecycle journey:

        1. User stores intervals.icu credentials.
        2. A successful live pull lands a `status=ok` row.
        3. User removes the credential (simulated here by replacing
           the store with an empty backend).
        4. `hai stats` reports `status=stale_credentials` for that
           source, even though the sync_run_log row's own status is
           still `ok`.
    """

    from health_agent_infra import cli as cli_mod
    from health_agent_infra.core.pull.auth import CredentialStore

    # Step 1 — credentials present. This is the pre-removal state.
    store = CredentialStore(backend=_FakeKeyring(), env={})
    store.store_intervals_icu("i123456", "initial_key")
    monkeypatch.setattr(
        cli_mod.CredentialStore, "default", classmethod(lambda cls: store),
    )

    # Step 2 — simulate a successful pull landing in sync_run_log.
    _seed_live_sync(e2e_env, source="intervals_icu")

    # Confirm stats reports OK while creds are present.
    pre_result = e2e_env.run_hai("stats", "--json")
    pre = pre_result["stdout_json"]["sync_freshness"]["intervals_icu"]
    assert pre["status"] == "ok"
    assert pre["credentials_available"] is True

    # Step 3 — user rotates keys / wipes keychain.
    empty = CredentialStore(backend=_FakeKeyring(), env={})
    monkeypatch.setattr(
        cli_mod.CredentialStore, "default", classmethod(lambda cls: empty),
    )

    # Step 4 — stats downgrades to stale_credentials; the sync row's
    # own status is untouched (history is history), but the surface
    # warns the user that the next live pull will fail.
    post_result = e2e_env.run_hai("stats", "--json")
    post = post_result["stdout_json"]["sync_freshness"]["intervals_icu"]
    assert post["status"] == "stale_credentials"
    assert post["credentials_available"] is False


def test_csv_source_survives_credential_rotation(
    e2e_env: E2EEnv, monkeypatch,
) -> None:
    """CSV fixture source doesn't need credentials — stats must not
    degrade it even when the keyring is completely empty. Catches the
    regression where cred-awareness is too aggressive and flags
    offline-adapter syncs."""

    from health_agent_infra import cli as cli_mod
    from health_agent_infra.core.pull.auth import CredentialStore

    empty = CredentialStore(backend=_FakeKeyring(), env={})
    monkeypatch.setattr(
        cli_mod.CredentialStore, "default", classmethod(lambda cls: empty),
    )

    _seed_live_sync(e2e_env, source="garmin")  # CSV-backed `garmin` source.
    # Note: the CSV fixture uses source="garmin" (not "garmin_live").

    result = e2e_env.run_hai("stats", "--json")
    fresh = result["stdout_json"]["sync_freshness"]["garmin"]
    assert fresh["status"] == "ok"
    assert fresh["credentials_available"] is None
