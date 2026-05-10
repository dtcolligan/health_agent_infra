"""F-PV14-01 — CSV-fixture pull isolation marker (v0.1.15).

Per `hai/reporting/plans/v0_1_15/PLAN.md` §2.C.

Carry-over evidence (`hai/reporting/plans/post_v0_1_14/carry_over_findings.md`):
the maintainer's canonical state DB acquired three fixture-shaped
`sync_run_log` rows (garmin, garmin_live, readiness_manual) on 2026-05-01
when no `hai daily` had been invoked. Root cause: the CSV adapter
(`core/pull/garmin.py:43 load_recovery_readiness_inputs`) writes through
the same `_open_sync_row` / `_close_sync_row_ok` codepath as live pulls,
with no `hai demo` marker check. The contamination shape is "for_date"
months/years before "last" — F-PV14-01 acceptance test 2 below probes
exactly that.

Acceptance per PLAN §2.C:

  1. Repro: `hai pull --source csv` against canonical-resolved DB without
     a demo marker → USER_INPUT exit, zero rows in `sync_run_log`.
  2. Regression: `hai stats` / `hai doctor` WARN when `last` (sync row
     started_at) and `for_date` diverge by >48h.

Plus contract clauses in PLAN §2.C:

  3. Default-deny escape paths: `--allow-fixture-into-real-state` flag
     OR active `hai demo` marker permits CSV→canonical writes.
  4. Capabilities-manifest source-type tagging (live vs fixture).
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)


USER = "u_test"
AS_OF = date(2026, 5, 2)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _isolated_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    """Initialise a tmp DB + base_dir AND clear env-var overrides so the
    canonical-DB resolver sees a "no overrides" state for the F-PV14-01
    guard tests. Returns (base_dir, db_path) — the tests pass these
    explicitly via --db-path / --base-dir for the *positive-escape*
    cases; the guard-fires test uses neither flag and relies on the
    DEFAULT_DB_PATH-monkeypatch to redirect away from the user's real
    home dir."""

    monkeypatch.delenv("HAI_STATE_DB", raising=False)
    monkeypatch.delenv("HAI_BASE_DIR", raising=False)
    monkeypatch.delenv("HAI_DEMO_MARKER_PATH", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)

    base = tmp_path / "intake"
    base.mkdir(parents=True, exist_ok=True)
    db = tmp_path / "state.db"
    initialize_database(db)
    return base, db


def _redirect_canonical_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Monkeypatch `DEFAULT_DB_PATH` to a tmp location so the F-PV14-01
    guard's `args.db_path is None and HAI_STATE_DB is unset` branch
    resolves to a sandboxed canonical path. Returns the redirected path.
    Also redirects `DEFAULT_BASE_DIR` so cmd_pull's base-dir resolution
    doesn't write to the user's real home."""

    canonical_db = tmp_path / "canonical_state.db"
    canonical_base = tmp_path / "canonical_intake"
    canonical_base.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        "health_agent_infra.core.state.store.DEFAULT_DB_PATH",
        canonical_db,
    )
    monkeypatch.setattr(
        "health_agent_infra.core.paths.DEFAULT_BASE_DIR",
        canonical_base,
    )
    initialize_database(canonical_db)
    return canonical_db


# ---------------------------------------------------------------------------
# Acceptance test 1 — `hai pull --source csv` refused against canonical DB
# ---------------------------------------------------------------------------


def test_csv_pull_against_canonical_db_refused_no_sync_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    """PLAN §2.C acceptance 1: `hai pull --source csv` against the
    canonical-resolved DB without a demo marker → USER_INPUT, ZERO rows
    in sync_run_log.
    """

    _isolated_dirs(tmp_path, monkeypatch)
    canonical_db = _redirect_canonical_paths(tmp_path, monkeypatch)

    # No --db-path, no --base-dir → resolver picks the (monkeypatched)
    # canonical default. No demo marker (cleared by _isolated_dirs).
    rc = cli_main([
        "pull",
        "--source", "csv",
        "--user-id", USER,
        "--date", AS_OF.isoformat(),
        "--use-default-manual-readiness",
    ])
    assert rc == exit_codes.USER_INPUT, (
        f"expected USER_INPUT refusal, got rc={rc}"
    )

    # Zero rows in sync_run_log.
    conn = open_connection(canonical_db)
    try:
        rows = conn.execute(
            "SELECT * FROM sync_run_log WHERE user_id = ?", (USER,),
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) == 0, (
        f"sync_run_log must have zero rows after refused CSV pull; "
        f"got {len(rows)} rows"
    )


# ---------------------------------------------------------------------------
# Escape path 1 — explicit --allow-fixture-into-real-state flag
# ---------------------------------------------------------------------------


