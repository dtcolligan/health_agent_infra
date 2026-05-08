# Skill-harness follow-up — status note

**Status**: partially resolved by the Phase E pilot at
`verification/evals/skill_harness/`. This note used to describe a fully
deferred gap; it now records what the pilot closed, what remains
open, and what is intentionally out of scope.

Phase 2.5 Track B Condition 3 ("skill-harness eval as a Phase 3 exit
criterion") attached the original gap. See
[`reporting/plans/historical/skill_harness_rfc.md`](../../reporting/plans/historical/skill_harness_rfc.md)
for the pilot's design and
[`reporting/plans/historical/post_v0_1_roadmap.md`](../../reporting/plans/historical/post_v0_1_roadmap.md)
§5 Phase E for scope.

## Original condition (verbatim)

> Run s1, s3, and s4 again at the end of Phase 3 with the skill
> actually invoked (via Claude Code subprocess or equivalent). Score
> the full ``rationale_quality`` axis. If any scenario scores below
> 2/3 on the full rubric, synthesis-skill-prompt redesign moves into
> Phase 3's late-phase scope as a visible correction.

The original condition targeted the **synthesis** skill. Phase E
moved the first-cut harness to the **recovery-readiness** skill first
because the domain skills have a simpler contract than the synthesis
skill's bundle + ``drafts_json`` overlay. v0.1.8 then extended the domain
pilot to **running-readiness** and added a separate deterministic
``synthesis_harness`` for ``daily-plan-synthesis`` output fixtures. The
remaining gap is live skill-behaviour evidence across the rest of the
skill surface, not absence of any skill-eval harness.

## What the Phase E pilot resolved

1. **Live agent runtime.** `verification/evals/skill_harness/runner.py
   --mode live` invokes `claude` as a subprocess with the selected readiness
   skill (`recovery-readiness` by default, `running-readiness` with
   `--domain running`) as the system prompt and a classifier-+-policy-derived
   snapshot as the user message. Opt-in via `HAI_SKILL_HARNESS_LIVE=1`.
   Writes the emitted `TrainingRecommendation` to a timestamped transcript
   under `scenarios/<domain>/transcripts/<scenario_id>/`.

2. **Skill-contract serialisation.** The pilot locks down the
   readiness skill output contract via three checks:
   - `validate_recommendation_dict` (runtime validator) —
     guarantees schema, action enum, confidence enum, banned-token
     absence, and 24h `follow_up` window.
   - `policy_decisions_preserved` — the skill must echo the
     runtime-produced `policy_decisions` verbatim (set-equal on
     `rule_id`/`decision`/`note` tuples). This is a long-standing
     SKILL.md invariant that deterministic evals could not check.
   - `action_detail_required_keys` — enforces per-action detail
     shape (e.g. `target_intensity` for a zone-2 downgrade;
     `reason_token` + `consecutive_days` for R6 escalation).

3. **Rubric scoring pipeline.** `rubrics/recovery.md` and
   `rubrics/running.md` define rubric sub-axes scored 0/1/2, including
   band references, uncertainty tokens, and forbidden-token hygiene. The
   scorer computes a per-scenario rubric mean and a corpus-level rubric mean,
   reported *separately* from the correctness verdict so that
   "contract-correct but thin rationale" surfaces as a visible rubric dip
   rather than a silent pass.

4. **Cost + CI discipline.** The harness lives outside the packaged
   `hai eval` tree, its pytest coverage uses replay/fixture paths only, and
   live mode is gated on an explicit env flag. Normal CI and `pytest` never
   trigger live invocation.

5. **Scenario coverage for recovery and running.** Seven frozen recovery
   scenarios exercise every action-matrix branch and every
   policy-forced branch: baseline proceed, mild zone-2 downgrade,
   impaired mobility-only, impaired rest day, R6 escalation,
   R1 insufficient-coverage defer, R5 sparse-coverage confidence
   cap. Six of the seven carry a committed
   `hand_authored_reference` transcript (h01, h02, h03, h04, h05,
   h07) so the scorer exercises every branch; h06 is deliberately
   left un-transcripted so the missing-transcript failure path
   stays exercised by `test_missing_transcript_scenario_is_not_silent`.
   Four running scenarios cover baseline proceed, insufficient defer, ACWR
   spike escalation, and recovery-coupled hold.

6. **Synthesis-output scoring.** `verification/evals/synthesis_harness/`
   scores `daily-plan-synthesis` output dicts against three fixture days:
   clean, partial X1a, and escalated X3b. The scorer checks all firings
   cited/summarised, no invented X-rule, no invented band, and no action
   mutation by prose.

## What remains open

1. **Live transcript capture is still operator-driven.** The pilot
   ships live-mode scaffolding and hand-authored reference
   transcripts, but capturing the first real `claude_code_subprocess`
   transcripts is a manual step the operator runs. Until those
   transcripts exist the rubric means represent what *a good*
   response should look like, not what *the live skill* actually
   produces.

2. **No LLM-judge axis.** The rubric is token-presence-based. A
   future `judge_rationale_prose` axis scored by a second-pass
   Claude call is planned but not shipped; the rubric doc and
   transcript shape reserve room for it.

3. **Two domains only.** The domain pilot covers recovery and running.
   The remaining four domains (sleep / stress / strength / nutrition)
   are intentionally deferred so the scenario + rubric shape can
   stabilise before broadening.

4. **Synthesis skill live capture still unscored.** W42 scores
   `daily-plan-synthesis` output fixtures, but does not invoke the live
   Claude Code skill against `hai synthesize --bundle-only` bundles. The
   `rationale_quality: skipped_requires_agent_harness` axis on synthesis
   scenarios in `src/health_agent_infra/evals/scenarios/synthesis/` should
   stay until the live synthesis shape is defined.

5. **Cross-run stability is not measured.** A live scenario
   produces one transcript per run; narrative variance across N
   runs is not yet scored. This matters because rubric "pass"
   on one run + rubric "fail" on another run is worse news than a
   consistent "fail" — both are hidden by single-run scoring today.

## Intentionally out of scope

- **Running live in CI.** The cost + secret-handling tradeoff has
  not changed since the original blocker; the pilot still fences
  live mode behind a local env flag.
- **Grounding retrieval or external-source LLM judging.** Any
  retrieval-backed rubric belongs downstream of Phase F (grounded
  expert prototype), not Phase E.
- **Treating the hand-authored reference transcripts as skill
  evidence.** They exist to exercise the scorer and to give
  operators a reference shape; they are labelled
  `source: hand_authored_reference` so they cannot be mistaken for
  live-skill output.

## How a future session should pick this up

Two meaningful next steps, either of which is independently useful:

1. **Capture the first live transcripts.** Run the pilot with
   `HAI_SKILL_HARNESS_LIVE=1 python verification/evals/skill_harness/
   runner.py --mode live` for the supported domain/scenario set that needs
   live evidence, review the emitted transcripts by eye, and commit them
   alongside the existing reference transcripts. Mean rubric score then
   becomes skill-behaviour evidence.
2. **Clone into a third domain.** Copy the recovery/running scenario +
   rubric shape into one of {sleep, stress, strength, nutrition}, keep the
   same harness code (it already parametrises on `--domain`), and run replay
   + live cycles for the new domain.

Both are well-scoped; either can happen without touching the shipped
runtime.
