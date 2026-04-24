"""E2E regression: the 2026-04-23 re-author journey.

This scenario is the canonical regression test for the v0.1.4 design
decisions ratified in `reporting/plans/v0_1_4/D1_re_author_semantics.md`
and drafted in D2 / D3 / D4.

It mirrors the session Dom ran on 2026-04-23:

    1. Pull evidence from intervals.icu for today (CSV fixture surrogate
       in this test environment — live intervals_icu is tested
       elsewhere).
    2. Post skill-authored proposals for all 6 domains via `hai propose`.
    3. Synthesize the v1 plan.
    4. User intakes readiness with a planned intervals session →
       `hai intake readiness` persists to `manual_readiness_raw` (D2).
    5. Re-pull so evidence incorporates the readiness signal.
    6. Re-author the affected proposals via `hai propose --replace` (D1).
    7. Synthesize with `--supersede` → v2 plan.
    8. `hai today` renders v2's content (D3).
    9. `hai review record` logs an outcome; if the rec was on v1 but v2
       exists, the outcome is re-linked to v2 (D1).

Today (before Workstream A lands), several of these steps fail because:

    - `hai intake readiness` does not persist (D2 fix pending).
    - `hai propose --replace` does not exist (D1 fix pending).
    - `hai today` does not exist (D3 fix pending).
    - Outcome re-link on supersede is absent (D1 fix pending).

Every assertion below is written against the *target* v0.1.4 behaviour.
Tests are marked xfail with the D-doc that tracks the fix. As each fix
lands, the xfail marker is removed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .conftest import E2EEnv


AS_OF = "2026-04-23"
USER_ID = "u_local_1"


# ---------------------------------------------------------------------------
# Scenario parts — reusable building blocks for each assertion
# ---------------------------------------------------------------------------


def _seed_recovery_evidence_csv(env: E2EEnv) -> None:
    """Seed the minimum recovery signal so the classifier can produce a
    meaningful state (HRV present, RHR present, sleep present).

    Uses direct SQL rather than a live pull because E2E tests must not
    depend on external services. The recovery classifier's inputs are
    well-typed; seeding them directly is equivalent to a successful pull
    from the test's perspective.
    """
    with __import__("sqlite3").connect(env.db_path) as conn:
        conn.execute(
            """
            INSERT INTO source_daily_garmin (
                as_of_date, user_id, export_batch_id, csv_row_index,
                source, ingest_actor, ingested_at,
                resting_hr, sleep_score_overall
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (AS_OF, USER_ID, "test_e2e_batch", 0, "garmin",
             "e2e_test_seed", "2026-04-23T08:00:00+00:00", 48.0, 91),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_intake_readiness_persists_and_feeds_pull(e2e_env: E2EEnv) -> None:
    """D2: ``hai intake readiness`` writes to ``manual_readiness_raw`` and
    ``hai pull`` automatically picks it up for the same-day date."""

    e2e_env.run_hai(
        "intake", "readiness",
        "--soreness", "low",
        "--energy", "high",
        "--planned-session-type", "intervals_4x4_z4_z2",
        "--active-goal", "improve_5k_and_sbd",
        "--as-of", AS_OF,
        "--user-id", USER_ID,
        "--base-dir", str(e2e_env.base_dir),
    )

    row = e2e_env.sql_one(
        "SELECT soreness, energy, planned_session_type FROM manual_readiness_raw "
        "WHERE user_id = ? AND as_of_date = ?",
        USER_ID, AS_OF,
    )
    assert row is not None, (
        "manual_readiness_raw row missing after hai intake readiness"
    )
    assert row[0] == "low"
    assert row[1] == "high"
    assert row[2] == "intervals_4x4_z4_z2"


def test_propose_replace_creates_new_revision_and_links_old_leaf(
    e2e_env: E2EEnv,
) -> None:
    """After Workstream A ships D1, re-authoring a proposal with
    `--replace` creates a new leaf at revision+1 and updates the old
    leaf's `superseded_by_proposal_id` in a single atomic transaction.
    """
    proposal_v1 = {
        "schema_version": "recovery_proposal.v1",
        "proposal_id": f"prop_{AS_OF}_{USER_ID}_recovery_01",
        "user_id": USER_ID,
        "for_date": AS_OF,
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "action_detail": None,
        "confidence": "moderate",
        "bounded": True,
        "rationale": ["hrv_above_baseline"],
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": "require_min_coverage", "decision": "allow", "note": "ok"},
        ],
    }
    v1_path = e2e_env.tmp_root / "prop_v1.json"
    v1_path.write_text(json.dumps(proposal_v1))
    e2e_env.run_hai(
        "propose", "--domain", "recovery",
        "--proposal-json", str(v1_path),
        "--base-dir", str(e2e_env.base_dir),
    )

    # Revise with new payload.
    proposal_v2 = {**proposal_v1,
                   "proposal_id": f"prop_{AS_OF}_{USER_ID}_recovery_02",
                   "rationale": ["hrv_above_baseline", "readiness_low_soreness"]}
    v2_path = e2e_env.tmp_root / "prop_v2.json"
    v2_path.write_text(json.dumps(proposal_v2))
    e2e_env.run_hai(
        "propose", "--domain", "recovery",
        "--proposal-json", str(v2_path),
        "--base-dir", str(e2e_env.base_dir),
        "--replace",
    )

    # After D1: both rows exist; v1 has superseded_by_proposal_id = v2.
    rows = e2e_env.sql(
        "SELECT proposal_id, revision, superseded_by_proposal_id "
        "FROM proposal_log WHERE for_date = ? AND user_id = ? AND domain = ? "
        "ORDER BY revision",
        AS_OF, USER_ID, "recovery",
    )
    assert len(rows) == 2
    assert rows[0][1] == 1
    assert rows[0][2] == proposal_v2["proposal_id"]  # v1 points forward to v2
    assert rows[1][1] == 2
    assert rows[1][2] is None  # v2 is leaf


