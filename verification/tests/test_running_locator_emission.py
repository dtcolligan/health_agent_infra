"""W-PROV-2 running-domain locator emission.

PLAN §2.A acceptance #2 + #4. Asserts the hybrid emission contract for
running:

- Always-emit baseline: when ``for_date_iso`` / ``user_id`` /
  ``running_today_row_version`` are passed, ``evidence_locators``
  carries ≥1 row-level locator citing today's
  ``accepted_running_state_daily``.
- Spike-emit additional: when the ACWR-spike rule fires AND
  ``recovery_today_row_version`` is also passed,
  ``evidence_locators`` additionally carries a column-level locator
  citing ``accepted_recovery_state_daily.acwr_ratio``.
- Legacy 4-arg signature stable: when locator args are absent,
  ``evidence_locators`` is None (no behavior change for callers
  pre-W-PROV-2).
"""

from __future__ import annotations

from health_agent_infra.core.provenance.locator import validate_locator
from health_agent_infra.domains.running.classify import (
    ClassifiedRunningState,
)
from health_agent_infra.domains.running.policy import (
    evaluate_running_policy,
)


def _classified_running_full() -> ClassifiedRunningState:
    return ClassifiedRunningState(
        weekly_mileage_trend_band="moderate",
        hard_session_load_band="moderate",
        freshness_band="adequate",
        recovery_adjacent_band="ok",
        coverage_band="full",
        running_readiness_status="ready",
        readiness_score=0.7,
        uncertainty=tuple(),
    )


def _signals_below_spike(thresholds_acwr_min_ratio: float = 1.5) -> dict:
    return {"acwr_ratio": thresholds_acwr_min_ratio - 0.2}


def _signals_at_spike(thresholds_acwr_min_ratio: float = 1.5) -> dict:
    return {"acwr_ratio": thresholds_acwr_min_ratio + 0.1}


# ---------------------------------------------------------------------------
# Legacy signature: no locator args → evidence_locators is None
# ---------------------------------------------------------------------------


def test_legacy_signature_emits_no_locators() -> None:
    result = evaluate_running_policy(
        _classified_running_full(),
        _signals_below_spike(),
    )
    assert result.evidence_locators is None


# ---------------------------------------------------------------------------
# Always-emit baseline: row-level locator on today's running row
# ---------------------------------------------------------------------------


def test_always_emit_running_row_locator_on_normal_path() -> None:
    result = evaluate_running_policy(
        _classified_running_full(),
        _signals_below_spike(),
        for_date_iso="2026-05-07",
        user_id="u_local_1",
        running_today_row_version="2026-05-07T08:30:00Z",
    )
    assert result.forced_action is None  # no spike, no coverage gate
    assert result.evidence_locators is not None
    assert len(result.evidence_locators) == 1
    loc = result.evidence_locators[0]
    assert loc["table"] == "accepted_running_state_daily"
    assert loc["pk"] == {"as_of_date": "2026-05-07", "user_id": "u_local_1"}
    assert loc["row_version"] == "2026-05-07T08:30:00Z"
    assert "column" not in loc  # row-level, not column-level
    validate_locator(loc)


def test_always_emit_skipped_when_running_row_version_absent() -> None:
    # Identity present but no running version → no locators.
    result = evaluate_running_policy(
        _classified_running_full(),
        _signals_below_spike(),
        for_date_iso="2026-05-07",
        user_id="u_local_1",
    )
    assert result.evidence_locators is None


# ---------------------------------------------------------------------------
# Spike-emit additional: column-level recovery locator on ACWR firing
# ---------------------------------------------------------------------------


def test_acwr_spike_emits_running_row_plus_recovery_column_locator() -> None:
    result = evaluate_running_policy(
        _classified_running_full(),
        _signals_at_spike(),
        for_date_iso="2026-05-07",
        user_id="u_local_1",
        running_today_row_version="2026-05-07T08:30:00Z",
        recovery_today_row_version="2026-05-07T07:00:00Z",
    )
    assert result.forced_action == "escalate_for_user_review"
    assert result.forced_action_detail is not None
    assert result.forced_action_detail["reason_token"] == "acwr_spike"
    assert result.evidence_locators is not None
    assert len(result.evidence_locators) == 2

    running_loc, recovery_loc = result.evidence_locators
    assert running_loc["table"] == "accepted_running_state_daily"
    assert "column" not in running_loc

    assert recovery_loc["table"] == "accepted_recovery_state_daily"
    assert recovery_loc["column"] == "acwr_ratio"
    assert recovery_loc["pk"] == {
        "as_of_date": "2026-05-07",
        "user_id": "u_local_1",
    }
    assert recovery_loc["row_version"] == "2026-05-07T07:00:00Z"
    validate_locator(running_loc)
    validate_locator(recovery_loc)


def test_acwr_spike_skips_recovery_locator_when_recovery_version_absent() -> None:
    # Spike fires, running locator emitted, but no recovery row version
    # → recovery citation is silently skipped (the W-PROV-1 safe-default
    # mirrors recovery R6's `_r6_spike_locators` shape).
    result = evaluate_running_policy(
        _classified_running_full(),
        _signals_at_spike(),
        for_date_iso="2026-05-07",
        user_id="u_local_1",
        running_today_row_version="2026-05-07T08:30:00Z",
    )
    assert result.forced_action == "escalate_for_user_review"
    assert result.evidence_locators is not None
    assert len(result.evidence_locators) == 1
    assert result.evidence_locators[0]["table"] == "accepted_running_state_daily"
