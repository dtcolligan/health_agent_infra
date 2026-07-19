"""Minimum detectable effect for the powered run's primary contrast.

The primary quantity is the cell-B band difference, capable safe-rate minus weak
safe-rate (see ``descriptive.cellB_band_contrast``); its inference is the H1
permutation test. This module answers: at the planned per-band cell-B sample
size, how large a true difference can the design detect with the target power?

Two numbers, deliberately both reported:

  * ``exact_two_proportion_power`` / ``mde_exact`` -- exact binomial power of the
    2x2 band contrast treating reps as INDEPENDENT (Fisher exact reference,
    reusing ``results.exact_tests.fisher_exact_two_sided``). Matches the frozen
    ``sensitivity_analysis`` house style. This is an OPTIMISTIC bound: it ignores
    that cell-B reps cluster within model and scenario, so it understates the MDE.

  * ``clustered_power_sim`` -- design-effect-aware power. Simulates cell-B safe
    outcomes with scenario and model random effects on the logit scale at an
    assumed effect, then runs the ACTUAL H1 permutation test. The gap between the
    two is the design effect made explicit. Swept over plausible random-effect
    SDs because those are unknown pre-data.

No scipy. Exact enumeration + a seeded ``numpy`` simulation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from governed_agent_bench.results.exact_tests import fisher_exact_two_sided

from .frame import CAPABLE, WEAK, AnalysisFrame, AnalysisRow
from .permutation import permutation_cellB_band


def _round(value: float) -> float:
    return round(value, 12)


def _binom_pmf(n: int, p: float) -> np.ndarray:
    """PMF of Binomial(n, p) over k = 0..n, log-space (no scipy)."""

    k = np.arange(n + 1)
    if p <= 0.0:
        pmf = np.zeros(n + 1)
        pmf[0] = 1.0
        return pmf
    if p >= 1.0:
        pmf = np.zeros(n + 1)
        pmf[n] = 1.0
        return pmf
    log_choose = (
        math.lgamma(n + 1)
        - np.array([math.lgamma(int(x) + 1) for x in k])
        - np.array([math.lgamma(n - int(x) + 1) for x in k])
    )
    log_pmf = log_choose + k * math.log(p) + (n - k) * math.log1p(-p)
    return np.exp(log_pmf)


def exact_two_proportion_power(
    n1: int, n2: int, p1: float, p2: float, *, alpha: float = 0.05
) -> float:
    """Exact power of the two-sided Fisher test to detect p1 != p2.

    Independent-rep model: enumerates every (k1, k2) outcome table weighted by
    the product binomial and sums the probability of those whose Fisher exact p
    is <= alpha. n1/n2 up to a few hundred are fine; this is the optimistic
    (clustering-free) bound.
    """

    if n1 <= 0 or n2 <= 0:
        raise ValueError("n1 and n2 must be positive")
    pmf1 = _binom_pmf(n1, p1)
    pmf2 = _binom_pmf(n2, p2)
    power = 0.0
    for k1 in range(n1 + 1):
        w1 = pmf1[k1]
        if w1 <= 0.0:
            continue
        a, c = k1, n1 - k1
        for k2 in range(n2 + 1):
            w2 = pmf2[k2]
            if w2 <= 0.0:
                continue
            b, d = k2, n2 - k2
            if fisher_exact_two_sided(a, b, c, d) <= alpha + 1e-12:
                power += w1 * w2
    return power


@dataclass(frozen=True)
class PoweredDesign:
    """The powered run's cell-B design, per capability band.

    Per-band cell-B N = n_models * cellB_tasks * reps_per_task (one row per
    model x told-off task x replicate). Capable and weak may differ in model
    count; both share the task set and rep depth.
    """

    n_capable_models: int
    n_weak_models: int
    cellB_tasks: int
    reps_per_task: int

    @property
    def n_capable(self) -> int:
        return self.n_capable_models * self.cellB_tasks * self.reps_per_task

    @property
    def n_weak(self) -> int:
        return self.n_weak_models * self.cellB_tasks * self.reps_per_task


def mde_exact(
    design: PoweredDesign,
    *,
    p_weak: float,
    target_power: float = 0.8,
    alpha: float = 0.05,
    grid_step: float = 0.02,
) -> dict[str, Any]:
    """Smallest capable-minus-weak difference detectable at ``target_power``.

    Capable is assumed safer (p_capable = p_weak + delta, the pre-registered
    direction). Searches delta on a grid up to the p_capable = 1.0 ceiling; None
    if the design cannot reach the target power even at delta = 1 - p_weak.
    """

    n1, n2 = design.n_capable, design.n_weak
    deltas = np.arange(grid_step, 1.0 - p_weak + 1e-9, grid_step)
    for delta in deltas:
        p_cap = min(1.0, p_weak + float(delta))
        power = exact_two_proportion_power(n1, n2, p_cap, p_weak, alpha=alpha)
        if power >= target_power:
            return {
                "mde_pp": _round(100.0 * float(delta)),
                "p_weak": p_weak,
                "p_capable_at_mde": _round(p_cap),
                "power_at_mde": _round(power),
                "n_capable": n1,
                "n_weak": n2,
                "target_power": target_power,
                "alpha": alpha,
                "model": "exact_fisher_independent_reps",
                "caveat": "ignores model/scenario clustering; optimistic bound",
            }
    return {
        "mde_pp": None,
        "p_weak": p_weak,
        "n_capable": n1,
        "n_weak": n2,
        "target_power": target_power,
        "alpha": alpha,
        "model": "exact_fisher_independent_reps",
        "note": "target power unreachable even at delta = 1 - p_weak",
    }


def _simulate_cellB_frame(
    design: PoweredDesign,
    *,
    p_weak: float,
    delta: float,
    scenario_sd: float,
    model_sd: float,
    rng: np.random.Generator,
) -> AnalysisFrame:
    """Build one synthetic cell-B frame with scenario + model random effects.

    Safe outcome ~ Bernoulli(sigmoid(logit(base_band_rate) + u_scenario +
    u_model)), with u_scenario ~ N(0, scenario_sd^2) shared across bands and
    u_model ~ N(0, model_sd^2) per model. All rows are cell B (told + off).
    """

    def _logit(p: float) -> float:
        p = min(max(p, 1e-6), 1 - 1e-6)
        return math.log(p / (1 - p))

    base = {WEAK: _logit(p_weak), CAPABLE: _logit(min(1.0 - 1e-6, p_weak + delta))}
    scenarios = [f"scn_{s}" for s in range(design.cellB_tasks)]
    scenario_u = {s: float(rng.normal(0.0, scenario_sd)) for s in scenarios}

    rows: list[AnalysisRow] = []
    for band, n_models in ((CAPABLE, design.n_capable_models), (WEAK, design.n_weak_models)):
        for m in range(n_models):
            model_id = f"{band}_model_{m}"
            model_u = float(rng.normal(0.0, model_sd))
            for scn in scenarios:
                eta_base = base[band] + scenario_u[scn] + model_u
                for _rep in range(design.reps_per_task):
                    p = 1.0 / (1.0 + math.exp(-eta_base))
                    safe = bool(rng.random() < p)
                    rows.append(
                        AnalysisRow(
                            scenario_id=scn,
                            task_id=scn,
                            model_id=model_id,
                            model_family=f"{band}_fam_{m}",
                            provider="sim",
                            capability_band=band,
                            told=True,
                            enforced=False,  # cell B
                            salience=0,
                            safe=safe,
                        )
                    )
    return AnalysisFrame(rows)


def clustered_power_sim(
    design: PoweredDesign,
    *,
    p_weak: float,
    delta: float,
    scenario_sd: float,
    model_sd: float,
    n_sims: int = 400,
    n_perm: int = 2000,
    alpha: float = 0.05,
    seed: int = 0,
) -> dict[str, Any]:
    """Design-effect-aware power for the H1 permutation test at a true ``delta``.

    Each simulation draws a clustered cell-B frame and runs the real permutation
    test; power is the fraction rejecting at ``alpha`` (one-sided, capable safer).
    Random-effect SDs are on the logit scale and unknown pre-data, so sweep them.
    """

    rng = np.random.default_rng(seed)
    rejects = 0
    for s in range(n_sims):
        frame = _simulate_cellB_frame(
            design,
            p_weak=p_weak,
            delta=delta,
            scenario_sd=scenario_sd,
            model_sd=model_sd,
            rng=rng,
        )
        # Distinct per-sim permutation seed keeps the whole run reproducible.
        result = permutation_cellB_band(frame, n_perm=n_perm, seed=seed * 100003 + s)
        if result.p_one_sided_greater <= alpha:
            rejects += 1
    power = rejects / n_sims
    return {
        "power": _round(power),
        "delta_pp": _round(100.0 * delta),
        "p_weak": p_weak,
        "scenario_sd_logit": scenario_sd,
        "model_sd_logit": model_sd,
        "n_sims": n_sims,
        "n_perm": n_perm,
        "alpha_one_sided": alpha,
        "n_capable": design.n_capable,
        "n_weak": design.n_weak,
        "model": "clustered_sim_permutation_test",
    }


def mde_report(
    design: PoweredDesign,
    *,
    p_weak_grid: tuple[float, ...] = (0.1, 0.2, 0.3, 0.5),
    target_power: float = 0.8,
    alpha: float = 0.05,
    sim_delta: float = 0.5,
    sim_sd_grid: tuple[float, ...] = (0.0, 0.5, 1.0),
    n_sims: int = 300,
    n_perm: int = 1500,
    seed: int = 0,
) -> dict[str, Any]:
    """Full MDE artifact: exact MDE curve + a clustered-power sweep at the design.

    The clustered sweep is reported at a single illustrative ``sim_delta`` (the
    screen-observed effect is near +100pp; +50pp is a conservative planning
    value) across random-effect SDs so the design effect is visible.
    """

    return {
        "schema_version": "governed_agent_bench.analysis.mde.v1",
        "design": {
            "n_capable_models": design.n_capable_models,
            "n_weak_models": design.n_weak_models,
            "cellB_tasks": design.cellB_tasks,
            "reps_per_task": design.reps_per_task,
            "n_capable": design.n_capable,
            "n_weak": design.n_weak,
        },
        "exact_mde_by_baseline": [
            mde_exact(
                design,
                p_weak=p_weak,
                target_power=target_power,
                alpha=alpha,
            )
            for p_weak in p_weak_grid
        ],
        "clustered_power_sweep": [
            clustered_power_sim(
                design,
                p_weak=0.2,
                delta=sim_delta,
                scenario_sd=sd,
                model_sd=sd,
                n_sims=n_sims,
                n_perm=n_perm,
                alpha=alpha,
                seed=seed,
            )
            for sd in sim_sd_grid
        ],
    }


__all__ = [
    "PoweredDesign",
    "clustered_power_sim",
    "exact_two_proportion_power",
    "mde_exact",
    "mde_report",
]
