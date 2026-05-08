"""W-29 §2.A acceptance item 5: handler-dispatch smoke test.

Exercises one non-default flag per moved handler-group module
(≥11 smoke tests, one per group). Catches subtle ``argparse``
``dest`` renames or handler-namespace breaks the manifest-shape
test would miss — the manifest walker at
``core/capabilities/walker.py:437`` records flag name/kind/choices/default
but NOT ``dest`` or the resolved handler callable.

Each test invokes a non-default code path and asserts:
- exit code is OK or USER_INPUT (handler ran cleanly without
  NameError / AttributeError / unhandled exception)
- a meaningful side effect proves the handler reached its body
  (stdout JSON shape, stderr error message, or DB row created)

These are smoke tests — they don't pin payload shape, just that the
parser-tree resolves to the correct ``cmd_*`` callable in each
handler group post-W-29.2 split.
"""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import initialize_database


def _run(*argv: str) -> tuple[int, str, str]:
    """Run cli_main with stdout/stderr captured. Returns (rc, stdout, stderr)."""

    out_buf = io.StringIO()
    err_buf = io.StringIO()
    try:
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = cli_main(list(argv))
    except SystemExit as exc:
        rc = int(exc.code) if isinstance(exc.code, int) else 2
    return rc, out_buf.getvalue(), err_buf.getvalue()


def _fresh_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


# ---------------------------------------------------------------------------
# One smoke per handler-group module.
# Each smoke invokes a non-default surface and asserts the handler ran
# cleanly (no NameError / AttributeError / unhandled exception).
# ---------------------------------------------------------------------------


def test_smoke_auth_handler_group_resolves():
    """cli/handlers/auth.py — `hai auth status` is the simplest read-only
    surface. Returns OK and emits backend JSON when handler resolves."""

    rc, out, err = _run("auth", "status")
    assert rc == exit_codes.OK, f"auth status failed rc={rc}, stderr={err[:200]}"
    assert "backend" in out, f"auth status JSON missing 'backend': {out[:200]}"


def test_smoke_pull_clean_handler_group_resolves(tmp_path):
    """cli/handlers/pull_clean.py — `hai clean --evidence-json <path>` with
    a non-existent path: handler runs and emits USER_INPUT (not crash)."""

    fake = tmp_path / "no_such_evidence.json"
    rc, out, err = _run("clean", "--evidence-json", str(fake))
    assert rc == exit_codes.USER_INPUT, (
        f"clean dispatch failed: rc={rc}, stderr={err[:200]}"
    )
    assert "evidence-json" in err.lower() or "not found" in err.lower(), (
        f"clean stderr should mention the missing file: {err[:200]}"
    )


def test_smoke_state_handler_group_resolves(tmp_path):
    """cli/handlers/state.py — `hai state read --domain recovery` with
    a fresh DB: handler runs and emits an empty list."""

    db = _fresh_db(tmp_path)
    rc, out, err = _run(
        "state", "read",
        "--db-path", str(db),
        "--domain", "recovery",
        "--since", "2026-04-01",
    )
    assert rc == exit_codes.OK, f"state read failed rc={rc}, stderr={err[:200]}"
    assert out.strip().startswith("[") or out.strip().startswith("{"), (
        f"state read should emit JSON: {out[:200]}"
    )


def test_smoke_config_init_handler_group_resolves(tmp_path):
    """cli/handlers/config_init.py — `hai config init --path X --force`
    creates a thresholds file. Non-default `--force` flag exercises the
    handler's overwrite path."""

    cfg = tmp_path / "thresholds.toml"
    rc, out, err = _run("config", "init", "--path", str(cfg), "--force")
    assert rc == exit_codes.OK, (
        f"config init dispatch failed: rc={rc}, stderr={err[:200]}"
    )
    assert cfg.exists(), "config init should have created the thresholds file"


def test_smoke_intake_handler_group_resolves(tmp_path):
    """cli/handlers/intake.py — `hai intake readiness` with non-default
    --soreness flag exercises the readiness handler."""

    rc, out, err = _run(
        "intake", "readiness",
        "--soreness", "low",
        "--energy", "moderate",
        "--planned-session-type", "rest",
        "--base-dir", str(tmp_path),
        "--db-path", str(_fresh_db(tmp_path)),
        "--user-id", "u_smoke",
    )
    assert rc == exit_codes.OK, (
        f"intake readiness failed rc={rc}, stderr={err[:200]}"
    )
    assert "submission_id" in out or "submission" in out, (
        f"intake readiness should emit submission JSON: {out[:200]}"
    )


