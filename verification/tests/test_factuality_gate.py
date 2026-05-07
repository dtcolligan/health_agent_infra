"""W58D factuality gate tests (v0.2.0 §2.F).

Step 1: gate logic skeleton tested against synthetic in-memory
atoms — no corpus yet. Step 6 wires the real ``factuality/`` corpus
and step 7 wires the ``--bypass-factuality-gate`` CLI flag.

The synthetic-fixture approach lets step 1 ship the gate semantics
independently of the corpus authoring. Every block reason has a
dedicated fixture; the bundle-level aggregation is also exercised.
"""

from __future__ import annotations

import sqlite3

import pytest

from health_agent_infra.core.eval import (
    BlockReason,
    ClaimGateInput,
    FactualityGateOutcome,
    GateOutcome,
    gate_claim,
    run_factuality_gate,
)


# ---------------------------------------------------------------------------
# Fixture infrastructure
# ---------------------------------------------------------------------------


@pytest.fixture
def conn() -> sqlite3.Connection:
    """In-memory DB with one accepted_recovery_state_daily row + one
    daily_plan row + one recommendation_log row, just enough to
    exercise both lanes (locator resolution + audit-ref existence).
    """

    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row

    # Locator-resolved table — accepted_recovery_state_daily with a
    # row_version column so drift testing is possible.
    c.execute(
        "CREATE TABLE accepted_recovery_state_daily ("
        " as_of_date TEXT NOT NULL,"
        " user_id TEXT NOT NULL,"
        " row_version TEXT NOT NULL,"
        " resting_hr INTEGER,"
        " hrv_rmssd INTEGER,"
        " PRIMARY KEY (as_of_date, user_id))"
    )
    c.execute(
        "INSERT INTO accepted_recovery_state_daily VALUES "
        "('2026-04-28', 'u_test', '2026-04-28T19:00Z', 52, 65)"
    )

    # Audit-chain tables.
    c.execute(
        "CREATE TABLE daily_plan (daily_plan_id TEXT PRIMARY KEY, "
        "user_id TEXT, for_date TEXT)"
    )
    c.execute(
        "INSERT INTO daily_plan VALUES "
        "('plan_2026-04-28', 'u_test', '2026-04-28')"
    )

    c.execute(
        "CREATE TABLE recommendation_log (recommendation_id TEXT "
        "PRIMARY KEY, user_id TEXT, for_date TEXT)"
    )
    c.execute(
        "INSERT INTO recommendation_log VALUES "
        "('rec_2026-04-28_recovery', 'u_test', '2026-04-28')"
    )

    c.commit()
    yield c
    c.close()


def _good_locator() -> dict:
    return {
        "table": "accepted_recovery_state_daily",
        "pk": {"as_of_date": "2026-04-28", "user_id": "u_test"},
        "row_version": "2026-04-28T19:00Z",
        "column": "resting_hr",
    }


# ---------------------------------------------------------------------------
# 1. Qualitative atom — SKIP
# ---------------------------------------------------------------------------


def test_gate_claim_qualitative_atom_skips(conn):
    claim = ClaimGateInput(
        atom_text="This review is informational.",
        atom_type="qualitative",
    )
    result = gate_claim(conn, claim)
    assert result.outcome == GateOutcome.SKIP
    assert result.block_reason is None


# ---------------------------------------------------------------------------
# 2. Quantitative + comparative — vacuous PASS (no provenance)
# ---------------------------------------------------------------------------


def test_gate_claim_vacuous_quantitative_passes(conn):
    """A quantitative atom with no locators and no audit_refs vacuously
    passes — there is nothing to validate. Step 6's corpus will exercise
    the populated paths; this test pins the empty-input behaviour.
    """

    claim = ClaimGateInput(
        atom_text="You ran `hai daily` on 5 of 7 days this week.",
        atom_type="quantitative",
    )
    result = gate_claim(conn, claim)
    assert result.outcome == GateOutcome.PASS


def test_gate_claim_vacuous_comparative_passes(conn):
    claim = ClaimGateInput(
        atom_text="Rules that shaped the recommendation: low recovery (X1).",
        atom_type="comparative",
    )
    result = gate_claim(conn, claim)
    assert result.outcome == GateOutcome.PASS


