"""D1 test coverage #11 — migration 013 + 014 backfill semantics.

Seed a v0.1.3-era DB (schema at version 12, before 013_proposal_revisions
landed), insert realistic pre-migration rows into ``proposal_log`` and
``daily_plan``, apply the forward migrations, then assert:

- Every existing ``proposal_log`` row becomes a canonical leaf
  (``revision = 1``, forward pointer NULL, ``superseded_at`` NULL).
- ``daily_plan`` rows with ``synthesis_meta_json.$.superseded_by`` set
  are backfilled into the new ``superseded_by_plan_id`` column; rows
  without the attribute stay canonical leaves.
- Both new indexes (``idx_proposal_log_canonical``,
  ``idx_daily_plan_canonical``) exist post-migration.

These tests are the contract check on the forward-only migration step
documented in ``reporting/plans/v0_1_4/D1_re_author_semantics.md`` —
they catch the class of regression where a future edit to 013 or 014
would silently leave an existing row in a non-leaf state (or miss the
JSON-attribute walk) and corrupt canonical-leaf reads.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from health_agent_infra.core.state.store import (
    _ensure_migrations_table,
    apply_pending_migrations,
    current_schema_version,
    discover_migrations,
    open_connection,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_V013_VERSION = 13


def _seed_pre_013_db(tmp_path: Path) -> Path:
    """Return a DB at schema version 12 (pre-013).

    Applies every packaged migration whose version is < 13. After this
    call, the DB looks like a freshly-upgraded v0.1.3 install.
    """

    db_path = tmp_path / "state.db"
    conn = open_connection(db_path)
    try:
        _ensure_migrations_table(conn)
        pre_013 = [
            (v, name, body)
            for (v, name, body) in discover_migrations()
            if v < _V013_VERSION
        ]
        apply_pending_migrations(conn, migrations=pre_013)
        assert current_schema_version(conn) == _V013_VERSION - 1
    finally:
        conn.close()
    return db_path


def _apply_remaining_migrations(db_path: Path) -> None:
    conn = open_connection(db_path)
    try:
        apply_pending_migrations(conn)
    finally:
        conn.close()


def _insert_proposal(
    conn: sqlite3.Connection,
    *,
    proposal_id: str,
    domain: str,
    for_date: str = "2026-04-22",
    user_id: str = "u_1",
    daily_plan_id: str | None = None,
) -> None:
    """Insert a proposal_log row using the pre-013 column set.

    Pre-013 ``proposal_log`` has no ``revision`` /
    ``superseded_by_proposal_id`` / ``superseded_at`` columns, so the
    INSERT must omit them. The seeding function deliberately spells
    out every column so the test would fail loudly if migration 003's
    schema ever widened (and this file would need an update).
    """

    payload = {
        "proposal_id": proposal_id,
        "domain": domain,
        "action": "proceed_with_planned_session",
        "confidence": "moderate",
    }
    conn.execute(
        """
        INSERT INTO proposal_log (
            proposal_id, daily_plan_id, user_id, domain, for_date,
            schema_version, action, confidence, payload_json,
            source, ingest_actor, agent_version, produced_at,
            validated_at, projected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            proposal_id, daily_plan_id, user_id, domain, for_date,
            f"{domain}_proposal.v1",
            "proceed_with_planned_session",
            "moderate",
            json.dumps(payload, sort_keys=True),
            "claude_agent_v1", "claude_agent_v1", "claude_agent_v1",
            "2026-04-22T06:00:00+00:00",
            "2026-04-22T06:00:00+00:00",
            "2026-04-22T06:00:00+00:00",
        ),
    )


