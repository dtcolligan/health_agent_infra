"""D4 test #6 — stress cold-start lighter relaxation.

Stress cold-start is lighter than running/strength: a user who
reports an ``energy`` self-report on their readiness intake gets the
coverage defer lifted so the stress skill can produce
``maintain_routine`` at capped ``low`` confidence.

Without the energy signal, stress still defers.
"""

from __future__ import annotations

from typing import Any

import pytest

from health_agent_infra.domains.stress.classify import (
    ClassifiedStressState,
)
from health_agent_infra.domains.stress.policy import (
    evaluate_stress_policy,
)


def _classified(coverage_band: str = "insufficient") -> ClassifiedStressState:
    return ClassifiedStressState(
        garmin_stress_band="unknown",
        manual_stress_band="unknown",
        body_battery_trend_band="unknown",
        coverage_band=coverage_band,
        stress_state="unknown",
        stress_score=None,
        body_battery_delta=None,
        uncertainty=(),
    )


def _signals() -> dict[str, Any]:
    return {"stress_history_garmin_last_7": []}


def _ctx(
    *,
    cold_start: bool = True,
    energy_self_report: str | None = "moderate",
) -> dict[str, Any]:
    return {
        "cold_start": cold_start,
        "energy_self_report": energy_self_report,
    }


# ---------------------------------------------------------------------------
# D4 test #6 — energy signal lifts defer at low confidence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("energy", ["low", "moderate", "high"])
def test_cold_start_with_energy_signal_lifts_defer_at_low_confidence(energy: str):
    result = evaluate_stress_policy(
        _classified(coverage_band="insufficient"),
        _signals(),
        cold_start_context=_ctx(energy_self_report=energy),
    )
    assert result.forced_action is None
    assert result.capped_confidence == "low"
    assert "cold_start_stress_history_limited" in result.extra_uncertainty

    relax = [
        d for d in result.policy_decisions
        if d.rule_id == "cold_start_relaxation"
    ]
    assert len(relax) == 1
    assert relax[0].decision == "soften"


def test_cold_start_without_energy_signal_still_defers():
    result = evaluate_stress_policy(
        _classified(coverage_band="insufficient"),
        _signals(),
        cold_start_context=_ctx(energy_self_report=None),
    )
    assert result.forced_action == "defer_decision_insufficient_signal"
    assert "cold_start_stress_history_limited" not in result.extra_uncertainty


def test_cold_start_with_empty_string_energy_still_defers():
    result = evaluate_stress_policy(
        _classified(coverage_band="insufficient"),
        _signals(),
        cold_start_context=_ctx(energy_self_report=""),
    )
    assert result.forced_action == "defer_decision_insufficient_signal"


def test_non_cold_start_user_with_energy_still_defers_on_insufficient_coverage():
    """A graduated user with insufficient stress coverage + an energy
    report shouldn't get the cold-start relaxation — they're past
    the window."""
    result = evaluate_stress_policy(
        _classified(coverage_band="insufficient"),
        _signals(),
        cold_start_context=_ctx(cold_start=False),
    )
    assert result.forced_action == "defer_decision_insufficient_signal"


def test_missing_context_preserves_legacy_defer():
    result = evaluate_stress_policy(
        _classified(coverage_band="insufficient"),
        _signals(),
    )
    assert result.forced_action == "defer_decision_insufficient_signal"
    assert result.extra_uncertainty == ()


# ---------------------------------------------------------------------------
# Sustained-stress escalation still wins during cold-start
# ---------------------------------------------------------------------------


def test_sustained_stress_still_escalates_under_cold_start():
    """Safety — a consecutive-days high-stress run forces the escalate
    action even during cold-start. Cold-start relaxation only lifts the
    coverage defer."""

    # Default thresholds: `r_sustained_stress_min_score=60`,
    # `r_sustained_stress_days=5`. Push five consecutive high-stress
    # days ending today to trigger the escalation rule.
    result = evaluate_stress_policy(
        _classified(coverage_band="insufficient"),
        {"stress_history_garmin_last_7": [80, 80, 80, 80, 80]},
        cold_start_context=_ctx(energy_self_report="low"),
    )
    assert result.forced_action == "escalate_for_user_review"
