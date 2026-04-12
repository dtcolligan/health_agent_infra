from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from typing import Any

from health_model.agent_interface import (
    append_fragment_and_regenerate_daily_context,
    submit_hydration_log,
    submit_nutrition_text_note,
)


class CliParseError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliParseError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        description="Submit one nutrition or hydration record and atomically regenerate Health Lab daily context artifacts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for entry_type in ("hydration", "meal"):
        subparser = subparsers.add_parser(entry_type)
        _add_shared_arguments(subparser)
        if entry_type == "hydration":
            subparser.add_argument("--amount-ml", type=float, required=True)
            subparser.add_argument("--beverage-type")
            subparser.add_argument("--notes")
        else:
            subparser.add_argument("--note-text", required=True)
            subparser.add_argument("--meal-label")
            subparser.add_argument("--estimated", required=True, choices=("true", "false"))
            subparser.add_argument("--notes")

    return parser


def _add_shared_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--bundle-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--collected-at", required=True)
    parser.add_argument("--ingested-at", required=True)
    parser.add_argument("--raw-location", required=True)
    parser.add_argument("--confidence-score", type=float, required=True)
    parser.add_argument("--completeness-state", required=True, choices=("partial", "complete", "corrected"))
    parser.add_argument("--source-name")


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
    timestamp_validation = _validate_requested_day(args)
    if timestamp_validation is not None:
        return timestamp_validation

    if args.command == "hydration":
        intake = submit_hydration_log(
            user_id=args.user_id,
            date=args.date,
            amount_ml=args.amount_ml,
            beverage_type=args.beverage_type,
            completeness_state=args.completeness_state,
            collected_at=args.collected_at,
            ingested_at=args.ingested_at,
            raw_location=args.raw_location,
            confidence_score=args.confidence_score,
            source_name=args.source_name or "manual_hydration_log",
            notes=args.notes,
        )
    elif args.command == "meal":
        intake = submit_nutrition_text_note(
            user_id=args.user_id,
            date=args.date,
            note_text=args.note_text,
            meal_label=args.meal_label,
            estimated=_parse_bool(args.estimated),
            completeness_state=args.completeness_state,
            collected_at=args.collected_at,
            ingested_at=args.ingested_at,
            raw_location=args.raw_location,
            confidence_score=args.confidence_score,
            source_name=args.source_name or "manual_nutrition_log",
            notes=args.notes,
        )
    else:
        raise ValueError(f"Unsupported command: {args.command}")

    if not intake["ok"]:
        return {
            "ok": False,
            "bundle_path": args.bundle_path,
            "dated_artifact_path": None,
            "latest_artifact_path": None,
            "accepted_provenance": _accepted_provenance_from_intake(intake),
            "validation": intake["validation"],
            "error": intake["error"],
        }

    result = append_fragment_and_regenerate_daily_context(
        bundle_path=args.bundle_path,
        output_dir=args.output_dir,
        fragment=intake["bundle_fragment"],
        user_id=args.user_id,
        date=args.date,
    )
    if not result["ok"]:
        result["accepted_provenance"] = _accepted_provenance_from_intake(intake)
    return result


def _accepted_provenance_from_intake(intake: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "source_artifact_ids": [intake["artifact"]["artifact_id"]] if intake.get("artifact") else [],
        "input_event_ids": [event["event_id"] for event in intake.get("derived_events", [])],
        "subjective_entry_ids": [],
        "manual_log_entry_ids": [intake["entry"]["entry_id"]] if intake.get("entry") else [],
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
        "bundle_path": getattr(args, "bundle_path", None),
        "dated_artifact_path": None,
        "latest_artifact_path": None,
        "accepted_provenance": {},
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


def _validate_requested_day(args: argparse.Namespace) -> dict[str, Any] | None:
    semantic_issues = []
    for field_name in ("collected_at", "ingested_at"):
        timestamp_value = getattr(args, field_name)
        timestamp_day = datetime.fromisoformat(timestamp_value).date().isoformat()
        if timestamp_day != args.date:
            semantic_issues.append(
                {
                    "code": "timestamp_date_mismatch",
                    "message": f"{field_name} must fall on the requested date.",
                    "path": field_name,
                }
            )

    if not semantic_issues:
        return None

    return {
        "ok": False,
        "bundle_path": args.bundle_path,
        "dated_artifact_path": None,
        "latest_artifact_path": None,
        "accepted_provenance": {},
        "validation": {"is_valid": False, "schema_issues": [], "semantic_issues": semantic_issues},
        "error": {
            "code": "bundle_fragment_scope_mismatch",
            "message": "CLI request timestamps must match the requested date.",
            "retryable": False,
            "details": {"user_id": args.user_id, "date": args.date},
        },
    }


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"Expected true or false, got: {value}")


if __name__ == "__main__":
    raise SystemExit(main())
