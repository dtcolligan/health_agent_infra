from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
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
RECOMMENDATION_JUDGMENT_ARTIFACT_TYPE = "recommendation_judgment"
RECOMMENDATION_ARTIFACT_TYPE = "agent_recommendation"
RECOMMENDATION_EVIDENCE_KEYS = [
    "recommendation_id",
    "summary",
    "rationale",
    "evidence_refs",
    "confidence_score",
    "context_artifact_path",
    "context_artifact_id",
]
RECOMMENDATION_JUDGMENT_EVIDENCE_KEYS = [
    "judgment_id",
    "judgment_label",
    "action_taken",
    "why",
    "recommendation_artifact_path",
    "recommendation_artifact_id",
    "recommendation_evidence_refs",
    "written_at",
    "request_id",
    "requested_at",
]
RECOMMENDATION_FEEDBACK_RECOMMENDATION_KEYS = RECOMMENDATION_EVIDENCE_KEYS
RECOMMENDATION_FEEDBACK_JUDGMENT_KEYS = RECOMMENDATION_JUDGMENT_EVIDENCE_KEYS


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

    recommendation_judgment = subparsers.add_parser("recommendation-judgment")
    recommendation_judgment.add_argument("--artifact-path", required=True)
    recommendation_judgment.add_argument("--user-id", required=True)
    recommendation_judgment.add_argument("--date", required=True)
    recommendation_judgment.add_argument("--request-id", required=True)
    recommendation_judgment.add_argument("--requested-at", required=True)
    recommendation_judgment.add_argument("--include-conflicts", choices=["true", "false"])
    recommendation_judgment.add_argument("--include-missingness", choices=["true", "false"])

    recommendation = subparsers.add_parser("recommendation")
    recommendation.add_argument("--artifact-path", required=True)
    recommendation.add_argument("--user-id", required=True)
    recommendation.add_argument("--date", required=True)
    recommendation.add_argument("--request-id", required=True)
    recommendation.add_argument("--requested-at", required=True)
    recommendation.add_argument("--include-conflicts", choices=["true", "false"])
    recommendation.add_argument("--include-missingness", choices=["true", "false"])

    recommendation_feedback = subparsers.add_parser("recommendation-feedback")
    recommendation_feedback.add_argument("--recommendation-artifact-path", required=True)
    recommendation_feedback.add_argument("--judgment-artifact-path", required=True)
    recommendation_feedback.add_argument("--user-id", required=True)
    recommendation_feedback.add_argument("--date", required=True)
    recommendation_feedback.add_argument("--request-id", required=True)
    recommendation_feedback.add_argument("--requested-at", required=True)
    recommendation_feedback.add_argument("--include-conflicts", choices=["true", "false"])
    recommendation_feedback.add_argument("--include-missingness", choices=["true", "false"])

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
    if args.command == "sleep-review":
        return _run_sleep_review(args)
    if args.command == "recommendation-judgment":
        return _run_recommendation_judgment(args)
    if args.command == "recommendation":
        return _run_recommendation(args)
    if args.command == "recommendation-feedback":
        return _run_recommendation_feedback(args)
    raise ValueError(f"Unsupported command: {args.command}")


def _run_sleep_review(args: argparse.Namespace) -> dict[str, Any]:
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


def _run_recommendation_judgment(args: argparse.Namespace) -> dict[str, Any]:
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

    artifact_response = _read_recommendation_judgment_artifact(
        path=Path(args.artifact_path),
        user_id=args.user_id,
        date=args.date,
    )
    if not artifact_response["ok"]:
        return {
            "ok": False,
            "artifact_path": artifact_response.get("artifact_path"),
            "retrieval": None,
            "validation": {
                **artifact_response["validation"],
                "request_echo": request_validation["request_echo"],
            },
            "error": artifact_response["error"],
        }

    artifact = artifact_response["artifact"]
    important_gaps: list[str] = []
    conflicts: list[dict[str, Any]] = [] if args.include_conflicts != "false" else []
    evidence = {key: artifact[key] for key in RECOMMENDATION_JUDGMENT_EVIDENCE_KEYS if key in artifact}

    return {
        "ok": True,
        "artifact_path": artifact_response["artifact_path"],
        "retrieval": {
            "operation": "retrieve.recommendation_judgment",
            "scope": {
                "user_id": args.user_id,
                "date": args.date,
            },
            "coverage_status": "present",
            "generated_from": {
                "artifact_path": artifact_response["artifact_path"],
                "recommendation_artifact_path": artifact.get("recommendation_artifact_path"),
                "request_id": artifact.get("request_id"),
            },
            "evidence": evidence,
            "important_gaps": important_gaps if args.include_missingness != "false" else [],
            "conflicts": conflicts,
            "unsupported_claims": [],
        },
        "validation": {
            **artifact_response["validation"],
            "request_echo": request_validation["request_echo"],
        },
        "error": None,
    }


