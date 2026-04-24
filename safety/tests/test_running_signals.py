"""Tests for ``derive_running_signals`` (Phase 2 step 3).

The derivation function is the single hop between the snapshot's raw inputs
(running history rows + raw_summary + recovery's classified_state) and the
``running_signals`` dict that ``classify_running_state`` consumes. These
tests pin the aggregation contract so a future change to weekly-mileage
window length or hard-session threshold surfaces as a contract drift.
"""

from __future__ import annotations

from health_agent_infra.domains.running.signals import derive_running_signals


def _row(distance_m: float | None, vigorous_min: int | None) -> dict:
    return {
        "total_distance_m": distance_m,
        "vigorous_intensity_min": vigorous_min,
    }


def _seven_uniform_history(distance_m: float = 5_000.0, vig: int = 0) -> list[dict]:
    return [_row(distance_m, vig) for _ in range(7)]


# ---------------------------------------------------------------------------
# Output shape
# ---------------------------------------------------------------------------

def test_signals_dict_keys_match_classifier_input_contract():
    sig = derive_running_signals(
        {}, running_today=None, running_history=[], recovery_classified=None,
    )
    assert set(sig.keys()) == {
        "weekly_mileage_m",
        "weekly_mileage_baseline_m",
        "recent_hard_session_count_7d",
        "acwr_ratio",
        "training_readiness_pct",
        "sleep_debt_band",
        "resting_hr_band",
        # v0.1.4 structural signals from running_activity.
        "z4_plus_seconds_today",
        "z4_plus_seconds_7d",
        "last_hard_session_days_ago",
        "today_interval_summary",
        "activity_count_14d",
    }


# ---------------------------------------------------------------------------
# Pass-through fields from raw_summary + recovery_classified
# ---------------------------------------------------------------------------

def test_acwr_ratio_passes_through_from_raw_summary():
    sig = derive_running_signals(
        {"garmin_acwr_ratio": 1.42},
        running_today=None, running_history=[], recovery_classified=None,
    )
    assert sig["acwr_ratio"] == 1.42


def test_acwr_ratio_is_none_when_raw_summary_lacks_it():
    sig = derive_running_signals(
        {}, running_today=None, running_history=[], recovery_classified=None,
    )
    assert sig["acwr_ratio"] is None


def test_training_readiness_pct_uses_component_mean():
    sig = derive_running_signals(
        {"training_readiness_component_mean_pct": 65.0},
        running_today=None, running_history=[], recovery_classified=None,
    )
    assert sig["training_readiness_pct"] == 65.0


def test_recovery_classified_passes_through_when_present():
    sig = derive_running_signals(
        {},
        running_today=None, running_history=[],
        recovery_classified={
            "sleep_debt_band": "moderate",
            "resting_hr_band": "above",
        },
    )
    assert sig["sleep_debt_band"] == "moderate"
    assert sig["resting_hr_band"] == "above"


def test_recovery_classified_absent_means_none_for_cross_domain_bands():
    sig = derive_running_signals(
        {}, running_today=None, running_history=[], recovery_classified=None,
    )
    assert sig["sleep_debt_band"] is None
    assert sig["resting_hr_band"] is None


# ---------------------------------------------------------------------------
# Weekly mileage aggregation (last 7 days = today + 6 most recent history)
# ---------------------------------------------------------------------------

def test_weekly_mileage_sums_today_plus_six_most_recent_history_days():
    today = _row(8_000.0, 0)
    # History is oldest -> newest. The function should walk it newest-first
    # for the 7-day window, so the most recent 6 history days count.
    history = [_row(1_000.0, 0)] * 5 + [_row(5_000.0, 0)] * 6
    sig = derive_running_signals(
        {}, running_today=today, running_history=history,
    )
    assert sig["weekly_mileage_m"] == 8_000.0 + 6 * 5_000.0


def test_weekly_mileage_handles_missing_today():
    history = [_row(5_000.0, 0)] * 7
    sig = derive_running_signals(
        {}, running_today=None, running_history=history,
    )
    # The 7-day window is provenance-independent: with no today and 7
    # history rows, all 7 rows fill the window.
    assert sig["weekly_mileage_m"] == 7 * 5_000.0


def test_weekly_mileage_handles_null_distance_in_some_days():
    history = [_row(None, 0), _row(5_000.0, 0), _row(None, 0)]
    sig = derive_running_signals(
        {}, running_today=_row(3_000.0, 0), running_history=history,
    )
    # Today (3000) + the two non-null history rows (5000) = 8000.
    assert sig["weekly_mileage_m"] == 8_000.0