def test_propose_without_replace_rejects_on_existing(e2e_env: E2EEnv) -> None:
    proposal = {
        "schema_version": "recovery_proposal.v1",
        "proposal_id": f"prop_{AS_OF}_{USER_ID}_recovery_01",
        "user_id": USER_ID,
        "for_date": AS_OF,
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "action_detail": None,
        "confidence": "moderate",
        "bounded": True,
        "rationale": ["baseline"],
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": "require_min_coverage", "decision": "allow", "note": "ok"},
        ],
    }
    path = e2e_env.tmp_root / "prop.json"
    path.write_text(json.dumps(proposal))
    e2e_env.run_hai(
        "propose", "--domain", "recovery",
        "--proposal-json", str(path),
        "--base-dir", str(e2e_env.base_dir),
    )

    # Re-propose without --replace must be rejected.
    from health_agent_infra.core import exit_codes
    result = e2e_env.run_hai(
        "propose", "--domain", "recovery",
        "--proposal-json", str(path),
        "--base-dir", str(e2e_env.base_dir),
        expect_exit=exit_codes.USER_INPUT,
    )
    assert "existing canonical proposal" in result["stderr"] or "--replace" in result["stderr"]


def test_propose_stdout_shape_matches_agent_contract(e2e_env: E2EEnv) -> None:
    """Codex r2 pushback: the agent contract documents
    ``for_date`` / ``user_id`` / ``revision`` / ``superseded_by_proposal_id``
    on `hai propose`'s stdout, but the pre-fix output only carried
    ``proposal_id`` / ``domain`` / ``writeback_path`` / ``idempotency_key``
    / ``performed_at``. Post-fix the output is the union of both — this
    test pins that contract.

    On a fresh-chain insert (no --replace), revision=1 and
    superseded_by_proposal_id=None.
    """

    proposal = {
        "schema_version": "recovery_proposal.v1",
        "proposal_id": f"prop_{AS_OF}_{USER_ID}_recovery_01",
        "user_id": USER_ID,
        "for_date": AS_OF,
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "action_detail": None,
        "confidence": "high",
        "bounded": True,
        "rationale": ["baseline"],
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": "require_min_coverage", "decision": "allow", "note": "ok"},
        ],
    }
    path = e2e_env.tmp_root / "prop.json"
    path.write_text(json.dumps(proposal))
    result = e2e_env.run_hai(
        "propose", "--domain", "recovery",
        "--proposal-json", str(path),
        "--base-dir", str(e2e_env.base_dir),
    )
    payload = result["stdout_json"]
    # Contract-claimed keys — these must be present.
    for key in (
        "proposal_id", "domain", "for_date", "user_id",
        "revision", "superseded_by_proposal_id",
    ):
        assert key in payload, f"hai propose output missing contract key: {key!r}"
    # Useful legacy keys — kept for backwards compatibility.
    for key in ("writeback_path", "idempotency_key", "performed_at"):
        assert key in payload, f"hai propose output missing audit key: {key!r}"
    # Fresh-chain values.
    assert payload["revision"] == 1
    assert payload["superseded_by_proposal_id"] is None
    assert payload["for_date"] == AS_OF
    assert payload["user_id"] == USER_ID


