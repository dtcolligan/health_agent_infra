"""
Synthesis eval pack runner.

Exercises each scenario JSON against the current synthesis runtime and
captures the observable behaviour. Manual scoring against rubric.md is
recorded separately in findings.md — this runner only produces the raw
evidence.

IMPORTANT: this runner tests the RUNTIME layer (core/synthesis.py +
core/synthesis_policy.py + core/writeback/proposal.py). It does NOT
invoke the daily-plan-synthesis skill. The skill is an agent artifact
that requires running Claude Code as a subprocess, which is out of
scope for an automated eval.

The eval's rubric scores what the runtime does with the bundle; skill
narration quality (rationale prose, uncertainty sorting, joint
narration) is not exercised here.
"""

from __future__ import annotations

import json
import sys
import traceback
from datetime import date
from pathlib import Path

from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_proposal,
)
from health_agent_infra.core.synthesis import run_synthesis, SynthesisError
from health_agent_infra.core.writeback.proposal import (
    PROPOSAL_SCHEMA_VERSIONS,
    ProposalValidationError,
    validate_proposal_dict,
)


HERE = Path(__file__).parent
SCENARIOS_DIR = HERE / "scenarios"
OUTPUTS_DIR = HERE / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)


USER_ID = "u_eval_pack"


def _to_v1_proposal(payload: dict) -> dict:
    """Normalise scenario proposal JSON to the v1 proposal writeback shape.

    Scenarios author proposals with the plan's full shape (schema_version
    '1.0' plus optional fields); the v1 writeback demands domain-specific
    schema_version strings and requires policy_decisions. Fill the gaps
    so valid scenario proposals exercise the runtime correctly.
    """

    domain = payload["domain"]
    expected_schema = PROPOSAL_SCHEMA_VERSIONS.get(domain)
    out = dict(payload)
    if expected_schema and out.get("schema_version") in ("1.0", None):
        out["schema_version"] = expected_schema
    out.setdefault("action_detail", None)
    out.setdefault("rationale", [])
    out.setdefault("uncertainty", [])
    out.setdefault("user_id", USER_ID)
    out.setdefault(
        "policy_decisions",
        [{"rule_id": "r1_coverage", "decision": "allow", "note": "eval_pack"}],
    )
    # Defect markers must NOT be passed through to the writeback layer.
    out.pop("_defect", None)
    return out


def _synthesis_snapshot(scenario_snapshot: dict) -> dict:
    """Project a scenario's rich per-domain snapshot into the shape
    synthesis_policy expects.

    Scenarios author per-domain blocks (recovery, running, stress,
    nutrition, sleep, strength). The current runtime only reads from
    recovery.{classified_state,today} — see synthesis_policy._sleep_debt_band,
    _acwr_ratio, _body_battery, _stress_band. We lift the scenario's
    stress numbers onto recovery.today.all_day_stress so X7 can fire,
    and we carry ACWR and body_battery in the same place.
    """

    rec = scenario_snapshot.get("recovery") or {}
    stress = scenario_snapshot.get("stress") or {}

    stress_score = None
    if stress.get("evidence"):
        stress_score = stress["evidence"].get("garmin_all_day_stress")

    today = {
        "acwr_ratio": (rec.get("raw_summary") or {}).get("acwr_ratio"),
        "body_battery_end_of_day": (stress.get("raw_summary") or {}).get(
            "body_battery_end_of_day"
        ),
        "all_day_stress": stress_score,
    }
    classified = rec.get("classified_state") or {}
    return {
        "recovery": {
            "classified_state": classified,
            "today": today,
        },
        "running": {},
    }


def run_scenario_s1(tmpdir: Path) -> dict:
    scenario = json.loads((SCENARIOS_DIR / "s1_orphan_firing.json").read_text())
    db_path = tmpdir / "s1.db"
    initialize_database(db_path)

    proposals = [_to_v1_proposal(p) for p in scenario["proposals"]]
    conn = open_connection(db_path)
    try:
        for p in proposals:
            project_proposal(conn, p)
    finally:
        conn.close()

    snapshot = _synthesis_snapshot(scenario["snapshot"])

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=date.fromisoformat(scenario["as_of_date"]),
            user_id=USER_ID,
            snapshot=snapshot,
        )
    finally:
        conn.close()

    # Read what landed in the DB.
    conn = open_connection(db_path)
    try:
        firings = [
            dict(row) for row in conn.execute(
                "SELECT x_rule_id, tier, affected_domain, mutation_json "
                "FROM x_rule_firing WHERE daily_plan_id = ?",
                (result.daily_plan_id,),
            ).fetchall()
        ]
        recs = [
            dict(row) for row in conn.execute(
                "SELECT recommendation_id, domain, action, payload_json "
                "FROM recommendation_log "
                "WHERE recommendation_id IN "
                "(" + ",".join("?" * len(result.recommendation_ids)) + ")",
                tuple(result.recommendation_ids),
            ).fetchall()
        ]
    finally:
        conn.close()

    return {
        "scenario_id": "s1_orphan_firing",
        "result": result.to_dict(),
        "persisted_firings": firings,
        "persisted_recommendations": [
            {
                "recommendation_id": r["recommendation_id"],
                "domain": r["domain"],
                "action": r["action"],
                "confidence": json.loads(r["payload_json"])["confidence"],
            }
            for r in recs
        ],
    }


