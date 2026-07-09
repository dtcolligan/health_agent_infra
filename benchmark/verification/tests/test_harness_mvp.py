"""Harness MVP contract tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

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
import governed_agent_bench.harness.core as harness_core  # noqa: E402


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
            "--user-id": "u_local_1",
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
        "u_local_1",
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
            "--user-id": "u_local_1",
            "--intent-id": metadata["pending_intent_id"],
            "--confirm": True,
        },
        "reason": "Exercise mechanism_disabled marker capture against fixture state.",
    }

    trajectory = run_operator_action(
        task,
        action,
        HarnessConfig(
            fixture_root=fixture_root,
            output_dir=tmp_path / "out",
            runtime_mode="no_runtime_enforcement",
        ),
    )

    step_types = [step["step_type"] for step in trajectory["steps"]]
    # no_runtime_enforcement disables every mechanism, so more than one
    # mechanism_disabled marker can be captured; the command still runs first
    # and the observation last, with the agent_safe marker among them.
    assert step_types[0] == "command"
    assert step_types[-1] == "observation"
    markers = [s for s in trajectory["steps"] if s["step_type"] == "mechanism_disabled"]
    assert any(m["mechanism"] == "agent_safe" for m in markers)
    assert all(
        m["metadata"]["runtime_mode"] == "no_runtime_enforcement" for m in markers
    )
    # under all-off the gated commit actually executes (unsafe mutation lands).
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


# --- Audit fix A4: the HAI subprocess wait is bounded --------------------------


def test_hai_subprocess_timeout_maps_to_crash_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A hung HAI subprocess is killed at the 120s bound and surfaces as an
    out-of-taxonomy exit code (EXIT_124), i.e. the subprocess_crash path --
    not an unbounded wait that stalls the whole sweep."""

    seen_timeouts: list[Any] = []

    def hang(*args: Any, **kwargs: Any) -> Any:
        seen_timeouts.append(kwargs.get("timeout"))
        raise subprocess.TimeoutExpired(
            cmd=list(args[0]),
            timeout=kwargs.get("timeout"),
            output="partial stdout before the hang",
            stderr="",
        )

    monkeypatch.setattr(harness_core.subprocess, "run", hang)
    task = load_task(TASK_ID)

    trajectory = run_operator_action(
        task,
        {
            "action_type": "command",
            "command": "hai capabilities",
            "args": {"--json": True},
            "reason": "Exercise the harness subprocess timeout bound.",
        },
        _config(tmp_path),
    )

    assert seen_timeouts == [120]
    observation = trajectory["steps"][-1]
    assert observation["step_type"] == "observation"
    # 124 is deliberately absent from EXIT_CODE_NAMES, so the observation
    # classifies as a crash (the agent loop stops on it).
    assert observation["exit_code"] == "EXIT_124"
    assert observation["metadata"]["returncode"] == 124
    stdout = (_config(tmp_path).output_dir / observation["stdout_ref"]).read_text(
        encoding="utf-8"
    )
    assert "partial stdout before the hang" in stdout
    stderr = (_config(tmp_path).output_dir / observation["stderr_ref"]).read_text(
        encoding="utf-8"
    )
    assert "exceeded 120s" in stderr


# --- M2: contract-in-prompt withholding (untold arm) --------------------------

from governed_agent_bench.harness import load_manifest_snapshot  # noqa: E402
from governed_agent_bench.harness.core import TASK_ROOT  # noqa: E402

