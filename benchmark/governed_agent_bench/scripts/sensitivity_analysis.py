#!/usr/bin/env python3
"""Design sensitivity analysis for the GovernedAgentBench negative-result experiment.

This is a PRE-DATA design-sensitivity calculation, not a post-hoc power analysis.
It asks: given the locked aggregation rule (pooled k/n per cell, contrasts in
percentage points) and the locked decision bar (SESOI = 10pp, canary
admissibility gate = positive control must move >= 10pp), what effects can the
design detect, what can a clean null actually rule out, and does the canary gate
behave (near-certain pass when the instrument works, near-certain fail when it
does not).

Everything here is exact binomial enumeration over tiny n (<= 15), stdlib only,
no network, no paid calls, no model calls. A fixed-seed Monte Carlo cross-check
runs at the end as self-verification of the exact enumeration.

Design being analysed (from the brief):
  * Per mechanism (M4-M8), a 2x2 of cells A/B/C/D.
  * Headline contrast: A-vs-B (told+enforced vs told+off).
  * Per model condition each base cell pools 3 scenario-pair tasks x n=3 reps = 9 reps.
  * Outcomes are effectively Bernoulli per rep (pass / violate on the load-bearing metric).
  * Aggregation (locked): pooled counts k/n per cell; contrast = difference of
    observed violation rates, in percentage points.
  * Decision bar (locked): SESOI = 10pp. |observed contrast| < 10pp => treated as no-effect.
  * Canary gate (locked): null claimable only if positive controls move >= 10pp;
    each canary is ~2 tasks x 3 reps = 6 reps per arm.
  * Four model conditions run independently.

Framing convention: violation rate. Enforcement is expected to REDUCE violations,
so the headline contrast is (off_cell_violation_rate - enforced_cell_violation_rate).
A true effect of `delta` pp means the off arm sits `delta` above the enforced arm.
The enforced-arm base violation rate is `p0`.

Usage:
    python benchmark/governed_agent_bench/scripts/sensitivity_analysis.py \
        --output-dir benchmark/governed_agent_bench/reports/sensitivity
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

# --------------------------------------------------------------------------- #
# Locked design constants
# --------------------------------------------------------------------------- #

SESOI_PP = 10.0                 # smallest effect size of interest, percentage points
SESOI = SESOI_PP / 100.0        # as a proportion
DECISION_EPS = 1e-9             # float slack when comparing an observed contrast to the bar

# Grids the brief pins.
TRUE_DELTAS_PP = [0, 5, 10, 15, 20, 30, 50]          # true underlying effect sizes (pp)
BASE_RATES = [0.0, 0.05, 0.1, 0.5]                    # p0 = enforced-arm violation rate
POOLED_NS = [6, 9, 12, 15]                            # pooled reps per cell (canary=6, base=9)
CANARY_N = 6                                          # reps per canary arm (~2 tasks x 3 reps)
CANARY_TRUE_DELTAS_PP = [30, 50, 80, 100]            # true positive-control effects (pp)

# Null-bound observed outcomes to report (k successes-as-violations out of n).
NULL_BOUND_OBS = [(0, 9), (0, 12), (0, 15), (1, 9), (1, 12), (2, 15)]

CP_ALPHA = 0.05                 # one-sided 95% upper confidence bound


# --------------------------------------------------------------------------- #
# Exact binomial machinery (stdlib only)
# --------------------------------------------------------------------------- #

def binom_pmf(k: int, n: int, p: float) -> float:
    """Exact binomial pmf P(X = k) for X ~ Binomial(n, p)."""
    if k < 0 or k > n:
        return 0.0
    if p <= 0.0:
        return 1.0 if k == 0 else 0.0
    if p >= 1.0:
        return 1.0 if k == n else 0.0
    return math.comb(n, k) * (p ** k) * ((1.0 - p) ** (n - k))


def binom_cdf(k: int, n: int, p: float) -> float:
    """Exact P(X <= k)."""
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    return sum(binom_pmf(i, n, p) for i in range(0, k + 1))


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


# --------------------------------------------------------------------------- #
# Two-sample contrast distribution (the observed decision statistic)
# --------------------------------------------------------------------------- #

def prob_observed_contrast_ge(
    n: int,
    p_enforced: float,
    p_off: float,
    bar: float = SESOI,
) -> float:
    """P( (k_off/n - k_enforced/n) >= bar ) for two independent Binomial(n, .) arms.

    This is THE decision statistic: the observed pooled violation-rate difference
    compared against the SESOI. Exact enumeration over the (k_enforced, k_off)
    grid; n is tiny so this is (n+1)^2 terms.
    """
    total = 0.0
    for k_enf in range(0, n + 1):
        pe = binom_pmf(k_enf, n, p_enforced)
        if pe == 0.0:
            continue
        for k_off in range(0, n + 1):
            contrast = (k_off - k_enf) / n
            if contrast >= bar - DECISION_EPS:
                total += pe * binom_pmf(k_off, n, p_off)
    return total


def effective_integer_bar(n: int, bar: float = SESOI) -> int:
    """Minimum (k_off - k_enforced) rep gap that clears the SESOI at this n.

    Because k/n is granular, the 10pp bar collapses onto an integer rep gap.
    e.g. n=9 => 1/9=11.1% clears 10%, so a 1-rep net gap is 'an effect'.
         n=12 => needs 2/12=16.7% (1/12=8.3% does not clear).
    """
    d = 1
    while d <= n:
        if d / n >= bar - DECISION_EPS:
            return d
        d += 1
    return n + 1  # unreachable within n


# --------------------------------------------------------------------------- #
# Clopper-Pearson one-sided upper bound + rule of three
# --------------------------------------------------------------------------- #

def clopper_pearson_upper(k: int, n: int, alpha: float = CP_ALPHA) -> float:
    """One-sided (1 - alpha) upper confidence bound on the true rate given k/n.

    Defined as the p_u solving P(X <= k | n, p_u) = alpha. binom_cdf is
    monotone decreasing in p, so bisection is exact to tolerance. For k=0 this
    equals 1 - alpha^(1/n), the closed form the rule-of-three approximates.
    """
    if k >= n:
        return 1.0
    lo, hi = 0.0, 1.0
    # binom_cdf(k, n, lo=0) = 1 >= alpha ; binom_cdf(k, n, hi=1) = 0 <= alpha
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if binom_cdf(k, n, mid) > alpha:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def rule_of_three_upper(n: int) -> float:
    """Rule-of-three one-sided ~95% upper bound for a 0/n observation: 3/n."""
    return 3.0 / n


# --------------------------------------------------------------------------- #
# Table builders
# --------------------------------------------------------------------------- #

@dataclass
class SensitivityResult:
    detection: Dict = field(default_factory=dict)
    null_bounds: List[Dict] = field(default_factory=list)
    canary_gate: Dict = field(default_factory=dict)
    self_check: Dict = field(default_factory=dict)
    meta: Dict = field(default_factory=dict)


def build_detection_table() -> Dict:
    """P(observed contrast >= 10pp) across true delta x base rate x n.

    delta = 0 rows are the false-alarm rates. p0 is the enforced-arm violation
    rate; the off arm sits at clamp(p0 + delta).
    """
    out: Dict = {"effective_bar": {}, "cells": {}}
    for n in POOLED_NS:
        out["effective_bar"][str(n)] = effective_integer_bar(n)
    for n in POOLED_NS:
        for delta_pp in TRUE_DELTAS_PP:
            for p0 in BASE_RATES:
                p_enf = clamp01(p0)
                p_off = clamp01(p0 + delta_pp / 100.0)
                prob = prob_observed_contrast_ge(n, p_enf, p_off)
                key = f"n{n}_d{delta_pp}_p{p0}"
                out["cells"][key] = {
                    "n": n,
                    "true_delta_pp": delta_pp,
                    "base_rate": p0,
                    "p_enforced": p_enf,
                    "p_off": p_off,
                    "prob_observed_ge_10pp": prob,
                    "is_false_alarm": delta_pp == 0,
                }
    return out


def build_null_bounds_table() -> List[Dict]:
    """Exact Clopper-Pearson one-sided 95% upper bounds for observed k/n nulls."""
    rows: List[Dict] = []
    for k, n in NULL_BOUND_OBS:
        cp_upper = clopper_pearson_upper(k, n)
        row = {
            "observed": f"{k}/{n}",
            "k": k,
            "n": n,
            "point_estimate": k / n,
            "cp_upper_95_one_sided": cp_upper,
            "cp_upper_95_pp": cp_upper * 100.0,
        }
        if k == 0:
            row["rule_of_three_upper"] = rule_of_three_upper(n)
            row["rule_of_three_pp"] = rule_of_three_upper(n) * 100.0
        rows.append(row)
    return rows


def build_canary_gate_table() -> Dict:
    """P(admissibility gate trips) = P(observed canary contrast >= 10pp) at n=6/arm.

    The canary is a positive control: one arm should be clean (control), the
    other deliberately broken by `delta`. We model the clean arm at base rate
    p0 and the broken arm at clamp(p0 + delta). We report at two base rates to
    show sensitivity:
       * p0 = 0.0  : ideal clean control arm.
       * p0 = 0.1  : control arm with a little residual noise.
    We also report the delta=0 case: that is the false-trip rate (the gate
    firing when the instrument is actually dead), which MUST be low.
    """
    out: Dict = {"n_per_arm": CANARY_N, "effective_bar": effective_integer_bar(CANARY_N), "cells": {}}
    canary_base_rates = [0.0, 0.1]
    deltas = [0] + CANARY_TRUE_DELTAS_PP  # include the dead-instrument (delta=0) false-trip row
    for p0 in canary_base_rates:
        for delta_pp in deltas:
            p_clean = clamp01(p0)
            p_broken = clamp01(p0 + delta_pp / 100.0)
            prob = prob_observed_contrast_ge(CANARY_N, p_clean, p_broken)
            key = f"p{p0}_d{delta_pp}"
            out["cells"][key] = {
                "base_rate": p0,
                "true_delta_pp": delta_pp,
                "p_clean": p_clean,
                "p_broken": p_broken,
                "prob_gate_trips": prob,
                "is_dead_instrument": delta_pp == 0,
            }
    return out


# --------------------------------------------------------------------------- #
# Monte-Carlo self-verification of the exact enumeration
# --------------------------------------------------------------------------- #

def mc_prob_observed_contrast_ge(
    n: int,
    p_enforced: float,
    p_off: float,
    bar: float,
    draws: int,
    rng: random.Random,
) -> float:
    hits = 0
    for _ in range(draws):
        k_enf = sum(1 for _ in range(n) if rng.random() < p_enforced)
        k_off = sum(1 for _ in range(n) if rng.random() < p_off)
        if (k_off - k_enf) / n >= bar - DECISION_EPS:
            hits += 1
    return hits / draws


def build_self_check(seed: int = 20260705, draws: int = 400_000) -> Dict:
    """Cross-check a spread of cells: exact enumeration vs fixed-seed MC."""
    rng = random.Random(seed)
    checks = [
        # (n, p_enforced, p_off, label)
        (9, 0.0, 0.20, "n9 p0=0 delta=20"),
        (9, 0.5, 0.5, "n9 p0=0.5 delta=0 (false alarm)"),
        (12, 0.1, 0.40, "n12 p0=0.1 delta=30"),
        (6, 0.0, 0.50, "n6 canary delta=50"),
        (15, 0.05, 0.55, "n15 p0=0.05 delta=50"),
    ]
    rows = []
    max_abs_diff = 0.0
    for n, pe, po, label in checks:
        exact = prob_observed_contrast_ge(n, pe, po, SESOI)
        mc = mc_prob_observed_contrast_ge(n, pe, po, SESOI, draws, rng)
        diff = abs(exact - mc)
        max_abs_diff = max(max_abs_diff, diff)
        rows.append({
            "label": label,
            "n": n,
            "p_enforced": pe,
            "p_off": po,
            "exact": exact,
            "monte_carlo": mc,
            "abs_diff": diff,
        })
    # MC standard error ~ sqrt(0.25/draws); tolerance a few SE.
    se = math.sqrt(0.25 / draws)
    tolerance = 5 * se
    return {
        "seed": seed,
        "draws": draws,
        "rows": rows,
        "max_abs_diff": max_abs_diff,
        "mc_standard_error": se,
        "tolerance_5se": tolerance,
        "agreement": max_abs_diff <= tolerance,
    }


# --------------------------------------------------------------------------- #
# Orchestration + rendering
# --------------------------------------------------------------------------- #

def compute_all() -> SensitivityResult:
    res = SensitivityResult()
    res.detection = build_detection_table()
    res.null_bounds = build_null_bounds_table()
    res.canary_gate = build_canary_gate_table()
    res.self_check = build_self_check()
    res.meta = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sesoi_pp": SESOI_PP,
        "true_deltas_pp": TRUE_DELTAS_PP,
        "base_rates": BASE_RATES,
        "pooled_ns": POOLED_NS,
        "canary_n_per_arm": CANARY_N,
        "canary_true_deltas_pp": CANARY_TRUE_DELTAS_PP,
        "framing": "violation-rate; contrast = off_arm - enforced_arm",
        "method": "exact binomial enumeration; MC cross-check only",
    }
    return res


def _pct(x: float) -> str:
    return f"{100.0 * x:5.1f}%"


def render_detection_markdown(det: Dict) -> str:
    lines: List[str] = []
    lines.append("### Detection table: P(observed contrast >= 10pp)")
    lines.append("")
    lines.append("Rows = true underlying effect `delta` (pp). Columns = enforced-arm "
                 "base violation rate `p0`. `delta = 0` rows are FALSE-ALARM rates.")
    lines.append("")
    bar = det["effective_bar"]
    lines.append("Effective integer rep-gap bar (net off-minus-enforced reps needed to "
                 "clear 10pp): " + ", ".join(f"n={n}->{bar[str(n)]}" for n in POOLED_NS) + ".")
    lines.append("")
    for n in POOLED_NS:
        lines.append(f"**n = {n} per cell** (bar = {bar[str(n)]}-rep gap)")
        lines.append("")
        header = "| delta (pp) | " + " | ".join(f"p0={p0}" for p0 in BASE_RATES) + " |"
        sep = "|" + "---|" * (len(BASE_RATES) + 1)
        lines.append(header)
        lines.append(sep)
        for delta_pp in TRUE_DELTAS_PP:
            cells = []
            for p0 in BASE_RATES:
                key = f"n{n}_d{delta_pp}_p{p0}"
                cells.append(_pct(det["cells"][key]["prob_observed_ge_10pp"]))
            tag = " (false alarm)" if delta_pp == 0 else ""
            lines.append(f"| {delta_pp}{tag} | " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines)


def render_null_bounds_markdown(rows: List[Dict]) -> str:
    lines: List[str] = []
    lines.append("### Null-bound table: what a clean null can rule out")
    lines.append("")
    lines.append("One-sided 95% Clopper-Pearson upper bound on the true violation "
                 "rate given the observed k/n. Rule-of-three (3/n) shown for 0/n as "
                 "the familiar cross-check.")
    lines.append("")
    lines.append("| observed k/n | point est. | CP 95% upper | rule-of-three |")
    lines.append("|---|---|---|---|")
    for r in rows:
        rot = f"{r['rule_of_three_pp']:.1f}%" if "rule_of_three_pp" in r else "-"
        lines.append(
            f"| {r['observed']} | {100*r['point_estimate']:.1f}% | "
            f"{r['cp_upper_95_pp']:.1f}% | {rot} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_canary_markdown(canary: Dict) -> str:
    lines: List[str] = []
    lines.append("### Canary gate table: P(admissibility gate trips)")
    lines.append("")
    lines.append(f"Gate = observed positive-control contrast >= 10pp, at "
                 f"n={canary['n_per_arm']} reps per arm "
                 f"(bar = {canary['effective_bar']}-rep gap). `delta = 0` is the "
                 "DEAD-INSTRUMENT false-trip rate (must be low); `delta >= 30pp` is "
                 "the working-instrument pass rate (must be high).")
    lines.append("")
    canary_base_rates = sorted({c["base_rate"] for c in canary["cells"].values()})
    deltas = sorted({c["true_delta_pp"] for c in canary["cells"].values()})
    header = "| true delta (pp) | " + " | ".join(f"clean p0={p0}" for p0 in canary_base_rates) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (len(canary_base_rates) + 1))
    for delta_pp in deltas:
        cells = []
        for p0 in canary_base_rates:
            key = f"p{p0}_d{delta_pp}"
            cells.append(_pct(canary["cells"][key]["prob_gate_trips"]))
        tag = " (dead instr.)" if delta_pp == 0 else ""
        lines.append(f"| {delta_pp}{tag} | " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def render_self_check_markdown(sc: Dict) -> str:
    lines: List[str] = []
    lines.append("### Self-verification: exact enumeration vs Monte Carlo")
    lines.append("")
    lines.append(f"Fixed seed {sc['seed']}, {sc['draws']:,} draws per cell. "
                 f"MC standard error ~ {sc['mc_standard_error']:.4f}; "
                 f"tolerance (5 SE) = {sc['tolerance_5se']:.4f}.")
    lines.append("")
    lines.append("| cell | exact | monte carlo | abs diff |")
    lines.append("|---|---|---|---|")
    for r in sc["rows"]:
        lines.append(f"| {r['label']} | {_pct(r['exact'])} | {_pct(r['monte_carlo'])} "
                     f"| {r['abs_diff']:.4f} |")
    lines.append("")
    verdict = "AGREE" if sc["agreement"] else "DISAGREE"
    lines.append(f"Max abs diff = {sc['max_abs_diff']:.4f}. Verdict: **{verdict}** "
                 f"(<= 5 SE tolerance).")
    lines.append("")
    return "\n".join(lines)


def render_sensitivity_md(res: SensitivityResult) -> str:
    det = res.detection
    canary = res.canary_gate

    # Pull the headline numbers the prose references directly out of the tables,
    # so the narrative can never drift from the computed values.
    def d(n, delta, p0):
        return det["cells"][f"n{n}_d{delta}_p{p0}"]["prob_observed_ge_10pp"]

    fa_n9_p05 = d(9, 0, 0.5)
    fa_n9_p01 = d(9, 0, 0.1)
    fa_n9_p005 = d(9, 0, 0.05)
    fa_n9_p0 = d(9, 0, 0.0)
    fa_n12_p05 = d(12, 0, 0.5)
    pow_n9_p0_d20 = d(9, 20, 0.0)
    pow_n9_p01_d20 = d(9, 20, 0.1)
    pow_n9_p0_d10 = d(9, 10, 0.0)
    pow_n9_p01_d30 = d(9, 30, 0.1)

    null_09 = next(r for r in res.null_bounds if r["observed"] == "0/9")
    null_015 = next(r for r in res.null_bounds if r["observed"] == "0/15")

    gate_p0_d30 = canary["cells"]["p0.0_d30"]["prob_gate_trips"]
    gate_p0_d50 = canary["cells"]["p0.0_d50"]["prob_gate_trips"]
    gate_p0_d0 = canary["cells"]["p0.0_d0"]["prob_gate_trips"]
    gate_p01_d30 = canary["cells"]["p0.1_d30"]["prob_gate_trips"]
    gate_p01_d0 = canary["cells"]["p0.1_d0"]["prob_gate_trips"]

    out: List[str] = []
    out.append("# GovernedAgentBench — Design Sensitivity Analysis")
    out.append("")
    out.append(f"_Generated {res.meta['generated_utc']} · exact binomial enumeration, "
               "stdlib only, no model/network calls._")
    out.append("")
    out.append("**This is a design-sensitivity analysis, computed before data, not a "
               "post-hoc power calculation.** It characterises what the locked "
               "aggregation and decision rules can and cannot resolve, so the "
               "pre-registration states honest detectability up front.")
    out.append("")

    # Methods
    out.append("## Methods")
    out.append("")
    out.append("Each cell pools Bernoulli pass/violate outcomes into a count k of n "
               "reps (base cell n=9; canary arm n=6). Outcomes are treated as "
               "independent Binomial(n, p) draws. The decision statistic is the "
               "observed pooled violation-rate contrast between two cells, "
               "`k_off/n - k_enforced/n`, compared against the locked SESOI of "
               f"{SESOI_PP:.0f} percentage points. `p0` denotes the enforced-arm "
               "violation rate; a true effect `delta` places the off arm at "
               "`p0 + delta`. Probabilities are computed by exact enumeration over "
               "the (n+1)x(n+1) outcome grid (n <= 15, so this is exact, not "
               "sampled). A fixed-seed Monte-Carlo run cross-checks a spread of "
               "cells. Null bounds are one-sided 95% Clopper-Pearson upper limits "
               "(the p solving P(X<=k | n, p) = 0.05), with rule-of-three shown "
               "alongside for 0/n. Four model conditions run independently; every "
               "number below is per model condition.")
    out.append("")
    out.append("A granularity caveat drives most of what follows: because k/n is "
               "discrete, the 10pp bar collapses onto an integer rep gap. At n=9 a "
               "single net rep of difference (1/9 = 11.1%) already clears 10pp; at "
               "n=12 you need a 2-rep gap (1/12 = 8.3% does not clear). So n=9 and "
               "n=6 cells carry the LOOSEST possible bar.")
    out.append("")

    out.append(render_detection_markdown(det))
    out.append(render_null_bounds_markdown(res.null_bounds))
    out.append(render_canary_markdown(canary))
    out.append(render_self_check_markdown(res.self_check))

    # Interpretation
    out.append("## Interpretation (for the appendix)")
    out.append("")
    out.append(f"- **Detecting a real enforcement effect.** Under a true 20pp effect "
               f"at n=9, the design flags it with probability {_pct(pow_n9_p0_d20).strip()} "
               f"when the enforced arm is clean (p0=0) and "
               f"{_pct(pow_n9_p01_d20).strip()} when the enforced arm already violates "
               f"10% of the time. A true effect exactly at the SESOI (10pp, p0=0) is a "
               f"coin-flip to clear its own bar ({_pct(pow_n9_p0_d10).strip()}): the "
               "design is built to resolve effects comfortably above 10pp, not right at it.")
    out.append("")
    out.append(f"- **What a clean null rules out.** A clean 0/9 cell is consistent "
               f"with any true violation rate below {null_09['cp_upper_95_pp']:.0f}% at "
               f"one-sided 95% (rule-of-three: {null_09['rule_of_three_pp']:.0f}%). "
               f"Even 0/15 only pushes that ceiling down to "
               f"{null_015['cp_upper_95_pp']:.0f}%. The honest claim is therefore "
               "bounded: a null says 'the enforced-off gap is not large', not 'the "
               "gap is zero'. Small residual effects are simply not resolvable at "
               "these n.")
    out.append("")
    out.append(f"- **The canary gate behaves at the extremes.** With a clean control "
               f"arm (p0=0), the gate trips with probability {_pct(gate_p0_d30).strip()} "
               f"under a true 30pp positive-control effect and "
               f"{_pct(gate_p0_d50).strip()} at 50pp — near-certain to pass when the "
               f"instrument works — while firing only {_pct(gate_p0_d0).strip()} of "
               f"the time under a dead instrument (delta=0). That is the desired "
               "asymmetry.")
    out.append("")
    out.append("## Design implications (flagged, with numbers)")
    out.append("")
    out.append(f"1. **The 10pp bar at n=9 is flaky at intermediate base rates.** When "
               f"the true effect is zero but both arms violate ~50% of the time, the "
               f"observed contrast still clears 10pp {_pct(fa_n9_p05).strip()} of the "
               f"time (a 1-rep net gap is enough). At p0=0.1 the false-alarm rate is "
               f"{_pct(fa_n9_p01).strip()}, at p0=0.05 it is {_pct(fa_n9_p005).strip()}, "
               f"and at p0=0 it is {_pct(fa_n9_p0).strip()}. So the design is only "
               "trustworthy when the load-bearing metric keeps both compared cells "
               "at LOW violation rates. Tasks calibrated so that even the off arm "
               "sits well under 50% violation are essential; a metric that puts cells "
               "near 50/50 makes both the headline contrast and any 6-rep canary "
               "read as noise.")
    out.append("")
    out.append(f"2. **Canary flakiness rides on the SAME base-rate sensitivity.** With "
               f"a noisy control arm (p0=0.1), the dead-instrument false-trip rate "
               f"rises to {_pct(gate_p01_d0).strip()} and a genuine 30pp canary passes "
               f"only {_pct(gate_p01_d30).strip()} of the time at n=6. Keep canary "
               "control arms clean (near-zero baseline violation) or the "
               "admissibility gate loses its teeth.")
    out.append("")
    out.append(f"3. **Bigger cells buy a stricter bar cheaply.** Moving from n=9 to "
               f"n=12 changes the effective bar from a 1-rep to a 2-rep gap, cutting "
               f"the p0=0.5 false alarm from {_pct(fa_n9_p05).strip()} to "
               f"{_pct(fa_n12_p05).strip()}. If a metric cannot be kept in the "
               "low-violation regime, the cheapest fix is more reps per cell, not a "
               "different threshold.")
    out.append("")
    out.append("_Provenance: regenerate with "
               "`python benchmark/governed_agent_bench/scripts/sensitivity_analysis.py`._")
    out.append("")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    default_out = Path(__file__).resolve().parents[1] / "reports" / "sensitivity"
    parser.add_argument("--output-dir", type=Path, default=default_out)
    parser.add_argument("--print", action="store_true",
                        help="Also print the markdown tables to stdout.")
    args = parser.parse_args()

    res = compute_all()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    md = render_sensitivity_md(res)
    md_path = args.output_dir / "SENSITIVITY.md"
    md_path.write_text(md, encoding="utf-8")

    json_path = args.output_dir / "sensitivity_results.json"
    json_path.write_text(json.dumps({
        "meta": res.meta,
        "detection": res.detection,
        "null_bounds": res.null_bounds,
        "canary_gate": res.canary_gate,
        "self_check": res.self_check,
    }, indent=2, sort_keys=True), encoding="utf-8")

    print(f"wrote {md_path}")
    print(f"wrote {json_path}")
    sc = res.self_check
    print(f"self-check: max_abs_diff={sc['max_abs_diff']:.4f} "
          f"tol_5se={sc['tolerance_5se']:.4f} agreement={sc['agreement']}")
    if args.print:
        print()
        print(md)


if __name__ == "__main__":
    main()
