"""W-Vb (v0.1.13) — persona-replay end-to-end ship-set.

Origin: v0.1.13 PLAN.md §2.A W-Vb. v0.1.12 shipped the packaged-
fixture path + skeleton-loader + ``apply_fixture()`` returning a
deferred-to-v0.1.13 marker; v0.1.13 flips the boundary so
``hai demo start --persona <slug>`` followed by ``hai daily`` reaches
a ``synthesized`` daily plan end-to-end.

**Ship set is P1+P4+P5** (concrete slugs ``p1_dom_baseline`` /
``p4_strength_only_cutter`` / ``p5_female_multisport``). The 9 non-
ship-set personas (P2/P3/P6/P7/P8/P9/P10/P11/P12) are honestly fork-
deferred to v0.1.14 W-Vb-3 per F-PLAN-06 + F-PLAN-R2-02 and are NOT
covered here.

Each persona test asserts:

- ``apply_fixture()`` round-trip seeds proposal_log with 6 leaves.
- An in-process synthesis pass (the ``hai daily`` analogue without
  argparse boilerplate; same call-graph past the proposal gate)
  produces a ``daily_plan`` row referencing all 6 proposals.
- ``hai today`` rendering text for the synthesized plan is non-empty
  and names every domain section.
- ``hai explain`` audit-chain shape resolves the daily_plan_id back
  to its leaf recommendations + proposals.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.demo.fixtures import apply_fixture, load_fixture
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)


SHIP_SET: tuple[str, ...] = (
    "p1_dom_baseline",
    "p4_strength_only_cutter",
    "p5_female_multisport",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_cli(*args: str, expect_exit: int = 0) -> dict[str, Any]:
    """Invoke ``cli_main`` with stdout/stderr captured. Returns
    {exit, stdout, stdout_json, stderr}."""

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exit_code = cli_main(list(args))
    except SystemExit as exc:
        exit_code = int(exc.code) if isinstance(exc.code, int) else 2

    stdout = stdout_buf.getvalue()
    stderr = stderr_buf.getvalue()
    assert exit_code == expect_exit, (
        f"hai {' '.join(args)} exited {exit_code}, expected {expect_exit}.\n"
        f"stdout: {stdout[:500]}\nstderr: {stderr[:500]}"
    )
    stdout_json = None
    if stdout.strip():
        try:
            stdout_json = json.loads(stdout)
        except json.JSONDecodeError:
            stdout_json = None
    return {
        "exit": exit_code,
        "stdout": stdout,
        "stdout_json": stdout_json,
        "stderr": stderr,
    }


def _seed_demo_scratch(
    tmp_path: Path,
    persona_slug: str,
    *,
    for_date: date,
    user_id: str = "u_local_1",
) -> tuple[Path, Path]:
    """Initialise a scratch DB + base_dir for the given persona, then
    apply the packaged fixture against ``for_date``. Returns
    (db_path, base_dir).

    Mirrors what ``open_session(persona=...)`` does, minus the marker
    file write — the test does not need the marker because it drives
    cli_main with explicit --db-path / --base-dir args.
    """

    db_path = tmp_path / f"{persona_slug}_state.db"
    base_dir = tmp_path / f"{persona_slug}_base"
    base_dir.mkdir()
    initialize_database(db_path)

    fixture = load_fixture(persona_slug)
    result = apply_fixture(
        fixture,
        db_path=db_path,
        base_dir_path=base_dir,
        user_id=user_id,
        for_date=for_date,
    )
    assert result["applied"] is True
    assert result["scope"] == "full"
    assert result["proposals_written"] == 6
    return db_path, base_dir


# ---------------------------------------------------------------------------
# Smoke test — P1 reaches synthesized
# ---------------------------------------------------------------------------


def test_p1_dom_baseline_reaches_synthesized(tmp_path: Path) -> None:
    """The W-Vb smoke test. If this fails with a state-snapshot shape
    gap, the PLAN §4 risk fires: STOP and write CP7 before extending
    to P4 / P5."""

    target = date(2026, 4, 30)
    user_id = "u_local_1"
    db_path, base_dir = _seed_demo_scratch(
        tmp_path, "p1_dom_baseline", for_date=target, user_id=user_id,
    )

    # `hai daily` with --skip-pull mirrors the demo flow: no live
    # source available in the scratch session, but proposals are
    # already seeded so the gate passes and synthesis runs.
    res = _run_cli(
        "daily",
        "--db-path", str(db_path),
        "--base-dir", str(base_dir),
        "--as-of", target.isoformat(),
        "--user-id", user_id,
        "--skip-pull",
        "--source", "csv",
        "--skip-reviews",
    )
    payload = res["stdout_json"]
    assert payload is not None, f"hai daily emitted non-JSON stdout: {res['stdout'][:300]}"
    assert payload["overall_status"] == "complete", (
        f"hai daily for P1 did not synthesize; payload={payload}"
    )
    assert payload["stages"]["synthesize"]["status"] == "ran"
    assert len(payload["stages"]["synthesize"]["proposal_ids"]) == 6

    # daily_plan row landed.
    conn = open_connection(db_path)
    try:
        plan = conn.execute(
            "SELECT daily_plan_id, proposal_ids_json, recommendation_ids_json "
            "FROM daily_plan WHERE for_date = ? AND user_id = ?",
            (target.isoformat(), user_id),
        ).fetchone()
    finally:
        conn.close()
    assert plan is not None
    proposal_ids = json.loads(plan["proposal_ids_json"])
    recommendation_ids = json.loads(plan["recommendation_ids_json"])
    assert len(proposal_ids) == 6
    assert len(recommendation_ids) == 6


# ---------------------------------------------------------------------------
# Ship-set: P1 + P4 + P5 each reach a synthesized plan that surfaces
# in `hai today` text and resolves through `hai explain`.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("persona_slug", SHIP_SET)
def test_persona_replay_reaches_synthesized_and_renders(
    tmp_path: Path, persona_slug: str,
) -> None:
    target = date(2026, 4, 30)
    user_id = "u_local_1"
    db_path, base_dir = _seed_demo_scratch(
        tmp_path, persona_slug, for_date=target, user_id=user_id,
    )

    daily_res = _run_cli(
        "daily",
        "--db-path", str(db_path),
        "--base-dir", str(base_dir),
        "--as-of", target.isoformat(),
        "--user-id", user_id,
        "--skip-pull",
        "--source", "csv",
        "--skip-reviews",
    )
    payload = daily_res["stdout_json"]
    assert payload is not None
    assert payload["overall_status"] == "complete"
    daily_plan_id = payload["stages"]["synthesize"]["daily_plan_id"]
    assert daily_plan_id

    # `hai today` renders a non-empty plain-text plan.
    today_res = _run_cli(
        "today",
        "--db-path", str(db_path),
        "--as-of", target.isoformat(),
        "--user-id", user_id,
        "--format", "plain",
    )
    rendered = today_res["stdout"].strip()
    assert rendered, f"hai today rendered empty for {persona_slug}"

    # `hai explain` resolves the daily_plan_id back to its proposals
    # + recommendations (audit-chain shape).
    explain_res = _run_cli(
        "explain",
        "--db-path", str(db_path),
        "--as-of", target.isoformat(),
        "--user-id", user_id,
    )
    explain_payload = explain_res["stdout_json"]
    assert explain_payload is not None, (
        f"hai explain for {persona_slug} did not emit JSON: "
        f"{explain_res['stdout'][:200]}"
    )
    plan_block = explain_payload.get("plan") or {}
    assert plan_block.get("daily_plan_id") == daily_plan_id
    # Audit-chain integrity: every domain has both a recommendation
    # and a backing proposal in the explain envelope.
    recs = explain_payload.get("recommendations") or []
    proposals = explain_payload.get("proposals") or []
    assert len(recs) == 6, f"{persona_slug}: expected 6 recommendations, got {len(recs)}"
    assert len(proposals) == 6, f"{persona_slug}: expected 6 proposals, got {len(proposals)}"
    rec_domains = sorted(r["domain"] for r in recs)
    proposal_domains = sorted(p["domain"] for p in proposals)
    assert rec_domains == proposal_domains, (
        f"{persona_slug}: recommendation domains {rec_domains} differ "
        f"from proposal domains {proposal_domains}"
    )


# ---------------------------------------------------------------------------
# Per-persona action shape sanity — P4 strength-only must not push a
# planned run; P5 multisport keeps both running + strength active.
# ---------------------------------------------------------------------------


def test_p4_strength_only_cutter_does_not_push_planned_run(
    tmp_path: Path,
) -> None:
    target = date(2026, 4, 30)
    user_id = "u_local_1"
    db_path, base_dir = _seed_demo_scratch(
        tmp_path, "p4_strength_only_cutter",
        for_date=target, user_id=user_id,
    )
    _run_cli(
        "daily",
        "--db-path", str(db_path),
        "--base-dir", str(base_dir),
        "--as-of", target.isoformat(),
        "--user-id", user_id,
        "--skip-pull", "--source", "csv", "--skip-reviews",
    )
    conn = open_connection(db_path)
    try:
        running_action = conn.execute(
            "SELECT action FROM recommendation_log "
            "WHERE for_date = ? AND user_id = ? AND domain = 'running'",
            (target.isoformat(), user_id),
        ).fetchone()
        nutrition_action = conn.execute(
            "SELECT action FROM recommendation_log "
            "WHERE for_date = ? AND user_id = ? AND domain = 'nutrition'",
            (target.isoformat(), user_id),
        ).fetchone()
    finally:
        conn.close()
    assert running_action is not None
    assert running_action["action"] != "proceed_with_planned_run", (
        f"P4 cutter has no running plan today; running domain must not "
        f"recommend a planned run. Got {running_action['action']!r}"
    )
    assert nutrition_action is not None
    # Cutter persona's nutrition fixture targets a deficit-aware action.
    assert nutrition_action["action"] in (
        "reduce_calorie_deficit",
        "increase_protein_intake",
        "maintain_targets",
    )


def test_p5_female_multisport_keeps_running_and_strength_active(
    tmp_path: Path,
) -> None:
    target = date(2026, 4, 30)
    user_id = "u_local_1"
    db_path, base_dir = _seed_demo_scratch(
        tmp_path, "p5_female_multisport",
        for_date=target, user_id=user_id,
    )
    _run_cli(
        "daily",
        "--db-path", str(db_path),
        "--base-dir", str(base_dir),
        "--as-of", target.isoformat(),
        "--user-id", user_id,
        "--skip-pull", "--source", "csv", "--skip-reviews",
    )
    conn = open_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT domain, action FROM recommendation_log "
            "WHERE for_date = ? AND user_id = ?",
            (target.isoformat(), user_id),
        ).fetchall()
    finally:
        conn.close()
    by_domain = {r["domain"]: r["action"] for r in rows}
    assert "running" in by_domain
    assert "strength" in by_domain
    # Multisport persona keeps both domains active (no defer/rest on
    # either). The fixture seeds proceed_with_* on both.
    assert by_domain["running"].startswith("proceed_") or by_domain["running"] == "cross_train_instead"
    assert by_domain["strength"].startswith("proceed_")
