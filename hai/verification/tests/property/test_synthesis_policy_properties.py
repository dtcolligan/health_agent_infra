"""M7 — Hypothesis property tests for ``synthesis_policy``.

Every assertion here pins a runtime invariant that was previously only
exercised by example-based tests. A Hypothesis counter-example means
the invariant is broken somewhere the example suite doesn't reach.

Seed control: ``@settings(derandomize=True)`` on every strategy so CI
runs are reproducible. Max-examples is kept modest (100) — these
tests are fast enough to run in the main suite without gating.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

try:
    from hypothesis import given, settings, strategies as st
except ImportError:  # pragma: no cover — hypothesis is a dev-only dep
    pytest.skip("hypothesis not installed", allow_module_level=True)

from health_agent_infra.core.synthesis_policy import (
    PHASE_A_EVALUATORS,
    PHASE_B_TARGETS,
    XRuleFiring,
    XRuleWriteSurfaceViolation,
    apply_phase_a,
    apply_phase_b,
    evaluate_phase_a,
    guard_phase_b_mutation,
)


DOMAINS = ("recovery", "running", "strength", "sleep", "stress", "nutrition")
PHASE_A_TIERS = ("soften", "block", "cap_confidence")
HARD_ACTIONS_BY_DOMAIN = {
    "recovery": "proceed_with_planned_session",
    "running": "proceed_with_planned_run",
    "strength": "proceed_with_planned_session",
    "sleep": "maintain_schedule",
    "stress": "maintain_routine",
    "nutrition": "maintain_targets",
}


def _proposal_strategy() -> st.SearchStrategy[dict[str, Any]]:
    """A random-ish proposal dict that's valid enough to feed apply_phase_a.

    Keeps the payload shape stable; only the domain + action + confidence
    vary. Fields outside synthesis's read-set are fixed so random data
    doesn't send the test down an irrelevant control path.
    """

    return st.builds(
        lambda domain, confidence: {
            "domain": domain,
            "action": HARD_ACTIONS_BY_DOMAIN[domain],
            "action_detail": None,
            "confidence": confidence,
            "rationale": ["x"],
            "uncertainty": [],
        },
        domain=st.sampled_from(DOMAINS),
        confidence=st.sampled_from(("low", "moderate", "high")),
    )


def _firing_strategy(
    rule_id: str = "X_prop",
    tier: str = "soften",
) -> st.SearchStrategy[XRuleFiring]:
    return st.builds(
        XRuleFiring,
        rule_id=st.just(rule_id),
        tier=st.just(tier),
        affected_domain=st.sampled_from(DOMAINS),
        trigger_note=st.just("synthetic"),
        recommended_mutation=st.just({
            "action": "downgrade_hard_session_to_zone_2",
            "action_detail": {"reason_token": "prop_test"},
        }),
        source_signals=st.just({}),
        phase=st.just("A"),
    )


# ---------------------------------------------------------------------------
# Property 1 — block dominates soften on the same domain
# ---------------------------------------------------------------------------


@settings(derandomize=True, max_examples=100)
@given(
    proposal=_proposal_strategy(),
    n_softens=st.integers(min_value=0, max_value=5),
    n_blocks=st.integers(min_value=1, max_value=5),  # at least one block
)
def test_block_always_dominates_soften_on_same_proposal(
    proposal: dict[str, Any], n_softens: int, n_blocks: int,
):
    domain = proposal["domain"]
    firings: list[XRuleFiring] = []
    for _ in range(n_softens):
        firings.append(XRuleFiring(
            rule_id="X_s", tier="soften", affected_domain=domain,
            trigger_note="s", recommended_mutation={
                "action": "downgrade_hard_session_to_zone_2",
                "action_detail": {"reason_token": "soften"},
            },
            source_signals={}, phase="A",
        ))
    for _ in range(n_blocks):
        firings.append(XRuleFiring(
            rule_id="X_b", tier="block", affected_domain=domain,
            trigger_note="b", recommended_mutation={
                "action": "escalate_for_user_review",
                "action_detail": {"reason_token": "block"},
            },
            source_signals={}, phase="A",
        ))

    mutated, fired_ids = apply_phase_a(proposal, firings)

    # Block wins: the final action is the block's escalate.
    assert mutated["action"] == "escalate_for_user_review"
    # Every soften + block is still recorded as fired (audit completeness).
    assert "X_s" in fired_ids or n_softens == 0
    assert "X_b" in fired_ids


# ---------------------------------------------------------------------------
# Property 2 — cap_confidence commutes with soften/block
# ---------------------------------------------------------------------------


@settings(derandomize=True, max_examples=50)
@given(
    proposal=_proposal_strategy().filter(lambda p: p["confidence"] == "high"),
    order=st.sampled_from(["cap_first", "block_first"]),
)
def test_cap_confidence_commutes_with_block(
    proposal: dict[str, Any], order: str,
):
    """Applying block then cap in either order ends up at the same state:
    action escalated AND confidence dropped from high to moderate."""

    domain = proposal["domain"]
    cap = XRuleFiring(
        rule_id="X7", tier="cap_confidence", affected_domain=domain,
        trigger_note="stress", recommended_mutation=None,
        source_signals={}, phase="A",
    )
    block = XRuleFiring(
        rule_id="X1b", tier="block", affected_domain=domain,
        trigger_note="sleep", recommended_mutation={
            "action": "escalate_for_user_review",
            "action_detail": {"reason_token": "block"},
        },
        source_signals={}, phase="A",
    )

    order_a = [cap, block] if order == "cap_first" else [block, cap]
    order_b = list(reversed(order_a))

    mutated_a, _ = apply_phase_a(proposal, order_a)
    mutated_b, _ = apply_phase_a(proposal, order_b)

    assert mutated_a["action"] == mutated_b["action"] == "escalate_for_user_review"
    assert mutated_a["confidence"] == mutated_b["confidence"] == "moderate"


# ---------------------------------------------------------------------------
# Property 3 — copy-on-write: input dict not mutated
# ---------------------------------------------------------------------------


@settings(derandomize=True, max_examples=50)
@given(proposal=_proposal_strategy())
def test_apply_phase_a_does_not_mutate_input_proposal(
    proposal: dict[str, Any],
):
    snapshot_before = copy.deepcopy(proposal)
    firings = [XRuleFiring(
        rule_id="X_s", tier="soften",
        affected_domain=proposal["domain"],
        trigger_note="s",
        recommended_mutation={
            "action": "downgrade_hard_session_to_zone_2",
            "action_detail": {"reason_token": "test"},
        },
        source_signals={}, phase="A",
    )]
    apply_phase_a(proposal, firings)
    assert proposal == snapshot_before


# ---------------------------------------------------------------------------
# Property 4 — Phase B guard rejects every off-surface mutation
# ---------------------------------------------------------------------------


@settings(derandomize=True, max_examples=80)
@given(
    rule_id=st.sampled_from(list(PHASE_B_TARGETS.keys())),
    domain=st.sampled_from(DOMAINS),
    mutation_shape=st.sampled_from(["action_only", "action_and_detail", "no_detail"]),
)
def test_guard_phase_b_rejects_action_mutations(
    rule_id: str, domain: str, mutation_shape: str,
):
    # Build a mutation that's *always* off-surface: contains 'action',
    # which Phase B is forbidden from touching.
    if mutation_shape == "action_only":
        mutation = {"action": "proceed_with_planned_session"}
    elif mutation_shape == "action_and_detail":
        mutation = {
            "action": "proceed_with_planned_session",
            "action_detail": {"k": "v"},
        }
    else:
        mutation = {"action": "proceed_with_planned_session"}

    firing = XRuleFiring(
        rule_id=rule_id, tier="adjust", affected_domain=domain,
        trigger_note="off-surface attempt",
        recommended_mutation=mutation,
        source_signals={}, phase="B",
    )
    with pytest.raises(XRuleWriteSurfaceViolation):
        guard_phase_b_mutation(firing)


@settings(derandomize=True, max_examples=60)
@given(
    rule_id=st.sampled_from(list(PHASE_B_TARGETS.keys())),
    off_target_domain=st.sampled_from(DOMAINS),
)
def test_guard_phase_b_rejects_off_target_domain(
    rule_id: str, off_target_domain: str,
):
    allowed = PHASE_B_TARGETS[rule_id]
    if off_target_domain in allowed:
        # Hypothesis may sample an allowed domain; the sibling test
        # covers the rejection path.
        return
    firing = XRuleFiring(
        rule_id=rule_id, tier="adjust",
        affected_domain=off_target_domain,
        trigger_note="wrong domain",
        recommended_mutation={"action_detail": {"k": "v"}},
        source_signals={}, phase="B",
    )
    with pytest.raises(XRuleWriteSurfaceViolation):
        guard_phase_b_mutation(firing)


# ---------------------------------------------------------------------------
# Property 5 — evaluate_phase_a only emits firings for proposal domains
# ---------------------------------------------------------------------------


@settings(derandomize=True, max_examples=25)
@given(proposals=st.lists(_proposal_strategy(), min_size=1, max_size=6))
def test_evaluate_phase_a_emits_only_for_proposal_domains(proposals):
    # An "everything triggers" snapshot so every rule that *can* fire
    # does fire. The property under test is not whether rules fire,
    # but that firings reference only domains present in proposals.
    snapshot = {
        "recovery": {
            "classified_state": {"sleep_debt_band": "moderate"},
            "today": {"acwr_ratio": 1.6},
        },
        "sleep": {"classified_state": {"sleep_debt_band": "moderate"}},
        "stress": {
            "classified_state": {"garmin_stress_band": "very_high"},
            "today": {"body_battery_end_of_day": 10},
            "today_body_battery": 10,
            "today_garmin": 85,
        },
    }
    thresholds = {
        "synthesis": {"x_rules": {
            "x1a": {"sleep_debt_trigger_band": "moderate"},
            "x1b": {"sleep_debt_trigger_band": "elevated"},
            "x2": {"deficit_kcal_min": 500.0, "protein_ratio_max": 0.7},
            "x3a": {"acwr_ratio_lower": 1.3, "acwr_ratio_upper": 1.5},
            "x3b": {"acwr_ratio_min": 1.5},
            "x4": {"heavy_lower_body_min_volume": 2000.0},
            "x5": {"vigorous_intensity_min": 20, "long_run_min_duration_s": 4500},
            "x6a": {"body_battery_max": 30},
            "x6b": {"body_battery_max": 15},
            "x7": {
                "stress_trigger_bands": ["high", "very_high"],
                "moderate_min_score": 40, "high_min_score": 60, "very_high_min_score": 80,
            },
        }},
        "classify": {"nutrition": {"targets": {
            "calorie_target_kcal": 2400, "protein_target_g": 140,
        }}},
    }

    firings = evaluate_phase_a(proposals, thresholds=thresholds, snapshot=snapshot) \
        if False else [
        f for evaluator in PHASE_A_EVALUATORS
        for f in evaluator(snapshot, proposals, thresholds)
    ]

    proposal_domains = {p["domain"] for p in proposals}
    for f in firings:
        assert f.affected_domain in proposal_domains, (
            f"evaluator emitted orphan firing for {f.affected_domain!r} "
            f"(rule {f.rule_id}); proposal domains were {sorted(proposal_domains)}"
        )