def test_csv_pull_with_allow_fixture_flag_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    """PLAN §2.C contract: explicit `--allow-fixture-into-real-state`
    flag overrides the F-PV14-01 default-deny."""

    _isolated_dirs(tmp_path, monkeypatch)
    canonical_db = _redirect_canonical_paths(tmp_path, monkeypatch)

    rc = cli_main([
        "pull",
        "--source", "csv",
        "--user-id", USER,
        "--date", AS_OF.isoformat(),
        "--use-default-manual-readiness",
        "--allow-fixture-into-real-state",
    ])
    assert rc == exit_codes.OK, (
        f"--allow-fixture-into-real-state should permit CSV pull; rc={rc}"
    )

    conn = open_connection(canonical_db)
    try:
        rows = conn.execute(
            "SELECT * FROM sync_run_log WHERE user_id = ?", (USER,),
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) >= 1, (
        f"explicit-flag escape should write at least one sync row; got {len(rows)}"
    )


# ---------------------------------------------------------------------------
# Escape path 2 — explicit --db-path opts in (non-canonical target)
# ---------------------------------------------------------------------------


def test_csv_pull_with_explicit_db_path_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    """User-explicit --db-path means user opted in: the F-PV14-01 guard
    only fires when the resolver lands on the canonical default, not
    when the user explicitly redirects."""

    base, db = _isolated_dirs(tmp_path, monkeypatch)
    _redirect_canonical_paths(tmp_path, monkeypatch)

    rc = cli_main([
        "pull",
        "--source", "csv",
        "--user-id", USER,
        "--date", AS_OF.isoformat(),
        "--use-default-manual-readiness",
        "--db-path", str(db),
    ])
    assert rc == exit_codes.OK, (
        f"explicit --db-path should permit CSV pull; rc={rc}"
    )

    conn = open_connection(db)
    try:
        rows = conn.execute(
            "SELECT * FROM sync_run_log WHERE user_id = ?", (USER,),
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) >= 1


# ---------------------------------------------------------------------------
# Escape path 3 — HAI_STATE_DB env-var override opts in
# ---------------------------------------------------------------------------


def test_csv_pull_with_hai_state_db_env_var_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    """HAI_STATE_DB env var means user (or harness) opted in to a
    non-canonical destination."""

    base, db = _isolated_dirs(tmp_path, monkeypatch)
    _redirect_canonical_paths(tmp_path, monkeypatch)
    monkeypatch.setenv("HAI_STATE_DB", str(db))

    rc = cli_main([
        "pull",
        "--source", "csv",
        "--user-id", USER,
        "--date", AS_OF.isoformat(),
        "--use-default-manual-readiness",
    ])
    assert rc == exit_codes.OK, (
        f"HAI_STATE_DB env override should permit CSV pull; rc={rc}"
    )


# ---------------------------------------------------------------------------
# F-IR-02 round-1 IR fix — `hai daily` enforces the same guard
# ---------------------------------------------------------------------------


def test_hai_daily_csv_against_canonical_db_refused_no_sync_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys,
):
    """F-IR-02: `hai daily --source csv` against canonical-resolved DB
    without demo marker → refused. Same guard `hai pull` enforces.
    Pre-fix the daily orchestrator silently bypassed F-PV14-01 and
    wrote fixture rows into the canonical DB."""

    _isolated_dirs(tmp_path, monkeypatch)
    canonical_db = _redirect_canonical_paths(tmp_path, monkeypatch)

    rc = cli_main([
        "daily",
        "--source", "csv",
        "--user-id", USER,
        "--as-of", AS_OF.isoformat(),
    ])
    # The refusal exits USER_INPUT (the same code cmd_pull uses).
    assert rc == exit_codes.USER_INPUT, (
        f"hai daily --source csv against canonical DB should refuse; "
        f"got rc={rc}"
    )

    conn = open_connection(canonical_db)
    try:
        rows = conn.execute(
            "SELECT * FROM sync_run_log WHERE user_id=?", (USER,),
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) == 0, (
        f"hai daily refused-by-F-PV14-01 must not write any sync rows; "
        f"got {len(rows)} rows"
    )

    # The daily report shape on stdout includes the structured refusal.
    payload = json.loads(capsys.readouterr().out)
    assert payload.get("overall_status") == "refused"
    assert payload.get("stages", {}).get("pull", {}).get("status") == "refused"
    assert "F-PV14-01" in payload["stages"]["pull"].get("reason", "")


