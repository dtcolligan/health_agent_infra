"""Tests for the permutation inference (analysis.permutation).

The critical properties: H1 recovers a planted capability gate and is exactly 1.0
under a symmetric null; H2 recovers a planted interaction AND is provably blind to
a pure salience main effect (the design property that lets it isolate the
interaction); both are reproducible under a fixed seed.
"""

from __future__ import annotations

from governed_agent_bench.analysis.frame import CAPABLE, WEAK, AnalysisFrame, AnalysisRow
from governed_agent_bench.analysis.permutation import (
    permutation_cellB_band,
    permutation_interaction,
    permutation_report,
)


def _cellB_rows(band, n, k_safe, *, salience=0, model_id=None):
    mid = model_id or f"{band}_m{salience}"
    return [
        AnalysisRow(
            scenario_id=f"scn{salience}",
            task_id=f"t{salience}",
            model_id=mid,
            model_family=f"{band}_fam",
            provider="p",
            capability_band=band,
            told=True,
            enforced=False,
            salience=salience,
            safe=(i < k_safe),
        )
        for i in range(n)
    ]


# --- H1: the capability gate ------------------------------------------------ #


def test_h1_recovers_planted_gate():
    frame = AnalysisFrame(_cellB_rows(CAPABLE, 12, 12) + _cellB_rows(WEAK, 12, 0))
    res = permutation_cellB_band(frame, n_perm=2000, seed=0)
    assert res.observed == 1.0
    assert res.p_one_sided_greater < 0.01
    assert res.p_two_sided < 0.02


def test_h1_symmetric_null_is_p_one():
    # Balanced, identical bands => observed delta exactly 0 => p_two == 1.0.
    frame = AnalysisFrame(_cellB_rows(CAPABLE, 10, 5) + _cellB_rows(WEAK, 10, 5))
    res = permutation_cellB_band(frame, n_perm=1000, seed=0)
    assert res.observed == 0.0
    assert res.p_two_sided == 1.0


def test_h1_reproducible_under_seed():
    frame = AnalysisFrame(_cellB_rows(CAPABLE, 8, 6) + _cellB_rows(WEAK, 8, 2))
    a = permutation_cellB_band(frame, n_perm=1500, seed=7)
    b = permutation_cellB_band(frame, n_perm=1500, seed=7)
    assert a.p_two_sided == b.p_two_sided
    assert a.observed == b.observed


# --- H2: the capability x salience interaction ------------------------------ #


def _interaction_frame():
    # Gap grows with salience: level 0 gap = 0, level 1 gap = 0.8.
    rows = []
    rows += _cellB_rows(CAPABLE, 10, 5, salience=0, model_id="cap_lo")
    rows += _cellB_rows(WEAK, 10, 5, salience=0, model_id="weak_lo")
    rows += _cellB_rows(CAPABLE, 10, 9, salience=1, model_id="cap_hi")
    rows += _cellB_rows(WEAK, 10, 1, salience=1, model_id="weak_hi")
    return AnalysisFrame(rows)


def _main_effect_only_frame():
    # Both bands improve with salience by the SAME amount => gap flat => no
    # interaction, only a salience main effect (+ a band main effect).
    rows = []
    rows += _cellB_rows(CAPABLE, 10, 5, salience=0, model_id="cap_lo")  # 0.5
    rows += _cellB_rows(WEAK, 10, 4, salience=0, model_id="weak_lo")    # 0.4
    rows += _cellB_rows(CAPABLE, 10, 9, salience=1, model_id="cap_hi")  # 0.9
    rows += _cellB_rows(WEAK, 10, 8, salience=1, model_id="weak_hi")    # 0.8
    return AnalysisFrame(rows)  # gap = 0.1 at both levels


def test_h2_recovers_planted_interaction():
    res = permutation_interaction(_interaction_frame(), n_perm=3000, seed=0)
    assert res.observed > 0.5  # positive slope of the gap
    assert res.p_two_sided < 0.05


def test_h2_blind_to_pure_salience_main_effect():
    # The key property: a salience main effect with a FLAT gap => slope exactly
    # 0 => p_two exactly 1.0. The statistic does not fire on a main effect.
    res = permutation_interaction(_main_effect_only_frame(), n_perm=1000, seed=0)
    assert res.observed == 0.0
    assert res.p_two_sided == 1.0


def test_h2_reproducible_under_seed():
    frame = _interaction_frame()
    a = permutation_interaction(frame, n_perm=2000, seed=3)
    b = permutation_interaction(frame, n_perm=2000, seed=3)
    assert a.p_two_sided == b.p_two_sided


def test_report_skips_h2_without_two_salience_levels():
    frame = AnalysisFrame(_cellB_rows(CAPABLE, 6, 6) + _cellB_rows(WEAK, 6, 0))
    report = permutation_report(frame, n_perm=500, seed=0)
    assert report["H1_cellB_capability_gate"]["observed"] == 1.0
    assert report["H2_capability_x_salience"].get("skipped") is True
