"""Tests for the MDE / power module (analysis.mde)."""

from __future__ import annotations

import pytest

from governed_agent_bench.analysis.mde import (
    PoweredDesign,
    clustered_power_sim,
    exact_two_proportion_power,
    mde_exact,
)


def test_power_monotone_in_delta():
    p_lo = exact_two_proportion_power(20, 20, 0.5, 0.5)  # null
    p_mid = exact_two_proportion_power(20, 20, 0.7, 0.5)
    p_hi = exact_two_proportion_power(20, 20, 0.95, 0.5)
    assert p_lo < p_mid < p_hi


def test_null_power_at_or_below_alpha():
    # Fisher exact is conservative: size <= alpha under the null.
    assert exact_two_proportion_power(15, 15, 0.4, 0.4, alpha=0.05) <= 0.06


def test_power_monotone_in_n():
    small = exact_two_proportion_power(10, 10, 0.8, 0.5)
    big = exact_two_proportion_power(40, 40, 0.8, 0.5)
    assert big > small


def test_design_cellB_sizes():
    design = PoweredDesign(
        n_capable_models=3, n_weak_models=4, cellB_tasks=6, reps_per_task=4
    )
    assert design.n_capable == 72
    assert design.n_weak == 96


def test_mde_exact_returns_sensible_pp_and_shrinks_with_n():
    small = PoweredDesign(1, 1, 3, 3)   # 9 vs 9
    big = PoweredDesign(3, 4, 6, 4)     # 72 vs 96
    m_small = mde_exact(small, p_weak=0.2, target_power=0.8)
    m_big = mde_exact(big, p_weak=0.2, target_power=0.8)
    assert 0.0 < m_big["mde_pp"] <= 100.0
    # More data detects a smaller effect.
    assert m_big["mde_pp"] < m_small["mde_pp"]
    assert m_big["caveat"].startswith("ignores")


def test_clustered_sim_reproducible_and_bounded():
    design = PoweredDesign(2, 2, 2, 3)  # 12 vs 12
    a = clustered_power_sim(
        design, p_weak=0.2, delta=0.6, scenario_sd=0.5, model_sd=0.5,
        n_sims=80, n_perm=300, seed=1,
    )
    b = clustered_power_sim(
        design, p_weak=0.2, delta=0.6, scenario_sd=0.5, model_sd=0.5,
        n_sims=80, n_perm=300, seed=1,
    )
    assert a["power"] == b["power"]  # deterministic under seed
    assert 0.0 <= a["power"] <= 1.0


def test_clustering_reduces_power():
    # Design effect: at the same true delta, adding between-cluster variance
    # cannot INCREASE power. Allow MC slack.
    design = PoweredDesign(2, 2, 2, 4)  # 16 vs 16
    no_clustering = clustered_power_sim(
        design, p_weak=0.2, delta=0.5, scenario_sd=0.0, model_sd=0.0,
        n_sims=150, n_perm=300, seed=2,
    )["power"]
    heavy_clustering = clustered_power_sim(
        design, p_weak=0.2, delta=0.5, scenario_sd=1.5, model_sd=1.5,
        n_sims=150, n_perm=300, seed=2,
    )["power"]
    assert heavy_clustering <= no_clustering + 0.1
