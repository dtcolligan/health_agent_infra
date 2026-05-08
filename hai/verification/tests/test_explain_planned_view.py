"""Phase 1 follow-up — `hai explain` surfaces the planned-recommendation ledger.

Contracts pinned:

  1. The explain bundle carries a ``planned_recommendations`` list,
     populated from the migration-011 table.
  2. JSON output (``bundle_to_dict``) exposes a top-level
     ``planned_recommendations`` key that mirrors the adapted
     recommendation fields, plus ``proposal_id`` for FK walk-back.
  3. Text output (``render_bundle_text``) includes a "Planned
     recommendations" section between the proposals and the Phase A
     firings.
  4. When an X-rule softened a domain, the planned row carries the
     ORIGINAL action and the adapted row carries the softened action —
     the diff is visible at the render layer.
  5. Backward compatibility: the explain surface does not crash on a
     plan with no planned rows (e.g. a pre-migration-011 canonical plan
     simulated by deleting the rows).
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from health_agent_infra.core.explain.queries import (
    load_bundle_by_daily_plan_id,
)
from health_agent_infra.core.explain.render import (
    bundle_to_dict,
    render_bundle_text,
)
from health_agent_infra.core.schemas import canonical_daily_plan_id
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_proposal,
)
from health_agent_infra.core.synthesis import run_synthesis
from health_agent_infra.core.writeback.proposal import PROPOSAL_SCHEMA_VERSIONS


FOR_DATE = date(2026, 4, 22)
USER = "u_explain"


def _make_proposal(domain: str, action: str) -> dict:
    return {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS[domain],
        "proposal_id": f"prop_{FOR_DATE}_{USER}_{domain}_01",
        "user_id": USER,
        "for_date": FOR_DATE.isoformat(),
        "domain": domain,
        "action": action,
        "action_detail": None,
        "rationale": [f"{domain}_baseline"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": "r1", "decision": "allow", "note": "n"},
        ],
        "bounded": True,
    }


def _stressful_snapshot() -> dict:
    """Moderate sleep debt → X1a fires on hard proposals."""
    return {
        "recovery": {
            "classified_state": {"sleep_debt_band": "moderate"},
            "today": {"acwr_ratio": 1.0},
        },
        "sleep": {"classified_state": {"sleep_debt_band": "moderate"}},
        "stress": {
            "classified_state": {"garmin_stress_band": "low"},
            "today_body_battery": 75,
        },
        "running": {},
    }


def _prepare_db_with_plan(tmp_path: Path) -> Path:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    proposal = _make_proposal("recovery", "proceed_with_planned_session")
    conn = open_connection(db_path)
    try:
        project_proposal(conn, proposal)
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_stressful_snapshot(),
        )
    finally:
        conn.close()
    return db_path


def _plan_id() -> str:
    return canonical_daily_plan_id(FOR_DATE, USER)


# ---------------------------------------------------------------------------
# Bundle loader
# ---------------------------------------------------------------------------


def test_bundle_includes_planned_recommendations(tmp_path: Path):
    db_path = _prepare_db_with_plan(tmp_path)
    conn = open_connection(db_path)
    try:
        bundle = load_bundle_by_daily_plan_id(
            conn, daily_plan_id=_plan_id(),
        )
    finally:
        conn.close()
    assert len(bundle.planned_recommendations) == 1
    planned = bundle.planned_recommendations[0]
    assert planned.domain == "recovery"
    # Planned preserves the ORIGINAL proposal action.
    assert planned.action == "proceed_with_planned_session"
    assert planned.proposal_id.startswith("prop_")


# ---------------------------------------------------------------------------
# JSON render
# ---------------------------------------------------------------------------


def test_bundle_json_has_planned_recommendations_key(tmp_path: Path):
    db_path = _prepare_db_with_plan(tmp_path)
    conn = open_connection(db_path)
    try:
        bundle = load_bundle_by_daily_plan_id(
            conn, daily_plan_id=_plan_id(),
        )
    finally:
        conn.close()
    payload = bundle_to_dict(bundle)
    assert "planned_recommendations" in payload
    planned_list = payload["planned_recommendations"]
    assert isinstance(planned_list, list)
    assert len(planned_list) == 1
    entry = planned_list[0]
    for key in (
        "planned_id", "proposal_id", "domain", "action",
        "action_detail", "confidence", "schema_version", "captured_at",
    ):
        assert key in entry, f"expected key {key!r} in planned entry; got {sorted(entry)}"


# ---------------------------------------------------------------------------
# Text render
# ---------------------------------------------------------------------------


def test_bundle_text_has_planned_section(tmp_path: Path):
    db_path = _prepare_db_with_plan(tmp_path)
    conn = open_connection(db_path)
    try:
        bundle = load_bundle_by_daily_plan_id(
            conn, daily_plan_id=_plan_id(),
        )
    finally:
        conn.close()
    text = render_bundle_text(bundle)
    assert "## Planned recommendations (pre-X-rule aggregate)" in text
    # Section lists the original action, not the softened one.
    assert "proceed_with_planned_session" in text


def test_text_render_shows_planned_vs_adapted_diff(tmp_path: Path):
    """The planned section carries the ORIGINAL action, and the
    recommendations section carries the post-X-rule action. Both are
    visible side-by-side in the rendered text."""

    db_path = _prepare_db_with_plan(tmp_path)
    conn = open_connection(db_path)
    try:
        bundle = load_bundle_by_daily_plan_id(
            conn, daily_plan_id=_plan_id(),
        )
    finally:
        conn.close()
    text = render_bundle_text(bundle)
    # Planned section shows original hard action.
    planned_section_start = text.index(
        "## Planned recommendations (pre-X-rule aggregate)"
    )
    planned_section_end = text.index("## Phase A X-rule firings")
    planned_section = text[planned_section_start:planned_section_end]
    assert "proceed_with_planned_session" in planned_section
    # Final recommendations section shows adapted (softened) action.
    recs_section_start = text.index("## Final recommendations")
    recs_section_end = text.index("## Reviews")
    recs_section = text[recs_section_start:recs_section_end]
    assert "downgrade_hard_session_to_zone_2" in recs_section


# ---------------------------------------------------------------------------
# Backward compatibility: no planned rows → empty list, no crash
# ---------------------------------------------------------------------------


def test_firing_carries_human_explanation_in_json_and_text(tmp_path: Path):
    """Phase 3 — the sentence-form human explanation surfaces on every
    firing in both the JSON bundle and the text render, alongside the
    machine-readable slug."""

    db_path = _prepare_db_with_plan(tmp_path)
    conn = open_connection(db_path)
    try:
        bundle = load_bundle_by_daily_plan_id(
            conn, daily_plan_id=_plan_id(),
        )
    finally:
        conn.close()

    # There's exactly one firing in this scenario: X1a on recovery.
    firings = bundle.phase_a_firings
    assert len(firings) == 1
    firing = firings[0]
    assert firing.rule_id == "X1a"
    assert firing.human_explanation is not None
    assert firing.human_explanation.startswith("Sleep debt is moderate")

    # JSON render carries the sentence.
    payload = bundle_to_dict(bundle)
    json_firing = payload["x_rule_firings"]["phase_a"][0]
    assert json_firing["human_explanation"] == firing.human_explanation
    assert json_firing["public_name"] == "sleep-debt-softens-hard"

    # Text render shows the sentence alongside the slug header.
    text = render_bundle_text(bundle)
    assert firing.human_explanation in text
    assert "sleep-debt-softens-hard" in text


def test_bundle_with_no_planned_rows_degrades_to_empty_list(tmp_path: Path):
    """Simulate a pre-migration-011 plan by deleting the planned rows
    post-synthesis. The explain bundle must still render cleanly with
    an empty planned_recommendations list."""

    db_path = _prepare_db_with_plan(tmp_path)
    conn = open_connection(db_path)
    try:
        conn.execute("DELETE FROM planned_recommendation")
        conn.commit()
        bundle = load_bundle_by_daily_plan_id(
            conn, daily_plan_id=_plan_id(),
        )
    finally:
        conn.close()

    assert bundle.planned_recommendations == []
    # JSON render still includes the key with an empty list.
    payload = bundle_to_dict(bundle)
    assert payload["planned_recommendations"] == []
    # Text render prints the section with the "(none recorded)" marker.
    text = render_bundle_text(bundle)
    assert "## Planned recommendations (pre-X-rule aggregate)" in text
    assert "(none recorded)" in text
