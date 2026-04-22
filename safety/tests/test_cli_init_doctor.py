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
    """Credential store with a populated keyring entry."""

    store = _fake_store()
    store.store_garmin("alice@example.com", "s3cret")
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
        "writeback-protocol",
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
    import builtins
    import getpass as getpass_mod

    prompts_seen: list[str] = []

    def fake_input(prompt: str = "") -> str:
        prompts_seen.append(prompt)
        return "new_user@example.com"

    def fake_getpass(prompt: str = "") -> str:
        prompts_seen.append(prompt)
        return "s3cret!"

    monkeypatch.setattr(builtins, "input", fake_input)
    monkeypatch.setattr(getpass_mod, "getpass", fake_getpass)

    rc = cli_main(_init_argv(tmp_path, "--with-auth"))
    assert rc == 0
    report = _stdout_json(capsys)

    assert report["steps"]["interactive_auth"]["status"] == "configured"
    # Credentials actually landed in the injected keyring.
    creds = fake_empty_store.load_garmin()
    assert creds is not None
    assert creds.email == "new_user@example.com"
    assert creds.password == "s3cret!"
    # Both prompts fired — proof we actually hit the interactive path.
    assert any("email" in p.lower() for p in prompts_seen)
    assert any("password" in p.lower() for p in prompts_seen)


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


def test_init_with_first_pull_runs_default_seven_days(
    tmp_path, capsys, monkeypatch, fake_stored_store,
):
    # Inject a fake live adapter so no network / real Garmin call happens.
    monkeypatch.setattr(
        cli_mod, "_build_live_adapter", lambda args: _NoRawRowAdapter(),
    )

    rc = cli_main(_init_argv(tmp_path, "--with-first-pull"))
    assert rc == 0
    report = _stdout_json(capsys)

    first = report["steps"]["first_pull"]
    assert first["status"] == "ran"
    assert first["days_requested"] == 7
    assert first["days_succeeded"] == 7
    assert first["days_failed"] == 0
    assert len(first["per_day"]) == 7
    # Dates are unique and chronological (oldest → newest).
    dates_seen = [entry["date"] for entry in first["per_day"]]
    assert dates_seen == sorted(dates_seen)
    assert len(set(dates_seen)) == 7
    # Every entry reports the source name and no projection (no raw_daily_row).
    for entry in first["per_day"]:
        assert entry["status"] == "ok"
        assert entry["source"] == "garmin_live"
        assert entry["projected_raw_daily"] is False


def test_init_with_first_pull_respects_days_override(
    tmp_path, capsys, monkeypatch, fake_stored_store,
):
    monkeypatch.setattr(
        cli_mod, "_build_live_adapter", lambda args: _NoRawRowAdapter(),
    )

    rc = cli_main(_init_argv(tmp_path, "--with-first-pull", "--first-pull-days", "3"))
    assert rc == 0
    report = _stdout_json(capsys)

    first = report["steps"]["first_pull"]
    assert first["days_requested"] == 3
    assert first["days_succeeded"] == 3
    assert len(first["per_day"]) == 3


def test_init_with_first_pull_writes_one_sync_row_per_day(
    tmp_path, capsys, monkeypatch, fake_stored_store,
):
    from health_agent_infra.core.state import open_connection

    monkeypatch.setattr(
        cli_mod, "_build_live_adapter", lambda args: _NoRawRowAdapter(),
    )

    rc = cli_main(_init_argv(tmp_path, "--with-first-pull", "--first-pull-days", "4"))
    assert rc == 0

    conn = open_connection(tmp_path / "state.db")
    try:
        rows = conn.execute(
            "SELECT source, status, mode, for_date FROM sync_run_log "
            "ORDER BY sync_id"
        ).fetchall()
    finally:
        conn.close()

    # Four successful live-pull rows, one per backfill day.
    assert len(rows) == 4
    assert all(row["source"] == "garmin_live" for row in rows)
    assert all(row["status"] == "ok" for row in rows)
    assert all(row["mode"] == "live" for row in rows)
    # for_date values cover a chronological 4-day window with no gaps.
    for_dates = sorted(row["for_date"] for row in rows)
    assert len(set(for_dates)) == 4


def test_init_with_first_pull_continues_past_per_day_failure(
    tmp_path, capsys, monkeypatch, fake_stored_store,
):
    from health_agent_infra.core.pull.garmin_live import GarminLiveError

    class _SometimesFailingAdapter:
        source_name = "garmin_live"

        def __init__(self):
            self._call_count = 0

        def load(self, as_of):
            self._call_count += 1
            # Fail on the 2nd call so we can prove the loop doesn't abort.
            if self._call_count == 2:
                raise GarminLiveError("simulated 503 on day 2")
            return {
                "sleep": None,
                "resting_hr": [],
                "hrv": [],
                "training_load": [],
                "raw_daily_row": None,
            }

    # Reuse one adapter instance across the backfill so call_count survives.
    adapter = _SometimesFailingAdapter()
    monkeypatch.setattr(cli_mod, "_build_live_adapter", lambda args: adapter)

    rc = cli_main(_init_argv(tmp_path, "--with-first-pull", "--first-pull-days", "5"))
    assert rc == 0
    report = _stdout_json(capsys)

    first = report["steps"]["first_pull"]
    assert first["status"] == "ran"
    assert first["days_requested"] == 5
    assert first["days_succeeded"] == 4
    assert first["days_failed"] == 1
    # The failure entry carries error context for later triage.
    failed_entries = [e for e in first["per_day"] if e["status"] == "failed"]
    assert len(failed_entries) == 1
    assert failed_entries[0]["error_class"] == "GarminLiveError"
    assert "503" in failed_entries[0]["error"]


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
        tmp_path, "--with-auth", "--with-first-pull", "--first-pull-days", "2",
    ))
    assert rc == 0
    report = _stdout_json(capsys)

    # Step 5: auth moved from missing → configured.
    assert report["steps"]["auth_garmin"]["status"] == "missing"  # pre-prompt snapshot
    assert report["steps"]["interactive_auth"]["status"] == "configured"

    # Step 6: first-pull honoured the freshly-stored creds.
    first = report["steps"]["first_pull"]
    assert first["status"] == "ran"
    assert first["days_requested"] == 2
    assert first["days_succeeded"] == 2


def test_init_without_new_flags_does_not_add_new_steps(
    tmp_path, capsys, fake_empty_store,
):
    """Backward compatibility: default `hai init` shape is unchanged."""

    rc = cli_main(_init_argv(tmp_path))
    assert rc == 0
    report = _stdout_json(capsys)

    expected_steps = {"config", "state_db", "skills", "auth_garmin"}
    assert set(report["steps"].keys()) == expected_steps
