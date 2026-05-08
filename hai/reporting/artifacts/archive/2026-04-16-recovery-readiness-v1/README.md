# Flagship Loop Proof — recovery_readiness_v1 (2026-04-16, synthetic)

This bundle captures end-to-end runs of the flagship loop across eight synthetic scenarios, using the pre-reshape Python implementation (dated 2026-04-16). It is retained as an inputs-and-outputs reference — useful for pattern-matching on what the agent-plus-skills should produce on similar inputs after the 2026-04-17 tools-plus-skills reshape.

**Important caveat for post-reshape readers:** the `captured/*.json` files were produced by Python modules that executed state classification, policy rules, and recommendation shaping deterministically. After the reshape, that judgment moved to the `skills/recovery-readiness/SKILL.md` markdown and is produced by an agent. Regenerating these captures via the agent+skills flow is a follow-on task (see `STATUS.md`). Until then:

- The **inputs** (cleaned evidence + raw summary) remain valid examples.
- The **outputs** (recommendations, policy decisions) show what the pre-reshape Python emitted. An agent working from the same inputs plus the recovery-readiness skill will produce shape-compatible outputs but may differ in specifics (e.g., rationale wording).
- **`recovery_state`** objects in the captures reference types that no longer exist in `schemas.py` (they were stripped in the reshape). Treat those as legacy context, not current schema.

## Scenarios captured

| scenario | recovery_status | action | coverage | demonstrates |
|---|---|---|---|---|
| recovered_with_easy_plan | recovered | proceed_with_planned_session | full | green-path behavior |
| mildly_impaired_with_hard_plan | mildly_impaired | downgrade_hard_session_to_zone_2 | full | bounded downgrade for mild signals + hard plan |
| impaired_with_hard_plan | impaired | downgrade_session_to_mobility_only | full | stronger downgrade for impaired signals + hard plan |
| rhr_spike_three_days | mildly_impaired | escalate_for_user_review | full | R6 persistent-RHR-spike escalation |
| insufficient_signal | unknown | defer_decision_insufficient_signal | insufficient | R1 block on missing required inputs |
| sparse_signal | mildly_impaired | proceed_with_planned_session (confidence: moderate) | sparse | R5 confidence cap under sparse coverage |
| tailoring_recovered_strength_block | recovered | proceed_with_planned_session | full | active_goal surfaces in action_detail — identical evidence as endurance row |
| tailoring_recovered_endurance_taper | recovered | proceed_with_planned_session | full | active_goal surfaces in action_detail — identical evidence as strength row |

## Files

- `captured/*.json` — one full run artifact per scenario.
- `summary/*.txt` — human-readable one-screen summaries.
- `writeback/recovery_readiness_v1/` — actual local writeback targets produced during the 2026-04-16 capture: `recommendation_log.jsonl`, `daily_plan_2026-04-16.md`, `review_events.jsonl`, `review_outcomes.jsonl`.

## How to regenerate under the current (post-reshape) flow

1. Pick a scenario and construct a synthetic evidence JSON matching the pre-reshape fixture shape (reference the scenario's `cleaned_evidence` field in `captured/*.json`).
2. Run `hai clean --evidence-json <path>` to get CleanedEvidence + RawSummary.
3. Have a Claude agent read the output plus `skills/recovery-readiness/SKILL.md` and produce a TrainingRecommendation JSON.
4. Run `hai writeback --recommendation-json <path> --base-dir <somewhere/recovery_readiness_v1>`.
5. Run `hai review schedule` and `hai review record` as needed.

The bundle file layout above is what you'd expect the new flow to produce. Specific numeric values may drift because the agent's classification is skill-driven, not formula-driven. That's working as intended.

## Proof conditions (from the pre-reshape flagship spec)

Each `captured/*.json` includes:

1. **Deterministic evidence path** — `cleaned_evidence` showing the inputs.
2. **Typed state** — `recovery_state` object (legacy, stripped from current schemas; retained here for historical context).
3. **Policy gate** — `training_recommendation.policy_decisions` records each rule that fired.
4. **Structured recommendation** — `action`, `rationale`, `confidence`, `uncertainty`, `follow_up`, `policy_decisions`, `bounded=true`.
5. **Bounded writeback** — `writeback/recovery_readiness_v1/` shows only local JSONL appends + a daily-plan markdown note.
6. **Review loop** — `review_events.jsonl` + `review_outcomes.jsonl` linked via `recommendation_id`.

## Scope and honesty

- PULL here is a synthetic fixture. The sibling bundle `reporting/artifacts/flagship_loop_proof/2026-04-16-garmin-real-slice/` runs the same pipeline against the real committed Garmin CSV export.
- Live scheduled pulls are out of scope per the explicit non-goals.
- No diagnostic, clinical, or nutrition outputs.
