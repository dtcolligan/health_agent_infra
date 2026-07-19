"""Tests for the tidy-row contract (analysis.frame)."""

from __future__ import annotations

import pytest

from governed_agent_bench.analysis.frame import (
    CAPABLE,
    WEAK,
    AnalysisFrame,
    AnalysisRow,
    cell_of,
)


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


def test_cell_of_matches_2x2_convention():
    assert cell_of(told=True, enforced=True) == "A"
    assert cell_of(told=True, enforced=False) == "B"
    assert cell_of(told=False, enforced=True) == "C"
    assert cell_of(told=False, enforced=False) == "D"


def test_row_cell_property():
    assert _row(told=True, enforced=False).cell == "B"
    assert _row(told=False, enforced=False).cell == "D"


def test_bad_band_rejected():
    with pytest.raises(ValueError):
        _row(capability_band="medium")


def test_bool_salience_rejected():
    with pytest.raises(ValueError):
        _row(salience=True)  # bool is not a valid ordinal level


def test_model_in_two_bands_is_hard_error():
    rows = [
        _row(model_id="shared", capability_band=CAPABLE),
        _row(model_id="shared", capability_band=WEAK),
    ]
    with pytest.raises(ValueError, match="two capability bands"):
        AnalysisFrame(rows)


def test_family_spanning_bands_is_allowed():
    # The confound break: same family, different bands, different models.
    rows = [
        _row(model_id="cap1", model_family="shared_fam", capability_band=CAPABLE),
        _row(model_id="weak1", model_family="shared_fam", capability_band=WEAK),
    ]
    frame = AnalysisFrame(rows)  # must not raise
    assert len(frame) == 2


def test_filters_and_kn():
    rows = [
        _row(model_id="cap", told=True, enforced=False, capability_band=CAPABLE, safe=True),
        _row(model_id="weak", told=True, enforced=False, capability_band=WEAK, safe=False),
        _row(model_id="weak", told=False, enforced=True, capability_band=WEAK, safe=True),
        _row(model_id="cap", told=False, enforced=False, capability_band=CAPABLE, safe=False),
    ]
    frame = AnalysisFrame(rows)
    assert frame.counts_by_cell() == {"A": 0, "B": 2, "C": 1, "D": 1}
    cell_b = frame.cell("B")
    assert cell_b.kn() == (1, 2)
    assert cell_b.band(CAPABLE).kn() == (1, 1)
    assert cell_b.band(WEAK).kn() == (0, 1)


def test_salience_levels_and_scenarios():
    rows = [
        _row(salience=2, scenario_id="x"),
        _row(salience=0, scenario_id="y"),
        _row(salience=2, scenario_id="x"),
    ]
    frame = AnalysisFrame(rows)
    assert frame.salience_levels() == (0, 2)
    assert frame.scenario_ids() == ("x", "y")
