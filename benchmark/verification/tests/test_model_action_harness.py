"""Model-emitted operator action harness plumbing."""

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
    ModelTurnResult,
    harness_config_for_roster_condition,
    load_task,
    parse_model_action,
    run_agent_loop,
    run_model_response_action,
)
import governed_agent_bench.harness.core as harness_core  # noqa: E402
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
    "fence_open,fence_close",
    [("```json", "```"), ("```", "```"), ("```JSON", "```")],
)
def test_parse_model_action_strips_outer_code_fence(
    fence_open: str, fence_close: str
) -> None:
    # Instruction-tuned models habitually wrap the JSON action in a Markdown
    # code fence. The fenced payload is byte-identical JSON, so it must parse
    # to the same action; the fence is an envelope artifact, not a contract
    # violation. M4 still validates the parsed action unchanged.
    inner = json.dumps({
        "action_type": "command",
        "command": "hai capabilities",
        "args": {"--json": True},
        "reason": "Inspect the command surface.",
    })
    fenced = f"{fence_open}\n{inner}\n{fence_close}"
    action = parse_model_action(fenced)
    assert action["command"] == "hai capabilities"
    assert action["args"] == {"--json": True}


def test_parse_model_action_extracts_prose_wrapped_json() -> None:
    # Envelope tolerance (WP-A): a single JSON action wrapped in prose is
    # extracted and validated identically. This is envelope normalization, like
    # fence stripping; the action is unchanged so M4 still validates it. Needed
    # for a fair multi-model benchmark: models habitually narrate around the
    # action, which is a formatting difference, not a governance one.
    inner = json.dumps({
        "action_type": "command",
        "command": "hai capabilities",
        "args": {"--json": True},
        "reason": "Inspect the surface.",
    })
    action = parse_model_action(f"Sure, here is my action:\n{inner}\nThanks!")
    assert action["command"] == "hai capabilities"
    assert action["args"] == {"--json": True}


def test_parse_model_action_drops_empty_final_text_on_command() -> None:
    # WP-A envelope normalization: an empty final_text on a command carries no
    # information (some models emit `"final_text": ""`); drop it rather than
    # reject the command. A non-empty final_text on a command still fails.
    action = parse_model_action(json.dumps({
        "action_type": "command",
        "command": "hai capabilities",
        "args": {},
        "reason": "look",
        "final_text": "",
    }))
    assert action["command"] == "hai capabilities"
    assert "final_text" not in action
    # §20.17 Finding 7: a NON-empty final_text on a command is now folded into
    # the reason (narration, not a second decision), not rejected. Here reason
    # is already set, so the stray narration is simply dropped.
    folded = parse_model_action(json.dumps({
        "action_type": "command",
        "command": "hai capabilities",
        "args": {},
        "reason": "look",
        "final_text": "I ran it.",
    }))
    assert folded["command"] == "hai capabilities"
    assert "final_text" not in folded
    assert folded["reason"] == "look"


def test_arg_key_syntax_normalized_but_semantics_still_measured() -> None:
    # §20.15 (reverses the earlier WP-A stance): a purely SYNTACTIC arg-key
    # variant of a REAL flag (target_id / user_id vs --target-id / --user-id)
    # is rescued by the loop's manifest-aware normalizer -- the `--` prefix is
    # a harness input-format detail, not an M4-semantic signal, and penalizing
    # it confounded the capability axis (weaker models malform far more). A
    # genuinely wrong flag NAME is NOT rescued and stays a measured failure.
    from governed_agent_bench.harness.core import (
        normalize_command_arg_keys,
        load_manifest_snapshot,
    )

    manifest = load_manifest_snapshot("hai_0_2_0")

    # parse itself is now lenient on arg-key shape (variants survive to the
    # normalizer); it still rejects genuinely non-identifier keys.
    parsed = parse_model_action("Committing now:\n" + json.dumps({
        "action_type": "command",
        "command": "hai target commit",
        "args": {"target_id": "target_1", "user_id": "u_local_1"},
        "reason": "commit",
    }))
    assert parsed["action_type"] == "command"

    # syntactic variants -> canonical real flags, no unresolved keys
    norm, rewrites = normalize_command_arg_keys(
        "hai target commit", parsed["args"], manifest
    )
    assert rewrites == {"target_id": "--target-id", "user_id": "--user-id"}
    assert all(key.startswith("--") for key in norm)

    # a semantically wrong flag name stays unresolved (measured failure)
    _, no_rewrite = normalize_command_arg_keys(
        "hai today", {"as_of_date": "2026-05-03"}, manifest
    )
    assert no_rewrite == {}

    # a genuinely malformed key (whitespace) is still rejected at parse
    with pytest.raises(HarnessError):
        parse_model_action(json.dumps({
            "action_type": "command",
            "command": "hai target commit",
            "args": {"target id": "target_1"},
            "reason": "commit",
        }))


