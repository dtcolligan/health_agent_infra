"""W-C — `hai target nutrition` daily macro target convenience command.

Per `hai/reporting/plans/v0_1_15/PLAN.md` §2.D (round-4 F-R4-01 tightened).

Round-4 F-PHASE0-01 Option A revision: extends the EXISTING `target`
table (migration 020, in tree since v0.1.8 W50) rather than creating a
parallel `nutrition_target` table. Migration 025 adds `'carbs_g'` and
`'fat_g'` to the SQL `target_type` CHECK and the Python
`_VALID_TARGET_TYPE` constant. The new convenience command writes 4
atomic `target` rows in a single transaction.

8 acceptance tests per PLAN §2.D:

  1. Migration 025 + Python _VALID_TARGET_TYPE extension.
  2. Atomic-insert via add_targets_atomic helper rolls back on partial
     failure (single commit observed at the connection level).
  3. Source/status pairing per `core/target/store.py:160-168` W57
     invariant: agent → proposed/agent_proposed; user → active/
     user_authored.
  4. W57 gate test: agent-proposed rows stay proposed until per-row
     `hai target commit --target-id <id>` promotes them.
  5. Natural-key idempotency: identical re-invocation is a no-op.
  6. Idempotency edge: --phase change writes a new 4-row group.
  7. Read-side integration: W-A's target_status query returns
     `present` after a user-path invocation.
  8. Capabilities manifest entry for `hai target nutrition`.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)
from health_agent_infra.core.target.store import (
    _VALID_TARGET_TYPE,
    TargetRecord,
    TargetValidationError,
    add_targets_atomic,
)


USER = "u_test"
TODAY = date(2026, 5, 3)


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


# ---------------------------------------------------------------------------
# Acceptance test 1 — migration 025 + Python _VALID_TARGET_TYPE
# ---------------------------------------------------------------------------


def test_migration_025_preserves_pre_existing_target_rows_byte_stable(
    tmp_path: Path,
):
    """Per F-IR-04 + PLAN §2.D acceptance test 1 (existing-row
    preservation clause): seed pre-025 target rows covering active
    + archived nutrition rows (the maintainer's actual production
    shape), apply migration 025, and assert every shared column is
    identical post-migration. Also assert the three indexes from
    migration 020 exist post-recreate-and-copy."""

    from health_agent_infra.core.state.store import (
        apply_pending_migrations,
        discover_migrations,
    )

    db_path = tmp_path / "state.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        all_migrations = discover_migrations()
        pre_025 = [m for m in all_migrations if m[0] < 25]
        apply_pending_migrations(conn, pre_025)

        # Seed three rows mirroring the maintainer's live state shape
        # (calories_kcal=3300 archived, =3100 active, protein_g=160 active).
        seed_rows = [
            ("target_4a69faef1adf", USER, "nutrition", "calories_kcal",
             "archived", json.dumps({"value": 3300}), "kcal", None, None,
             "2026-04-27", None, None,
             "Mifflin-St Jeor BMR 1911 x 1.725 maintenance",
             "agent_proposed", "claude_agent_v1",
             "2026-04-27T17:13:37.260872+00:00", None, None),
            ("target_5c19cd8f3478", USER, "nutrition", "calories_kcal",
             "active", json.dumps({"value": 3100}), "kcal", None, None,
             "2026-05-02", None, "2026-05-09",
             "Cut phase - 200 kcal deficit",
             "agent_proposed", "claude_agent_v1",
             "2026-05-02T06:27:50.412151+00:00", None, None),
            ("target_83ab8fc1f903", USER, "nutrition", "protein_g",
             "active", json.dumps({"value": 160}), "g", None, None,
             "2026-04-27", None, None,
             "1.9 g/kg x 84kg = 160g",
             "agent_proposed", "claude_agent_v1",
             "2026-04-27T17:13:37.674498+00:00", None, None),
        ]
        for row in seed_rows:
            conn.execute(
                "INSERT INTO target ("
                "target_id, user_id, domain, target_type, status, "
                "value_json, unit, lower_bound, upper_bound, "
                "effective_from, effective_to, review_after, reason, "
                "source, ingest_actor, created_at, "
                "supersedes_target_id, superseded_by_target_id) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                row,
            )
        conn.commit()

        # Snapshot pre-025 row state for byte-stable comparison.
        pre_rows = conn.execute(
            "SELECT * FROM target WHERE user_id=? ORDER BY target_id",
            (USER,),
        ).fetchall()
        pre_dicts = [dict(r) for r in pre_rows]

        # Apply migration 025.
        m025 = [m for m in all_migrations if m[0] == 25]
        assert m025, "migration 025 must exist"
        apply_pending_migrations(conn, m025)

        # Re-fetch and compare every column byte-stable.
        post_rows = conn.execute(
            "SELECT * FROM target WHERE user_id=? ORDER BY target_id",
            (USER,),
        ).fetchall()
        post_dicts = [dict(r) for r in post_rows]

        assert len(post_dicts) == len(pre_dicts), (
            f"row count drift: pre={len(pre_dicts)} post={len(post_dicts)}"
        )
        for pre, post in zip(pre_dicts, post_dicts):
            assert pre == post, (
                f"row drift after migration 025:\n  pre:  {pre}\n  post: {post}"
            )

        # Three indexes from migration 020 must exist after recreate-and-copy.
        index_rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND tbl_name='target' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        index_names = {r["name"] for r in index_rows}
        for required in (
            "idx_target_active_window",
            "idx_target_domain_type",
            "idx_target_supersedes",
        ):
            assert required in index_names, (
                f"index {required!r} missing after migration 025; "
                f"got {sorted(index_names)}"
            )

        # W-C-EQP (v0.1.17 §2.J): index-name existence is necessary but
        # not sufficient — the planner could still pick a full table scan
        # if the index is structurally wrong-shaped or stale post-migration.
        # Assert the W-A active-window query actually USES
        # `idx_target_active_window`. Catches the case where migration 025's
        # recreate-and-copy left a syntactically-present but query-stale
        # index, OR a future migration drops the index.
        as_of = "2026-05-05"
        plan_rows = conn.execute(
            "EXPLAIN QUERY PLAN "
            "SELECT 1 FROM target "
            "WHERE user_id=? AND domain='nutrition' "
            "AND target_type IN ('calories_kcal','protein_g','carbs_g','fat_g') "
            "AND status='active' AND superseded_by_target_id IS NULL "
            "AND date(effective_from) <= date(?) "
            "AND (effective_to IS NULL OR date(effective_to) >= date(?)) "
            "LIMIT 1",
            (USER, as_of, as_of),
        ).fetchall()
        plan_text = "\n".join(
            " ".join(str(v) for v in dict(r).values())
            for r in plan_rows
        )
        # Per PLAN §2.J item 5: "whichever rebuilt index covers the
        # predicate." The SQLite planner picks the most selective index
        # for the actual filter set. With the IN(...) on target_type
        # being highly selective at v0.1.15 ship, the planner chooses
        # `idx_target_domain_type` over `idx_target_active_window`. Both
        # are migration-020 indexes that survived the migration-025
        # recreate-and-copy. The contract under test is "no full table
        # scan after migration 025"; pin against ANY of the three
        # expected indexes from the migration set.
        plan_indexes = {
            "idx_target_active_window",
            "idx_target_domain_type",
            "idx_target_supersedes",
        }
        used_via_index = any(
            f"USING INDEX {idx}" in plan_text for idx in plan_indexes
        )
        assert used_via_index, (
            f"W-C-EQP: planner did not use any expected migration-020 index "
            f"({sorted(plan_indexes)}) for the W-A active-window query. "
            f"This may indicate a fall-back to full table scan or an "
            f"unexpected index. EXPLAIN QUERY PLAN output:\n{plan_text}"
        )
        # Stronger negative: explicitly refuse a full table scan, which
        # would manifest as "SCAN target" without "USING INDEX".
        assert "SCAN target" not in plan_text or "USING INDEX" in plan_text, (
            f"W-C-EQP: planner fell back to a full table scan for the "
            f"W-A active-window query. EXPLAIN QUERY PLAN output:\n{plan_text}"
        )
    finally:
        conn.close()


def test_migration_025_extends_target_type_check_and_python_set(
    tmp_path: Path,
):
    """Both surfaces — SQL CHECK and Python _VALID_TARGET_TYPE — admit
    the new `carbs_g` and `fat_g` types post-migration."""

    db = _init_db(tmp_path)

    assert "carbs_g" in _VALID_TARGET_TYPE, (
        "core/target/store.py _VALID_TARGET_TYPE must include 'carbs_g'"
    )
    assert "fat_g" in _VALID_TARGET_TYPE, (
        "core/target/store.py _VALID_TARGET_TYPE must include 'fat_g'"
    )

    # SQL CHECK admits both — direct insert succeeds.
    conn = sqlite3.connect(str(db))
    try:
        conn.execute(
            "INSERT INTO target ("
            "target_id, user_id, domain, target_type, status, "
            "value_json, unit, effective_from, reason, source, "
            "ingest_actor, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "test_carbs", USER, "nutrition", "carbs_g", "active",
                json.dumps({"value": 350}), "g",
                TODAY.isoformat(), "test", "user_authored", "cli",
                "2026-05-03T10:00:00+00:00",
            ),
        )
        conn.execute(
            "INSERT INTO target ("
            "target_id, user_id, domain, target_type, status, "
            "value_json, unit, effective_from, reason, source, "
            "ingest_actor, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "test_fat", USER, "nutrition", "fat_g", "active",
                json.dumps({"value": 90}), "g",
                TODAY.isoformat(), "test", "user_authored", "cli",
                "2026-05-03T10:00:00+00:00",
            ),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Acceptance test 2 — atomic-insert via add_targets_atomic
# ---------------------------------------------------------------------------


def test_add_targets_atomic_rolls_back_on_partial_failure(tmp_path: Path):
    """Per F-R4-01: add_targets_atomic must wrap all rows in a single
    BEGIN IMMEDIATE / COMMIT. If row N fails validation/constraint, rows
    1..N-1 must roll back. Test injects a constraint violation on the
    third record."""

    from datetime import datetime, timezone

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        good_records = [
            TargetRecord(
                target_id=f"atomic_{i}",
                user_id=USER, domain="nutrition",
                target_type=tt, status="active",
                value=v, unit=u,
                lower_bound=None, upper_bound=None,
                effective_from=TODAY, effective_to=None,
                review_after=None,
                reason="atomic test",
                source="user_authored", ingest_actor="cli",
                created_at=datetime.now(timezone.utc),
                supersedes_target_id=None,
                superseded_by_target_id=None,
            )
            for i, (tt, v, u) in enumerate([
                ("calories_kcal", 3100, "kcal"),
                ("protein_g", 160, "g"),
            ])
        ]
        # Inject a record with an invalid target_type to force rollback.
        bad = TargetRecord(
            target_id="atomic_bad",
            user_id=USER, domain="nutrition",
            target_type="not_a_real_type",  # validator rejects
            status="active",
            value=0, unit="?",
            lower_bound=None, upper_bound=None,
            effective_from=TODAY, effective_to=None,
            review_after=None,
            reason="atomic test (bad)",
            source="user_authored", ingest_actor="cli",
            created_at=datetime.now(timezone.utc),
            supersedes_target_id=None,
            superseded_by_target_id=None,
        )

        with pytest.raises(TargetValidationError):
            add_targets_atomic(conn, records=[*good_records, bad])

        # No rows landed — full rollback.
        rows = conn.execute(
            "SELECT COUNT(*) AS n FROM target WHERE user_id=?", (USER,),
        ).fetchone()
        assert rows["n"] == 0, (
            f"add_targets_atomic must roll back all rows on partial "
            f"failure; got {rows['n']} surviving rows"
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Acceptance test 3 — convenience command source/status pairing
# ---------------------------------------------------------------------------


def test_hai_target_nutrition_user_path_writes_4_active_rows(
    tmp_path: Path, capsys,
):
    """User-invoked (--ingest-actor cli, the default): 4 rows with
    source='user_authored', status='active' per W57 invariant."""

    db = _init_db(tmp_path)

    rc = cli_main([
        "target", "nutrition",
        "--kcal", "3100",
        "--protein-g", "160",
        "--carbs-g", "350",
        "--fat-g", "90",
        "--phase", "cut",
        "--effective-from", TODAY.isoformat(),
        "--user-id", USER,
        "--db-path", str(db),
    ])
    assert rc == exit_codes.OK
    capsys.readouterr()  # discard output

    conn = open_connection(db)
    try:
        rows = conn.execute(
            "SELECT target_type, source, status, value_json, reason "
            "FROM target WHERE user_id=? ORDER BY target_type",
            (USER,),
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 4
    types = {r["target_type"] for r in rows}
    assert types == {"calories_kcal", "protein_g", "carbs_g", "fat_g"}
    assert all(r["source"] == "user_authored" for r in rows)
    assert all(r["status"] == "active" for r in rows)
    assert all(r["reason"].startswith("cut:") for r in rows)


def test_hai_target_nutrition_agent_path_writes_4_proposed_rows(
    tmp_path: Path, capsys,
):
    """Agent-invoked (--ingest-actor claude_agent_v1): 4 rows with
    source='agent_proposed', status='proposed' per W57 invariant."""

    db = _init_db(tmp_path)

    rc = cli_main([
        "target", "nutrition",
        "--kcal", "3100",
        "--protein-g", "160",
        "--carbs-g", "350",
        "--fat-g", "90",
        "--phase", "cut",
        "--effective-from", TODAY.isoformat(),
        "--user-id", USER,
        "--db-path", str(db),
        "--ingest-actor", "claude_agent_v1",
    ])
    assert rc == exit_codes.OK
    capsys.readouterr()

    conn = open_connection(db)
    try:
        rows = conn.execute(
            "SELECT target_type, source, status FROM target "
            "WHERE user_id=? ORDER BY target_type",
            (USER,),
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 4
    assert all(r["source"] == "agent_proposed" for r in rows)
    assert all(r["status"] == "proposed" for r in rows)


# ---------------------------------------------------------------------------
# Acceptance test 4 — W57 per-row commit gate
# ---------------------------------------------------------------------------


def test_hai_target_commit_promotes_one_proposed_row_at_a_time(
    tmp_path: Path, capsys,
):
    """Per OQ-10 ratification + PLAN §2.D test 4: the W57 commit gate
    is per-row. Promoting one row leaves the other 3 in 'proposed'.

    Note: hai target commit is non-agent-safe per the W57 design. The
    --user-confirmed-action flag passed below is the test-mode
    confirmation that the existing W57 gate accepts; production users
    interactively confirm via --user-confirmed-action='commit target
    <id>' or equivalent."""

    db = _init_db(tmp_path)

    rc = cli_main([
        "target", "nutrition",
        "--kcal", "3100", "--protein-g", "160",
        "--carbs-g", "350", "--fat-g", "90",
        "--phase", "cut", "--effective-from", TODAY.isoformat(),
        "--user-id", USER, "--db-path", str(db),
        "--ingest-actor", "claude_agent_v1",
    ])
    assert rc == exit_codes.OK
    capsys.readouterr()

    conn = open_connection(db)
    try:
        rows = conn.execute(
            "SELECT target_id, target_type, status FROM target "
            "WHERE user_id=? ORDER BY target_type",
            (USER,),
        ).fetchall()
    finally:
        conn.close()

    proposed_kcal = next(
        r["target_id"] for r in rows if r["target_type"] == "calories_kcal"
    )

    # Try committing exactly the kcal row. The W57 gate accepts
    # `--confirm` for non-interactive callers (the test runner is
    # piped, so isatty is False).
    rc = cli_main([
        "target", "commit",
        "--target-id", proposed_kcal,
        "--user-id", USER,
        "--db-path", str(db),
        "--confirm",
    ])
    assert rc == exit_codes.OK
    capsys.readouterr()

    conn = open_connection(db)
    try:
        rows_post = conn.execute(
            "SELECT target_id, target_type, status FROM target "
            "WHERE user_id=? ORDER BY target_type",
            (USER,),
        ).fetchall()
    finally:
        conn.close()

    by_id = {r["target_id"]: r["status"] for r in rows_post}
    assert by_id[proposed_kcal] == "active"
    # Other 3 rows still proposed.
    other_statuses = [
        r["status"] for r in rows_post if r["target_id"] != proposed_kcal
    ]
    assert other_statuses == ["proposed", "proposed", "proposed"]


