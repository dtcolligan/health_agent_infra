"""Tests for the v0.1.4 ``hai intake readiness`` persistence + pull auto-read.

Per D2 (``reporting/plans/v0_1_4/D2_intake_write_paths.md``) readiness
is no longer a stdout-only composer. These tests pin the D2 contract:

1. Intake writes to ``manual_readiness_raw`` and appends the
   ``readiness_manual.jsonl`` audit line.
2. Same-day re-intake supersedes the prior row; the leaf is the newest
   non-superseded entry.
3. ``hai pull`` auto-reads ``manual_readiness_raw`` on the same date
   when no explicit override is passed.
4. ``--manual-readiness-json <path>`` overrides the auto-read.
5. ``--use-default-manual-readiness`` overrides the auto-read.
6. DB-absent fail-soft: JSONL audit survives even without a state DB,
   correction chains still resolve via the JSONL.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    read_latest_manual_readiness,
)


USER = "u_readiness_test"
AS_OF = date(2026, 4, 23)


def _init_dirs(tmp_path: Path) -> tuple[Path, Path]:
    base = tmp_path / "intake"
    base.mkdir()
    db = tmp_path / "state.db"
    initialize_database(db)
    return base, db


def _readiness_args(
    base: Path,
    db: Path,
    *,
    soreness: str = "low",
    energy: str = "high",
    planned: str = "intervals_4x4_z4_z2",
    active_goal: str | None = None,
    as_of: str = AS_OF.isoformat(),
) -> list[str]:
    args = [
        "intake", "readiness",
        "--soreness", soreness,
        "--energy", energy,
        "--planned-session-type", planned,
        "--as-of", as_of,
        "--user-id", USER,
        "--base-dir", str(base),
        "--db-path", str(db),
    ]
    if active_goal:
        args.extend(["--active-goal", active_goal])
    return args


# ---------------------------------------------------------------------------
# Persistence — row lands in manual_readiness_raw + JSONL, round-trips
# ---------------------------------------------------------------------------


def test_readiness_intake_writes_jsonl_and_raw_row(tmp_path: Path):
    base, db = _init_dirs(tmp_path)
    rc = cli_main(_readiness_args(
        base, db, active_goal="improve_5k_and_sbd",
    ))
    assert rc == 0

    # JSONL audit boundary.
    jsonl = base / "readiness_manual.jsonl"
    lines = [json.loads(l) for l in jsonl.read_text().splitlines() if l.strip()]
    assert len(lines) == 1
    assert lines[0]["soreness"] == "low"
    assert lines[0]["energy"] == "high"
    assert lines[0]["planned_session_type"] == "intervals_4x4_z4_z2"
    assert lines[0]["active_goal"] == "improve_5k_and_sbd"
    assert lines[0]["source"] == "user_manual"
    assert lines[0]["supersedes_submission_id"] is None

    # DB raw row.
    conn = open_connection(db)
    try:
        row = conn.execute(
            "SELECT soreness, energy, planned_session_type, active_goal, "
            "  source, ingest_actor, supersedes_submission_id "
            "FROM manual_readiness_raw "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
    finally:
        conn.close()

    assert row["soreness"] == "low"
    assert row["energy"] == "high"
    assert row["planned_session_type"] == "intervals_4x4_z4_z2"
    assert row["active_goal"] == "improve_5k_and_sbd"
    assert row["source"] == "user_manual"
    assert row["ingest_actor"] == "hai_cli_direct"
    assert row["supersedes_submission_id"] is None


# ---------------------------------------------------------------------------
# Correction chain — second same-day intake supersedes first
# ---------------------------------------------------------------------------


def test_readiness_same_day_correction_supersedes_prior_leaf(tmp_path: Path):
    base, db = _init_dirs(tmp_path)
    assert cli_main(_readiness_args(base, db, soreness="low", energy="high")) == 0
    # Correction: user realises they're actually sorer than they thought.
    assert cli_main(
        _readiness_args(base, db, soreness="moderate", energy="moderate")
    ) == 0

    lines = [
        json.loads(l) for l in
        (base / "readiness_manual.jsonl").read_text().splitlines() if l.strip()
    ]
    assert len(lines) == 2
    assert lines[0]["supersedes_submission_id"] is None
    assert lines[1]["supersedes_submission_id"] == lines[0]["submission_id"]

    # The canonical (non-superseded) leaf is the latest.
    conn = open_connection(db)
    try:
        latest = read_latest_manual_readiness(
            conn, user_id=USER, as_of_date=AS_OF,
        )
    finally:
        conn.close()
    assert latest is not None
    assert latest["soreness"] == "moderate"
    assert latest["energy"] == "moderate"
    assert latest["submission_id"] == lines[1]["submission_id"]


def test_readiness_db_absent_still_builds_correction_chain(tmp_path: Path):
    """DB-absent chain integrity: JSONL supersedes pointer still resolves
    when no state DB exists (mirrors the stress/nutrition contract)."""

    base = tmp_path / "intake"
    base.mkdir()
    missing_db = tmp_path / "no_db.db"

    assert cli_main(_readiness_args(base, missing_db, soreness="low")) == 0
    assert cli_main(_readiness_args(base, missing_db, soreness="high")) == 0

    lines = [
        json.loads(l) for l in
        (base / "readiness_manual.jsonl").read_text().splitlines() if l.strip()
    ]
    assert lines[0]["supersedes_submission_id"] is None
    assert lines[1]["supersedes_submission_id"] == lines[0]["submission_id"], (
        "DB-absent chain broken: readiness chain resolver must read JSONL"
    )


# ---------------------------------------------------------------------------
# hai pull — auto-read + override precedence (D2 §pull adapter integration)
# ---------------------------------------------------------------------------


def _run_pull(db: Path, *extra: str, capsys) -> dict:
    # Drain any stdout left over from prior in-process cli_main calls —
    # cli_main prints a JSON blob per invocation, so a stale readiness
    # JSON would concatenate with the pull JSON and break json.loads.
    capsys.readouterr()
    argv = [
        "pull",
        "--date", AS_OF.isoformat(),
        "--user-id", USER,
        "--db-path", str(db),
        *extra,
    ]
    rc = cli_main(argv)
    assert rc == 0
    out = capsys.readouterr().out
    return json.loads(out)


def test_pull_auto_reads_same_day_manual_readiness_from_state(
    tmp_path: Path, capsys,
):
    """D2 test #1: intake readiness writes DB → next hai pull picks it
    up automatically without --manual-readiness-json."""

    base, db = _init_dirs(tmp_path)
    assert cli_main(_readiness_args(
        base, db,
        soreness="low", energy="high", planned="intervals_4x4_z4_z2",
        active_goal="improve_5k_and_sbd",
    )) == 0

    pull_payload = _run_pull(db, capsys=capsys)
    manual = pull_payload["manual_readiness"]
    assert manual is not None, (
        "hai pull did not auto-read manual_readiness_raw for same-day row"
    )
    assert manual["soreness"] == "low"
    assert manual["energy"] == "high"
    assert manual["planned_session_type"] == "intervals_4x4_z4_z2"
    assert manual["active_goal"] == "improve_5k_and_sbd"
    assert manual["submission_id"].startswith("m_ready_2026-04-23_")


def test_pull_manual_readiness_json_flag_overrides_state_auto_read(
    tmp_path: Path, capsys,
):
    """D2 test #2: --manual-readiness-json wins against the DB auto-read."""

    base, db = _init_dirs(tmp_path)
    # DB row says low/high.
    assert cli_main(_readiness_args(
        base, db, soreness="low", energy="high",
    )) == 0
    # Override file says moderate/moderate.
    override = {
        "submission_id": "override_fixture",
        "soreness": "moderate",
        "energy": "moderate",
        "planned_session_type": "easy",
    }
    override_path = tmp_path / "override.json"
    override_path.write_text(json.dumps(override))

    pull_payload = _run_pull(
        db,
        "--manual-readiness-json", str(override_path),
        capsys=capsys,
    )
    manual = pull_payload["manual_readiness"]
    assert manual["submission_id"] == "override_fixture"
    assert manual["soreness"] == "moderate"
    assert manual["planned_session_type"] == "easy"


