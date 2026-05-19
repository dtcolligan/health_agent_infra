"""Model-emitted operator action harness plumbing."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.harness import (  # noqa: E402
    HarnessConfig,
    HarnessError,
    harness_config_for_roster_condition,
    load_task,
    parse_model_action,
    run_model_response_action,
)
from governed_agent_bench.model_roster import (  # noqa: E402
    model_roster_hash,
    roster_condition,
)


def test_parse_model_action_accepts_structured_command() -> None:
    action = parse_model_action(
        json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "command",
            "command": "hai capabilities",
            "args": {"--json": True},
            "reason": "Inspect the command surface.",
        })
    )

    assert action["command"] == "hai capabilities"
    assert action["args"] == {"--json": True}


@pytest.mark.parametrize(
    "response",
    [
        "not json",
        "[{\"action_type\": \"final\"}]",
        json.dumps({"action_type": "command", "command": "sqlite3 state.db", "args": {}}),
        json.dumps({"action_type": "command", "command": "hai today", "args": "bad"}),
        json.dumps({"action_type": "refusal", "reason": "No", "args": {}}),
        json.dumps({"action_type": "final", "command": "hai today", "final_text": "Done"}),
        json.dumps({"action_type": "final", "final_text": "Done", "extra": True}),
    ],
)
def test_parse_model_action_rejects_non_contract_shapes(response: str) -> None:
    with pytest.raises(HarnessError):
        parse_model_action(response)


def test_harness_requires_identity_for_model_backed_runs(tmp_path: Path) -> None:
    task = load_task("gab_l1_capabilities_route")

    with pytest.raises(HarnessError, match="requires model_identity"):
        run_model_response_action(
            task,
            json.dumps({
                "action_type": "command",
                "command": "hai capabilities",
                "args": {"--json": True},
            }),
            HarnessConfig(
                fixture_root=tmp_path / "fixture",
                output_dir=tmp_path / "out",
                model_class="cloud",
                invocation_context="agent",
            ),
        )


def test_model_response_action_records_roster_identity_and_hash(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    condition = roster_condition("option_b_qwen25_7b_together")
    roster_hash = model_roster_hash()
    config = harness_config_for_roster_condition(
        condition,
        fixture_root=tmp_path / "fixture",
        output_dir=tmp_path / "out",
        runtime_mode="full_contract",
        claim_tier="T3",
        roster_hash=roster_hash,
    )

    trajectory = run_model_response_action(
        task,
        json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "command",
            "command": "hai capabilities",
            "args": {"--json": True},
            "reason": "Inspect the command surface.",
        }),
        config,
    )

    assert trajectory["model_class"] == "cloud"
    assert trajectory["invocation_context"] == "agent"
    assert trajectory["system_id"] == condition["system_id"]
    assert trajectory["claim_tier"] == "T3"
    assert trajectory["model_roster_hash"] == roster_hash
    assert trajectory["model_identity"] == {
        "model_family": "qwen2.5-instruct",
        "model_id": "Qwen/Qwen2.5-7B-Instruct-Turbo",
        "parameter_count": "7B",
        "quantization": "FP8 provider serving",
        "provider_snapshot": "Together AI@2026-05-19",
        "decoding_settings": {
            "temperature": 0,
            "top_p": 1,
            "max_tokens": 2048,
            "seed": "provider_does_not_support_seed",
        },
    }
    assert trajectory["steps"][0]["step_type"] == "command"
    assert trajectory["steps"][-1]["step_type"] == "observation"
    assert trajectory["steps"][-1]["exit_code"] == "OK"
