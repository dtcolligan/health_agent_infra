"""Phase 7A.3 — `hai clean` projects into the state DB.

Three contracts this file pins:

  1. Projectors (unit): `project_source_daily_garmin`,
     `project_accepted_recovery_state_daily`, and
     `project_accepted_running_state_daily` each produce the right row shape
     from a Garmin raw daily row. UPSERT for accepted tables sets
     `corrected_at` only on update; raw is append-only and idempotent on the
     (as_of_date, user_id, export_batch_id) PK.

  2. CLI integration: `hai clean --evidence-json <p> --db-path <p>` populates
     source_daily_garmin + the two accepted daily tables, and a subsequent
     `hai state snapshot` returns `missingness='present'` for recovery and
     running. Fail-soft if DB is absent — stdout is still emitted.

  3. 7D snapshot semantics fixes:
       - stress: Garmin present + manual null + day closed → `partial:...`,
         not `absent`.
       - user-reported domain, same-day, before cutover, row exists with
         null fields → `pending_user_input:<fields>`, not `partial:...`.
       - running with `derivation_path='garmin_daily'` +
         `session_count=NULL` is not mislabeled partial.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, time
from io import StringIO
from pathlib import Path
from contextlib import redirect_stdout

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.state import (
    build_snapshot,
    initialize_database,
    open_connection,
    project_accepted_recovery_state_daily,
    project_accepted_running_state_daily,
    project_source_daily_garmin,
    read_domain,
)


USER = "u_test"
AS_OF = date(2026, 4, 17)


def _full_raw_row() -> dict:
    """A full-ish Garmin daily row — the subset of columns 7A.3 projects."""

    return {
        "steps": 12000,
        "distance_m": 8500.0,
        "active_kcal": 620.0,
        "total_kcal": 2400.0,
        "moderate_intensity_min": 35,
        "vigorous_intensity_min": 18,
        "floors_ascended_m": 24.0,
        "avg_environment_altitude_m": 180.0,
        "resting_hr": 52.0,
        "min_hr_day": 44.0,
        "max_hr_day": 168.0,
        "sleep_deep_sec": 5400,
        "sleep_light_sec": 12600,
        "sleep_rem_sec": 5400,
        "sleep_awake_sec": 600,
        "avg_sleep_respiration": 14.1,
        "avg_sleep_stress": 22.0,
        "awake_count": 2,
        "sleep_score_overall": 84,
        "sleep_score_quality": 80,
        "sleep_score_duration": 88,
        "sleep_score_recovery": 82,
        "all_day_stress": 30,
        "body_battery": 65,
        "training_readiness_level": "High",
        "training_recovery_time_hours": 18.0,
        "training_readiness_sleep_pct": 82.0,
        "training_readiness_hrv_pct": 70.0,
        "training_readiness_stress_pct": 75.0,
        "training_readiness_sleep_history_pct": 88.0,
        "training_readiness_load_pct": 65.0,
        "training_readiness_hrv_weekly_avg": 48.0,
        "training_readiness_valid_sleep": 1,
        "acute_load": 400.0,
        "chronic_load": 380.0,
        "acwr_status": "Optimal",
        "acwr_status_feedback": "Training load is well balanced.",
        "training_status": "Productive",
        "training_status_feedback": "Your fitness is improving.",
        "health_hrv_value": 48.0,
        "health_hrv_status": "Balanced",
        "health_hrv_baseline_low": 38.0,
        "health_hrv_baseline_high": 58.0,
        "health_hr_value": 52.0,
        "health_hr_status": "Balanced",
        "health_hr_baseline_low": 48.0,
        "health_hr_baseline_high": 60.0,
        "health_spo2_value": 97.0,
        "health_spo2_status": "Balanced",
        "health_spo2_baseline_low": 94.0,
        "health_spo2_baseline_high": 99.0,
        "health_skin_temp_c_value": 36.4,
        "health_skin_temp_c_status": "Balanced",
        "health_skin_temp_c_baseline_low": 36.0,
        "health_skin_temp_c_baseline_high": 36.8,
        "health_respiration_value": 14.0,
        "health_respiration_status": "Balanced",
        "health_respiration_baseline_low": 12.0,
        "health_respiration_baseline_high": 16.0,
    }


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


# ---------------------------------------------------------------------------
# Unit: source_daily_garmin projector
# ---------------------------------------------------------------------------

def test_source_daily_garmin_insert_happy_path(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        inserted = project_source_daily_garmin(
            conn,
            as_of_date=AS_OF,
            user_id=USER,
            raw_row=_full_raw_row(),
            export_batch_id="batch_2026-04-17_01",
        )
        assert inserted is True
        rows = read_domain(
            conn, domain="recovery", since=AS_OF, until=AS_OF, user_id=USER,
        )
        # No accepted row yet; snapshot 'recovery' would be absent.
        assert rows == []

        raw_rows = conn.execute(
            "SELECT resting_hr, health_hrv_value, distance_m, moderate_intensity_min, "
            "all_day_stress, acute_load, source, ingest_actor "
            "FROM source_daily_garmin WHERE as_of_date = ? AND user_id = ?",
            (AS_OF.isoformat(), USER),
        ).fetchall()
        assert len(raw_rows) == 1
        r = raw_rows[0]
        assert r["resting_hr"] == 52.0
        assert r["health_hrv_value"] == 48.0
        assert r["distance_m"] == 8500.0
        assert r["moderate_intensity_min"] == 35
        assert r["all_day_stress"] == 30
        assert r["acute_load"] == 400.0
        assert r["source"] == "garmin"
        assert r["ingest_actor"] == "garmin_csv_adapter"
    finally:
        conn.close()


def test_source_daily_garmin_is_idempotent_on_pk(tmp_path: Path):
    """Re-running with the same export_batch_id is a no-op."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        assert project_source_daily_garmin(
            conn, as_of_date=AS_OF, user_id=USER,
            raw_row=_full_raw_row(), export_batch_id="batch_x",
        ) is True
        assert project_source_daily_garmin(
            conn, as_of_date=AS_OF, user_id=USER,
            raw_row=_full_raw_row(), export_batch_id="batch_x",
        ) is False
        count = conn.execute(
            "SELECT COUNT(*) FROM source_daily_garmin "
            "WHERE as_of_date = ? AND user_id = ?",
            (AS_OF.isoformat(), USER),
        ).fetchone()[0]
        assert count == 1
    finally:
        conn.close()


