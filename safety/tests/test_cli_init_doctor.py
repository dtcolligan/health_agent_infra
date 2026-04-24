"""Tests for ``hai init``, ``hai doctor``, and ``hai --version``
(Phase 7 step 2).

``hai init`` is a first-run wizard that wraps the existing setup
subcommands (``config init`` + ``state init`` + ``setup-skills``) into a
single idempotent invocation and reports Garmin auth status without
prompting. ``hai doctor`` is a read-only diagnostic that reports the
same surfaces as present / missing / malformed. Both commands are
agent-friendly: no interactive prompts, structured JSON on stdout.

These tests pin:

- ``hai init`` first run (config + DB + skills created; auth missing).
- ``hai init`` rerun idempotency (reports ``already_present`` /
  ``already_at_head`` without clobbering files).
- ``hai init --skip-skills`` honours the skip.
- ``hai init --force`` overwrites existing config.
- ``hai doctor`` happy path (all ok after init).
- ``hai doctor`` missing-config / missing-db / missing-auth /
  missing-skills warnings.
- ``hai doctor`` malformed-config → fail + exit 2.
- ``hai doctor`` pending-migrations warn + exit 0.
- ``hai --version`` prints and exits 0 without a subcommand.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from health_agent_infra import __version__ as _PACKAGE_VERSION
from health_agent_infra import cli as cli_mod
from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.config import scaffold_thresholds_toml
from health_agent_infra.core.pull.auth import CredentialStore
from health_agent_infra.core import exit_codes


# ---------------------------------------------------------------------------
# Fake credential store — keeps tests from reading the real keyring / env
# ---------------------------------------------------------------------------


class _FakeKeyring:
    def __init__(self):
        self._data: dict[tuple[str, str], str] = {}

    def get_password(self, service, username):
        return self._data.get((service, username))

    def set_password(self, service, username, password):
        self._data[(service, username)] = password

    def delete_password(self, service, username):
        self._data.pop((service, username), None)


def _fake_store(*, env=None) -> CredentialStore:
    return CredentialStore(backend=_FakeKeyring(), env=env or {})


@pytest.fixture
def fake_empty_store(monkeypatch):
    """Credential store with no keyring entries and no env vars."""

    store = _fake_store()
    monkeypatch.setattr(
        cli_mod.CredentialStore, "default", classmethod(lambda cls: store)
    )
    return store


@pytest.fixture
def fake_stored_store(monkeypatch):
    """Credential store with populated keyring entries for both services."""

    store = _fake_store()
    store.store_garmin("alice@example.com", "s3cret")
    store.store_intervals_icu("i123456", "test_api_key")
    monkeypatch.setattr(
        cli_mod.CredentialStore, "default", classmethod(lambda cls: store)
    )
    return store


def _stdout_json(capsys) -> dict:
    out = capsys.readouterr().out
    return json.loads(out)


# ---------------------------------------------------------------------------
# hai --version
# ---------------------------------------------------------------------------


def test_version_flag_prints_package_version_and_exits_zero(capsys):
    # argparse ``action="version"`` raises SystemExit(0) after printing.
    with pytest.raises(SystemExit) as exc:
        cli_main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert out.strip() == f"hai {_PACKAGE_VERSION}"
    # Package version is non-empty and matches the importable attribute.
    assert _PACKAGE_VERSION


def test_version_flag_works_without_subcommand(capsys):
    # Subcommand is required, but --version must short-circuit the check.
    with pytest.raises(SystemExit) as exc:
        cli_main(["--version"])
    assert exc.value.code == 0
    assert "hai" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# hai init — first run
# ---------------------------------------------------------------------------


def _init_argv(tmp_path: Path, *extra: str) -> list[str]:
    return [
        "init",
        "--thresholds-path", str(tmp_path / "thresholds.toml"),
        "--db-path", str(tmp_path / "state.db"),
        "--skills-dest", str(tmp_path / "skills"),
        *extra,
    ]


def test_init_first_run_creates_config_db_and_skills(
    tmp_path, capsys, fake_empty_store,
):
    rc = cli_main(_init_argv(tmp_path))
    assert rc == 0
    report = _stdout_json(capsys)

    assert report["version"] == _PACKAGE_VERSION
    assert report["steps"]["config"]["status"] == "created"
    assert report["steps"]["config"]["path"] == str(tmp_path / "thresholds.toml")
    assert (tmp_path / "thresholds.toml").exists()

    db_step = report["steps"]["state_db"]
    assert db_step["status"] == "created"
    assert db_step["path"] == str(tmp_path / "state.db")
    assert db_step["schema_version_before"] == 0
    # At least migration 001 lands on a fresh DB; exact count is
    # migration-head-dependent so we assert non-empty.
    assert len(db_step["applied_migrations"]) >= 1
    assert (tmp_path / "state.db").exists()

    skills_step = report["steps"]["skills"]
    assert skills_step["status"] == "ran"
    # Packaged skills directory has multiple skills; assert the critical
    # ones without pinning a specific count so new skills don't break.
    copied_names = {Path(p).name for p in skills_step["copied"]}
    for required in {
        "recovery-readiness",
        "daily-plan-synthesis",
        "review-protocol",
    }:
        assert required in copied_names
    assert skills_step["already_present"] == []

    auth = report["steps"]["auth_garmin"]
    assert auth["status"] == "missing"
    assert auth["credentials_available"] is False
    assert "hai auth garmin" in auth["hint"]


def test_init_rerun_is_idempotent(tmp_path, capsys, fake_empty_store):
    # First run: everything gets created.
    cli_main(_init_argv(tmp_path))
    capsys.readouterr()

    # Capture the config file contents and mtime — rerun must not touch it.
    cfg_path = tmp_path / "thresholds.toml"
    original = cfg_path.read_text(encoding="utf-8")

    rc = cli_main(_init_argv(tmp_path))
    assert rc == 0
    report = _stdout_json(capsys)

    assert report["steps"]["config"]["status"] == "already_present"
    assert cfg_path.read_text(encoding="utf-8") == original

    db_step = report["steps"]["state_db"]
    assert db_step["status"] == "already_at_head"
    # schema_version_before reflects the existing head — non-zero.
    assert db_step["schema_version_before"] >= 1
    assert db_step["applied_migrations"] == []

    skills_step = report["steps"]["skills"]
    assert skills_step["status"] == "ran"
    assert skills_step["copied"] == []
    # Every packaged skill is reported as already present.
    assert len(skills_step["already_present"]) >= 3


def test_init_skip_skills_leaves_dest_untouched(
    tmp_path, capsys, fake_empty_store,
):
    rc = cli_main(_init_argv(tmp_path, "--skip-skills"))
    assert rc == 0
    report = _stdout_json(capsys)

    assert report["steps"]["skills"]["status"] == "skipped"
    assert not (tmp_path / "skills").exists()


def test_init_force_overwrites_existing_config(
    tmp_path, capsys, fake_empty_store,
):
    cfg_path = tmp_path / "thresholds.toml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text("# stale custom content\n", encoding="utf-8")

    rc = cli_main(_init_argv(tmp_path, "--force"))
    assert rc == 0
    report = _stdout_json(capsys)
    assert report["steps"]["config"]["status"] == "overwrote"
    # File now contains the scaffold, not the stale content.
    assert cfg_path.read_text(encoding="utf-8") == scaffold_thresholds_toml()


def test_init_reports_configured_when_credentials_present(
    tmp_path, capsys, fake_stored_store,
):
    rc = cli_main(_init_argv(tmp_path, "--skip-skills"))
    assert rc == 0
    report = _stdout_json(capsys)
    auth = report["steps"]["auth_garmin"]
    assert auth["status"] == "configured"
    assert auth["credentials_available"] is True
    assert auth["hint"] is None


# ---------------------------------------------------------------------------
# hai doctor
# ---------------------------------------------------------------------------


def _doctor_argv(tmp_path: Path, **overrides) -> list[str]:
    paths = {
        "thresholds-path": str(tmp_path / "thresholds.toml"),
        "db-path": str(tmp_path / "state.db"),
        "skills-dest": str(tmp_path / "skills"),
    }
    paths.update({k.replace("_", "-"): v for k, v in overrides.items()})
    # Default stdout shape is human-readable (M5); existing assertions
    # parse JSON, so every test passes --json explicitly.
    argv = ["doctor", "--json"]
    for flag, value in paths.items():
        argv += [f"--{flag}", value]
    return argv


def test_doctor_all_missing_returns_warn_and_exit_zero(
    tmp_path, capsys, fake_empty_store,
):
    rc = cli_main(_doctor_argv(tmp_path))
    # warn-level issues must not gate downstream commands (exit 0).
    assert rc == 0
    report = _stdout_json(capsys)

    assert report["version"] == _PACKAGE_VERSION
    assert report["overall_status"] == "warn"

    checks = report["checks"]
    assert checks["config"]["status"] == "warn"
    assert "thresholds file not present" in checks["config"]["reason"]
    assert checks["state_db"]["status"] == "warn"
    assert "state DB file not present" in checks["state_db"]["reason"]
    assert checks["auth_garmin"]["status"] == "warn"
    assert "no Garmin credentials stored" in checks["auth_garmin"]["reason"]
    assert checks["skills"]["status"] == "warn"
    assert checks["skills"]["installed_count"] == 0
    assert checks["skills"]["packaged_count"] >= 1
    assert checks["domains"]["status"] == "ok"
    # All six v1 domains land in the domains check regardless of setup state.
    assert set(checks["domains"]["domains"]) == {
        "recovery", "running", "sleep", "stress", "strength", "nutrition",
    }


def test_doctor_happy_path_after_init_returns_ok(
    tmp_path, capsys, fake_stored_store,
):
    # `hai init` scaffolds everything except auth; we injected credentials
    # via fake_stored_store so the doctor pass is fully green.
    cli_main(_init_argv(tmp_path))
    capsys.readouterr()

    rc = cli_main(_doctor_argv(tmp_path))
    assert rc == 0
    report = _stdout_json(capsys)
    assert report["overall_status"] == "ok"
    assert all(c["status"] == "ok" for c in report["checks"].values())
    assert report["checks"]["auth_garmin"]["credentials_source"] == "keyring"


def test_doctor_malformed_config_returns_fail_exit_two(
    tmp_path, capsys, fake_empty_store,
):
    cfg_path = tmp_path / "thresholds.toml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text("lol = = not toml", encoding="utf-8")

    rc = cli_main(_doctor_argv(tmp_path))
    assert rc == exit_codes.USER_INPUT
    report = _stdout_json(capsys)
    assert report["overall_status"] == "fail"
    assert report["checks"]["config"]["status"] == "fail"
    assert "malformed" in report["checks"]["config"]["reason"]


def test_doctor_env_only_credentials_reports_env_source(
    tmp_path, capsys, monkeypatch,
):
    # Env-var fallback path: keyring empty, both HAI_GARMIN_* set.
    store = CredentialStore(
        backend=_FakeKeyring(),
        env={"HAI_GARMIN_EMAIL": "bob@example.com", "HAI_GARMIN_PASSWORD": "pw"},
    )
    monkeypatch.setattr(
        cli_mod.CredentialStore, "default", classmethod(lambda cls: store)
    )

    rc = cli_main(_doctor_argv(tmp_path))
    assert rc == 0
    report = _stdout_json(capsys)
    assert report["checks"]["auth_garmin"]["status"] == "ok"
    assert report["checks"]["auth_garmin"]["credentials_source"] == "env"


def test_doctor_pending_migrations_warn(
    tmp_path, capsys, monkeypatch, fake_empty_store,
):
    # Build a real DB + sqlite_migrations row, then monkeypatch the
    # migration-discovery helper to pretend a later migration exists. The
    # DB itself still functions; the doctor must report the pending
    # delta without crashing on missing SQL.
    from health_agent_infra.core.state import initialize_database
    from health_agent_infra.core.state import store as state_store

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    real = state_store.discover_migrations()
    head = max((v for v, _, _ in real), default=0)
    fake_future = real + [(head + 1, f"{head + 1:03d}_fake_future.sql", "SELECT 1;")]
    # ``cmd_doctor`` imports ``discover_migrations`` at call time, so
    # patching the module attribute is sufficient.
    monkeypatch.setattr(state_store, "discover_migrations", lambda: fake_future)

    rc = cli_main(_doctor_argv(tmp_path))
    assert rc == 0
    report = _stdout_json(capsys)
    db_check = report["checks"]["state_db"]
    assert db_check["status"] == "warn"
    assert db_check["pending_migrations"] == 1
    assert db_check["head_version"] == head + 1
    assert db_check["schema_version"] == head


def test_doctor_partial_skills_install_is_warn(
    tmp_path, capsys, fake_empty_store,
):
    # Create skills dest with only one skill; doctor must list the rest
    # under ``missing`` and status=warn.
    dest = tmp_path / "skills"
    dest.mkdir(parents=True)
    (dest / "recovery-readiness").mkdir()

    rc = cli_main(_doctor_argv(tmp_path))
    assert rc == 0
    report = _stdout_json(capsys)
    skills = report["checks"]["skills"]
    assert skills["status"] == "warn"
    assert skills["installed_count"] == 1
    assert skills["packaged_count"] >= 2
    # The other packaged skills show up in missing.
    assert "daily-plan-synthesis" in skills["missing"]


# ---------------------------------------------------------------------------
# hai init --with-auth
# ---------------------------------------------------------------------------


class _NoRawRowAdapter:
    """Fake live adapter: reports as garmin_live, returns no raw_daily_row.

    No raw_daily_row means _daily_pull_and_project returns projected=False
    and skips projection — the pull path and sync_run_log bookkeeping are
    exercised without needing the full projection-friendly row shape. The
    projection path has its own tests; the backfill loop is the target
    here.
    """

    source_name = "garmin_live"

    def load(self, as_of):
        return {
            "sleep": None,
            "resting_hr": [],
            "hrv": [],
            "training_load": [],
            "raw_daily_row": None,
        }


def test_init_with_auth_noops_when_already_configured(
    tmp_path, capsys, fake_stored_store,
):
    rc = cli_main(_init_argv(tmp_path, "--with-auth"))
    assert rc == 0
    report = _stdout_json(capsys)

    # Existing steps still present and unchanged in shape.
    assert report["steps"]["auth_garmin"]["credentials_available"] is True
    # New step records the short-circuit.
    assert report["steps"]["interactive_auth"]["status"] == "already_configured"


def test_init_with_auth_prompts_and_stores(
    tmp_path, capsys, monkeypatch, fake_empty_store,
):
    # Simulate a user typing an email at input() and a password at getpass().
    # 0.1.2 wiring: the email prompt is written to stderr *outside* of
    # input() so the redirect_stdout around cmd_auth_garmin doesn't eat
    # it. getpass already writes to stderr by default.
    import builtins
    import getpass as getpass_mod

    getpass_prompts: list[str] = []

    def fake_getpass(prompt: str = "") -> str:
        getpass_prompts.append(prompt)
        return "s3cret!"

    monkeypatch.setattr(builtins, "input", lambda _="": "new_user@example.com")
    monkeypatch.setattr(getpass_mod, "getpass", fake_getpass)

    rc = cli_main(_init_argv(tmp_path, "--with-auth"))
    assert rc == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert report["steps"]["interactive_auth"]["status"] == "configured"
    # Credentials actually landed in the injected keyring.
    creds = fake_empty_store.load_garmin()
    assert creds is not None
    assert creds.email == "new_user@example.com"
    assert creds.password == "s3cret!"
    # Email prompt went to stderr (the whole point of the 0.1.2 fix).
    assert "Garmin email:" in captured.err
    # Getpass prompt arg mentions password (getpass writes to stderr on its own).
    assert any("password" in p.lower() for p in getpass_prompts)


def test_init_with_auth_emits_single_json_document(
    tmp_path, capsys, monkeypatch, fake_empty_store,
):
    """cmd_auth_garmin's own JSON is silenced so stdout stays a single doc."""

    import builtins
    import getpass as getpass_mod

    monkeypatch.setattr(builtins, "input", lambda _="": "a@b.com")
    monkeypatch.setattr(getpass_mod, "getpass", lambda _="": "pw")

    rc = cli_main(_init_argv(tmp_path, "--with-auth"))
    assert rc == 0
    out = capsys.readouterr().out
    # Exactly one JSON document on stdout — json.loads on the whole stream
    # would fail if cmd_auth_garmin had leaked its own JSON through.
    parsed = json.loads(out)
    assert "steps" in parsed


