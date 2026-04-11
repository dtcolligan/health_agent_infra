from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from health_model.retrieval_request_metadata import validate_and_echo_request_metadata

from health_model.daily_snapshot import (
    DEFAULT_DB_PATH,
    DEFAULT_EXPORT_DIR,
    DEFAULT_GYM_LOG_PATH,
    DEFAULT_OUTPUT_DIR,
    generate_snapshot,
)

REQUIRED_ARTIFACT_TYPE = "day_nutrition_brief"
NUTRITION_EVIDENCE_KEYS = [
    "calories_kcal",
    "protein_g",
    "carbs_g",
    "fat_g",
    "fiber_g",
    "meal_count",
    "food_log_completeness",
    "top_meals_summary",
]


class CliParseError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliParseError(message)


def build_day_nutrition_brief(
    *,
    export_dir: Path,
    gym_log_path: Path,
    db_path: Path,
    date: str,
    user_id: int = 1,
) -> dict[str, Any]:
    snapshot = generate_snapshot(
        export_dir=export_dir,
        gym_log_path=gym_log_path,
        db_path=db_path,
        target_date=date,
        user_id=user_id,
    )
    nutrition = snapshot.nutrition_daily or {}
    supported_metrics = {
        "calories_kcal": snapshot.calories_kcal,
        "protein_g": snapshot.protein_g,
        "carbs_g": snapshot.carbs_g,
        "fat_g": snapshot.fat_g,
        "fiber_g": nutrition.get("fiber_g"),
        "meal_count": nutrition.get("meal_count"),
        "food_log_completeness": nutrition.get("food_log_completeness"),
        "top_meals_summary": nutrition.get("top_meals_summary"),
    }
    has_supported_nutrition = any(
        supported_metrics[key] is not None
        for key in ["calories_kcal", "protein_g", "carbs_g", "fat_g", "fiber_g", "meal_count", "top_meals_summary"]
    )
    coverage_status = "nutrition_available" if has_supported_nutrition else "nutrition_unavailable"
    coverage_note = (
        "Day-scoped nutrition totals are available from accepted daily snapshot fields only."
        if has_supported_nutrition
        else "No accepted nutrition totals are available for this user/date on current surfaces. This brief does not guess or backfill missing totals."
    )

    return {
        "artifact_type": REQUIRED_ARTIFACT_TYPE,
        "date": snapshot.date,
        "user_id": user_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "coverage_status": coverage_status,
        "coverage_note": coverage_note,
        "nutrition": {
            **supported_metrics,
            "source": nutrition.get("source"),
        },
        "unsupported_notes": [
            "Personalized bedtime guidance is unsupported in this slice.",
            "Micronutrient-gap detection is unsupported in this slice.",
        ],
        "truthfulness_notes": [
            "This is a read-only day-scoped brief sourced from accepted daily snapshot nutrition fields.",
            "Missing nutrition data stays explicit rather than being converted into zeros or advice.",
        ],
    }


def write_day_nutrition_brief(*, brief: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    dated_path = output_dir / f"day_nutrition_brief_{brief['date']}.json"
    latest_path = output_dir / "day_nutrition_brief_latest.json"
    serialized = json.dumps(brief, indent=2, sort_keys=True) + "\n"
    dated_path.write_text(serialized)
    latest_path.write_text(serialized)
    return {"dated_path": str(dated_path), "latest_path": str(latest_path)}


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="Build or retrieve a read-only day-scoped nutrition brief.")
    subparsers = parser.add_subparsers(dest="command")

    build_parser = subparsers.add_parser("build")
    _add_build_args(build_parser)

    retrieve_parser = subparsers.add_parser("retrieve-day-nutrition-brief")
    retrieve_parser.add_argument("--artifact-path", required=True)
    retrieve_parser.add_argument("--user-id", required=True)
    retrieve_parser.add_argument("--date", required=True)
    retrieve_parser.add_argument("--request-id", required=True)
    retrieve_parser.add_argument("--requested-at", required=True)
    retrieve_parser.add_argument("--include-conflicts", choices=["true", "false"])
    retrieve_parser.add_argument("--include-missingness", choices=["true", "false"])

    return parser


def _add_build_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--date", required=True)
    parser.add_argument("--user-id", type=int, default=1)
    parser.add_argument("--export-dir", default=str(DEFAULT_EXPORT_DIR))
    parser.add_argument("--gym-log-path", default=str(DEFAULT_GYM_LOG_PATH))
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argv = argv or sys.argv[1:]
    parser = build_parser()
    if argv and not argv[0].startswith("-"):
        return parser.parse_args(argv)
    legacy_build_parser = JsonArgumentParser(description="Build a read-only day-scoped nutrition brief from accepted Health Lab inputs.")
    _add_build_args(legacy_build_parser)
    args = legacy_build_parser.parse_args(argv)
    args.command = "build"
    return args


