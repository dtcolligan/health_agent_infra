"""Tests for the descriptive primary (analysis.descriptive)."""

from __future__ import annotations

import json

import pytest

from governed_agent_bench.analysis.descriptive import (
    cellB_band_contrast,
    descriptive_report,
    newcombe_diff_ci,
    rate_ci,
    wilson_interval,
)
from governed_agent_bench.analysis.frame import CAPABLE, WEAK, AnalysisFrame, AnalysisRow
from governed_agent_bench.results.cell_contrasts import _newcombe_ci
from governed_agent_bench.results.exact_tests import clopper_pearson


def _row(**kw) -> AnalysisRow:
    base = dict(
        scenario_id="s",
        task_id="t",
        model_id="m",
        model_family="fam",
        provider="p",
        capability_band=CAPABLE,
        told=True,
        enforced=False,
        salience=0,
        safe=True,
    )
    base.update(kw)
    return AnalysisRow(**base)


def _cellB(band, n, k_safe, *, salience=0, model_id=None):
    """n cell-B rows for a band, k_safe of them safe."""

    mid = model_id or f"{band}_m"
    return [
        _row(
            capability_band=band,
            model_id=mid,
            model_family=f"{band}_fam",
            told=True,
            enforced=False,
            salience=salience,
            safe=(i < k_safe),
        )
        for i in range(n)
    ]


def test_rate_ci_reuses_clopper_pearson():
    frame = AnalysisFrame(_cellB(CAPABLE, 8, 8))
    r = rate_ci(frame)
    assert (r.k, r.n) == (8, 8)
    assert (r.ci95_low, r.ci95_high) == pytest.approx(clopper_pearson(8, 8))


def test_saturated_cell_interval_is_not_degenerate():
    # 0/8 and 8/8 must produce honest non-point intervals.
    lo = rate_ci(AnalysisFrame(_cellB(WEAK, 8, 0)))
    hi = rate_ci(AnalysisFrame(_cellB(CAPABLE, 8, 8)))
    assert lo.ci95_low == 0.0 and lo.ci95_high > 0.2
    assert hi.ci95_high == 1.0 and hi.ci95_low < 0.8


def test_newcombe_matches_frozen_cell_contrasts():
    # Cross-check our reimplementation against the released module (in pp).
    for (k1, n1), (k2, n2) in [((8, 8), (0, 8)), ((3, 10), (5, 12)), ((5, 5), (0, 5))]:
        ours = newcombe_diff_ci(k1, n1, k2, n2)
        theirs = _newcombe_ci({"passes": k1, "n": n1}, {"passes": k2, "n": n2})
        assert [100.0 * ours[0], 100.0 * ours[1]] == pytest.approx(theirs)


def test_wilson_interval_bounds():
    lo, hi = wilson_interval(0, 10)
    assert lo == 0.0 and 0.0 < hi < 1.0
    lo, hi = wilson_interval(10, 10)
    assert hi == pytest.approx(1.0) and 0.0 < lo < 1.0


def test_headline_contrast_direction_and_sign():
    # Capable all safe, weak all unsafe in cell B => delta = +1.0.
    frame = AnalysisFrame(_cellB(CAPABLE, 6, 6) + _cellB(WEAK, 6, 0))
    c = cellB_band_contrast(frame)
    assert c.delta == pytest.approx(1.0)
    assert c.minuend.rate == 1.0  # capable
    assert c.subtrahend.rate == 0.0  # weak
    assert c.ci95_low > 0.0  # excludes zero: real gap


def test_report_is_json_serialisable_and_shaped():
    rows = (
        _cellB(CAPABLE, 4, 4, salience=0)
        + _cellB(WEAK, 4, 1, salience=0)
        + _cellB(CAPABLE, 4, 4, salience=1)
        + _cellB(WEAK, 4, 3, salience=1)
    )
    report = descriptive_report(AnalysisFrame(rows))
    # Round-trips through JSON (no numpy/dataclass leakage).
    json.dumps(report)
    assert report["headline_cellB_band_contrast"]["delta"] > 0
    levels = [entry["salience"] for entry in report["salience_breakdown"]]
    assert levels == [0, 1]
    # Gap should shrink as salience rises (weak improves 1/4 -> 3/4).
    g0 = report["salience_breakdown"][0]["contrast"]["delta"]
    g1 = report["salience_breakdown"][1]["contrast"]["delta"]
    assert g0 > g1


def test_headline_none_when_a_band_absent():
    report = descriptive_report(AnalysisFrame(_cellB(CAPABLE, 4, 4)))
    assert report["headline_cellB_band_contrast"] is None
