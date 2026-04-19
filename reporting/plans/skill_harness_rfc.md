# Skill-Harness Eval Pilot — RFC

- Author: Claude Code execution of Phase E
- Date: 2026-04-19
- Status: shipped as a pilot; open to revision
- Scope: `safety/evals/skill_harness/` + `reporting/plans/` +
  `safety/evals/skill_harness_blocker.md`
- Roadmap context:
  [`post_v0_1_roadmap.md`](post_v0_1_roadmap.md) §5 Phase E

This RFC records the honest design of the Phase E pilot: what the
pilot does automatically, what it still leaves to manual effort, and
where future work slots in without restructuring the scenario format.
Phase E does not close the Phase 2.5 Track B Condition 3 gap in full;
it narrows it enough that the remaining gap can be described precisely.

## Why a skill-harness pilot at all

`hai eval` scores the deterministic runtime (classify → policy →
synthesis → X-rules). It has never scored skill-mediated behaviour,
so every per-domain scenario carries a
`rationale_quality: skipped_requires_agent_harness` axis. The
[blocker note](../../safety/evals/skill_harness_blocker.md) explicitly
defers the skill-harness work to a later session.

At the v0.1.x state, the remaining project-level credibility gap is
not "the deterministic runtime might be wrong" — that is well covered —
but "the skill layer could drift away from SKILL.md and nobody would
notice." Phase E exists to start pulling at that loose thread,
starting with the one skill most tightly coupled to the shipped
runtime: `recovery-readiness`.

## Non-goals

- Multi-domain coverage. The pilot intentionally stays in the recovery
  domain. Broadening to running / sleep / stress / strength /
  nutrition is a future phase once this pilot's shape has stabilised
  and paid rent.
- Synthesis-skill evaluation. The synthesis skill has its own bundle
  + drafts contract and deserves its own harness; slotting it into the
  pilot scenario format would drag in shape that does not generalise
  back to the simpler domain case.
- CI integration. The pilot is deliberately opt-in. `pytest` touches
  only the replay mode against committed transcripts; live-mode
  invocation requires an explicit env flag and a local `claude` CLI.
- LLM-as-judge. The rubric is token-presence-only today. The rubric
  doc reserves a slot for a future judge axis without restructuring
  scenarios or transcripts.

## Design

### Three execution backends

Each scenario's input is the same no matter how the recommendation
gets produced. What differs is the transcript source:

- `replay` (default): the scorer loads the most recent transcript
  under `scenarios/<domain>/transcripts/<scenario_id>/`. Deterministic.
  CI + pytest use this. The committed reference transcripts carry
  `source: hand_authored_reference` — the RFC labels them honestly
  because they are NOT skill-behaviour evidence.
- `live`: gated on `HAI_SKILL_HARNESS_LIVE=1`. Invokes `claude` as a
  subprocess with the recovery-readiness SKILL.md as the system
  prompt and the composed snapshot as user input, writes the model
  response to a new transcript, then scores it. Transcript source is
  `claude_code_subprocess` — that is the skill-behaviour evidence.
- `demo`: prints the composed snapshot + expectation block without
  invoking any backend, so an operator can paste the pieces into
  Claude Code manually and compare responses by eye.

### Two axis groups

Scoring is split into two axis groups that are reported separately:

- **A. Deterministic correctness (pass/fail).** These axes fail fast
  and map directly to hard runtime contracts:
  - `schema_valid` — runs the same `validate_recommendation_dict`
    that `hai writeback` runs. A failure here means the skill broke a
    contract the runtime would have rejected anyway.
  - `action_matches` — exact match of the chosen enum value.
  - `confidence_within_bound` — honours R5 cap and any scenario cap.
  - `policy_decisions_preserved` — the `policy_decisions` list must
    equal (set-equal on rule_id/decision/note tuples) what
    `evaluate_recovery_policy` produced. SKILL.md requires this
    verbatim echo; the pilot now enforces it.
  - `action_detail_required_keys` — scenario-specified keys must be
    present (e.g. `target_intensity` for a zone-2 downgrade).
  - `recommendation_id_format` — scenario-specified regex.
- **B. Rationale rubric (0/1/2 per axis).** These axes are advisory
  and aggregate into a per-scenario mean. They never flip correctness
  from pass to fail:
  - `band_references` — how much of the required band vocabulary the
    rationale names.
  - `uncertainty_tokens` — presence of required + absence of
    forbidden uncertainty tokens.
  - `forbidden_tokens` — the rationale carries none of the
    diagnosis-shaped tokens in `core.validate.BANNED_TOKENS`.

Rubric scores are reported per-scenario and averaged across the
corpus. A skill can pass correctness with a low rubric average — that
is exactly the state the pilot should make visible, not the state it
should hide.

### Scenario shape

Scenarios live under
`safety/evals/skill_harness/scenarios/<domain>/<id>.json`. They carry:

- `scenario_id`, `domain`, `description`
- `input` with `evidence` + `raw_summary` + `today` (vendor signals) +
  `planned_session_type` + optional `active_goal`. The harness runs
  the real `classify_recovery_state` + `evaluate_recovery_policy`
  on these, so the snapshot shape the skill sees is authentic, not
  scenario-hard-coded.