def test_source_daily_garmin_different_batch_id_is_append(tmp_path: Path):
    """A correction pull lands as a distinct raw row (append-only semantics)."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        project_source_daily_garmin(
            conn, as_of_date=AS_OF, user_id=USER,
            raw_row=_full_raw_row(), export_batch_id="batch_a",
        )
        raw_b = dict(_full_raw_row())
        raw_b["resting_hr"] = 49.0  # Garmin re-stated RHR lower
        project_source_daily_garmin(
            conn, as_of_date=AS_OF, user_id=USER,
            raw_row=raw_b, export_batch_id="batch_b",
            supersedes_export_batch_id="batch_a",
        )
        rows = conn.execute(
            "SELECT resting_hr, supersedes_export_batch_id FROM source_daily_garmin "
            "WHERE as_of_date = ? AND user_id = ? ORDER BY export_batch_id",
            (AS_OF.isoformat(), USER),
        ).fetchall()
        assert len(rows) == 2
        assert rows[0]["resting_hr"] == 52.0
        assert rows[1]["resting_hr"] == 49.0
        assert rows[1]["supersedes_export_batch_id"] == "batch_a"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Unit: accepted_recovery_state_daily projector
# ---------------------------------------------------------------------------

def test_accepted_recovery_insert_sets_projected_at_and_null_corrected_at(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        inserted = project_accepted_recovery_state_daily(
            conn,
            as_of_date=AS_OF,
            user_id=USER,
            raw_row=_full_raw_row(),
            source_row_ids=["batch_x:0"],
        )
        assert inserted is True
        row = conn.execute(
            "SELECT * FROM accepted_recovery_state_daily "
            "WHERE as_of_date = ? AND user_id = ?",
            (AS_OF.isoformat(), USER),
        ).fetchone()
        assert row is not None
        assert row["sleep_hours"] == pytest.approx((5400 + 12600 + 5400) / 3600.0, rel=0.01)
        assert row["resting_hr"] == 52.0
        assert row["hrv_ms"] == 48.0
        assert row["all_day_stress"] == 30
        # manual_stress_score is NEVER populated by this projector in v1 —
        # it must flow through stress_manual_raw first (7C). Stays NULL.
        assert row["manual_stress_score"] is None
        assert row["acute_load"] == 400.0
        assert row["chronic_load"] == 380.0
        # acwr_ratio is computed: 400/380
        assert row["acwr_ratio"] == pytest.approx(400.0 / 380.0, rel=0.001)
        # training_readiness_pct deferred to 7B
        assert row["training_readiness_pct"] is None
        assert row["body_battery_end_of_day"] == 65
        assert row["projected_at"] is not None
        assert row["corrected_at"] is None
        derived = json.loads(row["derived_from"])
        assert derived == ["batch_x:0"]
    finally:
        conn.close()


def test_accepted_recovery_upsert_sets_corrected_at(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        project_accepted_recovery_state_daily(
            conn, as_of_date=AS_OF, user_id=USER, raw_row=_full_raw_row(),
        )
        corrected_row = dict(_full_raw_row())
        corrected_row["resting_hr"] = 49.0
        inserted = project_accepted_recovery_state_daily(
            conn, as_of_date=AS_OF, user_id=USER, raw_row=corrected_row,
        )
        assert inserted is False  # it was an UPDATE
        row = conn.execute(
            "SELECT resting_hr, manual_stress_score, corrected_at FROM "
            "accepted_recovery_state_daily WHERE as_of_date = ? AND user_id = ?",
            (AS_OF.isoformat(), USER),
        ).fetchone()
        assert row["resting_hr"] == 49.0
        assert row["manual_stress_score"] is None  # still NULL on upsert
        assert row["corrected_at"] is not None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Unit: accepted_running_state_daily projector
# ---------------------------------------------------------------------------

def test_accepted_running_insert_uses_garmin_daily_derivation_path(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        inserted = project_accepted_running_state_daily(
            conn, as_of_date=AS_OF, user_id=USER, raw_row=_full_raw_row(),
        )
        assert inserted is True
        row = conn.execute(
            "SELECT * FROM accepted_running_state_daily "
            "WHERE as_of_date = ? AND user_id = ?",
            (AS_OF.isoformat(), USER),
        ).fetchone()
        assert row["derivation_path"] == "garmin_daily"
        assert row["total_distance_m"] == 8500.0
        assert row["moderate_intensity_min"] == 35
        assert row["vigorous_intensity_min"] == 18
        assert row["session_count"] is None  # NULL by design on garmin_daily path
        assert row["total_duration_s"] is None  # 7B-deferred enrichment
        assert row["corrected_at"] is None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Snapshot semantics fix: running garmin_daily path does not mislabel partial
# ---------------------------------------------------------------------------

def test_snapshot_running_garmin_daily_is_present_with_core_fields(tmp_path: Path):
    """Running row with derivation_path='garmin_daily', session_count=NULL,
    total_duration_s=NULL must NOT be tagged partial. session_count is NULL
    by design on this derivation path (state_model_v1.md §8)."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        project_accepted_running_state_daily(
            conn, as_of_date=AS_OF, user_id=USER, raw_row=_full_raw_row(),
        )
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 5, 1, 10, 0),
        )
    finally:
        conn.close()

    assert snap["running"]["missingness"] == "present"