def run_scenario_s2(tmpdir: Path) -> dict:
    scenario = json.loads((SCENARIOS_DIR / "s2_cap_adjust_stacking.json").read_text())
    db_path = tmpdir / "s2.db"
    initialize_database(db_path)

    # v1 only supports recovery + running proposals. Filter the scenario's
    # 4-domain proposal list down to the runtime-supported subset and
    # record which ones were skipped.
    submitted, skipped = [], []
    for p in scenario["proposals"]:
        if p["domain"] in ("recovery", "running"):
            submitted.append(_to_v1_proposal(p))
        else:
            skipped.append({"proposal_id": p["proposal_id"], "domain": p["domain"]})

    # Adjust recovery proposal to the v1 action enum.
    for p in submitted:
        if p["domain"] == "recovery" and p["action"] == "training_day_hard":
            p["action"] = "proceed_with_planned_session"

    conn = open_connection(db_path)
    try:
        for p in submitted:
            project_proposal(conn, p)
    finally:
        conn.close()

    snapshot = _synthesis_snapshot(scenario["snapshot"])

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=date.fromisoformat(scenario["as_of_date"]),
            user_id=USER_ID,
            snapshot=snapshot,
        )
    finally:
        conn.close()

    conn = open_connection(db_path)
    try:
        firings = [
            dict(row) for row in conn.execute(
                "SELECT x_rule_id, tier, affected_domain "
                "FROM x_rule_firing WHERE daily_plan_id = ?",
                (result.daily_plan_id,),
            ).fetchall()
        ]
        recs = [
            dict(row) for row in conn.execute(
                "SELECT recommendation_id, domain, action, payload_json "
                "FROM recommendation_log "
                "WHERE recommendation_id IN "
                "(" + ",".join("?" * len(result.recommendation_ids)) + ")",
                tuple(result.recommendation_ids),
            ).fetchall()
        ]
    finally:
        conn.close()

    return {
        "scenario_id": "s2_cap_adjust_stacking",
        "result": result.to_dict(),
        "runtime_scope_gap": {
            "reason": "v1 SUPPORTED_DOMAINS = {recovery, running}; stress + nutrition proposals cannot be submitted. X9 (Phase B post_adjust on nutrition) cannot fire — scenario's adjust-stacking tail is untestable against v1.",
            "skipped_proposals": skipped,
        },
        "persisted_firings": firings,
        "persisted_recommendations": [
            {
                "recommendation_id": r["recommendation_id"],
                "domain": r["domain"],
                "action": r["action"],
                "confidence": json.loads(r["payload_json"])["confidence"],
            }
            for r in recs
        ],
    }


