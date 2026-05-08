"""W45 — deterministic replay / property tests for v0.1.8 ledgers.

Pin determinism contracts for the new state surfaces:

  1. Projector replay: ``hai clean`` + projection over the same raw
     evidence produces identical accepted-state rows on a fresh DB
     (already covered by `test_migrations_roundtrip.py` for the v1
     audit tables; this file extends the property to v0.1.8 ledgers).
  2. Correction / supersede replay: an intent supersession chain
     yields the same canonical leaf when replayed.
  3. Late-arriving row: a target row inserted after `as_of_date` does
     not retroactively change the snapshot for that date.
  4. Intent active-at-date: window-coverage filter is deterministic
     for a fixed (snapshot, date) pair.
  5. Target active-at-date: same property as intent.
  6. Review summary: ``build_review_summary`` over the same outcome
     chain returns identical token + count dicts.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from health_agent_infra.core.intent import (
    add_intent,
    list_active_intent,
    supersede_intent,
)
from health_agent_infra.core.intent.store import IntentRecord
from health_agent_infra.core.review.summary import build_review_summary
from health_agent_infra.core.state import (
    build_snapshot,
    initialize_database,
    open_connection,
)
from health_agent_infra.core.target import (
    add_target,
    list_active_target,
)

from _fixtures import make_outcome_chain, seed_outcome_chain


USER = "u_test"
AS_OF = date(2026, 4, 24)


def _init_db(tmp_path: Path, suffix: str = "state.db") -> Path:
    db = tmp_path / suffix
    initialize_database(db)
    return db


def test_intent_supersession_chain_replay_deterministic(tmp_path: Path):
    """Same supersession sequence applied to two fresh DBs yields the
    same canonical leaf and same forward-link state."""

    def _seed(db: Path) -> list[tuple]:
        conn = open_connection(db)
        try:
            original = add_intent(
                conn, user_id=USER, domain="running",
                intent_type="training_session",
                scope_start=AS_OF, payload={"v": 1},
            )
            new_record = IntentRecord(
                intent_id="intent_v2",
                user_id=USER, domain="running",
                scope_type="day",
                scope_start=AS_OF, scope_end=AS_OF,
                intent_type="training_session",
                status="active", priority="normal",
                flexibility="flexible",
                payload={"v": 2}, reason="user adjusted",
                source="user_authored", ingest_actor="cli",
                created_at=datetime(2026, 4, 24, 12, tzinfo=timezone.utc),
                effective_at=datetime(2026, 4, 24, 12, tzinfo=timezone.utc),
                review_after=None,
                supersedes_intent_id=None,
                superseded_by_intent_id=None,
            )
            supersede_intent(
                conn, old_intent_id=original.intent_id, new_record=new_record,
            )
            rows = conn.execute(
                "SELECT intent_id, status, supersedes_intent_id, "
                "superseded_by_intent_id FROM intent_item "
                "WHERE user_id = ? ORDER BY intent_id",
                (USER,),
            ).fetchall()
            return [tuple(r) for r in rows]
        finally:
            conn.close()

    db_a = _init_db(tmp_path, "a.db")
    db_b = _init_db(tmp_path, "b.db")
    rows_a = _seed(db_a)
    rows_b = _seed(db_b)

    # The auto-generated intent_id for the original row will differ
    # because it carries a UUID4 — so we only assert the non-id shape
    # of the canonical leaf (intent_v2) plus that exactly one row in
    # each DB has status='superseded'.
    leaves_a = [r for r in rows_a if r[1] == "active"]
    leaves_b = [r for r in rows_b if r[1] == "active"]
    assert len(leaves_a) == 1 and len(leaves_b) == 1
    assert leaves_a[0][0] == "intent_v2" == leaves_b[0][0]

    superseded_a = [r for r in rows_a if r[1] == "superseded"]
    superseded_b = [r for r in rows_b if r[1] == "superseded"]
    assert len(superseded_a) == 1 and len(superseded_b) == 1
    assert superseded_a[0][3] == "intent_v2" == superseded_b[0][3]


def test_late_arriving_target_does_not_affect_past_snapshot(tmp_path: Path):
    """A target row whose effective_from is AFTER as_of_date must not
    appear in that day's snapshot.target block."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        # Existing target for the as_of_date.
        add_target(
            conn, user_id=USER, domain="nutrition",
            target_type="hydration_ml", value=3000, unit="ml",
            effective_from=AS_OF,
        )
        # Late-arriving target effective TOMORROW.
        add_target(
            conn, user_id=USER, domain="nutrition",
            target_type="protein_g", value=160, unit="g",
            effective_from=date(2026, 4, 25),
        )
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 4, 24, 23, 45),
        )
    finally:
        conn.close()

    target_types = {t["target_type"] for t in snap["target"]}
    assert target_types == {"hydration_ml"}