def test_weekly_mileage_none_when_no_distance_data_anywhere():
    sig = derive_running_signals(
        {}, running_today=None, running_history=[],
    )
    assert sig["weekly_mileage_m"] is None


# ---------------------------------------------------------------------------
# Weekly mileage baseline (28d preferred, scaled fallback ≥7d, None <7d)
# ---------------------------------------------------------------------------

def test_baseline_uses_full_28_day_window_when_available():
    history = [_row(7_000.0, 0)] * 27
    sig = derive_running_signals(
        {}, running_today=_row(7_000.0, 0), running_history=history,
    )
    # 28 days * 7000 / 4 weeks = 49_000 baseline.
    assert sig["weekly_mileage_baseline_m"] == 49_000.0


def test_baseline_scales_when_fewer_than_28_days_but_at_least_7():
    history = _seven_uniform_history(distance_m=4_000.0)  # 7 history rows
    today = _row(4_000.0, 0)
    sig = derive_running_signals(
        {}, running_today=today, running_history=history,
    )
    # 8 populated days; mean = 4000; scaled to a week = 28_000.
    assert sig["weekly_mileage_baseline_m"] == 28_000.0


def test_baseline_none_when_fewer_than_seven_days_of_data():
    sig = derive_running_signals(
        {}, running_today=_row(5_000.0, 0),
        running_history=[_row(5_000.0, 0)] * 5,  # 6 days total
    )
    assert sig["weekly_mileage_baseline_m"] is None


def test_baseline_ignores_null_distance_days():
    # 27 valid + a few nulls = still scaled-fallback path (not full 28).
    history = [_row(None, 0)] * 5 + [_row(7_000.0, 0)] * 26
    sig = derive_running_signals(
        {}, running_today=_row(7_000.0, 0), running_history=history,
    )
    # 27 valid rows in the trailing-28 window: scale path → 7000 * 7 = 49000.
    assert sig["weekly_mileage_baseline_m"] == 49_000.0


# ---------------------------------------------------------------------------
# Hard-session counting (>= 30 vigorous minutes per day, 7-day window)
# ---------------------------------------------------------------------------

def test_hard_session_count_thresholds_at_30_vigorous_minutes():
    today = _row(8_000.0, 35)              # hard
    history = [_row(5_000.0, 29)] * 6      # under threshold
    sig = derive_running_signals(
        {}, running_today=today, running_history=history,
    )
    assert sig["recent_hard_session_count_7d"] == 1


def test_hard_session_count_includes_exactly_30_minute_days():
    today = _row(5_000.0, 30)
    history = [_row(5_000.0, 30)] * 6
    sig = derive_running_signals(
        {}, running_today=today, running_history=history,
    )
    assert sig["recent_hard_session_count_7d"] == 7


def test_hard_session_count_window_is_seven_days():
    today = _row(5_000.0, 60)              # day 0
    history = [_row(5_000.0, 60)] * 9      # days 1..9 — only 6 of these in window
    sig = derive_running_signals(
        {}, running_today=today, running_history=history,
    )
    # Today + 6 most recent history days = 7 hard days in window.
    assert sig["recent_hard_session_count_7d"] == 7


def test_hard_session_count_zero_when_no_day_clears_threshold():
    sig = derive_running_signals(
        {},
        running_today=_row(5_000.0, 5),
        running_history=[_row(5_000.0, 0)] * 6,
    )
    assert sig["recent_hard_session_count_7d"] == 0


def test_hard_session_count_none_when_no_day_has_vigorous_field_populated():
    """Distinguish "0 hard sessions" (we have data, none cleared threshold)
    from "no data at all" (classifier should mark uncertainty)."""

    sig = derive_running_signals(
        {},
        running_today=_row(5_000.0, None),
        running_history=[_row(5_000.0, None)] * 6,
    )
    assert sig["recent_hard_session_count_7d"] is None


# ---------------------------------------------------------------------------
# Compositional sanity: derive → classify → policy still works end-to-end
# ---------------------------------------------------------------------------