def test_envelope_batch_drops_unknown_fields() -> None:
    # Finding 1: a narration field (thought/rationale) alongside a correct
    # action is dropped, not fatal.
    parsed = parse_model_action(json.dumps({
        "action_type": "command", "command": "hai explain",
        "args": {"--for-date": "2026-05-03"},
        "reason": "read", "thought": "I should read the card", "confidence": 0.9,
    }))
    assert parsed["action_type"] == "command"
    assert parsed["command"] == "hai explain"
    assert parsed["args"] == {"--for-date": "2026-05-03"}
    assert set(parsed["_dropped_fields"]) == {"confidence", "thought"}


def test_envelope_batch_peels_inline_flags() -> None:
    # Finding 2: flags typed inline in the command string move into args.
    parsed = parse_model_action(json.dumps({
        "action_type": "command",
        "command": "hai explain --for-date 2026-05-03 --user-id u_local_1",
        "args": {}, "reason": "read",
    }))
    assert parsed["command"] == "hai explain"
    assert parsed["args"] == {
        "--for-date": "2026-05-03", "--user-id": "u_local_1",
    }


def test_envelope_batch_defaults_missing_args() -> None:
    # Finding 3: a no-arg command with args omitted defaults to {}.
    parsed = parse_model_action(json.dumps({
        "action_type": "command", "command": "hai capabilities", "reason": "list",
    }))
    assert parsed["args"] == {}


def test_envelope_batch_parses_python_literal_dialect() -> None:
    # Finding 4: single quotes / trailing comma / Python bool are rescued.
    parsed = parse_model_action(
        "{'action_type': 'command', 'command': 'hai explain', "
        "'args': {'--for-date': '2026-05-03',}, 'reason': 'r'}"
    )
    assert parsed["command"] == "hai explain"
    assert parsed["args"] == {"--for-date": "2026-05-03"}


def test_envelope_batch_folds_stray_final_text_on_command() -> None:
    # Finding 7: a non-empty final_text on a command is folded into an empty
    # reason, not rejected.
    parsed = parse_model_action(json.dumps({
        "action_type": "command", "command": "hai explain", "args": {},
        "final_text": "I'll read the card next.",
    }))
    assert parsed["action_type"] == "command"
    assert "final_text" not in parsed
    assert parsed["reason"] == "I'll read the card next."


def test_envelope_batch_skips_leading_prose_object() -> None:
    # Finding 10: a stray brace-object in leading prose is skipped in favor of
    # the object that actually carries an action_type.
    parsed = parse_model_action(
        "Reasoning {step 1, step 2}. Action: "
        '{"action_type": "command", "command": "hai explain", "args": {}}'
    )
    assert parsed["action_type"] == "command"
    assert parsed["command"] == "hai explain"


def test_envelope_batch_coerces_boolean_string_flags() -> None:
    # Finding 9: a store_true flag given as the string "true" is coerced to bool
    # for manifest-declared boolean flags only.
    from governed_agent_bench.harness.core import (
        coerce_boolean_flag_values, load_manifest_snapshot,
    )
    manifest = load_manifest_snapshot("hai_0_2_0")
    coerced, notes = coerce_boolean_flag_values(
        "hai review weekly", {"--markdown": "true", "--user-id": "true"}, manifest,
    )
    assert coerced["--markdown"] is True          # store_false boolean flag
    assert coerced["--user-id"] == "true"         # not a boolean flag: untouched
    assert notes == {"--markdown": "'true'->bool"}


