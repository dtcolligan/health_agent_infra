"""W-PROV-2 strength-domain locator emission.

PLAN §2.A acceptance #2 + #4. Asserts the hybrid emission contract for
strength (single-day rule, 1-row baseline + 1-column citation when the
volume-spike fires).
"""

from __future__ import annotations

from health_agent_infra.core.provenance.locator import validate_locator
from health_agent_infra.domains.strength.classify import (
    ClassifiedStrengthState,
)
from health_agent_infra.domains.strength.policy import (
    evaluate_strength_policy,
)


def _classified_strength(
    *, volume_ratio: float = 1.0, sessions_last_28d: int = 16
) -> ClassifiedStrengthState:
    return ClassifiedStrengthState(
        recent_volume_band="moderate",
        freshness_band_by_group={},
        coverage_band="full",
        strength_status="ready",
        strength_score=0.7,
        volume_ratio=volume_ratio,
        sessions_last_7d=4,
        sessions_last_28d=sessions_last_28d,
        unmatched_exercise_tokens=tuple(),
        uncertainty=tuple(),
    )


def test_legacy_signature_emits_no_locators() -> None:
    result = evaluate_strength_policy(_classified_strength())
    assert result.evidence_locators is None


def test_always_emit_strength_row_locator_on_normal_path() -> None:
    result = evaluate_strength_policy(
        _classified_strength(volume_ratio=1.0),
        for_date_iso="2026-05-07",
        user_id="u_local_1",
        strength_today_row_version="2026-05-07T19:30:00Z",
    )
    assert result.forced_action is None
    assert result.evidence_locators is not None
    assert len(result.evidence_locators) == 1
    loc = result.evidence_locators[0]
    assert loc["table"] == "accepted_resistance_training_state_daily"
    assert loc["pk"] == {"as_of_date": "2026-05-07", "user_id": "u_local_1"}
    assert "column" not in loc
    validate_locator(loc)


def test_volume_spike_emits_row_plus_column_locator() -> None:
    result = evaluate_strength_policy(
        _classified_strength(volume_ratio=1.6, sessions_last_28d=20),
        for_date_iso="2026-05-07",
        user_id="u_local_1",
        strength_today_row_version="2026-05-07T19:30:00Z",
    )
    assert result.forced_action == "escalate_for_user_review"
    assert result.forced_action_detail is not None
    assert (
        result.forced_action_detail["reason_token"] == "volume_spike_detected"
    )
    assert result.evidence_locators is not None
    assert len(result.evidence_locators) == 2
    row_loc, col_loc = result.evidence_locators
    assert "column" not in row_loc
    assert col_loc["column"] == "total_volume_kg_reps"
    assert col_loc["pk"] == row_loc["pk"]
    assert col_loc["row_version"] == row_loc["row_version"]
    for loc in result.evidence_locators:
        validate_locator(loc)


def test_emission_skipped_when_today_row_version_absent() -> None:
    result = evaluate_strength_policy(
        _classified_strength(volume_ratio=1.6, sessions_last_28d=20),
        for_date_iso="2026-05-07",
        user_id="u_local_1",
        # strength_today_row_version omitted
    )
    assert result.evidence_locators is None
