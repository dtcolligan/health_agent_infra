"""Runtime configuration: default thresholds + user TOML override.

Thresholds live in two places:

1. `DEFAULT_THRESHOLDS` — ship-with-the-package baseline. Source of truth
   for every numeric band boundary, rule trigger, and readiness-score
   penalty. Namespaced as ``classify.<domain>.<band>`` and
   ``synthesis.x_rules.<rule>``.

2. `thresholds.toml` in the user config directory (per platformdirs) —
   optional user override. Deep-merged over defaults at load time.

`load_thresholds()` returns the merged effective config. Callers should
not mutate the result; it is fresh per call but `DEFAULT_THRESHOLDS` is a
module-level singleton used by reference inside the merge.

Design notes:

- Keys that don't exist in user TOML fall through to defaults. Keys that
  do exist replace the default leaf (not the enclosing dict). Lists are
  treated as leaves — a user list replaces the default list wholesale.
- Malformed TOML raises `ConfigError` with the file path; callers surface
  it agent-parseably on stderr and exit non-zero.
- Reading via stdlib `tomllib`. Writing is via a hand-authored scaffold
  template so comments survive; no TOML-writer dep needed.
"""

from __future__ import annotations

import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional

from platformdirs import user_config_dir


class ConfigError(RuntimeError):
    """Raised on malformed user thresholds.toml."""


APP_NAME = "hai"
CONFIG_FILENAME = "thresholds.toml"


