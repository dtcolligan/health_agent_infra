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

    # `data.get("domain")` is `Any | None`; for the registry lookups we
    # need a str. Coerce defensively — empty string falls through to
    # the default in both registries.
    domain = data.get("domain") or ""
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

    # v0.1.9 B3 — strict text shape checks on the audit-bearing fields.
    # Pre-v0.1.9 the validator only checked presence; Codex 2026-04-26
    # confirmed string values for rationale/uncertainty passed today.
    check_rationale_shape(data, error_cls=RecommendationValidationError)
    check_uncertainty_shape(data, error_cls=RecommendationValidationError)
    check_policy_decisions_shape(data, error_cls=RecommendationValidationError)

    # R2 — banned diagnosis-shaped tokens. Sweeps every agent-/skill-authored
    # text surface via the shared helper so proposal + recommendation
    # surfaces stay in lockstep coverage.
    check_banned_tokens_in_surfaces(
        data,
        include_follow_up=True,
        error_cls=RecommendationValidationError,
    )

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

    # v0.1.9 B3 — review_question must be a non-empty string.
    check_review_question_shape(
        data, error_cls=RecommendationValidationError,
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


# NOTE: the legacy ``_check_banned_tokens`` helper that lived here pre-v0.1.9
# was extracted into the shared :func:`check_banned_tokens_in_surfaces` +
# :func:`iter_text_surfaces` helpers below ``_flatten_text_values`` so the
# proposal validator and the recommendation validator could share one source
# of truth for surface coverage. ``validate_recommendation_dict`` calls the
# shared helper directly with ``include_follow_up=True``.


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


# ---------------------------------------------------------------------------
# v0.1.9 B3 — shared text-surface enumeration + strict shape checks.
#
# The proposal validator (``core/writeback/proposal.py``) and the
# recommendation validator (this module) walk overlapping text surfaces
# for banned-token detection. Pre-v0.1.9 the surface-walking logic was
# duplicated; a fix to one validator's coverage would silently leave
# the other's stale. The shared helpers below ensure both validators
# enforce identical text shape and identical banned-token coverage.
#
# Shape checks (new in v0.1.9):
#   - rationale_list_of_strings — `rationale` must be list[str], non-empty.
#   - uncertainty_list_of_strings — `uncertainty` must be list[str].
#   - policy_decision_shape — every policy_decisions[i] is a dict with
#     str rule_id, str decision, and (when present) str note.
#   - review_question_string — recommendation `follow_up.review_question`
#     is a non-empty str.
# ---------------------------------------------------------------------------


def iter_text_surfaces(
    data: dict,
    *,
    include_follow_up: bool,
) -> list[str]:
    """Yield every agent-/skill-authored text surface as a flat list.

    Surfaces walked:
      - ``rationale[]`` — proposal-derived OR skill overlay
      - ``action_detail`` — recursed because nested dicts are common
      - ``uncertainty[]`` — skill overlay or runtime-emitted
      - ``policy_decisions[].note`` — runtime-authored, but a code-level
        bug that lets a banned token into a note is still a safety
        violation we should catch
      - ``follow_up.review_question`` — recommendation-only; pass
        ``include_follow_up=True`` for recommendation surfaces, False
        for proposal surfaces (proposals have no follow_up by contract)

    The single source of truth: both validators call this. A new text
    surface added here automatically gets both proposal-time and
    recommendation-time coverage.
    """

    parts: list[str] = []

    rationale = data.get("rationale", [])
    if isinstance(rationale, list):
        parts.extend(str(r) for r in rationale)
    else:
        parts.append(str(rationale))

    parts.extend(_flatten_text_values(data.get("action_detail")))

    uncertainty = data.get("uncertainty", [])
    if isinstance(uncertainty, list):
        parts.extend(str(u) for u in uncertainty)
    else:
        parts.append(str(uncertainty))

    if include_follow_up:
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

    return parts


def check_banned_tokens_in_surfaces(
    data: dict,
    *,
    include_follow_up: bool,
    error_cls: type,
) -> None:
    """Run the banned-token regex over every text surface.

    Raises ``error_cls(invariant="no_banned_tokens", message=...)`` on
    the first match. Both validators call this with their own error
    class — ``RecommendationValidationError`` (this module) or
    ``ProposalValidationError`` (proposal module). Raising distinct
    types means each validator's tests can pattern-match by exception
    class and the call site stays self-explanatory.
    """

    haystack = " ".join(iter_text_surfaces(data, include_follow_up=include_follow_up))
    for pattern, token in _BANNED_TOKEN_PATTERNS:
        if pattern.search(haystack):
            surface_label = (
                "rationale, action_detail, uncertainty, "
                "follow_up.review_question, or policy_decisions[].note"
                if include_follow_up
                else "rationale, action_detail, uncertainty, or "
                     "policy_decisions[].note"
            )
            raise error_cls(
                "no_banned_tokens",
                f"banned diagnosis-shaped token {token!r} found in "
                f"{surface_label}",
            )


def check_rationale_shape(data: dict, *, error_cls: type) -> None:
    """``rationale`` must be a ``list[str]`` (empty list permitted).

    Pre-v0.1.9 the validator only checked presence; a string value
    passed (Codex 2026-04-26 confirmed). v0.1.9 hardens the type-safety
    side without imposing a non-empty rule — empty rationale is a
    legitimate signal "the proposer chose not to surface narrative
    text" (e.g. minimal eval-scenario fixtures, defer-only proposals).
    The non-empty UX standard belongs in skill prose.
    """

    rationale = data.get("rationale")
    if not isinstance(rationale, list):
        raise error_cls(
            "rationale_list_of_strings",
            f"rationale must be a list of strings, got "
            f"{type(rationale).__name__}",
        )
    for i, item in enumerate(rationale):
        if not isinstance(item, str):
            raise error_cls(
                "rationale_list_of_strings",
                f"rationale[{i}] must be str, got {type(item).__name__}",
            )


def check_uncertainty_shape(data: dict, *, error_cls: type) -> None:
    """``uncertainty`` must be a ``list[str]`` (empty list is valid).

    An empty uncertainty list is the legitimate signal "the runtime
    has no caveats it wants to surface"; rejecting it would force
    skills to invent uncertainty tokens.
    """

    uncertainty = data.get("uncertainty")
    if not isinstance(uncertainty, list):
        raise error_cls(
            "uncertainty_list_of_strings",
            f"uncertainty must be a list of strings, got "
            f"{type(uncertainty).__name__}",
        )
    for i, item in enumerate(uncertainty):
        if not isinstance(item, str):
            raise error_cls(
                "uncertainty_list_of_strings",
                f"uncertainty[{i}] must be str, got {type(item).__name__}",
            )


def check_policy_decisions_shape(data: dict, *, error_cls: type) -> None:
    """Every ``policy_decisions[i]`` must be a dict with:

      - ``rule_id`` — str, required
      - ``decision`` — str, required
      - ``note`` — str when present (optional key)

    Other keys are permitted (forward-compat for new audit fields).
    """

    policy_decisions = data.get("policy_decisions", [])
    if not isinstance(policy_decisions, list):
        raise error_cls(
            "policy_decision_shape",
            f"policy_decisions must be a list, got "
            f"{type(policy_decisions).__name__}",
        )
    for i, decision in enumerate(policy_decisions):
        if not isinstance(decision, dict):
            raise error_cls(
                "policy_decision_shape",
                f"policy_decisions[{i}] must be a dict, got "
                f"{type(decision).__name__}",
            )
        for required in ("rule_id", "decision"):
            if required not in decision:
                raise error_cls(
                    "policy_decision_shape",
                    f"policy_decisions[{i}] missing required key "
                    f"{required!r}",
                )
            if not isinstance(decision[required], str):
                raise error_cls(
                    "policy_decision_shape",
                    f"policy_decisions[{i}].{required} must be str, "
                    f"got {type(decision[required]).__name__}",
                )
        if "note" in decision and not isinstance(decision["note"], str):
            raise error_cls(
                "policy_decision_shape",
                f"policy_decisions[{i}].note must be str when "
                f"present, got {type(decision['note']).__name__}",
            )


def check_review_question_shape(data: dict, *, error_cls: type) -> None:
    """Recommendation-only: ``follow_up.review_question`` must be a
    non-empty ``str``. Pre-v0.1.9 only the surrounding shape was
    checked; the field's value type was unconstrained.
    """

    follow_up = data.get("follow_up")
    if not isinstance(follow_up, dict):
        # The follow_up shape itself is checked separately by
        # validate_recommendation_dict; bail out here.
        return
    review_question = follow_up.get("review_question")
    if not isinstance(review_question, str):
        raise error_cls(
            "review_question_string",
            f"follow_up.review_question must be str, got "
            f"{type(review_question).__name__}",
        )
    if not review_question.strip():
        raise error_cls(
            "review_question_string",
            "follow_up.review_question must be a non-empty string",
        )


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=None)
    if not isinstance(value, str):
        raise ValueError(f"expected str or datetime, got {type(value).__name__}")
    return datetime.fromisoformat(value)
