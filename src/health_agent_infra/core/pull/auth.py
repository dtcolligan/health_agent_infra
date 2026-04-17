"""Credential storage for live Garmin pull.

Primary store is the OS keyring (via the ``keyring`` library). When keyring
is unavailable (ImportError, no backend configured, headless CI without a
secret store) the module falls through to two environment variables:

    HAI_GARMIN_EMAIL       — Garmin account email
    HAI_GARMIN_PASSWORD    — Garmin account password

The fallback is documented in the plan's locked decision #1 so agents can
run in non-interactive environments without needing an interactive keyring
unlock.

Two keyring entries back a single Garmin account:

    service=hai_garmin_email  username=default  password=<email>
    service=hai_garmin         username=<email>  password=<garmin_password>

The first entry stores the account identifier; the second stores the
Garmin password keyed by that identifier. This matches the plan's
``keyring.set_password("hai_garmin", email, password)`` shape while still
letting ``load_garmin()`` work without the caller knowing the email in
advance.

``garmin_status()`` reports only presence booleans, never the credentials
themselves — safe to print to stdout or log.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping, Optional, Protocol


GARMIN_SERVICE = "hai_garmin"
GARMIN_EMAIL_SERVICE = "hai_garmin_email"
GARMIN_EMAIL_KEY = "default"

EMAIL_ENV_VAR = "HAI_GARMIN_EMAIL"
PASSWORD_ENV_VAR = "HAI_GARMIN_PASSWORD"


@dataclass(frozen=True)
class GarminCredentials:
    """Resolved Garmin credentials. Never log or print either field."""

    email: str
    password: str


class KeyringUnavailableError(RuntimeError):
    """Raised when a keyring write is attempted without a working backend."""


class KeyringBackend(Protocol):
    """Subset of the ``keyring`` module-level API this store depends on."""

    def get_password(self, service: str, username: str) -> Optional[str]: ...

    def set_password(self, service: str, username: str, password: str) -> None: ...

    def delete_password(self, service: str, username: str) -> None: ...


class _NullBackend:
    """Backend used when ``keyring`` can't be imported or has no backend.

    Reads always return None so the store falls through to env vars.
    Writes raise ``KeyringUnavailableError`` so ``hai auth garmin`` surfaces
    a clean actionable error instead of silently dropping credentials.
    """

    def get_password(self, service: str, username: str) -> Optional[str]:
        return None

    def set_password(self, service: str, username: str, password: str) -> None:
        raise KeyringUnavailableError(
            "keyring backend unavailable: install the `keyring` package and a "
            f"platform backend, or set {EMAIL_ENV_VAR} and {PASSWORD_ENV_VAR} "
            "in the environment instead."
        )

    def delete_password(self, service: str, username: str) -> None:
        # No-op: nothing to delete when no backend is present.
        return None


def _default_backend() -> KeyringBackend:
    """Import keyring lazily; return a null backend if unavailable."""

    try:
        import keyring  # type: ignore
    except ImportError:
        return _NullBackend()
    return keyring


@dataclass
class CredentialStore:
    """Keyring-first credential store with env-var fallback.

    Tests inject a dict-backed ``KeyringBackend`` and an ``env`` mapping;
    production uses ``CredentialStore.default()`` which resolves to the
    real ``keyring`` module and ``os.environ``.
    """

    backend: KeyringBackend
    env: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def default(cls) -> "CredentialStore":
        return cls(backend=_default_backend(), env=os.environ)

    # ------------------------------------------------------------------
    # garmin credential lifecycle
    # ------------------------------------------------------------------

    def store_garmin(self, email: str, password: str) -> None:
        """Persist email + password to keyring. Raises on empty inputs."""

        if not email:
            raise ValueError("email must be a non-empty string")
        if not password:
            raise ValueError("password must be a non-empty string")
        self.backend.set_password(GARMIN_EMAIL_SERVICE, GARMIN_EMAIL_KEY, email)
        self.backend.set_password(GARMIN_SERVICE, email, password)

    def load_garmin(self) -> Optional[GarminCredentials]:
        """Return resolved credentials or None if nothing is configured.

        Resolution order: keyring first (email + password must both be
        present), then env vars (both ``HAI_GARMIN_EMAIL`` and
        ``HAI_GARMIN_PASSWORD`` must be set).
        """

        email = self.backend.get_password(GARMIN_EMAIL_SERVICE, GARMIN_EMAIL_KEY)
        password = None
        if email:
            password = self.backend.get_password(GARMIN_SERVICE, email)
        if email and password:
            return GarminCredentials(email=email, password=password)

        env_email = self.env.get(EMAIL_ENV_VAR)
        env_password = self.env.get(PASSWORD_ENV_VAR)
        if env_email and env_password:
            return GarminCredentials(email=env_email, password=env_password)
        return None

    def clear_garmin(self) -> None:
        """Remove keyring entries if present. Env vars are never touched."""

        email = self.backend.get_password(GARMIN_EMAIL_SERVICE, GARMIN_EMAIL_KEY)
        if email:
            try:
                self.backend.delete_password(GARMIN_SERVICE, email)
            except Exception:
                # keyring raises PasswordDeleteError when nothing to delete;
                # treat as already-clean, the point is idempotent removal.
                pass
        try:
            self.backend.delete_password(GARMIN_EMAIL_SERVICE, GARMIN_EMAIL_KEY)
        except Exception:
            pass

    def garmin_status(self) -> dict:
        """Non-secretive presence report. Never includes secret material."""

        keyring_email = self.backend.get_password(GARMIN_EMAIL_SERVICE, GARMIN_EMAIL_KEY)
        keyring_email_present = bool(keyring_email)
        keyring_password_present = False
        if keyring_email:
            keyring_password_present = bool(
                self.backend.get_password(GARMIN_SERVICE, keyring_email)
            )

        env_email_present = bool(self.env.get(EMAIL_ENV_VAR))
        env_password_present = bool(self.env.get(PASSWORD_ENV_VAR))

        credentials_available = (
            (keyring_email_present and keyring_password_present)
            or (env_email_present and env_password_present)
        )
        return {
            "service": "garmin",
            "credentials_available": credentials_available,
            "keyring": {
                "email_present": keyring_email_present,
                "password_present": keyring_password_present,
            },
            "env": {
                "email_var": EMAIL_ENV_VAR,
                "password_var": PASSWORD_ENV_VAR,
                "email_present": env_email_present,
                "password_present": env_password_present,
            },
        }
