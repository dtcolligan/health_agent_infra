from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from health_model import agent_retrieval_cli
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
RESOLUTION_TRANSITION_REQUIRED_PAYLOAD_FIELDS = {
    "user_id",
    "start_date",
    "end_date",
    "recommendation_artifact_path",
    "recommendation_artifact_id",
    "judgment_artifact_path",
    "judgment_artifact_id",
    "resolution_window_memory_path",
    "written_at",
    "request_id",
    "requested_at",
}
RESOLUTION_TRANSITION_OPTIONAL_PAYLOAD_FIELDS = {"feedback_window_memory_path"}


class CliParseError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliParseError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="Write bounded Health Lab recommendation writeback artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    writeback_parser = subparsers.add_parser("recommendation-judgment")
    writeback_parser.add_argument("--output-dir", required=True)
    payload_group = writeback_parser.add_mutually_exclusive_group(required=True)
    payload_group.add_argument("--payload-json")
    payload_group.add_argument("--payload-path")

    transition_parser = subparsers.add_parser("recommendation-resolution-transition")
    transition_parser.add_argument("--output-dir", required=True)
    transition_payload_group = transition_parser.add_mutually_exclusive_group(required=True)
    transition_payload_group.add_argument("--payload-json")
    transition_payload_group.add_argument("--payload-path")

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
    if args.command == "recommendation-judgment":
        return _run_recommendation_judgment(args)
    if args.command == "recommendation-resolution-transition":
        return _run_recommendation_resolution_transition(args)
    raise ValueError(f"Unsupported command: {args.command}")


def _run_recommendation_judgment(args: argparse.Namespace) -> dict[str, Any]:
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


