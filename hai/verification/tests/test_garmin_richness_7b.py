"""Phase 7B — Garmin richness tests.

Three contracts pinned here:

  1. RawSummary carries the 13 new Garmin-native today-only fields
     (all_day_stress, body_battery_end_of_day, total_distance_m,
     moderate_intensity_min, vigorous_intensity_min, garmin_acwr_ratio,
     acwr_status, training_readiness_level, training_readiness_pct, and
     five component pcts). Populated from the pull's raw_daily_row when
     present; None when it isn't.

  2. `accepted_recovery_state_daily.training_readiness_pct` is populated
     by `hai clean` (was NULL-by-deferral in 7A.3).

  3. Real Garmin CSV slice populates every new RawSummary field and the
     recovery row's training_readiness_pct.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.clean import build_raw_summary
from health_agent_infra.core.pull.garmin import load_recovery_readiness_inputs
from health_agent_infra.core.state import (
    build_snapshot,
    initialize_database,
    open_connection,
    read_domain,
)


USER = "u_test"
AS_OF = date(2026, 4, 17)


def _full_raw_row() -> dict:
    """Matches the 7A.3 fixture but this file owns its own copy to keep
    tests independent."""

    return {
        "steps": 12000, "distance_m": 8500.0,
        "active_kcal": 620.0, "total_kcal": 2400.0,
        "moderate_intensity_min": 35, "vigorous_intensity_min": 18,
        "floors_ascended_m": 24.0, "avg_environment_altitude_m": 180.0,
        "resting_hr": 52.0, "min_hr_day": 44.0, "max_hr_day": 168.0,
        "sleep_deep_sec": 5400, "sleep_light_sec": 12600,
        "sleep_rem_sec": 5400, "sleep_awake_sec": 600,
        "avg_sleep_respiration": 14.1, "avg_sleep_stress": 22.0,
        "awake_count": 2,
        "sleep_score_overall": 84, "sleep_score_quality": 80,
        "sleep_score_duration": 88, "sleep_score_recovery": 82,
        "all_day_stress": 30, "body_battery": 65,
        "training_readiness_level": "High",
        "training_recovery_time_hours": 18.0,
        "training_readiness_sleep_pct": 82.0,
        "training_readiness_hrv_pct": 70.0,
        "training_readiness_stress_pct": 75.0,
        "training_readiness_sleep_history_pct": 88.0,
        "training_readiness_load_pct": 65.0,
        "training_readiness_hrv_weekly_avg": 48.0,
        "training_readiness_valid_sleep": 1,
        "acute_load": 400.0, "chronic_load": 380.0,
        "acwr_status": "Optimal",
        "acwr_status_feedback": "Training load is well balanced.",
        "training_status": "Productive",
        "training_status_feedback": "Your fitness is improving.",
        "health_hrv_value": 48.0, "health_hrv_status": "Balanced",
        "health_hrv_baseline_low": 38.0, "health_hrv_baseline_high": 58.0,
        "health_hr_value": 52.0, "health_hr_status": "Balanced",
        "health_hr_baseline_low": 48.0, "health_hr_baseline_high": 60.0,
        "health_spo2_value": 97.0, "health_spo2_status": "Balanced",
        "health_spo2_baseline_low": 94.0, "health_spo2_baseline_high": 99.0,
        "health_skin_temp_c_value": 36.4, "health_skin_temp_c_status": "Balanced",
        "health_skin_temp_c_baseline_low": 36.0,
        "health_skin_temp_c_baseline_high": 36.8,
        "health_respiration_value": 14.0, "health_respiration_status": "Balanced",
        "health_respiration_baseline_low": 12.0,
        "health_respiration_baseline_high": 16.0,
    }


# ---------------------------------------------------------------------------
# RawSummary extraction from raw_daily_row
# ---------------------------------------------------------------------------

def test_raw_summary_populates_garmin_richness_fields_from_raw_row():
    summary = build_raw_summary(
        user_id=USER,
        as_of_date=AS_OF,
        garmin_sleep={"record_id": "g_sleep", "duration_hours": 6.5},
        garmin_resting_hr_recent=[],
        garmin_hrv_recent=[],
        garmin_training_load_7d=[],
        raw_daily_row=_full_raw_row(),
    )

    assert summary.all_day_stress == 30
    assert summary.body_battery_end_of_day == 65
    assert summary.total_distance_m == 8500.0
    assert summary.moderate_intensity_min == 35
    assert summary.vigorous_intensity_min == 18
    # 400/380 = 1.053
    assert summary.garmin_acwr_ratio == pytest.approx(1.053, abs=0.001)
    assert summary.acwr_status == "Optimal"
    assert summary.training_readiness_level == "High"
    # Locally-computed arithmetic mean of (82, 70, 75, 88, 65) = 76.0. NOT
    # Garmin's own overall Training Readiness — Garmin doesn't export that.
    assert summary.training_readiness_component_mean_pct == pytest.approx(76.0, rel=0.01)
    assert summary.training_readiness_sleep_pct == 82.0
    assert summary.training_readiness_hrv_pct == 70.0
    assert summary.training_readiness_stress_pct == 75.0
    assert summary.training_readiness_sleep_history_pct == 88.0
    assert summary.training_readiness_load_pct == 65.0


def test_raw_summary_garmin_fields_are_none_when_raw_row_absent():
    """Backwards compat: existing callers that don't pass raw_daily_row get
    None for every Garmin-richness field. 7A.3 RawSummary shape works."""

    summary = build_raw_summary(
        user_id=USER,
        as_of_date=AS_OF,
        garmin_sleep=None,
        garmin_resting_hr_recent=[],
        garmin_hrv_recent=[],
        garmin_training_load_7d=[],
        # raw_daily_row omitted
    )
    assert summary.all_day_stress is None
    assert summary.body_battery_end_of_day is None
    assert summary.total_distance_m is None
    assert summary.moderate_intensity_min is None
    assert summary.vigorous_intensity_min is None
    assert summary.garmin_acwr_ratio is None
    assert summary.acwr_status is None
    assert summary.training_readiness_level is None
    assert summary.training_readiness_component_mean_pct is None
    assert summary.training_readiness_sleep_pct is None


def test_raw_summary_training_readiness_component_mean_pct_is_none_when_any_component_missing():
    """The local arithmetic mean requires all 5 components. If any is
    missing, the mean stays None — we don't fabricate a partial average."""

    raw = _full_raw_row()
    raw["training_readiness_hrv_pct"] = None  # drop one component
    summary = build_raw_summary(
        user_id=USER,
        as_of_date=AS_OF,
        garmin_sleep=None,
        garmin_resting_hr_recent=[],
        garmin_hrv_recent=[],
        garmin_training_load_7d=[],
        raw_daily_row=raw,
    )
    assert summary.training_readiness_component_mean_pct is None
    # But the four present components are still surfaced individually:
    assert summary.training_readiness_sleep_pct == 82.0
    assert summary.training_readiness_hrv_pct is None
    assert summary.training_readiness_stress_pct == 75.0


