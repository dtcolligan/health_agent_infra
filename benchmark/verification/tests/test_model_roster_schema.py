"""Model roster gate schema invariants."""

from __future__ import annotations

import json
from pathlib import Path


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = BENCHMARK_ROOT / "governed_agent_bench" / "schema"


def _schema() -> dict:
    return json.loads(
        (SCHEMA_ROOT / "model_roster.schema.json").read_text(encoding="utf-8")
    )


def _condition_schema(schema: dict) -> dict:
    return schema["$defs"]["condition"]


def _condition_conditional(schema: dict, model_class: str) -> dict:
    for clause in _condition_schema(schema)["allOf"]:
        model_class_schema = clause["if"]["properties"]["model_class"]
        if model_class_schema.get("const") == model_class:
            return clause
        if model_class in model_class_schema.get("enum", []):
            return clause
    raise AssertionError(f"missing conditional for {model_class}")


def test_model_roster_schema_binds_markdown_roster_and_hash_scope() -> None:
    schema = _schema()

    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == (
        "governed_agent_bench.model_roster.v1"
    )
    assert schema["properties"]["roster_file"]["const"] == (
        "benchmark/governed_agent_bench/model_roster.md"
    )
    assert schema["properties"]["hash_algorithm"]["const"] == "sha256"
    assert schema["properties"]["hash_scope"]["const"] == (
        "entire_model_roster_md_file_bytes"
    )
    assert schema["properties"]["status"]["const"] == "predeclared"


def test_model_roster_schema_requires_dom_approval_and_synthetic_scope() -> None:
    schema = _schema()
    required = set(schema["required"])
    scope = schema["properties"]["scope"]

    assert {
        "approved_by",
        "approved_at",
        "decision_path",
        "scope",
        "conditions",
        "immutability_rule",
    }.issubset(required)
    assert schema["properties"]["approved_by"]["const"] == "Dom"
    assert schema["properties"]["decision_path"]["const"] == (
        "predeclared_model_roster"
    )
    assert scope["properties"]["data_boundary"]["const"] == (
        "synthetic_governed_agent_bench_fixtures_only"
    )
    assert scope["properties"]["private_data_allowed"]["const"] is False


def test_condition_schema_requires_identity_boundary_and_repro_fields() -> None:
    condition = _condition_schema(_schema())

    assert condition["additionalProperties"] is False
    assert set(condition["required"]) == {
        "condition_id",
        "system_id",
        "model_class",
        "model_family",
        "model_id",
        "provider",
        "provider_snapshot_date",
        "model_card_snapshot",
        "parameter_count",
        "quantization",
        "weights_source",
        "compute_boundary",
        "cost_boundary",
        "data_boundary",
        "decoding_settings",
        "prompt_id",
        "manifest_id",
        "runtime_modes",
        "failure_reporting",
    }
    assert condition["properties"]["model_class"]["enum"] == [
        "local",
        "cloud",
        "fine_tuned_local",
    ]
    assert condition["properties"]["data_boundary"]["const"] == (
        "synthetic_governed_agent_bench_fixtures_only"
    )
    assert condition["properties"]["prompt_id"]["enum"] == ["deployment_full_v1", "deployment_full_v2"]


def test_condition_schema_requires_deterministic_decoding_fields() -> None:
    decoding = _condition_schema(_schema())["properties"]["decoding_settings"]

    assert decoding["additionalProperties"] is False
    assert decoding["required"] == [
        "temperature",
        "top_p",
        "max_tokens",
        "seed",
    ]
    assert decoding["properties"]["temperature"]["minimum"] == 0
    assert decoding["properties"]["max_tokens"]["minimum"] == 1
    assert decoding["properties"]["seed"]["oneOf"][1]["const"] == (
        "provider_does_not_support_seed"
    )


def test_condition_schema_requires_runtime_modes_and_reportable_failures() -> None:
    condition = _condition_schema(_schema())
    runtime_modes = condition["properties"]["runtime_modes"]["items"]["enum"]
    failure_reporting = condition["properties"]["failure_reporting"]

    assert runtime_modes == [
        "full_contract",
        "no_validation",
        "no_agent_safe",
        "no_proposal_gate",
        "no_refusal",
        "no_audit_chain",
        "no_runtime_enforcement",
    ]
    assert failure_reporting["additionalProperties"] is False
    assert failure_reporting["required"] == [
        "timeout",
        "refusal",
        "invalid_json",
        "adapter_failure",
    ]
    for field in failure_reporting["required"]:
        assert failure_reporting["properties"][field]["const"] == (
            "reportable_outcome"
        )


def test_model_class_conditionals_require_matching_approvals() -> None:
    schema = _schema()

    local_clause = _condition_conditional(schema, "local")
    fine_tuned_clause = _condition_conditional(schema, "fine_tuned_local")
    cloud_clause = _condition_conditional(schema, "cloud")

    assert local_clause is fine_tuned_clause
    assert local_clause["then"]["required"] == ["local_compute_approval"]
    assert cloud_clause["then"]["required"] == ["cloud_approval"]
    assert (
        _condition_schema(schema)["properties"]["local_compute_approval"]["$ref"]
        == "#/$defs/approval"
    )
    assert (
        _condition_schema(schema)["properties"]["cloud_approval"]["$ref"]
        == "#/$defs/approval"
    )


def test_schema_readme_marks_roster_schema_as_non_authorizing() -> None:
    readme = (SCHEMA_ROOT / "README.md").read_text(encoding="utf-8")

    assert "model_roster.schema.json" in readme
    assert "model_roster.md" in readme
    assert "does not choose models" in readme
    assert "does not authorize model" in readme
