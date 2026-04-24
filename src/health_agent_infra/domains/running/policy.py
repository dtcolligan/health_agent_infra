"""Running-domain mechanical policy gates.

Phase 2 step 2. Mirrors the recovery R1/R5/R6 contract: a single entry
point ``evaluate_running_policy`` returns a frozen ``RunningPolicyResult``
carrying every decision (allow / soften / block / escalate) along with
any ``forced_action`` or ``capped_confidence`` the running-readiness
skill must honour.

Three rules in v1:

  - ``require_min_coverage`` (block + forced
    ``defer_decision_insufficient_signal``) when
    ``coverage_band == 'insufficient'``.
  - ``acwr_spike_escalation`` (escalate + forced
    ``escalate_for_user_review``) when ``acwr_ratio`` is at or above the
    spike threshold (default 1.5, aligned with X3b).
  - ``no_high_confidence_on_sparse_signal`` (soften + cap to
    ``moderate``) when ``coverage_band == 'sparse'``.

R-rules are domain-internal and fire deterministically off the running
classifier output + the raw signals. Cross-domain X-rules (X1, X3, X4,
X5, X6, X7, X9) live in the synthesis layer (step 4) and are evaluated
separately; an R-rule that overlaps with an X-rule (e.g. spike + X3b)
is intentional — the R-rule gives the domain its own forced action even
if synthesis is not run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from health_agent_infra.core.config import load_thresholds
from health_agent_infra.domains.running.classify import ClassifiedRunningState


DecisionTier = str  # "allow" | "soften" | "block" | "escalate"


@dataclass(frozen=True)
class PolicyDecision:
    rule_id: str
    decision: DecisionTier
    note: str


@dataclass(frozen=True)
class RunningPolicyResult:
    policy_decisions: tuple[PolicyDecision, ...]
    forced_action: Optional[str] = None
    forced_action_detail: Optional[dict[str, Any]] = None
    capped_confidence: Optional[str] = None
    # D4 cold-start relaxation may add uncertainty tokens that land on
    # ``classified_state.uncertainty`` in the snapshot surface. Empty
    # tuple means no policy-originated uncertainty tokens.
    extra_uncertainty: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Rule evaluators
# ---------------------------------------------------------------------------

def _r_coverage_gate(
    classified: ClassifiedRunningState,
) -> tuple[PolicyDecision, Optional[str]]:
    if classified.coverage_band == "insufficient":
        return (
            PolicyDecision(
                rule_id="require_min_coverage",
                decision="block",
                note="coverage=insufficient; required running inputs missing",
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
    classified: ClassifiedRunningState,
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


def _r_acwr_spike(
    running_signals: dict[str, Any],
    t: dict[str, Any],
) -> tuple[PolicyDecision, Optional[str], Optional[dict[str, Any]]]:
    acwr = running_signals.get("acwr_ratio")
    threshold = t["policy"]["running"]["r_acwr_spike_min_ratio"]

    if acwr is not None and acwr >= threshold:
        detail = {
            "reason_token": "acwr_spike",
            "acwr_ratio": acwr,
            "threshold": threshold,
        }
        return (
            PolicyDecision(
                rule_id="acwr_spike_escalation",
                decision="escalate",
                note=f"acwr_ratio={acwr} >= threshold={threshold}",
            ),
            "escalate_for_user_review",
            detail,
        )

    return (
        PolicyDecision(
            rule_id="acwr_spike_escalation",
            decision="allow",
            note=(
                f"acwr_ratio={acwr} below threshold={threshold}"
                if acwr is not None
                else "acwr_ratio unavailable; no escalation"
            ),
        ),
        None,
        None,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def evaluate_running_policy(
    classified: ClassifiedRunningState,
    running_signals: dict[str, Any],
    thresholds: Optional[dict[str, Any]] = None,
    cold_start_context: Optional[dict[str, Any]] = None,
) -> RunningPolicyResult:
    """Apply running R-rules to a classified running state.

    Returns every decision along with any forced_action or
    capped_confidence the skill must honour. Rule ordering: R-coverage
    short-circuits action selection; R-acwr-spike overrides even if
    R-coverage allows; R-sparse caps confidence independently of action.

    ``cold_start_context`` is the D4 cold-start relaxation payload:

        {"cold_start": bool,
         "recovery_status": "recovered" | "mildly_impaired" | "impaired" | None,
         "planned_session_type": str | None}

    When ``cold_start`` is True AND recovery is not ``impaired`` AND a
    ``planned_session_type`` is present, the coverage gate's forced
    defer is lifted: the skill gets to produce a non-defer recommendation
    at capped ``moderate`` confidence, with
    ``cold_start_running_history_limited`` added to uncertainty.
    Outside those conditions the pre-D4 behaviour stands.
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
        relax = _running_cold_start_relax(cov_forced, cold_start_context)
        if relax is not None:
            # D4: relaxation keeps the coverage decision as-is in the
            # audit trail but drops the forced defer. The relaxation
            # itself is logged as a separate allow/soften decision so
            # an auditor sees why the defer didn't fire.
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

    spike_dec, spike_forced, spike_detail = _r_acwr_spike(running_signals, t)
    decisions.append(spike_dec)
    if spike_forced is not None:
        # Spike overrides coverage-defer because escalation is the louder signal.
        forced_action = spike_forced
        forced_action_detail = spike_detail

    return RunningPolicyResult(
        policy_decisions=tuple(decisions),
        forced_action=forced_action,
        forced_action_detail=forced_action_detail,
        capped_confidence=capped_confidence,
        extra_uncertainty=tuple(extra_uncertainty),
    )


# ---------------------------------------------------------------------------
# D4 cold-start relaxation — lifts the coverage-gate's forced defer on
# first-run users when recovery is non-red and a planned session intent
# is present.
# ---------------------------------------------------------------------------


_COLD_START_UNCERTAINTY = "cold_start_running_history_limited"
_COLD_START_CAPPED_CONFIDENCE = "moderate"
_COLD_START_BLOCKING_RECOVERY_STATUSES = frozenset({"impaired"})


def _running_cold_start_relax(
    cov_forced: str,
    cold_start_context: Optional[dict[str, Any]],
) -> Optional[tuple[PolicyDecision, str, tuple[str, ...]]]:
    """If cold-start relaxation applies, return
    ``(audit_decision, capped_confidence, extra_uncertainty)``. Return
    ``None`` when the coverage-gate's forced defer should stand.

    Only operates when the coverage gate fired a defer — never
    relaxes an ACWR spike escalation or any other forced action.
    """

    if cov_forced != "defer_decision_insufficient_signal":
        return None
    if cold_start_context is None:
        return None
    if not cold_start_context.get("cold_start"):
        return None

    recovery_status = cold_start_context.get("recovery_status")
    planned_session_type = cold_start_context.get("planned_session_type")

    if recovery_status in _COLD_START_BLOCKING_RECOVERY_STATUSES:
        # Honest defer: even a first-run user with a planned session
        # shouldn't train through an impaired recovery state.
        return None
    if not planned_session_type:
        # No structured intent → no anchor for the skill to shape a
        # recommendation from. Stays defer.
        return None

    decision = PolicyDecision(
        rule_id="cold_start_relaxation",
        decision="soften",
        note=(
            "cold-start window active (history_days<14); recovery not "
            "impaired and planned_session_type supplied — allowing a "
            "non-defer recommendation at moderate confidence."
        ),
    )
    return decision, _COLD_START_CAPPED_CONFIDENCE, (_COLD_START_UNCERTAINTY,)