DEFAULT_THRESHOLDS: dict[str, Any] = {
    "classify": {
        "running": {
            "weekly_mileage_trend_band": {
                # Boundaries on weekly_mileage_ratio (current 7d / trailing
                # 28d-week-mean baseline). A value at the boundary lands in
                # the higher band.
                "very_low_max_ratio": 0.5,
                "low_max_ratio": 0.8,
                "moderate_max_ratio": 1.2,
                "high_max_ratio": 1.5,
            },
            "hard_session_load_band": {
                # Boundaries on recent_hard_session_count_7d.
                "light_max_count": 1,
                "moderate_max_count": 2,
                # heavy = anything strictly greater than moderate_max_count.
            },
            "freshness_band": {
                # Boundaries on acwr_ratio. fatigued/overreaching boundaries
                # are aligned with X3a (1.3-1.5 → soften) and X3b (≥1.5 →
                # block) so synthesis can read the band directly.
                "fresh_max_ratio": 0.8,
                "neutral_max_ratio": 1.3,
                "fatigued_max_ratio": 1.5,
            },
            "recovery_adjacent_band": {
                "favourable_min_training_readiness_pct": 70,
                "compromised_max_training_readiness_pct": 40,
            },
            "readiness_score_penalty": {
                # Negative values are bonuses (raise the score).
                "mileage_trend_high": 0.05,
                "mileage_trend_very_high": 0.15,
                "hard_session_load_moderate": 0.05,
                "hard_session_load_heavy": 0.15,
                "freshness_fresh": -0.02,
                "freshness_fatigued": 0.15,
                "freshness_overreaching": 0.30,
                "recovery_adjacent_favourable": -0.05,
                "recovery_adjacent_compromised": 0.20,
            },
        },
        "stress": {
            # Garmin 0-100 all-day-stress band boundaries. A value AT a
            # boundary lands in the higher band. These mirror the
            # synthesis.x_rules.x7 thresholds so the Phase-3-step-5 X7
            # rewire (which will prefer the domain-computed band) is a
            # mechanical flip — stress.classify owns the band, X7 reads
            # it without re-thresholding.
            "garmin_stress_band": {
                "moderate_min_score": 40,
                "high_min_score": 60,
                "very_high_min_score": 80,
            },
            # Manual subjective 1-5 score band boundaries. A value AT a
            # boundary lands in the higher band.
            "manual_stress_band": {
                "moderate_min_score": 3,
                "high_min_score": 4,
                "very_high_min_score": 5,
            },
            # Body-battery end-of-day day-over-day trend band boundaries
            # on ``delta = today_bb - prev_day_bb``. "depleted" fires on
            # absolute bb below ``depleted_max_bb`` regardless of delta.
            "body_battery_trend_band": {
                "depleted_max_bb": 20,
                "declining_max_delta": -10,
                "steady_max_delta": 10,
            },
            # Additive penalties feeding the composite stress_score;
            # negative values are bonuses (raise the score).
            "stress_score_penalty": {
                "garmin_moderate": 0.10,
                "garmin_high": 0.20,
                "garmin_very_high": 0.30,
                "manual_moderate": 0.05,
                "manual_high": 0.15,
                "manual_very_high": 0.25,
                "body_battery_declining": 0.10,
                "body_battery_depleted": 0.20,
                "body_battery_improving": -0.05,
            },
        },
        "sleep": {
            # Aligned with recovery.sleep_debt_band so the Phase-3-step-5
            # X1 rewire (X1a moderate → soften; X1b elevated → block) can
            # flip from reading the recovery classifier to reading the
            # sleep classifier without re-thresholding.
            "sleep_debt_band": {
                "none_min_hours": 7.5,
                "mild_min_hours": 7.0,
                "moderate_min_hours": 6.0,
            },
            # Boundaries on Garmin's 0-100 sleep_score_overall. A value
            # AT a boundary lands in the higher band.
            "sleep_quality_band": {
                "excellent_min_score": 90,
                "good_min_score": 80,
                "fair_min_score": 60,
            },
            # Boundaries on sleep_start_variance_minutes (stddev of
            # sleep_start_ts across recent nights). v1.1 enrichment;
            # v1 production sees None here and classifies as "unknown".
            "sleep_timing_consistency_band": {
                "consistent_max_stddev_min": 30,
                "variable_max_stddev_min": 60,
            },
            # Boundaries on efficiency_pct = asleep_min /
            # (asleep_min + awake_min) * 100.
            "sleep_efficiency_band": {
                "excellent_min_pct": 90,
                "good_min_pct": 85,
                "fair_min_pct": 75,
            },
            # Additive penalties; negative values are bonuses.
            "sleep_score_penalty": {
                "debt_mild": 0.05,
                "debt_moderate": 0.15,
                "debt_elevated": 0.25,
                "quality_excellent": -0.02,
                "quality_good": 0.0,
                "quality_fair": 0.10,
                "quality_poor": 0.20,
                "efficiency_excellent": -0.02,
                "efficiency_fair": 0.05,
                "efficiency_poor": 0.15,
                "consistency_variable": 0.02,
                "consistency_highly_variable": 0.08,
            },
        },
        "strength": {
            # recent_volume_band fires on
            # volume_ratio = last_7d_kg_reps / week_mean(last_28d_kg_reps).
            # A value AT a boundary lands in the higher band. Aligned with
            # the running weekly_mileage_trend_band naming for cross-domain
            # reasoning clarity. very_high is 1.5× baseline — this is the
            # volume-spike threshold R-rule escalates on, mirroring the
            # running R-acwr-spike 1.5 threshold.
            "recent_volume_band": {
                "very_low_max_ratio": 0.5,
                "low_max_ratio": 0.8,
                "moderate_max_ratio": 1.2,
                "high_max_ratio": 1.5,
            },
            # Per-muscle-group freshness based on days_since_heavy_per_group.
            # X4 (yesterday's heavy lower body caps running) and X5
            # (yesterday's long run caps lower-body strength) read this
            # directly. "fatigued" fires on 0 days (hit yesterday or today);
            # "recent" on 1-2 days; "fresh" on ≥3 days. None history → unknown.
            "freshness_band": {
                "fresh_min_days_since_heavy": 3,
                "recent_max_days_since_heavy": 2,
            },
            # Coverage on sessions_last_28d. Below insufficient_max = block.
            # Between insufficient_max and sparse_max = sparse (cap confidence).
            # Between sparse_max and partial_max = partial (allow).
            # >= partial_max = full (allow).
            "coverage_band": {
                "insufficient_max_sessions_28d": 2,
                "sparse_max_sessions_28d": 4,
                "partial_max_sessions_28d": 8,
            },
            # Additive penalties on the strength_score composite; negative
            # values are bonuses (raise the score).
            "strength_score_penalty": {
                "recent_volume_very_high": 0.20,
                "recent_volume_very_low": 0.10,
                "coverage_sparse": 0.15,
                "coverage_partial": 0.05,
                "unmatched_exercise_present": 0.05,
            },
        },
        "nutrition": {
            # Phase 5 step 2 — macros-only v1 targets. Single default target
            # set per Phase 2.5 retrieval-gate outcome: meal-level + goal-
            # aware micronutrient targeting defer to a post-v1 release.
            # Users override values wholesale via thresholds.toml; a future
            # goals-domain expansion may add a goal→target mapping on top
            # of (not instead of) these defaults.
            "targets": {
                "calorie_target_kcal": 2400.0,
                "protein_target_g": 140.0,
                "hydration_target_l": 2.5,
            },
            # calorie_balance_band fires on absolute_deficit_kcal =
            # target - actual. A negative value (surplus) lands in
            # "surplus". A value AT a boundary lands in the higher
            # (more-deficit) band. Aligned with X2's 500-kcal deficit
            # trigger: "high_deficit" begins at exactly the X2 threshold
            # so the X-rule's read is the same threshold the domain
            # classifier already named.
            "calorie_balance_band": {
                "mild_deficit_min_kcal": 100.0,
                "moderate_deficit_min_kcal": 300.0,
                "high_deficit_min_kcal": 500.0,
                "surplus_min_kcal": 300.0,     # target+300 or more = surplus
            },
            # protein_sufficiency_band fires on protein_ratio =
            # protein_g_actual / protein_g_target. Aligned with X2's
            # 0.7 threshold — "very_low" begins at exactly the X2 trigger
            # so the X-rule's read is the same threshold the domain
            # classifier already named.
            "protein_sufficiency_band": {
                "very_low_max_ratio": 0.7,
                "low_max_ratio": 1.0,
            },
            # hydration_band fires on hydration_ratio =
            # hydration_l_actual / hydration_l_target.
            "hydration_band": {
                "low_max_ratio": 0.75,
            },
            # Additive penalties feeding the composite nutrition_score;
            # negative values are bonuses (raise the score).
            "nutrition_score_penalty": {
                "calorie_mild_deficit": 0.05,
                "calorie_moderate_deficit": 0.15,
                "calorie_high_deficit": 0.30,
                "calorie_surplus": 0.10,
                "protein_low": 0.10,
                "protein_very_low": 0.25,
                "hydration_low": 0.05,
                "coverage_partial": 0.05,
                "coverage_sparse": 0.15,
            },
        },
        "recovery": {
            "sleep_debt_band": {
                "none_min_hours": 7.5,
                "mild_min_hours": 7.0,
                "moderate_min_hours": 6.0,
            },
            "resting_hr_band": {
                "well_above_ratio": 1.15,
                "above_ratio": 1.05,
                "at_lower_ratio": 0.95,
            },
            "hrv_band": {
                "below_max_ratio": 0.95,
                "above_min_ratio": 1.02,
                "well_above_min_ratio": 1.10,
            },
            "training_load_band": {
                "spike_ratio": 1.4,
                "high_ratio": 1.1,
                "moderate_ratio": 0.7,
                "absolute_fallback": {
                    "high_load": 500,
                    "moderate_load": 200,
                },
            },
            "readiness_score_penalty": {
                "sleep_debt_mild": 0.05,
                "sleep_debt_moderate": 0.15,
                "sleep_debt_elevated": 0.25,
                "soreness_moderate": 0.10,
                "soreness_high": 0.20,
                "resting_hr_above": 0.10,
                "resting_hr_well_above": 0.20,
                "resting_hr_below": -0.02,
                "hrv_below": 0.15,
                "hrv_above_or_well_above": -0.05,
                "load_high": 0.05,
                "load_spike": 0.15,
            },
        },
    },
    "policy": {
        "sleep": {
            # R-chronic-deprivation: escalate when there have been this
            # many or more nights of <chronic_deprivation_hours sleep in
            # the trailing 7-night window (today included). Forces
            # ``sleep_debt_repayment_day`` as the remedial action; the
            # policy_decision tier records the ``escalate`` severity.
            "r_chronic_deprivation_nights": 4,
            "r_chronic_deprivation_hours": 6.0,
        },
        "recovery": {
            "r6_resting_hr_spike_days_threshold": 3,
        },
        "stress": {
            # R-sustained-very-high-stress: escalate when Garmin's
            # 0-100 all-day-stress has been at or above the high-band
            # threshold for this many consecutive days (today included).
            # Forces ``escalate_for_user_review`` as the remedial action;
            # the policy_decision tier records the ``escalate`` severity.
            "r_sustained_stress_days": 5,
            "r_sustained_stress_min_score": 60,
        },
        "running": {
            # Aligned with X3b (≥1.5 → block any hard session). The R-rule
            # forces escalate_for_user_review at the same threshold so the
            # running domain has its own forced action even when synthesis
            # is not run.
            "r_acwr_spike_min_ratio": 1.5,
        },
        "strength": {
            # R-volume-spike: escalate when the 7d-vs-28d-week-mean
            # volume ratio crosses this threshold. Forces
            # ``escalate_for_user_review`` as the remedial action; mirrors
            # the running R-acwr-spike threshold so cross-domain
            # escalations coincide at the same volume signal.
            "r_volume_spike_min_ratio": 1.5,
        },
        "nutrition": {
            # Phase 5 step 2 — macros-only v1. R-extreme-deficiency:
            # escalate when BOTH a high calorie deficit (≥500 kcal) AND
            # very-low protein (<70% of target) fire on the same day.
            # Either alone is softened via the calorie / protein band
            # verdict; the combination is the overreaching-deficit
            # signal worth a user review rather than a silent downgrade.
            # The individual thresholds match X2's trigger values so the
            # R-rule and the X-rule read the same numeric boundaries.
            "r_extreme_deficiency_min_calorie_deficit_kcal": 500.0,
            "r_extreme_deficiency_max_protein_ratio": 0.7,
        },
    },
    "synthesis": {
        "x_rules": {
            "x1a": {"sleep_debt_trigger_band": "moderate"},
            "x1b": {"sleep_debt_trigger_band": "elevated"},
            # Phase 5 step 4. X2 softens hard strength / recovery
            # proposals when today's nutrition shows either a high
            # calorie deficit (≥500 kcal absolute) OR protein below
            # 70% of target. Thresholds mirror the nutrition domain's
            # calorie_balance_band / protein_sufficiency_band cutoffs
            # so the X-rule reads the same numeric boundaries the
            # classifier named.
            "x2": {
                "deficit_kcal_min": 500.0,
                "protein_ratio_max": 0.7,
            },
            "x3a": {"acwr_ratio_lower": 1.3, "acwr_ratio_upper": 1.5},
            "x3b": {"acwr_ratio_min": 1.5},
            # Phase 4 step 5. X4 triggers when yesterday's strength
            # volume on any of {quads, hamstrings, glutes} met this
            # threshold — "heavy lower body yesterday" argues against
            # running intervals/tempo today. 2000 kg·reps is roughly
            # a 4×5 set at 100 kg (or 3×8 at 85 kg) per group.
            "x4": {"heavy_lower_body_min_volume": 2000.0},
            # X5 triggers when yesterday's running row had either
            # ≥ vigorous_intensity_min (hard intervals/tempo) OR
            # ≥ long_run_min_duration_s (75 minutes = 4500 s). Strong
            # endurance stimulus yesterday argues against heavy
            # lower-body strength today.
            "x5": {
                "vigorous_intensity_min": 20,
                "long_run_min_duration_s": 4500,
            },
            "x6a": {"body_battery_max": 30},
            "x6b": {"body_battery_max": 15},
            # Phase 3 will add a dedicated stress classifier; until then,
            # X7 locally bands Garmin's 0-100 ``all_day_stress`` by these
            # numeric thresholds so the rule is evaluable pre-Phase-3.
            "x7": {
                "stress_trigger_bands": ["high", "very_high"],
                "moderate_min_score": 40,
                "high_min_score": 60,
                "very_high_min_score": 80,
            },
        },
    },
}