# ---------------------------------------------------------------------------
# Snapshot semantics fix: user-reported partial before cutover is pending
# ---------------------------------------------------------------------------

def test_snapshot_user_reported_partial_before_cutover_is_pending_not_partial(tmp_path: Path):
    """A nutrition row with some null fields, on today's date before 23:30,
    must emit `pending_user_input:<fields>`, not `partial:<fields>`."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        # Seed nutrition with carbs_g/fat_g NULL (mid-day state; dinner not
        # logged yet).
        conn.execute(
            """
            INSERT INTO accepted_nutrition_state_daily (
                as_of_date, user_id, calories, protein_g,
                carbs_g, fat_g, hydration_l, meals_count,
                derived_from, source, ingest_actor, projected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                AS_OF.isoformat(), USER, 1200.0, 90.0,
                None, None, 1.5, 2,
                "[]", "user_manual", "claude_agent_v1",
                "2026-04-17T14:45:00Z",
            ),
        )
        conn.commit()
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(AS_OF.year, AS_OF.month, AS_OF.day, 14, 45),
        )
    finally:
        conn.close()

    mx = snap["nutrition"]["missingness"]
    assert mx.startswith("pending_user_input:"), f"expected pending_user_input, got {mx!r}"
    assert "carbs_g" in mx and "fat_g" in mx


