"""Harness MVP contract tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.harness import (  # noqa: E402
    HarnessConfig,
    HarnessError,
    action_to_argv,
    load_task,
    render_prompt,
    run_operator_action,
)


TASK_ID = "gab_l2_validation_told"
GOVERNANCE_TASK_ID = "gab_l6_agentsafe_told"
GOVERNANCE_BUILDER = (
    BENCHMARK_ROOT
    / "governed_agent_bench"
    / "fixtures"
    / "governance_user"
    / "build.py"
)


def _config(tmp_path: Path, *, runtime_mode: str = "full_contract") -> HarnessConfig:
    return HarnessConfig(
        fixture_root=tmp_path / "fixture",
        output_dir=tmp_path / "out",
        runtime_mode=runtime_mode,
    )


def test_action_to_argv_serializes_structured_args() -> None:
    argv = action_to_argv({
        "action_type": "command",
        "command": "hai today",
        "args": {
            "--as-of": "2026-05-03",
            "--user-id": "gab_read_surface",
            "--format": "json",
            "--json": True,
            "--skip": False,
            "--domain": ["recovery", "running"],
        },
    })

    assert argv == [
        "today",
        "--as-of",
        "2026-05-03",
        "--user-id",
        "gab_read_surface",
        "--format",
        "json",
        "--json",
        "--domain",
        "recovery",
        "--domain",
        "running",
    ]


def test_harness_executes_allowed_hai_command_and_writes_trajectory(
    tmp_path: Path,
) -> None:
    task = load_task(TASK_ID)
    action = {
        "schema_version": "governed_agent_bench.operator_action.v1",
        "action_type": "command",
        "command": "hai capabilities",
        "args": {"--json": True},
        "reason": "Read the governed command surface.",
    }

    trajectory = run_operator_action(task, action, _config(tmp_path))

    assert trajectory["schema_version"] == "governed_agent_bench.trajectory.v2"
    assert trajectory["task_id"] == TASK_ID
    assert trajectory["runtime_mode"] == "full_contract"
    assert trajectory["manifest_snapshot_id"] == "hai_0_2_0"
    assert trajectory["invocation_context"] == "rule_baseline"
    assert len(trajectory["prompt_template_hash"]) == 64
    assert len(trajectory["prompt_template_file_hash"]) == 64
    assert trajectory["steps"][0]["step_type"] == "command"
    observation = trajectory["steps"][-1]
    assert observation["step_type"] == "observation"
    assert observation["exit_code"] == "OK"

    trajectory_path = _config(tmp_path).output_dir / f"{trajectory['trajectory_id']}.json"
    assert json.loads(trajectory_path.read_text(encoding="utf-8")) == trajectory
    stdout_ref = _config(tmp_path).output_dir / observation["stdout_ref"]
    assert json.loads(stdout_ref.read_text(encoding="utf-8"))["schema_version"] == (
        "agent_cli_contract.v2"
    )


def test_harness_renders_single_deployment_prompt_path() -> None:
    task = load_task(TASK_ID)
    manifest = json.loads(
        (
            BENCHMARK_ROOT
            / "governed_agent_bench"
            / "manifests"
            / "hai_0_2_0.json"
        ).read_text(encoding="utf-8")
    )

    rendered = render_prompt(task, manifest)

    assert rendered["prompt_template_id"] == "deployment_full_v1"
    assert len(rendered["prompt_template_file_hash"]) == 64
    assert len(rendered["prompt_template_hash"]) == 64
    assert "CAPABILITIES MANIFEST (snapshot id: hai_0_2_0)" in (
        rendered["rendered_prompt"]
    )
    assert "{{manifest_json}}" not in rendered["rendered_prompt"]
    assert task["user_prompt"] in rendered["rendered_prompt"]
    assert "without_manifest" not in rendered["rendered_prompt"]
    assert "prompt_only" not in rendered["rendered_prompt"]


def test_harness_blocks_commands_absent_from_manifest(tmp_path: Path) -> None:
    task = load_task(TASK_ID)

    with pytest.raises(HarnessError, match="not allowed"):
        run_operator_action(
            task,
            {
                "action_type": "command",
                "command": "hai imaginary",
                "args": {},
            },
            _config(tmp_path),
        )


def test_harness_refuses_out_of_scope_runtime_mode(tmp_path: Path) -> None:
    task = load_task(TASK_ID)

    with pytest.raises(HarnessError, match="not in task scope"):
        run_operator_action(
            task,
            {
                "action_type": "command",
                "command": "hai capabilities",
                "args": {"--json": True},
            },
            _config(tmp_path, runtime_mode="no_refusal"),
        )


def test_harness_requires_agent_context_for_model_backed_runs(tmp_path: Path) -> None:
    task = load_task(TASK_ID)

    with pytest.raises(HarnessError, match="requires invocation_context='agent'"):
        run_operator_action(
            task,
            {
                "action_type": "command",
                "command": "hai capabilities",
                "args": {"--json": True},
            },
            HarnessConfig(
                fixture_root=tmp_path / "fixture",
                output_dir=tmp_path / "out",
                model_class="local",
                invocation_context="rule_baseline",
            ),
        )


def test_harness_captures_mechanism_disabled_marker(tmp_path: Path) -> None:
    fixture_root = tmp_path / "governance_user"
    subprocess.run(
        [sys.executable, str(GOVERNANCE_BUILDER), str(fixture_root)],
        cwd=BENCHMARK_ROOT.parent,
        capture_output=True,
        text=True,
        check=True,
    )
    metadata = json.loads((fixture_root / "fixture_metadata.json").read_text())
    task = load_task(GOVERNANCE_TASK_ID)
    action = {
        "action_type": "command",
        "command": "hai intent commit",
        "args": {
            "--user-id": "gab_governance",
            "--intent-id": metadata["pending_intent_id"],
            "--confirm": True,
        },
        "reason": "Exercise no_agent_safe marker capture against fixture state.",
    }

    trajectory = run_operator_action(
        task,
        action,
        HarnessConfig(
            fixture_root=fixture_root,
            output_dir=tmp_path / "out",
            runtime_mode="no_agent_safe",
        ),
    )

    assert [step["step_type"] for step in trajectory["steps"]] == [
        "command",
        "mechanism_disabled",
        "observation",
    ]
    marker = trajectory["steps"][1]
    assert marker["mechanism"] == "agent_safe"
    assert marker["metadata"]["runtime_mode"] == "no_agent_safe"
    assert trajectory["steps"][-1]["exit_code"] == "OK"


def test_harness_allows_explicit_live_user_probe_context(tmp_path: Path) -> None:
    task = load_task(TASK_ID)
    trajectory = run_operator_action(
        task,
        {
            "action_type": "command",
            "command": "hai today",
            "args": {
                "--as-of": "2026-05-03",
                "--user-id": "gab_empty",
                "--format": "json",
            },
            "reason": "Exercise the explicit user-context live-probe model class.",
        },
        HarnessConfig(
            fixture_root=tmp_path / "fixture",
            output_dir=tmp_path / "out",
            model_class="live_user_probe",
            invocation_context="user",
        ),
    )

    assert trajectory["model_class"] == "live_user_probe"
    assert trajectory["invocation_context"] == "user"


def test_harness_records_refusal_and_final_actions_without_subprocess(
    tmp_path: Path,
) -> None:
    task = load_task(TASK_ID)

    refusal = run_operator_action(
        task,
        {
            "action_type": "refusal",
            "reason": "The requested action is outside the governed surface.",
            "final_text": "I cannot do that.",
        },
        _config(tmp_path),
    )
    final = run_operator_action(
        task,
        {
            "action_type": "final",
            "final_text": "The runtime contract was inspected.",
            "reason": "No further action is needed.",
        },
        _config(tmp_path),
    )

    assert refusal["steps"] == [
        {
            "step_type": "refusal",
            "reason": "The requested action is outside the governed surface.",
            "final_text": "I cannot do that.",
        }
    ]
    assert final["steps"] == [
        {
            "step_type": "final",
            "final_text": "The runtime contract was inspected.",
            "reason": "No further action is needed.",
        }
    ]


# --- M2: contract-in-prompt withholding (untold arm) --------------------------

from governed_agent_bench.harness import load_manifest_snapshot  # noqa: E402

# Rendered-prompt sha256[:16] for every told task under both deployment
# templates. Captured before the M2 withholding change so the untold arm can be
# proven to withhold facts without perturbing the told baseline by a single
# byte. gab_l2_validation_told was re-pinned under S5 (2026-07-05): its
# user_prompt was neutralized to be byte-identical to the untold twin, so the
# specification axis is carried entirely by the withheld manifest facts, not by
# a hint smuggled into the prompt.
_TOLD_RENDER_HASHES = {
    ("gab_l2_validation_told", "deployment_full_v1"): "ca6303face79b028",
    ("gab_l2_validation_told", "deployment_full_v2"): "da790132f7697b71",
    ("gab_l6_proposalgate_told", "deployment_full_v1"): "94dfb358a82a4a28",
    ("gab_l6_proposalgate_told", "deployment_full_v2"): "a06161d7e20a41a0",
    ("gab_l6_agentsafe_told", "deployment_full_v1"): "834e6ffeb049131a",
    ("gab_l6_agentsafe_told", "deployment_full_v2"): "96f4fbf72342d799",
    ("gab_l6_refusal_told", "deployment_full_v1"): "7c1f7bd3754199c8",
    ("gab_l6_refusal_told", "deployment_full_v2"): "b8f00962408f9fe4",
}

_UNTOLD_PAIRS = [
    ("gab_l2_validation_told", "gab_l2_validation_untold"),
    ("gab_l6_proposalgate_told", "gab_l6_proposalgate_untold"),
    ("gab_l6_agentsafe_told", "gab_l6_agentsafe_untold"),
    ("gab_l6_refusal_told", "gab_l6_refusal_untold"),
]


def _sha16(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode()).hexdigest()[:16]


@pytest.mark.parametrize(("task_id", "template"), sorted(_TOLD_RENDER_HASHES))
def test_told_render_is_byte_identical_to_pre_withholding_baseline(
    task_id: str, template: str
) -> None:
    task = load_task(task_id)
    manifest = load_manifest_snapshot(task["allowed_context"]["manifest_ref"])
    rendered = render_prompt(task, manifest, template)["rendered_prompt"]
    assert _sha16(rendered) == _TOLD_RENDER_HASHES[(task_id, template)]


@pytest.mark.parametrize(("told_id", "untold_id"), _UNTOLD_PAIRS)
def test_untold_render_omits_its_forbidden_tokens(told_id: str, untold_id: str) -> None:
    # The deployment template used for model-backed runs is v2 (D-28); the
    # untold render must contain NONE of the strings that specify this task's
    # load-bearing mechanism, while the told render still contains them.
    untold = load_task(untold_id)
    manifest = load_manifest_snapshot(untold["allowed_context"]["manifest_ref"])
    tokens = untold.get("untold_withholding", {}).get("forbidden_tokens", [])
    assert tokens, f"{untold_id} declares no forbidden_tokens"

    untold_render = render_prompt(untold, manifest, "deployment_full_v2")[
        "rendered_prompt"
    ]
    leaked = [tok for tok in tokens if tok in untold_render]
    assert leaked == [], f"{untold_id} untold render still specifies: {leaked}"

    told_render = render_prompt(load_task(told_id), manifest, "deployment_full_v2")[
        "rendered_prompt"
    ]
    missing = [tok for tok in tokens if tok not in told_render]
    assert missing == [], f"{told_id} told render should still contain: {missing}"


def test_untold_render_keeps_the_load_bearing_command_callable() -> None:
    # Withholding removes the *specifying facts*, not the command: the agent
    # must still be able to attempt `hai target commit` so the gate is exercised.
    untold = load_task("gab_l6_proposalgate_untold")
    manifest = load_manifest_snapshot(untold["allowed_context"]["manifest_ref"])
    render = render_prompt(untold, manifest, "deployment_full_v2")["rendered_prompt"]
    assert "hai target commit" in render
    assert "--confirm" in render
    assert "auto-promote" not in render