def test_propose_stdout_reflects_db_leaf_id_on_replace(e2e_env: E2EEnv) -> None:
    """Codex r3 P2 regression: on `--replace`, `project_proposal`
    auto-renames the new leaf to `prop_<date>_<user>_<domain>_<rev:02d>`
    regardless of the agent-supplied proposal_id. The stdout payload
    must echo the DB leaf's id + revision, not the pre-rename input.

    Pre-r3-fix: the helper only did a direct lookup by the input id,
    so stdout emitted the input id verbatim and `revision: null` (the
    renamed DB row didn't match the lookup). Post-r3-fix: canonical-
    leaf lookup by (for_date, user_id, domain) returns the real row.
    """

    agent_v1_id = "prop_agent_custom_v1"  # deliberately non-runtime shape
    proposal_v1 = {
        "schema_version": "recovery_proposal.v1",
        "proposal_id": agent_v1_id,
        "user_id": USER_ID,
        "for_date": AS_OF,
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "action_detail": None,
        "confidence": "high",
        "bounded": True,
        "rationale": ["initial"],
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": "require_min_coverage", "decision": "allow", "note": "ok"},
        ],
    }
    v1_path = e2e_env.tmp_root / "prop_v1.json"
    v1_path.write_text(json.dumps(proposal_v1))
    v1_result = e2e_env.run_hai(
        "propose", "--domain", "recovery",
        "--proposal-json", str(v1_path),
        "--base-dir", str(e2e_env.base_dir),
    )
    # Fresh chain: agent id preserved at rev=1.
    assert v1_result["stdout_json"]["proposal_id"] == agent_v1_id
    assert v1_result["stdout_json"]["revision"] == 1

    # Now --replace with a new rationale. Agent can supply any id; the
    # runtime renames to prop_<date>_<user>_recovery_02.
    proposal_v2 = {**proposal_v1,
                   "proposal_id": "prop_agent_custom_v2",
                   "rationale": ["revised per new evidence"]}
    v2_path = e2e_env.tmp_root / "prop_v2.json"
    v2_path.write_text(json.dumps(proposal_v2))
    v2_result = e2e_env.run_hai(
        "propose", "--domain", "recovery",
        "--proposal-json", str(v2_path),
        "--base-dir", str(e2e_env.base_dir),
        "--replace",
    )

    # The stdout must echo the DB leaf's id (runtime-renamed), not the
    # agent-supplied id. Revision must be the real revision (2), not null.
    expected_leaf_id = f"prop_{AS_OF}_{USER_ID}_recovery_02"
    assert v2_result["stdout_json"]["proposal_id"] == expected_leaf_id, (
        f"stdout proposal_id should be the DB-landed id {expected_leaf_id!r}, "
        f"got {v2_result['stdout_json']['proposal_id']!r}"
    )
    assert v2_result["stdout_json"]["revision"] == 2
    assert v2_result["stdout_json"]["superseded_by_proposal_id"] is None
    # idempotency_key should also align with the DB leaf id — agents that
    # dedupe by idempotency_key would otherwise mis-match across replace.
    assert v2_result["stdout_json"]["idempotency_key"] == expected_leaf_id

    # DB row confirms the rename.
    db_row = e2e_env.sql_one(
        "SELECT proposal_id, revision FROM proposal_log "
        "WHERE for_date = ? AND user_id = ? AND domain = ? "
        "AND superseded_by_proposal_id IS NULL",
        AS_OF, USER_ID, "recovery",
    )
    assert db_row[0] == expected_leaf_id
    assert db_row[1] == 2


