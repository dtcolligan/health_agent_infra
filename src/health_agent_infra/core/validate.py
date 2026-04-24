"""Pure validators for agent-produced JSON.

The validator is the runtime's code-enforced boundary on the agent's output.
Skills describe how the agent should reason; this module enforces the
invariants the runtime must guarantee regardless of skill drift or prompt
manipulation.

Every invariant has a stable machine-readable id so tests and callers can
pattern-match on the specific violation rather than parsing prose.

**Coverage contract** (v0.1.4 Phase A safety closure):

This validator runs on EVERY final recommendation before any synthesis
transaction commits — see ``core/synthesis.run_synthesis``. It covers all
six final recommendation schema versions (recovery, running, sleep,
strength, stress, nutrition). The legacy single-domain ``hai writeback``
path was removed in v0.1.4 D2; this module is the only safety net left
and runs from the canonical synthesis path.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from health_agent_infra.core.schemas import RECOMMENDATION_SCHEMA_VERSION


# Per-domain allowed-action enums. Mirrors the ``Literal[...]`` declarations
# on each domain's recommendation dataclass; extracted here so the runtime
# validator does not need to import every domain at validate time. A new
# domain action MUST land here in the same PR that introduces it, otherwise
# the synthesis safety closure will reject the new recommendation.
ALLOWED_ACTIONS_BY_DOMAIN: dict[str, frozenset[str]] = {
    "recovery": frozenset({
        "proceed_with_planned_session",
        "downgrade_hard_session_to_zone_2",
        "downgrade_session_to_mobility_only",
        "rest_day_recommended",
        "defer_decision_insufficient_signal",
        "escalate_for_user_review",
    }),
    "running": frozenset({
        "proceed_with_planned_run",
        "downgrade_intervals_to_tempo",
        "downgrade_to_easy_aerobic",
        "cross_train_instead",
        "rest_day_recommended",
        "defer_decision_insufficient_signal",
        "escalate_for_user_review",
    }),
    "sleep": frozenset({
        "maintain_schedule",
        "prioritize_wind_down",
        "sleep_debt_repayment_day",
        "earlier_bedtime_target",
        "defer_decision_insufficient_signal",
    }),
    "strength": frozenset({
        "proceed_with_planned_session",
        "downgrade_to_technique_or_accessory",
        "downgrade_to_moderate_load",
        "rest_day_recommended",
        "defer_decision_insufficient_signal",
        "escalate_for_user_review",
    }),
    "stress": frozenset({
        "maintain_routine",
        "add_low_intensity_recovery",
        "schedule_decompression_time",
        "escalate_for_user_review",
        "defer_decision_insufficient_signal",
    }),
    "nutrition": frozenset({
        "maintain_targets",
        "increase_protein_intake",
        "increase_hydration",
        "reduce_calorie_deficit",
        "defer_decision_insufficient_signal",
        "escalate_for_user_review",
    }),
}

# Stable union of every per-domain action. Used by the legacy single-domain
# entry point that doesn't carry a ``domain`` field.
ALLOWED_ACTIONS: frozenset[str] = frozenset().union(
    *ALLOWED_ACTIONS_BY_DOMAIN.values()
)

# Per-domain final recommendation schema versions. Mirrors
# ``RECOMMENDATION_SCHEMA_BY_DOMAIN`` in ``core/synthesis.py``; kept in sync
# manually because importing from synthesis would create a cycle.
SCHEMA_VERSION_BY_DOMAIN: dict[str, str] = {
    "recovery": "training_recommendation.v1",
    "running": "running_recommendation.v1",
    "sleep": "sleep_recommendation.v1",
    "strength": "strength_recommendation.v1",
    "stress": "stress_recommendation.v1",
    "nutrition": "nutrition_recommendation.v1",
}

ALLOWED_CONFIDENCE: frozenset[str] = frozenset({"low", "moderate", "high"})

# R2 — diagnosis-shaped tokens. Matching is **whole-word, case-insensitive**
# via _BANNED_TOKEN_PATTERNS below. A raw substring check (pre-Codex-r2)
# rejected legitimate language like `conditional_readiness` (contains
# "condition") — the fix is word-boundary regex.
BANNED_TOKENS: frozenset[str] = frozenset({
    "diagnosis",
    "diagnose",
    "diagnosed",
    "syndrome",
    "disease",
    "disorder",
    "condition",
    "infection",
    "illness",
    "sick",
})

# Pre-compiled whole-word patterns for each banned token. Compiled once
# at module load; the pattern list is small and the compile cost is tiny
# relative to the per-call regex.search overhead that would result from
# compiling on every validation call. Same shape as
# ``core/narration/voice.py::_banned_token_patterns``.
_BANNED_TOKEN_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(rf"\b{re.escape(token)}\b", re.IGNORECASE), token)
    for token in sorted(BANNED_TOKENS)
)

FOLLOW_UP_WINDOW = timedelta(hours=24)


REQUIRED_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "recommendation_id",
    "user_id",
    "issued_at",
    "for_date",
    "action",
    "rationale",
    "confidence",
    "uncertainty",
    "follow_up",
    "policy_decisions",
    "bounded",
})


class RecommendationValidationError(ValueError):
    """Raised when a recommendation dict violates a code-enforced invariant.

    The ``invariant`` attribute carries a stable machine-readable id so tests
    and `hai synthesize` can pattern-match on the specific violation.
    """

    def __init__(self, invariant: str, message: str) -> None:
        super().__init__(message)
        self.invariant = invariant


def validate_recommendation_dict(data: Any) -> None:
    """Validate an agent-produced recommendation dict.

    Raises ``RecommendationValidationError`` on the first violation, with
    ``.invariant`` set to the stable id of the invariant that failed.
    Returns ``None`` on success.

    Domain dispatch: when ``data`` carries a ``domain`` field, the
    schema_version check + action_enum check resolve against the
    per-domain tables. When ``domain`` is absent (legacy single-domain
    callers), the validator falls back to the recovery contract for
    backwards compatibility — recovery is the only domain whose
    recommendations historically lacked a ``domain`` field.

    Invariant ids (stable, machine-readable):
      - required_fields_present
      - schema_version
      - action_enum
      - confidence_enum
      - bounded_true
      - no_banned_tokens
      - follow_up_shape
      - review_at_within_24h
      - policy_decisions_present
    """

    if not isinstance(data, dict):
        raise RecommendationValidationError(
            "required_fields_present",
            f"expected dict, got {type(data).__name__}",
        )

    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise RecommendationValidationError(
            "required_fields_present",
            f"missing required fields: {sorted(missing)}",
        )

    domain = data.get("domain")
    expected_schema = SCHEMA_VERSION_BY_DOMAIN.get(
        domain, RECOMMENDATION_SCHEMA_VERSION,
    )
    if data["schema_version"] != expected_schema:
        raise RecommendationValidationError(
            "schema_version",
            f"expected {expected_schema!r} for domain {domain!r}, "
            f"got {data['schema_version']!r}",
        )

    allowed_actions = ALLOWED_ACTIONS_BY_DOMAIN.get(
        domain, ALLOWED_ACTIONS_BY_DOMAIN["recovery"],
    )
    action = data["action"]
    if action not in allowed_actions:
        raise RecommendationValidationError(
            "action_enum",
            f"action {action!r} not in allowed set for domain {domain!r}: "
            f"{sorted(allowed_actions)}",
        )

    confidence = data["confidence"]
    if confidence not in ALLOWED_CONFIDENCE:
        raise RecommendationValidationError(
            "confidence_enum",
            f"confidence {confidence!r} not in {sorted(ALLOWED_CONFIDENCE)}",
        )

    if data["bounded"] is not True:
        raise RecommendationValidationError(
            "bounded_true",
            f"bounded must be True, got {data['bounded']!r}",
        )

    # R2 — banned diagnosis-shaped tokens. Sweeps every agent-/skill-authored
    # text surface: rationale, action_detail, uncertainty, and the
    # follow_up.review_question. The synthesis layer composes the review
    # question from a curated template OR a skill overlay; either way it
    # passes through here before commit.
    _check_banned_tokens(data)

    follow_up = data.get("follow_up")
    if not isinstance(follow_up, dict):
        raise RecommendationValidationError(
            "follow_up_shape",
            f"follow_up must be an object, got {type(follow_up).__name__}",
        )
    for fu_field in ("review_at", "review_question", "review_event_id"):
        if fu_field not in follow_up:
            raise RecommendationValidationError(
                "follow_up_shape",
                f"follow_up missing {fu_field!r}",
            )

    # R4 — review_at within 24h of issued_at.
    try:
        issued_at = _parse_dt(data["issued_at"])
        review_at = _parse_dt(follow_up["review_at"])
    except ValueError as exc:
        raise RecommendationValidationError(
            "review_at_within_24h",
            f"could not parse timestamps: {exc}",
        )
    delta = review_at - issued_at
    if delta < timedelta(0) or delta > FOLLOW_UP_WINDOW:
        raise RecommendationValidationError(
            "review_at_within_24h",
            f"review_at must be within {FOLLOW_UP_WINDOW} of issued_at; "
            f"delta={delta}",
        )

    policy_decisions = data["policy_decisions"]
    if not isinstance(policy_decisions, list) or len(policy_decisions) < 1:
        raise RecommendationValidationError(
            "policy_decisions_present",
            f"policy_decisions must be a non-empty list; got {policy_decisions!r}",
        )


def _check_banned_tokens(data: dict) -> None:
    """Sweep every text-bearing surface for banned tokens.

    Surfaces (per Phase A brief + Codex 2026-04-24 review pushback):
      - ``rationale[]``: proposal-derived OR skill overlay
      - ``action_detail``: reason tokens, target zones, etc. — recursed
        because nested dicts are common (e.g. ``{"detail": {"reason": ...}}``)
      - ``uncertainty[]``: skill overlay
      - ``follow_up.review_question``: skill overlay or runtime template
      - ``policy_decisions[].note``: runtime-authored, but a code-level
        bug that lets a banned token into a note is still a safety
        violation we should catch — belt-and-suspenders per Codex review.
    """

    parts: list[str] = []

    rationale = data.get("rationale", [])
    if isinstance(rationale, list):
        parts.extend(str(r) for r in rationale)
    else:
        parts.append(str(rationale))

    detail = data.get("action_detail")
    parts.extend(_flatten_text_values(detail))

    uncertainty = data.get("uncertainty", [])
    if isinstance(uncertainty, list):
        parts.extend(str(u) for u in uncertainty)
    else:
        parts.append(str(uncertainty))

    follow_up = data.get("follow_up")
    if isinstance(follow_up, dict):
        review_question = follow_up.get("review_question")
        if review_question is not None:
            parts.append(str(review_question))

    policy_decisions = data.get("policy_decisions", [])
    if isinstance(policy_decisions, list):
        for decision in policy_decisions:
            if isinstance(decision, dict):
                note = decision.get("note")
                if note is not None:
                    parts.append(str(note))

    # Whole-word match, case-insensitive. Codex 2026-04-24 round-2 review:
    # a raw substring check rejected legitimate running language like
    # `conditional` and `conditional_readiness` because the banned-token
    # list contains `condition`. The fix is a word-boundary regex so a
    # standalone "condition" still rejects but "conditional_readiness"
    # passes. Same pattern as `core/narration/voice.py`.
    haystack = " ".join(parts)
    for pattern, token in _BANNED_TOKEN_PATTERNS:
        if pattern.search(haystack):
            raise RecommendationValidationError(
                "no_banned_tokens",
                f"banned diagnosis-shaped token {token!r} found in "
                f"rationale, action_detail, uncertainty, "
                f"follow_up.review_question, or policy_decisions[].note",
            )


def _flatten_text_values(value: Any) -> list[str]:
    """Recursively flatten any nested dict / list into a list of string
    representations. Used for ``action_detail`` because it accepts
    arbitrary structured payloads per domain."""

    if value is None:
        return []
    if isinstance(value, (str, int, float, bool)):
        return [str(value)]
    if isinstance(value, dict):
        out: list[str] = []
        for v in value.values():
            out.extend(_flatten_text_values(v))
        return out
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            out.extend(_flatten_text_values(item))
        return out
    return [str(value)]


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=None)
    if not isinstance(value, str):
        raise ValueError(f"expected str or datetime, got {type(value).__name__}")
    return datetime.fromisoformat(value)