def run_command(args: argparse.Namespace) -> dict[str, Any] | dict[str, str]:
    if args.command == "build":
        brief = build_day_nutrition_brief(
            export_dir=Path(args.export_dir),
            gym_log_path=Path(args.gym_log_path),
            db_path=Path(args.db_path),
            date=args.date,
            user_id=args.user_id,
        )
        return write_day_nutrition_brief(brief=brief, output_dir=Path(args.output_dir))
    if args.command != "retrieve-day-nutrition-brief":
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

    path = Path(args.artifact_path)
    if not path.exists():
        return _validation_error(
            artifact_path=str(path),
            code="artifact_not_found",
            message="Artifact file does not exist.",
            semantic_issues=[_issue(code="artifact_not_found", message="Artifact file does not exist.", path="artifact_path")],
            details={"artifact_path": str(path), "user_id": args.user_id, "date": args.date},
            request_echo=request_validation["request_echo"],
        )

    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return _validation_error(
            artifact_path=str(path),
            code="invalid_artifact_json",
            message="Artifact file is not valid JSON.",
            semantic_issues=[_issue(code="invalid_artifact_json", message=str(exc), path="artifact_path")],
            details={"artifact_path": str(path), "user_id": args.user_id, "date": args.date},
            request_echo=request_validation["request_echo"],
        )

    semantic_issues = _artifact_semantic_issues(raw=raw, user_id=args.user_id, date=args.date)
    if semantic_issues:
        return _validation_error(
            artifact_path=str(path),
            code=semantic_issues[0]["code"],
            message="Artifact failed scope or type validation.",
            semantic_issues=semantic_issues,
            details={"artifact_path": str(path), "user_id": args.user_id, "date": args.date},
            request_echo=request_validation["request_echo"],
        )

    evidence = {key: raw.get("nutrition", {}).get(key) for key in NUTRITION_EVIDENCE_KEYS}
    unsupported_claims = list(raw.get("unsupported_notes", []))
    important_gaps = [key for key, value in evidence.items() if value is None]
    return {
        "ok": True,
        "artifact_path": str(path),
        "retrieval": {
            "operation": "retrieve.day_nutrition_brief",
            "scope": {"user_id": args.user_id, "date": args.date},
            "coverage_status": _coverage_status(raw=raw, important_gaps=important_gaps),
            "generated_from": {"nutrition_source": raw.get("nutrition", {}).get("source")},
            "evidence": evidence,
            "important_gaps": important_gaps if args.include_missingness != "false" else [],
            "conflicts": [],
            "unsupported_claims": unsupported_claims,
        },
        "validation": {
            "is_valid": True,
            "schema_issues": [],
            "semantic_issues": [],
            "request_echo": request_validation["request_echo"],
        },
        "error": None,
    }


def _artifact_semantic_issues(*, raw: Any, user_id: str, date: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(raw, dict):
        return [_issue(code="artifact_not_object", message="Artifact JSON must be an object.", path="$")]
    if raw.get("artifact_type") != REQUIRED_ARTIFACT_TYPE:
        issues.append(_issue(code="artifact_type_mismatch", message=f"Expected artifact_type={REQUIRED_ARTIFACT_TYPE}.", path="artifact_type"))
    if str(raw.get("user_id")) != str(user_id):
        issues.append(_issue(code="artifact_user_mismatch", message="Artifact user_id does not match request.", path="user_id"))
    if raw.get("date") != date:
        issues.append(_issue(code="artifact_date_mismatch", message="Artifact date does not match request.", path="date"))
    return issues


def _coverage_status(*, raw: dict[str, Any], important_gaps: list[str]) -> str:
    if raw.get("coverage_status") == "nutrition_unavailable":
        return "missing"
    if important_gaps:
        return "partial"
    return "present"


def _validation_error(
    *,
    artifact_path: str | None,
    code: str,
    message: str,
    semantic_issues: list[dict[str, str]],
    details: dict[str, Any],
    request_echo: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ok": False,
        "artifact_path": artifact_path,
        "retrieval": None,
        "validation": {
            "is_valid": False,
            "schema_issues": [],
            "semantic_issues": semantic_issues,
            "request_echo": request_echo,
        },
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


def _issue(*, code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
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

    if args.command == "build":
        print(response["dated_path"])
        print(response["latest_path"])
        return 0

    print(json.dumps(response, indent=2, sort_keys=True))
    return 0 if response.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
