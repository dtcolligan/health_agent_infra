"""Lock-day checklist runner for PILOT_PROTOCOL.md §14."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from governed_agent_bench.harness import load_task
from governed_agent_bench.provider_probe import build_provider_probe_report
from governed_agent_bench.scripts.collect_lock_hashes import build_lock_hashes_payload


SCHEMA_VERSION = "governed_agent_bench.lock_checklist.v1"
BENCHMARK_ROOT = Path(__file__).resolve().parent
REPO_ROOT = BENCHMARK_ROOT.parents[1]
PILOT_PROTOCOL_PATH = BENCHMARK_ROOT / "PILOT_PROTOCOL.md"
SCORER_CONFIG_PATH = BENCHMARK_ROOT / "scorer_config.paper_v1.json"
SAFETY_SUBSET_PATH = BENCHMARK_ROOT / "safety_constrained_subset.json"
SCHEMA_DIR = BENCHMARK_ROOT / "schema"
L7_TURN_STEP_TYPES = {"command", "refusal", "final", "invalid_output"}
ProviderReportBuilder = Callable[[], dict[str, Any]]


def build_lock_checklist_report(
    *,
    protocol_path: Path = PILOT_PROTOCOL_PATH,
    now_utc: datetime | None = None,
    live_provider_probe: bool = False,
    provider_report_builder: ProviderReportBuilder | None = None,
) -> dict[str, Any]:
    """Return a lock checklist report without mutating lock documents."""

    when = now_utc or datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    checklist_rows = _extract_checklist_rows(protocol_path.read_text(encoding="utf-8"))
    mechanical_checks = {
        "lock_hashes": _check_lock_hashes(),
        "l7_turn_budget": _check_l7_turn_budget(),
        "provider_probe": _check_provider_probe(
            live=live_provider_probe,
            provider_report_builder=provider_report_builder,
        ),
        "safety_subset": _check_safety_subset(),
        "schema_json_parse": _check_schema_json_parse(),
        "scorer_config_provenance": _check_scorer_config_provenance(),
        "scorer_config_status": _check_scorer_config_status(),
    }
    rows = [
        _row_status(row, mechanical_checks)
        for row in checklist_rows
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _zfmt(when),
        "protocol_path": protocol_path.as_posix(),
        "no_lock_doc_mutation": True,
        "live_provider_probe": live_provider_probe,
        "overall_status": _overall_status(rows, mechanical_checks),
        "mechanical_checks": mechanical_checks,
        "checklist_rows": rows,
    }


def write_lock_checklist_report(
    *,
    output_dir: Path,
    now_utc: datetime | None = None,
    live_provider_probe: bool = False,
    provider_report_builder: ProviderReportBuilder | None = None,
) -> dict[str, Any]:
    when = now_utc or datetime.now(timezone.utc)
    report = build_lock_checklist_report(
        now_utc=when,
        live_provider_probe=live_provider_probe,
        provider_report_builder=provider_report_builder,
    )
    stamp = _zfmt(when).replace(":", "").replace("-", "").replace("Z", "Z")
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"lock_checklist_{stamp}.json"
    markdown_path = output_dir / f"lock_checklist_{stamp}.md"
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_markdown(report), encoding="utf-8")
    return {
        "schema_version": "governed_agent_bench.lock_checklist_output.v1",
        "json_path": json_path.as_posix(),
        "markdown_path": markdown_path.as_posix(),
        "overall_status": report["overall_status"],
    }


def _extract_checklist_rows(text: str) -> list[str]:
    start = text.index("## §14 Lock Procedure")
    end = text.index("## Locked Hashes", start)
    rows: list[str] = []
    current: list[str] = []
    for raw in text[start:end].splitlines():
        if raw.startswith("- [ ] "):
            if current:
                rows.append(" ".join(current).strip())
            current = [raw.removeprefix("- [ ] ").strip()]
        elif current and raw.startswith("      "):
            current.append(raw.strip())
        elif current and raw.strip() == "":
            continue
    if current:
        rows.append(" ".join(current).strip())
    return rows


def _row_status(
    row: str,
    mechanical_checks: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    lowered = row.lower()
    if "provider ids and pricing" in lowered:
        return _checklist_row(row, "provider_probe", mechanical_checks["provider_probe"])
    if "scorer_config.paper_v1.json provenance" in lowered:
        return _checklist_row(
            row,
            "scorer_config_provenance",
            mechanical_checks["scorer_config_provenance"],
        )
    if "status` field flipped" in lowered:
        return _pending_row(
            row,
            "operator_confirmation",
            "Lock-day status flip remains a Dom-authorized action.",
            mechanical_checks["scorer_config_status"],
        )
    if "l7 pass trajectories" in lowered:
        return _checklist_row(row, "l7_turn_budget", mechanical_checks["l7_turn_budget"])
    if "safety_constrained_subset" in lowered:
        return _pending_row(
            row,
            "operator_confirmation",
            "Safety-subset hash can be generated mechanically but must be recorded at lock.",
            mechanical_checks["safety_subset"],
        )
    if "sha-256 recorded" in lowered or "document's sha-256" in lowered:
        return _pending_row(
            row,
            "operator_confirmation",
            "SHA-256 values are mechanically available but must be recorded in the lock commit.",
            mechanical_checks["lock_hashes"],
        )
    if "d-o-01 decided" in lowered:
        return _pending_row(
            row,
            "operator_confirmation",
            "D-O-01 is a lock-day Dom decision.",
        )
    if "lock commit pushed" in lowered:
        return _pending_row(
            row,
            "operator_confirmation",
            "Push requires separate Dom authorization.",
        )
    if "cost budget reserve" in lowered or "ratified by dom" in lowered:
        return _pending_row(
            row,
            "operator_confirmation",
            "Requires operator confirmation at lock.",
        )
    return _pending_row(
        row,
        "operator_confirmation",
        "Checklist row requires operator confirmation.",
    )


def _checklist_row(
    row: str,
    check_id: str,
    check: Mapping[str, Any],
) -> dict[str, Any]:
    status = str(check["status"])
    return {
        "text": row,
        "status": status,
        "check_id": check_id,
        "detail": check.get("detail"),
    }


def _pending_row(
    row: str,
    pending_kind: str,
    detail: str,
    mechanical_check: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "text": row,
        "status": "pending_operator_confirmation",
        "pending_kind": pending_kind,
        "detail": detail,
    }
    if mechanical_check is not None:
        payload["mechanical_check_status"] = mechanical_check["status"]
        payload["mechanical_check_detail"] = mechanical_check.get("detail")
    return payload


def _check_lock_hashes() -> dict[str, Any]:
    try:
        payload = build_lock_hashes_payload()
    except Exception as exc:  # noqa: BLE001 - checklist artifact records failure.
        return {"status": "fail", "detail": str(exc)}
    fixed_count = len(payload.get("fixed_files", {}))
    task_count = len(payload.get("task_files", {}))
    status = "pass" if fixed_count == 6 and task_count == 28 else "fail"
    return {
        "status": status,
        "detail": f"{fixed_count} fixed files and {task_count} task files hashed",
        "total_count": payload.get("total_count"),
    }


def _check_l7_turn_budget() -> dict[str, Any]:
    failures = []
    for task_path in sorted((BENCHMARK_ROOT / "tasks" / "l7").glob("gab_*.json")):
        task_id = task_path.stem
        trajectory_path = (
            BENCHMARK_ROOT / "trajectories" / "hand_authored" / f"{task_id}_pass.json"
        )
        if not trajectory_path.exists():
            failures.append({"task_id": task_id, "reason": "missing pass trajectory"})
            continue
        payload = _load_json(trajectory_path)
        turn_count = sum(
            1
            for step in payload.get("steps", [])
            if isinstance(step, dict) and step.get("step_type") in L7_TURN_STEP_TYPES
        )
        if turn_count > 7:
            failures.append({
                "task_id": task_id,
                "reason": f"{turn_count} turns exceeds 7",
            })
    return {
        "status": "pass" if not failures else "fail",
        "detail": "all L7 pass trajectories are <=7 turns" if not failures else "L7 failures",
        "failures": failures,
    }


def _check_provider_probe(
    *,
    live: bool,
    provider_report_builder: ProviderReportBuilder | None,
) -> dict[str, Any]:
    report = (
        provider_report_builder()
        if provider_report_builder is not None
        else build_provider_probe_report(live=live)
    )
    status = "pass" if report["overall_status"] == "verified_live" else "pending"
    return {
        "status": status,
        "detail": str(report["overall_status"]),
        "provider_report": report,
    }


def _check_safety_subset() -> dict[str, Any]:
    subset = _load_json(SAFETY_SUBSET_PATH)
    task_ids = set(str(task_id) for task_id in subset.get("task_ids", []))
    expected = set()
    for task_path in sorted((BENCHMARK_ROOT / "tasks").glob("l[1-7]/gab_*.json")):
        task = load_task(task_path.stem)
        mechanisms = set(task.get("load_bearing_mechanisms", []))
        if mechanisms & {"refusal", "agent_safe", "proposal_gate"}:
            expected.add(str(task["task_id"]))
    status = "pass" if task_ids == expected and len(task_ids) == 14 else "fail"
    return {
        "status": status,
        "detail": f"{len(task_ids)} safety-constrained tasks enumerated",
        "missing": sorted(expected - task_ids),
        "extra": sorted(task_ids - expected),
    }


def _check_schema_json_parse() -> dict[str, Any]:
    failures = []
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        try:
            _load_json(path)
        except Exception as exc:  # noqa: BLE001 - checklist artifact records failure.
            failures.append({"path": path.as_posix(), "error": str(exc)})
    return {
        "status": "pass" if not failures else "fail",
        "detail": "all schema JSON files parse" if not failures else "schema parse failures",
        "failures": failures,
    }


def _check_scorer_config_provenance() -> dict[str, Any]:
    payload = _load_json(SCORER_CONFIG_PATH)
    provenance = payload.get("provenance", {})
    ok = (
        isinstance(provenance, dict)
        and provenance.get("source") == "PAPER.md"
        and provenance.get("decision_id") == "D-14"
    )
    return {
        "status": "pass" if ok else "fail",
        "detail": "scorer_config provenance points at PAPER.md D-14",
    }


def _check_scorer_config_status() -> dict[str, Any]:
    payload = _load_json(SCORER_CONFIG_PATH)
    status = payload.get("scorer_config_status")
    return {
        "status": "pass" if status == "frozen" else "pending",
        "detail": f"scorer_config_status={status!r}",
    }


def _overall_status(
    rows: Sequence[Mapping[str, Any]],
    mechanical_checks: Mapping[str, Mapping[str, Any]],
) -> str:
    if any(check["status"] == "fail" for check in mechanical_checks.values()):
        return "fail"
    if any(row["status"] == "pending_operator_confirmation" for row in rows):
        return "pending_operator_confirmation"
    if any(check["status"] == "pending" for check in mechanical_checks.values()):
        return "pending"
    return "pass"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _zfmt(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )


def _markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Lock Checklist",
        "",
        f"- Generated at UTC: `{report['generated_at_utc']}`",
        f"- Overall status: `{report['overall_status']}`",
        f"- Live provider probe: `{report['live_provider_probe']}`",
        f"- Lock docs mutated: `{not report['no_lock_doc_mutation']}`",
        "",
        "## Mechanical Checks",
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]
    for check_id, check in report["mechanical_checks"].items():
        lines.append(f"| `{check_id}` | `{check['status']}` | {check.get('detail', '')} |")
    lines.extend(["", "## §14 Rows", "", "| Status | Row |", "|---|---|"])
    for row in report["checklist_rows"]:
        lines.append(f"| `{row['status']}` | {row['text']} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--live-provider-probe",
        action="store_true",
        help="Attempt C1 read-only provider probe while running the checklist.",
    )
    args = parser.parse_args(argv)
    output = write_lock_checklist_report(
        output_dir=args.output_dir,
        live_provider_probe=args.live_provider_probe,
    )
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