def run_scenario_s3(tmpdir: Path) -> dict:
    scenario = json.loads((SCENARIOS_DIR / "s3_mixed_missingness.json").read_text())
    db_path = tmpdir / "s3.db"
    initialize_database(db_path)

    submitted, skipped = [], []
    for p in scenario["proposals"]:
        if p["domain"] in ("recovery", "running"):
            submitted.append(_to_v1_proposal(p))
        else:
            skipped.append({"proposal_id": p["proposal_id"], "domain": p["domain"]})

    # Map recovery's scenario-level actions into v1 enum.
    for p in submitted:
        if p["domain"] == "recovery" and p["action"] == "training_day_moderate":
            p["action"] = "proceed_with_planned_session"

    conn = open_connection(db_path)
    try:
        for p in submitted:
            project_proposal(conn, p)
    finally:
        conn.close()

    snapshot = _synthesis_snapshot(scenario["snapshot"])

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=date.fromisoformat(scenario["as_of_date"]),
            user_id=USER_ID,
            snapshot=snapshot,
        )
    finally:
        conn.close()

    conn = open_connection(db_path)
    try:
        firings = [
            dict(row) for row in conn.execute(
                "SELECT x_rule_id, tier, affected_domain "
                "FROM x_rule_firing WHERE daily_plan_id = ?",
                (result.daily_plan_id,),
            ).fetchall()
        ]
        recs = [
            dict(row) for row in conn.execute(
                "SELECT recommendation_id, domain, action, payload_json "
                "FROM recommendation_log "
                "WHERE recommendation_id IN "
                "(" + ",".join("?" * len(result.recommendation_ids)) + ")",
                tuple(result.recommendation_ids),
            ).fetchall()
        ]
    finally:
        conn.close()

    return {
        "scenario_id": "s3_mixed_missingness",
        "result": result.to_dict(),
        "runtime_scope_gap": {
            "reason": "v1 supports only recovery + running. The scenario's sleep (unavailable_at_source) and strength (pending_user_input) proposals cannot be submitted. Missingness propagation at the skill-narration layer cannot be fully exercised without those domains.",
            "skipped_proposals": skipped,
        },
        "persisted_firings": firings,
        "persisted_recommendations": [
            {
                "recommendation_id": r["recommendation_id"],
                "domain": r["domain"],
                "action": r["action"],
                "confidence": json.loads(r["payload_json"])["confidence"],
            }
            for r in recs
        ],
    }


def run_scenario_s4(tmpdir: Path) -> dict:
    scenario = json.loads((SCENARIOS_DIR / "s4_stale_proposal.json").read_text())
    db_path = tmpdir / "s4.db"
    initialize_database(db_path)

    validation_results = []
    for p in scenario["proposals"]:
        raw = dict(p)
        defect = raw.pop("_defect", None)
        # Pre-fill the v1-optional fields so the ONLY rejection reason is
        # the intended defect. Otherwise a missing required field would
        # short-circuit before the scenario's signal fires.
        raw.setdefault("action_detail", None)
        raw.setdefault("uncertainty", [])
        raw.setdefault("user_id", USER_ID)
        raw.setdefault(
            "policy_decisions",
            [{"rule_id": "r1_coverage", "decision": "allow", "note": "eval_pack"}],
        )
        # For the action-enum defect proposal, correct schema_version so
        # the validator reaches the action-enum check instead of failing
        # on schema_version first. For the stale-schema-version defect,
        # leave schema_version as scenario-authored.
        domain = raw["domain"]
        if defect and "enum" in defect.lower():
            raw["schema_version"] = PROPOSAL_SCHEMA_VERSIONS[domain]
        try:
            validate_proposal_dict(raw)
            verdict = {
                "proposal_id": p["proposal_id"],
                "intended_defect": defect,
                "accepted": True,
                "error_invariant": None,
                "error_message": None,
            }
        except ProposalValidationError as exc:
            verdict = {
                "proposal_id": p["proposal_id"],
                "intended_defect": defect,
                "accepted": False,
                "error_invariant": exc.invariant,
                "error_message": str(exc),
            }
        validation_results.append(verdict)

    # Assert no rows landed in proposal_log for this scenario's DB.
    conn = open_connection(db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM proposal_log"
        ).fetchone()
        proposal_log_count = row["n"]
    finally:
        conn.close()

    # Attempt synthesis — expect SynthesisError because no proposals exist.
    conn = open_connection(db_path)
    try:
        synthesis_error = None
        try:
            run_synthesis(
                conn,
                for_date=date.fromisoformat(scenario["as_of_date"]),
                user_id=USER_ID,
                snapshot=_synthesis_snapshot(scenario["snapshot"]),
            )
        except SynthesisError as exc:
            synthesis_error = str(exc)
    finally:
        conn.close()

    return {
        "scenario_id": "s4_stale_proposal",
        "validation_results": validation_results,
        "proposal_log_row_count": proposal_log_count,
        "synthesis_refused": synthesis_error is not None,
        "synthesis_error_message": synthesis_error,
    }


def main() -> int:
    import tempfile

    outputs = {}
    runners = [
        ("s1", run_scenario_s1),
        ("s2", run_scenario_s2),
        ("s3", run_scenario_s3),
        ("s4", run_scenario_s4),
    ]
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        for sid, fn in runners:
            try:
                outputs[sid] = fn(tmp_path)
            except Exception as exc:
                outputs[sid] = {
                    "scenario_id": sid,
                    "runner_exception": type(exc).__name__,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }

    out_path = OUTPUTS_DIR / "run_results.json"
    out_path.write_text(json.dumps(outputs, indent=2, default=str))
    print(f"wrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