# ---------------------------------------------------------------------------
# 3. Locator path — valid resolution
# ---------------------------------------------------------------------------


def test_gate_claim_passes_with_valid_locator(conn):
    claim = ClaimGateInput(
        atom_text="On April 28 your resting heart rate was 52 bpm.",
        atom_type="quantitative",
        locator_set=[_good_locator()],
    )
    result = gate_claim(conn, claim)
    assert result.outcome == GateOutcome.PASS
    assert result.block_reason is None


# ---------------------------------------------------------------------------
# 4. Locator path — block reasons
# ---------------------------------------------------------------------------


def test_gate_claim_blocks_on_malformed_locator(conn):
    """Locator with table not in the W-PROV-1 whitelist."""

    bad = {
        "table": "nope_not_a_real_table",
        "pk": {"as_of_date": "2026-04-28", "user_id": "u_test"},
        "row_version": "2026-04-28T19:00Z",
    }
    claim = ClaimGateInput(
        atom_text="...",
        atom_type="quantitative",
        locator_set=[bad],
    )
    result = gate_claim(conn, claim)
    assert result.outcome == GateOutcome.BLOCK
    assert result.block_reason == BlockReason.LOCATOR_INVALID
    assert "table_whitelist" in (result.block_detail or "")


def test_gate_claim_blocks_on_missing_locator_row(conn):
    """Locator validates but the row at its PK does not exist."""

    locator = dict(_good_locator())
    locator["pk"] = {"as_of_date": "2099-01-01", "user_id": "u_test"}
    claim = ClaimGateInput(
        atom_text="...",
        atom_type="quantitative",
        locator_set=[locator],
    )
    result = gate_claim(conn, claim)
    assert result.outcome == GateOutcome.BLOCK
    assert result.block_reason == BlockReason.LOCATOR_ROW_MISSING


def test_gate_claim_blocks_on_row_version_drift(conn):
    """Locator resolves but cited row_version mismatches current row."""

    locator = dict(_good_locator())
    locator["row_version"] = "2026-04-28T08:00Z"  # earlier snapshot
    claim = ClaimGateInput(
        atom_text="...",
        atom_type="quantitative",
        locator_set=[locator],
    )
    result = gate_claim(conn, claim)
    assert result.outcome == GateOutcome.BLOCK
    assert result.block_reason == BlockReason.LOCATOR_ROW_VERSION_DRIFT
    assert "2026-04-28T08:00Z" in (result.block_detail or "")
    assert "2026-04-28T19:00Z" in (result.block_detail or "")


# ---------------------------------------------------------------------------
# 5. Audit-ref path — valid + orphan
# ---------------------------------------------------------------------------


def test_gate_claim_passes_with_valid_audit_ref(conn):
    claim = ClaimGateInput(
        atom_text="...",
        atom_type="quantitative",
        audit_refs={
            "daily_plan": ["plan_2026-04-28"],
            "recommendation_log": ["rec_2026-04-28_recovery"],
        },
    )
    result = gate_claim(conn, claim)
    assert result.outcome == GateOutcome.PASS


def test_gate_claim_blocks_on_audit_ref_orphan(conn):
    claim = ClaimGateInput(
        atom_text="...",
        atom_type="quantitative",
        audit_refs={"daily_plan": ["plan_does_not_exist"]},
    )
    result = gate_claim(conn, claim)
    assert result.outcome == GateOutcome.BLOCK
    assert result.block_reason == BlockReason.AUDIT_REF_ORPHAN


def test_gate_claim_blocks_on_unknown_audit_chain_table(conn):
    """Table not in the audit-chain whitelist fails closed."""

    claim = ClaimGateInput(
        atom_text="...",
        atom_type="quantitative",
        audit_refs={"some_other_table": [42]},
    )
    result = gate_claim(conn, claim)
    assert result.outcome == GateOutcome.BLOCK
    assert result.block_reason == BlockReason.AUDIT_REF_ORPHAN
    assert "W58D whitelist" in (result.block_detail or "")


