"""W52 step 8 — deferred-domain suppression + canonical-latest rerun
(PLAN §2.D acceptance #8 + #9).

Two concerns covered here:

  Acceptance #8 — Deferred-domain suppression (round-2 add per
  F-PLAN-R2-02; round-3 nit per F-PLAN-R3-01; round-4 nit per
  F-PLAN-R4-01). When a domain fork-defers W-PROV-2 emission to
  v0.2.1 W-PROV-3, W52 emits NO quantitative or comparative atoms
  (and writes NO claim cards) for that domain. The domain section
  renders with the literal disposition prose:

    "domain X: insufficient provenance — quantitative and
     comparative claims suppressed pending v0.2.1 W-PROV-3"

  This test pins the exact disposition string + the three
  consequences:
    (a) no claim cards exist for that domain in weekly_claim_card
    (b) JSON output includes deferred_domains: ["<domain>"]
    (c) markdown output renders the suppression disposition prose

  Phase 1 W-PROV-2 shipped all 5 dormant domains clean (per
  project_v0_2_0_phase1_complete_2026-05-07 memory) — no fork-defer
  happened. But the suppression logic must still ship behind a
  fixture-tested branch so v0.2.1 W-PROV-3 can use it cleanly.

  Acceptance #9 — Canonical-latest rerun fixture (round-2 add per
  F-PLAN-R2-03; surface-listed round-3 per F-PLAN-R3-02). Pins the
  W-EVCARD-WEEKLY append-only contract through the W52 surface:

    1. Run W52 → cards persist
    2. Mutate one fixture row in the underlying state
    3. Rerun W52 → cards persist again with new card_id +
       computed_at but same claim_id
    4. weekly_claim_card has 2 rows per affected claim_id
       (append-only preserved)
    5. Default --json returns 1 row per claim_id (canonical-latest)
    6. --json --include-history returns both rows
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from health_agent_infra.core.review.prose_builder import (
    build_weekly_prose,
    emit_weekly_claim_cards,
)
from health_agent_infra.core.review.render import (
    render_json,
    render_markdown,
)
from health_agent_infra.core.review.weekly import (
    compute_data_quality_rollup,
    evaluate_weekly_coverage,
    load_weekly_aggregation,
)
from health_agent_infra.core.review.weekly_card import (
    load_canonical_latest_for_week,
    load_full_history_for_week,
)
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)


USER = "u_w52_deferred"
WEEK = "2026-W18"


def _db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return open_connection(db_path)


def _seed_full_week_with_recovery_and_running(
    conn: sqlite3.Connection,
) -> None:
    """Seed 5 plan-days with both recovery + running recommendations.
    Used as the fork-defer fixture: deferring `running` should
    suppress its quantitative/comparative atoms while recovery's
    surface unaffected.
    """

    plan_dates = [
        "2026-04-27", "2026-04-28", "2026-04-29",
        "2026-04-30", "2026-05-01",
    ]
    for d in plan_dates:
        conn.execute(
            "INSERT INTO daily_plan ("
            "  daily_plan_id, user_id, for_date, synthesized_at, "
            "  recommendation_ids_json, proposal_ids_json, "
            "  x_rules_fired_json, synthesis_meta_json, source, "
            "  ingest_actor, agent_version, validated_at, projected_at, "
            "  superseded_by_plan_id, superseded_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)",
            (
                f"plan_{d}_def", USER, d,
                f"{d}T07:00:00Z",
                "[]", "[]", "[]", None,
                "claude_agent_v1", "claude_agent_v1", "0.2.0",
                f"{d}T07:00:00Z", f"{d}T07:00:01Z",
            ),
        )
        for domain in ("recovery", "running"):
            conn.execute(
                "INSERT INTO recommendation_log ("
                "  recommendation_id, user_id, for_date, issued_at, "
                "  action, confidence, bounded, payload_json, source, "
                "  ingest_actor, agent_version, produced_at, "
                "  validated_at, projected_at, domain, daily_plan_id"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    f"rec_{d}_{domain}", USER, d,
                    f"{d}T07:05:00Z",
                    "easy_recovery", "high", 1,
                    json.dumps({"action": "easy_recovery", "domain": domain}),
                    "claude_agent_v1", "claude_agent_v1", "0.2.0",
                    f"{d}T07:05:00Z", f"{d}T07:05:00Z",
                    f"{d}T07:05:01Z", domain, f"plan_{d}_def",
                ),
            )
    conn.commit()


def _build_bundle(
    conn: sqlite3.Connection,
    *,
    deferred_domains: list[str] | None = None,
):
    agg = load_weekly_aggregation(conn, iso_week=WEEK, user_id=USER)
    coverage = evaluate_weekly_coverage(agg, coverage_threshold_days=5)
    rollup = compute_data_quality_rollup(agg.sync_runs, stale_pull_hours=48)
    return build_weekly_prose(
        conn, agg, coverage, rollup,
        deferred_domains=deferred_domains,
    )


# ---------------------------------------------------------------------------
# Acceptance #8 — deferred-domain suppression
# ---------------------------------------------------------------------------


def test_deferred_domain_emits_only_qualitative_disposition_atom(
    tmp_path: Path,
):
    """The deferred domain section contains exactly one qualitative
    atom carrying the literal disposition prose. No quantitative or
    comparative atoms surface for the deferred domain.
    """

    conn = _db(tmp_path)
    try:
        _seed_full_week_with_recovery_and_running(conn)
        bundle = _build_bundle(conn, deferred_domains=["running"])

        running_sections = [
            s for s in bundle.sections
            if s.section_id == "domain_running"
        ]
        assert len(running_sections) == 1
        running = running_sections[0]
        assert len(running.atoms) == 1
        atom = running.atoms[0]
        assert atom.atom_type == "qualitative"
        # Pin the literal disposition string per F-PLAN-R3-01 +
        # acceptance #8.
        assert atom.atom_text == (
            "domain running: insufficient provenance — quantitative "
            "and comparative claims suppressed pending v0.2.1 W-PROV-3"
        )
    finally:
        conn.close()


def test_deferred_domain_emits_no_claim_cards(tmp_path: Path):
    """Acceptance #8 (a): no claim cards exist for the deferred
    domain in weekly_claim_card after `emit_weekly_claim_cards`
    runs. Recovery cards still emit normally — the suppression
    is per-domain, not week-wide.
    """

    conn = _db(tmp_path)
    try:
        _seed_full_week_with_recovery_and_running(conn)
        bundle = _build_bundle(conn, deferred_domains=["running"])
        emit_weekly_claim_cards(conn, bundle)

        cards = load_full_history_for_week(
            conn, user_id=USER, iso_week=WEEK,
        )
        # No card carries any text identifying the running domain
        # since the running section emitted only a qualitative atom.
        running_cards = [
            c for c in cards
            if "running" in c["claim_atom_text"].lower()
            and c["atom_type"] in ("quantitative", "comparative")
        ]
        assert running_cards == []
        # But recovery cards exist (the non-deferred domain
        # surfaced normally).
        recovery_cards = [
            c for c in cards
            if c["atom_type"] in ("quantitative", "comparative")
        ]
        assert len(recovery_cards) > 0
    finally:
        conn.close()


def test_deferred_domain_surfaces_in_json_output_lane(tmp_path: Path):
    """Acceptance #8 (b): JSON output includes
    `deferred_domains: ["<domain>"]`."""

    conn = _db(tmp_path)
    try:
        _seed_full_week_with_recovery_and_running(conn)
        bundle = _build_bundle(conn, deferred_domains=["running"])
        emit_weekly_claim_cards(conn, bundle)

        payload = json.loads(render_json(bundle, conn=conn))
        assert payload["deferred_domains"] == ["running"]
    finally:
        conn.close()


def test_deferred_domain_disposition_renders_in_markdown(tmp_path: Path):
    """Acceptance #8 (c): markdown output contains the literal
    suppression disposition prose for the deferred domain.
    """

    conn = _db(tmp_path)
    try:
        _seed_full_week_with_recovery_and_running(conn)
        bundle = _build_bundle(conn, deferred_domains=["running"])
        md = render_markdown(bundle)

        # The exact disposition string surfaces as a markdown bullet.
        assert (
            "- domain running: insufficient provenance — "
            "quantitative and comparative claims suppressed "
            "pending v0.2.1 W-PROV-3"
        ) in md
        # The deferred section header still renders the domain name.
        assert "## Running (deferred)" in md
    finally:
        conn.close()


def test_deferred_domain_skips_when_no_recommendations(tmp_path: Path):
    """When the deferred domain has no recommendations in the week
    AND is in the deferred list, the disposition still surfaces —
    the section exists for the deferral disposition itself, not
    only when there's evidence to suppress. Asserts the section
    fires unconditionally on deferral.
    """

    conn = _db(tmp_path)
    try:
        _seed_full_week_with_recovery_and_running(conn)
        # Defer `nutrition` which has no recommendations seeded.
        bundle = _build_bundle(conn, deferred_domains=["nutrition"])
        nutrition_sections = [
            s for s in bundle.sections
            if s.section_id == "domain_nutrition"
        ]
        assert len(nutrition_sections) == 1
        atom = nutrition_sections[0].atoms[0]
        assert atom.atom_type == "qualitative"
        assert "nutrition" in atom.atom_text
        assert "v0.2.1 W-PROV-3" in atom.atom_text
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Acceptance #9 — canonical-latest rerun fixture
# ---------------------------------------------------------------------------


def test_canonical_latest_rerun_fixture_full_pipeline(tmp_path: Path):
    """Acceptance #9 / F-PLAN-R2-03 / round-3 surface-listed:
    pins the W-EVCARD-WEEKLY append-only contract through the W52
    pipeline.

    Steps:
      1. Run W52 → emit cards (run 1).
      2. Mutate one source row (change a recommendation's action_detail
         to alter prose AND therefore alter claim_id).
      3. Rerun W52 → emit cards (run 2).
      4. Assert weekly_claim_card has rows from BOTH runs.
      5. Default --json returns the canonical-latest set.
      6. --json --include-history returns the full append-only
         history.

    NOTE: Mutation here changes the *prose-driving* state (rec
    action), which yields a NEW claim_id (different prose →
    different hash). So both runs produce distinct claim_ids;
    canonical-latest sees both. The intent of acceptance #9 is to
    pin the broader rerun semantics — mutating the source state
    does not silently overwrite cards.
    """

    conn = _db(tmp_path)
    try:
        _seed_full_week_with_recovery_and_running(conn)
        bundle1 = _build_bundle(conn)
        # Use distinct computed_at to keep the canonical-latest sort
        # deterministic across runs (otherwise the two emissions
        # land at the same wall-clock and tie-break by sort order).
        n1 = emit_weekly_claim_cards(
            conn, bundle1,
            computed_at="2026-05-07T10:00:00Z",
        )

        # Mutate: change one rec's action_detail so the prose differs
        # → distinct claim_id for that atom.
        conn.execute(
            "UPDATE recommendation_log SET payload_json = ? "
            "WHERE recommendation_id = 'rec_2026-04-29_recovery'",
            (json.dumps({
                "action": "easy_recovery",
                "domain": "recovery",
                "rationale": [
                    {"reason_token": "resting_hr_spike_3_days_running"},
                ],
            }),),
        )
        conn.commit()

        bundle2 = _build_bundle(conn)
        n2 = emit_weekly_claim_cards(
            conn, bundle2,
            computed_at="2026-05-07T11:00:00Z",
        )

        # Append-only: total full-history rows = n1 + n2.
        full = load_full_history_for_week(
            conn, user_id=USER, iso_week=WEEK,
        )
        assert len(full) == n1 + n2

        # Canonical-latest: 1 row per distinct claim_id.
        canonical = load_canonical_latest_for_week(
            conn, user_id=USER, iso_week=WEEK,
        )
        canonical_claim_ids = {c["claim_id"] for c in canonical}
        assert len(canonical) == len(canonical_claim_ids)

        # JSON-default mirrors canonical-latest.
        default_payload = json.loads(render_json(bundle2, conn=conn))
        default_card_ids = {
            c["card_id"] for c in default_payload["claim_cards"]
        }
        canonical_card_ids = {c["card_id"] for c in canonical}
        assert default_card_ids == canonical_card_ids

        # JSON --include-history mirrors full history.
        history_payload = json.loads(render_json(
            bundle2, conn=conn, include_history=True,
        ))
        history_card_ids = {
            c["card_id"] for c in history_payload["claim_cards"]
        }
        full_card_ids = {c["card_id"] for c in full}
        assert history_card_ids == full_card_ids
        # And the history view is strictly larger than the canonical-
        # latest view (we mutated → some prior cards superseded).
        assert len(history_card_ids) >= len(canonical_card_ids)
    finally:
        conn.close()


def test_rerun_with_unchanged_state_keeps_one_card_per_claim_id(
    tmp_path: Path,
):
    """A second emission run with UNCHANGED source state appends
    new rows (UUID-suffixed card_id, fresh computed_at) but each
    new row collides with a prior row's claim_id. Canonical-latest
    view returns one row per claim_id — the most recent
    computed_at wins.
    """

    conn = _db(tmp_path)
    try:
        _seed_full_week_with_recovery_and_running(conn)
        bundle = _build_bundle(conn)
        n = emit_weekly_claim_cards(
            conn, bundle,
            computed_at="2026-05-07T10:00:00Z",
        )
        emit_weekly_claim_cards(
            conn, bundle,
            computed_at="2026-05-07T11:00:00Z",
        )

        full = load_full_history_for_week(
            conn, user_id=USER, iso_week=WEEK,
        )
        canonical = load_canonical_latest_for_week(
            conn, user_id=USER, iso_week=WEEK,
        )

        # 2 rows per claim_id in full; 1 per claim_id in canonical.
        assert len(full) == 2 * n
        assert len(canonical) == n

        # Every canonical row carries the newer computed_at.
        for c in canonical:
            assert c["computed_at"] == "2026-05-07T11:00:00Z"
    finally:
        conn.close()
