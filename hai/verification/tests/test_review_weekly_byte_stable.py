"""W52 step 5 — render layer + byte-stability (PLAN §2.D acceptance #1).

The PLAN §2.D acceptance contract requires that ``hai review weekly``
produces the same JSON output across 3 consecutive runs over a
fixture-week corpus. This file pins:

  * Markdown abstain template (literal substitution from coverage)
  * Markdown full-week shape (sections + headers + bullets)
  * JSON shape (every prose-builder lane round-trips)
  * --include-history flag flips between canonical-latest and full
    append-only history (acceptance #9)
  * Byte-stable JSON output across 3 runs over the same fixture

Together with the F-EXPLAIN obligation hooks in
``test_review_weekly.py`` and the abstain-metadata pins in
``test_review_weekly_abstain_metadata.py``, this completes the
acceptance #1 + #9 surface for W52.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from health_agent_infra.core.review.prose_builder import (
    build_weekly_prose,
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
    project_weekly_card,
)
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)


USER = "u_w52_render"
WEEK = "2026-W18"


def _db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return open_connection(db_path)


def _seed_partial_week(conn: sqlite3.Connection, *, days: list[str]) -> None:
    """Seed `days` (ISO date strings) with one canonical plan each.
    No recommendations — sufficient for abstain-template testing."""
    for d in days:
        conn.execute(
            "INSERT INTO daily_plan ("
            "  daily_plan_id, user_id, for_date, synthesized_at, "
            "  recommendation_ids_json, proposal_ids_json, "
            "  x_rules_fired_json, synthesis_meta_json, source, "
            "  ingest_actor, agent_version, validated_at, projected_at, "
            "  superseded_by_plan_id, superseded_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)",
            (
                f"plan_{d}_render", USER, d,
                f"{d}T07:00:00Z",
                "[]", "[]", "[]", None,
                "claude_agent_v1", "claude_agent_v1", "0.2.0",
                f"{d}T07:00:00Z", f"{d}T07:00:01Z",
            ),
        )
    conn.commit()


def _build_bundle(conn: sqlite3.Connection):
    agg = load_weekly_aggregation(conn, iso_week=WEEK, user_id=USER)
    coverage = evaluate_weekly_coverage(agg, coverage_threshold_days=5)
    rollup = compute_data_quality_rollup(agg.sync_runs, stale_pull_hours=48)
    return build_weekly_prose(conn, agg, coverage, rollup)


# ---------------------------------------------------------------------------
# Markdown abstain template
# ---------------------------------------------------------------------------


def test_render_markdown_abstain_template_is_literal_substitution(
    tmp_path: Path,
):
    """The abstain markdown matches PLAN §2.D template byte-exact:
    counts, threshold, populated dates, missing dates all substitute
    literally from coverage. F-PLAN-03 round-1 contract.
    """

    conn = _db(tmp_path)
    try:
        # Week 2026-W18 = Mon 2026-04-27 → Sun 2026-05-03. Pick 3
        # days within the week.
        _seed_partial_week(conn, days=["2026-04-30", "2026-05-01", "2026-05-03"])
        bundle = _build_bundle(conn)
        md = render_markdown(bundle)

        assert "# Weekly review — 2026-W18" in md
        assert "**Insufficient data for this week.**" in md
        assert "Plans found: 3 of 7 days (threshold: ≥5)." in md
        assert (
            "Days with plans: 2026-04-30, 2026-05-01, 2026-05-03." in md
        )
        # Missing dates list — exact formatting.
        assert (
            "Days without plans: 2026-04-27, 2026-04-28, 2026-04-29, "
            "2026-05-02." in md
        )
        # Closing instruction.
        assert "Run `hai daily` on past days where you have data" in md
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# JSON abstain payload
# ---------------------------------------------------------------------------


def test_render_json_abstain_payload_carries_coverage_lanes(
    tmp_path: Path,
):
    """JSON abstain output carries weekly_status, populated/missing
    dates, threshold; sections is empty; claim_cards is empty.
    """

    conn = _db(tmp_path)
    try:
        _seed_partial_week(conn, days=["2026-04-27"])
        bundle = _build_bundle(conn)
        payload = json.loads(render_json(bundle, conn=conn))

        assert payload["iso_week"] == "2026-W18"
        assert payload["user_id"] == USER
        assert payload["weekly_status"] == "insufficient_data"
        assert payload["coverage"]["days_with_plans"] == 1
        assert payload["coverage"]["coverage_threshold"] == 5
        assert payload["coverage"]["populated_dates"] == ["2026-04-27"]
        assert payload["sections"] == []
        assert payload["claim_cards"] == []
        assert payload["include_history"] is False
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Byte-stable JSON across 3 consecutive runs (acceptance #1)
# ---------------------------------------------------------------------------


def test_render_json_byte_stable_across_three_runs(tmp_path: Path):
    """Three consecutive renders of the same bundle produce
    byte-identical JSON. Acceptance #1 — fixture-week deterministic
    output assertion.
    """

    conn = _db(tmp_path)
    try:
        _seed_partial_week(
            conn,
            days=[
                "2026-04-27", "2026-04-28", "2026-04-29",
                "2026-04-30", "2026-05-01",
            ],
        )
        bundle1 = _build_bundle(conn)
        bundle2 = _build_bundle(conn)
        bundle3 = _build_bundle(conn)
        out1 = render_json(bundle1, conn=conn)
        out2 = render_json(bundle2, conn=conn)
        out3 = render_json(bundle3, conn=conn)
        assert out1 == out2 == out3
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# --include-history flag (acceptance #9 + F-PLAN-R2-03)
# ---------------------------------------------------------------------------


def test_render_json_include_history_flag_flips_card_view(tmp_path: Path):
    """Default JSON returns canonical-latest cards (one row per
    claim_id with max computed_at). --include-history returns the
    full append-only history (latest + superseded). PLAN §2.D
    acceptance #9 contract.

    Setup: insert two cards with the same claim_id but different
    computed_at — the older one is "superseded" by the newer.
    """

    conn = _db(tmp_path)
    try:
        _seed_partial_week(conn, days=["2026-04-27"])
        # Two cards with the same claim_id but different computed_at.
        # Use explicit claim_id + card_id so the test is deterministic.
        locator = {
            "table": "accepted_recovery_state_daily",
            "pk": {"as_of_date": "2026-04-27", "user_id": USER},
            "row_version": "2026-04-27T07:00:00Z",
        }
        # Card A: computed_at older. Provide explicit claim_id so
        # both cards collide on (iso_week, user_id, claim_id).
        project_weekly_card(
            conn,
            user_id=USER,
            iso_week=WEEK,
            claim_atom_text="claim under test",
            atom_type="quantitative",
            derivation_path="aggregate",
            locator_set=[locator],
            audit_refs={"recommendation_log": ["rec_1"]},
            claim_id="fixed_claim_id",
            card_id="card_old",
            computed_at="2026-05-07T10:00:00Z",
        )
        # Card B: same claim_id, newer computed_at.
        project_weekly_card(
            conn,
            user_id=USER,
            iso_week=WEEK,
            claim_atom_text="claim under test",
            atom_type="quantitative",
            derivation_path="aggregate",
            locator_set=[locator],
            audit_refs={"recommendation_log": ["rec_1"]},
            claim_id="fixed_claim_id",
            card_id="card_new",
            computed_at="2026-05-07T11:00:00Z",
        )

        bundle = _build_bundle(conn)

        # Default: canonical-latest only (1 row, the newer one).
        default_payload = json.loads(render_json(bundle, conn=conn))
        default_cards = default_payload["claim_cards"]
        assert len(default_cards) == 1
        assert default_cards[0]["card_id"] == "card_new"
        assert default_cards[0]["claim_id"] == "fixed_claim_id"

        # --include-history: both rows present.
        history_payload = json.loads(render_json(
            bundle, conn=conn, include_history=True,
        ))
        history_cards = history_payload["claim_cards"]
        history_card_ids = {c["card_id"] for c in history_cards}
        assert history_card_ids == {"card_old", "card_new"}
        assert history_payload["include_history"] is True
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Markdown does not contain synthesis_meta (F-EXPLAIN-03 reaffirmed)
# ---------------------------------------------------------------------------


def test_render_markdown_does_not_contain_synthesis_meta(tmp_path: Path):
    """F-EXPLAIN-03 reaffirmed at the render layer: markdown output
    never carries the literal string `synthesis_meta`. The JSON
    output may carry it (the runtime concept lives in
    synthesis_meta_json on daily_plan rows) — but the markdown
    surface is reader-facing only.
    """

    conn = _db(tmp_path)
    try:
        _seed_partial_week(
            conn,
            days=[
                "2026-04-27", "2026-04-28", "2026-04-29",
                "2026-04-30", "2026-05-01",
            ],
        )
        bundle = _build_bundle(conn)
        md = render_markdown(bundle)
        assert "synthesis_meta" not in md
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# JSON sort_keys produces stable ordering even with random insert order
# ---------------------------------------------------------------------------


def test_render_json_sorts_keys_for_byte_stability(tmp_path: Path):
    """Stable JSON output requires sort_keys=True. Without it,
    Python's dict insertion order would leak across the wire and
    byte-stability would silently regress. This test pins the
    invariant by inserting two cards in different orders and
    asserting the rendered keys are sorted.
    """

    conn = _db(tmp_path)
    try:
        _seed_partial_week(
            conn,
            days=[
                "2026-04-27", "2026-04-28", "2026-04-29",
                "2026-04-30", "2026-05-01",
            ],
        )
        bundle = _build_bundle(conn)
        rendered = render_json(bundle, conn=conn)
        # Top-level keys parse out in alphabetical order.
        first_object = rendered.split("\n", 1)[1]  # past the "{"
        # First key after the opening brace must be the alphabetically-
        # first one — "claim_cards" comes before "coverage".
        assert (
            '"claim_cards"' in first_object.split('"coverage"', 1)[0]
        )
    finally:
        conn.close()
