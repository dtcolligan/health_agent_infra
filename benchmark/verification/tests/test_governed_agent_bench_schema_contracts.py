"""Guard schema invariants required by the research planning layer."""

from __future__ import annotations

import json
from pathlib import Path


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = BENCHMARK_ROOT / "governed_agent_bench" / "schema"
TRAJECTORY_ROOT = BENCHMARK_ROOT / "governed_agent_bench" / "trajectories"


def _schema(name: str) -> dict:
    return json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))


# ---- trajectory --------------------------------------------------------


def test_trajectory_records_structured_operator_actions() -> None:
    trajectory = _schema("trajectory.schema.json")
    step_properties = trajectory["properties"]["steps"]["items"]["properties"]
    step_types = set(step_properties["step_type"]["enum"])

    assert "runtime_mode" in trajectory["required"]
    assert "model_class" in trajectory["required"]
    assert "manifest_snapshot_id" in trajectory["required"]
    assert "prompt_template_id" in trajectory["required"]
    assert "prompt_template_hash" in trajectory["required"]
    assert "args" in step_properties
    assert "reason" in step_properties
    assert "final_text" in step_properties
    assert "mechanism_disabled" in step_properties["step_type"]["enum"]
    assert "invalid_output" in step_types
    assert {"message", "command", "observation", "refusal", "final"}.issubset(
        step_types
    )


def test_trajectory_step_requires_mechanism_for_mechanism_disabled() -> None:
    """`mechanism_disabled` steps must declare which mechanism was disabled."""
    trajectory = _schema("trajectory.schema.json")
    step_schema = trajectory["properties"]["steps"]["items"]
    conditionals = step_schema["allOf"]

    # Find the `mechanism_disabled => mechanism required` rule.
    found = False
    for clause in conditionals:
        if (
            clause["if"]["properties"]["step_type"]["const"] == "mechanism_disabled"
            and "mechanism" in clause["then"]["required"]
        ):
            found = True
            break
    assert found, "trajectory step schema must require `mechanism` when step_type=mechanism_disabled"


def test_trajectory_command_step_requires_command() -> None:
    trajectory = _schema("trajectory.schema.json")
    step_schema = trajectory["properties"]["steps"]["items"]
    conditionals = step_schema["allOf"]

    found = False
    for clause in conditionals:
        if (
            clause["if"]["properties"]["step_type"]["const"] == "command"
            and "command" in clause["then"]["required"]
        ):
            found = True
            break
    assert found, "trajectory step schema must require `command` when step_type=command"


def test_trajectory_invalid_output_step_requires_raw_output_and_parse_error() -> None:
    trajectory = _schema("trajectory.schema.json")
    step_schema = trajectory["properties"]["steps"]["items"]
    step_properties = step_schema["properties"]
    conditionals = step_schema["allOf"]

    assert step_properties["raw_output"]["type"] == "string"
    assert step_properties["parse_error"]["type"] == "string"

    found = False
    for clause in conditionals:
        if (
            clause["if"]["properties"]["step_type"]["const"] == "invalid_output"
            and {"raw_output", "parse_error"}.issubset(
                clause["then"]["required"]
            )
        ):
            found = True
            break
    assert found, (
        "trajectory step schema must require `raw_output` and `parse_error` "
        "when step_type=invalid_output"
    )


def test_pre_existing_trajectory_step_types_still_match_schema() -> None:
    trajectory = _schema("trajectory.schema.json")
    allowed_step_types = set(
        trajectory["properties"]["steps"]["items"]["properties"]["step_type"]["enum"]
    )

    paths = [
        *sorted((TRAJECTORY_ROOT / "hand_authored").glob("*.json")),
        *sorted((TRAJECTORY_ROOT / "adversarial").glob("*.json")),
    ]
    assert paths
    for path in paths:
        row = json.loads(path.read_text(encoding="utf-8"))
        for step in row["steps"]:
            assert step["step_type"] in allowed_step_types, path


