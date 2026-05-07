"""One-shot generator for the W-FACT-ATOM 30-fixture corpus
(v0.2.0 §2.E).

Constructs synthetic ``WeeklyAggregation`` / ``WeeklyCoverage`` /
``WeeklyDataQualityRollup`` instances for diverse fixture shapes,
runs ``build_weekly_prose`` + ``render_markdown`` over each, and
emits one fixture JSON per case plus an ``index.json`` manifest.

The "manually-annotated ground truth" for each fixture is W52's
own emission tagging (``atom_type`` + ``derivation_path``), which is
the legitimate target the parser is measured against. The
"manual" aspect of the corpus is the deliberate choice of fixture
shapes — diverse coverage across full renders, abstain branches,
deferred-domain disposition, firings, data-quality variety, cadence
variety, and edge cases.

Re-run after any W52 prose-emission change to regenerate the
corpus; commit the regenerated artifacts.

Run::

    uv run python -m health_agent_infra.evals.scenarios.atomic_claims._build_corpus
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path
from collections.abc import Sequence
from typing import Any, Optional

from health_agent_infra.core.review.prose_builder import (
    WeeklyAtom,
    WeeklyProseBundle,
    WeeklyProseSection,
    build_weekly_prose,
)
from health_agent_infra.core.review.render import render_markdown
from health_agent_infra.core.review.weekly import (
    CanonicalPlanRow,
    DataQualityClassification,
    WeeklyAcceptedStateRow,
    WeeklyAggregation,
    WeeklyCoverage,
    WeeklyDataQualityRollup,
    WeeklyDataQualityRow,
    WeeklyEvidenceCard,
    WeeklyIntentRow,
    WeeklyRecommendation,
    WeeklyReviewOutcome,
    WeeklyRuntimeEventRow,
    WeeklySyncRunRow,
    WeeklyTargetRow,
    WeeklyXRuleFiring,
)


CORPUS_DIR = Path(__file__).parent
ISO_WEEK = "2026-W18"
USER_ID = "u_corpus"
WEEK_DATES = [
    "2026-04-27", "2026-04-28", "2026-04-29",
    "2026-04-30", "2026-05-01", "2026-05-02", "2026-05-03",
]


# ---------------------------------------------------------------------------
# Connection helper — empty in-memory DB or in-memory DB with primary_goal
# ---------------------------------------------------------------------------


def _make_conn(primary_goal: Optional[str] = None) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    if primary_goal is not None:
        conn.execute(
            "CREATE TABLE user_memory ("
            "  user_id TEXT NOT NULL,"
            "  key TEXT NOT NULL,"
            "  value TEXT,"
            "  archived_at TEXT,"
            "  created_at TEXT NOT NULL"
            ")"
        )
        conn.execute(
            "INSERT INTO user_memory (user_id, key, value, archived_at, "
            "created_at) VALUES (?, 'primary_goal', ?, NULL, ?)",
            (USER_ID, primary_goal, "2026-04-20T08:00:00Z"),
        )
        conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Fixture builders — synthetic aggregation rows
# ---------------------------------------------------------------------------


def _plan(date: str) -> CanonicalPlanRow:
    return CanonicalPlanRow(
        daily_plan_id=f"plan_{date}",
        user_id=USER_ID,
        for_date=date,
        synthesized_at=f"{date}T07:00:00Z",
        recommendation_ids=[],
        proposal_ids=[],
        x_rules_fired=[],
        synthesis_meta=None,
        superseded_by_plan_id=None,
        superseded_at=None,
    )


def _rec(
    date: str,
    domain: str,
    *,
    action: str = "easy_recovery",
    confidence: str = "high",
    locators: Optional[list[dict]] = None,
) -> WeeklyRecommendation:
    return WeeklyRecommendation(
        recommendation_id=f"rec_{date}_{domain}",
        daily_plan_id=f"plan_{date}",
        user_id=USER_ID,
        for_date=date,
        domain=domain,
        action=action,
        confidence=confidence,
        bounded=True,
        issued_at=f"{date}T07:05:00Z",
        payload={"action": action, "domain": domain},
        evidence_locators=list(locators or []),
    )


def _firing(
    date: str,
    *,
    rule_id: str = "X1",
    tier: str = "soften",
    domain: str = "recovery",
    firing_id: int = 1,
) -> WeeklyXRuleFiring:
    return WeeklyXRuleFiring(
        firing_id=firing_id,
        daily_plan_id=f"plan_{date}",
        user_id=USER_ID,
        x_rule_id=rule_id,
        tier=tier,
        affected_domain=domain,
        trigger_note="synthetic fixture firing",
        mutation=None,
        source_signals={},
        fired_at=f"{date}T07:00:30Z",
    )


def _sync_run(
    date: str,
    *,
    sync_id: int = 1,
    mode: str = "live",
    started_at: Optional[str] = None,
    for_date: Optional[str] = None,
    status: str = "ok",
    source: str = "intervals_icu",
) -> WeeklySyncRunRow:
    return WeeklySyncRunRow(
        sync_id=sync_id,
        source=source,
        user_id=USER_ID,
        mode=mode,
        started_at=started_at or f"{date}T07:00:00Z",
        completed_at=(started_at or f"{date}T07:00:00Z").replace("00Z", "30Z"),
        status=status,
        for_date=for_date or date,
    )


def _runtime_event(
    date: str,
    *,
    command: str = "hai daily",
    event_id: int = 1,
) -> WeeklyRuntimeEventRow:
    return WeeklyRuntimeEventRow(
        event_id=event_id,
        command=command,
        user_id=USER_ID,
        started_at=f"{date}T07:00:00Z",
        completed_at=f"{date}T07:00:30Z",
        status="ok",
        exit_code=0,
    )


def _aggregation(
    *,
    canonical_plans: list[CanonicalPlanRow],
    recommendations: list[WeeklyRecommendation],
    firings: Sequence[WeeklyXRuleFiring] = (),
    sync_runs: Sequence[WeeklySyncRunRow] = (),
    runtime_events: Sequence[WeeklyRuntimeEventRow] = (),
) -> WeeklyAggregation:
    return WeeklyAggregation(
        iso_week=ISO_WEEK,
        user_id=USER_ID,
        week_dates=list(WEEK_DATES),
        canonical_plans=canonical_plans,
        recommendations=recommendations,
        x_rule_firings=list(firings),
        review_outcomes=[],
        evidence_cards=[],
        accepted_state_rows=[],
        data_quality_rows=[],
        sync_runs=list(sync_runs),
        runtime_events=list(runtime_events),
        intent_rows=[],
        target_rows=[],
    )


def _data_quality_rollup(
    *,
    fresh: int = 0,
    stale_pull: int = 0,
    retrospective: int = 0,
    unclassifiable: int = 0,
    threshold_hours: int = 48,
) -> WeeklyDataQualityRollup:
    per_sync = []
    sync_id = 0
    for _ in range(fresh):
        sync_id += 1
        per_sync.append(DataQualityClassification(
            sync_id=sync_id, source="intervals_icu", mode="live",
            started_at="2026-04-27T07:00:00Z", for_date="2026-04-27",
            gap_hours=0.5, classification="fresh",
        ))
    for _ in range(stale_pull):
        sync_id += 1
        per_sync.append(DataQualityClassification(
            sync_id=sync_id, source="intervals_icu", mode="live",
            started_at="2026-04-29T07:00:00Z", for_date="2026-04-25",
            gap_hours=72.0, classification="stale_pull",
        ))
    for _ in range(retrospective):
        sync_id += 1
        per_sync.append(DataQualityClassification(
            sync_id=sync_id, source="manual", mode="manual",
            started_at="2026-05-02T08:00:00Z", for_date="2026-04-28",
            gap_hours=96.0, classification="retrospective_manual",
        ))
    for _ in range(unclassifiable):
        sync_id += 1
        per_sync.append(DataQualityClassification(
            sync_id=sync_id, source="unknown", mode="other",
            started_at="2026-04-30T09:00:00Z", for_date=None,
            gap_hours=None, classification="unclassifiable",
        ))
    return WeeklyDataQualityRollup(
        threshold_hours=threshold_hours,
        per_sync=per_sync,
        fresh_count=fresh,
        stale_pull_count=stale_pull,
        retrospective_manual_count=retrospective,
        unclassifiable_count=unclassifiable,
    )


def _coverage(
    *,
    days_with_plans: int,
    coverage_threshold: int = 5,
    populated_dates: Optional[list[str]] = None,
    missing_dates: Optional[list[str]] = None,
) -> WeeklyCoverage:
    weekly_status = (
        "insufficient_data" if days_with_plans < coverage_threshold
        else "ok"
    )
    return WeeklyCoverage(
        weekly_status=weekly_status,
        iso_week=ISO_WEEK,
        days_with_plans=days_with_plans,
        coverage_threshold=coverage_threshold,
        populated_dates=list(populated_dates or WEEK_DATES[:days_with_plans]),
        missing_dates=list(missing_dates or WEEK_DATES[days_with_plans:]),
    )


# ---------------------------------------------------------------------------
# Fixture cases
# ---------------------------------------------------------------------------


@dataclass
class FixtureCase:
    fixture_id: str
    category: str
    description: str
    primary_goal: Optional[str]
    aggregation: WeeklyAggregation
    coverage: WeeklyCoverage
    rollup: WeeklyDataQualityRollup
    deferred_domains: list[str] = field(default_factory=list)


def _full_week_plans() -> list[CanonicalPlanRow]:
    return [_plan(d) for d in WEEK_DATES[:5]]


def _make_cases() -> list[FixtureCase]:
    cases: list[FixtureCase] = []

    # ---------- A. full_render_minimal (5) ----------
    # ac_001 — one domain (recovery), goal set
    cases.append(FixtureCase(
        fixture_id="ac_001_one_domain_goal_set",
        category="full_render_minimal",
        description=(
            "Full-week render with one domain (recovery), primary goal set, "
            "no firings."
        ),
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[
                _rec(d, "recovery") for d in WEEK_DATES[:3]
            ],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
    ))

    # ac_002 — three domains, goal set
    cases.append(FixtureCase(
        fixture_id="ac_002_three_domains_goal_set",
        category="full_render_minimal",
        description=(
            "Full-week render with recovery + sleep + nutrition, primary "
            "goal set, no firings."
        ),
        primary_goal="strength baseline",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[
                _rec("2026-04-27", "recovery"),
                _rec("2026-04-28", "sleep", action="extend_sleep"),
                _rec("2026-04-29", "nutrition", action="hold_macros"),
            ],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:6])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
    ))

    # ac_003 — six domains, goal set
    cases.append(FixtureCase(
        fixture_id="ac_003_six_domains_goal_set",
        category="full_render_minimal",
        description=(
            "Full-week render with all six domains represented, primary "
            "goal set."
        ),
        primary_goal="exam-hold maintenance",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[
                _rec("2026-04-27", "recovery"),
                _rec("2026-04-27", "running", action="easy_zone_2"),
                _rec("2026-04-28", "sleep", action="extend_sleep"),
                _rec("2026-04-28", "stress", action="reduce_load"),
                _rec("2026-04-29", "strength", action="upper_volume_block"),
                _rec("2026-04-29", "nutrition", action="hold_macros"),
            ],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:7])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
    ))

    # ac_004 — one domain, goal unset (abstain branch in header)
    cases.append(FixtureCase(
        fixture_id="ac_004_one_domain_goal_unset",
        category="full_render_minimal",
        description=(
            "Full-week render with one domain, no primary goal — header "
            "carries goal_abstain disposition atom."
        ),
        primary_goal=None,
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[_rec(d, "recovery") for d in WEEK_DATES[:3]],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
    ))

    # ac_005 — three domains, goal unset
    cases.append(FixtureCase(
        fixture_id="ac_005_three_domains_goal_unset",
        category="full_render_minimal",
        description=(
            "Full-week render with three domains, no primary goal."
        ),
        primary_goal=None,
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[
                _rec("2026-04-27", "recovery"),
                _rec("2026-04-28", "sleep", action="extend_sleep"),
                _rec("2026-04-29", "running", action="easy_zone_2"),
            ],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:6])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
    ))

    # ---------- B. full_render_with_firings (5) ----------
    # ac_006 — Phase A only (soften)
    cases.append(FixtureCase(
        fixture_id="ac_006_phase_a_only_soften",
        category="full_render_with_firings",
        description=(
            "Recovery rec with one Phase A firing (X1, soften tier) — "
            "comparative atom emits."
        ),
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[_rec("2026-04-28", "recovery")],
            firings=[_firing("2026-04-28", rule_id="X1", tier="soften",
                             domain="recovery", firing_id=101)],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
    ))

    # ac_007 — Phase B only (adjust)
    cases.append(FixtureCase(
        fixture_id="ac_007_phase_b_only_adjust",
        category="full_render_with_firings",
        description=(
            "Recovery rec with one Phase B firing (X3, adjust tier)."
        ),
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[_rec("2026-04-28", "recovery")],
            firings=[_firing("2026-04-28", rule_id="X3", tier="adjust",
                             domain="recovery", firing_id=102)],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:4])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
    ))

    # ac_008 — Phase A + Phase B firings on same plan
    cases.append(FixtureCase(
        fixture_id="ac_008_phase_a_and_b",
        category="full_render_with_firings",
        description=(
            "Recovery rec with both Phase A (block) and Phase B (adjust) "
            "firings on the same plan."
        ),
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[_rec("2026-04-28", "recovery")],
            firings=[
                _firing("2026-04-28", rule_id="X2", tier="block",
                        domain="recovery", firing_id=103),
                _firing("2026-04-28", rule_id="X4", tier="adjust",
                        domain="recovery", firing_id=104),
            ],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:6])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
    ))

    # ac_009 — multiple Phase A firings
    cases.append(FixtureCase(
        fixture_id="ac_009_multiple_phase_a",
        category="full_render_with_firings",
        description=(
            "Two Phase A firings (cap_confidence + restructure) on the "
            "same plan."
        ),
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[_rec("2026-04-28", "running", action="easy_zone_2")],
            firings=[
                _firing("2026-04-28", rule_id="X5", tier="cap_confidence",
                        domain="running", firing_id=105),
                _firing("2026-04-28", rule_id="X6", tier="restructure",
                        domain="running", firing_id=106),
            ],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
    ))

    # ac_010 — firings across multiple recs
    cases.append(FixtureCase(
        fixture_id="ac_010_firings_across_recs",
        category="full_render_with_firings",
        description=(
            "Firings on two different recommendations within one week."
        ),
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[
                _rec("2026-04-27", "recovery"),
                _rec("2026-04-29", "sleep", action="extend_sleep"),
            ],
            firings=[
                _firing("2026-04-27", rule_id="X1", tier="soften",
                        domain="recovery", firing_id=107),
                _firing("2026-04-29", rule_id="X7", tier="adjust",
                        domain="sleep", firing_id=108),
            ],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
    ))

    # ---------- C. deferred_domain (5) ----------
    # ac_011 — one deferred (running)
    cases.append(FixtureCase(
        fixture_id="ac_011_one_deferred_running",
        category="deferred_domain",
        description=(
            "Running domain deferred; recovery still surfaces normally."
        ),
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[
                _rec("2026-04-27", "recovery"),
                _rec("2026-04-28", "running", action="easy_zone_2"),
            ],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
        deferred_domains=["running"],
    ))

    # ac_012 — two deferred (running + nutrition)
    cases.append(FixtureCase(
        fixture_id="ac_012_two_deferred",
        category="deferred_domain",
        description=(
            "Running + nutrition deferred; recovery still surfaces."
        ),
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[
                _rec("2026-04-27", "recovery"),
                _rec("2026-04-28", "running", action="easy_zone_2"),
                _rec("2026-04-29", "nutrition", action="hold_macros"),
            ],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
        deferred_domains=["running", "nutrition"],
    ))

    # ac_013 — three deferred
    cases.append(FixtureCase(
        fixture_id="ac_013_three_deferred",
        category="deferred_domain",
        description=(
            "Three domains deferred (running + sleep + nutrition); "
            "recovery and stress surface normally."
        ),
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[
                _rec("2026-04-27", "recovery"),
                _rec("2026-04-28", "stress", action="reduce_load"),
                _rec("2026-04-29", "running", action="easy_zone_2"),
                _rec("2026-04-30", "sleep", action="extend_sleep"),
                _rec("2026-05-01", "nutrition", action="hold_macros"),
            ],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
        deferred_domains=["running", "sleep", "nutrition"],
    ))

    # ac_014 — all six deferred (degenerate but valid)
    cases.append(FixtureCase(
        fixture_id="ac_014_all_six_deferred",
        category="deferred_domain",
        description=(
            "All six domains deferred — every domain section is "
            "qualitative-only."
        ),
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[
                _rec("2026-04-27", "recovery"),
                _rec("2026-04-28", "sleep", action="extend_sleep"),
                _rec("2026-04-29", "stress", action="reduce_load"),
                _rec("2026-04-30", "strength", action="upper_volume_block"),
                _rec("2026-05-01", "nutrition", action="hold_macros"),
                _rec("2026-05-02", "running", action="easy_zone_2"),
            ],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
        deferred_domains=["recovery", "running", "sleep", "stress",
                          "strength", "nutrition"],
    ))

    # ac_015 — deferred + goal unset
    cases.append(FixtureCase(
        fixture_id="ac_015_deferred_with_goal_unset",
        category="deferred_domain",
        description=(
            "One deferred domain + no primary goal — header carries "
            "goal_abstain AND deferred section emits."
        ),
        primary_goal=None,
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[
                _rec("2026-04-27", "recovery"),
                _rec("2026-04-28", "running", action="easy_zone_2"),
            ],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
        deferred_domains=["running"],
    ))

    # ---------- D. abstain_branch (3) ----------
    # ac_016 — abstain with 0 days
    cases.append(FixtureCase(
        fixture_id="ac_016_abstain_zero_days",
        category="abstain_branch",
        description=(
            "Insufficient data — 0 of 7 days have plans (abstain branch)."
        ),
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=[],
            recommendations=[],
            sync_runs=[],
            runtime_events=[],
        ),
        coverage=_coverage(
            days_with_plans=0,
            populated_dates=[],
            missing_dates=list(WEEK_DATES),
        ),
        rollup=_data_quality_rollup(),
    ))

    # ac_017 — abstain with 3 days
    cases.append(FixtureCase(
        fixture_id="ac_017_abstain_three_days",
        category="abstain_branch",
        description=(
            "Insufficient data — 3 of 7 days have plans (under threshold "
            "of 5)."
        ),
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=[_plan(d) for d in WEEK_DATES[:3]],
            recommendations=[_rec(d, "recovery") for d in WEEK_DATES[:3]],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:3])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:3])],
        ),
        coverage=_coverage(
            days_with_plans=3,
            populated_dates=list(WEEK_DATES[:3]),
            missing_dates=list(WEEK_DATES[3:]),
        ),
        rollup=_data_quality_rollup(fresh=3),
    ))

    # ac_018 — abstain even with goal set
    cases.append(FixtureCase(
        fixture_id="ac_018_abstain_with_goal_set",
        category="abstain_branch",
        description=(
            "Insufficient data even though primary goal set; goal does "
            "not change abstain disposition."
        ),
        primary_goal="exam-hold maintenance",
        aggregation=_aggregation(
            canonical_plans=[_plan(d) for d in WEEK_DATES[:2]],
            recommendations=[_rec(d, "sleep", action="extend_sleep") for d in WEEK_DATES[:2]],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:2])],
            runtime_events=[],
        ),
        coverage=_coverage(
            days_with_plans=2,
            populated_dates=list(WEEK_DATES[:2]),
            missing_dates=list(WEEK_DATES[2:]),
        ),
        rollup=_data_quality_rollup(fresh=2),
    ))

    # ---------- E. data_quality_variety (4) ----------
    # ac_019 — all fresh
    cases.append(FixtureCase(
        fixture_id="ac_019_dq_all_fresh",
        category="data_quality_variety",
        description="All sync runs classified fresh.",
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[_rec("2026-04-27", "recovery")],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:7])],
            runtime_events=[_runtime_event("2026-04-27")],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=7),
    ))

    # ac_020 — mixed modes
    cases.append(FixtureCase(
        fixture_id="ac_020_dq_mixed_modes",
        category="data_quality_variety",
        description="Mixed sync run modes — fresh + stale_pull + retrospective.",
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[_rec("2026-04-27", "recovery")],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event("2026-04-27")],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=3, stale_pull=1, retrospective=1),
    ))

    # ac_021 — all unclassifiable
    cases.append(FixtureCase(
        fixture_id="ac_021_dq_all_unclassifiable",
        category="data_quality_variety",
        description="All sync runs are unclassifiable.",
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[_rec("2026-04-27", "recovery")],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:3])],
            runtime_events=[_runtime_event("2026-04-27")],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(unclassifiable=3),
    ))

    # ac_022 — high stale_pull
    cases.append(FixtureCase(
        fixture_id="ac_022_dq_high_stale_pull",
        category="data_quality_variety",
        description="Mostly stale_pull — vendor pulled aged data all week.",
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[_rec("2026-04-27", "recovery")],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:6])],
            runtime_events=[_runtime_event("2026-04-27")],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=1, stale_pull=5),
    ))

    # ---------- F. cadence_variety (3) ----------
    # ac_023 — zero hai daily runs
    cases.append(FixtureCase(
        fixture_id="ac_023_cadence_zero_runs",
        category="cadence_variety",
        description="User ran hai daily 0 times this week.",
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[_rec("2026-04-27", "recovery")],
            sync_runs=[_sync_run("2026-04-27")],
            runtime_events=[],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=1),
    ))

    # ac_024 — full 7 days hai daily
    cases.append(FixtureCase(
        fixture_id="ac_024_cadence_seven_runs",
        category="cadence_variety",
        description="User ran hai daily on all 7 days.",
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[_rec("2026-04-27", "recovery")],
            sync_runs=[_sync_run("2026-04-27")],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES)],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=1),
    ))

    # ac_025 — partial 3 hai daily runs
    cases.append(FixtureCase(
        fixture_id="ac_025_cadence_three_runs",
        category="cadence_variety",
        description="User ran hai daily on 3 of 7 days.",
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[_rec("2026-04-27", "recovery")],
            sync_runs=[_sync_run("2026-04-27")],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:3])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=1),
    ))

    # ---------- G. edge_cases (5) ----------
    # ac_026 — long primary goal
    cases.append(FixtureCase(
        fixture_id="ac_026_long_primary_goal",
        category="edge_cases",
        description=(
            "Multi-clause primary goal — exercises long header atom text."
        ),
        primary_goal=(
            "maintain training volume during exam-hold then lean cut"
        ),
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[_rec("2026-04-27", "recovery")],
            sync_runs=[_sync_run("2026-04-27")],
            runtime_events=[_runtime_event("2026-04-27")],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=1),
    ))

    # ac_027 — special characters in action
    cases.append(FixtureCase(
        fixture_id="ac_027_special_chars_action",
        category="edge_cases",
        description=(
            "Action with snake_case + numerals — exercises action humanise "
            "path."
        ),
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[
                _rec("2026-04-27", "running", action="zone_2_easy_30min"),
            ],
            sync_runs=[_sync_run("2026-04-27")],
            runtime_events=[_runtime_event("2026-04-27")],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=1),
    ))

    # ac_028 — minimal recs (single-rec week)
    cases.append(FixtureCase(
        fixture_id="ac_028_single_rec_week",
        category="edge_cases",
        description="Only one recommendation in the entire week.",
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[_rec("2026-04-27", "recovery")],
            sync_runs=[_sync_run("2026-04-27")],
            runtime_events=[_runtime_event("2026-04-27")],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=1),
    ))

    # ac_029 — high atom density (many recs + firings)
    cases.append(FixtureCase(
        fixture_id="ac_029_high_atom_density",
        category="edge_cases",
        description=(
            "Multiple recs across multiple domains with multiple firings."
        ),
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[
                _rec("2026-04-27", "recovery"),
                _rec("2026-04-27", "sleep", action="extend_sleep"),
                _rec("2026-04-28", "running", action="easy_zone_2"),
                _rec("2026-04-29", "nutrition", action="hold_macros"),
                _rec("2026-05-01", "stress", action="reduce_load"),
            ],
            firings=[
                _firing("2026-04-27", rule_id="X1", tier="soften",
                        domain="recovery", firing_id=110),
                _firing("2026-04-28", rule_id="X2", tier="adjust",
                        domain="running", firing_id=111),
                _firing("2026-04-29", rule_id="X3", tier="cap_confidence",
                        domain="nutrition", firing_id=112),
            ],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=4, stale_pull=1),
    ))

    # ac_030 — rec with locator — exercises locator-cited lead-in
    cases.append(FixtureCase(
        fixture_id="ac_030_rec_with_locator_lead_in",
        category="edge_cases",
        description=(
            "Recovery rec carrying an evidence_locator with as_of_date — "
            "exercises F-EXPLAIN-07 locator-cited prose lead-in."
        ),
        primary_goal="lean cut",
        aggregation=_aggregation(
            canonical_plans=_full_week_plans(),
            recommendations=[
                _rec(
                    "2026-04-28", "recovery",
                    locators=[{
                        "table": "accepted_recovery_state_daily",
                        "row_version": "2026-04-28T19:00Z",
                        "pk": {
                            "user_id": USER_ID,
                            "as_of_date": "2026-04-28",
                        },
                        "column": "resting_hr",
                    }],
                ),
            ],
            sync_runs=[_sync_run(d, sync_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
            runtime_events=[_runtime_event(d, event_id=i + 1) for i, d in enumerate(WEEK_DATES[:5])],
        ),
        coverage=_coverage(days_with_plans=5),
        rollup=_data_quality_rollup(fresh=5),
    ))

    return cases


# ---------------------------------------------------------------------------
# Atom serialization
# ---------------------------------------------------------------------------


def _section_atom_to_dict(
    section_id: str, atom: WeeklyAtom,
) -> dict[str, Any]:
    return {
        "atom_text": atom.atom_text,
        "atom_type": atom.atom_type,
        "derivation_path": atom.derivation_path,
        "section_id": section_id,
    }


def _bundle_to_expected_atoms(
    bundle: WeeklyProseBundle,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for section in bundle.sections:
        for atom in section.atoms:
            out.append(_section_atom_to_dict(section.section_id, atom))
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def build_corpus(
    out_dir: Path = CORPUS_DIR,
) -> dict[str, Any]:
    """Build the corpus and write all fixture files.

    Returns a manifest dict matching ``index.json``'s schema.
    """

    fixtures_meta: list[dict[str, Any]] = []
    by_category: dict[str, list[str]] = {}

    cases = _make_cases()
    for case in cases:
        conn = _make_conn(primary_goal=case.primary_goal)
        try:
            bundle = build_weekly_prose(
                conn, case.aggregation, case.coverage, case.rollup,
                deferred_domains=case.deferred_domains,
            )
            markdown = render_markdown(bundle)
            expected_atoms = _bundle_to_expected_atoms(bundle)
        finally:
            conn.close()

        fixture_payload = {
            "schema_version": "atomic_claims_fixture.v1",
            "fixture_id": case.fixture_id,
            "category": case.category,
            "description": case.description,
            "input": {
                "markdown": markdown,
            },
            "expected": {
                "atoms": expected_atoms,
                "atom_count": len(expected_atoms),
            },
        }
        fixture_path = out_dir / f"{case.fixture_id}.json"
        fixture_path.write_text(
            json.dumps(fixture_payload, indent=2, sort_keys=True) + "\n",
        )
        fixtures_meta.append({
            "fixture_id": case.fixture_id,
            "category": case.category,
            "atom_count": len(expected_atoms),
        })
        by_category.setdefault(case.category, []).append(case.fixture_id)

    manifest = {
        "schema_version": "atomic_claims_index.v1",
        "description": (
            "30-fixture corpus for W-FACT-ATOM parser precision validation "
            "(PLAN §2.E acceptance #1). Each fixture pairs a W52-rendered "
            "markdown surface with its ground-truth atom triples "
            "(atom_text, atom_type, derivation_path, section_id). The "
            "ground truth is W52's own emission tagging — the legitimate "
            "target the parser is measured against."
        ),
        "total_fixtures": len(fixtures_meta),
        "categories": {
            cat: sorted(ids) for cat, ids in by_category.items()
        },
        "fixtures": sorted(
            fixtures_meta, key=lambda f: f["fixture_id"],
        ),
    }
    (out_dir / "index.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    )
    return manifest


def main() -> int:
    manifest = build_corpus()
    print(f"wrote {manifest['total_fixtures']} fixtures + index.json")
    print(f"categories: {sorted(manifest['categories'].keys())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
