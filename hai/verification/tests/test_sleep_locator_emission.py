"""W-PROV-2 sleep-domain locator emission.

PLAN §2.A acceptance #2 + #4. Asserts the hybrid emission contract for
sleep:

- Always-emit baseline: row-level locator on today's
  ``accepted_sleep_state_daily`` when identity + version map are
  passed.
- Spike-emit additional: chronic-deprivation firing appends
  column-level locators citing ``sleep_hours`` for each night in
  the trailing window present in the version map (mirrors recovery
  R6's ``_r6_spike_locators`` shape).
- Legacy 3-arg signature stable.
"""

from __future__ import annotations

from health_agent_infra.core.provenance.locator import validate_locator
from health_agent_infra.domains.sleep.classify import (
    ClassifiedSleepState,
)
from health_agent_infra.domains.sleep.policy import (
    evaluate_sleep_policy,
)


def _classified_sleep_full() -> ClassifiedSleepState:
    return ClassifiedSleepState(
        sleep_debt_band="none",
        sleep_quality_band="adequate",
        sleep_timing_consistency_band="consistent",
        sleep_efficiency_band="adequate",
        coverage_band="full",
        sleep_status="recovered",
        sleep_score=0.7,
        sleep_efficiency_pct=92.0,
        uncertainty=tuple(),
    )


def _signals_no_deprivation() -> dict:
    return {"sleep_history_hours_last_7": [8.0, 7.5, 8.2, 7.8, 8.0, 7.6, 8.1]}


def _signals_chronic_deprivation() -> dict:
    # 7 nights, all under typical 7h threshold
    return {"sleep_history_hours_last_7": [5.0, 4.5, 5.2, 4.8, 5.0, 4.6, 5.1]}


def _versions_for_window(end_iso: str, n: int = 7) -> dict[str, str]:
    from datetime import date, timedelta
    end = date.fromisoformat(end_iso)
    return {
        (end - timedelta(days=offset)).isoformat():
            f"{(end - timedelta(days=offset)).isoformat()}T07:00:00Z"
        for offset in range(n)
    }


# ---------------------------------------------------------------------------
# Legacy signature: no locator args → evidence_locators is None
# ---------------------------------------------------------------------------


def test_legacy_signature_emits_no_locators() -> None:
    result = evaluate_sleep_policy(
        _classified_sleep_full(),
        _signals_no_deprivation(),
    )
    assert result.evidence_locators is None


# ---------------------------------------------------------------------------
# Always-emit baseline: row-level locator on today's sleep row
# ---------------------------------------------------------------------------


def test_always_emit_sleep_row_locator_on_normal_path() -> None:
    versions = _versions_for_window("2026-05-07")
    result = evaluate_sleep_policy(
        _classified_sleep_full(),
        _signals_no_deprivation(),
        for_date_iso="2026-05-07",
        user_id="u_local_1",
        sleep_state_versions=versions,
    )
    assert result.forced_action is None
    assert result.evidence_locators is not None
    assert len(result.evidence_locators) == 1
    loc = result.evidence_locators[0]
    assert loc["table"] == "accepted_sleep_state_daily"
    assert loc["pk"] == {"as_of_date": "2026-05-07", "user_id": "u_local_1"}
    assert "column" not in loc
    validate_locator(loc)


# ---------------------------------------------------------------------------
# Spike-emit additional: column-level sleep_hours locators per window night
# ---------------------------------------------------------------------------


def test_chronic_deprivation_emits_today_row_plus_per_night_columns() -> None:
    versions = _versions_for_window("2026-05-07", n=7)
    result = evaluate_sleep_policy(
        _classified_sleep_full(),
        _signals_chronic_deprivation(),
        for_date_iso="2026-05-07",
        user_id="u_local_1",
        sleep_state_versions=versions,
    )
    assert result.forced_action == "sleep_debt_repayment_day"
    assert result.forced_action_detail is not None
    assert (
        result.forced_action_detail["reason_token"]
        == "chronic_deprivation_detected"
    )
    assert result.evidence_locators is not None
    # 1 row-level (today) + 7 column-level (one per window night)
    assert len(result.evidence_locators) == 8

    # First locator is the always-emit row-level today locator.
    today_loc = result.evidence_locators[0]
    assert today_loc["table"] == "accepted_sleep_state_daily"
    assert today_loc["pk"]["as_of_date"] == "2026-05-07"
    assert "column" not in today_loc

    # The remaining 7 are column-level sleep_hours for each window night.
    spike_locators = result.evidence_locators[1:]
    assert all(
        loc["column"] == "sleep_hours"
        and loc["table"] == "accepted_sleep_state_daily"
        for loc in spike_locators
    )
    spike_dates = {loc["pk"]["as_of_date"] for loc in spike_locators}
    assert "2026-05-07" in spike_dates  # today included in spike window
    assert "2026-05-01" in spike_dates  # 6 days back

    for loc in result.evidence_locators:
        validate_locator(loc)


def test_chronic_deprivation_skips_nights_missing_from_version_map() -> None:
    # Drop the middle 3 nights from the map; locator emission silently
    # skips them (mirrors _r6_spike_locators safe-default).
    versions = _versions_for_window("2026-05-07", n=7)
    for missing in ("2026-05-04", "2026-05-03", "2026-05-02"):
        versions.pop(missing)
    result = evaluate_sleep_policy(
        _classified_sleep_full(),
        _signals_chronic_deprivation(),
        for_date_iso="2026-05-07",
        user_id="u_local_1",
        sleep_state_versions=versions,
    )
    assert result.evidence_locators is not None
    # 1 today (still present) + 4 remaining nights = 5
    assert len(result.evidence_locators) == 5
    spike_dates = {
        loc["pk"]["as_of_date"]
        for loc in result.evidence_locators[1:]
    }
    assert spike_dates.isdisjoint({"2026-05-04", "2026-05-03", "2026-05-02"})
