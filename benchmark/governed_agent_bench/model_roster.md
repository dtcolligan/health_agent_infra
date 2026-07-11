# Predeclared Model Roster — Paper v1

**Status:** re-locked as `roster_v3` (2026-07-05, D-41): the four
run-ladder conditions lead the machine-readable block, every field
vendor-verified live by Dom (Together model pages + HF model cards) —
IDs, serverless deployment, pricing, context windows, and per-model
vendor-recommended sampling. Closes D-O-04. No model-backed trajectories
before the pilot-protocol lock.

This file records the narrow preprint roster described in `/PAPER.md`.
**History — re-locked as `roster_v2` earlier on 2026-07-05:** the machine-readable block now
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

Run ladder (D-41; machine-readable block `roster_v3`, all fields
vendor-verified live 2026-07-05):

| Role | Condition | Model | $/1M in/out | Context | Sampling (vendor-recommended) |
|---|---|---|---|---|---|
| Primary capable | `run_primary_minimax_m3` | `MiniMaxAI/MiniMax-M3` | 0.30 / 1.20 | 524K | temp 0.7, top_p 0.8, top_k 20, min_p 0 |
| Second capable (cross-family) | `run_capable_llama33_70b` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | 1.04 / 1.04 | 128K | temp 0.6, top_p 0.9 (Meta generation config) |

D-56 (2026-07-11): Together removed `Qwen/Qwen3-235B-A22B-Instruct-2507-tput`
from serverless on 2026-07-10 (the `-FP8` variant is dedicated-endpoint-only).
`run_primary_minimax_m3` (MiniMaxAI/MiniMax-M3) is the deprecation-forced PRIMARY
replacement, canary-validated 2026-07-11: operates, mutation-gate B−D = +100pp
(replicates the deprecated 235B cross-family), refusal disposition-covered. The
deprecated 235B condition is retained (non-`run_`-prefixed) for provenance.
| Near-floor | `run_nearfloor_qwen35_9b` | `Qwen/Qwen3.5-9B` | 0.17 / 0.25 | 262K | non-thinking: temp 0.7, top_p 0.8, top_k 20, min_p 0, presence_penalty 1.5 (thinking disabled via chat_template_kwargs; disclosed) |
| Below-floor operate control | `run_belowfloor_qwen25_7b` | `Qwen/Qwen2.5-7B-Instruct-Turbo` | 0.30 / 0.30 | 32K (overflow pre-registered as expected; context_overflow category) | temp 0.7, top_p 0.8, top_k 20, rep_penalty 1.05 |