def _run_recommendation(args: argparse.Namespace) -> dict[str, Any]:
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

    artifact_response = _read_recommendation_artifact(
        path=Path(args.artifact_path),
        user_id=args.user_id,
        date=args.date,
    )
    if not artifact_response["ok"]:
        return {
            "ok": False,
            "artifact_path": artifact_response.get("artifact_path"),
            "retrieval": None,
            "validation": {
                **artifact_response["validation"],
                "request_echo": request_validation["request_echo"],
            },
            "error": artifact_response["error"],
        }

    artifact = artifact_response["artifact"]
    important_gaps: list[str] = []
    conflicts: list[dict[str, Any]] = [] if args.include_conflicts != "false" else []
    evidence = {key: artifact[key] for key in RECOMMENDATION_EVIDENCE_KEYS if key in artifact}

    return {
        "ok": True,
        "artifact_path": artifact_response["artifact_path"],
        "retrieval": {
            "operation": "retrieve.recommendation",
            "scope": {
                "user_id": args.user_id,
                "date": args.date,
            },
            "coverage_status": "present",
            "generated_from": {
                "artifact_path": artifact_response["artifact_path"],
                "context_artifact_path": artifact.get("context_artifact_path"),
                "context_artifact_id": artifact.get("context_artifact_id"),
            },
            "evidence": evidence,
            "important_gaps": important_gaps if args.include_missingness != "false" else [],
            "conflicts": conflicts,
            "unsupported_claims": [],
        },
        "validation": {
            **artifact_response["validation"],
            "request_echo": request_validation["request_echo"],
        },
        "error": None,
    }


def _read_recommendation_judgment_artifact(*, path: Path, user_id: str, date: str) -> dict[str, Any]:
    if not path.exists():
        return _retrieval_validation_error(
            artifact_path=str(path),
            code="artifact_not_found",
            message="Artifact file does not exist.",
            semantic_issues=[_issue(code="artifact_not_found", message="Artifact file does not exist.", path="artifact_path")],
            details={"artifact_path": str(path)},
        )

    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return _retrieval_validation_error(
            artifact_path=str(path),
            code="invalid_artifact_json",
            message="Artifact file is not valid JSON.",
            semantic_issues=[_issue(code="invalid_artifact_json", message=str(exc), path="artifact_path")],
            details={"artifact_path": str(path)},
        )

    semantic_issues = _recommendation_judgment_semantic_issues(raw=raw, user_id=user_id, date=date)
    if semantic_issues:
        return _retrieval_validation_error(
            artifact_path=str(path),
            code=semantic_issues[0]["code"],
            message="Artifact failed scope or type validation.",
            semantic_issues=semantic_issues,
            details={"artifact_path": str(path), "user_id": user_id, "date": date},
        )

    return {
        "ok": True,
        "artifact_path": str(path),
        "artifact": raw,
        "validation": {"is_valid": True, "schema_issues": [], "semantic_issues": []},
        "error": None,
    }


