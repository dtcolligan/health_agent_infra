"""Bayesian crossed random-effects GLMM (D4=A secondary).

The descriptive contrast + permutation test are the primary readout; this is the
principled secondary that accounts for the clustered design directly. It fits, on
the cell-B reps,

    safe ~ capable * salience + C(model_family)     (fixed effects)
    + (1 | scenario) + (1 | model)                  (crossed random intercepts)

with ``statsmodels.BinomialBayesMixedGLM`` (variational Bayes). ``capable`` is a
0/1 indicator so its coefficient is the log-odds increment for capable models in
the told-and-unenforced cell -- positive means capable self-enforce more than
weak, the H1 direction. ``capable:salience`` is the interaction (H2). The
``C(model_family)`` covariate is the confound control (D3=B); it is estimable
only when families span both bands (the confound break) and is auto-dropped with
a note otherwise.

statsmodels is NOT a core benchmark dependency (the released reproduce/offline
path is stdlib + numpy). It is declared in the ``analysis`` optional-dependency
group; the import is guarded so importing this module never breaks a core
install. Fit it via ``uv run --with statsmodels`` or ``uv sync --extra analysis``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .frame import CAPABLE, AnalysisFrame

_IMPORT_HINT = (
    "The GLMM secondary needs statsmodels (+ scipy, pandas, patsy), which are "
    "not core benchmark dependencies. Install the analysis extra: "
    "`uv sync --extra analysis`, or run ad hoc with "
    "`uv run --with statsmodels python ...`."
)


def statsmodels_available() -> bool:
    """Whether the GLMM backend can be imported in this environment."""

    try:  # pragma: no cover - import probe
        import pandas  # noqa: F401
        from statsmodels.genmod.bayes_mixed_glm import (  # noqa: F401
            BinomialBayesMixedGLM,
        )
    except ImportError:
        return False
    return True


def require_statsmodels() -> None:
    """Raise a helpful ImportError if the GLMM backend is unavailable."""

    if not statsmodels_available():
        raise ImportError(_IMPORT_HINT)


@dataclass(frozen=True)
class GLMMResult:
    """Extracted fixed effects, variance components, and the H1/H2 estimates."""

    fixed_effects: dict[str, dict[str, float]]
    variance_components: dict[str, dict[str, float]]
    capability_logodds: dict[str, float] | None
    interaction_logodds: dict[str, float] | None
    n_obs: int
    formula: str
    vc_formulas: dict[str, str]
    included_family: bool
    included_salience: bool
    fit_method: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "governed_agent_bench.analysis.glmm.v1",
            "formula": self.formula,
            "vc_formulas": self.vc_formulas,
            "n_obs": self.n_obs,
            "included_family": self.included_family,
            "included_salience": self.included_salience,
            "fit_method": self.fit_method,
            "fixed_effects": self.fixed_effects,
            "variance_components": self.variance_components,
            "capability_logodds": self.capability_logodds,
            "interaction_logodds": self.interaction_logodds,
        }


def _cellB_dataframe(frame: AnalysisFrame):
    import pandas as pd

    rows = list(frame.cell("B"))
    if not rows:
        raise ValueError("no cell-B reps to fit")
    return pd.DataFrame(
        {
            "safe": [1 if r.safe else 0 for r in rows],
            "capable": [1 if r.capability_band == CAPABLE else 0 for r in rows],
            "salience": [float(r.salience) for r in rows],
            "model_family": [r.model_family for r in rows],
            "scenario_id": [r.scenario_id for r in rows],
            "model_id": [r.model_id for r in rows],
        }
    )


def _families_span_bands(df) -> bool:
    """True iff at least one family appears in both capability bands.

    A family covariate is only estimable alongside ``capable`` when some family
    is not perfectly aligned with the band -- i.e. the family/capability confound
    is actually broken in this frame.
    """

    per_family_bands = df.groupby("model_family")["capable"].nunique()
    return bool((per_family_bands > 1).any())


def fit_substitution_glmm(
    frame: AnalysisFrame,
    *,
    include_salience: bool = True,
    include_family: bool = True,
    fit_method: str = "vb",
) -> GLMMResult:
    """Fit the cell-B substitution GLMM and extract H1/H2 log-odds effects.

    ``include_salience`` is auto-disabled if fewer than two salience levels are
    present; ``include_family`` is auto-disabled if no family spans both bands
    (an unbroken confound would make the family covariate collinear with
    ``capable``). Both auto-drops are recorded on the result.
    """

    require_statsmodels()
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

    df = _cellB_dataframe(frame)

    use_salience = include_salience and df["salience"].nunique() >= 2
    use_family = include_family and _families_span_bands(df)

    terms = ["capable"]
    if use_salience:
        terms.append("salience")
        terms.append("capable:salience")
    if use_family:
        terms.append("C(model_family)")
    formula = "safe ~ " + " + ".join(terms)

    # Crossed random intercepts: one variance component per grouping factor.
    vc_formulas = {
        "scenario": "0 + C(scenario_id)",
        "model": "0 + C(model_id)",
    }

    model = BinomialBayesMixedGLM.from_formula(formula, vc_formulas, df)
    if fit_method == "vb":
        result = model.fit_vb()
    elif fit_method == "map":
        result = model.fit_map()
    else:
        raise ValueError(f"fit_method must be 'vb' or 'map', got {fit_method!r}")

    fe_names = list(result.model.exog_names)
    fe_mean = list(map(float, result.fe_mean))
    fe_sd = list(map(float, result.fe_sd))
    fixed_effects = {
        name: {"mean": round(m, 8), "sd": round(s, 8)}
        for name, m, s in zip(fe_names, fe_mean, fe_sd)
    }

    vcp_names = list(result.model.vcp_names)
    vcp_mean = list(map(float, result.vcp_mean))
    vcp_sd = list(map(float, result.vcp_sd))
    # statsmodels parameterises variance components as log standard deviations.
    variance_components = {
        name: {
            "log_sd_mean": round(m, 8),
            "log_sd_sd": round(s, 8),
            "sd_point": round(math.exp(m), 8),
        }
        for name, m, s in zip(vcp_names, vcp_mean, vcp_sd)
    }

    capability = fixed_effects.get("capable")
    interaction = fixed_effects.get("capable:salience")

    return GLMMResult(
        fixed_effects=fixed_effects,
        variance_components=variance_components,
        capability_logodds=capability,
        interaction_logodds=interaction,
        n_obs=int(df.shape[0]),
        formula=formula,
        vc_formulas=vc_formulas,
        included_family=use_family,
        included_salience=use_salience,
        fit_method=fit_method,
    )


__all__ = [
    "GLMMResult",
    "fit_substitution_glmm",
    "require_statsmodels",
    "statsmodels_available",
]
