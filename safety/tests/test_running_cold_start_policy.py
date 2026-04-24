"""D4 tests #2–#4 — running cold-start policy relaxation.

The running policy's coverage gate normally forces a defer when
``coverage_band == 'insufficient'``. D4 §Running replaces that rule
with a capped-confidence relaxation when:

  1. The user is in cold-start mode for running (< 14 days of history).
  2. Recovery status is not ``impaired``.
  3. A ``planned_session_type`` is present in manual readiness.

Outside those conditions the pre-D4 forced defer stands.

Covers:
- #2 cold-start + green recovery + planned session → no forced_action,
  capped_confidence='moderate', uncertainty gains
  ``cold_start_running_history_limited``, policy log records the
  ``cold_start_relaxation`` rule as ``soften``.
- #3 cold-start + impaired recovery → still defer.
- #4 cold-start + no planned_session_type → still defer.
- Non-cold-start user (context missing OR cold_start=False) → still defer.
- Coverage bands other than ``insufficient`` are unaffected.
- ACWR spike still overrides (relaxation doesn't touch the spike rule).
"""

from __future__ import annotations

from typing import Any

import pytest

from health_agent_infra.domains.running.classify import ClassifiedRunningState
from health_agent_infra.domains.running.policy import (
    RunningPolicyResult,
    evaluate_running_policy,
)


# ---------------------------------------------------------------------------
# Builders — keep tests readable; the classifier is out of scope here.
# ---------------------------------------------------------------------------


def _classified(
    coverage_band: str = "insufficient",
    uncertainty: tuple[str, ...] = (),
) -> ClassifiedRunningState:
    """Build a minimal ClassifiedRunningState — we only care about
    coverage + uncertainty for these tests.
    """
    return ClassifiedRunningState(
        weekly_mileage_trend_band="unknown",
        hard_session_load_band="unknown",
        freshness_band="unknown",
        recovery_adjacent_band="unknown",
        coverage_band=coverage_band,
        running_readiness_status="unknown",
        readiness_score=None,
        uncertainty=uncertainty,
    )


def _signals(acwr_ratio: float | None = None) -> dict[str, Any]:
    return {"acwr_ratio": acwr_ratio}


def _cold_start_ctx(
    *,
    cold_start: bool = True,
    recovery_status: str | None = "recovered",
    planned_session_type: str | None = "intervals_4x4_z4_z2",
) -> dict[str, Any]:
    return {
        "cold_start": cold_start,
        "recovery_status": recovery_status,
        "planned_session_type": planned_session_type,
    }


# ---------------------------------------------------------------------------
# D4 test #2 — cold-start with green recovery + planned session
# ---------------------------------------------------------------------------


def test_cold_start_green_recovery_with_planned_session_lifts_defer():
    result = evaluate_running_policy(
        _classified(coverage_band="insufficient"),
        _signals(),
        cold_start_context=_cold_start_ctx(
            recovery_status="recovered",
            planned_session_type="intervals_4x4_z4_z2",
        ),
    )

    assert result.forced_action is None
    assert result.capped_confidence == "moderate"
    assert "cold_start_running_history_limited" in result.extra_uncertainty

    rule_ids = [d.rule_id for d in result.policy_decisions]
    # Original coverage rule still fires (audit chain); relaxation rule
    # is recorded next to it.
    assert "require_min_coverage" in rule_ids
    assert "cold_start_relaxation" in rule_ids
    relax = next(
        d for d in result.policy_decisions if d.rule_id == "cold_start_relaxation"
    )
    assert relax.decision == "soften"


def test_cold_start_mildly_impaired_recovery_still_allows_relaxation():
    """D4: relaxation only blocks on ``impaired`` recovery. A
    ``mildly_impaired`` user with a planned session still gets to run.
    """
    result = evaluate_running_policy(
        _classified(coverage_band="insufficient"),
        _signals(),
        cold_start_context=_cold_start_ctx(
            recovery_status="mildly_impaired",
            planned_session_type="run_z2",
        ),
    )
    assert result.forced_action is None
    assert result.capped_confidence == "moderate"


# ---------------------------------------------------------------------------
# D4 test #3 — cold-start with impaired recovery → still defer
# ---------------------------------------------------------------------------


def test_cold_start_impaired_recovery_still_defers():
    result = evaluate_running_policy(
        _classified(coverage_band="insufficient"),
        _signals(),
        cold_start_context=_cold_start_ctx(
            recovery_status="impaired",
            planned_session_type="run_z2",
        ),
    )
    assert result.forced_action == "defer_decision_insufficient_signal"
    assert "cold_start_running_history_limited" not in result.extra_uncertainty
    assert not any(
        d.rule_id == "cold_start_relaxation" for d in result.policy_decisions
    )


# ---------------------------------------------------------------------------
# D4 test #4 — cold-start without planned_session_type → still defer
# ---------------------------------------------------------------------------


