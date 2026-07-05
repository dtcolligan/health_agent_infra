"""Tests for the design sensitivity analysis.

These pin the exact-enumeration math against closed-form values and guard the
boundary cases (p0=0, dead instrument, granularity of the 10pp bar). No network,
no model calls; pure arithmetic.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "governed_agent_bench"
    / "scripts"
    / "sensitivity_analysis.py"
)
_spec = importlib.util.spec_from_file_location("sensitivity_analysis", _MODULE_PATH)
assert _spec and _spec.loader
sa = importlib.util.module_from_spec(_spec)
# Register before exec so dataclass introspection (which looks the module up in
# sys.modules via cls.__module__) works under Python 3.12+.
sys.modules[_spec.name] = sa
_spec.loader.exec_module(sa)


def approx(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


# --------------------------------------------------------------------------- #
# Binomial primitives
# --------------------------------------------------------------------------- #

def test_binom_pmf_boundaries():
    assert approx(sa.binom_pmf(0, 6, 0.0), 1.0)
    assert approx(sa.binom_pmf(1, 6, 0.0), 0.0)
    assert approx(sa.binom_pmf(6, 6, 1.0), 1.0)
    assert approx(sa.binom_pmf(0, 6, 1.0), 0.0)


def test_binom_pmf_sums_to_one():
    for n in (6, 9, 12, 15):
        for p in (0.0, 0.05, 0.3, 0.5, 1.0):
            total = sum(sa.binom_pmf(k, n, p) for k in range(n + 1))
            assert approx(total, 1.0, tol=1e-9)


def test_binom_cdf_monotone_decreasing_in_p():
    prev = 1.0
    for p in (0.0, 0.1, 0.2, 0.5, 0.9):
        cur = sa.binom_cdf(3, 9, p)
        assert cur <= prev + 1e-12
        prev = cur


# --------------------------------------------------------------------------- #
# Effective integer bar (granularity of the 10pp threshold)
# --------------------------------------------------------------------------- #

def test_effective_integer_bar():
    # 1/6=16.7% clears 10 -> 1 ; 1/9=11.1% clears -> 1 ;
    # 1/12=8.3% does NOT clear, 2/12=16.7% does -> 2 ; 2/15=13.3% -> 2
    assert sa.effective_integer_bar(6) == 1
    assert sa.effective_integer_bar(9) == 1
    assert sa.effective_integer_bar(12) == 2
    assert sa.effective_integer_bar(15) == 2


# --------------------------------------------------------------------------- #
# Two-sample contrast distribution
# --------------------------------------------------------------------------- #

def test_contrast_zero_at_clean_null():
    # p0=0 both arms => always 0 violations => contrast never clears 10pp.
    assert approx(sa.prob_observed_contrast_ge(9, 0.0, 0.0), 0.0)


def test_false_alarm_p05_n9_matches_closed_form():
    # Two Binom(9,0.5): P(k_off - k_enf >= 1) = (1 - P(tie))/2.
    # P(tie) = C(18,9)/4^9.
    p_tie = math.comb(18, 9) / (4 ** 9)
    expected = (1.0 - p_tie) / 2.0
    got = sa.prob_observed_contrast_ge(9, 0.5, 0.5)
    assert approx(got, expected, tol=1e-9)


def test_canary_clean_control_closed_form():
    # p_clean=0 => enforced arm always 0 ; gate trips iff k_broken >= 1.
    # P(k>=1 | Binom(6, 0.5)) = 1 - 0.5^6.
    got = sa.prob_observed_contrast_ge(6, 0.0, 0.5)
    assert approx(got, 1.0 - 0.5 ** 6, tol=1e-9)


def test_detection_monotone_in_true_delta():
    # More true effect never lowers detection probability (fixed n, p0=0).
    probs = [sa.prob_observed_contrast_ge(9, 0.0, d / 100.0) for d in (0, 5, 10, 20, 30, 50)]
    assert all(probs[i] <= probs[i + 1] + 1e-12 for i in range(len(probs) - 1))


# --------------------------------------------------------------------------- #
# Clopper-Pearson / rule of three
# --------------------------------------------------------------------------- #

def test_cp_upper_zero_closed_form():
    # k=0: one-sided (1-alpha) upper = 1 - alpha^(1/n).
    for n in (9, 12, 15):
        expected = 1.0 - (0.05 ** (1.0 / n))
        assert approx(sa.clopper_pearson_upper(0, n), expected, tol=1e-6)


def test_cp_upper_recovers_alpha():
    # By definition P(X <= k | n, p_upper) == alpha.
    for k, n in ((0, 9), (1, 9), (2, 15)):
        p_u = sa.clopper_pearson_upper(k, n)
        assert approx(sa.binom_cdf(k, n, p_u), 0.05, tol=1e-6)


def test_rule_of_three():
    assert approx(sa.rule_of_three_upper(9), 3.0 / 9.0)


# --------------------------------------------------------------------------- #
# End-to-end build + self-check
# --------------------------------------------------------------------------- #

def test_self_check_agrees():
    sc = sa.build_self_check(draws=100_000)
    assert sc["agreement"], sc


def test_compute_all_shapes():
    res = sa.compute_all()
    # detection: one cell per (n, delta, p0)
    expected = len(sa.POOLED_NS) * len(sa.TRUE_DELTAS_PP) * len(sa.BASE_RATES)
    assert len(res.detection["cells"]) == expected
    # false-alarm at p0=0 is exactly zero everywhere
    for n in sa.POOLED_NS:
        assert approx(res.detection["cells"][f"n{n}_d0_p0.0"]["prob_observed_ge_10pp"], 0.0)
    # dead-instrument clean canary never trips
    assert approx(res.canary_gate["cells"]["p0.0_d0"]["prob_gate_trips"], 0.0)
    # a strong canary is near-certain to pass
    assert res.canary_gate["cells"]["p0.0_d50"]["prob_gate_trips"] > 0.95


def test_render_markdown_nonempty():
    res = sa.compute_all()
    md = sa.render_sensitivity_md(res)
    assert "Design Sensitivity Analysis" in md
    assert "Detection table" in md
    assert "Null-bound table" in md
    assert "Canary gate table" in md
