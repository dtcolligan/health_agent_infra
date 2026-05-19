# Predeclared Model Roster - Paper v1

Status: predeclared candidate roster for `WP-MODEL-ROSTER-001`.
Approved by Dom on 2026-05-19 for roster inclusion only. This file
does not authorize model-backed trajectories before the mid-June
pilot-protocol lock.

Paper: *Deterministic Software Contracts as Trusted Monitors in AI
Control Protocols*.

## Scope

This roster replaces the superseded nine-entry Houdini/Guard roster.
The current preprint scope is narrow:

- Option B headline: one model class over the 28-task suite with
  `full_contract`, the five single-mechanism-off modes, and
  `no_runtime_enforcement`.
- Option B default: `Qwen/Qwen2.5-7B-Instruct-Turbo` on Together AI.
- Option B fallback: `accounts/fireworks/models/qwen2p5-32b-instruct`
  on Fireworks AI, only if D-O-01 triggers because the 7B condition
  saturates the safety-constrained subset and cannot surface deltas.
- Option C stretch: `claude-sonnet-4-6` on the Anthropic Claude API,
  only if the substrate remains clean after Option B.

No Engels extension, LLM-Guard, HS contrast, local fine-tuning, or full
model-scale roster cell is authorized by this file.

## Cost Ceiling

Total model API spend remains capped at USD 300 across all model calls
per `PAPER.md` D-06. The per-condition ceilings below are accounting
reserves, not permission to spend all three reserves. Stop spending if
the cumulative run log reaches USD 300 or if any provider price has
changed materially since the provider snapshot date.

## Provider Snapshot

Provider facts were checked on 2026-05-19:

- Together AI lists `Qwen/Qwen2.5-7B-Instruct-Turbo` as the endpoint,
  with 7B parameters, FP8 serving, 32K context, and $0.30 / 1M input
  plus $0.30 / 1M output tokens.
- Fireworks lists `accounts/fireworks/models/qwen2p5-32b-instruct` as
  ready, backed by Hugging Face `Qwen/Qwen2.5-32B-Instruct`, with
  32.7B parameters. The model page marks serverless as not supported;
  use requires on-demand deployment setup if D-O-01 selects this
  fallback. Fireworks docs price non-headline dense models over 16B
  parameters at $0.90 / 1M tokens for input and output unless a
  model-specific price supersedes it.
- Anthropic lists `claude-sonnet-4-6` as the Claude API ID, priced at
  $3 / 1M input tokens and $15 / 1M output tokens, with 1M context and
  64K max synchronous output.

## Hash Discipline

Every paper-claim trajectory and score at claim tier T3/T4 must record
the SHA-256 of the complete bytes of this file:

```bash
sha256sum benchmark/governed_agent_bench/model_roster.md
```

Record that hash and the commit SHA in the model run log before any
model-backed trajectory is generated. Entries are immutable after the
first model-backed trajectory; additions require a new `roster_id`.

## Machine-Readable Roster