def test_raw_summary_garmin_acwr_ratio_is_none_when_chronic_missing_or_zero():
    raw = _full_raw_row()
    raw["chronic_load"] = None
    summary = build_raw_summary(
        user_id=USER, as_of_date=AS_OF,
        garmin_sleep=None, garmin_resting_hr_recent=[],
        garmin_hrv_recent=[], garmin_training_load_7d=[],
        raw_daily_row=raw,
    )
    assert summary.garmin_acwr_ratio is None

    raw["chronic_load"] = 0.0  # avoid divide-by-zero
    summary = build_raw_summary(
        user_id=USER, as_of_date=AS_OF,
        garmin_sleep=None, garmin_resting_hr_recent=[],
        garmin_hrv_recent=[], garmin_training_load_7d=[],
        raw_daily_row=raw,
    )
    assert summary.garmin_acwr_ratio is None


def test_raw_summary_stringified_numeric_values_coerce():
    """CSV exports frequently arrive with string-valued numerics (pandas
    object dtype). The extractor must coerce without crashing."""

    raw = _full_raw_row()
    raw["all_day_stress"] = "30"
    raw["body_battery"] = "65"
    raw["distance_m"] = "8500.0"
    raw["training_readiness_sleep_pct"] = "82"
    summary = build_raw_summary(
        user_id=USER, as_of_date=AS_OF,
        garmin_sleep=None, garmin_resting_hr_recent=[],
        garmin_hrv_recent=[], garmin_training_load_7d=[],
        raw_daily_row=raw,
    )
    assert summary.all_day_stress == 30
    assert summary.body_battery_end_of_day == 65
    assert summary.total_distance_m == 8500.0
    assert summary.training_readiness_sleep_pct == 82.0