def test_init_with_auth_handles_eof_gracefully(
    tmp_path, capsys, monkeypatch, fake_empty_store,
):
    # No stdin → cmd_auth_garmin's input() raises EOFError; we report
    # user_skipped rather than surfacing the traceback.
    import builtins

    def raising_input(prompt: str = "") -> str:
        raise EOFError()

    monkeypatch.setattr(builtins, "input", raising_input)

    rc = cli_main(_init_argv(tmp_path, "--with-auth"))
    assert rc == 0
    report = _stdout_json(capsys)
    assert report["steps"]["interactive_auth"]["status"] == "user_skipped"


# ---------------------------------------------------------------------------
# hai init --with-first-pull
# ---------------------------------------------------------------------------


def test_init_with_first_pull_skips_without_credentials(
    tmp_path, capsys, fake_empty_store,
):
    rc = cli_main(_init_argv(tmp_path, "--with-first-pull"))
    assert rc == 0
    report = _stdout_json(capsys)
    first = report["steps"]["first_pull"]
    assert first["status"] == "skipped"
    assert "credentials" in first["reason"].lower()


def test_init_with_first_pull_makes_single_adapter_call(
    tmp_path, capsys, monkeypatch, fake_stored_store,
):
    """0.1.2 design: one adapter.load(today), not a per-day loop."""

    call_log: list = []

    class _CountingAdapter:
        source_name = "garmin_live"

        def load(self, as_of):
            call_log.append(as_of)
            return {
                "sleep": None, "resting_hr": [], "hrv": [],
                "training_load": [], "raw_daily_row": None,
            }

    monkeypatch.setattr(
        cli_mod, "_build_live_adapter", lambda args: _CountingAdapter(),
    )

    rc = cli_main(_init_argv(tmp_path, "--with-first-pull"))
    assert rc == 0
    report = _stdout_json(capsys)

    first = report["steps"]["first_pull"]
    assert first["status"] == "ok"
    assert first["history_days"] == 1  # default
    assert first["approx_api_calls"] == 5  # 5 calls per fetch_day × 1 day
    assert first["source"] == "garmin_live"

    # Exactly one adapter.load(), and for today.
    assert len(call_log) == 1


