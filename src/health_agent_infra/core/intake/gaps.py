"""Intake-gap inventory — structured surface for agent-driven prompting.

The agent's problem at session start: given a snapshot, which manual inputs
does the user still need to provide to unlock each domain's recommendation?
Before this module, the agent drip-fed the question domain-by-domain (or
missed it entirely — the 2026-04-24 dogfood session surfaced exactly this
failure mode for sleep, which was fully covered passively but still got
asked about).

This module exposes a deterministic mapping from classifier-emitted
uncertainty tokens to the intake command that closes the gap. Agent reads
the list, composes one consolidated question in its own voice, routes the
user's free-text answer through the right ``hai intake <X>`` commands.

**Separation of concerns:**
  - Code owns the inventory: "these fields are missing; here's how to log each."
  - Agent owns the prose: "the natural morning question for this user today."

That separation is what makes this a long-term surface — consistent across
agent implementations, testable, user-visible as a stable contract.

## What counts as a "gap"

A gap is a piece of evidence that:

  1. The runtime classifier marks as missing via an uncertainty token, AND
  2. The user CAN close by running a specific ``hai intake <X>`` command.

Purely-historical gaps (``weekly_mileage_baseline_unavailable``) and
source-level gaps (``body_battery_unavailable`` — intervals.icu doesn't
expose it; needs garmin-direct) are NOT gaps in this sense: the user
can't close them today by answering a question, so asking wastes friction.

Sleep has no gaps in this module's sense: its coverage comes entirely from
passive wearable data. If the classifier defers sleep, the cause is a
source-level issue (e.g. the watch didn't log the night), not user input
the agent should ask for.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IntakeGap:
    """One actionable intake gap the user can close.

    Fields the agent reads:
      - ``domain``: which domain this gap blocks. The agent uses this to
        phrase context ("to unlock recovery: ...").
      - ``missing_field``: the uncertainty token emitted by the classifier.
        Stable across releases — matches the token in ``classified_state.uncertainty``.
      - ``field_description``: what this field IS, in plain terms. The agent
        composes the question FROM this; it is not the question itself.
        Example: "soreness + energy self-report + planned session type".
      - ``intake_command``: the canonical ``hai intake <X>`` path the agent
        should route the user's answer through. Always a full invocation
        path, not a subcommand fragment.
      - ``intake_args_template``: the flag template for the canonical command,
        with placeholder values the agent substitutes (e.g.
        ``"--soreness <low|moderate|high> --energy <low|moderate|high>"``).
      - ``blocks_coverage``: True when closing this gap flips the domain
        out of ``coverage=insufficient`` (so it's required for a non-defer
        recommendation). False when it's enriching only.
      - ``priority``: 1 = gating (skill defers without it), 2 = enriching
        (changes the recommendation but doesn't gate), 3 = optional.
    """

    domain: str
    missing_field: str
    field_description: str
    intake_command: str
    intake_args_template: str
    blocks_coverage: bool
    priority: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "missing_field": self.missing_field,
            "field_description": self.field_description,
            "intake_command": self.intake_command,
            "intake_args_template": self.intake_args_template,
            "blocks_coverage": self.blocks_coverage,
            "priority": self.priority,
        }


# ---------------------------------------------------------------------------
# Curated mapping: classifier uncertainty token → IntakeGap template
# ---------------------------------------------------------------------------
#
# A new entry here is a commitment. It says: "when the classifier emits
# this uncertainty token, the user can close it via this command." Adding
# an entry for a token that isn't user-closable (e.g. history-dependent,
# source-level) is worse than not adding it — the agent would ask a
# question the user can't meaningfully answer.
#
# Tokens NOT in this table are intentionally excluded:
#   - `weekly_mileage_baseline_unavailable` — time-dependent, accumulates
#   - `hard_session_history_unavailable` — time-dependent
#   - `training_load_baseline_missing` — time-dependent
#   - `sleep_efficiency_unavailable` / `sleep_start_ts_unavailable_in_v1`
#     — source-level (intervals.icu wellness doesn't expose)
#   - `body_battery_unavailable` / `garmin_all_day_stress_unavailable`
#     — source-level (intervals.icu doesn't expose; needs garmin-direct)
#   - `calorie_baseline_unavailable` / `protein_target_unavailable`
#     — time-dependent; user's macro baseline accumulates from logged days
#   - `sleep_record_missing`, `resting_hr_record_missing`, etc. — wearable
#     sync issues; agent asking doesn't help. Handled at pull-freshness layer.


# `manual_checkin_missing` (recovery) bundles three fields: soreness,
# energy, and planned_session_type. The intake command surface is
# `hai intake readiness` with a single call; the agent composes one
# question and passes all three as flags. Priority 1: recovery can't
# produce a non-defer recommendation without it.
_RECOVERY_MANUAL_CHECKIN = IntakeGap(
    domain="recovery",
    missing_field="manual_checkin_missing",
    field_description=(
        "morning self-report: soreness (low | moderate | high), energy "
        "(low | moderate | high), and the session you're planning today "
        "(e.g. 'intervals_4x4', 'easy_z2', 'strength_sbd', 'rest')"
    ),
    intake_command="hai intake readiness",
    intake_args_template=(
        "--soreness <low|moderate|high> --energy <low|moderate|high> "
        "--planned-session-type <str> [--active-goal <str>]"
    ),
    blocks_coverage=True,
    priority=1,
)


# `manual_stress_score_unavailable` (stress). Priority 1 when neither
# `body_battery` nor `garmin_all_day_stress` is populated — which on
# intervals.icu-only profiles is ALWAYS the case. On a garmin-direct
# profile with passive stress present, this falls to priority 3
# (enriching only). We lean on the snapshot check in
# `compute_intake_gaps` to decide blocks_coverage dynamically.
_STRESS_MANUAL_SCORE = IntakeGap(
    domain="stress",
    missing_field="manual_stress_score_unavailable",
    field_description=(
        "end-of-day stress self-rating (1–5, where 1 is very calm and "
        "5 is very stressed), and any tags you want to attach (e.g. "
        "'work_deadline', 'travel')"
    ),
    intake_command="hai intake stress",
    intake_args_template="--score <1|2|3|4|5> [--tags <comma_separated>]",
    blocks_coverage=True,
    priority=1,
)


# `no_nutrition_row_for_day` (nutrition). Priority 2 because the user
# logs at end of day in practice — asking at morning session start is
# premature. The agent can surface it as a reminder ("I'll need macros
# logged later to close nutrition") rather than a blocking question.
_NUTRITION_MACROS = IntakeGap(
    domain="nutrition",
    missing_field="no_nutrition_row_for_day",
    field_description=(
        "today's macro totals: calories (kcal), protein (g), carbs (g), "
        "fat (g). Optional: meals count, hydration (litres)"
    ),
    intake_command="hai intake nutrition",
    intake_args_template=(
        "--kcal <int> --protein-g <int> --carbs-g <int> --fat-g <int> "
        "[--meals-count <int>] [--hydration-l <float>]"
    ),
    blocks_coverage=True,
    priority=2,
)


# `sessions_history_unavailable` (strength). Priority 1 — until the user
# either logs a gym session OR explicitly says "no strength today",
# strength stays at coverage=insufficient. The intake command accepts a
# narrated session via `hai intake gym`, or the planned-session-type
# field on `hai intake readiness` carries the "no strength today"
# intent (running-readiness skill reads it).
_STRENGTH_GYM_OR_INTENT = IntakeGap(
    domain="strength",
    missing_field="sessions_history_unavailable",
    field_description=(
        "either today's gym session (sets × reps × load per exercise) "
        "OR the planned-session-type on your morning readiness check-in "
        "(e.g. 'strength_sbd', 'rest', 'easy_z2' — any non-strength "
        "session tells the system you're not lifting today)"
    ),
    intake_command="hai intake gym",
    intake_args_template=(
        "--session-json <path> OR narrate to strength-intake skill; "
        "alternatively set --planned-session-type on hai intake readiness"
    ),
    blocks_coverage=True,
    priority=1,
)


# Stable lookup by uncertainty token.
_TOKEN_TO_GAP: dict[str, IntakeGap] = {
    _RECOVERY_MANUAL_CHECKIN.missing_field: _RECOVERY_MANUAL_CHECKIN,
    _STRESS_MANUAL_SCORE.missing_field: _STRESS_MANUAL_SCORE,
    _NUTRITION_MACROS.missing_field: _NUTRITION_MACROS,
    _STRENGTH_GYM_OR_INTENT.missing_field: _STRENGTH_GYM_OR_INTENT,
}


def known_gap_tokens() -> frozenset[str]:
    """Return the set of uncertainty tokens this module recognises as gaps.

    Useful for tests that want to assert the classifier emits tokens the
    gap mapping actually covers.
    """

    return frozenset(_TOKEN_TO_GAP.keys())


def compute_intake_gaps(snapshot: dict[str, Any]) -> list[IntakeGap]:
    """Enumerate user-closeable intake gaps in the snapshot.

    Reads each domain block's ``classified_state.uncertainty`` and cross-
    references the curated mapping. Returns a list sorted by (priority,
    domain) so the agent can compose its prompt most-important-first.

    Snapshots without per-domain ``classified_state`` (the v1.0 lean shape,
    without ``--evidence-json``) produce an empty list rather than raising —
    the caller is expected to have already built a full snapshot before
    calling this function.

    The stress gap's ``blocks_coverage`` is decided dynamically: when
    either ``body_battery`` or ``garmin_all_day_stress`` is populated,
    the manual score is enriching (priority 3), not gating.
    """

    out: list[IntakeGap] = []
    for domain in ("recovery", "running", "sleep", "strength", "stress", "nutrition"):
        block = snapshot.get(domain)
        if not isinstance(block, dict):
            continue
        classified = block.get("classified_state")
        if not isinstance(classified, dict):
            continue
        tokens = classified.get("uncertainty") or []
        for token in tokens:
            gap = _TOKEN_TO_GAP.get(token)
            if gap is None:
                continue
            # Domain cross-check: the token's domain must match the block
            # we found it in. Defends against a stray token in the wrong
            # block (shouldn't happen, but cheap insurance).
            if gap.domain != domain:
                continue
            gap = _adjust_gap_for_context(gap, block)
            out.append(gap)

    # Sort: priority ascending (1 = highest), then domain alphabetical.
    out.sort(key=lambda g: (g.priority, g.domain))
    return out


def _adjust_gap_for_context(gap: IntakeGap, block: dict[str, Any]) -> IntakeGap:
    """Context-aware priority + blocks_coverage adjustment.

    Currently only stress: when passive stress signals (body_battery or
    garmin_all_day_stress) are present on the block, the manual score
    becomes enriching, not gating. For intervals.icu-only profiles
    (where both are always null), nothing changes.
    """

    if gap.domain != "stress":
        return gap

    classified = block.get("classified_state") or {}
    body_battery_present = classified.get("body_battery_delta") is not None
    garmin_stress_present = (
        classified.get("garmin_stress_band") not in (None, "unknown")
    )
    if body_battery_present or garmin_stress_present:
        # Passive signal already closes coverage; manual score is colour only.
        return IntakeGap(
            domain=gap.domain,
            missing_field=gap.missing_field,
            field_description=gap.field_description,
            intake_command=gap.intake_command,
            intake_args_template=gap.intake_args_template,
            blocks_coverage=False,
            priority=3,
        )
    return gap