def test_explain_for_date_returns_canonical_leaf(e2e_env: E2EEnv) -> None:
    """Per D1, `hai explain --for-date` default resolves the leaf of the
    supersede chain via ``superseded_by_plan_id IS NULL``, not the chain
    head.

    We seed the daily_plan table directly with a v1→v2→v3 chain. The
    explain command should default to v3 (the leaf), ``--plan-version
    first`` returns v1, ``--plan-version all`` returns all three.
    """
    import sqlite3 as _sq

    base_id = f"plan_{AS_OF}_{USER_ID}"
    v2_id = f"{base_id}_v2"
    v3_id = f"{base_id}_v3"

    def _insert_plan(
        plan_id: str,
        superseded_by: str | None,
    ) -> None:
        with _sq.connect(e2e_env.db_path) as conn:
            conn.execute(
                """
                INSERT INTO daily_plan (
                    daily_plan_id, user_id, for_date, synthesized_at,
                    recommendation_ids_json, proposal_ids_json,
                    x_rules_fired_json, synthesis_meta_json,
                    source, ingest_actor, validated_at, projected_at,
                    superseded_by_plan_id, superseded_at
                ) VALUES (?, ?, ?, ?, '[]', '[]', '[]', NULL,
                          'e2e_test', 'e2e_test', ?, ?, ?, ?)
                """,
                (
                    plan_id, USER_ID, AS_OF,
                    "2026-04-23T07:00:00+00:00",
                    "2026-04-23T07:00:00+00:00",
                    "2026-04-23T07:00:00+00:00",
                    superseded_by,
                    "2026-04-23T07:00:00+00:00" if superseded_by else None,
                ),
            )
            conn.commit()

    _insert_plan(base_id, superseded_by=v2_id)
    _insert_plan(v2_id, superseded_by=v3_id)
    _insert_plan(v3_id, superseded_by=None)  # leaf

    # Default: explain resolves the leaf (v3).
    result_default = e2e_env.run_hai(
        "explain", "--for-date", AS_OF, "--user-id", USER_ID,
    )
    assert result_default["stdout_json"]["plan"]["daily_plan_id"] == v3_id

    # --plan-version first: chain head.
    result_first = e2e_env.run_hai(
        "explain", "--for-date", AS_OF, "--user-id", USER_ID,
        "--plan-version", "first",
    )
    assert result_first["stdout_json"]["plan"]["daily_plan_id"] == base_id

    # --plan-version all: JSON array of all three bundles, chain-head → leaf.
    result_all = e2e_env.run_hai(
        "explain", "--for-date", AS_OF, "--user-id", USER_ID,
        "--plan-version", "all",
    )
    chain = result_all["stdout_json"]
    assert isinstance(chain, list)
    assert [b["plan"]["daily_plan_id"] for b in chain] == [base_id, v2_id, v3_id]


