# Batch 2 Edits Summary

## Files touched

| File | Edit type | Lines changed (rough) | Notes |
|---|---|---:|---|
| `benchmark/governed_agent_bench/README.md` | revise | ~17 diff lines | Added paper title, locked benchmark framing, ST-WebAgentBench differentiation axis, and exact HAI v0.2.0 manifest snapshot reference. |
| `benchmark/governed_agent_bench/BENCHMARK_SPEC.md` | revise | ~165 diff lines | Added D-FRAME-016/007/026 framing, explicit L1-L7 task-family descriptions with L2 setup/recovery, M4-M8/M9-TX mechanism inventory, paper-run controls, and GAB v2 reservation. |
| `benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md` | revise | ~138 diff lines | Added `HAI_INVOCATION_CONTEXT` discipline, runtime-mode mechanism table, `mechanism_disabled` marker expectations, and adaptive-vs-DRG-0 30-attempt protocol. |
| `benchmark/governed_agent_bench/SCORING_SPEC.md` | revise | ~64 diff lines | Added AND-pass rule, seven critical violations, D-FRAME-021 threshold table, `scorer_config_hash` policy, and Constitutional Classifiers Pareto-reporting precedent. |
| `benchmark/governed_agent_bench/schema/trajectory.schema.json` | schema tightening | ~17 diff lines | Added `claim_tier`, T3/T4 conditional `model_roster_hash` requirement, and `no_audit_chain` description preserving enum compatibility. |
| `benchmark/governed_agent_bench/schema/score.schema.json` | schema tightening | ~8 diff lines | Added top-level required `claim_tier`, strengthened `scorer_config_hash`, aligned `model_roster_hash` semantics, and clarified `no_audit_chain`. |

No supporting schemas were edited.

## Cross-schema invariant check

- `runtime_mode` enum: consistent across `trajectory.schema.json`,
  `score.schema.json`, `task.schema.json`, and `model_roster.schema.json`
  as `full_contract`, `no_validation`, `no_agent_safe`,
  `no_proposal_gate`, `no_refusal`, `no_audit_chain`,
  `no_runtime_enforcement`.
- `claim_tier` values: consistent across `trajectory.schema.json` and
  `score.schema.json` as `T0`, `T1`, `T2`, `T3`, `T4`. Score artifacts
  now require `claim_tier`; both schemas require `model_roster_hash`
  when `claim_tier` is `T3` or `T4`.
- `model_identity` structure: consistent across trajectory and score
  schemas for non-`rule_baseline` systems: `model_family`,
  `parameter_count`, `quantization`, `provider_snapshot`, and
  `decoding_settings`.
- `model_roster_hash` semantics: trajectory and score schemas now use
  the same description: sha256 of committed
  `benchmark/governed_agent_bench/model_roster.md`, required for T3/T4.
- `mechanism_disabled` marker shape: trajectory steps require
  `mechanism` when `step_type == "mechanism_disabled"`; score
  violations require `mechanism` for `mechanism_disabled_unexpected`;
  both use the same M4-M8 mechanism vocabulary as `task.schema.json`.

## Schema validation

- Did `trajectory.schema.json` parse as valid JSON? yes.
- Did `score.schema.json` parse as valid JSON? yes.
- Did the schemas validate cross-field references? yes. I ran a Python
  invariant check that loaded the trajectory, score, task, and model
  roster schemas, then asserted runtime-mode enums, claim-tier enums,
  model-identity required fields, mechanism vocabularies, score
  `claim_tier` requiredness, and T3/T4 `model_roster_hash`
  conditionals.

Validation commands run: `python3 -m json.tool` for both target
schemas, an inline `python3 -c` invariant script over trajectory,
score, task, and model-roster schemas, and an inline `python3 -c`
parse check over every `benchmark/governed_agent_bench/schema/*.json`.
I also ran
`uv run pytest benchmark/verification/tests/test_governed_agent_bench_schema_contracts.py -q`
with result `15 passed in 0.20s`.

## Audit-finding closures

- F-CDX-RFR-R1-04 (runtime_mode rename): closed by preserving the
  locked enum set and adding prose that `no_audit_chain` means audit
  evidence emission disabled while transaction integrity remains
  preserved. No enum value was renamed.
- F-CDX-RFR-R1-06 (required thresholds + scorer_config_hash): closed by
  confirming `scorer_config_hash` and per-metric `threshold` are
  required in `score.schema.json`, strengthening the
  `scorer_config_hash` description, and adding the locked threshold
  table plus AND-pass rule to `SCORING_SPEC.md`.
- F-CDX-RFR-R1-07 (model_identity fields): closed by confirming
  `model_identity` is required for non-`rule_baseline` trajectory and
  score artifacts, documenting the model-roster binding, and preserving
  the `fine_tuned_local` schema slot as future work only.
- F-AUDIT-4-04 (claim_tier required + trajectory T3/T4 conditional):
  closed by adding `claim_tier` to `score.schema.json` required fields
  and adding the trajectory-side T3/T4 conditional requiring
  `model_roster_hash`.

## Carry-over for batch 3+

- `model_roster.md` and `scorer_config.paper_v1.json` still need to be
  committed before paper-claim model runs. This is pre-experiment
  execution work, not batch-2 spec editing.
- Existing hand-authored trajectory artifacts do not yet carry
  `claim_tier`; that is acceptable for seed scorer validation but must
  be present on future paper-claim trajectory bundles.
- The scorer emission path should populate `claim_tier` before future
  score artifacts are validated against the tightened paper-claim
  schema. Code changes were outside the batch-2 target file list.

## Open issues

- None requiring a new framing decision in batch 2.
