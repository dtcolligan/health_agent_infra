# Running skill-harness rubric (W41)

Mirror of `recovery.md` adapted to the `running-readiness` skill. The
runner in `runner.py` scores running-domain transcripts against this
rubric the same way it does recovery.

## Axis group A — deterministic correctness (pass / fail)

- **schema_valid** — emitted dict passes
  `core.validate.validate_recommendation_dict`.
- **action_matches** — `action` enum value matches the scenario's
  `expected.action`. Exact string match.
- **confidence_within_bound** — `confidence` is no higher than
  `expected.confidence_at_or_below`. Uses `low < moderate < high`.
- **policy_decisions_preserved** — when the scenario sets
  `expected.policy_decisions_preserved: true`, the rationale's
  `policy_decisions` list must match what `evaluate_running_policy`
  produced verbatim. SKILL.md invariant: "copy `policy_decisions`
  verbatim — the runtime decided them."
- **action_detail_required_keys** — when set, each key must be
  present in the emitted `action_detail`.

## Axis group B — rationale quality (token presence)

- **bands_referenced** — every band name in
  `expected.rationale_must_reference_bands` must appear in the
  rationale text. Catches the "skill picked the right action but
  wrote a paragraph that doesn't cite the bands the classifier
  produced" failure mode.
- **uncertainty_must_contain** — every token in the list must appear
  in the recommendation's `uncertainty` array.
- **uncertainty_must_not_contain** — no token in the list may appear.

A future LLM-judge slot is reserved (same as recovery) once a
non-deterministic-rubric harness lands. Until then, scoring is
mechanical.
