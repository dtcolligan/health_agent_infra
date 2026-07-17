"""Tests for the Bayesian GLMM secondary (analysis.glmm).

Skipped unless statsmodels is installed (it is an optional-dependency; the core
venv omits it). Run this file with the analysis extra:

    PYTHONPATH=benchmark uv run --with statsmodels pytest -q \
        benchmark/verification/tests/test_analysis_glmm.py
"""

from __future__ import annotations

import math

import pytest

from governed_agent_bench.analysis.frame import CAPABLE, WEAK, AnalysisFrame, AnalysisRow
from governed_agent_bench.analysis.glmm import (
    fit_substitution_glmm,
    statsmodels_available,
)

pytestmark = pytest.mark.skipif(
    not statsmodels_available(), reason="statsmodels not installed (analysis extra)"
)


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _confound_broken_frame(cap_logodds: float, interaction: float = 0.0, seed: int = 0):
    """Cell-B frame where two families EACH span both bands (confound broken),
    with a planted capability log-odds effect (and optional interaction)."""

    import numpy as np

    rng = np.random.default_rng(seed)
    rows = []
    # Two families, each with a capable and a weak model: family is not aligned
    # with band, so C(model_family) is estimable alongside `capable`.
    specs = [
        ("famA", CAPABLE, "famA_cap"),
        ("famA", WEAK, "famA_weak"),
        ("famB", CAPABLE, "famB_cap"),
        ("famB", WEAK, "famB_weak"),
    ]
    for scenario in range(6):
        scn_u = float(rng.normal(0.0, 0.4))
        for salience in (0, 1):
            for family, band, model_id in specs:
                cap = 1 if band == CAPABLE else 0
                eta = -0.5 + scn_u + cap * cap_logodds + cap * salience * interaction
                p = _sigmoid(eta)
                for _rep in range(4):
                    rows.append(
                        AnalysisRow(
                            scenario_id=f"scn{scenario}",
                            task_id=f"t{scenario}",
                            model_id=model_id,
                            model_family=family,
                            provider="sim",
                            capability_band=band,
                            told=True,
                            enforced=False,
                            salience=salience,
                            safe=bool(rng.random() < p),
                        )
                    )
    return AnalysisFrame(rows)


def test_glmm_recovers_positive_capability_effect():
    frame = _confound_broken_frame(cap_logodds=2.5, seed=1)
    result = fit_substitution_glmm(frame)
    assert result.capability_logodds is not None
    # Planted a strong positive capability effect; recover its sign clearly.
    assert result.capability_logodds["mean"] > 0.5
    assert result.included_family is True  # families span both bands
    assert result.included_salience is True
    assert result.n_obs == frame.cell("B").kn()[1]


def test_glmm_reports_crossed_variance_components():
    frame = _confound_broken_frame(cap_logodds=1.5, seed=2)
    result = fit_substitution_glmm(frame)
    assert set(result.variance_components) == {"scenario", "model"}


def test_glmm_drops_family_when_confound_unbroken():
    # Family perfectly aligned with band => not estimable => auto-drop.
    rows = []
    for scenario in range(4):
        for band, family, model_id in (
            (CAPABLE, "cap_fam", "cap_m"),
            (WEAK, "weak_fam", "weak_m"),
        ):
            for _rep in range(6):
                rows.append(
                    AnalysisRow(
                        scenario_id=f"scn{scenario}",
                        task_id=f"t{scenario}",
                        model_id=model_id,
                        model_family=family,
                        provider="sim",
                        capability_band=band,
                        told=True,
                        enforced=False,
                        salience=0,
                        safe=(band == CAPABLE),
                    )
                )
    result = fit_substitution_glmm(AnalysisFrame(rows))
    assert result.included_family is False
    assert result.included_salience is False  # single salience level


def test_glmm_as_dict_serialisable():
    import json

    frame = _confound_broken_frame(cap_logodds=1.0, seed=3)
    result = fit_substitution_glmm(frame)
    json.dumps(result.as_dict())
