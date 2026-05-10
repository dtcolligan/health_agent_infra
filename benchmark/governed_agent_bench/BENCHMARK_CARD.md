# GovernedAgentBench Benchmark Card

**Status:** Current benchmark card, 2026-05-10.

This card describes the committed GovernedAgentBench artifact. It is
not a final paper claim and does not report model-backed performance.
Dom final review is still required before submission.

## Intended Use

GovernedAgentBench evaluates whether an operator can use a governed
runtime through an explicit software contract. The first reference
runtime is HAI, a local non-clinical personal-wellness runtime.

The benchmark is intended for:

- evaluating command selection against a manifest;
- evaluating structured operator actions;
- evaluating refusal of out-of-contract requests;
- evaluating respect for `agent_safe` and proposal/commit boundaries;
- evaluating narration from runtime read surfaces and audit references;
- evaluating robustness to stale contract snapshots;
- measuring runtime-mode ablations under a held-constant prompt.

## Non-Use And Misuse

The benchmark must not be used as:

- a medical benchmark;
- evidence of diagnosis, treatment, prescribing, or clinical reasoning;
- evidence that HAI is a consumer health product;
- evidence that any model is safe for unsupervised operation over real
  private data;
- a benchmark for free-form coaching quality;
- a benchmark for live wearable integrations.

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

The current MVP task set has 10 tasks:

| Level | Count | Coverage |
|---|---:|---|
| L1 | 2 | Intent-to-command routing. |
| L2 | 2 | Setup/recovery and safe pending-state inspection. |
| L5 | 2 | Faithful narration from read surfaces and audit evidence. |
| L6 | 2 | Governance and refusal. |
| L7 | 2 | Contract drift and stale manifest behavior. |

The task schema requires `load_bearing_mechanisms` and
`runtime_modes_in_scope`. A committed test proves each ablatable
mechanism M4..M8 is load-bearing in at least one MVP task.

## Runtime Modes

The prompt is held constant at `deployment_full_v1`. Runtime modes are:

- `full_contract`;
- `no_validation`;
- `no_agent_safe`;
- `no_proposal_gate`;
- `no_refusal`;
- `no_audit_chain`;
- `no_runtime_enforcement`.

The model is not told which mode is active. Mechanism-off modes are
allowed only under hermetic benchmark state.

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
- clinical-claim rate.

Known-good and known-bad hand-authored trajectories are committed and
tested.

## Known Blind Spots

Current limitations:

- The MVP task set is small and synthetic.
- The rule baseline verifies pipeline mechanics but is not model
  evidence.
- Model-scale claims are blocked until Dom approves a predeclared model
  roster.
- Unsupported narration, drift robustness, and schema-valid proposal
  scoring remain MVP-level and should be expanded before broad claims.
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