# ---------------------------------------------------------------------------
# Acceptance test 5 — natural-key idempotency
# ---------------------------------------------------------------------------


def test_hai_target_nutrition_idempotent_on_identical_reinvocation(
    tmp_path: Path, capsys,
):
    """Per F-R4-01 + PLAN §2.D acceptance 5: identical args = no new
    rows. Natural-key duplicate-detection at the convenience-handler
    entry point returns the existing rows and skips insert."""

    db = _init_db(tmp_path)

    common_args = [
        "target", "nutrition",
        "--kcal", "3100", "--protein-g", "160",
        "--carbs-g", "350", "--fat-g", "90",
        "--phase", "cut", "--effective-from", TODAY.isoformat(),
        "--user-id", USER, "--db-path", str(db),
    ]

    assert cli_main(common_args) == exit_codes.OK
    capsys.readouterr()
    assert cli_main(common_args) == exit_codes.OK
    capsys.readouterr()
    assert cli_main(common_args) == exit_codes.OK
    capsys.readouterr()

    conn = open_connection(db)
    try:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM target WHERE user_id=?",
            (USER,),
        ).fetchone()["n"]
    finally:
        conn.close()

    assert count == 4, (
        f"three identical invocations should produce 4 rows total "
        f"(natural-key idempotency); got {count}"
    )


