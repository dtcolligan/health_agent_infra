"""Core tests for the Phase D user-memory module.

Covers the acceptance criteria called out in
``hai/reporting/plans/historical/post_v0_1_roadmap.md`` §5 Phase D that do not run
through the ``hai memory`` CLI (the CLI path has its own test in
``test_cli_memory.py``):

- migration 007 lands the ``user_memory`` table with the expected
  shape (PK, CHECK constraint on category enum);
- ``insert_memory_entry`` / ``archive_memory_entry`` /
  ``list_memory_entries`` round-trip correctly, including
  ``archived_at`` soft-delete semantics;
- ``build_user_memory_bundle`` returns entries active at a given
  ``as_of`` date, including entries archived later than the date and
  excluding entries archived before it;
- the schema validators reject empty / unknown values loudly.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.core.memory import (
    UserMemoryEntry,
    UserMemoryValidationError,
    archive_memory_entry,
    build_user_memory_bundle,
    bundle_to_dict,
    insert_memory_entry,
    list_memory_entries,
    read_memory_entry,
)
from health_agent_infra.core.memory.schemas import (
    USER_MEMORY_CATEGORIES,
    validate_category,
    validate_domain,
    validate_value,
)
from health_agent_infra.core.state import (
    current_schema_version,
    initialize_database,
    open_connection,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path) -> Path:
    path = tmp_path / "state.db"
    initialize_database(path)
    return path


def _entry(
    *,
    memory_id: str,
    user_id: str = "u_local_1",
    category: str = "goal",
    value: str = "build strength through June",
    key: str | None = None,
    domain: str | None = None,
    created_at: datetime | None = None,
    archived_at: datetime | None = None,
    source: str = "user_manual",
    ingest_actor: str = "hai_cli_direct",
) -> UserMemoryEntry:
    return UserMemoryEntry(
        memory_id=memory_id,
        user_id=user_id,
        category=category,  # type: ignore[arg-type]
        value=value,
        key=key,
        domain=domain,
        created_at=created_at or datetime(2026, 4, 10, 12, 0, tzinfo=timezone.utc),
        archived_at=archived_at,
        source=source,
        ingest_actor=ingest_actor,
    )


# ---------------------------------------------------------------------------
# Migration 007 — schema landing
# ---------------------------------------------------------------------------


def test_migration_007_creates_user_memory_table(db_path):
    """The table shape must match the dataclass so the store and the
    projector never drift from the DDL."""

    conn = open_connection(db_path)
    try:
        assert current_schema_version(conn) >= 7, (
            "migration 007 must be applied by initialize_database"
        )
        cols = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(user_memory)").fetchall()
        }
    finally:
        conn.close()

    expected = {
        "memory_id", "user_id", "category", "key", "value", "domain",
        "created_at", "archived_at", "source", "ingest_actor",
    }
    assert expected <= cols, f"missing columns: {expected - cols}"


def test_user_memory_category_check_constraint(db_path):
    """A raw INSERT with an unknown category must be rejected by SQLite,
    not just by Python validation — this ensures the DDL itself pins
    the enum even if a bad caller bypasses the store."""

    conn = open_connection(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO user_memory (memory_id, user_id, category, "
                "value, created_at, source, ingest_actor) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    "m1", "u", "not_a_category", "v",
                    "2026-04-10T12:00:00+00:00",
                    "user_manual", "hai_cli_direct",
                ),
            )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Store — insert / archive / list / read
# ---------------------------------------------------------------------------


def test_insert_and_read_round_trip(db_path):
    conn = open_connection(db_path)
    try:
        entry = _entry(memory_id="m_goal_1", category="goal", key="primary_goal")
        inserted = insert_memory_entry(conn, entry)
        assert inserted is True

        fetched = read_memory_entry(conn, memory_id="m_goal_1")
        assert fetched is not None
        assert fetched.user_id == entry.user_id
        assert fetched.category == "goal"
        assert fetched.key == "primary_goal"
        assert fetched.value == entry.value
        assert fetched.archived_at is None
        # Timestamps round-trip as tz-aware datetimes.
        assert fetched.created_at == entry.created_at
    finally:
        conn.close()


def test_insert_is_idempotent_on_memory_id(db_path):
    """Re-inserting the same memory_id is a no-op — same contract as the
    other projectors (context_note, recommendation_log)."""

    conn = open_connection(db_path)
    try:
        entry = _entry(memory_id="m_dup", category="preference")
        assert insert_memory_entry(conn, entry) is True
        assert insert_memory_entry(conn, entry) is False
        rows = list_memory_entries(conn, user_id="u_local_1")
        assert len(rows) == 1
    finally:
        conn.close()


def test_archive_soft_deletes_without_removing_row(db_path):
    conn = open_connection(db_path)
    try:
        entry = _entry(memory_id="m_arch", category="constraint")
        insert_memory_entry(conn, entry)

        stamp = datetime(2026, 4, 15, 10, 0, tzinfo=timezone.utc)
        archived = archive_memory_entry(
            conn, memory_id="m_arch", archived_at=stamp,
        )
        assert archived is True

        # The row is still on disk.
        refreshed = read_memory_entry(conn, memory_id="m_arch")
        assert refreshed is not None
        assert refreshed.archived_at == stamp

        # Default list excludes archived.
        active = list_memory_entries(conn, user_id="u_local_1")
        assert active == []

        # include_archived=True returns it.
        everything = list_memory_entries(
            conn, user_id="u_local_1", include_archived=True,
        )
        assert len(everything) == 1
        assert everything[0].memory_id == "m_arch"
    finally:
        conn.close()


def test_archive_returns_false_for_unknown_and_already_archived(db_path):
    conn = open_connection(db_path)
    try:
        assert archive_memory_entry(conn, memory_id="nope") is False

        entry = _entry(memory_id="m_once", category="context")
        insert_memory_entry(conn, entry)
        assert archive_memory_entry(conn, memory_id="m_once") is True
        assert archive_memory_entry(conn, memory_id="m_once") is False
    finally:
        conn.close()


def test_list_filters_by_user_and_category(db_path):
    conn = open_connection(db_path)
    try:
        insert_memory_entry(conn, _entry(
            memory_id="a",
            user_id="alice",
            category="goal",
            created_at=datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc),
        ))
        insert_memory_entry(conn, _entry(
            memory_id="b",
            user_id="alice",
            category="preference",
            created_at=datetime(2026, 4, 2, 9, 0, tzinfo=timezone.utc),
        ))
        insert_memory_entry(conn, _entry(
            memory_id="c",
            user_id="bob",
            category="goal",
            created_at=datetime(2026, 4, 3, 9, 0, tzinfo=timezone.utc),
        ))

        alice_all = list_memory_entries(conn, user_id="alice")
        assert [e.memory_id for e in alice_all] == ["a", "b"]

        alice_goals = list_memory_entries(
            conn, user_id="alice", category="goal",
        )
        assert [e.memory_id for e in alice_goals] == ["a"]

        every_goal = list_memory_entries(conn, category="goal")
        assert sorted(e.memory_id for e in every_goal) == ["a", "c"]
    finally:
        conn.close()


def test_list_rejects_unknown_category(db_path):
    conn = open_connection(db_path)
    try:
        with pytest.raises(UserMemoryValidationError) as excinfo:
            list_memory_entries(conn, category="not_real")
        assert excinfo.value.invariant == "category_enum"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Projector — active-at-as_of semantics
# ---------------------------------------------------------------------------


def test_bundle_filters_by_as_of_date_inclusive_of_same_day_entries(db_path):
    """An entry created earlier on ``for_date`` must show up in the
    bundle for that date — the projector treats ``as_of_date`` as
    end-of-day UTC."""

    conn = open_connection(db_path)
    try:
        insert_memory_entry(conn, _entry(
            memory_id="same_day",
            category="goal",
            created_at=datetime(2026, 4, 17, 6, 0, tzinfo=timezone.utc),
        ))
        insert_memory_entry(conn, _entry(
            memory_id="future",
            category="goal",
            created_at=datetime(2026, 4, 18, 6, 0, tzinfo=timezone.utc),
        ))

        bundle = build_user_memory_bundle(
            conn, user_id="u_local_1", as_of=date(2026, 4, 17),
        )
        ids = [e.memory_id for e in bundle.entries]
        assert ids == ["same_day"]
        assert bundle.counts()["goal"] == 1
        assert bundle.counts()["total"] == 1
    finally:
        conn.close()


def test_bundle_includes_entries_archived_after_as_of(db_path):
    """An entry that was active on ``as_of`` but was archived later
    must still appear in the ``as_of`` bundle — this is what makes
    `hai explain` for yesterday's plan reflect yesterday's context."""

    conn = open_connection(db_path)
    try:
        insert_memory_entry(conn, _entry(
            memory_id="still_active_then",
            category="constraint",
            created_at=datetime(2026, 4, 10, 9, 0, tzinfo=timezone.utc),
        ))
        archive_memory_entry(
            conn,
            memory_id="still_active_then",
            archived_at=datetime(2026, 4, 19, 9, 0, tzinfo=timezone.utc),
        )

        bundle_then = build_user_memory_bundle(
            conn, user_id="u_local_1", as_of=date(2026, 4, 17),
        )
        assert [e.memory_id for e in bundle_then.entries] == ["still_active_then"]

        bundle_now = build_user_memory_bundle(
            conn, user_id="u_local_1", as_of=date(2026, 4, 20),
        )
        assert bundle_now.entries == ()
    finally:
        conn.close()


def test_bundle_to_dict_shape(db_path):
    """The dict shape is the contract snapshot + explain both read."""

    conn = open_connection(db_path)
    try:
        insert_memory_entry(conn, _entry(
            memory_id="m1",
            category="preference",
            key="time_of_day",
            value="no hard runs before 09:00",
            domain="running",
            created_at=datetime(2026, 4, 15, 8, 0, tzinfo=timezone.utc),
        ))
        bundle = build_user_memory_bundle(
            conn, user_id="u_local_1", as_of=date(2026, 4, 17),
        )
        payload = bundle_to_dict(bundle)

        assert set(payload.keys()) == {"as_of", "counts", "entries"}
        assert payload["as_of"] == "2026-04-17T23:59:59+00:00"
        assert payload["counts"]["preference"] == 1
        assert payload["counts"]["total"] == 1
        assert len(payload["entries"]) == 1
        entry = payload["entries"][0]
        assert entry["memory_id"] == "m1"
        assert entry["category"] == "preference"
        assert entry["key"] == "time_of_day"
        assert entry["value"] == "no hard runs before 09:00"
        assert entry["domain"] == "running"
        assert entry["archived_at"] is None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


def test_validate_category_rejects_unknown():
    with pytest.raises(UserMemoryValidationError) as excinfo:
        validate_category("preferance")  # typo
    assert excinfo.value.invariant == "category_enum"


def test_validate_category_accepts_every_enum_member():
    for category in USER_MEMORY_CATEGORIES:
        assert validate_category(category) == category


def test_validate_value_rejects_empty_and_whitespace():
    with pytest.raises(UserMemoryValidationError):
        validate_value("")
    with pytest.raises(UserMemoryValidationError):
        validate_value("   \n")


def test_validate_domain_normalises_blank_to_none():
    assert validate_domain(None) is None
    assert validate_domain("") is None
    assert validate_domain("  ") is None
    assert validate_domain("running") == "running"
