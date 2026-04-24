"""Snapshot tests for ``hai today`` (v0.1.4 WS-E / D3 test #7-ish).

Five scenarios, each pinning the byte shape of ``hai today --format
plain`` output so unintended rendering drift fires loudly. The
fixtures live under ``golden/`` next to this file; update them
deliberately when the voice / structure of ``hai today`` changes.

**Update policy.** If a test here fails after an intentional change
to ``core/narration/render.py`` or ``templates.py``, regenerate the
fixture file from the test's current output (the test prints a diff
on failure) and commit both the code change and the fixture update
in the same commit. The golden files are part of the voice
contract: their diffs are the place where a "renderer tweak" is
visible on a PR.

Scope note: ``hai explain --operator`` snapshots are listed in the
v0.1.4 acceptance criteria but are deferred — that surface is
operator-facing audit output and its drift is less user-visible
than ``hai today``'s. If a v0.1.5 consumer needs them, they slot
into this same harness.
"""

from __future__ import annotations

import io
import json
import sqlite3
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.schemas import canonical_daily_plan_id
from health_agent_infra.core.state import initialize_database


GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


USER = "u_snap"
AS_OF = date(2026, 4, 24)


# ---------------------------------------------------------------------------
# Helpers — seed a plan, invoke `hai today`, compare to golden.
# ---------------------------------------------------------------------------


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _seed_plan(
    db: Path,
    *,
    plan_id: str | None = None,
    recs: list[dict],
) -> str:
    plan_id = plan_id or canonical_daily_plan_id(AS_OF, USER)
    rec_ids = [r["recommendation_id"] for r in recs]
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            INSERT INTO daily_plan (
                daily_plan_id, user_id, for_date, synthesized_at,
                recommendation_ids_json, proposal_ids_json,
                x_rules_fired_json, synthesis_meta_json,
                source, ingest_actor, validated_at, projected_at
            ) VALUES (?, ?, ?, '2026-04-24T07:00:00+00:00', ?, '[]', '[]',
                      NULL, 'snapshot', 'snapshot',
                      '2026-04-24T07:00:00+00:00', '2026-04-24T07:00:00+00:00')
            """,
            (
                plan_id, USER, AS_OF.isoformat(),
                json.dumps(rec_ids),
            ),
        )
        for rec in recs:
            payload = {
                "recommendation_id": rec["recommendation_id"],
                "domain": rec["domain"],
                "action": rec["action"],
                "confidence": rec.get("confidence", "moderate"),
                "rationale": rec.get("rationale", [f"{rec['domain']}_baseline"]),
                "uncertainty": rec.get("uncertainty", []),
                "follow_up": {
                    "review_question": rec.get(
                        "review_question", f"How did today's {rec['domain']} land?",
                    ),
                },
            }
            conn.execute(
                """
                INSERT INTO recommendation_log (
                    recommendation_id, user_id, for_date, issued_at,
                    action, confidence, bounded, payload_json,
                    source, ingest_actor, produced_at, validated_at,
                    projected_at, domain, daily_plan_id
                ) VALUES (?, ?, ?, '2026-04-24T07:00:00+00:00',
                          ?, ?, 1, ?, 'snapshot', 'snapshot',
                          '2026-04-24T07:00:00+00:00',
                          '2026-04-24T07:00:00+00:00',
                          '2026-04-24T07:00:00+00:00', ?, ?)
                """,
                (
                    rec["recommendation_id"], USER, AS_OF.isoformat(),
                    rec["action"], payload["confidence"],
                    json.dumps(payload, sort_keys=True),
                    rec["domain"], plan_id,
                ),
            )
        conn.commit()
    return plan_id


def _run_today_plain(db: Path, *extra: str) -> str:
    argv = [
        "today",
        "--as-of", AS_OF.isoformat(),
        "--user-id", USER,
        "--db-path", str(db),
        "--format", "plain",
        *extra,
    ]
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        rc = cli_main(argv)
    return rc, stdout.getvalue(), stderr.getvalue()


def _assert_snapshot(actual: str, *, name: str) -> None:
    """Compare ``actual`` to ``GOLDEN_DIR / name``. On mismatch,
    raise with a readable diff. Seeds the fixture file on first
    run if it doesn't exist — makes adding new scenarios painless.

    To regenerate a fixture deliberately: delete the file and rerun.
    """

    GOLDEN_DIR.mkdir(exist_ok=True)
    golden_path = GOLDEN_DIR / name
    if not golden_path.exists():
        golden_path.write_text(actual, encoding="utf-8")
        pytest.skip(
            f"seeded new snapshot fixture at {golden_path}; rerun the test "
            f"to lock it in"
        )
    expected = golden_path.read_text(encoding="utf-8")
    if actual != expected:
        import difflib
        diff = "\n".join(difflib.unified_diff(
            expected.splitlines(),
            actual.splitlines(),
            fromfile=f"golden/{name}",
            tofile="actual",
            lineterm="",
        ))
        pytest.fail(
            f"`hai today` output drifted from {name!r}:\n{diff}\n"
            f"If this is intentional, delete {golden_path} and rerun."
        )


# ---------------------------------------------------------------------------
# Scenario 1 — green day (all six domains prescribe)
# ---------------------------------------------------------------------------


def test_green_day_snapshot(tmp_path: Path) -> None:
    db = _init_db(tmp_path)
    _seed_plan(db, recs=[
        {"recommendation_id": f"rec_{AS_OF}_{USER}_recovery_01",
         "domain": "recovery", "action": "proceed_with_planned_session"},
        {"recommendation_id": f"rec_{AS_OF}_{USER}_sleep_01",
         "domain": "sleep", "action": "maintain_schedule"},
        {"recommendation_id": f"rec_{AS_OF}_{USER}_running_01",
         "domain": "running", "action": "proceed_with_planned_run"},
        {"recommendation_id": f"rec_{AS_OF}_{USER}_strength_01",
         "domain": "strength", "action": "proceed_with_planned_session"},
        {"recommendation_id": f"rec_{AS_OF}_{USER}_stress_01",
         "domain": "stress", "action": "maintain_routine"},
        {"recommendation_id": f"rec_{AS_OF}_{USER}_nutrition_01",
         "domain": "nutrition", "action": "maintain_targets"},
    ])
    rc, out, _err = _run_today_plain(db)
    assert rc == 0
    _assert_snapshot(out, name="green_day.txt")


# ---------------------------------------------------------------------------
# Scenario 2 — mixed day (2 prescriptions + 4 defers)
# ---------------------------------------------------------------------------


def test_mixed_day_snapshot(tmp_path: Path) -> None:
    db = _init_db(tmp_path)
    _seed_plan(db, recs=[
        {"recommendation_id": f"rec_{AS_OF}_{USER}_recovery_01",
         "domain": "recovery", "action": "proceed_with_planned_session"},
        {"recommendation_id": f"rec_{AS_OF}_{USER}_sleep_01",
         "domain": "sleep", "action": "defer_decision_insufficient_signal"},
        {"recommendation_id": f"rec_{AS_OF}_{USER}_running_01",
         "domain": "running", "action": "defer_decision_insufficient_signal"},
        {"recommendation_id": f"rec_{AS_OF}_{USER}_strength_01",
         "domain": "strength", "action": "proceed_with_planned_session"},
        {"recommendation_id": f"rec_{AS_OF}_{USER}_stress_01",
         "domain": "stress", "action": "defer_decision_insufficient_signal"},
        {"recommendation_id": f"rec_{AS_OF}_{USER}_nutrition_01",
         "domain": "nutrition", "action": "defer_decision_insufficient_signal"},
    ])
    rc, out, _err = _run_today_plain(db)
    assert rc == 0
    _assert_snapshot(out, name="mixed_day.txt")


# ---------------------------------------------------------------------------
# Scenario 3 — no plan (user hasn't run `hai daily` yet)
# ---------------------------------------------------------------------------


def test_no_plan_snapshot(tmp_path: Path) -> None:
    """When no canonical plan exists for the date, `hai today` exits
    USER_INPUT with a stderr hint. The snapshot pins both surfaces."""

    from health_agent_infra.core import exit_codes

    db = _init_db(tmp_path)
    rc, out, err = _run_today_plain(db)
    assert rc == exit_codes.USER_INPUT
    assert out == ""
    _assert_snapshot(err, name="no_plan.stderr.txt")


# ---------------------------------------------------------------------------
# Scenario 4 — cold-start day (running cold-start uncertainty + footer)
# ---------------------------------------------------------------------------


def test_cold_start_day_snapshot(tmp_path: Path) -> None:
    """A day-one cold-start user who signalled running intent. All
    six domains are cold-start; recovery/sleep tend to have live
    wearable signal so they've prescribed; the others may defer or
    surface cold-start uncertainty depending on the classifier. The
    fixture captures the renderer's honest shape for this common
    day-one case."""

    db = _init_db(tmp_path)
    _seed_plan(db, recs=[
        {"recommendation_id": f"rec_{AS_OF}_{USER}_recovery_01",
         "domain": "recovery", "action": "proceed_with_planned_session",
         "rationale": ["hrv_above_baseline", "sleep_debt=none"]},
        {"recommendation_id": f"rec_{AS_OF}_{USER}_sleep_01",
         "domain": "sleep", "action": "maintain_schedule",
         "rationale": ["sleep_score_good"]},
        {"recommendation_id": f"rec_{AS_OF}_{USER}_running_01",
         "domain": "running", "action": "proceed_with_planned_run",
         "confidence": "moderate",
         "uncertainty": ["cold_start_running_history_limited"],
         "rationale": ["planned_intervals_4x4", "green_recovery"]},
        {"recommendation_id": f"rec_{AS_OF}_{USER}_strength_01",
         "domain": "strength", "action": "defer_decision_insufficient_signal"},
        {"recommendation_id": f"rec_{AS_OF}_{USER}_stress_01",
         "domain": "stress", "action": "defer_decision_insufficient_signal"},
        {"recommendation_id": f"rec_{AS_OF}_{USER}_nutrition_01",
         "domain": "nutrition", "action": "defer_decision_insufficient_signal"},
    ])
    rc, out, _err = _run_today_plain(db)
    assert rc == 0
    _assert_snapshot(out, name="cold_start_day.txt")


# ---------------------------------------------------------------------------
# Scenario 5 — superseded plan (leaf renders, chain head does not)
# ---------------------------------------------------------------------------


def test_superseded_plan_renders_canonical_leaf_snapshot(tmp_path: Path) -> None:
    """After `hai synthesize --supersede`, `hai today` must resolve
    the canonical leaf. The fixture captures the v2 plan's prose;
    the v1 plan should never appear."""

    db = _init_db(tmp_path)
    v1_id = canonical_daily_plan_id(AS_OF, USER)
    v2_id = f"{v1_id}_v2"

    # v1: recovery proceed. (Morning plan.)
    _seed_plan(db, plan_id=v1_id, recs=[
        {"recommendation_id": f"rec_{AS_OF}_{USER}_recovery_01",
         "domain": "recovery", "action": "proceed_with_planned_session",
         "rationale": ["v1_morning_hrv_ok"]},
    ])
    # v2: recovery downgraded after a midday readiness intake.
    _seed_plan(db, plan_id=v2_id, recs=[
        {"recommendation_id": f"rec_{AS_OF}_{USER}_recovery_01_v2",
         "domain": "recovery", "action": "downgrade_session_to_mobility_only",
         "rationale": ["v2_user_logged_soreness"]},
    ])
    with sqlite3.connect(db) as conn:
        conn.execute(
            "UPDATE daily_plan SET superseded_by_plan_id = ?, "
            "superseded_at = '2026-04-24T12:00:00+00:00' "
            "WHERE daily_plan_id = ?",
            (v2_id, v1_id),
        )
        conn.commit()

    rc, out, _err = _run_today_plain(db)
    assert rc == 0
    # Belt-and-braces: ensure only v2 content appears in the snapshot.
    assert "v2_user_logged_soreness" in out
    assert "v1_morning_hrv_ok" not in out
    assert v2_id in out
    assert v1_id not in out.replace(v2_id, "")
    _assert_snapshot(out, name="superseded_plan.txt")
