# Evaluation framework — v1

Scores the deterministic runtime layers of health_agent_infra against
frozen scenario bundles with expected outputs.

## What this evaluates

The v1 eval framework exercises two runtime layers:

- **Domain layer** — `classify.py` + `policy.py` per domain. Scored
  against expected classified bands, forced actions, capped
  confidences, and rule-id firings.
- **Synthesis layer** — `core/synthesis.py` + `core/synthesis_policy.py`.
  Scored against expected X-rule firings (by rule id), final per-
  domain actions, final confidences, and any authored
  validation-error or synthesis-error invariants.

## What this deliberately does NOT evaluate

- **Skill narration quality.** Rationale prose, uncertainty prose,
  joint-narration conflict resolution, and any other behaviour that
  lives inside `skills/<name>/SKILL.md` requires invoking Claude Code
  (or equivalent agent runtime) as a subprocess. Per Phase 2.5 Track B
  Condition 3 this is a deferred follow-up; scenarios carry a
  `rationale_quality: skipped_requires_agent_harness` axis so the gap
  is visible rather than silently green.

- **Live Garmin pull.** Evals run on frozen evidence bundles; the
  pull path is covered by `safety/tests/test_pull_garmin_live.py`
  with a mocked client.

See `rubrics/` for per-layer scoring definitions.

## Layout

    safety/evals/
        scenarios/
            recovery/       # domain scenarios
            running/
            sleep/
            stress/
            strength/       # classify + policy only; no writeback surface in v1
            nutrition/      # macros-only per Phase 2.5 retrieval-gate outcome
            synthesis/      # X-rule + synthesis.run_synthesis scenarios
        rubrics/
            domain.md
            synthesis.md
        runner.py           # scenario loader + scorer
        cli.py              # `hai eval run` argparse entry point

## Scenario schema

Every scenario is a JSON file with a shared envelope:

```json
{
  "scenario_id": "rec_001_rested_and_fresh",
  "kind": "domain",                          // "domain" | "synthesis"
  "domain": "recovery",                       // only for kind=domain
  "description": "Well-rested baseline; expect maintain + no policy firings.",
  "input": { "evidence": {...}, "raw_summary": {...} },   // domain scenarios
  "as_of_date": "2026-04-18",                              // synthesis only
  "user_id": "u_eval",                                     // synthesis only
  "snapshot": {...},                                        // synthesis only
  "proposals": [...],                                       // synthesis only
  "expected": {
    "classified": {"sleep_debt_band": "none", ...},
    "policy": {"forced_action": null, "capped_confidence": null,
               "fired_rule_ids": []}
    // For synthesis:
    // "x_rules_fired": ["X1a"],
    // "final_actions": {"recovery": "downgrade_hard_session_to_zone_2"},
    // "final_confidences": {"recovery": "moderate"},
    // "validation_errors": [{"proposal_id": "...", "accepted": false, ...}],
    // "synthesis_error": "expected" | "none"
  }
}
```

`expected.classified` only needs to assert on the keys you care about;
unasserted keys are ignored. Same for `expected.policy` and the
synthesis equivalents.

## CLI

    hai eval run --domain recovery          # run all recovery scenarios
    hai eval run --synthesis                # run all synthesis scenarios
    hai eval run --domain recovery --json   # machine-readable output

Exit code is 0 when all loaded scenarios pass, 1 when any fails, 2 on
usage error.

## Skill-harness follow-up

Phase 2.5 Track B recorded that the runtime runner does not invoke the
daily-plan-synthesis skill and cannot score rationale quality. The
runner here inherits that gap. A skill-harness follow-up would:

1. Spawn `claude` (or equivalent) with the `--print` / `--json-output`
   flag and the synthesis bundle on stdin.
2. Capture the emitted `skill_drafts` list and pass it to
   `run_synthesis(..., skill_drafts=...)`.
3. Extend `score_synthesis_result` to grade the overlay's rationale
   prose against the scenario's rubric cues.

This is a substantial external-process integration with its own
auth/permission/cost surface and is not in scope for Phase 6. The
skipped axis in each scenario's score documents the exact invariant
that remains unverified.
