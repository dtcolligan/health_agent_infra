"""Runtime-mode isolation checks for scaffold ablations."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.hermetic import (
    HAI_BASE_DIR_ENV,
    HAI_HERMETIC_ENV,
    HAI_STATE_DB_ENV,
)
from health_agent_infra.core.refusal import (
    HAI_INVOCATION_CONTEXT_ENV,
    INVOCATION_CONTEXT_AGENT,
)
from health_agent_infra.core.runtime_mode import (
    HAI_RUNTIME_MODE_ENV,
    NO_AGENT_SAFE,
    NO_AUDIT_CHAIN,
    NO_PROPOSAL_GATE,
    NO_REFUSAL,
    NO_VALIDATION,
)
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_proposal,
)
from health_agent_infra.core.synthesis import run_synthesis
from health_agent_infra.core.writeback.proposal import PROPOSAL_SCHEMA_VERSIONS


FOR_DATE = date(2026, 5, 10)
USER_ID = "u_runtime_modes"


def _run_cli(argv: list[str]) -> tuple[int, str, str]:
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        rc = cli_main(argv)
    return rc, stdout_buf.getvalue(), stderr_buf.getvalue()


def _recovery_proposal(**overrides) -> dict:
    proposal = {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS["recovery"],
        "proposal_id": f"prop_{FOR_DATE.isoformat()}_{USER_ID}_recovery_01",
        "user_id": USER_ID,
        "for_date": FOR_DATE.isoformat(),
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "action_detail": None,
        "rationale": ["runtime-mode fixture"],
        "confidence": "moderate",
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": "fixture", "decision": "allow", "note": "ok"},
        ],
        "bounded": True,
    }
    proposal.update(overrides)
    return proposal


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _quiet_snapshot() -> dict:
    return {
        "recovery": {
            "classified_state": {"sleep_debt_band": "none"},
            "today": {"acwr_ratio": 1.0},
        },
        "running": {},
        "sleep": {},
        "stress": {},
        "strength": {},
        "nutrition": {},
    }


def test_no_agent_safe_does_not_disable_proposal_validation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    bad_proposal = tmp_path / "bad_proposal.json"
    bad_proposal.write_text('{"schema_version": "bad"}', encoding="utf-8")
    monkeypatch.setenv(HAI_INVOCATION_CONTEXT_ENV, INVOCATION_CONTEXT_AGENT)
    monkeypatch.setenv(HAI_RUNTIME_MODE_ENV, NO_AGENT_SAFE)
    monkeypatch.setenv(HAI_HERMETIC_ENV, "1")
    monkeypatch.setenv(HAI_STATE_DB_ENV, str(tmp_path / "state.db"))
    monkeypatch.setenv(HAI_BASE_DIR_ENV, str(tmp_path / "base"))

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        rc = cli_main([
            "propose",
            "--domain",
            "recovery",
            "--proposal-json",
            str(bad_proposal),
            "--base-dir",
            str(tmp_path / "base"),
            "--db-path",
            str(tmp_path / "state.db"),
        ])

    assert rc == exit_codes.USER_INPUT
    assert stdout_buf.getvalue() == ""
    err = stderr_buf.getvalue()
    assert "mechanism_disabled_marker.v1" not in err
    assert "propose rejected: invariant=required_fields_present" in err


def test_no_validation_allows_stale_schema_proposal_with_marker(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    proposal_path = tmp_path / "stale_proposal.json"
    base_dir = tmp_path / "base"
    db_path = tmp_path / "state.db"
    _write_json(
        proposal_path,
        _recovery_proposal(schema_version="recovery_proposal.v0"),
    )
    monkeypatch.setenv(HAI_RUNTIME_MODE_ENV, NO_VALIDATION)
    monkeypatch.setenv(HAI_HERMETIC_ENV, "1")
    monkeypatch.setenv(HAI_STATE_DB_ENV, str(db_path))
    monkeypatch.setenv(HAI_BASE_DIR_ENV, str(base_dir))

    rc, stdout, stderr = _run_cli([
        "propose",
        "--domain",
        "recovery",
        "--proposal-json",
        str(proposal_path),
        "--base-dir",
        str(base_dir),
        "--db-path",
        str(db_path),
    ])

    assert rc == exit_codes.OK
    assert json.loads(stdout)["db_projection_status"] == "skipped_db_absent"
    marker = json.loads(stderr.splitlines()[0])
    assert marker["mechanism"] == "validation"
    assert marker["runtime_mode"] == NO_VALIDATION
    assert marker["details"]["invariant"] == "schema_version"
    assert (base_dir / "recovery_proposals.jsonl").exists()


def test_no_validation_does_not_disable_refusal_boundary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    proposal_path = tmp_path / "clinical_proposal.json"
    base_dir = tmp_path / "base"
    db_path = tmp_path / "state.db"
    _write_json(
        proposal_path,
        _recovery_proposal(rationale=["This fixture mentions diagnosis."]),
    )
    monkeypatch.setenv(HAI_RUNTIME_MODE_ENV, NO_VALIDATION)
    monkeypatch.setenv(HAI_HERMETIC_ENV, "1")
    monkeypatch.setenv(HAI_STATE_DB_ENV, str(db_path))
    monkeypatch.setenv(HAI_BASE_DIR_ENV, str(base_dir))

    rc, stdout, stderr = _run_cli([
        "propose",
        "--domain",
        "recovery",
        "--proposal-json",
        str(proposal_path),
        "--base-dir",
        str(base_dir),
        "--db-path",
        str(db_path),
    ])

    assert rc == exit_codes.USER_INPUT
    assert stdout == ""
    assert "invariant=no_banned_tokens" in stderr
    assert "mechanism_disabled_marker.v1" not in stderr


def test_no_refusal_does_not_disable_schema_validation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    proposal_path = tmp_path / "stale_proposal.json"
    base_dir = tmp_path / "base"
    db_path = tmp_path / "state.db"
    _write_json(
        proposal_path,
        _recovery_proposal(schema_version="recovery_proposal.v0"),
    )
    monkeypatch.setenv(HAI_RUNTIME_MODE_ENV, NO_REFUSAL)
    monkeypatch.setenv(HAI_HERMETIC_ENV, "1")
    monkeypatch.setenv(HAI_STATE_DB_ENV, str(db_path))
    monkeypatch.setenv(HAI_BASE_DIR_ENV, str(base_dir))

    rc, stdout, stderr = _run_cli([
        "propose",
        "--domain",
        "recovery",
        "--proposal-json",
        str(proposal_path),
        "--base-dir",
        str(base_dir),
        "--db-path",
        str(db_path),
    ])

    assert rc == exit_codes.USER_INPUT
    assert stdout == ""
    assert "invariant=schema_version" in stderr
    assert "mechanism_disabled_marker.v1" not in stderr


def test_no_proposal_gate_bypasses_w57_but_not_dispatch_agent_safe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv(HAI_RUNTIME_MODE_ENV, NO_PROPOSAL_GATE)
    monkeypatch.setenv(HAI_HERMETIC_ENV, "1")
    monkeypatch.setenv(HAI_STATE_DB_ENV, str(tmp_path / "state.db"))
    monkeypatch.setenv(HAI_BASE_DIR_ENV, str(tmp_path / "base"))

    rc, stdout, stderr = _run_cli([
        "intent",
        "commit",
        "--intent-id",
        "intent_fixture_1",
    ])

    assert rc == exit_codes.USER_INPUT
    assert stdout == ""
    first_line, rest = stderr.split("\n", 1)
    marker = json.loads(first_line)
    assert marker["mechanism"] == "proposal_gate"
    assert marker["runtime_mode"] == NO_PROPOSAL_GATE
    assert "no state DB" in rest

    monkeypatch.setenv(HAI_INVOCATION_CONTEXT_ENV, INVOCATION_CONTEXT_AGENT)

    rc, stdout, stderr = _run_cli([
        "intent",
        "commit",
        "--intent-id",
        "intent_fixture_1",
    ])

    assert rc == exit_codes.USER_INPUT
    assert stdout == ""
    envelope = json.loads(stderr)
    assert envelope["refusal_kind"] == "agent_safe_violation"
    assert envelope["mechanism"] == "agent_safe"


def test_no_audit_chain_suppresses_evidence_cards_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    monkeypatch.setenv(HAI_RUNTIME_MODE_ENV, NO_AUDIT_CHAIN)
    monkeypatch.setenv(HAI_HERMETIC_ENV, "1")
    monkeypatch.setenv(HAI_STATE_DB_ENV, str(db_path))
    monkeypatch.setenv(HAI_BASE_DIR_ENV, str(tmp_path / "base"))

    conn = open_connection(db_path)
    try:
        project_proposal(conn, _recovery_proposal())
        result = run_synthesis(
            conn,
            for_date=FOR_DATE,
            user_id=USER_ID,
            snapshot=_quiet_snapshot(),
        )
        rec_count = conn.execute(
            "SELECT COUNT(*) FROM recommendation_log WHERE user_id = ?",
            (USER_ID,),
        ).fetchone()[0]
        card_count = conn.execute(
            "SELECT COUNT(*) FROM recommendation_evidence_card WHERE user_id = ?",
            (USER_ID,),
        ).fetchone()[0]
    finally:
        conn.close()

    assert rec_count == 1
    assert card_count == 0
    assert [m["mechanism"] for m in result.mechanism_disabled_markers] == [
        "audit_chain"
    ]
    assert result.mechanism_disabled_markers[0]["runtime_mode"] == NO_AUDIT_CHAIN
