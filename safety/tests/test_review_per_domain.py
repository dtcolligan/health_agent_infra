"""Tests for Phase 2 step 5 — per-domain review flow.

Locks the contract that ``hai review schedule``, ``hai review record``, and
``hai review summary`` propagate and honor ``domain`` so recovery- and
running-domain reviews never leak into each other's summaries.

Covered here (per the plan's "Add targeted tests" checklist):

  1. ``schedule_review`` on a recovery recommendation persists ``domain =
     "recovery"`` on ``ReviewEvent`` and in the ``review_events.jsonl``
     payload.
  2. ``schedule_review`` on a running recommendation persists ``domain =
     "running"`` — the running recommendation's frozen ``domain`` attribute
     wins over the legacy default.
  3. ``record_review_outcome`` propagates the event's domain onto the
     outcome and into ``review_outcomes.jsonl``.
  4. ``summarize_review_history`` without ``domain=`` keeps its v1 totals
     (no regression).
  5. ``summarize_review_history(domain="recovery")`` and ``domain="running"``
     return cleanly separated counts when the history contains both
     domains.
  6. CLI round-trip: ``hai review schedule`` + ``hai review record`` on a
     running payload land a ``domain='running'`` row in the DB projections,
     not the default ``'recovery'``.
  7. CLI summary with ``--domain`` filter isolates per-domain counts on a
     mixed JSONL.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.review.outcomes import (
    record_review_outcome,
    schedule_review,
    summarize_review_history,
)
from health_agent_infra.core.schemas import (
    FollowUp,
    PolicyDecision,
    RECOMMENDATION_SCHEMA_VERSION,
    ReviewEvent,
    ReviewOutcome,
)
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_recommendation,
)
from health_agent_infra.domains.recovery.schemas import TrainingRecommendation


# D2: hai writeback was retired in v0.1.4. Tests that used it as a
# convenience seeder now use a plain tmp subdir — ``schedule_review``
# and ``record_review_outcome`` auto-create the directory on first use.
_WRITEBACK_ROOT_NAME = "writeback"


AS_OF = date(2026, 4, 17)
NOW = datetime(2026, 4, 17, 7, 15, tzinfo=timezone.utc)
REVIEW_AT = NOW.replace(day=18)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _recovery_rec(user: str = "u_rec") -> TrainingRecommendation:
    return TrainingRecommendation(
        schema_version=RECOMMENDATION_SCHEMA_VERSION,
        recommendation_id=f"rec_{AS_OF.isoformat()}_{user}_recovery",
        user_id=user,
        issued_at=NOW,
        for_date=AS_OF,
        action="proceed_with_planned_session",
        action_detail=None,
        rationale=["sleep_debt=none"],
        confidence="high",
        uncertainty=[],
        follow_up=FollowUp(
            review_at=REVIEW_AT,
            review_question="Did today feel appropriate?",
            review_event_id=f"rev_{AS_OF.isoformat()}_{user}_recovery",
        ),
        policy_decisions=[
            PolicyDecision(rule_id="require_min_coverage", decision="allow", note="ok"),
        ],
        bounded=True,
    )


def _running_rec_payload(user: str = "u_run") -> dict:
    """A running recommendation payload shaped like RunningRecommendation.to_dict().

    We build the dict directly rather than instantiating ``RunningRecommendation``
    because the CLI only sees JSON — this exercises the parse path realistically.
    """

    rec_id = f"rec_{AS_OF.isoformat()}_{user}_running"
    review_event_id = f"rev_{AS_OF.isoformat()}_{user}_running"
    return {
        "schema_version": "running_recommendation.v1",
        "recommendation_id": rec_id,
        "user_id": user,
        "issued_at": NOW.isoformat(),
        "for_date": AS_OF.isoformat(),
        "domain": "running",
        "action": "proceed_with_planned_run",
        "action_detail": None,
        "rationale": ["acwr=stable"],
        "confidence": "high",
        "uncertainty": [],
        "follow_up": {
            "review_at": REVIEW_AT.isoformat(),
            "review_question": "Did today's run feel right?",
            "review_event_id": review_event_id,
        },
        "policy_decisions": [
            {"rule_id": "require_min_coverage", "decision": "allow", "note": "ok"},
        ],
        "bounded": True,
        "daily_plan_id": None,
    }


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


# ---------------------------------------------------------------------------
# Library-level: schedule_review carries domain per recommendation source
# ---------------------------------------------------------------------------


def test_schedule_review_on_recovery_rec_persists_domain_recovery(tmp_path: Path):
    base = tmp_path / _WRITEBACK_ROOT_NAME
    rec = _recovery_rec()

    event = schedule_review(rec, base_dir=base)

    assert event.domain == "recovery"
    # Also lands in the JSONL audit.
    line = (base / "review_events.jsonl").read_text(encoding="utf-8").splitlines()[-1]
    assert json.loads(line)["domain"] == "recovery"


def test_schedule_review_with_explicit_domain_override(tmp_path: Path):
    """An explicit ``domain=`` kwarg wins over the recommendation's attribute.

    Guards against a caller ever needing to re-tag an event — e.g. a
    test fixture reusing the recovery builder for a running-shaped event.
    """

    base = tmp_path / _WRITEBACK_ROOT_NAME
    rec = _recovery_rec(user="u_override")

    event = schedule_review(rec, base_dir=base, domain="running")

    assert event.domain == "running"


def test_running_recommendation_domain_flows_through_duck_typed_schedule(tmp_path: Path):
    """Duck-typed schedule_review reads .domain when present.

    ``TrainingRecommendation`` has no ``domain`` attribute; ``RunningRecommendation``
    does. This test builds a minimal duck-typed stand-in to verify the
    attribute path that the CLI's direct ``persist_review_event`` call
    also relies on for the running domain.
    """

    base = tmp_path / _WRITEBACK_ROOT_NAME
    base.mkdir(parents=True)

    class _RunningStub:
        recommendation_id = "rec_run_01"
        user_id = "u_run"
        domain = "running"

        class follow_up:  # noqa: N801 — mirror real attribute name
            review_event_id = "rev_run_01"
            review_at = REVIEW_AT
            review_question = "Did today's run feel right?"

    event = schedule_review(_RunningStub(), base_dir=base)
    assert event.domain == "running"


# ---------------------------------------------------------------------------
# Library-level: record_review_outcome propagates event.domain
# ---------------------------------------------------------------------------


def test_record_review_outcome_inherits_domain_from_event(tmp_path: Path):
    base = tmp_path / _WRITEBACK_ROOT_NAME
    base.mkdir(parents=True)

    running_event = ReviewEvent(
        review_event_id="rev_run_01",
        recommendation_id="rec_run_01",
        user_id="u_run",
        review_at=REVIEW_AT,
        review_question="Did today's run feel right?",
        domain="running",
    )

    outcome = record_review_outcome(
        running_event,
        base_dir=base,
        followed_recommendation=True,
        self_reported_improvement=True,
        now=REVIEW_AT,
    )

    assert outcome.domain == "running"
    line = (base / "review_outcomes.jsonl").read_text(encoding="utf-8").splitlines()[-1]
    assert json.loads(line)["domain"] == "running"


def test_record_review_outcome_respects_explicit_domain_override(tmp_path: Path):
    base = tmp_path / _WRITEBACK_ROOT_NAME
    base.mkdir(parents=True)

    event = ReviewEvent(
        review_event_id="rev_01",
        recommendation_id="rec_01",
        user_id="u_1",
        review_at=REVIEW_AT,
        review_question="?",
        domain="recovery",
    )

    outcome = record_review_outcome(
        event,
        base_dir=base,
        followed_recommendation=False,
        self_reported_improvement=None,
        domain="running",
        now=REVIEW_AT,
    )

    assert outcome.domain == "running"


# ---------------------------------------------------------------------------
# Library-level: summarize_review_history filter
# ---------------------------------------------------------------------------


def _outcome(i: int, domain: str, *, followed: bool, improved) -> ReviewOutcome:
    return ReviewOutcome(
        review_event_id=f"rev_{i}",
        recommendation_id=f"rec_{i}",
        user_id="u_1",
        recorded_at=NOW,
        followed_recommendation=followed,
        self_reported_improvement=improved,
        domain=domain,
    )


def test_summary_without_filter_matches_pre_domain_v1_behavior():
    # 3 recovery (2 improved, 1 not-followed) + 2 running (1 improved, 1 no_change)
    outcomes = [
        _outcome(1, "recovery", followed=True, improved=True),
        _outcome(2, "recovery", followed=True, improved=True),
        _outcome(3, "recovery", followed=False, improved=None),
        _outcome(4, "running", followed=True, improved=True),
        _outcome(5, "running", followed=True, improved=False),
    ]

    summary = summarize_review_history(outcomes)

    assert summary == {
        "total": 5,
        "followed_improved": 3,
        "followed_no_change": 1,
        "followed_unknown": 0,
        "not_followed": 1,
    }


def test_summary_with_domain_filter_splits_cleanly_between_recovery_and_running():
    outcomes = [
        _outcome(1, "recovery", followed=True, improved=True),
        _outcome(2, "recovery", followed=True, improved=True),
        _outcome(3, "recovery", followed=False, improved=None),
        _outcome(4, "running", followed=True, improved=True),
        _outcome(5, "running", followed=True, improved=False),
    ]

    recovery = summarize_review_history(outcomes, domain="recovery")
    running = summarize_review_history(outcomes, domain="running")

    assert recovery == {
        "total": 3,
        "followed_improved": 2,
        "followed_no_change": 0,
        "followed_unknown": 0,
        "not_followed": 1,
    }
    assert running == {
        "total": 2,
        "followed_improved": 1,
        "followed_no_change": 1,
        "followed_unknown": 0,
        "not_followed": 0,
    }
    # Mixed-domain data never leaks: the two per-domain totals sum to the
    # unfiltered total, and neither overlaps the other's category counts.
    assert recovery["total"] + running["total"] == len(outcomes)


def test_summary_with_unknown_domain_filter_returns_zeroed_counts():
    outcomes = [
        _outcome(1, "recovery", followed=True, improved=True),
        _outcome(2, "running", followed=True, improved=True),
    ]
    summary = summarize_review_history(outcomes, domain="sleep")  # not yet landed
    assert summary["total"] == 0
    for k in ("followed_improved", "followed_no_change", "followed_unknown", "not_followed"):
        assert summary[k] == 0


# ---------------------------------------------------------------------------
# CLI round-trip: running recommendation → DB projection carries domain
# ---------------------------------------------------------------------------


def test_cli_review_schedule_on_running_payload_projects_domain_running(
    tmp_path: Path, capsys
):
    """End-to-end: a running recommendation JSON feeds ``hai review schedule``
    and the DB ``review_event.domain`` is 'running', not the backfill default.

    The recommendation is manually INSERTed into ``recommendation_log``
    with ``domain='running'`` to satisfy the review_event FK. In
    production, ``hai synthesize`` is the write path for every domain's
    recommendations (v0.1.4 removed the legacy recovery-only
    ``hai writeback``). This keeps the test scoped to the review flow.
    """

    db = _init_db(tmp_path)
    base_dir = tmp_path / _WRITEBACK_ROOT_NAME
    base_dir.mkdir(parents=True)

    payload = _running_rec_payload()
    rec_file = tmp_path / "running_rec.json"
    rec_file.write_text(json.dumps(payload), encoding="utf-8")

    # Satisfy the review_event → recommendation_log FK by inserting the
    # running recommendation directly into the DB (mirrors what Phase 2's
    # atomic ``hai synthesize`` transaction would do once running flows
    # through synthesis).
    conn = open_connection(db)
    try:
        conn.execute(
            """
            INSERT INTO recommendation_log (
                recommendation_id, user_id, for_date, issued_at,
                action, confidence, bounded, payload_json,
                jsonl_offset, source, ingest_actor, agent_version,
                produced_at, validated_at, projected_at, domain
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["recommendation_id"],
                payload["user_id"],
                payload["for_date"],
                payload["issued_at"],
                payload["action"],
                payload["confidence"],
                1,
                json.dumps(payload, sort_keys=True),
                1,
                "claude_agent_v1",
                "claude_agent_v1",
                "claude_agent_v1",
                payload["issued_at"],
                NOW.isoformat(),
                NOW.isoformat(),
                "running",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    rc = cli_main([
        "review", "schedule",
        "--recommendation-json", str(rec_file),
        "--base-dir", str(base_dir),
        "--db-path", str(db),
    ])
    capsys.readouterr()
    assert rc == 0

    conn = open_connection(db)
    try:
        row = conn.execute(
            "SELECT review_event_id, domain FROM review_event WHERE review_event_id = ?",
            (payload["follow_up"]["review_event_id"],),
        ).fetchone()
        assert row is not None
        assert row["domain"] == "running"
    finally:
        conn.close()

    # JSONL audit also carries the domain.
    ev_line = (base_dir / "review_events.jsonl").read_text(encoding="utf-8").splitlines()[-1]
    assert json.loads(ev_line)["domain"] == "running"


def test_cli_review_record_on_running_payload_projects_domain_running(
    tmp_path: Path, capsys
):
    db = _init_db(tmp_path)
    base_dir = tmp_path / _WRITEBACK_ROOT_NAME
    base_dir.mkdir(parents=True)

    payload = _running_rec_payload(user="u_run2")
    rec_file = tmp_path / "running_rec.json"
    rec_file.write_text(json.dumps(payload), encoding="utf-8")

    conn = open_connection(db)
    try:
        conn.execute(
            """
            INSERT INTO recommendation_log (
                recommendation_id, user_id, for_date, issued_at,
                action, confidence, bounded, payload_json,
                jsonl_offset, source, ingest_actor, agent_version,
                produced_at, validated_at, projected_at, domain
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["recommendation_id"], payload["user_id"],
                payload["for_date"], payload["issued_at"],
                payload["action"], payload["confidence"], 1,
                json.dumps(payload, sort_keys=True), 1,
                "claude_agent_v1", "claude_agent_v1", "claude_agent_v1",
                payload["issued_at"], NOW.isoformat(), NOW.isoformat(),
                "running",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    cli_main([
        "review", "schedule",
        "--recommendation-json", str(rec_file),
        "--base-dir", str(base_dir),
        "--db-path", str(db),
    ])
    capsys.readouterr()

    outcome_payload = {
        "review_event_id": payload["follow_up"]["review_event_id"],
        "recommendation_id": payload["recommendation_id"],
        "user_id": payload["user_id"],
        "review_at": payload["follow_up"]["review_at"],
        "review_question": payload["follow_up"]["review_question"],
        "followed_recommendation": True,
        "self_reported_improvement": True,
        "free_text": "felt smooth",
        "recorded_at": REVIEW_AT.isoformat(),
        "domain": "running",
    }
    outcome_file = tmp_path / "running_outcome.json"
    outcome_file.write_text(json.dumps(outcome_payload), encoding="utf-8")

    rc = cli_main([
        "review", "record",
        "--outcome-json", str(outcome_file),
        "--base-dir", str(base_dir),
        "--db-path", str(db),
    ])
    capsys.readouterr()
    assert rc == 0

    conn = open_connection(db)
    try:
        row = conn.execute(
            "SELECT domain, followed_recommendation FROM review_outcome "
            "WHERE review_event_id = ?",
            (payload["follow_up"]["review_event_id"],),
        ).fetchone()
        assert row is not None
        assert row["domain"] == "running"
        assert row["followed_recommendation"] == 1
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CLI summary: mixed-domain JSONL + --domain filter
# ---------------------------------------------------------------------------


def _write_outcome_line(base: Path, user: str, suffix: str, *, domain: str,
                        followed: bool, improved) -> None:
    """Append a synthetic outcome JSONL row with the given domain."""

    payload = {
        "review_event_id": f"rev_{suffix}",
        "recommendation_id": f"rec_{suffix}",
        "user_id": user,
        "recorded_at": REVIEW_AT.isoformat(),
        "followed_recommendation": followed,
        "self_reported_improvement": improved,
        "free_text": None,
        "domain": domain,
    }
    (base / "review_outcomes.jsonl").open("a", encoding="utf-8").write(
        json.dumps(payload, sort_keys=True) + "\n"
    )


def test_cli_review_summary_splits_mixed_domains_under_domain_filter(
    tmp_path: Path, capsys
):
    base_dir = tmp_path / _WRITEBACK_ROOT_NAME
    base_dir.mkdir(parents=True)

    # 3 recovery + 2 running mixed in the same JSONL.
    _write_outcome_line(base_dir, "u_1", "rec_a", domain="recovery",
                        followed=True, improved=True)
    _write_outcome_line(base_dir, "u_1", "rec_b", domain="recovery",
                        followed=True, improved=True)
    _write_outcome_line(base_dir, "u_1", "rec_c", domain="recovery",
                        followed=False, improved=None)
    _write_outcome_line(base_dir, "u_1", "run_a", domain="running",
                        followed=True, improved=True)
    _write_outcome_line(base_dir, "u_1", "run_b", domain="running",
                        followed=True, improved=False)

    # No filter → all five counted.
    rc = cli_main([
        "review", "summary",
        "--base-dir", str(base_dir),
    ])
    all_out = capsys.readouterr().out
    assert rc == 0
    all_summary = json.loads(all_out)
    assert all_summary["total"] == 5

    # --domain recovery → only the three recovery rows.
    rc = cli_main([
        "review", "summary",
        "--base-dir", str(base_dir),
        "--domain", "recovery",
    ])
    rec_out = capsys.readouterr().out
    assert rc == 0
    rec_summary = json.loads(rec_out)
    assert rec_summary == {
        "total": 3,
        "followed_improved": 2,
        "followed_no_change": 0,
        "followed_unknown": 0,
        "not_followed": 1,
    }

    # --domain running → only the two running rows. No recovery leakage.
    rc = cli_main([
        "review", "summary",
        "--base-dir", str(base_dir),
        "--domain", "running",
    ])
    run_out = capsys.readouterr().out
    assert rc == 0
    run_summary = json.loads(run_out)
    assert run_summary == {
        "total": 2,
        "followed_improved": 1,
        "followed_no_change": 1,
        "followed_unknown": 0,
        "not_followed": 0,
    }

    # Invariant: per-domain totals sum to the unfiltered total. No domain
    # row is counted twice or dropped.
    assert rec_summary["total"] + run_summary["total"] == all_summary["total"]


def test_cli_review_summary_legacy_rows_without_domain_field_count_as_recovery(
    tmp_path: Path, capsys
):
    """Migration-003 backfilled existing rows to ``domain='recovery'``. The
    JSONL reader mirrors that default so pre-Phase-2 outcomes stay visible
    under ``--domain recovery`` without any file rewrite."""

    base_dir = tmp_path / _WRITEBACK_ROOT_NAME
    base_dir.mkdir(parents=True)

    legacy_payload = {
        "review_event_id": "rev_legacy",
        "recommendation_id": "rec_legacy",
        "user_id": "u_1",
        "recorded_at": REVIEW_AT.isoformat(),
        "followed_recommendation": True,
        "self_reported_improvement": True,
        "free_text": None,
        # intentionally no 'domain' field — pre-Phase-2 JSONL shape.
    }
    (base_dir / "review_outcomes.jsonl").write_text(
        json.dumps(legacy_payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rc = cli_main([
        "review", "summary",
        "--base-dir", str(base_dir),
        "--domain", "recovery",
    ])
    out = capsys.readouterr().out
    assert rc == 0
    assert json.loads(out)["total"] == 1

    rc = cli_main([
        "review", "summary",
        "--base-dir", str(base_dir),
        "--domain", "running",
    ])
    out = capsys.readouterr().out
    assert rc == 0
    assert json.loads(out)["total"] == 0
