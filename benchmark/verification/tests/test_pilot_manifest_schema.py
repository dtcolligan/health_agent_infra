"""Pilot manifest gate schema + writer invariants (WP-A7).

Mirrors ``test_model_roster_schema.py``: structural assertions on the schema
dict (``jsonschema`` is not in the venv) plus writer-behaviour checks that the
emitted manifest matches the §12/§14 contract and sources its 33 embedded
input hashes
from a generated lock-hash sidecar rather than hardcoding them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.pilot_manifest import (  # noqa: E402
    SCHEMA_VERSION,
    build_pilot_manifest,
    load_lock_hashes,
)
from governed_agent_bench.scripts import collect_lock_hashes  # noqa: E402

SCHEMA_ROOT = BENCHMARK_ROOT / "governed_agent_bench" / "schema"

RUNTIME_MODES = [
    "full_contract",
    "no_validation",
    "no_agent_safe",
    "no_proposal_gate",
    "no_refusal",
    "no_audit_chain",
    "no_runtime_enforcement",
]


def _schema() -> dict:
    return json.loads(
        (SCHEMA_ROOT / "pilot_manifest.schema.json").read_text(encoding="utf-8")
    )


def _locked_conditional(schema: dict) -> dict:
    for clause in schema["allOf"]:
        if clause["if"]["properties"]["status"]["const"] == "locked":
            return clause
    raise AssertionError("missing locked conditional")


def _draft_kwargs(**overrides) -> dict:
    base = dict(
        status="draft",
        run_start_utc="2026-07-15T14:30Z",
        git_sha="0" * 40,
        conditions_executed=[
            {
                "system_id": "option_b_qwen25_7b_together_v1",
                "runtime_modes": ["full_contract", "no_validation"],
            }
        ],
        replication_n=3,
        d_o_01_selection="pending",
        run_outcome="completed",
    )
    base.update(overrides)
    return base


def _write_lock_hashes_sidecar(tmp_path: Path) -> Path:
    output_path = tmp_path / "lock_hashes.json"
    exit_code = collect_lock_hashes.main(["--output-json", str(output_path)])
    assert exit_code == 0
    return output_path


# --- schema structure -------------------------------------------------------


def test_schema_declares_closed_manifest_surface() -> None:
    schema = _schema()

    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == SCHEMA_VERSION
    assert schema["properties"]["status"]["enum"] == ["draft", "locked"]
    assert schema["properties"]["run_outcome"]["enum"] == [
        "completed",
        "aborted",
        "halted",
    ]
    assert set(schema["required"]) == {
        "schema_version",
        "status",
        "run_start_utc",
        "git_sha",
        "replication_n",
        "conditions_executed",
        "d_o_01_selection",
        "run_outcome",
    }


def test_schema_d_o_01_selection_uses_condition_id_namespace() -> None:
    # §14 option names == roster condition_ids, no _v1 suffix. The _v1 form is
    # reserved for conditions_executed[].system_id (the directory key).
    selection = _schema()["properties"]["d_o_01_selection"]

    assert selection["enum"] == [
        "option_b_qwen25_7b_together",
        "option_b_fallback_qwen25_32b_fireworks",
        "pending",
    ]
    assert all("_v1" not in value for value in selection["enum"])


def test_schema_conditions_executed_carries_inline_runtime_modes() -> None:
    item = _schema()["properties"]["conditions_executed"]["items"]

    assert item["additionalProperties"] is False
    assert set(item["required"]) == {"system_id", "runtime_modes"}
    assert item["properties"]["runtime_modes"]["items"]["enum"] == RUNTIME_MODES


def test_schema_locked_hashes_block_validates_shape_not_counts() -> None:
    # Schema validates hash SHAPE only. The specific inventory counts (5/28/33)
    # are derived data owned by the collector; pinning them in the schema would
    # create a drift-prone third source of truth. Equality to lock_hashes.json
    # is asserted by the writer test instead (single source = the collector).
    locked_hashes = _schema()["properties"]["locked_hashes"]
    fixed_files = locked_hashes["properties"]["fixed_files"]
    task_files = locked_hashes["properties"]["task_files"]
    sha_pattern = "^[a-f0-9]{64}$"

    assert locked_hashes["additionalProperties"] is False
    assert set(locked_hashes["required"]) == {
        "fixed_files",
        "task_files",
        "total_count",
    }
    assert fixed_files["additionalProperties"]["pattern"] == sha_pattern
    assert task_files["additionalProperties"]["pattern"] == sha_pattern
    # No count pinning: no fixed maxProperties, no total_count const.
    assert "maxProperties" not in fixed_files
    assert "maxProperties" not in task_files
    assert "const" not in locked_hashes["properties"]["total_count"]


def test_schema_locked_conditional_requires_full_lock_block() -> None:
    clause = _locked_conditional(_schema())

    assert set(clause["then"]["required"]) == {
        "locked_hashes",
        "lock_date",
        "lock_commit_sha",
    }
    assert clause["then"]["properties"]["d_o_01_selection"]["not"]["const"] == (
        "pending"
    )


# --- writer behaviour -------------------------------------------------------


def test_draft_manifest_omits_lock_block() -> None:
    manifest = build_pilot_manifest(**_draft_kwargs())

    assert manifest["schema_version"] == SCHEMA_VERSION
    assert manifest["status"] == "draft"
    assert manifest["run_outcome"] == "completed"
    for lock_field in ("locked_hashes", "lock_date", "lock_commit_sha"):
        assert lock_field not in manifest


def test_locked_manifest_sources_all_51_embedded_input_hashes_from_sidecar(
    tmp_path: Path,
) -> None:
    lock_hashes_path = _write_lock_hashes_sidecar(tmp_path)
    manifest = build_pilot_manifest(
        **_draft_kwargs(
            status="locked",
            d_o_01_selection="option_b_qwen25_7b_together",
            lock_date="2026-06-25",
            lock_commit_sha="a" * 40,
            lock_hashes_path=lock_hashes_path,
        )
    )

    expected = load_lock_hashes(lock_hashes_path)
    assert manifest["locked_hashes"] == expected
    # D-48 + concentration pass: 39 task files. Powered-run breadth (2026-07-17):
    # +12 mutation-gate tasks -> 51 task files + 5 fixed files = 56 embedded
    # input hashes.
    assert manifest["locked_hashes"]["total_count"] == 56
    assert len(manifest["locked_hashes"]["fixed_files"]) == 5
    assert len(manifest["locked_hashes"]["task_files"]) == 51
    assert manifest["lock_date"] == "2026-06-25"
    assert manifest["lock_commit_sha"] == "a" * 40


def test_namespace_split_selection_vs_system_id(tmp_path: Path) -> None:
    lock_hashes_path = _write_lock_hashes_sidecar(tmp_path)
    # A2 must not conflate the two: selection has no _v1, system_id keeps it.
    manifest = build_pilot_manifest(
        **_draft_kwargs(
            status="locked",
            d_o_01_selection="option_b_qwen25_7b_together",
            conditions_executed=[
                {
                    "system_id": "option_b_qwen25_7b_together_v1",
                    "runtime_modes": ["full_contract"],
                }
            ],
            lock_date="2026-06-22",
            lock_commit_sha="b" * 40,
            lock_hashes_path=lock_hashes_path,
        )
    )

    assert "_v1" not in manifest["d_o_01_selection"]
    assert manifest["conditions_executed"][0]["system_id"].endswith("_v1")


def test_locked_manifest_requires_lock_date_and_commit() -> None:
    with pytest.raises(ValueError, match="lock_date and lock_commit_sha"):
        build_pilot_manifest(
            **_draft_kwargs(
                status="locked",
                d_o_01_selection="option_b_qwen25_7b_together",
                lock_commit_sha="c" * 40,
            )
        )


def test_locked_manifest_rejects_pending_selection() -> None:
    with pytest.raises(ValueError, match="not 'pending'"):
        build_pilot_manifest(
            **_draft_kwargs(
                status="locked",
                d_o_01_selection="pending",
                lock_date="2026-06-22",
                lock_commit_sha="d" * 40,
            )
        )


def test_build_rejects_unknown_status() -> None:
    with pytest.raises(ValueError, match="status must be"):
        build_pilot_manifest(**_draft_kwargs(status="frozen"))


def test_schema_readme_documents_pilot_manifest_schema() -> None:
    readme = (SCHEMA_ROOT / "README.md").read_text(encoding="utf-8")

    assert "pilot_manifest.schema.json" in readme
