from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from health_model.shared_input_backbone import validate_shared_input_bundle


class CliParseError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliParseError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        description="Initialize one canonical empty shared-input bundle for a scoped external-agent flow."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--bundle-path", required=True)
    init_parser.add_argument("--user-id", required=True)
    init_parser.add_argument("--date", required=True)

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
    if args.command != "init":
        raise ValueError(f"Unsupported command: {args.command}")
    return _run_init(bundle_path=args.bundle_path, user_id=args.user_id, date=args.date)


def _run_init(*, bundle_path: str, user_id: str, date: str) -> dict[str, Any]:
    path = Path(bundle_path)
    if path.exists():
        return {
            "ok": False,
            "bundle_path": str(path),
            "bundle": None,
            "validation": {"is_valid": False, "schema_issues": [], "semantic_issues": []},
            "error": {
                "code": "bundle_path_exists",
                "message": "Target bundle file already exists.",
                "retryable": False,
                "details": {"bundle_path": str(path), "user_id": user_id, "date": date},
            },
        }

    bundle = _empty_bundle()
    validation = validate_shared_input_bundle(bundle)
    validation_payload = _validation_payload(validation)
    if not validation.is_valid:
        return {
            "ok": False,
            "bundle_path": str(path),
            "bundle": bundle,
            "validation": validation_payload,
            "error": {
                "code": "invalid_bundle",
                "message": "Canonical empty shared-input bundle failed validation.",
                "retryable": False,
                "details": {"bundle_path": str(path), "user_id": user_id, "date": date},
            },
        }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n")
    return {
        "ok": True,
        "bundle_path": str(path),
        "bundle": bundle,
        "validation": validation_payload,
        "error": None,
    }


def _empty_bundle() -> dict[str, list[dict[str, Any]]]:
    return {
        "source_artifacts": [],
        "input_events": [],
        "subjective_daily_entries": [],
        "manual_log_entries": [],
    }


def _validation_payload(validation: Any) -> dict[str, Any]:
    return {
        "is_valid": validation.is_valid,
        "schema_issues": [
            {"code": issue.code, "message": issue.message, "path": issue.path} for issue in validation.schema_issues
        ],
        "semantic_issues": [
            {"code": issue.code, "message": issue.message, "path": issue.path} for issue in validation.semantic_issues
        ],
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
        "bundle": None,
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
