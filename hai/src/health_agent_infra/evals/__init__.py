"""Evaluation framework for health_agent_infra v1 — shipped with the package.

Scores the deterministic runtime layer — classify, policy, synthesis
X-rule firings + mutations — against scenario JSON files with expected
outputs. Bundled scenarios + rubrics live under this package so the
framework is reachable from an installed wheel, not just a repo checkout.

The skill-layer narration axes (rationale quality, uncertainty
calibration as prose) are explicitly NOT invoked here: they require a
live Claude Code agent subprocess and are marked
``skipped_requires_agent_harness`` per scenario. See
``hai/verification/evals/skill_harness_blocker.md`` for the deferred follow-up.
"""

from .runner import (
    DomainScenarioResult,
    EvalRunError,
    SCENARIOS_ROOT,
    SUPPORTED_DOMAINS,
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
    "SCENARIOS_ROOT",
    "SUPPORTED_DOMAINS",
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