def test_snapshot_user_reported_partial_after_cutover_is_partial(tmp_path: Path):
    """Same partial nutrition row, but after 23:30 local → `partial`."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        conn.execute(
            """
            INSERT INTO accepted_nutrition_state_daily (
                as_of_date, user_id, calories, protein_g,
                carbs_g, fat_g,
                derived_from, source, ingest_actor, projected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                AS_OF.isoformat(), USER, 1200.0, 90.0,
                None, None,
                "[]", "user_manual", "claude_agent_v1",
                "2026-04-17T23:45:00Z",
            ),
        )
        conn.commit()
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(AS_OF.year, AS_OF.month, AS_OF.day, 23, 45),
        )
    finally:
        conn.close()

    mx = snap["nutrition"]["missingness"]
    assert mx.startswith("partial:"), f"expected partial, got {mx!r}"
    assert "carbs_g" in mx and "fat_g" in mx


# ---------------------------------------------------------------------------
# Snapshot semantics fix: stress with Garmin present + manual null
# ---------------------------------------------------------------------------

def test_snapshot_stress_garmin_present_manual_null_after_cutover_is_partial(tmp_path: Path):
    """Garmin all_day_stress=30, manual_stress_score=NULL, day closed →
    missingness must be `partial:manual_stress_score`, not `absent`."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        project_accepted_recovery_state_daily(
            conn, as_of_date=AS_OF, user_id=USER,
            raw_row=_full_raw_row(),  # carries all_day_stress=30
        )
        # manual_stress_score is NOT populated by this projector; it stays
        # NULL until 7C lands the stress_manual_raw path.
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 5, 1, 10, 0),  # day well-closed
        )
    finally:
        conn.close()

    assert snap["stress"]["today_garmin"] == 30
    assert snap["stress"]["today_manual"] is None
    mx = snap["stress"]["missingness"]
    assert mx == "partial:manual_stress_score", f"got {mx!r}"


def test_snapshot_stress_garmin_present_manual_null_before_cutover_is_pending(tmp_path: Path):
    """Same row, today before cutover → `pending_user_input:manual_stress_score`."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        project_accepted_recovery_state_daily(
            conn, as_of_date=AS_OF, user_id=USER, raw_row=_full_raw_row(),
        )
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(AS_OF.year, AS_OF.month, AS_OF.day, 14, 0),
        )
    finally:
        conn.close()

    mx = snap["stress"]["missingness"]
    assert mx == "pending_user_input:manual_stress_score", f"got {mx!r}"


def test_snapshot_stress_both_null_day_closed_is_absent(tmp_path: Path):
    """Both stress signals null, day closed → `absent` (unchanged behaviour)."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        # Seed a recovery row with all_day_stress=NULL and manual=NULL.
        conn.execute(
            """
            INSERT INTO accepted_recovery_state_daily (
                as_of_date, user_id, sleep_hours, resting_hr, hrv_ms,
                all_day_stress, manual_stress_score,
                acute_load, chronic_load, acwr_ratio,
                body_battery_end_of_day,
                derived_from, source, ingest_actor, projected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                AS_OF.isoformat(), USER, 7.8, 52.0, 48.0,
                None, None, 400.0, 380.0, 1.05, 65,
                "[]", "garmin", "garmin_csv_adapter",
                "2026-04-17T06:00:00Z",
            ),
        )
        conn.commit()
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 5, 1, 10, 0),
        )
    finally:
        conn.close()

    assert snap["stress"]["missingness"] == "absent"