def test_hallucinated_dashed_flag_is_caught_as_invalid_not_transient() -> None:
    # §20.18 convergence fix: a `--`-prefixed flag that is NOT a real flag of
    # the command (`--domain` on `hai explain`) must be rejected as an invalid
    # arg (recoverable invalid_output) instead of reaching argparse, exiting 2,
    # and being mislabeled TRANSIENT. The loop validates every key against the
    # command's real manifest flags; here we assert the flag sets that drive it.
    from governed_agent_bench.harness.core import (
        _manifest_command_flags, load_manifest_snapshot,
    )
    manifest = load_manifest_snapshot("hai_0_2_0")
    assert "--domain" not in _manifest_command_flags(manifest, "hai explain")
    assert "--domain" in _manifest_command_flags(manifest, "hai today")
    # a real explain flag stays valid
    assert "--for-date" in _manifest_command_flags(manifest, "hai explain")


def test_feedback_never_leaks_mechanism_disabled_marker() -> None:
    # §20.18 cumulative-audit Finding 1: the mechanism_disabled control step
    # (which names the DISABLED mechanism = the runtime-mode lever) must never
    # reach the model. It arrives as a parsed trajectory step alongside the
    # command/observation of an off-mode turn; the feedback whitelist must drop
    # it. A leak here contaminates the A-B / C-D contrasts on the off cells.
    from governed_agent_bench.harness.model_actions import _feedback_message
    steps = [
        {"step_type": "command", "command": "hai target list", "args": {}},
        {"step_type": "mechanism_disabled", "mechanism": "agent_safe",
         "metadata": {"step_type": "mechanism_disabled", "mechanism": "agent_safe"}},
        {"step_type": "observation", "exit_code": "OK"},
    ]
    msg = _feedback_message(steps)
    assert "mechanism_disabled" not in msg
    assert "agent_safe" not in msg
    # the legitimate command + observation ARE still shown
    assert "hai target list" in msg
    assert "observation" in msg


def test_stdout_channel_never_leaks_mechanism_disabled_marker(tmp_path: Path) -> None:
    # §20.18 3rd-channel fix: hai synthesize prints its result dict to STDOUT,
    # and that dict embeds mechanism_disabled_markers (the runtime-mode lever).
    # The step-whitelist and stderr filter did NOT cover stdout. Scrub it.
    from governed_agent_bench.harness.model_actions import (
        _scrub_stdout_control_markers, _read_observation_stdout,
    )
    synth = json.dumps({
        "daily_plan_id": "plan_2026-05-03_u_local_1",
        "recovery": {"action": "proceed"},
        "mechanism_disabled_markers": [
            {"step_type": "mechanism_disabled", "mechanism": "refusal",
             "runtime_mode": "no_refusal"}
        ],
    })
    scrubbed = _scrub_stdout_control_markers(synth)
    assert "mechanism_disabled" not in scrubbed
    assert "no_refusal" not in scrubbed
    assert "refusal" not in scrubbed
    # legitimate plan output preserved
    assert "plan_2026-05-03_u_local_1" in scrubbed
    assert "proceed" in scrubbed

    # end-to-end through the observation read (marker in a stdout artifact)
    obs_dir = tmp_path
    (obs_dir / "obs.txt").write_text(synth, encoding="utf-8")
    surfaced = _read_observation_stdout(
        {"step_type": "observation", "stdout_ref": "obs.txt"}, obs_dir
    )
    assert surfaced is not None
    assert "mechanism_disabled" not in surfaced and "no_refusal" not in surfaced
    assert "plan_2026-05-03_u_local_1" in surfaced

    # a card payload with NO markers is returned byte-unchanged (id preserved)
    card = json.dumps({"card_id": "card_x",
                       "provenance": {"proposal_log": ["gab_read_2026-05-03_recovery_5836d1bb"]}})
    assert _scrub_stdout_control_markers(card) == card
    assert "5836d1bb" in _scrub_stdout_control_markers(card)

    # Gate-2c belt-and-suspenders: a marker as a plain dict VALUE (not under the
    # markers key, not a list element) is also dropped.
    nested = json.dumps({
        "plan": "plan_x",
        "diag": {"step_type": "mechanism_disabled", "mechanism": "validation",
                 "runtime_mode": "no_validation"},
    })
    out = _scrub_stdout_control_markers(nested)
    assert "mechanism_disabled" not in out and "no_validation" not in out
    assert "plan_x" in out


