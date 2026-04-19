# Skill-harness eval pilot (Phase E)

Opt-in harness that exercises a real skill path (`recovery-readiness`)
end-to-end and scores the emitted `TrainingRecommendation` along two
explicitly separated axis groups:

- **A. Deterministic correctness** — pass/fail checks (schema, action,
  confidence bound, `policy_decisions` echoed verbatim, action_detail
  keys, recommendation-id format).
- **B. Rationale rubric** — per-scenario 0/1/2 scores on band
  references, uncertainty tokens, and forbidden-token hygiene.

See [`rubrics/recovery.md`](rubrics/recovery.md) for the rubric and
[`../../reporting/plans/skill_harness_rfc.md`](../../../reporting/plans/skill_harness_rfc.md)
for design context.

## Not part of normal CI

Normal `hai eval` and `pytest` behaviour is unchanged. This harness
lives under `safety/evals/skill_harness/` and is invoked directly:

    # default mode — replay committed transcripts
    python safety/evals/skill_harness/runner.py

    # single scenario
    python safety/evals/skill_harness/runner.py --scenario-id rec_h01_rested_baseline

    # machine-readable
    python safety/evals/skill_harness/runner.py --json

Exit code is `0` when every scenario passes the correctness group,
`1` otherwise, and `2` on a harness-level error (missing scenario,
malformed JSON, live-mode prerequisites unmet).

## Modes

- `--mode replay` (default) — loads the most recent transcript per
  scenario from `scenarios/recovery/transcripts/<scenario_id>/`. This
  is what pytest drives.
- `--mode live` — invokes Claude Code as a subprocess against the
  real `recovery-readiness/SKILL.md`, writes the response to a new
  transcript file, then scores it. Opt-in: requires
  `HAI_SKILL_HARNESS_LIVE=1` and `claude` on PATH.
- `--mode demo` — prints the composed snapshot + expectations for a
  single scenario so you can paste them into Claude Code yourself and
  compare responses by eye.

## Transcript shape

Each transcript is a JSON file under
`scenarios/recovery/transcripts/<scenario_id>/<stamp>.json` with:

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

- one domain (`recovery`) with seven frozen scenarios spanning all
  major action-matrix branches and every policy-forced branch
  (coverage-insufficient block, R5 sparse cap, R6 RHR-spike escalation);
- deterministic correctness scoring over real runtime contracts
  (schema validator + real `policy_decisions` echo);
- rationale-rubric scoring by token presence;
- offline replay over committed transcripts;
- live-mode scaffolding via Claude Code subprocess.

**Out of scope for the pilot:**

- five other domains (running / sleep / stress / strength / nutrition) —
  intentional. Broadening beyond recovery belongs in a later phase
  once the pilot's shape stabilises.
- cross-domain synthesis skill evaluation (X-rule-aware narration) —
  out of pilot scope; the deterministic synthesis runner already
  covers every mechanical axis and the skill-harness shape reserves
  room for a synthesis axis but does not ship one.
- LLM-as-judge rubric scoring — deliberately deferred. See the RFC's
  "Future work" section for the planned slot.
- running live in CI — the pilot is opt-in by design.
