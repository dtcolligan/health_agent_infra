# Methods And System Draft

**Status:** Draft section for `WP-PAPER-002`, 2026-05-10.

This draft describes committed implementation artifacts as of commit
`3cdd69b` and avoids interpreting model results. It is intentionally
separate from `DRAFT_PAPER.md`, which currently has user-owned dirty
changes.

## System: Runtime Contracts In HAI

The runtime contract is implemented as a local software boundary around
agent operation. The model or rule baseline emits structured operator
actions, but HAI owns validation, state mutation, policy gates, refusal
boundaries, and audit. The benchmark-facing contract is exposed through
`agent_cli_contract.v2` manifests and frozen benchmark snapshots.

HAI's contract surface includes:

- a capabilities manifest with command metadata, mutation classes,
  refusal taxonomies, exit-code semantics, and `agent_safe` flags;
- typed CLI commands rather than arbitrary shell execution;
- proposal/commit separation for user-authored intent and target rows;
- deterministic schema and policy validation before durable writes;
- runtime refusal envelopes for forbidden clinical or authority-crossing
  actions;
- audit-chain read surfaces used by `hai today`, `hai explain`, and
  review commands.

The runtime-mode axis ablates enforcement mechanisms while leaving the
deployment prompt path constant. The v2 trajectory schema records
`runtime_mode`, `model_class`, `manifest_snapshot_id`,
`prompt_template_id`, `prompt_template_hash`, and
`invocation_context`. Runtime modes are:

- `full_contract`;
- `no_validation`;
- `no_agent_safe`;
- `no_proposal_gate`;
- `no_refusal`;
- `no_audit_chain`;
- `no_runtime_enforcement`.

The held-constant controls are the operator-action envelope, the
structured action schema, the harness command allowlist, and transaction
integrity. The transaction invariant is not ablated because disabling it
would make runtime-mode comparisons uninterpretable.

## Harness

The model-agnostic harness lives under
`benchmark/governed_agent_bench/harness/`. It loads a task, loads the
manifest snapshot named by that task, renders the single
deployment-realistic prompt template, validates structured operator
actions against the manifest command surface, executes HAI in a hermetic
synthetic fixture environment, records observations, captures
`mechanism_disabled` markers from stderr, and writes v2 trajectories.

Harness executions set:

- `HAI_HERMETIC=1`;
- `HAI_STATE_DB=<fixture>/state.db`;
- `HAI_BASE_DIR=<fixture>/base`;
- `HAI_RUNTIME_MODE=<runtime_mode>`;
- `HAI_INVOCATION_CONTEXT=<agent|rule_baseline>`.

`rule_baseline` trajectories use `invocation_context=rule_baseline`.
Model-backed runs must use `invocation_context=agent`; the harness
refuses inconsistent `model_class` / invocation-context combinations.

The prompt path is intentionally singular. Every condition uses
`deployment_full_v1`; the experiment varies runtime mode, not prompt
content. Trajectories record both rendered-prompt and prompt-template
hashes so drift can be detected.

## GovernedAgentBench Task Set

The current MVP task set contains 10 committed tasks:

- 2 L1 routing tasks;
- 2 L2 setup/recovery tasks;
- 2 L5 faithful-narration tasks;
- 2 L6 governance/refusal tasks;
- 2 L7 contract-drift tasks.

The current synthetic fixture set contains six builders:

- `empty_user`;
- `ready_user_minimal`;
- `read_surface_user`;
- `governance_user`;
- `drift_user`;
- `adversarial_user`.

The task schema requires `load_bearing_mechanisms` and
`runtime_modes_in_scope`. The current tests prove that every ablatable
mechanism M4..M8 is declared by at least one MVP task and that paired
full/off oracle trajectories produce a primary-metric delta for each
mechanism.

## Trajectories And Scoring

Trajectory artifacts use `governed_agent_bench.trajectory.v2`. A
trajectory contains system identity, runtime mode, model class, manifest
snapshot, prompt hashes, invocation context, and ordered steps. Steps
may be messages, commands, observations, refusals, finals, or
`mechanism_disabled` markers.

The deterministic scorer produces `governed_agent_bench.score.v2` rows.
It reports:

- task success;
- valid-command rate;
- correct-command rate;
- hallucinated-command rate;
- schema validity;
- refusal accuracy;
- unsafe-action rate;
- direct-state-write attempt rate;
- clinical-claim rate.

Scores include `scorer_version` and `scorer_config_hash`, and the score
schema requires non-null thresholds for reported metrics. The benchmark
currently includes 10 hand-authored trajectories: one passing and one
failing trajectory for each of five representative tasks. Tests assert
that known-good trajectories pass, known-bad trajectories fail, and at
least four violation kinds are exercised by the seed failures.

## Baselines And Offline Reproducibility

The committed no-model baseline is `rule_baseline_v1`. It emits
structured operator actions through the same harness path as future
model-backed runs. Its report separates routing-only L1 tasks from
judgement-bearing tasks.

The offline ablation runner executes `rule_baseline_v1` across each
task's declared `runtime_modes_in_scope`. This is a scaffold dry run,
not a model result. It verifies that the benchmark can regenerate
trajectories, observations, scores, evidence tables, figures, and error
taxonomy artifacts without local or cloud model calls.

The reproducibility command is:

```bash
uv run python benchmark/governed_agent_bench/reproduce_offline.py \
  --output-dir /tmp/gab_offline_repro
```

It writes:

- rule-baseline ablation trajectories and scores;
- `evidence_table.json` and `evidence_table.csv`;
- SVG summary figures;
- `error_taxonomy.json`;
- `offline_repro_manifest.json`.

This path uses only synthetic fixtures. It does not call model APIs,
cloud services, live wearable sources, or private health data.

## Measurement Plan

The workshop-floor infrastructure supports the following evidence
ladder:

1. **T0 infrastructure:** reproducible benchmark artifacts exist and can
   be regenerated offline.
2. **T1 mechanism effect:** at least one M4..M8 ablation changes a
   primary metric under a tested `model_class`.
3. **T2 component ranking:** mechanism-off conditions can be compared
   by effect size.
4. **T3+ model-scale claims:** require a predeclared model roster before
   any model-backed trajectory.

As of this draft, model-roster approval remains a Dom judgement gate.
No local or cloud model-backed trajectories are claimed here.

## Threats To Validity

The current no-model pipeline verifies benchmark mechanics, not model
capability. The task set is intentionally small and synthetic. Health
domain content is non-clinical by construction, so results should not be
read as medical reasoning or advice quality. The scorer is deterministic
and inspectable, but it only measures the metrics currently encoded in
the MVP score logic. Model-scale and claim-strength conclusions require
Dom-approved model roster decisions and post-run claim review.
