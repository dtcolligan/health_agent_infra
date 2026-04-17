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
    assert rc == 2
    err = capsys.readouterr().err
    assert "MY_PW_VAR_X" in err


def test_auth_garmin_rejects_empty_password(monkeypatch, capsys):
    store = _fake_store()
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))
    monkeypatch.setattr(sys, "stdin", io.StringIO("\n"))

    rc = cli_main(["auth", "garmin", "--email", "alice@example.com", "--password-stdin"])
    assert rc == 2
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
    assert payload["credentials_available"] is False


def test_auth_status_keyring_present(monkeypatch, capsys):
    store = _fake_store()
    store.store_garmin("alice@example.com", "s3cret")
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))
    rc = cli_main(["auth", "status"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["credentials_available"] is True
    assert payload["keyring"]["email_present"] is True
    assert payload["keyring"]["password_present"] is True
    # Status never surfaces the email or password literal.
    raw = capsys.readouterr().out  # second read: now empty
    del raw
    full_stdout = json.dumps(payload)
    assert "alice@example.com" not in full_stdout
    assert "s3cret" not in full_stdout


def test_auth_status_env_only(monkeypatch, capsys):
    store = _fake_store(env={EMAIL_ENV_VAR: "env@example.com", PASSWORD_ENV_VAR: "envpw"})
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))
    rc = cli_main(["auth", "status"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["credentials_available"] is True
    assert payload["env"]["email_present"] is True
    assert payload["env"]["password_present"] is True
    assert payload["keyring"]["email_present"] is False


# ---------------------------------------------------------------------------
# hai pull --live
# ---------------------------------------------------------------------------

def test_pull_live_fails_cleanly_without_credentials(monkeypatch, capsys):
    store = _fake_store()
    monkeypatch.setattr(cli_mod.CredentialStore, "default", classmethod(lambda cls: store))

    rc = cli_main(["pull", "--live", "--date", "2026-04-17"])
    assert rc == 2
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


def test_pull_default_still_reads_csv(capsys):
    """`hai pull` without --live uses the CSV adapter unchanged."""

    rc = cli_main(["pull", "--date", "2026-02-10"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    # CSV adapter reports source "garmin"; live reports "garmin_live".
    assert payload["source"] == "garmin"
    assert payload["as_of_date"] == "2026-02-10"
    assert set(payload["pull"].keys()) == {
        "sleep", "resting_hr", "hrv", "training_load", "raw_daily_row"
    }


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
    assert rc == 2
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
    monkeypatch.setattr(cli_mod, "build_default_client", lambda creds: StubClient())

    import argparse
    args = argparse.Namespace(live=True, history_days=3)
    adapter = cli_mod._build_live_adapter(args)
    assert isinstance(adapter, GarminLiveAdapter)
    assert adapter.history_days == 3
