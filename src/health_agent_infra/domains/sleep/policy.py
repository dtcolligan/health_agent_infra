"""Sleep-domain mechanical policy gates.

Phase 3 step 3. Mirrors the recovery / running R-rule contract: a
single entry point ``evaluate_sleep_policy`` returns a frozen
``SleepPolicyResult`` carrying every decision (allow / soften / block /
escalate) along with any ``forced_action`` or ``capped_confidence`` the
sleep-quality skill must honour.

Three rules in v1:

  - ``require_min_coverage`` (block + forced
    ``defer_decision_insufficient_signal``) when
    ``coverage_band == 'insufficient'``.
  - ``no_high_confidence_on_sparse_signal`` (soften + cap to
    ``moderate``) when ``coverage_band == 'sparse'``.
  - ``chronic_deprivation_escalation`` (escalate + forced
    ``sleep_debt_repayment_day``) when the trailing 7-night window has
    >= r_chronic_deprivation_nights nights under
    r_chronic_deprivation_hours. Sleep's v1 action enum has no
    ``escalate_for_user_review`` — the remedial action
    ``sleep_debt_repayment_day`` is forced, and the severity is
    recorded in the ``escalate`` decision tier on the audit record.

R-rules are domain-internal and fire deterministically off the sleep
classifier output + the sleep signals dict. Cross-domain X-rules (X1
sleep → training) live in the synthesis layer and are evaluated
separately; an R-rule that overlaps with an X-rule (e.g. chronic
deprivation + X1b elevated debt) is intentional — the R-rule gives the
domain its own forced action even if synthesis is not run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from health_agent_infra.core.config import load_thresholds
from health_agent_infra.domains.sleep.classify import ClassifiedSleepState


DecisionTier = str  # "allow" | "soften" | "block" | "escalate"


@dataclass(frozen=True)
class PolicyDecision:
    rule_id: str
    decision: DecisionTier
    note: str


@dataclass(frozen=True)
class SleepPolicyResult:
    policy_decisions: tuple[PolicyDecision, ...]
    forced_action: Optional[str] = None
    forced_action_detail: Optional[dict[str, Any]] = None
    capped_confidence: Optional[str] = None


# ---------------------------------------------------------------------------
# Rule evaluators
# ---------------------------------------------------------------------------

def _r_coverage_gate(
    classified: ClassifiedSleepState,
) -> tuple[PolicyDecision, Optional[str]]:
    if classified.coverage_band == "insufficient":
        return (
            PolicyDecision(
                rule_id="require_min_coverage",
                decision="block",
                note="coverage=insufficient; required sleep inputs missing",
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
    classified: ClassifiedSleepState,
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


def _r_chronic_deprivation(
    sleep_signals: dict[str, Any],
    t: dict[str, Any],
) -> tuple[PolicyDecision, Optional[str], Optional[dict[str, Any]]]:
    """Count nights in the trailing 7-night window under the deprivation
    threshold. Fires when >= ``r_chronic_deprivation_nights``.

    The caller supplies ``sleep_history_hours_last_7`` as a list of
    floats (most-recent 7 nights of ``sleep_hours``, including today
    if available). Absent / None entries are treated as non-deprivation
    nights — the R1 coverage gate is the authoritative signal for
    missing-data escalation; this rule only counts explicit shortfalls.
    """

    history = sleep_signals.get("sleep_history_hours_last_7") or []
    threshold_hours = t["policy"]["sleep"]["r_chronic_deprivation_hours"]
    threshold_nights = t["policy"]["sleep"]["r_chronic_deprivation_nights"]

    short_nights = sum(
        1 for h in history if h is not None and h < threshold_hours
    )

    if short_nights >= threshold_nights:
        detail = {
            "reason_token": "chronic_deprivation_detected",
            "short_nights": short_nights,
            "window_nights": len(history),
            "threshold_hours": threshold_hours,
            "threshold_nights": threshold_nights,
        }
        return (
            PolicyDecision(
                rule_id="chronic_deprivation_escalation",
                decision="escalate",
                note=(
                    f"short_nights={short_nights} >= threshold={threshold_nights} "
                    f"(< {threshold_hours}h in last {len(history)} nights)"
                ),
            ),
            "sleep_debt_repayment_day",
            detail,
        )

    return (
        PolicyDecision(
            rule_id="chronic_deprivation_escalation",
            decision="allow",
            note=(
                f"short_nights={short_nights} below threshold={threshold_nights} "
                f"(history_len={len(history)})"
            ),
        ),
        None,
        None,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def evaluate_sleep_policy(
    classified: ClassifiedSleepState,
    sleep_signals: dict[str, Any],
    thresholds: Optional[dict[str, Any]] = None,
) -> SleepPolicyResult:
    """Apply sleep R-rules to a classified sleep state.

    Returns every decision along with any forced_action or
    capped_confidence the skill must honour. Rule ordering:
    R-coverage short-circuits action selection; R-chronic-deprivation
    overrides even if R-coverage allows; R-sparse caps confidence
    independently of action.
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

    chron_dec, chron_forced, chron_detail = _r_chronic_deprivation(
        sleep_signals, t,
    )
    decisions.append(chron_dec)
    if chron_forced is not None:
        # Chronic deprivation is the louder signal — mirrors recovery
        # R6 and running R-acwr-spike precedence — so it overrides any
        # R-coverage defer that may have fired earlier.
        forced_action = chron_forced
        forced_action_detail = chron_detail

    return SleepPolicyResult(
        policy_decisions=tuple(decisions),
        forced_action=forced_action,
        forced_action_detail=forced_action_detail,
        capped_confidence=capped_confidence,
    )
