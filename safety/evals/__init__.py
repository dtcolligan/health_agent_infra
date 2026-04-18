"""Evaluation framework for health_agent_infra v1.

Scores the deterministic runtime layer — classify, policy, synthesis
X-rule firings + mutations — against scenario JSON files with expected
outputs. The skill-layer narration axes (rationale quality, uncertainty
calibration as prose) are explicitly NOT invoked here: they require a
live Claude Code agent subprocess and are marked
``skipped_requires_agent_harness`` per scenario. See README.md for the
honesty contract.
"""

from .runner import (
    DomainScenarioResult,
    EvalRunError,
    ScenarioScore,
    SynthesisScenarioResult,
    load_scenario,
    load_scenarios,
    run_domain_scenario,
    run_scenarios,
    run_synthesis_scenario,
    score_domain_result,
    score_synthesis_result,
)


__all__ = [
    "DomainScenarioResult",
    "EvalRunError",
    "ScenarioScore",
    "SynthesisScenarioResult",
    "load_scenario",
    "load_scenarios",
    "run_domain_scenario",
    "run_scenarios",
    "run_synthesis_scenario",
    "score_domain_result",
    "score_synthesis_result",
]
