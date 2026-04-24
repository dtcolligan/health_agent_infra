"""End-to-end tests for ``hai explain`` (Phase C of the post-v0.1.0 roadmap).

Covers the acceptance criteria called out in
``reporting/plans/post_v0_1_roadmap.md`` §5 Phase C:

1. **Read-only**: a JSON or text explain run leaves every persisted
   table at the same row count it had before.
2. **End-to-end six-domain**: a canonical six-domain plan can be
   reconstructed in full — proposals, X-rule firings (split by phase),
   final recommendations, and review linkage.
3. **Plan-id form**: ``--daily-plan-id`` returns the same bundle as the
   date/user form for the canonical plan.
4. **Supersession linkage**: a ``_v<N>`` plan reports its
   ``supersedes`` pointer back to the canonical it replaced, and the
   canonical reports ``superseded_by`` to the new variant.
5. **Argument hygiene**: missing or conflicting flags reject loudly
   without touching state.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from health_agent_infra.core import exit_codes
from health_agent_infra.core.schemas import (
    ReviewEvent,
    ReviewOutcome,
    canonical_daily_plan_id,
)
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_proposal,
    project_review_event,
    project_review_outcome,
)
from health_agent_infra.core.synthesis import run_synthesis
from health_agent_infra.core.writeback.proposal import (
    PROPOSAL_SCHEMA_VERSIONS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _fresh_db(tmp_path) -> Path:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return db_path


def _proposal(domain: str, action: str, **overrides: Any) -> dict[str, Any]:
    base = {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS[domain],
        "proposal_id": f"prop_2026-04-17_u_local_1_{domain}_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-17",
        "domain": domain,
        "action": action,
        "action_detail": None,
        "rationale": [f"{domain}_baseline_signal"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }
    base.update(overrides)
    return base


def _six_domain_proposals() -> list[dict[str, Any]]:
    return [
        _proposal("recovery", "proceed_with_planned_session"),
        _proposal("running", "proceed_with_planned_run"),
        _proposal("sleep", "maintain_schedule"),
        _proposal("stress", "maintain_routine"),
        _proposal("strength", "proceed_with_planned_session"),
        _proposal(
            "nutrition", "maintain_targets",
            action_detail={"protein_target_g": 140},
        ),
    ]


def _stressful_snapshot() -> dict[str, Any]:
    """Snapshot that fires X1a (sleep_debt=moderate) + X7 (stress=high).

    Picked so the explain bundle exercises both Phase A firing classes
    (``soften`` and ``cap_confidence``) end to end, alongside the calm
    domains. Mirrors the snapshot in
    ``test_cli_synthesize::_four_domain_snapshot_stressful``.
    """

    return {
        "recovery": {
            "classified_state": {"sleep_debt_band": "none"},
            "today": {"acwr_ratio": 1.0},
        },
        "sleep": {
            "classified_state": {"sleep_debt_band": "moderate"},
            "today": {"sleep_hours": 6.5},
        },
        "stress": {
            "classified_state": {"garmin_stress_band": "high"},
            "today": {
                "garmin_all_day_stress": 65,
                "body_battery_end_of_day": 45,
            },
            "today_garmin": 65,
            "today_body_battery": 45,
        },
        "running": {},
    }


def _seed_six_domain_plan(db_path: Path) -> str:
    conn = open_connection(db_path)
    try:
        for proposal in _six_domain_proposals():
            project_proposal(conn, proposal)
        result = run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_stressful_snapshot(),
        )
    finally:
        conn.close()
    return result.daily_plan_id


def _seed_review(
    db_path: Path,
    *,
    recommendation_id: str,
    domain: str,
    record_outcome: bool = True,
) -> str:
    """Persist a review_event (+ optional review_outcome) for an existing rec."""

    review_event_id = f"rev_for_{recommendation_id}"
    event = ReviewEvent(
        review_event_id=review_event_id,
        recommendation_id=recommendation_id,
        user_id="u_local_1",
        review_at=datetime(2026, 4, 18, 7, 0, tzinfo=timezone.utc),
        review_question="Did yesterday's plan land well?",
        domain=domain,
    )
    conn = open_connection(db_path)
    try:
        project_review_event(conn, event)
        if record_outcome:
            outcome = ReviewOutcome(
                review_event_id=review_event_id,
                recommendation_id=recommendation_id,
                user_id="u_local_1",
                recorded_at=datetime(2026, 4, 18, 19, 0, tzinfo=timezone.utc),
                followed_recommendation=True,
                self_reported_improvement=True,
                free_text="felt easier than expected",
                domain=domain,
            )
            project_review_outcome(conn, outcome)
    finally:
        conn.close()
    return review_event_id


def _table_counts(db_path: Path) -> dict[str, int]:
    conn = open_connection(db_path)
    try:
        return {
            table: conn.execute(
                f"SELECT COUNT(*) AS n FROM {table}"  # noqa: S608 — fixed table list
            ).fetchone()["n"]
            for table in (
                "proposal_log",
                "daily_plan",
                "x_rule_firing",
                "recommendation_log",
                "review_event",
                "review_outcome",
            )
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_explain_for_date_reconstructs_six_domain_plan_end_to_end(
    tmp_path, capsys,
):
    """Acceptance criterion 3: a canonical six-domain plan can be
    explained in full. The JSON bundle must surface proposals, firings
    (split by phase), recommendations, and any review linkage —
    sourced from persisted state alone."""

    from health_agent_infra.cli import main as cli_main

    db_path = _fresh_db(tmp_path)
    daily_plan_id = _seed_six_domain_plan(db_path)

    # Pick the recovery recommendation as the one with a recorded review.
    recovery_rec_id = "rec_2026-04-17_u_local_1_recovery_01"
    _seed_review(
        db_path,
        recommendation_id=recovery_rec_id,
        domain="recovery",
        record_outcome=True,
    )

    before_counts = _table_counts(db_path)

    rc = cli_main([
        "explain",
        "--for-date", "2026-04-17",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)

    # Plan header
    assert payload["plan"]["daily_plan_id"] == daily_plan_id
    assert payload["plan"]["user_id"] == "u_local_1"
    assert payload["plan"]["for_date"] == "2026-04-17"
    assert payload["plan"]["supersedes"] is None
    assert payload["plan"]["superseded_by"] is None
    # X-rules surfaced on the plan should at least cover the firings
    # the stressful snapshot drives (X1a + X7).
    assert "X1a" in payload["plan"]["x_rules_fired"]
    assert "X7" in payload["plan"]["x_rules_fired"]

    # Proposals — six domains in
    proposal_domains = sorted(p["domain"] for p in payload["proposals"])
    assert proposal_domains == [
        "nutrition", "recovery", "running", "sleep", "strength", "stress",
    ]
    # Each proposal carries its action + confidence + rationale.
    nutrition_proposal = next(
        p for p in payload["proposals"] if p["domain"] == "nutrition"
    )
    assert nutrition_proposal["action"] == "maintain_targets"
    assert nutrition_proposal["action_detail"] == {"protein_target_g": 140}
    assert nutrition_proposal["confidence"] == "high"
    assert nutrition_proposal["rationale"] == ["nutrition_baseline_signal"]

    # X-rule firings — split by phase, each row carries enough to walk
    # the cause chain (rule_id + tier + affected_domain + trigger_note).
    phase_a = payload["x_rule_firings"]["phase_a"]
    phase_b = payload["x_rule_firings"]["phase_b"]
    assert phase_a, "Phase A firings should be non-empty under stressful snapshot"
    fired_rule_ids_a = {f["rule_id"] for f in phase_a}
    assert "X1a" in fired_rule_ids_a
    assert "X7" in fired_rule_ids_a
    # Every Phase A firing must declare a tier and an affected domain.
    for firing in phase_a:
        assert firing["tier"] in {
            "soften", "block", "cap_confidence", "restructure",
        }
        assert firing["affected_domain"] in {
            "recovery", "running", "sleep", "stress", "strength", "nutrition",
        }
        # Phase A firings under current rule set are not orphans.
        assert firing["orphan"] is False
    # Phase B firings, when present, must all be tier='adjust'.
    for firing in phase_b:
        assert firing["tier"] == "adjust"

    # Recommendations — six domains out
    rec_domains = sorted(r["domain"] for r in payload["recommendations"])
    assert rec_domains == [
        "nutrition", "recovery", "running", "sleep", "strength", "stress",
    ]
    # Running was softened by X1a (proceed → easy_aerobic).
    running_rec = next(
        r for r in payload["recommendations"] if r["domain"] == "running"
    )
    assert running_rec["action"] == "downgrade_to_easy_aerobic"
    # Every recommendation carries a follow-up review_event_id.
    for rec in payload["recommendations"]:
        assert rec["review_event_id"], (
            f"recommendation {rec['recommendation_id']} missing review_event_id"
        )

    # Review linkage — exactly the one we recorded surfaces with its outcome.
    assert len(payload["reviews"]) == 1
    review = payload["reviews"][0]
    assert review["recommendation_id"] == recovery_rec_id
    assert review["domain"] == "recovery"
    assert len(review["outcomes"]) == 1
    outcome = review["outcomes"][0]
    assert outcome["followed_recommendation"] is True
    assert outcome["self_reported_improvement"] is True
    assert outcome["free_text"] == "felt easier than expected"

    # Read-only: nothing changed in any persisted table.
    assert _table_counts(db_path) == before_counts


def test_explain_by_daily_plan_id_matches_for_date(tmp_path, capsys):
    """``--daily-plan-id`` returns the same bundle as ``--for-date`` for
    the canonical plan. Anything that diverges is a queries.py bug."""

    from health_agent_infra.cli import main as cli_main

    db_path = _fresh_db(tmp_path)
    daily_plan_id = _seed_six_domain_plan(db_path)

    rc = cli_main([
        "explain",
        "--for-date", "2026-04-17",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
    ])
    assert rc == 0
    by_date = json.loads(capsys.readouterr().out)

    rc = cli_main([
        "explain",
        "--daily-plan-id", daily_plan_id,
        "--db-path", str(db_path),
    ])
    assert rc == 0
    by_id = json.loads(capsys.readouterr().out)

    assert by_date == by_id


def test_explain_text_output_is_human_readable(tmp_path, capsys):
    """``--text`` emits the operator report. We check for stable section
    markers rather than exact wording so render tweaks don't ratchet the
    test."""

    from health_agent_infra.cli import main as cli_main

    db_path = _fresh_db(tmp_path)
    daily_plan_id = _seed_six_domain_plan(db_path)
    _seed_review(
        db_path,
        recommendation_id="rec_2026-04-17_u_local_1_recovery_01",
        domain="recovery",
    )

    rc = cli_main([
        "explain",
        "--daily-plan-id", daily_plan_id,
        "--db-path", str(db_path),
        "--text",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert f"daily_plan_id : {daily_plan_id}" in out
    assert "## Proposals" in out
    assert "## Phase A X-rule firings" in out
    assert "## Phase B X-rule firings" in out
    assert "## Final recommendations" in out
    assert "## Reviews" in out


# ---------------------------------------------------------------------------
# D3 §hai explain --operator rename — canonical flag + deprecation hint
# ---------------------------------------------------------------------------


def test_explain_operator_flag_produces_the_same_report_as_text(tmp_path, capsys):
    """``--operator`` is the canonical flag as of v0.1.4; it renders
    byte-identical output to the deprecated ``--text``."""

    from health_agent_infra.cli import main as cli_main

    db_path = _fresh_db(tmp_path)
    daily_plan_id = _seed_six_domain_plan(db_path)

    rc_op = cli_main([
        "explain", "--daily-plan-id", daily_plan_id,
        "--db-path", str(db_path), "--operator",
    ])
    operator_out = capsys.readouterr().out

    rc_text = cli_main([
        "explain", "--daily-plan-id", daily_plan_id,
        "--db-path", str(db_path), "--text",
    ])
    # Discard stderr (carries the deprecation note for --text) but keep
    # stdout so we can compare renders.
    text_capture = capsys.readouterr()
    text_out = text_capture.out

    assert rc_op == 0
    assert rc_text == 0
    assert operator_out == text_out


def test_explain_text_emits_deprecation_hint_on_stderr(tmp_path, capsys):
    """``--text`` keeps working for one release cycle but must nudge the
    caller to migrate via a stderr note. Scripts that parse stdout JSON
    aren't affected."""

    from health_agent_infra.cli import main as cli_main

    db_path = _fresh_db(tmp_path)
    daily_plan_id = _seed_six_domain_plan(db_path)

    rc = cli_main([
        "explain", "--daily-plan-id", daily_plan_id,
        "--db-path", str(db_path), "--text",
    ])
    captured = capsys.readouterr()
    assert rc == 0
    assert "--text is deprecated" in captured.err
    assert "--operator" in captured.err


