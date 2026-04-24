"""``hai today`` — user-facing prose renderer over the canonical plan.

D3 test coverage #1–#6. Each test seeds a DB with a plan of a known
shape and asserts against the rendered output. Not full snapshot files
(those land in ``safety/tests/snapshot/`` under Workstream E) — these
tests assert on substrings / structural invariants so the test file is
self-contained.
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
from health_agent_infra.core import exit_codes
from health_agent_infra.core.schemas import canonical_daily_plan_id
from health_agent_infra.core.state import initialize_database, open_connection


USER = "u_today"
AS_OF = date(2026, 4, 23)


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
    """Seed a plan row + recommendation_log rows directly.

    Bypasses the full synthesis pipeline so tests can shape the output
    exactly (e.g. the mixed-day 2-presc + 4-defer scenario). The plan
    ID defaults to the canonical one for (AS_OF, USER).
    """

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
            ) VALUES (?, ?, ?, ?, ?, '[]', '[]', NULL,
                      'test', 'test', ?, ?)
            """,
            (
                plan_id, USER, AS_OF.isoformat(),
                "2026-04-23T07:00:00+00:00",
                json.dumps(rec_ids),
                "2026-04-23T07:00:00+00:00",
                "2026-04-23T07:00:00+00:00",
            ),
        )
        for rec in recs:
            conn.execute(
                """
                INSERT INTO recommendation_log (
                    recommendation_id, user_id, for_date, issued_at,
                    action, confidence, bounded, payload_json,
                    source, ingest_actor, produced_at, validated_at,
                    projected_at, domain, daily_plan_id
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, 'test', 'test',
                          ?, ?, ?, ?, ?)
                """,
                (
                    rec["recommendation_id"], USER, AS_OF.isoformat(),
                    "2026-04-23T07:00:00+00:00",
                    rec["action"], rec["confidence"],
                    json.dumps(rec["payload"]),
                    "2026-04-23T07:00:00+00:00",
                    "2026-04-23T07:00:00+00:00",
                    "2026-04-23T07:00:00+00:00",
                    rec["domain"], plan_id,
                ),
            )
        conn.commit()
    return plan_id


def _mk_rec(domain: str, action: str, **kw):
    confidence = kw.pop("confidence", "moderate")
    rationale = kw.pop("rationale", [f"{domain}_looked_ok"])
    uncertainty = kw.pop("uncertainty", [])
    review_q = kw.pop(
        "review_question",
        f"How did today's {domain} plan land?",
    )
    return {
        "recommendation_id": f"rec_{AS_OF.isoformat()}_{USER}_{domain}_01",
        "domain": domain,
        "action": action,
        "confidence": confidence,
        "payload": {
            "recommendation_id": f"rec_{AS_OF.isoformat()}_{USER}_{domain}_01",
            "domain": domain,
            "action": action,
            "confidence": confidence,
            "rationale": rationale,
            "uncertainty": uncertainty,
            "follow_up": {"review_question": review_q},
        },
    }


def _run_today(db: Path, *extra: str) -> tuple[int, str, str]:
    argv = [
        "today",
        "--as-of", AS_OF.isoformat(),
        "--user-id", USER,
        "--db-path", str(db),
        *extra,
    ]
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        rc = cli_main(argv)
    return rc, stdout_buf.getvalue(), stderr_buf.getvalue()


# ---------------------------------------------------------------------------
# Test 1 — green day: all 6 domains with real prescriptions
# ---------------------------------------------------------------------------


def test_hai_today_green_day_renders_all_six_domains_in_markdown(tmp_path: Path):
    db = _init_db(tmp_path)
    _seed_plan(db, recs=[
        _mk_rec("recovery", "proceed_with_planned_session"),
        _mk_rec("sleep", "maintain_schedule"),
        _mk_rec("running", "proceed_with_planned_run"),
        _mk_rec("strength", "proceed_with_planned_session"),
        _mk_rec("stress", "maintain_routine"),
        _mk_rec("nutrition", "maintain_targets"),
    ])

    rc, out, err = _run_today(db, "--format", "markdown")
    assert rc == 0, err
    # Top matter + date.
    assert "# Today, 2026-04-23 — your plan" in out
    # All 6 domain headers rendered, in canonical order.
    domain_positions = []
    for domain in ("Recovery", "Sleep", "Running", "Strength", "Stress", "Nutrition"):
        assert domain in out, f"missing domain header: {domain}"
        domain_positions.append(out.index(domain))
    assert domain_positions == sorted(domain_positions), (
        "domain sections rendered out of canonical order"
    )
    # All prescriptions carry the proceed-class emoji.
    assert out.count("🟢") == 6
    # Footer with plan id.
    assert f"plan_{AS_OF.isoformat()}_{USER}" in out
    # Idempotent: a second run produces byte-identical output.
    rc2, out2, _ = _run_today(db, "--format", "markdown")
    assert rc2 == 0
    assert out == out2


# ---------------------------------------------------------------------------
# Test 2 — mixed day: 2 prescriptions + 4 defers
# ---------------------------------------------------------------------------