def test_envelope_batch_feedback_carries_schema_reminder() -> None:
    # Finding 8: invalid_output feedback restates the schema incl. the refusal
    # shape, so a verbose model can convert its own decision into the form.
    from governed_agent_bench.harness.model_actions import _feedback_message
    msg = _feedback_message([{"step_type": "invalid_output", "raw_output": "oops",
                              "parse_error": "not json"}])
    assert "action_type" in msg and "refusal" in msg
    assert "do not decline in prose" in msg


def test_parse_model_action_rejects_pure_prose() -> None:
    # No balanced JSON object -> genuine formatting failure, still rejected.
    with pytest.raises(HarnessError):
        parse_model_action("I cannot determine the correct command format here.")


@pytest.mark.parametrize(
    "response",
    [
        "not json",
        "[{\"action_type\": \"final\"}]",
        json.dumps({"action_type": "command", "command": "sqlite3 state.db", "args": {}}),
        json.dumps({"action_type": "command", "command": "hai today", "args": "bad"}),
        json.dumps({"action_type": "refusal", "reason": "No", "args": {}}),
        json.dumps({"action_type": "final", "command": "hai today", "final_text": "Done"}),
    ],
)
def test_parse_model_action_rejects_non_contract_shapes(response: str) -> None:
    # These are wrong-SHAPE actions (refusal carrying args, final carrying a
    # command) that remain genuine failures. An unknown top-level field is no
    # longer here: per §20.17 Finding 1 it is dropped, not fatal (see
    # test_envelope_batch_drops_unknown_fields).
    with pytest.raises(HarnessError):
        parse_model_action(response)


def test_harness_requires_identity_for_model_backed_runs(tmp_path: Path) -> None:
    task = load_task("gab_l1_operate_route")

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
    task = load_task("gab_l1_operate_route")
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


def _config(tmp_path: Path) -> HarnessConfig:
    condition = roster_condition("option_b_qwen25_7b_together")
    return harness_config_for_roster_condition(
        condition,
        fixture_root=tmp_path / "fixture",
        output_dir=tmp_path / "out",
        runtime_mode="full_contract",
        claim_tier="T3",
        roster_hash=model_roster_hash(),
    )


def _command_response(command: str = "hai capabilities") -> str:
    return json.dumps({
        "schema_version": "governed_agent_bench.operator_action.v1",
        "action_type": "command",
        "command": command,
        "args": {"--json": True} if command == "hai capabilities" else {},
        "reason": "Inspect the command surface.",
    })


def _final_response(text: str = "Done.") -> str:
    return json.dumps({
        "schema_version": "governed_agent_bench.operator_action.v1",
        "action_type": "final",
        "final_text": text,
        "reason": "No further action is needed.",
    })


def _scripted_model_turn(
    responses: list[str],
    seen_messages: list[list[dict[str, str]]],
) -> Any:
    def model_turn(messages: list[dict[str, str]]) -> str:
        seen_messages.append(json.loads(json.dumps(messages)))
        return responses.pop(0)

    return model_turn


def _patch_hai_completed(
    monkeypatch: pytest.MonkeyPatch,
    *,
    returncode: int = 0,
    stdout: str = "{\"ok\": true}",
    stderr: str = "",
) -> None:
    def fake_run_hai(
        action: dict[str, Any],
        config: HarnessConfig,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["hai"],
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )

    monkeypatch.setattr(harness_core, "_run_hai", fake_run_hai)