def test_explain_operator_does_not_emit_deprecation_hint(tmp_path, capsys):
    """Callers already on the canonical flag see clean stderr."""

    from health_agent_infra.cli import main as cli_main

    db_path = _fresh_db(tmp_path)
    daily_plan_id = _seed_six_domain_plan(db_path)

    rc = cli_main([
        "explain", "--daily-plan-id", daily_plan_id,
        "--db-path", str(db_path), "--operator",
    ])
    captured = capsys.readouterr()
    assert rc == 0
    assert "deprecated" not in captured.err


def test_explain_supersession_linkage_walks_both_directions(tmp_path, capsys):
    """A ``--supersede`` rerun creates a ``_v2`` variant. The canonical
    plan's bundle must report ``superseded_by=_v2`` and the variant
    bundle must report ``supersedes=<canonical>``."""

    from health_agent_infra.cli import main as cli_main

    db_path = _fresh_db(tmp_path)
    canonical = _seed_six_domain_plan(db_path)

    # Re-run synthesis with --supersede via the orchestration entrypoint.
    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_stressful_snapshot(),
            supersede=True,
        )
    finally:
        conn.close()
    variant_id = result.daily_plan_id
    assert variant_id == f"{canonical}_v2"

    # Canonical plan bundle reports superseded_by → variant.
    rc = cli_main([
        "explain",
        "--daily-plan-id", canonical,
        "--db-path", str(db_path),
    ])
    assert rc == 0
    canonical_payload = json.loads(capsys.readouterr().out)
    assert canonical_payload["plan"]["superseded_by"] == variant_id
    assert canonical_payload["plan"]["supersedes"] is None

    # Variant plan bundle reports supersedes → canonical.
    rc = cli_main([
        "explain",
        "--daily-plan-id", variant_id,
        "--db-path", str(db_path),
    ])
    assert rc == 0
    variant_payload = json.loads(capsys.readouterr().out)
    assert variant_payload["plan"]["supersedes"] == canonical
    assert variant_payload["plan"]["superseded_by"] is None


