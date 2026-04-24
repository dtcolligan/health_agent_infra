"""Strength-domain mechanical policy gates.

Phase 4 step 3. Mirrors the sleep / running R-rule contract: a single
entry point ``evaluate_strength_policy`` returns a frozen
``StrengthPolicyResult`` carrying every decision (allow / soften /
block / escalate) along with any ``forced_action`` or
``capped_confidence`` the strength-readiness skill must honour.

Three rules in v1:

  - ``require_min_coverage`` (block + forced
    ``defer_decision_insufficient_signal``) when
    ``coverage_band == 'insufficient'``.
  - ``no_high_confidence_on_sparse_signal`` (soften + cap to
    ``moderate``) when ``coverage_band == 'sparse'``.
  - ``volume_spike_escalation`` (escalate + forced
    ``escalate_for_user_review``) when the recent volume ratio is at
    or above ``r_volume_spike_min_ratio``. Aligned with the running
    R-acwr-spike threshold (1.5) so cross-domain escalations coincide.
  - ``unmatched_exercise_confidence_cap`` (soften + cap to ``moderate``)
    when ``unmatched_exercise_tokens_present`` is set. Low-confidence
    taxonomy matches are an intake-quality signal, not a training
    signal; capping confidence signals to the agent that the audit
    layer can't fully reason about these sets.

R-rules are domain-internal and fire deterministically off the
classifier output. Cross-domain X-rules (X3 ACWR caps strength, X4 /
X5 lower-body caps) live in the synthesis layer and are evaluated
separately; an R-rule that overlaps with an X-rule (e.g. R-volume-spike
+ X3b) is intentional — the R-rule gives the strength domain its own
forced action even if synthesis is not run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from health_agent_infra.core.config import load_thresholds
from health_agent_infra.domains.strength.classify import ClassifiedStrengthState


DecisionTier = str  # "allow" | "soften" | "block" | "escalate"


@dataclass(frozen=True)
class PolicyDecision:
    rule_id: str
    decision: DecisionTier
    note: str


@dataclass(frozen=True)
class StrengthPolicyResult:
    policy_decisions: tuple[PolicyDecision, ...]
    forced_action: Optional[str] = None
    forced_action_detail: Optional[dict[str, Any]] = None
    capped_confidence: Optional[str] = None
    # D4 cold-start relaxation may add uncertainty tokens the snapshot
    # layer folds into classified_state.uncertainty.
    extra_uncertainty: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Rule evaluators
# ---------------------------------------------------------------------------


def _r_coverage_gate(
    classified: ClassifiedStrengthState,
) -> tuple[PolicyDecision, Optional[str]]:
    if classified.coverage_band == "insufficient":
        return (
            PolicyDecision(
                rule_id="require_min_coverage",
                decision="block",
                note="coverage=insufficient; required strength inputs missing",
            ),
            "defer_decision_insufficient_signal",
        )
    return (
        PolicyDecision(
            rule_id="require_min_coverage",
            decision="allow",
            note=f"coverage={classified.coverage_band}; required inputs present",
        ),
        None,
    )


def _r_sparse_confidence_cap(
    classified: ClassifiedStrengthState,
) -> tuple[PolicyDecision, Optional[str]]:
    if classified.coverage_band == "sparse":
        return (
            PolicyDecision(
                rule_id="no_high_confidence_on_sparse_signal",
                decision="soften",
                note="capped confidence to moderate on sparse session history",
            ),
            "moderate",
        )
    return (
        PolicyDecision(
            rule_id="no_high_confidence_on_sparse_signal",
            decision="allow",
            note=f"coverage={classified.coverage_band}; no cap required",
        ),
        None,
    )


def _r_volume_spike(
    classified: ClassifiedStrengthState,
    t: dict[str, Any],
) -> tuple[PolicyDecision, Optional[str], Optional[dict[str, Any]]]:
    threshold = t["policy"]["strength"]["r_volume_spike_min_ratio"]
    ratio = classified.volume_ratio

    if ratio is not None and ratio >= threshold:
        detail = {
            "reason_token": "volume_spike_detected",
            "volume_ratio": round(ratio, 2),
            "threshold_ratio": threshold,
        }
        return (
            PolicyDecision(
                rule_id="volume_spike_escalation",
                decision="escalate",
                note=(
                    f"volume_ratio={ratio:.2f} >= threshold={threshold}; "
                    f"escalate for user review"
                ),
            ),
            "escalate_for_user_review",
            detail,
        )

    return (
        PolicyDecision(
            rule_id="volume_spike_escalation",
            decision="allow",
            note=(
                f"volume_ratio="
                f"{('unknown' if ratio is None else f'{ratio:.2f}')} "
                f"below threshold={threshold}"
            ),
        ),
        None,
        None,
    )


def _r_unmatched_exercise_cap(
    classified: ClassifiedStrengthState,
) -> tuple[PolicyDecision, Optional[str]]:
    if classified.unmatched_exercise_tokens:
        tokens_str = ",".join(classified.unmatched_exercise_tokens)
        return (
            PolicyDecision(
                rule_id="unmatched_exercise_confidence_cap",
                decision="soften",
                note=(
                    f"capped confidence to moderate on unmatched tokens "
                    f"({tokens_str})"
                ),
            ),
            "moderate",
        )
    return (
        PolicyDecision(
            rule_id="unmatched_exercise_confidence_cap",
            decision="allow",
            note="no unmatched exercise tokens",
        ),
        None,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def evaluate_strength_policy(
    classified: ClassifiedStrengthState,
    thresholds: Optional[dict[str, Any]] = None,
    cold_start_context: Optional[dict[str, Any]] = None,
) -> StrengthPolicyResult:
    """Apply strength R-rules to a classified strength state.

    Returns every decision along with any forced_action or
    capped_confidence the skill must honour. Rule ordering:
    R-coverage short-circuits action selection; R-volume-spike
    overrides even if R-coverage allows; R-sparse + R-unmatched cap
    confidence independently of action. When both sparse and unmatched
    caps fire, the cap value is the same (``moderate``) so there is
    no tie-breaker to resolve.

    ``cold_start_context`` is the D4 strength relaxation payload:

        {"cold_start": bool,
         "recovery_status": "recovered" | "mildly_impaired" | "impaired" | None,
         "planned_session_type": str | None}

    Strength's relaxation requires explicit strength intent — unlike
    running, we don't assume cold-start users want to lift without
    being told. The ``planned_session_type`` substring must contain
    ``strength`` (case-insensitive) for the defer to lift.
    """

    t = thresholds if thresholds is not None else load_thresholds()
    decisions: list[PolicyDecision] = []
    forced_action: Optional[str] = None
    forced_action_detail: Optional[dict[str, Any]] = None
    capped_confidence: Optional[str] = None
    extra_uncertainty: list[str] = []

    cov_dec, cov_forced = _r_coverage_gate(classified)
    decisions.append(cov_dec)
    if cov_forced is not None:
        relax = _strength_cold_start_relax(cov_forced, cold_start_context)
        if relax is not None:
            relax_decision, relax_capped, relax_uncertainty = relax
            decisions.append(relax_decision)
            capped_confidence = relax_capped
            extra_uncertainty.extend(relax_uncertainty)
        else:
            forced_action = cov_forced

    spike_dec, spike_forced, spike_detail = _r_volume_spike(classified, t)
    decisions.append(spike_dec)
    if spike_forced is not None:
        # Volume spike is the louder signal — mirrors sleep's chronic
        # deprivation override + running's R-acwr-spike — so it
        # overrides any R-coverage defer that may have fired earlier.
        forced_action = spike_forced
        forced_action_detail = spike_detail

    cap_dec, cap_value = _r_sparse_confidence_cap(classified)
    decisions.append(cap_dec)
    if cap_value is not None:
        capped_confidence = cap_value

    unmatched_dec, unmatched_cap = _r_unmatched_exercise_cap(classified)
    decisions.append(unmatched_dec)
    if unmatched_cap is not None and capped_confidence is None:
        capped_confidence = unmatched_cap

    return StrengthPolicyResult(
        policy_decisions=tuple(decisions),
        forced_action=forced_action,
        forced_action_detail=forced_action_detail,
        capped_confidence=capped_confidence,
        extra_uncertainty=tuple(extra_uncertainty),
    )


# ---------------------------------------------------------------------------
# D4 strength cold-start relaxation — explicit intent required.
# ---------------------------------------------------------------------------


_STRENGTH_COLD_START_UNCERTAINTY = "cold_start_strength_history_limited"
_STRENGTH_COLD_START_CAPPED = "moderate"
_STRENGTH_BLOCKING_RECOVERY = frozenset({"impaired"})


def _strength_cold_start_relax(
    cov_forced: str,
    cold_start_context: Optional[dict[str, Any]],
) -> Optional[tuple[PolicyDecision, str, tuple[str, ...]]]:
    if cov_forced != "defer_decision_insufficient_signal":
        return None
    if cold_start_context is None:
        return None
    if not cold_start_context.get("cold_start"):
        return None
    if cold_start_context.get("recovery_status") in _STRENGTH_BLOCKING_RECOVERY:
        return None

    planned = cold_start_context.get("planned_session_type") or ""
    if "strength" not in planned.lower():
        # No explicit strength intent → honest defer. D4 §Strength
        # rejects implicit relaxation to avoid recommending lifts
        # users didn't signal they wanted to do.
        return None

    decision = PolicyDecision(
        rule_id="cold_start_relaxation",
        decision="soften",
        note=(
            "cold-start window active (history_days<14); recovery not "
            "impaired and planned_session_type indicates strength — "
            "allowing a non-defer recommendation at moderate confidence."
        ),
    )
    return (
        decision,
        _STRENGTH_COLD_START_CAPPED,
        (_STRENGTH_COLD_START_UNCERTAINTY,),
    )
