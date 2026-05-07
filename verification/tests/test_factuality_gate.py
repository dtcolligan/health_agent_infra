"""W58D factuality gate tests (v0.2.0 §2.F).

Step 1: gate logic skeleton tested against synthetic in-memory
atoms — no corpus yet. Step 6 wires the real ``factuality/`` corpus
and step 7 wires the ``--bypass-factuality-gate`` CLI flag.

The synthetic-fixture approach lets step 1 ship the gate semantics
independently of the corpus authoring. Every block reason has a
dedicated fixture; the bundle-level aggregation is also exercised.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from health_agent_infra.core.config import (
    DEFAULT_THRESHOLDS,
    ConfigCoerceError,
    load_thresholds,
    scaffold_thresholds_toml,
)
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


# ---------------------------------------------------------------------------
# 9. Threshold defaults — DEFAULT_THRESHOLDS surface
# ---------------------------------------------------------------------------


def test_default_thresholds_include_factuality_gate_block():
    """``DEFAULT_THRESHOLDS["policy"]["factuality_gate"]`` ships with
    the PLAN §2.F threshold-acceptance values and types.
    """

    block = DEFAULT_THRESHOLDS["policy"]["factuality_gate"]
    assert block == {
        "block_known_bad_min_pct": 97.0,
        "pass_known_good_min_pct": 99.0,
    }
    # Types match the D13 contract: float defaults so any non-float /
    # non-int / bool override is rejected at load time.
    assert isinstance(block["block_known_bad_min_pct"], float)
    assert isinstance(block["pass_known_good_min_pct"], float)
    assert not isinstance(block["block_known_bad_min_pct"], bool)


def test_scaffold_thresholds_toml_includes_factuality_gate_section():
    """``scaffold_thresholds_toml`` writes a ``[policy.factuality_gate]``
    block matching the defaults so a fresh ``hai config init`` produces
    a file effective-equivalent to no config at all.
    """

    scaffold = scaffold_thresholds_toml()
    assert "[policy.factuality_gate]" in scaffold
    assert "block_known_bad_min_pct = 97.0" in scaffold
    assert "pass_known_good_min_pct = 99.0" in scaffold


# ---------------------------------------------------------------------------
# 10. D13 threshold-injection-seam — bool override rejection
# ---------------------------------------------------------------------------


def test_load_thresholds_rejects_bool_override_for_block_known_bad_min_pct(
    tmp_path: Path,
):
    """Per D13: ``_validate_threshold_types`` at the load_thresholds
    boundary rejects bool overrides on float defaults. A user writing
    ``block_known_bad_min_pct = true`` would silently coerce to
    ``1.0`` (passing every fixture) — exactly the silent-failure mode
    D13 closes.
    """

    bad_toml = tmp_path / "thresholds.toml"
    bad_toml.write_text(
        "[policy.factuality_gate]\n"
        "block_known_bad_min_pct = true\n"
    )
    with pytest.raises(ConfigCoerceError) as exc_info:
        load_thresholds(path=bad_toml)
    msg = str(exc_info.value)
    assert "factuality_gate" in msg
    assert "block_known_bad_min_pct" in msg


def test_load_thresholds_rejects_bool_override_for_pass_known_good_min_pct(
    tmp_path: Path,
):
    bad_toml = tmp_path / "thresholds.toml"
    bad_toml.write_text(
        "[policy.factuality_gate]\n"
        "pass_known_good_min_pct = false\n"
    )
    with pytest.raises(ConfigCoerceError) as exc_info:
        load_thresholds(path=bad_toml)
    msg = str(exc_info.value)
    assert "factuality_gate" in msg
    assert "pass_known_good_min_pct" in msg


# ---------------------------------------------------------------------------
# 11. D13 — legitimate float / int overrides round-trip
# ---------------------------------------------------------------------------


def test_load_thresholds_applies_float_override_for_factuality_gate(
    tmp_path: Path,
):
    """Positive companion: legitimate float overrides load cleanly
    and flow through to ``policy.factuality_gate``. TOML allows ``99``
    and ``99.0`` interchangeably for float defaults; both pass.
    """

    user_toml = tmp_path / "thresholds.toml"
    user_toml.write_text(
        "[policy.factuality_gate]\n"
        "block_known_bad_min_pct = 95.5\n"
        "pass_known_good_min_pct = 98\n"  # int form — float-coercible
    )
    merged = load_thresholds(path=user_toml)
    block = merged["policy"]["factuality_gate"]
    assert block["block_known_bad_min_pct"] == 95.5
    assert block["pass_known_good_min_pct"] == 98
    # Neither value is a bool after the round-trip.
    assert not isinstance(block["block_known_bad_min_pct"], bool)
    assert not isinstance(block["pass_known_good_min_pct"], bool)


# ---------------------------------------------------------------------------
# 12. X-rule-conflict — user-disagreement lane (step 3 gate extension)
# ---------------------------------------------------------------------------


def _seeded_db():
    """Return a fresh in-memory connection seeded with the W58D
    factuality baseline."""

    from health_agent_infra.evals.scenarios.factuality._seed import (
        seed_factuality_baseline,
    )

    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    seed_factuality_baseline(c)
    return c


def test_gate_blocks_on_disagreed_x_rule_firing():
    """Atom citing a firing in the user's disagreed_firing_ids list
    blocks with the new X_RULE_CONFLICT_USER_DISAGREED reason.
    """

    from health_agent_infra.evals.scenarios.factuality._seed import (
        SEED_DISAGREED_FIRING_ID, SEED_USER_ID,
    )

    c = _seeded_db()
    try:
        claim = ClaimGateInput(
            atom_text="Rules that shaped the recommendation: low recovery (X1).",
            atom_type="comparative",
            audit_refs={"x_rule_firing": [SEED_DISAGREED_FIRING_ID]},
            user_id=SEED_USER_ID,
        )
        result = gate_claim(c, claim)
        assert result.outcome == GateOutcome.BLOCK
        assert (
            result.block_reason
            == BlockReason.X_RULE_CONFLICT_USER_DISAGREED
        )
        assert "disagreed_firing_ids" in (result.block_detail or "")
    finally:
        c.close()


def test_gate_passes_on_resolvable_x_rule_firing_no_disagreement():
    """Atom citing a firing the user has NOT disagreed with passes."""

    from health_agent_infra.evals.scenarios.factuality._seed import (
        SEED_RESOLVABLE_FIRING_ID, SEED_USER_ID,
    )

    c = _seeded_db()
    try:
        claim = ClaimGateInput(
            atom_text="Rules that shaped the recommendation: low recovery (X1).",
            atom_type="comparative",
            audit_refs={"x_rule_firing": [SEED_RESOLVABLE_FIRING_ID]},
            user_id=SEED_USER_ID,
        )
        result = gate_claim(c, claim)
        assert result.outcome == GateOutcome.PASS
    finally:
        c.close()


def test_gate_passes_disagreed_firing_when_user_id_absent():
    """Without user_id the disagreement lane is a no-op (the
    structural check needs a user identity to look up history).
    The firing exists, so audit-ref-orphan also passes.
    """

    from health_agent_infra.evals.scenarios.factuality._seed import (
        SEED_DISAGREED_FIRING_ID,
    )

    c = _seeded_db()
    try:
        claim = ClaimGateInput(
            atom_text="...",
            atom_type="comparative",
            audit_refs={"x_rule_firing": [SEED_DISAGREED_FIRING_ID]},
            # user_id intentionally None — backward-compatible path
        )
        result = gate_claim(c, claim)
        assert result.outcome == GateOutcome.PASS
    finally:
        c.close()


def test_gate_disagreement_check_handles_review_outcome_table_missing():
    """When ``review_outcome`` doesn't exist (legacy DB), the
    disagreement lane treats it as no-disagreement (graceful
    degradation; the audit-ref-orphan lane still fail-closes when
    the firing itself is missing).
    """

    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    # Seed only the x_rule_firing table — review_outcome absent.
    c.execute(
        "CREATE TABLE x_rule_firing (firing_id INTEGER PRIMARY KEY)"
    )
    c.execute("INSERT INTO x_rule_firing VALUES (12345)")
    c.commit()
    try:
        claim = ClaimGateInput(
            atom_text="...",
            atom_type="comparative",
            audit_refs={"x_rule_firing": [12345]},
            user_id="some_user",
        )
        result = gate_claim(c, claim)
        assert result.outcome == GateOutcome.PASS
    finally:
        c.close()


# ---------------------------------------------------------------------------
# 13. Corpus harness — every fixture produces its expected outcome
# ---------------------------------------------------------------------------


_CORPUS_DIR = (
    Path(__file__).resolve().parents[1].parent
    / "src" / "health_agent_infra" / "evals" / "scenarios" / "factuality"
)


def _load_factuality_fixtures():
    return [
        json.loads(p.read_text())
        for p in sorted(_CORPUS_DIR.glob("fac_*.json"))
    ]


def test_factuality_corpus_index_manifest_total_matches_fixtures():
    """``index.json`` cardinality matches on-disk ``fac_*.json`` count."""

    manifest = json.loads((_CORPUS_DIR / "index.json").read_text())
    on_disk = len(list(_CORPUS_DIR.glob("fac_*.json")))
    assert manifest["total_fixtures"] == on_disk


def test_factuality_corpus_meets_step_3_minimums():
    """PLAN §2.F sub-category sums: ≥30 source_quality + ≥15
    x_rule_conflict known-bad. The corpus may grow beyond these
    minimums in step 4 + 5; the floors are pinned here.
    """

    manifest = json.loads((_CORPUS_DIR / "index.json").read_text())
    cats = manifest["categories"]
    assert len(cats.get("source_quality", [])) >= 30
    assert len(cats.get("x_rule_conflict", [])) >= 15


def test_factuality_corpus_meets_step_4_minimums():
    """PLAN §2.F sub-categories 3-5 sums: ≥15 source_signal_conflict
    + ≥15 source_row_drift + ≥10 audit_ref_orphan known-bad.
    Combined with step 3 these total ≥85 known-bad (the round-1
    sub-category-sum reconciliation per F-PLAN-06).
    """

    manifest = json.loads((_CORPUS_DIR / "index.json").read_text())
    cats = manifest["categories"]
    assert len(cats.get("source_signal_conflict", [])) >= 15
    assert len(cats.get("source_row_drift", [])) >= 15
    assert len(cats.get("audit_ref_orphan", [])) >= 10
    # Total known-bad floor.
    block_count = sum(
        1 for f in manifest["fixtures"]
        if f["expected_outcome"] == "block"
    )
    assert block_count >= 85, (
        f"corpus has {block_count} known-bad fixtures; "
        f"PLAN §2.F sub-category sum requires ≥85"
    )


# ---------------------------------------------------------------------------
# 14. SOURCE_SIGNAL_CONFLICT lane (step 4 gate extension)
# ---------------------------------------------------------------------------


def test_gate_blocks_on_locator_column_not_on_row_schema():
    """Locator cites a column that doesn't exist on the resolved
    row's schema → SOURCE_SIGNAL_CONFLICT."""

    c = _seeded_db()
    try:
        claim = ClaimGateInput(
            atom_text="...",
            atom_type="quantitative",
            locator_set=[{
                "table": "accepted_recovery_state_daily",
                "pk": {
                    "as_of_date": "2026-04-28",
                    "user_id": "u_factuality_corpus",
                },
                "row_version": "2026-04-28T19:00Z",
                "column": "vo2max",  # not on schema
            }],
        )
        result = gate_claim(c, claim)
        assert result.outcome == GateOutcome.BLOCK
        assert (
            result.block_reason == BlockReason.SOURCE_SIGNAL_CONFLICT
        )
        assert "not on row schema" in (result.block_detail or "")
    finally:
        c.close()