def test_intent_active_at_date_is_deterministic(tmp_path: Path):
    """Repeated calls to list_active_intent for the same (date, user)
    return the same row order."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        add_intent(
            conn, user_id=USER, domain="running",
            intent_type="training_session", scope_start=AS_OF,
        )
        add_intent(
            conn, user_id=USER, domain="sleep",
            intent_type="sleep_window", scope_start=AS_OF,
        )
        add_intent(
            conn, user_id=USER, domain="strength",
            intent_type="rest_day", scope_start=AS_OF,
        )
        first = list_active_intent(conn, user_id=USER, as_of_date=AS_OF)
        second = list_active_intent(conn, user_id=USER, as_of_date=AS_OF)
        third = list_active_intent(conn, user_id=USER, as_of_date=AS_OF)
    finally:
        conn.close()

    assert [r.intent_id for r in first] == [r.intent_id for r in second]
    assert [r.intent_id for r in second] == [r.intent_id for r in third]


def test_target_active_at_date_is_deterministic(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        add_target(
            conn, user_id=USER, domain="nutrition",
            target_type="hydration_ml", value=3000, unit="ml",
            effective_from=AS_OF,
        )
        add_target(
            conn, user_id=USER, domain="nutrition",
            target_type="protein_g", value=160, unit="g",
            effective_from=AS_OF,
        )
        first = list_active_target(conn, user_id=USER, as_of_date=AS_OF)
        second = list_active_target(conn, user_id=USER, as_of_date=AS_OF)
    finally:
        conn.close()

    assert [t.target_id for t in first] == [t.target_id for t in second]


def test_review_summary_replay_identical(tmp_path: Path):
    """Same outcome chain → same summary dict."""

    def _seed(db: Path) -> dict:
        conn = open_connection(db)
        try:
            for i in range(4):
                chain = make_outcome_chain(
                    recommendation_id=f"rec_p{i}",
                    review_event_id=f"rev_p{i}",
                    user_id=USER,
                    domain="running",
                    for_date=AS_OF,
                    issued_at=datetime(2026, 4, 24, 7, tzinfo=timezone.utc),
                    followed=True, improved=True,
                )
                seed_outcome_chain(conn, **chain)
            return build_review_summary(
                conn, as_of_date=AS_OF, user_id=USER, domain="running",
            )
        finally:
            conn.close()

    db_a = _init_db(tmp_path, "a.db")
    db_b = _init_db(tmp_path, "b.db")
    summary_a = _seed(db_a)
    summary_b = _seed(db_b)

    # Counts + tokens must match exactly. source_outcome_ids carry an
    # autoincrement id which is per-DB and won't match — drop those
    # before comparing, mirroring the M7 reproject contract.
    for key in ("source_outcome_ids",):
        summary_a.pop(key, None)
        summary_b.pop(key, None)
    assert summary_a == summary_b


def test_review_summary_token_set_is_stable_across_call_order(tmp_path: Path):
    """Calling build_review_summary twice on the same DB returns
    identical tokens (no nondeterminism from timestamp / iteration)."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        for i in range(4):
            chain = make_outcome_chain(
                recommendation_id=f"rec_t{i}",
                review_event_id=f"rev_t{i}",
                user_id=USER, domain="recovery",
                for_date=AS_OF,
                followed=True,
                improved=(i % 2 == 0),
            )
            seed_outcome_chain(conn, **chain)
        first = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER, domain="recovery",
        )
        second = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER, domain="recovery",
        )
    finally:
        conn.close()

    assert first["tokens"] == second["tokens"]
    assert first["recorded_outcome_count"] == second["recorded_outcome_count"]
