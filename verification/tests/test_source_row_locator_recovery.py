"""W-PROV-1 roundtrip: recovery R6 firing emits source-row locators
that survive the proposal → recommendation → explain pipeline and
resolve back to evidence rows.

v0.1.14 cycle: end-to-end demo on the recovery domain only. Other
domains adopt locator emission in v0.1.15+.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

import pytest

from health_agent_infra.core.provenance.locator import (
    LocatorValidationError,
    dedupe_locators,
    deserialize_locators,
    render_locators_markdown,
    resolve_locator,
    serialize_locators,
    validate_locator,
)
from health_agent_infra.core.state.store import (
    apply_pending_migrations,
    open_connection,
)
from health_agent_infra.core.writeback.proposal import (
    ProposalValidationError,
    validate_proposal_dict,
)
from health_agent_infra.domains.recovery.classify import ClassifiedRecoveryState
from health_agent_infra.domains.recovery.policy import evaluate_recovery_policy


# ---------------------------------------------------------------------------
# Validator unit tests
# ---------------------------------------------------------------------------

_VALID_LOCATOR = {
    "table": "accepted_recovery_state_daily",
    "pk": {"as_of_date": "2026-04-30", "user_id": "u_local_1"},
    "column": "resting_hr",
    "row_version": "2026-04-30T19:26:05.234Z",
}


def test_validate_locator_accepts_valid_recovery_locator():
    validate_locator(_VALID_LOCATOR)


def test_validate_locator_rejects_unwhitelisted_table():
    bad = dict(_VALID_LOCATOR, table="recommendation_log")
    bad["pk"] = {"recommendation_id": "r"}
    with pytest.raises(LocatorValidationError) as exc_info:
        validate_locator(bad)
    assert exc_info.value.invariant == "table_whitelist"


def test_validate_locator_rejects_pk_shape_mismatch():
    bad = dict(_VALID_LOCATOR, pk={"wrong_col": "x"})
    with pytest.raises(LocatorValidationError) as exc_info:
        validate_locator(bad)
    assert exc_info.value.invariant == "pk_shape"


def test_validate_locator_rejects_non_scalar_pk_value():
    bad = dict(_VALID_LOCATOR, pk={"as_of_date": ["nope"], "user_id": "u_local_1"})
    with pytest.raises(LocatorValidationError) as exc_info:
        validate_locator(bad)
    assert exc_info.value.invariant == "pk_value_scalar"


def test_validate_locator_rejects_missing_required_field():
    bad = {k: v for k, v in _VALID_LOCATOR.items() if k != "row_version"}
    with pytest.raises(LocatorValidationError) as exc_info:
        validate_locator(bad)
    assert exc_info.value.invariant == "required_fields"


def test_validate_locator_accepts_omitted_column():
    omitted = {k: v for k, v in _VALID_LOCATOR.items() if k != "column"}
    validate_locator(omitted)


def test_dedupe_locators_drops_exact_duplicates_first_wins():
    same = dict(_VALID_LOCATOR)
    other_version = dict(_VALID_LOCATOR, row_version="2026-04-30T20:00:00Z")
    out = dedupe_locators([same, other_version])
    assert len(out) == 1
    assert out[0]["row_version"] == _VALID_LOCATOR["row_version"]


def test_serialize_deserialize_locators_roundtrip():
    blob = serialize_locators([_VALID_LOCATOR])
    assert blob is not None
    parsed = deserialize_locators(blob)
    assert parsed == [_VALID_LOCATOR]


def test_serialize_locators_none_or_empty_returns_none():
    assert serialize_locators(None) is None
    assert serialize_locators([]) is None


def test_render_locators_markdown_shape():
    out = render_locators_markdown([_VALID_LOCATOR])
    assert "accepted_recovery_state_daily" in out
    assert "as_of_date=2026-04-30" in out
    assert "resting_hr" in out


# ---------------------------------------------------------------------------
# Proposal validator integration
# ---------------------------------------------------------------------------

def _proposal(*, evidence_locators=None) -> dict:
    base = {
        "schema_version": "recovery_proposal.v1",
        "proposal_id": "prop_2026-04-30_u_local_1_recovery_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-30",
        "domain": "recovery",
        "action": "escalate_for_user_review",
        "action_detail": {
            "reason_token": "resting_hr_spike_3_days_running",
            "consecutive_days": 3,
        },
        "rationale": ["Resting HR elevated 3 days running."],
        "confidence": "moderate",
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": "resting_hr_spike_escalation",
             "decision": "escalate",
             "note": "spike >= threshold"},
        ],
        "bounded": True,
    }
    if evidence_locators is not None:
        base["evidence_locators"] = evidence_locators
    return base


def test_proposal_validator_accepts_proposal_without_locators():
    validate_proposal_dict(_proposal())


def test_proposal_validator_accepts_proposal_with_valid_locators():
    validate_proposal_dict(_proposal(evidence_locators=[_VALID_LOCATOR]))


def test_proposal_validator_rejects_invalid_locator():
    bad_proposal = _proposal(evidence_locators=[{"table": "wrong"}])
    with pytest.raises(ProposalValidationError) as exc_info:
        validate_proposal_dict(bad_proposal)
    assert exc_info.value.invariant == "evidence_locators_entry"


def test_proposal_validator_rejects_non_list_locators():
    bad_proposal = _proposal(evidence_locators={"not": "a list"})
    with pytest.raises(ProposalValidationError) as exc_info:
        validate_proposal_dict(bad_proposal)
    assert exc_info.value.invariant == "evidence_locators_shape"


# ---------------------------------------------------------------------------
# Recovery policy integration — R6 firing populates evidence_locators
# ---------------------------------------------------------------------------

def _classified_for_spike():
    return ClassifiedRecoveryState(
        sleep_debt_band="none",
        resting_hr_band="elevated",
        hrv_band="at",
        training_load_band="moderate",
        soreness_band="low",
        coverage_band="full",
        recovery_status="recovered",
        readiness_score=0.6,
        uncertainty=tuple(),
    )


def test_evaluate_recovery_policy_emits_locators_when_r6_spike_fires():
    versions = {
        "2026-04-28": "2026-04-28T19:26:05.234Z",
        "2026-04-29": "2026-04-29T19:26:05.234Z",
        "2026-04-30": "2026-04-30T19:26:05.234Z",
    }
    result = evaluate_recovery_policy(
        _classified_for_spike(),
        raw_summary={"resting_hr_spike_days": 3},
        for_date_iso="2026-04-30",
        user_id="u_local_1",
        accepted_state_versions=versions,
    )
    assert result.forced_action == "escalate_for_user_review"
    assert result.evidence_locators is not None
    assert len(result.evidence_locators) == 3
    days = sorted(loc["pk"]["as_of_date"] for loc in result.evidence_locators)
    assert days == ["2026-04-28", "2026-04-29", "2026-04-30"]
    for loc in result.evidence_locators:
        validate_locator(loc)
        assert loc["table"] == "accepted_recovery_state_daily"
        assert loc["column"] == "resting_hr"


def test_evaluate_recovery_policy_omits_locators_without_provenance_args():
    """Legacy 3-arg signature returns None for evidence_locators."""

    result = evaluate_recovery_policy(
        _classified_for_spike(),
        raw_summary={"resting_hr_spike_days": 3},
    )
    assert result.forced_action == "escalate_for_user_review"
    assert result.evidence_locators is None


def test_evaluate_recovery_policy_omits_locators_for_non_spike_firings():
    """R1 / R5 firings don't populate locators."""

    classified_insufficient = ClassifiedRecoveryState(
        sleep_debt_band="none",
        resting_hr_band="at",
        hrv_band="at",
        training_load_band="moderate",
        soreness_band="low",
        coverage_band="insufficient",
        recovery_status="recovered",
        readiness_score=None,
        uncertainty=tuple(),
    )
    result = evaluate_recovery_policy(
        classified_insufficient,
        raw_summary={"resting_hr_spike_days": 0},
        for_date_iso="2026-04-30",
        user_id="u_local_1",
        accepted_state_versions={},
    )
    assert result.forced_action == "defer_decision_insufficient_signal"
    assert result.evidence_locators is None


