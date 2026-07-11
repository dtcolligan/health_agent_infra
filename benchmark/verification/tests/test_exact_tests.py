"""Pin the paper's Section 5.1 exact-test figures to the released helper."""
from __future__ import annotations

from governed_agent_bench.results.exact_tests import (
    clopper_pearson,
    fisher_exact_two_sided,
    mutation_gate_exact_tests,
)


def test_fisher_matches_paper_headline_figures() -> None:
    # weak-model marginal value of enforcement given told, cell A(8/8) vs B(0/8)
    assert round(fisher_exact_two_sided(8, 0, 0, 8), 5) == 0.00016
    # unit-of-analysis correction: task-level (2v2) and per-sub-gate (4v4)
    assert round(fisher_exact_two_sided(2, 0, 0, 2), 2) == 0.33
    assert round(fisher_exact_two_sided(4, 0, 0, 4), 3) == 0.029


def test_clopper_pearson_saturated_cells_match_paper() -> None:
    lo, hi = clopper_pearson(0, 8)  # weak cell B, 0/8 safe -> [0, 37]
    assert round(100 * lo) == 0 and round(100 * hi) == 37
    lo, hi = clopper_pearson(8, 8)  # capable cell B, 8/8 safe -> [63, 100]
    assert round(100 * lo) == 63 and round(100 * hi) == 100


def test_mutation_gate_exact_tests_bundle() -> None:
    t = mutation_gate_exact_tests(b_safe=0, b_n=8, d_safe=1, d_n=8, n_models=4)
    assert round(t.rep_level_p, 5) == 0.00016
    assert round(t.task_level_p, 2) == 0.33
    assert round(t.per_subgate_p, 3) == 0.029
    assert round(t.bonferroni_p, 5) == 0.00062
    assert (round(100 * t.cell_b_ci[0]), round(100 * t.cell_b_ci[1])) == (0, 37)
