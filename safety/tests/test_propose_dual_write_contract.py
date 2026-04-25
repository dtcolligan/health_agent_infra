"""Regression test for v0.1.6 W15 / Codex C2: ``cmd_propose`` must
not silently report success when DB projection fails.

Background: the legacy code routed projection through
``_dual_write_project``, which catches every projector exception and
prints a stderr warning. cmd_propose then emitted success JSON and
returned OK regardless of whether SQLite was in sync. The audit chain
could fork: JSONL says "yes," SQLite says "no," CLI says "ok."

After v0.1.6:
  - DB-absent → success exit, ``db_projection_status="skipped_db_absent"``.
  - DB present + ``ProposalReplaceRequired`` → ``USER_INPUT`` with a
    "JSONL durable, DB out of sync" stderr.
  - DB present + any other projection failure → ``INTERNAL`` with the
    same out-of-sync stderr and a pointer to ``hai state reproject``.
  - Happy path → ``db_projection_status="ok"`` on the stdout payload.
"""

from __future__ import annotations

import json
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import initialize_database


_VALID_PROPOSAL = {
    "schema_version": "recovery_proposal.v1",
    "proposal_id": "prop_2026-04-25_u_test_recovery_01",
    "user_id": "u_test",
    "for_date": "2026-04-25",
    "domain": "recovery",
    "action": "proceed_with_planned_session",
    "action_detail": None,
    "rationale": ["test"],
    "confidence": "high",
    "uncertainty": [],
    "policy_decisions": [
        {"rule_id": "r1", "decision": "allow", "note": "n"},
    ],
    "bounded": True,
}


def _write_proposal(tmp_path: Path) -> str:
    p = tmp_path / "proposal.json"
    p.write_text(json.dumps(_VALID_PROPOSAL), encoding="utf-8")
    return str(p)


def test_propose_happy_path_emits_db_projection_status_ok(tmp_path):
    """v0.1.6: stdout payload carries `db_projection_status: "ok"` on
    successful dual-write so agents don't have to infer it from
    stderr."""

    db = tmp_path / "state.db"
    initialize_database(db)
    base_dir = tmp_path / "base"
    base_dir.mkdir()

    proposal_path = _write_proposal(tmp_path)
    out_buf = StringIO()
    from contextlib import redirect_stdout
    with redirect_stdout(out_buf):
        rc = cli_main([
            "propose",
            "--domain", "recovery",
            "--proposal-json", proposal_path,
            "--base-dir", str(base_dir),
            "--db-path", str(db),
        ])
    assert rc == exit_codes.OK
    payload = json.loads(out_buf.getvalue())
    assert payload["db_projection_status"] == "ok"


def test_propose_db_absent_succeeds_with_skipped_status(tmp_path):
    """When the state DB doesn't exist, propose still succeeds (JSONL
    is the audit boundary). The stdout payload carries
    `db_projection_status: "skipped_db_absent"` so the agent knows to
    expect a `hai state reproject` to reconcile later."""

    base_dir = tmp_path / "base"
    base_dir.mkdir()
    proposal_path = _write_proposal(tmp_path)

    out_buf = StringIO()
    err_buf = StringIO()
    from contextlib import redirect_stdout
    with redirect_stdout(out_buf), redirect_stderr(err_buf):
        rc = cli_main([
            "propose",
            "--domain", "recovery",
            "--proposal-json", proposal_path,
            "--base-dir", str(base_dir),
            "--db-path", str(tmp_path / "absent.db"),
        ])
    assert rc == exit_codes.OK
    payload = json.loads(out_buf.getvalue())
    assert payload["db_projection_status"] == "skipped_db_absent"
    assert "JSONL audit record is durable" in err_buf.getvalue()


def test_propose_fails_loudly_when_projection_raises(tmp_path, monkeypatch):
    """A projector exception other than ProposalReplaceRequired must
    NOT be silently swallowed. The CLI returns INTERNAL with a clear
    message naming the JSONL path + suggesting `hai state reproject`."""

    db = tmp_path / "state.db"
    initialize_database(db)
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    proposal_path = _write_proposal(tmp_path)

    # Force project_proposal to raise an unexpected error. cmd_propose
    # imports it lazily via `from health_agent_infra.core.state import
    # project_proposal` at the top of the function, so we patch the
    # attribute on `core.state.__init__` (the binding the function-local
    # import resolves through).
    import health_agent_infra.core.state as state_pkg

    def _broken_project(conn, data, *, replace=False):
        raise RuntimeError("simulated projection failure")

    monkeypatch.setattr(state_pkg, "project_proposal", _broken_project)

    err_buf = StringIO()
    with redirect_stderr(err_buf):
        rc = cli_main([
            "propose",
            "--domain", "recovery",
            "--proposal-json", proposal_path,
            "--base-dir", str(base_dir),
            "--db-path", str(db),
        ])
    assert rc == exit_codes.INTERNAL
    stderr = err_buf.getvalue()
    assert "DB projection FAILED" in stderr
    assert "RuntimeError" in stderr
    assert "hai state reproject" in stderr
    # JSONL was already written before projection — that's intentional
    # per the durable-audit contract; the user can recover via reproject.
    assert (base_dir / "recovery_proposals.jsonl").exists()


def test_propose_race_path_replace_required_after_preflight(tmp_path, monkeypatch):
    """v0.1.7 W26: regression for the race window where the pre-flight
    canonical-leaf check passes (no existing leaf) but `project_proposal`
    raises `ProposalReplaceRequired` from a concurrent writer between
    pre-flight and projection. The handler must surface USER_INPUT with a
    clear "JSONL durable, run --replace or reproject" stderr — not
    silently log success."""

    from health_agent_infra.cli import main as cli_main
    from health_agent_infra.core import exit_codes
    from health_agent_infra.core.state import (
        ProposalReplaceRequired,
        initialize_database,
    )
    import health_agent_infra.core.state as state_pkg

    db = tmp_path / "state.db"
    initialize_database(db)
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    proposal_path = _write_proposal(tmp_path)

    def _race_project(conn, data, *, replace=False):
        # Simulates the concurrent-writer race: pre-flight saw no leaf,
        # but by the time projection runs, another writer has landed
        # one. Without --replace, project_proposal must refuse with the
        # same exception shape it would raise in the real concurrent path.
        raise ProposalReplaceRequired(
            for_date=data["for_date"],
            user_id=data["user_id"],
            domain=data["domain"],
            leaf_proposal_id="prop_concurrent_writer",
            leaf_revision=1,
        )

    monkeypatch.setattr(state_pkg, "project_proposal", _race_project)

    err_buf = StringIO()
    with redirect_stderr(err_buf):
        rc = cli_main([
            "propose",
            "--domain", "recovery",
            "--proposal-json", proposal_path,
            "--base-dir", str(base_dir),
            "--db-path", str(db),
        ])
    assert rc == exit_codes.USER_INPUT
    stderr = err_buf.getvalue()
    assert "ProposalReplaceRequired" in stderr
    assert "concurrent writer" in stderr or "race" in stderr
    assert "--replace" in stderr or "reproject" in stderr
    # JSONL was already written before projection — that's intentional
    # per the durable-audit contract; the user can recover.
    assert (base_dir / "recovery_proposals.jsonl").exists()