def _recommendation_judgment_semantic_issues(*, raw: Any, user_id: str, date: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(raw, dict):
        return [_issue(code="artifact_not_object", message="Artifact JSON must be an object.", path="$")]
    if raw.get("artifact_type") != RECOMMENDATION_JUDGMENT_ARTIFACT_TYPE:
        issues.append(
            _issue(
                code="artifact_type_mismatch",
                message=f"Expected artifact_type={RECOMMENDATION_JUDGMENT_ARTIFACT_TYPE}.",
                path="artifact_type",
            )
        )
    if raw.get("user_id") != user_id:
        issues.append(_issue(code="artifact_user_mismatch", message="Artifact user_id does not match request.", path="user_id"))
    if raw.get("date") != date:
        issues.append(_issue(code="artifact_date_mismatch", message="Artifact date does not match request.", path="date"))
    return issues


def _run_recommendation_feedback(args: argparse.Namespace) -> dict[str, Any]:
    request_validation, _request_echo = validate_and_echo_request_metadata(
        request_id=args.request_id,
        requested_at=args.requested_at,
    )
    if not request_validation["is_valid"]:
        return {
            "ok": False,
            "artifact_path": args.judgment_artifact_path,
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

    recommendation_response = _read_recommendation_artifact(
        path=Path(args.recommendation_artifact_path),
        user_id=args.user_id,
        date=args.date,
    )
    if not recommendation_response["ok"]:
        return {
            "ok": False,
            "artifact_path": recommendation_response.get("artifact_path"),
            "retrieval": None,
            "validation": {
                **recommendation_response["validation"],
                "request_echo": request_validation["request_echo"],
            },
            "error": recommendation_response["error"],
        }

    judgment_response = _read_recommendation_judgment_artifact(
        path=Path(args.judgment_artifact_path),
        user_id=args.user_id,
        date=args.date,
    )
    if not judgment_response["ok"]:
        return {
            "ok": False,
            "artifact_path": judgment_response.get("artifact_path"),
            "retrieval": None,
            "validation": {
                **judgment_response["validation"],
                "request_echo": request_validation["request_echo"],
            },
            "error": judgment_response["error"],
        }

    recommendation = recommendation_response["artifact"]
    judgment = judgment_response["artifact"]
    linkage_issues = _recommendation_feedback_linkage_issues(
        recommendation=recommendation,
        judgment=judgment,
        supplied_recommendation_artifact_path=args.recommendation_artifact_path,
    )
    if linkage_issues:
        return {
            "ok": False,
            "artifact_path": judgment_response["artifact_path"],
            "retrieval": None,
            "validation": {
                "is_valid": False,
                "schema_issues": [],
                "semantic_issues": linkage_issues,
                "request_echo": request_validation["request_echo"],
            },
            "error": {
                "code": linkage_issues[0]["code"],
                "message": "Recommendation feedback linkage validation failed.",
                "retryable": False,
                "details": {
                    "recommendation_artifact_path": recommendation_response["artifact_path"],
                    "judgment_artifact_path": judgment_response["artifact_path"],
                    "recommendation_id": recommendation.get("recommendation_id"),
                    "judgment_recommendation_artifact_id": judgment.get("recommendation_artifact_id"),
                    "judgment_recommendation_artifact_path": judgment.get("recommendation_artifact_path"),
                },
            },
        }

    conflicts: list[dict[str, Any]] = [] if args.include_conflicts != "false" else []
    important_gaps: list[str] = [] if args.include_missingness != "false" else []
    return {
        "ok": True,
        "artifact_path": judgment_response["artifact_path"],
        "retrieval": {
            "operation": "retrieve.recommendation_feedback",
            "scope": {
                "user_id": args.user_id,
                "date": args.date,
            },
            "coverage_status": "present",
            "generated_from": {
                "recommendation_artifact_path": recommendation_response["artifact_path"],
                "judgment_artifact_path": judgment_response["artifact_path"],
            },
            "evidence": {
                "recommendation": {
                    key: recommendation[key] for key in RECOMMENDATION_FEEDBACK_RECOMMENDATION_KEYS if key in recommendation
                },
                "judgment": {key: judgment[key] for key in RECOMMENDATION_FEEDBACK_JUDGMENT_KEYS if key in judgment},
            },
            "linkage": {
                "recommendation_artifact_id": recommendation.get("recommendation_id"),
                "judgment_recommendation_artifact_id": judgment.get("recommendation_artifact_id"),
                "judgment_recommendation_artifact_path": judgment.get("recommendation_artifact_path"),
                "supplied_recommendation_artifact_path": recommendation_response["artifact_path"],
            },
            "important_gaps": important_gaps,
            "conflicts": conflicts,
            "unsupported_claims": [],
        },
        "validation": {
            "is_valid": True,
            "schema_issues": [],
            "semantic_issues": [],
            "request_echo": request_validation["request_echo"],
        },
        "error": None,
    }


def _read_recommendation_artifact(*, path: Path, user_id: str, date: str) -> dict[str, Any]:
    if not path.exists():
        return _retrieval_validation_error(
            artifact_path=str(path),
            code="artifact_not_found",
            message="Artifact file does not exist.",
            semantic_issues=[_issue(code="artifact_not_found", message="Artifact file does not exist.", path="artifact_path")],
            details={"artifact_path": str(path)},
        )

    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return _retrieval_validation_error(
            artifact_path=str(path),
            code="invalid_artifact_json",
            message="Artifact file is not valid JSON.",
            semantic_issues=[_issue(code="invalid_artifact_json", message=str(exc), path="artifact_path")],
            details={"artifact_path": str(path)},
        )

    semantic_issues = _recommendation_semantic_issues(raw=raw, user_id=user_id, date=date)
    if semantic_issues:
        return _retrieval_validation_error(
            artifact_path=str(path),
            code=semantic_issues[0]["code"],
            message="Artifact failed scope or type validation.",
            semantic_issues=semantic_issues,
            details={"artifact_path": str(path), "user_id": user_id, "date": date},
        )

    return {
        "ok": True,
        "artifact_path": str(path),
        "artifact": raw,
        "validation": {"is_valid": True, "schema_issues": [], "semantic_issues": []},
        "error": None,
    }


def _recommendation_semantic_issues(*, raw: Any, user_id: str, date: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(raw, dict):
        return [_issue(code="artifact_not_object", message="Artifact JSON must be an object.", path="$")]
    if raw.get("artifact_type") != RECOMMENDATION_ARTIFACT_TYPE:
        issues.append(
            _issue(
                code="artifact_type_mismatch",
                message=f"Expected artifact_type={RECOMMENDATION_ARTIFACT_TYPE}.",
                path="artifact_type",
            )
        )
    if raw.get("user_id") != user_id:
        issues.append(_issue(code="artifact_user_mismatch", message="Artifact user_id does not match request.", path="user_id"))
    if raw.get("date") != date:
        issues.append(_issue(code="artifact_date_mismatch", message="Artifact date does not match request.", path="date"))
    return issues


def _recommendation_feedback_linkage_issues(
    *,
    recommendation: dict[str, Any],
    judgment: dict[str, Any],
    supplied_recommendation_artifact_path: str,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if judgment.get("recommendation_artifact_id") != recommendation.get("recommendation_id"):
        issues.append(
            _issue(
                code="recommendation_linkage_mismatch",
                message="Judgment recommendation_artifact_id does not match recommendation recommendation_id.",
                path="recommendation_artifact_id",
            )
        )
    supplied_path = _resolve_artifact_path(supplied_recommendation_artifact_path)
    judgment_path = _resolve_artifact_path(judgment.get("recommendation_artifact_path")) if judgment.get("recommendation_artifact_path") else None
    if judgment_path != supplied_path:
        issues.append(
            _issue(
                code="recommendation_artifact_path_mismatch",
                message="Judgment recommendation_artifact_path does not match the supplied recommendation artifact path.",
                path="recommendation_artifact_path",
            )
        )
    return issues


def _resolve_artifact_path(path_value: str | None) -> str | None:
    if not path_value:
        return None
    return str(Path(path_value).resolve())


def _retrieval_validation_error(
    *,
    artifact_path: str,
    code: str,
    message: str,
    semantic_issues: list[dict[str, str]],
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ok": False,
        "artifact_path": artifact_path,
        "artifact": None,
        "validation": {"is_valid": False, "schema_issues": [], "semantic_issues": semantic_issues},
        "error": {
            "code": code,
            "message": message,
            "retryable": False,
            "details": details,
        },
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


def _issue(*, code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


if __name__ == "__main__":
    raise SystemExit(main())