def test_gate_blocks_on_locator_column_value_null():
    """Locator cites a column whose value is NULL on the resolved
    row → SOURCE_SIGNAL_CONFLICT."""

    c = _seeded_db()
    try:
        # 2026-04-29 row is seeded with resting_hr=NULL.
        claim = ClaimGateInput(
            atom_text="...",
            atom_type="quantitative",
            locator_set=[{
                "table": "accepted_recovery_state_daily",
                "pk": {
                    "as_of_date": "2026-04-29",
                    "user_id": "u_factuality_corpus",
                },
                "row_version": "2026-04-29T19:00Z",
                "column": "resting_hr",
            }],
        )
        result = gate_claim(c, claim)
        assert result.outcome == GateOutcome.BLOCK
        assert (
            result.block_reason == BlockReason.SOURCE_SIGNAL_CONFLICT
        )
        assert "is NULL" in (result.block_detail or "")
    finally:
        c.close()


def test_gate_passes_when_locator_column_has_non_null_value():
    """Sanity companion: locator cites a column whose value is
    non-null → PASS. Confirms the lane is not over-strict."""

    c = _seeded_db()
    try:
        claim = ClaimGateInput(
            atom_text="...",
            atom_type="quantitative",
            locator_set=[{
                "table": "accepted_recovery_state_daily",
                "pk": {
                    "as_of_date": "2026-04-28",
                    "user_id": "u_factuality_corpus",
                },
                "row_version": "2026-04-28T19:00Z",
                "column": "resting_hr",  # value is 52, non-null
            }],
        )
        result = gate_claim(c, claim)
        assert result.outcome == GateOutcome.PASS
    finally:
        c.close()


