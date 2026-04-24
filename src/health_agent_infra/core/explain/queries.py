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
from health_agent_infra.core.synthesis_policy import (
    description_for,
    public_name_for,
)


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
    human_explanation: Optional[str] = None


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
class ExplainPlannedRecommendation:
    """Pre-X-rule aggregate recommendation shape for one domain.

    Sourced from the ``planned_recommendation`` table (migration 011).
    Mirrors the essential fields of ``ExplainRecommendation`` so the
    three-state audit view (planned / adapted / performed) reads
    naturally: pair each planned row with the adapted row on the same
    ``domain`` + ``daily_plan_id``, and attach any performed outcomes
    from the adapted row's review chain.

    Legacy plans from before migration 011 have no paired planned rows;
    the bundle's ``planned_recommendations`` list is empty in that case
    and the view degrades to two-state (adapted + performed).
    """

    planned_id: str
    proposal_id: str
    domain: str
    action: str
    action_detail: Optional[Any]
    confidence: str
    schema_version: str
    captured_at: str


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
    planned_recommendations: list[ExplainPlannedRecommendation] = field(
        default_factory=list
    )


# ---------------------------------------------------------------------------
# Public loaders
# ---------------------------------------------------------------------------


def load_bundle_for_date(
    conn: sqlite3.Connection,
    *,
    for_date: date,
    user_id: str,
    plan_version: str = "latest",
) -> ExplainBundle:
    """Load a plan bundle for ``(for_date, user_id)``.

    Per D1 (``reporting/plans/v0_1_4/D1_re_author_semantics.md``), the
    default resolves the **canonical leaf** of the supersede chain —
    the plan a user asking "what's today's plan?" actually cares about.
    Before D1, this returned the chain head (i.e. the first plan
    ever synthesized for the key), which produced the 2026-04-23 bug
    where ``hai explain --for-date`` showed the morning's superseded
    plan instead of the current canonical one.

    ``plan_version`` values:

    - ``"latest"`` (default): canonical leaf (``superseded_by_plan_id
      IS NULL``). If the chain head has no forward link, returns the
      head — covers non-superseded days.
    - ``"first"``: chain head — ``plan_<date>_<user>`` base id.

    ``"all"`` is handled by :func:`load_bundle_chain_for_date` since
    it returns multiple bundles and therefore a different shape.

    Raises :class:`ExplainNotFoundError` when the resolved plan
    doesn't exist.
    """

    if plan_version == "first":
        plan_id = canonical_daily_plan_id(for_date, user_id)
        return load_bundle_by_daily_plan_id(conn, daily_plan_id=plan_id)
    if plan_version == "latest":
        leaf_id = _resolve_leaf_plan_id(
            conn, for_date=for_date, user_id=user_id,
        )
        return load_bundle_by_daily_plan_id(conn, daily_plan_id=leaf_id)
    raise ValueError(
        f"plan_version must be 'latest' or 'first' for single-bundle load "
        f"(got {plan_version!r}); use load_bundle_chain_for_date for 'all'."
    )


def load_bundle_chain_for_date(
    conn: sqlite3.Connection,
    *,
    for_date: date,
    user_id: str,
) -> list[ExplainBundle]:
    """Return every bundle in the supersede chain for ``(for_date, user_id)``,
    ordered chain-head → leaf.

    Each bundle is a full :class:`ExplainBundle` so callers can render
    the entire history (proposals, firings, recommendations, reviews)
    for audit purposes. The chain-head is ``plan_<date>_<user>``; the
    chain follows ``superseded_by_plan_id`` pointers (column added in
    migration 014) until NULL.
    """

    head_id = canonical_daily_plan_id(for_date, user_id)
    bundles: list[ExplainBundle] = []
    seen: set[str] = set()
    next_id: Optional[str] = head_id

    while next_id is not None:
        if next_id in seen:
            # Defensive cycle-guard — shouldn't happen under D1's
            # atomic supersede, but forward-link loops would silently
            # hang without this.
            break
        seen.add(next_id)
        try:
            bundles.append(load_bundle_by_daily_plan_id(
                conn, daily_plan_id=next_id,
            ))
        except ExplainNotFoundError:
            # Head may not exist if the day was never synthesized;
            # partial chains (rare) terminate cleanly.
            break

        row = conn.execute(
            "SELECT superseded_by_plan_id FROM daily_plan "
            "WHERE daily_plan_id = ?",
            (next_id,),
        ).fetchone()
        next_id = row["superseded_by_plan_id"] if row else None

    if not bundles:
        raise ExplainNotFoundError(
            f"no daily_plan chain for (for_date={for_date!r}, "
            f"user_id={user_id!r})"
        )
    return bundles


