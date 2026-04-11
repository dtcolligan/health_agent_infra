from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from health_model.retrieval_request_metadata import validate_and_echo_request_metadata


ARTIFACT_TYPE = "recommendation_judgment"
RECOMMENDATION_ARTIFACT_TYPE = "agent_recommendation"
ALLOWED_JUDGMENT_LABELS = ["useful", "obvious", "wrong", "ignored"]
REQUIRED_PAYLOAD_FIELDS = {
    "user_id",
    "date",
    "recommendation_artifact_path",
    "recommendation_artifact_id",
    "judgment_id",
    "judgment_label",
    "action_taken",
    "why",
    "written_at",
    "request_id",
    "requested_at",
}
OPTIONAL_PAYLOAD_FIELDS = {"caveat", "time_cost_note", "friction_points", "gym_note"}


class CliParseError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliParseError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="Write one validated same-day recommendation judgment artifact.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    writeback_parser = subparsers.add_parser("recommendation-judgment")
    writeback_parser.add_argument("--output-dir", required=True)
    payload_group = writeback_parser.add_mutually_exclusive_group(required=True)
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
    if args.command != "recommendation-judgment":
        raise ValueError(f"Unsupported command: {args.command}")

    payload_result = _load_payload(args)
    if not payload_result["ok"]:
        return payload_result

    payload = payload_result["payload"]
    validation_issues = _payload_semantic_issues(payload)
    if validation_issues:
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code=validation_issues[0]["code"],
            message="Recommendation judgment payload failed validation.",
            semantic_issues=validation_issues,
            details={"payload_source": payload_result["payload_source"]},
        )

    request_validation, request_echo = validate_and_echo_request_metadata(
        request_id=payload["request_id"],
        requested_at=payload["requested_at"],
    )
    if not request_validation["is_valid"]:
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code=request_validation["semantic_issues"][0]["code"],
            message="Request metadata failed validation.",
            semantic_issues=request_validation["semantic_issues"],
            details={"payload_source": payload_result["payload_source"], "request_echo": request_echo},
            request_echo=request_echo,
        )

    recommendation_path = Path(str(payload["recommendation_artifact_path"]))
    recommendation_result = _load_recommendation_artifact(recommendation_path=recommendation_path)
    if not recommendation_result["ok"]:
        return {
            **recommendation_result,
            "validation": {
                **recommendation_result["validation"],
                "request_echo": request_echo,
            },
        }

    recommendation = recommendation_result["recommendation"]
    recommendation_issues = _recommendation_semantic_issues(
        recommendation=recommendation,
        payload=payload,
        recommendation_path=recommendation_path,
    )
    if recommendation_issues:
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code=recommendation_issues[0]["code"],
            message="Referenced recommendation artifact failed validation.",
            semantic_issues=recommendation_issues,
            details={"recommendation_artifact_path": str(recommendation_path)},
            request_echo=request_echo,
        )

    judgment = _build_judgment(payload=payload, recommendation=recommendation, recommendation_path=recommendation_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dated_path = output_dir / f"{ARTIFACT_TYPE}_{payload['date']}.json"
    latest_path = output_dir / f"{ARTIFACT_TYPE}_latest.json"
    serialized = json.dumps(judgment, indent=2, sort_keys=True) + "\n"
    _write_artifact_pair_atomically(serialized=serialized, dated_path=dated_path, latest_path=latest_path)

    return {
        "ok": True,
        "artifact_path": str(dated_path),
        "latest_artifact_path": str(latest_path),
        "writeback": judgment,
        "validation": {"is_valid": True, "schema_issues": [], "semantic_issues": [], "request_echo": request_echo},
        "error": None,
    }


def _load_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload_source = "payload_json"
    raw_payload = args.payload_json

    if args.payload_path is not None:
        payload_source = "payload_path"
        payload_path = Path(args.payload_path)
        if not payload_path.exists():
            return _validation_error(
                artifact_path=None,
                latest_artifact_path=None,
                code="payload_not_found",
                message="Recommendation judgment payload file does not exist.",
                semantic_issues=[_issue(code="payload_not_found", message="Recommendation judgment payload file does not exist.", path="payload_path")],
                details={"payload_path": str(payload_path)},
            )
        raw_payload = payload_path.read_text()

    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="invalid_payload_json",
            message="Recommendation judgment payload is not valid JSON.",
            semantic_issues=[_issue(code="invalid_payload_json", message=str(exc), path=payload_source)],
            details={"payload_source": payload_source},
        )

    if not isinstance(payload, dict):
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="invalid_payload_shape",
            message="Recommendation judgment payload JSON must be an object.",
            semantic_issues=[_issue(code="invalid_payload_shape", message="Recommendation judgment payload JSON must be an object.", path="$")],
            details={"payload_source": payload_source},
        )

    return {"ok": True, "payload": payload, "payload_source": payload_source}


