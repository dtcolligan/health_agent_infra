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
        "recovery": {
            "r6_resting_hr_spike_days_threshold": 3,
        },
    },
    "synthesis": {
        "x_rules": {
            "x1a": {"sleep_debt_trigger_band": "moderate"},
            "x1b": {"sleep_debt_trigger_band": "elevated"},
            "x3a": {"acwr_ratio_lower": 1.3, "acwr_ratio_upper": 1.5},
            "x3b": {"acwr_ratio_min": 1.5},
            "x6a": {"body_battery_max": 30},
            "x6b": {"body_battery_max": 15},
            "x7": {"stress_trigger_bands": ["high", "very_high"]},
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
stress_trigger_bands = ["high", "very_high"]
"""


def scaffold_thresholds_toml() -> str:
    """Return the scaffolded thresholds.toml as a string.

    Used by `hai config init` to write a fresh user config file. Every
    value in the scaffold matches `DEFAULT_THRESHOLDS`; the file is
    immediately effective-equivalent to no config at all, so users can
    delete sections they don't want to override.
    """

    return SCAFFOLD_THRESHOLDS_TOML