```json
{
  "schema_version": "governed_agent_bench.model_roster.v1",
  "roster_id": "roster_v1",
  "roster_file": "benchmark/governed_agent_bench/model_roster.md",
  "hash_algorithm": "sha256",
  "hash_scope": "entire_model_roster_md_file_bytes",
  "status": "predeclared",
  "approved_by": "Dom",
  "approved_at": "2026-05-19",
  "decision_path": "predeclared_model_roster",
  "scope": {
    "data_boundary": "synthetic_governed_agent_bench_fixtures_only",
    "private_data_allowed": false,
    "cloud_or_paid_api_allowed": true,
    "local_download_allowed": false,
    "notes": "Roster inclusion only. No model-backed trajectories before the pilot-protocol lock. No private health data, live wearable rows, or hosted production state may be sent to model providers."
  },
  "conditions": [
    {
      "condition_id": "option_b_qwen25_7b_together",
      "system_id": "option_b_qwen25_7b_together_v1",
      "model_class": "cloud",
      "model_family": "qwen2.5-instruct",
      "model_id": "Qwen/Qwen2.5-7B-Instruct-Turbo",
      "provider": "Together AI",
      "provider_snapshot_date": "2026-05-19",
      "model_card_snapshot": "https://www.together.ai/models/qwen2-5-7b-instruct-turbo",
      "parameter_count": "7B",
      "quantization": "FP8 provider serving",
      "weights_source": "Qwen2.5 7B Instruct Turbo via Together AI serverless inference",
      "compute_boundary": {
        "hardware": "Together AI managed serverless inference",
        "runtime": "Together AI chat completions API",
        "max_wall_time_minutes": 240,
        "network_access": true
      },
      "cost_boundary": {
        "budget_type": "approved_cloud_budget",
        "max_cost_usd": 100.0,
        "billing_boundary": "Counts against the PAPER.md D-06 USD 300 aggregate model-call ceiling."
      },
      "data_boundary": "synthetic_governed_agent_bench_fixtures_only",
      "decoding_settings": {
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 2048,
        "seed": "provider_does_not_support_seed"
      },
      "prompt_id": "deployment_full_v1",
      "manifest_id": "hai_0_2_0",
      "runtime_modes": [
        "full_contract",
        "no_validation",
        "no_agent_safe",
        "no_proposal_gate",
        "no_refusal",
        "no_audit_chain",
        "no_runtime_enforcement"
      ],
      "failure_reporting": {
        "timeout": "reportable_outcome",
        "refusal": "reportable_outcome",
        "invalid_json": "reportable_outcome",
        "adapter_failure": "reportable_outcome"
      },
      "cloud_approval": {
        "approval_id": "wp_model_roster_001_dom_2026_05_19",
        "approved_by": "Dom",
        "approved_at": "2026-05-19",
        "approved_scope": "Roster inclusion for Option B default only; model-backed run still waits for pilot-protocol lock."
      }
    },
    {
      "condition_id": "option_b_fallback_qwen25_32b_fireworks",
      "system_id": "option_b_fallback_qwen25_32b_fireworks_v1",
      "model_class": "cloud",
      "model_family": "qwen2.5-instruct",
      "model_id": "accounts/fireworks/models/qwen2p5-32b-instruct",
      "provider": "Fireworks AI",
      "provider_snapshot_date": "2026-05-19",
      "model_card_snapshot": "https://fireworks.ai/models/fireworks/qwen2p5-32b-instruct",
      "parameter_count": "32.7B",
      "quantization": "vendor_undisclosed_on_demand_serving",
      "weights_source": "Qwen/Qwen2.5-32B-Instruct via Fireworks model library",
      "compute_boundary": {
        "hardware": "Fireworks on-demand deployment; exact GPU class recorded at run time",
        "runtime": "Fireworks API using an on-demand deployment",
        "max_wall_time_minutes": 240,
        "network_access": true
      },
      "cost_boundary": {
        "budget_type": "approved_cloud_budget",
        "max_cost_usd": 100.0,
        "billing_boundary": "Counts against the PAPER.md D-06 USD 300 aggregate model-call ceiling; deploy only if D-O-01 selects the 32B fallback."
      },
      "data_boundary": "synthetic_governed_agent_bench_fixtures_only",
      "decoding_settings": {
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 2048,
        "seed": "provider_does_not_support_seed"
      },
      "prompt_id": "deployment_full_v1",
      "manifest_id": "hai_0_2_0",
      "runtime_modes": [
        "full_contract",
        "no_validation",
        "no_agent_safe",
        "no_proposal_gate",
        "no_refusal",
        "no_audit_chain",
        "no_runtime_enforcement"
      ],
      "failure_reporting": {
        "timeout": "reportable_outcome",
        "refusal": "reportable_outcome",
        "invalid_json": "reportable_outcome",
        "adapter_failure": "reportable_outcome"
      },
      "cloud_approval": {
        "approval_id": "wp_model_roster_001_dom_2026_05_19",
        "approved_by": "Dom",
        "approved_at": "2026-05-19",
        "approved_scope": "Roster inclusion for D-O-01 fallback only; model-backed run still waits for pilot-protocol lock."
      }
    },
    {
      "condition_id": "option_c_stretch_claude_sonnet_46",
      "system_id": "option_c_stretch_claude_sonnet_46_v1",
      "model_class": "cloud",
      "model_family": "claude-sonnet-4.6",
      "model_id": "claude-sonnet-4-6",
      "provider": "Anthropic",
      "provider_snapshot_date": "2026-05-19",
      "model_card_snapshot": "https://platform.claude.com/docs/en/about-claude/models/overview",
      "parameter_count": "vendor_undisclosed",
      "quantization": "vendor_undisclosed",
      "weights_source": "Anthropic first-party Claude API",
      "compute_boundary": {
        "hardware": "Anthropic managed cloud inference",
        "runtime": "Anthropic Messages API",
        "max_wall_time_minutes": 120,
        "network_access": true
      },
      "cost_boundary": {
        "budget_type": "approved_cloud_budget",
        "max_cost_usd": 100.0,
        "billing_boundary": "Counts against the PAPER.md D-06 USD 300 aggregate model-call ceiling; run only as Option C stretch after Option B is clean."
      },
      "data_boundary": "synthetic_governed_agent_bench_fixtures_only",
      "decoding_settings": {
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 2048,
        "seed": "provider_does_not_support_seed"
      },
      "prompt_id": "deployment_full_v1",
      "manifest_id": "hai_0_2_0",
      "runtime_modes": [
        "full_contract",
        "no_runtime_enforcement"
      ],
      "failure_reporting": {
        "timeout": "reportable_outcome",
        "refusal": "reportable_outcome",
        "invalid_json": "reportable_outcome",
        "adapter_failure": "reportable_outcome"
      },
      "cloud_approval": {
        "approval_id": "wp_model_roster_001_dom_2026_05_19",
        "approved_by": "Dom",
        "approved_at": "2026-05-19",
        "approved_scope": "Roster inclusion for optional Option C stretch only; model-backed run still waits for pilot-protocol lock."
      }
    }
  ],
  "immutability_rule": "Entries are immutable after the first model-backed trajectory; additions require a new roster_id."
}
```

## Pilot-Lock Checklist

- Recompute this file's SHA-256 after the roster commit.
- Reconfirm provider availability and pricing before the first
  model-backed trajectory.
- Record the final D-O-01 choice: default 7B, or 32B fallback only if
  the 7B condition saturates the safety-constrained subset.
- Record the task-suite hash, prompt-template hash, scorer-config hash,
  and manifest snapshot id in the run log.
- Keep static canaries, live runtime probes, and model-backed results in
  separate evidence tiers.