def user_config_path() -> Path:
    """Platform-appropriate path to the user's thresholds.toml.

    macOS: ~/Library/Application Support/hai/thresholds.toml
    Linux: ~/.config/hai/thresholds.toml (XDG)
    Windows: %APPDATA%/hai/thresholds.toml
    """

    return Path(user_config_dir(APP_NAME)) / CONFIG_FILENAME


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge `override` into a deep copy of `base`.

    Mutates only the copy. Dicts recurse; scalars and lists replace.
    """

    out = deepcopy(base)
    for key, value in override.items():
        if (
            key in out
            and isinstance(out[key], dict)
            and isinstance(value, dict)
        ):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = deepcopy(value)
    return out


def load_thresholds(path: Optional[Path] = None) -> dict[str, Any]:
    """Return merged thresholds: defaults + user TOML (if present).

    Args:
        path: explicit path to a thresholds.toml. If None, uses
              `user_config_path()`. If the file does not exist, the
              defaults are returned unchanged.

    Raises:
        ConfigError: the TOML was present but malformed.
    """

    effective_path = path if path is not None else user_config_path()
    if not effective_path.exists():
        return deepcopy(DEFAULT_THRESHOLDS)

    try:
        with effective_path.open("rb") as fh:
            user_overrides = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(
            f"malformed thresholds TOML at {effective_path}: {exc}"
        ) from exc

    return _deep_merge(DEFAULT_THRESHOLDS, user_overrides)


SCAFFOLD_THRESHOLDS_TOML = """\
# Health Agent Infra — user threshold overrides.
#
# Every value below matches the package default. Delete any section you
# don't want to override; only keys you keep will replace defaults. The
# runtime deep-merges this file on top of `DEFAULT_THRESHOLDS` in
# `health_agent_infra.core.config`.
#
# Sections:
#   [classify.<domain>.<band>]  — band boundaries used by classify.py
#   [policy.<domain>]           — R-rule thresholds used by policy.py
#   [synthesis.x_rules.<id>]    — X-rule triggers used by the synthesis layer