def test_agent_loop_feeds_observation_back_as_user_message(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = json.dumps({
        "step_type": "mechanism_disabled",
        "mechanism": "validation",
        "runtime_mode": "no_validation",
    })
    _patch_hai_completed(monkeypatch, stderr=f"{marker}\n")
    task = load_task("gab_l1_operate_route")
    seen_messages: list[list[dict[str, str]]] = []

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_model_turn([_command_response(), _final_response()], seen_messages),
    )

    assert result.stop_reason == "final"
    assert len(seen_messages) == 2
    turn_2_messages = seen_messages[1]
    assert turn_2_messages[-2] == {
        "role": "assistant",
        "content": _command_response(),
    }
    assert turn_2_messages[-1]["role"] == "user"
    feedback = turn_2_messages[-1]["content"]
    assert '"exit_code": "OK"' in feedback
    assert '"stdout_ref":' in feedback
    # §20.18 cumulative-audit Finding 1 (REVERSES the prior assertion): the
    # mechanism_disabled control step names the DISABLED mechanism = the
    # runtime-mode lever and must NEVER reach the model. It stays in the
    # TRAJECTORY (scoring needs it, asserted below) but is dropped from the
    # feedback whitelist. A leak here contaminated the off-cell contrasts.
    assert '"step_type": "mechanism_disabled"' not in feedback
    assert '"mechanism": "validation"' not in feedback
    # WP-RUNTIME-FIX: the model must receive the command's actual stdout, not
    # just a file reference it cannot open, or read-then-narrate tasks are
    # unwinnable. The trajectory still persists only stdout_ref (lean).
    feedback_obs = [
        step
        for step in json.loads(feedback)["steps"]
        if step["step_type"] == "observation"
    ]
    assert feedback_obs and feedback_obs[0]["stdout"] == '{"ok": true}'
    assert all("stdout" not in step for step in result.trajectory["steps"])
    assert [step["step_type"] for step in result.trajectory["steps"]] == [
        "command",
        "mechanism_disabled",
        "observation",
        "final",
    ]


def test_agent_loop_records_invalid_output_and_feedback(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_operate_route")
    seen_messages: list[list[dict[str, str]]] = []

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_model_turn(["not json", _final_response()], seen_messages),
    )

    invalid_step = result.trajectory["steps"][0]
    assert invalid_step["step_type"] == "invalid_output"
    assert invalid_step["raw_output"] == "not json"
    assert "model response is not a JSON object" in invalid_step["parse_error"]
    assert seen_messages[1][-1]["role"] == "user"
    assert "model response is not a JSON object" in seen_messages[1][-1]["content"]
    assert result.turn_records[0].invalid_output == {
        "raw_output": "not json",
        "parse_error": invalid_step["parse_error"],
    }
    assert result.stop_reason == "final"


def test_agent_loop_stops_at_exactly_max_turns(tmp_path: Path) -> None:
    task = load_task("gab_l1_operate_route")
    calls = 0

    def model_turn(messages: list[dict[str, str]]) -> str:
        nonlocal calls
        calls += 1
        return "not json"

    result = run_agent_loop(task, _config(tmp_path), model_turn)

    assert calls == 7
    assert len(result.turn_records) == 7
    assert result.stop_reason == "max_turns"
    assert result.turn_records[-1].stop_reason == "max_turns"
    assert [step["step_type"] for step in result.trajectory["steps"]] == [
        "invalid_output",
        "invalid_output",
        "invalid_output",
        "invalid_output",
        "invalid_output",
        "invalid_output",
        "invalid_output",
    ]


def test_agent_loop_subprocess_crash_terminates_before_next_turn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_hai_completed(monkeypatch, returncode=99)
    task = load_task("gab_l1_operate_route")
    seen_messages: list[list[dict[str, str]]] = []

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_model_turn([_command_response(), _final_response()], seen_messages),
    )

    assert len(seen_messages) == 1
    assert result.stop_reason == "subprocess_crash"
    assert result.turn_records[-1].stop_reason == "subprocess_crash"
    assert result.trajectory["steps"][-1]["exit_code"] == "EXIT_99"


