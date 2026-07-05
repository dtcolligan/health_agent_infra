# Predeclared Model Roster — Paper v1

**Status:** predeclared candidate roster for `WP-MODEL-ROSTER-001`. The
working-model selection was superseded by D-33 (2026-07-01): the working
model is now `Qwen/Qwen3-235B-A22B-Instruct-2507-tput` (Together
serverless), resolving the old D-O-01 `option_b_qwen25_7b_together`
choice. No model-backed trajectories before the pilot-protocol lock.

This file records the narrow preprint roster described in `/PAPER.md`.
**Re-locked as `roster_v2` on 2026-07-05:** the machine-readable block now
leads with the vendor-verified `primary_qwen3_235b_together` condition
(provider ID, serverless deployment, FP8 serving, and $0.20/$0.60 per 1M
pricing verified live by Dom on the Together model page). The superseded
7B/32B/Sonnet conditions are retained for provenance and harness/test
compatibility (`roster_condition` still resolves them); they are not run
targets. Remaining before any paper-claim run: record the roster hash and
lock the pilot protocol.

## Scope

This roster replaces superseded broader model-roster drafts. Current
scope is Option B mechanism ablation on one model class, with an
optional small Option C stretch.

## Roster

Working roster (D-33; machine-readable block re-locked as `roster_v2`,
2026-07-05):

| Role | Model | Provider | Purpose |
|---|---|---|---|
| Rule baseline | deterministic harness | n/a | No model call; anchors routing, scorer, and reproducibility plumbing. |
| Working model | `Qwen/Qwen3-235B-A22B-Instruct-2507-tput` | Together AI (serverless) | The capable cooperative agent above the operate floor for the 2×2. |
| Audit fallback | `claude-sonnet-4-6` | Anthropic | Reliable fallback for narration-heavy audit (M8) tests. |
| Capability ladder | small screened set above the operate floor | Together serverless | Bounded moderator (D-34/D-36), not a scaling-law claim. |
| Excluded | `Qwen2.5-7B`, `Qwen2.5-32B`, `Mistral-Small-24B`, `Gemma-3-27B`, `Gemma-4-31B` | — | Below the operate floor as configured, or excluded per `/PAPER.md` Model Roster. |

## Budget

Current paper budget: **USD 300** across all model API calls. Option B
alone should be well below USD 100; the remaining headroom covers the
optional Option C cell and one retry cycle.

## Machine-Readable Roster

```json
{
  "schema_version": "governed_agent_bench.model_roster.v1",
  "roster_id": "roster_v2",
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
      "condition_id": "primary_qwen3_235b_together",
      "system_id": "primary_qwen3_235b_together_v1",
      "model_class": "cloud",
      "model_family": "qwen3-instruct-moe",
      "model_id": "Qwen/Qwen3-235B-A22B-Instruct-2507-tput",
      "provider": "Together AI",
      "provider_snapshot_date": "2026-07-05",
      "model_card_snapshot": "https://www.together.ai/models/qwen3-235b-a22b-instruct-2507-fp8",
      "parameter_count": "235B total / 22B active (MoE)",
      "quantization": "FP8 provider serving (model page: Qwen3 235B A22B Instruct 2507 FP8 Throughput)",
      "weights_source": "Qwen3 235B A22B Instruct 2507 (non-thinking) via Together AI serverless throughput endpoint; 262K context",
      "compute_boundary": {
        "hardware": "Together AI managed serverless inference",
        "runtime": "Together AI chat completions API",
        "max_wall_time_minutes": 240,
        "network_access": true
      },
      "cost_boundary": {
        "budget_type": "approved_cloud_budget",
        "max_cost_usd": 100.0,
        "billing_boundary": "Counts against the PAPER.md D-06 USD 300 aggregate model-call ceiling. Vendor-verified 2026-07-05 on the live Together model page: input $0.20/1M tokens, output $0.60/1M tokens."
      },
      "data_boundary": "synthetic_governed_agent_bench_fixtures_only",
      "decoding_settings": {
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 2048,
        "seed": "provider_does_not_support_seed"
      },
      "prompt_id": "deployment_full_v2",
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
        "approval_id": "d33_roster_reselection_dom_2026_07_01",
        "approved_by": "Dom",
        "approved_at": "2026-07-01",
        "approved_scope": "Working-model selection per PAPER.md D-33; provider ID, pricing, quantization, and model-card URL vendor-verified live by Dom (browser session) on 2026-07-05."
      }
    },
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
      "prompt_id": "deployment_full_v2",
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
      "prompt_id": "deployment_full_v2",
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
      "prompt_id": "deployment_full_v2",
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

- [x] Decide the working model. D-O-01 (`option_b_qwen25_7b_together`)
      was superseded by D-33: working model is
      `Qwen/Qwen3-235B-A22B-Instruct-2507-tput`.
- [x] Re-lock the machine-readable block: `roster_v2` adds
      `primary_qwen3_235b_together` with vendor-verified provider ID,
      model-card URL, snapshot date (2026-07-05), and pricing
      ($0.20/$0.60 per 1M) from the live Together model page.
- [x] Verify the model ID resolves on Together serverless: the live page
      lists Serverless deployment for endpoint
      `QWEN/QWEN3-235B-A22B-INSTRUCT-2507-TPUT` (verified 2026-07-05).
- [ ] Record the SHA-256 of this file and the commit SHA before any
      paper-claim model run.
- [ ] Ensure every paper-claim trajectory records the roster hash.
