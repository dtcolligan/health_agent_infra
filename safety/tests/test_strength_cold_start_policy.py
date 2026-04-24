"""D4 test #5 — strength cold-start with explicit intent check.

Strength's cold-start relaxation is stricter than running's: the
user's ``planned_session_type`` must contain the substring
``strength`` (case-insensitive). D4 §Strength rejects implicit
relaxation to prevent recommending a lift users didn't signal.

Covers:
- Cold-start + planned_session_type="strength_legs" → relaxation.
- Cold-start + planned_session_type="strength_upper_body" → relaxation.
- Cold-start + planned_session_type="run_z2" → still defer.
- Cold-start + planned_session_type=None → still defer.
- Impaired recovery → still defer.
- Missing cold_start_context → legacy pre-D4 defer behaviour.
"""

from __future__ import annotations

from typing import Any

import pytest

from health_agent_infra.domains.strength.classify import (
    ClassifiedStrengthState,
)
from health_agent_infra.domains.strength.policy import (
    evaluate_strength_policy,
)


def _classified(
    coverage_band: str = "insufficient",
    volume_ratio: float | None = None,
) -> ClassifiedStrengthState:
    return ClassifiedStrengthState(
        recent_volume_band="unknown",
        freshness_band_by_group={},
        coverage_band=coverage_band,
        strength_status="unknown",
        strength_score=None,
        volume_ratio=volume_ratio,
        sessions_last_7d=None,
        sessions_last_28d=None,
        unmatched_exercise_tokens=(),
        uncertainty=(),
    )


def _ctx(
    *,
    cold_start: bool = True,
    recovery_status: str | None = "recovered",
    planned_session_type: str | None = "strength_legs",
) -> dict[str, Any]:
    return {
        "cold_start": cold_start,
        "recovery_status": recovery_status,
        "planned_session_type": planned_session_type,
    }


# ---------------------------------------------------------------------------
# D4 test #5 — explicit strength intent lifts defer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "planned",
    ["strength_legs", "strength_upper_body", "Strength_Push", "STRENGTH_LEGS"],
)
def test_cold_start_with_explicit_strength_intent_lifts_defer(planned: str):
    result = evaluate_strength_policy(
        _classified(coverage_band="insufficient"),
        cold_start_context=_ctx(planned_session_type=planned),
    )
    assert result.forced_action is None
    assert result.capped_confidence == "moderate"
    assert "cold_start_strength_history_limited" in result.extra_uncertainty


@pytest.mark.parametrize(
    "planned",
    ["run_z2", "intervals_4x4_z4_z2", "easy_run", "rest", "cross_train"],
)
def test_cold_start_without_strength_intent_still_defers(planned: str):
    result = evaluate_strength_policy(
        _classified(coverage_band="insufficient"),
        cold_start_context=_ctx(planned_session_type=planned),
    )
    assert result.forced_action == "defer_decision_insufficient_signal"
    assert not any(
        d.rule_id == "cold_start_relaxation" for d in result.policy_decisions
    )


def test_cold_start_with_no_planned_session_still_defers():
    result = evaluate_strength_policy(
        _classified(coverage_band="insufficient"),
        cold_start_context=_ctx(planned_session_type=None),
    )
    assert result.forced_action == "defer_decision_insufficient_signal"


def test_cold_start_impaired_recovery_still_defers():
    result = evaluate_strength_policy(
        _classified(coverage_band="insufficient"),
        cold_start_context=_ctx(
            recovery_status="impaired",
            planned_session_type="strength_legs",
        ),
    )
    assert result.forced_action == "defer_decision_insufficient_signal"


def test_non_cold_start_user_still_defers_on_insufficient_coverage():
    result = evaluate_strength_policy(
        _classified(coverage_band="insufficient"),
        cold_start_context=_ctx(cold_start=False),
    )
    assert result.forced_action == "defer_decision_insufficient_signal"


def test_missing_context_preserves_legacy_defer():
    result = evaluate_strength_policy(
        _classified(coverage_band="insufficient"),
    )
    assert result.forced_action == "defer_decision_insufficient_signal"
    assert result.extra_uncertainty == ()


# ---------------------------------------------------------------------------
# Volume spike still escalates under cold-start
# ---------------------------------------------------------------------------


def test_volume_spike_escalates_under_cold_start():
    """Safety — even with cold-start + strength intent, a volume
    spike ratio forces escalation. Cold-start only lifts coverage
    gate, not the spike rule."""

    result = evaluate_strength_policy(
        _classified(coverage_band="insufficient", volume_ratio=2.0),
        cold_start_context=_ctx(planned_session_type="strength_legs"),
    )
    assert result.forced_action == "escalate_for_user_review"