def test_hai_today_renders_canonical_plan(e2e_env: E2EEnv) -> None:
    """D3: ``hai today`` reads the canonical leaf and renders prose.

    End-to-end scenario: seed a minimum plan directly into the DB,
    confirm ``hai today`` produces output with the top-matter header
    and at least one domain section.
    """

    import json
    import sqlite3 as _sq

    plan_id = f"plan_{AS_OF}_{USER_ID}"
    rec_id = f"rec_{AS_OF}_{USER_ID}_recovery_01"
    payload = {
        "recommendation_id": rec_id,
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "confidence": "moderate",
        "rationale": ["hrv_looks_ok"],
        "uncertainty": [],
        "follow_up": {
            "review_question": "Did today's session feel appropriate?",
        },
    }
    with _sq.connect(e2e_env.db_path) as conn:
        conn.execute(
            """
            INSERT INTO daily_plan (
                daily_plan_id, user_id, for_date, synthesized_at,
                recommendation_ids_json, proposal_ids_json,
                x_rules_fired_json, synthesis_meta_json,
                source, ingest_actor, validated_at, projected_at
            ) VALUES (?, ?, ?, ?, ?, '[]', '[]', NULL,
                      'e2e_test', 'e2e_test', ?, ?)
            """,
            (
                plan_id, USER_ID, AS_OF,
                "2026-04-23T07:00:00+00:00",
                json.dumps([rec_id]),
                "2026-04-23T07:00:00+00:00",
                "2026-04-23T07:00:00+00:00",
            ),
        )
        conn.execute(
            """
            INSERT INTO recommendation_log (
                recommendation_id, user_id, for_date, issued_at,
                action, confidence, bounded, payload_json,
                source, ingest_actor, produced_at, validated_at,
                projected_at, domain, daily_plan_id
            ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, 'e2e_test', 'e2e_test',
                      ?, ?, ?, 'recovery', ?)
            """,
            (
                rec_id, USER_ID, AS_OF,
                "2026-04-23T07:00:00+00:00",
                payload["action"], payload["confidence"],
                json.dumps(payload),
                "2026-04-23T07:00:00+00:00",
                "2026-04-23T07:00:00+00:00",
                "2026-04-23T07:00:00+00:00",
                plan_id,
            ),
        )
        conn.commit()

    result = e2e_env.run_hai(
        "today", "--as-of", AS_OF, "--user-id", USER_ID,
        "--format", "plain",
    )
    assert f"Today, {AS_OF}" in result["stdout"]
    assert "Recovery" in result["stdout"]
    assert plan_id in result["stdout"]


