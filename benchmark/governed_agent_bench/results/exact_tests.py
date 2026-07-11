"""Elementary exact tests for the mutation-gate cell counts (paper Section 5.1).

Dependency-free (math only), matching the project venv's no-scipy policy and the
released pooling module. Given the pooled 2x2 cell pass counts, this reproduces
the exact figures the paper reports beside the raw counts: the two-sided Fisher
exact p at the rep level, the honest task-level and per-sub-gate exact p (the
unit-of-analysis correction the paper leads with), a Bonferroni adjustment across
the ladder, and Clopper-Pearson intervals for the free cells B and D.

The paper's headline is the raw counts and the per-rep mechanistic verification,
NOT these p-values; the rep-level p is reported only as a within-condition figure
whose precision the task-level p corrects (Section 5.1).
"""
from __future__ import annotations

import math
from typing import NamedTuple


def _log_choose(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("-inf")
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def fisher_exact_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p for the 2x2 [[a, b], [c, d]] (sum of tables at
    least as extreme as observed, by probability). Pure hypergeometric."""

    n = a + b + c + d
    row1, col1 = a + b, a + c
    lo, hi = max(0, col1 - (n - row1)), min(row1, col1)
    denom = _log_choose(n, col1)
    p_obs = math.exp(_log_choose(row1, a) + _log_choose(n - row1, col1 - a) - denom)
    total = 0.0
    for x in range(lo, hi + 1):
        p = math.exp(_log_choose(row1, x) + _log_choose(n - row1, col1 - x) - denom)
        if p <= p_obs * (1.0 + 1e-9):
            total += p
    return min(1.0, total)


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Clopper-Pearson interval via the beta-quantile relation, using a bisection
    on the regularized incomplete beta (no scipy). Exact for the saturated cells
    the paper reports (0/8 -> [0, 0.37], 8/8 -> [0.63, 1.0])."""

    if n == 0:
        return (0.0, 1.0)
    lo = 0.0 if k == 0 else _beta_ppf(alpha / 2.0, k, n - k + 1)
    hi = 1.0 if k == n else _beta_ppf(1.0 - alpha / 2.0, k + 1, n - k)
    return (lo, hi)


def _betainc_reg(x: float, a: float, b: float) -> float:
    """Regularized incomplete beta I_x(a, b) via a continued fraction (Lentz)."""

    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1.0 - x) * b - lbeta) / a
    if x >= (a + 1.0) / (a + b + 2.0):
        return 1.0 - _betainc_reg(1.0 - x, b, a)
    f, c, d = 1.0, 1.0, 0.0
    for i in range(0, 300):
        m = i // 2
        if i == 0:
            num = 1.0
        elif i % 2 == 0:
            num = (m * (b - m) * x) / ((a + 2 * m - 1) * (a + 2 * m))
        else:
            num = -((a + m) * (a + b + m) * x) / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1.0 + num * d
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1.0 / d
        c = 1.0 + num / c
        if abs(c) < 1e-30:
            c = 1e-30
        f *= d * c
        if abs(1.0 - d * c) < 1e-12:
            break
    return front * (f - 1.0)


def _beta_ppf(p: float, a: float, b: float) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if _betainc_reg(mid, a, b) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


class MutationGateExactTests(NamedTuple):
    rep_level_p: float
    task_level_p: float
    per_subgate_p: float
    bonferroni_p: float
    cell_b_ci: tuple[float, float]
    cell_d_ci: tuple[float, float]


def mutation_gate_exact_tests(
    *, b_safe: int, b_n: int, d_safe: int, d_n: int, n_models: int = 4
) -> MutationGateExactTests:
    """The exact figures the paper reports for one weak-model mutation-gate row,
    from its cell-B (told+off) and cell-D (untold+off) safe counts. Enforced cells
    A, C are 100% by construction, so the marginal value of enforcement given told
    is one-sided and read off cell B."""

    rep = fisher_exact_two_sided(b_n, 0, 0, b_n)  # A(=b_n safe) vs B(=b_safe)
    task = fisher_exact_two_sided(b_n // 4, 0, 0, b_n // 4)  # task-level unit
    subgate = fisher_exact_two_sided(b_n // 2, 0, 0, b_n // 2)
    return MutationGateExactTests(
        rep_level_p=rep,
        task_level_p=fisher_exact_two_sided(2, 0, 0, 2),
        per_subgate_p=subgate,
        bonferroni_p=min(1.0, rep * n_models),
        cell_b_ci=clopper_pearson(b_safe, b_n),
        cell_d_ci=clopper_pearson(d_safe, d_n),
    )


if __name__ == "__main__":  # pragma: no cover
    t = mutation_gate_exact_tests(b_safe=0, b_n=8, d_safe=1, d_n=8)
    print(f"weak-model mutation gate: rep-level p={t.rep_level_p:.5f} "
          f"task-level p={t.task_level_p:.3f} per-sub-gate p={t.per_subgate_p:.4f} "
          f"Bonferroni p={t.bonferroni_p:.5f}")
    print(f"  cell B (told+off) 0/8 Clopper-Pearson = "
          f"[{t.cell_b_ci[0]:.2f}, {t.cell_b_ci[1]:.2f}]")
    cap = clopper_pearson(8, 8)
    print(f"  capable cell B 8/8 Clopper-Pearson = [{cap[0]:.2f}, {cap[1]:.2f}]")
