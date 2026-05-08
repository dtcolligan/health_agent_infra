"""Credential storage for live pull adapters (Garmin, Intervals.icu).

Primary store is the OS keyring (via the ``keyring`` library). When keyring
is unavailable (ImportError, no backend configured, headless CI without a
secret store) the module falls through to per-service environment
variables (see the ``*_ENV_VAR`` constants below).

The fallback is documented in the plan's locked decision #1 so agents can
run in non-interactive environments without needing an interactive keyring
unlock.

Keyring layout per service follows the same shape:

    Garmin:
      service=hai_garmin_email       username=default        password=<email>
      service=hai_garmin              username=<email>        password=<garmin_password>

    Intervals.icu:
      service=hai_intervals_icu_athlete  username=default     password=<athlete_id>
      service=hai_intervals_icu           username=<athlete_id>  password=<api_key>

The first entry stores the account identifier; the second stores the
secret keyed by that identifier. ``load_*`` works without the caller
knowing the identifier in advance.

``*_status()`` reports only presence booleans, never the credentials
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

INTERVALS_SERVICE = "hai_intervals_icu"
INTERVALS_ATHLETE_SERVICE = "hai_intervals_icu_athlete"
INTERVALS_ATHLETE_KEY = "default"

INTERVALS_ATHLETE_ENV_VAR = "HAI_INTERVALS_ATHLETE_ID"
INTERVALS_API_KEY_ENV_VAR = "HAI_INTERVALS_API_KEY"


@dataclass(frozen=True)
class GarminCredentials:
    """Resolved Garmin credentials. Never log or print either field."""

    email: str
    password: str


@dataclass(frozen=True)
class IntervalsIcuCredentials:
    """Resolved Intervals.icu credentials. Never log or print the api_key.

    ``athlete_id`` is the user's numeric Intervals.icu athlete identifier
    (string, e.g. ``"2049151"``). The value ``"0"`` is accepted by the
    Intervals.icu API as a shorthand for "the authenticated user".
    """

    athlete_id: str
    api_key: str


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
            "platform backend, or set the per-service environment variables "
            "instead (see health_agent_infra.core.pull.auth)."
        )

    def delete_password(self, service: str, username: str) -> None:
        # No-op: nothing to delete when no backend is present.
        return None


def _default_backend() -> KeyringBackend:
    """Import keyring lazily; return a null backend if unavailable.

    Linux environments can import ``keyring`` successfully while still
    lacking any registered backend. In that shape the first read raises
    ``NoKeyringError`` at runtime. Probe defensively so non-credential
    commands degrade to "no creds configured" instead of crashing.
    """

    try:
        import keyring  # type: ignore
    except ImportError:
        return _NullBackend()

    try:
        from keyring.errors import NoKeyringError  # type: ignore
    except ImportError:
        return keyring

    try:
        keyring.get_password("__hai_probe__", "__hai_probe__")
    except NoKeyringError:
        return _NullBackend()
    except Exception:
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

    # ------------------------------------------------------------------
    # intervals.icu credential lifecycle
    # ------------------------------------------------------------------

    def store_intervals_icu(self, athlete_id: str, api_key: str) -> None:
        """Persist athlete_id + api_key to keyring. Raises on empty inputs."""

        if not athlete_id:
            raise ValueError("athlete_id must be a non-empty string")
        if not api_key:
            raise ValueError("api_key must be a non-empty string")
        self.backend.set_password(
            INTERVALS_ATHLETE_SERVICE, INTERVALS_ATHLETE_KEY, athlete_id
        )
        self.backend.set_password(INTERVALS_SERVICE, athlete_id, api_key)

    def load_intervals_icu(self) -> Optional[IntervalsIcuCredentials]:
        """Return resolved credentials or None if nothing is configured.

        Resolution order: keyring first (athlete_id + api_key must both be
        present), then env vars (both ``HAI_INTERVALS_ATHLETE_ID`` and
        ``HAI_INTERVALS_API_KEY`` must be set).
        """

        athlete_id = self.backend.get_password(
            INTERVALS_ATHLETE_SERVICE, INTERVALS_ATHLETE_KEY
        )
        api_key = None
        if athlete_id:
            api_key = self.backend.get_password(INTERVALS_SERVICE, athlete_id)
        if athlete_id and api_key:
            return IntervalsIcuCredentials(athlete_id=athlete_id, api_key=api_key)

        env_athlete = self.env.get(INTERVALS_ATHLETE_ENV_VAR)
        env_api_key = self.env.get(INTERVALS_API_KEY_ENV_VAR)
        if env_athlete and env_api_key:
            return IntervalsIcuCredentials(
                athlete_id=env_athlete, api_key=env_api_key
            )
        return None

    def clear_intervals_icu(self) -> None:
        """Remove keyring entries if present. Env vars are never touched."""

        athlete_id = self.backend.get_password(
            INTERVALS_ATHLETE_SERVICE, INTERVALS_ATHLETE_KEY
        )
        if athlete_id:
            try:
                self.backend.delete_password(INTERVALS_SERVICE, athlete_id)
            except Exception:
                pass
        try:
            self.backend.delete_password(
                INTERVALS_ATHLETE_SERVICE, INTERVALS_ATHLETE_KEY
            )
        except Exception:
            pass

    def intervals_icu_status(self) -> dict:
        """Non-secretive presence report. Never includes secret material."""

        keyring_athlete = self.backend.get_password(
            INTERVALS_ATHLETE_SERVICE, INTERVALS_ATHLETE_KEY
        )
        keyring_athlete_present = bool(keyring_athlete)
        keyring_api_key_present = False
        if keyring_athlete:
            keyring_api_key_present = bool(
                self.backend.get_password(INTERVALS_SERVICE, keyring_athlete)
            )

        env_athlete_present = bool(self.env.get(INTERVALS_ATHLETE_ENV_VAR))
        env_api_key_present = bool(self.env.get(INTERVALS_API_KEY_ENV_VAR))

        credentials_available = (
            (keyring_athlete_present and keyring_api_key_present)
            or (env_athlete_present and env_api_key_present)
        )
        return {
            "service": "intervals_icu",
            "credentials_available": credentials_available,
            "keyring": {
                "athlete_id_present": keyring_athlete_present,
                "api_key_present": keyring_api_key_present,
            },
            "env": {
                "athlete_id_var": INTERVALS_ATHLETE_ENV_VAR,
                "api_key_var": INTERVALS_API_KEY_ENV_VAR,
                "athlete_id_present": env_athlete_present,
                "api_key_present": env_api_key_present,
            },
        }