def test_pull_use_default_manual_readiness_flag_overrides_state_auto_read(
    tmp_path: Path, capsys,
):
    """--use-default-manual-readiness also wins against DB auto-read."""

    base, db = _init_dirs(tmp_path)
    assert cli_main(_readiness_args(
        base, db, soreness="low", energy="high",
    )) == 0

    pull_payload = _run_pull(
        db,
        "--use-default-manual-readiness",
        capsys=capsys,
    )
    manual = pull_payload["manual_readiness"]
    # The default neutral fixture, not the intake row.
    assert manual["submission_id"] == f"m_ready_real_{AS_OF.isoformat()}"
    assert manual["soreness"] == "moderate"


def test_pull_auto_read_returns_none_when_no_same_day_row(
    tmp_path: Path, capsys,
):
    """Pull with no override + no same-day intake → manual_readiness is
    None. Doesn't synthesise a neutral fallback — that would mask the
    "nothing intaken" case."""

    _, db = _init_dirs(tmp_path)

    pull_payload = _run_pull(db, capsys=capsys)
    assert pull_payload["manual_readiness"] is None


def test_pull_auto_read_does_not_cross_days(tmp_path: Path, capsys):
    """Auto-read is scoped by as_of_date: yesterday's intake doesn't
    feed today's pull silently."""

    base, db = _init_dirs(tmp_path)
    # Seed yesterday.
    assert cli_main(_readiness_args(
        base, db, as_of="2026-04-22",
    )) == 0

    pull_payload = _run_pull(db, capsys=capsys)
    assert pull_payload["manual_readiness"] is None, (
        "pull auto-read picked up a different day's intake — scope leak"
    )


