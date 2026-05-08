"""Tests for the packaged eval runner.

Exercises the domain and synthesis runners against a minimal hand-built
scenario for each kind, then the load + dispatch path from
``run_scenarios``. Keeps the scope tight: the per-domain scenario
content itself is validated by the ``test_eval_scenarios_*`` tests, not
here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from health_agent_infra.evals.runner import (
    EvalRunError,
    load_scenario,
    load_scenarios,
    run_domain_scenario,
    run_scenarios,
    run_synthesis_scenario,
    score_domain_result,
    score_synthesis_result,
)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _rested_recovery_scenario() -> dict:
    return {
        "scenario_id": "test_rec_rested",
        "kind": "domain",
        "domain": "recovery",
        "description": "Well-rested baseline; expect no forced_action.",
        "input": {
            "evidence": {
                "as_of_date": "2026-04-17",
                "user_id": "u_eval",
                "sleep_hours": 8.0,
                "resting_hr": 52.0,
                "hrv_ms": 80.0,
                "soreness_self_report": "low",
            },
            "raw_summary": {
                "as_of_date": "2026-04-17",
                "user_id": "u_eval",
                "resting_hr_baseline": 52.0,
                "resting_hr_ratio_vs_baseline": 1.0,
                "hrv_ratio_vs_baseline": 1.0,
                "trailing_7d_training_load": 400.0,
                "training_load_baseline": 400.0,
                "training_load_ratio_vs_baseline": 1.0,
                "resting_hr_spike_days": 0,
            },
        },
        "expected": {
            "classified": {"sleep_debt_band": "none"},
            "policy": {"forced_action": None, "capped_confidence": None},
        },
    }


def _rhr_spike_recovery_scenario() -> dict:
    # R6 fires at resting_hr_spike_days ≥ 3; forces escalate_for_user_review.
    return {
        "scenario_id": "test_rec_rhr_spike",
        "kind": "domain",
        "domain": "recovery",
        "description": "Sustained RHR spike (≥3 days) → R6 escalates.",
        "input": {
            "evidence": {
                "as_of_date": "2026-04-17",
                "user_id": "u_eval",
                "sleep_hours": 8.0,
                "resting_hr": 65.0,
                "hrv_ms": 80.0,
                "soreness_self_report": "low",
            },
            "raw_summary": {
                "as_of_date": "2026-04-17",
                "user_id": "u_eval",
                "resting_hr_baseline": 52.0,
                "resting_hr_ratio_vs_baseline": 1.25,
                "hrv_ratio_vs_baseline": 1.0,
                "trailing_7d_training_load": 400.0,
                "training_load_baseline": 400.0,
                "training_load_ratio_vs_baseline": 1.0,
                "resting_hr_spike_days": 3,
            },
        },
        "expected": {
            "policy": {"forced_action": "escalate_for_user_review"},
        },
    }


def _synthesis_x1a_scenario() -> dict:
    return {
        "scenario_id": "test_syn_x1a_soften",
        "kind": "synthesis",
        "description": "Moderate sleep debt softens hard recovery proposal.",
        "as_of_date": "2026-04-18",
        "user_id": "u_eval",
        "snapshot": {
            "sleep": {
                "classified_state": {"sleep_debt_band": "moderate"},
            },
            "recovery": {"today": {"acwr_ratio": 1.0}},
            "stress": {"today_garmin": 20, "today_body_battery": 60},
        },
        "proposals": [
            {
                "proposal_id": "prop_rec_2026-04-18_u_eval",
                "user_id": "u_eval",
                "for_date": "2026-04-18",
                "domain": "recovery",
                "action": "proceed_with_planned_session",
                "confidence": "high",
            },
        ],
        "expected": {
            "x_rules_fired": ["X1a"],
            "final_actions": {"recovery": "downgrade_hard_session_to_zone_2"},
            "final_confidences": {"recovery": "high"},
        },
    }


# ---------------------------------------------------------------------------
# Domain runner
# ---------------------------------------------------------------------------


class TestDomainRunner:
    def test_rested_scenario_passes_all_axes(self) -> None:
        scenario = _rested_recovery_scenario()
        result = run_domain_scenario(scenario)
        score = score_domain_result(result, scenario["expected"])
        assert score.passed is True
        assert score.axes["classified_bands"] == "pass"
        assert score.axes["policy_decisions"] == "pass"
        assert score.axes["rationale_quality"] == "skipped_requires_agent_harness"

    def test_rhr_spike_forces_rest(self) -> None:
        scenario = _rhr_spike_recovery_scenario()
        result = run_domain_scenario(scenario)
        score = score_domain_result(result, scenario["expected"])
        assert score.passed is True
        # Cross-check on the actual result: R6 must have fired.
        decisions = result.policy.get("policy_decisions", [])
        escalations = {d["rule_id"] for d in decisions if d.get("decision") == "escalate"}
        assert "resting_hr_spike_escalation" in escalations

    def test_mismatched_classified_band_fails_axis_with_diff(self) -> None:
        scenario = _rested_recovery_scenario()
        scenario["expected"]["classified"]["sleep_debt_band"] = "elevated"
        result = run_domain_scenario(scenario)
        score = score_domain_result(result, scenario["expected"])
        assert score.passed is False
        assert score.axes["classified_bands"] == "fail"
        diff = score.diffs["classified_bands"]["sleep_debt_band"]
        assert diff["expected"] == "elevated"
        assert diff["actual"] == "none"


# ---------------------------------------------------------------------------
# Synthesis runner
# ---------------------------------------------------------------------------


class TestSynthesisRunner:
    def test_x1a_soften_passes(self) -> None:
        scenario = _synthesis_x1a_scenario()
        result = run_synthesis_scenario(scenario)
        score = score_synthesis_result(result, scenario["expected"])
        assert score.passed is True, f"diffs={score.diffs}"
        assert score.axes["x_rules_fired"] == "pass"
        assert score.axes["final_actions"] == "pass"
        assert score.axes["final_confidences"] == "pass"

    def test_scenario_with_no_firings(self) -> None:
        scenario = _synthesis_x1a_scenario()
        scenario["scenario_id"] = "test_syn_no_firings"
        # Rested snapshot.
        scenario["snapshot"]["sleep"]["classified_state"]["sleep_debt_band"] = "none"
        scenario["expected"] = {
            "x_rules_fired": [],
            "final_actions": {"recovery": "proceed_with_planned_session"},
            "final_confidences": {"recovery": "high"},
        }
        result = run_synthesis_scenario(scenario)
        score = score_synthesis_result(result, scenario["expected"])
        assert score.passed is True, f"diffs={score.diffs}"

    def test_mismatched_final_action_fails_axis(self) -> None:
        scenario = _synthesis_x1a_scenario()
        scenario["expected"]["final_actions"]["recovery"] = "rest_day_recommended"
        result = run_synthesis_scenario(scenario)
        score = score_synthesis_result(result, scenario["expected"])
        assert score.passed is False
        assert score.axes["final_actions"] == "fail"
        diff = score.diffs["final_actions"]["recovery"]
        assert diff["expected"] == "rest_day_recommended"
        assert diff["actual"] == "downgrade_hard_session_to_zone_2"


# ---------------------------------------------------------------------------
# Dispatch + loader
# ---------------------------------------------------------------------------


class TestLoaderAndDispatch:
    def test_load_scenario_accepts_well_formed_file(self, tmp_path: Path) -> None:
        scenario = _rested_recovery_scenario()
        p = tmp_path / "s.json"
        p.write_text(json.dumps(scenario))
        loaded = load_scenario(p)
        assert loaded["scenario_id"] == scenario["scenario_id"]

    def test_load_scenario_missing_fields_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "s.json"
        p.write_text(json.dumps({"scenario_id": "x"}))
        with pytest.raises(EvalRunError, match="missing required field"):
            load_scenario(p)

    def test_load_scenario_malformed_json_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "s.json"
        p.write_text("{not valid json")
        with pytest.raises(EvalRunError, match="not valid JSON"):
            load_scenario(p)

    def test_load_scenarios_rejects_unknown_domain(self) -> None:
        with pytest.raises(EvalRunError, match="unsupported domain"):
            load_scenarios("domain", domain="not_a_domain")

    def test_load_scenarios_rejects_unknown_kind(self) -> None:
        with pytest.raises(EvalRunError, match="unknown scenario kind"):
            load_scenarios("meta")

    def test_run_scenarios_dispatches_by_kind(self) -> None:
        domain_s = _rested_recovery_scenario()
        synthesis_s = _synthesis_x1a_scenario()
        scores = run_scenarios([domain_s, synthesis_s])
        assert len(scores) == 2
        assert scores[0].scenario_id == domain_s["scenario_id"]
        assert scores[1].scenario_id == synthesis_s["scenario_id"]

    def test_run_scenarios_rejects_unknown_kind(self) -> None:
        with pytest.raises(EvalRunError, match="unknown kind"):
            run_scenarios([{"scenario_id": "bad", "kind": "other",
                            "description": "x", "expected": {}}])
