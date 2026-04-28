"""Synthesis orchestration (Phase 2 step 4).

Glues :mod:`health_agent_infra.core.synthesis_policy` to the DB + JSONL
side. One function — :func:`run_synthesis` — is called by
``hai synthesize``. Everything it does in a single SQLite BEGIN/COMMIT:

  1. Read snapshot for ``(for_date, user_id)`` from the DB.
  2. Read every proposal in ``proposal_log`` for ``(for_date, user_id)``.
  3. Run Phase A — X1a, X1b, X2, X3a, X3b, X4, X5, X6a, X6b, X7
     (the full ``PHASE_A_EVALUATORS`` tuple in
     :mod:`core.synthesis_policy`).
  4. Apply Phase A mutations mechanically → draft BoundedRecommendations.
  5. Overlay skill-authored rationale + uncertainty if ``drafts_json``
     was provided (the skill's judgment layer). Skill cannot change
     ``action`` / ``action_detail`` / ``confidence`` — those are
     runtime-owned after Phase A.
  6. Run Phase B — X9. Apply mutations via :func:`apply_phase_b` with
     :func:`guard_phase_b_mutation` enforcing the write-surface
     contract.
  7. Write ``daily_plan`` + N ``recommendation_log`` rows + M
     ``x_rule_firing`` rows + link ``proposal_log.daily_plan_id`` — all
     in one SQLite transaction. A failure anywhere rolls the whole
     thing back.

**Idempotency + supersession.**

- Default: re-running for the same ``(for_date, user_id)`` replaces the
  prior canonical plan atomically — old plan + firings + recommendations
  are deleted and new ones inserted in the same transaction.
- ``supersede=True``: the prior plan stays; its ``superseded_by`` pointer
  is flipped to the new plan's id; the new plan is written under a fresh
  ``_v<N>`` id (deterministic: count existing ``_v<N>`` plans for that
  key, pick next).

**Error surface.**

- :class:`SynthesisError` — bundle inputs don't satisfy preconditions
  (no proposals, proposal validation failure, etc.).
- :class:`XRuleWriteSurfaceViolation` — a Phase B rule attempted an
  off-limits mutation. Bubbles up from the policy layer.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from health_agent_infra.core.config import load_thresholds
from health_agent_infra.core.validate import (
    RecommendationValidationError,
    validate_recommendation_dict,
)
from health_agent_infra.core.schemas import (
    RECOMMENDATION_SCHEMA_VERSION,
    canonical_daily_plan_id,
)
from health_agent_infra.core.state.projector import (
    delete_canonical_plan_cascade,
    link_proposal_to_plan,
    mark_plan_superseded,
    project_bounded_recommendation,
    project_daily_plan,
    project_planned_recommendation,
    project_x_rule_firing,
    read_proposals_for_plan_key,
)
from health_agent_infra.core.state.snapshot import build_snapshot
from health_agent_infra.core.synthesis_policy import (
    XRuleFiring,
    apply_phase_a,
    apply_phase_b,
    evaluate_phase_a,
    evaluate_phase_b,
    guard_phase_b_mutation,
)


RECOMMENDATION_SCHEMA_BY_DOMAIN: dict[str, str] = {
    "recovery": "training_recommendation.v1",
    "running": "running_recommendation.v1",
    "sleep": "sleep_recommendation.v1",
    "stress": "stress_recommendation.v1",
    "strength": "strength_recommendation.v1",
    "nutrition": "nutrition_recommendation.v1",
}


class SynthesisError(RuntimeError):
    """Raised when synthesis preconditions fail."""


@dataclass
class SynthesisResult:
    daily_plan_id: str
    recommendation_ids: list[str]
    proposal_ids: list[str]
    phase_a_firings: list[XRuleFiring]
    phase_b_firings: list[XRuleFiring]
    superseded_prior: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "daily_plan_id": self.daily_plan_id,
            "recommendation_ids": list(self.recommendation_ids),
            "proposal_ids": list(self.proposal_ids),
            "phase_a_firings": [f.to_dict() for f in self.phase_a_firings],
            "phase_b_firings": [f.to_dict() for f in self.phase_b_firings],
            "superseded_prior": self.superseded_prior,
        }


# ---------------------------------------------------------------------------
# Draft construction — mechanically transform proposals into
# BoundedRecommendation-shaped drafts before the skill sees them.
# ---------------------------------------------------------------------------

def _mechanical_draft(
    proposal: dict[str, Any],
    *,
    daily_plan_id: str,
    issued_at: datetime,
    agent_version: str,
    plan_version_suffix: str = "",
) -> dict[str, Any]:
    """Convert a proposal dict to a draft BoundedRecommendation dict.

    The runtime synthesises the missing fields (``recommendation_id``,
    ``follow_up``, ``daily_plan_id``) deterministically so this function
    stays pure. Rationale and uncertainty are copied verbatim from the
    proposal and can be replaced by the skill's drafts-json overlay.

    ``plan_version_suffix`` is appended to the recommendation id to keep
    superseded plan recommendations collision-free in
    ``recommendation_log`` (the table's PK is ``recommendation_id`` only).
    Empty on the canonical plan path.
    """

    recommendation_id = (
        f"rec_{proposal['for_date']}_{proposal['user_id']}_"
        f"{proposal['domain']}_01{plan_version_suffix}"
    )
    review_at = issued_at + timedelta(hours=23)
    review_event_id = f"rev_{proposal['for_date']}_{proposal['user_id']}_{recommendation_id}"

    return {
        "schema_version": RECOMMENDATION_SCHEMA_BY_DOMAIN.get(
            proposal["domain"], RECOMMENDATION_SCHEMA_VERSION,
        ),
        "recommendation_id": recommendation_id,
        "user_id": proposal["user_id"],
        "issued_at": issued_at.isoformat(),
        "for_date": proposal["for_date"],
        "domain": proposal["domain"],
        "action": proposal["action"],
        "action_detail": proposal.get("action_detail"),
        "rationale": list(proposal.get("rationale") or []),
        "confidence": proposal["confidence"],
        "uncertainty": list(proposal.get("uncertainty") or []),
        "follow_up": {
            "review_at": review_at.isoformat(),
            "review_question": _default_review_question(
                proposal["action"], proposal["domain"],
            ),
            "review_event_id": review_event_id,
        },
        "policy_decisions": list(proposal.get("policy_decisions") or []),
        "bounded": True,
        "daily_plan_id": daily_plan_id,
    }


_DEFAULT_REVIEW_QUESTIONS: dict[str, str] = {
    "proceed_with_planned_session": "Did today's session feel appropriate for your recovery?",
    "proceed_with_planned_run": "Did today's run feel appropriate for your current form?",
    "downgrade_hard_session_to_zone_2": "Did yesterday's downgrade to Zone 2 improve how today feels?",
    "downgrade_session_to_mobility_only": "Did yesterday's mobility-only day help your recovery?",
    "downgrade_intervals_to_tempo": "Did yesterday's tempo session land well?",
    "downgrade_to_easy_aerobic": "Did the easy run yesterday leave you feeling better today?",
    "cross_train_instead": "Did the cross-training session suit your recovery?",
    "rest_day_recommended": "Did yesterday's rest day help your recovery?",
    # NOTE: defer_decision_insufficient_signal is sourced per-domain from
    # core.narration.templates.DEFER_REVIEW_QUESTION_TEMPLATES — see
    # _default_review_question below. The recovery wording used to live
    # here and leaked session-language into every non-recovery defer
    # (D3 bug). Don't re-add it without changing the resolver.
    "escalate_for_user_review": "You had a persistent signal we flagged. Did you take any action?",
    # Sleep (Phase 3 step 5)
    "maintain_schedule": "Did sticking with your usual sleep schedule feel right last night?",
    "prioritize_wind_down": "Did the earlier wind-down help last night's sleep?",
    "sleep_debt_repayment_day": "Were you able to log extra sleep to repay the debt?",
    "earlier_bedtime_target": "Were you able to hit the earlier bedtime target?",
    # Stress (Phase 3 step 5)
    "maintain_routine": "Did your usual routine feel right given yesterday's stress signals?",
    "add_low_intensity_recovery": "Did the low-intensity recovery block help yesterday?",
    "schedule_decompression_time": "Were you able to take the decompression time you planned?",
    # Strength (Phase 7 closure: strength wired as a real proposal/synthesis
    # domain). ``proceed_with_planned_session`` is shared with recovery; the
    # per-domain override below gives strength a domain-appropriate prompt
    # without touching the recovery wording any existing test / artifact
    # captures depend on.
    "downgrade_to_technique_or_accessory": "Did yesterday's technique / accessory work land well?",
    "downgrade_to_moderate_load": "Did yesterday's moderate-load session feel appropriate?",
    # Nutrition (Phase 5 step 4)
    "maintain_targets": "Did yesterday's macro targets feel sustainable?",
    "increase_protein_intake": "Were you able to hit the higher protein target yesterday?",
    "increase_hydration": "Did the extra fluids help yesterday?",
    "reduce_calorie_deficit": "Did yesterday's adjusted intake feel right for your training?",
}


# Per-(domain, action) overrides for actions whose enum value is shared
# across domains but whose natural review question differs. Looked up
# before the action-only map so existing domain wordings stay intact.
_DOMAIN_REVIEW_QUESTION_OVERRIDES: dict[tuple[str, str], str] = {
    ("strength", "proceed_with_planned_session"):
        "Did today's planned strength session feel appropriate?",
    ("strength", "rest_day_recommended"):
        "Did yesterday's rest day leave you fresh for the next lift?",
}


def _default_review_question(action: str, domain: str = "recovery") -> str:
    # D3 §defer review_question improvements — defer is sourced per
    # domain so nutrition/stress/sleep/strength don't inherit recovery
    # session-language. The narration module is the single source of
    # truth for these templates so ``hai today``'s defer rendering and
    # ``hai synthesize``'s persisted review_question stay aligned.
    if action == "defer_decision_insufficient_signal":
        from health_agent_infra.core.narration.templates import (
            DEFER_REVIEW_QUESTION_TEMPLATES,
        )
        template = DEFER_REVIEW_QUESTION_TEMPLATES.get(domain)
        if template is not None:
            return template
        # Unknown domain falls through to the generic text below.
    override = _DOMAIN_REVIEW_QUESTION_OVERRIDES.get((domain, action))
    if override is not None:
        return override
    return _DEFAULT_REVIEW_QUESTIONS.get(
        action, "How did yesterday's plan work out?",
    )


_OVERLAY_ALLOWED_TOPLEVEL_KEYS: frozenset[str] = frozenset({
    "recommendation_id",  # required match key
    "rationale",
    "uncertainty",
    "follow_up",
})

_OVERLAY_ALLOWED_FOLLOW_UP_KEYS: frozenset[str] = frozenset({
    "review_question",
})


def _overlay_skill_drafts(
    drafts: list[dict[str, Any]],
    skill_drafts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Overlay skill-authored rationale + uncertainty onto mechanical drafts.

    The skill may only edit fields that belong to its judgment layer:
    ``rationale``, ``uncertainty``, and ``follow_up.review_question``.
    Any other key on a skill draft — ``action``, ``action_detail``,
    ``confidence``, ``daily_plan_id``, ``policy_decisions``, ``bounded``,
    ``schema_version``, anything else — is a runtime-owned field that
    the skill must not touch. v0.1.9 makes this fail-loud (was
    fail-soft pre-v0.1.9): a skill draft attempting to edit a
    runtime-owned field raises :class:`SynthesisError` with invariant
    id ``skill_overlay_out_of_lane`` BEFORE the synthesis transaction
    opens.

    Drafts referring to a ``recommendation_id`` that doesn't match any
    mechanical draft for the current synthesis run also raise
    ``skill_overlay_out_of_lane`` — silently dropping unmatched drafts
    would mask drift between the agent's bundle read and the synthesis
    write.

    Skill drafts that omit allowed fields are still valid (the
    mechanical draft simply stands for those fields).
    """

    mechanical_ids = {d["recommendation_id"] for d in drafts}

    for skill_draft in skill_drafts:
        if not isinstance(skill_draft, dict):
            raise SynthesisError(
                f"skill_overlay_out_of_lane: skill draft entry must be a dict; "
                f"got {type(skill_draft).__name__}"
            )
        rec_id = skill_draft.get("recommendation_id")
        if rec_id is None:
            raise SynthesisError(
                "skill_overlay_out_of_lane: skill draft missing "
                "'recommendation_id' — every overlay entry must name "
                "the mechanical draft it modifies."
            )
        if rec_id not in mechanical_ids:
            raise SynthesisError(
                f"skill_overlay_out_of_lane: skill draft references "
                f"recommendation_id={rec_id!r} which has no matching "
                f"mechanical draft for this synthesis run. Refusing to "
                f"overlay a phantom recommendation."
            )

        out_of_lane = set(skill_draft.keys()) - _OVERLAY_ALLOWED_TOPLEVEL_KEYS
        if out_of_lane:
            raise SynthesisError(
                f"skill_overlay_out_of_lane: skill draft for "
                f"recommendation_id={rec_id!r} attempted to edit "
                f"runtime-owned field(s) {sorted(out_of_lane)}. The "
                f"skill may only set rationale, uncertainty, and "
                f"follow_up.review_question."
            )

        if "rationale" in skill_draft:
            rationale = skill_draft["rationale"]
            if not isinstance(rationale, list) or not all(
                isinstance(item, str) for item in rationale
            ):
                raise SynthesisError(
                    f"skill_overlay_out_of_lane: skill draft for "
                    f"recommendation_id={rec_id!r} set rationale with "
                    f"invalid shape; expected list[str]."
                )

        if "uncertainty" in skill_draft:
            uncertainty = skill_draft["uncertainty"]
            if not isinstance(uncertainty, list) or not all(
                isinstance(item, str) for item in uncertainty
            ):
                raise SynthesisError(
                    f"skill_overlay_out_of_lane: skill draft for "
                    f"recommendation_id={rec_id!r} set uncertainty with "
                    f"invalid shape; expected list[str]."
                )

        follow_up = skill_draft.get("follow_up")
        if follow_up is not None:
            if not isinstance(follow_up, dict):
                raise SynthesisError(
                    f"skill_overlay_out_of_lane: skill draft for "
                    f"recommendation_id={rec_id!r} has follow_up of "
                    f"type {type(follow_up).__name__}; expected dict."
                )
            fu_out_of_lane = set(follow_up.keys()) - _OVERLAY_ALLOWED_FOLLOW_UP_KEYS
            if fu_out_of_lane:
                raise SynthesisError(
                    f"skill_overlay_out_of_lane: skill draft for "
                    f"recommendation_id={rec_id!r} attempted to edit "
                    f"follow_up field(s) {sorted(fu_out_of_lane)}. The "
                    f"skill may only set follow_up.review_question; "
                    f"review_at and review_event_id are runtime-owned."
                )
            if "review_question" in follow_up:
                review_question = follow_up["review_question"]
                if not isinstance(review_question, str) or not review_question.strip():
                    raise SynthesisError(
                        f"skill_overlay_out_of_lane: skill draft for "
                        f"recommendation_id={rec_id!r} set "
                        f"follow_up.review_question with invalid shape; "
                        f"expected non-empty str."
                    )

    by_id = {d["recommendation_id"]: d for d in skill_drafts}
    out: list[dict[str, Any]] = []
    for draft in drafts:
        skill_draft = by_id.get(draft["recommendation_id"])
        if skill_draft is None:
            out.append(draft)
            continue
        merged = dict(draft)
        if isinstance(skill_draft.get("rationale"), list):
            merged["rationale"] = list(skill_draft["rationale"])
        if isinstance(skill_draft.get("uncertainty"), list):
            merged["uncertainty"] = list(skill_draft["uncertainty"])
        incoming_fu = skill_draft.get("follow_up") or {}
        if isinstance(incoming_fu, dict) and "review_question" in incoming_fu:
            fu = dict(merged["follow_up"])
            fu["review_question"] = incoming_fu["review_question"]
            merged["follow_up"] = fu
        out.append(merged)
    return out


# ---------------------------------------------------------------------------
# Plan id supersession helpers
# ---------------------------------------------------------------------------

def _next_superseded_plan_id(
    conn: sqlite3.Connection,
    *,
    canonical_id: str,
) -> str:
    """Pick the next ``<canonical>_v<N>`` suffix not yet in ``daily_plan``.

    N = 2 on first supersession (``_v2``), 3 next, etc. Canonical id
    itself is reserved for the default-idempotent path — supersession
    always assigns a suffixed variant.
    """

    rows = conn.execute(
        "SELECT daily_plan_id FROM daily_plan WHERE daily_plan_id LIKE ?",
        (f"{canonical_id}_v%",),
    ).fetchall()
    existing_suffixes: set[int] = set()
    for row in rows:
        suffix = row["daily_plan_id"].rsplit("_v", 1)[-1]
        try:
            existing_suffixes.add(int(suffix))
        except ValueError:
            continue
    # Canonical counts as v1 for the purposes of picking the next suffix.
    n = 2
    while n in existing_suffixes:
        n += 1
    return f"{canonical_id}_v{n}"


def _resolve_canonical_leaf_plan_id(
    conn: sqlite3.Connection,
    *,
    canonical_id: str,
) -> Optional[str]:
    """Walk the supersede chain from ``canonical_id`` to the leaf.

    Per D1, ``--supersede`` must point the new plan's back-pointer at
    the canonical **leaf** at time of synthesis, not the chain head.
    v1→v2→v3 + a fourth supersede should produce v3.superseded_by=v4
    (not v1.superseded_by=v4 overwriting the v1→v2 link).

    Returns ``None`` when ``canonical_id`` doesn't exist — the caller
    treats that as "no prior plan" and skips the mark-superseded step.
    Defensive cycle-guard prevents infinite loops if a future bug
    corrupts forward pointers.
    """

    current_id: Optional[str] = canonical_id
    seen: set[str] = set()
    while current_id is not None:
        if current_id in seen:
            return current_id
        seen.add(current_id)
        row = conn.execute(
            "SELECT superseded_by_plan_id FROM daily_plan "
            "WHERE daily_plan_id = ?",
            (current_id,),
        ).fetchone()
        if row is None:
            return None if current_id == canonical_id else current_id
        next_id = row["superseded_by_plan_id"]
        if next_id is None:
            return current_id
        current_id = next_id
    return None


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

V1_EXPECTED_DOMAINS: frozenset[str] = frozenset({
    "recovery", "running", "sleep", "stress", "strength", "nutrition",
})


def run_synthesis(
    conn: sqlite3.Connection,
    *,
    for_date: date,
    user_id: str,
    snapshot: Optional[dict[str, Any]] = None,
    skill_drafts: Optional[list[dict[str, Any]]] = None,
    thresholds: Optional[dict[str, Any]] = None,
    agent_version: str = "claude_agent_v1",
    now: Optional[datetime] = None,
    supersede: bool = False,
    expected_domains: Optional[frozenset[str]] = None,
) -> SynthesisResult:
    """Run synthesis end-to-end inside a single SQLite transaction.

    ``snapshot`` defaults to :func:`build_snapshot(conn, for_date, user_id)`
    if not supplied. Tests pass a synthetic snapshot dict.

    ``skill_drafts`` lets callers feed the skill's judgment overlay as a
    list of partial BoundedRecommendation dicts. When None, drafts are
    purely mechanical — action, confidence, and follow_up are all set by
    the runtime.

    ``thresholds`` falls through to
    :func:`health_agent_infra.core.config.load_thresholds` when None.

    ``supersede=False`` (default) → replace prior canonical plan.
    ``supersede=True`` → keep prior plan, write new one at
    ``<canonical_id>_v<N>``, flip ``superseded_by`` pointer on prior.

    ``expected_domains`` (v0.1.9 B4): when provided, refuse synthesis if
    any expected domain is missing a canonical-leaf proposal. This
    closes the gap Codex 2026-04-26 caught — pre-v0.1.9 ``run_synthesis``
    only refused on zero proposals, so a direct ``hai synthesize`` could
    commit a partial-domain plan even though the capabilities manifest
    declared a ``proposal_log_has_row_for_each_target_domain``
    precondition. ``hai daily`` had the gate; direct synthesize did
    not. v0.1.9 makes the gate live in ``run_synthesis`` so every
    caller — daily, direct synthesize, programmatic — gets the same
    contract. Default ``None`` keeps the legacy "any non-zero
    proposals" behavior so test fixtures and the eval runner that pass
    minimal proposal sets still work.
    """

    if snapshot is None:
        snapshot = build_snapshot(
            conn, as_of_date=for_date, user_id=user_id, lookback_days=14,
        )
    if thresholds is None:
        thresholds = load_thresholds()
    now = now or datetime.now(timezone.utc)

    for_date_iso = for_date.isoformat()
    proposals = read_proposals_for_plan_key(
        conn, for_date=for_date_iso, user_id=user_id,
    )
    if not proposals:
        raise SynthesisError(
            f"no proposals in proposal_log for (for_date={for_date_iso}, "
            f"user_id={user_id!r}). Call `hai propose` first."
        )

    if expected_domains is not None:
        present_domains = {p["domain"] for p in proposals}
        missing = sorted(expected_domains - present_domains)
        if missing:
            raise SynthesisError(
                f"missing_expected_proposals: synthesis blocked because "
                f"the following expected domains have no canonical-leaf "
                f"proposal in proposal_log for (for_date={for_date_iso}, "
                f"user_id={user_id!r}): {missing}. Either post "
                f"DomainProposal rows via `hai propose --domain <d>` "
                f"for those domains, or narrow the expected set."
            )

    # Defensive guard (Phase A safety closure): under D1 revision
    # semantics, ``read_proposals_for_plan_key`` already returns canonical
    # leaves only — exactly one per (for_date, user_id, domain) chain key.
    # If two ever land here the deterministic recommendation_id generator
    # at ``_mechanical_draft`` would PK-collide on ``recommendation_log``
    # mid-transaction. Catching it before the transaction starts keeps
    # the rollback story clean (no partial commit possible) and surfaces
    # any future regression in the canonical-leaf walker as a SynthesisError
    # at the synthesis seam, not as a silent overwrite.
    seen_chain_keys: dict[tuple[str, str, str], str] = {}
    for p in proposals:
        key = (p["for_date"], p["user_id"], p["domain"])
        if key in seen_chain_keys:
            raise SynthesisError(
                f"multiple active proposals for chain key {key}: "
                f"{seen_chain_keys[key]!r} and {p['proposal_id']!r}. "
                f"Expected exactly one canonical leaf per (for_date, "
                f"user_id, domain). This is a runtime invariant; either "
                f"the canonical-leaf walker regressed or proposals were "
                f"inserted out-of-band. Refusing to synthesize."
            )
        seen_chain_keys[key] = p["proposal_id"]

    # Phase A
    phase_a_firings = evaluate_phase_a(snapshot, proposals, thresholds)

    canonical_id = canonical_daily_plan_id(for_date, user_id)
    if supersede:
        # v0.1.11 W-F (Codex F-DEMO-05 + maintainer Q-A: option b):
        # --supersede on a date with no canonical plan is a programming
        # error. Pre-v0.1.11 this minted an orphan _v2 unreachable via
        # `hai today` / `hai explain --for-date`. Refuse with USER_INPUT
        # rather than silently fall through to first-version semantics.
        canonical_exists = conn.execute(
            "SELECT 1 FROM daily_plan WHERE daily_plan_id = ?",
            (canonical_id,),
        ).fetchone()
        if canonical_exists is None:
            raise SynthesisError(
                f"--supersede requires an existing canonical plan for "
                f"({for_date.isoformat()}, {user_id}); none found "
                f"(canonical id would be {canonical_id!r}). Re-run "
                f"without --supersede to write the first-version plan."
            )
        daily_plan_id = _next_superseded_plan_id(conn, canonical_id=canonical_id)
        plan_version_suffix = daily_plan_id[len(canonical_id):]  # e.g. "_v2"
    else:
        daily_plan_id = canonical_id
        plan_version_suffix = ""

    # Phase 1 (agent-operable runtime plan §1) — capture the
    # pre-X-rule aggregate BEFORE apply_phase_a mutates anything. Each
    # planned_recommendation row mirrors the draft we'd have committed if
    # no X-rule had fired. Written inside the atomic transaction below
    # so the planned/adapted pair is always consistent.
    planned_rows: list[dict[str, Any]] = []
    for proposal in proposals:
        planned_draft = _mechanical_draft(
            proposal,
            daily_plan_id=daily_plan_id,
            issued_at=now,
            agent_version=agent_version,
            plan_version_suffix=plan_version_suffix,
        )
        planned_rows.append({
            "planned_id": (
                f"planned_{proposal['for_date']}_{proposal['user_id']}_"
                f"{proposal['domain']}_01{plan_version_suffix}"
            ),
            "daily_plan_id": daily_plan_id,
            "proposal_id": proposal["proposal_id"],
            "user_id": proposal["user_id"],
            "for_date": proposal["for_date"],
            "domain": proposal["domain"],
            "action": planned_draft["action"],
            "confidence": planned_draft["confidence"],
            "action_detail": planned_draft.get("action_detail"),
            "captured_at": now.isoformat(),
        })

    # Draft construction + skill overlay
    drafts: list[dict[str, Any]] = []
    for proposal in proposals:
        mutated_proposal, _fired = apply_phase_a(proposal, phase_a_firings)
        draft = _mechanical_draft(
            mutated_proposal,
            daily_plan_id=daily_plan_id,
            issued_at=now,
            agent_version=agent_version,
            plan_version_suffix=plan_version_suffix,
        )
        drafts.append(draft)

    if skill_drafts is not None:
        drafts = _overlay_skill_drafts(drafts, skill_drafts)

    # Phase B — evaluate, guard, apply.
    phase_b_firings = evaluate_phase_b(snapshot, drafts, thresholds)
    for firing in phase_b_firings:
        guard_phase_b_mutation(firing)
    final_recommendations: list[dict[str, Any]] = []
    for draft in drafts:
        mutated, _fired_b = apply_phase_b(draft, phase_b_firings)
        final_recommendations.append(mutated)

    # Phase A safety closure (v0.1.4): every final recommendation must pass
    # the runtime's banned-token + shape validator before any partial commit
    # can persist. The legacy ``hai writeback`` path enforced this at its
    # CLI seam; D2 retired writeback in v0.1.4 and the canonical synthesis
    # path inherited the responsibility. Failing here raises a
    # ``SynthesisError`` BEFORE ``BEGIN EXCLUSIVE``, so no daily_plan,
    # recommendation_log, x_rule_firing, or proposal_log.daily_plan_id
    # mutation can land — atomic rollback by construction.
    #
    # Coverage (per the Phase A brief):
    #   - proposal-derived rationale (carried into final via _mechanical_draft)
    #   - skill overlay rationale (applied via _overlay_skill_drafts above)
    #   - skill overlay uncertainty (same path)
    #   - action_detail (proposal + Phase B mutations)
    #   - follow_up.review_question (curated template OR skill overlay)
    for rec in final_recommendations:
        try:
            validate_recommendation_dict(rec)
        except RecommendationValidationError as exc:
            raise SynthesisError(
                f"recommendation {rec.get('recommendation_id')!r} for domain "
                f"{rec.get('domain')!r} failed safety validation "
                f"(invariant={exc.invariant}): {exc}"
            ) from exc

    proposal_ids = [p["proposal_id"] for p in proposals]
    recommendation_ids = [r["recommendation_id"] for r in final_recommendations]
    all_firings = [*phase_a_firings, *phase_b_firings]

    plan_dict = {
        "daily_plan_id": daily_plan_id,
        "user_id": user_id,
        "for_date": for_date_iso,
        "synthesized_at": now.isoformat(),
        "recommendation_ids": recommendation_ids,
        "proposal_ids": proposal_ids,
        "x_rules_fired": sorted({f.rule_id for f in all_firings}),
        "synthesis_meta": {
            "phase_a_count": len(phase_a_firings),
            "phase_b_count": len(phase_b_firings),
            "supersede": supersede,
        },
        "agent_version": agent_version,
    }

    superseded_prior: Optional[str] = None

    # Atomic commit.
    conn.execute("BEGIN EXCLUSIVE")
    try:
        if supersede:
            # D1: --supersede marks the canonical *leaf* at time of
            # synthesis (not the chain head) so v1→v2→v3 + another
            # supersede produces v3.superseded_by=v4, preserving the
            # v1→v2 link that would otherwise be overwritten.
            leaf_id = _resolve_canonical_leaf_plan_id(
                conn, canonical_id=canonical_id,
            )
            if leaf_id is not None:
                mark_plan_superseded(
                    conn,
                    daily_plan_id=leaf_id,
                    superseded_by=daily_plan_id,
                    commit_after=False,
                )
                superseded_prior = leaf_id
        else:
            delete_canonical_plan_cascade(
                conn, daily_plan_id=canonical_id, commit_after=False,
            )

        project_daily_plan(
            conn, plan_dict, commit_after=False,
        )

        # Phase 2.5 Condition 1 — orphan defensive check. A firing whose
        # affected_domain is not in the committing plan's proposal domains
        # is stamped orphan=1 so future regressions (e.g. a rule that
        # emits firings from snapshot-only signals without iterating
        # proposals) surface in the audit table rather than silently
        # leaving dead rows. Current rules cannot emit orphans by
        # construction, so this is a monitor, not a gate.
        proposal_domains = {p["domain"] for p in proposals}
        for firing in all_firings:
            is_orphan = firing.affected_domain not in proposal_domains
            project_x_rule_firing(
                conn,
                firing.to_dict(),
                daily_plan_id=daily_plan_id,
                user_id=user_id,
                orphan=is_orphan,
                commit_after=False,
            )

        for recommendation in final_recommendations:
            project_bounded_recommendation(
                conn,
                recommendation,
                agent_version=agent_version,
                commit_after=False,
            )

        # D1: only the canonical-replace path relinks proposals.
        # ``--supersede`` intentionally leaves ``proposal_log.daily_plan_id``
        # pointed at the plan that first consumed each proposal; the new
        # leaf's join to its proposals lives in ``daily_plan.proposal_ids_json``.
        # Explain reads via that array so both the superseded chain head
        # and the new leaf render their full proposal set. (Fixes 2026-04-23
        # bug #3: supersede orphaned the prior plan's proposals.)
        if not supersede:
            for proposal_id in proposal_ids:
                link_proposal_to_plan(
                    conn,
                    proposal_id=proposal_id,
                    daily_plan_id=daily_plan_id,
                    commit_after=False,
                )

        # Planned-recommendation ledger rows: written last so the
        # daily_plan FK parent is populated (project_daily_plan above).
        # On the canonical-replace path, proposal_log.daily_plan_id is
        # also freshly linked by the loop just above. On the supersede
        # path, proposals retain whatever linkage they already had
        # (possibly NULL for proposals revised via ``hai propose --replace``
        # since the last synth) — the planned-recommendation FK is to
        # ``proposal_log(proposal_id)``, not to daily_plan_id, so writes
        # still resolve. The planned-row set is derived from the ORIGINAL
        # (pre-mutation) proposals, so rollback semantics hold: if any
        # prior insert fails the planned rows never land.
        for planned_row in planned_rows:
            project_planned_recommendation(
                conn,
                planned_row,
                agent_version=agent_version,
                commit_after=False,
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return SynthesisResult(
        daily_plan_id=daily_plan_id,
        recommendation_ids=recommendation_ids,
        proposal_ids=proposal_ids,
        phase_a_firings=phase_a_firings,
        phase_b_firings=phase_b_firings,
        superseded_prior=superseded_prior,
    )


# ---------------------------------------------------------------------------
# Bundle emission for the skill (read-only; no DB writes)
# ---------------------------------------------------------------------------

def build_synthesis_bundle(
    conn: sqlite3.Connection,
    *,
    for_date: date,
    user_id: str,
    thresholds: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Return ``{"snapshot", "proposals", "phase_a_firings"}`` for the skill.

    The skill reads this bundle to understand what mutations the runtime
    will apply, then composes rationale + uncertainty on top. The skill
    never sees Phase B firings (those run after the skill returns).
    """

    if thresholds is None:
        thresholds = load_thresholds()
    snapshot = build_snapshot(
        conn, as_of_date=for_date, user_id=user_id, lookback_days=14,
    )
    proposals = read_proposals_for_plan_key(
        conn, for_date=for_date.isoformat(), user_id=user_id,
    )
    firings = evaluate_phase_a(snapshot, proposals, thresholds)
    return {
        "snapshot": snapshot,
        "proposals": proposals,
        "phase_a_firings": [f.to_dict() for f in firings],
    }