def _payload_semantic_issues(payload: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    allowed_fields = REQUIRED_PAYLOAD_FIELDS | OPTIONAL_PAYLOAD_FIELDS
    extra_fields = sorted(set(payload.keys()) - allowed_fields)
    for field in extra_fields:
        issues.append(_issue(code="unexpected_payload_field", message="Unexpected payload field.", path=field))

    missing_fields = sorted(REQUIRED_PAYLOAD_FIELDS - set(payload.keys()))
    for field in missing_fields:
        issues.append(_issue(code="missing_required_field", message="Missing required field.", path=field))

    if issues:
        return issues

    for field in (
        "user_id",
        "date",
        "recommendation_artifact_path",
        "recommendation_artifact_id",
        "judgment_id",
        "action_taken",
        "why",
        "written_at",
        "request_id",
        "requested_at",
    ):
        if not isinstance(payload[field], str) or not payload[field].strip():
            issues.append(_issue(code="invalid_string_field", message="Field must be a non-empty string.", path=field))

    if payload.get("judgment_label") not in ALLOWED_JUDGMENT_LABELS:
        issues.append(_issue(code="invalid_judgment_label", message="judgment_label must be one of the accepted labels.", path="judgment_label"))

    if not _is_iso_datetime_with_timezone(payload["written_at"]):
        issues.append(_issue(code="invalid_written_at", message="written_at must be an ISO 8601 datetime string with timezone information.", path="written_at"))

    for optional_string_field in ("caveat", "time_cost_note", "gym_note"):
        if optional_string_field in payload and (not isinstance(payload[optional_string_field], str) or not payload[optional_string_field].strip()):
            issues.append(_issue(code="invalid_string_field", message="Field must be a non-empty string when provided.", path=optional_string_field))

    if "friction_points" in payload:
        friction_points = payload["friction_points"]
        if not isinstance(friction_points, list) or not friction_points:
            issues.append(_issue(code="invalid_friction_points", message="friction_points must be a non-empty array of strings when provided.", path="friction_points"))
        else:
            for index, value in enumerate(friction_points):
                if not isinstance(value, str) or not value.strip():
                    issues.append(_issue(code="invalid_friction_point", message="Each friction point must be a non-empty string.", path=f"friction_points[{index}]"))

    return issues


def _is_iso_datetime_with_timezone(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _load_recommendation_artifact(*, recommendation_path: Path) -> dict[str, Any]:
    if not recommendation_path.exists():
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="recommendation_artifact_not_found",
            message="Referenced recommendation artifact file does not exist.",
            semantic_issues=[
                _issue(code="recommendation_artifact_not_found", message="Referenced recommendation artifact file does not exist.", path="recommendation_artifact_path")
            ],
            details={"recommendation_artifact_path": str(recommendation_path)},
        )

    try:
        raw = json.loads(recommendation_path.read_text())
    except json.JSONDecodeError as exc:
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="invalid_recommendation_artifact_json",
            message="Referenced recommendation artifact is not valid JSON.",
            semantic_issues=[_issue(code="invalid_recommendation_artifact_json", message=str(exc), path="recommendation_artifact_path")],
            details={"recommendation_artifact_path": str(recommendation_path)},
        )

    if not isinstance(raw, dict):
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="invalid_recommendation_artifact_shape",
            message="Referenced recommendation artifact JSON must be an object.",
            semantic_issues=[_issue(code="invalid_recommendation_artifact_shape", message="Referenced recommendation artifact JSON must be an object.", path="$")],
            details={"recommendation_artifact_path": str(recommendation_path)},
        )

    return {"ok": True, "recommendation": raw}


