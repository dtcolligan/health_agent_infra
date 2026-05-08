"""W42 — synthesis-skill scoring."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


HARNESS_DIR = (
    Path(__file__).resolve().parents[1] / "evals" / "synthesis_harness"
)


@pytest.fixture(scope="module")
def harness():
    runner_path = HARNESS_DIR / "runner.py"
    spec = importlib.util.spec_from_file_location(
        "hai_synthesis_harness_runner", runner_path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_rubric_doc_present() -> None:
    rubric = HARNESS_DIR / "rubrics" / "synthesis.md"
    assert rubric.exists()
    assert rubric.read_text().strip()


def test_three_fixture_scenarios_present(harness) -> None:
    """W42 acceptance: at least three fixture days — clean / partial /
    escalated."""

    scenarios = harness.load_scenarios()
    assert len(scenarios) >= 3
    ids = {s["scenario_id"] for s in scenarios}
    assert any("clean" in i for i in ids)
    assert any("partial" in i for i in ids)
    assert any("escalated" in i for i in ids)


def test_clean_scenario_passes_with_minimal_output(harness) -> None:
    scenarios = {s["scenario_id"]: s for s in harness.load_scenarios()}
    scenario = scenarios["syn_d01_clean"]
    output = {
        "joint_narration": "Recovery is full and running is steady — proceed with the planned day.",
        "per_domain_action": {
            "recovery": "proceed_with_planned_session",
            "running": "proceed_with_planned_run",
        },
    }
    score = harness.score_synthesis_output(scenario, output)
    assert score.correctness_passed, score.correctness


def test_missing_firing_flags_failure(harness) -> None:
    scenarios = {s["scenario_id"]: s for s in harness.load_scenarios()}
    scenario = scenarios["syn_d02_partial_x1a"]
    # Output that ignores the X1a firing.
    output = {
        "joint_narration": "Sleep is fine; recovery is solid.",
    }
    score = harness.score_synthesis_output(scenario, output)
    assert not score.correctness_passed
    detail = score.correctness["all_firings_cited_or_summarised"].detail
    assert "X1a" in detail


def test_invented_xrule_flags_failure(harness) -> None:
    scenarios = {s["scenario_id"]: s for s in harness.load_scenarios()}
    scenario = scenarios["syn_d01_clean"]
    output = {
        "joint_narration": "X9 fired (it didn't), bumping protein.",
        "per_domain_action": {
            "recovery": "proceed_with_planned_session",
            "running": "proceed_with_planned_run",
        },
    }
    score = harness.score_synthesis_output(scenario, output)
    assert not score.correctness_passed
    assert "X9" in score.correctness["no_invented_xrule"].detail


def test_action_mutation_by_prose_flags_failure(harness) -> None:
    scenarios = {s["scenario_id"]: s for s in harness.load_scenarios()}
    scenario = scenarios["syn_d01_clean"]
    output = {
        "joint_narration": "Recovery looks fine; running is steady.",
        "per_domain_action": {
            "recovery": "rest_day_recommended",  # mutation vs draft_action
            "running": "proceed_with_planned_run",
        },
    }
    score = harness.score_synthesis_output(scenario, output)
    assert not score.correctness_passed
    assert "recovery" in score.correctness["no_action_mutation_by_prose"].detail


def test_escalated_scenario_with_correct_output_passes(harness) -> None:
    scenarios = {s["scenario_id"]: s for s in harness.load_scenarios()}
    scenario = scenarios["syn_d03_escalated_x3b"]
    output = {
        "joint_narration": "X3b fired — block on hard sessions; running flips to escalate_for_user_review.",
        "per_domain_action": {
            "running": "escalate_for_user_review",
        },
    }
    score = harness.score_synthesis_output(scenario, output)
    assert score.correctness_passed, score.correctness
