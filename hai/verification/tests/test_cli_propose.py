"""End-to-end tests for ``hai propose`` (Phase 2 step 4).

Covers:

- Validation: domain enum, action enum, schema_version, confidence, bounded,
  policy_decisions, forbidden fields (``follow_up`` / ``daily_plan_id``).
- Writeback: JSONL append to ``<base_dir>/<domain>_proposals.jsonl``.
- Idempotency: re-running with the same proposal_id is a no-op.
- DB projection: row lands in ``proposal_log`` with the right columns.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)
from health_agent_infra.core.writeback.proposal import (
    PROPOSAL_SCHEMA_VERSIONS,
    ProposalValidationError,
    perform_proposal_writeback,
    validate_proposal_dict,
)


def _valid_running_proposal(**overrides):
    base = {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS["running"],
        "proposal_id": "prop_2026-04-17_u_local_1_running_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-17",
        "domain": "running",
        "action": "proceed_with_planned_run",
        "action_detail": None,
        "rationale": ["weekly_mileage_trend=moderate"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Validator unit tests
# ---------------------------------------------------------------------------

def test_validate_accepts_valid_running_proposal():
    validate_proposal_dict(_valid_running_proposal(), expected_domain="running")


def test_validate_rejects_follow_up_field():
    prop = _valid_running_proposal()
    prop["follow_up"] = {"review_at": "x"}
    with pytest.raises(ProposalValidationError) as exc:
        validate_proposal_dict(prop)
    assert exc.value.invariant == "forbidden_fields_absent"


def test_validate_rejects_daily_plan_id_field():
    prop = _valid_running_proposal()
    prop["daily_plan_id"] = "plan_2026-04-17_u_local_1"
    with pytest.raises(ProposalValidationError) as exc:
        validate_proposal_dict(prop)
    assert exc.value.invariant == "forbidden_fields_absent"


def test_validate_rejects_domain_mismatch_against_expected():
    prop = _valid_running_proposal()
    with pytest.raises(ProposalValidationError) as exc:
        validate_proposal_dict(prop, expected_domain="recovery")
    assert exc.value.invariant == "domain_match"


def test_validate_rejects_unsupported_domain():
    # ``cycling`` is not in v1 SUPPORTED_DOMAINS; strength was promoted to
    # a full proposal-submitting domain in the Phase 7 closure commit, so
    # this test needs a genuinely-never-supported placeholder.
    prop = _valid_running_proposal(domain="cycling")
    with pytest.raises(ProposalValidationError) as exc:
        validate_proposal_dict(prop)
    assert exc.value.invariant == "domain_supported"


def test_validate_rejects_action_outside_running_enum():
    prop = _valid_running_proposal(action="proceed_with_planned_session")
    with pytest.raises(ProposalValidationError) as exc:
        validate_proposal_dict(prop)
    assert exc.value.invariant == "action_enum"


def test_validate_rejects_schema_version_mismatch():
    prop = _valid_running_proposal(schema_version="running_proposal.v2")
    with pytest.raises(ProposalValidationError) as exc:
        validate_proposal_dict(prop)
    assert exc.value.invariant == "schema_version"


def test_validate_rejects_missing_required_field():
    prop = _valid_running_proposal()
    del prop["rationale"]
    with pytest.raises(ProposalValidationError) as exc:
        validate_proposal_dict(prop)
    assert exc.value.invariant == "required_fields_present"


def test_validate_rejects_bad_confidence():
    prop = _valid_running_proposal(confidence="certain")
    with pytest.raises(ProposalValidationError) as exc:
        validate_proposal_dict(prop)
    assert exc.value.invariant == "confidence_enum"


def test_validate_rejects_bounded_false():
    prop = _valid_running_proposal(bounded=False)
    with pytest.raises(ProposalValidationError) as exc:
        validate_proposal_dict(prop)
    assert exc.value.invariant == "bounded_true"


def test_validate_rejects_empty_policy_decisions():
    prop = _valid_running_proposal(policy_decisions=[])
    with pytest.raises(ProposalValidationError) as exc:
        validate_proposal_dict(prop)
    assert exc.value.invariant == "policy_decisions_present"


def test_validate_rejects_non_iso_for_date():
    prop = _valid_running_proposal(for_date="17 April 2026")
    with pytest.raises(ProposalValidationError) as exc:
        validate_proposal_dict(prop)
    assert exc.value.invariant == "for_date_iso"


# ---------------------------------------------------------------------------
# Writeback layer: JSONL append + idempotency
# ---------------------------------------------------------------------------

def test_writeback_appends_to_per_domain_jsonl(tmp_path):
    prop = _valid_running_proposal()
    record = perform_proposal_writeback(prop, base_dir=tmp_path)
    assert Path(record.writeback_path).name == "running_proposals.jsonl"
    lines = Path(record.writeback_path).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["proposal_id"] == prop["proposal_id"]


def test_writeback_is_idempotent_on_proposal_id(tmp_path):
    prop = _valid_running_proposal()
    perform_proposal_writeback(prop, base_dir=tmp_path)
    perform_proposal_writeback(prop, base_dir=tmp_path)  # rerun
    lines = (tmp_path / "running_proposals.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


def test_writeback_uses_separate_files_per_domain(tmp_path):
    running = _valid_running_proposal()
    recovery = _valid_running_proposal(
        schema_version=PROPOSAL_SCHEMA_VERSIONS["recovery"],
        proposal_id="prop_2026-04-17_u_local_1_recovery_01",
        domain="recovery",
        action="proceed_with_planned_session",
    )
    perform_proposal_writeback(running, base_dir=tmp_path)
    perform_proposal_writeback(recovery, base_dir=tmp_path)

    assert (tmp_path / "running_proposals.jsonl").exists()
    assert (tmp_path / "recovery_proposals.jsonl").exists()


# ---------------------------------------------------------------------------
# End-to-end via the CLI subprocess: validation + JSONL + DB row
# ---------------------------------------------------------------------------

def _run_cli(*args, env_extras=None):
    env = {"PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src")}
    if env_extras:
        env.update(env_extras)
    return subprocess.run(
        [sys.executable, "-m", "health_agent_infra.cli", *args],
        capture_output=True,
        text=True,
        env=env,
    )


def test_cli_propose_validates_and_persists_end_to_end(tmp_path):
    # Initialize DB
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    proposal_path = tmp_path / "proposal.json"
    proposal_path.write_text(json.dumps(_valid_running_proposal()), encoding="utf-8")

    base_dir = tmp_path / "writeback"
    base_dir.mkdir()

    result = _run_cli(
        "propose",
        "--domain", "running",
        "--proposal-json", str(proposal_path),
        "--base-dir", str(base_dir),
        "--db-path", str(db_path),
    )
    assert result.returncode == 0, result.stderr
    record = json.loads(result.stdout)
    assert record["proposal_id"] == "prop_2026-04-17_u_local_1_running_01"
    assert record["domain"] == "running"

    # JSONL exists
    log_path = base_dir / "running_proposals.jsonl"
    assert log_path.exists()

    # DB row exists
    conn = open_connection(db_path)
    try:
        row = conn.execute(
            "SELECT proposal_id, domain, for_date, user_id, action, confidence, "
            "daily_plan_id FROM proposal_log WHERE proposal_id = ?",
            ("prop_2026-04-17_u_local_1_running_01",),
        ).fetchone()
        assert row is not None
        assert row["domain"] == "running"
        assert row["user_id"] == "u_local_1"
        assert row["action"] == "proceed_with_planned_run"
        assert row["daily_plan_id"] is None  # not yet linked by synthesize
    finally:
        conn.close()


def test_cli_propose_rejects_invalid_and_exits_2(tmp_path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    bad = _valid_running_proposal(action="proceed_with_planned_session")  # recovery action
    proposal_path = tmp_path / "proposal.json"
    proposal_path.write_text(json.dumps(bad), encoding="utf-8")

    base_dir = tmp_path / "writeback"
    base_dir.mkdir()

    result = _run_cli(
        "propose",
        "--domain", "running",
        "--proposal-json", str(proposal_path),
        "--base-dir", str(base_dir),
        "--db-path", str(db_path),
    )
    assert result.returncode == exit_codes.USER_INPUT
    assert "invariant=action_enum" in result.stderr


def test_cli_propose_domain_flag_matches_payload(tmp_path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    running = _valid_running_proposal()
    proposal_path = tmp_path / "proposal.json"
    proposal_path.write_text(json.dumps(running), encoding="utf-8")

    base_dir = tmp_path / "writeback"
    base_dir.mkdir()

    # Running payload passed to --domain recovery → rejected
    result = _run_cli(
        "propose",
        "--domain", "recovery",
        "--proposal-json", str(proposal_path),
        "--base-dir", str(base_dir),
        "--db-path", str(db_path),
    )
    assert result.returncode == exit_codes.USER_INPUT
    assert "invariant=domain_match" in result.stderr


# ---------------------------------------------------------------------------
# Strength closure — strength is a real proposal-submitting domain.
# ---------------------------------------------------------------------------

def _valid_strength_proposal(**overrides):
    base = {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS["strength"],
        "proposal_id": "prop_2026-04-17_u_local_1_strength_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-17",
        "domain": "strength",
        "action": "proceed_with_planned_session",
        "action_detail": None,
        "rationale": ["recent_volume_trend=steady"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }
    base.update(overrides)
    return base


def test_validate_accepts_valid_strength_proposal():
    validate_proposal_dict(_valid_strength_proposal(), expected_domain="strength")


def test_validate_rejects_action_outside_strength_enum():
    # ``downgrade_intervals_to_tempo`` is a running-only action.
    prop = _valid_strength_proposal(action="downgrade_intervals_to_tempo")
    with pytest.raises(ProposalValidationError) as exc:
        validate_proposal_dict(prop)
    assert exc.value.invariant == "action_enum"


def test_validate_accepts_strength_specific_action_names():
    # ``downgrade_to_technique_or_accessory`` and
    # ``downgrade_to_moderate_load`` are strength-only softenings.
    for action in (
        "downgrade_to_technique_or_accessory",
        "downgrade_to_moderate_load",
    ):
        validate_proposal_dict(_valid_strength_proposal(action=action))


def test_cli_propose_strength_validates_and_persists_end_to_end(tmp_path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    proposal_path = tmp_path / "proposal.json"
    proposal_path.write_text(
        json.dumps(_valid_strength_proposal()), encoding="utf-8",
    )

    base_dir = tmp_path / "writeback"
    base_dir.mkdir()

    result = _run_cli(
        "propose",
        "--domain", "strength",
        "--proposal-json", str(proposal_path),
        "--base-dir", str(base_dir),
        "--db-path", str(db_path),
    )
    assert result.returncode == 0, result.stderr
    record = json.loads(result.stdout)
    assert record["domain"] == "strength"

    assert (base_dir / "strength_proposals.jsonl").exists()

    conn = open_connection(db_path)
    try:
        row = conn.execute(
            "SELECT domain, action, schema_version, daily_plan_id "
            "FROM proposal_log WHERE proposal_id = ?",
            ("prop_2026-04-17_u_local_1_strength_01",),
        ).fetchone()
        assert row is not None
        assert row["domain"] == "strength"
        assert row["action"] == "proceed_with_planned_session"
        assert row["schema_version"] == "strength_proposal.v1"
        assert row["daily_plan_id"] is None
    finally:
        conn.close()
