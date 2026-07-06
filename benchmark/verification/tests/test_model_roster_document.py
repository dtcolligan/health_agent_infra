"""Preprint model roster document checks."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
ROSTER_PATH = BENCHMARK_ROOT / "governed_agent_bench" / "model_roster.md"
README_PATH = BENCHMARK_ROOT / "governed_agent_bench" / "README.md"


def _roster_text() -> str:
    return ROSTER_PATH.read_text(encoding="utf-8")


def _roster_json() -> dict[str, Any]:
    text = _roster_text()
    match = re.search(r"```json\n(.*?)\n```", text, flags=re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))


def test_model_roster_matches_preprint_scope() -> None:
    text = _roster_text()

    assert "Qwen/Qwen2.5-7B-Instruct-Turbo" in text
    assert "accounts/fireworks/models/qwen2p5-32b-instruct" in text
    assert "claude-sonnet-4-6" in text
    assert "USD 300" in text
    assert "No model-backed trajectories before the pilot-protocol lock" in text

    stale_terms = [
        "NeurIPS 2027",
        "USD 1,500",
        "Houdinis (6)",
        "Guards (3)",
        "Engels Backdoor Code",
        "Hierarchical Summarization",
        "gpt-4o-mini",
        "claude-3-5-haiku",
    ]
    for term in stale_terms:
        assert term not in text


def test_model_roster_machine_readable_block_has_expected_conditions() -> None:
    roster = _roster_json()

    assert roster["schema_version"] == "governed_agent_bench.model_roster.v1"
    assert roster["roster_file"] == "benchmark/governed_agent_bench/model_roster.md"
    assert roster["hash_algorithm"] == "sha256"
    assert roster["hash_scope"] == "entire_model_roster_md_file_bytes"
    assert roster["approved_by"] == "Dom"
    assert roster["approved_at"] == "2026-05-19"
    assert roster["scope"]["data_boundary"] == (
        "synthetic_governed_agent_bench_fixtures_only"
    )
    assert roster["scope"]["private_data_allowed"] is False
    assert roster["scope"]["cloud_or_paid_api_allowed"] is True

    condition_ids = {condition["condition_id"] for condition in roster["conditions"]}
    assert condition_ids == {
        # roster_v3 (2026-07-05): the four D-41 run-ladder conditions,
        # vendor-verified live (Together pages + HF cards).
        "run_primary_qwen3_235b",
        "run_capable_llama33_70b",
        "run_nearfloor_qwen35_9b",
        "run_belowfloor_qwen25_7b",
        # Superseded conditions retained for provenance and harness/test
        # compatibility; not run targets.
        "primary_qwen3_235b_together",
        "option_b_qwen25_7b_together",
        "option_b_fallback_qwen25_32b_fireworks",
        "option_c_stretch_claude_sonnet_46",
    }
    assert roster["roster_id"] == "roster_v3"
    assert roster["conditions"][0]["condition_id"] == "run_primary_qwen3_235b"


def test_model_roster_conditions_keep_runtime_and_reporting_contracts() -> None:
    roster = _roster_json()
    all_modes = [
        "full_contract",
        "no_validation",
        "no_agent_safe",
        "no_proposal_gate",
        "no_refusal",
        "no_audit_chain",
        "no_runtime_enforcement",
    ]

    legacy_decoding = {
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 2048,
        "seed": "provider_does_not_support_seed",
    }
    # D-41: run-ladder conditions carry per-model vendor-recommended
    # sampling (verified live 2026-07-05); legacy conditions keep the
    # temp-0 settings they were locked with.
    run_decoding = {
        "run_primary_qwen3_235b": {
            "temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0,
            "max_tokens": 2048, "seed": "provider_does_not_support_seed",
        },
        "run_capable_llama33_70b": {
            "temperature": 0.6, "top_p": 0.9,
            "max_tokens": 2048, "seed": "provider_does_not_support_seed",
        },
        "run_nearfloor_qwen35_9b": {
            "temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0,
            "presence_penalty": 1.5, "repetition_penalty": 1.0,
            "max_tokens": 2048, "seed": "provider_does_not_support_seed",
            "chat_template_kwargs": {"enable_thinking": False},
        },
        "run_belowfloor_qwen25_7b": {
            "temperature": 0.7, "top_p": 0.8, "top_k": 20,
            "repetition_penalty": 1.05,
            "max_tokens": 2048, "seed": "provider_does_not_support_seed",
        },
    }
    for condition in roster["conditions"]:
        assert condition["model_class"] == "cloud"
        assert condition["data_boundary"] == (
            "synthetic_governed_agent_bench_fixtures_only"
        )
        expected_decoding = run_decoding.get(
            condition["condition_id"], legacy_decoding
        )
        assert condition["decoding_settings"] == expected_decoding, (
            condition["condition_id"]
        )
        # Run-ladder conditions use v3 (the read-only agent-authorization
        # template, §20.14); superseded/legacy conditions stay on v2.
        expected_prompt = (
            "deployment_full_v3"
            if str(condition["condition_id"]).startswith("run_")
            else "deployment_full_v2"
        )
        assert condition["prompt_id"] == expected_prompt, condition["condition_id"]
        assert condition["manifest_id"] == "hai_0_2_0"
        assert set(condition["failure_reporting"].values()) == {
            "reportable_outcome"
        }
        assert condition["cloud_approval"]["approved_by"] == "Dom"

    by_id = {condition["condition_id"]: condition for condition in roster["conditions"]}
    assert by_id["option_b_qwen25_7b_together"]["runtime_modes"] == all_modes
    assert by_id["option_b_fallback_qwen25_32b_fireworks"]["runtime_modes"] == all_modes
    assert by_id["option_c_stretch_claude_sonnet_46"]["runtime_modes"] == [
        "full_contract",
        "no_runtime_enforcement",
    ]


def test_benchmark_readme_no_longer_claims_roster_is_absent() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "No\n`model_roster.md` is committed yet" not in readme
    assert "WP-MODEL-ROSTER-001" in readme
    assert "No model-backed trajectory runs until the pilot protocol locks." in readme
