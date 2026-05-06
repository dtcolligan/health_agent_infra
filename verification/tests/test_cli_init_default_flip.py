"""W-OB-2 (v0.1.18 §2.B) — `hai init` default-flip release-blocker test.

Acceptance per PLAN.md §2.B item 3 (5-case test, expanded from 4 per
OQ-2 Codex disposition):

  (i)    interactive TTY + missing onboarding fields → ``--guided`` fires
  (ii)   interactive TTY + complete onboarding state → bare init
  (iii)  non-interactive (no TTY) → bare init regardless of state
  (iv-f) ``--non-interactive`` flag + isatty=True + missing fields → bare init
  (iv-e) ``HAI_INIT_NON_INTERACTIVE=1`` env + isatty=True + missing fields → bare init

Each test uses ``monkeypatch`` of ``sys.stdin.isatty`` + ``os.environ``
rather than launching subprocesses. The default-flip decision is also
captured in the JSON report at ``report["default_flip"]["decision"]``
so the test can assert on the predicate outcome directly without
parsing prompt output.
"""

from __future__ import annotations

import io
import json
import os
import sqlite3
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from health_agent_infra import cli as cli_mod
from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.init import ScriptedPrompts
from health_agent_infra.core.pull.auth import CredentialStore
from health_agent_infra.core.state import initialize_database


USER = "u_w_ob_2"


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class _FakeKeyring:
    def __init__(self) -> None:
        self._data: dict[tuple[str, str], str] = {}

    def get_password(self, service, username):
        return self._data.get((service, username))

    def set_password(self, service, username, password):
        self._data[(service, username)] = password

    def delete_password(self, service, username):
        self._data.pop((service, username), None)


def _fake_store() -> CredentialStore:
    return CredentialStore(backend=_FakeKeyring(), env={})


@pytest.fixture
def fake_credential_store(monkeypatch):
    store = _fake_store()
    monkeypatch.setattr(
        cli_mod.CredentialStore, "default", classmethod(lambda cls: store)
    )
    return store


@pytest.fixture
def restore_default_flip_env(monkeypatch):
    """Override the suite-wide ``HAI_INIT_NON_INTERACTIVE=1`` autouse so
    these tests can exercise the default-flip predicate."""

    monkeypatch.delenv("HAI_INIT_NON_INTERACTIVE", raising=False)


def _set_isatty(monkeypatch, value: bool) -> None:
    """Force ``sys.stdin.isatty()`` to return a fixed value."""

    monkeypatch.setattr("sys.stdin.isatty", lambda: value)


def _run_cmd_init(*argv: str, prompts=None) -> tuple[int, dict, str]:
    """Run ``hai init`` and return (rc, json_report, stderr).

    If ``prompts`` is supplied (a ScriptedPrompts), wires it to the
    guided onboarding orchestrator so we can answer the focus + target
    prompts deterministically when the default-flip fires.
    """

    # Inject the test prompts into the guided orchestrator. The
    # cmd_init handler calls _run_guided_onboarding which honours
    # ``args._guided_prompts_override`` (existing test seam).
    out_buf = io.StringIO()
    err_buf = io.StringIO()

    # Build args via argparse so the new --non-interactive flag parses
    # correctly; we attach the prompts override to the parsed namespace.
    parser = cli_mod.build_parser()
    args = parser.parse_args(["init", *argv])
    if prompts is not None:
        args._guided_prompts_override = prompts
        args._guided_pull_runner_override = lambda **kw: {
            "status": "ok", "for_date": str(kw.get("as_of"))
        }
        args._guided_today_renderer_override = lambda **kw: {
            "status": "no_plan_yet", "for_date": str(kw.get("as_of")),
            "user_id": kw.get("user_id"),
        }

    try:
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = args.func(args)
    except SystemExit as exc:
        rc = int(exc.code) if isinstance(exc.code, int) else 2

    out = out_buf.getvalue()
    try:
        report = json.loads(out)
    except json.JSONDecodeError:
        report = {}
    return rc, report, err_buf.getvalue()


