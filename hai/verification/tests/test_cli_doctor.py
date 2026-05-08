"""M5 — hai doctor consolidation.

Pins the M5-added checks (sync-source freshness + today counts + DB
size) and the new output format toggle (``--json`` vs human text).
Tests for the pre-M5 doctor behavior (config / state_db / auth_garmin
/ skills / domains) live in ``test_cli_init_doctor.py`` — this file
only covers what M5 added.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from health_agent_infra import cli as cli_mod
from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.pull.auth import CredentialStore
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_proposal,
    project_review_event,
    project_review_outcome,
)
from health_agent_infra.core.schemas import (
    ReviewEvent,
    ReviewOutcome,
)


class _FakeKeyring:
    def __init__(self):
        self._data: dict[tuple[str, str], str] = {}

    def get_password(self, service, username):
        return self._data.get((service, username))

    def set_password(self, service, username, password):
        self._data[(service, username)] = password

    def delete_password(self, service, username):
        self._data.pop((service, username), None)


@pytest.fixture
def fake_store(monkeypatch):
    store = CredentialStore(backend=_FakeKeyring(), env={})
    monkeypatch.setattr(
        cli_mod.CredentialStore, "default", classmethod(lambda cls: store),
    )
    return store


def _doctor_argv(tmp_path: Path, *extra: str, json_output: bool = True) -> list[str]:
    argv = ["doctor"]
    if json_output:
        argv.append("--json")
    argv += [
        "--thresholds-path", str(tmp_path / "thresholds.toml"),
        "--db-path", str(tmp_path / "state.db"),
        "--skills-dest", str(tmp_path / "skills"),
    ]
    argv += list(extra)
    return argv


def _init_db_at(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


# ---------------------------------------------------------------------------
# sources freshness block
# ---------------------------------------------------------------------------


def test_doctor_sources_block_empty_on_fresh_db(tmp_path, capsys, fake_store):
    _init_db_at(tmp_path)
    rc = cli_main(_doctor_argv(tmp_path, "--user-id", "u_test"))
    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    sources = report["checks"]["sources"]
    assert sources["status"] == "ok"
    assert sources["sources"] == {}


def test_doctor_sources_block_reports_freshness_per_source(
    tmp_path, capsys, fake_store,
):
    db = _init_db_at(tmp_path)
    as_of = date(2026, 4, 17)

    conn = open_connection(db)
    try:
        conn.executemany(
            "INSERT INTO sync_run_log "
            "(source, user_id, mode, started_at, completed_at, status, "
            " rows_pulled, rows_accepted, duplicates_skipped) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("garmin", "u_test", "csv",
                 "2026-04-17T06:00:00+00:00", "2026-04-17T06:00:00+00:00",
                 "ok", 1, 1, 0),
                # A failed run must not surface.
                ("garmin", "u_test", "csv",
                 "2026-04-17T10:00:00+00:00", "2026-04-17T10:00:02+00:00",
                 "failed", None, None, None),
                ("nutrition_manual", "u_test", "manual",
                 "2026-04-17T20:00:00+00:00", "2026-04-17T20:00:00+00:00",
                 "ok", 1, 1, 0),
            ],
        )
        conn.commit()
    finally:
        conn.close()

    rc = cli_main(_doctor_argv(
        tmp_path, "--user-id", "u_test", "--as-of", as_of.isoformat(),
    ))
    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    sources = report["checks"]["sources"]["sources"]

    # Anchor = 2026-04-18 00:00 UTC. garmin @ 06:00 → 18h, nutrition @ 20:00 → 4h.
    assert set(sources.keys()) == {"garmin", "nutrition_manual"}
    assert sources["garmin"]["staleness_hours"] == 18.0
    assert sources["nutrition_manual"]["staleness_hours"] == 4.0


# ---------------------------------------------------------------------------
# today counts
# ---------------------------------------------------------------------------


def test_doctor_today_counts_zero_on_empty_db(tmp_path, capsys, fake_store):
    _init_db_at(tmp_path)
    rc = cli_main(_doctor_argv(
        tmp_path, "--user-id", "u_test", "--as-of", "2026-04-17",
    ))
    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    today = report["checks"]["today"]
    assert today["status"] == "ok"
    assert today["for_date"] == "2026-04-17"
    assert today["user_id"] == "u_test"
    assert today["proposals"] == 0
    assert today["recommendations"] == 0
    assert today["pending_reviews"] == 0


def test_doctor_today_counts_reflect_seeded_state(tmp_path, capsys, fake_store):
    """Seed one proposal, one recommendation, one unresolved review event,
    and one resolved review event. pending_reviews should be 1."""

    db = _init_db_at(tmp_path)
    as_of = "2026-04-17"
    review_at = datetime(2026, 4, 17, 8, tzinfo=timezone.utc)
    recorded_at = datetime(2026, 4, 17, 20, tzinfo=timezone.utc)

    proposal = {
        "schema_version": "domain_proposal.v1",
        "proposal_id": "prop_2026-04-17_u_test_recovery_01",
        "user_id": "u_test",
        "for_date": as_of,
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "action_detail": None,
        "rationale": ["x"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "ok"}],
        "bounded": True,
    }

    conn = open_connection(db)
    try:
        project_proposal(conn, proposal)
        # One recommendation (no daily_plan_id needed for count).
        conn.execute(
            "INSERT INTO recommendation_log ("
            "recommendation_id, user_id, for_date, issued_at, action, "
            "confidence, bounded, payload_json, jsonl_offset, source, "
            "ingest_actor, agent_version, produced_at, validated_at, "
            "projected_at, domain) VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("rec_a", "u_test", as_of, review_at.isoformat(),
             "proceed_with_planned_session", "high", 1, "{}", None,
             "manual", "manual", None, review_at.isoformat(),
             review_at.isoformat(), review_at.isoformat(), "recovery"),
        )
        # Second recommendation for the resolved review.
        conn.execute(
            "INSERT INTO recommendation_log ("
            "recommendation_id, user_id, for_date, issued_at, action, "
            "confidence, bounded, payload_json, jsonl_offset, source, "
            "ingest_actor, agent_version, produced_at, validated_at, "
            "projected_at, domain) VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("rec_b", "u_test", as_of, review_at.isoformat(),
             "proceed_with_planned_session", "high", 1, "{}", None,
             "manual", "manual", None, review_at.isoformat(),
             review_at.isoformat(), review_at.isoformat(), "recovery"),
        )
        pending_event = ReviewEvent(
            review_event_id="rev_pending",
            recommendation_id="rec_a",
            user_id="u_test",
            review_at=review_at,
            review_question="How did it feel?",
            domain="recovery",
        )
        resolved_event = ReviewEvent(
            review_event_id="rev_resolved",
            recommendation_id="rec_b",
            user_id="u_test",
            review_at=review_at,
            review_question="How did it feel?",
            domain="recovery",
        )
        project_review_event(conn, pending_event)
        project_review_event(conn, resolved_event)
        project_review_outcome(conn, ReviewOutcome(
            review_event_id="rev_resolved",
            recommendation_id="rec_b",
            user_id="u_test",
            recorded_at=recorded_at,
            followed_recommendation=True,
            self_reported_improvement=True,
            free_text=None,
            domain="recovery",
        ))
        conn.commit()
    finally:
        conn.close()

    rc = cli_main(_doctor_argv(
        tmp_path, "--user-id", "u_test", "--as-of", as_of,
    ))
    assert rc == 0
    today = json.loads(capsys.readouterr().out)["checks"]["today"]
    assert today["proposals"] == 1
    assert today["recommendations"] == 2
    # rev_pending has no outcome; rev_resolved does → exactly one pending.
    assert today["pending_reviews"] == 1


# ---------------------------------------------------------------------------
# DB size
# ---------------------------------------------------------------------------


def test_doctor_state_db_includes_size_bytes(tmp_path, capsys, fake_store):
    _init_db_at(tmp_path)
    rc = cli_main(_doctor_argv(tmp_path))
    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    db_check = report["checks"]["state_db"]
    assert "size_bytes" in db_check
    assert db_check["size_bytes"] > 0


# ---------------------------------------------------------------------------
# Human-readable default
# ---------------------------------------------------------------------------


def test_doctor_default_output_is_human_readable_text(tmp_path, capsys, fake_store):
    _init_db_at(tmp_path)
    rc = cli_main(_doctor_argv(tmp_path, json_output=False))
    assert rc == 0
    out = capsys.readouterr().out

    # It's not JSON — parsing as JSON must fail loudly.
    with pytest.raises(json.JSONDecodeError):
        json.loads(out)

    # Headings for every check present.
    for heading in (
        "## config", "## state_db", "## auth_garmin",
        "## skills", "## domains", "## sources", "## today",
    ):
        assert heading in out

    # Overall status is surfaced.
    assert "overall:" in out
