"""W-A — `hai intake gaps` presence block + is_partial_day + target_status.

Per `hai/reporting/plans/v0_1_15/PLAN.md` §2.B (round-4 typed contract).

Output contract additions to `hai intake gaps`:

  - `present` block:
      `{nutrition, gym, readiness, sleep, weigh_in}.logged: bool`
      Plus per-domain context (submission_id / session_id / set_count /
      meals_count / source). `weigh_in` always returns
      `{logged: false, reason: "intake_surface_not_yet_implemented"}`
      because W-B (intake weight surface) is deferred to v0.1.17 per
      F-PLAN-09 / W-E.
  - `is_partial_day: bool` — pure time + meal-count signal,
      target-independent. True when as_of==today_local AND local_now
      < cutoff (default 18:00) AND meals_count < expected (default 3).
  - `is_partial_day_reason: str` — diagnostic.
  - `target_status: "present" | "absent" | "unavailable"` — three-valued
      enum reading the existing `target` table per round-4 F-PHASE0-01
      Option A revision (no separate `nutrition_target` table).

Acceptance per PLAN §2.B:

  1. Output shape matches the round-4 contract; capabilities-manifest
     entry is updated.
  2. `is_partial_day` true at 10:00 with 1 meal; false at 19:00 with 4
     meals; transitions across cutoff.
  3. `target_status` cycles through present/absent/unavailable across
     three fixture states (active row covering today; row exists but
     doesn't cover today via effective_to bound; no nutrition rows at
     all).
  4. Read-side parallel with W-C: W-A is testable independently against
     `target` rows seeded directly in fixtures (no dependency on the
     `hai target nutrition` convenience handler).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.intake.presence import (
    compute_presence_block,
    is_partial_day,
)
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)


USER = "u_test"
TODAY = date(2026, 5, 3)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _seed_nutrition_intake(
    db_path: Path, *, as_of: date, meals_count: int,
) -> str:
    """Insert a nutrition_intake_raw row for (as_of, user). Returns
    the submission_id."""
    submission_id = (
        f"m_nut_{as_of.isoformat()}_{datetime.now().strftime('%H%M%S%f')}"
    )
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO nutrition_intake_raw "
            "(submission_id, user_id, as_of_date, calories, protein_g, "
            "carbs_g, fat_g, hydration_l, meals_count, source, "
            "ingest_actor, ingested_at, supersedes_submission_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                submission_id, USER, as_of.isoformat(),
                2200.0, 160.0, 220.0, 70.0, 2.5, meals_count,
                "user_manual", "cli",
                datetime.now(timezone.utc).isoformat(), None,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return submission_id


def _seed_gym_session(
    db_path: Path, *, as_of: date, set_count: int,
) -> str:
    """Insert a gym_session + N gym_set rows. Returns session_id."""
    session_id = f"sess_{as_of.isoformat()}_{set_count}"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO gym_session (session_id, user_id, as_of_date, "
            "session_name, notes, source, ingest_actor, submission_id, "
            "ingested_at, supersedes_session_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                session_id, USER, as_of.isoformat(), "Test session", None,
                "user_manual", "cli", f"m_gym_{session_id}",
                datetime.now(timezone.utc).isoformat(), None,
            ),
        )
        for n in range(1, set_count + 1):
            conn.execute(
                "INSERT INTO gym_set (set_id, session_id, set_number, "
                "exercise_name, weight_kg, reps, rpe, ingested_at, "
                "supersedes_set_id) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    f"set_{session_id}_test_{n:03d}", session_id, n,
                    "Test", 50.0, 5, 7.0,
                    datetime.now(timezone.utc).isoformat(), None,
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return session_id


def _seed_nutrition_target(
    db_path: Path,
    *,
    target_type: str,
    value: float,
    unit: str,
    effective_from: date,
    effective_to: Optional[date] = None,
    status: str = "active",
) -> str:
    """Insert a nutrition target row in the existing `target` table."""
    target_id = (
        f"target_{target_type}_{effective_from.isoformat()}_"
        f"{datetime.now().strftime('%H%M%S%f')}"
    )
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO target ("
            "target_id, user_id, domain, target_type, status, "
            "value_json, unit, effective_from, effective_to, reason, "
            "source, ingest_actor, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                target_id, USER, "nutrition", target_type, status,
                json.dumps({"value": value}), unit,
                effective_from.isoformat(),
                effective_to.isoformat() if effective_to else None,
                "test seed", "user_authored", "cli",
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return target_id


# ---------------------------------------------------------------------------
# is_partial_day unit tests (pure function)
# ---------------------------------------------------------------------------


def test_is_partial_day_true_morning_with_few_meals():
    """PLAN §2.B acceptance 4: is_partial_day true at 10:00 with 1 meal."""
    now = datetime(2026, 5, 3, 10, 17)
    result, reason = is_partial_day(
        as_of=now.date(), meals_count=1, now_local=now,
    )
    assert result is True
    assert "10:17" in reason and "18:00" in reason


def test_is_partial_day_false_evening_with_many_meals():
    """PLAN §2.B acceptance 4: is_partial_day false at 19:00 with 4 meals."""
    now = datetime(2026, 5, 3, 19, 0)
    result, reason = is_partial_day(
        as_of=now.date(), meals_count=4, now_local=now,
    )
    assert result is False


def test_is_partial_day_false_past_cutoff_alone():
    """Past cutoff with low meal count: still false (day is closed)."""
    now = datetime(2026, 5, 3, 19, 0)
    result, reason = is_partial_day(
        as_of=now.date(), meals_count=1, now_local=now,
    )
    assert result is False
    assert "cutoff" in reason


def test_is_partial_day_false_meals_met_alone():
    """Pre-cutoff but meals already met: false (user logged whole day)."""
    now = datetime(2026, 5, 3, 14, 0)
    result, reason = is_partial_day(
        as_of=now.date(), meals_count=4, now_local=now,
    )
    assert result is False
    assert "meals" in reason


def test_is_partial_day_false_for_past_day():
    """as_of < today_local: day is closed regardless of time."""
    now = datetime(2026, 5, 3, 10, 0)
    result, reason = is_partial_day(
        as_of=date(2026, 5, 1), meals_count=0, now_local=now,
    )
    assert result is False
    assert "today" in reason or "past" in reason


def test_compute_presence_block_honours_threshold_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    """F-IR-03 (round-1 IR): the W-A cutoff + expected_meals defaults
    are configurable via `gap_detection.presence_partial_day_*` keys
    in thresholds.toml. Override via DEFAULT_THRESHOLDS monkeypatch
    so the test doesn't write to the user's real config."""

    from health_agent_infra.core import config as _cfg

    db = _init_db(tmp_path)
    _seed_nutrition_intake(db, as_of=TODAY, meals_count=2)

    # Override cutoff to 09:00 — at 10:00 the call should now NOT
    # be partial-day (we're past the cutoff). Default 18:00 would
    # have returned partial=True.
    overridden = dict(_cfg.DEFAULT_THRESHOLDS)
    overridden["gap_detection"] = dict(overridden["gap_detection"])
    overridden["gap_detection"]["presence_partial_day_cutoff_hour"] = 9
    monkeypatch.setattr(_cfg, "DEFAULT_THRESHOLDS", overridden)

    conn = open_connection(db)
    try:
        block = compute_presence_block(
            conn, as_of=TODAY, user_id=USER,
            now_local=datetime(2026, 5, 3, 10, 0),
        )
    finally:
        conn.close()

    assert block["is_partial_day"] is False, (
        f"override cutoff_hour=9 should make 10:00 past-cutoff; "
        f"got is_partial_day={block['is_partial_day']!r}, "
        f"reason={block['is_partial_day_reason']!r}"
    )


# ---------------------------------------------------------------------------
# Presence block — compute_presence_block tests
# ---------------------------------------------------------------------------


def test_presence_block_shape_when_nothing_logged(tmp_path: Path):
    """Empty DB: every domain reports logged=false; weigh_in carries the
    intake-surface-not-yet-implemented reason."""
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        block = compute_presence_block(
            conn,
            as_of=TODAY,
            user_id=USER,
            now_local=datetime(2026, 5, 3, 10, 0),
        )
    finally:
        conn.close()

    assert set(block["present"].keys()) == {
        "nutrition", "gym", "readiness", "sleep", "weigh_in",
    }
    assert block["present"]["nutrition"]["logged"] is False
    assert block["present"]["gym"]["logged"] is False
    assert block["present"]["readiness"]["logged"] is False
    assert block["present"]["sleep"]["logged"] is False
    assert block["present"]["weigh_in"] == {
        "logged": False,
        "reason": "intake_surface_not_yet_implemented",
    }


def test_presence_block_reflects_logged_nutrition_and_gym(tmp_path: Path):
    """When nutrition + gym are logged for today, presence block reports
    logged=true with the relevant submission/session ids and counts."""
    db = _init_db(tmp_path)
    submission = _seed_nutrition_intake(db, as_of=TODAY, meals_count=2)
    session = _seed_gym_session(db, as_of=TODAY, set_count=11)

    conn = open_connection(db)
    try:
        block = compute_presence_block(
            conn,
            as_of=TODAY,
            user_id=USER,
            now_local=datetime(2026, 5, 3, 10, 0),
        )
    finally:
        conn.close()

    assert block["present"]["nutrition"]["logged"] is True
    assert block["present"]["nutrition"]["submission_id"] == submission
    assert block["present"]["nutrition"]["meals_count"] == 2
    assert block["present"]["gym"]["logged"] is True
    assert block["present"]["gym"]["session_id"] == session
    assert block["present"]["gym"]["set_count"] == 11


def test_presence_block_carries_is_partial_day_signals(tmp_path: Path):
    """is_partial_day + is_partial_day_reason are present + correctly
    derived from the presence-block context."""
    db = _init_db(tmp_path)
    _seed_nutrition_intake(db, as_of=TODAY, meals_count=1)

    conn = open_connection(db)
    try:
        morning = compute_presence_block(
            conn, as_of=TODAY, user_id=USER,
            now_local=datetime(2026, 5, 3, 10, 17),
        )
        evening = compute_presence_block(
            conn, as_of=TODAY, user_id=USER,
            now_local=datetime(2026, 5, 3, 19, 0),
        )
    finally:
        conn.close()

    assert morning["is_partial_day"] is True
    assert "10:17" in morning["is_partial_day_reason"]
    assert evening["is_partial_day"] is False


# ---------------------------------------------------------------------------
# target_status — three-valued enum tests
# ---------------------------------------------------------------------------


def test_target_status_present_with_active_row_covering_today(tmp_path: Path):
    """Active nutrition target row whose effective window includes today:
    target_status='present'."""
    db = _init_db(tmp_path)
    _seed_nutrition_target(
        db,
        target_type="calories_kcal",
        value=3000,
        unit="kcal",
        effective_from=TODAY - timedelta(days=2),
        effective_to=None,  # open-ended
    )

    conn = open_connection(db)
    try:
        block = compute_presence_block(
            conn, as_of=TODAY, user_id=USER,
            now_local=datetime(2026, 5, 3, 10, 0),
        )
    finally:
        conn.close()

    assert block["target_status"] == "present"


def test_target_status_absent_when_row_exists_but_does_not_cover_today(
    tmp_path: Path,
):
    """Nutrition target row exists historically but its effective_to is
    in the past: target_status='absent' (not 'unavailable')."""
    db = _init_db(tmp_path)
    _seed_nutrition_target(
        db,
        target_type="calories_kcal",
        value=3000,
        unit="kcal",
        effective_from=TODAY - timedelta(days=30),
        effective_to=TODAY - timedelta(days=1),  # expired yesterday
    )

    conn = open_connection(db)
    try:
        block = compute_presence_block(
            conn, as_of=TODAY, user_id=USER,
            now_local=datetime(2026, 5, 3, 10, 0),
        )
    finally:
        conn.close()

    assert block["target_status"] == "absent"


def test_target_status_unavailable_when_no_nutrition_rows_at_all(
    tmp_path: Path,
):
    """No nutrition target rows for the user: target_status='unavailable'.
    A non-nutrition target row (e.g., training_load) does NOT count."""
    db = _init_db(tmp_path)
    # Seed a non-nutrition target to confirm filter by domain.
    _seed_nutrition_target(
        db,
        target_type="training_load",  # type-correct row but
        value=200,
        unit="trimp",
        effective_from=TODAY,
    )
    # Override the domain to "training" via direct SQL (the seed helper
    # uses domain='nutrition'; we want a non-nutrition row).
    conn = sqlite3.connect(str(db))
    try:
        conn.execute(
            "UPDATE target SET domain = 'training' WHERE user_id = ?",
            (USER,),
        )
        conn.commit()
    finally:
        conn.close()

    conn = open_connection(db)
    try:
        block = compute_presence_block(
            conn, as_of=TODAY, user_id=USER,
            now_local=datetime(2026, 5, 3, 10, 0),
        )
    finally:
        conn.close()

    assert block["target_status"] == "unavailable"


# ---------------------------------------------------------------------------
# CLI integration — `hai intake gaps --from-state-snapshot`
# ---------------------------------------------------------------------------


def test_intake_gaps_cli_emits_present_block_and_target_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys,
):
    """Full CLI invocation: `hai intake gaps --from-state-snapshot`
    emits the new W-A keys in the JSON payload."""
    monkeypatch.delenv("HAI_DEMO_MARKER_PATH", raising=False)
    db = _init_db(tmp_path)
    _seed_nutrition_intake(db, as_of=TODAY, meals_count=1)

    # Seed a sync_run_log row so --from-state-snapshot's staleness gate
    # passes (the gate refuses with no successful pull within 48h).
    conn = sqlite3.connect(str(db))
    try:
        conn.execute(
            "INSERT INTO sync_run_log "
            "(source, user_id, mode, started_at, completed_at, status, "
            "for_date, rows_pulled, rows_accepted, duplicates_skipped) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                "intervals_icu", USER, "live",
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat(),
                "ok", TODAY.isoformat(), 1, 1, 0,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    rc = cli_main([
        "intake", "gaps",
        "--from-state-snapshot",
        "--as-of", TODAY.isoformat(),
        "--user-id", USER,
        "--db-path", str(db),
    ])
    assert rc == exit_codes.OK
    payload = json.loads(capsys.readouterr().out)

    assert "present" in payload, (
        f"intake gaps payload must include W-A 'present' block: keys={list(payload.keys())}"
    )
    assert set(payload["present"].keys()) == {
        "nutrition", "gym", "readiness", "sleep", "weigh_in",
    }
    assert payload["present"]["weigh_in"]["logged"] is False
    assert payload["present"]["weigh_in"]["reason"] == (
        "intake_surface_not_yet_implemented"
    )

    assert "is_partial_day" in payload
    assert "is_partial_day_reason" in payload
    assert "target_status" in payload
    assert payload["target_status"] in ("present", "absent", "unavailable")
