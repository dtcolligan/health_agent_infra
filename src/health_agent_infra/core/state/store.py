"""SQLite state store — connection management, WAL enablement, migrations.

Phase 7A.1 substrate. This module owns exactly three concerns:

    1. Deciding where the DB file lives (``HAI_STATE_DB`` env var ->
       ``~/.local/share/health_agent_infra/state.db``).
    2. Opening SQLite connections with WAL mode + foreign-key enforcement.
    3. Running forward-only versioned migrations from
       ``src/health_agent_infra/state/migrations/NNN_*.sql`` against a
       ``schema_migrations`` version table.

Projection (raw -> accepted), dual-write, read CLIs, and snapshot logic
are explicitly not in this module. They land in later phases.
"""

from __future__ import annotations

import os
import re
import sqlite3
from importlib.resources import files
from pathlib import Path
from typing import Iterable, Optional


DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "health_agent_infra" / "state.db"

_HAI_STATE_DB_ENV = "HAI_STATE_DB"

_MIGRATION_FILENAME_RE = re.compile(r"^(\d{3,})_[a-zA-Z0-9_]+\.sql$")


def resolve_db_path(explicit: Optional[Path | str] = None) -> Path:
    """Return the DB path to use, preferring explicit arg > env var > default."""

    if explicit is not None:
        return Path(explicit).expanduser()
    env_value = os.environ.get(_HAI_STATE_DB_ENV)
    if env_value:
        return Path(env_value).expanduser()
    return DEFAULT_DB_PATH