def test_cold_start_without_planned_session_still_defers():
    result = evaluate_running_policy(
        _classified(coverage_band="insufficient"),
        _signals(),
        cold_start_context=_cold_start_ctx(planned_session_type=None),
    )
    assert result.forced_action == "defer_decision_insufficient_signal"
    assert "cold_start_running_history_limited" not in result.extra_uncertainty


def test_cold_start_with_empty_planned_session_still_defers():
    """Empty string is truthy to `is not None` but D4 treats it as
    'no intent'. The helper's ``not planned_session_type`` check covers
    both None and empty-string."""
    result = evaluate_running_policy(
        _classified(coverage_band="insufficient"),
        _signals(),
        cold_start_context=_cold_start_ctx(planned_session_type=""),
    )
    assert result.forced_action == "defer_decision_insufficient_signal"


# ---------------------------------------------------------------------------
# Non-cold-start users see pre-D4 behaviour unchanged
# ---------------------------------------------------------------------------


def test_non_cold_start_user_still_defers():
    """A user who's graduated out of cold-start with insufficient
    coverage today (rare but possible — e.g. wearable failure) sees
    the pre-D4 forced defer."""
    result = evaluate_running_policy(
        _classified(coverage_band="insufficient"),
        _signals(),
        cold_start_context=_cold_start_ctx(cold_start=False),
    )
    assert result.forced_action == "defer_decision_insufficient_signal"


def test_missing_cold_start_context_preserves_legacy_behaviour():
    """Existing callers that don't pass ``cold_start_context`` must see
    the pre-D4 defer; no silent behaviour change when the arg is
    omitted."""
    result = evaluate_running_policy(
        _classified(coverage_band="insufficient"),
        _signals(),
    )
    assert result.forced_action == "defer_decision_insufficient_signal"
    assert result.extra_uncertainty == ()


# ---------------------------------------------------------------------------
# Relaxation doesn't misfire when coverage is fine
# ---------------------------------------------------------------------------


def test_cold_start_with_full_coverage_does_not_apply_relaxation():
    """If coverage already allows, there's no forced defer to relax.
    The cold_start_relaxation rule should NOT fire."""
    result = evaluate_running_policy(
        _classified(coverage_band="full"),
        _signals(),
        cold_start_context=_cold_start_ctx(),
    )
    assert result.forced_action is None
    assert result.capped_confidence is None
    assert not any(
        d.rule_id == "cold_start_relaxation" for d in result.policy_decisions
    )
    assert "cold_start_running_history_limited" not in result.extra_uncertainty


# ---------------------------------------------------------------------------
# ACWR spike escalation still wins over cold-start relaxation
# ---------------------------------------------------------------------------


def test_acwr_spike_still_escalates_under_cold_start():
    """Safety-critical: even during cold-start, an ACWR spike must
    force the escalate action. Cold-start relaxation only lifts the
    coverage-gate defer; it doesn't touch the spike rule."""
    result = evaluate_running_policy(
        _classified(coverage_band="insufficient"),
        _signals(acwr_ratio=1.8),
        cold_start_context=_cold_start_ctx(),
    )
    assert result.forced_action == "escalate_for_user_review"


# ---------------------------------------------------------------------------
# Classified_state.uncertainty merge path (via snapshot layer)
# ---------------------------------------------------------------------------


def test_classified_state_uncertainty_merges_cold_start_token():
    """The snapshot layer invokes ``_merge_policy_uncertainty`` to
    fold ``policy.extra_uncertainty`` into the classified_state
    uncertainty list the skill reads. Exercise that merge directly."""

    from health_agent_infra.core.state.snapshot import (
        _merge_policy_uncertainty,
    )

    result = evaluate_running_policy(
        _classified(
            coverage_band="insufficient",
            uncertainty=("training_readiness_unavailable_at_source",),
        ),
        _signals(),
        cold_start_context=_cold_start_ctx(),
    )

    classified = {
        "uncertainty": list(result.extra_uncertainty) and list(
            ("training_readiness_unavailable_at_source",)
        ),
    }
    classified["uncertainty"] = ["training_readiness_unavailable_at_source"]
    _merge_policy_uncertainty(classified, result)

    assert classified["uncertainty"] == [
        "training_readiness_unavailable_at_source",
        "cold_start_running_history_limited",
    ]


def test_merge_is_idempotent_under_repeated_calls():
    """Re-applying the merge mustn't duplicate tokens."""
    from health_agent_infra.core.state.snapshot import (
        _merge_policy_uncertainty,
    )

    result = RunningPolicyResult(
        policy_decisions=(),
        extra_uncertainty=("cold_start_running_history_limited",),
    )
    classified = {"uncertainty": ["cold_start_running_history_limited"]}
    _merge_policy_uncertainty(classified, result)
    _merge_policy_uncertainty(classified, result)

    assert classified["uncertainty"] == ["cold_start_running_history_limited"]