def test_hai_daily_csv_with_allow_fixture_flag_passes_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys,
):
    """F-IR-02 + F-IR-R2-01 (round 2): `hai daily --source csv
    --allow-fixture-into-real-state` MUST step the F-PV14-01 guard
    aside. Pre-round-2 the test was vacuous (assertion always True);
    Codex round 2 caught the gap. Now we capture stdout and assert
    the daily payload is NOT the F-PV14-01 refusal shape — i.e., the
    guard didn't fire even though the resolver would have landed on
    the canonical default DB."""

    _isolated_dirs(tmp_path, monkeypatch)
    canonical_db = _redirect_canonical_paths(tmp_path, monkeypatch)

    cli_main([
        "daily",
        "--source", "csv",
        "--user-id", USER,
        "--as-of", AS_OF.isoformat(),
        "--allow-fixture-into-real-state",
    ])
    captured = capsys.readouterr()

    # The F-PV14-01 refusal shape: stdout payload has
    # `overall_status="refused"` and `stages.pull.status="refused"`
    # with the `F-PV14-01: ...` reason. Any other shape (success,
    # downstream INTERNAL failure, USER_INPUT for a different cause)
    # means the guard correctly stepped aside.
    if captured.out.strip():
        try:
            payload = json.loads(captured.out)
        except json.JSONDecodeError:
            payload = {}
    else:
        payload = {}

    assert payload.get("overall_status") != "refused", (
        f"--allow-fixture-into-real-state must step F-PV14-01 guard "
        f"aside; got refusal payload: {payload}"
    )
    pull_stage = (payload.get("stages") or {}).get("pull") or {}
    assert pull_stage.get("status") != "refused", (
        f"daily pull stage must not refuse with F-PV14-01 when allow-flag "
        f"is set; got pull stage: {pull_stage}"
    )

    # Stronger positive proof: at least one sync row landed in the
    # canonical-redirected DB. The F-PV14-01 refusal would have
    # blocked the sync row, so its presence proves the guard let
    # the pull through.
    conn = open_connection(canonical_db)
    try:
        rows = conn.execute(
            "SELECT * FROM sync_run_log WHERE user_id=?", (USER,),
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) >= 1, (
        f"--allow-fixture-into-real-state should let the daily pull "
        f"stage write a sync row; got {len(rows)} rows"
    )


def test_hai_daily_csv_with_active_demo_marker_passes_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys,
):
    """F-IR-R2-01 (round 2): close the daily-side coverage gap for
    the demo-marker escape path. `hai pull` already has a
    demo-marker test; `hai daily` should too since the shared
    helper is called from both."""

    from health_agent_infra.core.demo import session as _demo_session

    _isolated_dirs(tmp_path, monkeypatch)
    canonical_db = _redirect_canonical_paths(tmp_path, monkeypatch)

    # Activate a demo marker. The is_demo_active() helper at
    # core/demo/session.py:126 is a cheap presence check on the
    # marker file path.
    marker_path = tmp_path / "demo_marker.json"
    marker_path.write_text(
        json.dumps({"marker_id": "test", "scratch_root": str(tmp_path)}),
        encoding="utf-8",
    )
    monkeypatch.setenv("HAI_DEMO_MARKER_PATH", str(marker_path))

    # Sanity: confirm the monkeypatch took.
    assert _demo_session.is_demo_active() is True, (
        "demo marker monkeypatch failed; test setup invalid"
    )

    cli_main([
        "daily",
        "--source", "csv",
        "--user-id", USER,
        "--as-of", AS_OF.isoformat(),
    ])
    captured = capsys.readouterr()

    # The guard must step aside when a demo marker is active.
    if captured.out.strip():
        try:
            payload = json.loads(captured.out)
        except json.JSONDecodeError:
            payload = {}
    else:
        payload = {}

    pull_stage = (payload.get("stages") or {}).get("pull") or {}
    assert payload.get("overall_status") != "refused", (
        f"active demo marker must step F-PV14-01 guard aside on hai daily; "
        f"got refusal payload: {payload}"
    )
    assert pull_stage.get("status") != "refused", (
        f"daily pull stage must not refuse with F-PV14-01 when demo marker "
        f"is active; got pull stage: {pull_stage}"
    )


def test_hai_daily_csv_with_explicit_db_path_passes_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    """F-IR-02: explicit --db-path opts the user into a non-canonical
    target; the F-PV14-01 guard does not fire."""

    base, db = _isolated_dirs(tmp_path, monkeypatch)
    _redirect_canonical_paths(tmp_path, monkeypatch)

    rc = cli_main([
        "daily",
        "--source", "csv",
        "--user-id", USER,
        "--as-of", AS_OF.isoformat(),
        "--db-path", str(db),
        "--base-dir", str(base),
    ])
    # The F-PV14-01 refusal returns USER_INPUT with overall_status=
    # 'refused'. Other USER_INPUT exits (e.g., no proposals) are fine.
    # The presence of sync rows in the explicit DB confirms the guard
    # stepped aside and the pull stage actually ran.
    conn = open_connection(db)
    try:
        rows = conn.execute(
            "SELECT * FROM sync_run_log WHERE user_id=?", (USER,),
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) >= 1, (
        f"explicit --db-path should let the daily pull stage run; "
        f"got {len(rows)} sync rows in the explicit DB"
    )


