"""Caveat-token → plain-English translations (v0.2.0 W52).

Closes W-EXPLAIN-UX-CARRY obligation #4 (P0) from
``hai/reporting/docs/archive/cycle_artifacts/explain_ux_review_2026_05.md``:

  > Each caveat token has a code-owned plain-English translation.
  > Weekly-review prose surfaces the translation, not the token.

Caveat tokens (a.k.a. ``reason_token`` values in domain proposals
and X-rule firings) are short snake_case identifiers the runtime
emits to mark *why* a recommendation was bounded or escalated.
Tokens are stable, machine-readable, and useful for the audit
chain — but they are illegible to a non-maintainer reader.

The registry below translates every token currently emitted by the
six domain ``policy.py`` modules and the X-rule engine. New tokens
must land here before they ship to user-facing prose surfaces; the
test suite asserts coverage against the runtime's emitted token set
so silent omissions surface at PR-review time, not at user read time.

Obligation hook: weekly-review prose contains zero raw caveat-token
strings (asserted in ``test_review_weekly.py`` once the prose
builder runs).
"""

from __future__ import annotations

from typing import Optional


# Per-domain ``reason_token`` values emitted by the runtime as of
# v0.2.0. Sourced from grepping ``"reason_token":`` across
# ``hai/src/health_agent_infra/domains/`` and
# ``hai/src/health_agent_infra/core/synthesis*.py``. Each entry maps to
# a plain-English phrase that fits naturally inside a prose sentence.
#
# Format convention: lowercase, no leading article, no terminal
# punctuation. Authors compose a sentence around the phrase rather
# than substituting it as a stand-alone string.
_DOMAIN_TOKENS: dict[str, str] = {
    # Recovery domain (resting-HR multi-day spike).
    "resting_hr_spike_3_days_running": (
        "your resting heart rate has been elevated for 3 days running"
    ),

    # Running domain (ACWR-driven escalation).
    "acwr_spike": (
        "your acute-to-chronic workload ratio has spiked above the "
        "fatigue threshold"
    ),

    # Sleep domain (multi-day chronic deprivation).
    "chronic_deprivation_detected": (
        "you've shown sustained sleep deprivation across the trailing "
        "window"
    ),

    # Stress domain (sustained very-high stress days).
    "sustained_very_high_stress": (
        "your day-stress score has held at very-high levels across "
        "the trailing window"
    ),

    # Strength domain (single-day volume spike).
    "volume_spike_detected": (
        "yesterday's resistance-training volume spiked above the "
        "trailing baseline"
    ),

    # Nutrition domain (single-day extreme deficiency).
    "extreme_deficiency_detected": (
        "today's logged nutrition shows extreme calorie or protein "
        "deficiency"
    ),
}


# X-rule firing tokens. Tier names ("soften", "block",
# "cap_confidence", "adjust", "restructure") are NOT translated here —
# the prose layer surfaces tier as the verb of the sentence
# ("softened", "blocked"), keeping the token solely for the *why*.
#
# Public names for X-rule IDs themselves (``X1a`` etc.) live in
# ``core/synthesis_policy.public_name_for`` per W-EXPLAIN-UX-CARRY
# obligation #1; this module is the *caveat-reason* layer underneath.
_X_RULE_TOKENS: dict[str, str] = {
    "x1a_sleep_debt_trigger": (
        "your sleep debt landed in the moderate band"
    ),
    "x1b_sleep_debt_elevated": (
        "your sleep debt landed in the elevated band"
    ),
    "x3a_acwr_elevated": (
        "your acute-to-chronic workload ratio landed in the elevated "
        "band"
    ),
    "x3b_acwr_spike": (
        "your acute-to-chronic workload ratio landed in the spike band"
    ),
    "x4_heavy_lower_body_yesterday": (
        "yesterday's lower-body resistance training was heavy enough "
        "to argue against hard running today"
    ),
    "x5_endurance_fatigue_yesterday": (
        "yesterday's endurance session was hard enough to argue "
        "against heavy lower-body strength today"
    ),
    "x6a_body_battery_low": (
        "your body-battery is in the low band"
    ),
    "x6b_body_battery_critical": (
        "your body-battery is in the critical band"
    ),
    "x9_training_intensity_bump": (
        "the supporting evidence is strong enough to bump training "
        "intensity slightly"
    ),
}