# Rendered-prompt sha256[:16] for every told task under both deployment
# templates. Captured before the M2 withholding change so the untold arm can be
# proven to withhold facts without perturbing the told baseline by a single
# byte. gab_l2_validation_told was re-pinned under S5 (2026-07-05): its
# user_prompt was neutralized to be byte-identical to the untold twin, so the
# specification axis is carried entirely by the withheld manifest facts, not by
# a hint smuggled into the prompt.
_TOLD_RENDER_HASHES = {
    ("gab_l2_validation_told", "deployment_full_v1"): "e0cadd193aef1fd4",
    ("gab_l2_validation_told", "deployment_full_v2"): "7365948494389d3a",
    ("gab_l2_validation_told", "deployment_full_v3"): "443d6ba091981035",
    ("gab_l6_proposalgate_told", "deployment_full_v1"): "c959677e8ea7d2a3",
    ("gab_l6_proposalgate_told", "deployment_full_v2"): "478b94c0b9faefb0",
    ("gab_l6_proposalgate_told", "deployment_full_v3"): "0097e2b06596123c",
    # Re-pinned 2026-07-09 (D-52 told-arm reconciliation): the agent_safe told
    # arms now carry a contract_clause stating the operative W57 rule (scrubbed
    # in untold), so the told render legitimately changed. The untold-omits /
    # told-contains contrast is enforced by test_untold_render_omits_its_forbidden_tokens.
    ("gab_l6_agentsafe_told", "deployment_full_v1"): "918eef94acc616e4",
    ("gab_l6_agentsafe_told", "deployment_full_v2"): "a717cecee6cc43e8",
    ("gab_l6_agentsafe_told", "deployment_full_v3"): "6a1fbde5b33e7f0e",
    ("gab_l6_refusal_told", "deployment_full_v1"): "95b37540fbe8f59f",
    ("gab_l6_refusal_told", "deployment_full_v2"): "de94f7344c3bc140",
    ("gab_l6_refusal_told", "deployment_full_v3"): "f5be1d47fb3a0c56",
    # D-39 expansion pairs; the two validation prompts were de-named in the
    # Option-1 user-resolution fix (§20.13, 2026-07-06) and re-pinned here.
    ("gab_l2_validation_notfound_told", "deployment_full_v1"): "2029b98b586ad4e3",
    ("gab_l2_validation_notfound_told", "deployment_full_v2"): "0eab3ed2fb78c6e0",
    ("gab_l2_validation_notfound_told", "deployment_full_v3"): "a1e57284364952e4",
    # Re-pinned 2026-07-09 (D-52): intent/auth told arms carry the operative
    # rule (W57 / interactive-credential) in a contract_clause, scrubbed in untold.
    ("gab_l6_agentsafe_intent_told", "deployment_full_v1"): "013d1cfefac42776",
    ("gab_l6_agentsafe_intent_told", "deployment_full_v2"): "29ff0c3bae5f26b5",
    ("gab_l6_agentsafe_intent_told", "deployment_full_v3"): "9b52ef35c38ce4d5",
    ("gab_l6_agentsafe_auth_told", "deployment_full_v1"): "b10112f8ea69931f",
    ("gab_l6_agentsafe_auth_told", "deployment_full_v2"): "fc12e7b67f83ba3c",
    ("gab_l6_agentsafe_auth_told", "deployment_full_v3"): "1b12da9c13e83039",
    ("gab_l6_proposalgate_intent_told", "deployment_full_v1"): "be9c4683fec06783",
    ("gab_l6_proposalgate_intent_told", "deployment_full_v2"): "888061128a199128",
    ("gab_l6_proposalgate_intent_told", "deployment_full_v3"): "7651ef4603a8f176",
    ("gab_l6_proposalgate_archive_told", "deployment_full_v1"): "eb757d436ed95199",
    ("gab_l6_proposalgate_archive_told", "deployment_full_v2"): "275c5f8c7318eb3a",
    ("gab_l6_proposalgate_archive_told", "deployment_full_v3"): "dbea803fa1d2cd4a",
    ("gab_l6_refusal_credential_told", "deployment_full_v1"): "b74af0892268df4d",
    ("gab_l6_refusal_credential_told", "deployment_full_v2"): "56149d6d230e46f1",
    ("gab_l6_refusal_credential_told", "deployment_full_v3"): "2122563de3ecc197",
    ("gab_l6_refusal_export_told", "deployment_full_v1"): "eeaca8e5ad854d77",
    ("gab_l6_refusal_export_told", "deployment_full_v2"): "3cde62324e0d4529",
    ("gab_l6_refusal_export_told", "deployment_full_v3"): "a41fd89b8c4fa06c",
}

def _discover_untold_pairs() -> list[tuple[str, str]]:
    """Enumerate every told/untold pair that declares forbidden tokens.

    Dynamic so newly authored pairs are covered automatically (the D-39
    expansion added eight); M8 audit untold twins carry no
    untold_withholding (nothing manifest-level to scrub) and are excluded
    by the forbidden_tokens filter.
    """

    pairs: list[tuple[str, str]] = []
    for path in sorted(TASK_ROOT.glob("l[1-7]/gab_*_untold.json")):
        task = json.loads(path.read_text(encoding="utf-8"))
        tokens = task.get("untold_withholding", {}).get("forbidden_tokens", [])
        if not tokens:
            continue
        untold_id = task["task_id"]
        pairs.append((untold_id.replace("_untold", "_told"), untold_id))
    return pairs


_UNTOLD_PAIRS = _discover_untold_pairs()


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
    # Audit fix A12: containment is case-insensitive, so a Case-Variant
    # restatement of the constraint counts as a leak too.
    lowered_render = untold_render.lower()
    leaked = [tok for tok in tokens if tok.lower() in lowered_render]
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


def test_scrub_forbidden_prose_matches_case_insensitively() -> None:
    """Audit fix A12: a case-variant restatement of a forbidden token must be
    blanked from prose surfaces; structural strings stay untouched."""

    node = {
        "name": "hai target commit",
        "description": "Requires EXPLICIT User Approval before activation.",
        "flags": [
            {"name": "--confirm", "help": "Explicit USER approval gate."},
            {"name": "--target-id", "help": "Which target to commit."},
        ],
        # Not a prose key: never scrubbed even if it matched.
        "mutation_class": "explicit user approval",
    }

    harness_core._scrub_forbidden_prose(node, ("explicit user approval",))

    assert node["description"] == ""
    assert node["flags"][0]["help"] == ""
    assert node["flags"][1]["help"] == "Which target to commit."
    assert node["name"] == "hai target commit"
    assert node["mutation_class"] == "explicit user approval"


def test_append_operator_action_steps_rejects_unknown_disallowed_policy(
    tmp_path: Path,
) -> None:
    """IC-1: the disallowed-command handling policy is a closed enum -- the
    authored path raises (default, pinned by
    test_harness_blocks_commands_absent_from_manifest), the model loop records,
    and anything else is a programming error."""

    task = load_task(TASK_ID)
    config = _config(tmp_path)
    state = harness_core.prepare_operator_run(task, config, trajectory_id="t")

    with pytest.raises(HarnessError, match="on_disallowed_command"):
        harness_core.append_operator_action_steps(
            {"action_type": "command", "command": "hai imaginary", "args": {}},
            config,
            state,
            [],
            on_disallowed_command="ignore",
        )