def _resolve_leaf_plan_id(
    conn: sqlite3.Connection,
    *,
    for_date: date,
    user_id: str,
) -> str:
    """Walk the supersede chain from the canonical head to the leaf.

    The head is ``plan_<for_date>_<user_id>`` (the id synthesis
    assigns to the first plan for the key). Each non-leaf has
    ``superseded_by_plan_id`` pointing at the next link. The leaf has
    ``superseded_by_plan_id IS NULL``.

    Raises :class:`ExplainNotFoundError` if the head doesn't exist.
    """

    head_id = canonical_daily_plan_id(for_date, user_id)
    current_id = head_id
    seen: set[str] = set()

    while True:
        if current_id in seen:
            # Cycle guard — shouldn't happen, but never hang.
            return current_id
        seen.add(current_id)

        row = conn.execute(
            "SELECT superseded_by_plan_id FROM daily_plan "
            "WHERE daily_plan_id = ?",
            (current_id,),
        ).fetchone()
        if row is None:
            if current_id == head_id:
                raise ExplainNotFoundError(
                    f"no daily_plan chain for (for_date={for_date!r}, "
                    f"user_id={user_id!r})"
                )
            # Dangling pointer — treat the previous as the leaf.
            return current_id
        next_id = row["superseded_by_plan_id"]
        if next_id is None:
            return current_id
        current_id = next_id


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
    planned = _load_planned_recommendations_for_plan(
        conn, daily_plan_id=daily_plan_id,
    )

    return ExplainBundle(
        plan=plan,
        proposals=proposals,
        phase_a_firings=phase_a,
        phase_b_firings=phase_b,
        recommendations=recommendations,
        reviews=reviews,
        user_memory=user_memory,
        planned_recommendations=planned,
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
    """Return the proposals this plan was synthesized from.

    Per D1 (§supersede behavior change), the join uses the plan's
    stored ``proposal_ids_json`` array rather than the
    ``proposal_log.daily_plan_id`` FK. Under the old FK-based path,
    superseding a plan relinked the proposals forward and the prior
    chain link's explain view silently lost its inputs; storing the
    ids on the plan row keeps every bundle self-contained.
    """

    plan_row = conn.execute(
        "SELECT proposal_ids_json FROM daily_plan WHERE daily_plan_id = ?",
        (daily_plan_id,),
    ).fetchone()
    if plan_row is None:
        return []
    proposal_ids = _loads(plan_row["proposal_ids_json"]) or []
    if not proposal_ids:
        return []

    placeholders = ",".join(["?"] * len(proposal_ids))
    rows = conn.execute(
        f"SELECT proposal_id, domain, schema_version, action, "
        f"  payload_json, confidence, produced_at, validated_at "
        f"FROM proposal_log WHERE proposal_id IN ({placeholders})",
        proposal_ids,
    ).fetchall()
    by_id = {row["proposal_id"]: row for row in rows}

    out: list[ExplainProposal] = []
    for pid in proposal_ids:
        row = by_id.get(pid)
        if row is None:
            # Stored id no longer resolves — rare, but honestly skip
            # rather than fabricate. Audit-chain integrity test #10
            # is responsible for catching this class of drift.
            continue
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
    out.sort(key=lambda p: (p.domain, p.proposal_id))
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
            human_explanation=description_for(row["x_rule_id"]),
        )
        if firing.tier in _PHASE_B_TIERS:
            phase_b.append(firing)
        else:
            phase_a.append(firing)
    return phase_a, phase_b


def _load_recommendations_for_plan(
    conn: sqlite3.Connection, *, daily_plan_id: str,
) -> list[ExplainRecommendation]:
    # M3: ``daily_plan_id`` is now a first-class column with a dedicated
    # index (``idx_recommendation_log_daily_plan_id``), so this is a
    # plain B-tree lookup. The column is populated on write and
    # backfilled for pre-M3 rows by migration 009.
    rows = conn.execute(
        "SELECT recommendation_id, domain, action, confidence, "
        "  bounded, payload_json, issued_at "
        "FROM recommendation_log "
        "WHERE daily_plan_id = ? "
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


def _load_planned_recommendations_for_plan(
    conn: sqlite3.Connection, *, daily_plan_id: str,
) -> list[ExplainPlannedRecommendation]:
    """Load the planned-aggregate rows (migration 011) for this plan.

    Degrades to ``[]`` when the ``planned_recommendation`` table is
    absent (DB predates migration 011) — mirroring the user-memory
    loader's pattern so the explain surface keeps working on older DBs.
    An empty list is also the correct answer for legacy plans synthesised
    before 011 landed: no planned rows were written for them, so the
    three-state view degrades cleanly to two-state (adapted + performed).
    """

    try:
        rows = conn.execute(
            "SELECT planned_id, proposal_id, domain, action, "
            "  action_detail_json, confidence, schema_version, captured_at "
            "FROM planned_recommendation "
            "WHERE daily_plan_id = ? "
            "ORDER BY domain, planned_id",
            (daily_plan_id,),
        ).fetchall()
    except sqlite3.OperationalError:
        return []

    out: list[ExplainPlannedRecommendation] = []
    for row in rows:
        out.append(
            ExplainPlannedRecommendation(
                planned_id=row["planned_id"],
                proposal_id=row["proposal_id"],
                domain=row["domain"],
                action=row["action"],
                action_detail=_loads(row["action_detail_json"]),
                confidence=row["confidence"],
                schema_version=row["schema_version"],
                captured_at=row["captured_at"],
            )
        )
    return out


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
