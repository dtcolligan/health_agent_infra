"""Weekly-review prose builder — W52 step 4 (v0.2.0 §2.D + §2.K).

Consumes the typed :class:`WeeklyAggregation` row set from
``core/review/weekly.py`` and produces a structured atom-shaped
prose bundle the render layer (step 5) translates to markdown / JSON
and the claim-card emission layer (step 7) reads to write per-atom
``weekly_claim_card`` rows.

W-EXPLAIN-UX-CARRY consumption (PLAN §2.K + acceptance #7). The
prose-builder enforces all six obligations from
``reporting/docs/archive/cycle_artifacts/explain_ux_review_2026_05.md``:

  1. Rule IDs (F-EXPLAIN-01) — atoms surface ``public_name_for``
     plain-English phrasing; raw ``X<N>`` strings appear ONLY in
     parentheses (audit citation), never as the leading subject.
  2. Phase A / B (F-EXPLAIN-02) — atoms never carry the raw
     ``phase_a`` / ``phase_b`` strings; the runtime concept
     surfaces as inline prose
     ("rules that shaped the recommendation" /
      "rules that adjusted the result after the skill ran").
  3. ``synthesis_meta`` (F-EXPLAIN-03) — debug telemetry never
     appears in atom text. The render layer keeps
     ``synthesis_meta`` in JSON only.
  4. Caveat tokens (F-EXPLAIN-04, P0) — every reason_token routes
     through :func:`translate_caveat` from
     ``core/explain/caveat_translations.py`` before reaching prose.
     No raw caveat-token string surfaces in atom text.
  5. Goal echo (F-EXPLAIN-05) — the bundle's header section opens
     with the user's ``primary_goal`` value (read from
     ``user_memory``) as the first noun phrase. Honest abstain
     when no goal is recorded.
  6. Locator-cited prose (F-EXPLAIN-07) — when an atom carries
     locators, prose explicitly names a pk-field (date or metric)
     before the claim ("Looking at your resting heart rate on
     April 27, 28, 29, …").

The bundle's atoms are deliberately strict: each atom_text is a
single sentence with its atom_type, derivation_path, locator_set,
and audit_refs. W58D consumes these to validate every quantitative
+ comparative claim against source state.

Scope discipline (PLAN §2.D "What this WS does NOT do"):
  - No markdown / JSON rendering (step 5).
  - No claim-card persistence (step 7).
  - No CLI surface (step 6).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Optional

from health_agent_infra.core.explain.caveat_translations import (
    translate_caveat,
)
from health_agent_infra.core.review.weekly import (
    CanonicalPlanRow,
    DataQualityClassification,
    TABLE_TO_DOMAIN,
    WeeklyAggregation,
    WeeklyCoverage,
    WeeklyDataQualityRollup,
    WeeklyEvidenceCard,
    WeeklyRecommendation,
    WeeklyXRuleFiring,
)
from health_agent_infra.core.review.weekly_card import (
    project_weekly_card,
)
from health_agent_infra.core.synthesis_policy import public_name_for


# Atom types that emit a weekly_claim_card row when the prose ships.
# Qualitative atoms emit no card per F-PLAN-10 (qualitative atoms
# contain no factual past-week content and so have no claim to gate).
_CARD_EMITTING_ATOM_TYPES = frozenset({"quantitative", "comparative"})


# Mechanical assertion alphabet for `assert_qualitative_atom_is_non_factual`
# per F-PLAN-10 round-1 addition. Qualitative atoms must contain none of:
#   - numeric tokens (\d+)
#   - month-name date tokens (January, February, ...)
#   - comparison operators (<, >, <=, >=, ratio language)
_NUMERIC_RE = __import__("re").compile(r"\b\d+\b")
_DATE_MONTH_RE = __import__("re").compile(
    r"\b(January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\b"
)
_COMPARISON_TOKENS = frozenset({
    "more than", "less than", "greater than", "fewer than",
    "above", "below", "above the", "below the",
    "↑", "↓", "→", ">", "<", ">=", "<=",
})


# Six domain order for stable section emission.
_DOMAIN_ORDER: tuple[str, ...] = (
    "recovery", "running", "sleep",
    "stress", "strength", "nutrition",
)


# ---------------------------------------------------------------------------
# Typed prose dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WeeklyAtom:
    """One factual or qualitative claim in the weekly prose.

    ``atom_type`` per W-FACT-ATOM contract:
      - ``quantitative``: contains a numeric or date value
        (validated by W58D against locators / audit_refs).
      - ``comparative``: compares two state slices
        (also W58D-validated).
      - ``qualitative``: framing / disposition prose with NO
        factual past-week content (mechanically asserted: no
        numeric tokens, no date tokens, no comparison operators).

    ``derivation_path`` per W-EVCARD-WEEKLY contract: ``aggregate``
    | ``comparison`` | ``literal``.

    Quantitative + comparative atoms get ``weekly_claim_card`` rows
    written in step 7. Qualitative atoms emit no card.
    """

    atom_id: str
    atom_text: str
    atom_type: str
    derivation_path: str
    domain: Optional[str]
    locator_set: list[dict] = field(default_factory=list)
    audit_refs: dict[str, list] = field(default_factory=dict)


@dataclass(frozen=True)
class WeeklyProseSection:
    """One titled section of the weekly prose.

    ``section_id`` is stable across runs (`header`, `domain_recovery`,
    `data_quality`, `cadence`, `footer`, ...) so the render layer
    can map sections to markdown headings deterministically.
    """

    section_id: str
    title: str
    atoms: list[WeeklyAtom]


@dataclass(frozen=True)
class WeeklyProseBundle:
    """Complete prose output for one week.

    On the abstain branch (``coverage.weekly_status ==
    'insufficient_data'``), ``sections`` is empty and the render
    layer surfaces the abstain template directly from ``coverage``.
    The abstain branch writes no claim cards (validation is
    structurally simpler — deterministic substitution from
    coverage metadata, no prose authoring).
    """

    iso_week: str
    user_id: str
    primary_goal: Optional[str]
    coverage: WeeklyCoverage
    data_quality_rollup: WeeklyDataQualityRollup
    sections: list[WeeklyProseSection]
    deferred_domains: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# user_memory primary_goal lookup (F-EXPLAIN-05)
# ---------------------------------------------------------------------------


def load_primary_goal(
    conn: sqlite3.Connection,
    *,
    user_id: str,
) -> Optional[str]:
    """Read the most-recent active ``primary_goal`` entry from
    ``user_memory``. Returns ``None`` when no active goal is recorded
    — the prose builder surfaces this honestly per W-EXPLAIN-UX-CARRY
    obligation #5 (no fabricated goal echo).
    """

    try:
        row = conn.execute(
            "SELECT value FROM user_memory "
            "WHERE user_id = ? AND key = 'primary_goal' "
            "  AND archived_at IS NULL "
            "ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    if row is None:
        return None
    value = row["value"] if hasattr(row, "keys") else row[0]
    return value if value else None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def build_weekly_prose(
    conn: sqlite3.Connection,
    aggregation: WeeklyAggregation,
    coverage: WeeklyCoverage,
    data_quality_rollup: WeeklyDataQualityRollup,
    *,
    deferred_domains: Optional[list[str]] = None,
) -> WeeklyProseBundle:
    """Compose the full weekly prose bundle.

    On ``coverage.weekly_status == "insufficient_data"`` returns a
    bundle with empty sections — the render layer surfaces the
    abstain template directly from coverage metadata.
    """

    primary_goal = load_primary_goal(conn, user_id=aggregation.user_id)
    deferred = list(deferred_domains or [])

    if coverage.weekly_status == "insufficient_data":
        return WeeklyProseBundle(
            iso_week=aggregation.iso_week,
            user_id=aggregation.user_id,
            primary_goal=primary_goal,
            coverage=coverage,
            data_quality_rollup=data_quality_rollup,
            sections=[],
            deferred_domains=deferred,
        )

    sections: list[WeeklyProseSection] = []

    # 1. Header section — goal echo (F-EXPLAIN-05).
    sections.append(_build_header_section(
        iso_week=aggregation.iso_week,
        primary_goal=primary_goal,
        coverage=coverage,
    ))

    # 2. Per-domain sections in stable order.
    rec_by_domain = _group_recommendations_by_domain(
        aggregation.recommendations,
    )
    cards_by_rec = _group_evidence_cards_by_rec(aggregation.evidence_cards)
    firings_by_plan = _group_firings_by_plan(aggregation.x_rule_firings)
    plan_by_id = {p.daily_plan_id: p for p in aggregation.canonical_plans}

    for domain in _DOMAIN_ORDER:
        if domain in deferred:
            sections.append(_build_deferred_domain_section(domain))
            continue
        domain_recs = rec_by_domain.get(domain, [])
        if not domain_recs:
            continue
        sections.append(_build_domain_section(
            domain=domain,
            recommendations=domain_recs,
            evidence_cards_by_rec=cards_by_rec,
            firings_by_plan=firings_by_plan,
            plans_by_id=plan_by_id,
        ))

    # 3. Data-quality section.
    sections.append(_build_data_quality_section(data_quality_rollup))

    # 4. Cadence section.
    sections.append(_build_cadence_section(
        runtime_events=aggregation.runtime_events,
        coverage=coverage,
    ))

    # 5. Footer (purely qualitative — disposition + carry-forward
    # framing, never a factual past-week claim).
    sections.append(_build_footer_section(
        coverage=coverage,
        deferred_domains=deferred,
    ))

    return WeeklyProseBundle(
        iso_week=aggregation.iso_week,
        user_id=aggregation.user_id,
        primary_goal=primary_goal,
        coverage=coverage,
        data_quality_rollup=data_quality_rollup,
        sections=sections,
        deferred_domains=deferred,
    )


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _build_header_section(
    *,
    iso_week: str,
    primary_goal: Optional[str],
    coverage: WeeklyCoverage,
) -> WeeklyProseSection:
    """Header — goal echo (F-EXPLAIN-05). The first noun phrase of
    the body references the user's ``primary_goal`` when set; honest
    abstain otherwise.

    All atoms in this section are ``qualitative`` (framing, not
    factual past-week claims) so they emit no claim cards.
    """

    atoms: list[WeeklyAtom] = []
    if primary_goal:
        atoms.append(WeeklyAtom(
            atom_id="header.goal_echo",
            atom_text=(
                f"Your primary goal — {primary_goal} — frames how this "
                f"week's evidence reads."
            ),
            atom_type="qualitative",
            derivation_path="literal",
            domain=None,
        ))
    else:
        atoms.append(WeeklyAtom(
            atom_id="header.goal_abstain",
            atom_text=(
                "No primary goal is recorded in user memory — this "
                "review is plan-driven and does not echo a goal "
                "frame. Set one with `hai memory set primary_goal "
                "your-goal-here` to ground future reviews."
            ),
            atom_type="qualitative",
            derivation_path="literal",
            domain=None,
        ))

    atoms.append(WeeklyAtom(
        atom_id="header.coverage_frame",
        atom_text=(
            "This review is grounded in plan evidence from the "
            "canonical (non-superseded) version of each day."
        ),
        atom_type="qualitative",
        derivation_path="literal",
        domain=None,
    ))

    return WeeklyProseSection(
        section_id="header",
        title=f"Weekly review — {iso_week}",
        atoms=atoms,
    )


def _build_domain_section(
    *,
    domain: str,
    recommendations: list[WeeklyRecommendation],
    evidence_cards_by_rec: dict[str, list[WeeklyEvidenceCard]],
    firings_by_plan: dict[str, list[WeeklyXRuleFiring]],
    plans_by_id: dict[str, CanonicalPlanRow],
) -> WeeklyProseSection:
    """Per-domain section.

    For each recommendation:
      * Emit one quantitative atom describing the action + date set
        (locator-cited prose per F-EXPLAIN-07).
      * If the recommendation's plan had X-rule firings affecting
        this domain, emit one comparative atom describing the
        Phase A vs Phase B framing in plain English (F-EXPLAIN-02:
        no raw `phase_a`/`phase_b` strings).
      * Caveat tokens flow through :func:`translate_caveat`
        (F-EXPLAIN-04: P0).
      * Rule IDs surface only in parentheses (F-EXPLAIN-01).
    """

    atoms: list[WeeklyAtom] = []
    rec_count = len(recommendations)
    distinct_dates = sorted({r.for_date for r in recommendations})

    # Section-level summary (quantitative).
    atoms.append(WeeklyAtom(
        atom_id=f"domain_{domain}.recommendation_count",
        atom_text=(
            f"You received {rec_count} {domain} recommendation"
            f"{'' if rec_count == 1 else 's'} on "
            f"{_format_date_list(distinct_dates)}."
        ),
        atom_type="quantitative",
        derivation_path="aggregate",
        domain=domain,
        locator_set=[],
        audit_refs={
            "recommendation_log": [r.recommendation_id for r in recommendations],
        },
    ))

    # Per-recommendation atoms.
    for rec in recommendations:
        cards = evidence_cards_by_rec.get(rec.recommendation_id, [])
        plan = plans_by_id.get(rec.daily_plan_id) if rec.daily_plan_id else None
        firings = firings_by_plan.get(rec.daily_plan_id, []) if rec.daily_plan_id else []
        domain_firings = [f for f in firings if f.affected_domain == domain]

        # Locator-cited lead-in (F-EXPLAIN-07).
        lead_in = _format_locator_lead_in(rec.evidence_locators, domain)
        action_phrase = _humanise_action(rec.action)
        rationale_text = _summarise_rationale(rec.payload.get("rationale") or [])

        prose = (
            f"{lead_in}On {_format_date(rec.for_date)} the {domain} "
            f"recommendation was \"{action_phrase}\" at "
            f"{rec.confidence} confidence{rationale_text}."
        )
        atoms.append(WeeklyAtom(
            atom_id=f"domain_{domain}.rec.{rec.recommendation_id}",
            atom_text=prose,
            atom_type="quantitative",
            derivation_path="aggregate",
            domain=domain,
            locator_set=list(rec.evidence_locators or []),
            audit_refs={
                "recommendation_log": [rec.recommendation_id],
                "daily_plan": [rec.daily_plan_id] if rec.daily_plan_id else [],
            },
        ))

        # Phase A vs Phase B framing for any firings on this rec's
        # plan (F-EXPLAIN-02). Comparative atom — claims a
        # before/after relationship.
        if domain_firings:
            atom_text = _phase_a_b_framing(domain_firings)
            atoms.append(WeeklyAtom(
                atom_id=(
                    f"domain_{domain}.firings.{rec.recommendation_id}"
                ),
                atom_text=atom_text,
                atom_type="comparative",
                derivation_path="comparison",
                domain=domain,
                locator_set=[],
                audit_refs={
                    "x_rule_firing": [f.firing_id for f in domain_firings],
                    "daily_plan": [rec.daily_plan_id] if rec.daily_plan_id else [],
                },
            ))

    return WeeklyProseSection(
        section_id=f"domain_{domain}",
        title=f"{domain.capitalize()}",
        atoms=atoms,
    )


def _build_deferred_domain_section(domain: str) -> WeeklyProseSection:
    """Deferred-domain section (F-PLAN-R3-01 + acceptance #8).

    When a domain fork-defers its W-PROV-2 emission to a later
    cycle, W52 emits NO quantitative or comparative atoms for that
    domain. The single qualitative atom surfaces the literal
    disposition string the test pins.

    Disposition phrasing is deictic (no version-string numerics) so
    the qualitative atom is genuinely non-factual under F-PLAN-10's
    mechanical assertion. (Earlier wording read ``v0.2.1 W-PROV-3``;
    the suffix matched ``\\b\\d+\\b`` which W-FACT-ATOM's parser
    surfaced as a hidden alignment hole.)
    """

    atom = WeeklyAtom(
        atom_id=f"domain_{domain}.deferred",
        atom_text=(
            f"domain {domain}: insufficient provenance — quantitative "
            f"and comparative claims suppressed pending the next "
            f"provenance cycle"
        ),
        atom_type="qualitative",
        derivation_path="literal",
        domain=domain,
    )
    return WeeklyProseSection(
        section_id=f"domain_{domain}",
        title=f"{domain.capitalize()} (deferred)",
        atoms=[atom],
    )


def _build_data_quality_section(
    rollup: WeeklyDataQualityRollup,
) -> WeeklyProseSection:
    """Data-quality section. Cites the four classification counts
    using the existing ``sync_run_log.mode`` lane (F-PLAN-04).
    """

    atoms: list[WeeklyAtom] = []
    total = (
        rollup.fresh_count
        + rollup.stale_pull_count
        + rollup.retrospective_manual_count
        + rollup.unclassifiable_count
    )
    atoms.append(WeeklyAtom(
        atom_id="data_quality.summary",
        atom_text=(
            f"Of {total} sync run{'' if total == 1 else 's'} this week, "
            f"{rollup.fresh_count} ran for the same day they covered, "
            f"{rollup.stale_pull_count} pulled data older than "
            f"{rollup.threshold_hours} hours from upstream "
            f"(stale-pull lane), "
            f"{rollup.retrospective_manual_count} were manual "
            f"backfill entries, and {rollup.unclassifiable_count} "
            f"could not be classified."
        ),
        atom_type="quantitative",
        derivation_path="aggregate",
        domain=None,
        locator_set=[],
        audit_refs={
            "sync_run_log": [s.sync_id for s in rollup.per_sync],
        },
    ))
    return WeeklyProseSection(
        section_id="data_quality",
        title="Data quality",
        atoms=atoms,
    )


def _build_cadence_section(
    *,
    runtime_events: list,
    coverage: WeeklyCoverage,
) -> WeeklyProseSection:
    """Cadence section — how many days the user actually ran
    ``hai daily`` this week.
    """

    daily_runs = [e for e in runtime_events if e.command == "hai daily"]
    distinct_run_days = sorted({
        e.started_at[:10] for e in daily_runs if e.started_at
    })
    atoms = [WeeklyAtom(
        atom_id="cadence.hai_daily_runs",
        atom_text=(
            f"You ran `hai daily` on {len(distinct_run_days)} of 7 days "
            f"this week."
        ),
        atom_type="quantitative",
        derivation_path="aggregate",
        domain=None,
        locator_set=[],
        audit_refs={
            "runtime_event_log": [e.event_id for e in daily_runs],
        },
    )]
    return WeeklyProseSection(
        section_id="cadence",
        title="Cadence",
        atoms=atoms,
    )


def _build_footer_section(
    *,
    coverage: WeeklyCoverage,
    deferred_domains: list[str],
) -> WeeklyProseSection:
    """Footer — qualitative framing only. No factual past-week
    content (mechanical assertion: ``test_review_weekly`` confirms).

    Deferred-domain status is already conveyed by (a) each deferred
    domain's own qualitative disposition atom in its domain section,
    (b) the ``deferred_domains`` field in the JSON output, and
    (c) the ``## <Domain> (deferred)`` markdown heading. The footer
    therefore does not name deferral counts — naming a count here
    would emit a numeric token that violates F-PLAN-10's mechanical
    assertion (W-FACT-ATOM finding).
    """

    text = (
        "This review is informational. Nothing here mutates intent, "
        "targets, or thresholds — that path is user-gated."
    )
    return WeeklyProseSection(
        section_id="footer",
        title="Notes",
        atoms=[WeeklyAtom(
            atom_id="footer.disposition",
            atom_text=text,
            atom_type="qualitative",
            derivation_path="literal",
            domain=None,
        )],
    )


# ---------------------------------------------------------------------------
# Atom helpers
# ---------------------------------------------------------------------------


def _group_recommendations_by_domain(
    recommendations: list[WeeklyRecommendation],
) -> dict[str, list[WeeklyRecommendation]]:
    out: dict[str, list[WeeklyRecommendation]] = {}
    for rec in recommendations:
        out.setdefault(rec.domain, []).append(rec)
    return out


def _group_evidence_cards_by_rec(
    cards: list[WeeklyEvidenceCard],
) -> dict[str, list[WeeklyEvidenceCard]]:
    out: dict[str, list[WeeklyEvidenceCard]] = {}
    for card in cards:
        out.setdefault(card.recommendation_id, []).append(card)
    return out


def _group_firings_by_plan(
    firings: list[WeeklyXRuleFiring],
) -> dict[str, list[WeeklyXRuleFiring]]:
    out: dict[str, list[WeeklyXRuleFiring]] = {}
    for f in firings:
        out.setdefault(f.daily_plan_id, []).append(f)
    return out


def _format_date(iso_date: str) -> str:
    """Format a YYYY-MM-DD civil date as 'Month Day' for prose."""
    from datetime import date as _date
    try:
        d = _date.fromisoformat(iso_date)
    except ValueError:
        return iso_date
    return d.strftime("%B %-d") if hasattr(d, "strftime") else iso_date


def _format_date_list(iso_dates: list[str]) -> str:
    """Format a list of ISO dates as a human-readable comma-separated
    list with an Oxford 'and' before the last entry. Used in
    quantitative atoms that cite multiple days.
    """
    if not iso_dates:
        return "(no dates)"
    formatted = [_format_date(d) for d in iso_dates]
    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) == 2:
        return f"{formatted[0]} and {formatted[1]}"
    return ", ".join(formatted[:-1]) + f", and {formatted[-1]}"


def _format_locator_lead_in(
    locators: list[dict],
    domain: str,
) -> str:
    """F-EXPLAIN-07 locator-cited prose lead-in.

    When locators exist, names at least one pk-field (typically a
    date) before the claim. Returns empty string when no locators
    present (no false citation).
    """

    if not locators:
        return ""
    dates = sorted({
        loc.get("pk", {}).get("as_of_date")
        for loc in locators
        if isinstance(loc, dict)
        and isinstance(loc.get("pk"), dict)
        and loc.get("pk", {}).get("as_of_date")
    })
    if not dates:
        return ""
    metric_phrase = _domain_metric_phrase(domain)
    return (
        f"Looking at {metric_phrase} on {_format_date_list(list(dates))}: "
    )


def _domain_metric_phrase(domain: str) -> str:
    """Return a domain-flavored metric phrase for the locator lead-in.
    Plain-English; avoids any raw column-name leakage.
    """

    return {
        "recovery": "your resting-heart-rate evidence",
        "running": "your running-load evidence",
        "sleep": "your sleep evidence",
        "stress": "your stress evidence",
        "strength": "your resistance-training evidence",
        "nutrition": "your nutrition evidence",
    }.get(domain, "your domain evidence")


def _humanise_action(action: str) -> str:
    """Turn a snake_case action token into a human-readable phrase."""

    return action.replace("_", " ").strip() or "(no action recorded)"


def _summarise_rationale(rationale: list) -> str:
    """Translate any reason_token in the rationale through the caveat
    registry and join into a comma-separated 'because' clause.
    Returns an empty string when no rationale is present (so the
    atom_text reads naturally either way).
    """

    if not rationale:
        return ""
    pieces: list[str] = []
    for entry in rationale:
        if isinstance(entry, dict):
            token = entry.get("reason_token") or entry.get("token")
            if token:
                pieces.append(translate_caveat(token))
                continue
            text = entry.get("text") or entry.get("note")
            if text:
                pieces.append(str(text))
        elif isinstance(entry, str):
            # Bare strings may be plain English already OR a caveat
            # token. Be conservative: route any underscore-shaped
            # string through translate_caveat (which falls back
            # gracefully on plain English).
            if "_" in entry and " " not in entry:
                pieces.append(translate_caveat(entry))
            else:
                pieces.append(entry)
    if not pieces:
        return ""
    joined = "; ".join(pieces)
    return f", because {joined}"


def _phase_a_b_framing(
    firings: list[WeeklyXRuleFiring],
) -> str:
    """Translate Phase A / Phase B firings into plain English (F-EXPLAIN-02).

    Phase A tiers (soften / block / cap_confidence / restructure)
    shape the recommendation BEFORE the skill renders. Phase B tier
    (`adjust`) adjusts the result AFTER. The prose surfaces the
    distinction inline; the raw `phase_a` / `phase_b` keys never
    appear in atom text.

    Rule IDs surface only in parentheses (F-EXPLAIN-01). The
    `public_name_for` helper provides the leading subject; the
    rule_id is the audit citation.
    """

    phase_a = [f for f in firings if f.tier in
               {"soften", "block", "cap_confidence", "restructure"}]
    phase_b = [f for f in firings if f.tier == "adjust"]

    parts: list[str] = []
    if phase_a:
        names = [_rule_phrase(f.x_rule_id) for f in phase_a]
        parts.append(
            "Rules that shaped the recommendation: "
            + "; ".join(names) + "."
        )
    if phase_b:
        names = [_rule_phrase(f.x_rule_id) for f in phase_b]
        parts.append(
            "Rules that adjusted the result after the skill ran: "
            + "; ".join(names) + "."
        )
    return " ".join(parts) if parts else (
        "No rules fired against this recommendation."
    )


def emit_weekly_claim_cards(
    conn: sqlite3.Connection,
    bundle: WeeklyProseBundle,
    *,
    computed_at: Optional[str] = None,
    commit_after: bool = True,
) -> int:
    """Persist a ``weekly_claim_card`` row for every quantitative +
    comparative atom in the bundle's sections.

    Per PLAN §2.D acceptance #6: the count of cards equals the count
    of (quantitative + comparative) atoms in non-abstain prose.
    Qualitative atoms emit NO card per F-PLAN-10 (they carry no
    factual past-week content; W58D has no claim to gate).

    Per W-EVCARD-WEEKLY's append-only contract: every call appends new
    rows with fresh ``card_id`` (UUID-suffixed) and fresh
    ``computed_at``; consumers dedup at the canonical-latest view.

    On the abstain branch (``coverage.weekly_status ==
    'insufficient_data'``) returns 0 — no cards are written
    (validation is structurally simpler via deterministic substitution
    from coverage; see step 2 PLAN §2.D round-1 correction).

    Returns the count of cards persisted.
    """

    if bundle.coverage.weekly_status == "insufficient_data":
        return 0

    written = 0
    for section in bundle.sections:
        for atom in section.atoms:
            if atom.atom_type not in _CARD_EMITTING_ATOM_TYPES:
                continue
            project_weekly_card(
                conn,
                user_id=bundle.user_id,
                iso_week=bundle.iso_week,
                claim_atom_text=atom.atom_text,
                atom_type=atom.atom_type,
                derivation_path=atom.derivation_path,
                locator_set=list(atom.locator_set),
                audit_refs=dict(atom.audit_refs),
                computed_at=computed_at,
                commit_after=False,
            )
            written += 1

    if commit_after:
        conn.commit()
    return written


def assert_qualitative_atom_is_non_factual(atom: WeeklyAtom) -> None:
    """F-PLAN-10 mechanical assertion (round-1 addition).

    Qualitative atoms must contain NO factual past-week content —
    no numeric tokens, no date tokens (month names), no comparison
    operators / ratio language. The structural argument: qualitative
    atoms exist for framing and disposition, not for past-week
    claims; if a "qualitative" atom carries a date or a number, it's
    actually a quantitative claim mis-tagged and W58D would miss it.

    Raises :class:`AssertionError` when the atom violates the
    invariant. Used by the test suite as a mechanical
    closed-set check at prose-builder output time.
    """

    if atom.atom_type != "qualitative":
        return
    text = atom.atom_text
    numeric_match = _NUMERIC_RE.search(text)
    assert numeric_match is None, (
        f"qualitative atom {atom.atom_id!r} contains numeric token "
        f"{numeric_match.group()!r} — re-tag as quantitative or "
        f"strip the factual content. atom_text={text!r}"
    )
    date_match = _DATE_MONTH_RE.search(text)
    assert date_match is None, (
        f"qualitative atom {atom.atom_id!r} contains date token "
        f"{date_match.group()!r} — re-tag as quantitative or strip "
        f"the factual content. atom_text={text!r}"
    )
    lower = text.lower()
    for token in _COMPARISON_TOKENS:
        assert token not in lower, (
            f"qualitative atom {atom.atom_id!r} contains comparison "
            f"token {token!r} — re-tag as comparative or strip the "
            f"factual content. atom_text={text!r}"
        )


def _rule_phrase(rule_id: str) -> str:
    """Return ``"<public name> (X<N>)"`` (F-EXPLAIN-01: rule_id only
    in parentheses, public_name as the leading subject).
    """

    public_name = public_name_for(rule_id) or rule_id
    if public_name == rule_id:
        # No public_name configured: surface the rule_id only as a
        # last resort, in parentheses (still no leading X<N>).
        return f"(rule {rule_id})"
    return f"{public_name} ({rule_id})"