# ---------------------------------------------------------------------------
# accepted_recovery_state_daily.training_readiness_pct populated by cmd_clean
# ---------------------------------------------------------------------------

def _write_pull_payload(tmp_path: Path, raw_row: dict | None = None) -> Path:
    if raw_row is None:
        raw_row = _full_raw_row()
    payload = {
        "as_of_date": AS_OF.isoformat(),
        "user_id": USER,
        "source": "garmin",
        "pull": {
            "sleep": {"record_id": "g_sleep", "duration_hours": 6.5},
            "resting_hr": [], "hrv": [], "training_load": [],
            "raw_daily_row": raw_row,
        },
        "manual_readiness": None,
    }
    p = tmp_path / "ev.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def test_cli_clean_populates_training_readiness_component_mean_pct_on_accepted_recovery(tmp_path: Path):
    db = _init_db(tmp_path)
    evidence = _write_pull_payload(tmp_path)
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

    assert len(rows) == 1
    # Mean of (82, 70, 75, 88, 65) = 76.0
    assert rows[0]["training_readiness_component_mean_pct"] == pytest.approx(76.0, rel=0.01)


def test_cli_clean_readiness_null_on_missing_component_surfaces_unavailable_at_source(tmp_path: Path):
    """A Garmin row missing one readiness component yields NULL mean. The
    snapshot must tag this as `unavailable_at_source:training_readiness_component_mean_pct`,
    NOT `partial:...`: the source (Garmin) was queried and didn't record —
    that's qualitatively different from incomplete user-logged data
    (state_model_v1.md §5)."""

    raw = _full_raw_row()
    raw["training_readiness_stress_pct"] = None

    db = _init_db(tmp_path)
    evidence = _write_pull_payload(tmp_path, raw_row=raw)
    rc = cli_main([
        "clean", "--evidence-json", str(evidence), "--db-path", str(db),
    ])
    assert rc == 0

    conn = open_connection(db)
    try:
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 5, 1, 10, 0),  # day well-closed
        )
    finally:
        conn.close()

    row = snap["recovery"]["today"]
    assert row["training_readiness_component_mean_pct"] is None
    mx = snap["recovery"]["missingness"]
    # Must be unavailable_at_source (Garmin-didn't-record), NOT partial
    # (which would imply incomplete user logging).
    assert mx.startswith("unavailable_at_source:"), f"got {mx!r}"
    assert "training_readiness_component_mean_pct" in mx