# ---------------------------------------------------------------------------
# 15. Step 5 — known-good corpus floor (≥75)
# ---------------------------------------------------------------------------


def test_factuality_corpus_meets_step_5_known_good_minimum():
    """PLAN §2.F threshold-acceptance #2: ≥75 known-good fixtures.
    Combined with the ≥85 known-bad floor from steps 3-4, the total
    corpus is ≥150.

    Known-good = expected_outcome ∈ {"pass", "skip"}. Qualitative
    atoms (gate SKIP) and quantitative/comparative atoms with valid
    provenance (gate PASS) both count — neither blocks the bundle.
    """

    manifest = json.loads((_CORPUS_DIR / "index.json").read_text())
    counts = manifest["expected_outcome_counts"]
    known_good = counts.get("pass", 0) + counts.get("skip", 0)
    assert known_good >= 75, (
        f"corpus has {known_good} known-good fixtures "
        f"(pass={counts.get('pass', 0)}, "
        f"skip={counts.get('skip', 0)}); "
        f"PLAN §2.F threshold-acceptance #2 requires ≥75"
    )
    # Total corpus floor.
    assert manifest["total_fixtures"] >= 150


def test_factuality_corpus_known_good_category_present_with_floor():
    """The ``known_good`` category specifically holds ≥75 fixtures
    (vs the bare ≥75 known-good floor which could in principle be
    distributed across categories). Pinning the category-specific
    count keeps the corpus shape comprehensible.
    """

    manifest = json.loads((_CORPUS_DIR / "index.json").read_text())
    cats = manifest["categories"]
    assert len(cats.get("known_good", [])) >= 75