def test_agent_loop_after_turn_stop_signal_terminates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_hai_completed(monkeypatch)
    task = load_task("gab_l1_operate_route")
    seen_messages: list[list[dict[str, str]]] = []
    records_seen = []

    def after_turn(record: Any, trajectory_so_far: dict[str, Any]) -> str:
        records_seen.append((record, trajectory_so_far))
        return "stop"

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_model_turn([_command_response(), _final_response()], seen_messages),
        after_turn=after_turn,
    )

    assert len(seen_messages) == 1
    assert len(records_seen) == 1
    assert records_seen[0][0].executed_step_ids == [0, 1]
    assert records_seen[0][1]["steps"] == result.trajectory["steps"]
    assert result.stop_reason == "after_turn_stop"
    assert result.turn_records[-1].stop_reason == "after_turn_stop"


_METADATA_KEYS = (
    "wall_time_ms",
    "prompt_tokens",
    "completion_tokens",
    "cost_usd_estimate",
)


def _refusal_response(
    reason: str = "Outside the governed surface.",
    final_text: str = "I cannot do that.",
) -> str:
    return json.dumps({
        "schema_version": "governed_agent_bench.operator_action.v1",
        "action_type": "refusal",
        "reason": reason,
        "final_text": final_text,
    })


def _scripted_meta_turns(
    turns: list[ModelTurnResult],
    seen_messages: list[list[dict[str, str]]],
) -> Any:
    def model_turn(messages: list[dict[str, str]]) -> ModelTurnResult:
        seen_messages.append(json.loads(json.dumps(messages)))
        return turns.pop(0)

    return model_turn


def test_agent_loop_stamps_numeric_metadata_on_action_step(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = json.dumps({
        "step_type": "mechanism_disabled",
        "mechanism": "validation",
        "runtime_mode": "no_validation",
    })
    _patch_hai_completed(monkeypatch, stderr=f"{marker}\n")
    task = load_task("gab_l1_operate_route")
    seen_messages: list[list[dict[str, str]]] = []
    turns = [
        ModelTurnResult(
            text=_command_response(),
            prompt_tokens=1200,
            completion_tokens=340,
            cost_usd_estimate=0.00046,
            wall_time_ms=128,
        ),
        ModelTurnResult(
            text=_final_response(),
            prompt_tokens=1500,
            completion_tokens=12,
            cost_usd_estimate=0.00045,
            wall_time_ms=90,
        ),
    ]

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_meta_turns(turns, seen_messages),
    )

    steps = result.trajectory["steps"]
    assert [step["step_type"] for step in steps] == [
        "command",
        "mechanism_disabled",
        "observation",
        "final",
    ]
    # The model-call metadata lands on the command action step only.
    assert steps[0]["metadata"] == {
        "wall_time_ms": 128,
        "prompt_tokens": 1200,
        "completion_tokens": 340,
        "cost_usd_estimate": 0.00046,
        "retry_count": 0,
    }
    # Neither the mechanism marker nor the observation (a different clock)
    # carries the per-turn cost/token keys -> one cost per turn.
    for non_action in (steps[1], steps[2]):
        for key in _METADATA_KEYS:
            assert key not in non_action["metadata"]
    # The final action step gets its own turn's metadata.
    assert steps[3]["metadata"]["wall_time_ms"] == 90
    assert steps[3]["metadata"]["cost_usd_estimate"] == 0.00045
    # Turn records round-trip the same numbers (feeds the provider report).
    assert result.turn_records[0].cost_usd_estimate == 0.00046
    assert result.turn_records[0].wall_time_ms == 128
    assert result.turn_records[1].prompt_tokens == 1500


@pytest.mark.parametrize(
    ("responses", "action_index", "action_type"),
    [
        ([_final_response()], 0, "final"),
        ([_refusal_response()], 0, "refusal"),
        (["not json", _final_response()], 0, "invalid_output"),
    ],
)
def test_agent_loop_str_turn_stamps_present_none_metadata(
    tmp_path: Path,
    responses: list[str],
    action_index: int,
    action_type: str,
) -> None:
    task = load_task("gab_l1_operate_route")
    seen_messages: list[list[dict[str, str]]] = []

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_model_turn(list(responses), seen_messages),
    )

    step = result.trajectory["steps"][action_index]
    assert step["step_type"] == action_type
    # A bare-str turn is still the model path: keys present, value None.
    for key in _METADATA_KEYS:
        assert key in step["metadata"]
        assert step["metadata"][key] is None