def test_derived_signals_round_trip_through_classifier_and_policy():
    """Final guard: every signal derived here must be a valid input shape
    for ``classify_running_state``, and the resulting state must be a
    valid input for ``evaluate_running_policy``. Catches a future
    rename in classify.py that the field-set test alone might miss."""

    from health_agent_infra.domains.running.classify import classify_running_state
    from health_agent_infra.domains.running.policy import evaluate_running_policy

    history = [_row(7_000.0, 30)] * 27
    sig = derive_running_signals(
        {"garmin_acwr_ratio": 1.1, "training_readiness_component_mean_pct": 75.0},
        running_today=_row(7_000.0, 30), running_history=history,
        recovery_classified={"sleep_debt_band": "none", "resting_hr_band": "at"},
    )
    classified = classify_running_state(sig)
    policy = evaluate_running_policy(classified, sig)

    assert classified.coverage_band == "full"
    assert policy.forced_action is None


# ---------------------------------------------------------------------------
# v0.1.4 structural signals from running_activity
# ---------------------------------------------------------------------------

def _activity(
    *,
    as_of: str = "2026-04-23",
    activity_id: str = "i1",
    hr_zone_times_s: list[int] | None = None,
    interval_summary: list[str] | None = None,
) -> dict:
    return {
        "activity_id": activity_id,
        "as_of_date": as_of,
        "hr_zone_times_s": hr_zone_times_s,
        "interval_summary": interval_summary,
    }


def test_z4_plus_seconds_today_sums_zones_4_through_7():
    # Z4=282, Z5=0, Z6=0, Z7=0 → 282s
    a = _activity(hr_zone_times_s=[1312, 254, 550, 282, 0, 0, 0])
    sig = derive_running_signals(
        {}, running_today=None, running_history=[],
        activities_today=[a], activities_history=[],
    )
    assert sig["z4_plus_seconds_today"] == 282


def test_z4_plus_seconds_today_sums_across_multiple_activities():
    a = _activity(activity_id="i_a", hr_zone_times_s=[0, 0, 0, 100, 50, 0, 0])
    b = _activity(activity_id="i_b", hr_zone_times_s=[0, 0, 0, 200, 0, 0, 0])
    sig = derive_running_signals(
        {}, running_today=None, running_history=[],
        activities_today=[a, b], activities_history=[],
    )
    assert sig["z4_plus_seconds_today"] == 350


def test_z4_plus_seconds_today_none_when_no_zone_data():
    sig = derive_running_signals(
        {}, running_today=None, running_history=[],
        activities_today=[_activity(hr_zone_times_s=None)],
        activities_history=[],
    )
    assert sig["z4_plus_seconds_today"] is None


def test_last_hard_session_days_ago_is_zero_when_today_is_hard():
    # Z4+ = 700s > 600s hard-session threshold
    a = _activity(as_of="2026-04-23", hr_zone_times_s=[0, 0, 0, 700, 0, 0, 0])
    sig = derive_running_signals(
        {}, running_today=None, running_history=[],
        activities_today=[a], activities_history=[],
    )
    assert sig["last_hard_session_days_ago"] == 0


def test_last_hard_session_days_ago_counts_history():
    today_a = _activity(as_of="2026-04-23", hr_zone_times_s=[0, 100, 100, 0, 0, 0, 0])  # not hard
    hist_a = _activity(as_of="2026-04-20", activity_id="i_old",
                       hr_zone_times_s=[0, 0, 0, 1200, 0, 0, 0])  # hard, 3 days ago
    sig = derive_running_signals(
        {}, running_today=None, running_history=[],
        activities_today=[today_a], activities_history=[hist_a],
    )
    assert sig["last_hard_session_days_ago"] == 3


def test_last_hard_session_days_ago_none_when_no_hard_session_in_window():
    today_a = _activity(as_of="2026-04-23",
                        hr_zone_times_s=[0, 200, 300, 100, 0, 0, 0])  # Z4+=100 <600
    sig = derive_running_signals(
        {}, running_today=None, running_history=[],
        activities_today=[today_a], activities_history=[],
    )
    assert sig["last_hard_session_days_ago"] is None


def test_last_hard_session_days_ago_anchors_to_as_of_date_not_latest_activity():
    """Codex r2 regression guard: when there is no activity today, the
    function previously anchored the gap to the first historical activity
    (→ yesterday's hard session = 0 days ago, off-by-one). Passing
    ``as_of_date`` anchors correctly: yesterday's hard session = 1 day."""

    yesterday = _activity(
        as_of="2026-04-23",
        hr_zone_times_s=[0, 0, 0, 1200, 0, 0, 0],  # hard
    )
    sig = derive_running_signals(
        {}, running_today=None, running_history=[],
        activities_today=[],  # NO activity today
        activities_history=[yesterday],
        as_of_date="2026-04-24",  # plan date
    )
    assert sig["last_hard_session_days_ago"] == 1


