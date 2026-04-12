from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from health_model.agent_interface import append_fragment_and_regenerate_daily_context
from health_model.voice_note_intake import canonicalize_voice_note_payload


class CliParseError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliParseError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        description="Submit one bounded transcribed daily voice note and atomically regenerate Health Lab daily context artifacts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    submit_parser = subparsers.add_parser("submit")
    submit_parser.add_argument("--bundle-path", required=True)
    submit_parser.add_argument("--output-dir", required=True)
    submit_parser.add_argument("--user-id", required=True)
    submit_parser.add_argument("--date", required=True)

    payload_group = submit_parser.add_mutually_exclusive_group(required=True)
    payload_group.add_argument("--payload-json")
    payload_group.add_argument("--payload-path")

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
    if args.command != "submit":
        raise ValueError(f"Unsupported command: {args.command}")

    payload_result = _load_payload(args)
    if not payload_result["ok"]:
        return payload_result

    payload = payload_result["payload"]
    try:
        fragment = canonicalize_voice_note_payload(payload)
    except (KeyError, TypeError, ValueError) as exc:
        return _validation_error(
            args=args,
            code="invalid_voice_note_payload",
            message="Voice-note payload failed canonicalization.",
            semantic_issues=[
                _issue(
                    code="invalid_voice_note_payload",
                    message=str(exc),
                    path="$",
                )
            ],
            details={"payload_source": payload_result["payload_source"]},
        )

    result = append_fragment_and_regenerate_daily_context(
        bundle_path=args.bundle_path,
        output_dir=args.output_dir,
        fragment=fragment,
        user_id=args.user_id,
        date=args.date,
    )
    if not result["ok"]:
        result["accepted_provenance"] = _accepted_provenance_from_fragment(fragment)
    return result


def _load_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload_source = "payload_json"
    raw_payload = args.payload_json

    if args.payload_path is not None:
        payload_source = "payload_path"
        payload_path = Path(args.payload_path)
        if not payload_path.exists():
            return _validation_error(
                args=args,
                code="payload_not_found",
                message="Voice-note payload file does not exist.",
                semantic_issues=[_issue(code="payload_not_found", message="Voice-note payload file does not exist.", path="payload_path")],
                details={"payload_path": str(payload_path)},
            )
        raw_payload = payload_path.read_text()

    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        return _validation_error(
            args=args,
            code="invalid_payload_json",
            message="Voice-note payload is not valid JSON.",
            semantic_issues=[_issue(code="invalid_payload_json", message=str(exc), path=payload_source)],
            details={"payload_source": payload_source},
        )

    if not isinstance(payload, dict):
        return _validation_error(
            args=args,
            code="invalid_payload_shape",
            message="Voice-note payload JSON must be an object.",
            semantic_issues=[_issue(code="invalid_payload_shape", message="Voice-note payload JSON must be an object.", path="$")],
            details={"payload_source": payload_source},
        )

    return {"ok": True, "payload": payload, "payload_source": payload_source}


def _accepted_provenance_from_fragment(fragment: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    return {
        "source_artifact_ids": [artifact["artifact_id"] for artifact in fragment.get("source_artifacts", [])],
        "input_event_ids": [event["event_id"] for event in fragment.get("input_events", [])],
        "subjective_entry_ids": [entry["entry_id"] for entry in fragment.get("subjective_daily_entries", [])],
        "manual_log_entry_ids": [entry["entry_id"] for entry in fragment.get("manual_log_entries", [])],
    }


def _validation_error(
    *,
    args: argparse.Namespace,
    code: str,
    message: str,
    semantic_issues: list[dict[str, str]],
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ok": False,
        "bundle_path": args.bundle_path,
        "dated_artifact_path": None,
        "latest_artifact_path": None,
        "accepted_provenance": {},
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


def _issue(*, code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


if __name__ == "__main__":
    raise SystemExit(main())