def test_trajectory_requires_model_identity_unless_rule_baseline() -> None:
    """A rule baseline does not need model_identity; everything else does."""
    trajectory = _schema("trajectory.schema.json")
    conditionals = trajectory["allOf"]

    found = False
    for clause in conditionals:
        if (
            clause["if"]["properties"]["model_class"]["const"] == "rule_baseline"
            and "model_identity" in clause.get("else", {}).get("required", [])
        ):
            found = True
            break
    assert found, (
        "trajectory schema must require `model_identity` for non-rule_baseline runs"
    )


# ---- score ------------------------------------------------------------


def test_score_schema_records_reproducibility_anchors() -> None:
    trajectory = _schema("trajectory.schema.json")
    score = _schema("score.schema.json")

    for field in (
        "runtime_mode",
        "model_class",
        "manifest_version",
        "scorer_version",
        "scorer_config_hash",
    ):
        assert field in score["required"], (
            f"score schema must require `{field}` for reproducibility"
        )

    assert (
        score["properties"]["runtime_mode"]["enum"]
        == trajectory["properties"]["runtime_mode"]["enum"]
    )
    assert (
        score["properties"]["model_class"]["enum"]
        == trajectory["properties"]["model_class"]["enum"]
    )


def test_score_metric_requires_threshold_no_null() -> None:
    """Every reported metric must have a non-null threshold; per F-CDX-RFR-R1-06."""
    score = _schema("score.schema.json")
    metric_props = score["properties"]["metrics"]["additionalProperties"]
    assert "threshold" in metric_props["required"], (
        "score metric must require `threshold`"
    )
    threshold_types = metric_props["properties"]["threshold"]["type"]
    assert "null" not in threshold_types, (
        "score metric `threshold` must not allow null"
    )
    assert "string" not in metric_props["properties"]["value"]["type"]


def test_score_violation_requires_mechanism_for_mechanism_disabled_unexpected() -> None:
    score = _schema("score.schema.json")
    violation_schema = score["properties"]["violations"]["items"]
    conditionals = violation_schema["allOf"]

    found = False
    for clause in conditionals:
        if (
            clause["if"]["properties"]["kind"]["const"]
            == "mechanism_disabled_unexpected"
            and "mechanism" in clause["then"]["required"]
        ):
            found = True
            break
    assert found, (
        "score violation schema must require `mechanism` when "
        "kind=mechanism_disabled_unexpected"
    )


def test_score_requires_model_identity_unless_rule_baseline() -> None:
    score = _schema("score.schema.json")
    conditionals = score["allOf"]

    found = False
    for clause in conditionals:
        if (
            clause["if"]["properties"]["model_class"]["const"] == "rule_baseline"
            and "model_identity" in clause.get("else", {}).get("required", [])
        ):
            found = True
            break
    assert found, "score schema must require `model_identity` for non-rule_baseline"


# ---- task -------------------------------------------------------------


def test_task_metric_enum_matches_scoring_spec() -> None:
    task = _schema("task.schema.json")
    metrics = task["properties"]["metrics"]["items"]["enum"]

    assert "audit_reference_faithfulness" in metrics


def test_task_records_mechanism_load_bearing_field() -> None:
    task = _schema("task.schema.json")
    assert "load_bearing_mechanisms" in task["properties"]
    assert "runtime_modes_in_scope" in task["properties"]
    assert "load_bearing_mechanisms" in task["required"]
    assert "runtime_modes_in_scope" in task["required"]


def test_task_load_bearing_enum_excludes_held_constant_mechanisms() -> None:
    """Per F-CDX-RFR-R1-13: `harness_allowlist` (a held-constant M3 control)
    must not leak into the task's load_bearing_mechanisms enum."""
    task = _schema("task.schema.json")
    enum_values = set(
        task["properties"]["load_bearing_mechanisms"]["items"]["enum"]
    )
    assert "harness_allowlist" not in enum_values, (
        "harness_allowlist is held constant; it must not appear as a load-bearing "
        "mechanism in tasks"
    )
    expected = {"validation", "agent_safe", "proposal_gate", "refusal", "audit_chain"}
    assert enum_values == expected