def test_every_factuality_fixture_produces_its_expected_outcome():
    """Run each known-bad fixture through the gate and assert the
    outcome matches its declared ``expected_outcome`` +
    ``expected_block_reason``. This is the corpus-correctness gate
    that prevents fixture rot — a fixture whose payload no longer
    triggers the expected lane is a corpus bug.
    """

    import json as _json

    c = _seeded_db()
    try:
        fixtures = _load_factuality_fixtures()
        assert fixtures, "factuality corpus must not be empty"
        for fixture in fixtures:
            inp = fixture["input"]
            claim = ClaimGateInput(
                atom_text=inp["atom_text"],
                atom_type=inp["atom_type"],
                locator_set=inp.get("locator_set", []),
                audit_refs=inp.get("audit_refs", {}),
                user_id=inp.get("user_id"),
            )
            result = gate_claim(c, claim)
            actual_outcome = result.outcome.value
            assert actual_outcome == fixture["expected_outcome"], (
                f"{fixture['fixture_id']}: expected outcome "
                f"{fixture['expected_outcome']!r} but gate returned "
                f"{actual_outcome!r} ({result.block_reason})"
            )
            if fixture["expected_outcome"] == "block":
                expected_reason = fixture["expected_block_reason"]
                actual_reason = (
                    result.block_reason.value if result.block_reason
                    else None
                )
                assert actual_reason == expected_reason, (
                    f"{fixture['fixture_id']}: expected block_reason "
                    f"{expected_reason!r} but gate returned "
                    f"{actual_reason!r}"
                )
    finally:
        c.close()


def test_factuality_corpus_fixture_categories_complete():
    """Every fixture in ``manifest.fixtures`` has a matching entry
    in ``manifest.categories`` (no orphan IDs)."""

    manifest = json.loads((_CORPUS_DIR / "index.json").read_text())
    fixture_ids = {f["fixture_id"] for f in manifest["fixtures"]}
    flat = {fid for ids in manifest["categories"].values() for fid in ids}
    assert fixture_ids == flat
