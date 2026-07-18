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
  * ``paired``      -- within-family paired capability contrast (the PRIMARY:
                       each family one difference d_f = capable - weak in cell B;
                       exact sign-flip permutation + paired-t supplement).
  * ``descriptive`` -- per-cell/per-band safe rates + exact CIs (D4=A).
  * ``permutation`` -- the capability x salience interaction test (numpy, fixed
                       seed, no scipy).
  * ``mde``         -- minimum detectable effect at the planned N.
  * ``glmm``        -- Bayesian crossed-RE GLMM (D4=A secondary; statsmodels,
                       guarded import, optional-dependency group).
  * ``adapter``     -- the thin rep-dir -> row bridge. Wraps ``results/`` for the
                       run-dir walk + first-attempt re-score; carries the F1/F6/
                       first-attempt/infra-drop guards and the roster labelling.

The statistical core consumes an :class:`~.frame.AnalysisFrame` and never reads a
run directory; only ``adapter`` touches run dirs. The core is additionally
validated on synthetic frames with a planted effect.
"""