def test_last_hard_session_days_ago_three_days_ago_no_activity_today():
    """Same shape but a larger gap. No activity today; hard session three
    days ago; plan date is today. Gap must be 3."""

    three_days_ago = _activity(
        as_of="2026-04-21",
        hr_zone_times_s=[0, 0, 0, 800, 0, 0, 0],  # hard
    )
    sig = derive_running_signals(
        {}, running_today=None, running_history=[],
        activities_today=[],
        activities_history=[three_days_ago],
        as_of_date="2026-04-24",
    )
    assert sig["last_hard_session_days_ago"] == 3


def test_last_hard_session_days_ago_falls_back_when_as_of_date_absent():
    """Backwards compatibility: callers that don't pass as_of_date still
    get the legacy anchor behaviour (gap from first-seen activity).
    Existing tests rely on this path; no silent change."""

    today_a = _activity(as_of="2026-04-23", hr_zone_times_s=[0, 100, 100, 0, 0, 0, 0])
    hist_a = _activity(as_of="2026-04-20", activity_id="i_old",
                       hr_zone_times_s=[0, 0, 0, 1200, 0, 0, 0])
    sig = derive_running_signals(
        {}, running_today=None, running_history=[],
        activities_today=[today_a], activities_history=[hist_a],
        # no as_of_date passed
    )
    # Legacy behaviour: today_iso = today_a.as_of_date = 2026-04-23 → gap = 3
    assert sig["last_hard_session_days_ago"] == 3


def test_today_interval_summary_is_first_non_empty():
    a = _activity(interval_summary=None)
    b = _activity(activity_id="i_b", interval_summary=["4x 9m29s 156bpm", "1x 2m7s 146bpm"])
    sig = derive_running_signals(
        {}, running_today=None, running_history=[],
        activities_today=[a, b], activities_history=[],
    )
    assert sig["today_interval_summary"] == ["4x 9m29s 156bpm", "1x 2m7s 146bpm"]


def test_today_interval_summary_none_when_no_activities():
    sig = derive_running_signals(
        {}, running_today=None, running_history=[],
        activities_today=[], activities_history=[],
    )
    assert sig["today_interval_summary"] is None


def test_activity_signals_backwards_compatible_without_kwargs():
    """Skipping the activity kwargs must still work (existing callers)."""

    sig = derive_running_signals(
        {"garmin_acwr_ratio": 1.0},
        running_today=None, running_history=[], recovery_classified=None,
    )
    assert sig["z4_plus_seconds_today"] is None
    assert sig["z4_plus_seconds_7d"] is None
    assert sig["last_hard_session_days_ago"] is None
    assert sig["today_interval_summary"] is None
    assert sig["activity_count_14d"] == 0


def test_activity_count_14d_counts_today_plus_history():
    sig = derive_running_signals(
        {}, running_today=None, running_history=[],
        activities_today=[_activity(activity_id="t1"), _activity(activity_id="t2")],
        activities_history=[
            _activity(activity_id="h1"),
            _activity(activity_id="h2"),
            _activity(activity_id="h3"),
        ],
    )
    assert sig["activity_count_14d"] == 5


def test_activity_count_relaxation_flips_coverage_from_insufficient(db_free=True):
    """Integration: five history activities + today's distance should lift
    coverage off `insufficient`, even when the 28-day rollup baseline is
    sparse. Mirrors the 2026-04-24 live-data scenario (6 intervals.icu
    activities across 14 days, no activity today)."""

    from health_agent_infra.domains.running.classify import classify_running_state

    history_rows = [_row(8_000.0, 5)] * 4  # 4 rollup rows, below 7-day baseline
    sig = derive_running_signals(
        {"garmin_acwr_ratio": 1.1},
        running_today=_row(5_000.0, 5),
        running_history=history_rows,
        recovery_classified={"sleep_debt_band": "none", "resting_hr_band": "at"},
        activities_today=[],
        activities_history=[_activity(activity_id=f"h{i}") for i in range(5)],
    )
    classified = classify_running_state(sig)
    # With 5 activities in the window, coverage is no longer `insufficient`.
    assert classified.coverage_band != "insufficient"
