"""Tests for the credential storage module (`core/pull/auth.py`).

Scope:
  - ``CredentialStore.store_garmin`` writes to keyring in the expected shape.
  - ``load_garmin`` resolves keyring first, env fallback second.
  - Missing credentials → ``load_garmin`` returns None.
  - ``garmin_status`` reports presence booleans without leaking secrets.
  - ``clear_garmin`` is idempotent across empty / partial / full states.
  - ``_NullBackend`` (no keyring available) still supports env-only flow.

Tests inject an in-memory keyring backend so no real keyring is touched.
"""

from __future__ import annotations

import pytest

from health_agent_infra.core.pull.auth import (
    EMAIL_ENV_VAR,
    GARMIN_EMAIL_KEY,
    GARMIN_EMAIL_SERVICE,
    GARMIN_SERVICE,
    PASSWORD_ENV_VAR,
    CredentialStore,
    GarminCredentials,
    KeyringUnavailableError,
    _NullBackend,
)


class FakeKeyring:
    """In-memory stand-in for the ``keyring`` module-level API."""

    def __init__(self):
        self._data: dict[tuple[str, str], str] = {}

    def get_password(self, service, username):
        return self._data.get((service, username))

    def set_password(self, service, username, password):
        self._data[(service, username)] = password

    def delete_password(self, service, username):
        if (service, username) not in self._data:
            raise KeyError(f"no entry for ({service}, {username})")
        del self._data[(service, username)]


def _empty_store() -> CredentialStore:
    return CredentialStore(backend=FakeKeyring(), env={})


# ---------------------------------------------------------------------------
# store / load happy path
# ---------------------------------------------------------------------------

def test_store_garmin_writes_both_keyring_entries():
    store = _empty_store()
    store.store_garmin("alice@example.com", "s3cret")

    assert store.backend.get_password(
        GARMIN_EMAIL_SERVICE, GARMIN_EMAIL_KEY
    ) == "alice@example.com"
    assert store.backend.get_password(
        GARMIN_SERVICE, "alice@example.com"
    ) == "s3cret"


def test_load_garmin_returns_credentials_after_store():
    store = _empty_store()
    store.store_garmin("alice@example.com", "s3cret")
    creds = store.load_garmin()
    assert creds == GarminCredentials(email="alice@example.com", password="s3cret")


def test_store_garmin_rejects_empty_email():
    store = _empty_store()
    with pytest.raises(ValueError):
        store.store_garmin("", "s3cret")


def test_store_garmin_rejects_empty_password():
    store = _empty_store()
    with pytest.raises(ValueError):
        store.store_garmin("alice@example.com", "")


# ---------------------------------------------------------------------------
# load precedence: keyring > env
# ---------------------------------------------------------------------------

def test_load_garmin_prefers_keyring_over_env():
    store = CredentialStore(
        backend=FakeKeyring(),
        env={EMAIL_ENV_VAR: "env@example.com", PASSWORD_ENV_VAR: "envpw"},
    )
    store.store_garmin("ring@example.com", "ringpw")
    assert store.load_garmin() == GarminCredentials(
        email="ring@example.com", password="ringpw"
    )


def test_load_garmin_falls_back_to_env_when_keyring_empty():
    store = CredentialStore(
        backend=FakeKeyring(),
        env={EMAIL_ENV_VAR: "env@example.com", PASSWORD_ENV_VAR: "envpw"},
    )
    assert store.load_garmin() == GarminCredentials(
        email="env@example.com", password="envpw"
    )


def test_load_garmin_requires_both_env_vars():
    store = CredentialStore(
        backend=FakeKeyring(),
        env={EMAIL_ENV_VAR: "env@example.com"},
    )
    assert store.load_garmin() is None

    store2 = CredentialStore(
        backend=FakeKeyring(),
        env={PASSWORD_ENV_VAR: "envpw"},
    )
    assert store2.load_garmin() is None


