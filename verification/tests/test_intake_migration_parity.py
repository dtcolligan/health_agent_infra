"""W-OB-7 (v0.1.18 §2.G) — intake-handler migration parity.

Acceptance per PLAN.md §2.G + audit_findings.md §F-OB-PRE-01:

  1. ``open_connection_with_migrations`` exists in ``core/state/store.py``
     next to ``open_connection``; additive (does not replace
     ``open_connection`` globally).
  2. All eight ``cmd_intake_*`` handlers route through
     ``open_connection_with_migrations`` for canonical-state-DB connections.
  3. Per-handler regression: each intake command succeeds against a
     synthetic schema-25 DB (one migration behind v0.1.18 head 26).
     Post-command DB is at schema head 26.
  4. F-OB-PRE-01 reproducer: ``hai intake weight`` succeeds against
     the schema-25 DB and writes the row to the migrated ``body_comp``
     table. The bug shape was ``OperationalError: no such table:
     body_comp`` — this test prevents regression.
  5. Existing handlers continue to write fine on a current-schema DB.
"""

from __future__ import annotations

import io
import json
import sqlite3
from contextlib import closing, redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import (
    apply_pending_migrations,
    current_schema_version,
    open_connection,
    open_connection_with_migrations,
)
from health_agent_infra.core.state.store import discover_migrations


USER = "u_w_ob_7"
SCHEMA_25_HEAD = 25
SCHEMA_HEAD_AT_v0_1_17 = 26


def _build_schema_25_db(db_path: Path) -> None:
    """Construct a synthetic v0.1.17-pre-W-B state DB (schema head 25).

    Applies every packaged migration whose version <= 25, leaving the
    DB exactly one migration behind the v0.1.18 package head. This is
    the failure mode F-OB-PRE-01 reproduced on the maintainer's own DB.
    """

    db_path.parent.mkdir(parents=True, exist_ok=True)
    all_migrations = discover_migrations()
    pre_v0_1_17 = [m for m in all_migrations if m[0] <= SCHEMA_25_HEAD]

    conn = open_connection(db_path)
    try:
        apply_pending_migrations(conn, migrations=pre_v0_1_17)
    finally:
        conn.close()


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
# Acceptance 1 — helper exists
# ---------------------------------------------------------------------------


def test_open_connection_with_migrations_is_additive(tmp_path):
    """The new helper applies migrations on connect; ``open_connection``
    is unchanged (does not migrate)."""

    db = tmp_path / "state.db"
    _build_schema_25_db(db)

    # open_connection alone leaves DB at schema 25 (no migration applied).
    with closing(open_connection(db)) as conn:
        assert current_schema_version(conn) == SCHEMA_25_HEAD

    # open_connection_with_migrations advances to head.
    with closing(open_connection_with_migrations(db)) as conn:
        assert current_schema_version(conn) >= SCHEMA_HEAD_AT_v0_1_17


# ---------------------------------------------------------------------------
# Acceptance 4 — F-OB-PRE-01 reproducer (release-blocker per PLAN §2.G)
# ---------------------------------------------------------------------------


def test_intake_weight_on_pre_v0_1_17_db(tmp_path):
    """``hai intake weight`` must succeed against a schema-25 DB.

    Pre-fix: raises ``OperationalError: no such table: body_comp``.
    Post-fix: applies migration 026, writes to the now-existing
    ``body_comp`` table, returns OK.
    """

    db = tmp_path / "state.db"
    _build_schema_25_db(db)

    base_dir = tmp_path / "hai_base"
    base_dir.mkdir()

    rc, out, err = _run(
        "intake",
        "weight",
        "--kg",
        "82.0",
        "--as-of",
        "2026-05-06",
        "--user-id",
        USER,
        "--db-path",
        str(db),
        "--base-dir",
        str(base_dir),
    )

    assert rc == exit_codes.OK, f"intake weight failed: {err}"

    with closing(open_connection(db)) as conn:
        assert current_schema_version(conn) >= SCHEMA_HEAD_AT_v0_1_17, (
            "DB should be migrated to head"
        )
        rows = conn.execute(
            "SELECT weight_kg, user_id FROM body_comp WHERE user_id = ?",
            (USER,),
        ).fetchall()
        assert len(rows) == 1
        assert rows[0]["weight_kg"] == 82.0


# ---------------------------------------------------------------------------
# Acceptance 3 — per-handler parity (8 handlers)
# ---------------------------------------------------------------------------


def test_intake_gym_on_pre_v0_1_17_db(tmp_path):
    db = tmp_path / "state.db"
    _build_schema_25_db(db)
    base_dir = tmp_path / "hai_base"
    base_dir.mkdir()

    rc, _out, err = _run(
        "intake",
        "gym",
        "--session-id",
        "session_w_ob_7",
        "--exercise",
        "back_squat",
        "--set-number",
        "1",
        "--weight-kg",
        "100.0",
        "--reps",
        "5",
        "--user-id",
        USER,
        "--db-path",
        str(db),
        "--base-dir",
        str(base_dir),
    )

    assert rc == exit_codes.OK, f"intake gym failed: {err}"
    with closing(open_connection(db)) as conn:
        assert current_schema_version(conn) >= SCHEMA_HEAD_AT_v0_1_17