# ---- cross-schema -----------------------------------------------------


def test_runtime_modes_cover_mechanism_ablations() -> None:
    """The runtime_mode enum must include the full_contract baseline plus one
    mechanism_off mode per ablatable mechanism, plus the no_runtime_enforcement
    extreme. Names must be honest about scope."""
    trajectory = _schema("trajectory.schema.json")
    modes = set(trajectory["properties"]["runtime_mode"]["enum"])

    expected = {
        "full_contract",
        "no_validation",
        "no_agent_safe",
        "no_proposal_gate",
        "no_refusal",
        "no_audit_chain",
        "no_runtime_enforcement",
    }
    assert modes == expected, (
        f"runtime_mode enum mismatch: missing {expected - modes}, "
        f"unexpected {modes - expected}"
    )
    # Per F-CDX-RFR-R1-04: the misleading `no_runtime` name is retired in v2.
    assert "no_runtime" not in modes


def test_mechanism_enum_consistent_across_schemas() -> None:
    trajectory = _schema("trajectory.schema.json")
    score = _schema("score.schema.json")
    task = _schema("task.schema.json")

    traj_mech = set(
        trajectory["properties"]["steps"]["items"]["properties"]["mechanism"]["enum"]
    )
    score_mech = set(
        score["properties"]["violations"]["items"]["properties"]["mechanism"]["enum"]
    )
    task_mech = set(
        task["properties"]["load_bearing_mechanisms"]["items"]["enum"]
    )

    expected = {"validation", "agent_safe", "proposal_gate", "refusal", "audit_chain"}
    assert traj_mech == expected
    assert score_mech == expected
    assert task_mech == expected


# ---- round-2 closeout schema additions ------------------------------------


def test_trajectory_records_round_2_closeout_fields() -> None:
    """Per F-CDX-RFR-R2-03/05/06, trajectories must accept the round-2
    closeout fields: `prompt_template_file_hash`, `invocation_context`,
    and `model_roster_hash`.
    """
    trajectory = _schema("trajectory.schema.json")
    properties = trajectory["properties"]

    assert "prompt_template_file_hash" in properties, (
        "F-CDX-RFR-R2-05: prompt_template_file_hash distinguishes "
        "template-file hash from rendered-prompt hash."
    )
    assert "invocation_context" in properties, (
        "F-CDX-RFR-R2-03: invocation_context records the CLI-dispatch "
        "agent_safe enforcer's caller classification."
    )
    assert properties["invocation_context"]["enum"] == [
        "agent",
        "user",
        "rule_baseline",
    ]
    assert "model_roster_hash" in properties, (
        "F-CDX-RFR-R2-06: model_roster_hash binds the trajectory to a "
        "predeclared model roster for Tier 3/4 evidence."
    )


def test_score_requires_model_roster_hash_for_t3_t4() -> None:
    """Per F-CDX-RFR-R2-06, scores tagged claim_tier ∈ {T3, T4} must
    carry a non-null `model_roster_hash`. The conditional invariant is
    encoded in the score schema's allOf block.
    """
    score = _schema("score.schema.json")

    assert "claim_tier" in score["properties"]
    assert score["properties"]["claim_tier"]["enum"] == [
        "T0",
        "T1",
        "T2",
        "T3",
        "T4",
    ]
    assert "model_roster_hash" in score["properties"]

    conditionals = score["allOf"]
    roster_conditional = next(
        (
            c
            for c in conditionals
            if "claim_tier" in (c.get("if", {}).get("properties", {}) or {})
        ),
        None,
    )
    assert roster_conditional is not None, (
        "F-CDX-RFR-R2-06: score schema must encode the T3/T4 → "
        "model_roster_hash required conditional."
    )
    triggers = roster_conditional["if"]["properties"]["claim_tier"]["enum"]
    assert set(triggers) == {"T3", "T4"}
    assert "model_roster_hash" in roster_conditional["then"]["required"]