# ---------------------------------------------------------------------------
# Acceptance test 2 — stats/doctor WARN on >48h last-vs-for_date divergence
# ---------------------------------------------------------------------------


def _seed_sync_row_with_divergence(
    db_path: Path, *, source: str, days_diverged: int,
) -> None:
    """Write a sync_run_log row with `started_at` = today and `for_date`
    = today - days_diverged. Used to simulate the F-PV14-01 contamination
    shape (CSV fixture for an old date, written today)."""

    started_at = datetime.now(timezone.utc).replace(microsecond=0)
    for_date = (started_at.date() - timedelta(days=days_diverged))
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO sync_run_log "
            "(source, user_id, mode, started_at, completed_at, "
            "status, for_date, rows_pulled, rows_accepted, "
            "duplicates_skipped) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                source, USER, "csv",
                started_at.isoformat(), started_at.isoformat(),
                "ok", for_date.isoformat(),
                1, 1, 0,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def test_stats_warns_on_for_date_divergence_over_48h(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys,
):
    """PLAN §2.C acceptance 2: `hai stats --json` flags sources whose
    `last` and `for_date` diverge by >48h."""

    base, db = _isolated_dirs(tmp_path, monkeypatch)

    _seed_sync_row_with_divergence(db, source="garmin", days_diverged=80)
    _seed_sync_row_with_divergence(db, source="intervals_icu", days_diverged=0)

    rc = cli_main([
        "stats", "--json",
        "--user-id", USER,
        "--db-path", str(db),
    ])
    assert rc == exit_codes.OK
    payload = json.loads(capsys.readouterr().out)

    freshness = payload.get("sync_freshness", {})
    assert "garmin" in freshness
    assert "intervals_icu" in freshness

    garmin = freshness["garmin"]
    assert garmin.get("for_date_divergence_hours") is not None
    assert garmin["for_date_divergence_hours"] > 48
    assert garmin.get("for_date_divergence_warn") is True, (
        f"garmin row diverged 80 days; expected for_date_divergence_warn=True. "
        f"Got: {garmin}"
    )

    icu = freshness["intervals_icu"]
    assert icu.get("for_date_divergence_warn") is False, (
        f"intervals_icu row is fresh-day; expected divergence_warn=False. "
        f"Got: {icu}"
    )


def test_doctor_warns_on_for_date_divergence_over_48h(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys,
):
    """PLAN §2.C acceptance 2 (doctor side): `hai doctor` `sources`
    block warns when any source's last-vs-for_date divergence > 48h."""

    base, db = _isolated_dirs(tmp_path, monkeypatch)

    _seed_sync_row_with_divergence(db, source="garmin", days_diverged=80)

    rc = cli_main([
        "doctor", "--json",
        "--user-id", USER,
        "--db-path", str(db),
    ])
    # doctor exit code is OK even when warnings present; the WARN is
    # informational (matches existing doctor convention for warnings).
    payload = json.loads(capsys.readouterr().out)

    sources = payload.get("checks", {}).get("sources", {})
    assert sources.get("status") == "warn", (
        f"doctor sources status should be 'warn' when a sync row diverges "
        f">48h; got status={sources.get('status')!r}. Payload: {sources}"
    )


# ---------------------------------------------------------------------------
# Capabilities-manifest source-type tagging (live vs fixture)
# ---------------------------------------------------------------------------


def test_capabilities_manifest_tags_pull_source_choices_with_source_type(
    capsys,
):
    """PLAN §2.C contract: `hai capabilities --json` annotates each
    `--source` choice with a `source_type` tag (`live` vs `fixture`)
    so an agent driving the CLI knows the CSV path is fixture-only."""

    rc = cli_main(["capabilities", "--json"])
    assert rc == exit_codes.OK
    payload = json.loads(capsys.readouterr().out)

    pull_cmd = next(
        c for c in payload["commands"] if c["name"] == "hai pull"
    )
    source_flag = next(
        f for f in pull_cmd["flags"] if f.get("name") == "--source"
    )
    metadata = source_flag.get("choice_metadata") or {}

    csv_meta = metadata.get("csv") or {}
    assert csv_meta.get("source_type") == "fixture", (
        f"csv source must be tagged source_type='fixture'; got {csv_meta}"
    )
    icu_meta = metadata.get("intervals_icu") or {}
    assert icu_meta.get("source_type") == "live", (
        f"intervals_icu must be tagged source_type='live'; got {icu_meta}"
    )
    live_meta = metadata.get("garmin_live") or {}
    assert live_meta.get("source_type") == "live", (
        f"garmin_live must be tagged source_type='live'; got {live_meta}"
    )