def test_smoke_intent_handler_group_resolves(tmp_path):
    """cli/handlers/intent.py — `hai intent list --user-id X` with a fresh
    DB: handler runs and emits an empty list (no intent rows yet)."""

    db = _fresh_db(tmp_path)
    rc, out, err = _run(
        "intent", "list",
        "--db-path", str(db),
        "--user-id", "u_smoke",
    )
    assert rc == exit_codes.OK, f"intent list failed rc={rc}, stderr={err[:200]}"
    assert out.strip().startswith("[") or out.strip().startswith("{"), (
        f"intent list should emit JSON: {out[:200]}"
    )


def test_smoke_target_handler_group_resolves(tmp_path):
    """cli/handlers/target.py — `hai target list --user-id X` with a fresh
    DB: handler runs and emits an empty list (no target rows yet)."""

    db = _fresh_db(tmp_path)
    rc, out, err = _run(
        "target", "list",
        "--db-path", str(db),
        "--user-id", "u_smoke",
    )
    assert rc == exit_codes.OK, f"target list failed rc={rc}, stderr={err[:200]}"
    assert out.strip().startswith("[") or out.strip().startswith("{"), (
        f"target list should emit JSON: {out[:200]}"
    )


def test_smoke_recommend_handler_group_resolves(tmp_path):
    """cli/handlers/recommend.py — `hai daily --skip-pull` with --as-of
    flag exercises the daily orchestrator's parser path. With no proposals
    in DB, exits OK with overall_status=awaiting_proposals."""

    db = _fresh_db(tmp_path)
    base_dir = tmp_path / "out"
    rc, out, err = _run(
        "daily",
        "--db-path", str(db),
        "--base-dir", str(base_dir),
        "--as-of", "2026-04-22",
        "--user-id", "u_smoke",
        "--skip-pull",
    )
    assert rc == exit_codes.OK, f"daily dispatch failed rc={rc}, stderr={err[:200]}"
    assert "overall_status" in out, (
        f"daily should emit JSON with overall_status: {out[:200]}"
    )


def test_smoke_review_handler_group_resolves(tmp_path):
    """cli/handlers/review.py — `hai review summary --user-id X` with no
    outcomes file: handler runs and emits the empty-summary shape."""

    rc, out, err = _run(
        "review", "summary",
        "--base-dir", str(tmp_path),
        "--user-id", "u_smoke",
    )
    assert rc == exit_codes.OK, f"review summary failed rc={rc}, stderr={err[:200]}"
    assert out.strip().startswith("{"), (
        f"review summary should emit JSON object: {out[:200]}"
    )


def test_smoke_inspect_handler_group_resolves(tmp_path):
    """cli/handlers/inspect.py — `hai today --format json` with --user-id flag.
    Exercises the inspect handler-group's dispatch even when no plan exists."""

    db = _fresh_db(tmp_path)
    rc, out, err = _run(
        "today",
        "--db-path", str(db),
        "--user-id", "u_smoke",
        "--format", "json",
    )
    # rc may be OK or USER_INPUT depending on whether no-plan is treated
    # as honest-absence (OK) or unrecoverable (USER_INPUT). Either is a
    # clean handler dispatch — just not a NameError.
    assert rc in (exit_codes.OK, exit_codes.USER_INPUT), (
        f"today dispatch failed rc={rc}, stderr={err[:200]}"
    )


def test_smoke_tools_handler_group_resolves(tmp_path):
    """cli/handlers/tools.py — `hai memory list --user-id X` with a fresh
    DB: handler runs and emits an empty list."""

    db = _fresh_db(tmp_path)
    rc, out, err = _run(
        "memory", "list",
        "--db-path", str(db),
        "--user-id", "u_smoke",
    )
    assert rc == exit_codes.OK, f"memory list failed rc={rc}, stderr={err[:200]}"


# ---------------------------------------------------------------------------
# Coverage assertion — at least one smoke per handler group
# ---------------------------------------------------------------------------


def test_smoke_coverage_matches_handler_modules():
    """Sanity: there's one smoke test per handler-group module.

    If a new handler-group module is added under cli/handlers/, this
    test fails — author the corresponding smoke above.
    """

    handlers_dir = (
        Path(__file__).resolve().parents[2]
        / "src" / "health_agent_infra" / "cli" / "handlers"
    )
    modules = {p.stem for p in handlers_dir.glob("*.py") if p.name != "__init__.py"}
    expected = {
        "auth", "pull_clean", "state", "config_init",
        "intake", "intent", "target", "recommend",
        "review", "inspect", "tools",
    }
    missing_smoke = modules - expected
    assert not missing_smoke, (
        f"new handler-group module(s) lack a smoke test in this file: "
        f"{sorted(missing_smoke)}. Add one per W-29 §2.A item 5."
    )
    missing_module = expected - modules
    assert not missing_module, (
        f"smoke test(s) reference non-existent handler-group module(s): "
        f"{sorted(missing_module)}."
    )
