"""ReviewOutcome validation — the third determinism boundary.

The v0.1.6 audit cycle (Codex r1 + internal + Codex r2) found that
``hai review record`` was NOT a real boundary: the CLI handler
called ``json.loads(...)`` and passed the result straight into
``record_review_outcome()`` without runtime type validation. The
JSONL audit row preserved whatever was written
(``"followed_recommendation": "definitely"``); the SQLite projector
coerced it to ``1`` via ``_bool_to_int()`` (truthy Python value).
The audit chain disagreed with itself across storage layers — a
silent data-integrity bug.

This module is the parallel of ``writeback/proposal.py`` for review
outcomes. ``validate_review_outcome_dict`` rejects with named
invariants on first violation; the CLI handler routes the failure
through the same governed ``USER_INPUT`` exit shape ``hai propose``
already uses.

Invariant ids (each maps to a stable slug an agent can pattern-match
on without parsing prose):

  - ``required_fields_present`` — every field in
    :data:`REQUIRED_OUTCOME_FIELDS` must be present.
  - ``review_event_id_str`` — must be a non-empty string.
  - ``recommendation_id_str`` — must be a non-empty string.
  - ``user_id_str`` — must be a non-empty string.
  - ``domain_str`` — when present, must be a non-empty string.
  - ``followed_recommendation_must_be_bool`` — strict ``bool``,
    not ``"yes"`` / ``1`` / truthy-string. The whole point of this
    boundary is to refuse the silent JSONL-vs-SQLite divergence.
  - ``self_reported_improvement_must_be_bool_or_null`` — strict
    ``bool`` or ``None`` when present.
  - ``free_text_str_or_null`` — string or None when present.
  - ``completed_must_be_bool_or_null`` — strict ``bool`` or None
    when present in the payload (CLI flag ``--completed yes|no`` is
    parsed into bool before merging, so this catches JSON-only
    callers).
  - ``intensity_delta_enum`` — when present, must be one of the
    documented enum values.
  - ``duration_minutes_int_or_null`` — int or None.
  - ``pre_energy_score_in_range`` / ``post_energy_score_in_range``
    — int in 1..5 or None.
  - ``disagreed_firing_ids_list_of_str_or_null`` — list of strings
    or None.
"""

from __future__ import annotations

from typing import Any, Final


REQUIRED_OUTCOME_FIELDS: Final[frozenset[str]] = frozenset({
    "review_event_id",
    "recommendation_id",
    "user_id",
    "followed_recommendation",
})

INTENSITY_DELTA_ENUM: Final[frozenset[str]] = frozenset({
    "much_lighter", "lighter", "same", "harder", "much_harder",
})


class ReviewOutcomeValidationError(ValueError):
    """Raised when a review-outcome dict violates a code-enforced
    invariant. The ``invariant`` attribute names the rule that failed
    so tests + agents can pattern-match without parsing prose."""

    def __init__(self, invariant: str, message: str) -> None:
        super().__init__(message)
        self.invariant = invariant


def _is_strict_bool(value: Any) -> bool:
    """Strict bool check that distinguishes ``True`` / ``False`` from
    other Python truthy values. ``isinstance(True, int)`` is True in
    Python, so we check via ``type(value) is bool`` to make truthy
    integers and strings fail loudly."""

    return type(value) is bool


