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
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from health_agent_infra.core.schemas import (
    ReviewEvent,
    ReviewOutcome,
)


@dataclass(frozen=True)
class ReLinkResolution:
    """Result of resolving a review outcome's target recommendation per D1.

    Three effective cases:

    - **Passthrough** — the target recommendation is on a canonical-leaf
      plan. ``recommendation_id`` equals the caller's input; the two
      ``re_link_*`` fields are ``None``; ``refuse`` is ``False``.
    - **Re-linked** — the target recommendation is on a superseded plan
      and the canonical leaf has a matching-domain rec for the same
      ``for_date``. ``recommendation_id`` is the leaf rec id;
      ``re_linked_from_recommendation_id`` is the caller's input;
      ``re_link_note`` is a short human-readable message.
    - **Refused** — the target recommendation is on a superseded plan
      and the canonical leaf has no matching-domain rec. ``refuse`` is
      ``True``; ``refusal_reason`` explains. The CLI converts this to
      exit code ``USER_INPUT``.
    """

    recommendation_id: str
    re_linked_from_recommendation_id: Optional[str] = None
    re_link_note: Optional[str] = None
    refuse: bool = False
    refusal_reason: Optional[str] = None


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

    from health_agent_infra.core.privacy import secure_directory, secure_file

    base_dir = base_dir.resolve()
    secure_directory(base_dir, create=True)
    events_path = base_dir / "review_events.jsonl"

    if not _event_already_written(events_path, event.review_event_id):
        with events_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
    secure_file(events_path)
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
    completed: Optional[bool] = None,
    intensity_delta: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    pre_energy_score: Optional[int] = None,
    post_energy_score: Optional[int] = None,
    disagreed_firing_ids: Optional[list[str]] = None,
    re_linked_from_recommendation_id: Optional[str] = None,
    re_link_note: Optional[str] = None,
) -> ReviewOutcome:
    """Persist a user-supplied outcome for a previously scheduled review event.

    ``domain`` defaults to the event's domain (which itself defaults to
    ``"recovery"``) so outcomes stay aligned with their owning event.

    The M4 enrichment kwargs (``completed`` / ``intensity_delta`` /
    ``duration_minutes`` / ``pre_energy_score`` / ``post_energy_score`` /
    ``disagreed_firing_ids``) are all optional. Callers that don't
    populate them land NULL columns — which is how pre-M4 outcomes
    always looked, so the expansion is backward-compatible.

    When the outcome is being recorded against a superseded plan's
    recommendation, ``event.recommendation_id`` should already reflect
    the re-linked (canonical leaf) id; the two ``re_link_*`` kwargs
    capture the audit trail. That resolution happens in
    :func:`resolve_review_relink` so this function stays a thin writer.
    """

    from health_agent_infra.core.privacy import secure_directory, secure_file

    now = now or datetime.now(timezone.utc)
    base_dir = base_dir.resolve()
    secure_directory(base_dir, create=True)
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
        completed=completed,
        intensity_delta=intensity_delta,
        duration_minutes=duration_minutes,
        pre_energy_score=pre_energy_score,
        post_energy_score=post_energy_score,
        disagreed_firing_ids=disagreed_firing_ids,
        re_linked_from_recommendation_id=re_linked_from_recommendation_id,
        re_link_note=re_link_note,
    )

    with outcomes_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(outcome.to_dict(), sort_keys=True) + "\n")
    secure_file(outcomes_path)
    return outcome


def resolve_review_relink(
    conn: sqlite3.Connection,
    *,
    recommendation_id: str,
) -> ReLinkResolution:
    """Resolve the effective recommendation id for a review outcome write.

    Implements D1 §review record behavior. Reads three tables:

    1. ``recommendation_log`` — locate the owning plan, domain, for_date.
    2. ``daily_plan`` — test ``superseded_by_plan_id``; walk forward to
       the canonical leaf.
    3. ``recommendation_log`` again — find the leaf plan's
       matching-domain recommendation for the same ``for_date``.

    Returns one of three :class:`ReLinkResolution` shapes. Never raises;
    every failure mode is encoded in the returned value so callers can
    branch on ``refuse`` / ``re_linked_from_recommendation_id`` without
    exception handling.

    The cycle-guard on chain walking mirrors
    :func:`_resolve_canonical_leaf_plan_id` in ``core/synthesis.py`` —
    forward-link corruption would otherwise silently hang.
    """

    rec_row = conn.execute(
        "SELECT daily_plan_id, domain, for_date "
        "FROM recommendation_log WHERE recommendation_id = ?",
        (recommendation_id,),
    ).fetchone()
    if rec_row is None:
        # Unknown rec id — passthrough and let downstream writes surface
        # the FK violation if any. Pre-D1 behavior for this edge case.
        return ReLinkResolution(recommendation_id=recommendation_id)

    owning_plan_id = rec_row["daily_plan_id"]
    domain = rec_row["domain"]
    for_date = rec_row["for_date"]
    if owning_plan_id is None:
        return ReLinkResolution(recommendation_id=recommendation_id)

    leaf_id = _walk_plan_chain_to_leaf(conn, plan_id=owning_plan_id)
    if leaf_id is None or leaf_id == owning_plan_id:
        return ReLinkResolution(recommendation_id=recommendation_id)

    leaf_rec_row = conn.execute(
        "SELECT recommendation_id FROM recommendation_log "
        "WHERE daily_plan_id = ? AND domain = ? AND for_date = ? "
        "ORDER BY issued_at DESC LIMIT 1",
        (leaf_id, domain, for_date),
    ).fetchone()
    if leaf_rec_row is None:
        return ReLinkResolution(
            recommendation_id=recommendation_id,
            refuse=True,
            refusal_reason=(
                f"recommendation {recommendation_id} is on plan "
                f"{owning_plan_id}, which has been superseded by {leaf_id}; "
                f"the canonical leaf has no matching-domain recommendation "
                f"({domain} for {for_date}). Refusing to create an orphaned "
                f"outcome."
            ),
        )

    leaf_rec_id = leaf_rec_row["recommendation_id"]
    return ReLinkResolution(
        recommendation_id=leaf_rec_id,
        re_linked_from_recommendation_id=recommendation_id,
        re_link_note=(
            f"re-linked from {recommendation_id} to {leaf_rec_id}: "
            f"owning plan {owning_plan_id} superseded by {leaf_id}."
        ),
    )


