# Synthesis-skill scoring rubric (W42)

Scores apply to a synthesis output dict produced by the
`daily-plan-synthesis` skill against a fixture bundle.

## Axis group A — deterministic correctness (pass / fail)

- **all_firings_cited_or_summarised** — every `rule_id` in
  `phase_a_firings` is either named verbatim in the synthesis prose
  OR matched by a token in `expected.firing_summaries[rule_id]`.
  Catches: skill picked up the bundle but forgot to narrate that the
  runtime applied a soften/block firing.
- **no_invented_xrule** — every `Xn[ab]?` token in the prose
  corresponds to a firing actually in the bundle. Catches: the skill
  invented an X-rule the runtime did not actually apply.
- **no_invented_band** — every `<...>_band` token in the prose
  corresponds to a band actually present in
  `snapshot.<domain>.classified_state`. Catches: the skill named a
  band the classifier didn't compute.
- **no_action_mutation_by_prose** — for every domain in the
  bundle's proposals, if the synthesis output asserts an action via
  `per_domain_action[<domain>]`, it must equal the proposal's
  `draft_action` (or `action` when no draft was made). Catches: the
  skill silently changed an action via prose phrasing.

A failure on any axis flips correctness to `fail`. The detail field
identifies the missing firing / invented token / mismatched action so
a contributor can locate the broken rationale line without reading
the whole transcript.
