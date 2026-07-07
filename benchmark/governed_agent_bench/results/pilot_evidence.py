"""Pilot evidence-table and mechanism-coverage generation for A2 run dirs.

Locked decision 3 (IA-4): the pre-registered 5pp H1 verdict machinery
(the 0.05 delta thresholds, full/off median comparisons, and the
pass/falsify verdict strings) was deleted.
This module now builds the normalized per-rep evidence table plus a MINIMAL
per-mechanism coverage summary (eligible row counts, pooled pass counts,
pass-rate deltas, full-contract critical-violation surfacing, sanity floor).
The paper's quantities are the per-mechanism 2x2 cell contrasts computed by
``results/cell_contrasts.py``; nothing here renders a verdict.

The nested-layout walking (.done-sentinel respect, cross-artifact identity
checks) lives in the shared reader ``results/run_layout.py`` (IA-1) and is
consumed by cell_contrasts and evidence_tables as well.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from governed_agent_bench.harness import load_task
from governed_agent_bench.scorer.core import CRITICAL_VIOLATIONS

from .run_layout import (
    MODE_SORT_ORDER,
    RepRecord,
    iter_nested_condition_dirs,
    iter_nested_rep_records,
    load_json_object,
    require_keys,
)


PILOT_EVIDENCE_TABLE_SCHEMA_VERSION = (
    "governed_agent_bench.pilot_evidence_table.v1"
)
PILOT_MECHANISM_COVERAGE_SCHEMA_VERSION = (
    "governed_agent_bench.pilot_mechanism_coverage.v1"
)
MODEL_BACKED_EVIDENCE_TIER = "model_backed_pilot"
DIAGNOSTIC_EVIDENCE_TIER = "diagnostic_only"
SANITY_FLOOR_ROLE = "sanity_floor"
H1_ATTRIBUTION_ROLE = "h1_attribution"

# Post-audit substitution 2x2 (D-48): only two clean MODEL-ACTION constraints.
# The mutation gate is M5+M6 jointly (redundant defense-in-depth), isolable only
# at the all-off floor (no_agent_safe leaves the untold arm W57-blocked). M7
# clinical refusal is uniquely isolable. M4 validation and M8 audit are
# runtime-internal (reported as scope / blind twin, not 2x2 cells).
MECHANISM_OFF_MODES = {
    "agent_safe": "no_runtime_enforcement",
    "refusal": "no_refusal",
}
MECHANISM_IDS = {
    "validation": "M4",
    "agent_safe": "M5",
    "proposal_gate": "M6",
    "refusal": "M7",
    "audit_chain": "M8",
}
PILOT_CSV_COLUMNS = [
    "run_id",
    "source_run_dir",
    "run_outcome",
    "system_id",
    "runtime_mode",
    "task_id",
    "rep_label",
    "trajectory_id",
    "model_class",
    "model_family",
    "model_id",
    "parameter_count",
    "quantization",
    "provider_snapshot",
    "decoding_settings_json",
    "manifest_id",
    "prompt_template_id",
    "prompt_template_hash",
    "prompt_template_file_hash",
    "claim_tier",
    "model_roster_hash",
    "overall_pass",
    "metric_count",
    "violation_count",
    "violation_kinds",
    "critical_violation_kinds",
    "metrics_json",
    "violations_json",
    "load_bearing_mechanisms",
    "load_bearing_mechanisms_json",
    "evidence_tier",
    "evidence_role",
    "attribution_mechanism",
    "cell_outcome",
    "condition_disposition",
    "abort_reason",
    "offending_mechanism",
    "condition_index_status",
    "task_outcome",
    "reps_completed",
    "ledger_disposition",
    "ledger_disposition_triggers_json",
    "scorer_version",
    "scorer_config_hash",
]

BENCHMARK_ROOT = Path(__file__).resolve().parents[1]


def build_pilot_evidence_rows(run_dir: Path) -> list[dict[str, Any]]:
    """Build one normalized row per completed A2 pilot rep."""

    manifest = load_json_object(run_dir / "pilot_manifest.json")
    require_keys(
        manifest,
        ("schema_version", "run_outcome"),
        run_dir / "pilot_manifest.json",
    )

    condition_indexes: dict[str, dict[str, Any]] = {}
    condition_summaries: dict[tuple[str, str], dict[str, Any]] = {}
    for system_id, system_dir, runtime_mode, mode_dir in (
        iter_nested_condition_dirs(run_dir)
    ):
        if system_id not in condition_indexes:
            condition_index = load_json_object(system_dir / "condition_index.json")
            require_keys(
                condition_index,
                ("coverage", "system_id"),
                system_dir / "condition_index.json",
            )
            if condition_index["system_id"] != system_id:
                raise ValueError(
                    f"{system_dir / 'condition_index.json'}: system_id mismatch"
                )
            condition_indexes[system_id] = condition_index
        summary = load_json_object(mode_dir / "condition_summary.json")
        _validate_condition_summary(summary, system_id, runtime_mode, mode_dir)
        condition_summaries[(system_id, runtime_mode)] = summary

    rows: list[dict[str, Any]] = []
    for record in iter_nested_rep_records(run_dir):
        condition_summary = condition_summaries[
            (record.system_id, record.runtime_mode)
        ]
        index_row = _condition_index_row(
            condition_indexes[record.system_id],
            record.runtime_mode,
            record.task_id,
        )
        rows.append(
            _pilot_row(
                run_dir=run_dir,
                manifest=manifest,
                record=record,
                task=load_task(record.task_id),
                index_row=index_row,
                condition_summary=condition_summary,
            )
        )
    if not rows:
        raise ValueError(f"no completed pilot reps found under {run_dir}")
    return sorted(
        rows,
        key=lambda row: (
            row["system_id"],
            _mode_sort_key(str(row["runtime_mode"])),
            row["task_id"],
            row["rep_label"],
        ),
    )


def build_pilot_evidence_table(run_dir: Path) -> dict[str, Any]:
    rows = build_pilot_evidence_rows(run_dir)
    return {
        "schema_version": PILOT_EVIDENCE_TABLE_SCHEMA_VERSION,
        "source_run_dir": str(run_dir),
        "run_id": run_dir.name,
        "row_count": len(rows),
        "columns": list(PILOT_CSV_COLUMNS),
        "rows": rows,
    }


def write_pilot_evidence_tables(
    *,
    run_dir: Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Write pilot evidence JSON/CSV plus the mechanism-coverage summary."""

    out = output_dir or run_dir / "evidence_tables"
    out.mkdir(parents=True, exist_ok=True)
    table = build_pilot_evidence_table(run_dir)
    table_json_path = out / "pilot_evidence_table.json"
    table_csv_path = out / "pilot_evidence_table.csv"
    coverage_path = out / "pilot_mechanism_coverage.json"

    _write_json(table_json_path, table)
    _write_csv(table_csv_path, table["rows"])
    coverage = build_pilot_mechanism_coverage(table)
    _write_json(coverage_path, coverage)

    return {
        "schema_version": "governed_agent_bench.pilot_evidence_output.v1",
        "row_count": table["row_count"],
        "json_path": table_json_path.as_posix(),
        "csv_path": table_csv_path.as_posix(),
        "mechanism_coverage_path": coverage_path.as_posix(),
    }


