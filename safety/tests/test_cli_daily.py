"""Tests for ``hai daily`` (Phase 7 step 1).

``hai daily`` is an orchestration surface over the existing runtime:

    pull → clean → snapshot → proposal-gate → synthesize → schedule reviews

The gate is the agent seam — skills stay judgment-only, so when
``proposal_log`` is empty for ``(for_date, user_id)`` the command exits 0
with ``overall_status=awaiting_proposals`` rather than fabricating
proposals. These tests pin:

- Argument rejection (unknown ``--domains`` tokens, missing state DB).
- The awaiting-proposals branch.
- The full 6-domain happy path (synthesize + review scheduling landing
  real rows in real tables and JSONL).
- ``--domains`` narrows the gate-report expected set only; it does not
  filter synthesis.
- ``--skip-pull`` bypasses the Garmin adapter entirely (so the command
  is usable offline once proposals are in place).
- Rerun idempotency — scheduling is safe under replay.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_proposal,
)
from health_agent_infra.core.writeback.proposal import (
    PROPOSAL_SCHEMA_VERSIONS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

AS_OF = "2026-04-17"
USER_ID = "u_local_1"


# v1 domain → default action + schema. Kept in lockstep with
# ``core.writeback.proposal.DOMAIN_ACTION_ENUMS``; re-used across tests so a
# new default action gets rolled out in one place.
_DOMAIN_DEFAULTS: dict[str, str] = {
    "recovery": "proceed_with_planned_session",
    "running": "proceed_with_planned_run",
    "sleep": "maintain_schedule",
    "stress": "maintain_routine",
    "strength": "proceed_with_planned_session",
    "nutrition": "maintain_targets",
}


def _fresh_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return db_path


def _proposal_for(domain: str, **overrides) -> dict:
    base = {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS[domain],
        "proposal_id": f"prop_{AS_OF}_{USER_ID}_{domain}_01",
        "user_id": USER_ID,
        "for_date": AS_OF,
        "domain": domain,
        "action": _DOMAIN_DEFAULTS[domain],
        "action_detail": None,
        "rationale": [f"{domain}_baseline"],
        "confidence": "moderate",
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": "r_baseline", "decision": "allow", "note": "ok"},
        ],
        "bounded": True,
    }
    base.update(overrides)
    return base


def _seed_proposals(db_path: Path, domains: list[str]) -> list[dict]:
    """Insert one proposal per domain into ``proposal_log``."""

    proposals = [_proposal_for(d) for d in domains]
    conn = open_connection(db_path)
    try:
        for p in proposals:
            project_proposal(conn, p)
    finally:
        conn.close()
    return proposals


def _run_daily(*extra_argv: str) -> int:
    return cli_main(["daily", *extra_argv])


def _stdout_json(capsys) -> dict:
    out = capsys.readouterr().out
    # The CLI emits exactly one JSON document on stdout per run.
    return json.loads(out)


# ---------------------------------------------------------------------------
# Rejection paths
# ---------------------------------------------------------------------------


def test_daily_rejects_unknown_domain_subset(tmp_path, capsys, monkeypatch):
    db_path = _fresh_db(tmp_path)
    monkeypatch.setenv("HAI_STATE_DB", str(db_path))

    rc = _run_daily(
        "--base-dir", str(tmp_path / "out"),
        "--as-of", AS_OF,
        "--user-id", USER_ID,
        "--db-path", str(db_path),
        "--skip-pull",
        "--domains", "recovery,sleep,bogus",
    )
    captured = capsys.readouterr()
    assert rc == exit_codes.USER_INPUT
    assert "bogus" in captured.err
    assert "unsupported --domains" in captured.err


def test_daily_rejects_missing_db(tmp_path, capsys, monkeypatch):
    db_path = tmp_path / "does_not_exist.db"
    monkeypatch.setenv("HAI_STATE_DB", str(db_path))

    rc = _run_daily(
        "--base-dir", str(tmp_path / "out"),
        "--as-of", AS_OF,
        "--user-id", USER_ID,
        "--db-path", str(db_path),
        "--skip-pull",
    )
    captured = capsys.readouterr()
    assert rc == exit_codes.USER_INPUT
    assert "hai state init" in captured.err


# ---------------------------------------------------------------------------
# Agent seam — empty proposal_log stops the orchestrator gracefully
# ---------------------------------------------------------------------------


def test_daily_awaits_proposals_when_none_present(tmp_path, capsys, monkeypatch):
    db_path = _fresh_db(tmp_path)
    monkeypatch.setenv("HAI_STATE_DB", str(db_path))
    base_dir = tmp_path / "out"

    rc = _run_daily(
        "--base-dir", str(base_dir),
        "--as-of", AS_OF,
        "--user-id", USER_ID,
        "--db-path", str(db_path),
        "--skip-pull",
    )
    report = _stdout_json(capsys)

    assert rc == 0
    assert report["overall_status"] == "awaiting_proposals"
    assert report["stages"]["proposal_gate"]["status"] == "awaiting_proposals"
    assert report["stages"]["proposal_gate"]["present"] == []
    assert set(report["stages"]["proposal_gate"]["missing"]) == {
        "recovery", "running", "sleep", "stress", "strength", "nutrition",
    }
    assert report["stages"]["synthesize"]["status"] == "skipped_awaiting_proposals"
    assert report["stages"]["reviews"]["status"] == "skipped"
    # No recommendations committed → no JSONL review events either.
    assert not (base_dir / "review_events.jsonl").exists()


# ---------------------------------------------------------------------------
# Full 6-domain happy path — real synthesis, real review scheduling
# ---------------------------------------------------------------------------


def test_daily_orchestrates_6_domains_happy_path(tmp_path, capsys, monkeypatch):
    db_path = _fresh_db(tmp_path)
    monkeypatch.setenv("HAI_STATE_DB", str(db_path))
    base_dir = tmp_path / "out"

    all_domains = ["recovery", "running", "sleep", "stress", "strength", "nutrition"]
    seeded = _seed_proposals(db_path, all_domains)

    rc = _run_daily(
        "--base-dir", str(base_dir),
        "--as-of", AS_OF,
        "--user-id", USER_ID,
        "--db-path", str(db_path),
        "--skip-pull",
    )
    report = _stdout_json(capsys)

    assert rc == 0, report
    assert report["overall_status"] == "complete"
    assert report["stages"]["pull"]["status"] == "skipped"
    assert report["stages"]["clean"]["status"] == "skipped"
    assert report["stages"]["snapshot"]["status"] == "ran"
    gate = report["stages"]["proposal_gate"]
    assert gate["status"] == "complete"
    assert set(gate["present"]) == set(all_domains)
    assert gate["missing"] == []

    synthesize = report["stages"]["synthesize"]
    assert synthesize["status"] == "ran"
    assert len(synthesize["recommendation_ids"]) == 6
    assert set(synthesize["proposal_ids"]) == {p["proposal_id"] for p in seeded}

    reviews = report["stages"]["reviews"]
    assert reviews["status"] == "ran"
    assert len(reviews["scheduled_event_ids"]) == 6

    # Real rows landed in the DB — one daily_plan, six recommendations,
    # six review_events — not just a JSON report.
    conn = open_connection(db_path)
    try:
        plan_count = conn.execute(
            "SELECT COUNT(*) AS c FROM daily_plan WHERE for_date = ? AND user_id = ?",
            (AS_OF, USER_ID),
        ).fetchone()["c"]
        assert plan_count == 1

        rec_domains = [
            r["domain"]
            for r in conn.execute(
                "SELECT domain FROM recommendation_log "
                "WHERE json_extract(payload_json, '$.for_date') = ? "
                "AND json_extract(payload_json, '$.user_id') = ?",
                (AS_OF, USER_ID),
            ).fetchall()
        ]
        assert set(rec_domains) == set(all_domains)

        review_rows = conn.execute(
            "SELECT review_event_id, domain FROM review_event "
            "WHERE user_id = ?",
            (USER_ID,),
        ).fetchall()
        assert len(review_rows) == 6
        assert {r["domain"] for r in review_rows} == set(all_domains)
    finally:
        conn.close()

    # JSONL audit — review_events.jsonl should have six lines.
    events_path = base_dir / "review_events.jsonl"
    assert events_path.exists()
    lines = [
        line for line in events_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(lines) == 6


# ---------------------------------------------------------------------------
# Domain subset affects the gate report, not synthesis
# ---------------------------------------------------------------------------


def test_daily_domain_subset_narrows_gate_report(tmp_path, capsys, monkeypatch):
    db_path = _fresh_db(tmp_path)
    monkeypatch.setenv("HAI_STATE_DB", str(db_path))
    base_dir = tmp_path / "out"

    # Seed only two proposals — recovery + running.
    _seed_proposals(db_path, ["recovery", "running"])

    rc = _run_daily(
        "--base-dir", str(base_dir),
        "--as-of", AS_OF,
        "--user-id", USER_ID,
        "--db-path", str(db_path),
        "--skip-pull",
        "--domains", "recovery,sleep",
    )
    report = _stdout_json(capsys)

    assert rc == 0, report
    gate = report["stages"]["proposal_gate"]
    assert gate["expected"] == ["recovery", "sleep"]
    # Present lists what actually landed, not what was expected.
    assert gate["present"] == ["recovery", "running"]
    # Missing is restricted to the --domains subset; 'running' does not
    # appear here despite being outside the subset.
    assert gate["missing"] == ["sleep"]

    # Synthesis still ran because proposals were present — but over both
    # recovery AND running, not just the subset. --domains is a report
    # filter, not a synthesis filter.
    synthesize = report["stages"]["synthesize"]
    assert synthesize["status"] == "ran"
    assert len(synthesize["recommendation_ids"]) == 2


# ---------------------------------------------------------------------------
# --skip-pull actually skips the Garmin adapter
# ---------------------------------------------------------------------------


def test_daily_skip_pull_bypasses_pull_adapter(tmp_path, capsys, monkeypatch):
    db_path = _fresh_db(tmp_path)
    monkeypatch.setenv("HAI_STATE_DB", str(db_path))
    base_dir = tmp_path / "out"
    _seed_proposals(db_path, ["recovery"])

    from health_agent_infra import cli as cli_mod

    calls: list[str] = []

    def _should_not_be_called(*_a, **_kw):
        calls.append("adapter.load")
        raise AssertionError("--skip-pull must not instantiate the pull adapter")

    # Stub both the CSV and live adapter entry points so any accidental
    # pull call blows up loudly.
    monkeypatch.setattr(
        cli_mod, "GarminRecoveryReadinessAdapter", _should_not_be_called,
    )
    monkeypatch.setattr(
        cli_mod, "_build_live_adapter", _should_not_be_called,
    )

    rc = _run_daily(
        "--base-dir", str(base_dir),
        "--as-of", AS_OF,
        "--user-id", USER_ID,
        "--db-path", str(db_path),
        "--skip-pull",
    )
    report = _stdout_json(capsys)

    assert rc == 0, report
    assert calls == []
    assert report["stages"]["pull"]["status"] == "skipped"
    assert report["stages"]["clean"]["status"] == "skipped"


# ---------------------------------------------------------------------------
# Rerun idempotency — review scheduling survives replay cleanly
# ---------------------------------------------------------------------------


def test_daily_rerun_is_idempotent_on_review_events(tmp_path, capsys, monkeypatch):
    db_path = _fresh_db(tmp_path)
    monkeypatch.setenv("HAI_STATE_DB", str(db_path))
    base_dir = tmp_path / "out"
    _seed_proposals(db_path, ["recovery", "sleep"])

    argv = [
        "--base-dir", str(base_dir),
        "--as-of", AS_OF,
        "--user-id", USER_ID,
        "--db-path", str(db_path),
        "--skip-pull",
    ]

    assert _run_daily(*argv) == 0
    _ = capsys.readouterr()
    assert _run_daily(*argv) == 0
    report2 = _stdout_json(capsys)

    assert report2["overall_status"] == "complete"
    # After replay, still exactly two scheduled events; JSONL stayed at
    # two lines (idempotent on review_event_id).
    assert len(report2["stages"]["reviews"]["scheduled_event_ids"]) == 2

    events_path = base_dir / "review_events.jsonl"
    lines = [
        line for line in events_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(lines) == 2

    # DB also settles to exactly two review events, and a single canonical
    # daily_plan (synthesis replaced atomically on rerun).
    conn = open_connection(db_path)
    try:
        plan_count = conn.execute(
            "SELECT COUNT(*) AS c FROM daily_plan WHERE for_date = ? AND user_id = ?",
            (AS_OF, USER_ID),
        ).fetchone()["c"]
        assert plan_count == 1
        review_count = conn.execute(
            "SELECT COUNT(*) AS c FROM review_event WHERE user_id = ?",
            (USER_ID,),
        ).fetchone()["c"]
        assert review_count == 2
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# D3 §hai daily hint — TTY-aware stderr pointer to `hai today`
# ---------------------------------------------------------------------------


def test_daily_emits_hai_today_hint_on_tty_stderr(tmp_path, capsys, monkeypatch):
    """When stderr is an interactive TTY, `hai daily` appends a one-line
    hint pointing at `hai today` so new users discover the user surface
    without having to read docs.
    """

    import sys as _sys

    db_path = _fresh_db(tmp_path)
    monkeypatch.setenv("HAI_STATE_DB", str(db_path))
    base_dir = tmp_path / "out"
    _seed_proposals(db_path, ["recovery"])

    monkeypatch.setattr(_sys.stderr, "isatty", lambda: True)

    rc = _run_daily(
        "--base-dir", str(base_dir),
        "--as-of", AS_OF,
        "--user-id", USER_ID,
        "--db-path", str(db_path),
        "--skip-pull",
        "--domains", "recovery",
    )
    captured = capsys.readouterr()

    assert rc == 0
    assert "hai today" in captured.err
    assert f"--as-of {AS_OF}" in captured.err
    assert f"--user-id {USER_ID}" in captured.err
    # Stdout JSON stays byte-stable regardless of TTY.
    report = json.loads(captured.out)
    assert report["overall_status"] == "complete"


def test_daily_omits_hint_on_non_tty_stderr(tmp_path, capsys, monkeypatch):
    """Scripted / piped callers (including CI, pytest) must get
    byte-stable stderr — no hint when stderr isn't a TTY.
    """

    db_path = _fresh_db(tmp_path)
    monkeypatch.setenv("HAI_STATE_DB", str(db_path))
    base_dir = tmp_path / "out"
    _seed_proposals(db_path, ["recovery"])

    # Default capsys = non-TTY; no monkeypatching needed. Confirm for clarity.
    import sys as _sys
    assert not _sys.stderr.isatty()

    rc = _run_daily(
        "--base-dir", str(base_dir),
        "--as-of", AS_OF,
        "--user-id", USER_ID,
        "--db-path", str(db_path),
        "--skip-pull",
        "--domains", "recovery",
    )
    captured = capsys.readouterr()

    assert rc == 0
    assert "hai today" not in captured.err
