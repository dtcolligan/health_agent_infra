"""W48 — code-owned review summary builder.

Per ``hai/reporting/plans/v0_1_8/PLAN.md`` § 2 W48: the runtime owns the
deterministic outcome summary layer. Skills can surface the resulting
tokens but MUST NOT compute them.

This module reads ``recommendation_log``, ``review_event``, and
``review_outcome`` for a rolling window ending on ``as_of_date`` and
emits per-domain (or aggregate) summary dicts with stable token strings:

  - ``outcome_pattern_insufficient_denominator``
  - ``outcome_pattern_recent_negative``
  - ``outcome_pattern_recent_positive``
  - ``outcome_pattern_mixed``

Token thresholds live in ``DEFAULT_THRESHOLDS["policy"]["review_summary"]``
and are user-tunable via ``thresholds.toml`` (see W39).

The summary is visibility-only in v0.1.8 — it never mutates thresholds,
classifiers, policy, X-rules, confidence, intent, or targets. Callers
that want to ship a future adaptation loop must reach through an
explicit user-approved commit path; outcomes do NOT flow into runtime
state on their own (per `hai/docs/non_goals.md`).
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from typing import Any, Iterable, Optional

from health_agent_infra.core.config import load_thresholds


# Stable token strings. Imported by tests and skill text so renames go
# through one source of truth.
TOKEN_INSUFFICIENT_DENOMINATOR = "outcome_pattern_insufficient_denominator"
TOKEN_RECENT_NEGATIVE = "outcome_pattern_recent_negative"
TOKEN_RECENT_POSITIVE = "outcome_pattern_recent_positive"
TOKEN_MIXED = "outcome_pattern_mixed"

ALL_TOKENS = (
    TOKEN_INSUFFICIENT_DENOMINATOR,
    TOKEN_RECENT_NEGATIVE,
    TOKEN_RECENT_POSITIVE,
    TOKEN_MIXED,
)


# Six v1 domains. Aggregate summaries are reported alongside per-domain
# entries when the caller asks for ``domain=None``.
DOMAINS: tuple[str, ...] = (
    "recovery",
    "running",
    "sleep",
    "stress",
    "strength",
    "nutrition",
)


class ReviewSummaryThresholdError(ValueError):
    """Raised when ``policy.review_summary`` carries a value of the wrong
    runtime type. Distinct from the validator's ``type_mismatch`` issue
    so callers can surface a clear "your thresholds.toml is invalid"
    error even when ``hai config validate`` was skipped.
    """


# v0.1.8 Codex R3-1 invariant: numeric thresholds must be real
# numbers, not booleans. Python's ``bool`` is a subclass of ``int``,
# so ``int(True) == 1`` and ``float(False) == 0.0`` would silently
# coerce ``window_days = true`` into a usable-but-wrong value.
# ``hai config validate`` already rejects this at the user surface
# (round-2 R2-3); this guard rejects it at the runtime surface so
# the two boundaries are defence-in-depth.
def _coerce_int(value: Any, *, key: str, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        raise ReviewSummaryThresholdError(
            f"policy.review_summary.{key}: expected number, got bool "
            f"({value!r}). Run `hai config validate` to surface every "
            f"such issue in your thresholds.toml."
        )
    if not isinstance(value, (int, float)):
        raise ReviewSummaryThresholdError(
            f"policy.review_summary.{key}: expected number, got "
            f"{type(value).__name__}. Run `hai config validate` for "
            f"the full diagnostic."
        )
    return int(value)


def _coerce_float(value: Any, *, key: str, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, bool):
        raise ReviewSummaryThresholdError(
            f"policy.review_summary.{key}: expected number, got bool "
            f"({value!r}). Run `hai config validate` to surface every "
            f"such issue in your thresholds.toml."
        )
    if not isinstance(value, (int, float)):
        raise ReviewSummaryThresholdError(
            f"policy.review_summary.{key}: expected number, got "
            f"{type(value).__name__}. Run `hai config validate` for "
            f"the full diagnostic."
        )
    return float(value)


def _resolve_thresholds(
    thresholds: Optional[dict[str, Any]],
) -> dict[str, Any]:
    """Return the ``policy.review_summary`` block from supplied or loaded
    thresholds. Falls back to safe v0.1.8 defaults when keys are missing.

    Raises ``ReviewSummaryThresholdError`` on bool-shaped or non-numeric
    values for any numeric leaf. The error message names
    ``hai config validate`` as the diagnostic tool. This is the runtime
    half of the W57-style defence-in-depth pattern (validator boundary
    + runtime boundary both reject the same class of malformed input).
    """

    effective = thresholds if thresholds is not None else load_thresholds()
    block = effective.get("policy", {}).get("review_summary", {})

    return {
        "window_days": _coerce_int(
            block.get("window_days"), key="window_days", default=7,
        ),
        "min_denominator": _coerce_int(
            block.get("min_denominator"),
            key="min_denominator", default=3,
        ),
        "recent_negative_threshold": _coerce_int(
            block.get("recent_negative_threshold"),
            key="recent_negative_threshold", default=4,
        ),
        "recent_positive_threshold": _coerce_int(
            block.get("recent_positive_threshold"),
            key="recent_positive_threshold", default=4,
        ),
        "mixed_token_lower_bound": _coerce_float(
            block.get("mixed_token_lower_bound"),
            key="mixed_token_lower_bound", default=0.4,
        ),
        "mixed_token_upper_bound": _coerce_float(
            block.get("mixed_token_upper_bound"),
            key="mixed_token_upper_bound", default=0.6,
        ),
    }


def _eligible_recommendations(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    domain: Optional[str],
    window_start: date,
    window_end: date,
) -> list[dict[str, Any]]:
    """Recommendations issued for a date inside the window."""

    sql = (
        "SELECT recommendation_id, for_date, action, confidence, domain "
        "FROM recommendation_log "
        "WHERE user_id = ? "
        "  AND for_date >= ? AND for_date <= ?"
    )
    params: list[Any] = [user_id, window_start.isoformat(), window_end.isoformat()]
    if domain is not None:
        sql += " AND domain = ?"
        params.append(domain)
    sql += " ORDER BY for_date, recommendation_id"

    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def _scheduled_reviews(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    domain: Optional[str],
    window_start: date,
    window_end: date,
) -> list[dict[str, Any]]:
    """Review events scheduled for a date inside the window."""

    sql = (
        "SELECT review_event_id, recommendation_id, review_at, domain "
        "FROM review_event "
        "WHERE user_id = ? "
        "  AND substr(review_at, 1, 10) >= ? "
        "  AND substr(review_at, 1, 10) <= ?"
    )
    params: list[Any] = [user_id, window_start.isoformat(), window_end.isoformat()]
    if domain is not None:
        sql += " AND domain = ?"
        params.append(domain)
    sql += " ORDER BY review_at, review_event_id"

    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def _recorded_outcomes(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    domain: Optional[str],
    window_start: date,
    window_end: date,
) -> list[dict[str, Any]]:
    """Outcomes recorded for a review whose review_at falls in the window.

    The window is keyed off ``review_event.review_at`` (not
    ``review_outcome.recorded_at``) so a late-recorded outcome still
    counts toward the window the review actually belonged to.
    """

    sql = (
        "SELECT o.outcome_id, o.review_event_id, o.recommendation_id, "
        "       o.followed_recommendation, o.self_reported_improvement, "
        "       o.intensity_delta, o.completed, o.duration_minutes, "
        "       o.pre_energy_score, o.post_energy_score, "
        "       o.re_linked_from_recommendation_id, o.domain, "
        "       e.review_at AS review_at "
        "FROM review_outcome o "
        "JOIN review_event e ON e.review_event_id = o.review_event_id "
        "WHERE o.user_id = ? "
        "  AND substr(e.review_at, 1, 10) >= ? "
        "  AND substr(e.review_at, 1, 10) <= ?"
    )
    params: list[Any] = [user_id, window_start.isoformat(), window_end.isoformat()]
    if domain is not None:
        sql += " AND o.domain = ?"
        params.append(domain)
    sql += " ORDER BY e.review_at, o.outcome_id"

    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def _intensity_distribution(
    outcomes: Iterable[dict[str, Any]],
) -> dict[str, int]:
    """Count outcomes by ``intensity_delta`` ordinal label."""

    distribution: dict[str, int] = {
        "much_lighter": 0,
        "lighter": 0,
        "same": 0,
        "harder": 0,
        "much_harder": 0,
    }
    for outcome in outcomes:
        label = outcome.get("intensity_delta")
        if label in distribution:
            distribution[label] += 1
    return distribution


def _compute_tokens(
    *,
    followed_count: int,
    followed_improved_count: int,
    followed_no_change_count: int,
    thresholds: dict[str, Any],
) -> list[str]:
    """Apply the four token rules; return tokens deterministically sorted.

    Tokens are orthogonal — multiple may fire when both the negative and
    positive thresholds are crossed in the same window (e.g. a noisy
    ledger). Order in the returned list is stable so snapshot diffs
    remain readable.
    """

    if followed_count < thresholds["min_denominator"]:
        return [TOKEN_INSUFFICIENT_DENOMINATOR]

    tokens: list[str] = []

    if followed_no_change_count >= thresholds["recent_negative_threshold"]:
        tokens.append(TOKEN_RECENT_NEGATIVE)
    if followed_improved_count >= thresholds["recent_positive_threshold"]:
        tokens.append(TOKEN_RECENT_POSITIVE)

    rate = (
        followed_improved_count / followed_count if followed_count > 0 else 0.0
    )
    if (
        thresholds["mixed_token_lower_bound"]
        <= rate
        <= thresholds["mixed_token_upper_bound"]
    ):
        tokens.append(TOKEN_MIXED)

    # Stable alphabetical ordering of the orthogonal tokens — keeps
    # snapshot diffs deterministic across runs.
    return sorted(tokens)


def _summarize_outcome_set(
    outcomes: list[dict[str, Any]],
    *,
    thresholds: dict[str, Any],
    eligible_recommendation_ids: list[str],
    scheduled_review_event_ids: list[str],
    window_start: date,
    window_end: date,
    as_of_date: date,
    domain_label: str,
) -> dict[str, Any]:
    """Reduce a domain-filtered outcome list to the summary dict shape."""

    followed_improved = 0
    followed_no_change = 0
    followed_unknown = 0
    not_followed = 0
    relinked = 0

    for outcome in outcomes:
        if outcome.get("re_linked_from_recommendation_id") is not None:
            relinked += 1
        if outcome["followed_recommendation"]:
            improved = outcome["self_reported_improvement"]
            if improved == 1 or improved is True:
                followed_improved += 1
            elif improved == 0 or improved is False:
                followed_no_change += 1
            else:
                followed_unknown += 1
        else:
            not_followed += 1

    followed_count = followed_improved + followed_no_change + followed_unknown
    recorded_count = len(outcomes)

    # ``followed_recommendation_rate`` uses the recorded outcome count as
    # the denominator. ``self_reported_improvement_rate`` uses
    # ``followed_count`` so the denominator matches the question — "of
    # the times the user actually followed the recommendation, how often
    # did they report improvement?" Both are ``None`` when the
    # denominator is zero so the consumer doesn't have to special-case
    # division-by-zero.
    followed_recommendation_rate: Optional[float] = (
        followed_count / recorded_count if recorded_count > 0 else None
    )
    self_reported_improvement_rate: Optional[float] = (
        followed_improved / followed_count if followed_count > 0 else None
    )

    tokens = _compute_tokens(
        followed_count=followed_count,
        followed_improved_count=followed_improved,
        followed_no_change_count=followed_no_change,
        thresholds=thresholds,
    )

    # ``pending`` / ``overdue`` / ``due`` are filled by the caller
    # (``build_review_summary``) using the event rows it already
    # fetched, so we don't re-query review_event here.

    return {
        "domain": domain_label,
        "window": {
            "days": (window_end - window_start).days + 1,
            "start": window_start.isoformat(),
            "end": window_end.isoformat(),
        },
        "eligible_recommendation_count": len(eligible_recommendation_ids),
        "scheduled_review_count": len(scheduled_review_event_ids),
        "due_review_count": 0,
        "recorded_outcome_count": recorded_count,
        "pending_review_count": 0,
        "overdue_review_count": 0,
        "followed_count": followed_count,
        "followed_improved_count": followed_improved,
        "followed_no_change_count": followed_no_change,
        "followed_unknown_count": followed_unknown,
        "not_followed_count": not_followed,
        "missing_improvement_count": followed_unknown,
        "relinked_outcome_count": relinked,
        "followed_recommendation_rate": followed_recommendation_rate,
        "self_reported_improvement_rate": self_reported_improvement_rate,
        "intensity_delta_distribution": _intensity_distribution(outcomes),
        "tokens": tokens,
        "source_recommendation_ids": list(eligible_recommendation_ids),
        "source_review_event_ids": list(scheduled_review_event_ids),
        "source_outcome_ids": [outcome["outcome_id"] for outcome in outcomes],
    }


def build_review_summary(
    conn: sqlite3.Connection,
    *,
    as_of_date: date,
    user_id: str,
    domain: Optional[str] = None,
    window_days: Optional[int] = None,
    thresholds: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build a deterministic review summary for one domain or all domains.

    Args:
        conn: open sqlite connection over the project state DB.
        as_of_date: civil date the window ends on (inclusive).
        user_id: scope to one user.
        domain: when supplied, returns one summary dict for that domain;
            when ``None``, returns a dict with one entry per v1 domain
            plus an ``aggregate`` entry covering the full union.
        window_days: override the configured window. Defaults to the
            value in ``thresholds["policy"]["review_summary"]
            ["window_days"]`` (or 7 if missing).
        thresholds: explicit threshold dict (e.g. tests). When ``None``,
            calls :func:`load_thresholds`.

    Returns:
        A dict whose shape depends on ``domain``:

        - ``domain="running"`` → returns the per-domain summary dict.
        - ``domain=None`` → returns
          ``{"as_of_date": ..., "window_days": N, "domains": {<d>: ...},
             "aggregate": {...}}``.

    Notes:
        - All counts and rates are visibility-only. Callers must not
          feed them into thresholds, classifiers, or X-rules in v0.1.8.
        - Outcomes are joined to events on ``review_event_id``; events
          are filtered by ``substr(review_at, 1, 10)`` to keep the
          window keyed off civil dates rather than UTC instants.
    """

    cfg = _resolve_thresholds(thresholds)
    effective_window = (
        int(window_days) if window_days is not None else cfg["window_days"]
    )
    if effective_window < 1:
        raise ValueError("window_days must be >= 1")

    window_end = as_of_date
    window_start = as_of_date - timedelta(days=effective_window - 1)

    def _summary_for(d: Optional[str]) -> dict[str, Any]:
        recs = _eligible_recommendations(
            conn,
            user_id=user_id,
            domain=d,
            window_start=window_start,
            window_end=window_end,
        )
        events = _scheduled_reviews(
            conn,
            user_id=user_id,
            domain=d,
            window_start=window_start,
            window_end=window_end,
        )
        outcomes = _recorded_outcomes(
            conn,
            user_id=user_id,
            domain=d,
            window_start=window_start,
            window_end=window_end,
        )

        summary = _summarize_outcome_set(
            outcomes,
            thresholds=cfg,
            eligible_recommendation_ids=[r["recommendation_id"] for r in recs],
            scheduled_review_event_ids=[
                e["review_event_id"] for e in events
            ],
            window_start=window_start,
            window_end=window_end,
            as_of_date=as_of_date,
            domain_label=d if d is not None else "aggregate",
        )

        # Bucket pending vs overdue using the event rows we already fetched.
        answered = {o["review_event_id"] for o in outcomes}
        pending = 0
        overdue = 0
        due = 0
        for event in events:
            event_date_str = event["review_at"][:10]
            event_date = date.fromisoformat(event_date_str)
            if event["review_event_id"] in answered:
                continue
            if event_date <= as_of_date:
                overdue += 1
            else:
                pending += 1
            if event_date <= as_of_date:
                due += 1

        summary["pending_review_count"] = pending
        summary["overdue_review_count"] = overdue
        summary["due_review_count"] = due
        return summary

    if domain is not None:
        return _summary_for(domain)

    per_domain = {d: _summary_for(d) for d in DOMAINS}
    aggregate = _summary_for(None)

    return {
        "as_of_date": as_of_date.isoformat(),
        "window_days": effective_window,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "domains": per_domain,
        "aggregate": aggregate,
    }