def test_load_garmin_keyring_email_without_password_falls_through_to_env():
    """A half-written keyring (email but no password) should still let env
    win rather than pinning the caller on a broken keyring state."""

    backend = FakeKeyring()
    backend.set_password(GARMIN_EMAIL_SERVICE, GARMIN_EMAIL_KEY, "ring@example.com")
    store = CredentialStore(
        backend=backend,
        env={EMAIL_ENV_VAR: "env@example.com", PASSWORD_ENV_VAR: "envpw"},
    )
    creds = store.load_garmin()
    assert creds == GarminCredentials(email="env@example.com", password="envpw")


def test_load_garmin_returns_none_when_nothing_is_configured():
    assert _empty_store().load_garmin() is None


# ---------------------------------------------------------------------------
# status — non-secretive
# ---------------------------------------------------------------------------

def test_garmin_status_reports_no_credentials_when_empty():
    status = _empty_store().garmin_status()
    assert status["service"] == "garmin"
    assert status["credentials_available"] is False
    assert status["keyring"]["email_present"] is False
    assert status["keyring"]["password_present"] is False
    assert status["env"]["email_present"] is False
    assert status["env"]["password_present"] is False


def test_garmin_status_does_not_leak_credentials():
    store = _empty_store()
    store.store_garmin("alice@example.com", "supersecret")
    status = store.garmin_status()
    # Walk every string value and assert it contains neither the email nor
    # the password. Emails and passwords should never appear in status output.
    def _walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                yield from _walk(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from _walk(v)
        elif isinstance(obj, str):
            yield obj
    for s in _walk(status):
        assert "alice@example.com" not in s
        assert "supersecret" not in s


def test_garmin_status_reports_keyring_when_populated():
    store = _empty_store()
    store.store_garmin("alice@example.com", "s3cret")
    status = store.garmin_status()
    assert status["credentials_available"] is True
    assert status["keyring"]["email_present"] is True
    assert status["keyring"]["password_present"] is True


def test_garmin_status_reports_env_when_populated():
    store = CredentialStore(
        backend=FakeKeyring(),
        env={EMAIL_ENV_VAR: "env@example.com", PASSWORD_ENV_VAR: "envpw"},
    )
    status = store.garmin_status()
    assert status["credentials_available"] is True
    assert status["env"]["email_present"] is True
    assert status["env"]["password_present"] is True
    assert status["keyring"]["email_present"] is False


# ---------------------------------------------------------------------------
# clear — idempotent
# ---------------------------------------------------------------------------

def test_clear_garmin_on_empty_store_is_noop():
    store = _empty_store()
    store.clear_garmin()  # must not raise
    assert store.load_garmin() is None


def test_clear_garmin_removes_keyring_entries():
    store = _empty_store()
    store.store_garmin("alice@example.com", "s3cret")
    store.clear_garmin()
    assert store.load_garmin() is None
    assert store.backend.get_password(GARMIN_EMAIL_SERVICE, GARMIN_EMAIL_KEY) is None
    assert store.backend.get_password(GARMIN_SERVICE, "alice@example.com") is None


# ---------------------------------------------------------------------------
# NullBackend — keyring-unavailable path
# ---------------------------------------------------------------------------

def test_null_backend_reads_return_none():
    b = _NullBackend()
    assert b.get_password("hai_garmin", "x") is None


def test_null_backend_raises_on_write():
    b = _NullBackend()
    with pytest.raises(KeyringUnavailableError):
        b.set_password("hai_garmin", "alice", "pw")


def test_null_backend_store_loads_via_env_only():
    """With a null keyring backend, env fallback must still work."""

    store = CredentialStore(
        backend=_NullBackend(),
        env={EMAIL_ENV_VAR: "env@example.com", PASSWORD_ENV_VAR: "envpw"},
    )
    creds = store.load_garmin()
    assert creds == GarminCredentials(email="env@example.com", password="envpw")
