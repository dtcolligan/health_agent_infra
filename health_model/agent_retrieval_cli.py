from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from health_model import agent_context_cli
from health_model.retrieval_request_metadata import validate_and_echo_request_metadata


class CliParseError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliParseError(message)


SLEEP_EVIDENCE_KEYS = [
    "primary_sleep_window",
    "total_sleep_duration_minutes",
    "subjective_sleep_quality",
    "sleep_timing_regularity_marker",
    "sleep_disruption_markers",
]


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="Run bounded Health Lab retrieval operations through a stable JSON CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sleep_review = subparsers.add_parser("sleep-review")
    sleep_review.add_argument("--artifact-path", required=True)
    sleep_review.add_argument("--user-id", required=True)
    sleep_review.add_argument("--date", required=True)
    sleep_review.add_argument("--request-id", required=True)
    sleep_review.add_argument("--requested-at", required=True)
    sleep_review.add_argument("--include-conflicts", choices=["true", "false"])
    sleep_review.add_argument("--include-missingness", choices=["true", "false"])

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
    if args.command != "sleep-review":
        raise ValueError(f"Unsupported command: {args.command}")

    request_validation, _request_echo = validate_and_echo_request_metadata(
        request_id=args.request_id,
        requested_at=args.requested_at,
    )
    if not request_validation["is_valid"]:
        return {
            "ok": False,
            "artifact_path": args.artifact_path,
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

    context_response = agent_context_cli.run_command(
        argparse.Namespace(
            command="get",
            artifact_path=args.artifact_path,
            user_id=args.user_id,
            date=args.date,
        )
    )
    if not context_response.get("ok"):
        return {
            "ok": False,
            "artifact_path": context_response.get("artifact_path"),
            "retrieval": None,
            "validation": {
                **context_response["validation"],
                "request_echo": request_validation["request_echo"],
            },
            "error": context_response["error"],
        }

    context = context_response["context"]
    sleep_context = context["semantic_context"]["sleep"]
    evidence = {key: sleep_context[key] for key in SLEEP_EVIDENCE_KEYS}
    important_gaps = [gap["code"] for gap in sleep_context.get("important_gaps", [])]
    conflicts = sleep_context.get("conflicts", []) if args.include_conflicts != "false" else []

    return {
        "ok": True,
        "artifact_path": context_response["artifact_path"],
        "retrieval": {
            "operation": "retrieve.sleep_review",
            "scope": {
                "user_id": args.user_id,
                "date": args.date,
            },
            "coverage_status": _coverage_status(evidence=evidence, important_gaps=important_gaps),
            "generated_from": context.get("generated_from", {}),
            "evidence": evidence,
            "important_gaps": important_gaps if args.include_missingness != "false" else [],
            "conflicts": conflicts,
            "unsupported_claims": [],
        },
        "validation": {
            **context_response["validation"],
            "request_echo": request_validation["request_echo"],
        },
        "error": None,
    }


def _coverage_status(*, evidence: dict[str, Any], important_gaps: list[str]) -> str:
    statuses = [item.get("status") for item in evidence.values() if isinstance(item, dict)]
    if not statuses or all(status == "missing" for status in statuses):
        return "missing"
    if important_gaps or any(status == "missing" for status in statuses):
        return "partial"
    return "present"


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
        "retrieval": None,
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


if __name__ == "__main__":
    raise SystemExit(main())
