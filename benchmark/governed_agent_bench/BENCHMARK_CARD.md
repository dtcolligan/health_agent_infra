# GovernedAgentBench Benchmark Card

**Status:** Current benchmark card, 2026-07-04 (post-D-37
specify-vs-enforce rebuild).

This card describes the committed GovernedAgentBench artifact. It is
not a final paper claim and does not report model-backed performance.
Dom final review is still required before submission.

## Intended Use

GovernedAgentBench is a purpose-built instrument for the *Told or
Enforced* specify-vs-enforce paper. It evaluates deterministic
governance mechanisms in an agent harness by varying two levers per
mechanism: whether the constraint is **specified** in the in-context
contract (task field `contract_arm`, told/untold) and whether the
runtime **enforces** it (`runtime_mode`). The model, prompt template,
manifest, task suite, and scorer are held fixed while those two axes
move. The reference runtime is HAI, a local non-clinical
personal-wellness runtime used to instantiate a concrete software
contract. The benchmark is designed to admit other runtimes in future
work.

Secondary use: the told-not-enforced cell (specification present, runtime
off) measures the self-enforcement a model supplies once told, separate
from runtime enforcement, a quantity a post-training evaluation could
track; the benchmark measures it and does no training.

The benchmark supports two headline contributions:

- a **substitution-measurement result**: telling the rule moves behavior
  (+24 points pooled with the runtime off) but does not stand in for
  enforcement, whose marginal value given telling is 41 points pooled and
  small only for the self-enforcing families, so substitution holds in a
  narrow corner; capability does not cleanly order it; and
- a **methodological** finding: harness blindness (withholding command
  stdout) manufactures spurious fabrication findings.

The benchmark is intended for:

- measuring the per-mechanism specify-vs-enforce 2x2 (told/untold x
  enforcement on/off) under a held-constant prompt template;
- evaluating whether specific deterministic contract mechanisms are
  necessary for constraint-respecting behavior;
- evaluating command selection against a manifest;
- evaluating structured operator actions;
- evaluating refusal of out-of-contract requests;
- evaluating respect for `agent_safe` and proposal/commit boundaries;
- evaluating narration from runtime read surfaces and audit references,
  including under blind (stdout-withheld) observation;
- evaluating robustness to stale contract snapshots.

The benchmark's main estimand is conditional: the marginal contribution
of specification and of enforcement for a mechanism within this fixed
harness, task suite, prompt template, model condition, and evidence
tier.

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

Keep the two live evidence tiers separate: the deterministic offline
scorer (pipeline mechanics and reproducibility) and the model-backed
2x2 (behavioral specify-vs-enforce effects). Offline rule-baseline
plumbing is mode-tagged evidence of pipeline correctness, not
behavioral mode-delta evidence.

## Data Provenance

The committed task set uses synthetic benchmark fixtures only. Fixture
builders live under `fixtures/` and construct state through HAI commands
under hermetic environment redirection.

Committed fixture builders:

- `empty_user`;
- `ready_user_minimal`;
- `read_surface_user`;
- `governance_user`;
- `drift_user`;
- `adversarial_user`;
- `audit_pending_user`.

The live 16-task suite references `empty_user`, `read_surface_user`,
`governance_user`, `drift_user`, and `adversarial_user`.

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

The sharp preprint suite has 36 tasks (three scenario pairs per mechanism, D-39). Each task is a labelled cell of
the per-mechanism specify-vs-enforce 2x2 (`contract_arm` told/untold x
runtime enforcement on/off), plus an operate floor and a conflict/blind
extension for the mechanisms that need one.

| Level | Count | Coverage |
|---|---:|---|
| L1 | 2 | Operate floor: intent-to-command routing and read (`full_contract` only). |
| L2 | 2 | M4 validation: recover from a `USER_INPUT` exit (told/untold). |
| L5 | 4 | M8 audit: faithful narration from read/audit surfaces (told, untold, conflict, blind). |
| L6 | 7 | Governance and refusal: M5 `agent_safe` (told/untold/conflict), M6 proposal gate (told/untold), M7 refusal (told/untold). |
| L7 | 1 | Contract drift on a stale manifest (uses the M4 validation mechanism). |

Task ids, grouped by mechanism:

