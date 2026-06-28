# GovernedAgentBench Benchmark Card

**Status:** Current benchmark card, 2026-06-28.

This card describes the committed GovernedAgentBench artifact. It is
not a final paper claim and does not report model-backed performance.
Dom final review is still required before submission.

## Intended Use

GovernedAgentBench evaluates deterministic governance mechanisms in an
agent harness. It holds the model, prompt, manifest, task suite, and
scorer fixed while varying only `runtime_mode`. The reference runtime
is HAI, a local non-clinical personal-wellness runtime used to
instantiate a concrete software contract. The benchmark is designed to
admit other runtimes in future work.

The benchmark is intended for:

- measuring runtime-mode ablations under a held-constant prompt;
- evaluating whether specific deterministic contract mechanisms are
  load-bearing for constraint-respecting behavior;
- evaluating command selection against a manifest;
- evaluating structured operator actions;
- evaluating refusal of out-of-contract requests;
- evaluating respect for `agent_safe` and proposal/commit boundaries;
- evaluating narration from runtime read surfaces and audit references;
- evaluating robustness to stale contract snapshots.

The benchmark's main estimand is conditional: the marginal contribution
of a mechanism within this fixed harness, task suite, prompt, model
condition, and evidence tier.

## Non-Use And Misuse

The benchmark must not be used as:

- a universal agent-safety benchmark;
- a model leaderboard divorced from the runtime contract;
- a medical benchmark;
- evidence of diagnosis, treatment, prescribing, or clinical reasoning;
- evidence that HAI is a consumer health product;
- evidence that any model is safe for unsupervised operation over real
  private data;
- a benchmark for free-form coaching quality;
- a benchmark for live wearable integrations.

Do not collapse static oracle-pair rows, live runtime-probe rows, and
model-backed trajectories into one causal claim. Those evidence tiers
answer different questions.

## Data Provenance

The committed task set uses synthetic benchmark fixtures only. Fixture
builders live under `fixtures/` and construct state through HAI commands
under hermetic environment redirection.

Current fixtures:

- `empty_user`;
- `ready_user_minimal`;
- `read_surface_user`;
- `governance_user`;
- `drift_user`;
- `adversarial_user`.

No fixture is allowed to contain maintainer health data, live wearable
exports, live credentials, clinical records, names, email addresses, or
free text copied from a real user session.

## Private-Data Exclusions

GovernedAgentBench runs must use synthetic fixture state. The offline
reproducibility path sets hermetic state paths and does not touch the
default user HAI state. It does not use private health data, live
wearable sources, or cloud services.

## Clinical Boundary

HAI is explicitly non-clinical. The runtime contract excludes:

- diagnosis;
- treatment;
- prescribing;
- autonomous medical decisions.

L6 tasks include clinical-boundary pressure so the operator can be
scored on refusal behavior. Passing such tasks is evidence of boundary
obedience, not medical quality.

## Task Family Coverage

The current preprint task set has 28 tasks:

| Level | Count | Coverage |
|---|---:|---|
| L1 | 4 | Intent-to-command routing. |
| L2 | 4 | Setup/recovery and safe pending-state inspection. |
| L5 | 5 | Faithful narration from read surfaces and audit evidence. |
| L6 | 12 | Governance and refusal. |
| L7 | 3 | Contract drift and stale manifest behavior. |

The task schema requires `load_bearing_mechanisms` and
`runtime_modes_in_scope`. Static oracle-pair tests cover each ablatable
mechanism M4..M8 with at least 3 tasks. These tests are scorer/coverage
canaries, not live mechanism-causality proof.

## Runtime Modes

The prompt is held constant. Runtime mode is the treatment. Runtime
modes are:

- `full_contract`;
- `no_validation`;
- `no_agent_safe`;
- `no_proposal_gate`;
- `no_refusal`;
- `no_audit_chain`;
- `no_runtime_enforcement`.

The model is not told which mode is active. Mechanism-off modes are
allowed only under hermetic benchmark state.

## Mechanisms Under Test

| ID | Mechanism | Disable mode | Load-bearing consequence |
|---|---|---|---|
| M4 | Validation of typed commands and proposal payloads | `no_validation` | Malformed or unsupported structure can leak past the contract. |
| M5 | `agent_safe` dispatch refusal | `no_agent_safe` | Agent-context calls to unsafe commands can execute instead of being refused. |
| M6 | W57 proposal/commit gate | `no_proposal_gate` | User-gated state changes can be committed without explicit user confirmation. |
| M7 | Clinical-boundary and forbidden-request refusal | `no_refusal` | Out-of-contract requests can reach user-facing output. |
| M8 | Audit evidence emission | `no_audit_chain` | The runtime may omit evidence needed for faithful narration and traceability. |
| M9-TX | Transaction integrity | Held constant | Not ablated; protects atomicity across all modes. |

## Model Conditions Tested

Committed tested condition:

- `model_class=rule_baseline`;
- `system_id=rule_baseline_v1`;
- no model call;
- synthetic fixtures only;
- offline rule-baseline ablation dry run available through
  `reproduce_offline.py`.

Not yet tested:

- local language models;
- cloud language models;
- fine-tuned local models.

Model-backed runs require Dom approval of `WP-MODEL-ROSTER-001` before
any trajectory is produced.

## Scorer

The deterministic scorer is offline and does not call models. It
records `scorer_version` and `scorer_config_hash` and emits
`governed_agent_bench.score.v2` scores.

Current implemented checks include:

- task success;
- valid-command rate;
- correct-command rate;
- hallucinated-command rate;
- refusal accuracy;
- unsafe-action rate;
- direct-state-write attempt rate;
- clinical-claim rate;
- unsupported-narration rate;
- audit-reference faithfulness;
- exit-code recovery accuracy;
- drift robustness.

Known-good and known-bad hand-authored trajectories are committed and
tested, including L5 audit-reference faithfulness and L7 stale-manifest
drift exhibits.

## Known Blind Spots

Current limitations:

- The task set is synthetic and still narrow.
- The rule baseline verifies pipeline mechanics but is not model
  evidence.
- The primary claim is conditional on the fixed controller: harness,
  task suite, prompt, model condition, scorer, and evidence tier.
- Mechanisms are coupled. Per-mechanism deltas are marginal
  contributions in this runtime, not additive independent effects.
- Model-scale claims are blocked until Dom approves a predeclared model
  roster.
- Rule-baseline ablation scores are mode-tagged plumbing evidence, not
  behavioral mode-delta evidence.
- Static isolation oracles are hand-authored canaries. Live isolation
  now covers targeted hermetic runtime probes for M4-M8, but those rows
  are mechanism probes, not model-result trajectories from the 28-task
  suite. The M5/M6 live rows measure blocked-vs-allowed runtime outcome
  separately from normal unsafe-action attempt scoring.
- Unsupported narration, audit-reference faithfulness, exit-code
  recovery, drift robustness, and schema-valid proposal scoring are
  deterministic MVP heuristics and should be expanded before broad
  claims.
- The benchmark currently evaluates HAI as the reference runtime; other
  domains/runtimes are future work.

## Reproducibility

Offline reproducibility command:

```bash
uv run python benchmark/governed_agent_bench/reproduce_offline.py \
  --output-dir /tmp/gab_offline_repro
```

This regenerates synthetic fixtures, rule-baseline ablation
trajectories, scores, evidence tables, SVG figures, an error taxonomy,
and an offline reproducibility manifest.
