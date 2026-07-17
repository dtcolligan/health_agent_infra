"""Powered-run analysis stack for the GovernedAgentBench expansion (D-EXP).

This package is the confirmatory analysis layer for the powered re-run of the
mutation-gate substitution study (n=2 -> a pre-registered, confound-broken
experiment across a param-count-banded roster). It is SEPARATE from the frozen
paper-v1 evidence code under ``results/`` on purpose: v1 reports per-``system_id``
2x2 cells (one model at a time); the powered run's headline is a cross-model
quantity -- whether the value of runtime enforcement in the told cell is gated
by model capability, and whether that gate moves with boundary salience.

Layering:
  * ``frame``       -- the tidy-row contract + estimand (pure, stdlib only).
  * ``descriptive`` -- per-cell/per-band safe rates + exact CIs (D4=A primary).
  * ``permutation`` -- the capability x salience interaction test (primary
                       inference; numpy, fixed seed, no scipy).
  * ``mde``         -- minimum detectable effect at the planned N.
  * ``glmm``        -- Bayesian crossed-RE GLMM (D4=A secondary; statsmodels,
                       guarded import, optional-dependency group).

The statistical core consumes an :class:`~.frame.AnalysisFrame` and never reads a
run directory. A thin adapter (built once roster_v4 + a real run exist) maps
scored reps -> rows; until then the core is validated on synthetic frames with a
planted effect.
"""
