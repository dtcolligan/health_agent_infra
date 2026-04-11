from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any


ARTIFACT_TYPE = "agent_recommendation"
CONTEXT_ARTIFACT_TYPE = "agent_readable_daily_context"
REQUIRED_PAYLOAD_FIELDS = {
    "user_id",
    "date",
    "context_artifact_path",
    "context_artifact_id",
    "resolution_window_artifact_path",
    "recommendation_id",
    "summary",
    "rationale",
    "evidence_refs",
    "confidence_score",
    "policy_basis",
}


class CliParseError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliParseError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        description="Create one validated day-scoped Health Lab recommendation artifact from a scoped daily context artifact."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--output-dir", required=True)

    payload_group = create_parser.add_mutually_exclusive_group(required=True)
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
    if args.command != "create":
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
            message="Recommendation payload failed validation.",
            semantic_issues=validation_issues,
            details={"payload_source": payload_result["payload_source"]},
        )

    context_path = Path(str(payload["context_artifact_path"]))
    context_result = _load_context_artifact(context_path=context_path)
    if not context_result["ok"]:
        return context_result

    context = context_result["context"]
    context_issues = _context_semantic_issues(context=context, payload=payload, context_path=context_path)
    if context_issues:
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code=context_issues[0]["code"],
            message="Referenced context artifact failed validation.",
            semantic_issues=context_issues,
            details={"context_artifact_path": str(context_path)},
        )

    resolution_window_path = Path(str(payload["resolution_window_artifact_path"]))
    resolution_window_result = _load_resolution_window_artifact(resolution_window_path=resolution_window_path)
    if not resolution_window_result["ok"]:
        return resolution_window_result

    resolution_window = resolution_window_result["resolution_window"]
    resolution_window_issues = _resolution_window_semantic_issues(
        resolution_window=resolution_window,
        payload=payload,
        resolution_window_path=resolution_window_path,
    )
    if resolution_window_issues:
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code=resolution_window_issues[0]["code"],
            message="Referenced resolution-window artifact failed validation.",
            semantic_issues=resolution_window_issues,
            details={"resolution_window_artifact_path": str(resolution_window_path)},
        )

    recommendation = _build_recommendation(
        payload=payload,
        context_path=context_path,
        resolution_window_path=resolution_window_path,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dated_path = output_dir / f"{ARTIFACT_TYPE}_{payload['date']}.json"
    latest_path = output_dir / f"{ARTIFACT_TYPE}_latest.json"
    serialized = json.dumps(recommendation, indent=2, sort_keys=True) + "\n"
    _write_artifact_pair_atomically(serialized=serialized, dated_path=dated_path, latest_path=latest_path)

    return {
        "ok": True,
        "artifact_path": str(dated_path),
        "latest_artifact_path": str(latest_path),
        "recommendation": recommendation,
        "validation": {"is_valid": True, "schema_issues": [], "semantic_issues": []},
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
                message="Recommendation payload file does not exist.",
                semantic_issues=[_issue(code="payload_not_found", message="Recommendation payload file does not exist.", path="payload_path")],
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
            message="Recommendation payload is not valid JSON.",
            semantic_issues=[_issue(code="invalid_payload_json", message=str(exc), path=payload_source)],
            details={"payload_source": payload_source},
        )

    if not isinstance(payload, dict):
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="invalid_payload_shape",
            message="Recommendation payload JSON must be an object.",
            semantic_issues=[_issue(code="invalid_payload_shape", message="Recommendation payload JSON must be an object.", path="$")],
            details={"payload_source": payload_source},
        )

    return {"ok": True, "payload": payload, "payload_source": payload_source}


