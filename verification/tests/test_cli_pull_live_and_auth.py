"""CLI tests for `hai auth garmin`, `hai auth status`, and `hai pull --live`.

Scope:
  - ``hai auth garmin`` with ``--email`` + ``--password-stdin`` stores via
    the credential store.
  - ``hai auth garmin`` rejects missing password cleanly.
  - ``hai auth status`` reports presence and never leaks secrets.
  - ``hai pull --live`` exits with a clean error when no credentials exist.
  - ``hai pull --live`` wires a mock adapter end-to-end and emits the same
    payload shape as CSV pull.
  - ``hai pull`` (no ``--live``) continues to read CSV unchanged.

Tests never touch the real OS keyring or the real Garmin API — a fake
credential store and a mock live adapter are injected via monkeypatching
the CLI module.
"""

from __future__ import annotations

import io
import json
import sys
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra import cli as cli_mod
from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.pull.auth import (
    EMAIL_ENV_VAR,
    PASSWORD_ENV_VAR,
    CredentialStore,
    GarminCredentials,
)
from health_agent_infra.core.pull.garmin_live import (
    GarminLiveAdapter,
    GarminLiveError,
)


class FakeKeyring:
    def __init__(self):
        self._data: dict[tuple[str, str], str] = {}

    def get_password(self, service, username):
        return self._data.get((service, username))

    def set_password(self, service, username, password):
        self._data[(service, username)] = password

    def delete_password(self, service, username):
        self._data.pop((service, username), None)


def _fake_store(env=None) -> CredentialStore:
    return CredentialStore(backend=FakeKeyring(), env=env or {})


# ---------------------------------------------------------------------------
# hai auth garmin
# ---------------------------------------------------------------------------

def test_auth_garmin_stores_credentials_via_stdin(monkeypatch, capsys):
    store = _fake_store()
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))

    monkeypatch.setattr(sys, "stdin", io.StringIO("s3cret\n"))
    rc = cli_main(["auth", "garmin", "--email", "alice@example.com", "--password-stdin"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["stored"] is True
    assert payload["service"] == "garmin"
    assert payload["email"] == "alice@example.com"
    # Credentials resolved by the store match what we passed in.
    assert store.load_garmin() == GarminCredentials("alice@example.com", "s3cret")


def test_auth_garmin_reads_password_from_env_var(monkeypatch, capsys):
    store = _fake_store()
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))
    monkeypatch.setenv("MY_PW_VAR", "envpw")

    rc = cli_main([
        "auth", "garmin", "--email", "alice@example.com",
        "--password-env", "MY_PW_VAR",
    ])
    assert rc == 0
    creds = store.load_garmin()
    assert creds is not None
    assert creds.password == "envpw"


def test_auth_garmin_fails_cleanly_when_password_env_missing(monkeypatch, capsys):
    store = _fake_store()
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))
    monkeypatch.delenv("MY_PW_VAR_X", raising=False)

    rc = cli_main([
        "auth", "garmin", "--email", "alice@example.com",
        "--password-env", "MY_PW_VAR_X",
    ])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "MY_PW_VAR_X" in err


def test_auth_garmin_rejects_empty_password(monkeypatch, capsys):
    store = _fake_store()
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))
    monkeypatch.setattr(sys, "stdin", io.StringIO("\n"))

    rc = cli_main(["auth", "garmin", "--email", "alice@example.com", "--password-stdin"])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "password" in err
    assert store.load_garmin() is None


# ---------------------------------------------------------------------------
# hai auth status
# ---------------------------------------------------------------------------