def test_hai_today_mixed_day_renders_prescriptions_and_defers_distinctly(
    tmp_path: Path,
):
    db = _init_db(tmp_path)
    _seed_plan(db, recs=[
        _mk_rec("recovery", "proceed_with_planned_session"),
        _mk_rec("sleep", "defer_decision_insufficient_signal"),
        _mk_rec("running", "defer_decision_insufficient_signal"),
        _mk_rec("strength", "proceed_with_planned_session"),
        _mk_rec("stress", "defer_decision_insufficient_signal"),
        _mk_rec("nutrition", "defer_decision_insufficient_signal"),
    ])

    rc, out, err = _run_today(db, "--format", "markdown")
    assert rc == 0, err
    # Summary reports the split.
    assert "2 prescriptions" in out
    assert "4 defers" in out
    # Defer emoji present for the 4 defers.
    assert out.count("⚪") == 4
    # Defers get "what would unblock me" prose — e.g. for nutrition, the
    # hint mentions `hai intake nutrition` as the unblock path.
    assert "hai intake nutrition" in out


# ---------------------------------------------------------------------------
# Test 3 — no-plan day: exits USER_INPUT with a readable stderr hint
# ---------------------------------------------------------------------------


def test_hai_today_on_date_with_no_plan_exits_user_input(tmp_path: Path):
    db = _init_db(tmp_path)
    # No plan seeded at all.
    rc, out, err = _run_today(db, "--format", "plain")
    assert rc == exit_codes.USER_INPUT
    assert out == ""
    assert "No plan for 2026-04-23" in err
    assert "hai daily" in err


# ---------------------------------------------------------------------------
# Test 4 — --domain filter returns exactly one section
# ---------------------------------------------------------------------------


def test_hai_today_domain_filter_narrows_to_one_section(tmp_path: Path):
    db = _init_db(tmp_path)
    _seed_plan(db, recs=[
        _mk_rec("recovery", "proceed_with_planned_session"),
        _mk_rec("running", "proceed_with_planned_run"),
        _mk_rec("nutrition", "maintain_targets"),
    ])

    rc, out, err = _run_today(
        db, "--format", "markdown", "--domain", "recovery",
    )
    assert rc == 0, err
    # Recovery section present.
    assert "Recovery" in out
    # Running/nutrition sections absent — filter narrowed the output.
    assert "Running" not in out
    assert "Nutrition" not in out


# ---------------------------------------------------------------------------
# Test 5 — --format json emits structured shape
# ---------------------------------------------------------------------------


def test_hai_today_format_json_emits_structured_shape(tmp_path: Path):
    db = _init_db(tmp_path)
    _seed_plan(db, recs=[
        _mk_rec("recovery", "proceed_with_planned_session"),
        _mk_rec("nutrition", "maintain_targets"),
    ])

    rc, out, err = _run_today(db, "--format", "json")
    assert rc == 0, err
    payload = json.loads(out)
    assert payload["daily_plan_id"] == canonical_daily_plan_id(AS_OF, USER)
    assert payload["for_date"] == "2026-04-23"
    assert payload["user_id"] == USER
    # One section per seeded rec.
    sections = payload["sections"]
    domains = {s["domain"] for s in sections}
    assert domains == {"recovery", "nutrition"}
    # Each section carries action_class + action_summary + rationale.
    for s in sections:
        assert s["action_class"] in ("proceed", "caution", "rest", "defer")
        assert s["action_summary"]
        assert "rationale" in s
    # Summary carries prescription + defer counts.
    assert payload["summary"] == {"prescriptions": 2, "defers": 0}


# ---------------------------------------------------------------------------
# Test 6 — superseded plan: canonical leaf (v2) renders, not chain head (v1)
# ---------------------------------------------------------------------------


def test_hai_today_on_superseded_plan_renders_canonical_leaf(tmp_path: Path):
    """Per D1, ``hai today`` must resolve the canonical leaf for the
    date when the chain has been superseded — that's the plan the user
    actually cares about. Chain-head renders would regress to the
    2026-04-23 bug where ``hai explain`` showed the morning's plan even
    though the afternoon had written a new leaf.
    """

    db = _init_db(tmp_path)
    v1_id = canonical_daily_plan_id(AS_OF, USER)
    v2_id = f"{v1_id}_v2"

    # Seed v1 with a "proceed" recovery rec, then v2 with a softened one.
    _seed_plan(db, plan_id=v1_id, recs=[
        _mk_rec("recovery", "proceed_with_planned_session",
                rationale=["v1_hrv_ok"]),
    ])
    # v2 has a different rec id to avoid PK collision in recommendation_log.
    v2_recs = [_mk_rec("recovery", "downgrade_session_to_mobility_only",
                        rationale=["v2_user_logged_soreness"])]
    v2_recs[0]["recommendation_id"] = (
        f"rec_{AS_OF.isoformat()}_{USER}_recovery_01_v2"
    )
    v2_recs[0]["payload"]["recommendation_id"] = v2_recs[0]["recommendation_id"]
    _seed_plan(db, plan_id=v2_id, recs=v2_recs)

    # Link v1 → v2 via the forward pointer.
    with sqlite3.connect(db) as conn:
        conn.execute(
            "UPDATE daily_plan SET superseded_by_plan_id = ?, "
            "superseded_at = ? WHERE daily_plan_id = ?",
            (v2_id, "2026-04-23T12:00:00+00:00", v1_id),
        )
        conn.commit()

    rc, out, err = _run_today(db, "--format", "markdown")
    assert rc == 0, err
    # Leaf's action surfaces; head's doesn't.
    assert "mobility" in out.lower() or "Mobility" in out
    assert "v2_user_logged_soreness" in out
    # Footer stamps the leaf id, not the chain head.
    assert v2_id in out
    assert v1_id not in out.replace(v2_id, "")