def test_review_record_re_links_outcome_to_canonical_leaf(
    e2e_env: E2EEnv,
) -> None:
    """D1 step 9: ``hai review record`` against a superseded-plan rec
    re-links the outcome to the canonical leaf's matching-domain rec.

    Seeds a v1 → v2 chain (both with a recovery rec + review_event),
    invokes ``hai review record`` with outcome-json naming the v1 rec,
    and asserts the landed outcome (JSONL + DB) targets v2's rec with
    the re-link audit fields populated.
    """
    import sqlite3 as _sq

    v1_id = f"plan_{AS_OF}_{USER_ID}"
    v2_id = f"{v1_id}_v2"
    v1_rec = f"rec_{AS_OF}_{USER_ID}_recovery_01"
    v2_rec = f"rec_{AS_OF}_{USER_ID}_recovery_01_v2"
    review_event_id = f"rev_{AS_OF}_{USER_ID}_recovery"

    def _insert_plan_with_recovery_rec(
        plan_id: str, rec_id: str, superseded_by: str | None,
    ) -> None:
        with _sq.connect(e2e_env.db_path) as conn:
            conn.execute(
                """
                INSERT INTO daily_plan (
                    daily_plan_id, user_id, for_date, synthesized_at,
                    recommendation_ids_json, proposal_ids_json,
                    x_rules_fired_json, synthesis_meta_json,
                    source, ingest_actor, validated_at, projected_at,
                    superseded_by_plan_id, superseded_at
                ) VALUES (?, ?, ?, ?, ?, '[]', '[]', NULL,
                          'e2e_test', 'e2e_test', ?, ?, ?, ?)
                """,
                (
                    plan_id, USER_ID, AS_OF,
                    "2026-04-23T07:00:00+00:00",
                    json.dumps([rec_id]),
                    "2026-04-23T07:00:00+00:00",
                    "2026-04-23T07:00:00+00:00",
                    superseded_by,
                    "2026-04-23T07:00:00+00:00" if superseded_by else None,
                ),
            )
            payload = {
                "recommendation_id": rec_id,
                "domain": "recovery",
                "action": "proceed_with_planned_session",
                "confidence": "moderate",
                "rationale": ["ok"],
                "uncertainty": [],
                "follow_up": {"review_question": "?"},
            }
            conn.execute(
                """
                INSERT INTO recommendation_log (
                    recommendation_id, user_id, for_date, issued_at,
                    action, confidence, bounded, payload_json,
                    source, ingest_actor, produced_at, validated_at,
                    projected_at, domain, daily_plan_id
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, 'e2e_test', 'e2e_test',
                          ?, ?, ?, 'recovery', ?)
                """,
                (
                    rec_id, USER_ID, AS_OF,
                    "2026-04-23T07:00:00+00:00",
                    payload["action"], payload["confidence"],
                    json.dumps(payload),
                    "2026-04-23T07:00:00+00:00",
                    "2026-04-23T07:00:00+00:00",
                    "2026-04-23T07:00:00+00:00",
                    plan_id,
                ),
            )
            conn.commit()

    _insert_plan_with_recovery_rec(v1_id, v1_rec, superseded_by=v2_id)
    _insert_plan_with_recovery_rec(v2_id, v2_rec, superseded_by=None)

    # Review_event points at the v1 rec (the question was scheduled when
    # v1 was the leaf — this is the situation D1 §review record is
    # designed to handle).
    with _sq.connect(e2e_env.db_path) as conn:
        conn.execute(
            """
            INSERT INTO review_event (
                review_event_id, recommendation_id, user_id,
                review_at, review_question, domain, projected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_event_id, v1_rec, USER_ID,
                "2026-04-24T07:00:00+00:00",
                "How did yesterday land?", "recovery",
                "2026-04-24T07:00:00+00:00",
            ),
        )
        conn.commit()

    outcome_path = e2e_env.tmp_root / "outcome.json"
    outcome_path.write_text(json.dumps({
        "review_event_id": review_event_id,
        "recommendation_id": v1_rec,
        "user_id": USER_ID,
        "domain": "recovery",
        "followed_recommendation": True,
        "self_reported_improvement": True,
        "free_text": None,
    }))

    result = e2e_env.run_hai(
        "review", "record",
        "--outcome-json", str(outcome_path),
        "--base-dir", str(e2e_env.base_dir),
    )
    assert f"re-linked from {v1_rec} to {v2_rec}" in result["stderr"]

    # JSONL carries the leaf rec id + re-link audit.
    outcomes_path = e2e_env.base_dir / "review_outcomes.jsonl"
    outcome = json.loads(outcomes_path.read_text(encoding="utf-8").splitlines()[0])
    assert outcome["recommendation_id"] == v2_rec
    assert outcome["re_linked_from_recommendation_id"] == v1_rec

    # DB row has the re-link columns populated.
    row = e2e_env.sql_one(
        "SELECT recommendation_id, re_linked_from_recommendation_id, "
        "re_link_note FROM review_outcome WHERE review_event_id = ?",
        review_event_id,
    )
    assert row is not None
    assert row[0] == v2_rec
    assert row[1] == v1_rec
    assert row[2] is not None


@pytest.mark.xfail(
    reason="D4 pending: running cold-start relaxation not implemented. "
    "Tracked in reporting/plans/v0_1_4/D4_cold_start.md."
)
def test_running_cold_start_produces_non_defer_with_green_recovery(
    e2e_env: E2EEnv,
) -> None:
    """After Workstream D ships cold-start mode, a first-run user with
    green recovery + planned_session_type in readiness gets a non-defer
    running recommendation (capped at moderate confidence, with the
    `cold_start_running_history_limited` uncertainty tag).
    """
    pytest.skip("Implementation deferred until Workstream D's cold-start mode lands.")
