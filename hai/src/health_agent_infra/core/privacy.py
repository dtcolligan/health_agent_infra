"""Local data-sovereignty helpers: secure-by-default file + directory perms.

Per the v0.1.4 Phase D privacy hardening (Codex strategic report §7), every
piece of user data the runtime writes locally — state DB, JSONL audit logs,
intake submissions, anything owned by the user — should be readable only
by the OS user who owns the file. This module is the single point that
enforces that contract.

Design choices:
  - **POSIX-only.** ``os.chmod`` semantics differ on Windows; this module
    no-ops on non-POSIX so the runtime keeps working without raising
    spurious permission errors. Windows users get whatever default ACLs
    their NTFS gives them; documenting that gap in ``privacy.md``.
  - **Idempotent.** Re-running ``secure_directory`` / ``secure_file`` on
    an already-locked-down path is a no-op (same chmod, no race).
  - **Conservative defaults.** Directories: 0o700 (owner rwx, no group/
    other). Files: 0o600 (owner rw, no group/other).
  - **Best-effort, never raise on permission errors.** A user who's
    already running with restrictive perms may find themselves on a
    filesystem where chmod is rejected (e.g. a network mount). We log
    once via stderr in that case and continue — the alternative
    (refusing to write data) is worse than the privacy gap the chmod
    would have closed.
"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path
from typing import Optional


# Standard masks. Octal literals so they read like the chmod commands an
# operator would type.
_DIR_MODE: int = 0o700
_FILE_MODE: int = 0o600


def is_posix() -> bool:
    """True when the platform supports the POSIX permission model."""

    return os.name == "posix"


def secure_directory(path: Path, *, create: bool = True) -> None:
    """Restrict ``path`` to owner-only access (0o700) on POSIX.

    When ``create=True`` (default), creates the directory tree with
    parents if missing. When ``create=False``, the function does nothing
    if the path doesn't exist.

    Idempotent. No-ops on non-POSIX. Best-effort on chmod failure
    (warns once on stderr; never raises).
    """

    if create:
        path.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        return
    if not is_posix():
        return
    try:
        os.chmod(path, _DIR_MODE)
    except (OSError, PermissionError) as exc:
        _warn_once(
            f"could not chmod directory {path} to 0700: {exc}. "
            f"Local data is still being written but may be readable by "
            f"other users on this machine."
        )


def secure_file(path: Path) -> None:
    """Restrict ``path`` to owner-only access (0o600) on POSIX.

    Does nothing if the file doesn't exist (caller is responsible for
    invoking AFTER the file lands). No-ops on non-POSIX. Best-effort
    on chmod failure.
    """

    if not path.exists():
        return
    if not is_posix():
        return
    try:
        os.chmod(path, _FILE_MODE)
    except (OSError, PermissionError) as exc:
        _warn_once(
            f"could not chmod file {path} to 0600: {exc}. "
            f"Local data is still being written but may be readable by "
            f"other users on this machine."
        )


def secure_state_db(db_path: Path) -> None:
    """Convenience: secure the parent directory + the DB file together.

    Used by ``initialize_database`` and any caller that re-touches the
    DB. Sets the parent dir to 0o700 (covers the WAL + journal files
    SQLite drops alongside the DB) and the DB file itself to 0o600.
    """

    secure_directory(db_path.parent, create=True)
    secure_file(db_path)
    # SQLite WAL + SHM siblings (created lazily on first transaction).
    # Their existence is opportunistic; we secure them when present.
    for sibling_suffix in ("-wal", "-shm", "-journal"):
        sibling = db_path.with_name(db_path.name + sibling_suffix)
        secure_file(sibling)


def secure_intake_dir(base_dir: Path) -> None:
    """Convenience: secure an intake / writeback root + every JSONL inside.

    Called by intake / propose / review CLIs after the JSONL append
    completes. JSONLs are append-only and may already exist; chmod is
    cheap and idempotent so re-running is safe.
    """

    secure_directory(base_dir, create=True)
    if not base_dir.exists():
        return
    for child in base_dir.iterdir():
        if child.is_file() and child.suffix == ".jsonl":
            secure_file(child)


# ---------------------------------------------------------------------------
# Internal: warn-once stderr helper.
# Keeps the runtime quiet on a misconfigured filesystem after the first
# warning. The warning is the user's signal to investigate; spamming it
# every write turns a privacy incident into log noise.
# ---------------------------------------------------------------------------

_WARNED_PATHS: set[str] = set()


def _warn_once(message: str) -> None:
    if message in _WARNED_PATHS:
        return
    _WARNED_PATHS.add(message)
    print(f"warning: {message}", file=sys.stderr)


def reset_warn_cache_for_tests() -> None:
    """Clear the warn-once dedup set. Test-only helper."""

    _WARNED_PATHS.clear()


def expected_dir_mode() -> int:
    """The mask ``secure_directory`` applies. Exposed for tests."""

    return _DIR_MODE


def expected_file_mode() -> int:
    """The mask ``secure_file`` applies. Exposed for tests."""

    return _FILE_MODE


def current_mode(path: Path) -> Optional[int]:
    """Return the lower-9-bit perm mask of ``path``, or None on non-POSIX
    or missing path. Exposed for tests; not part of the runtime API."""

    if not is_posix() or not path.exists():
        return None
    return stat.S_IMODE(path.stat().st_mode)
