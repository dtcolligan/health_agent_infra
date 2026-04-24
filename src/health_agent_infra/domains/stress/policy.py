"""Stress-domain mechanical policy gates.

Phase 3 step 4. Mirrors the recovery / running / sleep R-rule contract:
a single entry point ``evaluate_stress_policy`` returns a frozen
``StressPolicyResult`` carrying every decision (allow / soften / block /
escalate) along with any ``forced_action`` or ``capped_confidence`` the
stress-regulation skill must honour.

Three rules in v1:

  - ``require_min_coverage`` (block + forced
    ``defer_decision_insufficient_signal``) when
    ``coverage_band == 'insufficient'``.
  - ``no_high_confidence_on_sparse_signal`` (soften + cap to
    ``moderate``) when ``coverage_band == 'sparse'``.
  - ``sustained_very_high_stress_escalation`` (escalate + forced
    ``escalate_for_user_review``) when Garmin's all-day-stress has been
    at or above ``r_sustained_stress_min_score`` for
    ``r_sustained_stress_days`` consecutive days (today included).

R-rules are domain-internal and fire deterministically off the stress
classifier output + the stress signals dict. Cross-domain X-rules (X6
body battery → everything, X7 stress → cap confidence) live in the
synthesis layer and are evaluated separately; an R-rule that overlaps
with an X-rule (e.g. sustained stress + X7 cap) is intentional — the
R-rule gives the domain its own forced action even if synthesis is not
run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from health_agent_infra.core.config import load_thresholds
from health_agent_infra.domains.stress.classify import ClassifiedStressState


DecisionTier = str  # "allow" | "soften" | "block" | "escalate"


@dataclass(frozen=True)
class PolicyDecision:
    rule_id: str
    decision: DecisionTier
    note: str


@dataclass(frozen=True)
class StressPolicyResult:
    policy_decisions: tuple[PolicyDecision, ...]
    forced_action: Optional[str] = None
    forced_action_detail: Optional[dict[str, Any]] = None
    capped_confidence: Optional[str] = None
    # D4 cold-start — tokens the snapshot layer folds into
    # classified_state.uncertainty.
    extra_uncertainty: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Rule evaluators
# ---------------------------------------------------------------------------

def _r_coverage_gate(
    classified: ClassifiedStressState,
) -> tuple[PolicyDecision, Optional[str]]:
    if classified.coverage_band == "insufficient":
        return (
            PolicyDecision(
                rule_id="require_min_coverage",
                decision="block",
                note="coverage=insufficient; required stress inputs missing",
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
    classified: ClassifiedStressState,
) -> tuple[PolicyDecision, Optional[str]]:
    if classified.coverage_band == "sparse":
        tokens_str = ",".join(classified.uncertainty) if classified.uncertainty else ""
        return (
            PolicyDecision(
                rule_id="no_high_confidence_on_sparse_signal",
                decision="soften",
                note=f"capped confidence to moderate on sparse signal ({tokens_str})",
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


def _r_sustained_stress(
    stress_signals: dict[str, Any],
    t: dict[str, Any],
) -> tuple[PolicyDecision, Optional[str], Optional[dict[str, Any]]]:
    """Count consecutive days (ending today) with Garmin all-day-stress
    at or above the threshold. Fires when the run length is >=
    ``r_sustained_stress_days``.

    The caller supplies ``stress_history_garmin_last_7`` as a list of
    Optional[int] — the trailing-7 day window of
    ``garmin_all_day_stress`` values with the final element being today.
    Absent / None entries break the consecutive run; only explicit
    at-or-above-threshold values extend it. The R1 coverage gate is the
    authoritative signal for missing-data escalation; this rule only
    counts explicit high-stress days.
    """

    history = stress_signals.get("stress_history_garmin_last_7") or []
    threshold_score = t["policy"]["stress"]["r_sustained_stress_min_score"]
    threshold_days = t["policy"]["stress"]["r_sustained_stress_days"]

    # Count the trailing consecutive run ending at today. Walk from the
    # end of the window back; a missing value or a value below the
    # threshold breaks the run.
    run_length = 0
    for value in reversed(history):
        if value is None or value < threshold_score:
            break
        run_length += 1

    if run_length >= threshold_days:
        detail = {
            "reason_token": "sustained_very_high_stress",
            "consecutive_days": run_length,
            "window_nights": len(history),
            "threshold_score": threshold_score,
            "threshold_days": threshold_days,
        }
        return (
            PolicyDecision(
                rule_id="sustained_very_high_stress_escalation",
                decision="escalate",
                note=(
                    f"consecutive_days={run_length} >= threshold={threshold_days} "
                    f"(>= {threshold_score} in last {len(history)} days)"
                ),
            ),
            "escalate_for_user_review",
            detail,
        )

    return (
        PolicyDecision(
            rule_id="sustained_very_high_stress_escalation",
            decision="allow",
            note=(
                f"consecutive_days={run_length} below threshold={threshold_days} "
                f"(history_len={len(history)})"
            ),
        ),
        None,
        None,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def evaluate_stress_policy(
    classified: ClassifiedStressState,
    stress_signals: dict[str, Any],
    thresholds: Optional[dict[str, Any]] = None,
    cold_start_context: Optional[dict[str, Any]] = None,
) -> StressPolicyResult:
    """Apply stress R-rules to a classified stress state.

    Returns every decision along with any forced_action or
    capped_confidence the skill must honour. Rule ordering:
    R-coverage short-circuits action selection; R-sustained-stress
    overrides even if R-coverage allows; R-sparse caps confidence
    independently of action.

    ``cold_start_context`` is the D4 stress relaxation payload:

        {"cold_start": bool, "energy_self_report": str | None}

    Lighter than running/strength: if the user reported an energy
    band on their readiness intake, the stress skill may produce a
    ``maintain_routine`` recommendation at capped ``low`` confidence.
    Without the energy signal, still defer.
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
        relax = _stress_cold_start_relax(cov_forced, cold_start_context)
        if relax is not None:
            relax_decision, relax_capped, relax_uncertainty = relax
            decisions.append(relax_decision)
            capped_confidence = relax_capped
            extra_uncertainty.extend(relax_uncertainty)
        else:
            forced_action = cov_forced

    cap_dec, cap_value = _r_sparse_confidence_cap(classified)
    decisions.append(cap_dec)
    if cap_value is not None:
        capped_confidence = cap_value

    sust_dec, sust_forced, sust_detail = _r_sustained_stress(stress_signals, t)
    decisions.append(sust_dec)
    if sust_forced is not None:
        # Sustained stress is the louder signal — mirrors recovery R6
        # and sleep's R-chronic-deprivation precedence — so it overrides
        # any R-coverage defer that may have fired earlier.
        forced_action = sust_forced
        forced_action_detail = sust_detail

    return StressPolicyResult(
        policy_decisions=tuple(decisions),
        forced_action=forced_action,
        forced_action_detail=forced_action_detail,
        capped_confidence=capped_confidence,
        extra_uncertainty=tuple(extra_uncertainty),
    )