def test_auth_status_empty_reports_no_credentials(monkeypatch, capsys):
    store = _fake_store()
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))
    rc = cli_main(["auth", "status"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["garmin"]["credentials_available"] is False
    assert payload["intervals_icu"]["credentials_available"] is False


def test_auth_status_keyring_present(monkeypatch, capsys):
    store = _fake_store()
    store.store_garmin("alice@example.com", "s3cret")
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))
    rc = cli_main(["auth", "status"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["garmin"]["credentials_available"] is True
    assert payload["garmin"]["keyring"]["email_present"] is True
    assert payload["garmin"]["keyring"]["password_present"] is True
    # Status never surfaces the email or password literal.
    full_stdout = json.dumps(payload)
    assert "alice@example.com" not in full_stdout
    assert "s3cret" not in full_stdout


def test_auth_status_env_only(monkeypatch, capsys):
    store = _fake_store(env={EMAIL_ENV_VAR: "env@example.com", PASSWORD_ENV_VAR: "envpw"})
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))
    rc = cli_main(["auth", "status"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["garmin"]["credentials_available"] is True
    assert payload["garmin"]["env"]["email_present"] is True
    assert payload["garmin"]["env"]["password_present"] is True
    assert payload["garmin"]["keyring"]["email_present"] is False


# ---------------------------------------------------------------------------
# hai auth remove (v0.1.12 W-PRIV)
# ---------------------------------------------------------------------------

def test_auth_remove_garmin_clears_keyring(monkeypatch, capsys):
    store = _fake_store()
    store.store_garmin("alice@example.com", "s3cret")
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))

    rc = cli_main(["auth", "remove", "--source", "garmin"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["removed"] == ["garmin"]
    # Keyring is empty; load_garmin returns None.
    assert store.load_garmin() is None
    assert payload["garmin"]["credentials_available"] is False


def test_auth_remove_intervals_icu_clears_keyring(monkeypatch, capsys):
    store = _fake_store()
    store.store_intervals_icu("athlete-99", "key-shh")
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))

    rc = cli_main(["auth", "remove", "--source", "intervals-icu"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["removed"] == ["intervals_icu"]
    assert store.load_intervals_icu() is None


def test_auth_remove_all_clears_both(monkeypatch, capsys):
    store = _fake_store()
    store.store_garmin("alice@example.com", "s3cret")
    store.store_intervals_icu("athlete-99", "key-shh")
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))

    rc = cli_main(["auth", "remove", "--source", "all"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["removed"] == ["garmin", "intervals_icu"]
    assert store.load_garmin() is None
    assert store.load_intervals_icu() is None


def test_auth_remove_idempotent_on_empty_keyring(monkeypatch, capsys):
    """Removing absent credentials is a no-op, not an error.
    Closes the privacy-doc claim that ``hai auth remove`` is
    idempotent."""

    store = _fake_store()
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))

    rc = cli_main(["auth", "remove", "--source", "all"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["removed"] == ["garmin", "intervals_icu"]
    # Status still reports no credentials.
    assert payload["garmin"]["credentials_available"] is False
    assert payload["intervals_icu"]["credentials_available"] is False


def test_auth_remove_does_not_touch_env_vars(monkeypatch, capsys):
    """Env-var credentials are intentionally outside the removal
    surface. The privacy doc says so; this test enforces."""

    store = _fake_store(env={EMAIL_ENV_VAR: "env@example.com", PASSWORD_ENV_VAR: "envpw"})
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))

    rc = cli_main(["auth", "remove", "--source", "garmin"])
    assert rc == 0
    # Env-supplied credentials still resolvable after the remove.
    creds = store.load_garmin()
    assert creds is not None
    assert creds.password == "envpw"


# ---------------------------------------------------------------------------
# hai pull --live
# ---------------------------------------------------------------------------

def test_pull_live_fails_cleanly_without_credentials(monkeypatch, capsys):
    store = _fake_store()
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))

    rc = cli_main(["pull", "--live", "--date", "2026-04-17"])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "credentials" in err.lower()


class _FakeAdapter:
    """Drop-in GarminLiveAdapter for CLI wiring tests."""

    source_name = "garmin_live"

    def load(self, as_of):
        return {
            "sleep": {"record_id": f"g_sleep_{as_of.isoformat()}", "duration_hours": 7.5},
            "resting_hr": [
                {"date": as_of.isoformat(), "bpm": 58.0, "record_id": "g_rhr_x"}
            ],
            "hrv": [],
            "training_load": [],
            "raw_daily_row": {"date": as_of.isoformat(), "resting_hr": 58},
        }


