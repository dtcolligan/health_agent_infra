"""``hai auth`` handler group — credential surface.

Owns: ``hai auth garmin``, ``hai auth intervals-icu``, ``hai auth status``,
``hai auth remove``. Plus the auth-private helpers ``_credential_store_for``,
``_backend_kind``, and ``_print_keychain_acl_hint``. The ``_run_interactive_auth``
helper used by ``hai init --guided`` lives in ``cli/handlers/config_init.py``
because its caller (``cmd_init``) lives there.

W-29.2 split: extracted from ``cli/__init__.py`` lines 1188-1399 (handler
bodies preserved byte-for-byte; only the import statements at the top and
the absent module-level constants change).
"""

from __future__ import annotations

import argparse
import os
import sys

from health_agent_infra.core import exit_codes
from health_agent_infra.core.pull.auth import (
    CredentialStore,
    KeyringUnavailableError,
)


# ---------------------------------------------------------------------------
# hai auth garmin / hai auth status
# ---------------------------------------------------------------------------

def cmd_auth_garmin(args: argparse.Namespace) -> int:
    """Store Garmin credentials in the OS keyring.

    Non-interactive callers (agents, tests) supply ``--email`` and either
    ``--password-stdin`` (reads one password line from stdin) or the
    ``HAI_GARMIN_PASSWORD`` env var. Interactive callers are prompted via
    ``input()`` / ``getpass``. The password is never echoed or logged.
    """

    import getpass

    from health_agent_infra.cli import _emit_json

    email = args.email
    password = None

    if args.password_stdin:
        password = sys.stdin.readline().rstrip("\n")
    elif args.password_env:
        password = os.environ.get(args.password_env)
        if not password:
            print(
                f"auth error: env var {args.password_env} is not set or empty",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT

    if email is None:
        try:
            email = input("Garmin email: ").strip()
        except EOFError:
            print("auth error: no email provided", file=sys.stderr)
            return exit_codes.USER_INPUT
    if not email:
        print("auth error: email must be non-empty", file=sys.stderr)
        return exit_codes.USER_INPUT

    if password is None:
        try:
            password = getpass.getpass("Garmin password: ")
        except EOFError:
            print("auth error: no password provided", file=sys.stderr)
            return exit_codes.USER_INPUT
    if not password:
        print("auth error: password must be non-empty", file=sys.stderr)
        return exit_codes.USER_INPUT

    store = _credential_store_for(args)
    try:
        store.store_garmin(email, password)
    except KeyringUnavailableError as exc:
        print(f"auth error: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT
    except ValueError as exc:
        print(f"auth error: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT

    # Emit a non-secret confirmation. Email presence is fine to surface so
    # the operator sees which account was stored; password is never shown.
    _emit_json({
        "stored": True,
        "service": "garmin",
        "email": email,
        "backend": _backend_kind(store),
    })
    _print_keychain_acl_hint(store, service="Garmin")
    return exit_codes.OK


def cmd_auth_intervals_icu(args: argparse.Namespace) -> int:
    """Store Intervals.icu credentials in the OS keyring.

    Non-interactive callers supply ``--athlete-id`` and either
    ``--api-key-stdin`` or ``--api-key-env``. Interactive callers are
    prompted via ``input()`` / ``getpass``. The API key is never echoed.
    """

    import getpass

    from health_agent_infra.cli import _emit_json

    athlete_id = args.athlete_id
    api_key = None

    if args.api_key_stdin:
        api_key = sys.stdin.readline().rstrip("\n")
    elif args.api_key_env:
        api_key = os.environ.get(args.api_key_env)
        if not api_key:
            print(
                f"auth error: env var {args.api_key_env} is not set or empty",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT

    if athlete_id is None:
        try:
            athlete_id = input("Intervals.icu athlete id (e.g. i123456): ").strip()
        except EOFError:
            print("auth error: no athlete id provided", file=sys.stderr)
            return exit_codes.USER_INPUT
    if not athlete_id:
        print("auth error: athlete id must be non-empty", file=sys.stderr)
        return exit_codes.USER_INPUT

    if api_key is None:
        try:
            api_key = getpass.getpass("Intervals.icu API key: ")
        except EOFError:
            print("auth error: no API key provided", file=sys.stderr)
            return exit_codes.USER_INPUT
    if not api_key:
        print("auth error: API key must be non-empty", file=sys.stderr)
        return exit_codes.USER_INPUT

    store = _credential_store_for(args)
    try:
        store.store_intervals_icu(athlete_id, api_key)
    except KeyringUnavailableError as exc:
        print(f"auth error: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT
    except ValueError as exc:
        print(f"auth error: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT

    _emit_json({
        "stored": True,
        "service": "intervals_icu",
        "athlete_id": athlete_id,
        "backend": _backend_kind(store),
    })
    _print_keychain_acl_hint(store, service="Intervals.icu")
    return exit_codes.OK


def _print_keychain_acl_hint(store, *, service: str) -> None:
    """Print a one-line stderr hint about macOS Keychain 'Always Allow'
    so users aren't surprised by the re-prompt each time ``hai pull
    --live`` wakes the keyring.

    Only fires when the backend is the macOS Keychain (``KeychainKeyring``
    class from the ``keyring`` package). Linux Secret Service + the
    in-memory test backend don't have this UX issue, so we don't clutter
    their stderr.
    """

    if _backend_kind(store) != "KeychainKeyring":
        return
    print(
        f"note: macOS will prompt the first time `hai pull --live` "
        f"reads the {service} credentials. Click 'Always Allow' so "
        f"subsequent pulls run without re-prompting.",
        file=sys.stderr,
    )


def cmd_auth_status(args: argparse.Namespace) -> int:
    """Report credential presence only — never prints secrets."""

    from health_agent_infra.cli import _emit_json

    store = _credential_store_for(args)
    _emit_json({
        "backend": _backend_kind(store),
        "garmin": store.garmin_status(),
        "intervals_icu": store.intervals_icu_status(),
    })
    return exit_codes.OK


def cmd_auth_remove(args: argparse.Namespace) -> int:
    """Remove credentials from the OS keyring. Idempotent.

    Origin: v0.1.12 W-PRIV (PLAN.md §2.7) — closes the privacy-doc
    discrepancy that referenced a removal command which did not yet
    exist in the CLI surface, despite the underlying ``clear_garmin``
    / ``clear_intervals_icu`` helpers already living in
    ``core/pull/auth.py``.

    ``--source`` accepts ``garmin``, ``intervals-icu``, or ``all``.
    Env-var-supplied credentials are never touched (keyring only).
    """

    from health_agent_infra.cli import _emit_json

    store = _credential_store_for(args)
    source = args.source
    cleared: list[str] = []
    if source in ("garmin", "all"):
        store.clear_garmin()
        cleared.append("garmin")
    if source in ("intervals-icu", "all"):
        store.clear_intervals_icu()
        cleared.append("intervals_icu")

    _emit_json({
        "backend": _backend_kind(store),
        "removed": cleared,
        "garmin": store.garmin_status(),
        "intervals_icu": store.intervals_icu_status(),
    })
    return exit_codes.OK


def _credential_store_for(args: argparse.Namespace) -> CredentialStore:
    # Tests set ``_credential_store_override`` via monkeypatching to inject
    # a backend; production falls through to the real keyring + env.
    override = getattr(args, "_credential_store_override", None)
    if override is not None:
        return override
    return CredentialStore.default()


def _backend_kind(store: CredentialStore) -> str:
    return type(store.backend).__name__