def build_pilot_mechanism_coverage(
    evidence_table: Mapping[str, Any],
) -> dict[str, Any]:
    """Minimal per-mechanism coverage bookkeeping for an evidence table.

    Coverage only -- eligible row counts, pooled pass counts and pass-rate
    deltas (locked decision 2 shape), full-contract critical-violation
    surfacing, and the sanity floor. No pre-registered verdicts, no medians,
    no 5pp threshold rule: the paper's quantities live in cell_contrasts.
    """

    rows = _coerce_rows(evidence_table)
    system_ids = sorted({str(row["system_id"]) for row in rows})
    all_scope = _build_coverage_scope(rows)
    per_system = {
        system_id: _build_coverage_scope(
            [row for row in rows if row["system_id"] == system_id]
        )
        for system_id in system_ids
    }
    return {
        "schema_version": PILOT_MECHANISM_COVERAGE_SCHEMA_VERSION,
        "source_evidence_schema_version": evidence_table.get("schema_version"),
        "source_run_dir": evidence_table.get("source_run_dir"),
        "run_id": evidence_table.get("run_id"),
        "row_count": len(rows),
        "evidence_tier": MODEL_BACKED_EVIDENCE_TIER,
        "scope_note": (
            "Coverage bookkeeping only; per-mechanism 2x2 contrasts are "
            "computed by cell_contrasts. Model-backed pilot rows are "
            "summarized separately from static oracle-pair and live "
            "runtime-probe evidence. Diagnostic rows and "
            "no_runtime_enforcement sanity-floor rows are excluded from "
            "per-mechanism eligible counts. Halted whole-run manifests are "
            "conservatively demoted to diagnostic_only until operator "
            "disposition resolves their evidence eligibility."
        ),
        "system_ids": system_ids,
        "mechanisms": all_scope["mechanisms"],
        "sanity_floor": all_scope["sanity_floor"],
        "per_system": per_system,
    }


