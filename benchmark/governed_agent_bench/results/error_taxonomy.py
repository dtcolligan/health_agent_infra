"""Violation taxonomy reports from evidence tables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from governed_agent_bench.harness import load_task


ERROR_TAXONOMY_SCHEMA_VERSION = "governed_agent_bench.error_taxonomy.v1"
MODE_TO_MECHANISM = {
    "no_validation": "validation",
    "no_agent_safe": "agent_safe",
    "no_proposal_gate": "proposal_gate",
    "no_refusal": "refusal",
    "no_audit_chain": "audit_chain",
    "no_runtime_enforcement": "all_runtime_mechanisms",
}


def build_error_taxonomy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate violation counts by benchmark-relevant axes."""

    parsed = [_parse_row(row) for row in rows]
    violations = [violation for row in parsed for violation in row["violations"]]
    return {
        "schema_version": ERROR_TAXONOMY_SCHEMA_VERSION,
        "row_count": len(parsed),
        "violating_row_count": sum(1 for row in parsed if row["violations"]),
        "violation_count": len(violations),
        "by_violation_kind": _count_by(violations, "kind"),
        "by_task_level": _axis_counts(parsed, "level"),
        "by_runtime_mode": _axis_counts(parsed, "runtime_mode"),
        "by_model_class": _axis_counts(parsed, "model_class"),
        "by_task_mechanism": _task_mechanism_counts(parsed),
        "by_runtime_mechanism": _runtime_mechanism_counts(parsed),
    }


def write_error_taxonomy(
    *,
    evidence_table_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Write an error-taxonomy JSON report from an evidence table."""

    table = json.loads(evidence_table_path.read_text(encoding="utf-8"))
    taxonomy = build_error_taxonomy(table["rows"])
    taxonomy["source_evidence_table"] = evidence_table_path.as_posix()
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "error_taxonomy.json"
    path.write_text(
        json.dumps(taxonomy, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "schema_version": "governed_agent_bench.error_taxonomy_output.v1",
        "json_path": path.as_posix(),
        "row_count": taxonomy["row_count"],
        "violation_count": taxonomy["violation_count"],
    }


def _parse_row(row: dict[str, Any]) -> dict[str, Any]:
    parsed = dict(row)
    parsed["violations"] = _violations(row)
    parsed["task_mechanisms"] = load_task(row["task_id"])["load_bearing_mechanisms"]
    parsed["runtime_mechanism"] = MODE_TO_MECHANISM.get(row["runtime_mode"])
    return parsed


def _violations(row: dict[str, Any]) -> list[dict[str, Any]]:
    payload = row.get("violations_json")
    if isinstance(payload, str) and payload:
        loaded = json.loads(payload)
        if isinstance(loaded, list):
            return loaded
    kinds = [
        kind.strip()
        for kind in str(row.get("violation_kinds", "")).split(",")
        if kind.strip()
    ]
    return [{"kind": kind, "detail": ""} for kind in kinds]


def _axis_counts(
    rows: list[dict[str, Any]],
    key: str,
) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        bucket = output.setdefault(
            str(row[key]),
            {
                "row_count": 0,
                "violating_row_count": 0,
                "violation_count": 0,
                "kinds": {},
            },
        )
        bucket["row_count"] += 1
        if row["violations"]:
            bucket["violating_row_count"] += 1
        bucket["violation_count"] += len(row["violations"])
        _merge_kind_counts(bucket["kinds"], row["violations"])
    return output


def _task_mechanism_counts(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        for mechanism in row["task_mechanisms"]:
            bucket = output.setdefault(
                mechanism,
                {
                    "row_count": 0,
                    "violating_row_count": 0,
                    "violation_count": 0,
                    "kinds": {},
                },
            )
            bucket["row_count"] += 1
            if row["violations"]:
                bucket["violating_row_count"] += 1
            bucket["violation_count"] += len(row["violations"])
            _merge_kind_counts(bucket["kinds"], row["violations"])
    return output


def _runtime_mechanism_counts(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        mechanism = row["runtime_mechanism"]
        if mechanism is None:
            continue
        bucket = output.setdefault(
            mechanism,
            {
                "row_count": 0,
                "violating_row_count": 0,
                "violation_count": 0,
                "kinds": {},
            },
        )
        bucket["row_count"] += 1
        if row["violations"]:
            bucket["violating_row_count"] += 1
        bucket["violation_count"] += len(row["violations"])
        _merge_kind_counts(bucket["kinds"], row["violations"])
    return output


def _count_by(
    violations: list[dict[str, Any]],
    key: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for violation in violations:
        value = str(violation[key])
        counts[value] = counts.get(value, 0) + 1
    return counts


def _merge_kind_counts(
    counts: dict[str, int],
    violations: list[dict[str, Any]],
) -> None:
    for violation in violations:
        kind = str(violation["kind"])
        counts[kind] = counts.get(kind, 0) + 1
