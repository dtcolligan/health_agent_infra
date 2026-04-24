# Recovery skill-harness rubric (pilot)

Scores apply to a `TrainingRecommendation` JSON emitted by the
`recovery-readiness` skill for a given pilot scenario. The runner in
`runner.py` scores transcripts against this rubric mechanically.

The pilot deliberately splits scoring into two axis groups so the
reader can see at a glance whether a skill failure was **structural**
(the runtime contract was broken) or **narrative** (the prose did not
cover the signals it was supposed to cover).

## Axis group A — deterministic correctness (pass / fail)

Each axis returns `pass`, `fail`, or `skipped` (when the scenario did
not assert on it). A single `fail` makes the scenario's correctness
verdict `fail`.

- **schema_valid** — the emitted dict passes
  `core.validate.validate_recommendation_dict`. This is the same
  validator `hai synthesize` applies before persisting. A failure
  here means the skill broke a hard runtime contract (required field
  missing, banned token leaked, `review_at` outside the 24h window,
  etc.).
- **action_matches** — the `action` enum value matches the scenario's
  `expected.action`. Exact string match.
- **confidence_within_bound** — `confidence` is no higher than
  `expected.confidence_at_or_below`. Uses the usual `low < moderate <
  high` ordering.
- **policy_decisions_preserved** — when the scenario sets
  `expected.policy_decisions_preserved: true`, the rationale's
  `policy_decisions` list must match what
  `evaluate_recovery_policy` produced on the scenario's evidence
  (verbatim `(rule_id, decision, note)` tuples, set-equal). This is the
  SKILL.md invariant "copy `policy_decisions` verbatim — the runtime
  decided them."
- **action_detail_required_keys** — when the scenario lists keys under
  `expected.action_detail_required_keys`, each must be present in the
  emitted `action_detail`. Catches e.g. a `downgrade_hard_session_to_
  zone_2` recommendation that forgets `target_intensity`.
- **recommendation_id_format** — when the scenario carries
  `expected.recommendation_id_pattern`, the emitted
  `recommendation_id` must match the regex. Enforces SKILL.md's
  `rec_<for_date>_<user_id>_01` format.

## Axis group B — rationale rubric (0 / 1 / 2 per axis)

Each axis returns a small-integer score, never a hard fail. A
scenario's correctness verdict is independent of rubric scores, so a
skill that satisfies the runtime contract but narrates poorly shows up
as "correctness pass, rubric low."

The pilot scores by **token presence**. A future revision may layer an
LLM-as-judge axis on top (see `skill_harness_rfc.md` § "Future work");
this rubric is deliberately cheap to compute today so the pipeline can
run offline and without an API key.

- **band_references** — the scenario lists
  `expected.rationale_must_reference_bands` (a list of short tokens
  like `sleep_debt`, `resting_hr`, `hrv`, `training_load`,
  `soreness`). Score:
  - `2` — every listed token appears somewhere in the rationale
    (case-insensitive substring match).
  - `1` — at least half of them appear.
  - `0` — fewer than half appear.
- **uncertainty_tokens** — the scenario lists tokens that the skill's
  `uncertainty` array must contain (`expected.uncertainty_must_contain`)
  or must not contain (`expected.uncertainty_must_not_contain`). Score:
  - `2` — every required token present, no forbidden token present.
  - `1` — required tokens mostly present and/or a forbidden token leaked
    despite requireds being present.
  - `0` — required tokens missing with nothing else covering them.
- **forbidden_tokens** — the emitted `rationale[]` is scanned for the
  diagnosis-shaped tokens in `core.validate.BANNED_TOKENS` (the same
  list the writeback validator enforces). Score:
  - `2` — no banned token present.
  - `0` — any banned token present.

The rubric mean is the arithmetic mean of the three axes, reported per
scenario. The harness also prints a corpus-level mean across scenarios.

## What this rubric deliberately does NOT score

- **Prose quality as writing.** "Reads naturally," "flows well," and
  "sounds confident" are not scored. A token-presence rubric cannot
  judge them, and this pilot does not ship an LLM judge.
- **Branching reasoning chains.** Did the rationale walk through
  `classified_state → policy → action` in the right order? Not scored.
- **Clinical safety beyond banned tokens.** The banned-tokens list is a
  narrow backstop against diagnosis-shaped language; real safety review
  is covered by `safety/tests/test_core_schemas.py` and
  `safety/tests/test_banned_tokens.py`.

The RFC documents how an LLM-judge axis could be added without
restructuring the rubric: new axis id, same transcript format, same
scenario expectation block (plus a `judge_rubric_ref` pointer).