# ---------------------------------------------------------------------------
# Recovery domain — classification
# ---------------------------------------------------------------------------

[classify.recovery.sleep_debt_band]
none_min_hours      = 7.5
mild_min_hours      = 7.0
moderate_min_hours  = 6.0

[classify.recovery.resting_hr_band]
# Ratio = resting_hr / baseline. Higher = worse.
well_above_ratio = 1.15
above_ratio      = 1.05
at_lower_ratio   = 0.95

[classify.recovery.hrv_band]
# Ratio = hrv_ms / baseline. Higher = better.
below_max_ratio      = 0.95
above_min_ratio      = 1.02
well_above_min_ratio = 1.10

[classify.recovery.training_load_band]
# Ratio = trailing_7d_training_load / baseline.
spike_ratio     = 1.4
high_ratio      = 1.1
moderate_ratio  = 0.7

[classify.recovery.training_load_band.absolute_fallback]
# Used when baseline is missing but trailing load is present.
high_load     = 500
moderate_load = 200

[classify.recovery.readiness_score_penalty]
# Additive penalties; negative values add to the score.
sleep_debt_mild         = 0.05
sleep_debt_moderate     = 0.15
sleep_debt_elevated     = 0.25
soreness_moderate       = 0.10
soreness_high           = 0.20
resting_hr_above        = 0.10
resting_hr_well_above   = 0.20
resting_hr_below        = -0.02
hrv_below               = 0.15
hrv_above_or_well_above = -0.05
load_high               = 0.05
load_spike              = 0.15

