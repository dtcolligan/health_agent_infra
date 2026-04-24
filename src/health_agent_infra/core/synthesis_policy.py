"""Synthesis-layer X-rule evaluators (Phase 2 step 4).

Deterministic cross-domain rule evaluation. Two phases:

  **Phase A** — runs over ``(snapshot, proposals)`` BEFORE the synthesis
  skill composes final recommendations. Tiers: ``soften``, ``block``,
  ``cap_confidence``. Output firings specify a ``recommended_mutation``
  the runtime applies mechanically to copy-on-write drafts; the skill
  never sees Phase A firings as "to be applied" — it sees them as
  "already applied" mutations on the drafts it receives.

  **Phase B** — runs over ``(snapshot, final_recommendations)`` AFTER the
  skill returns. Tier: ``adjust``. Strictly limited to
  ``action_detail`` mutations on a fixed registry of target domains. A
  write-surface guard (:func:`guard_phase_b_mutation`) rejects any
  firing that would touch ``action`` or a non-target domain.

All thresholds flow from :mod:`health_agent_infra.core.config` so a
user TOML can tune triggers without editing code. Rule bodies never
compute bands or scores themselves — they read the classified state the
domain runtime already produced and compare against configured numeric
thresholds.

This module has no I/O and no DB access. It operates on plain dicts
shaped like the synthesis bundle: ``snapshot`` is the
:func:`~health_agent_infra.core.state.snapshot.build_snapshot` output;
``proposals`` is a list of :class:`DomainProposal`-shaped dicts (as
emitted by ``hai propose``); ``drafts`` is a list of
:class:`BoundedRecommendation`-shaped dicts. The orchestration layer
in :mod:`health_agent_infra.core.synthesis` owns the I/O + mutation
application.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Literal, Optional


Tier = Literal["soften", "block", "cap_confidence", "adjust", "restructure"]
Phase = Literal["A", "B"]


# ---------------------------------------------------------------------------
# Mutation-tier precedence. Higher number wins when two firings target the
# same (proposal_id, field). "block" (escalate) beats "soften" (downgrade)
# beats no-op. "cap_confidence" is independent — applied additively.
# ---------------------------------------------------------------------------
TIER_PRECEDENCE: dict[str, int] = {
    "soften": 1,
    "block": 2,
    "cap_confidence": 0,    # independent, not ordered with soften/block
    "adjust": 0,            # Phase B only
    "restructure": 3,       # reserved; not used in v1
}


# ---------------------------------------------------------------------------
# Domain action registries. Keyed by domain → (hard_actions, downgrade_action,
# escalate_action). "hard_actions" are the proposal actions that mean "I plan
# to train at the domain's baseline intensity" — they are the actions Phase A
# soften/block rules target. "downgrade_action" is the action a soften rule
# writes in. "escalate_action" is the action a block rule writes in.
# ---------------------------------------------------------------------------
_DOMAIN_ACTION_REGISTRY: dict[str, dict[str, Any]] = {
    "recovery": {
        "hard_actions": frozenset({"proceed_with_planned_session"}),
        "downgrade_action": "downgrade_hard_session_to_zone_2",
        "escalate_action": "escalate_for_user_review",
    },
    "running": {
        "hard_actions": frozenset({"proceed_with_planned_run"}),
        "downgrade_action": "downgrade_to_easy_aerobic",
        "escalate_action": "escalate_for_user_review",
    },
    # Phase 4 step 5: X3a/X3b soften/block hard strength proposals.
    # X3a → downgrade_action (default softening). X5 overrides to
    # ``downgrade_to_technique_or_accessory`` rule-locally because
    # yesterday's long-run fatigue argues for technique work, not a
    # moderate-load session.
    "strength": {
        "hard_actions": frozenset({"proceed_with_planned_session"}),
        "downgrade_action": "downgrade_to_moderate_load",
        "escalate_action": "escalate_for_user_review",
    },
}


# ---------------------------------------------------------------------------
# Phase B target registry — which rules may mutate which domains.
# Write-surface guard consults this. v1 holds only X9 → nutrition.
# ---------------------------------------------------------------------------
PHASE_B_TARGETS: dict[str, frozenset[str]] = {
    "X9": frozenset({"nutrition"}),
}


# ---------------------------------------------------------------------------
# Semantic public names for each X-rule. The internal IDs (``X1a``, ``X3b``,
# …) stay the stable handle across logs, DB rows, and scenario fixtures — a
# public name is a readability aid layered on top, surfaced in
# :meth:`XRuleFiring.to_dict`, the explain bundle, and the docs tables.
#
# Naming pattern: ``<trigger>-<tier_verb>-<target>``. Tier verbs follow the
# tier taxonomy — ``softens`` / ``blocks`` / ``caps-confidence`` / ``bumps``.
# Registering a new rule means appending a row here *and* adding the column
# to the Phase A / Phase B tables in ``reporting/docs/x_rules.md`` so the
# internal id and public name never diverge between code and docs.
# ---------------------------------------------------------------------------
X_RULE_PUBLIC_NAMES: dict[str, str] = {
    "X1a": "sleep-debt-softens-hard",
    "X1b": "sleep-debt-blocks-hard",
    "X2": "underfuelling-softens-hard",
    "X3a": "load-spike-softens-hard",
    "X3b": "load-spike-blocks-hard",
    "X4": "lower-body-sequencing-softens-run",
    "X5": "endurance-fatigue-softens-strength",
    "X6a": "body-battery-low-softens-hard",
    "X6b": "body-battery-depleted-blocks-hard",
    "X7": "stress-elevated-caps-confidence",
    "X9": "training-intensity-bumps-protein",
}


# ---------------------------------------------------------------------------
# Sentence-form explanations for each X-rule (Phase 3 of the
# agent-operable runtime plan; see reporting/plans/
# agent_operable_runtime_plan.md §3).
#
# The slug in ``X_RULE_PUBLIC_NAMES`` is a stable machine-readable handle;
# the sentence here is what a skill or agent narrates back to the user.
# Pattern:
#
#   "<trigger in plain terms>, so <action the rule takes>
#    (because <reason>)."
#
# Design choices:
#   - No raw threshold numbers. Sentences stay bounded — they describe
#     the qualitative state ("moderate", "elevated", "depleted") that
#     synthesis already classified, not the tuning knobs. A future
#     threshold change doesn't invalidate the sentence.
#   - One line each, ≤ 160 chars, so a CLI consumer or skill can print
#     them inline without wrapping logic.
#   - Consistent tense and voice across rules.
#   - Internal ids are frozen (``X1a``/``X3b``/…); the sentences are
#     free to evolve. Adding a new rule means appending a row here
#     *and* a row in ``X_RULE_PUBLIC_NAMES`` — a coverage test
#     (``test_every_x_rule_has_a_sentence``) asserts the two maps
#     stay aligned.
# ---------------------------------------------------------------------------
X_RULE_DESCRIPTIONS: dict[str, str] = {
    "X1a": (
        "Sleep debt is moderate, so hard sessions are softened "
        "to reduce injury risk while sleep recovers."
    ),
    "X1b": (
        "Sleep debt is elevated, so hard sessions are blocked "
        "until sleep catches up."
    ),
    "X2": (
        "Fuelling is low (calorie deficit or insufficient protein), "
        "so hard strength or recovery sessions are softened to "
        "protect adaptation."
    ),
    "X3a": (
        "Training load is spiking above recent baseline, so hard "
        "sessions are softened to reduce injury risk."
    ),
    "X3b": (
        "Training load is spiking well above recent baseline, so "
        "hard sessions are blocked until load settles."
    ),
    "X4": (
        "Yesterday's heavy lower-body strength means today's hard "
        "run is softened to an easy aerobic effort."
    ),
    "X5": (
        "Yesterday's long run or hard intervals means today's "
        "lower-body strength is softened to technique or accessory "
        "work."
    ),
    "X6a": (
        "Body battery is low, so hard sessions are softened to "
        "match available capacity."
    ),
    "X6b": (
        "Body battery is depleted, so hard sessions are blocked — "
        "today should be rest or very light."
    ),
    "X7": (
        "Stress is elevated today, so recommendation confidence is "
        "capped at moderate because the signal is noisier than usual."
    ),
    "X9": (
        "Training is hard today, so the nutrition target bumps "
        "protein to support adaptation."
    ),
}


def public_name_for(rule_id: str) -> Optional[str]:
    """Return the human-readable public name for ``rule_id``, or ``None``.

    Unknown / experimental rule ids deliberately return ``None`` rather
    than raising, so historical DB rows written before a rename land
    cleanly — callers render them under their internal id alone.
    """

    return X_RULE_PUBLIC_NAMES.get(rule_id)


def description_for(rule_id: str) -> Optional[str]:
    """Return the sentence-form explanation for ``rule_id``, or ``None``.

    Counterpart to :func:`public_name_for`. The sentence is what a
    skill or agent narrates back to the user — more complete than the
    slug ("sleep-debt-softens-hard") and more stable than the
    ``trigger_note`` string on individual firings (which encodes the
    specific signal that fired, not the rule's rationale).

    Unknown / experimental rule ids return ``None`` so historical DB
    rows written before a new rule lands render under their internal
    id alone.
    """

    return X_RULE_DESCRIPTIONS.get(rule_id)


@dataclass(frozen=True)
class XRuleFiring:
    """One deterministic firing of a cross-domain X-rule.

    Attributes:
      rule_id: stable rule identifier (e.g. ``"X1a"``, ``"X3b"``, ``"X9"``).
      tier: the firing tier — ``soften``, ``block``, ``cap_confidence``
        (Phase A), or ``adjust`` (Phase B). Reserved: ``restructure``.
      affected_domain: the single domain whose proposal/recommendation
        is mutated by this firing. Rules that affect multiple domains
        emit multiple firings (one per domain).
      trigger_note: human-readable string describing the trigger, e.g.
        ``"sleep_debt_band=moderate with running proposal"``.
      recommended_mutation: either ``None`` (for ``cap_confidence``, which
        carries its cap in the tier name itself) or a dict shaped as
        ``{"action": ..., "action_detail": {...}}`` for soften/block, or
        ``{"action_detail": {...}}`` for Phase B ``adjust``.
      source_signals: the snapshot signals that drove the firing, kept
        as-is so the firing is self-documenting.
      phase: ``"A"`` or ``"B"``. Phase A firings are applied before the
        skill composes; Phase B firings are applied after.
    """

    rule_id: str
    tier: Tier
    affected_domain: str
    trigger_note: str
    recommended_mutation: Optional[dict[str, Any]]
    source_signals: dict[str, Any]
    phase: Phase

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "public_name": public_name_for(self.rule_id),
            "human_explanation": description_for(self.rule_id),
            "tier": self.tier,
            "affected_domain": self.affected_domain,
            "trigger_note": self.trigger_note,
            "recommended_mutation": self.recommended_mutation,
            "source_signals": dict(self.source_signals),
            "phase": self.phase,
        }


class XRuleWriteSurfaceViolation(ValueError):
    """Phase B firing attempted to mutate an off-limits field or domain.

    Guard invariant: Phase B rules may only mutate ``action_detail`` on a
    domain listed in :data:`PHASE_B_TARGETS[rule_id]`. Any other shape is
    a bug in the rule implementation and must be rejected loudly rather
    than silently corrupting the plan.
    """


# ===========================================================================
# Snapshot accessors — tolerant reads. Missing path ⇒ ``None``.
# ===========================================================================

def _get(d: Optional[dict[str, Any]], *path: str) -> Any:
    """Dotted-path getter that returns None on any missing step."""

    cur: Any = d
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _sleep_debt_band(snapshot: dict[str, Any]) -> Optional[str]:
    """Read the canonical sleep_debt_band for X1a / X1b.

    Phase 3 step 5 rewire: the sleep domain is now the source of truth.
    Prefer ``sleep.classified_state.sleep_debt_band``; fall back to the
    recovery block's echo when the sleep block wasn't expanded (e.g. a
    snapshot built without ``evidence_bundle``). Both derive from the
    same underlying ``sleep_hours`` signal, so the fallback preserves
    X1's behavior on pre-step-5 snapshots and test fixtures while the
    new primary path lights up under ``hai state snapshot
    --evidence-json`` + the sleep classifier.
    """

    sleep_band = _get(snapshot, "sleep", "classified_state", "sleep_debt_band")
    if sleep_band is not None:
        return sleep_band
    return _get(snapshot, "recovery", "classified_state", "sleep_debt_band")


def _acwr_ratio(snapshot: dict[str, Any]) -> Optional[float]:
    value = _get(snapshot, "recovery", "today", "acwr_ratio")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _body_battery(snapshot: dict[str, Any]) -> Optional[int]:
    """Read day-end body battery from the Phase 3 stress block.

    Body battery moved off ``accepted_recovery_state_daily`` onto
    ``accepted_stress_state_daily`` in migration 004. The snapshot
    surfaces it both on ``stress.today.body_battery_end_of_day`` and as
    the convenience key ``stress.today_body_battery``; this reader
    prefers the convenience key (cheaper, no nested get), falling back
    to the today row if only that is populated.
    """

    value = _get(snapshot, "stress", "today_body_battery")
    if value is None:
        value = _get(snapshot, "stress", "today", "body_battery_end_of_day")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _stress_band(
    snapshot: dict[str, Any],
    thresholds: dict[str, Any],
) -> Optional[str]:
    """Derive a categorical stress band from the Phase 3 stress block.

    Reads ``stress.today_garmin`` (Garmin's numeric 0-100 all-day stress)
    as the X7 input. Migration 004 moved this signal off the recovery
    accepted row onto ``accepted_stress_state_daily.garmin_all_day_stress``;
    the snapshot exposes it as the convenience key ``stress.today_garmin``.

    X7 still bands locally using the same numeric thresholds as pre-
    Phase-3. Once the stress domain ships a dedicated
    ``classify_stress_state`` (Phase 3 step 4) this reader will prefer
    ``stress.classified_state.garmin_stress_band`` and fall back to the
    local banding as a defensive second path — the band computation
    moves to the domain but X7's trigger registry stays here.
    """

    classified_band = _get(snapshot, "stress", "classified_state", "garmin_stress_band")
    if classified_band is not None:
        return classified_band

    value = _get(snapshot, "stress", "today_garmin")
    if value is None:
        value = _get(snapshot, "stress", "today", "garmin_all_day_stress")
    if value is None:
        return None
    try:
        score = int(value)
    except (TypeError, ValueError):
        return None
    x7_cfg = _get(thresholds, "synthesis", "x_rules", "x7") or {}
    very_high_min = int(x7_cfg.get("very_high_min_score", 80))
    high_min = int(x7_cfg.get("high_min_score", 60))
    moderate_min = int(x7_cfg.get("moderate_min_score", 40))
    if score >= very_high_min:
        return "very_high"
    if score >= high_min:
        return "high"
    if score >= moderate_min:
        return "moderate"
    return "low"


def _is_hard_proposal(proposal: dict[str, Any]) -> bool:
    """True when the proposal's action is the domain's baseline-hard action.

    A proposal that has already been softened or escalated at policy time
    (e.g. ``downgrade_intervals_to_tempo``, ``rest_day_recommended``,
    ``escalate_for_user_review``) is not "hard" and no further soften/block
    rule fires against it. This keeps X-rule mutations idempotent across
    re-runs.
    """

    domain = proposal.get("domain")
    registry = _DOMAIN_ACTION_REGISTRY.get(domain)
    if registry is None:
        return False
    return proposal.get("action") in registry["hard_actions"]


# ===========================================================================
# Phase A rules
# ===========================================================================

def evaluate_x1a(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X1a (soften): sleep_debt at configured trigger → downgrade hard sessions.

    Trigger: ``sleep.classified_state.sleep_debt_band`` equals the
    config-keyed band (default ``"moderate"``). Falls back to
    ``recovery.classified_state.sleep_debt_band`` on snapshots built
    without the sleep-domain expansion. Affects every hard proposal in
    the bundle.
    """

    trigger_band = _get(thresholds, "synthesis", "x_rules", "x1a", "sleep_debt_trigger_band")
    sleep_debt = _sleep_debt_band(snapshot)
    if sleep_debt is None or sleep_debt != trigger_band:
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        if not _is_hard_proposal(p):
            continue
        domain = p["domain"]
        registry = _DOMAIN_ACTION_REGISTRY.get(domain)
        if registry is None:
            continue
        firings.append(XRuleFiring(
            rule_id="X1a",
            tier="soften",
            affected_domain=domain,
            trigger_note=(
                f"sleep_debt_band={sleep_debt} with hard {domain} proposal "
                f"(action={p.get('action')})"
            ),
            recommended_mutation={
                "action": registry["downgrade_action"],
                "action_detail": {
                    "reason_token": "x1a_sleep_debt_trigger",
                    "trigger_band": sleep_debt,
                },
            },
            source_signals={
                "sleep_debt_band": sleep_debt,
                "proposal_domain": domain,
                "proposal_action": p.get("action"),
            },
            phase="A",
        ))
    return firings


def evaluate_x1b(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X1b (block): elevated sleep debt → escalate hard sessions.

    Trigger: ``sleep.classified_state.sleep_debt_band`` equals the
    config-keyed band (default ``"elevated"``). Falls back to
    ``recovery.classified_state.sleep_debt_band`` when the sleep block
    wasn't expanded. Forces escalate on every hard proposal.
    """

    trigger_band = _get(thresholds, "synthesis", "x_rules", "x1b", "sleep_debt_trigger_band")
    sleep_debt = _sleep_debt_band(snapshot)
    if sleep_debt is None or sleep_debt != trigger_band:
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        if not _is_hard_proposal(p):
            continue
        domain = p["domain"]
        registry = _DOMAIN_ACTION_REGISTRY.get(domain)
        if registry is None:
            continue
        firings.append(XRuleFiring(
            rule_id="X1b",
            tier="block",
            affected_domain=domain,
            trigger_note=(
                f"sleep_debt_band={sleep_debt} with hard {domain} proposal"
            ),
            recommended_mutation={
                "action": registry["escalate_action"],
                "action_detail": {
                    "reason_token": "x1b_sleep_debt_elevated",
                    "trigger_band": sleep_debt,
                },
            },
            source_signals={
                "sleep_debt_band": sleep_debt,
                "proposal_domain": domain,
            },
            phase="A",
        ))
    return firings


def _nutrition_deficit_and_protein(
    snapshot: dict[str, Any],
) -> tuple[Optional[float], Optional[float]]:
    """Read today's calorie deficit + protein ratio from the Phase 5
    nutrition block.

    Prefers ``nutrition.classified_state.calorie_deficit_kcal`` +
    ``protein_ratio`` — the classifier is the authoritative source of
    truth. Falls back to computing them from ``nutrition.today`` against
    the config targets when the bundle wasn't expanded (e.g. a snapshot
    built without ``evidence_bundle``). Both paths honour the same
    thresholds so the fallback stays in sync with the classifier.
    """

    deficit = _get(snapshot, "nutrition", "classified_state", "calorie_deficit_kcal")
    protein_ratio = _get(snapshot, "nutrition", "classified_state", "protein_ratio")
    if deficit is not None or protein_ratio is not None:
        return (
            float(deficit) if deficit is not None else None,
            float(protein_ratio) if protein_ratio is not None else None,
        )
    # Fallback: compute from today's row against the config targets.
    today = _get(snapshot, "nutrition", "today") or {}
    calories = today.get("calories")
    protein_g = today.get("protein_g")
    # Thresholds aren't in this function's closure; read from a stable
    # module import. A deeper wiring would accept thresholds as an arg,
    # but X2 already gets thresholds at call-time — we use those.
    return (
        None if calories is None else None,  # placeholder; real fallback in evaluate_x2
        None if protein_g is None else None,
    )


def evaluate_x2(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X2 (soften): nutrition deficit softens hard strength / recovery.

    Trigger: today's nutrition shows either
    ``calorie_deficit_kcal >= deficit_kcal_min`` OR
    ``protein_ratio < protein_ratio_max`` AND there is a hard strength
    or recovery proposal in the bundle. Thresholds default to the X2
    boundaries (500 kcal / 0.7 ratio) which align with the nutrition
    classifier's ``high_deficit`` / ``very_low`` band cutoffs — the
    X-rule reads the same numeric boundaries the classifier named.

    Target: soften the hard proposal to the domain's default downgrade
    action (``downgrade_to_moderate_load`` for strength,
    ``downgrade_hard_session_to_zone_2`` for recovery). Running is not
    X2-targeted in v1 — endurance fuelling is a different question than
    heavy-load training and would collapse a meaningful distinction
    if bundled here.

    Reads nutrition signals via
    :func:`_nutrition_deficit_and_protein` which prefers the nutrition
    classifier's output, falling back to computing against config
    targets so snapshots built without ``evidence_bundle`` still fire
    the rule.
    """

    cfg = _get(thresholds, "synthesis", "x_rules", "x2") or {}
    deficit_min = float(cfg.get("deficit_kcal_min", 500.0))
    protein_ratio_max = float(cfg.get("protein_ratio_max", 0.7))

    deficit, protein_ratio = _nutrition_deficit_and_protein(snapshot)

    # Fallback: if the classifier didn't fill these in, compute from
    # today's row against the nutrition classify targets. Keeps X2
    # correct on pre-step-4 snapshots and synthetic fixtures.
    if deficit is None or protein_ratio is None:
        today = _get(snapshot, "nutrition", "today") or {}
        targets = _get(thresholds, "classify", "nutrition", "targets") or {}
        cal_target = targets.get("calorie_target_kcal")
        prot_target = targets.get("protein_target_g")
        calories = today.get("calories") if isinstance(today, dict) else None
        protein_g = today.get("protein_g") if isinstance(today, dict) else None
        if deficit is None and calories is not None and cal_target is not None:
            deficit = float(cal_target) - float(calories)
        if (
            protein_ratio is None
            and protein_g is not None
            and prot_target is not None
            and float(prot_target) > 0
        ):
            protein_ratio = float(protein_g) / float(prot_target)

    deficit_triggers = deficit is not None and deficit >= deficit_min
    protein_triggers = protein_ratio is not None and protein_ratio < protein_ratio_max
    if not (deficit_triggers or protein_triggers):
        return []

    trigger_reason = (
        "deficit_and_protein_gap" if (deficit_triggers and protein_triggers)
        else ("calorie_deficit" if deficit_triggers else "protein_gap")
    )

    firings: list[XRuleFiring] = []
    for p in proposals:
        if p.get("domain") not in ("strength", "recovery"):
            continue
        if not _is_hard_proposal(p):
            continue
        domain = p["domain"]
        registry = _DOMAIN_ACTION_REGISTRY.get(domain)
        if registry is None:
            continue
        firings.append(XRuleFiring(
            rule_id="X2",
            tier="soften",
            affected_domain=domain,
            trigger_note=(
                f"nutrition {trigger_reason} "
                f"(calorie_deficit_kcal="
                f"{('unknown' if deficit is None else f'{deficit:.0f}')}, "
                f"protein_ratio="
                f"{('unknown' if protein_ratio is None else f'{protein_ratio:.2f}')}) "
                f"with hard {domain} proposal"
            ),
            recommended_mutation={
                "action": registry["downgrade_action"],
                "action_detail": {
                    "reason_token": f"x2_nutrition_{trigger_reason}",
                    "calorie_deficit_kcal": (
                        round(deficit, 1) if deficit is not None else None
                    ),
                    "protein_ratio": (
                        round(protein_ratio, 3) if protein_ratio is not None else None
                    ),
                },
            },
            source_signals={
                "calorie_deficit_kcal": deficit,
                "protein_ratio": protein_ratio,
                "proposal_domain": domain,
            },
            phase="A",
        ))
    return firings


def evaluate_x3a(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X3a (soften): 1.3 ≤ acwr_ratio < 1.5 → downgrade hard sessions."""

    cfg = _get(thresholds, "synthesis", "x_rules", "x3a") or {}
    lower = float(cfg.get("acwr_ratio_lower", 1.3))
    upper = float(cfg.get("acwr_ratio_upper", 1.5))
    acwr = _acwr_ratio(snapshot)
    if acwr is None or not (lower <= acwr < upper):
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        if not _is_hard_proposal(p):
            continue
        domain = p["domain"]
        registry = _DOMAIN_ACTION_REGISTRY.get(domain)
        if registry is None:
            continue
        firings.append(XRuleFiring(
            rule_id="X3a",
            tier="soften",
            affected_domain=domain,
            trigger_note=f"acwr_ratio={acwr:.3f} in [{lower}, {upper}) with hard {domain} proposal",
            recommended_mutation={
                "action": registry["downgrade_action"],
                "action_detail": {
                    "reason_token": "x3a_acwr_elevated",
                    "acwr_ratio": acwr,
                },
            },
            source_signals={
                "acwr_ratio": acwr,
                "proposal_domain": domain,
            },
            phase="A",
        ))
    return firings


def evaluate_x3b(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X3b (block): acwr_ratio ≥ 1.5 → escalate hard sessions."""

    cfg = _get(thresholds, "synthesis", "x_rules", "x3b") or {}
    minimum = float(cfg.get("acwr_ratio_min", 1.5))
    acwr = _acwr_ratio(snapshot)
    if acwr is None or acwr < minimum:
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        if not _is_hard_proposal(p):
            continue
        domain = p["domain"]
        registry = _DOMAIN_ACTION_REGISTRY.get(domain)
        if registry is None:
            continue
        firings.append(XRuleFiring(
            rule_id="X3b",
            tier="block",
            affected_domain=domain,
            trigger_note=f"acwr_ratio={acwr:.3f} ≥ {minimum} with hard {domain} proposal",
            recommended_mutation={
                "action": registry["escalate_action"],
                "action_detail": {
                    "reason_token": "x3b_acwr_spike",
                    "acwr_ratio": acwr,
                },
            },
            source_signals={
                "acwr_ratio": acwr,
                "proposal_domain": domain,
            },
            phase="A",
        ))
    return firings


# ---------------------------------------------------------------------------
# Strength cross-domain rules — X4 + X5.
# ---------------------------------------------------------------------------

_LOWER_BODY_GROUPS: frozenset[str] = frozenset({"quads", "hamstrings", "glutes"})


def _yesterday_strength_volume_by_group(
    snapshot: dict[str, Any],
) -> Optional[dict[str, float]]:
    """Return yesterday's ``volume_by_muscle_group_json`` as a dict, or
    None if no prior strength row exists or it's not parseable."""

    history = _get(snapshot, "strength", "history") or []
    if not history:
        return None
    # history is oldest-first per build_snapshot; yesterday is the last row.
    last = history[-1]
    raw = last.get("volume_by_muscle_group_json") if isinstance(last, dict) else None
    if not raw:
        return None
    if isinstance(raw, dict):
        return {k: float(v) for k, v in raw.items() if v is not None}
    try:
        import json as _json
        parsed = _json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(parsed, dict):
        return None
    return {k: float(v) for k, v in parsed.items() if v is not None}


def _yesterday_running_row(snapshot: dict[str, Any]) -> Optional[dict[str, Any]]:
    history = _get(snapshot, "running", "history") or []
    if not history:
        return None
    last = history[-1]
    return last if isinstance(last, dict) else None


def evaluate_x4(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X4 (soften): yesterday's heavy lower body caps running hard sessions.

    Trigger: any of ``{quads, hamstrings, glutes}`` in yesterday's
    ``strength.history[-1].volume_by_muscle_group_json`` meets the
    configured ``heavy_lower_body_min_volume`` threshold AND there is
    a hard running proposal in the bundle.

    Target: soften every hard running proposal to
    ``downgrade_to_easy_aerobic`` (the running registry's default
    downgrade action).
    """

    cfg = _get(thresholds, "synthesis", "x_rules", "x4") or {}
    threshold = float(cfg.get("heavy_lower_body_min_volume", 2000.0))

    vol_by_group = _yesterday_strength_volume_by_group(snapshot)
    if not vol_by_group:
        return []

    heavy_groups = [
        g for g in _LOWER_BODY_GROUPS
        if vol_by_group.get(g) is not None and vol_by_group[g] >= threshold
    ]
    if not heavy_groups:
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        if p.get("domain") != "running":
            continue
        if not _is_hard_proposal(p):
            continue
        registry = _DOMAIN_ACTION_REGISTRY["running"]
        firings.append(XRuleFiring(
            rule_id="X4",
            tier="soften",
            affected_domain="running",
            trigger_note=(
                f"yesterday's lower-body strength volume "
                f"{sorted(heavy_groups)} >= {threshold} kg·reps with hard "
                f"running proposal"
            ),
            recommended_mutation={
                "action": registry["downgrade_action"],
                "action_detail": {
                    "reason_token": "x4_heavy_lower_body_yesterday",
                    "heavy_groups": sorted(heavy_groups),
                    "threshold_kg_reps": threshold,
                },
            },
            source_signals={
                "yesterday_volume_by_muscle_group": {
                    g: vol_by_group.get(g) for g in _LOWER_BODY_GROUPS
                },
                "proposal_domain": "running",
            },
            phase="A",
        ))
    return firings


def evaluate_x5(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X5 (soften): yesterday's long run / hard intervals caps lower-body strength.

    Trigger: yesterday's running row had either
    ``vigorous_intensity_min >= x5.vigorous_intensity_min`` OR
    ``total_duration_s >= x5.long_run_min_duration_s`` AND there is
    a hard strength proposal in the bundle.

    Target: soften the hard strength proposal to
    ``downgrade_to_technique_or_accessory`` (rule-local override of
    the strength registry's default ``downgrade_to_moderate_load`` —
    fatigue from yesterday's endurance work argues for technique,
    not heavier loading).
    """

    cfg = _get(thresholds, "synthesis", "x_rules", "x5") or {}
    min_vigorous_min = int(cfg.get("vigorous_intensity_min", 20))
    min_long_run_s = int(cfg.get("long_run_min_duration_s", 4500))

    yrow = _yesterday_running_row(snapshot)
    if yrow is None:
        return []

    vig = yrow.get("vigorous_intensity_min")
    dur = yrow.get("total_duration_s")
    triggered_reason: Optional[str] = None
    if vig is not None and vig >= min_vigorous_min:
        triggered_reason = "hard_intervals"
    elif dur is not None and dur >= min_long_run_s:
        triggered_reason = "long_run"
    if triggered_reason is None:
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        if p.get("domain") != "strength":
            continue
        if not _is_hard_proposal(p):
            continue
        firings.append(XRuleFiring(
            rule_id="X5",
            tier="soften",
            affected_domain="strength",
            trigger_note=(
                f"yesterday's running = {triggered_reason} "
                f"(vigorous_intensity_min={vig}, total_duration_s={dur}) "
                f"with hard strength proposal"
            ),
            recommended_mutation={
                "action": "downgrade_to_technique_or_accessory",
                "action_detail": {
                    "reason_token": "x5_endurance_fatigue_yesterday",
                    "trigger": triggered_reason,
                    "yesterday_vigorous_intensity_min": vig,
                    "yesterday_total_duration_s": dur,
                },
            },
            source_signals={
                "yesterday_vigorous_intensity_min": vig,
                "yesterday_total_duration_s": dur,
                "proposal_domain": "strength",
            },
            phase="A",
        ))
    return firings


def evaluate_x6a(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X6a (soften): body_battery < 30 → downgrade every hard proposal."""

    cfg = _get(thresholds, "synthesis", "x_rules", "x6a") or {}
    ceiling = int(cfg.get("body_battery_max", 30))
    bb = _body_battery(snapshot)
    if bb is None or bb >= ceiling:
        return []

    # X6b also reads body_battery; if its (lower) threshold fires, skip X6a
    # for the same proposal to avoid double-downgrading. X6b's block tier
    # wins via precedence anyway, but suppressing the duplicate keeps the
    # firings list clean.
    x6b_cfg = _get(thresholds, "synthesis", "x_rules", "x6b") or {}
    x6b_ceiling = int(x6b_cfg.get("body_battery_max", 15))
    if bb < x6b_ceiling:
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        if not _is_hard_proposal(p):
            continue
        domain = p["domain"]
        registry = _DOMAIN_ACTION_REGISTRY.get(domain)
        if registry is None:
            continue
        firings.append(XRuleFiring(
            rule_id="X6a",
            tier="soften",
            affected_domain=domain,
            trigger_note=f"body_battery_end_of_day={bb} < {ceiling} (depleted reserve)",
            recommended_mutation={
                "action": registry["downgrade_action"],
                "action_detail": {
                    "reason_token": "x6a_body_battery_low",
                    "body_battery_end_of_day": bb,
                },
            },
            source_signals={
                "body_battery_end_of_day": bb,
                "proposal_domain": domain,
            },
            phase="A",
        ))
    return firings


def evaluate_x6b(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X6b (block): body_battery < 15 → escalate every hard proposal."""

    cfg = _get(thresholds, "synthesis", "x_rules", "x6b") or {}
    ceiling = int(cfg.get("body_battery_max", 15))
    bb = _body_battery(snapshot)
    if bb is None or bb >= ceiling:
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        if not _is_hard_proposal(p):
            continue
        domain = p["domain"]
        registry = _DOMAIN_ACTION_REGISTRY.get(domain)
        if registry is None:
            continue
        firings.append(XRuleFiring(
            rule_id="X6b",
            tier="block",
            affected_domain=domain,
            trigger_note=f"body_battery_end_of_day={bb} < {ceiling} (severely depleted)",
            recommended_mutation={
                "action": registry["escalate_action"],
                "action_detail": {
                    "reason_token": "x6b_body_battery_critical",
                    "body_battery_end_of_day": bb,
                },
            },
            source_signals={
                "body_battery_end_of_day": bb,
                "proposal_domain": domain,
            },
            phase="A",
        ))
    return firings


def evaluate_x7(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X7 (cap_confidence): elevated stress → cap confidence at moderate.

    No action mutation — only caps confidence on every proposal's final
    recommendation. Applies regardless of whether the proposal is "hard".
    """

    cfg = _get(thresholds, "synthesis", "x_rules", "x7") or {}
    trigger_bands = set(cfg.get("stress_trigger_bands") or [])
    band = _stress_band(snapshot, thresholds)
    if band is None or band not in trigger_bands:
        return []

    firings: list[XRuleFiring] = []
    for p in proposals:
        domain = p.get("domain")
        if not domain:
            continue
        firings.append(XRuleFiring(
            rule_id="X7",
            tier="cap_confidence",
            affected_domain=domain,
            trigger_note=f"stress_band={band} ∈ {sorted(trigger_bands)}",
            recommended_mutation=None,  # cap is implicit in tier
            source_signals={
                "stress_band": band,
                "garmin_all_day_stress": _get(snapshot, "stress", "today_garmin"),
            },
            phase="A",
        ))
    return firings


PHASE_A_EVALUATORS = (
    evaluate_x1a,
    evaluate_x1b,
    evaluate_x2,
    evaluate_x3a,
    evaluate_x3b,
    evaluate_x4,
    evaluate_x5,
    evaluate_x6a,
    evaluate_x6b,
    evaluate_x7,
)


def evaluate_phase_a(
    snapshot: dict[str, Any],
    proposals: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """Run every Phase A rule and return the concatenated firings list.

    Order matches :data:`PHASE_A_EVALUATORS`. The orchestration layer
    applies mutations with tier precedence (block > soften); the order
    here is therefore informational and does not affect final drafts.
    """

    firings: list[XRuleFiring] = []
    for evaluator in PHASE_A_EVALUATORS:
        firings.extend(evaluator(snapshot, proposals, thresholds))
    return firings


# ===========================================================================
# Phase B rules — action_detail adjustments only, guarded write surface
# ===========================================================================

def evaluate_x9(
    snapshot: dict[str, Any],
    drafts: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """X9 (adjust): training intensity → nutrition target adjustments.

    v1 scope: operates only on ``nutrition`` drafts. For every draft in
    the nutrition domain, if the user has **explicitly planned** a
    session (``planned_session_type`` non-null on cleaned evidence) and
    any training-domain draft (recovery / running / strength) carries a
    "hard" baseline action, append a note to the nutrition
    ``action_detail`` bumping protein / carb targets.

    **Precondition added in v0.1.4 (acceptance criterion #7):** the
    ``planned_session_type`` gate. Before the gate, X9 bumped nutrition
    whenever a domain proposal defaulted to its hard baseline action,
    even when the user hadn't stated what they were planning. That's
    the opposite of conservative: "we don't know what you're doing, so
    we're bumping your protein anyway." After the gate, if no readiness
    intake has declared a planned session, X9 stays quiet.

    ``planned_session_type`` is sourced from
    ``snapshot.recovery.evidence`` (populated by ``hai clean`` from the
    manual_readiness block) — the same field the recovery-readiness
    skill keys on.
    """

    nutrition_drafts = [d for d in drafts if d.get("domain") == "nutrition"]
    if not nutrition_drafts:
        return []

    # Precondition: user has explicitly planned something today.
    recovery_block = snapshot.get("recovery") or {}
    evidence = recovery_block.get("evidence") or {}
    planned_session_type = evidence.get("planned_session_type")
    if not planned_session_type:
        return []

    # Phase 5 step 4: strength is now a first-class training domain and
    # a hard strength session is as much a protein-driver as a hard
    # recovery/running session. X9 fires on any of the three.
    training_hard = any(
        d.get("domain") in ("recovery", "running", "strength")
        and _is_hard_proposal(d)
        for d in drafts
    )
    if not training_hard:
        return []

    firings: list[XRuleFiring] = []
    for d in nutrition_drafts:
        firings.append(XRuleFiring(
            rule_id="X9",
            tier="adjust",
            affected_domain="nutrition",
            trigger_note="training_intensity=hard → nutrition target adjustment",
            recommended_mutation={
                "action_detail": {
                    "reason_token": "x9_training_intensity_bump",
                    "protein_target_multiplier": 1.1,
                },
            },
            source_signals={
                "training_intensity": "hard",
                "nutrition_domain": d.get("domain"),
            },
            phase="B",
        ))
    return firings


PHASE_B_EVALUATORS = (
    evaluate_x9,
)


def evaluate_phase_b(
    snapshot: dict[str, Any],
    drafts: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[XRuleFiring]:
    """Run every Phase B rule and return firings. Does NOT apply mutations.

    Callers run :func:`guard_phase_b_mutation` and then :func:`apply_phase_b`
    to mutate drafts. The split lets tests assert against the raw firing
    list before mutation application.
    """

    firings: list[XRuleFiring] = []
    for evaluator in PHASE_B_EVALUATORS:
        firings.extend(evaluator(snapshot, drafts, thresholds))
    return firings


def guard_phase_b_mutation(firing: XRuleFiring) -> None:
    """Reject any Phase B firing that violates the write-surface contract.

    Raises :class:`XRuleWriteSurfaceViolation` on:

      - tier not equal to ``"adjust"``
      - ``affected_domain`` not in :data:`PHASE_B_TARGETS[rule_id]`
      - ``recommended_mutation`` touching ``action`` (Phase B may only
        mutate ``action_detail``)
      - ``recommended_mutation`` being ``None`` (every Phase B firing
        must carry a concrete mutation — caps are Phase A only)

    Runs at mutation-application time in the orchestration layer.
    """

    if firing.phase != "B":
        raise XRuleWriteSurfaceViolation(
            f"guard_phase_b_mutation called on non-B firing {firing.rule_id!r}"
        )
    if firing.tier != "adjust":
        raise XRuleWriteSurfaceViolation(
            f"Phase B tier must be 'adjust'; got {firing.tier!r} on {firing.rule_id!r}"
        )
    allowed_domains = PHASE_B_TARGETS.get(firing.rule_id)
    if allowed_domains is None:
        raise XRuleWriteSurfaceViolation(
            f"Phase B rule {firing.rule_id!r} has no target registry entry"
        )
    if firing.affected_domain not in allowed_domains:
        raise XRuleWriteSurfaceViolation(
            f"Phase B rule {firing.rule_id!r} tried to touch domain "
            f"{firing.affected_domain!r} — allowed: {sorted(allowed_domains)}"
        )
    mutation = firing.recommended_mutation
    if not isinstance(mutation, dict):
        raise XRuleWriteSurfaceViolation(
            f"Phase B rule {firing.rule_id!r} must carry a dict mutation; "
            f"got {type(mutation).__name__}"
        )
    if "action" in mutation:
        raise XRuleWriteSurfaceViolation(
            f"Phase B rule {firing.rule_id!r} attempted to mutate 'action' — "
            f"Phase B may only mutate 'action_detail'"
        )
    if "action_detail" not in mutation:
        raise XRuleWriteSurfaceViolation(
            f"Phase B rule {firing.rule_id!r} mutation must contain 'action_detail'"
        )


# ===========================================================================
# Mutation application helpers
# ===========================================================================

def apply_phase_a(
    proposal: dict[str, Any],
    firings: Iterable[XRuleFiring],
) -> tuple[dict[str, Any], list[str]]:
    """Return ``(mutated_proposal, fired_rule_ids)`` for a single proposal.

    Precedence:
      1. ``block`` tier wins over ``soften`` tier. If any block firing
         targets this proposal, the block mutation is applied and any
         soften firings are recorded-as-fired but not applied.
      2. ``cap_confidence`` firings apply independently — they lower
         ``confidence`` to ``"moderate"`` when the current confidence is
         ``"high"``. They never raise.
      3. If multiple block firings target the same proposal, the first
         one in iteration order wins (stable). Ditto multiple softens.

    Returns the mutated proposal as a fresh dict; the input is not
    modified. ``fired_rule_ids`` lists every rule id that matched this
    proposal (including capped-by-precedence softens) so the firings
    table receives a complete audit trail.
    """

    proposal_domain = proposal.get("domain")
    relevant = [f for f in firings if f.affected_domain == proposal_domain]

    blocks = [f for f in relevant if f.tier == "block"]
    softens = [f for f in relevant if f.tier == "soften"]
    caps = [f for f in relevant if f.tier == "cap_confidence"]

    mutated = dict(proposal)
    if "action_detail" in mutated and isinstance(mutated["action_detail"], dict):
        mutated["action_detail"] = dict(mutated["action_detail"])

    applied_action_mutation = False
    # Precedence: block > soften.
    if blocks:
        block = blocks[0]
        mutation = block.recommended_mutation or {}
        if "action" in mutation:
            mutated["action"] = mutation["action"]
        if "action_detail" in mutation:
            mutated["action_detail"] = dict(mutation["action_detail"])
        applied_action_mutation = True
    elif softens:
        soften = softens[0]
        mutation = soften.recommended_mutation or {}
        if "action" in mutation:
            mutated["action"] = mutation["action"]
        if "action_detail" in mutation:
            mutated["action_detail"] = dict(mutation["action_detail"])
        applied_action_mutation = True

    # cap_confidence: independent. Lower "high" to "moderate"; never raise.
    if caps:
        current = mutated.get("confidence")
        if current == "high":
            mutated["confidence"] = "moderate"

    fired_ids = [f.rule_id for f in relevant]
    return mutated, fired_ids


def apply_phase_b(
    draft: dict[str, Any],
    firings: Iterable[XRuleFiring],
) -> tuple[dict[str, Any], list[str]]:
    """Return ``(mutated_draft, fired_rule_ids)`` after Phase B.

    Every firing is guarded by :func:`guard_phase_b_mutation` before
    application. Mutations merge into ``action_detail`` (not replace);
    keys from later firings overwrite earlier ones on collision.
    """

    domain = draft.get("domain")
    relevant = [f for f in firings if f.affected_domain == domain]
    if not relevant:
        return dict(draft), []

    mutated = dict(draft)
    detail = dict(mutated.get("action_detail") or {})
    fired_ids: list[str] = []
    for firing in relevant:
        guard_phase_b_mutation(firing)
        mutation = firing.recommended_mutation or {}
        incoming_detail = mutation.get("action_detail") or {}
        detail.update(incoming_detail)
        fired_ids.append(firing.rule_id)

    mutated["action_detail"] = detail
    return mutated, fired_ids