def test_intake_nutrition_on_pre_v0_1_17_db(tmp_path):
    db = tmp_path / "state.db"
    _build_schema_25_db(db)
    base_dir = tmp_path / "hai_base"
    base_dir.mkdir()

    rc, _out, err = _run(
        "intake",
        "nutrition",
        "--calories",
        "2200",
        "--protein-g",
        "150",
        "--carbs-g",
        "240",
        "--fat-g",
        "70",
        "--as-of",
        "2026-05-06",
        "--user-id",
        USER,
        "--db-path",
        str(db),
        "--base-dir",
        str(base_dir),
    )

    assert rc == exit_codes.OK, f"intake nutrition failed: {err}"
    with closing(open_connection(db)) as conn:
        assert current_schema_version(conn) >= SCHEMA_HEAD_AT_v0_1_17


def test_intake_stress_on_pre_v0_1_17_db(tmp_path):
    db = tmp_path / "state.db"
    _build_schema_25_db(db)
    base_dir = tmp_path / "hai_base"
    base_dir.mkdir()

    rc, _out, err = _run(
        "intake",
        "stress",
        "--score",
        "5",
        "--as-of",
        "2026-05-06",
        "--user-id",
        USER,
        "--db-path",
        str(db),
        "--base-dir",
        str(base_dir),
    )

    assert rc == exit_codes.OK, f"intake stress failed: {err}"
    with closing(open_connection(db)) as conn:
        assert current_schema_version(conn) >= SCHEMA_HEAD_AT_v0_1_17


def test_intake_note_on_pre_v0_1_17_db(tmp_path):
    db = tmp_path / "state.db"
    _build_schema_25_db(db)
    base_dir = tmp_path / "hai_base"
    base_dir.mkdir()

    rc, _out, err = _run(
        "intake",
        "note",
        "--text",
        "feeling great today",
        "--as-of",
        "2026-05-06",
        "--user-id",
        USER,
        "--db-path",
        str(db),
        "--base-dir",
        str(base_dir),
    )

    assert rc == exit_codes.OK, f"intake note failed: {err}"
    with closing(open_connection(db)) as conn:
        assert current_schema_version(conn) >= SCHEMA_HEAD_AT_v0_1_17


def test_intake_readiness_on_pre_v0_1_17_db(tmp_path):
    db = tmp_path / "state.db"
    _build_schema_25_db(db)
    base_dir = tmp_path / "hai_base"
    base_dir.mkdir()

    rc, _out, err = _run(
        "intake",
        "readiness",
        "--soreness",
        "moderate",
        "--energy",
        "high",
        "--planned-session-type",
        "easy_run",
        "--as-of",
        "2026-05-06",
        "--user-id",
        USER,
        "--db-path",
        str(db),
        "--base-dir",
        str(base_dir),
    )

    assert rc == exit_codes.OK, f"intake readiness failed: {err}"
    with closing(open_connection(db)) as conn:
        assert current_schema_version(conn) >= SCHEMA_HEAD_AT_v0_1_17


def test_intake_gaps_on_pre_v0_1_17_db(tmp_path):
    db = tmp_path / "state.db"
    _build_schema_25_db(db)
    base_dir = tmp_path / "hai_base"
    base_dir.mkdir()

    rc, _out, err = _run(
        "intake",
        "gaps",
        "--as-of",
        "2026-05-06",
        "--user-id",
        USER,
        "--db-path",
        str(db),
        "--from-state-snapshot",
        "--allow-stale-snapshot",
    )

    assert rc == exit_codes.OK, f"intake gaps failed: {err}"
    with closing(open_connection(db)) as conn:
        assert current_schema_version(conn) >= SCHEMA_HEAD_AT_v0_1_17


def test_intake_exercise_on_pre_v0_1_17_db(tmp_path):
    db = tmp_path / "state.db"
    _build_schema_25_db(db)
    base_dir = tmp_path / "hai_base"
    base_dir.mkdir()

    rc, _out, err = _run(
        "intake",
        "exercise",
        "--name",
        "custom_w_ob_7_lift",
        "--primary-muscle-group",
        "quads",
        "--category",
        "compound",
        "--equipment",
        "barbell",
        "--db-path",
        str(db),
    )

    assert rc == exit_codes.OK, f"intake exercise failed: {err}"
    with closing(open_connection(db)) as conn:
        assert current_schema_version(conn) >= SCHEMA_HEAD_AT_v0_1_17


# ---------------------------------------------------------------------------
# Acceptance 5 — no regression on current-schema DB
# ---------------------------------------------------------------------------


def test_intake_weight_on_current_schema_db_no_regression(tmp_path):
    """``hai intake weight`` against an already-current DB stays
    correct (no double-migration; no regression on the path that
    already worked)."""

    from health_agent_infra.core.state import initialize_database

    db = tmp_path / "state.db"
    initialize_database(db)

    base_dir = tmp_path / "hai_base"
    base_dir.mkdir()

    rc, _out, err = _run(
        "intake",
        "weight",
        "--kg",
        "82.0",
        "--as-of",
        "2026-05-06",
        "--user-id",
        USER,
        "--db-path",
        str(db),
        "--base-dir",
        str(base_dir),
    )

    assert rc == exit_codes.OK, f"intake weight on current schema failed: {err}"