# ---------------------------------------------------------------------------
# D4 stress cold-start relaxation — lighter than running/strength:
# an energy self-report alone is enough to lift the coverage defer,
# but confidence drops to low.
# ---------------------------------------------------------------------------


_STRESS_COLD_START_UNCERTAINTY = "cold_start_stress_history_limited"
_STRESS_COLD_START_CAPPED = "low"


def _stress_cold_start_relax(
    cov_forced: str,
    cold_start_context: Optional[dict[str, Any]],
) -> Optional[tuple[PolicyDecision, str, tuple[str, ...]]]:
    if cov_forced != "defer_decision_insufficient_signal":
        return None
    if cold_start_context is None:
        return None
    if not cold_start_context.get("cold_start"):
        return None

    energy = cold_start_context.get("energy_self_report")
    if not energy:
        # No subjective signal anywhere → honest defer. D4 §Stress
        # keeps relaxation dependent on the energy self-report.
        return None

    decision = PolicyDecision(
        rule_id="cold_start_relaxation",
        decision="soften",
        note=(
            "cold-start window active (history_days<14); readiness "
            "energy self-report present — allowing a maintain_routine "
            "recommendation at low confidence."
        ),
    )
    return (
        decision,
        _STRESS_COLD_START_CAPPED,
        (_STRESS_COLD_START_UNCERTAINTY,),
    )