# ---------------------------------------------------------------------------
# DB-level resolve roundtrip
# ---------------------------------------------------------------------------

def _seed_recovery_evidence(conn: sqlite3.Connection) -> None:
    """Insert 3 days of accepted_recovery_state_daily rows with elevated rhr."""

    rows = [
        ("2026-04-28", "u_local_1", 65.0, 50.0, 100.0, 95.0, 1.05, 0.6,
         "[]", "garmin", "garmin_csv_adapter", "2026-04-28T19:26:05.234Z", None),
        ("2026-04-29", "u_local_1", 66.0, 49.0, 105.0, 95.0, 1.10, 0.55,
         "[]", "garmin", "garmin_csv_adapter", "2026-04-29T19:26:05.234Z", None),
        ("2026-04-30", "u_local_1", 67.0, 48.0, 110.0, 95.0, 1.15, 0.5,
         "[]", "garmin", "garmin_csv_adapter", "2026-04-30T19:26:05.234Z", None),
    ]
    conn.executemany(
        "INSERT INTO accepted_recovery_state_daily ("
        "  as_of_date, user_id, resting_hr, hrv_ms, "
        "  acute_load, chronic_load, acwr_ratio, "
        "  training_readiness_component_mean_pct, derived_from, "
        "  source, ingest_actor, projected_at, corrected_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def test_resolve_locator_returns_row_when_present(tmp_path):
    db_path = tmp_path / "state.db"
    conn = open_connection(db_path)
    apply_pending_migrations(conn)
    _seed_recovery_evidence(conn)

    resolved = resolve_locator(conn, _VALID_LOCATOR)
    assert resolved is not None
    assert resolved["resting_hr"] == 67.0
    assert resolved["as_of_date"] == "2026-04-30"
    assert resolved["user_id"] == "u_local_1"


def test_resolve_locator_returns_none_when_row_missing(tmp_path):
    db_path = tmp_path / "state.db"
    conn = open_connection(db_path)
    apply_pending_migrations(conn)
    # Don't seed.
    resolved = resolve_locator(conn, _VALID_LOCATOR)
    assert resolved is None


# ---------------------------------------------------------------------------
# Migration 023 sanity — column appears on recommendation_log
# ---------------------------------------------------------------------------

def test_migration_023_adds_evidence_locators_column(tmp_path):
    db_path = tmp_path / "state.db"
    conn = open_connection(db_path)
    apply_pending_migrations(conn)
    cols = {row[1] for row in conn.execute(
        "PRAGMA table_info(recommendation_log)"
    ).fetchall()}
    assert "evidence_locators_json" in cols


# ---------------------------------------------------------------------------
# Recommendation projection — locators land in the column
# ---------------------------------------------------------------------------

def test_project_recommendation_writes_evidence_locators_json_column(tmp_path):
    from health_agent_infra.core.state.projector import (
        project_bounded_recommendation,
    )

    db_path = tmp_path / "state.db"
    conn = open_connection(db_path)
    apply_pending_migrations(conn)
    _seed_recovery_evidence(conn)

    rec = {
        "schema_version": "recovery_recommendation.v1",
        "recommendation_id": "rec_2026-04-30_u_local_1_recovery_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-30",
        "domain": "recovery",
        "action": "escalate_for_user_review",
        "action_detail": {
            "reason_token": "resting_hr_spike_3_days_running",
        },
        "rationale": ["Resting HR elevated 3 days running."],
        "confidence": "moderate",
        "uncertainty": [],
        "policy_decisions": [],
        "bounded": True,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "evidence_locators": [_VALID_LOCATOR],
    }
    project_bounded_recommendation(conn, rec)

    row = conn.execute(
        "SELECT evidence_locators_json FROM recommendation_log "
        "WHERE recommendation_id = ?",
        (rec["recommendation_id"],),
    ).fetchone()
    assert row is not None
    assert row[0] is not None
    parsed = json.loads(row[0])
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["table"] == "accepted_recovery_state_daily"