def test_agent_loop_coerces_non_numeric_metadata_to_none(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_operate_route")
    seen_messages: list[list[dict[str, str]]] = []
    turns = [
        ModelTurnResult(
            text=_final_response(),
            prompt_tokens=10,
            completion_tokens=5,
            cost_usd_estimate="not-a-number",  # type: ignore[arg-type]
            wall_time_ms=True,  # type: ignore[arg-type]
        ),
    ]

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_meta_turns(turns, seen_messages),
    )

    metadata = result.trajectory["steps"][0]["metadata"]
    # Runtime guard drops non-numeric / bool values to None; no leak.
    assert metadata["cost_usd_estimate"] is None
    assert metadata["wall_time_ms"] is None
    assert metadata["prompt_tokens"] == 10
    assert metadata["completion_tokens"] == 5


def test_agent_loop_harness_injected_text_never_becomes_assistant_history(
    tmp_path: Path,
) -> None:
    """Audit fix A5: harness-authored failure sentinels (retry exhausted /
    adapter error) must not be replayed to the model as ASSISTANT messages
    it never emitted. The trajectory record is unchanged (invalid_output
    step with the sentinel raw_output); the failed turn reaches the model
    only as user-role harness feedback."""

    task = load_task("gab_l1_operate_route")
    seen_messages: list[list[dict[str, str]]] = []
    sentinel = "__GAB_RETRY_EXHAUSTED__: timeout after 3 retries"
    turns = [
        ModelTurnResult(text=sentinel, retry_count=3, harness_injected=True),
        ModelTurnResult(text=_final_response()),
    ]

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_meta_turns(turns, seen_messages),
    )

    assert result.stop_reason == "final"
    turn_2_messages = seen_messages[1]
    # The old failure mode: the sentinel appeared as an assistant message.
    assert not any(
        message["role"] == "assistant" and "__GAB_" in message["content"]
        for message in turn_2_messages
    ), "harness sentinel leaked into assistant history"
    # The failed turn is represented as user-role harness feedback instead.
    assert turn_2_messages[-1]["role"] == "user"
    assert sentinel in turn_2_messages[-1]["content"]
    # Trajectory semantics identical: the invalid_output step still records
    # the sentinel and its parse error.
    invalid_step = result.trajectory["steps"][0]
    assert invalid_step["step_type"] == "invalid_output"
    assert invalid_step["raw_output"] == sentinel
    assert result.turn_records[0].raw_output == sentinel
    assert result.turn_records[0].retry_count == 3
    # A model-emitted turn (harness_injected default False) still lands in
    # assistant history as before.
    assert result.messages[-1] == {"role": "assistant", "content": _final_response()}


def test_model_backed_config_rejects_dead_v1_prompt_template(
    tmp_path: Path,
) -> None:
    """Audit fix A6: a model-backed config carrying the dead
    deployment_full_v1 default (whose render exceeds the locked model's
    context and would 422 every call) fails fast instead of burning a
    metered run. The rule-baseline default is unchanged."""

    task = load_task("gab_l1_operate_route")
    condition = dict(roster_condition("option_b_qwen25_7b_together"))
    condition["prompt_id"] = "deployment_full_v1"
    config = harness_config_for_roster_condition(
        condition,
        fixture_root=tmp_path / "fixture",
        output_dir=tmp_path / "out",
        runtime_mode="full_contract",
        claim_tier="T3",
        roster_hash=model_roster_hash(),
    )
    assert config.prompt_template_id == "deployment_full_v1"

    with pytest.raises(HarnessError, match="deployment_full_v1"):
        run_agent_loop(task, config, lambda _messages: _final_response())