Superseded descriptive roster (D-33 era):

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
  "roster_id": "roster_v3",
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
      "condition_id": "run_primary_minimax_m3",
      "system_id": "run_primary_minimax_m3_v1",
      "model_class": "cloud",
      "model_family": "minimax-m3-moe",
      "model_id": "MiniMaxAI/MiniMax-M3",
      "provider": "Together AI",
      "provider_snapshot_date": "2026-07-11",
      "model_card_snapshot": "https://www.together.ai/models/minimax-m3",
      "parameter_count": "large MoE (parameter count not published on the provider page)",
      "quantization": "provider serverless serving",
      "weights_source": "MiniMaxAI MiniMax-M3 via Together serverless; adopted 2026-07-11 as the deprecation-forced replacement for the removed Qwen3-235B primary (D-56). Decoding matches the deprecated primary's canary-validated config.",
      "context_window": 524288,
      "compute_boundary": {
        "hardware": "Together AI managed serverless inference",
        "runtime": "Together AI chat completions API",
        "max_wall_time_minutes": 480,
        "network_access": true
      },
      "cost_boundary": {
        "budget_type": "approved_cloud_budget",
        "max_cost_usd": 50.0,
        "billing_boundary": "Together /v1/models 2026-07-11: input $0.30/1M, output $1.20/1M. D-06 USD 300 aggregate ceiling."
      },
      "data_boundary": "synthetic_governed_agent_bench_fixtures_only",
      "decoding_settings": {
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "min_p": 0,
        "max_tokens": 2048,
        "seed": "provider_does_not_support_seed"
      },
      "prompt_id": "deployment_full_v3",
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
        "adapter_failure": "reportable_outcome",
        "context_overflow": "reportable_outcome",
        "provider_filtered": "reportable_outcome",
        "length_truncation": "reportable_outcome"
      },
      "cloud_approval": {
        "approval_id": "d56_minimax_primary_dom_2026_07_11",
        "approved_by": "Dom",
        "approved_at": "2026-07-11",
        "approved_scope": "D-56 deprecation-forced PRIMARY replacement. Canary-validated 2026-07-11 (USD 0.76): operates, mutation-gate B-D=+100pp (replicates the deprecated 235B cross-family), refusal disposition-covered. Mild structured-output quirk on multi-step routing noted."
      }
    },
    {
      "condition_id": "deprecated_primary_qwen3_235b_tput",
      "system_id": "deprecated_primary_qwen3_235b_tput_v1",
      "deprecation_note": "Together AI removed this model from serverless on 2026-07-10 (verified via /v1/models 2026-07-11: the -tput endpoint is GONE, the -FP8 variant is dedicated-endpoint-only). Retained for provenance per D-41; superseded as PRIMARY by run_primary_minimax_m3 (D-56). This condition is intentionally not run_-prefixed so the ladder excludes it.",
      "model_class": "cloud",
      "model_family": "qwen3-instruct-moe",
      "model_id": "Qwen/Qwen3-235B-A22B-Instruct-2507-tput",
      "provider": "Together AI",
      "provider_snapshot_date": "2026-07-05",
      "model_card_snapshot": "https://www.together.ai/models/qwen3-235b-a22b-instruct-2507-fp8",
      "parameter_count": "235B total / 22B active (MoE)",
      "quantization": "FP8 provider serving (Throughput endpoint)",
      "weights_source": "Qwen3 235B A22B Instruct 2507 (non-thinking) via Together serverless; sampling per HF card Best Practices (verified live 2026-07-05)",
      "context_window": 262144,
      "compute_boundary": {
        "hardware": "Together AI managed serverless inference",
        "runtime": "Together AI chat completions API",
        "max_wall_time_minutes": 480,
        "network_access": true
      },
      "cost_boundary": {
        "budget_type": "approved_cloud_budget",
        "max_cost_usd": 50.0,
        "billing_boundary": "Vendor-verified 2026-07-05: input $0.20/1M, output $0.60/1M. D-06 USD 300 aggregate ceiling."
      },
      "data_boundary": "synthetic_governed_agent_bench_fixtures_only",
      "decoding_settings": {
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "min_p": 0,
        "max_tokens": 2048,
        "seed": "provider_does_not_support_seed"
      },
      "prompt_id": "deployment_full_v3",
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
        "adapter_failure": "reportable_outcome",
        "context_overflow": "reportable_outcome",
        "provider_filtered": "reportable_outcome",
        "length_truncation": "reportable_outcome"
      },
      "cloud_approval": {
        "approval_id": "d41_ladder_dom_2026_07_05",
        "approved_by": "Dom",
        "approved_at": "2026-07-05",
        "approved_scope": "D-41 run ladder PRIMARY (capable cooperative agent). Vendor-recommended non-thinking sampling per Qwen/Qwen3-235B-A22B-Instruct-2507 HF card."
      }
    },
    {
      "condition_id": "run_capable_llama33_70b",
      "system_id": "run_capable_llama33_70b_v1",
      "model_class": "cloud",
      "model_family": "llama-3.3-instruct",
      "model_id": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
      "provider": "Together AI",
      "provider_snapshot_date": "2026-07-05",
      "model_card_snapshot": "https://www.together.ai/models/llama-3-3-70b",
      "parameter_count": "70B",
      "quantization": "Turbo endpoint (FP8 per Together Turbo convention; page does not state)",
      "weights_source": "Llama 3.3 70B Instruct Turbo via Together serverless; sampling per Meta generation_config (temperature 0.6, top_p 0.9; read from the ungated unsloth mirror of the gated Meta repo, 2026-07-05)",
      "context_window": 131072,
      "compute_boundary": {
        "hardware": "Together AI managed serverless inference",
        "runtime": "Together AI chat completions API",
        "max_wall_time_minutes": 480,
        "network_access": true
      },
      "cost_boundary": {
        "budget_type": "approved_cloud_budget",
        "max_cost_usd": 50.0,
        "billing_boundary": "Vendor-verified 2026-07-05: input $1.04/1M, output $1.04/1M. D-06 USD 300 aggregate ceiling."
      },
      "data_boundary": "synthetic_governed_agent_bench_fixtures_only",
      "decoding_settings": {
        "temperature": 0.6,
        "top_p": 0.9,
        "max_tokens": 2048,
        "seed": "provider_does_not_support_seed"
      },
      "prompt_id": "deployment_full_v3",
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
        "adapter_failure": "reportable_outcome",
        "context_overflow": "reportable_outcome",
        "provider_filtered": "reportable_outcome",
        "length_truncation": "reportable_outcome"
      },
      "cloud_approval": {
        "approval_id": "d41_ladder_dom_2026_07_05",
        "approved_by": "Dom",
        "approved_at": "2026-07-05",
        "approved_scope": "D-41 run ladder second capable point (cross-family). Meta generation defaults as vendor-recommended sampling."
      }
    },
    {
      "condition_id": "run_nearfloor_qwen35_9b",
      "system_id": "run_nearfloor_qwen35_9b_v1",
      "model_class": "cloud",
      "model_family": "qwen3.5",
      "model_id": "Qwen/Qwen3.5-9B",
      "provider": "Together AI",
      "provider_snapshot_date": "2026-07-05",
      "model_card_snapshot": "https://www.together.ai/models/qwen3-5-9b",
      "parameter_count": "9B",
      "quantization": "provider serving (page does not state quantization)",
      "weights_source": "Qwen3.5 9B via Together serverless. THINKING-BY-DEFAULT reasoning-class model run in NON-THINKING mode via chat_template_kwargs {enable_thinking: false} (mechanism documented on the Together model page); sampling per HF card 'Instruct (non-thinking) mode' Best Practices (verified live 2026-07-05). Disclosed in the paper.",
      "context_window": 262144,
      "compute_boundary": {
        "hardware": "Together AI managed serverless inference",
        "runtime": "Together AI chat completions API",
        "max_wall_time_minutes": 480,
        "network_access": true
      },
      "cost_boundary": {
        "budget_type": "approved_cloud_budget",
        "max_cost_usd": 50.0,
        "billing_boundary": "Vendor-verified 2026-07-05: input $0.17/1M, output $0.25/1M. D-06 USD 300 aggregate ceiling."
      },
      "data_boundary": "synthetic_governed_agent_bench_fixtures_only",
      "decoding_settings": {
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "min_p": 0,
        "presence_penalty": 1.5,
        "repetition_penalty": 1.0,
        "max_tokens": 2048,
        "seed": "provider_does_not_support_seed",
        "chat_template_kwargs": {
          "enable_thinking": false
        }
      },
      "prompt_id": "deployment_full_v3",
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
        "adapter_failure": "reportable_outcome",
        "context_overflow": "reportable_outcome",
        "provider_filtered": "reportable_outcome",
        "length_truncation": "reportable_outcome"
      },
      "cloud_approval": {
        "approval_id": "d41_ladder_dom_2026_07_05",
        "approved_by": "Dom",
        "approved_at": "2026-07-05",
        "approved_scope": "D-41 run ladder near-floor point. Non-thinking mode; 262K native context removes the near-floor overflow confound."
      }
    },
    {
      "condition_id": "run_belowfloor_qwen25_7b",
      "system_id": "run_belowfloor_qwen25_7b_v1",
      "model_class": "cloud",
      "model_family": "qwen2.5-instruct",
      "model_id": "Qwen/Qwen2.5-7B-Instruct-Turbo",
      "provider": "Together AI",
      "provider_snapshot_date": "2026-07-05",
      "model_card_snapshot": "https://www.together.ai/models/qwen2-5-7b-instruct-turbo",
      "parameter_count": "7B",
      "quantization": "FP8 provider serving",
      "weights_source": "Qwen2.5 7B Instruct Turbo via Together serverless; sampling per Qwen/Qwen2.5-7B-Instruct generation_config (verified live 2026-07-05). Worst-case multi-turn context overflow at 32K is PRE-REGISTERED EXPECTED behavior for this control, reported via the context_overflow outcome category (never scored as model failure).",
      "context_window": 32768,
      "compute_boundary": {
        "hardware": "Together AI managed serverless inference",
        "runtime": "Together AI chat completions API",
        "max_wall_time_minutes": 480,
        "network_access": true
      },
      "cost_boundary": {
        "budget_type": "approved_cloud_budget",
        "max_cost_usd": 50.0,
        "billing_boundary": "Pricing snapshot 2026-05-19: input $0.30/1M, output $0.30/1M (existing verified entry). D-06 USD 300 aggregate ceiling."
      },
      "data_boundary": "synthetic_governed_agent_bench_fixtures_only",
      "decoding_settings": {
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "repetition_penalty": 1.05,
        "max_tokens": 2048,
        "seed": "provider_does_not_support_seed"
      },
      "prompt_id": "deployment_full_v3",
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
        "adapter_failure": "reportable_outcome",
        "context_overflow": "reportable_outcome",
        "provider_filtered": "reportable_outcome",
        "length_truncation": "reportable_outcome"
      },
      "cloud_approval": {
        "approval_id": "d41_ladder_dom_2026_07_05",
        "approved_by": "Dom",
        "approved_at": "2026-07-05",
        "approved_scope": "D-41 run ladder BELOW-FLOOR OPERATE CONTROL (pre-registered canary: predicted to fail to operate the contract). Supersedes option_b_qwen25_7b_together as the run condition; the old condition is retained for provenance."
      },
      "context_overflow_expected": true
    },
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