def test_explain_rejects_when_plan_id_missing(tmp_path, capsys):
    """An unknown plan id reports a not-found error and exits NOT_FOUND."""

    from health_agent_infra.cli import main as cli_main

    db_path = _fresh_db(tmp_path)

    rc = cli_main([
        "explain",
        "--daily-plan-id", "plan_2099-01-01_nope",
        "--db-path", str(db_path),
    ])
    assert rc == exit_codes.NOT_FOUND
    err = capsys.readouterr().err
    assert "no daily_plan row" in err


def test_explain_rejects_conflicting_flags(tmp_path, capsys):
    """Passing both --daily-plan-id and (--for-date / --user-id)
    must reject without opening the DB."""

    from health_agent_infra.cli import main as cli_main

    db_path = _fresh_db(tmp_path)

    rc = cli_main([
        "explain",
        "--daily-plan-id", "plan_x",
        "--for-date", "2026-04-17",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
    ])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "either --daily-plan-id" in err.lower() or "not both" in err.lower()


def test_explain_rejects_when_no_selectors(tmp_path, capsys):
    """Calling explain with neither selector form fails fast."""

    from health_agent_infra.cli import main as cli_main

    db_path = _fresh_db(tmp_path)

    rc = cli_main([
        "explain",
        "--db-path", str(db_path),
    ])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "provide --daily-plan-id" in err or "for-date" in err
