"""Regression test for the v0.1.6 JSON-arg helper + main() exception
guard. The audit cycle (Codex r1 + internal + Codex r2) found that
``cmd_propose``, ``cmd_review_record``, ``cmd_review_schedule``,
``cmd_pull --manual-readiness-json``, and ``cmd_clean`` all called
``json.loads(Path().read_text())`` before any guard, AND ``main()``
had no top-level exception guard. Bad path or malformed JSON escaped
as a raw Python traceback instead of the documented governed
USER_INPUT exit. This test pins the fix.

Each handler must:
  - Exit with USER_INPUT (1) when the path doesn't exist.
  - Exit with USER_INPUT (1) when the file isn't valid JSON.
  - Print a stderr line that names the command + the flag + the
    underlying error (so an agent can route on it).
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes


# ---------------------------------------------------------------------------
# Per-handler fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def bad_path(tmp_path: Path) -> str:
    return str(tmp_path / "nonexistent.json")


@pytest.fixture
def malformed_path(tmp_path: Path) -> str:
    p = tmp_path / "malformed.json"
    p.write_text("{ this is not valid json", encoding="utf-8")
    return str(p)


@pytest.fixture
def base_dir(tmp_path: Path) -> str:
    return str(tmp_path)


# ---------------------------------------------------------------------------
# Each command + flag combination — parametrised
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("argv,flag_label,command_label", [
    # cmd_propose
    (
        ["propose", "--domain", "recovery", "--proposal-json", "<PATH>",
         "--base-dir", "<BASE>"],
        "--proposal-json",
        "hai propose",
    ),
    # cmd_review_schedule
    (
        ["review", "schedule", "--recommendation-json", "<PATH>",
         "--base-dir", "<BASE>"],
        "--recommendation-json",
        "hai review schedule",
    ),
    # cmd_review_record
    (
        ["review", "record", "--outcome-json", "<PATH>",
         "--base-dir", "<BASE>"],
        "--outcome-json",
        "hai review record",
    ),
    # cmd_clean
    (
        ["clean", "--evidence-json", "<PATH>"],
        "--evidence-json",
        "hai clean",
    ),
])
def test_bad_path_exits_user_input_with_named_stderr(
    argv, flag_label, command_label, bad_path, base_dir,
):
    """Nonexistent path → USER_INPUT, stderr names command + flag."""

    argv = [a.replace("<PATH>", bad_path).replace("<BASE>", base_dir)
            for a in argv]
    err_buf = StringIO()
    with redirect_stderr(err_buf):
        rc = cli_main(argv)
    assert rc == exit_codes.USER_INPUT, (
        f"expected USER_INPUT for {command_label} with bad path, got {rc}"
    )
    stderr = err_buf.getvalue()
    assert command_label in stderr
    assert flag_label in stderr
    # Underlying OSError reason should surface, not a Python traceback.
    assert "Traceback" not in stderr


@pytest.mark.parametrize("argv,flag_label,command_label", [
    (
        ["propose", "--domain", "recovery", "--proposal-json", "<PATH>",
         "--base-dir", "<BASE>"],
        "--proposal-json",
        "hai propose",
    ),
    (
        ["review", "schedule", "--recommendation-json", "<PATH>",
         "--base-dir", "<BASE>"],
        "--recommendation-json",
        "hai review schedule",
    ),
    (
        ["review", "record", "--outcome-json", "<PATH>",
         "--base-dir", "<BASE>"],
        "--outcome-json",
        "hai review record",
    ),
    (
        ["clean", "--evidence-json", "<PATH>"],
        "--evidence-json",
        "hai clean",
    ),
])
def test_malformed_json_exits_user_input_with_named_stderr(
    argv, flag_label, command_label, malformed_path, base_dir,
):
    """Malformed JSON → USER_INPUT, stderr names command + flag + parse err."""

    argv = [a.replace("<PATH>", malformed_path).replace("<BASE>", base_dir)
            for a in argv]
    err_buf = StringIO()
    with redirect_stderr(err_buf):
        rc = cli_main(argv)
    assert rc == exit_codes.USER_INPUT
    stderr = err_buf.getvalue()
    assert command_label in stderr
    assert flag_label in stderr
    assert "not valid JSON" in stderr or "JSONDecodeError" in stderr
    assert "Traceback" not in stderr


# ---------------------------------------------------------------------------
# Top-level main() guard
# ---------------------------------------------------------------------------

def test_main_guard_catches_unexpected_exception(monkeypatch):
    """If a handler raises an unguarded exception, main() must catch it
    and return INTERNAL with a clean stderr line — never a raw traceback
    by default."""

    from health_agent_infra import cli

    def _explode(args):
        raise RuntimeError("simulated handler bug")

    monkeypatch.setattr(cli, "cmd_doctor", _explode)
    err_buf = StringIO()
    with redirect_stderr(err_buf):
        rc = cli.main(["doctor"])
    assert rc == exit_codes.INTERNAL
    stderr = err_buf.getvalue()
    assert "internal error" in stderr
    assert "RuntimeError" in stderr
    assert "simulated handler bug" in stderr
    # Default mode: no traceback. (HAI_DEBUG_TRACEBACK=1 surfaces it,
    # tested separately to avoid env-var leakage.)
    assert "Traceback" not in stderr


def test_main_guard_emits_traceback_when_env_var_set(monkeypatch):
    from health_agent_infra import cli

    def _explode(args):
        raise RuntimeError("debug-traceback test")

    monkeypatch.setattr(cli, "cmd_doctor", _explode)
    monkeypatch.setenv("HAI_DEBUG_TRACEBACK", "1")
    err_buf = StringIO()
    with redirect_stderr(err_buf):
        rc = cli.main(["doctor"])
    assert rc == exit_codes.INTERNAL
    stderr = err_buf.getvalue()
    assert "Traceback" in stderr
    assert "RuntimeError" in stderr


def test_main_guard_passes_through_systemexit():
    """argparse's own error path uses SystemExit(2). It must not be
    re-classified as INTERNAL."""

    from health_agent_infra import cli

    with pytest.raises(SystemExit) as exc_info:
        # A required arg is missing → argparse exits with SystemExit(2).
        cli.main(["propose"])
    assert exc_info.value.code == 2


def test_main_guard_handles_keyboard_interrupt(monkeypatch):
    from health_agent_infra import cli

    def _interrupt(args):
        raise KeyboardInterrupt()

    monkeypatch.setattr(cli, "cmd_doctor", _interrupt)
    err_buf = StringIO()
    with redirect_stderr(err_buf):
        rc = cli.main(["doctor"])
    assert rc == exit_codes.USER_INPUT
    stderr = err_buf.getvalue()
    assert "interrupted" in stderr


# ---------------------------------------------------------------------------
# cmd_pull --manual-readiness-json: harder to test without auth + DB,
# so we cover the guard via the helper directly.
# ---------------------------------------------------------------------------

def test_load_json_arg_helper_handles_all_three_failure_modes(tmp_path):
    """The helper itself is the contract — the per-handler tests above
    exercise the wiring; this test pins the helper's surface."""

    from health_agent_infra.cli import _load_json_arg

    # Missing path arg.
    err_buf = StringIO()
    with redirect_stderr(err_buf):
        data, code = _load_json_arg(
            None, arg_name="--evidence-json", command_label="hai test",
        )
    assert data is None
    assert code == exit_codes.USER_INPUT
    assert "is required" in err_buf.getvalue()

    # Bad path.
    err_buf = StringIO()
    with redirect_stderr(err_buf):
        data, code = _load_json_arg(
            str(tmp_path / "nope.json"),
            arg_name="--evidence-json", command_label="hai test",
        )
    assert data is None
    assert code == exit_codes.USER_INPUT
    assert "could not read" in err_buf.getvalue()

    # Malformed JSON.
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    err_buf = StringIO()
    with redirect_stderr(err_buf):
        data, code = _load_json_arg(
            str(bad), arg_name="--evidence-json", command_label="hai test",
        )
    assert data is None
    assert code == exit_codes.USER_INPUT
    assert "not valid JSON" in err_buf.getvalue()

    # Happy path.
    good = tmp_path / "good.json"
    good.write_text(json.dumps({"hello": "world"}), encoding="utf-8")
    data, code = _load_json_arg(
        str(good), arg_name="--evidence-json", command_label="hai test",
    )
    assert data == {"hello": "world"}
    assert code is None