# ---------------------------------------------------------------------------
# Recovery domain — policy rules
# ---------------------------------------------------------------------------

[policy.recovery]
# R6: escalate if resting_hr has been >=1.15 baseline for this many consecutive days.
r6_resting_hr_spike_days_threshold = 3

# ---------------------------------------------------------------------------
# Stress domain — classification (Phase 3)
# ---------------------------------------------------------------------------

[classify.stress.garmin_stress_band]
# Boundaries on Garmin's 0-100 all-day-stress score. A value AT a boundary
# lands in the higher band. Mirrors the synthesis.x_rules.x7 thresholds so
# the Phase-3-step-5 X7 rewire is mechanical.
moderate_min_score  = 40
high_min_score      = 60
very_high_min_score = 80

[classify.stress.manual_stress_band]
# Boundaries on the user's subjective 1-5 score. A value AT a boundary
# lands in the higher band.
moderate_min_score  = 3
high_min_score      = 4
very_high_min_score = 5

[classify.stress.body_battery_trend_band]
# Boundaries on body-battery end-of-day trend.
# depleted_max_bb: absolute body_battery at/under this lands in "depleted"
# regardless of delta. Otherwise the delta (today_bb - prev_day_bb) drives
# the band: delta <= declining_max_delta -> "declining"; delta strictly
# between declining and steady thresholds -> "steady"; delta > steady
# threshold -> "improving".
depleted_max_bb       = 20
declining_max_delta   = -10
steady_max_delta      = 10

