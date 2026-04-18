"""Test that every committed scenario under safety/evals/scenarios/ passes.

These tests are the integration regression for the Phase 6 eval
content: changes to classifier / policy / synthesis that silently
break the eval contract should fail here first. Failures should be
treated as either (a) intentional runtime changes that require the
scenario's ``expected`` block to be updated, or (b) regressions that
must be fixed before merge.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from safety.evals.runner import (  # noqa: E402
    SUPPORTED_DOMAINS,
    load_scenarios,
    run_scenarios,
)


@pytest.mark.parametrize("domain", sorted(SUPPORTED_DOMAINS))
def test_all_domain_scenarios_pass(domain: str) -> None:
    scenarios = load_scenarios("domain", domain=domain)
    assert scenarios, (
        f"no domain scenarios registered under safety/evals/scenarios/{domain}/"
    )
    scores = run_scenarios(scenarios)
    failures = [s for s in scores if not s.passed]
    assert not failures, (
        f"{len(failures)}/{len(scores)} {domain} scenarios failed:\n"
        + "\n".join(
            f"  - {s.scenario_id}: {s.diffs}" for s in failures
        )
    )


def test_all_synthesis_scenarios_pass() -> None:
    scenarios = load_scenarios("synthesis")
    assert scenarios, (
        "no synthesis scenarios registered under "
        "safety/evals/scenarios/synthesis/"
    )
    scores = run_scenarios(scenarios)
    failures = [s for s in scores if not s.passed]
    assert not failures, (
        f"{len(failures)}/{len(scores)} synthesis scenarios failed:\n"
        + "\n".join(
            f"  - {s.scenario_id}: {s.diffs}" for s in failures
        )
    )


def test_every_domain_has_at_least_three_scenarios() -> None:
    """Coverage floor: each of the six v1 domains ships at least three
    scenarios (baseline, firing, gap). Below three is a red flag that
    the domain rubric was never exercised on its own turf.
    """

    for domain in sorted(SUPPORTED_DOMAINS):
        scenarios = load_scenarios("domain", domain=domain)
        assert len(scenarios) >= 3, (
            f"{domain} has only {len(scenarios)} scenarios; "
            "expected ≥ 3 (baseline + R-rule firing + coverage gap)"
        )


def test_synthesis_scenarios_cover_key_x_rules() -> None:
    """Coverage floor: synthesis scenarios must collectively exercise
    the core Phase A rule set plus the Phase B rule and the
    validation-error path.
    """

    scenarios = load_scenarios("synthesis")
    all_expected_rules: set[str] = set()
    has_validation_error_scenario = False
    has_no_firings_scenario = False
    for s in scenarios:
        expected = s.get("expected", {})
        for rule in expected.get("x_rules_fired") or []:
            all_expected_rules.add(rule)
        if expected.get("x_rules_fired") == []:
            has_no_firings_scenario = True
        if expected.get("validation_errors"):
            has_validation_error_scenario = True

    # At minimum these cross-domain rules must be covered.
    required = {"X1a", "X1b", "X3a", "X3b", "X6a", "X7", "X2", "X9"}
    missing = required - all_expected_rules
    assert not missing, f"synthesis scenarios miss X-rules: {sorted(missing)}"
    assert has_validation_error_scenario, (
        "no synthesis scenario asserts on the validation-error path "
        "(writeback rejects stale proposals)"
    )
    assert has_no_firings_scenario, (
        "no synthesis scenario asserts the baseline no-firings case "
        "(actions pass through unchanged)"
    )
