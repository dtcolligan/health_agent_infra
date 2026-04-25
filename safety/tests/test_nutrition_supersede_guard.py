"""Regression test for v0.1.7 W34: nutrition same-day supersede guard.

Background: nutrition is a daily total, not per-meal. Pre-v0.1.7, a
second same-day `hai intake nutrition` call silently created a
supersede chain — fine for the user correcting a typo, dangerous for
the agent treating the command as a per-meal logger. v0.1.7 makes the
supersede explicit: refuse with USER_INPUT unless `--replace` is
passed.
"""

from __future__ import annotations

import json
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes


def _intake_args(*, base_dir: Path, db_path: Path, calories: float):
    return [
        "intake", "nutrition",
        "--calories", str(calories),
        "--protein-g", "180",
        "--carbs-g", "200",
        "--fat-g", "60",
        "--as-of", "2026-04-25",
        "--user-id", "u_test",
        "--base-dir", str(base_dir),
        "--db-path", str(db_path),
    ]


def test_first_intake_succeeds(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    db = tmp_path / "state.db"
    out_buf = StringIO()
    with redirect_stdout(out_buf):
        rc = cli_main(_intake_args(base_dir=base, db_path=db, calories=2000))
    assert rc == exit_codes.OK
    payload = json.loads(out_buf.getvalue())
    assert payload["supersedes_submission_id"] is None


def test_second_intake_same_day_refuses_without_replace(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    db = tmp_path / "state.db"
    # First call succeeds.
    rc = cli_main(_intake_args(base_dir=base, db_path=db, calories=2000))
    assert rc == exit_codes.OK
    # Second call refuses.
    err_buf = StringIO()
    with redirect_stderr(err_buf):
        rc = cli_main(_intake_args(base_dir=base, db_path=db, calories=2400))
    assert rc == exit_codes.USER_INPUT
    stderr = err_buf.getvalue()
    assert "refusing to silently supersede" in stderr
    assert "DAILY TOTAL" in stderr
    assert "--replace" in stderr
    # Confirm only ONE row landed in JSONL.
    jsonl = (base / "nutrition_intake.jsonl").read_text(encoding="utf-8")
    rows = [json.loads(line) for line in jsonl.splitlines() if line.strip()]
    assert len(rows) == 1
    assert rows[0]["calories"] == 2000


def test_second_intake_with_replace_succeeds_and_supersedes(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    db = tmp_path / "state.db"
    rc = cli_main(_intake_args(base_dir=base, db_path=db, calories=2000))
    assert rc == exit_codes.OK
    out_buf = StringIO()
    with redirect_stdout(out_buf):
        rc = cli_main(_intake_args(base_dir=base, db_path=db, calories=2400)
                      + ["--replace"])
    assert rc == exit_codes.OK
    payload = json.loads(out_buf.getvalue())
    assert payload["supersedes_submission_id"] is not None
    # JSONL has both rows: original + the superseding correction.
    jsonl = (base / "nutrition_intake.jsonl").read_text(encoding="utf-8")
    rows = [json.loads(line) for line in jsonl.splitlines() if line.strip()]
    assert len(rows) == 2


def test_different_day_does_not_trigger_guard(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    db = tmp_path / "state.db"
    rc = cli_main(_intake_args(base_dir=base, db_path=db, calories=2000))
    assert rc == exit_codes.OK
    # Different day — no guard.
    other = list(_intake_args(base_dir=base, db_path=db, calories=2200))
    other[other.index("2026-04-25")] = "2026-04-26"
    rc = cli_main(other)
    assert rc == exit_codes.OK
