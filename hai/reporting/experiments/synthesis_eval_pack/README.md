# Synthesis Eval Pack — Phase 2.5 Track B

Independently-authored stress test for the synthesis runtime, authored
per the plan's "scenarios frozen before reading skill body" protocol.

## Contents

- `scenarios/s1_orphan_firing.json` — X-rule firing whose
  `affected_domain` is not in the proposal set
- `scenarios/s2_cap_adjust_stacking.json` — Phase A cap + Phase B
  adjust on the same domain
- `scenarios/s3_mixed_missingness.json` — four-domain day with
  present / partial / unavailable / pending_user_input mix
- `scenarios/s4_stale_proposal.json` — stale schema_version +
  out-of-enum action; both must be rejected pre-synthesis
- `rubric.md` — 3-point rubric (action correctness, rationale quality,
  uncertainty calibration)
- `runner.py` — exercises each scenario against the current runtime,
  captures observable behaviour
- `outputs/run_results.json` — raw runner output
- `scoring.json` — manual verdicts against the rubric
- `findings.md` — prose write-up + gate decision

## Scope limitation

The runner tests the RUNTIME layer only. The synthesis skill itself
(daily-plan-synthesis/SKILL.md) is an agent artifact that would require
invoking Claude Code as a subprocess to exercise. Skill-layer scoring
(rationale_quality) is therefore marked `skipped` in scoring.json. See
findings.md for what that means for confidence in the gate decision.

## Reproduce

    pip install -e .
    python3 runner.py

## Status

Complete. See `findings.md` for the gate decision.
Gate document: `../../plans/historical/phase_2_5_independent_eval.md`.