# ---------------------------------------------------------------------------
# CLI integration: `hai clean` populates the DB + snapshot returns present
# ---------------------------------------------------------------------------

def _write_pull_payload(tmp_path: Path) -> Path:
    """Emit a `hai pull`-shaped JSON file with a raw_daily_row."""

    payload = {
        "as_of_date": AS_OF.isoformat(),
        "user_id": USER,
        "source": "garmin",
        "pull": {
            "sleep": {"record_id": "g_sleep_2026-04-17", "duration_hours": 6.5},
            "resting_hr": [{"date": AS_OF.isoformat(), "bpm": 52.0,
                             "record_id": "g_rhr_2026-04-17"}],
            "hrv": [{"date": AS_OF.isoformat(), "rmssd_ms": 48.0,
                       "record_id": "g_hrv_2026-04-17"}],
            "training_load": [{"date": AS_OF.isoformat(), "load": 400.0,
                                "record_id": "g_load_2026-04-17"}],
            "raw_daily_row": _full_raw_row(),
        },
        "manual_readiness": {
            "submission_id": "m_ready_2026-04-17_test",
            "soreness": "moderate",
            "energy": "moderate",
            "planned_session_type": "moderate",
        },
    }
    p = tmp_path / "evidence.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def test_cli_clean_projects_recovery_and_running(tmp_path: Path):
    db = _init_db(tmp_path)
    evidence = _write_pull_payload(tmp_path)
    out = StringIO()
    with redirect_stdout(out):
        rc = cli_main([
            "clean",
            "--evidence-json", str(evidence),
            "--db-path", str(db),
        ])
    assert rc == 0
    # stdout still includes the cleaned_evidence/raw_summary envelope.
    stdout_json = json.loads(out.getvalue())
    assert "cleaned_evidence" in stdout_json
    assert "raw_summary" in stdout_json

    conn = open_connection(db)
    try:
        recovery = read_domain(
            conn, domain="recovery", since=AS_OF, until=AS_OF, user_id=USER,
        )
        running = read_domain(
            conn, domain="running", since=AS_OF, until=AS_OF, user_id=USER,
        )
        raw_count = conn.execute(
            "SELECT COUNT(*) FROM source_daily_garmin "
            "WHERE as_of_date = ? AND user_id = ?",
            (AS_OF.isoformat(), USER),
        ).fetchone()[0]
    finally:
        conn.close()

    assert len(recovery) == 1
    assert recovery[0]["resting_hr"] == 52.0
    # manual_stress_score stays NULL — it must flow through stress_manual_raw
    # (7C), never via `hai clean`.
    assert recovery[0]["manual_stress_score"] is None
    assert recovery[0]["source"] == "garmin"
    assert recovery[0]["ingest_actor"] == "garmin_csv_adapter"
    assert len(running) == 1
    assert running[0]["derivation_path"] == "garmin_daily"
    assert running[0]["session_count"] is None
    assert raw_count == 1


def test_cli_clean_then_snapshot_returns_present_recovery_and_running(tmp_path: Path):
    db = _init_db(tmp_path)
    evidence = _write_pull_payload(tmp_path)
    rc = cli_main([
        "clean",
        "--evidence-json", str(evidence),
        "--db-path", str(db),
    ])
    assert rc == 0

    conn = open_connection(db)
    try:
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 5, 1, 10, 0),
        )
    finally:
        conn.close()

    assert snap["recovery"]["missingness"] == "present"
    assert snap["running"]["missingness"] == "present"
    assert snap["recovery"]["today"]["sleep_hours"] == pytest.approx(6.5, rel=0.01)
    assert snap["recovery"]["today"]["all_day_stress"] == 30
    assert snap["recovery"]["today"]["manual_stress_score"] is None
    assert snap["running"]["today"]["total_distance_m"] == 8500.0
    # Stress is `partial:manual_stress_score` because Garmin landed but
    # no stress_manual_raw row exists yet — 7C territory.
    assert snap["stress"]["missingness"] == "partial:manual_stress_score"


