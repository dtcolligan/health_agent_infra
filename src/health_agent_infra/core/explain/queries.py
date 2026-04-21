"""Read-only loaders for the explain bundle.

The bundle reconstructs the audit chain a recommendation already left in
SQLite: which proposals fed synthesis, which X-rules fired, what was
finally committed, what supersession linkage applies, and which review
outcomes (if any) followed.

Nothing in this module opens a write transaction or recomputes runtime
state — it only reads ``proposal_log`` / ``daily_plan`` /
``x_rule_firing`` / ``recommendation_log`` / ``review_event`` /
``review_outcome``. If a piece of state was never written, the
corresponding field comes back empty rather than fabricated.

Two entry points:

- :func:`load_bundle_by_daily_plan_id` — exact plan, including
  ``_v<N>`` superseded variants.
- :func:`load_bundle_for_date` — the canonical plan for
  ``(for_date, user_id)``; the bundle's ``supersedes`` /
  ``superseded_by`` fields point at any chained variants so a caller
  can walk the chain explicitly.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

from health_agent_infra.core.schemas import canonical_daily_plan_id
from health_agent_infra.core.synthesis_policy import public_name_for


class ExplainNotFoundError(LookupError):
    """Raised when the requested plan id (or date/user) has no committed plan."""


# Phase A vs Phase B classification — synthesis_policy uses ``tier='adjust'``
# only for Phase B (X9 today). Every other tier (``soften`` / ``block`` /
# ``cap_confidence`` / ``restructure``) is Phase A. Pinning the rule here
# rather than reaching into ``synthesis_policy`` keeps the explain surface
# decoupled from runtime evaluator wiring.
_PHASE_B_TIERS: frozenset[str] = frozenset({"adjust"})


@dataclass(frozen=True)
class ExplainProposal:
    proposal_id: str
    domain: str
    schema_version: str
    action: str
    action_detail: Optional[Any]
    confidence: str
    rationale: list[str]
    uncertainty: list[str]
    policy_decisions: list[dict[str, Any]]
    produced_at: Optional[str]
    validated_at: Optional[str]


@dataclass(frozen=True)
class ExplainXRuleFiring:
    firing_id: int
    rule_id: str
    tier: str
    affected_domain: str
    trigger_note: str
    mutation: Optional[Any]
    source_signals: dict[str, Any]
    orphan: bool
    fired_at: str
    public_name: Optional[str] = None


@dataclass(frozen=True)
class ExplainRecommendation:
    recommendation_id: str
    domain: str
    schema_version: str
    action: str
    action_detail: Optional[Any]
    confidence: str
    bounded: bool
    rationale: list[str]
    uncertainty: list[str]
    policy_decisions: list[dict[str, Any]]
    issued_at: str
    review_event_id: Optional[str]
    review_question: Optional[str]
    supersedes: Optional[str]
    superseded_by: Optional[str]


@dataclass(frozen=True)
class ExplainReviewOutcome:
    outcome_id: int
    recorded_at: str
    followed_recommendation: bool
    self_reported_improvement: Optional[bool]
    free_text: Optional[str]


@dataclass(frozen=True)
class ExplainReview:
    review_event_id: str
    recommendation_id: str
    domain: str
    review_at: str
    review_question: str
    outcomes: list[ExplainReviewOutcome] = field(default_factory=list)


@dataclass(frozen=True)
class ExplainPlan:
    daily_plan_id: str
    user_id: str
    for_date: str
    synthesized_at: str
    agent_version: Optional[str]
    supersedes: Optional[str]
    superseded_by: Optional[str]
    x_rules_fired: list[str]
    synthesis_meta: dict[str, Any]


@dataclass(frozen=True)
class ExplainUserMemory:
    """User-memory entries active at the plan's ``for_date``.

    A bounded read-only slice of the ``user_memory`` table (migration
    007). Added in Phase D alongside the existing plan / proposals /
    firings / recommendations / reviews fields — the explain reader
    does not retrofit memory into any prior bundle key.

    The memory rows are not written inside the synthesis transaction
    and are therefore not part of the audit chain proper; they are
    exposed here as *context* that was active when the plan landed, so
    a reader can see what durable user context the skills had access
    to. See ``reporting/docs/explainability.md`` §3 + ``memory_model.md``
    §2.1 for framing.
    """

    as_of: Optional[str]
    entries: list[dict[str, Any]] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class ExplainBundle:
    plan: ExplainPlan
    proposals: list[ExplainProposal]
    phase_a_firings: list[ExplainXRuleFiring]
    phase_b_firings: list[ExplainXRuleFiring]
    recommendations: list[ExplainRecommendation]
    reviews: list[ExplainReview]
    user_memory: ExplainUserMemory = field(
        default_factory=lambda: ExplainUserMemory(as_of=None)
    )


# ---------------------------------------------------------------------------
# Public loaders
# ---------------------------------------------------------------------------


def load_bundle_for_date(
    conn: sqlite3.Connection,
    *,
    for_date: date,
    user_id: str,
) -> ExplainBundle:
    """Load the canonical plan bundle for ``(for_date, user_id)``.

    Raises :class:`ExplainNotFoundError` when no canonical plan exists
    for the key. The bundle's :attr:`ExplainPlan.supersedes` /
    :attr:`ExplainPlan.superseded_by` fields point at any ``_v<N>``
    variants so the caller can walk the chain by issuing
    :func:`load_bundle_by_daily_plan_id` for each id in turn.
    """

    plan_id = canonical_daily_plan_id(for_date, user_id)
    return load_bundle_by_daily_plan_id(conn, daily_plan_id=plan_id)


def load_bundle_by_daily_plan_id(
    conn: sqlite3.Connection,
    *,
    daily_plan_id: str,
) -> ExplainBundle:
    """Load the explain bundle for an exact ``daily_plan_id``.

    Raises :class:`ExplainNotFoundError` when the plan id is unknown.
    """

    plan_row = conn.execute(
        "SELECT * FROM daily_plan WHERE daily_plan_id = ?",
        (daily_plan_id,),
    ).fetchone()
    if plan_row is None:
        raise ExplainNotFoundError(
            f"no daily_plan row for daily_plan_id={daily_plan_id!r}"
        )

    plan = _hydrate_plan(conn, plan_row)
    proposals = _load_proposals_for_plan(conn, daily_plan_id=daily_plan_id)
    phase_a, phase_b = _load_firings_for_plan(conn, daily_plan_id=daily_plan_id)
    recommendations = _load_recommendations_for_plan(
        conn, daily_plan_id=daily_plan_id,
    )
    reviews = _load_reviews_for_recommendations(
        conn,
        recommendation_ids=[r.recommendation_id for r in recommendations],
    )
    user_memory = _load_user_memory_for_plan(
        conn,
        user_id=plan.user_id,
        for_date=plan.for_date,
    )

    return ExplainBundle(
        plan=plan,
        proposals=proposals,
        phase_a_firings=phase_a,
        phase_b_firings=phase_b,
        recommendations=recommendations,
        reviews=reviews,
        user_memory=user_memory,
    )


# ---------------------------------------------------------------------------
# Hydration helpers
# ---------------------------------------------------------------------------


def _hydrate_plan(
    conn: sqlite3.Connection, plan_row: sqlite3.Row,
) -> ExplainPlan:
    meta = _loads(plan_row["synthesis_meta_json"]) or {}
    superseded_by = meta.get("superseded_by") if isinstance(meta, dict) else None

    # supersedes: the prior plan whose synthesis_meta_json.superseded_by
    # equals this plan's id. Survives chain ordering — works for the
    # canonical → _v2 → _v3 chain because each link gets its own row.
    supersedes_row = conn.execute(
        "SELECT daily_plan_id FROM daily_plan "
        "WHERE json_extract(synthesis_meta_json, '$.superseded_by') = ?",
        (plan_row["daily_plan_id"],),
    ).fetchone()
    supersedes = supersedes_row["daily_plan_id"] if supersedes_row else None

    return ExplainPlan(
        daily_plan_id=plan_row["daily_plan_id"],
        user_id=plan_row["user_id"],
        for_date=plan_row["for_date"],
        synthesized_at=plan_row["synthesized_at"],
        agent_version=plan_row["agent_version"],
        supersedes=supersedes,
        superseded_by=superseded_by,
        x_rules_fired=_loads(plan_row["x_rules_fired_json"]) or [],
        synthesis_meta=meta if isinstance(meta, dict) else {},
    )


def _load_proposals_for_plan(
    conn: sqlite3.Connection, *, daily_plan_id: str,
) -> list[ExplainProposal]:
    rows = conn.execute(
        "SELECT proposal_id, domain, schema_version, action, "
        "  payload_json, confidence, produced_at, validated_at "
        "FROM proposal_log WHERE daily_plan_id = ? "
        "ORDER BY domain, proposal_id",
        (daily_plan_id,),
    ).fetchall()
    out: list[ExplainProposal] = []
    for row in rows:
        payload = _loads(row["payload_json"]) or {}
        out.append(
            ExplainProposal(
                proposal_id=row["proposal_id"],
                domain=row["domain"],
                schema_version=row["schema_version"],
                action=row["action"],
                action_detail=payload.get("action_detail"),
                confidence=row["confidence"],
                rationale=list(payload.get("rationale") or []),
                uncertainty=list(payload.get("uncertainty") or []),
                policy_decisions=list(payload.get("policy_decisions") or []),
                produced_at=row["produced_at"],
                validated_at=row["validated_at"],
            )
        )
    return out


def _load_firings_for_plan(
    conn: sqlite3.Connection, *, daily_plan_id: str,
) -> tuple[list[ExplainXRuleFiring], list[ExplainXRuleFiring]]:
    rows = conn.execute(
        "SELECT firing_id, x_rule_id, tier, affected_domain, "
        "  trigger_note, mutation_json, source_signals_json, "
        "  orphan, fired_at "
        "FROM x_rule_firing WHERE daily_plan_id = ? "
        "ORDER BY firing_id",
        (daily_plan_id,),
    ).fetchall()
    phase_a: list[ExplainXRuleFiring] = []
    phase_b: list[ExplainXRuleFiring] = []
    for row in rows:
        firing = ExplainXRuleFiring(
            firing_id=int(row["firing_id"]),
            rule_id=row["x_rule_id"],
            tier=row["tier"],
            affected_domain=row["affected_domain"],
            trigger_note=row["trigger_note"],
            mutation=_loads(row["mutation_json"]),
            source_signals=_loads(row["source_signals_json"]) or {},
            orphan=bool(row["orphan"]),
            fired_at=row["fired_at"],
            public_name=public_name_for(row["x_rule_id"]),
        )
        if firing.tier in _PHASE_B_TIERS:
            phase_b.append(firing)
        else:
            phase_a.append(firing)
    return phase_a, phase_b


def _load_recommendations_for_plan(
    conn: sqlite3.Connection, *, daily_plan_id: str,
) -> list[ExplainRecommendation]:
    # ``daily_plan_id`` lives inside ``payload_json`` (recommendation_log
    # carries no FK column for it), so we json_extract on lookup. Same
    # pattern :func:`delete_canonical_plan_cascade` uses on the write side.
    rows = conn.execute(
        "SELECT recommendation_id, domain, action, confidence, "
        "  bounded, payload_json, issued_at "
        "FROM recommendation_log "
        "WHERE json_extract(payload_json, '$.daily_plan_id') = ? "
        "ORDER BY domain, recommendation_id",
        (daily_plan_id,),
    ).fetchall()
    out: list[ExplainRecommendation] = []
    for row in rows:
        payload = _loads(row["payload_json"]) or {}
        follow_up = payload.get("follow_up") or {}
        out.append(
            ExplainRecommendation(
                recommendation_id=row["recommendation_id"],
                domain=row["domain"],
                schema_version=payload.get("schema_version", ""),
                action=row["action"],
                action_detail=payload.get("action_detail"),
                confidence=row["confidence"],
                bounded=bool(row["bounded"]),
                rationale=list(payload.get("rationale") or []),
                uncertainty=list(payload.get("uncertainty") or []),
                policy_decisions=list(payload.get("policy_decisions") or []),
                issued_at=row["issued_at"],
                review_event_id=follow_up.get("review_event_id") if isinstance(follow_up, dict) else None,
                review_question=follow_up.get("review_question") if isinstance(follow_up, dict) else None,
                supersedes=payload.get("supersedes"),
                superseded_by=payload.get("superseded_by"),
            )
        )
    return out


def _load_reviews_for_recommendations(
    conn: sqlite3.Connection,
    *,
    recommendation_ids: list[str],
) -> list[ExplainReview]:
    if not recommendation_ids:
        return []

    placeholders = ",".join(["?"] * len(recommendation_ids))
    event_rows = conn.execute(
        f"SELECT review_event_id, recommendation_id, domain, "
        f"  review_at, review_question "
        f"FROM review_event "
        f"WHERE recommendation_id IN ({placeholders}) "
        f"ORDER BY review_at, review_event_id",
        recommendation_ids,
    ).fetchall()
    if not event_rows:
        return []

    event_ids = [r["review_event_id"] for r in event_rows]
    outcome_placeholders = ",".join(["?"] * len(event_ids))
    outcome_rows = conn.execute(
        f"SELECT outcome_id, review_event_id, recorded_at, "
        f"  followed_recommendation, self_reported_improvement, free_text "
        f"FROM review_outcome "
        f"WHERE review_event_id IN ({outcome_placeholders}) "
        f"ORDER BY recorded_at, outcome_id",
        event_ids,
    ).fetchall()

    outcomes_by_event: dict[str, list[ExplainReviewOutcome]] = {}
    for row in outcome_rows:
        outcomes_by_event.setdefault(row["review_event_id"], []).append(
            ExplainReviewOutcome(
                outcome_id=int(row["outcome_id"]),
                recorded_at=row["recorded_at"],
                followed_recommendation=bool(row["followed_recommendation"]),
                self_reported_improvement=(
                    None if row["self_reported_improvement"] is None
                    else bool(row["self_reported_improvement"])
                ),
                free_text=row["free_text"],
            )
        )

    return [
        ExplainReview(
            review_event_id=row["review_event_id"],
            recommendation_id=row["recommendation_id"],
            domain=row["domain"],
            review_at=row["review_at"],
            review_question=row["review_question"],
            outcomes=outcomes_by_event.get(row["review_event_id"], []),
        )
        for row in event_rows
    ]


def _load_user_memory_for_plan(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    for_date: str,
) -> ExplainUserMemory:
    """Return the user-memory bundle active at the plan's ``for_date``.

    Degrades to an empty bundle when the ``user_memory`` table is
    absent (DB predates migration 007). Does not raise — the existing
    explain surfaces must keep working on a pre-007 DB; the empty
    bundle is an honest signal that no memory was recorded here.
    """

    from datetime import date as _date

    from health_agent_infra.core.memory import (
        build_user_memory_bundle,
        bundle_to_dict,
    )

    try:
        as_of = _date.fromisoformat(for_date)
        bundle = build_user_memory_bundle(conn, user_id=user_id, as_of=as_of)
    except sqlite3.OperationalError:
        return ExplainUserMemory(as_of=None, entries=[], counts={
            "goal": 0, "preference": 0, "constraint": 0,
            "context": 0, "total": 0,
        })

    serialised = bundle_to_dict(bundle)
    return ExplainUserMemory(
        as_of=serialised["as_of"],
        entries=list(serialised["entries"]),
        counts=dict(serialised["counts"]),
    )


def _loads(blob: Optional[str]) -> Any:
    if blob is None or blob == "":
        return None
    try:
        return json.loads(blob)
    except (TypeError, ValueError):
        return None
