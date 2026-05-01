"""Recovery-domain mechanical policy gates (R1, R5, R6).

Extracted from `skills/recovery-readiness/SKILL.md` (Phase 1 step 3).
These three rules produce deterministic decisions that the skill must
honour; the remaining invariants (R2 banned tokens, R3 action envelope,
R4 review-within-24h) stay in `core/validate.py` as writeback-time
checks.

After calling `classify_recovery_state`, callers pass the result and the
same `raw_summary` to `evaluate_recovery_policy`. The returned
`RecoveryPolicyResult` carries:

- `policy_decisions`: every rule evaluated, with decision tier + note.
- `forced_action`: set when a rule mechanically determines the action
  (R1 → `defer_decision_insufficient_signal`, R6 →
  `escalate_for_user_review`). The skill honours this instead of running
  the action matrix.
- `forced_action_detail`: optional dict of reason tokens / counters for
  the forced action.
- `capped_confidence`: set when a rule enforces a ceiling (R5 →
  `moderate`). The skill applies this after choosing confidence from
  coverage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from health_agent_infra.core.config import load_thresholds
from health_agent_infra.domains.recovery.classify import ClassifiedRecoveryState


DecisionTier = str  # "allow" | "soften" | "block" | "escalate"


@dataclass(frozen=True)
class PolicyDecision:
    rule_id: str
    decision: DecisionTier
    note: str


@dataclass(frozen=True)
class RecoveryPolicyResult:
    policy_decisions: tuple[PolicyDecision, ...]
    forced_action: Optional[str] = None
    forced_action_detail: Optional[dict[str, Any]] = None
    capped_confidence: Optional[str] = None
    # v0.1.14 W-PROV-1 — populated when R6 fires with the
    # `resting_hr_spike_3_days_running` reason token. The skill
    # is expected to copy these onto the proposal as
    # `evidence_locators`. None means "no locators required by
    # the gate" (R1 / R5 / non-spike R6 firings); empty list is
    # never produced. See reporting/docs/source_row_provenance.md.
    evidence_locators: Optional[tuple[dict[str, Any], ...]] = None


# ---------------------------------------------------------------------------
# Rule evaluators
# ---------------------------------------------------------------------------

def _r1_coverage_gate(
    classified: ClassifiedRecoveryState,
) -> tuple[PolicyDecision, Optional[str]]:
    """R1 require_min_coverage. Returns (decision, forced_action_or_None)."""

    if classified.coverage_band == "insufficient":
        return (
            PolicyDecision(
                rule_id="require_min_coverage",
                decision="block",
                note="coverage=insufficient; required inputs missing",
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


def _r5_sparse_confidence_cap(
    classified: ClassifiedRecoveryState,
) -> tuple[PolicyDecision, Optional[str]]:
    """R5 no_high_confidence_on_sparse_signal. Caps at moderate when sparse."""

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


def _r6_resting_hr_spike(
    raw_summary: dict[str, Any],
    t: dict[str, Any],
) -> tuple[PolicyDecision, Optional[str], Optional[dict[str, Any]]]:
    """R6 resting_hr_spike_escalation. Escalates when spike days >= threshold."""

    from health_agent_infra.core.config import coerce_int  # noqa: PLC0415

    spike_days = raw_summary.get("resting_hr_spike_days")
    threshold = coerce_int(
        t["policy"]["recovery"]["r6_resting_hr_spike_days_threshold"],
        name="policy.recovery.r6_resting_hr_spike_days_threshold",
    )

    if spike_days is not None and spike_days >= threshold:
        detail = {
            "reason_token": "resting_hr_spike_3_days_running",
            "consecutive_days": spike_days,
        }
        return (
            PolicyDecision(
                rule_id="resting_hr_spike_escalation",
                decision="escalate",
                note=f"resting_hr_spike_days={spike_days} >= threshold={threshold}",
            ),
            "escalate_for_user_review",
            detail,
        )

    return (
        PolicyDecision(
            rule_id="resting_hr_spike_escalation",
            decision="allow",
            note=(
                f"resting_hr_spike_days={spike_days} below threshold={threshold}"
                if spike_days is not None
                else "resting_hr_spike_days unavailable; no escalation"
            ),
        ),
        None,
        None,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def evaluate_recovery_policy(
    classified: ClassifiedRecoveryState,
    raw_summary: dict[str, Any],
    thresholds: Optional[dict[str, Any]] = None,
    *,
    for_date_iso: Optional[str] = None,
    user_id: Optional[str] = None,
    accepted_state_versions: Optional[dict[str, str]] = None,
) -> RecoveryPolicyResult:
    """Apply R1, R5, R6 to a classified recovery state.

    Returns every decision (allow / block / soften / escalate) along with
    any forced_action or capped_confidence the skill must honour. Rule
    ordering matches the skill: R1 short-circuits action selection; R6
    overrides even if R1 allows; R5 caps confidence independently of
    action.

    v0.1.14 W-PROV-1: when R6 fires with the
    ``resting_hr_spike_3_days_running`` reason token AND the optional
    ``for_date_iso`` / ``user_id`` / ``accepted_state_versions`` args
    are provided, populate ``evidence_locators`` on the result with one
    locator per spike day (the trailing ``consecutive_days`` from
    ``for_date_iso``). The skill is expected to copy these onto the
    proposal as ``evidence_locators``. The args are optional to preserve
    the legacy 3-arg signature for callers that don't have access to
    snapshot row-version data.
    """

    t = thresholds if thresholds is not None else load_thresholds()
    decisions: list[PolicyDecision] = []
    forced_action: Optional[str] = None
    forced_action_detail: Optional[dict[str, Any]] = None
    capped_confidence: Optional[str] = None

    r1_dec, r1_forced = _r1_coverage_gate(classified)
    decisions.append(r1_dec)
    if r1_forced is not None:
        forced_action = r1_forced

    r5_dec, r5_cap = _r5_sparse_confidence_cap(classified)
    decisions.append(r5_dec)
    if r5_cap is not None:
        capped_confidence = r5_cap

    r6_dec, r6_forced, r6_detail = _r6_resting_hr_spike(raw_summary, t)
    decisions.append(r6_dec)
    if r6_forced is not None:
        # R6 overrides R1's defer because it's a louder signal; if R1
        # already blocked we still prefer the escalation.
        forced_action = r6_forced
        forced_action_detail = r6_detail

    evidence_locators: Optional[tuple[dict[str, Any], ...]] = None
    if (
        forced_action == "escalate_for_user_review"
        and forced_action_detail is not None
        and forced_action_detail.get("reason_token")
        == "resting_hr_spike_3_days_running"
        and for_date_iso is not None
        and user_id is not None
        and accepted_state_versions is not None
    ):
        evidence_locators = _r6_spike_locators(
            for_date_iso=for_date_iso,
            user_id=user_id,
            consecutive_days=forced_action_detail.get("consecutive_days", 3),
            accepted_state_versions=accepted_state_versions,
        )

    return RecoveryPolicyResult(
        policy_decisions=tuple(decisions),
        forced_action=forced_action,
        forced_action_detail=forced_action_detail,
        capped_confidence=capped_confidence,
        evidence_locators=evidence_locators,
    )


def _r6_spike_locators(
    *,
    for_date_iso: str,
    user_id: str,
    consecutive_days: int,
    accepted_state_versions: dict[str, str],
) -> tuple[dict[str, Any], ...]:
    """Build the locator tuple cited by an R6 spike firing.

    Emits one locator per `accepted_recovery_state_daily` row for the
    trailing `consecutive_days` from `for_date_iso`. The
    `accepted_state_versions` map is `{as_of_date_iso: row_version}` —
    typically the row's `projected_at` timestamp — and must contain
    every spike day. Days missing from the map are silently skipped
    (the skill or caller's responsibility to populate completely;
    skipping is the safe-default rather than fabricating a row_version).
    """

    from datetime import date, timedelta

    end_date = date.fromisoformat(for_date_iso)
    out: list[dict[str, Any]] = []
    for offset in range(consecutive_days):
        day = end_date - timedelta(days=offset)
        day_iso = day.isoformat()
        version = accepted_state_versions.get(day_iso)
        if version is None:
            continue
        out.append({
            "table": "accepted_recovery_state_daily",
            "pk": {"as_of_date": day_iso, "user_id": user_id},
            "column": "resting_hr",
            "row_version": version,
        })
    return tuple(out)