def test_cli_clean_without_db_is_failsoft_and_emits_stdout(tmp_path: Path, capsys):
    """If the state DB file doesn't exist, `hai clean` must still succeed."""

    evidence = _write_pull_payload(tmp_path)
    missing_db = tmp_path / "nonexistent.db"
    rc = cli_main([
        "clean",
        "--evidence-json", str(evidence),
        "--db-path", str(missing_db),
    ])
    assert rc == 0
    captured = capsys.readouterr()
    assert "cleaned_evidence" in captured.out
    # Warning goes to stderr; stdout is untouched.
    assert "projection skipped" in captured.err


def test_cli_clean_without_raw_daily_row_is_failsoft(tmp_path: Path):
    """A pull payload without raw_daily_row (older adapters) must still
    produce stdout. Projection simply doesn't run."""

    db = _init_db(tmp_path)
    payload = {
        "as_of_date": AS_OF.isoformat(),
        "user_id": USER,
        "source": "garmin",
        "pull": {
            "sleep": {"record_id": "g_sleep_2026-04-17", "duration_hours": 6.5},
            "resting_hr": [], "hrv": [], "training_load": [],
            # no raw_daily_row
        },
        "manual_readiness": None,
    }
    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps(payload), encoding="utf-8")
    rc = cli_main([
        "clean", "--evidence-json", str(evidence), "--db-path", str(db),
    ])
    assert rc == 0
    conn = open_connection(db)
    try:
        rows = read_domain(
            conn, domain="recovery", since=AS_OF, until=AS_OF, user_id=USER,
        )
    finally:
        conn.close()
    assert rows == []  # projection was skipped


# ---------------------------------------------------------------------------
# Atomicity — mid-flight projector failure rolls the whole clean write back
# ---------------------------------------------------------------------------

def test_cli_clean_projection_is_atomic_on_middle_failure(tmp_path, monkeypatch):
    """If project_accepted_recovery_state_daily raises, neither
    source_daily_garmin nor accepted_running_state_daily should persist —
    the whole projection is one transaction. Without atomicity, a partial
    write leaves the DB in a state no JSONL reproject can repair."""

    db = _init_db(tmp_path)
    evidence = _write_pull_payload(tmp_path)

    import health_agent_infra.state.projector as projector_module

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated projector failure mid-flight")

    monkeypatch.setattr(
        projector_module, "project_accepted_recovery_state_daily", _boom,
    )
    # CLI imports the projector at call time via `from ... import ...`. We
    # need to patch the symbol the CLI will see — i.e. within the
    # `health_agent_infra.state` package too.
    import health_agent_infra.state as state_pkg
    monkeypatch.setattr(
        state_pkg, "project_accepted_recovery_state_daily", _boom,
    )

    rc = cli_main([
        "clean", "--evidence-json", str(evidence), "--db-path", str(db),
    ])
    # Fail-soft: CLI still exits 0 (stdout is the audit boundary; DB is
    # best-effort). The warning lands on stderr; we don't assert its exact
    # wording here.
    assert rc == 0

    conn = open_connection(db)
    try:
        raw_count = conn.execute(
            "SELECT COUNT(*) FROM source_daily_garmin"
        ).fetchone()[0]
        recovery_count = conn.execute(
            "SELECT COUNT(*) FROM accepted_recovery_state_daily"
        ).fetchone()[0]
        running_count = conn.execute(
            "SELECT COUNT(*) FROM accepted_running_state_daily"
        ).fetchone()[0]
    finally:
        conn.close()

    # All three tables stayed empty: the first INSERT was rolled back when
    # the middle projector raised. No half-projected state.
    assert raw_count == 0, (
        f"expected source_daily_garmin to be rolled back, got {raw_count} rows"
    )
    assert recovery_count == 0
    assert running_count == 0


