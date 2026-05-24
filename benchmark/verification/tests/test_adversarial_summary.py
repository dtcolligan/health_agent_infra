"""Adversarial summary artifact tests."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

import pytest


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
TEST_ROOT = Path(__file__).resolve().parent
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

from governed_agent_bench.reproduce_offline import (  # noqa: E402
    _exit_code_for_manifest,
)
from governed_agent_bench.results.adversarial_summary import (  # noqa: E402
    ADVERSARIAL_FAMILIES,
    EXPECTED_VIOLATIONS,
    build_adversarial_summary,
)
from test_adversarial_trajectories import EXPECTED_ATTACKS  # noqa: E402


@pytest.fixture()
def summary_artifacts(tmp_path: Path) -> tuple[dict[str, Any], Path]:
    output_dir = tmp_path / "adversarial_summary"
    summary = build_adversarial_summary(output_dir=output_dir)
    return summary, output_dir


def _json_rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["rows"]
    assert isinstance(rows, list)
    return rows


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_aggregated_table_has_four_family_rows(
    summary_artifacts: tuple[dict[str, Any], Path],
) -> None:
    summary, output_dir = summary_artifacts
    rows = _json_rows(output_dir / "adversarial_summary_aggregated.json")

    assert summary["aggregated_count"] == 4
    assert len(rows) == 4
    assert {row["family"] for row in rows} == {
        "validation",
        "mutation_escalation",
        "refusal_bypass",
        "audit_tampering",
    }


def test_per_trajectory_table_has_sixteen_rows(
    summary_artifacts: tuple[dict[str, Any], Path],
) -> None:
    summary, output_dir = summary_artifacts
    rows = _json_rows(output_dir / "adversarial_summary_per_trajectory.json")

    assert summary["per_trajectory_count"] == 16
    assert len(rows) == 16


def test_every_trajectory_scored_overall_pass_false(
    summary_artifacts: tuple[dict[str, Any], Path],
) -> None:
    summary, output_dir = summary_artifacts
    rows = _json_rows(output_dir / "adversarial_summary_per_trajectory.json")

    assert summary["all_expected_failures_observed"] is True
    assert all(row["overall_pass"] is False for row in rows)


def test_family_counts_balanced(
    summary_artifacts: tuple[dict[str, Any], Path],
) -> None:
    summary, output_dir = summary_artifacts
    aggregated_rows = _json_rows(output_dir / "adversarial_summary_aggregated.json")

    assert summary["family_counts"] == {
        "validation": 4,
        "mutation_escalation": 4,
        "refusal_bypass": 4,
        "audit_tampering": 4,
    }
    assert {
        row["family"]: row["n_trajectories"] for row in aggregated_rows
    } == summary["family_counts"]


def test_csv_and_json_rowcounts_match(
    summary_artifacts: tuple[dict[str, Any], Path],
) -> None:
    _summary, output_dir = summary_artifacts

    aggregated_json_rows = _json_rows(
        output_dir / "adversarial_summary_aggregated.json"
    )
    aggregated_csv_rows = _csv_rows(
        output_dir / "adversarial_summary_aggregated.csv"
    )
    per_json_rows = _json_rows(
        output_dir / "adversarial_summary_per_trajectory.json"
    )
    per_csv_rows = _csv_rows(
        output_dir / "adversarial_summary_per_trajectory.csv"
    )

    assert len(aggregated_csv_rows) == len(aggregated_json_rows)
    assert len(per_csv_rows) == len(per_json_rows)


def test_summary_dict_passes_offline_repro_exit_code_check(
    summary_artifacts: tuple[dict[str, Any], Path],
) -> None:
    summary, _output_dir = summary_artifacts
    manifest = {
        "isolation_matrix": {"all_isolated": True},
        "live_isolation": {"skipped": True, "reason": "skip_flag"},
        "adversarial_summary": {
            "all_expected_failures_observed": summary[
                "all_expected_failures_observed"
            ],
            "all_expected_violation_kinds_observed": summary[
                "all_expected_violation_kinds_observed"
            ],
        },
    }

    assert summary["all_expected_failures_observed"] is True
    assert summary["all_expected_violation_kinds_observed"] is True
    assert _exit_code_for_manifest(manifest) == 0


def test_family_mapping_matches_expected_attacks() -> None:
    expected = {
        filename: row["target"]
        for filename, row in EXPECTED_ATTACKS.items()
    }

    assert ADVERSARIAL_FAMILIES == expected


def test_expected_violations_mapping_matches_expected_attacks() -> None:
    expected = {
        filename: set(row["violations"])
        for filename, row in EXPECTED_ATTACKS.items()
    }

    assert EXPECTED_VIOLATIONS == expected


def test_every_trajectory_emits_expected_violation_kinds(
    summary_artifacts: tuple[dict[str, Any], Path],
) -> None:
    summary, output_dir = summary_artifacts
    rows = _json_rows(output_dir / "adversarial_summary_per_trajectory.json")

    assert summary["all_expected_violation_kinds_observed"] is True
    for row in rows:
        filename = row["trajectory_filename"]
        observed = set(row["violation_kinds"])
        assert observed >= EXPECTED_VIOLATIONS[filename]
