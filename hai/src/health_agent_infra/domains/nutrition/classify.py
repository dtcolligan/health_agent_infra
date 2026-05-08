"""Nutrition-domain state classification — deterministic bands + scoring.

Phase 5 step 2, under the Phase 2.5 retrieval-gate outcome (macros-only).
Mirrors the structure of ``domains.strength.classify`` and
``domains.sleep.classify``: a single entry point
``classify_nutrition_state`` consumes a ``nutrition_signals`` dict and
returns a frozen ``ClassifiedNutritionState``. All numerical decisions
live here; the nutrition-alignment skill (SKILL.md) only writes prose.

Bands:

- **calorie_balance_band** ∈ {met, mild_deficit, moderate_deficit,
  high_deficit, surplus, unknown} — from
  ``absolute_deficit_kcal = target - actual``. ``high_deficit`` begins
  at the X2 threshold (500 kcal) so the X-rule and the classifier
  share the same named boundary.
- **protein_sufficiency_band** ∈ {met, low, very_low, unknown} — from
  ``protein_ratio = actual / target``. ``very_low`` begins at the X2
  threshold (0.7) so the X-rule and the classifier share the same
  named boundary.
- **hydration_band** ∈ {met, low, unknown} — from
  ``hydration_ratio = actual / target``. When the user did not log a
  hydration value (hydration_l is NULL in the raw row), the band is
  ``unknown`` rather than ``low`` — absence of a log is not a deficit.
- **micronutrient_coverage** — always ``unavailable_at_source`` in v1
  when ``derivation_path='daily_macros'`` (the only v1 derivation path).
  Any future meal-level derivation will flip this band without changing
  the field name. The skill reads this band to decide whether to surface
  micronutrient rationale at all — in v1 it does not.
- **coverage_band** ∈ {insufficient, sparse, partial, full} — from the
  accepted row's macro + optional-field population. "insufficient"
  means no row at all for the day; "sparse" means row present but
  neither hydration nor meals_count logged; "partial" means one of
  {hydration, meals_count} logged; "full" means both logged.
- **nutrition_status** ∈ {aligned, deficit_caloric, protein_gap,
  under_hydrated, surplus, unknown, insufficient_data} — composite
  verdict over every band. Precedence high→low: deficit_caloric (high
  or moderate), then protein_gap (very_low or low), then
  under_hydrated (low), then surplus (surplus), then aligned.
  ``unknown`` iff coverage=insufficient. **``insufficient_data``** is
  the v0.1.15 W-D arm-1 short-circuit: emitted when
  ``is_partial_day=True`` AND ``target_status in ('absent',
  'unavailable')``. The runtime explicitly refuses to classify rather
  than misclassifying partial-day intake against a config-baseline
  target the user hasn't committed to. Downstream policy treats
  ``insufficient_data`` via the existing forced-action path
  (coverage=insufficient → defer_decision_insufficient_signal); the
  status enum value is the audit-visible token + the
  ``partial_day_no_target`` uncertainty reason carries the cause.
- **nutrition_score** ∈ [0.0, 1.0] or None — None iff
  ``coverage_band == 'insufficient'`` (which includes the W-D arm-1
  suppression path).
- **uncertainty**: tuple of dedup'd, sorted reason tokens. W-D arm-1
  emits exactly ``("partial_day_no_target",)`` when suppressing.

Signal dict keys recognised:

  - ``today_row`` (dict | None): the accepted nutrition row for the day,
    or None if no row exists. Keys: calories, protein_g, carbs_g,
    fat_g, hydration_l, meals_count, derivation_path.
  - ``goal_domain`` (optional str): reserved for post-v1 goal-aware
    targets. Ignored in v1 — the target set is config-driven only.
  - ``is_partial_day`` (bool, optional, v0.1.15 W-A): True iff the
    snapshot is for today + local clock is before the W-A cutoff +
    fewer than expected meals are logged. When omitted (the pre-W-D
    call shape), the W-D arm-1 short-circuit doesn't fire — backwards-
    compat for callers that haven't been wired to W-A yet.
  - ``target_status`` (str, optional, v0.1.15 W-A): three-valued enum
    ``"present" | "absent" | "unavailable"`` reading the existing
    ``target`` table for nutrition macros. Together with
    ``is_partial_day``, drives the W-D arm-1 suppression.

All keys are optional; absent keys propagate as ``unknown`` bands and
``insufficient`` coverage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from health_agent_infra.core.config import coerce_float, load_thresholds


CalorieBalanceBand = str    # "met"|"mild_deficit"|"moderate_deficit"|"high_deficit"|"surplus"|"unknown"
ProteinSufficiencyBand = str  # "met"|"low"|"very_low"|"unknown"
HydrationBand = str         # "met"|"low"|"unknown"
MicronutrientCoverage = str  # "unavailable_at_source"|"unknown"
CoverageBand = str          # "insufficient"|"sparse"|"partial"|"full"
NutritionStatus = str       # "aligned"|"deficit_caloric"|"protein_gap"|"under_hydrated"|"surplus"|"unknown"|"insufficient_data"


@dataclass(frozen=True)
class ClassifiedNutritionState:
    calorie_balance_band: CalorieBalanceBand
    protein_sufficiency_band: ProteinSufficiencyBand
    hydration_band: HydrationBand
    micronutrient_coverage: MicronutrientCoverage
    coverage_band: CoverageBand
    nutrition_status: NutritionStatus
    nutrition_score: Optional[float]  # None iff coverage=insufficient
    calorie_deficit_kcal: Optional[float]  # target - actual, or None
    protein_ratio: Optional[float]         # actual / target, or None
    hydration_ratio: Optional[float]       # actual / target, or None
    derivation_path: Optional[str]
    uncertainty: tuple[str, ...] = field(default_factory=tuple)
    # W-D arm-2 (v0.1.17 §2.I) — end-of-day macro projections.
    # Populated only when arm-2 fires (is_partial_day=True AND
    # target_status="present"). When the projection branch is the
    # default ``target_anchored``, projected_eod_X equals the active
    # macro target for X. None on every other path (arm-1 suppression,
    # day-closed, no-target). Carbs + fat are emitted as informational
    # values when present; only kcal + protein drive band classification
    # in v1 (no carbs/fat band thresholds in DEFAULT_THRESHOLDS).
    projected_eod_kcal: Optional[float] = None
    projected_eod_protein_g: Optional[float] = None
    projected_eod_carbs_g: Optional[float] = None
    projected_eod_fat_g: Optional[float] = None


# ---------------------------------------------------------------------------
# Band classifiers
# ---------------------------------------------------------------------------


def _classify_calorie_balance(
    deficit_kcal: Optional[float], t: dict[str, Any]
) -> tuple[CalorieBalanceBand, list[str]]:
    if deficit_kcal is None:
        return "unknown", ["calorie_baseline_unavailable"]
    from health_agent_infra.core.config import coerce_float

    cfg = t["classify"]["nutrition"]["calorie_balance_band"]
    surplus_min = coerce_float(cfg["surplus_min_kcal"], name="surplus_min_kcal")
    high = coerce_float(cfg["high_deficit_min_kcal"], name="high_deficit_min_kcal")
    moderate = coerce_float(cfg["moderate_deficit_min_kcal"], name="moderate_deficit_min_kcal")
    mild = coerce_float(cfg["mild_deficit_min_kcal"], name="mild_deficit_min_kcal")
    # Surplus is when actual - target >= surplus_min_kcal, i.e.
    # deficit <= -surplus_min_kcal.
    if deficit_kcal <= -surplus_min:
        return "surplus", []
    if deficit_kcal >= high:
        return "high_deficit", []
    if deficit_kcal >= moderate:
        return "moderate_deficit", []
    if deficit_kcal >= mild:
        return "mild_deficit", []
    return "met", []


def _classify_protein_sufficiency(
    protein_ratio: Optional[float], t: dict[str, Any]
) -> tuple[ProteinSufficiencyBand, list[str]]:
    if protein_ratio is None:
        return "unknown", ["protein_target_unavailable"]
    cfg = t["classify"]["nutrition"]["protein_sufficiency_band"]
    very_low_max = coerce_float(
        cfg["very_low_max_ratio"],
        name="classify.nutrition.protein_sufficiency_band.very_low_max_ratio",
    )
    low_max = coerce_float(
        cfg["low_max_ratio"],
        name="classify.nutrition.protein_sufficiency_band.low_max_ratio",
    )
    if protein_ratio < very_low_max:
        return "very_low", []
    if protein_ratio < low_max:
        return "low", []
    return "met", []


def _classify_hydration(
    hydration_ratio: Optional[float], t: dict[str, Any]
) -> tuple[HydrationBand, list[str]]:
    if hydration_ratio is None:
        # Absence of a log is not a deficit. Surface as unknown + an
        # honest uncertainty token so the skill can decide whether to
        # nudge the user to log hydration.
        return "unknown", ["hydration_not_logged"]
    cfg = t["classify"]["nutrition"]["hydration_band"]
    low_max = coerce_float(
        cfg["low_max_ratio"],
        name="classify.nutrition.hydration_band.low_max_ratio",
    )
    if hydration_ratio < low_max:
        return "low", []
    return "met", []


def _classify_micronutrient_coverage(
    derivation_path: Optional[str],
) -> tuple[MicronutrientCoverage, list[str]]:
    """In v1 the only legitimate derivation_path is 'daily_macros'; that
    derivation carries no micronutrient evidence, so the band is always
    ``unavailable_at_source``. Unknown derivation paths (which cannot
    appear from v1 code but defensively surface here on malformed data)
    land in ``unknown`` with an uncertainty token."""

    if derivation_path is None:
        return "unknown", ["derivation_path_unavailable"]
    if derivation_path == "daily_macros":
        return "unavailable_at_source", ["micronutrients_unavailable_at_source"]
    # Future meal_log derivation will flip this band without changing
    # the field name. For now, surface loudly.
    return "unknown", [f"derivation_path_unknown:{derivation_path}"]


def _classify_coverage(
    today_row: Optional[dict[str, Any]],
) -> tuple[CoverageBand, list[str]]:
    if today_row is None:
        return "insufficient", ["no_nutrition_row_for_day"]
    # Macros are enforced at the CLI boundary — a present row always
    # carries calories/protein/carbs/fat. Optional fields determine the
    # coverage gradient.
    macros = ("calories", "protein_g", "carbs_g", "fat_g")
    null_macros = [m for m in macros if today_row.get(m) is None]
    if null_macros:
        # Rare but defensively handled: a raw CLI bypass or a legacy
        # row may land without all four macros.
        return "insufficient", [f"macros_null:{','.join(null_macros)}"]

    hydration_present = today_row.get("hydration_l") is not None
    meals_count_present = today_row.get("meals_count") is not None
    optional_present = int(hydration_present) + int(meals_count_present)
    if optional_present == 0:
        return "sparse", ["optional_fields_missing:hydration,meals_count"]
    if optional_present == 1:
        missing = [k for k, present in (
            ("hydration_l", hydration_present),
            ("meals_count", meals_count_present),
        ) if not present]
        return "partial", [f"optional_fields_missing:{','.join(missing)}"]
    return "full", []


def _nutrition_status(
    calorie: CalorieBalanceBand,
    protein: ProteinSufficiencyBand,
    hydration: HydrationBand,
    coverage: CoverageBand,
) -> NutritionStatus:
    if coverage == "insufficient":
        return "unknown"
    if calorie in ("high_deficit", "moderate_deficit"):
        return "deficit_caloric"
    if protein in ("very_low", "low"):
        return "protein_gap"
    if hydration == "low":
        return "under_hydrated"
    if calorie == "surplus":
        return "surplus"
    return "aligned"


def _nutrition_score(
    calorie: CalorieBalanceBand,
    protein: ProteinSufficiencyBand,
    hydration: HydrationBand,
    coverage: CoverageBand,
    t: dict[str, Any],
) -> Optional[float]:
    if coverage == "insufficient":
        return None

    raw_penalties = t["classify"]["nutrition"]["nutrition_score_penalty"]
    # Coerce each penalty leaf once so the arithmetic below sees only
    # well-typed floats. Load-time validation already rejects bool-on-
    # numeric overrides; the explicit coerce_float here is consistent
    # with W-A's pattern and self-documents the type contract for
    # readers.
    penalties = {
        key: coerce_float(
            raw_penalties[key],
            name=f"classify.nutrition.nutrition_score_penalty.{key}",
        )
        for key in (
            "calorie_mild_deficit",
            "calorie_moderate_deficit",
            "calorie_high_deficit",
            "calorie_surplus",
            "protein_low",
            "protein_very_low",
            "hydration_low",
            "coverage_partial",
            "coverage_sparse",
        )
    }
    score = 1.0

    if calorie == "mild_deficit":
        score -= penalties["calorie_mild_deficit"]
    elif calorie == "moderate_deficit":
        score -= penalties["calorie_moderate_deficit"]
    elif calorie == "high_deficit":
        score -= penalties["calorie_high_deficit"]
    elif calorie == "surplus":
        score -= penalties["calorie_surplus"]

    if protein == "low":
        score -= penalties["protein_low"]
    elif protein == "very_low":
        score -= penalties["protein_very_low"]

    if hydration == "low":
        score -= penalties["hydration_low"]

    if coverage == "partial":
        score -= penalties["coverage_partial"]
    elif coverage == "sparse":
        score -= penalties["coverage_sparse"]

    return round(max(0.0, min(1.0, score)), 2)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def classify_nutrition_state(
    nutrition_signals: dict[str, Any],
    thresholds: Optional[dict[str, Any]] = None,
) -> ClassifiedNutritionState:
    """Classify today's accepted nutrition row into bands, status, score.

    Args:
        nutrition_signals: dict bundling the nutrition-domain inputs.
            Recognised keys described in module docstring. All keys are
            optional; an absent ``today_row`` propagates as
            ``insufficient`` coverage and ``unknown`` status/score.
        thresholds: optional pre-loaded config dict. If None, loads via
            ``core.config.load_thresholds()``.

    Returns:
        ``ClassifiedNutritionState``. ``uncertainty`` is dedup'd + sorted.
    """

    t = thresholds if thresholds is not None else load_thresholds()
    uncertainty: list[str] = []

    # v0.1.15 W-D arm-1: partial-day suppression. When the W-A signals
    # indicate today's intake is partial-day AND no nutrition target
    # covers today, refuse to classify rather than misclassifying the
    # partial intake against the config-baseline target. This is a
    # named-incomplete fix per PLAN §4 risk 4: arm-1 covers no-target
    # only; arm-2 (end-of-day projection when target IS present)
    # defers to v0.1.17. Backwards-compat: when either signal is
    # absent (the pre-W-D call shape), suppression doesn't fire.
    is_partial_day = nutrition_signals.get("is_partial_day")
    target_status = nutrition_signals.get("target_status")
    if (
        is_partial_day is True
        and target_status in ("absent", "unavailable")
    ):
        return ClassifiedNutritionState(
            calorie_balance_band="unknown",
            protein_sufficiency_band="unknown",
            hydration_band="unknown",
            micronutrient_coverage="unavailable_at_source",
            coverage_band="insufficient",
            nutrition_status="insufficient_data",
            nutrition_score=None,
            calorie_deficit_kcal=None,
            protein_ratio=None,
            hydration_ratio=None,
            derivation_path=(nutrition_signals.get("today_row") or {}).get(
                "derivation_path"
            ),
            uncertainty=("partial_day_no_target",),
        )

    today_row: Optional[dict[str, Any]] = nutrition_signals.get("today_row")
    targets = t["classify"]["nutrition"]["targets"]
    calorie_target = coerce_float(
        targets["calorie_target_kcal"],
        name="classify.nutrition.targets.calorie_target_kcal",
    )
    protein_target = coerce_float(
        targets["protein_target_g"],
        name="classify.nutrition.targets.protein_target_g",
    )
    hydration_target = coerce_float(
        targets["hydration_target_l"],
        name="classify.nutrition.targets.hydration_target_l",
    )

    # Derived intermediates.
    calorie_deficit: Optional[float] = None
    protein_ratio: Optional[float] = None
    hydration_ratio: Optional[float] = None
    derivation_path: Optional[str] = None

    if today_row is not None:
        derivation_path = today_row.get("derivation_path")
        calories = today_row.get("calories")
        protein_g = today_row.get("protein_g")
        hydration_l = today_row.get("hydration_l")

        if calories is not None:
            calorie_deficit = calorie_target - float(calories)
        if protein_g is not None and protein_target > 0:
            protein_ratio = float(protein_g) / protein_target
        if hydration_l is not None and hydration_target > 0:
            hydration_ratio = float(hydration_l) / hydration_target

    # W-D arm-2 (v0.1.17 §2.I): when partial-day intake AND a target
    # exists, project end-of-day macros + drive band classification
    # against the projection rather than the raw partial intake.
    # Default mode is "target_anchored" (the projection IS the target):
    # the user is assumed to close the gap by EOD, so calorie_deficit
    # collapses to 0 and protein_ratio to 1.0. This avoids the
    # false-deficit cascade the v0.1.15 W-D arm-1 fallback handles
    # only by suppressing classification entirely.
    projection_mode = (
        t.get("classify", {}).get("nutrition", {}).get("projection_mode")
    )
    is_partial_day = nutrition_signals.get("is_partial_day")
    target_status = nutrition_signals.get("target_status")
    arm2_active = (
        is_partial_day is True
        and target_status == "present"
        and projection_mode in ("target_anchored", "linear_extrapolation")
    )

    projected_eod_kcal: Optional[float] = None
    projected_eod_protein_g: Optional[float] = None
    projected_eod_carbs_g: Optional[float] = None
    projected_eod_fat_g: Optional[float] = None

    if arm2_active:
        targets_block = t["classify"]["nutrition"]["targets"]
        target_carbs = targets_block.get("carbs_target_g")
        target_fat = targets_block.get("fat_target_g")
        if projection_mode == "target_anchored":
            # Target IS the projection: user closes the gap by EOD.
            projected_eod_kcal = float(calorie_target)
            projected_eod_protein_g = float(protein_target)
            if target_carbs is not None:
                projected_eod_carbs_g = float(target_carbs)
            if target_fat is not None:
                projected_eod_fat_g = float(target_fat)
            # Re-derive deficit + ratio against the projection so
            # downstream band classifiers see the closed-gap state.
            calorie_deficit = 0.0
            protein_ratio = 1.0 if protein_target > 0 else None
        elif projection_mode == "linear_extrapolation":
            # Reachable via threshold override; not the v1 default.
            # Linear-extrapolate: scale current intake to a 24h window.
            from datetime import datetime as _dt
            now_local = nutrition_signals.get("now_local")
            if now_local is None:
                fraction = 0.5  # defensive midday fallback
            elif isinstance(now_local, _dt):
                fraction = max(
                    1.0 / 24.0,
                    (now_local.hour + now_local.minute / 60.0) / 24.0,
                )
            else:
                fraction = 0.5
            if calories is not None:
                projected_eod_kcal = round(float(calories) / fraction, 1)
                calorie_deficit = calorie_target - projected_eod_kcal
            if protein_g is not None:
                projected_eod_protein_g = round(
                    float(protein_g) / fraction, 1
                )
                if protein_target > 0:
                    protein_ratio = projected_eod_protein_g / protein_target
            # Carbs/fat: emit projection if target present + intake
            # tracked. v1 doesn't band-classify these.
            today_carbs = (today_row or {}).get("carbs_g")
            today_fat = (today_row or {}).get("fat_g")
            if today_carbs is not None and target_carbs is not None:
                projected_eod_carbs_g = round(
                    float(today_carbs) / fraction, 1
                )
            if today_fat is not None and target_fat is not None:
                projected_eod_fat_g = round(float(today_fat) / fraction, 1)

    coverage_band, u = _classify_coverage(today_row)
    uncertainty.extend(u)

    calorie_band, u = _classify_calorie_balance(calorie_deficit, t)
    uncertainty.extend(u)

    protein_band, u = _classify_protein_sufficiency(protein_ratio, t)
    uncertainty.extend(u)

    hydration_band, u = _classify_hydration(hydration_ratio, t)
    uncertainty.extend(u)

    micronutrient_band, u = _classify_micronutrient_coverage(derivation_path)
    uncertainty.extend(u)

    status = _nutrition_status(calorie_band, protein_band, hydration_band, coverage_band)
    score = _nutrition_score(calorie_band, protein_band, hydration_band, coverage_band, t)

    goal_domain = nutrition_signals.get("goal_domain")
    if goal_domain == "resistance_training":
        uncertainty.append("goal_domain_is_resistance_training")

    return ClassifiedNutritionState(
        calorie_balance_band=calorie_band,
        protein_sufficiency_band=protein_band,
        hydration_band=hydration_band,
        micronutrient_coverage=micronutrient_band,
        coverage_band=coverage_band,
        nutrition_status=status,
        nutrition_score=score,
        calorie_deficit_kcal=(
            round(calorie_deficit, 1) if calorie_deficit is not None else None
        ),
        protein_ratio=(
            round(protein_ratio, 3) if protein_ratio is not None else None
        ),
        hydration_ratio=(
            round(hydration_ratio, 3) if hydration_ratio is not None else None
        ),
        derivation_path=derivation_path,
        uncertainty=tuple(sorted(set(uncertainty))),
        projected_eod_kcal=projected_eod_kcal,
        projected_eod_protein_g=projected_eod_protein_g,
        projected_eod_carbs_g=projected_eod_carbs_g,
        projected_eod_fat_g=projected_eod_fat_g,
    )
