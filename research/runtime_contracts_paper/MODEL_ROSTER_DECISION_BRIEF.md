# Model Roster Decision Brief

**Status:** Dom judgement brief for `WP-MODEL-ROSTER-001`,
2026-05-10.

This is not a model roster, not an experiment authorization, and not a
claim update. It exists to make the current gate explicit before any
model-backed trajectory, local model download, cloud provider call, or
stronger paper claim is produced.

## Current Gate

Autonomous execution is blocked at `WP-MODEL-ROSTER-001`.

Verified current state:

- `benchmark/governed_agent_bench/model_roster.md` is absent.
- The committed tested condition is `rule_baseline_v1` only.
- No model-backed trajectories have been produced.
- Cloud, paid, and model API runs remain disallowed without explicit
  Dom approval.

## Decision Needed

Dom should choose one path before Codex proceeds.

### Path A: Predeclared Model Roster

Choose this path if the workshop package should include model-backed
baseline or ablation evidence.

Dom must approve:

- the allowed model families and exact model identifiers;
- whether each model is local, cloud, hosted, or fine-tuned;
- any allowed downloads, local compute, or runtime budget;
- any allowed paid/cloud provider, API budget, and billing boundary;
- the data boundary, restricted to synthetic GovernedAgentBench
  fixtures unless a separate explicit approval says otherwise;
- decoding settings and run determinism posture;
- whether failed/incomplete runs are still reported.

After this approval, Codex may author and commit
`benchmark/governed_agent_bench/model_roster.md` before any model run.
Only then may Codex implement adapters or execute runs within the
approved scope.

### Path B: Rule-Baseline-Only Workshop Package

Choose this path if the workshop submission should make a narrower T0
infrastructure claim with no model-backed evidence.

Under this path, Codex may:

- revise the claim ladder to rule-baseline-only evidence;
- draft results and discussion from the offline rule baseline,
  deterministic ablations, hand-authored trajectories, and scorer
  validation;
- frame the contribution as runtime substrate, benchmark artifact,
  reproducibility package, and measurement protocol;
- explicitly state that model-scale conclusions are future work.

Codex must not imply model viability, scaling behavior, or comparative
model performance under this path.

## Required Roster Fields

If Dom chooses Path A, the first roster commit should include one
immutable entry per condition with these fields:

| Field | Required content |
|---|---|
| `roster_id` | Stable identifier, for example `roster_v1`. |
| `condition_id` | Stable per-model/run condition identifier. |
| `model_family` | Family name, such as Llama, Qwen, Mistral, Claude, GPT, or other approved family. |
| `model_id` | Exact model identifier or local artifact name. |
| `model_class` | `local_lm`, `cloud_lm`, `fine_tuned_local_lm`, or another predeclared class. |
| `provider` | Local runtime or approved provider name. |
| `provider_snapshot_date` | Date used to freeze provider or model-card metadata. |
| `model_card_snapshot` | URL, file path, or documented absence. |
| `parameter_count` | Parameter count or documented unknown. |
| `quantization` | Quantization setting or `none`. |
| `weights_source` | Approved local path, download source, or hosted endpoint name. |
| `compute_boundary` | Approved device, hardware class, and runtime constraints. |
| `cost_boundary` | Approved budget or `local_only_no_paid_api`. |
| `data_boundary` | Synthetic fixture state only unless Dom explicitly broadens scope. |
| `temperature` | Numeric decoding setting. |
| `top_p` | Numeric decoding setting or `not_applicable`. |
| `max_tokens` | Maximum output tokens per call. |
| `seed` | Seed value or documented provider limitation. |
| `prompt_id` | Expected prompt path, currently `deployment_full_v1`. |
| `manifest_id` | Frozen manifest identifier used for runs. |
| `runtime_modes` | Runtime modes approved for this condition. |
| `failure_reporting` | Whether timeout, refusal, invalid JSON, and adapter failure count as reportable outcomes. |
| `immutability_rule` | Roster entries cannot change after the first model-backed trajectory; additions require a new roster id. |

The roster commit should also include a roster hash or a documented hash
procedure so trajectories can record the roster state they used.

## Hard Stops

Codex must stop and ask before:

- creating `model_roster.md` with any specific model choice;
- downloading local weights or installing model runtimes;
- executing local model inference;
- calling a cloud or paid model API;
- using live credentials, private health data, live wearable exports, or
  non-synthetic user data;
- changing the clinical boundary, W57, proposal/commit separation, audit
  chain, Strava exclusion, MCP autoload exclusion, or threshold-mutation
  governance decisions;
- strengthening the claim ladder or paper discussion beyond the evidence
  path Dom selected.

## Recommended Default Without Model Approval

If no model evidence is approved, the safest workshop path is Path B: a
rule-baseline-only T0 infrastructure paper.

That package can still be coherent if it is explicit that the evidence
supports the runtime contract, benchmark harness, deterministic scorer,
fixtures, ablation protocol, and reproducibility workflow. It should not
claim that smaller local models are empirically viable operators until
model-backed trajectories exist under a predeclared roster.

## Next Codex Actions After Dom Decision

If Dom chooses Path A:

- author `benchmark/governed_agent_bench/model_roster.md`;
- add or document the roster hash;
- wire `model_roster_hash` into model-backed trajectory metadata if not
  already present;
- implement only the approved adapter path;
- run only approved local or cloud conditions;
- generate evidence tables, figures, taxonomy, and paper text from the
  resulting committed outputs.

If Dom chooses Path B:

- update the claim ladder to T0-only evidence;
- draft results and discussion around offline artifacts only;
- add final limitations and reproducibility language;
- run the final offline verification suite;
- prepare the final audit/status packet for Dom review.
