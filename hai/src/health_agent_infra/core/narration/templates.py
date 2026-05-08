"""Per-domain templates + action classification for ``hai today``.

Per D3 §defer review_question improvements — each domain owns its own
defer template so the default "did you decide on a session yesterday?"
text no longer leaks into nutrition / stress / sleep.

Per D3 §Output shape per domain — action-class emojis give a
TTY-scannable overview. ``plain`` mode swaps emojis for bracketed text
markers so TTS and non-emoji terminals stay legible.
"""

from __future__ import annotations


# Canonical section order. Matches D3's specified ordering — recovery
# first (sets the overall tone), sleep + running before strength +
# stress so the reader hits the training-bearing domains early, nutrition
# last (it's a consequence of the training decisions).
DOMAIN_ORDER: tuple[str, ...] = (
    "recovery",
    "sleep",
    "running",
    "strength",
    "stress",
    "nutrition",
)


# Action-class taxonomy. Each recommendation action maps to one of four
# classes so the user sees a consistent prefix regardless of domain.
ACTION_CLASS_PROCEED = "proceed"
ACTION_CLASS_CAUTION = "caution"
ACTION_CLASS_REST = "rest"
ACTION_CLASS_DEFER = "defer"


# Every action in the system mapped to an action-class. New actions
# default to "caution" — a loud, conservative prefix — so an unmapped
# action is visible rather than silently rendered as "proceed."
_ACTION_CLASS: dict[str, str] = {
    # Proceed / maintain / prescriptive positive
    "proceed_with_planned_session": ACTION_CLASS_PROCEED,
    "proceed_with_planned_run": ACTION_CLASS_PROCEED,
    "maintain_targets": ACTION_CLASS_PROCEED,
    "maintain_schedule": ACTION_CLASS_PROCEED,
    "maintain_routine": ACTION_CLASS_PROCEED,
    # Caution / downgrade / caveat
    "downgrade_hard_session_to_zone_2": ACTION_CLASS_CAUTION,
    "downgrade_session_to_mobility_only": ACTION_CLASS_CAUTION,
    "downgrade_intervals_to_tempo": ACTION_CLASS_CAUTION,
    "downgrade_to_easy_aerobic": ACTION_CLASS_CAUTION,
    "downgrade_to_technique_or_accessory": ACTION_CLASS_CAUTION,
    "downgrade_to_moderate_load": ACTION_CLASS_CAUTION,
    "cross_train_instead": ACTION_CLASS_CAUTION,
    "prioritize_wind_down": ACTION_CLASS_CAUTION,
    "earlier_bedtime_target": ACTION_CLASS_CAUTION,
    "sleep_debt_repayment_day": ACTION_CLASS_CAUTION,
    "add_low_intensity_recovery": ACTION_CLASS_CAUTION,
    "schedule_decompression_time": ACTION_CLASS_CAUTION,
    "increase_protein_intake": ACTION_CLASS_CAUTION,
    "increase_hydration": ACTION_CLASS_CAUTION,
    "reduce_calorie_deficit": ACTION_CLASS_CAUTION,
    # Rest / escalate
    "rest_day_recommended": ACTION_CLASS_REST,
    "escalate_for_user_review": ACTION_CLASS_REST,
    # Defer — explicit insufficient-signal case
    "defer_decision_insufficient_signal": ACTION_CLASS_DEFER,
}


ACTION_CLASS_EMOJI: dict[str, str] = {
    ACTION_CLASS_PROCEED: "🟢",
    ACTION_CLASS_CAUTION: "🟡",
    ACTION_CLASS_REST: "🔴",
    ACTION_CLASS_DEFER: "⚪",
}


ACTION_CLASS_PLAIN_MARKERS: dict[str, str] = {
    ACTION_CLASS_PROCEED: "[PROCEED]",
    ACTION_CLASS_CAUTION: "[CAUTION]",
    ACTION_CLASS_REST: "[REST]",
    ACTION_CLASS_DEFER: "[DEFER]",
}


