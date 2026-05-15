# Flagship Loop Proof — multi-domain evals (2026-04-18)

Captures a complete pass of the Phase 6 deterministic eval runner
across all six v1 domains plus the synthesis layer. Replaces the
pre-reshape single-domain bundles now archived under
``reporting/artifacts/archive/``.

## Scope

- **28 scenarios** total: 18 per-domain (3 × 6 domains: recovery,
  running, sleep, stress, strength, nutrition) + 10 synthesis.
- Each capture bundles the frozen scenario JSON, the runtime result
  the scenario produced, and the scored axes.
- ``rationale_quality`` is marked ``skipped_requires_agent_harness``
  on every scenario — the runner tests the deterministic runtime
  only, not the skill-layer narration. See
  ``verification/evals/skill_harness_blocker.md`` for the deferred
  follow-up.

## What this bundle proves

- Per-domain classify + policy land the expected bands and force the
  expected actions / confidence caps against frozen inputs.
- Synthesis X-rule evaluators (X1a, X1b, X2, X3a, X3b, X6a, X7, X9)
  fire correctly against frozen snapshot + proposal bundles, and the
  writeback validator rejects stale proposals before synthesis runs.
- The eval framework itself pipes scenarios → runner → scorer → exit
  code cleanly via ``hai eval run``.

## Files

- ``captured/{recovery,running,sleep,stress,strength,nutrition}.json``
  — one file per domain; each holds a list of ``{scenario, result,
  score}`` records.
- ``captured/synthesis.json`` — the same shape for the synthesis
  scenarios.
- ``summary.json`` — pass/total counts per surface. All green on this
  capture (6 × 3/3 domain + 10/10 synthesis).

## How to regenerate

    .venv/bin/python -c "$(cat <<'PY'
    import json, sys; from pathlib import Path
    sys.path.insert(0, 'src'); sys.path.insert(0, '.')
    from health_agent_infra.evals.runner import (
        SUPPORTED_DOMAINS, load_scenarios,
        run_domain_scenario, run_synthesis_scenario,
        score_domain_result, score_synthesis_result,
    )
    # ... see the one-off script used to produce this bundle
    PY
    )"

Or run ``hai eval run --domain <d>`` / ``hai eval run --synthesis``
and redirect the ``--json`` output into per-surface files.

## What this bundle deliberately does NOT prove

- The daily-plan-synthesis skill's rationale prose is accurate or
  non-contradictory. That requires the deferred skill-harness
  follow-up (Phase 2.5 Condition 3).
- The live Garmin pull returns well-formed evidence. Covered
  separately by ``verification/tests/test_pull_garmin_live.py`` with a
  mocked client.
- Any intake CLI surface end-to-end. Covered by
  ``verification/tests/test_intake_*.py``.
