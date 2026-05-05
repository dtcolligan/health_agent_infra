"""W-B (v0.1.17 §2.H) — `hai intake weight` body-composition intake.

Acceptance per PLAN.md §2.H:

  1. Migration 026 test: applies against empty DB; asserts table +
     2 indexes + CHECK(source = 'user_authored'). Applies against a
     v0.1.15.1-shaped DB (target table + 3 nutrition rows); asserts
     existing tables byte-stable + migration-025 indexes survive.
  2. Intake test: `hai intake weight --kg 84.0` writes 1 row + 1
     JSONL + returns body_comp_id. source='user_authored' regardless
     of --ingest-actor.
  3. Multi-measurement-per-day: 2 invocations same day → 2 rows;
     list_body_comp(as_of_date=D) returns both ordered by measured_at.
  4. Capabilities manifest: mutation='writes-state', agent_safe=False,
     idempotent='no'.
  5. Validation: --kg in (20, 250) inclusive; --body-fat-pct in (0, 75).
  6. JSONL audit appended on success; absent on validation failure.
"""

from __future__ import annotations

import io
import json
import sqlite3
from contextlib import closing, redirect_stderr, redirect_stdout
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.body_comp import (
    BodyCompValidationError,
    add_body_comp,
    list_body_comp,
)
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)


USER = "u_wb"


def _run(*argv: str) -> tuple[int, str, str]:
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    try:
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = cli_main(list(argv))
    except SystemExit as exc:
        rc = int(exc.code) if isinstance(exc.code, int) else 2
    return rc, out_buf.getvalue(), err_buf.getvalue()


# ---------------------------------------------------------------------------
# Acceptance test 1 — migration 026
# ---------------------------------------------------------------------------


def test_migration_026_creates_body_comp_table_with_indexes(tmp_path):
    """Empty DB → migration 026 creates body_comp + 2 indexes + the
    CHECK(source = 'user_authored') constraint."""

    db = tmp_path / "state.db"
    initialize_database(db)

    with closing(open_connection(db)) as conn:
        # body_comp table exists.
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='body_comp'"
        ).fetchall()
        assert len(tables) == 1, "body_comp table missing post-migration 026"

        # Required columns.
        cols = {r["name"] for r in conn.execute(
            "PRAGMA table_info(body_comp)"
        ).fetchall()}
        for required in (
            "body_comp_id", "user_id", "measured_at", "as_of_date",
            "weight_kg", "body_fat_pct", "source", "ingest_actor",
            "notes", "created_at",
        ):
            assert required in cols, f"body_comp missing column {required!r}"

        # 2 indexes from migration 026.
        idx_rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND tbl_name='body_comp' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        idx_names = {r["name"] for r in idx_rows}
        for required in ("idx_body_comp_user_asof", "idx_body_comp_user_measured"):
            assert required in idx_names, (
                f"body_comp missing index {required!r}; got {sorted(idx_names)}"
            )

        # CHECK(source = 'user_authored') is enforced — a different value
        # raises an IntegrityError on insert.
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO body_comp ("
                "body_comp_id, user_id, measured_at, as_of_date, "
                "weight_kg, source, ingest_actor) "
                "VALUES ('bc_test', ?, ?, ?, 80.0, 'wearable_pull', 'cli')",
                (USER, "2026-05-04T08:00:00+00:00", "2026-05-04"),
            )