def test_pull_live_happy_path(monkeypatch, capsys):
    store = _fake_store()
    store.store_garmin("alice@example.com", "s3cret")
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))

    # Inject a fake live adapter by replacing the helper the CLI uses.
    def fake_build(args):
        return _FakeAdapter()

    monkeypatch.setattr(cli_mod, "_build_live_adapter", fake_build)

    rc = cli_main(["pull", "--live", "--date", "2026-04-17"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["as_of_date"] == "2026-04-17"
    assert payload["source"] == "garmin_live"
    assert set(payload["pull"].keys()) == {
        "sleep", "resting_hr", "hrv", "training_load", "raw_daily_row"
    }
    assert payload["pull"]["sleep"]["duration_hours"] == 7.5


def test_pull_explicit_csv_source_uses_committed_fixture(capsys):
    """`hai pull --source csv` uses the CSV adapter unchanged.

    v0.1.6 W5 changed the *default* source resolution: when neither
    --source nor --live is passed and intervals.icu credentials are
    present, the default flips to intervals.icu (the supported live
    source). This test pins the explicit-csv path that was previously
    the unconditional default."""

    rc = cli_main(["pull", "--date", "2026-02-10", "--source", "csv"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    # CSV adapter reports source "garmin"; live reports "garmin_live".
    assert payload["source"] == "garmin"
    assert payload["as_of_date"] == "2026-02-10"
    assert set(payload["pull"].keys()) == {
        "sleep", "resting_hr", "hrv", "training_load", "raw_daily_row"
    }


def test_pull_default_falls_back_to_csv_when_no_intervals_auth(
    capsys, monkeypatch,
):
    """v0.1.6 W5: when intervals.icu credentials are NOT configured,
    the default source resolution falls back to csv (preserving the
    legacy behaviour for fresh installs / offline / test environments)."""

    # Force the credential store to report no intervals.icu auth.
    from health_agent_infra import cli as cli_mod

    class _NoCreds:
        @classmethod
        def default(cls):
            inst = cls()
            return inst

        def load_intervals_icu(self):
            return None

    monkeypatch.setattr(cli_mod, "CredentialStore", _NoCreds)

    rc = cli_mod.main(["pull", "--date", "2026-02-10"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["source"] == "garmin"  # csv adapter


def test_pull_live_wraps_adapter_error(monkeypatch, capsys):
    """If the adapter's .load() raises GarminLiveError, CLI exits cleanly."""

    store = _fake_store()
    store.store_garmin("alice@example.com", "s3cret")
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))

    class ExplodingAdapter:
        source_name = "garmin_live"
        def load(self, as_of):
            raise GarminLiveError("upstream 500")

    monkeypatch.setattr(cli_mod, "_build_live_adapter", lambda args: ExplodingAdapter())

    rc = cli_main(["pull", "--live", "--date", "2026-04-17"])
    assert rc == exit_codes.TRANSIENT
    err = capsys.readouterr().err
    assert "upstream 500" in err


# ---------------------------------------------------------------------------
# _build_live_adapter helper
# ---------------------------------------------------------------------------

def test_build_live_adapter_raises_without_creds(monkeypatch):
    store = _fake_store()
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))
    import argparse
    args = argparse.Namespace(live=True, history_days=14)
    with pytest.raises(GarminLiveError):
        cli_mod._build_live_adapter(args)


def test_build_live_adapter_returns_adapter_when_creds_and_client_ok(monkeypatch):
    store = _fake_store()
    store.store_garmin("alice@example.com", "s3cret")
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))

    # Stub out build_default_client so no real login happens.
    class StubClient:
        def fetch_day(self, day):
            return {}
    # M6 wired retry_config through; accept kwargs so the stub keeps
    # matching the real signature.
    monkeypatch.setattr(
        cli_mod, "build_default_client",
        lambda creds, **kwargs: StubClient(),
    )

    import argparse
    args = argparse.Namespace(live=True, history_days=3)
    adapter = cli_mod._build_live_adapter(args)
    assert isinstance(adapter, GarminLiveAdapter)
    assert adapter.history_days == 3