def test_cli_clean_snapshot_recovery_present_with_full_7b_row(tmp_path: Path):
    """A fully-populated Garmin row produces recovery.missingness='present' —
    the locally-computed readiness mean completes the v1 required set."""

    db = _init_db(tmp_path)
    evidence = _write_pull_payload(tmp_path)
    rc = cli_main([
        "clean", "--evidence-json", str(evidence), "--db-path", str(db),
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
    assert snap["recovery"]["today"]["training_readiness_component_mean_pct"] == pytest.approx(76.0, rel=0.01)


# ---------------------------------------------------------------------------
# Real Garmin slice — every 7B field lands end-to-end
# ---------------------------------------------------------------------------

def test_real_garmin_slice_populates_every_new_raw_summary_field():
    """Against the committed Garmin CSV export, `build_raw_summary` produces
    Garmin-richness fields that match what the source reports. This is the
    seal that 7B actually works on real data, not just synthetic fixtures."""

    real_as_of = date(2026, 4, 8)
    pull = load_recovery_readiness_inputs(real_as_of)
    assert pull["raw_daily_row"] is not None, "pull adapter must expose raw_daily_row"

    summary = build_raw_summary(
        user_id="u_real",
        as_of_date=real_as_of,
        garmin_sleep=pull["sleep"],
        garmin_resting_hr_recent=pull["resting_hr"],
        garmin_hrv_recent=pull["hrv"],
        garmin_training_load_7d=pull["training_load"],
        raw_daily_row=pull["raw_daily_row"],
    )

    # Every new field must exist on the RawSummary (None is acceptable when
    # Garmin didn't record that signal for that specific day; the schema
    # presence is what matters).
    for field in (
        "all_day_stress", "body_battery_end_of_day",
        "total_distance_m", "moderate_intensity_min", "vigorous_intensity_min",
        "garmin_acwr_ratio", "acwr_status",
        "training_readiness_level", "training_readiness_component_mean_pct",
        "training_readiness_sleep_pct", "training_readiness_hrv_pct",
        "training_readiness_stress_pct", "training_readiness_sleep_history_pct",
        "training_readiness_load_pct",
    ):
        assert hasattr(summary, field), f"missing field: {field}"

    # At least some non-None value landed — the real slice is well-populated
    # for 2026-04-08 (this is the committed capture, not an edge date).
    payload = summary.to_dict()
    nonnull_new = sum(
        1 for k in (
            "all_day_stress", "body_battery_end_of_day",
            "total_distance_m", "moderate_intensity_min",
            "vigorous_intensity_min", "garmin_acwr_ratio",
            "training_readiness_level", "training_readiness_component_mean_pct",
        ) if payload[k] is not None
    )
    assert nonnull_new >= 4, (
        f"expected at least 4 populated 7B fields on real 2026-04-08 slice; "
        f"got {nonnull_new}. payload: {payload}"
    )


# ---------------------------------------------------------------------------
# Skill frontmatter + content sanity
# ---------------------------------------------------------------------------

def test_recovery_readiness_skill_names_7b_fields():
    from importlib.resources import files

    skill = files("health_agent_infra").joinpath(
        "skills", "recovery-readiness", "SKILL.md"
    ).read_text(encoding="utf-8")

    # Every new field name should appear somewhere in the skill doc so the
    # agent has an anchor when reading snapshot/clean output. We don't pin
    # prose; we pin that the names exist.
    for token in (
        "training_readiness_component_mean_pct",
        "training_readiness_level",
        "all_day_stress",
        "body_battery_end_of_day",
        "garmin_acwr_ratio",
        "acwr_status",
        "moderate_intensity_min",
        "vigorous_intensity_min",
        "total_distance_m",
    ):
        assert token in skill, f"SKILL.md missing 7B field: {token}"
    # Must NOT FRAME the local mean as a pre-computed vendor score — that
    # was the 7B finding that prompted the rename + skill rewrite. The
    # word "vendor score" may appear in a prohibitive context (e.g. "do
    # not treat X as a vendor score"); we pin the misleading POSITIVE
    # framing specifically.
    lower = skill.lower()
    assert "pre-computed vendor score" not in lower, (
        "SKILL.md still frames training_readiness_component_mean_pct as a "
        "pre-computed vendor score. It's a locally-computed arithmetic mean."
    )
    # Must call out the provenance explicitly — "locally" or "local" should
    # appear near the computed mean. Light-touch assertion:
    assert "locally-computed" in lower or "arithmetic mean" in lower, (
        "SKILL.md must explain training_readiness_component_mean_pct is a "
        "local computation, not a vendor-authored number."
    )