def _insert_plan(
    conn: sqlite3.Connection,
    *,
    daily_plan_id: str,
    synthesis_meta: dict | None,
    for_date: str = "2026-04-22",
    user_id: str = "u_1",
    validated_at: str = "2026-04-22T07:00:00+00:00",
) -> None:
    """Insert a daily_plan row using the pre-014 column set.

    Pre-014 there is no ``superseded_by_plan_id`` / ``superseded_at``
    column; the supersede link (if any) lived inside the JSON blob at
    ``synthesis_meta_json.$.superseded_by``. Migration 014's backfill
    walks that attribute into the new column.
    """

    conn.execute(
        """
        INSERT INTO daily_plan (
            daily_plan_id, user_id, for_date, synthesized_at,
            recommendation_ids_json, proposal_ids_json, x_rules_fired_json,
            synthesis_meta_json, source, ingest_actor, agent_version,
            validated_at, projected_at
        ) VALUES (?, ?, ?, ?, '[]', '[]', '[]', ?, ?, ?, ?, ?, ?)
        """,
        (
            daily_plan_id, user_id, for_date,
            "2026-04-22T07:00:00+00:00",
            json.dumps(synthesis_meta, sort_keys=True) if synthesis_meta is not None else None,
            "test", "test", "test_agent",
            validated_at,
            "2026-04-22T07:00:00+00:00",
        ),
    )


def _seed_proposals_and_plans(db_path: Path) -> dict[str, object]:
    """Seed a mixed set of pre-migration rows. Returns the seeded ids
    so tests can reason about them by name.
    """

    v1_id = "plan_2026-04-22_u_1"
    v2_id = f"{v1_id}_v2"
    lone_id = "plan_2026-04-21_u_1"

    conn = open_connection(db_path)
    try:
        # Six proposals spread across domains, on one date. All of them
        # are expected to become canonical leaves post-013.
        for i, domain in enumerate(
            ("recovery", "running", "sleep", "strength", "stress", "nutrition"),
            start=1,
        ):
            _insert_proposal(
                conn,
                proposal_id=f"prop_2026-04-22_u_1_{domain}_{i:02d}",
                domain=domain,
            )
        # Plus one pre-existing proposal on a different date.
        _insert_proposal(
            conn,
            proposal_id="prop_2026-04-21_u_1_recovery_01",
            domain="recovery",
            for_date="2026-04-21",
        )

        # Plans: two in a supersede chain on 2026-04-22 (v1 → v2), plus
        # one non-superseded plan on 2026-04-21.
        _insert_plan(
            conn,
            daily_plan_id=v1_id,
            synthesis_meta={"superseded_by": v2_id, "phase_a_count": 1},
            validated_at="2026-04-22T07:00:00+00:00",
        )
        _insert_plan(
            conn,
            daily_plan_id=v2_id,
            # Leaf in the chain — no superseded_by attribute.
            synthesis_meta={"phase_a_count": 1, "supersede": True},
            validated_at="2026-04-22T12:00:00+00:00",
        )
        _insert_plan(
            conn,
            daily_plan_id=lone_id,
            synthesis_meta=None,  # Pre-014 rows often had NULL meta.
            for_date="2026-04-21",
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "v1_id": v1_id,
        "v2_id": v2_id,
        "lone_id": lone_id,
        "v1_validated_at": "2026-04-22T07:00:00+00:00",
    }


# ---------------------------------------------------------------------------
# Migration 013 — proposal_log revision backfill
# ---------------------------------------------------------------------------


def test_013_backfills_every_existing_proposal_as_canonical_leaf(tmp_path: Path):
    db_path = _seed_pre_013_db(tmp_path)
    ids = _seed_proposals_and_plans(db_path)
    _apply_remaining_migrations(db_path)

    conn = open_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT proposal_id, revision, superseded_by_proposal_id, "
            "superseded_at FROM proposal_log ORDER BY proposal_id"
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 7  # 6 on 2026-04-22 + 1 on 2026-04-21
    for row in rows:
        assert row["revision"] == 1, row["proposal_id"]
        assert row["superseded_by_proposal_id"] is None, row["proposal_id"]
        assert row["superseded_at"] is None, row["proposal_id"]

    _ = ids  # keep the return value referenced for debug parity


def test_013_installs_canonical_index(tmp_path: Path):
    db_path = _seed_pre_013_db(tmp_path)
    _apply_remaining_migrations(db_path)

    conn = open_connection(db_path)
    try:
        indexes = {
            r["name"]
            for r in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'index' AND tbl_name = 'proposal_log'"
            ).fetchall()
        }
    finally:
        conn.close()

    assert "idx_proposal_log_canonical" in indexes


