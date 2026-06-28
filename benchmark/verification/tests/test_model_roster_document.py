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
        "option_b_qwen25_7b_together",
        "option_b_fallback_qwen25_32b_fireworks",
        "option_c_stretch_claude_sonnet_46",
    }


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

    for condition in roster["conditions"]:
        assert condition["model_class"] == "cloud"
        assert condition["data_boundary"] == (
            "synthetic_governed_agent_bench_fixtures_only"
        )
        assert condition["decoding_settings"] == {
            "temperature": 0,
            "top_p": 1,
            "max_tokens": 2048,
            "seed": "provider_does_not_support_seed",
        }
        assert condition["prompt_id"] == "deployment_full_v2"
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
