"""Nutrition-domain mechanical policy gates.

Phase 5 step 2, under the Phase 2.5 retrieval-gate outcome (macros-only).
Mirrors the sleep / strength / running R-rule contract: a single entry
point ``evaluate_nutrition_policy`` returns a frozen
``NutritionPolicyResult`` carrying every decision (allow / soften /
block / escalate) along with any ``forced_action`` or
``capped_confidence`` the nutrition-alignment skill must honour.

Three rules in v1:

  - ``require_min_coverage`` (block + forced
    ``defer_decision_insufficient_signal``) when
    ``coverage_band == 'insufficient'``. No accepted row for the day,
    or macros missing on a malformed row, means classify cannot land a
    verdict — the policy forces the defer action so downstream does
    not read silence as alignment.
  - ``no_high_confidence_on_sparse_signal`` (soften + cap to
    ``moderate``) when ``coverage_band ∈ {'sparse', 'partial'}``. Row
    present but user skipped at least one optional field
    (hydration_l / meals_count); the four-macro read is trustworthy,
    but the missing optional fields dampen confidence on the full
    verdict.
  - ``extreme_deficiency_escalation`` (escalate + forced
    ``escalate_for_user_review``) when BOTH calorie_deficit ≥
    r_extreme_deficiency_min_calorie_deficit_kcal AND protein_ratio <
    r_extreme_deficiency_max_protein_ratio fire on the same day. Either
    alone is softened via the band verdict; the combination is the
    overreaching-deficit signal worth a user review rather than a
    silent downgrade.

R-rules are domain-internal and fire deterministically off the
classifier output. Cross-domain X-rules (X2 nutrition deficit softens
strength; X9 post-adjust nutrition targets off training) live in the
synthesis layer and are evaluated separately; an R-rule that overlaps
with an X-rule (R-extreme-deficiency + X2) is intentional — the R-rule
gives the nutrition domain its own forced action even when synthesis
is not run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from health_agent_infra.core.config import load_thresholds
from health_agent_infra.domains.nutrition.classify import ClassifiedNutritionState


DecisionTier = str  # "allow" | "soften" | "block" | "escalate"


@dataclass(frozen=True)
class PolicyDecision:
    rule_id: str
    decision: DecisionTier
    note: str


@dataclass(frozen=True)
class NutritionPolicyResult:
    policy_decisions: tuple[PolicyDecision, ...]
    forced_action: Optional[str] = None
    forced_action_detail: Optional[dict[str, Any]] = None
    capped_confidence: Optional[str] = None


# ---------------------------------------------------------------------------
# Rule evaluators
# ---------------------------------------------------------------------------


def _r_coverage_gate(
    classified: ClassifiedNutritionState,
) -> tuple[PolicyDecision, Optional[str]]:
    if classified.coverage_band == "insufficient":
        return (
            PolicyDecision(
                rule_id="require_min_coverage",
                decision="block",
                note="coverage=insufficient; no nutrition row for the day",
            ),
            "defer_decision_insufficient_signal",
        )
    return (
        PolicyDecision(
            rule_id="require_min_coverage",
            decision="allow",
            note=f"coverage={classified.coverage_band}; macros present",
        ),
        None,
    )


def _r_sparse_confidence_cap(
    classified: ClassifiedNutritionState,
) -> tuple[PolicyDecision, Optional[str]]:
    if classified.coverage_band in ("sparse", "partial"):
        return (
            PolicyDecision(
                rule_id="no_high_confidence_on_sparse_signal",
                decision="soften",
                note=(
                    f"capped confidence to moderate on "
                    f"coverage={classified.coverage_band}"
                ),
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


def _r_extreme_deficiency(
    classified: ClassifiedNutritionState,
    t: dict[str, Any],
) -> tuple[PolicyDecision, Optional[str], Optional[dict[str, Any]]]:
    cfg = t["policy"]["nutrition"]
    min_deficit = float(cfg["r_extreme_deficiency_min_calorie_deficit_kcal"])
    max_protein_ratio = float(cfg["r_extreme_deficiency_max_protein_ratio"])

    deficit = classified.calorie_deficit_kcal
    protein_ratio = classified.protein_ratio

    deficit_triggers = deficit is not None and deficit >= min_deficit
    protein_triggers = protein_ratio is not None and protein_ratio < max_protein_ratio

    if deficit_triggers and protein_triggers:
        detail = {
            "reason_token": "extreme_deficiency_detected",
            "calorie_deficit_kcal": round(deficit, 1),
            "calorie_deficit_threshold_kcal": min_deficit,
            "protein_ratio": round(protein_ratio, 3),
            "protein_ratio_threshold": max_protein_ratio,
        }
        return (
            PolicyDecision(
                rule_id="extreme_deficiency_escalation",
                decision="escalate",
                note=(
                    f"calorie_deficit_kcal={deficit:.0f} >= {min_deficit:.0f} "
                    f"AND protein_ratio={protein_ratio:.2f} < "
                    f"{max_protein_ratio:.2f}; escalate for user review"
                ),
            ),
            "escalate_for_user_review",
            detail,
        )

    return (
        PolicyDecision(
            rule_id="extreme_deficiency_escalation",
            decision="allow",
            note=(
                f"calorie_deficit_kcal="
                f"{('unknown' if deficit is None else f'{deficit:.0f}')}, "
                f"protein_ratio="
                f"{('unknown' if protein_ratio is None else f'{protein_ratio:.2f}')}; "
                f"no extreme-deficiency combination"
            ),
        ),
        None,
        None,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def evaluate_nutrition_policy(
    classified: ClassifiedNutritionState,
    thresholds: Optional[dict[str, Any]] = None,
) -> NutritionPolicyResult:
    """Apply nutrition R-rules to a classified nutrition state.

    Returns every decision along with any forced_action or
    capped_confidence the skill must honour. Rule ordering:
    R-coverage short-circuits action selection; R-extreme-deficiency
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

    extreme_dec, extreme_forced, extreme_detail = _r_extreme_deficiency(classified, t)
    decisions.append(extreme_dec)
    if extreme_forced is not None:
        # Extreme deficiency is the louder signal — mirrors strength's
        # R-volume-spike override + running's R-acwr-spike override —
        # so it overrides any R-coverage defer that may have fired
        # earlier.
        forced_action = extreme_forced
        forced_action_detail = extreme_detail

    cap_dec, cap_value = _r_sparse_confidence_cap(classified)
    decisions.append(cap_dec)
    if cap_value is not None:
        capped_confidence = cap_value

    return NutritionPolicyResult(
        policy_decisions=tuple(decisions),
        forced_action=forced_action,
        forced_action_detail=forced_action_detail,
        capped_confidence=capped_confidence,
    )