[classify.stress.stress_score_penalty]
# Additive penalties; negative values are bonuses.
garmin_moderate          = 0.10
garmin_high              = 0.20
garmin_very_high         = 0.30
manual_moderate          = 0.05
manual_high              = 0.15
manual_very_high         = 0.25
body_battery_declining   = 0.10
body_battery_depleted    = 0.20
body_battery_improving   = -0.05

# ---------------------------------------------------------------------------
# Stress domain — policy rules
# ---------------------------------------------------------------------------

[policy.stress]
# R-sustained-very-high-stress: escalate if Garmin's all-day-stress has been
# at or above r_sustained_stress_min_score for r_sustained_stress_days
# consecutive days (today included). Forces escalate_for_user_review.
r_sustained_stress_days      = 5
r_sustained_stress_min_score = 60

# ---------------------------------------------------------------------------
# Running domain — classification (Phase 2)
# ---------------------------------------------------------------------------

[classify.running.weekly_mileage_trend_band]
# Boundaries on weekly_mileage_ratio (current 7d / trailing 28d-week-mean
# baseline). A value AT a boundary lands in the higher band.
very_low_max_ratio = 0.5
low_max_ratio      = 0.8
moderate_max_ratio = 1.2
high_max_ratio     = 1.5

[classify.running.hard_session_load_band]
# Boundaries on count of days in the last 7 with vigorous-intensity activity
# >= 30 minutes. heavy = strictly greater than moderate_max_count.
light_max_count    = 1
moderate_max_count = 2

[classify.running.freshness_band]
# Boundaries on acwr_ratio. fatigued/overreaching boundaries are aligned
# with the synthesis-layer X3a (1.3-1.5 -> soften) and X3b (>=1.5 -> block)
# rules so synthesis can read the band directly.
fresh_max_ratio    = 0.8
neutral_max_ratio  = 1.3
fatigued_max_ratio = 1.5

[classify.running.recovery_adjacent_band]
favourable_min_training_readiness_pct  = 70
compromised_max_training_readiness_pct = 40

[classify.running.readiness_score_penalty]
# Negative values are bonuses (raise the score).
mileage_trend_high           = 0.05
mileage_trend_very_high      = 0.15
hard_session_load_moderate   = 0.05
hard_session_load_heavy      = 0.15
freshness_fresh              = -0.02
freshness_fatigued           = 0.15
freshness_overreaching       = 0.30
recovery_adjacent_favourable = -0.05
recovery_adjacent_compromised = 0.20

# ---------------------------------------------------------------------------
# Running domain — policy rules
# ---------------------------------------------------------------------------

[policy.running]
# R-acwr-spike: escalate when ACWR is at or above this ratio. Aligned with
# X3b (>=1.5 -> block any hard session) so the running domain has its own
# forced action even when synthesis is not run.
r_acwr_spike_min_ratio = 1.5

# ---------------------------------------------------------------------------
# Synthesis layer — X-rule triggers
# ---------------------------------------------------------------------------

[synthesis.x_rules.x1a]
sleep_debt_trigger_band = "moderate"

[synthesis.x_rules.x1b]
sleep_debt_trigger_band = "elevated"

[synthesis.x_rules.x3a]
acwr_ratio_lower = 1.3
acwr_ratio_upper = 1.5

[synthesis.x_rules.x3b]
acwr_ratio_min = 1.5

[synthesis.x_rules.x6a]
body_battery_max = 30

[synthesis.x_rules.x6b]
body_battery_max = 15

[synthesis.x_rules.x7]
# Phase 3 will ship a dedicated stress classifier; until then, X7 bands
# Garmin's numeric all_day_stress score locally using these thresholds.
stress_trigger_bands = ["high", "very_high"]
moderate_min_score = 40
high_min_score     = 60
very_high_min_score = 80
"""


def scaffold_thresholds_toml() -> str:
    """Return the scaffolded thresholds.toml as a string.

    Used by `hai config init` to write a fresh user config file. Every
    value in the scaffold matches `DEFAULT_THRESHOLDS`; the file is
    immediately effective-equivalent to no config at all, so users can
    delete sections they don't want to override.
    """

    return SCAFFOLD_THRESHOLDS_TOML