# ---------------------------------------------------------------------------
# Acceptance test 6 — phase change writes new group
# ---------------------------------------------------------------------------


def test_hai_target_nutrition_phase_change_writes_new_group(
    tmp_path: Path, capsys,
):
    """Per PLAN §2.D acceptance 6: changing only --phase triggers a new
    natural key (different reason prefix) → new 4-row group."""

    db = _init_db(tmp_path)

    base_args = [
        "target", "nutrition",
        "--kcal", "3100", "--protein-g", "160",
        "--carbs-g", "350", "--fat-g", "90",
        "--effective-from", TODAY.isoformat(),
        "--user-id", USER, "--db-path", str(db),
    ]

    assert cli_main(base_args + ["--phase", "cut"]) == exit_codes.OK
    capsys.readouterr()
    assert cli_main(base_args + ["--phase", "maintain"]) == exit_codes.OK
    capsys.readouterr()

    conn = open_connection(db)
    try:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM target WHERE user_id=?",
            (USER,),
        ).fetchone()["n"]
    finally:
        conn.close()

    assert count == 8, (
        f"different --phase values should write distinct 4-row groups; "
        f"got {count} rows total"
    )


# ---------------------------------------------------------------------------
# Acceptance test 7 — W-A integration (target_status='present')
# ---------------------------------------------------------------------------