# X2 nutrition tokens follow a templated shape: x2_nutrition_<reason>.
# The runtime emits the suffix as a band name (e.g., `high_deficit`,
# `protein_gap`); the translation function strips the prefix and
# delegates to a band-name lookup so we don't enumerate every
# permutation here.
_X2_NUTRITION_BANDS: dict[str, str] = {
    "moderate_deficit": "your day-calorie balance is in moderate deficit",
    "high_deficit": "your day-calorie balance is in high deficit",
    "protein_gap": "your day-protein intake is short of target",
}


# Sleep / recovery / stress / strength / running policy band-driver
# tokens that pass through `reason_token` directly when
# ``policy.py`` cites a band as the driver of an action. These are
# *band names* the prose layer translates inline.
_BAND_TOKENS: dict[str, str] = {
    # Sleep
    "sleep_quality_band": "your sleep-quality band",
    "sleep_efficiency_band": "your sleep-efficiency band",
    "sleep_timing_consistency_band": "your sleep-timing-consistency band",
    "sleep_debt_band": "your sleep-debt band",
    "impaired_sleep_status": "your sleep status is impaired",
    "impaired_recovery_with_hard_plan": (
        "your recovery is impaired and the plan called for a hard session"
    ),
    "conditional_readiness": "your recovery readiness is conditional",
    "hold_status_avoid_impact": (
        "your recovery is on hold and impact training is contraindicated"
    ),

    # Stress
    "garmin_stress_band": "your day-stress band",
    "manual_stress_band": "your subjective-stress band",
    "body_battery_trend_band": "your body-battery trend band",

    # Nutrition
    "calorie_balance_band": "your calorie-balance band",
    "protein_sufficiency_band": "your protein-sufficiency band",
}


def translate_caveat(token: str) -> str:
    """Return the plain-English translation for a caveat token.

    Lookup order:
      1. Exact match in :data:`_DOMAIN_TOKENS` (per-domain
         ``reason_token``).
      2. Exact match in :data:`_X_RULE_TOKENS` (X-rule firing tokens).
      3. ``x2_nutrition_<band>`` template — strip prefix, look up band.
      4. Exact match in :data:`_BAND_TOKENS` (band-driver tokens).
      5. ``fatigued_group:<group>`` template — strip prefix.
      6. Default fallback: humanise the snake_case token. The fallback
         always returns a non-empty string so the prose builder can
         substitute without conditional branching at every site.

    The function never returns the raw token, never returns None, and
    never returns an empty string — those would defeat the obligation
    hook (no caveat-token string in weekly-review prose).
    """

    if not token or not isinstance(token, str):
        return "(no rationale recorded)"

    if token in _DOMAIN_TOKENS:
        return _DOMAIN_TOKENS[token]

    if token in _X_RULE_TOKENS:
        return _X_RULE_TOKENS[token]

    # X2 nutrition template.
    if token.startswith("x2_nutrition_"):
        band = token[len("x2_nutrition_"):]
        if band in _X2_NUTRITION_BANDS:
            return _X2_NUTRITION_BANDS[band]

    if token in _BAND_TOKENS:
        return _BAND_TOKENS[token]

    # Fatigued-group template ("fatigued_group:quads").
    if token.startswith("fatigued_group:"):
        group = token.split(":", 1)[1].replace("_", " ")
        return f"your {group} muscle group is in the fatigued band"

    # Default: humanise the snake_case token.
    humanised = token.replace("_", " ").strip()
    return f"the rule cited \"{humanised}\""


def known_token_keys() -> set[str]:
    """Return every token the registry translates with a non-default
    answer. Used by the test suite to assert coverage parity with the
    runtime's actually-emitted token set.
    """

    return (
        set(_DOMAIN_TOKENS.keys())
        | set(_X_RULE_TOKENS.keys())
        | {f"x2_nutrition_{band}" for band in _X2_NUTRITION_BANDS}
        | set(_BAND_TOKENS.keys())
    )


def is_registered_token(token: Optional[str]) -> bool:
    """``True`` if the token has an explicit registry entry (i.e.
    falls in lookup steps 1-4 above), ``False`` if it would hit the
    fallback. Lets tests detect silent default-fallback drift when a
    new runtime token ships without a registry entry.
    """

    if not token:
        return False
    if token in _DOMAIN_TOKENS or token in _X_RULE_TOKENS:
        return True
    if token.startswith("x2_nutrition_"):
        band = token[len("x2_nutrition_"):]
        return band in _X2_NUTRITION_BANDS
    if token in _BAND_TOKENS:
        return True
    if token.startswith("fatigued_group:"):
        return True
    return False
