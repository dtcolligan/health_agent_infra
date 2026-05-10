"""Error-taxonomy report tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.results import (  # noqa: E402
    ERROR_TAXONOMY_SCHEMA_VERSION,
    build_error_taxonomy,
    write_error_taxonomy,
)


def _row(
    *,
    task_id: str,
    level: str,
    runtime_mode: str,
    model_class: str,
    violations: list[dict[str, str]],
) -> dict:
    return {
        "task_id": task_id,
        "level": level,
        "trajectory_id": f"traj_{task_id}_{runtime_mode}",
        "system_id": "test_system",
        "model_class": model_class,
        "runtime_mode": runtime_mode,
        "manifest_id": "hai_0_2_0",
        "prompt_template_id": "deployment_full_v1",
        "prompt_template_hash": "0" * 64,
        "prompt_template_file_hash": "1" * 64,
        "scorer_version": "test_scorer",
        "scorer_config_hash": "2" * 64,
        "overall_pass": not violations,
        "metric_count": 1,
        "violation_count": len(violations),
        "violation_kinds": ",".join(sorted({item["kind"] for item in violations})),
        "violations_json": json.dumps(violations, sort_keys=True),
        "metrics_json": "{}",
    }


def test_error_taxonomy_aggregates_by_required_axes() -> None:
    rows = [
        _row(
            task_id="gab_l6_block_agent_commit",
            level="L6",
            runtime_mode="no_agent_safe",
            model_class="rule_baseline",
            violations=[
                {"kind": "unsafe_mutation", "detail": "hai intent commit"},
                {"kind": "refusal_error", "detail": "required refusal missing"},
            ],
        ),
        _row(
            task_id="gab_l6_refuse_diagnosis_request",
            level="L6",
            runtime_mode="no_refusal",
            model_class="local",
            violations=[{"kind": "clinical_claim", "detail": "phrase"}],
        ),
        _row(
            task_id="gab_l1_today_json_route",
            level="L1",
            runtime_mode="full_contract",
            model_class="rule_baseline",
            violations=[],
        ),
    ]

    taxonomy = build_error_taxonomy(rows)

    assert taxonomy["schema_version"] == ERROR_TAXONOMY_SCHEMA_VERSION
    assert taxonomy["row_count"] == 3
    assert taxonomy["violating_row_count"] == 2
    assert taxonomy["violation_count"] == 3
    assert taxonomy["by_violation_kind"] == {
        "clinical_claim": 1,
        "refusal_error": 1,
        "unsafe_mutation": 1,
    }
    assert taxonomy["by_task_level"]["L6"]["violation_count"] == 3
    assert taxonomy["by_runtime_mode"]["no_agent_safe"]["kinds"]["unsafe_mutation"] == 1
    assert taxonomy["by_model_class"]["rule_baseline"]["violation_count"] == 2
    assert taxonomy["by_task_mechanism"]["agent_safe"]["violation_count"] == 2
    assert taxonomy["by_task_mechanism"]["refusal"]["violation_count"] == 1
    assert taxonomy["by_runtime_mechanism"]["agent_safe"]["violation_count"] == 2
    assert taxonomy["by_runtime_mechanism"]["refusal"]["violation_count"] == 1


def test_write_error_taxonomy_is_deterministic(tmp_path: Path) -> None:
    evidence_path = tmp_path / "evidence_table.json"
    rows = [
        _row(
            task_id="gab_l6_refuse_diagnosis_request",
            level="L6",
            runtime_mode="no_refusal",
            model_class="local",
            violations=[{"kind": "clinical_claim", "detail": "phrase"}],
        )
    ]
    evidence_path.write_text(
        json.dumps({"schema_version": "test", "rows": rows}, sort_keys=True),
        encoding="utf-8",
    )

    first = write_error_taxonomy(
        evidence_table_path=evidence_path,
        output_dir=tmp_path / "out",
    )
    first_json = (tmp_path / "out" / "error_taxonomy.json").read_text(
        encoding="utf-8"
    )
    second = write_error_taxonomy(
        evidence_table_path=evidence_path,
        output_dir=tmp_path / "out",
    )
    second_json = (tmp_path / "out" / "error_taxonomy.json").read_text(
        encoding="utf-8"
    )

    assert first == second
    assert first_json == second_json
    assert first["violation_count"] == 1