- Operate floor: `gab_l1_operate_route`, `gab_l1_operate_read`.
- M4 validation: `gab_l2_validation_told`, `gab_l2_validation_untold`.
- M5 `agent_safe`: `gab_l6_agentsafe_told`, `gab_l6_agentsafe_untold`,
  `gab_l6_agentsafe_conflict`.
- M6 proposal gate: `gab_l6_proposalgate_told`,
  `gab_l6_proposalgate_untold`.
- M7 refusal: `gab_l6_refusal_told`, `gab_l6_refusal_untold`.
- M8 audit: `gab_l5_audit_told`, `gab_l5_audit_untold`,
  `gab_l5_audit_conflict`, `gab_l5_audit_blind`.
- Drift: `gab_l7_drift`.

Each task carries `load_bearing_mechanisms` and `runtime_modes_in_scope`
in schema `governed_agent_bench.task.v2`. Summing the per-task
runtime-mode set gives 72 task-cells; at n=4 replications this is 288
reps. The all-off `no_runtime_enforcement` sanity floor is carried by
`gab_l6_agentsafe_untold` alone.

## Axes

The prompt template is held constant. The benchmark moves two axes.

**Enforcement axis (`runtime_mode`).** Whether the runtime enforces the
mechanism:

- `full_contract`;
- `no_validation`;
- `no_agent_safe`;
- `no_proposal_gate`;
- `no_refusal`;
- `no_audit_chain`;
- `no_runtime_enforcement`.

`no_runtime_enforcement` turns M4-M8 off together and is the all-off
sanity floor, carried by `gab_l6_agentsafe_untold` only. The model is
not told which mode is active. Mechanism-off modes are allowed only
under hermetic benchmark state.

**Contract-in-prompt axis (`contract_arm`).** Whether the constraint is
specified to the agent. `told` (default) presents the full manifest;
`untold` withholds the manifest facts that specify the task's
load-bearing mechanism, plus the parameterized boundary-prose blocks in
`prompts/deployment_full_v2.md` (`{{agent_safe_boundary}}`,
`{{refusal_boundary}}`) for M5/M7. The `told` rendering is
byte-preserved.

**Blind observation (`hide_stdout`).** An orthogonal task field that
withholds command stdout from the model's observation feedback.
`gab_l5_audit_blind` is the blind twin of `gab_l5_audit_told` and
underwrites the harness-blindness methodological finding.

## Mechanisms Under Test

| ID | Mechanism | Disable mode | Load-bearing consequence |
|---|---|---|---|
| M4 | Validation of typed commands and proposal payloads | `no_validation` | Malformed or unsupported structure can leak past the contract. |
| M5 | `agent_safe` dispatch refusal | `no_agent_safe` | Agent-context calls to unsafe commands can execute instead of being refused. |
| M6 | W57 proposal/commit gate | `no_proposal_gate` | User-gated state changes can be committed without explicit user confirmation. |
| M7 | Clinical-boundary and forbidden-request refusal | `no_refusal` | Out-of-contract requests can reach user-facing output. |
| M8 | Audit evidence emission | `no_audit_chain` | The runtime may omit evidence needed for faithful narration and traceability. |
| M9-TX | Transaction integrity | Held constant | Not ablated; protects atomicity across all modes. |

M4-M7 are context-verifiable mechanisms: the agent could in principle
satisfy the constraint from the in-context contract alone. M8 (audit
reference faithfulness) is the pre-registered non-verifiable exception
in the mechanism inventory. M9-TX is held constant and is not ablatable.

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
- Model-backed claims are blocked until Dom approves a predeclared model
  roster.
- Rule-baseline ablation scores are mode-tagged plumbing evidence, not
  behavioral mode-delta evidence.
- The static oracle-pair isolation matrix and the live isolation sweep
  were retired in the D-37 rebuild. Evidence is now the deterministic
  offline scorer plus the model-backed specify-vs-enforce 2x2. The
  adversarial arm is future work only.
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

The sharp pipeline (D-37) runs rule-baseline ablation -> evidence
tables -> figures -> error taxonomy. It regenerates synthetic fixtures,
rule-baseline ablation trajectories, scores, evidence tables, SVG
figures, an error taxonomy, and an offline reproducibility manifest. It
is deterministic and offline: no model call, no network. Results
generators live under `results/` (`evidence_tables.py`,
`error_taxonomy.py`, `figures.py`, `pilot_evidence.py`).
`REPRODUCIBILITY_GOLDEN.json` fingerprints the expected outputs.