def _payload_semantic_issues(payload: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    extra_fields = sorted(set(payload.keys()) - REQUIRED_PAYLOAD_FIELDS)
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
        "context_artifact_path",
        "context_artifact_id",
        "resolution_window_artifact_path",
        "recommendation_id",
        "summary",
        "rationale",
    ):
        if not isinstance(payload[field], str) or not payload[field].strip():
            issues.append(_issue(code="invalid_string_field", message="Field must be a non-empty string.", path=field))

    evidence_refs = payload["evidence_refs"]
    if not isinstance(evidence_refs, list) or not evidence_refs:
        issues.append(_issue(code="invalid_evidence_refs", message="evidence_refs must be a non-empty array of strings.", path="evidence_refs"))
    else:
        for index, ref in enumerate(evidence_refs):
            if not isinstance(ref, str) or not ref.strip():
                issues.append(
                    _issue(
                        code="invalid_evidence_ref",
                        message="Each evidence ref must be a non-empty string.",
                        path=f"evidence_refs[{index}]",
                    )
                )

    confidence_score = payload["confidence_score"]
    if not isinstance(confidence_score, (int, float)) or isinstance(confidence_score, bool):
        issues.append(
            _issue(
                code="invalid_confidence_score",
                message="confidence_score must be a number in the closed interval [0.0, 1.0].",
                path="confidence_score",
            )
        )
    elif not 0.0 <= float(confidence_score) <= 1.0:
        issues.append(
            _issue(
                code="invalid_confidence_score",
                message="confidence_score must be a number in the closed interval [0.0, 1.0].",
                path="confidence_score",
            )
        )

    return issues


def _load_context_artifact(*, context_path: Path) -> dict[str, Any]:
    if not context_path.exists():
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="context_artifact_not_found",
            message="Referenced context artifact file does not exist.",
            semantic_issues=[
                _issue(code="context_artifact_not_found", message="Referenced context artifact file does not exist.", path="context_artifact_path")
            ],
            details={"context_artifact_path": str(context_path)},
        )

    try:
        raw = json.loads(context_path.read_text())
    except json.JSONDecodeError as exc:
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="invalid_context_artifact_json",
            message="Referenced context artifact is not valid JSON.",
            semantic_issues=[_issue(code="invalid_context_artifact_json", message=str(exc), path="context_artifact_path")],
            details={"context_artifact_path": str(context_path)},
        )

    if not isinstance(raw, dict):
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="invalid_context_artifact_shape",
            message="Referenced context artifact JSON must be an object.",
            semantic_issues=[
                _issue(code="invalid_context_artifact_shape", message="Referenced context artifact JSON must be an object.", path="$")
            ],
            details={"context_artifact_path": str(context_path)},
        )

    return {"ok": True, "context": raw}


def _load_resolution_window_artifact(*, resolution_window_path: Path) -> dict[str, Any]:
    if not resolution_window_path.exists():
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="resolution_window_artifact_not_found",
            message="Referenced resolution-window artifact file does not exist.",
            semantic_issues=[
                _issue(
                    code="resolution_window_artifact_not_found",
                    message="Referenced resolution-window artifact file does not exist.",
                    path="resolution_window_artifact_path",
                )
            ],
            details={"resolution_window_artifact_path": str(resolution_window_path)},
        )

    try:
        raw = json.loads(resolution_window_path.read_text())
    except json.JSONDecodeError as exc:
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="invalid_resolution_window_artifact",
            message="Referenced resolution-window artifact is not valid JSON.",
            semantic_issues=[_issue(code="invalid_resolution_window_artifact", message=str(exc), path="resolution_window_artifact_path")],
            details={"resolution_window_artifact_path": str(resolution_window_path)},
        )

    if not isinstance(raw, dict):
        return _validation_error(
            artifact_path=None,
            latest_artifact_path=None,
            code="invalid_resolution_window_artifact",
            message="Referenced resolution-window artifact JSON must be an object.",
            semantic_issues=[
                _issue(code="invalid_resolution_window_artifact", message="Referenced resolution-window artifact JSON must be an object.", path="$")
            ],
            details={"resolution_window_artifact_path": str(resolution_window_path)},
        )

    return {"ok": True, "resolution_window": raw}