def open_connection(db_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection with WAL + foreign keys enforced.

    Creates the parent directory if needed. The DB file is created by SQLite
    on first connect if absent. Uses Python's default deferred isolation so
    DML can be wrapped in explicit transactions.
    """

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    """Create the ``schema_migrations`` bookkeeping table if it doesn't exist."""

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version     INTEGER PRIMARY KEY,
            filename    TEXT NOT NULL,
            applied_at  TEXT NOT NULL
        )
        """
    )


def current_schema_version(conn: sqlite3.Connection) -> int:
    """Return the highest applied migration version, or 0 if none."""

    _ensure_migrations_table(conn)
    row = conn.execute(
        "SELECT MAX(version) AS v FROM schema_migrations"
    ).fetchone()
    if row is None or row["v"] is None:
        return 0
    return int(row["v"])


def discover_migrations() -> list[tuple[int, str, str]]:
    """Return sorted list of ``(version, filename, sql_body)`` from packaged migrations.

    Resolves via ``importlib.resources`` so the migrations ship inside the
    wheel. Only files matching ``NNN_name.sql`` are considered.
    """

    migrations_dir = files("health_agent_infra").joinpath("core", "state", "migrations")
    discovered: list[tuple[int, str, str]] = []
    for entry in migrations_dir.iterdir():
        name = entry.name
        match = _MIGRATION_FILENAME_RE.match(name)
        if not match:
            continue
        version = int(match.group(1))
        sql_body = entry.read_text(encoding="utf-8")
        discovered.append((version, name, sql_body))
    discovered.sort(key=lambda t: t[0])
    return discovered


def _split_sql_statements(sql: str) -> list[str]:
    """Split a SQL script into individual statements on statement-terminating ``;``.

    Handles ``--`` line comments and single-quoted string literals (including
    the SQL ``''`` escape).

    **Migration-authoring constraint:** this splitter is intentionally narrow.
    It does **not** handle ``/* */`` block comments, trigger bodies with
    internal semicolons, ``BEGIN ... END;`` compound statements, or any SQL
    shape that places ``;`` inside a parsed construct other than a string
    literal. Migration authors must keep each statement terminated by a
    single ``;`` followed by whitespace/newline and use ``--`` for inline
    commentary. If a future migration needs triggers or block comments, this
    splitter must be upgraded first.
    """

    statements: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(sql)
    in_string = False

    while i < n:
        ch = sql[i]

        if in_string:
            buf.append(ch)
            if ch == "'":
                # ``''`` inside a string literal is an escaped single quote,
                # not a terminator.
                if i + 1 < n and sql[i + 1] == "'":
                    buf.append(sql[i + 1])
                    i += 2
                    continue
                in_string = False
            i += 1
            continue

        if ch == "'":
            in_string = True
            buf.append(ch)
            i += 1
            continue

        if ch == "-" and i + 1 < n and sql[i + 1] == "-":
            # Line comment: skip to end of line.
            while i < n and sql[i] != "\n":
                i += 1
            continue

        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def apply_pending_migrations(
    conn: sqlite3.Connection,
    migrations: Optional[list[tuple[int, str, str]]] = None,
) -> list[tuple[int, str]]:
    """Apply every migration whose version > ``current_schema_version``.

    Each migration file runs inside a single ``BEGIN EXCLUSIVE`` / ``COMMIT``
    transaction that also stamps ``schema_migrations``. A failure anywhere in
    the file — bad DDL, constraint violation, bookkeeping insert — rolls the
    whole file back, leaving the DB exactly as it was before this migration
    started.

    Successive migrations are independent transactions: if migration 002
    fails, migration 001 (already committed in its own transaction) stays
    applied.

    Returns the list of ``(version, filename)`` tuples that were committed in
    this call. Empty list means the DB was already at head.

    Args:
        conn: an open connection (default deferred isolation). Autocommit
            mode is not supported — explicit BEGIN/COMMIT would fail there.
        migrations: optional iterable of ``(version, filename, sql_body)``
            tuples, overriding packaged discovery. Primarily a test seam so
            a deliberately broken migration can prove rollback behaviour.
    """

    pending = migrations if migrations is not None else discover_migrations()
    applied_now: list[tuple[int, str]] = []
    current = current_schema_version(conn)

    for version, filename, sql_body in pending:
        if version <= current:
            continue
        statements = _split_sql_statements(sql_body)

        conn.execute("BEGIN EXCLUSIVE")
        try:
            for stmt in statements:
                conn.execute(stmt)
            conn.execute(
                "INSERT INTO schema_migrations (version, filename, applied_at) "
                "VALUES (?, ?, datetime('now'))",
                (version, filename),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        applied_now.append((version, filename))
        current = version

    return applied_now


def initialize_database(db_path: Path) -> tuple[Path, list[tuple[int, str]]]:
    """Open the DB at ``db_path`` (creating file + parent dir if needed),
    enable WAL + FKs, ensure the bookkeeping table, and apply pending
    migrations.

    Returns ``(resolved_path, applied_migrations)`` where
    ``applied_migrations`` is empty if the DB was already at head.

    Phase D (v0.1.4) privacy hardening: after the migration pass lands the
    DB on disk, the parent directory is locked to 0o700 and every file
    in it (DB + WAL + SHM + journal siblings) to 0o600 on POSIX. No-ops
    on Windows. Best-effort on chmod failure (warn + continue).
    """

    from health_agent_infra.core.privacy import secure_state_db

    conn = open_connection(db_path)
    try:
        _ensure_migrations_table(conn)
        applied = apply_pending_migrations(conn)
    finally:
        conn.close()
    secure_state_db(db_path)
    return db_path, applied


def list_applied_migrations(conn: sqlite3.Connection) -> Iterable[sqlite3.Row]:
    """Yield rows from schema_migrations ordered by version ascending."""

    _ensure_migrations_table(conn)
    return conn.execute(
        "SELECT version, filename, applied_at FROM schema_migrations ORDER BY version"
    ).fetchall()


# ---------------------------------------------------------------------------
# Dry-run diff gates (per-migration, safety net before forward-running)
# ---------------------------------------------------------------------------

def migration_004_dry_run_diff(conn: sqlite3.Connection) -> dict:
    """Compare accepted_recovery columns the migration moves against raw.

    Run against a DB at schema version 3 (before 004 applies). For each
    ``accepted_recovery_state_daily`` row, derives the value the
    post-migration sleep / stress projectors would produce from the
    latest non-superseded raw rows (source_daily_garmin +
    stress_manual_raw), and reports any field where the current accepted
    value differs from what the projector would produce.

    A non-empty diff means the existing accepted rows hold values that
    wouldn't survive a clean re-projection — either because the raw has
    drifted, because a manual patch was applied, or because a past bug
    left inconsistent state. The operator must investigate before the
    migration runs forward.

    Returns a dict shaped::

        {
            "migration": "004_sleep_stress_tables",
            "schema_version": <int>,
            "rows_checked": <int>,
            "mismatches": [
                {
                    "as_of_date": "YYYY-MM-DD",
                    "user_id": "...",
                    "field": "sleep_hours" | ...,
                    "accepted_value": ...,
                    "reprojected_value": ...,
                },
                ...
            ],
        }

    If the DB has already moved past migration 003 the helper raises —
    callers are expected to run this gate on a pre-004 DB.
    """

    version = current_schema_version(conn)
    if version < 3:
        raise RuntimeError(
            f"dry-run diff for migration 004 needs schema version ≥ 3 "
            f"(synthesis scaffolding); got {version}"
        )
    if version >= 4:
        raise RuntimeError(
            f"dry-run diff for migration 004 is a pre-apply gate; DB is "
            f"already at schema version {version}"
        )

    mismatches: list[dict] = []
    rows_checked = 0

    accepted_rows = conn.execute(
        "SELECT as_of_date, user_id, sleep_hours, all_day_stress, "
        "manual_stress_score, body_battery_end_of_day "
        "FROM accepted_recovery_state_daily "
        "ORDER BY as_of_date, user_id"
    ).fetchall()

    for row in accepted_rows:
        rows_checked += 1
        as_of = row["as_of_date"]
        uid = row["user_id"]

        garmin = conn.execute(
            "SELECT sleep_deep_sec, sleep_light_sec, sleep_rem_sec, "
            "all_day_stress, body_battery "
            "FROM source_daily_garmin "
            "WHERE as_of_date = ? AND user_id = ? "
            "  AND export_batch_id NOT IN ("
            "      SELECT supersedes_export_batch_id FROM source_daily_garmin "
            "      WHERE supersedes_export_batch_id IS NOT NULL"
            "  ) "
            "ORDER BY ingested_at DESC LIMIT 1",
            (as_of, uid),
        ).fetchone()

        reprojected_sleep_hours = None
        reprojected_all_day_stress = None
        reprojected_body_battery = None
        if garmin is not None:
            total_sec = 0.0
            seen = False
            for col in ("sleep_deep_sec", "sleep_light_sec", "sleep_rem_sec"):
                v = garmin[col]
                if v is not None:
                    total_sec += float(v)
                    seen = True
            if seen and total_sec > 0:
                reprojected_sleep_hours = round(total_sec / 3600.0, 2)
            reprojected_all_day_stress = garmin["all_day_stress"]
            reprojected_body_battery = garmin["body_battery"]

        stress_raw = conn.execute(
            "SELECT score FROM stress_manual_raw "
            "WHERE as_of_date = ? AND user_id = ? "
            "  AND submission_id NOT IN ("
            "      SELECT supersedes_submission_id FROM stress_manual_raw "
            "      WHERE supersedes_submission_id IS NOT NULL"
            "  ) "
            "ORDER BY ingested_at DESC LIMIT 1",
            (as_of, uid),
        ).fetchone()
        reprojected_manual_score = stress_raw["score"] if stress_raw else None

        checks = (
            ("sleep_hours", row["sleep_hours"], reprojected_sleep_hours),
            ("all_day_stress", row["all_day_stress"], reprojected_all_day_stress),
            ("manual_stress_score", row["manual_stress_score"], reprojected_manual_score),
            ("body_battery_end_of_day", row["body_battery_end_of_day"], reprojected_body_battery),
        )
        for field, accepted_value, reproj_value in checks:
            if accepted_value != reproj_value:
                mismatches.append({
                    "as_of_date": as_of,
                    "user_id": uid,
                    "field": field,
                    "accepted_value": accepted_value,
                    "reprojected_value": reproj_value,
                })

    return {
        "migration": "004_sleep_stress_tables",
        "schema_version": version,
        "rows_checked": rows_checked,
        "mismatches": mismatches,
    }
