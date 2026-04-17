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
) -> RunningPolicyResult:
    """Apply running R-rules to a classified running state.

    Returns every decision along with any forced_action or
    capped_confidence the skill must honour. Rule ordering: R-coverage
    short-circuits action selection; R-acwr-spike overrides even if
    R-coverage allows; R-sparse caps confidence independently of action.
    """

    t = thresholds if thresholds is not None else load_thresholds()
    decisions: list[PolicyDecision] = []
    forced_action: Optional[str] = None
    forced_action_detail: Optional[dict[str, Any]] = None
    capped_confidence: Optional[str] = None

    cov_dec, cov_forced = _r_coverage_gate(classified)
    decisions.append(cov_dec)
    if cov_forced is not None:
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
    )
