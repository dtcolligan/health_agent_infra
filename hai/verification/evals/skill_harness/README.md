# Skill-harness eval pilot (Phase E)

Opt-in harness that exercises real readiness skill paths
(`recovery-readiness`, `running-readiness`) end-to-end and scores the emitted
`TrainingRecommendation` along two explicitly separated axis groups:

- **A. Deterministic correctness** — pass/fail checks (schema, action,
  confidence bound, `policy_decisions` echoed verbatim, action_detail
  keys, recommendation-id format).
- **B. Rationale rubric** — per-scenario 0/1/2 scores on band
  references, uncertainty tokens, and forbidden-token hygiene.

See [`rubrics/recovery.md`](rubrics/recovery.md) and
[`rubrics/running.md`](rubrics/running.md) for the rubrics and
[`../../reporting/plans/historical/skill_harness_rfc.md`](../../../reporting/plans/historical/skill_harness_rfc.md)
for design context.

## Not part of normal CI

Normal `hai eval` and `pytest` behaviour is unchanged. This harness
lives under `verification/evals/skill_harness/` and is invoked directly:

    # default mode — replay committed transcripts
    python verification/evals/skill_harness/runner.py

    # single scenario
    python verification/evals/skill_harness/runner.py --scenario-id rec_h01_rested_baseline

    # running readiness scenarios
    python verification/evals/skill_harness/runner.py --domain running

    # machine-readable
    python verification/evals/skill_harness/runner.py --json

Exit code is `0` when every scenario passes the correctness group,
`1` otherwise, and `2` on a harness-level error (missing scenario,
malformed JSON, live-mode prerequisites unmet).

## Modes

- `--mode replay` (default) — loads the most recent transcript per
  scenario from `scenarios/<domain>/transcripts/<scenario_id>/` when present.
  This is what pytest drives.
- `--mode live` — invokes Claude Code as a subprocess against the
  selected real readiness skill, writes the response to a new transcript file,
  then scores it. Opt-in: requires
  `HAI_SKILL_HARNESS_LIVE=1` and `claude` on PATH.
- `--mode demo` — prints the composed snapshot + expectations for a
  single scenario so you can paste them into Claude Code yourself and
  compare responses by eye.

## Transcript shape

Each transcript is a JSON file under
`scenarios/<domain>/transcripts/<scenario_id>/<stamp>.json` with:

    {
      "scenario_id": "...",
      "source": "claude_code_subprocess" | "hand_authored_reference" | ...,
      "recorded_at": "2026-04-19T12:00:00Z",
      "notes": "optional operator note",
      "recommendation": { ...TrainingRecommendation... }
    }

The committed reference transcripts are labelled
`source: hand_authored_reference` and exist only to exercise the
scoring pipeline end-to-end; they are not evidence of live skill
behaviour. Running `--mode live` produces genuine
`claude_code_subprocess` transcripts — those are the Phase E
deliverable for skill-quality evidence.

## What the pilot covers / does not cover

**Covered today:**

- recovery with seven frozen scenarios spanning all
  major action-matrix branches and every policy-forced branch
  (coverage-insufficient block, R5 sparse cap, R6 RHR-spike escalation);
- running with four frozen scenarios covering baseline proceed, insufficient
  signal defer, ACWR spike escalation, and recovery-coupled hold;
- deterministic correctness scoring over real runtime contracts
  (schema validator + real `policy_decisions` echo);
- rationale-rubric scoring by token presence;
- offline replay over committed transcripts;
- live-mode scaffolding via Claude Code subprocess.

**Out of scope for the pilot:**

- four other domain skills (sleep / stress / strength / nutrition) —
  intentional. Broadening belongs in a later phase once the pilot's shape
  stabilises across recovery and running.
- live cross-domain synthesis skill evaluation — out of this pilot's scope.
  A deterministic synthesis-output scorer exists under
  `verification/evals/synthesis_harness/`, but live `daily-plan-synthesis`
  transcript capture is still separate future work.
- LLM-as-judge rubric scoring — deliberately deferred. See the RFC's
  "Future work" section for the planned slot.
- running live in CI — the pilot is opt-in by design.