def _run_recommendation_resolution_transition(args: argparse.Namespace) -> dict[str, Any]:
    payload_result = _load_payload(args)
    if not payload_result["ok"]:
        return payload_result

    payload = payload_result["payload"]
    validation_issues = _resolution_transition_payload_issues(payload)
    if validation_issues:
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code=validation_issues[0]["code"],
            message="Recommendation resolution transition payload failed validation.",
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
    recommendation_response = _read_artifact_json(recommendation_path, missing_code="recommendation_artifact_not_found", invalid_code="invalid_recommendation_artifact_json")
    if not recommendation_response["ok"]:
        return _with_request_echo(recommendation_response, request_echo)
    recommendation = recommendation_response["artifact"]
    recommendation_date = recommendation.get("date")
    recommendation_issues = agent_retrieval_cli._recommendation_semantic_issues(raw=recommendation, user_id=payload["user_id"], date=recommendation_date)
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
    if recommendation.get("recommendation_id") != payload["recommendation_artifact_id"]:
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="recommendation_artifact_id_mismatch",
            message="Referenced recommendation artifact id did not match payload.",
            semantic_issues=[_issue(code="recommendation_artifact_id_mismatch", message="Referenced recommendation artifact id did not match payload.", path="recommendation_artifact_id")],
            details={"recommendation_artifact_path": str(recommendation_path)},
            request_echo=request_echo,
        )

    judgment_path = Path(str(payload["judgment_artifact_path"]))
    judgment_response = agent_retrieval_cli._read_recommendation_judgment_artifact(
        path=judgment_path,
        user_id=payload["user_id"],
        date=str(recommendation_date),
    )
    if not judgment_response["ok"]:
        return _with_request_echo(judgment_response, request_echo)
    judgment = judgment_response["artifact"]

    linkage_issues = agent_retrieval_cli._recommendation_feedback_linkage_issues(
        recommendation=recommendation,
        judgment=judgment,
        supplied_recommendation_artifact_path=str(recommendation_path),
    )
    if judgment.get("judgment_id") != payload["judgment_artifact_id"]:
        linkage_issues.append(
            _issue(code="judgment_artifact_id_mismatch", message="Referenced judgment artifact id did not match payload.", path="judgment_artifact_id")
        )
    if linkage_issues:
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code=linkage_issues[0]["code"],
            message="Recommendation resolution transition linkage validation failed.",
            semantic_issues=linkage_issues,
            details={
                "recommendation_artifact_path": str(recommendation_path),
                "judgment_artifact_path": str(judgment_path),
            },
            request_echo=request_echo,
        )

    locator_path = Path(str(payload["resolution_window_memory_path"]))
    locator_result = _load_resolution_window_locator(
        path=locator_path,
        user_id=payload["user_id"],
        start_date=payload["start_date"],
        end_date=payload["end_date"],
    )
    if not locator_result["ok"]:
        return _with_request_echo(locator_result, request_echo)

    transition_result = _apply_resolution_transition(
        locator_payload=locator_result["locator"],
        recommendation_path=recommendation_path,
        judgment_path=judgment_path,
    )
    if not transition_result["ok"]:
        return _with_request_echo(transition_result, request_echo)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dated_path = output_dir / f"recommendation_resolution_window_memory_{payload['start_date']}_{payload['end_date']}.json"
    latest_path = output_dir / "recommendation_resolution_window_memory_latest.json"
    serialized_locator = json.dumps(transition_result["locator"], indent=2, sort_keys=True) + "\n"
    _write_artifact_pair_atomically(serialized=serialized_locator, dated_path=dated_path, latest_path=latest_path)

    feedback_written_paths = None
    feedback_memory_path = payload.get("feedback_window_memory_path")
    if feedback_memory_path:
        feedback_result = _build_feedback_window_locator(
            path=Path(str(feedback_memory_path)),
            user_id=payload["user_id"],
            start_date=payload["start_date"],
            end_date=payload["end_date"],
            recommendation_path=recommendation_path,
            judgment_path=judgment_path,
        )
        if not feedback_result["ok"]:
            return _with_request_echo(feedback_result, request_echo)
        feedback_dated_path = output_dir / f"recommendation_feedback_window_memory_{payload['start_date']}_{payload['end_date']}.json"
        feedback_latest_path = output_dir / "recommendation_feedback_window_memory_latest.json"
        serialized_feedback = json.dumps(feedback_result["locator"], indent=2, sort_keys=True) + "\n"
        _write_artifact_pair_atomically(serialized=serialized_feedback, dated_path=feedback_dated_path, latest_path=feedback_latest_path)
        feedback_written_paths = {
            "artifact_path": str(feedback_dated_path),
            "latest_artifact_path": str(feedback_latest_path),
        }

    return {
        "ok": True,
        "artifact_path": str(dated_path),
        "latest_artifact_path": str(latest_path),
        "writeback": {
            "operation": "writeback.recommendation_resolution_transition",
            "user_id": payload["user_id"],
            "start_date": payload["start_date"],
            "end_date": payload["end_date"],
            "recommendation_artifact_path": str(recommendation_path),
            "recommendation_artifact_id": payload["recommendation_artifact_id"],
            "judgment_artifact_path": str(judgment_path),
            "judgment_artifact_id": payload["judgment_artifact_id"],
            "resolution_window_memory_path": str(locator_path),
            "feedback_window_memory_path": str(feedback_memory_path) if feedback_memory_path else None,
            "written_at": payload["written_at"],
            "request_id": payload["request_id"],
            "requested_at": payload["requested_at"],
            "written_locator_artifacts": {
                "resolution_window": {
                    "artifact_path": str(dated_path),
                    "latest_artifact_path": str(latest_path),
                },
                "feedback_window": feedback_written_paths,
            },
            "transition_target": {
                "date": transition_result["target_date"],
                "resolution_status": "judged",
            },
        },
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
                message="Payload file does not exist.",
                semantic_issues=[_issue(code="payload_not_found", message="Payload file does not exist.", path="payload_path")],
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
            message="Payload is not valid JSON.",
            semantic_issues=[_issue(code="invalid_payload_json", message=str(exc), path=payload_source)],
            details={"payload_source": payload_source},
        )

    if not isinstance(payload, dict):
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="invalid_payload_shape",
            message="Payload JSON must be an object.",
            semantic_issues=[_issue(code="invalid_payload_shape", message="Payload JSON must be an object.", path="$")],
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


