"""End-to-end tests for ``hai memory set | list | archive`` (Phase D).

Covers the acceptance criteria in
``hai/reporting/plans/historical/post_v0_1_roadmap.md`` §5 Phase D that flow through
the CLI:

- create / list / archive works without manual SQL;
- the entries land in SQLite and are visible to the core store;
- JSON output is structured for scripting;
- archived rows stay on disk and surface via ``--include-archived``;
- user memory appears in ``hai state snapshot`` and ``hai explain``
  under a new ``user_memory`` top-level key (no existing key mutated).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from health_agent_infra.core.schemas import (
    ReviewEvent,
    ReviewOutcome,
    canonical_daily_plan_id,
)
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_proposal,
    project_review_event,
    project_review_outcome,
)
from health_agent_infra.core.synthesis import run_synthesis
from health_agent_infra.core.writeback.proposal import PROPOSAL_SCHEMA_VERSIONS
from health_agent_infra.core import exit_codes


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path) -> Path:
    path = tmp_path / "state.db"
    initialize_database(path)
    return path


def _run(argv, capsys) -> tuple[int, dict[str, Any] | None, str]:
    """Run the CLI and return (rc, parsed_json_if_any, stderr).

    Catches ``SystemExit`` so argparse's own rejections (unknown
    ``--category`` choice, missing required args) surface as the same
    ``(rc, None, err)`` tuple callers expect.
    """

    from health_agent_infra.cli import main as cli_main

    try:
        rc = cli_main(argv)
    except SystemExit as exc:
        rc = int(exc.code) if exc.code is not None else 0
    captured = capsys.readouterr()
    parsed: dict[str, Any] | None = None
    if captured.out.strip():
        try:
            parsed = json.loads(captured.out)
        except json.JSONDecodeError:
            parsed = None
    return rc, parsed, captured.err


# ---------------------------------------------------------------------------
# hai memory set / list / archive
# ---------------------------------------------------------------------------


def test_memory_set_list_archive_round_trip(db_path, capsys):
    rc, payload, err = _run([
        "memory", "set",
        "--category", "goal",
        "--value", "build strength through June",
        "--key", "primary_goal",
        "--domain", "strength",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
    ], capsys)
    assert rc == 0, err
    assert payload is not None
    assert payload["inserted"] is True
    assert payload["category"] == "goal"
    memory_id = payload["memory_id"]
    assert memory_id.startswith("umem_u_local_1_goal_")

    # List picks it up.
    rc, payload, err = _run([
        "memory", "list",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
    ], capsys)
    assert rc == 0, err
    assert payload is not None
    ids = [e["memory_id"] for e in payload["entries"]]
    assert memory_id in ids
    assert payload["counts"]["goal"] >= 1

    # Archive it.
    rc, payload, err = _run([
        "memory", "archive",
        "--memory-id", memory_id,
        "--db-path", str(db_path),
    ], capsys)
    assert rc == 0, err
    assert payload["archived"] is True
    assert payload["archived_at"] is not None

    # Default list no longer returns the archived row.
    rc, payload, err = _run([
        "memory", "list",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
    ], capsys)
    assert rc == 0, err
    active_ids = [e["memory_id"] for e in payload["entries"]]
    assert memory_id not in active_ids

    # --include-archived returns it.
    rc, payload, err = _run([
        "memory", "list",
        "--user-id", "u_local_1",
        "--include-archived",
        "--db-path", str(db_path),
    ], capsys)
    assert rc == 0, err
    every_id = [e["memory_id"] for e in payload["entries"]]
    assert memory_id in every_id


def test_memory_set_rejects_empty_value(db_path, capsys):
    rc, payload, err = _run([
        "memory", "set",
        "--category", "preference",
        "--value", "   ",
        "--db-path", str(db_path),
    ], capsys)
    assert rc == exit_codes.USER_INPUT
    assert "invariant=value_non_empty" in err


def test_memory_set_rejects_unknown_category(db_path, capsys):
    rc, _, err = _run([
        "memory", "set",
        "--category", "preferance",  # typo
        "--value", "x",
        "--db-path", str(db_path),
    ], capsys)
    # argparse rejects with rc=2 before our handler runs — this is
    # argparse's own exit path, outside the exit_codes taxonomy.
    assert rc == 2
    assert "invalid choice" in err or "not in" in err.lower()


def test_memory_archive_unknown_memory_id_exits_2(db_path, capsys):
    rc, _, err = _run([
        "memory", "archive",
        "--memory-id", "umem_nope",
        "--db-path", str(db_path),
    ], capsys)
    assert rc == exit_codes.USER_INPUT
    assert "no entry" in err.lower()


def test_memory_archive_is_idempotent(db_path, capsys):
    rc, set_payload, _ = _run([
        "memory", "set",
        "--category", "constraint",
        "--value", "no hard running",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
    ], capsys)
    assert rc == 0
    memory_id = set_payload["memory_id"]

    rc, payload, _ = _run([
        "memory", "archive",
        "--memory-id", memory_id,
        "--db-path", str(db_path),
    ], capsys)
    assert rc == 0 and payload["archived"] is True

    rc, payload, _ = _run([
        "memory", "archive",
        "--memory-id", memory_id,
        "--db-path", str(db_path),
    ], capsys)
    assert rc == 0
    assert payload["archived"] is False  # already archived, but not an error


def test_memory_list_filters_by_category(db_path, capsys):
    # Seed two goals + one preference.
    for value, category in (
        ("build strength", "goal"),
        ("marathon PR", "goal"),
        ("no early alarms", "preference"),
    ):
        rc, _, _ = _run([
            "memory", "set",
            "--category", category,
            "--value", value,
            "--user-id", "u_local_1",
            "--db-path", str(db_path),
        ], capsys)
        assert rc == 0

    rc, payload, _ = _run([
        "memory", "list",
        "--user-id", "u_local_1",
        "--category", "goal",
        "--db-path", str(db_path),
    ], capsys)
    assert rc == 0
    categories = {e["category"] for e in payload["entries"]}
    assert categories == {"goal"}
    assert len(payload["entries"]) == 2


# ---------------------------------------------------------------------------
# Snapshot + explain exposure
# ---------------------------------------------------------------------------


def test_state_snapshot_exposes_user_memory_block(db_path, capsys):
    # Seed two active entries and one archived entry. Bundle date is
    # after archive so the archived row must be excluded.
    rc, _, _ = _run([
        "memory", "set",
        "--category", "goal",
        "--value", "base-build through May",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
    ], capsys)
    assert rc == 0

    rc, _, _ = _run([
        "memory", "set",
        "--category", "preference",
        "--value", "bike instead of run on heat days",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
    ], capsys)
    assert rc == 0

    rc, stale_payload, _ = _run([
        "memory", "set",
        "--category", "constraint",
        "--value", "retired injury flag",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
    ], capsys)
    assert rc == 0
    _run([
        "memory", "archive",
        "--memory-id", stale_payload["memory_id"],
        "--db-path", str(db_path),
    ], capsys)

    # Reach the snapshot surface.
    rc, snap, err = _run([
        "state", "snapshot",
        "--as-of", datetime.now(timezone.utc).date().isoformat(),
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
    ], capsys)
    assert rc == 0, err
    assert "user_memory" in snap, (
        "snapshot must expose a top-level user_memory key alongside "
        "the existing per-domain keys"
    )

    block = snap["user_memory"]
    assert set(block.keys()) == {"as_of", "counts", "entries"}
    ids = {e["memory_id"] for e in block["entries"]}
    # Active entries (goal + preference) are present; archived constraint is not.
    assert len(ids) == 2
    categories = {e["category"] for e in block["entries"]}
    assert categories == {"goal", "preference"}
    assert block["counts"]["goal"] == 1
    assert block["counts"]["preference"] == 1
    assert block["counts"]["constraint"] == 0
    assert block["counts"]["total"] == 2


def _proposal(domain: str, action: str, **overrides: Any) -> dict[str, Any]:
    base = {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS[domain],
        "proposal_id": f"prop_2026-04-17_u_local_1_{domain}_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-17",
        "domain": domain,
        "action": action,
        "action_detail": None,
        "rationale": [f"{domain}_baseline_signal"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }
    base.update(overrides)
    return base


def _seed_six_domain_plan(db_path: Path) -> str:
    proposals = [
        _proposal("recovery", "proceed_with_planned_session"),
        _proposal("running", "proceed_with_planned_run"),
        _proposal("sleep", "maintain_schedule"),
        _proposal("stress", "maintain_routine"),
        _proposal("strength", "proceed_with_planned_session"),
        _proposal(
            "nutrition", "maintain_targets",
            action_detail={"protein_target_g": 140},
        ),
    ]
    snapshot = {
        "recovery": {
            "classified_state": {"sleep_debt_band": "none"},
            "today": {"acwr_ratio": 1.0},
        },
        "sleep": {"classified_state": {"sleep_debt_band": "none"}},
        "stress": {
            "classified_state": {"garmin_stress_band": "moderate"},
            "today": {"garmin_all_day_stress": 40},
        },
        "running": {},
    }
    conn = open_connection(db_path)
    try:
        for p in proposals:
            project_proposal(conn, p)
        result = run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=snapshot,
        )
    finally:
        conn.close()
    return result.daily_plan_id


def test_explain_exposes_user_memory_for_plan_for_date(db_path, capsys):
    # Seed a user-memory entry whose created_at is earlier than the
    # plan's for_date (2026-04-17). The CLI uses datetime.now() for
    # created_at, so the direct API is the honest way to set up a
    # "memory existed before plan" scenario.
    from health_agent_infra.core.memory import (
        UserMemoryEntry,
        insert_memory_entry,
    )
    entry = UserMemoryEntry(
        memory_id="umem_u_local_1_goal_test_1",
        user_id="u_local_1",
        category="goal",
        value="improve mile time",
        key="primary_goal",
        domain="running",
        created_at=datetime(2026, 4, 10, 9, 0, tzinfo=timezone.utc),
        archived_at=None,
        source="user_manual",
        ingest_actor="hai_cli_direct",
    )
    conn = open_connection(db_path)
    try:
        insert_memory_entry(conn, entry)
    finally:
        conn.close()

    # Seed a committed plan for 2026-04-17.
    plan_id = _seed_six_domain_plan(db_path)

    # Explain must carry the memory under its own top-level key.
    rc, payload, err = _run([
        "explain",
        "--daily-plan-id", plan_id,
        "--db-path", str(db_path),
    ], capsys)
    assert rc == 0, err
    assert "user_memory" in payload, (
        "explain JSON must include a top-level user_memory key"
    )
    # Existing keys are unchanged.
    assert {"plan", "proposals", "x_rule_firings", "recommendations",
            "reviews"} <= set(payload.keys())

    mem = payload["user_memory"]
    assert set(mem.keys()) == {"as_of", "counts", "entries"}
    assert mem["as_of"] == "2026-04-17T23:59:59+00:00"
    ids = {e["memory_id"] for e in mem["entries"]}
    assert "umem_u_local_1_goal_test_1" in ids
    assert mem["counts"]["goal"] >= 1


def test_explain_text_output_includes_user_memory_section(db_path, capsys):
    # Memory must pre-date the plan's for_date (2026-04-17) to show up
    # in the bundle; use the direct API to backdate created_at.
    from health_agent_infra.core.memory import (
        UserMemoryEntry,
        insert_memory_entry,
    )
    entry = UserMemoryEntry(
        memory_id="umem_u_local_1_preference_test_1",
        user_id="u_local_1",
        category="preference",
        value="prefer evening sessions",
        key=None,
        domain=None,
        created_at=datetime(2026, 4, 12, 9, 0, tzinfo=timezone.utc),
        archived_at=None,
        source="user_manual",
        ingest_actor="hai_cli_direct",
    )
    conn = open_connection(db_path)
    try:
        insert_memory_entry(conn, entry)
    finally:
        conn.close()

    plan_id = _seed_six_domain_plan(db_path)

    from health_agent_infra.cli import main as cli_main

    rc = cli_main([
        "explain",
        "--daily-plan-id", plan_id,
        "--db-path", str(db_path),
        "--text",
    ])
    out = capsys.readouterr().out
    assert rc == 0
    assert "## User memory" in out
    assert "prefer evening sessions" in out


def test_explain_user_memory_respects_for_date_archive_semantics(
    db_path, capsys,
):
    """A memory archived *after* the plan's for_date must still appear
    in that plan's explain bundle — the explain surface reconstructs
    what was active at plan time, not what is active now."""

    # Seed the plan first so for_date is locked.
    plan_id = _seed_six_domain_plan(db_path)

    # Set + archive a memory with timestamps that straddle for_date.
    from health_agent_infra.core.memory import (
        UserMemoryEntry,
        archive_memory_entry,
        insert_memory_entry,
    )
    entry = UserMemoryEntry(
        memory_id="umem_active_at_plan_time",
        user_id="u_local_1",
        category="constraint",
        value="left knee sensitive to lateral movement",
        key="injury_left_knee",
        domain="strength",
        created_at=datetime(2026, 4, 10, 9, 0, tzinfo=timezone.utc),
        archived_at=None,
        source="user_manual",
        ingest_actor="hai_cli_direct",
    )
    conn = open_connection(db_path)
    try:
        insert_memory_entry(conn, entry)
        archive_memory_entry(
            conn,
            memory_id=entry.memory_id,
            archived_at=datetime(2026, 4, 18, 9, 0, tzinfo=timezone.utc),
        )
    finally:
        conn.close()

    rc, payload, err = _run([
        "explain",
        "--daily-plan-id", plan_id,
        "--db-path", str(db_path),
    ], capsys)
    assert rc == 0, err
    ids = [e["memory_id"] for e in payload["user_memory"]["entries"]]
    assert "umem_active_at_plan_time" in ids


def test_memory_cli_read_only_leaves_other_tables_untouched(db_path, capsys):
    """Sanity guard: writes to user_memory must not touch any other
    table. A stray INSERT into (say) proposal_log from the memory CLI
    would be a bug."""

    def _row_count(conn, table):
        return conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]

    conn = open_connection(db_path)
    try:
        before = {
            t: _row_count(conn, t)
            for t in (
                "proposal_log", "daily_plan", "x_rule_firing",
                "recommendation_log", "review_event", "review_outcome",
            )
        }
    finally:
        conn.close()

    _run([
        "memory", "set",
        "--category", "context",
        "--value", "coach said to back off on Fridays",
        "--db-path", str(db_path),
    ], capsys)

    conn = open_connection(db_path)
    try:
        after = {
            t: _row_count(conn, t)
            for t in (
                "proposal_log", "daily_plan", "x_rule_firing",
                "recommendation_log", "review_event", "review_outcome",
            )
        }
    finally:
        conn.close()
    assert before == after