- `expected` with:
  - structural expectations (`action`, `confidence_at_or_below`,
    `policy_decisions_preserved`, `action_detail_required_keys`,
    `recommendation_id_pattern`);
  - rubric expectations
    (`rationale_must_reference_bands`,
    `uncertainty_must_contain`, `uncertainty_must_not_contain`).

The pilot ships seven scenarios covering: recovered + hard planned
(baseline), mildly-impaired + hard (zone-2 downgrade), impaired +
hard (mobility-only), impaired + other (rest day), R6 escalation,
R1 insufficient-coverage block, and R5 sparse-coverage cap. Together
they exercise every branch of the SKILL.md action matrix and every
policy-forced code path.

### Transcript shape

Each transcript is one JSON file per scenario per invocation. The
format is deliberately stable so a live run today and a recorded
replay tomorrow score identically:

    {
      "scenario_id": "...",
      "source": "claude_code_subprocess" | "hand_authored_reference" | "anthropic_sdk" | ...,
      "recorded_at": "2026-04-19T12:00:00Z",
      "notes": "optional operator note",
      "recommendation": { ...TrainingRecommendation... }
    }

## What this pilot resolves from the blocker note

Of the four preconditions the blocker listed, the pilot addresses
three and partially addresses the fourth. See the updated blocker
note for the gap-by-gap rewrite.

- **Live agent runtime** — now scaffolded via
  `runner.invoke_live`. Opt-in through `HAI_SKILL_HARNESS_LIVE=1`.
- **Skill-contract serialisation** — the pilot validates the skill's
  output shape via the runtime's `validate_recommendation_dict`
  plus `policy_decisions_preserved` plus
  `action_detail_required_keys`. This locks down enough of the
  contract that scoring is deterministic.
- **Non-determinism + rubric scoring** — the token-presence rubric
  is deterministic, cheap, and honest. The LLM-judge axis is
  reserved as a future add-on.
- **Cost + CI secrecy** — addressed by the opt-in gate. Normal `hai
  eval` and `pytest` never trigger live mode; tokens are never spent
  unless the operator runs live manually.

## What remains out of scope

- Multi-domain skill-harness coverage. The format is ready to clone
  per domain (`scenarios/running/...`, `rubrics/running.md`, etc.);
  the pilot deliberately does not do that yet.
- Synthesis-skill rubric. Would need a distinct transcript shape
  (bundle in, drafts_json overlay out) and a distinct rubric.
- Cross-run stability measurement. A single live run produces one
  transcript; running three times and measuring cross-run narrative
  drift is future work.
- LLM-as-judge rubric axis. Reserved slot; not shipping in the pilot.
- Integration with `hai eval`. Until the pilot shows rent-paying
  signal, keeping it separate from `hai eval` protects the clean
  deterministic CI story.

## Future work

Enumerated so a later session can pick any of them up cleanly:

1. **`hai eval run --skill-harness`** — register the pilot runner as
   a `hai eval` subcommand once scope broadens beyond recovery. Keeps
   the opt-in gate; adds the CLI consistency.
2. **LLM-judge axis** — add a rubric axis scored by a second-pass
   Claude call with its own system prompt under `rubrics/judge.md`.
   Cache prompts; record the judge transcript alongside the primary
   transcript for replay. Keep it gated on a separate env flag so
   running the pilot never silently spends extra tokens.
3. **Second domain** — clone the recovery scenario shape into one of
   {sleep, stress, running} before expanding into all remaining
   domains.
4. **Cross-run stability axis** — capture N transcripts per scenario
   per live run, score variance (action stability, rubric variance).
   A low-variance, low-score scenario is a known bad branch in the
   skill; a high-variance, high-score scenario is brittle narration
   even if average rubric score looks fine.
5. **Golden-transcript diff** — surface a structured diff between a
   new live transcript and the latest committed one. Useful for
   reviewing whether a SKILL.md edit changed rationale prose in the
   expected way.

## Acceptance per roadmap §5 Phase E

| Criterion | Status |
|---|---|
| At least one real skill path exercised end to end | `live` mode wires `recovery-readiness/SKILL.md` through `claude` subprocess; replay mode runs against committed transcripts. The pilot ships both halves; the operator capturing a live transcript is the honest exit for full coverage. |
| Rationale quality scored by explicit rubric | `rubrics/recovery.md` scores three sub-axes 0/1/2; mean reported per scenario and across the corpus. |
| Pilot reporting separates deterministic correctness from narration/rationale quality | `_print_report` prints two report lines and labels each scenario with its correctness verdict + rubric mean distinctly. |
| Pilot is opt-in; does not destabilise normal CI | Runner lives under `safety/evals/` but outside the packaged `hai eval` tree. Live mode gated on an env flag. `pytest` touches replay only. |
| Blocker note meaningfully reduced or superseded | Rewritten as "what the pilot resolves / what still remains / what is intentionally out of scope." |
