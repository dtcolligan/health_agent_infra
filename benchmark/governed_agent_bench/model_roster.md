# Predeclared Model Roster — Paper v1

**Status:** predeclared candidate roster for `WP-MODEL-ROSTER-001`.
Approved by Dom on 2026-05-19 for roster inclusion only. No
model-backed trajectories before the pilot-protocol lock. Lock-day
D-O-01 selection on 2026-06-25: `option_b_qwen25_7b_together`.

This file records the narrow preprint roster currently described in
`/PAPER.md`. It is not frozen for paper-claim runs until Dom verifies the
provider IDs/pricing against live vendor docs, records the roster hash,
and locks the pilot protocol.

## Scope

This roster replaces superseded broader model-roster drafts. Current
scope is Option B mechanism ablation on one model class, with an
optional small Option C stretch.

## Roster

| Role | Model | Provider | Purpose |
|---|---|---|---|
| Rule baseline | deterministic harness | n/a | No model call; anchors routing, scorer, and reproducibility plumbing. |
| Option B default | `Qwen/Qwen2.5-7B-Instruct-Turbo` | Together AI | Single model class for the mechanism-ablation headline. |
| Option B fallback | `accounts/fireworks/models/qwen2p5-32b-instruct` | Fireworks | Use only if 7B saturates the safety-constrained subset and no `no_X` delta can surface. |
| Option C stretch | `claude-sonnet-4-6` | Anthropic | Optional cloud cell for a small `runtime_mode` x `model_class` cross-product. |

## Budget

Current paper budget: **USD 300** across all model API calls. Option B
alone should be well below USD 100; the remaining headroom covers the
optional Option C cell and one retry cycle.

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
        "billing_boundary": "Counts against the PAPER.md D-06 USD 300 aggregate model-call ceiling; deploy only if D-O-01 selects this fallback."
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

## Freeze Checklist

- [x] Verify every model ID resolves on the named provider.
- [x] Verify pricing against live vendor docs as of the run date.
- [x] Decide D-O-01: 7B default or 32B fallback. Selected
      `option_b_qwen25_7b_together` on 2026-06-25.
- [ ] Record the SHA-256 of this file and the commit SHA before any
      paper-claim model run.
- [ ] Ensure every paper-claim trajectory records the roster hash.