def action_class_for(action: str) -> str:
    """Return the action-class for a recommendation action string.

    Unmapped actions fall through to ``caution`` — conservative default
    so a new action's prefix doesn't silently misrepresent intent.
    """

    return _ACTION_CLASS.get(action, ACTION_CLASS_CAUTION)


# Per-domain defer review_question templates (D3). Replaces the
# generic "Did you decide on a session yesterday?" fallback that
# leaked session-language across every domain's defer rec.
DEFER_REVIEW_QUESTION_TEMPLATES: dict[str, str] = {
    "recovery": "Did you decide on a session yesterday? How did it go?",
    "running": "Did you go for a run yesterday? How did it feel?",
    "sleep": "Did anything shift in your sleep last night worth noting?",
    "strength": "Did you train yesterday? Anything worth logging?",
    "stress": "How were your stress levels yesterday?",
    "nutrition": "How did yesterday's eating go? Anything worth logging as macros?",
}


# Per-domain "what would unblock me?" hint for defer recs — what intake
# command the user can run so tomorrow's plan has the signal it needs.
_DEFER_UNBLOCK_HINTS: dict[str, str] = {
    "recovery": (
        "Log a readiness check so the next run has something to work "
        "with: `hai intake readiness --soreness … --energy … "
        "--planned-session-type …`."
    ),
    "running": (
        "Either the pull didn't find today's run or the history is too "
        "thin. If you haven't synced your watch in a few days, start "
        "with `hai pull`; otherwise log any runs you've done recently."
    ),
    "sleep": (
        "The sleep signal for today is missing. `hai pull` re-reads "
        "Garmin sleep; if the watch didn't record, there's nothing to "
        "recommend on."
    ),
    "strength": (
        "Log recent sessions so the classifier has history: `hai intake "
        "gym --session-json …` or the structured flag form."
    ),
    "stress": (
        "Log today's subjective stress on a 1-5 scale: `hai intake "
        "stress --score …`. Garmin stress (if present) pairs with this."
    ),
    "nutrition": (
        "No macros logged for today. `hai intake nutrition "
        "--calories … --protein-g … --carbs-g … --fat-g …` when you "
        "have the totals."
    ),
}


def defer_unblock_hint(domain: str) -> str:
    """Return the per-domain "what would unblock me" prose for a defer rec."""

    return _DEFER_UNBLOCK_HINTS.get(
        domain,
        "Not enough information for today. Log relevant evidence and re-run `hai daily`.",
    )


# D4 §Nutrition — cold-start users need explicit "I'd be making it up"
# framing rather than the generic defer hint. Macros genuinely need
# today's totals; there is no honest default.
_COLD_START_NUTRITION_DEFER_HINT = (
    "You haven't logged any nutrition for today, and I don't have a "
    "history of your typical macros. My recommendation would be made "
    "up. Log today's totals with `hai intake nutrition --calories N "
    "--protein-g N --carbs-g N --fat-g N` — even rough estimates help; "
    "the system gets more accurate as you log more days."
)


def cold_start_nutrition_defer_hint() -> str:
    """Return the cold-start-specific defer framing for nutrition.

    Used by ``hai today`` when ``nutrition.cold_start=True`` and the
    domain is deferring. Replaces the generic unblock hint with D4's
    prescribed language so first-run users understand why we can't
    recommend rather than assuming the system is broken.
    """

    return _COLD_START_NUTRITION_DEFER_HINT


# D4 §Interaction with `hai today` — one-line footer per cold-start
# domain so the reader knows their recommendations will improve as
# history accrues. Rendered once per cold-start domain per day.
_COLD_START_FOOTER_TEMPLATE = (
    "_Note: you're in the first 14 days of using the agent. My "
    "{domain} recommendations will get more specific as history "
    "accumulates ({history_days}/14 days so far)._"
)


