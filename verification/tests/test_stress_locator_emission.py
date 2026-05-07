"""W-PROV-2 stress-domain locator emission.

PLAN §2.A acceptance #2 + #4. Asserts the hybrid emission contract for
stress (multi-day sustained-stress rule mirrors recovery R6 / sleep
chronic-deprivation):

- Always-emit baseline: row-level locator on today's
  ``accepted_stress_state_daily``.
- Spike-emit additional: sustained-stress firing appends column-level
  locators citing ``garmin_all_day_stress`` per consecutive day in
  the trailing run.
- Legacy 4-arg signature stable.
"""

from __future__ import annotations

from health_agent_infra.core.provenance.locator import validate_locator
from health_agent_infra.domains.stress.classify import (
    ClassifiedStressState,
)
from health_agent_infra.domains.stress.policy import (
    evaluate_stress_policy,
)


def _classified_stress_full() -> ClassifiedStressState:
    return ClassifiedStressState(
        garmin_stress_band="moderate",
        manual_stress_band="moderate",
        body_battery_trend_band="stable",
        coverage_band="full",
        stress_state="balanced",
        stress_score=0.6,
        body_battery_delta=5,
        uncertainty=tuple(),
    )


def _signals_no_run() -> dict:
    return {"stress_history_garmin_last_7": [40, 35, 45, 50, 55, 50, 45]}


def _signals_sustained_run(days: int = 5) -> dict:
    # Trailing `days` at >=60 (default threshold), preceded by lower
    # values so the rule sees exactly that consecutive run length.
    history = [30] * (7 - days) + [70] * days
    return {"stress_history_garmin_last_7": history}


def _versions_for_window(end_iso: str, n: int = 7) -> dict[str, str]:
    from datetime import date, timedelta
    end = date.fromisoformat(end_iso)
    return {
        (end - timedelta(days=offset)).isoformat():
            f"{(end - timedelta(days=offset)).isoformat()}T18:00:00Z"
        for offset in range(n)
    }


# ---------------------------------------------------------------------------
# Legacy: no locator args → no locators
# ---------------------------------------------------------------------------


def test_legacy_signature_emits_no_locators() -> None:
    result = evaluate_stress_policy(
        _classified_stress_full(),
        _signals_no_run(),
    )
    assert result.evidence_locators is None


# ---------------------------------------------------------------------------
# Always-emit baseline
# ---------------------------------------------------------------------------


def test_always_emit_stress_row_locator_on_normal_path() -> None:
    versions = _versions_for_window("2026-05-07")
    result = evaluate_stress_policy(
        _classified_stress_full(),
        _signals_no_run(),
        for_date_iso="2026-05-07",
        user_id="u_local_1",
        stress_state_versions=versions,
    )
    assert result.forced_action is None
    assert result.evidence_locators is not None
    assert len(result.evidence_locators) == 1
    loc = result.evidence_locators[0]
    assert loc["table"] == "accepted_stress_state_daily"
    assert loc["pk"] == {"as_of_date": "2026-05-07", "user_id": "u_local_1"}
    assert "column" not in loc
    validate_locator(loc)


# ---------------------------------------------------------------------------
# Spike-emit additional
# ---------------------------------------------------------------------------


def test_sustained_stress_emits_today_plus_per_run_day_columns() -> None:
    versions = _versions_for_window("2026-05-07")
    result = evaluate_stress_policy(
        _classified_stress_full(),
        _signals_sustained_run(days=5),
        for_date_iso="2026-05-07",
        user_id="u_local_1",
        stress_state_versions=versions,
    )
    assert result.forced_action == "escalate_for_user_review"
    assert result.forced_action_detail is not None
    assert (
        result.forced_action_detail["reason_token"]
        == "sustained_very_high_stress"
    )
    assert result.forced_action_detail["consecutive_days"] == 5
    assert result.evidence_locators is not None
    # 1 row-level today + 5 column-level per run day
    assert len(result.evidence_locators) == 6
    today_loc = result.evidence_locators[0]
    assert "column" not in today_loc
    spike_locators = result.evidence_locators[1:]
    assert all(
        loc["column"] == "garmin_all_day_stress"
        and loc["table"] == "accepted_stress_state_daily"
        for loc in spike_locators
    )
    spike_dates = {loc["pk"]["as_of_date"] for loc in spike_locators}
    assert "2026-05-07" in spike_dates
    assert "2026-05-03" in spike_dates  # 4 days back (5-day run)
    for loc in result.evidence_locators:
        validate_locator(loc)


def test_sustained_stress_skips_days_missing_from_version_map() -> None:
    versions = _versions_for_window("2026-05-07")
    versions.pop("2026-05-04")
    result = evaluate_stress_policy(
        _classified_stress_full(),
        _signals_sustained_run(days=5),
        for_date_iso="2026-05-07",
        user_id="u_local_1",
        stress_state_versions=versions,
    )
    assert result.evidence_locators is not None
    # 1 today + 4 remaining run days = 5
    assert len(result.evidence_locators) == 5
    spike_dates = {
        loc["pk"]["as_of_date"]
        for loc in result.evidence_locators[1:]
    }
    assert "2026-05-04" not in spike_dates
