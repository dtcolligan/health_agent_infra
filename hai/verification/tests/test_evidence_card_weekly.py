"""W-EVCARD-WEEKLY — weekly claim-card carrier (v0.2.0 §2.C).

Tests cover acceptance items 1-4 + 6 from PLAN §2.C:
  #1 migration 028 lands; weekly_claim_card table + indexes created
  #2 card construction validates: locator entries per W-PROV-1;
     audit_refs as plain-PK arrays per F-PHASE0-12
  #3 claim_id hashing is deterministic
  #4 append-only audit history (re-run with corrected data → new
     row + new card_id; superseded rows remain)
  #6 test count grows ≥ 8 vs W-EVCARD-DAILY baseline (this file
     targets 12+)

Acceptance #5 (hai review weekly --json default canonical-latest +
--include-history flag) is owned by the W52 workstream (§2.D); the
underlying load_canonical_latest_for_week + load_full_history_for_week
helpers tested here are what W52 will consume.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.core.review.weekly_card import (
    WEEKLY_CARD_SCHEMA_VERSION,
    WeeklyCardValidationError,
    compute_claim_id,
    load_canonical_latest_for_week,
    load_full_history_for_week,
    project_weekly_card,
    validate_weekly_card_fields,
)
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


_VALID_LOCATOR = {
    "table": "accepted_recovery_state_daily",
    "pk": {"as_of_date": "2026-05-04", "user_id": "u_local_1"},
    "row_version": "2026-05-04T07:00:00Z",
}


def _db(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return open_connection(db_path)


# ---------------------------------------------------------------------------
# Migration 028 — acceptance #1
# ---------------------------------------------------------------------------


def test_migration_028_creates_weekly_claim_card_table(tmp_path: Path):
    conn = _db(tmp_path)
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='weekly_claim_card'"
        )
        assert cur.fetchone() is not None
        cols = {
            row[1] for row in conn.execute(
                "PRAGMA table_info(weekly_claim_card)"
            )
        }
        assert {
            "card_id", "user_id", "iso_week", "claim_id",
            "claim_atom_text", "atom_type", "derivation_path",
            "locator_set_json", "audit_refs_json", "computed_at",
            "source", "ingest_actor", "agent_version",
        }.issubset(cols)
    finally:
        conn.close()


def test_migration_028_creates_indexes(tmp_path: Path):
    conn = _db(tmp_path)
    try:
        idx = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='weekly_claim_card'"
            )
        }
        assert "idx_weekly_card_iso_week" in idx
        assert "idx_weekly_card_claim_id" in idx
    finally:
        conn.close()


def test_migration_028_check_constraint_rejects_bad_atom_type(tmp_path: Path):
    """The CHECK constraint is part of the schema contract — a direct
    SQL insert with atom_type='qualitative' must be rejected."""
    import sqlite3
    conn = _db(tmp_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO weekly_claim_card ("
                "card_id, user_id, iso_week, claim_id, claim_atom_text, "
                "atom_type, derivation_path, locator_set_json, "
                "audit_refs_json, computed_at, source, ingest_actor"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "x", "u", "2026-W18", "c", "x",
                    "qualitative",  # not in CHECK enum
                    "literal",
                    "[]", "{}", "2026-05-04T00:00:00Z",
                    "test", "test",
                ),
            )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Field validator — acceptance #2
# ---------------------------------------------------------------------------


def test_validator_accepts_minimal_valid_card():
    validate_weekly_card_fields(
        iso_week="2026-W18",
        claim_atom_text="Average sleep was 7.4 hours.",
        atom_type="quantitative",
        derivation_path="aggregate",
        locator_set=[_VALID_LOCATOR],
        audit_refs={"recommendation_log": ["rec_a", "rec_b"]},
    )


def test_validator_rejects_invalid_atom_type():
    with pytest.raises(WeeklyCardValidationError) as exc:
        validate_weekly_card_fields(
            iso_week="2026-W18",
            claim_atom_text="x",
            atom_type="qualitative",  # not allowed
            derivation_path="aggregate",
            locator_set=[],
            audit_refs={},
        )
    assert exc.value.invariant == "atom_type_enum"


def test_validator_rejects_invalid_derivation_path():
    with pytest.raises(WeeklyCardValidationError) as exc:
        validate_weekly_card_fields(
            iso_week="2026-W18",
            claim_atom_text="x",
            atom_type="quantitative",
            derivation_path="opinion",  # not allowed
            locator_set=[],
            audit_refs={},
        )
    assert exc.value.invariant == "derivation_path_enum"


def test_validator_rejects_locator_with_unwhitelisted_table():
    bad = {
        "table": "recommendation_log",  # write-side audit-chain
        "pk": {"recommendation_id": "x"},
        "row_version": "2026-05-04T00:00:00Z",
    }
    with pytest.raises(WeeklyCardValidationError) as exc:
        validate_weekly_card_fields(
            iso_week="2026-W18",
            claim_atom_text="x",
            atom_type="quantitative",
            derivation_path="literal",
            locator_set=[bad],
            audit_refs={},
        )
    assert exc.value.invariant == "locator_set_entry"


def test_validator_accepts_audit_refs_with_composite_pk_dicts():
    """Per F-PHASE0-12 — audit_refs values may be scalar PKs or
    composite-PK dicts. ``data_quality_daily`` uses composite PK
    ``{"as_of_date": ..., "user_id": ...}``."""
    validate_weekly_card_fields(
        iso_week="2026-W18",
        claim_atom_text="x",
        atom_type="quantitative",
        derivation_path="literal",
        locator_set=[],
        audit_refs={
            "recommendation_log": ["rec_a"],
            "x_rule_firing": [1, 2, 3],
            "data_quality_daily": [
                {"as_of_date": "2026-05-04", "user_id": "u_local_1"},
            ],
        },
    )


def test_validator_rejects_audit_refs_non_list_value():
    with pytest.raises(WeeklyCardValidationError) as exc:
        validate_weekly_card_fields(
            iso_week="2026-W18",
            claim_atom_text="x",
            atom_type="quantitative",
            derivation_path="literal",
            locator_set=[],
            audit_refs={"recommendation_log": "not_a_list"},
        )
    assert exc.value.invariant == "audit_refs_entry_shape"


# ---------------------------------------------------------------------------
# claim_id determinism — acceptance #3
# ---------------------------------------------------------------------------


def test_claim_id_is_deterministic_for_identical_content():
    args = dict(
        iso_week="2026-W18",
        user_id="u_local_1",
        claim_atom_text="Average sleep was 7.4 hours.",
        derivation_path="aggregate",
        locator_set=[_VALID_LOCATOR],
    )
    a = compute_claim_id(**args)
    b = compute_claim_id(**args)
    assert a == b


def test_claim_id_changes_when_prose_changes():
    base = dict(
        iso_week="2026-W18",
        user_id="u_local_1",
        derivation_path="aggregate",
        locator_set=[_VALID_LOCATOR],
    )
    a = compute_claim_id(**base, claim_atom_text="Sleep avg 7.4h")
    b = compute_claim_id(**base, claim_atom_text="Sleep avg 7.5h")
    assert a != b


def test_claim_id_invariant_to_locator_order():
    loc1 = dict(_VALID_LOCATOR)
    loc2 = dict(_VALID_LOCATOR, pk={"as_of_date": "2026-05-05", "user_id": "u"})
    a = compute_claim_id(
        iso_week="2026-W18",
        user_id="u",
        claim_atom_text="x",
        derivation_path="aggregate",
        locator_set=[loc1, loc2],
    )
    b = compute_claim_id(
        iso_week="2026-W18",
        user_id="u",
        claim_atom_text="x",
        derivation_path="aggregate",
        locator_set=[loc2, loc1],  # reversed
    )
    assert a == b


# ---------------------------------------------------------------------------
# Append-only audit history — acceptance #4
# ---------------------------------------------------------------------------


def test_append_only_history_two_runs_same_content_two_rows(tmp_path: Path):
    """Re-running W52 for the same week with same data still appends a
    new row (different card_id; same claim_id; newer computed_at).
    The canonical-latest view returns just 1 row; the full history
    returns both."""
    conn = _db(tmp_path)
    try:
        first = project_weekly_card(
            conn,
            user_id="u",
            iso_week="2026-W18",
            claim_atom_text="Sleep avg 7.4h",
            atom_type="quantitative",
            derivation_path="aggregate",
            locator_set=[_VALID_LOCATOR],
            audit_refs={"recommendation_log": ["rec_a"]},
            computed_at="2026-05-04T08:00:00Z",
            commit_after=False,
        )
        second = project_weekly_card(
            conn,
            user_id="u",
            iso_week="2026-W18",
            claim_atom_text="Sleep avg 7.4h",
            atom_type="quantitative",
            derivation_path="aggregate",
            locator_set=[_VALID_LOCATOR],
            audit_refs={"recommendation_log": ["rec_a"]},
            computed_at="2026-05-04T09:00:00Z",
            commit_after=False,
        )
        conn.commit()

        # Same content → same claim_id; new card_id per row.
        assert first["claim_id"] == second["claim_id"]
        assert first["card_id"] != second["card_id"]

        full = load_full_history_for_week(conn, user_id="u", iso_week="2026-W18")
        assert len(full) == 2

        latest = load_canonical_latest_for_week(
            conn, user_id="u", iso_week="2026-W18",
        )
        assert len(latest) == 1
        # Latest is the second (newer computed_at).
        assert latest[0]["card_id"] == second["card_id"]
    finally:
        conn.close()


def test_append_only_history_corrected_prose_creates_distinct_claim(tmp_path: Path):
    """When W52 re-runs with corrected data and the prose changes,
    the new card has a NEW claim_id; the canonical-latest view
    surfaces both claims (they're different claims, not different
    versions of the same claim)."""
    conn = _db(tmp_path)
    try:
        project_weekly_card(
            conn,
            user_id="u",
            iso_week="2026-W18",
            claim_atom_text="Sleep avg 7.4h",
            atom_type="quantitative",
            derivation_path="aggregate",
            locator_set=[_VALID_LOCATOR],
            audit_refs={"recommendation_log": ["rec_a"]},
            computed_at="2026-05-04T08:00:00Z",
            commit_after=False,
        )
        project_weekly_card(
            conn,
            user_id="u",
            iso_week="2026-W18",
            claim_atom_text="Sleep avg 7.6h",  # corrected number
            atom_type="quantitative",
            derivation_path="aggregate",
            locator_set=[_VALID_LOCATOR],
            audit_refs={"recommendation_log": ["rec_a"]},
            computed_at="2026-05-04T09:00:00Z",
            commit_after=False,
        )
        conn.commit()

        latest = load_canonical_latest_for_week(
            conn, user_id="u", iso_week="2026-W18",
        )
        # Two distinct claims (different prose) → 2 rows in canonical view.
        assert len(latest) == 2

        full = load_full_history_for_week(
            conn, user_id="u", iso_week="2026-W18",
        )
        assert len(full) == 2  # 1 row per claim
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Payload separation persistence — acceptance #2 (round-trip)
# ---------------------------------------------------------------------------


def test_persisted_card_round_trips_locator_and_audit_refs(tmp_path: Path):
    conn = _db(tmp_path)
    try:
        project_weekly_card(
            conn,
            user_id="u",
            iso_week="2026-W18",
            claim_atom_text="x",
            atom_type="comparative",
            derivation_path="comparison",
            locator_set=[_VALID_LOCATOR],
            audit_refs={
                "recommendation_log": ["rec_a"],
                "x_rule_firing": [1, 2],
                "data_quality_daily": [
                    {"as_of_date": "2026-05-04", "user_id": "u"},
                ],
            },
            commit_after=True,
        )
        latest = load_canonical_latest_for_week(
            conn, user_id="u", iso_week="2026-W18",
        )
        assert len(latest) == 1
        card = latest[0]
        # Locator round-trips.
        assert card["locator_set"] == [_VALID_LOCATOR]
        # Audit-refs round-trip with mixed scalar + composite-PK.
        assert card["audit_refs"]["recommendation_log"] == ["rec_a"]
        assert card["audit_refs"]["x_rule_firing"] == [1, 2]
        assert (
            card["audit_refs"]["data_quality_daily"]
            == [{"as_of_date": "2026-05-04", "user_id": "u"}]
        )
        assert card["atom_type"] == "comparative"
        assert card["derivation_path"] == "comparison"
    finally:
        conn.close()
