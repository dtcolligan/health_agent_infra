# Skill-harness follow-up — blocker notes

Phase 2.5 Track B ("Independently-authored synthesis eval pack")
attached three follow-up conditions to the Phase 3 authorisation. One
of them — **Condition 3: skill-harness eval as a Phase 3 exit
criterion** — remains deferred. Phase 6 inherits the gap rather than
pretending to close it. This note records exactly what is blocking
implementation so a future session can pick it up cleanly.

## The condition

> Run s1, s3, and s4 again at the end of Phase 3 with the skill
> actually invoked (via Claude Code subprocess or equivalent). Score
> the full ``rationale_quality`` axis. If any scenario scores below
> 2/3 on the full rubric, synthesis-skill-prompt redesign moves into
> Phase 3's late-phase scope as a visible correction.

The runtime runner under ``safety/evals/runner.py`` invokes
``run_synthesis`` directly against the scenario bundle. It does NOT
invoke ``skills/daily-plan-synthesis/SKILL.md`` — so
``rationale_quality`` is marked ``skipped_requires_agent_harness`` on
every synthesis scenario.

## Why this is non-trivial

A faithful skill-harness eval needs all four of:

1. **Live agent runtime.** Either ``claude`` CLI (Claude Code) as a
   subprocess with ``--print --output-format json``, or a direct
   Anthropic SDK call with the skill markdown inlined into a system
   prompt. Both require an API key or a logged-in session. Not
   available from the deterministic runner today.

2. **Skill-contract serialisation.** The synthesis skill reads a
   ``build_synthesis_bundle`` output and emits a ``drafts_json``
   overlay (list of partial BoundedRecommendation dicts). The wire
   format is agent-authored and not currently machine-validated end-
   to-end — ``_overlay_skill_drafts`` in ``core/synthesis.py``
   validates shape but the output contract from the skill side is
   loose. Locking this down is a prerequisite for reliable scoring.

3. **Non-determinism + rubric scoring.** Rationale prose varies
   between runs. Scoring "does the rationale reference the key signals
   that drove the decision" reliably needs either (a) a second LLM as
   judge, configured with its own rubric and temperature settings, or
   (b) a human grader — neither of which fits a ``pytest`` run.

4. **Cost + CI secrecy.** Running the full scenario pack on every CI
   push burns tokens and leaks whatever API key manages them. Even a
   nightly cadence raises questions about secret storage and failure
   semantics.

## What an honest implementation would need

- An opt-in entry point (``hai eval run --skill-harness``) that is
  silent unless a ``CLAUDE_API_KEY`` (or project-scoped equivalent)
  is present.
- A "judge" prompt + rubric pair kept under
  ``safety/evals/rubrics/skill_judge.md`` with its own frozen version.
- A recorded-transcript mode so a single live run can be replayed
  offline for unit-level assertion of the parsing / scoring pipeline
  without re-burning tokens.
- CI integration (nightly only, explicit gate) — NOT on every PR.

## What Phase 6 chose to do instead

Ship the deterministic runner and commit the skipped axis explicitly.
Scenarios carry ``rationale_quality:
skipped_requires_agent_harness`` so the gap is visible to anyone
reading a score. The scoring + dispatch pipeline is designed so
plugging a skill harness in later does not require reshaping the
scenario format: a new scorer axis ``rationale_quality`` would simply
flip from ``skipped_`` to ``pass``/``fail`` once the harness lands.

See ``reporting/plans/phase_2_5_independent_eval.md`` sections
"What the eval does NOT cover" and "Conditions on the Phase 3
authorisation" for the original gap record.