# ---------------------------------------------------------------------------
# Migration 014 — daily_plan forward-link backfill
# ---------------------------------------------------------------------------


def test_014_backfills_superseded_by_from_synthesis_meta_json(tmp_path: Path):
    db_path = _seed_pre_013_db(tmp_path)
    ids = _seed_proposals_and_plans(db_path)
    _apply_remaining_migrations(db_path)

    conn = open_connection(db_path)
    try:
        rows = {
            row["daily_plan_id"]: row
            for row in conn.execute(
                "SELECT daily_plan_id, superseded_by_plan_id, superseded_at, "
                "validated_at FROM daily_plan"
            ).fetchall()
        }
    finally:
        conn.close()

    v1 = rows[ids["v1_id"]]
    v2 = rows[ids["v2_id"]]
    lone = rows[ids["lone_id"]]

    # v1 was superseded pre-014 via the JSON attribute — now in the column.
    assert v1["superseded_by_plan_id"] == ids["v2_id"]
    # Migration picks validated_at as the backfill stamp for the link time.
    assert v1["superseded_at"] == ids["v1_validated_at"]
    assert v1["superseded_at"] == v1["validated_at"]

    # v2 is the canonical leaf — no forward link.
    assert v2["superseded_by_plan_id"] is None
    assert v2["superseded_at"] is None

    # lone plan had NULL synthesis_meta_json — no forward link.
    assert lone["superseded_by_plan_id"] is None
    assert lone["superseded_at"] is None


def test_014_leaves_plans_without_superseded_by_attr_as_canonical_leaves(tmp_path: Path):
    """A plan whose synthesis_meta_json is a non-null dict without a
    ``superseded_by`` key must still land as a canonical leaf — the
    backfill walks ONLY the attribute it expects, not every dict key.
    """

    db_path = _seed_pre_013_db(tmp_path)

    # Seed a single plan whose synthesis_meta_json carries unrelated
    # attributes but no ``superseded_by``.
    conn = open_connection(db_path)
    try:
        _insert_plan(
            conn,
            daily_plan_id="plan_2026-04-20_u_1",
            synthesis_meta={"phase_a_count": 2, "phase_b_count": 0},
            for_date="2026-04-20",
        )
        conn.commit()
    finally:
        conn.close()

    _apply_remaining_migrations(db_path)

    conn = open_connection(db_path)
    try:
        row = conn.execute(
            "SELECT superseded_by_plan_id, superseded_at FROM daily_plan "
            "WHERE daily_plan_id = 'plan_2026-04-20_u_1'"
        ).fetchone()
    finally:
        conn.close()

    assert row["superseded_by_plan_id"] is None
    assert row["superseded_at"] is None


def test_014_installs_canonical_index(tmp_path: Path):
    db_path = _seed_pre_013_db(tmp_path)
    _apply_remaining_migrations(db_path)

    conn = open_connection(db_path)
    try:
        indexes = {
            r["name"]
            for r in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'index' AND tbl_name = 'daily_plan'"
            ).fetchall()
        }
    finally:
        conn.close()

    assert "idx_daily_plan_canonical" in indexes


# ---------------------------------------------------------------------------
# Whole-migration-stack sanity
# ---------------------------------------------------------------------------


def test_pre_013_seed_followed_by_full_migration_stack_reaches_head(tmp_path: Path):
    """Full round trip: pre-013 → seed → apply 013..016 → head schema."""

    db_path = _seed_pre_013_db(tmp_path)
    _seed_proposals_and_plans(db_path)
    _apply_remaining_migrations(db_path)

    conn = open_connection(db_path)
    try:
        head = current_schema_version(conn)
        # 023_source_row_locator (v0.1.14 W-PROV-1) is the current head;
        # if a future migration lands, bump the expectation here
        # deliberately.
        assert head == 23
    finally:
        conn.close()
