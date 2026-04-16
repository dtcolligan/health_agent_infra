"""REVIEW layer.

Schedules the next-day review event for an emitted recommendation, and records
the review outcome once the user provides a response. Review outcomes are
appended to a local JSONL and linked to the originating recommendation via
recommendation_id.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from health_model.recovery_readiness_v1.schemas import (
    ReviewEvent,
    ReviewOutcome,
    TrainingRecommendation,
)


def schedule_review(
    recommendation: TrainingRecommendation,
    *,
    base_dir: Path,
) -> ReviewEvent:
    """Persist a pending review event for the given recommendation."""

    base_dir = base_dir.resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    events_path = base_dir / "review_events.jsonl"

    event = ReviewEvent(
        review_event_id=recommendation.follow_up.review_event_id,
        recommendation_id=recommendation.recommendation_id,
        user_id=recommendation.user_id,
        review_at=recommendation.follow_up.review_at,
        review_question=recommendation.follow_up.review_question,
    )

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
) -> ReviewOutcome:
    """Persist a user-supplied outcome for a previously scheduled review event."""

    now = now or datetime.now(timezone.utc)
    base_dir = base_dir.resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    outcomes_path = base_dir / "review_outcomes.jsonl"

    outcome = ReviewOutcome(
        review_event_id=event.review_event_id,
        recommendation_id=event.recommendation_id,
        user_id=event.user_id,
        recorded_at=now,
        followed_recommendation=followed_recommendation,
        self_reported_improvement=self_reported_improvement,
        free_text=free_text,
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


def derive_confidence_adjustment(outcomes: list[ReviewOutcome]) -> float:
    """Return a confidence delta in ``[-0.5, 0.5]`` derived from review history.

    Structural stub. No persistence, no per-user state, no learning loop: a
    pure function over a list of past ``ReviewOutcome`` records. Callers may
    use the returned delta to nudge future recommendation confidence.

    TODO(founder): refine these first-pass deltas and add a decay term.

    First-pass rules (explicit so a reviewer can push back):
      - ``followed_recommendation=True`` + ``self_reported_improvement=True``
        => +0.05 per outcome. System proposed something that helped.
      - ``followed_recommendation=True`` + ``self_reported_improvement=False``
        => -0.02 per outcome. Followed but did not help. Smaller magnitude
        than the positive case because non-improvement has many benign
        explanations (life stress, partial adherence, measurement noise).
      - ``followed_recommendation=True`` + ``self_reported_improvement=None``
        => 0.0. Ambiguous.
      - ``followed_recommendation=False`` => 0.0. No counterfactual available;
        the user may have disagreed for reasons unrelated to correctness.
      - Sum clamped to ``[-0.25, 0.25]`` — half the contract envelope of
        ``[-0.5, 0.5]`` — so one bad week cannot collapse the system.
      - Empty history => 0.0.
    """

    if not outcomes:
        return 0.0

    delta = 0.0
    for outcome in outcomes:
        if not outcome.followed_recommendation:
            continue
        if outcome.self_reported_improvement is True:
            delta += 0.05
        elif outcome.self_reported_improvement is False:
            delta -= 0.02

    return max(-0.25, min(0.25, delta))