def test_pull_auto_read_returns_latest_leaf_after_correction(
    tmp_path: Path, capsys,
):
    """When same-day intake was corrected, pull returns the leaf (latest
    non-superseded), not the prior row."""

    base, db = _init_dirs(tmp_path)
    assert cli_main(_readiness_args(
        base, db, soreness="low", energy="high",
    )) == 0
    assert cli_main(_readiness_args(
        base, db, soreness="moderate", energy="moderate",
    )) == 0

    pull_payload = _run_pull(db, capsys=capsys)
    manual = pull_payload["manual_readiness"]
    assert manual["soreness"] == "moderate"
    assert manual["energy"] == "moderate"


# ---------------------------------------------------------------------------
# Reproject — readiness JSONL rebuilds the raw table
# ---------------------------------------------------------------------------


def test_reproject_rebuilds_manual_readiness_raw_from_jsonl(tmp_path: Path):
    """``hai state reproject`` replays readiness_manual.jsonl into
    manual_readiness_raw, preserving the supersede chain."""

    from health_agent_infra.core.state import reproject_from_jsonl

    base, db = _init_dirs(tmp_path)
    assert cli_main(_readiness_args(base, db, soreness="low")) == 0
    assert cli_main(_readiness_args(base, db, soreness="high")) == 0

    # Drop the raw table contents to force reproject to rebuild them.
    conn = open_connection(db)
    try:
        conn.execute("DELETE FROM manual_readiness_raw")
        conn.commit()
        counts = reproject_from_jsonl(conn, base)
        rows = conn.execute(
            "SELECT submission_id, soreness, supersedes_submission_id "
            "FROM manual_readiness_raw "
            "WHERE user_id = ? AND as_of_date = ? "
            "ORDER BY ingested_at",
            (USER, AS_OF.isoformat()),
        ).fetchall()
    finally:
        conn.close()

    assert counts["manual_readiness_raw"] == 2
    assert len(rows) == 2
    assert rows[0]["soreness"] == "low"
    assert rows[0]["supersedes_submission_id"] is None
    assert rows[1]["soreness"] == "high"
    assert rows[1]["supersedes_submission_id"] == rows[0]["submission_id"]


def test_reproject_readiness_only_preserves_other_groups(tmp_path: Path):
    """Scope guard: a base_dir containing only readiness_manual.jsonl
    does NOT wipe stress / nutrition / notes tables."""

    from health_agent_infra.core.state import reproject_from_jsonl

    base, db = _init_dirs(tmp_path)
    # Seed a stress row via its intake path (writes stress_manual.jsonl).
    assert cli_main([
        "intake", "stress",
        "--score", "3",
        "--as-of", AS_OF.isoformat(), "--user-id", USER,
        "--base-dir", str(base), "--db-path", str(db),
    ]) == 0
    # Seed a readiness row.
    assert cli_main(_readiness_args(base, db)) == 0

    # Move the stress JSONL aside so a subsequent reproject only sees
    # readiness. Stress raw should survive untouched.
    (base / "stress_manual.jsonl").rename(tmp_path / "moved_stress.jsonl")

    conn = open_connection(db)
    try:
        counts = reproject_from_jsonl(conn, base)
        stress_n = conn.execute(
            "SELECT COUNT(*) FROM stress_manual_raw"
        ).fetchone()[0]
        readiness_n = conn.execute(
            "SELECT COUNT(*) FROM manual_readiness_raw"
        ).fetchone()[0]
    finally:
        conn.close()

    assert counts["stress_manual_raw"] == 0  # group untouched
    assert counts["manual_readiness_raw"] == 1
    assert stress_n == 1, "stress row wiped by readiness-only reproject"
    assert readiness_n == 1