# ---------------------------------------------------------------------------
# 6. Unknown atom_type — fail-closed
# ---------------------------------------------------------------------------


def test_gate_claim_unknown_atom_type_blocks(conn):
    claim = ClaimGateInput(
        atom_text="...",
        atom_type="speculative",  # not in {quant, comp, qual}
    )
    result = gate_claim(conn, claim)
    assert result.outcome == GateOutcome.BLOCK
    assert result.block_reason == BlockReason.UNKNOWN_ATOM_TYPE


# ---------------------------------------------------------------------------
# 7. Bundle-level aggregation
# ---------------------------------------------------------------------------


def test_run_factuality_gate_all_pass(conn):
    claims = [
        ClaimGateInput(
            atom_text="qualitative framing",
            atom_type="qualitative",
        ),
        ClaimGateInput(
            atom_text="vacuous quant",
            atom_type="quantitative",
        ),
        ClaimGateInput(
            atom_text="quant with valid locator",
            atom_type="quantitative",
            locator_set=[_good_locator()],
        ),
    ]
    outcome = run_factuality_gate(conn, claims)
    assert outcome.total == 3
    assert outcome.passed == 2
    assert outcome.skipped == 1
    assert outcome.blocked == 0
    assert outcome.all_passed is True
    assert outcome.first_block() is None


def test_run_factuality_gate_one_block_aggregates_correctly(conn):
    claims = [
        ClaimGateInput(
            atom_text="qualitative",
            atom_type="qualitative",
        ),
        ClaimGateInput(
            atom_text="bad locator",
            atom_type="quantitative",
            locator_set=[{
                "table": "not_in_whitelist",
                "pk": {"as_of_date": "x", "user_id": "y"},
                "row_version": "z",
            }],
            claim_id="claim_block_1",
        ),
        ClaimGateInput(
            atom_text="valid quant",
            atom_type="quantitative",
            locator_set=[_good_locator()],
        ),
    ]
    outcome = run_factuality_gate(conn, claims)
    assert outcome.total == 3
    assert outcome.skipped == 1
    assert outcome.passed == 1
    assert outcome.blocked == 1
    assert outcome.all_passed is False

    first = outcome.first_block()
    assert first is not None
    assert first.claim_id == "claim_block_1"
    assert first.outcome == GateOutcome.BLOCK


def test_run_factuality_gate_empty_claims_passes_vacuously(conn):
    outcome = run_factuality_gate(conn, [])
    assert outcome.total == 0
    assert outcome.all_passed is True


# ---------------------------------------------------------------------------
# 8. Two-lane separation invariant (F-PHASE0-12 + F-PLAN-12)
# ---------------------------------------------------------------------------


def test_two_lane_separation_locator_table_cannot_be_audit_ref(conn):
    """An accepted-state table is a locator target, NOT an audit-ref
    target. Citing it as audit_refs must fail closed (it's not in the
    audit-chain whitelist).
    """

    claim = ClaimGateInput(
        atom_text="...",
        atom_type="quantitative",
        audit_refs={"accepted_recovery_state_daily": ["any-pk"]},
    )
    result = gate_claim(conn, claim)
    assert result.outcome == GateOutcome.BLOCK
    assert result.block_reason == BlockReason.AUDIT_REF_ORPHAN


def test_two_lane_separation_audit_chain_table_cannot_be_locator_target(conn):
    """An audit-chain table (daily_plan, recommendation_log, etc.) is
    NOT in the W-PROV-1 locator whitelist. Citing it as a locator must
    fail closed via locator validation.
    """

    locator = {
        "table": "daily_plan",  # audit-chain, not locator-whitelisted
        "pk": {"daily_plan_id": "plan_2026-04-28"},
        "row_version": "v1",
    }
    claim = ClaimGateInput(
        atom_text="...",
        atom_type="quantitative",
        locator_set=[locator],
    )
    result = gate_claim(conn, claim)
    assert result.outcome == GateOutcome.BLOCK
    assert result.block_reason == BlockReason.LOCATOR_INVALID
