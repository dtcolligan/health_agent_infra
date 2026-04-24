"""D4 test #1 — cold-start detection per domain.

``_cold_start_flags`` counts distinct ``as_of_date`` values with
*meaningful* signal (not just bare row presence) up to — but not
including — ``as_of_date``. A user crosses out of cold-start for a
given domain when they accumulate
``COLD_START_THRESHOLD_DAYS`` (14) such days.

The predicate is deliberately strict-less-than: today's row doesn't
count because cold-start is about history accrued *before* the day
being planned. This matches D4 §Cold-start detection.

Covers:

- Zero history → cold_start True for every domain.
- 13 days of meaningful signal → cold_start True.
- Exactly 14 days → cold_start False (graduation).
- Rows that don't satisfy the domain predicate (e.g. running row
  with all aggregate columns NULL) don't count toward the window.
- Each domain's predicate is independent — 14 running days leaves
  strength / stress / nutrition still cold-start.
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest

from health_agent_infra.core.state import initialize_database
from health_agent_infra.core.state.snapshot import (
    COLD_START_THRESHOLD_DAYS,
    _cold_start_flags,
    _domain_history_days,
    build_snapshot,
)


USER = "u_cold"
AS_OF = date(2026, 4, 24)


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _conn(db: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn


def _insert_running(
    conn: sqlite3.Connection,
    *,
    as_of_date: date,
    user_id: str = USER,
    total_distance_m: float | None = 5000.0,
    total_duration_s: float | None = 1800.0,
    session_count: int | None = 1,
) -> None:
    conn.execute(
        """
        INSERT INTO accepted_running_state_daily (
            as_of_date, user_id,
            total_distance_m, total_duration_s,
            moderate_intensity_min, vigorous_intensity_min,
            session_count, derivation_path,
            derived_from, source, ingest_actor, projected_at
        ) VALUES (?, ?, ?, ?, NULL, NULL, ?, 'running_sessions',
                  'seed', 'seed', 'seed', '2026-04-24T00:00:00+00:00')
        """,
        (
            as_of_date.isoformat(), user_id,
            total_distance_m, total_duration_s,
            session_count,
        ),
    )


def _insert_recovery(
    conn: sqlite3.Connection,
    *,
    as_of_date: date,
    user_id: str = USER,
    resting_hr: float | None = 52.0,
    hrv_ms: float | None = 55.0,
) -> None:
    conn.execute(
        """
        INSERT INTO accepted_recovery_state_daily (
            as_of_date, user_id,
            resting_hr, hrv_ms,
            derived_from, source, ingest_actor, projected_at
        ) VALUES (?, ?, ?, ?, 'seed', 'seed', 'seed',
                  '2026-04-24T00:00:00+00:00')
        """,
        (
            as_of_date.isoformat(), user_id,
            resting_hr, hrv_ms,
        ),
    )


# ---------------------------------------------------------------------------
# Zero-history baseline
# ---------------------------------------------------------------------------


def test_fresh_db_puts_every_domain_in_cold_start(tmp_path: Path):
    db = _init_db(tmp_path)
    with _conn(db) as conn:
        flags = _cold_start_flags(conn, user_id=USER, as_of_date=AS_OF)

    # All six tracked domains must report cold_start=True on a fresh DB.
    for domain, row in flags.items():
        assert row["cold_start"] is True, domain
        assert row["history_days"] == 0, domain


# ---------------------------------------------------------------------------
# Running predicate — aggregate-column-null rows don't count
# ---------------------------------------------------------------------------


def test_running_only_counts_days_with_meaningful_signal(tmp_path: Path):
    db = _init_db(tmp_path)
    with _conn(db) as conn:
        # Insert a metadata-only running row (all aggregate columns NULL).
        _insert_running(
            conn,
            as_of_date=AS_OF - timedelta(days=5),
            total_distance_m=None,
            total_duration_s=None,
            session_count=None,
        )
        conn.commit()

        flags = _cold_start_flags(conn, user_id=USER, as_of_date=AS_OF)

    # Metadata-only row doesn't satisfy the predicate — still zero days.
    assert flags["running"]["history_days"] == 0
    assert flags["running"]["cold_start"] is True


# ---------------------------------------------------------------------------
# Boundary conditions — THRESHOLD - 1, THRESHOLD, THRESHOLD + 1
# ---------------------------------------------------------------------------


def test_thirteen_days_keeps_running_in_cold_start(tmp_path: Path):
    """13 distinct days of real running signal — still below the 14-day
    threshold, so cold_start remains True."""

    db = _init_db(tmp_path)
    with _conn(db) as conn:
        for offset in range(1, COLD_START_THRESHOLD_DAYS):  # 1..13
            _insert_running(conn, as_of_date=AS_OF - timedelta(days=offset))
        conn.commit()

        flags = _cold_start_flags(conn, user_id=USER, as_of_date=AS_OF)

    assert flags["running"]["history_days"] == 13
    assert flags["running"]["cold_start"] is True


def test_exactly_fourteen_days_graduates_from_cold_start(tmp_path: Path):
    """Crossing the 14-day threshold flips cold_start to False."""

    db = _init_db(tmp_path)
    with _conn(db) as conn:
        for offset in range(1, COLD_START_THRESHOLD_DAYS + 1):  # 1..14
            _insert_running(conn, as_of_date=AS_OF - timedelta(days=offset))
        conn.commit()

        flags = _cold_start_flags(conn, user_id=USER, as_of_date=AS_OF)

    assert flags["running"]["history_days"] == 14
    assert flags["running"]["cold_start"] is False


def test_today_row_does_not_count_toward_the_window(tmp_path: Path):
    """Cold-start is about history *before* today. A row on ``as_of``
    should not shorten the window — otherwise a user's first day always
    reports `history_days >= 1` spuriously.
    """

    db = _init_db(tmp_path)
    with _conn(db) as conn:
        _insert_running(conn, as_of_date=AS_OF)
        conn.commit()

        assert _domain_history_days(
            conn, domain="running", user_id=USER, as_of_date=AS_OF,
        ) == 0


# ---------------------------------------------------------------------------
# Per-domain independence
# ---------------------------------------------------------------------------


def test_domains_track_cold_start_independently(tmp_path: Path):
    """Seeding 14 days of running must NOT graduate recovery (or any
    other domain) out of cold-start."""

    db = _init_db(tmp_path)
    with _conn(db) as conn:
        for offset in range(1, COLD_START_THRESHOLD_DAYS + 1):
            _insert_running(conn, as_of_date=AS_OF - timedelta(days=offset))
        conn.commit()

        flags = _cold_start_flags(conn, user_id=USER, as_of_date=AS_OF)

    assert flags["running"]["cold_start"] is False
    # Every other domain still cold-start.
    for domain in ("recovery", "sleep", "strength", "stress", "nutrition"):
        assert flags[domain]["cold_start"] is True, domain
        assert flags[domain]["history_days"] == 0, domain


def test_recovery_graduates_independently(tmp_path: Path):
    db = _init_db(tmp_path)
    with _conn(db) as conn:
        for offset in range(1, COLD_START_THRESHOLD_DAYS + 1):
            _insert_recovery(conn, as_of_date=AS_OF - timedelta(days=offset))
        conn.commit()

        flags = _cold_start_flags(conn, user_id=USER, as_of_date=AS_OF)

    assert flags["recovery"]["cold_start"] is False
    assert flags["running"]["cold_start"] is True


# ---------------------------------------------------------------------------
# Snapshot integration — each block carries cold_start + history_days
# ---------------------------------------------------------------------------


def test_build_snapshot_attaches_cold_start_to_every_domain(tmp_path: Path):
    db = _init_db(tmp_path)
    with _conn(db) as conn:
        snap = build_snapshot(conn, as_of_date=AS_OF, user_id=USER)

    for domain in ("recovery", "running", "sleep", "strength", "stress", "nutrition"):
        block = snap[domain]
        assert "cold_start" in block, domain
        assert "history_days" in block, domain
        assert block["cold_start"] is True
        assert block["history_days"] == 0


def test_build_snapshot_reflects_partial_graduation(tmp_path: Path):
    """A user with 14 days of running but zero other history gets
    mixed cold-start state on the snapshot blocks."""

    db = _init_db(tmp_path)
    with _conn(db) as conn:
        for offset in range(1, COLD_START_THRESHOLD_DAYS + 1):
            _insert_running(conn, as_of_date=AS_OF - timedelta(days=offset))
        conn.commit()

        snap = build_snapshot(conn, as_of_date=AS_OF, user_id=USER)

    assert snap["running"]["cold_start"] is False
    assert snap["running"]["history_days"] == 14
    for domain in ("recovery", "sleep", "strength", "stress", "nutrition"):
        assert snap[domain]["cold_start"] is True, domain
