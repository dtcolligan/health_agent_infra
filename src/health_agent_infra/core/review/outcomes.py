"""REVIEW layer.

Schedules the next-day review event for an emitted recommendation, and records
the review outcome once the user provides a response. Review outcomes are
appended to a local JSONL and linked to the originating recommendation via
recommendation_id.

Every event + outcome carries a ``domain`` so per-domain review summaries can
split recovery vs running (vs sleep/stress/strength/nutrition as those land).
Backward compatibility: when callers don't supply a domain, the runtime
resolves it from the recommendation object (``.domain`` attribute) or falls
back to ``"recovery"`` — matching the migration-003 backfill default.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from health_agent_infra.core.schemas import (
    ReviewEvent,
    ReviewOutcome,
)


def schedule_review(
    recommendation: Any,
    *,
    base_dir: Path,
    domain: Optional[str] = None,
) -> ReviewEvent:
    """Persist a pending review event for the given recommendation.

    ``recommendation`` is duck-typed: any object with ``recommendation_id``,
    ``user_id``, and a ``follow_up`` bearing ``review_event_id`` /
    ``review_at`` / ``review_question`` works. ``domain`` is taken from the
    explicit kwarg, then from ``recommendation.domain``, then defaults to
    ``"recovery"`` for v1 recovery-only callers.
    """

    resolved_domain = (
        domain
        if domain is not None
        else getattr(recommendation, "domain", "recovery")
    )
    event = ReviewEvent(
        review_event_id=recommendation.follow_up.review_event_id,
        recommendation_id=recommendation.recommendation_id,
        user_id=recommendation.user_id,
        review_at=recommendation.follow_up.review_at,
        review_question=recommendation.follow_up.review_question,
        domain=resolved_domain,
    )
    return persist_review_event(event, base_dir=base_dir)


def persist_review_event(event: ReviewEvent, *, base_dir: Path) -> ReviewEvent:
    """Append the event to ``review_events.jsonl`` idempotently.

    Separated from :func:`schedule_review` so non-recovery callers (e.g. the
    CLI reading a running recommendation payload) can build a
    ``ReviewEvent`` directly without duck-typing through a recommendation
    object or re-running recovery-specific validation.
    """

    base_dir = base_dir.resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    events_path = base_dir / "review_events.jsonl"

    if not _event_already_written(events_path, event.review_event_id):
        with events_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
    return event


def record_review_outcome(
    event: ReviewEvent,
    *,
    base_dir: Path,
    followed_recommendation: bool,
    self_reported_improvement: Optional[bool],
    free_text: Optional[str] = None,
    now: Optional[datetime] = None,
    domain: Optional[str] = None,
) -> ReviewOutcome:
    """Persist a user-supplied outcome for a previously scheduled review event.

    ``domain`` defaults to the event's domain (which itself defaults to
    ``"recovery"``) so outcomes stay aligned with their owning event.
    """

    now = now or datetime.now(timezone.utc)
    base_dir = base_dir.resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    outcomes_path = base_dir / "review_outcomes.jsonl"

    resolved_domain = domain if domain is not None else event.domain
    outcome = ReviewOutcome(
        review_event_id=event.review_event_id,
        recommendation_id=event.recommendation_id,
        user_id=event.user_id,
        recorded_at=now,
        followed_recommendation=followed_recommendation,
        self_reported_improvement=self_reported_improvement,
        free_text=free_text,
        domain=resolved_domain,
    )

    with outcomes_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(outcome.to_dict(), sort_keys=True) + "\n")
    return outcome


def _event_already_written(path: Path, review_event_id: str) -> bool:
    if not path.exists():
        return False
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("review_event_id") == review_event_id:
                return True
    return False


def summarize_review_history(
    outcomes: list[ReviewOutcome],
    *,
    domain: Optional[str] = None,
) -> dict[str, int]:
    """Count review outcomes by category. Deterministic bookkeeping, not judgment.

    The runtime surfaces structured summary state; the LLM consumer forms
    its own view about what the numbers mean for future recommendation
    confidence. This function does not encode any opinion about how good
    or bad a given outcome distribution is.

    When ``domain`` is provided, only outcomes whose ``.domain`` matches
    the filter are counted — ensures ``hai review summary --domain running``
    never bleeds recovery rows (or vice versa) into its counts.

    Returned keys (all non-negative integers, always present):
      - ``total``: total number of outcomes in the filtered input.
      - ``followed_improved``: followed recommendation AND self-reported
        improvement was ``True``.
      - ``followed_no_change``: followed recommendation AND self-reported
        improvement was ``False``.
      - ``followed_unknown``: followed recommendation AND self-reported
        improvement was ``None`` (ambiguous).
      - ``not_followed``: did not follow the recommendation (improvement
        field ignored — no counterfactual).

    The four non-total keys always sum to ``total``; a consumer can derive
    any rate it wants from these counts without the runtime taking a
    position on which rate matters.
    """

    if domain is not None:
        outcomes = [o for o in outcomes if o.domain == domain]

    summary = {
        "total": len(outcomes),
        "followed_improved": 0,
        "followed_no_change": 0,
        "followed_unknown": 0,
        "not_followed": 0,
    }

    for outcome in outcomes:
        if not outcome.followed_recommendation:
            summary["not_followed"] += 1
            continue
        if outcome.self_reported_improvement is True:
            summary["followed_improved"] += 1
        elif outcome.self_reported_improvement is False:
            summary["followed_no_change"] += 1
        else:
            summary["followed_unknown"] += 1

    return summary