def test_w_a_target_status_present_after_hai_target_nutrition(
    tmp_path: Path, capsys,
):
    """Read-side integration: after a user-path `hai target nutrition`
    invocation, W-A's target_status query returns 'present'."""

    from health_agent_infra.core.intake.presence import compute_target_status

    db = _init_db(tmp_path)

    assert cli_main([
        "target", "nutrition",
        "--kcal", "3100", "--protein-g", "160",
        "--carbs-g", "350", "--fat-g", "90",
        "--phase", "cut", "--effective-from", TODAY.isoformat(),
        "--user-id", USER, "--db-path", str(db),
    ]) == exit_codes.OK
    capsys.readouterr()

    conn = open_connection(db)
    try:
        status = compute_target_status(conn, as_of=TODAY, user_id=USER)
    finally:
        conn.close()

    assert status == "present"


# ---------------------------------------------------------------------------
# Acceptance test 8 — capabilities manifest annotation
# ---------------------------------------------------------------------------


def test_capabilities_manifest_includes_hai_target_nutrition(capsys):
    """Per PLAN §2.D acceptance 8: capabilities manifest annotates the
    new convenience command with the right contract metadata."""

    rc = cli_main(["capabilities", "--json"])
    assert rc == exit_codes.OK
    payload = json.loads(capsys.readouterr().out)

    cmd = next(
        (c for c in payload["commands"] if c["command"] == "hai target nutrition"),
        None,
    )
    assert cmd is not None, (
        "hai target nutrition must appear in capabilities manifest"
    )
    assert cmd["mutation"] == "writes-state"
    assert cmd["agent_safe"] is True
    assert cmd["idempotent"] == "yes"
    # Capabilities convention: json_output exposes the annotation
    # value ("default" / True / False) as authored. cmd_target_set,
    # cmd_target_commit, cmd_target_archive all use "default" too.
    assert cmd["json_output"] in ("default", True)