def _walk_plan_chain_to_leaf(
    conn: sqlite3.Connection,
    *,
    plan_id: str,
) -> Optional[str]:
    """Walk ``daily_plan.superseded_by_plan_id`` from ``plan_id`` to a leaf.

    Returns the plan id whose ``superseded_by_plan_id`` is NULL, or
    ``None`` if ``plan_id`` doesn't exist. Cycle-guarded.
    """

    current: Optional[str] = plan_id
    seen: set[str] = set()
    while current is not None:
        if current in seen:
            return current
        seen.add(current)
        row = conn.execute(
            "SELECT superseded_by_plan_id FROM daily_plan "
            "WHERE daily_plan_id = ?",
            (current,),
        ).fetchone()
        if row is None:
            return None if current == plan_id else current
        next_id = row["superseded_by_plan_id"]
        if next_id is None:
            return current
        current = next_id
    return None


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


# M4 — intensity_delta ordinal axis. Surfaced alongside the CLI's
# ``INTENSITY_DELTA_CHOICES`` as a single source of truth for how an
# ordinal "intensity_delta" string maps to a numeric score. Unknown
# strings are skipped during aggregation rather than silently treated
# as zero, because "unrecognised label" and "user reported same
# intensity" are not the same signal.
INTENSITY_DELTA_ORDINAL: dict[str, int] = {
    "much_lighter": -2,
    "lighter": -1,
    "same": 0,
    "harder": 1,
    "much_harder": 2,
}


def summarize_review_history(
    outcomes: list[ReviewOutcome],
    *,
    domain: Optional[str] = None,
) -> dict[str, Any]:
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

    M4 enrichment aggregates are emitted under the ``enriched`` key
    **only when at least one outcome in the filtered input populates at
    least one enriched field**. This keeps the legacy shape intact for
    callers that only see pre-M4 rows and avoids inventing zero-valued
    aggregates for samples that were never collected. The ``enriched``
    dict carries:
      - ``completion_rate``: fraction of outcomes with ``completed=True``
        out of outcomes where ``completed`` was recorded. ``None`` when
        no outcome recorded a completion.
      - ``completion_count``: count contributing to ``completion_rate``.
      - ``mean_intensity_delta``: mean of
        ``INTENSITY_DELTA_ORDINAL[intensity_delta]`` across outcomes
        whose ``intensity_delta`` is a recognised key. ``None`` when no
        outcome contributed.
      - ``intensity_delta_count``: count contributing.
      - ``mean_energy_delta``: mean of ``post - pre`` across outcomes
        where both scores are populated. ``None`` when no outcome
        contributed.
      - ``energy_delta_count``: count contributing.
    """

    if domain is not None:
        outcomes = [o for o in outcomes if o.domain == domain]

    summary: dict[str, Any] = {
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

    enriched = _enriched_aggregates(outcomes)
    if enriched is not None:
        summary["enriched"] = enriched

    return summary


def _enriched_aggregates(
    outcomes: list[ReviewOutcome],
) -> Optional[dict[str, Any]]:
    """Compute the M4 enriched-tier aggregates, or return ``None``.

    Returns ``None`` when no outcome in ``outcomes`` populates any of the
    enrichment fields, so the legacy 5-key summary shape is preserved
    for callers that only see pre-M4 data.
    """

    completed_values = [
        o.completed for o in outcomes if o.completed is not None
    ]
    intensity_values = [
        INTENSITY_DELTA_ORDINAL[o.intensity_delta]
        for o in outcomes
        if o.intensity_delta in INTENSITY_DELTA_ORDINAL
    ]
    energy_deltas = [
        o.post_energy_score - o.pre_energy_score
        for o in outcomes
        if o.pre_energy_score is not None and o.post_energy_score is not None
    ]

    has_any = (
        bool(completed_values)
        or bool(intensity_values)
        or bool(energy_deltas)
        or any(
            o.duration_minutes is not None
            or o.disagreed_firing_ids is not None
            for o in outcomes
        )
    )
    if not has_any:
        return None

    completion_rate = (
        sum(1 for v in completed_values if v) / len(completed_values)
        if completed_values
        else None
    )
    mean_intensity_delta = (
        sum(intensity_values) / len(intensity_values)
        if intensity_values
        else None
    )
    mean_energy_delta = (
        sum(energy_deltas) / len(energy_deltas)
        if energy_deltas
        else None
    )

    return {
        "completion_rate": completion_rate,
        "completion_count": len(completed_values),
        "mean_intensity_delta": mean_intensity_delta,
        "intensity_delta_count": len(intensity_values),
        "mean_energy_delta": mean_energy_delta,
        "energy_delta_count": len(energy_deltas),
    }