def test_cli_clean_projection_recovers_on_retry_after_rollback(tmp_path, monkeypatch):
    """After the rolled-back failure above, a clean rerun (without the
    injected failure) must succeed and land all three rows."""

    db = _init_db(tmp_path)
    evidence = _write_pull_payload(tmp_path)

    import health_agent_infra.state as state_pkg
    real_projector = state_pkg.project_accepted_recovery_state_daily

    boom = {"armed": True}

    def _fail_once(*args, **kwargs):
        if boom["armed"]:
            boom["armed"] = False
            raise RuntimeError("first-run failure")
        return real_projector(*args, **kwargs)

    monkeypatch.setattr(
        state_pkg, "project_accepted_recovery_state_daily", _fail_once,
    )

    assert cli_main([
        "clean", "--evidence-json", str(evidence), "--db-path", str(db),
    ]) == 0
    assert cli_main([
        "clean", "--evidence-json", str(evidence), "--db-path", str(db),
    ]) == 0

    conn = open_connection(db)
    try:
        recovery = read_domain(
            conn, domain="recovery", since=AS_OF, until=AS_OF, user_id=USER,
        )
        running = read_domain(
            conn, domain="running", since=AS_OF, until=AS_OF, user_id=USER,
        )
        raw_count = conn.execute(
            "SELECT COUNT(*) FROM source_daily_garmin"
        ).fetchone()[0]
    finally:
        conn.close()
    assert len(recovery) == 1
    assert len(running) == 1
    # Only the successful run wrote a raw row; the first transaction was
    # rolled back before source_daily_garmin could commit.
    assert raw_count == 1


# ---------------------------------------------------------------------------
# Provenance: hai clean never populates manual_stress_score
# ---------------------------------------------------------------------------

def test_cli_clean_never_populates_manual_stress_score(tmp_path):
    """Even if a future intake path attaches manual stress to the readiness
    payload, `hai clean` must leave accepted_recovery_state_daily's
    manual_stress_score NULL. That fact must enter via stress_manual_raw
    (7C) so the raw→accepted audit chain holds."""

    db = _init_db(tmp_path)
    payload = {
        "as_of_date": AS_OF.isoformat(),
        "user_id": USER,
        "source": "garmin",
        "pull": {
            "sleep": None, "resting_hr": [], "hrv": [], "training_load": [],
            "raw_daily_row": _full_raw_row(),
        },
        # Deliberately include a stress field that a misbehaving upstream
        # might attach. cmd_clean must ignore it.
        "manual_readiness": {
            "submission_id": "m_ready_x",
            "soreness": "moderate", "energy": "moderate",
            "planned_session_type": "moderate",
            "manual_stress_score": 4,  # MUST NOT land in the accepted row
        },
    }
    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps(payload), encoding="utf-8")
    rc = cli_main([
        "clean", "--evidence-json", str(evidence), "--db-path", str(db),
    ])
    assert rc == 0

    conn = open_connection(db)
    try:
        row = conn.execute(
            "SELECT manual_stress_score, source, ingest_actor FROM "
            "accepted_recovery_state_daily WHERE as_of_date = ? AND user_id = ?",
            (AS_OF.isoformat(), USER),
        ).fetchone()
        # stress_manual_raw must stay empty — clean does not touch it.
        raw_count = conn.execute(
            "SELECT COUNT(*) FROM stress_manual_raw"
        ).fetchone()[0]
    finally:
        conn.close()

    assert row["manual_stress_score"] is None
    assert row["source"] == "garmin"
    assert row["ingest_actor"] == "garmin_csv_adapter"
    assert raw_count == 0


# ---------------------------------------------------------------------------
# Skill frontmatter sanity
# ---------------------------------------------------------------------------

def test_recovery_readiness_skill_allows_hai_state_snapshot():
    from importlib.resources import files

    skill = files("health_agent_infra").joinpath(
        "skills", "recovery-readiness", "SKILL.md"
    ).read_text(encoding="utf-8")
    # First frontmatter block contains allowed-tools.
    # Cheap parse: look at the line starting `allowed-tools:`.
    allowed_line = next(
        ln for ln in skill.splitlines() if ln.startswith("allowed-tools:")
    )
    assert "hai state snapshot" in allowed_line
    assert "hai writeback" in allowed_line
    assert "hai review" in allowed_line