def _recommendation_semantic_issues(*, recommendation: dict[str, Any], payload: dict[str, Any], recommendation_path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    if recommendation.get("artifact_type") != RECOMMENDATION_ARTIFACT_TYPE:
        issues.append(_issue(code="recommendation_artifact_type_mismatch", message=f"Expected artifact_type={RECOMMENDATION_ARTIFACT_TYPE}.", path="artifact_type"))
    if recommendation.get("recommendation_id") != payload["recommendation_artifact_id"]:
        issues.append(_issue(code="recommendation_artifact_id_mismatch", message="Referenced recommendation artifact id does not match payload.", path="recommendation_artifact_id"))
    if recommendation.get("user_id") != payload["user_id"]:
        issues.append(_issue(code="artifact_user_mismatch", message="Recommendation user_id does not match payload.", path="user_id"))
    if recommendation.get("date") != payload["date"]:
        issues.append(_issue(code="artifact_date_mismatch", message="Recommendation date does not match payload.", path="date"))
    if str(recommendation_path) != payload["recommendation_artifact_path"]:
        issues.append(_issue(code="recommendation_artifact_path_mismatch", message="Payload recommendation_artifact_path does not match the referenced file path.", path="recommendation_artifact_path"))

    return issues


def _build_judgment(*, payload: dict[str, Any], recommendation: dict[str, Any], recommendation_path: Path) -> dict[str, Any]:
    judgment = {
        "artifact_type": ARTIFACT_TYPE,
        "user_id": payload["user_id"],
        "date": payload["date"],
        "judgment_id": payload["judgment_id"],
        "judgment_label": payload["judgment_label"],
        "action_taken": payload["action_taken"],
        "why": payload["why"],
        "written_at": payload["written_at"],
        "request_id": payload["request_id"],
        "requested_at": payload["requested_at"],
        "recommendation_artifact_path": str(recommendation_path),
        "recommendation_artifact_id": payload["recommendation_artifact_id"],
        "recommendation_evidence_refs": list(recommendation.get("evidence_refs", [])),
    }
    for field in ("caveat", "time_cost_note", "friction_points", "gym_note"):
        if field in payload:
            judgment[field] = payload[field]
    return judgment


def _write_artifact_pair_atomically(*, serialized: str, dated_path: Path, latest_path: Path) -> None:
    original_states = {
        dated_path: _capture_file_state(dated_path),
        latest_path: _capture_file_state(latest_path),
    }
    temp_paths = {
        dated_path: _write_temp_artifact_file(target_path=dated_path, serialized=serialized),
        latest_path: _write_temp_artifact_file(target_path=latest_path, serialized=serialized),
    }

    try:
        temp_paths[dated_path].replace(dated_path)
        temp_paths[latest_path].replace(latest_path)
    except Exception:
        for target_path, state in original_states.items():
            _restore_artifact_file_state(target_path=target_path, state=state)
        raise
    finally:
        for temp_path in temp_paths.values():
            if temp_path.exists():
                temp_path.unlink()


def _capture_file_state(path: Path) -> dict[str, str | bool | None]:
    if not path.exists():
        return {"exists": False, "content": None}
    return {"exists": True, "content": path.read_text()}


def _write_temp_artifact_file(*, target_path: Path, serialized: str) -> Path:
    temp_path = target_path.with_name(f".{target_path.name}.{os.getpid()}.tmp")
    temp_path.write_text(serialized)
    return temp_path


def _restore_artifact_file_state(*, target_path: Path, state: dict[str, str | bool | None]) -> None:
    if state["exists"]:
        target_path.write_text(str(state["content"]))
        return
    if target_path.exists():
        target_path.unlink()


def _validation_error(
    *,
    artifact_path: str | None,
    latest_artifact_path: str | None,
    code: str,
    message: str,
    semantic_issues: list[dict[str, str]],
    details: dict[str, Any],
    request_echo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validation: dict[str, Any] = {"is_valid": False, "schema_issues": [], "semantic_issues": semantic_issues}
    if request_echo is not None:
        validation["request_echo"] = request_echo
    return {
        "ok": False,
        "artifact_path": artifact_path,
        "latest_artifact_path": latest_artifact_path,
        "writeback": None,
        "validation": validation,
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
        "artifact_path": None,
        "latest_artifact_path": None,
        "writeback": None,
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