def _context_semantic_issues(*, context: dict[str, Any], payload: dict[str, Any], context_path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    if context.get("artifact_type") != CONTEXT_ARTIFACT_TYPE:
        issues.append(
            _issue(
                code="context_artifact_type_mismatch",
                message=f"Expected artifact_type={CONTEXT_ARTIFACT_TYPE}.",
                path="artifact_type",
            )
        )
    if context.get("context_id") != payload["context_artifact_id"]:
        issues.append(
            _issue(
                code="context_artifact_id_mismatch",
                message="Referenced context artifact id does not match payload.",
                path="context_artifact_id",
            )
        )
    if context.get("user_id") != payload["user_id"]:
        issues.append(_issue(code="artifact_user_mismatch", message="Context user_id does not match payload.", path="user_id"))
    if context.get("date") != payload["date"]:
        issues.append(_issue(code="artifact_date_mismatch", message="Context date does not match payload.", path="date"))

    if str(context_path) != payload["context_artifact_path"]:
        issues.append(
            _issue(
                code="context_artifact_path_mismatch",
                message="Payload context_artifact_path does not match the referenced file path.",
                path="context_artifact_path",
            )
        )

    grounded_refs = _collect_context_evidence_refs(context)
    for index, ref in enumerate(payload["evidence_refs"]):
        if ref not in grounded_refs:
            issues.append(
                _issue(
                    code="ungrounded_evidence_ref",
                    message="Evidence ref is not grounded in the referenced context artifact.",
                    path=f"evidence_refs[{index}]",
                )
            )

    return issues


def _collect_context_evidence_refs(context: dict[str, Any]) -> set[str]:
    refs: set[str] = set()

    generated_from = context.get("generated_from", {})
    for key in ("source_artifact_ids", "input_event_ids", "subjective_entry_ids", "manual_log_entry_ids"):
        for ref in generated_from.get(key, []):
            if isinstance(ref, str) and ref:
                refs.add(ref)

    for signal in context.get("explicit_grounding", {}).get("signals", []):
        for ref in signal.get("evidence_refs", []):
            if isinstance(ref, str) and ref:
                refs.add(ref)

    for gap in context.get("important_gaps", []):
        for ref in gap.get("evidence_refs", []):
            if isinstance(ref, str) and ref:
                refs.add(ref)

    for conflict in context.get("conflicts", []):
        for ref in conflict.get("evidence_refs", []):
            if isinstance(ref, str) and ref:
                refs.add(ref)

    return refs


def _resolution_window_semantic_issues(
    *, resolution_window: dict[str, Any], payload: dict[str, Any], resolution_window_path: Path
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    if resolution_window.get("ok") is not True:
        issues.append(_issue(code="invalid_resolution_window_artifact", message="Resolution-window artifact must be a successful retrieval envelope.", path="ok"))

    retrieval = resolution_window.get("retrieval")
    if not isinstance(retrieval, dict):
        issues.append(_issue(code="invalid_resolution_window_artifact", message="Resolution-window artifact must include a retrieval object.", path="retrieval"))
        return issues

    if retrieval.get("operation") != "retrieve.recommendation_resolution_window":
        issues.append(_issue(code="invalid_resolution_window_artifact", message="Resolution-window artifact must come from retrieve.recommendation_resolution_window.", path="retrieval.operation"))

    scope = retrieval.get("scope")
    if not isinstance(scope, dict):
        issues.append(_issue(code="invalid_resolution_window_artifact", message="Resolution-window artifact must include a scope object.", path="retrieval.scope"))
        return issues

    if scope.get("user_id") != payload["user_id"]:
        issues.append(_issue(code="resolution_window_user_mismatch", message="Resolution-window user_id does not match payload.", path="retrieval.scope.user_id"))

    try:
        start_date = date.fromisoformat(str(scope.get("start_date")))
        end_date = date.fromisoformat(str(scope.get("end_date")))
        payload_date = date.fromisoformat(str(payload["date"]))
    except ValueError:
        issues.append(_issue(code="invalid_resolution_window_artifact", message="Resolution-window scope dates must be valid ISO dates.", path="retrieval.scope"))
        return issues

    if (end_date - start_date).days != 6:
        issues.append(_issue(code="invalid_resolution_window_artifact", message="Resolution-window scope must span exactly seven days.", path="retrieval.scope"))

    if payload_date != end_date + timedelta(days=1):
        issues.append(_issue(code="policy_basis_window_inconsistency", message="Recommendation date must be exactly one day after the supplied resolution-window end_date.", path="date"))

    policy_basis = payload.get("policy_basis")
    if not isinstance(policy_basis, dict):
        issues.append(_issue(code="invalid_policy_basis", message="policy_basis must be an object.", path="policy_basis"))
        return issues

    required_policy_fields = {"window_dates_considered", "prior_recommendation_refs", "policy_note"}
    for field in sorted(required_policy_fields - set(policy_basis.keys())):
        issues.append(_issue(code="missing_policy_basis_field", message="Missing required policy_basis field.", path=f"policy_basis.{field}"))
    if issues:
        return issues

    expected_dates = [start_date.isoformat(), end_date.isoformat()]
    if policy_basis["window_dates_considered"] != expected_dates:
        issues.append(_issue(code="policy_basis_window_inconsistency", message="policy_basis.window_dates_considered must match the supplied resolution-window scope.", path="policy_basis.window_dates_considered"))

    if not isinstance(policy_basis["policy_note"], str) or not policy_basis["policy_note"].strip():
        issues.append(_issue(code="invalid_policy_basis", message="policy_basis.policy_note must be a non-empty string.", path="policy_basis.policy_note"))

    prior_refs = policy_basis["prior_recommendation_refs"]
    if not isinstance(prior_refs, list) or not prior_refs:
        issues.append(_issue(code="invalid_policy_basis", message="policy_basis.prior_recommendation_refs must be a non-empty array.", path="policy_basis.prior_recommendation_refs"))
        return issues

    per_recommendation = retrieval.get("evidence", {}).get("per_recommendation", [])
    indexed = {entry.get("recommendation", {}).get("recommendation_id"): entry for entry in per_recommendation if isinstance(entry, dict)}
    for index, ref in enumerate(prior_refs):
        if not isinstance(ref, dict):
            issues.append(_issue(code="invalid_policy_basis", message="Each prior recommendation ref must be an object.", path=f"policy_basis.prior_recommendation_refs[{index}]"))
            continue
        recommendation_id = ref.get("recommendation_id")
        expected_entry = indexed.get(recommendation_id)
        if expected_entry is None:
            issues.append(_issue(code="uncited_window_reference", message="Cited prior recommendation is not present in the supplied resolution window.", path=f"policy_basis.prior_recommendation_refs[{index}].recommendation_id"))
            continue
        if ref.get("date") != expected_entry.get("date"):
            issues.append(_issue(code="policy_basis_window_inconsistency", message="Cited prior recommendation date does not match the supplied resolution window.", path=f"policy_basis.prior_recommendation_refs[{index}].date"))
        if ref.get("resolution_status") != expected_entry.get("resolution_status"):
            issues.append(_issue(code="policy_basis_window_inconsistency", message="Cited prior recommendation resolution_status does not match the supplied resolution window.", path=f"policy_basis.prior_recommendation_refs[{index}].resolution_status"))

    if str(resolution_window_path) != payload["resolution_window_artifact_path"]:
        issues.append(_issue(code="resolution_window_artifact_path_mismatch", message="Payload resolution_window_artifact_path does not match the referenced file path.", path="resolution_window_artifact_path"))

    return issues


def _build_recommendation(*, payload: dict[str, Any], context_path: Path, resolution_window_path: Path) -> dict[str, Any]:
    return {
        "artifact_type": ARTIFACT_TYPE,
        "user_id": payload["user_id"],
        "date": payload["date"],
        "context_artifact_path": str(context_path),
        "context_artifact_id": payload["context_artifact_id"],
        "resolution_window_artifact_path": str(resolution_window_path),
        "recommendation_id": payload["recommendation_id"],
        "summary": payload["summary"],
        "rationale": payload["rationale"],
        "evidence_refs": list(payload["evidence_refs"]),
        "confidence_score": float(payload["confidence_score"]),
        "policy_basis": payload["policy_basis"],
    }


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
) -> dict[str, Any]:
    return {
        "ok": False,
        "artifact_path": artifact_path,
        "latest_artifact_path": latest_artifact_path,
        "recommendation": None,
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
        "artifact_path": None,
        "latest_artifact_path": None,
        "recommendation": None,
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