def load_pilot_evidence_table(path: Path) -> dict[str, Any]:
    payload = load_json_object(path)
    require_keys(payload, ("schema_version", "rows"), path)
    return payload


def write_pilot_mechanism_coverage(
    *,
    evidence_table_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    coverage = build_pilot_mechanism_coverage(
        load_pilot_evidence_table(evidence_table_path)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, coverage)
    return {
        "schema_version": "governed_agent_bench.pilot_mechanism_coverage_output.v1",
        "mechanism_coverage_path": output_path.as_posix(),
    }


def _pilot_row(
    *,
    run_dir: Path,
    manifest: Mapping[str, Any],
    record: RepRecord,
    task: Mapping[str, Any],
    index_row: Mapping[str, Any],
    condition_summary: Mapping[str, Any],
) -> dict[str, Any]:
    score = record.score
    trajectory = record.trajectory
    ledger = record.ledger or {}
    metrics = _dict_value(score.get("metrics"), "score.metrics")
    violations = _list_value(score.get("violations", []), "score.violations")
    violation_kinds = sorted(
        {str(violation.get("kind")) for violation in violations}
    )
    critical_kinds = sorted(set(violation_kinds) & set(CRITICAL_VIOLATIONS))
    load_bearing = [str(value) for value in task.get("load_bearing_mechanisms", [])]
    model_identity = _dict_value(
        score.get("model_identity") or trajectory.get("model_identity") or {},
        "model_identity",
    )
    evidence_tier = _evidence_tier(manifest, condition_summary)
    evidence_role = _evidence_role(
        runtime_mode=record.runtime_mode,
        evidence_tier=evidence_tier,
        load_bearing_mechanisms=load_bearing,
    )
    return {
        "run_id": run_dir.name,
        "source_run_dir": str(run_dir),
        "run_outcome": str(manifest["run_outcome"]),
        "system_id": record.system_id,
        "runtime_mode": record.runtime_mode,
        "task_id": str(score["task_id"]),
        "rep_label": record.rep_label,
        "trajectory_id": str(score["trajectory_id"]),
        "model_class": str(score["model_class"]),
        "model_family": str(model_identity.get("model_family", "")),
        "model_id": str(model_identity.get("model_id", "")),
        "parameter_count": str(model_identity.get("parameter_count", "")),
        "quantization": str(model_identity.get("quantization", "")),
        "provider_snapshot": str(model_identity.get("provider_snapshot", "")),
        "decoding_settings_json": _compact_json(
            model_identity.get("decoding_settings", {})
        ),
        "manifest_id": str(score["manifest_version"]),
        "prompt_template_id": str(trajectory.get("prompt_template_id", "")),
        "prompt_template_hash": str(trajectory.get("prompt_template_hash", "")),
        "prompt_template_file_hash": str(
            trajectory.get("prompt_template_file_hash", "")
        ),
        "claim_tier": str(score.get("claim_tier", trajectory.get("claim_tier", ""))),
        "model_roster_hash": str(
            score.get("model_roster_hash", trajectory.get("model_roster_hash", ""))
        ),
        "overall_pass": bool(score["overall_pass"]),
        "metric_count": len(metrics),
        "violation_count": len(violations),
        "violation_kinds": ",".join(violation_kinds),
        "critical_violation_kinds": ",".join(critical_kinds),
        "metrics_json": _compact_json(metrics),
        "violations_json": _compact_json(violations),
        "load_bearing_mechanisms": ",".join(load_bearing),
        "load_bearing_mechanisms_json": _compact_json(load_bearing),
        "evidence_tier": evidence_tier,
        "evidence_role": evidence_role,
        "attribution_mechanism": _attribution_mechanism(record.runtime_mode),
        "cell_outcome": str(condition_summary["cell_outcome"]),
        "condition_disposition": str(condition_summary["disposition"]),
        "abort_reason": str(condition_summary.get("abort_reason") or ""),
        "offending_mechanism": str(
            condition_summary.get("offending_mechanism") or ""
        ),
        "condition_index_status": str(index_row["status"]),
        "task_outcome": str(index_row.get("task_outcome") or ""),
        "reps_completed": int(index_row.get("reps_completed") or 0),
        "ledger_disposition": str(ledger.get("disposition", "")),
        "ledger_disposition_triggers_json": _compact_json(
            ledger.get("disposition_triggers", [])
        ),
        "scorer_version": str(score["scorer_version"]),
        "scorer_config_hash": str(score["scorer_config_hash"]),
    }


def _build_coverage_scope(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    mechanisms = {
        mechanism: _mechanism_coverage(rows, mechanism)
        for mechanism in MECHANISM_OFF_MODES
    }
    return {
        "mechanisms": mechanisms,
        "sanity_floor": _sanity_floor_summary(rows),
    }


def _mechanism_coverage(
    rows: Sequence[Mapping[str, Any]],
    mechanism: str,
) -> dict[str, Any]:
    """Coverage counts for one mechanism: eligible rows, pooled pass counts,
    pass-rate delta, and full-contract critical-violation surfacing."""

    off_mode = MECHANISM_OFF_MODES[mechanism]
    load_bearing_tasks = _load_bearing_tasks(mechanism, off_mode=None)
    comparison_tasks = _load_bearing_tasks(mechanism, off_mode=off_mode)
    eligible = [
        row
        for row in rows
        if row["evidence_tier"] == MODEL_BACKED_EVIDENCE_TIER
        and row["task_id"] in comparison_tasks
    ]
    full_rows = [
        row for row in eligible if row["runtime_mode"] == "full_contract"
    ]
    off_rows = [row for row in eligible if row["runtime_mode"] == off_mode]
    all_full_rows = [
        row
        for row in rows
        if row["runtime_mode"] == "full_contract"
        and row["task_id"] in load_bearing_tasks
    ]
    full_critical = _critical_violations(all_full_rows)
    full_pass_count = _pass_count(full_rows)
    off_pass_count = _pass_count(off_rows)
    full_total = len(full_rows)
    off_total = len(off_rows)
    pass_rate_delta = _rate(full_pass_count, full_total) - _rate(
        off_pass_count, off_total
    )
    return {
        "mechanism_id": MECHANISM_IDS[mechanism],
        "mechanism": mechanism,
        "disabled_by_runtime_mode": off_mode,
        "load_bearing_tasks": load_bearing_tasks,
        "comparison_task_ids": comparison_tasks,
        "eligible_full_contract_pass_count": full_pass_count,
        "eligible_full_contract_total": full_total,
        "eligible_no_x_pass_count": off_pass_count,
        "eligible_no_x_total": off_total,
        "pass_rate_delta_full_minus_no_x": round(pass_rate_delta, 12),
        "full_contract_critical_violation_observed": bool(full_critical),
        "full_contract_critical_violations": full_critical,
        "enough_eligible_rows_for_model_backed_comparison": (
            full_total > 0 and off_total > 0
        ),
    }


def _sanity_floor_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    sanity_rows = [
        row
        for row in rows
        if row["runtime_mode"] == "no_runtime_enforcement"
        and row["evidence_tier"] == MODEL_BACKED_EVIDENCE_TIER
    ]
    return {
        "runtime_mode": "no_runtime_enforcement",
        "role": SANITY_FLOOR_ROLE,
        "assigned_to_h1_attribution": False,
        "eligible_rep_count": len(sanity_rows),
        "eligible_pass_count": _pass_count(sanity_rows),
        "pass_rate": round(_rate(_pass_count(sanity_rows), len(sanity_rows)), 12),
        "task_ids": sorted({str(row["task_id"]) for row in sanity_rows}),
    }


def _evidence_tier(
    manifest: Mapping[str, Any],
    condition_summary: Mapping[str, Any],
) -> str:
    cell_outcome = condition_summary.get("cell_outcome")
    if cell_outcome in {"aborted", "halted", "paused"}:
        return DIAGNOSTIC_EVIDENCE_TIER
    if manifest.get("run_outcome") == "halted":
        return DIAGNOSTIC_EVIDENCE_TIER
    return MODEL_BACKED_EVIDENCE_TIER


def _evidence_role(
    *,
    runtime_mode: str,
    evidence_tier: str,
    load_bearing_mechanisms: Sequence[str],
) -> str:
    if evidence_tier == DIAGNOSTIC_EVIDENCE_TIER:
        return DIAGNOSTIC_EVIDENCE_TIER
    if runtime_mode == "no_runtime_enforcement":
        return SANITY_FLOOR_ROLE
    if load_bearing_mechanisms:
        return H1_ATTRIBUTION_ROLE
    return "model_backed_context"


def _attribution_mechanism(runtime_mode: str) -> str:
    for mechanism, off_mode in MECHANISM_OFF_MODES.items():
        if runtime_mode == off_mode:
            return mechanism
    return ""


def _load_bearing_tasks(mechanism: str, off_mode: str | None) -> list[str]:
    task_ids: list[str] = []
    for path in sorted((BENCHMARK_ROOT / "tasks").glob("l[1-7]/gab_*.json")):
        task = load_json_object(path)
        if mechanism not in task.get("load_bearing_mechanisms", []):
            continue
        modes = task.get("runtime_modes_in_scope", [])
        if off_mode is not None and not (
            "full_contract" in modes and off_mode in modes
        ):
            continue
        task_ids.append(str(task["task_id"]))
    return task_ids


def _condition_index_row(
    condition_index: Mapping[str, Any],
    runtime_mode: str,
    task_id: str,
) -> Mapping[str, Any]:
    try:
        row = condition_index["coverage"][runtime_mode]["per_task"][task_id]
    except KeyError as exc:
        raise ValueError(
            f"condition_index missing coverage row for {runtime_mode}/{task_id}"
        ) from exc
    if not isinstance(row, dict):
        raise ValueError(
            f"condition_index coverage row must be an object for {runtime_mode}/{task_id}"
        )
    require_keys(row, ("status", "reps_completed"), Path("condition_index.json"))
    if row["status"] != "in_scope_run":
        raise ValueError(
            "condition_index coverage row for a scored rep must be "
            f"in_scope_run: {runtime_mode}/{task_id}"
        )
    return row


def _validate_condition_summary(
    summary: Mapping[str, Any],
    system_id: str,
    runtime_mode: str,
    mode_dir: Path,
) -> None:
    require_keys(
        summary,
        ("system_id", "runtime_mode", "cell_outcome", "disposition"),
        mode_dir / "condition_summary.json",
    )
    if summary["system_id"] != system_id:
        raise ValueError(f"{mode_dir}: condition_summary system_id mismatch")
    if summary["runtime_mode"] != runtime_mode:
        raise ValueError(f"{mode_dir}: condition_summary runtime_mode mismatch")


def _critical_violations(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        for violation in _violations(row):
            kind = str(violation.get("kind", ""))
            if kind not in CRITICAL_VIOLATIONS:
                continue
            out.append({
                "task_id": row["task_id"],
                "rep_label": row["rep_label"],
                "kind": kind,
                "mechanism": violation.get("mechanism"),
                "evidence_tier": row["evidence_tier"],
            })
    return out


def _violations(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    value = json.loads(str(row["violations_json"]))
    if not isinstance(value, list):
        raise ValueError("violations_json must decode to a list")
    return [item for item in value if isinstance(item, dict)]


def _pass_count(rows: Sequence[Mapping[str, Any]]) -> int:
    return sum(1 for row in rows if row["overall_pass"] is True)


def _rate(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return count / total


def _coerce_rows(evidence_table: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = evidence_table.get("rows")
    if not isinstance(rows, list):
        raise ValueError("pilot evidence table must contain rows list")
    coerced: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("pilot evidence table rows must be objects")
        missing = set(PILOT_CSV_COLUMNS) - set(row)
        if missing:
            raise ValueError(f"pilot evidence row missing columns: {sorted(missing)}")
        coerced.append(row)
    return coerced


def _mode_sort_key(runtime_mode: str) -> int:
    try:
        return MODE_SORT_ORDER.index(runtime_mode)
    except ValueError:
        return len(MODE_SORT_ORDER)


def _dict_value(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _list_value(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def _compact_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PILOT_CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in PILOT_CSV_COLUMNS})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    output = write_pilot_evidence_tables(
        run_dir=args.run_dir,
        output_dir=args.output_dir,
    )
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