def _seed_complete_onboarding_state(db_path: Path, user_id: str = USER) -> None:
    """Create intent + target rows so check_onboarding_readiness returns
    OK (or at least not WARN with missing intent/target). We don't need
    a real wellness pull for the predicate to skip the default-flip on
    'complete' — but the docstring says all three preconditions need to
    pass for OK. So seed wellness_pull too via a direct sync_run_log row.
    """

    initialize_database(db_path)

    from health_agent_infra.core.intent import add_intent
    from health_agent_infra.core.target import add_target
    from health_agent_infra.core.state import open_connection
    from datetime import date as _date

    today = _date.today()

    conn = open_connection(db_path)
    try:
        add_intent(
            conn,
            user_id=user_id,
            domain="running",
            intent_type="training_session",
            scope_start=today,
            scope_type="day",
            status="active",
            priority="normal",
            flexibility="flexible",
            payload={"focus": "running"},
            reason="seed for test",
            source="user_authored",
            ingest_actor="cli",
        )
        add_target(
            conn,
            user_id=user_id,
            domain="nutrition",
            target_type="calories_kcal",
            value=2400,
            unit="kcal",
            effective_from=today,
            status="active",
            reason="seed for test",
            source="user_authored",
            ingest_actor="cli",
        )
        # Seed a successful wellness pull row.
        conn.execute(
            "INSERT INTO sync_run_log (user_id, source, mode, "
            "for_date, status, started_at, completed_at) "
            "VALUES (?, ?, 'live', ?, 'ok', datetime('now'), datetime('now'))",
            (user_id, "intervals_icu", today.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Case (i) — interactive TTY + missing fields → guided fires
# ---------------------------------------------------------------------------


def test_case_i_tty_plus_missing_fields_fires_guided(
    tmp_path, monkeypatch, restore_default_flip_env, fake_credential_store
):
    db_path = tmp_path / "state.db"
    skills_dest = tmp_path / "skills"
    skills_dest.mkdir()
    thresholds = tmp_path / "thresholds.toml"

    _set_isatty(monkeypatch, True)

    # Provide scripted prompts so the guided flow can run end-to-end.
    prompts = ScriptedPrompts(
        responses=[
            None,            # athlete id (skip auth)
            "running",       # focus
            "2400",          # kcal
            "140",           # protein
            "8",             # sleep
        ]
    )

    rc, report, err = _run_cmd_init(
        "--db-path", str(db_path),
        "--thresholds-path", str(thresholds),
        "--skills-dest", str(skills_dest),
        "--skip-skills",
        "--user-id", USER,
        prompts=prompts,
    )

    assert report.get("default_flip", {}).get("decision") == "fired_incomplete"
    assert "guided" in report.get("steps", {})
    # Exit code may be OK or USER_INPUT depending on whether auth was skipped;
    # the default-flip firing is what we're testing, not the eventual exit.


# ---------------------------------------------------------------------------
# Case (ii) — interactive TTY + complete state → bare init
# ---------------------------------------------------------------------------


def test_case_ii_tty_plus_complete_state_runs_bare_init(
    tmp_path, monkeypatch, restore_default_flip_env, fake_credential_store
):
    db_path = tmp_path / "state.db"
    skills_dest = tmp_path / "skills"
    skills_dest.mkdir()
    thresholds = tmp_path / "thresholds.toml"

    _seed_complete_onboarding_state(db_path)
    _set_isatty(monkeypatch, True)

    rc, report, err = _run_cmd_init(
        "--db-path", str(db_path),
        "--thresholds-path", str(thresholds),
        "--skills-dest", str(skills_dest),
        "--skip-skills",
        "--user-id", USER,
    )

    assert rc == exit_codes.OK
    assert report.get("default_flip", {}).get("decision") == "not_fired_already_complete"
    # No guided block in the report.
    assert "guided" not in report.get("steps", {})


# ---------------------------------------------------------------------------
# Case (iii) — no TTY → bare init regardless of state
# ---------------------------------------------------------------------------


def test_case_iii_no_tty_runs_bare_init(
    tmp_path, monkeypatch, restore_default_flip_env, fake_credential_store
):
    db_path = tmp_path / "state.db"
    skills_dest = tmp_path / "skills"
    skills_dest.mkdir()
    thresholds = tmp_path / "thresholds.toml"

    # No TTY — opt-out via the implicit predicate.
    _set_isatty(monkeypatch, False)

    rc, report, err = _run_cmd_init(
        "--db-path", str(db_path),
        "--thresholds-path", str(thresholds),
        "--skills-dest", str(skills_dest),
        "--skip-skills",
        "--user-id", USER,
    )

    assert rc == exit_codes.OK
    assert report.get("default_flip", {}).get("decision") == "opt_out_no_tty"
    assert "guided" not in report.get("steps", {})


# ---------------------------------------------------------------------------
# Case (iv-flag) — explicit --non-interactive flag + TTY → bare init
# ---------------------------------------------------------------------------


def test_case_iv_flag_explicit_non_interactive_runs_bare_init(
    tmp_path, monkeypatch, restore_default_flip_env, fake_credential_store
):
    db_path = tmp_path / "state.db"
    skills_dest = tmp_path / "skills"
    skills_dest.mkdir()
    thresholds = tmp_path / "thresholds.toml"

    _set_isatty(monkeypatch, True)

    rc, report, err = _run_cmd_init(
        "--db-path", str(db_path),
        "--thresholds-path", str(thresholds),
        "--skills-dest", str(skills_dest),
        "--skip-skills",
        "--non-interactive",
        "--user-id", USER,
    )

    assert rc == exit_codes.OK
    assert report.get("default_flip", {}).get("decision") == "opt_out_flag"
    assert "guided" not in report.get("steps", {})


# ---------------------------------------------------------------------------
# Case (iv-env) — HAI_INIT_NON_INTERACTIVE=1 env + TTY → bare init
# ---------------------------------------------------------------------------


def test_case_iv_env_hai_init_non_interactive_runs_bare_init(
    tmp_path, monkeypatch, restore_default_flip_env, fake_credential_store
):
    db_path = tmp_path / "state.db"
    skills_dest = tmp_path / "skills"
    skills_dest.mkdir()
    thresholds = tmp_path / "thresholds.toml"

    _set_isatty(monkeypatch, True)
    monkeypatch.setenv("HAI_INIT_NON_INTERACTIVE", "1")

    rc, report, err = _run_cmd_init(
        "--db-path", str(db_path),
        "--thresholds-path", str(thresholds),
        "--skills-dest", str(skills_dest),
        "--skip-skills",
        "--user-id", USER,
    )

    assert rc == exit_codes.OK
    assert report.get("default_flip", {}).get("decision") == "opt_out_env"
    assert "guided" not in report.get("steps", {})


# ---------------------------------------------------------------------------
# Bonus — explicit --guided still works (should be unaffected by the flip)
# ---------------------------------------------------------------------------


def test_explicit_guided_flag_unaffected_by_default_flip(
    tmp_path, monkeypatch, restore_default_flip_env, fake_credential_store
):
    db_path = tmp_path / "state.db"
    skills_dest = tmp_path / "skills"
    skills_dest.mkdir()
    thresholds = tmp_path / "thresholds.toml"

    # No TTY but explicit --guided — should still fire the guided flow.
    _set_isatty(monkeypatch, False)

    prompts = ScriptedPrompts(
        responses=[
            None,            # athlete id (skip)
            "running",       # focus
            "2400",          # kcal
            None, None,      # protein, sleep skipped
        ]
    )

    rc, report, err = _run_cmd_init(
        "--db-path", str(db_path),
        "--thresholds-path", str(thresholds),
        "--skills-dest", str(skills_dest),
        "--skip-skills",
        "--guided",
        "--user-id", USER,
        prompts=prompts,
    )

    assert report.get("default_flip", {}).get("decision") == "explicit_guided"
    assert "guided" in report.get("steps", {})