def cold_start_footer(domain: str, history_days: int) -> str:
    """Return the per-domain cold-start footer line for ``hai today``."""

    return _COLD_START_FOOTER_TEMPLATE.format(
        domain=domain,
        history_days=max(0, history_days),
    )


# Enum-to-prose mapping for the one-sentence action summary. Keeps the
# per-domain override in one place so the renderer doesn't hard-code
# strings. Missing actions degrade to the raw enum value as the fallback.
_ACTION_PROSE: dict[tuple[str, str], str] = {
    # Recovery
    ("recovery", "proceed_with_planned_session"): "Proceed with your planned session.",
    ("recovery", "downgrade_hard_session_to_zone_2"): "Downgrade today's hard session to Zone 2.",
    ("recovery", "downgrade_session_to_mobility_only"): "Swap today's session for mobility work only.",
    ("recovery", "cross_train_instead"): "Cross-train today instead of your planned session.",
    ("recovery", "rest_day_recommended"): "Rest today.",
    ("recovery", "escalate_for_user_review"): "Pause — a persistent signal needs your attention.",
    ("recovery", "defer_decision_insufficient_signal"): "Not enough information to recommend a training call today.",
    # Running
    ("running", "proceed_with_planned_run"): "Proceed with your planned run.",
    ("running", "downgrade_intervals_to_tempo"): "Soften today's intervals to a tempo effort.",
    ("running", "downgrade_to_easy_aerobic"): "Keep today's run easy-aerobic.",
    ("running", "rest_day_recommended"): "Rest day — no running today.",
    ("running", "defer_decision_insufficient_signal"): "Not enough information to recommend a run today.",
    # Sleep
    ("sleep", "maintain_schedule"): "Stick with your usual sleep schedule tonight.",
    ("sleep", "prioritize_wind_down"): "Wind down earlier tonight.",
    ("sleep", "sleep_debt_repayment_day"): "Repay sleep debt tonight — extend sleep if you can.",
    ("sleep", "earlier_bedtime_target"): "Target an earlier bedtime tonight.",
    ("sleep", "defer_decision_insufficient_signal"): "Not enough sleep information to recommend a change.",
    # Stress
    ("stress", "maintain_routine"): "Keep your usual routine today.",
    ("stress", "add_low_intensity_recovery"): "Add a low-intensity recovery block today.",
    ("stress", "schedule_decompression_time"): "Schedule decompression time today.",
    ("stress", "defer_decision_insufficient_signal"): "Not enough stress information to recommend today.",
    # Strength
    ("strength", "proceed_with_planned_session"): "Proceed with your planned strength session.",
    ("strength", "downgrade_to_technique_or_accessory"): "Downgrade today's lift to technique / accessory work.",
    ("strength", "downgrade_to_moderate_load"): "Keep today's loads moderate.",
    ("strength", "rest_day_recommended"): "Rest from lifting today.",
    ("strength", "defer_decision_insufficient_signal"): "Not enough strength information to recommend today.",
    # Nutrition
    ("nutrition", "maintain_targets"): "Hold today's macro targets.",
    ("nutrition", "increase_protein_intake"): "Bump protein today.",
    ("nutrition", "increase_hydration"): "Drink more today.",
    ("nutrition", "reduce_calorie_deficit"): "Ease today's calorie deficit.",
    ("nutrition", "defer_decision_insufficient_signal"): "Not enough macros logged to recommend today.",
}


def humanize_action(domain: str, action: str) -> str:
    """Return a one-sentence plain-language summary of an action.

    Falls back to the raw enum-as-prose when the (domain, action) pair
    isn't in the registry — a loud fallback that a reviewer will notice
    during dogfood so we add the missing mapping rather than ship a
    silently-ugly sentence.
    """

    return _ACTION_PROSE.get((domain, action), action.replace("_", " ").capitalize() + ".")
