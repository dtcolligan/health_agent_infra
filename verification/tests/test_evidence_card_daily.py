"""W-EVCARD-DAILY — daily evidence-card carrier (v0.2.0 §2.B).

Tests cover acceptance items 1-7 from PLAN §2.B:
  #1 migration 027 lands; table created
  #2 synthesis transaction writes exactly one card per committed
     recommendation
  #3 synthesis rollback proves no card survives a failed synthesis
  #4 card payload validates against recommendation_evidence_card.v1
     schema; locator entries validate per W-PROV-1
  #5 evidence_cards surface (consumed by hai explain in commit 4)
  #6 test count grows ≥ 12 vs v0.1.18 (this file alone targets 12+)

Plus the validator-unit edge cases that round out the schema
enforcement contract.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from health_agent_infra.core.schemas import canonical_daily_plan_id
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_proposal,
)
from health_agent_infra.core.state.projectors.evidence_card import (
    EVIDENCE_CARD_SCHEMA_VERSION,
    EvidenceCardValidationError,
    build_evidence_card_payload,
    validate_evidence_card_payload,
)
from health_agent_infra.core.synthesis import run_synthesis
from health_agent_infra.core.writeback.proposal import PROPOSAL_SCHEMA_VERSIONS


FOR_DATE = date(2026, 5, 7)
USER = "u_evc_test"


# ---------------------------------------------------------------------------
# Migration 027 contract — acceptance #1
# ---------------------------------------------------------------------------


def test_migration_027_creates_recommendation_evidence_card_table(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    conn = open_connection(db_path)
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='recommendation_evidence_card'"
        )
        assert cur.fetchone() is not None
        cols = {
            row[1] for row in conn.execute(
                "PRAGMA table_info(recommendation_evidence_card)"
            )
        }
        assert {
            "card_id", "daily_plan_id", "recommendation_id",
            "planned_id", "proposal_id", "user_id", "for_date",
            "domain", "schema_version", "payload_json",
            "computed_at", "source", "ingest_actor", "agent_version",
        }.issubset(cols)
    finally:
        conn.close()


def test_migration_027_creates_indexes(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    conn = open_connection(db_path)
    try:
        idx = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='recommendation_evidence_card'"
            )
        }
        assert "idx_evidence_card_for_date" in idx
        assert "idx_evidence_card_recommendation" in idx
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Payload validator contract — acceptance #4
# ---------------------------------------------------------------------------


_VALID_LOCATOR = {
    "table": "accepted_recovery_state_daily",
    "pk": {"as_of_date": "2026-05-07", "user_id": USER},
    "row_version": "2026-05-07T07:00:00Z",
}


def test_build_evidence_card_payload_minimal_passes_validation():
    rec = {
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "confidence": "high",
        "rationale": ["x"],
        "uncertainty": [],
    }
    payload = build_evidence_card_payload(rec)
    validate_evidence_card_payload(payload)
    assert payload["schema_version"] == EVIDENCE_CARD_SCHEMA_VERSION
    assert payload["decision"]["domain"] == "recovery"
    assert payload["provenance"]["accepted_state_rows"] == []


def test_build_evidence_card_payload_with_full_provenance_passes_validation():
    rec = {"domain": "recovery", "action": "rest_day", "confidence": "moderate"}
    payload = build_evidence_card_payload(
        rec,
        accepted_state_rows=[_VALID_LOCATOR],
        proposal_log_ids=["prop_1"],
        planned_ids=["planned_1"],
        recommendation_log_ids=["rec_1"],
        x_rule_firing_ids=[1, 2, 3],
    )
    assert payload["provenance"]["accepted_state_rows"] == [_VALID_LOCATOR]
    assert payload["provenance"]["x_rule_firing"] == [1, 2, 3]


def test_validator_rejects_non_dict_payload():
    with pytest.raises(EvidenceCardValidationError) as exc:
        validate_evidence_card_payload(["not", "a", "dict"])
    assert exc.value.invariant == "shape"


def test_validator_rejects_payload_missing_required_lanes():
    bad = {"decision": {}, "evidence": {}}  # missing provenance
    with pytest.raises(EvidenceCardValidationError) as exc:
        validate_evidence_card_payload(bad)
    assert exc.value.invariant == "required_lanes"


def test_validator_rejects_locator_with_unwhitelisted_table():
    bad_locator = {
        "table": "recommendation_log",  # write-side audit-chain table
        "pk": {"recommendation_id": "x"},
        "row_version": "2026-05-07T00:00:00Z",
    }
    with pytest.raises(EvidenceCardValidationError) as exc:
        build_evidence_card_payload(
            {"domain": "recovery"},
            accepted_state_rows=[bad_locator],
        )
    # Failure routes via accepted_state_rows_entry → locator validation
    assert "accepted_state_rows" in exc.value.invariant


def test_validator_rejects_non_list_audit_chain_entry():
    payload = {
        "decision": {},
        "evidence": {},
        "provenance": {
            "recommendation_log": "not_a_list",
            "accepted_state_rows": [],
            "raw_source_refs": [],
        },
    }
    with pytest.raises(EvidenceCardValidationError) as exc:
        validate_evidence_card_payload(payload)
    assert exc.value.invariant == "recommendation_log_shape"


# ---------------------------------------------------------------------------
# End-to-end synthesis integration — acceptance #2 + #3
# ---------------------------------------------------------------------------


def _proposal(domain: str, idx: int = 1) -> dict[str, Any]:
    actions = {
        "recovery": "proceed_with_planned_session",
        "running": "proceed_with_planned_run",
        "sleep": "maintain_schedule",
        "stress": "maintain_routine",
        "strength": "proceed_with_planned_session",
        "nutrition": "maintain_targets",
    }
    return {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS[domain],
        "proposal_id": f"prop_{FOR_DATE}_{USER}_{domain}_{idx:02d}",
        "user_id": USER,
        "for_date": FOR_DATE.isoformat(),
        "domain": domain,
        "action": actions[domain],
        "action_detail": None,
        "rationale": [f"{domain} ok"],
        "confidence": "moderate",
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": f"{domain}_r1", "decision": "allow", "note": "n"},
        ],
        "bounded": True,
    }


def _quiet_snapshot() -> dict[str, Any]:
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


def _seed_proposals(db_path: Path, domains: list[str]) -> None:
    initialize_database(db_path)
    conn = open_connection(db_path)
    try:
        for domain in domains:
            project_proposal(conn, _proposal(domain))
    finally:
        conn.close()


def test_synthesis_writes_one_card_per_recommendation_single_domain(
    tmp_path: Path,
):
    db_path = tmp_path / "state.db"
    _seed_proposals(db_path, ["recovery"])
    conn = open_connection(db_path)
    try:
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_quiet_snapshot(),
        )
        n = conn.execute(
            "SELECT COUNT(*) FROM recommendation_evidence_card "
            "WHERE user_id = ? AND for_date = ?",
            (USER, FOR_DATE.isoformat()),
        ).fetchone()[0]
        assert n == 1
        rec_count = conn.execute(
            "SELECT COUNT(*) FROM recommendation_log "
            "WHERE user_id = ? AND for_date = ?",
            (USER, FOR_DATE.isoformat()),
        ).fetchone()[0]
        assert rec_count == n  # one card per recommendation
    finally:
        conn.close()


def test_synthesis_writes_one_card_per_recommendation_multi_domain(
    tmp_path: Path,
):
    db_path = tmp_path / "state.db"
    domains = ["recovery", "running", "sleep", "stress", "strength", "nutrition"]
    _seed_proposals(db_path, domains)
    conn = open_connection(db_path)
    try:
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_quiet_snapshot(),
        )
        rec_rows = conn.execute(
            "SELECT recommendation_id FROM recommendation_log "
            "WHERE user_id = ? AND for_date = ?",
            (USER, FOR_DATE.isoformat()),
        ).fetchall()
        card_rows = conn.execute(
            "SELECT card_id, recommendation_id, domain, schema_version "
            "FROM recommendation_evidence_card "
            "WHERE user_id = ? AND for_date = ?",
            (USER, FOR_DATE.isoformat()),
        ).fetchall()
        # 6 recommendations → 6 cards, each cross-referenceable.
        assert len(rec_rows) == 6
        assert len(card_rows) == 6
        rec_ids = {r[0] for r in rec_rows}
        card_rec_ids = {r[1] for r in card_rows}
        assert rec_ids == card_rec_ids
        for card in card_rows:
            assert card[3] == EVIDENCE_CARD_SCHEMA_VERSION
    finally:
        conn.close()


def test_synthesis_rollback_drops_all_cards_when_card_insert_fails(
    tmp_path: Path, monkeypatch,
):
    db_path = tmp_path / "state.db"
    _seed_proposals(db_path, ["recovery", "running"])

    # Monkey-patch project_evidence_card so the SECOND call raises;
    # the first card insert succeeds, then the second fails. The
    # synthesis transaction should roll back and leave NO cards
    # AND no daily_plan / recommendation_log rows behind.
    from health_agent_infra.core import synthesis as synthesis_mod
    real = synthesis_mod.project_evidence_card
    call_count = {"n": 0}

    def flaky(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise RuntimeError("simulated card-insert failure")
        return real(*args, **kwargs)

    monkeypatch.setattr(synthesis_mod, "project_evidence_card", flaky)

    conn = open_connection(db_path)
    try:
        with pytest.raises(RuntimeError, match="simulated card-insert"):
            run_synthesis(
                conn, for_date=FOR_DATE, user_id=USER,
                snapshot=_quiet_snapshot(),
            )

        # All four lanes rolled back together.
        n_cards = conn.execute(
            "SELECT COUNT(*) FROM recommendation_evidence_card"
        ).fetchone()[0]
        n_recs = conn.execute(
            "SELECT COUNT(*) FROM recommendation_log "
            "WHERE for_date = ?",
            (FOR_DATE.isoformat(),),
        ).fetchone()[0]
        n_plans = conn.execute(
            "SELECT COUNT(*) FROM daily_plan "
            "WHERE for_date = ?",
            (FOR_DATE.isoformat(),),
        ).fetchone()[0]
        n_planned = conn.execute(
            "SELECT COUNT(*) FROM planned_recommendation "
            "WHERE for_date = ?",
            (FOR_DATE.isoformat(),),
        ).fetchone()[0]
        assert n_cards == 0
        assert n_recs == 0
        assert n_plans == 0
        assert n_planned == 0
    finally:
        conn.close()


def test_synthesis_card_payload_carries_recommendation_id_and_domain(
    tmp_path: Path,
):
    db_path = tmp_path / "state.db"
    _seed_proposals(db_path, ["recovery"])
    conn = open_connection(db_path)
    try:
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_quiet_snapshot(),
        )
        row = conn.execute(
            "SELECT recommendation_id, domain, payload_json "
            "FROM recommendation_evidence_card LIMIT 1"
        ).fetchone()
        assert row is not None
        rec_id, domain, payload_json = row[0], row[1], row[2]
        payload = json.loads(payload_json)
        assert payload["decision"]["domain"] == domain
        # Self-reference: the rec_id appears in the recommendation_log
        # audit-chain ref lane.
        assert rec_id in payload["provenance"]["recommendation_log"]
        # Each card validates re-loaded against the v1 schema.
        validate_evidence_card_payload(payload)
    finally:
        conn.close()


def test_synthesis_card_carries_audit_chain_refs(tmp_path: Path):
    """Acceptance #4: payload separation per F-PHASE0-12 — audit-chain
    refs go in payload lanes (NOT as SourceRowLocator instances)."""
    db_path = tmp_path / "state.db"
    _seed_proposals(db_path, ["recovery"])
    conn = open_connection(db_path)
    try:
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_quiet_snapshot(),
        )
        row = conn.execute(
            "SELECT payload_json FROM recommendation_evidence_card LIMIT 1"
        ).fetchone()
        payload = json.loads(row[0])
        prov = payload["provenance"]
        # Audit-chain lanes exist as plain-PK arrays, NOT locator dicts.
        assert isinstance(prov["proposal_log"], list)
        assert isinstance(prov["planned_recommendation"], list)
        assert isinstance(prov["recommendation_log"], list)
        assert len(prov["proposal_log"]) == 1
        assert len(prov["planned_recommendation"]) == 1
        # The strings are PK refs, not dicts.
        for entry in (
            prov["proposal_log"]
            + prov["planned_recommendation"]
            + prov["recommendation_log"]
        ):
            assert isinstance(entry, str)
        # Provenance locator lanes are still empty for recovery R6's
        # "didn't fire" path (the spike rule did not trigger), so
        # accepted_state_rows + raw_source_refs are [].
        assert prov["accepted_state_rows"] == []
        assert prov["raw_source_refs"] == []
    finally:
        conn.close()


def test_canonical_replace_path_deletes_old_cards(tmp_path: Path):
    """When run_synthesis is re-run on the same canonical day,
    delete_canonical_plan_cascade prunes the old cards before the
    new daily_plan + recommendation_log + cards land. No orphan
    cards should persist post-second-synthesis."""
    db_path = tmp_path / "state.db"
    _seed_proposals(db_path, ["recovery"])
    conn = open_connection(db_path)
    try:
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_quiet_snapshot(),
        )
        first_count = conn.execute(
            "SELECT COUNT(*) FROM recommendation_evidence_card"
        ).fetchone()[0]
        assert first_count == 1

        # Re-synthesize (canonical replace path).
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_quiet_snapshot(),
        )
        second_count = conn.execute(
            "SELECT COUNT(*) FROM recommendation_evidence_card"
        ).fetchone()[0]
        assert second_count == 1  # not 2 — old card was cascaded out
    finally:
        conn.close()


def test_explain_bundle_surfaces_evidence_cards(tmp_path: Path):
    """Acceptance #5: hai explain --json includes evidence_cards
    field with one entry per card for the requested plan."""
    from health_agent_infra.core.explain.queries import load_bundle_for_date
    from health_agent_infra.core.explain.render import bundle_to_dict

    db_path = tmp_path / "state.db"
    _seed_proposals(db_path, ["recovery", "running"])
    conn = open_connection(db_path)
    try:
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_quiet_snapshot(),
        )
        bundle = load_bundle_for_date(
            conn, for_date=FOR_DATE, user_id=USER,
        )
        assert len(bundle.evidence_cards) == 2
        bundle_dict = bundle_to_dict(bundle)
        assert "evidence_cards" in bundle_dict
        assert len(bundle_dict["evidence_cards"]) == 2
        # Each surfaced card carries the canonical fields.
        for card in bundle_dict["evidence_cards"]:
            assert {
                "card_id", "daily_plan_id", "recommendation_id",
                "domain", "schema_version", "payload", "computed_at",
            }.issubset(card.keys())
            assert card["schema_version"] == EVIDENCE_CARD_SCHEMA_VERSION
            # Cross-reference to recommendation_log: card.rec_id appears
            # in the corresponding ExplainRecommendation.
            rec_ids = {r.recommendation_id for r in bundle.recommendations}
            assert card["recommendation_id"] in rec_ids
    finally:
        conn.close()


def test_explain_bundle_evidence_cards_is_empty_list_for_legacy_plan(
    tmp_path: Path,
):
    """A plan whose synthesis ran fine but had its evidence-card rows
    pruned out-of-band still loads cleanly with evidence_cards=[]."""
    from health_agent_infra.core.explain.queries import load_bundle_for_date

    db_path = tmp_path / "state.db"
    _seed_proposals(db_path, ["recovery"])
    conn = open_connection(db_path)
    try:
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_quiet_snapshot(),
        )
        # Manually wipe the cards (simulates legacy / pre-W-EVCARD-DAILY plan).
        conn.execute("DELETE FROM recommendation_evidence_card")
        conn.commit()
        bundle = load_bundle_for_date(
            conn, for_date=FOR_DATE, user_id=USER,
        )
        assert bundle.evidence_cards == []
    finally:
        conn.close()


def test_card_planned_id_reference_set_null_when_planned_row_deleted(
    tmp_path: Path,
):
    """Migration 027's ``ON DELETE SET NULL`` on planned_id keeps the
    card as audit-trail when planned rows are pruned independently of
    the daily_plan cascade."""
    db_path = tmp_path / "state.db"
    _seed_proposals(db_path, ["recovery"])
    conn = open_connection(db_path)
    try:
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_quiet_snapshot(),
        )
        # Verify planned_id populated, then drop the planned row.
        before = conn.execute(
            "SELECT planned_id FROM recommendation_evidence_card LIMIT 1"
        ).fetchone()
        assert before[0] is not None

        # Drop the planned row directly; the FK should null the card's
        # planned_id rather than block the delete.
        conn.execute("DELETE FROM planned_recommendation")
        after = conn.execute(
            "SELECT planned_id FROM recommendation_evidence_card LIMIT 1"
        ).fetchone()
        assert after[0] is None  # FK ON DELETE SET NULL fired
        # Card still exists (audit-trail preserved).
        n = conn.execute(
            "SELECT COUNT(*) FROM recommendation_evidence_card"
        ).fetchone()[0]
        assert n == 1
    finally:
        conn.close()
