from __future__ import annotations

import argparse
import json
import sys
from datetime import date as date_type
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from health_model.retrieval_request_metadata import validate_and_echo_request_metadata


class CliParseError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliParseError(message)


REQUIRED_ARTIFACT_TYPE = "agent_readable_daily_context"
WEEKLY_MEMORY_ARTIFACT_TYPE = "weekly_pattern_review_memory"
WEEKLY_RANGE_LIMIT_DAYS = 7


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        description="Read a scoped Health Lab daily context artifact through a stable external CLI."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("--artifact-path", required=True)
    get_parser.add_argument("--user-id", required=True)
    get_parser.add_argument("--date", required=True)

    latest_parser = subparsers.add_parser("get-latest")
    latest_parser.add_argument("--artifact-path", required=True)
    latest_parser.add_argument("--user-id", required=True)

    weekly_parser = subparsers.add_parser("retrieve-weekly-pattern-review")
    weekly_parser.add_argument("--user-id", required=True)
    weekly_parser.add_argument("--start-date", required=True)
    weekly_parser.add_argument("--end-date", required=True)
    weekly_parser.add_argument("--memory-locator", required=True)
    weekly_parser.add_argument("--request-id", required=True)
    weekly_parser.add_argument("--requested-at", required=True)
    weekly_parser.add_argument("--timezone")
    weekly_parser.add_argument("--max-evidence-items", type=int)
    weekly_parser.add_argument("--include-conflicts", choices=["true", "false"])
    weekly_parser.add_argument("--include-missingness", choices=["true", "false"])

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()

    try:
        args = parser.parse_args(argv)
        response = run_command(args)
    except CliParseError as exc:
        print(json.dumps(_error_response(code="cli_parse_error", message=str(exc), argv=argv), indent=2, sort_keys=True))
        return 1
    except Exception as exc:
        print(
            json.dumps(
                _error_response(
                    code="cli_runtime_error",
                    message=str(exc),
                    args=args if "args" in locals() else None,
                    argv=argv,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    print(json.dumps(response, indent=2, sort_keys=True))
    return 0 if response.get("ok") else 1


def run_command(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "retrieve-weekly-pattern-review":
        return _run_weekly_pattern_review(args)
    if args.command not in {"get", "get-latest"}:
        raise ValueError(f"Unsupported command: {args.command}")

    path = Path(args.artifact_path)
    return _read_context_artifact(path=path, user_id=args.user_id, date=getattr(args, "date", None))


def _read_context_artifact(*, path: Path, user_id: str, date: str | None) -> dict[str, Any]:
    if not path.exists():
        return _validation_error(
            artifact_path=str(path),
            code="artifact_not_found",
            message="Artifact file does not exist.",
            semantic_issues=[_issue(code="artifact_not_found", message="Artifact file does not exist.", path="artifact_path")],
            details={"artifact_path": str(path)},
        )

    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return _validation_error(
            artifact_path=str(path),
            code="invalid_artifact_json",
            message="Artifact file is not valid JSON.",
            semantic_issues=[_issue(code="invalid_artifact_json", message=str(exc), path="artifact_path")],
            details={"artifact_path": str(path)},
        )

    semantic_issues = _artifact_semantic_issues(raw=raw, user_id=user_id, date=date)
    if semantic_issues:
        error_code = semantic_issues[0]["code"]
        return _validation_error(
            artifact_path=str(path),
            code=error_code,
            message="Artifact failed scope or type validation.",
            semantic_issues=semantic_issues,
            details={"artifact_path": str(path), "user_id": user_id, "date": date},
        )

    return {
        "ok": True,
        "artifact_path": str(path),
        "context": raw,
        "validation": {"is_valid": True, "schema_issues": [], "semantic_issues": []},
        "error": None,
    }


def _run_weekly_pattern_review(args: argparse.Namespace) -> dict[str, Any]:
    request_validation, _request_echo = validate_and_echo_request_metadata(
        request_id=args.request_id,
        requested_at=args.requested_at,
    )
    if not request_validation["is_valid"]:
        return {
            "ok": False,
            "artifact_path": args.memory_locator,
            "retrieval": None,
            "validation": request_validation,
            "error": {
                "code": request_validation["semantic_issues"][0]["code"],
                "message": "Request metadata failed validation.",
                "retryable": False,
                "details": {
                    "command": args.command,
                    "request_echo": request_validation["request_echo"],
                },
            },
        }

    range_validation = _validate_weekly_scope(
        user_id=args.user_id,
        start_date=args.start_date,
        end_date=args.end_date,
        memory_locator=args.memory_locator,
    )
    if range_validation is not None:
        return _weekly_error(
            memory_locator=args.memory_locator,
            code=range_validation["semantic_issues"][0]["code"],
            message="Weekly scope failed validation.",
            semantic_issues=range_validation["semantic_issues"],
            request_validation=request_validation,
            details=range_validation["details"],
        )

    locator_path = Path(args.memory_locator)
    if not locator_path.exists():
        return _weekly_error(
            memory_locator=args.memory_locator,
            code="memory_locator_not_found",
            message="memory_locator could not be resolved.",
            semantic_issues=[_issue(code="memory_locator_not_found", message="memory_locator could not be resolved.", path="memory_locator")],
            request_validation=request_validation,
            details={"memory_locator": args.memory_locator},
        )

    try:
        locator_payload = json.loads(locator_path.read_text())
    except json.JSONDecodeError as exc:
        return _weekly_error(
            memory_locator=args.memory_locator,
            code="invalid_memory_locator_json",
            message="memory_locator did not resolve to valid JSON.",
            semantic_issues=[_issue(code="invalid_memory_locator_json", message=str(exc), path="memory_locator")],
            request_validation=request_validation,
            details={"memory_locator": args.memory_locator},
        )

    locator_issues = _weekly_memory_locator_issues(
        payload=locator_payload,
        user_id=args.user_id,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    if locator_issues:
        return _weekly_error(
            memory_locator=args.memory_locator,
            code=locator_issues[0]["code"],
            message="memory_locator failed bounded weekly fixture validation.",
            semantic_issues=locator_issues,
            request_validation=request_validation,
            details={
                "memory_locator": args.memory_locator,
                "user_id": args.user_id,
                "start_date": args.start_date,
                "end_date": args.end_date,
            },
        )

    day_paths = [Path(path_str) for path_str in locator_payload["accepted_daily_artifact_paths"]]
    contexts: list[dict[str, Any]] = []
    generated_from: list[dict[str, Any]] = []
    for day_path in day_paths:
        context_response = _read_context_artifact(path=day_path, user_id=args.user_id, date=None)
        if not context_response.get("ok"):
            return _weekly_error(
                memory_locator=args.memory_locator,
                code=context_response["error"]["code"],
                message="Accepted daily artifact failed validation.",
                semantic_issues=context_response["validation"]["semantic_issues"],
                request_validation=request_validation,
                details={
                    "memory_locator": args.memory_locator,
                    "daily_artifact_path": str(day_path),
                },
            )
        context = context_response["context"]
        expected_date = day_path.stem.rsplit("_", 1)[-1]
        if context.get("date") != expected_date:
            return _weekly_error(
                memory_locator=args.memory_locator,
                code="artifact_date_mismatch",
                message="Accepted daily artifact date did not match its bounded weekly fixture path.",
                semantic_issues=[
                    _issue(
                        code="artifact_date_mismatch",
                        message="Accepted daily artifact date did not match its bounded weekly fixture path.",
                        path="date",
                    )
                ],
                request_validation=request_validation,
                details={"daily_artifact_path": str(day_path), "expected_date": expected_date},
            )
        contexts.append(context)
        generated_from.append(
            {
                "date": context["date"],
                "artifact_path": str(day_path),
                "context_id": context.get("context_id"),
            }
        )

    contexts.sort(key=lambda item: item["date"])
    if [ctx["date"] for ctx in contexts] != _expected_dates(args.start_date, args.end_date):
        return _weekly_error(
            memory_locator=args.memory_locator,
            code="non_contiguous_range",
            message="Accepted daily artifacts did not cover one contiguous bounded weekly range.",
            semantic_issues=[
                _issue(
                    code="non_contiguous_range",
                    message="Accepted daily artifacts did not cover one contiguous bounded weekly range.",
                    path="accepted_daily_artifact_paths",
                )
            ],
            request_validation=request_validation,
            details={"memory_locator": args.memory_locator},
        )

    include_conflicts = args.include_conflicts != "false"
    include_missingness = args.include_missingness != "false"
    max_evidence_items = args.max_evidence_items if args.max_evidence_items is not None and args.max_evidence_items > 0 else None

    per_day = [_build_weekly_day_summary(context) for context in contexts]
    if max_evidence_items is not None:
        per_day = per_day[:max_evidence_items]

    important_gap_counts: dict[str, int] = {}
    conflicts: list[dict[str, Any]] = []
    missing_days = 0
    partial_days = 0
    for context in contexts:
        for gap in context.get("important_gaps", []):
            if isinstance(gap, dict):
                code = gap.get("code")
            else:
                code = gap
            if isinstance(code, str):
                important_gap_counts[code] = important_gap_counts.get(code, 0) + 1
        if context.get("conflicts"):
            for conflict in context["conflicts"]:
                conflicts.append({"date": context["date"], **conflict})
        day_status = _context_coverage_status(context)
        if day_status == "missing":
            missing_days += 1
        elif day_status == "partial":
            partial_days += 1

    repeated_gaps = [
        {"code": code, "days_present": count}
        for code, count in sorted(important_gap_counts.items())
        if count >= 2
    ]
    if not include_missingness:
        repeated_gaps = []

    if not include_conflicts:
        conflicts = []

    return {
        "ok": True,
        "artifact_path": args.memory_locator,
        "retrieval": {
            "operation": "retrieve.weekly_pattern_review",
            "scope": {
                "user_id": args.user_id,
                "start_date": args.start_date,
                "end_date": args.end_date,
                "timezone": args.timezone,
            },
            "coverage_status": _weekly_coverage_status(missing_days=missing_days, partial_days=partial_days),
            "generated_from": {
                "memory_locator": args.memory_locator,
                "accepted_daily_artifacts": generated_from,
            },
            "evidence": {
                "days_reviewed": len(contexts),
                "per_day": per_day,
            },
            "important_gaps": repeated_gaps,
            "conflicts": conflicts,
            "unsupported_claims": [],
        },
        "validation": request_validation,
        "error": None,
    }


def _validate_weekly_scope(*, user_id: str, start_date: str, end_date: str, memory_locator: str) -> dict[str, Any] | None:
    semantic_issues: list[dict[str, str]] = []
    parsed_start = _parse_iso_date(start_date)
    parsed_end = _parse_iso_date(end_date)
    if parsed_start is None:
        semantic_issues.append(_issue(code="invalid_start_date", message="start_date must be YYYY-MM-DD.", path="start_date"))
    if parsed_end is None:
        semantic_issues.append(_issue(code="invalid_end_date", message="end_date must be YYYY-MM-DD.", path="end_date"))
    if not isinstance(user_id, str) or not user_id.strip():
        semantic_issues.append(_issue(code="invalid_user_id", message="user_id must be a non-empty string.", path="user_id"))
    if not isinstance(memory_locator, str) or not memory_locator.strip():
        semantic_issues.append(
            _issue(code="invalid_memory_locator", message="memory_locator must be a non-empty string.", path="memory_locator")
        )
    if parsed_start is not None and parsed_end is not None:
        if parsed_end < parsed_start:
            semantic_issues.append(
                _issue(code="non_contiguous_range", message="end_date must be on or after start_date.", path="end_date")
            )
        elif (parsed_end - parsed_start).days + 1 > WEEKLY_RANGE_LIMIT_DAYS:
            semantic_issues.append(
                _issue(
                    code="range_limit_exceeded",
                    message=f"Weekly retrieval is capped at {WEEKLY_RANGE_LIMIT_DAYS} contiguous days.",
                    path="end_date",
                )
            )
    if semantic_issues:
        return {
            "semantic_issues": semantic_issues,
            "details": {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date,
                "memory_locator": memory_locator,
            },
        }
    return None


def _weekly_memory_locator_issues(*, payload: Any, user_id: str, start_date: str, end_date: str) -> list[dict[str, str]]:
    if not isinstance(payload, dict):
        return [_issue(code="invalid_memory_locator_payload", message="memory_locator payload must be an object.", path="$")]
    issues: list[dict[str, str]] = []
    if payload.get("artifact_type") != WEEKLY_MEMORY_ARTIFACT_TYPE:
        issues.append(
            _issue(
                code="memory_locator_wrong_type",
                message=f"Expected artifact_type={WEEKLY_MEMORY_ARTIFACT_TYPE}.",
                path="artifact_type",
            )
        )
    if payload.get("user_id") != user_id:
        issues.append(_issue(code="memory_locator_wrong_scope", message="memory_locator user_id did not match request.", path="user_id"))
    if payload.get("start_date") != start_date:
        issues.append(
            _issue(code="memory_locator_wrong_scope", message="memory_locator start_date did not match request.", path="start_date")
        )
    if payload.get("end_date") != end_date:
        issues.append(
            _issue(code="memory_locator_wrong_scope", message="memory_locator end_date did not match request.", path="end_date")
        )
    paths = payload.get("accepted_daily_artifact_paths")
    if not isinstance(paths, list) or not paths:
        issues.append(
            _issue(
                code="memory_locator_missing_daily_artifacts",
                message="memory_locator must list accepted_daily_artifact_paths.",
                path="accepted_daily_artifact_paths",
            )
        )
    return issues


def _build_weekly_day_summary(context: dict[str, Any]) -> dict[str, Any]:
    sleep = context.get("semantic_context", {}).get("sleep", {})
    return {
        "date": context["date"],
        "coverage_status": _context_coverage_status(context),
        "sleep_review": {
            "primary_sleep_window": sleep.get("primary_sleep_window", {}),
            "total_sleep_duration_minutes": sleep.get("total_sleep_duration_minutes", {}),
            "subjective_sleep_quality": sleep.get("subjective_sleep_quality", {}),
        },
        "important_gap_codes": [
            gap.get("code") if isinstance(gap, dict) else gap for gap in context.get("important_gaps", [])
        ],
        "conflict_codes": [conflict.get("code") for conflict in context.get("conflicts", []) if isinstance(conflict, dict)],
    }


def _context_coverage_status(context: dict[str, Any]) -> str:
    gap_count = len(context.get("important_gaps", []))
    statuses = [
        signal.get("status")
        for signal in context.get("explicit_grounding", {}).get("signals", [])
        if isinstance(signal, dict) and signal.get("domain") == "sleep"
    ]
    if statuses and all(status == "missing" for status in statuses):
        return "missing"
    if gap_count or any(status == "missing" for status in statuses):
        return "partial"
    return "present"


def _weekly_coverage_status(*, missing_days: int, partial_days: int) -> str:
    if missing_days == WEEKLY_RANGE_LIMIT_DAYS:
        return "missing"
    if missing_days or partial_days:
        return "partial"
    return "present"


def _expected_dates(start_date: str, end_date: str) -> list[str]:
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    days = []
    current = start
    while current <= end:
        days.append(current.isoformat())
        current += timedelta(days=1)
    return days


def _parse_iso_date(value: str) -> date_type | None:
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def _artifact_semantic_issues(*, raw: Any, user_id: str, date: str | None) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(raw, dict):
        return [_issue(code="artifact_not_object", message="Artifact JSON must be an object.", path="$")]
    if raw.get("artifact_type") != REQUIRED_ARTIFACT_TYPE:
        issues.append(
            _issue(
                code="artifact_type_mismatch",
                message=f"Expected artifact_type={REQUIRED_ARTIFACT_TYPE}.",
                path="artifact_type",
            )
        )
    if raw.get("user_id") != user_id:
        issues.append(_issue(code="artifact_user_mismatch", message="Artifact user_id does not match request.", path="user_id"))
    if date is not None and raw.get("date") != date:
        issues.append(_issue(code="artifact_date_mismatch", message="Artifact date does not match request.", path="date"))
    return issues


def _weekly_error(
    *,
    memory_locator: str,
    code: str,
    message: str,
    semantic_issues: list[dict[str, str]],
    request_validation: dict[str, Any],
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ok": False,
        "artifact_path": memory_locator,
        "retrieval": None,
        "validation": {
            **request_validation,
            "is_valid": False,
            "semantic_issues": semantic_issues,
        },
        "error": {
            "code": code,
            "message": message,
            "retryable": False,
            "details": details,
        },
    }


def _validation_error(
    *,
    artifact_path: str | None,
    code: str,
    message: str,
    semantic_issues: list[dict[str, str]],
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ok": False,
        "artifact_path": artifact_path,
        "context": None,
        "validation": {"is_valid": False, "schema_issues": [], "semantic_issues": semantic_issues},
        "error": {
            "code": code,
            "message": message,
            "retryable": False,
            "details": details,
        },
    }


def _error_response(
    *,
    code: str,
    message: str,
    args: argparse.Namespace | None = None,
    argv: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "artifact_path": getattr(args, "artifact_path", None),
        "context": None,
        "validation": {"is_valid": False, "schema_issues": [], "semantic_issues": []},
        "error": {
            "code": code,
            "message": message,
            "retryable": False,
            "details": {
                "command": getattr(args, "command", None),
                "argv": argv or sys.argv[1:],
            },
        },
    }


def _issue(*, code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


if __name__ == "__main__":
    raise SystemExit(main())