def validate_review_outcome_dict(data: Any) -> None:
    """Validate a review-outcome dict against the frozen contract.

    Raises :class:`ReviewOutcomeValidationError` on the first
    violation. Caller is expected to print the invariant id alongside
    the message for parseability:

        f"hai review record rejected: invariant={exc.invariant}: {exc}"
    """

    if not isinstance(data, dict):
        raise ReviewOutcomeValidationError(
            "required_fields_present",
            f"expected dict, got {type(data).__name__}",
        )

    missing = REQUIRED_OUTCOME_FIELDS - set(data.keys())
    if missing:
        raise ReviewOutcomeValidationError(
            "required_fields_present",
            f"missing required fields: {sorted(missing)}",
        )

    # String fields — non-empty.
    for field, invariant in (
        ("review_event_id", "review_event_id_str"),
        ("recommendation_id", "recommendation_id_str"),
        ("user_id", "user_id_str"),
    ):
        value = data[field]
        if not isinstance(value, str) or not value:
            raise ReviewOutcomeValidationError(
                invariant,
                f"{field}: expected non-empty string, got "
                f"{type(value).__name__} ({value!r})",
            )

    # Optional string field.
    if "domain" in data and data["domain"] is not None:
        value = data["domain"]
        if not isinstance(value, str) or not value:
            raise ReviewOutcomeValidationError(
                "domain_str",
                f"domain: expected non-empty string or absent, got "
                f"{type(value).__name__} ({value!r})",
            )

    # Strict-bool boundary — the bug we're fixing.
    if not _is_strict_bool(data["followed_recommendation"]):
        raise ReviewOutcomeValidationError(
            "followed_recommendation_must_be_bool",
            f"followed_recommendation: expected strict True or False, "
            f"got {type(data['followed_recommendation']).__name__} "
            f"({data['followed_recommendation']!r}). The audit chain "
            f"requires JSONL and SQLite to agree on this value; "
            f"truthy strings or ints would fork.",
        )

    if "self_reported_improvement" in data:
        v = data["self_reported_improvement"]
        if v is not None and not _is_strict_bool(v):
            raise ReviewOutcomeValidationError(
                "self_reported_improvement_must_be_bool_or_null",
                f"self_reported_improvement: expected bool or null, "
                f"got {type(v).__name__} ({v!r})",
            )

    if "free_text" in data and data["free_text"] is not None:
        if not isinstance(data["free_text"], str):
            raise ReviewOutcomeValidationError(
                "free_text_str_or_null",
                f"free_text: expected string or null, got "
                f"{type(data['free_text']).__name__}",
            )

    # Migration-010 enrichment fields. All optional; strict types when
    # present (CLI flags do their own parsing into the right type so
    # this catches JSON-only callers).
    if "completed" in data and data["completed"] is not None:
        if not _is_strict_bool(data["completed"]):
            raise ReviewOutcomeValidationError(
                "completed_must_be_bool_or_null",
                f"completed: expected bool or null, got "
                f"{type(data['completed']).__name__} ({data['completed']!r})",
            )

    if "intensity_delta" in data and data["intensity_delta"] is not None:
        v = data["intensity_delta"]
        if v not in INTENSITY_DELTA_ENUM:
            raise ReviewOutcomeValidationError(
                "intensity_delta_enum",
                f"intensity_delta: expected one of "
                f"{sorted(INTENSITY_DELTA_ENUM)}, got {v!r}",
            )

    if "duration_minutes" in data and data["duration_minutes"] is not None:
        v = data["duration_minutes"]
        if not isinstance(v, int) or _is_strict_bool(v):
            raise ReviewOutcomeValidationError(
                "duration_minutes_int_or_null",
                f"duration_minutes: expected int or null, got "
                f"{type(v).__name__} ({v!r})",
            )

    for field, invariant in (
        ("pre_energy_score", "pre_energy_score_in_range"),
        ("post_energy_score", "post_energy_score_in_range"),
    ):
        if field in data and data[field] is not None:
            v = data[field]
            if (
                not isinstance(v, int) or _is_strict_bool(v)
                or v < 1 or v > 5
            ):
                raise ReviewOutcomeValidationError(
                    invariant,
                    f"{field}: expected int in 1..5 or null, got "
                    f"{type(v).__name__} ({v!r})",
                )

    if "disagreed_firing_ids" in data and data["disagreed_firing_ids"] is not None:
        v = data["disagreed_firing_ids"]
        if not isinstance(v, list) or any(not isinstance(x, str) for x in v):
            raise ReviewOutcomeValidationError(
                "disagreed_firing_ids_list_of_str_or_null",
                f"disagreed_firing_ids: expected list of strings or "
                f"null, got {type(v).__name__} ({v!r})",
            )


__all__ = [
    "INTENSITY_DELTA_ENUM",
    "REQUIRED_OUTCOME_FIELDS",
    "ReviewOutcomeValidationError",
    "validate_review_outcome_dict",
]