def _resolution_transition_payload_issues(payload: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    allowed_fields = RESOLUTION_TRANSITION_REQUIRED_PAYLOAD_FIELDS | RESOLUTION_TRANSITION_OPTIONAL_PAYLOAD_FIELDS
    extra_fields = sorted(set(payload.keys()) - allowed_fields)
    for field in extra_fields:
        issues.append(_issue(code="unexpected_payload_field", message="Unexpected payload field.", path=field))

    missing_fields = sorted(RESOLUTION_TRANSITION_REQUIRED_PAYLOAD_FIELDS - set(payload.keys()))
    for field in missing_fields:
        issues.append(_issue(code="missing_required_field", message="Missing required field.", path=field))

    if issues:
        return issues

    for field in sorted(RESOLUTION_TRANSITION_REQUIRED_PAYLOAD_FIELDS):
        if not isinstance(payload[field], str) or not payload[field].strip():
            issues.append(_issue(code="invalid_string_field", message="Field must be a non-empty string.", path=field))

    if "feedback_window_memory_path" in payload and (not isinstance(payload["feedback_window_memory_path"], str) or not payload["feedback_window_memory_path"].strip()):
        issues.append(_issue(code="invalid_string_field", message="Field must be a non-empty string when provided.", path="feedback_window_memory_path"))

    if agent_retrieval_cli.agent_context_cli._parse_iso_date(payload["start_date"]) is None:
        issues.append(_issue(code="invalid_start_date", message="start_date must be YYYY-MM-DD.", path="start_date"))
    if agent_retrieval_cli.agent_context_cli._parse_iso_date(payload["end_date"]) is None:
        issues.append(_issue(code="invalid_end_date", message="end_date must be YYYY-MM-DD.", path="end_date"))
    if not _is_iso_datetime_with_timezone(payload["written_at"]):
        issues.append(_issue(code="invalid_written_at", message="written_at must be an ISO 8601 datetime string with timezone information.", path="written_at"))

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


def _load_resolution_window_locator(*, path: Path, user_id: str, start_date: str, end_date: str) -> dict[str, Any]:
    raw_result = _read_artifact_json(path, missing_code="memory_locator_not_found", invalid_code="invalid_memory_locator_json")
    if not raw_result["ok"]:
        return raw_result
    issues = agent_retrieval_cli._recommendation_resolution_window_locator_issues(
        payload=raw_result["artifact"],
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )
    if issues:
        return _validation_error(
            artifact_path=str(path),
            latest_artifact_path=None,
            code=issues[0]["code"],
            message="resolution_window_memory_path failed bounded validation.",
            semantic_issues=issues,
            details={"resolution_window_memory_path": str(path)},
        )
    return {
        "ok": True,
        "artifact_path": str(path),
        "locator": raw_result["artifact"],
        "validation": {"is_valid": True, "schema_issues": [], "semantic_issues": []},
        "error": None,
    }


def _apply_resolution_transition(*, locator_payload: dict[str, Any], recommendation_path: Path, judgment_path: Path) -> dict[str, Any]:
    updated_payload = json.loads(json.dumps(locator_payload))
    target_path = str(recommendation_path.resolve())
    matches = [
        entry
        for entry in updated_payload.get("accepted_recommendations", [])
        if agent_retrieval_cli._resolve_artifact_path(entry.get("recommendation_artifact_path")) == target_path
    ]
    if not matches:
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="target_recommendation_not_found",
            message="Target recommendation was absent from resolution locator.",
            semantic_issues=[_issue(code="target_recommendation_not_found", message="Target recommendation was absent from resolution locator.", path="recommendation_artifact_path")],
            details={"recommendation_artifact_path": str(recommendation_path)},
        )
    if len(matches) > 1:
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="duplicate_target_recommendation",
            message="Resolution locator listed the target recommendation more than once.",
            semantic_issues=[_issue(code="duplicate_target_recommendation", message="Resolution locator listed the target recommendation more than once.", path="accepted_recommendations")],
            details={"recommendation_artifact_path": str(recommendation_path)},
        )

    target_entry = matches[0]
    if target_entry.get("judgment_artifact_path"):
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="target_already_judged",
            message="Target recommendation already has a judgment_artifact_path.",
            semantic_issues=[_issue(code="target_already_judged", message="Target recommendation already has a judgment_artifact_path.", path="judgment_artifact_path")],
            details={"recommendation_artifact_path": str(recommendation_path)},
        )

    target_entry["judgment_artifact_path"] = str(judgment_path)
    return {"ok": True, "locator": updated_payload, "target_date": target_entry["date"], "validation": {"is_valid": True, "schema_issues": [], "semantic_issues": []}, "error": None}