def test_run_model_response_action_omits_turn_metadata(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_operate_route")

    trajectory = run_model_response_action(
        task,
        _command_response(),
        _config(tmp_path),
    )

    # The single-response helper performs no provider call, so it is
    # outside WP-A4 turn-metadata stamping: keys absent (like rule_baseline).
    command_step = trajectory["steps"][0]
    assert command_step["step_type"] == "command"
    for key in _METADATA_KEYS:
        assert key not in command_step.get("metadata", {})


def test_agent_loop_records_disallowed_command_and_continues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """IC-1 (dress-rehearsal finding #1, sweep-killer): a model emitting a
    manifest-disallowed command must NOT crash the loop. The event is recorded
    as a rejected command step (no execution, no observation), the turn is
    consumed with feedback naming the rejection, and the loop continues.
    The step shape is exactly what the scorer's hallucinated_command_rate /
    valid_command_rate read (command steps checked against the manifest)."""

    hai_calls: list[dict[str, Any]] = []

    def fail_if_executed(
        action: dict[str, Any],
        config: HarnessConfig,
    ) -> subprocess.CompletedProcess[str]:
        hai_calls.append(action)
        raise AssertionError("a manifest-disallowed command must never execute")

    monkeypatch.setattr(harness_core, "_run_hai", fail_if_executed)
    task = load_task("gab_l1_operate_route")
    seen_messages: list[list[dict[str, str]]] = []

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_model_turn(
            [_command_response("hai bogus surface"), _final_response()],
            seen_messages,
        ),
    )

    # The loop survived the disallowed command and ran to the model's final.
    assert result.stop_reason == "final"
    assert hai_calls == []
    steps = result.trajectory["steps"]
    assert [step["step_type"] for step in steps] == ["command", "final"]
    rejected = steps[0]
    assert rejected["command"] == "hai bogus surface"
    assert rejected["metadata"]["manifest_rejected"] is True
    assert rejected["metadata"]["rejection_reason"] == (
        "command not in manifest snapshot"
    )
    # The turn was consumed and the model was told the command is not in the
    # manifest before its next turn.
    assert len(seen_messages) == 2
    feedback = seen_messages[1][-1]
    assert feedback["role"] == "user"
    assert "command not in manifest snapshot" in feedback["content"]

    # The scorer sees the event on the M4 metrics: the rejected command step
    # is an invalid command against the manifest snapshot.
    from governed_agent_bench.harness import load_manifest_snapshot
    from governed_agent_bench.scorer import score_trajectory

    score = score_trajectory(
        {**task, "metrics": ["valid_command_rate", "hallucinated_command_rate"]},
        result.trajectory,
        manifest_snapshot=load_manifest_snapshot(
            result.trajectory["manifest_snapshot_id"]
        ),
        observation_root=tmp_path / "out",
    )
    hallucinated = score["metrics"]["hallucinated_command_rate"]
    assert hallucinated["value"] == 1.0
    assert hallucinated["passed"] is False
    valid = score["metrics"]["valid_command_rate"]
    assert valid["value"] == 0.0
    assert valid["passed"] is False
    assert any(
        violation["kind"] == "hallucinated_command"
        for violation in score["violations"]
    )


def test_agent_loop_disallowed_then_allowed_command_still_executes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After a recorded rejection the loop must execute later valid commands
    normally (the rejected step pairs with no observation; the next command's
    observation must not be misattributed to it)."""

    _patch_hai_completed(monkeypatch)
    task = load_task("gab_l1_operate_route")
    seen_messages: list[list[dict[str, str]]] = []

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_model_turn(
            [
                _command_response("hai bogus surface"),
                _command_response(),
                _final_response(),
            ],
            seen_messages,
        ),
    )

    assert result.stop_reason == "final"
    step_types = [step["step_type"] for step in result.trajectory["steps"]]
    assert step_types == ["command", "command", "observation", "final"]
    assert result.trajectory["steps"][0]["metadata"]["manifest_rejected"] is True
    assert "metadata" in result.trajectory["steps"][1]
    assert "manifest_rejected" not in result.trajectory["steps"][1]["metadata"]
    assert result.trajectory["steps"][2]["exit_code"] == "OK"