def test_migration_026_against_v0_1_15_1_shaped_db_preserves_target_rows(tmp_path):
    """Apply migration 026 against a DB that already has migration 025
    applied + 3 nutrition target rows. Existing target rows survive
    byte-stable; migration-025 indexes survive."""

    from health_agent_infra.core.state.store import (
        apply_pending_migrations,
        discover_migrations,
    )

    db_path = tmp_path / "state.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        # Apply through migration 025.
        all_migrations = discover_migrations()
        through_025 = [m for m in all_migrations if m[0] <= 25]
        apply_pending_migrations(conn, through_025)

        # Seed 3 nutrition target rows (per W-C-EQP fixture pattern).
        seed_rows = [
            ("target_aaaa", USER, "nutrition", "calories_kcal", "active",
             json.dumps({"value": 3100}), "kcal", None, None,
             "2026-05-02", None, None, "v1 baseline",
             "user_authored", "cli", "2026-05-02T06:27:50+00:00", None, None),
            ("target_bbbb", USER, "nutrition", "protein_g", "active",
             json.dumps({"value": 160}), "g", None, None,
             "2026-05-02", None, None, "1.9 g/kg",
             "user_authored", "cli", "2026-05-02T06:27:50+00:00", None, None),
            ("target_cccc", USER, "nutrition", "carbs_g", "active",
             json.dumps({"value": 350}), "g", None, None,
             "2026-05-02", None, None, "carbs target",
             "user_authored", "cli", "2026-05-02T06:27:50+00:00", None, None),
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

        # Snapshot pre-026 state.
        pre_target_rows = [
            dict(r) for r in conn.execute(
                "SELECT * FROM target WHERE user_id=? ORDER BY target_id",
                (USER,),
            ).fetchall()
        ]
        pre_index_names = {
            r["name"] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' "
                "AND tbl_name='target' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }

        # Apply migration 026.
        m026 = [m for m in all_migrations if m[0] == 26]
        assert m026, "migration 026 must exist"
        apply_pending_migrations(conn, m026)

        # Target rows byte-stable.
        post_target_rows = [
            dict(r) for r in conn.execute(
                "SELECT * FROM target WHERE user_id=? ORDER BY target_id",
                (USER,),
            ).fetchall()
        ]
        assert post_target_rows == pre_target_rows, (
            f"target rows drifted after migration 026:\n"
            f"  pre:  {pre_target_rows}\n  post: {post_target_rows}"
        )

        # Migration-025 indexes survive.
        post_index_names = {
            r["name"] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' "
                "AND tbl_name='target' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        assert pre_index_names <= post_index_names, (
            f"migration-025 indexes lost after migration 026: "
            f"pre={sorted(pre_index_names)} post={sorted(post_index_names)}"
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Acceptance test 2 — intake (CLI happy path)
# ---------------------------------------------------------------------------


def test_intake_weight_writes_row_and_jsonl(tmp_path):
    """`hai intake weight --kg 84.0 --as-of 2026-05-04` writes 1 row +
    1 JSONL line + returns body_comp_id JSON."""

    db = tmp_path / "state.db"
    initialize_database(db)
    base_dir = tmp_path / "intake"

    rc, out, err = _run(
        "intake", "weight",
        "--kg", "84.0",
        "--as-of", "2026-05-04",
        "--user-id", USER,
        "--db-path", str(db),
        "--base-dir", str(base_dir),
    )
    assert rc == exit_codes.OK, f"intake weight failed: rc={rc}, stderr={err[:200]}"
    payload = json.loads(out)
    assert payload["body_comp_id"].startswith("bc_")
    assert payload["weight_kg"] == 84.0
    assert payload["as_of_date"] == "2026-05-04"
    assert payload["source"] == "user_authored"

    # Row in body_comp.
    with closing(open_connection(db)) as conn:
        rows = conn.execute(
            "SELECT * FROM body_comp WHERE user_id=?", (USER,)
        ).fetchall()
    assert len(rows) == 1
    assert rows[0]["weight_kg"] == 84.0
    assert rows[0]["source"] == "user_authored"

    # JSONL line.
    jsonl = base_dir / "body_comp_intake.jsonl"
    assert jsonl.exists()
    audit_lines = jsonl.read_text(encoding="utf-8").splitlines()
    assert len(audit_lines) == 1
    audit = json.loads(audit_lines[0])
    assert audit["weight_kg"] == 84.0
    assert audit["body_comp_id"] == payload["body_comp_id"]


def test_intake_weight_source_always_user_authored(tmp_path):
    """source='user_authored' regardless of --ingest-actor value."""

    db = tmp_path / "state.db"
    initialize_database(db)
    rc, out, err = _run(
        "intake", "weight",
        "--kg", "84.0",
        "--user-id", USER,
        "--db-path", str(db),
        "--base-dir", str(tmp_path),
        "--ingest-actor", "claude_agent_v1",
    )
    assert rc == exit_codes.OK, f"rc={rc}, stderr={err[:200]}"
    payload = json.loads(out)
    assert payload["source"] == "user_authored"
    assert payload["ingest_actor"] == "claude_agent_v1"


# ---------------------------------------------------------------------------
# Acceptance test 3 — multi-measurement per day
# ---------------------------------------------------------------------------


def test_multi_measurement_per_day_appends_rather_than_replaces(tmp_path):
    """Two `hai intake weight` invocations same day → 2 rows;
    list_body_comp(as_of_date=D) returns both ordered by measured_at."""

    db = tmp_path / "state.db"
    initialize_database(db)
    base_dir = tmp_path / "intake"
    as_of_date = date(2026, 5, 4)

    # Morning fasted.
    rc1, out1, _ = _run(
        "intake", "weight",
        "--kg", "84.0",
        "--measured-at", "2026-05-04T07:00:00+00:00",
        "--as-of", "2026-05-04",
        "--user-id", USER,
        "--db-path", str(db),
        "--base-dir", str(base_dir),
        "--notes", "fasted morning",
    )
    assert rc1 == exit_codes.OK
    bc1 = json.loads(out1)["body_comp_id"]

    # Evening post-meal.
    rc2, out2, _ = _run(
        "intake", "weight",
        "--kg", "85.4",
        "--measured-at", "2026-05-04T19:30:00+00:00",
        "--as-of", "2026-05-04",
        "--user-id", USER,
        "--db-path", str(db),
        "--base-dir", str(base_dir),
        "--notes", "post-meal evening",
    )
    assert rc2 == exit_codes.OK
    bc2 = json.loads(out2)["body_comp_id"]

    assert bc1 != bc2

    # list_body_comp returns both, ordered by measured_at ASC.
    with closing(open_connection(db)) as conn:
        rows = list_body_comp(conn, user_id=USER, as_of_date=as_of_date)
    assert len(rows) == 2
    assert rows[0].weight_kg == 84.0
    assert rows[1].weight_kg == 85.4
    assert rows[0].measured_at < rows[1].measured_at


# ---------------------------------------------------------------------------
# Acceptance test 4 — capabilities manifest
# ---------------------------------------------------------------------------


def test_capabilities_manifest_registers_intake_weight_correctly():
    """`hai capabilities --json` registers `hai intake weight` with the
    right contract: writes-state, agent_safe=False, idempotent=no."""

    rc, out, err = _run("capabilities", "--json")
    assert rc == exit_codes.OK
    manifest = json.loads(out)
    weight = next(
        (c for c in manifest["commands"] if c["command"] == "hai intake weight"),
        None,
    )
    assert weight is not None, "hai intake weight missing from manifest"
    assert weight["mutation"] == "writes-state", weight
    assert weight["agent_safe"] is False, weight
    assert weight["idempotent"] == "no", weight


# ---------------------------------------------------------------------------
# Acceptance test 5 — validation
# ---------------------------------------------------------------------------


def test_intake_weight_rejects_out_of_range_kg(tmp_path):
    """--kg below 20 or above 250 → USER_INPUT exit; no row, no JSONL."""

    db = tmp_path / "state.db"
    initialize_database(db)
    base_dir = tmp_path / "intake"

    rc, out, err = _run(
        "intake", "weight",
        "--kg", "10.0",  # below floor
        "--user-id", USER,
        "--db-path", str(db),
        "--base-dir", str(base_dir),
    )
    assert rc == exit_codes.USER_INPUT, f"rc={rc}, stderr={err[:200]}"
    assert "out of range" in err

    with closing(open_connection(db)) as conn:
        assert conn.execute("SELECT COUNT(*) FROM body_comp").fetchone()[0] == 0
    assert not (base_dir / "body_comp_intake.jsonl").exists()


def test_intake_weight_rejects_out_of_range_body_fat_pct(tmp_path):
    """--body-fat-pct above 75 → USER_INPUT exit."""

    db = tmp_path / "state.db"
    initialize_database(db)
    rc, out, err = _run(
        "intake", "weight",
        "--kg", "84.0",
        "--body-fat-pct", "80.0",
        "--user-id", USER,
        "--db-path", str(db),
        "--base-dir", str(tmp_path),
    )
    assert rc == exit_codes.USER_INPUT, f"rc={rc}, stderr={err[:200]}"
    assert "body_fat_pct" in err


def test_intake_weight_rejects_invalid_as_of(tmp_path):
    """--as-of that doesn't parse as YYYY-MM-DD → USER_INPUT."""

    db = tmp_path / "state.db"
    initialize_database(db)
    rc, out, err = _run(
        "intake", "weight",
        "--kg", "84.0",
        "--as-of", "not-a-date",
        "--user-id", USER,
        "--db-path", str(db),
        "--base-dir", str(tmp_path),
    )
    assert rc == exit_codes.USER_INPUT, f"rc={rc}, stderr={err[:200]}"


# ---------------------------------------------------------------------------
# Acceptance test 6 — JSONL audit (covered by tests 2 + 3 + 5 above)
# ---------------------------------------------------------------------------


def test_jsonl_absent_on_validation_failure(tmp_path):
    """Validation failure leaves the JSONL file absent / empty."""

    db = tmp_path / "state.db"
    initialize_database(db)
    base_dir = tmp_path / "intake"

    rc, out, err = _run(
        "intake", "weight",
        "--kg", "300.0",  # above ceiling
        "--user-id", USER,
        "--db-path", str(db),
        "--base-dir", str(base_dir),
    )
    assert rc == exit_codes.USER_INPUT
    jsonl = base_dir / "body_comp_intake.jsonl"
    assert not jsonl.exists() or jsonl.read_text(encoding="utf-8") == ""
