from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class CliParseError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliParseError(message)


REQUIRED_ARTIFACT_TYPE = "agent_readable_daily_context"


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
    path = Path(args.artifact_path)
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

    semantic_issues = _artifact_semantic_issues(raw=raw, user_id=args.user_id, date=getattr(args, "date", None))
    if semantic_issues:
        error_code = semantic_issues[0]["code"]
        return _validation_error(
            artifact_path=str(path),
            code=error_code,
            message="Artifact failed scope or type validation.",
            semantic_issues=semantic_issues,
            details={"artifact_path": str(path), "user_id": args.user_id, "date": getattr(args, "date", None)},
        )

    return {
        "ok": True,
        "artifact_path": str(path),
        "context": raw,
        "validation": {"is_valid": True, "schema_issues": [], "semantic_issues": []},
        "error": None,
    }


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