def test_init_with_first_pull_respects_history_days_override(
    tmp_path, capsys, monkeypatch, fake_stored_store,
):
    monkeypatch.setattr(
        cli_mod, "_build_live_adapter", lambda args: _NoRawRowAdapter(),
    )

    rc = cli_main(_init_argv(
        tmp_path, "--with-first-pull", "--history-days", "7",
    ))
    assert rc == 0
    report = _stdout_json(capsys)

    first = report["steps"]["first_pull"]
    assert first["status"] == "ok"
    assert first["history_days"] == 7
    assert first["approx_api_calls"] == 35  # 5 × 7


def test_init_with_first_pull_writes_one_sync_row(
    tmp_path, capsys, monkeypatch, fake_stored_store,
):
    """Single pull → single sync_run_log row, status='ok'."""

    from health_agent_infra.core.state import open_connection

    monkeypatch.setattr(
        cli_mod, "_build_live_adapter", lambda args: _NoRawRowAdapter(),
    )

    rc = cli_main(_init_argv(tmp_path, "--with-first-pull"))
    assert rc == 0

    conn = open_connection(tmp_path / "state.db")
    try:
        rows = conn.execute(
            "SELECT source, status, mode, for_date FROM sync_run_log "
            "ORDER BY sync_id"
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 1
    assert rows[0]["source"] == "garmin_live"
    assert rows[0]["status"] == "ok"
    assert rows[0]["mode"] == "live"


def test_init_with_first_pull_records_failure_with_hint(
    tmp_path, capsys, monkeypatch, fake_stored_store,
):
    """A GarminLiveError (e.g. 429) is surfaced with a retry hint."""

    from health_agent_infra.core.pull.garmin_live import GarminLiveError
    from health_agent_infra.core.state import open_connection

    class _ExplodingAdapter:
        source_name = "garmin_live"

        def load(self, as_of):
            raise GarminLiveError("429 Too Many Requests")

    monkeypatch.setattr(
        cli_mod, "_build_live_adapter", lambda args: _ExplodingAdapter(),
    )

    rc = cli_main(_init_argv(tmp_path, "--with-first-pull"))
    # Init itself doesn't fail — first_pull is advisory, not required.
    assert rc == 0
    report = _stdout_json(capsys)

    first = report["steps"]["first_pull"]
    assert first["status"] == "failed"
    assert first["error_class"] == "GarminLiveError"
    assert "429" in first["error"]
    # The hint guides the user to a lower-footprint retry.
    assert "history-days 1" in first["hint"]
    # Failed sync row is still persisted for the audit trail.
    conn = open_connection(tmp_path / "state.db")
    try:
        rows = conn.execute(
            "SELECT status, error_class FROM sync_run_log"
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) == 1
    assert rows[0]["status"] == "failed"
    assert rows[0]["error_class"] == "GarminLiveError"


def test_init_with_auth_and_first_pull_end_to_end(
    tmp_path, capsys, monkeypatch, fake_empty_store,
):
    """Happy path: fresh machine → --with-auth → --with-first-pull in one call."""

    import builtins
    import getpass as getpass_mod

    monkeypatch.setattr(builtins, "input", lambda _="": "flow@example.com")
    monkeypatch.setattr(getpass_mod, "getpass", lambda _="": "s3cret")
    monkeypatch.setattr(
        cli_mod, "_build_live_adapter", lambda args: _NoRawRowAdapter(),
    )

    rc = cli_main(_init_argv(
        tmp_path, "--with-auth", "--with-first-pull", "--history-days", "2",
    ))
    assert rc == 0
    report = _stdout_json(capsys)

    # Step 5: auth moved from missing → configured.
    assert report["steps"]["auth_garmin"]["status"] == "missing"  # pre-prompt snapshot
    assert report["steps"]["interactive_auth"]["status"] == "configured"

    # Step 6: first-pull honoured the freshly-stored creds with the chosen window.
    first = report["steps"]["first_pull"]
    assert first["status"] == "ok"
    assert first["history_days"] == 2
    assert first["approx_api_calls"] == 10


def test_init_without_new_flags_does_not_add_new_steps(
    tmp_path, capsys, fake_empty_store,
):
    """Backward compatibility: default `hai init` shape is unchanged."""

    rc = cli_main(_init_argv(tmp_path))
    assert rc == 0
    report = _stdout_json(capsys)

    expected_steps = {"config", "state_db", "skills", "auth_garmin"}
    assert set(report["steps"].keys()) == expected_steps
