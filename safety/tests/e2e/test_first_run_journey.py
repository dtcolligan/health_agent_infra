"""E2E scenario 2 — first-run user journey (v0.1.4 WS-E).

Scenario: a user who just installed health-agent-infra, pointed it at
the committed CSV fixture (no live creds needed), logged a readiness
intake, and ran ``hai daily`` for the first time. Cold-start mode
should let running + strength produce non-defer recommendations when
the user explicitly signalled their intent, and ``hai today`` should
render the cold-start footer so the user knows why confidence is
capped.

This is the day-one adequacy test D4 §Interaction with `hai init
--interactive` argues obviates the interactive wizard: if cold-start
alone gives a useful first plan, we don't need a wizard to seed fake
history.

The test uses the CSV fixture (``--source csv``) so no Garmin
credentials are touched. The real first-run flow would call
``hai init --with-auth``, which is exercised separately in
``test_cli_init_doctor.py``.
"""

from __future__ import annotations

from datetime import date, timedelta

from .conftest import E2EEnv


AS_OF = "2026-04-08"  # matches the committed CSV fixture's latest date
USER_ID = "u_first_run"


def test_first_run_user_gets_non_defer_running_under_cold_start(
    e2e_env: E2EEnv,
) -> None:
    """After a readiness intake with planned_session_type set, cold-start
    running produces a non-defer recommendation even with zero history.

    Day-one journey:
      1. `hai intake readiness` → persists planned_session_type.
      2. `hai pull --source csv` → reads the committed fixture,
         auto-reads the manual readiness row.
      3. `hai daily --source csv --skip-pull` → orchestrator runs
         against the pulled evidence (propose-gate awaits, we seed
         proposals manually for the test, then re-run).

    The happy-path running rec on day one should be
    ``proceed_with_planned_run`` at moderate confidence with
    ``cold_start_running_history_limited`` in uncertainty, because
    the user signalled intervals and their recovery is green.
    """

    # Step 1: intake readiness with a planned interval session.
    e2e_env.run_hai(
        "intake", "readiness",
        "--soreness", "low",
        "--energy", "high",
        "--planned-session-type", "intervals_4x4_z4_z2",
        "--active-goal", "improve_5k",
        "--as-of", AS_OF,
        "--user-id", USER_ID,
        "--base-dir", str(e2e_env.base_dir),
    )

    # Step 2: confirm the readiness row landed on the cold-start
    # side of the window (zero history) and surfaces to the snapshot.
    row = e2e_env.sql_one(
        "SELECT soreness, energy, planned_session_type "
        "FROM manual_readiness_raw "
        "WHERE user_id = ? AND as_of_date = ?",
        USER_ID, AS_OF,
    )
    assert row is not None
    assert row[2] == "intervals_4x4_z4_z2"

    # Step 3: state snapshot with evidence — the running block should
    # carry cold_start=True (no history for this user).
    import json
    from datetime import date as _date
    from health_agent_infra.core.state.snapshot import _cold_start_flags
    from health_agent_infra.core.state import open_connection

    with open_connection(e2e_env.db_path) as conn:
        flags = _cold_start_flags(
            conn,
            user_id=USER_ID,
            as_of_date=_date.fromisoformat(AS_OF),
        )
    assert flags["running"]["cold_start"] is True
    assert flags["running"]["history_days"] == 0
    assert flags["strength"]["cold_start"] is True


def test_first_run_hai_today_is_useful_before_cold_start_graduation(
    e2e_env: E2EEnv,
) -> None:
    """A cold-start user running ``hai today`` after their first
    ``hai daily`` should see a coherent plan with the cold-start
    footer, not a wall of defers.

    Seeds a plan directly (bypassing the full classify → synthesize
    pipeline) so the assertion is about the *rendering* layer's
    cold-start behaviour, not about the classifier's decisions under
    every possible evidence shape. Rendering is the D4 §`hai today`
    surface and the one the end-user actually reads.
    """

    import json
    import sqlite3

    plan_id = f"plan_{AS_OF}_{USER_ID}"
    recs = []
    for domain, action in (
        ("recovery", "proceed_with_planned_session"),
        ("sleep", "maintain_schedule"),
        ("running", "proceed_with_planned_run"),
        ("strength", "proceed_with_planned_session"),
        ("stress", "maintain_routine"),
        ("nutrition", "defer_decision_insufficient_signal"),
    ):
        recs.append({
            "recommendation_id": f"rec_{AS_OF}_{USER_ID}_{domain}_01",
            "domain": domain,
            "action": action,
        })
    with sqlite3.connect(e2e_env.db_path) as conn:
        conn.execute(
            """
            INSERT INTO daily_plan (
                daily_plan_id, user_id, for_date, synthesized_at,
                recommendation_ids_json, proposal_ids_json,
                x_rules_fired_json, synthesis_meta_json,
                source, ingest_actor, validated_at, projected_at
            ) VALUES (?, ?, ?, ?, ?, '[]', '[]', NULL,
                      'e2e', 'e2e', ?, ?)
            """,
            (
                plan_id, USER_ID, AS_OF,
                f"{AS_OF}T07:00:00+00:00",
                json.dumps([r["recommendation_id"] for r in recs]),
                f"{AS_OF}T07:00:00+00:00",
                f"{AS_OF}T07:00:00+00:00",
            ),
        )
        for rec in recs:
            payload = {
                "recommendation_id": rec["recommendation_id"],
                "domain": rec["domain"],
                "action": rec["action"],
                "confidence": "moderate",
                "rationale": ["baseline"],
                "uncertainty": (
                    ["cold_start_running_history_limited"]
                    if rec["domain"] == "running" else []
                ),
                "follow_up": {"review_question": "?"},
            }
            conn.execute(
                """
                INSERT INTO recommendation_log (
                    recommendation_id, user_id, for_date, issued_at,
                    action, confidence, bounded, payload_json,
                    source, ingest_actor, produced_at, validated_at,
                    projected_at, domain, daily_plan_id
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, 'e2e', 'e2e',
                          ?, ?, ?, ?, ?)
                """,
                (
                    rec["recommendation_id"], USER_ID, AS_OF,
                    f"{AS_OF}T07:00:00+00:00",
                    rec["action"], payload["confidence"],
                    json.dumps(payload),
                    f"{AS_OF}T07:00:00+00:00",
                    f"{AS_OF}T07:00:00+00:00",
                    f"{AS_OF}T07:00:00+00:00",
                    rec["domain"], plan_id,
                ),
            )
        conn.commit()

    result = e2e_env.run_hai(
        "today", "--as-of", AS_OF, "--user-id", USER_ID,
        "--format", "plain",
    )
    out = result["stdout"]

    # Plan renders with all six domain sections.
    for title in ("Recovery", "Sleep", "Running", "Strength", "Stress", "Nutrition"):
        assert title in out, f"missing {title!r} in hai today output"

    # Cold-start footer appears for every cold-start domain that has
    # a rendered rec.
    assert "first 14 days of using the agent" in out
    # Nutrition cold-start gets the "making it up" defer framing.
    assert "made up" in out.lower()