def _build_feedback_window_locator(
    *,
    path: Path,
    user_id: str,
    start_date: str,
    end_date: str,
    recommendation_path: Path,
    judgment_path: Path,
) -> dict[str, Any]:
    if path.exists():
        raw_result = _read_artifact_json(path, missing_code="memory_locator_not_found", invalid_code="invalid_memory_locator_json")
        if not raw_result["ok"]:
            return raw_result
        updated = raw_result["artifact"]
        issues = agent_retrieval_cli._recommendation_feedback_window_locator_issues(
            payload=updated,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        if issues:
            return _validation_error(
                artifact_path=str(path),
                latest_artifact_path=None,
                code=issues[0]["code"],
                message="feedback_window_memory_path failed bounded validation.",
                semantic_issues=issues,
                details={"feedback_window_memory_path": str(path)},
            )
        updated = json.loads(json.dumps(updated))
    else:
        updated = {
            "artifact_type": agent_retrieval_cli.RECOMMENDATION_FEEDBACK_WINDOW_MEMORY_ARTIFACT_TYPE,
            "operation": "retrieve.recommendation_feedback_window",
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
            "accepted_feedback_pairs": [],
        }

    target_date = _artifact_date(recommendation_path)
    resolved_recommendation_path = str(recommendation_path.resolve())
    resolved_judgment_path = str(judgment_path.resolve())
    for entry in updated["accepted_feedback_pairs"]:
        if agent_retrieval_cli._resolve_artifact_path(entry.get("recommendation_artifact_path")) == resolved_recommendation_path:
            if agent_retrieval_cli._resolve_artifact_path(entry.get("judgment_artifact_path")) != resolved_judgment_path:
                return _validation_error(
                    artifact_path=str(path),
                    latest_artifact_path=None,
                    code="feedback_pair_conflict",
                    message="feedback_window_memory_path already linked the target recommendation inconsistently.",
                    semantic_issues=[_issue(code="feedback_pair_conflict", message="feedback_window_memory_path already linked the target recommendation inconsistently.", path="accepted_feedback_pairs")],
                    details={"feedback_window_memory_path": str(path)},
                )
            return {"ok": True, "locator": updated, "validation": {"is_valid": True, "schema_issues": [], "semantic_issues": []}, "error": None}

    updated["accepted_feedback_pairs"].append(
        {
            "date": target_date,
            "recommendation_artifact_path": str(recommendation_path),
            "judgment_artifact_path": str(judgment_path),
        }
    )
    updated["accepted_feedback_pairs"] = sorted(updated["accepted_feedback_pairs"], key=lambda item: (item["date"], item["recommendation_artifact_path"]))
    return {"ok": True, "locator": updated, "validation": {"is_valid": True, "schema_issues": [], "semantic_issues": []}, "error": None}


def _read_artifact_json(path: Path, *, missing_code: str, invalid_code: str) -> dict[str, Any]:
    if not path.exists():
        return _validation_error(
            artifact_path=str(path),
            latest_artifact_path=None,
            code=missing_code,
            message="Artifact file does not exist.",
            semantic_issues=[_issue(code=missing_code, message="Artifact file does not exist.", path="artifact_path")],
            details={"artifact_path": str(path)},
        )
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return _validation_error(
            artifact_path=str(path),
            latest_artifact_path=None,
            code=invalid_code,
            message="Artifact file is not valid JSON.",
            semantic_issues=[_issue(code=invalid_code, message=str(exc), path="artifact_path")],
            details={"artifact_path": str(path)},
        )
    if not isinstance(raw, dict):
        return _validation_error(
            artifact_path=str(path),
            latest_artifact_path=None,
            code="invalid_artifact_shape",
            message="Artifact JSON must be an object.",
            semantic_issues=[_issue(code="invalid_artifact_shape", message="Artifact JSON must be an object.", path="$")],
            details={"artifact_path": str(path)},
        )
    return {"ok": True, "artifact_path": str(path), "artifact": raw, "validation": {"is_valid": True, "schema_issues": [], "semantic_issues": []}, "error": None}


def _artifact_date(path: Path) -> str:
    return str(json.loads(path.read_text())["date"])


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


def _with_request_echo(response: dict[str, Any], request_echo: dict[str, Any]) -> dict[str, Any]:
    validation = dict(response.get("validation", {}))
    validation["request_echo"] = request_echo
    return {**response, "validation": validation}


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
