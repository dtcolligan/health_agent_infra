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
    "recommendation_class",
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
RECOMMENDATION_FEEDBACK_WINDOW_MEMORY_ARTIFACT_TYPE = "recommendation_feedback_window_memory"
RECOMMENDATION_RESOLUTION_WINDOW_MEMORY_ARTIFACT_TYPE = "recommendation_resolution_window_memory"
RECOMMENDATION_WINDOW_RANGE_LIMIT_DAYS = 7
DAY_SNAPSHOT_ARTIFACT_TYPE = "daily_health_snapshot"


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

    day_snapshot = subparsers.add_parser("day-snapshot")
    day_snapshot.add_argument("--artifact-path", required=True)
    day_snapshot.add_argument("--user-id", required=True)
    day_snapshot.add_argument("--date", required=True)
    day_snapshot.add_argument("--request-id", required=True)
    day_snapshot.add_argument("--requested-at", required=True)
    day_snapshot.add_argument("--include-conflicts", choices=["true", "false"])
    day_snapshot.add_argument("--include-missingness", choices=["true", "false"])

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

    recommendation_feedback_window = subparsers.add_parser("recommendation-feedback-window")
    recommendation_feedback_window.add_argument("--user-id", required=True)
    recommendation_feedback_window.add_argument("--start-date", required=True)
    recommendation_feedback_window.add_argument("--end-date", required=True)
    recommendation_feedback_window.add_argument("--memory-locator", required=True)
    recommendation_feedback_window.add_argument("--request-id", required=True)
    recommendation_feedback_window.add_argument("--requested-at", required=True)
    recommendation_feedback_window.add_argument("--timezone")
    recommendation_feedback_window.add_argument("--max-feedback-items", type=int)
    recommendation_feedback_window.add_argument("--include-conflicts", choices=["true", "false"])
    recommendation_feedback_window.add_argument("--include-missingness", choices=["true", "false"])

    recommendation_resolution_window = subparsers.add_parser("recommendation-resolution-window")
    recommendation_resolution_window.add_argument("--user-id", required=True)
    recommendation_resolution_window.add_argument("--start-date", required=True)
    recommendation_resolution_window.add_argument("--end-date", required=True)
    recommendation_resolution_window.add_argument("--memory-locator", required=True)
    recommendation_resolution_window.add_argument("--request-id", required=True)
    recommendation_resolution_window.add_argument("--requested-at", required=True)
    recommendation_resolution_window.add_argument("--timezone")
    recommendation_resolution_window.add_argument("--max-recommendation-items", type=int)
    recommendation_resolution_window.add_argument("--include-conflicts", choices=["true", "false"])
    recommendation_resolution_window.add_argument("--include-missingness", choices=["true", "false"])

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
    if args.command == "day-snapshot":
        return _run_day_snapshot(args)
    if args.command == "sleep-review":
        return _run_sleep_review(args)
    if args.command == "recommendation-judgment":
        return _run_recommendation_judgment(args)
    if args.command == "recommendation":
        return _run_recommendation(args)
    if args.command == "recommendation-feedback":
        return _run_recommendation_feedback(args)
    if args.command == "recommendation-feedback-window":
        return _run_recommendation_feedback_window(args)
    if args.command == "recommendation-resolution-window":
        return _run_recommendation_resolution_window(args)
    raise ValueError(f"Unsupported command: {args.command}")


def _run_day_snapshot(args: argparse.Namespace) -> dict[str, Any]:
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

    artifact_response = _read_day_snapshot_artifact(
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
    retrieval = _assemble_day_snapshot(artifact=artifact)
    if args.include_missingness == "false":
        retrieval["agent_notes"]["generic_or_missingness_notes"] = []

    conflicts = [] if args.include_conflicts == "false" else _day_snapshot_conflicts(artifact=artifact)

    return {
        "ok": True,
        "artifact_path": artifact_response["artifact_path"],
        "retrieval": {
            "operation": "retrieve.day_snapshot",
            "scope": {
                "user_id": args.user_id,
                "date": args.date,
            },
            "coverage_status": _day_snapshot_overall_coverage(retrieval=retrieval),
            "generated_from": {
                "artifact_path": artifact_response["artifact_path"],
                "daily_health_snapshot_id": artifact.get("daily_health_snapshot_id"),
            },
            "evidence": retrieval,
            "important_gaps": retrieval["coverage_status"]["missing_sources"] if args.include_missingness != "false" else [],
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


def _read_day_snapshot_artifact(*, path: Path, user_id: str, date: str) -> dict[str, Any]:
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

    semantic_issues = _day_snapshot_semantic_issues(raw=raw, user_id=user_id, date=date)
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


def _day_snapshot_semantic_issues(*, raw: Any, user_id: str, date: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(raw, dict):
        return [_issue(code="artifact_not_object", message="Artifact JSON must be an object.", path="$")]
    if raw.get("artifact_type") != DAY_SNAPSHOT_ARTIFACT_TYPE:
        issues.append(_issue(code="artifact_type_mismatch", message=f"Expected artifact_type={DAY_SNAPSHOT_ARTIFACT_TYPE}.", path="artifact_type"))
    if str(raw.get("user_id")) != str(user_id):
        issues.append(_issue(code="artifact_user_mismatch", message="Artifact user_id does not match request.", path="user_id"))
    if raw.get("date") != date:
        issues.append(_issue(code="artifact_date_mismatch", message="Artifact date does not match request.", path="date"))
    return issues


def _assemble_day_snapshot(*, artifact: dict[str, Any]) -> dict[str, Any]:
    sleep = artifact.get("sleep_daily") or {}
    readiness = artifact.get("readiness_daily") or {}
    subjective = artifact.get("subjective_daily") or {}
    nutrition = artifact.get("nutrition_daily") or {}
    running_sessions = artifact.get("running_sessions") or []
    gym_sessions = artifact.get("gym_sessions") or []
    gym_sets = artifact.get("gym_set_records") or artifact.get("gym_exercise_sets") or []
    source_flags = artifact.get("source_flags") or {}

    garmin_ready = bool(source_flags.get("garmin")) or any(
        value is not None
        for value in [
            artifact.get("sleep_duration_hours"),
            artifact.get("sleep_score"),
            artifact.get("body_battery_or_readiness"),
            artifact.get("readiness_label"),
            readiness.get("data_backed_observation"),
        ]
    )
    subjective_ready = bool(source_flags.get("subjective")) or any(
        value is not None
        for value in [
            artifact.get("subjective_energy_1_5"),
            artifact.get("subjective_soreness_1_5"),
            artifact.get("subjective_stress_1_5"),
            artifact.get("overall_day_note"),
            subjective.get("subjective_energy_1_5"),
            subjective.get("subjective_soreness_1_5"),
            subjective.get("subjective_stress_1_5"),
            subjective.get("overall_day_note"),
        ]
    )
    nutrition_present = bool(source_flags.get("cronometer")) or any(
        value is not None
        for value in [
            artifact.get("calories_kcal"),
            artifact.get("protein_g"),
            artifact.get("carbs_g"),
            artifact.get("fat_g"),
            nutrition.get("food_log_completeness"),
        ]
    )
    manual_gym_present = bool(source_flags.get("manual_gym_log")) or bool(gym_sessions or gym_sets)

    missing_sources: list[str] = []
    blocked_sources: list[str] = []
    if not garmin_ready:
        missing_sources.append("garmin")
    if not subjective_ready:
        missing_sources.append("subjective")

    provenance_refs = []
    for section, payload in (("garmin", sleep), ("garmin", readiness), ("subjective", subjective), ("nutrition_bridge", nutrition)):
        if isinstance(payload, dict) and any(value is not None for key, value in payload.items() if key.endswith("_id") or key in {"source_name", "source"}):
            provenance_refs.append(
                {
                    "section": section,
                    "source_name": payload.get("source_name") or payload.get("source"),
                    "source_record_id": payload.get("source_record_id"),
                    "provenance_record_id": payload.get("provenance_record_id"),
                }
            )

    data_backed_notes = [note for note in [readiness.get("data_backed_observation"), artifact.get("overall_day_note")] if note]
    generic_notes = []
    if garmin_ready and subjective_ready:
        generic_notes.append("Garmin and subjective flagship lanes are ready for this date.")
    if not nutrition_present:
        generic_notes.append("Cronometer remains optional bridge enrichment and does not gate the flagship day snapshot.")
    if not manual_gym_present:
        generic_notes.append("Manual gym or external gym connectors remain optional and do not gate the flagship day snapshot.")
    if readiness.get("caveat"):
        generic_notes.append(readiness["caveat"])

    manual_gym_sessions = []
    for session in running_sessions:
        provenance_refs.append(
            {
                "section": "garmin",
                "source_name": session.get("source_name") or session.get("source"),
                "source_record_id": session.get("source_record_id"),
                "provenance_record_id": session.get("provenance_record_id"),
            }
        )
    for session in gym_sessions:
        manual_gym_sessions.append(
            {
                "session_id": session.get("session_id") or session.get("training_session_id"),
                "session_title": session.get("session_title"),
                "session_type": session.get("session_type"),
                "lift_focus": session.get("lift_focus"),
                "source_name": session.get("source_name") or session.get("source"),
            }
        )
        provenance_refs.append(
            {
                "section": "manual_gym_enrichment",
                "source_name": session.get("source_name") or session.get("source"),
                "source_record_id": session.get("source_record_id"),
                "provenance_record_id": session.get("provenance_record_id"),
            }
        )

    return {
        "date": artifact["date"],
        "coverage_status": {
            "garmin_ready": garmin_ready,
            "subjective_ready": subjective_ready,
            "nutrition_present": nutrition_present,
            "manual_gym_present": manual_gym_present,
            "missing_sources": missing_sources,
            "blocked_sources": blocked_sources,
        },
        "flagship_summary": {
            "sleep_duration_hours": artifact.get("sleep_duration_hours") or _sec_to_hours(sleep.get("total_sleep_sec")),
            "sleep_score": artifact.get("sleep_score") or sleep.get("sleep_score"),
            "readiness_score": readiness.get("readiness_score") or artifact.get("body_battery_or_readiness"),
            "readiness_label": artifact.get("readiness_label") or readiness.get("readiness_label"),
            "running_sessions_count": artifact.get("running_sessions_count"),
            "running_volume_m": artifact.get("running_volume_m"),
            "data_backed_observation": readiness.get("data_backed_observation"),
            "subjective_energy_1_5": artifact.get("subjective_energy_1_5") or subjective.get("subjective_energy_1_5"),
            "subjective_soreness_1_5": artifact.get("subjective_soreness_1_5") or subjective.get("subjective_soreness_1_5"),
            "subjective_stress_1_5": artifact.get("subjective_stress_1_5") or subjective.get("subjective_stress_1_5"),
            "overall_day_note": artifact.get("overall_day_note") or subjective.get("overall_day_note"),
        },
        "bridge_enrichment": {
            "nutrition_summary": {
                "present": nutrition_present,
                "calories_kcal": artifact.get("calories_kcal") or nutrition.get("calories_kcal"),
                "protein_g": artifact.get("protein_g") or nutrition.get("protein_g"),
                "carbs_g": artifact.get("carbs_g") or nutrition.get("carbs_g"),
                "fat_g": artifact.get("fat_g") or nutrition.get("fat_g"),
                "food_log_completeness": nutrition.get("food_log_completeness"),
                "source_name": nutrition.get("source_name"),
            },
            "manual_gym_summary": {
                "present": manual_gym_present,
                "session_count": len(manual_gym_sessions),
                "sessions": manual_gym_sessions,
                "total_sets": _sum_present([session.get("total_sets") for session in gym_sessions]) or artifact.get("gym_total_sets"),
                "total_reps": _sum_present([session.get("total_reps") for session in gym_sessions]) or artifact.get("gym_total_reps"),
                "total_load_kg": _sum_present([session.get("total_load_kg") for session in gym_sessions]) or artifact.get("gym_total_load_kg"),
            },
        },
        "agent_notes": {
            "data_backed_notes": data_backed_notes,
            "generic_or_missingness_notes": generic_notes,
        },
        "provenance_refs": provenance_refs,
    }


def _day_snapshot_overall_coverage(*, retrieval: dict[str, Any]) -> str:
    flags = retrieval["coverage_status"]
    present_count = sum(1 for key in ["garmin_ready", "subjective_ready"] if flags[key])
    if present_count == 0:
        return "missing"
    if present_count == 2:
        return "present"
    return "partial"


def _day_snapshot_conflicts(*, artifact: dict[str, Any]) -> list[dict[str, Any]]:
    conflicts = []
    for path, payload in [
        ("sleep_daily", artifact.get("sleep_daily")),
        ("readiness_daily", artifact.get("readiness_daily")),
        ("subjective_daily", artifact.get("subjective_daily")),
        ("nutrition_daily", artifact.get("nutrition_daily")),
    ]:
        if isinstance(payload, dict) and payload.get("conflict_status") not in {None, "none"}:
            conflicts.append({"path": path, "conflict_status": payload.get("conflict_status")})
    return conflicts


def _sec_to_hours(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value) / 3600, 2)


def _sum_present(values: list[Any]) -> float | int | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present)


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


def _run_recommendation_feedback_window(args: argparse.Namespace) -> dict[str, Any]:
    request_validation, _request_echo = validate_and_echo_request_metadata(
        request_id=args.request_id,
        requested_at=args.requested_at,
    )
    if not request_validation["is_valid"]:
        return {
            "ok": False,
            "artifact_path": args.memory_locator,
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

    range_validation = _validate_recommendation_feedback_window_scope(
        user_id=args.user_id,
        start_date=args.start_date,
        end_date=args.end_date,
        memory_locator=args.memory_locator,
    )
    if range_validation is not None:
        return _recommendation_feedback_window_error(
            memory_locator=args.memory_locator,
            code=range_validation["semantic_issues"][0]["code"],
            message="Recommendation feedback window scope failed validation.",
            semantic_issues=range_validation["semantic_issues"],
            request_validation=request_validation,
            details=range_validation["details"],
        )

    locator_path = Path(args.memory_locator)
    if not locator_path.exists():
        return _recommendation_feedback_window_error(
            memory_locator=args.memory_locator,
            code="memory_locator_not_found",
            message="memory_locator could not be resolved.",
            semantic_issues=[_issue(code="memory_locator_not_found", message="memory_locator could not be resolved.", path="memory_locator")],
            request_validation=request_validation,
            details={"memory_locator": args.memory_locator},
        )

    try:
        locator_payload = json.loads(locator_path.read_text())
    except json.JSONDecodeError as exc:
        return _recommendation_feedback_window_error(
            memory_locator=args.memory_locator,
            code="invalid_memory_locator_json",
            message="memory_locator did not resolve to valid JSON.",
            semantic_issues=[_issue(code="invalid_memory_locator_json", message=str(exc), path="memory_locator")],
            request_validation=request_validation,
            details={"memory_locator": args.memory_locator},
        )

    locator_issues = _recommendation_feedback_window_locator_issues(
        payload=locator_payload,
        user_id=args.user_id,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    if locator_issues:
        return _recommendation_feedback_window_error(
            memory_locator=args.memory_locator,
            code=locator_issues[0]["code"],
            message="memory_locator failed bounded recommendation feedback window validation.",
            semantic_issues=locator_issues,
            request_validation=request_validation,
            details={
                "memory_locator": args.memory_locator,
                "user_id": args.user_id,
                "start_date": args.start_date,
                "end_date": args.end_date,
            },
        )

    pair_entries = locator_payload.get("accepted_feedback_pairs", [])
    expected_dates = agent_context_cli._expected_dates(args.start_date, args.end_date)
    max_feedback_items = args.max_feedback_items if args.max_feedback_items is not None and args.max_feedback_items > 0 else None
    include_missingness = args.include_missingness != "false"
    feedback_items: list[dict[str, Any]] = []
    generated_pairs: list[dict[str, Any]] = []

    for entry in sorted(pair_entries, key=lambda item: item["date"]):
        pair_issues = _recommendation_feedback_window_pair_entry_issues(entry=entry)
        if pair_issues:
            return _recommendation_feedback_window_error(
                memory_locator=args.memory_locator,
                code=pair_issues[0]["code"],
                message="memory_locator listed a malformed recommendation feedback pair.",
                semantic_issues=pair_issues,
                request_validation=request_validation,
                details={"memory_locator": args.memory_locator, "pair_entry": entry},
            )

        recommendation_response = _read_recommendation_artifact(
            path=Path(entry["recommendation_artifact_path"]),
            user_id=args.user_id,
            date=entry["date"],
        )
        if not recommendation_response["ok"]:
            return _recommendation_feedback_window_error(
                memory_locator=args.memory_locator,
                code=recommendation_response["error"]["code"],
                message="Accepted recommendation artifact failed validation.",
                semantic_issues=recommendation_response["validation"]["semantic_issues"],
                request_validation=request_validation,
                details={"memory_locator": args.memory_locator, "pair_entry": entry},
            )
        judgment_response = _read_recommendation_judgment_artifact(
            path=Path(entry["judgment_artifact_path"]),
            user_id=args.user_id,
            date=entry["date"],
        )
        if not judgment_response["ok"]:
            return _recommendation_feedback_window_error(
                memory_locator=args.memory_locator,
                code=judgment_response["error"]["code"],
                message="Accepted judgment artifact failed validation.",
                semantic_issues=judgment_response["validation"]["semantic_issues"],
                request_validation=request_validation,
                details={"memory_locator": args.memory_locator, "pair_entry": entry},
            )

        linkage_issues = _recommendation_feedback_linkage_issues(
            recommendation=recommendation_response["artifact"],
            judgment=judgment_response["artifact"],
            supplied_recommendation_artifact_path=entry["recommendation_artifact_path"],
        )
        if linkage_issues:
            return _recommendation_feedback_window_error(
                memory_locator=args.memory_locator,
                code=linkage_issues[0]["code"],
                message="Recommendation feedback window linkage validation failed.",
                semantic_issues=linkage_issues,
                request_validation=request_validation,
                details={
                    "memory_locator": args.memory_locator,
                    "pair_entry": entry,
                    "recommendation_artifact_path": recommendation_response["artifact_path"],
                    "judgment_artifact_path": judgment_response["artifact_path"],
                },
            )

        feedback_items.append(
            {
                "date": entry["date"],
                "coverage_status": "present",
                "recommendation": {
                    key: recommendation_response["artifact"][key]
                    for key in RECOMMENDATION_FEEDBACK_RECOMMENDATION_KEYS
                    if key in recommendation_response["artifact"]
                },
                "judgment": {
                    key: judgment_response["artifact"][key]
                    for key in RECOMMENDATION_FEEDBACK_JUDGMENT_KEYS
                    if key in judgment_response["artifact"]
                },
                "linkage": {
                    "recommendation_artifact_id": recommendation_response["artifact"].get("recommendation_id"),
                    "judgment_recommendation_artifact_id": judgment_response["artifact"].get("recommendation_artifact_id"),
                    "judgment_recommendation_artifact_path": judgment_response["artifact"].get("recommendation_artifact_path"),
                    "supplied_recommendation_artifact_path": recommendation_response["artifact_path"],
                },
            }
        )
        generated_pairs.append(
            {
                "date": entry["date"],
                "recommendation_artifact_path": recommendation_response["artifact_path"],
                "judgment_artifact_path": judgment_response["artifact_path"],
            }
        )

    if max_feedback_items is not None:
        feedback_items = feedback_items[:max_feedback_items]
        generated_pairs = generated_pairs[:max_feedback_items]

    missing_dates = [date for date in expected_dates if date not in {item["date"] for item in feedback_items}]
    important_gaps = [{"date": date, "code": "no_linked_feedback_pair"} for date in missing_dates] if include_missingness else []

    return {
        "ok": True,
        "artifact_path": args.memory_locator,
        "retrieval": {
            "operation": "retrieve.recommendation_feedback_window",
            "scope": {
                "user_id": args.user_id,
                "start_date": args.start_date,
                "end_date": args.end_date,
                "timezone": args.timezone,
            },
            "coverage_status": "present" if len(feedback_items) == len(expected_dates) else "partial",
            "generated_from": {
                "memory_locator": args.memory_locator,
                "accepted_feedback_pairs": generated_pairs,
            },
            "evidence": {
                "days_requested": len(expected_dates),
                "days_with_feedback": len(feedback_items),
                "per_day": feedback_items,
            },
            "important_gaps": important_gaps,
            "conflicts": [],
            "unsupported_claims": [],
        },
        "validation": request_validation,
        "error": None,
    }


def _run_recommendation_resolution_window(args: argparse.Namespace) -> dict[str, Any]:
    request_validation, _request_echo = validate_and_echo_request_metadata(
        request_id=args.request_id,
        requested_at=args.requested_at,
    )
    if not request_validation["is_valid"]:
        return {
            "ok": False,
            "artifact_path": args.memory_locator,
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

    range_validation = _validate_recommendation_feedback_window_scope(
        user_id=args.user_id,
        start_date=args.start_date,
        end_date=args.end_date,
        memory_locator=args.memory_locator,
    )
    if range_validation is not None:
        return _recommendation_feedback_window_error(
            memory_locator=args.memory_locator,
            code=range_validation["semantic_issues"][0]["code"],
            message="Recommendation resolution window scope failed validation.",
            semantic_issues=range_validation["semantic_issues"],
            request_validation=request_validation,
            details=range_validation["details"],
        )

    locator_path = Path(args.memory_locator)
    if not locator_path.exists():
        return _recommendation_feedback_window_error(
            memory_locator=args.memory_locator,
            code="memory_locator_not_found",
            message="memory_locator could not be resolved.",
            semantic_issues=[_issue(code="memory_locator_not_found", message="memory_locator could not be resolved.", path="memory_locator")],
            request_validation=request_validation,
            details={"memory_locator": args.memory_locator},
        )

    try:
        locator_payload = json.loads(locator_path.read_text())
    except json.JSONDecodeError as exc:
        return _recommendation_feedback_window_error(
            memory_locator=args.memory_locator,
            code="invalid_memory_locator_json",
            message="memory_locator did not resolve to valid JSON.",
            semantic_issues=[_issue(code="invalid_memory_locator_json", message=str(exc), path="memory_locator")],
            request_validation=request_validation,
            details={"memory_locator": args.memory_locator},
        )

    locator_issues = _recommendation_resolution_window_locator_issues(
        payload=locator_payload,
        user_id=args.user_id,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    if locator_issues:
        return _recommendation_feedback_window_error(
            memory_locator=args.memory_locator,
            code=locator_issues[0]["code"],
            message="memory_locator failed bounded recommendation resolution window validation.",
            semantic_issues=locator_issues,
            request_validation=request_validation,
            details={
                "memory_locator": args.memory_locator,
                "user_id": args.user_id,
                "start_date": args.start_date,
                "end_date": args.end_date,
            },
        )

    recommendation_entries = locator_payload.get("accepted_recommendations", [])
    expected_dates = agent_context_cli._expected_dates(args.start_date, args.end_date)
    max_recommendation_items = args.max_recommendation_items if args.max_recommendation_items is not None and args.max_recommendation_items > 0 else None
    include_missingness = args.include_missingness != "false"
    resolution_items = []
    generated_entries = []

    for entry in sorted(recommendation_entries, key=lambda item: (item["date"], item.get("recommendation_artifact_path", ""))):
        entry_issues = _recommendation_resolution_window_entry_issues(entry=entry)
        if entry_issues:
            return _recommendation_feedback_window_error(
                memory_locator=args.memory_locator,
                code=entry_issues[0]["code"],
                message="memory_locator listed a malformed recommendation resolution entry.",
                semantic_issues=entry_issues,
                request_validation=request_validation,
                details={"memory_locator": args.memory_locator, "recommendation_entry": entry},
            )

        recommendation_response = _read_recommendation_artifact(
            path=Path(entry["recommendation_artifact_path"]),
            user_id=args.user_id,
            date=entry["date"],
        )
        if not recommendation_response["ok"]:
            return _recommendation_feedback_window_error(
                memory_locator=args.memory_locator,
                code=recommendation_response["error"]["code"],
                message="Accepted recommendation artifact failed validation.",
                semantic_issues=recommendation_response["validation"]["semantic_issues"],
                request_validation=request_validation,
                details={"memory_locator": args.memory_locator, "recommendation_entry": entry},
            )

        item = {
            "date": entry["date"],
            "coverage_status": "present",
            "resolution_status": "pending_judgment",
            "recommendation": {
                key: recommendation_response["artifact"][key]
                for key in RECOMMENDATION_FEEDBACK_RECOMMENDATION_KEYS
                if key in recommendation_response["artifact"]
            },
        }
        generated_entry = {
            "date": entry["date"],
            "recommendation_artifact_path": recommendation_response["artifact_path"],
        }

        if entry.get("judgment_artifact_path"):
            judgment_response = _read_recommendation_judgment_artifact(
                path=Path(entry["judgment_artifact_path"]),
                user_id=args.user_id,
                date=entry["date"],
            )
            if not judgment_response["ok"]:
                return _recommendation_feedback_window_error(
                    memory_locator=args.memory_locator,
                    code=judgment_response["error"]["code"],
                    message="Accepted judgment artifact failed validation.",
                    semantic_issues=judgment_response["validation"]["semantic_issues"],
                    request_validation=request_validation,
                    details={"memory_locator": args.memory_locator, "recommendation_entry": entry},
                )
            linkage_issues = _recommendation_feedback_linkage_issues(
                recommendation=recommendation_response["artifact"],
                judgment=judgment_response["artifact"],
                supplied_recommendation_artifact_path=entry["recommendation_artifact_path"],
            )
            if linkage_issues:
                return _recommendation_feedback_window_error(
                    memory_locator=args.memory_locator,
                    code=linkage_issues[0]["code"],
                    message="Recommendation resolution window linkage validation failed.",
                    semantic_issues=linkage_issues,
                    request_validation=request_validation,
                    details={"memory_locator": args.memory_locator, "recommendation_entry": entry},
                )
            item["resolution_status"] = "judged"
            item["judgment"] = {key: judgment_response["artifact"][key] for key in RECOMMENDATION_FEEDBACK_JUDGMENT_KEYS if key in judgment_response["artifact"]}
            item["linkage"] = {
                "recommendation_artifact_id": recommendation_response["artifact"].get("recommendation_id"),
                "judgment_recommendation_artifact_id": judgment_response["artifact"].get("recommendation_artifact_id"),
                "judgment_recommendation_artifact_path": judgment_response["artifact"].get("recommendation_artifact_path"),
                "supplied_recommendation_artifact_path": recommendation_response["artifact_path"],
            }
            generated_entry["judgment_artifact_path"] = judgment_response["artifact_path"]

        resolution_items.append(item)
        generated_entries.append(generated_entry)

    if max_recommendation_items is not None:
        resolution_items = resolution_items[:max_recommendation_items]
        generated_entries = generated_entries[:max_recommendation_items]

    dates_with_recommendations = {item["date"] for item in resolution_items}
    no_recommendation_dates = [date for date in expected_dates if date not in dates_with_recommendations]
    important_gaps = [{"date": date, "code": "no_recommendation"} for date in no_recommendation_dates] if include_missingness else []

    return {
        "ok": True,
        "artifact_path": args.memory_locator,
        "retrieval": {
            "operation": "retrieve.recommendation_resolution_window",
            "scope": {
                "user_id": args.user_id,
                "start_date": args.start_date,
                "end_date": args.end_date,
                "timezone": args.timezone,
            },
            "coverage_status": "present" if len(no_recommendation_dates) == 0 else "partial",
            "generated_from": {
                "memory_locator": args.memory_locator,
                "accepted_recommendations": generated_entries,
            },
            "evidence": {
                "days_requested": len(expected_dates),
                "days_with_recommendations": len(dates_with_recommendations),
                "recommendation_items": len(resolution_items),
                "judged_items": sum(1 for item in resolution_items if item["resolution_status"] == "judged"),
                "pending_judgment_items": sum(1 for item in resolution_items if item["resolution_status"] == "pending_judgment"),
                "per_recommendation": resolution_items,
            },
            "important_gaps": important_gaps,
            "conflicts": [],
            "unsupported_claims": [],
        },
        "validation": request_validation,
        "error": None,
    }


def _validate_recommendation_feedback_window_scope(*, user_id: str, start_date: str, end_date: str, memory_locator: str) -> dict[str, Any] | None:
    semantic_issues: list[dict[str, str]] = []
    parsed_start = agent_context_cli._parse_iso_date(start_date)
    parsed_end = agent_context_cli._parse_iso_date(end_date)
    if parsed_start is None:
        semantic_issues.append(_issue(code="invalid_start_date", message="start_date must be YYYY-MM-DD.", path="start_date"))
    if parsed_end is None:
        semantic_issues.append(_issue(code="invalid_end_date", message="end_date must be YYYY-MM-DD.", path="end_date"))
    if not isinstance(user_id, str) or not user_id.strip():
        semantic_issues.append(_issue(code="invalid_user_id", message="user_id must be a non-empty string.", path="user_id"))
    if not isinstance(memory_locator, str) or not memory_locator.strip():
        semantic_issues.append(_issue(code="invalid_memory_locator", message="memory_locator must be a non-empty string.", path="memory_locator"))
    if parsed_start is not None and parsed_end is not None:
        if parsed_end < parsed_start:
            semantic_issues.append(_issue(code="non_contiguous_range", message="end_date must be on or after start_date.", path="end_date"))
        elif (parsed_end - parsed_start).days + 1 > RECOMMENDATION_WINDOW_RANGE_LIMIT_DAYS:
            semantic_issues.append(
                _issue(
                    code="range_limit_exceeded",
                    message=f"Recommendation feedback window retrieval is capped at {RECOMMENDATION_WINDOW_RANGE_LIMIT_DAYS} contiguous days.",
                    path="end_date",
                )
            )
    if semantic_issues:
        return {
            "semantic_issues": semantic_issues,
            "details": {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date,
                "memory_locator": memory_locator,
            },
        }
    return None


def _recommendation_resolution_window_locator_issues(*, payload: Any, user_id: str, start_date: str, end_date: str) -> list[dict[str, str]]:
    if not isinstance(payload, dict):
        return [_issue(code="invalid_memory_locator_payload", message="memory_locator payload must be an object.", path="$")]
    issues = []
    if payload.get("artifact_type") != RECOMMENDATION_RESOLUTION_WINDOW_MEMORY_ARTIFACT_TYPE:
        issues.append(_issue(code="memory_locator_wrong_type", message=f"Expected artifact_type={RECOMMENDATION_RESOLUTION_WINDOW_MEMORY_ARTIFACT_TYPE}.", path="artifact_type"))
    if payload.get("user_id") != user_id:
        issues.append(_issue(code="memory_locator_wrong_scope", message="memory_locator user_id did not match request.", path="user_id"))
    if payload.get("start_date") != start_date:
        issues.append(_issue(code="memory_locator_wrong_scope", message="memory_locator start_date did not match request.", path="start_date"))
    if payload.get("end_date") != end_date:
        issues.append(_issue(code="memory_locator_wrong_scope", message="memory_locator end_date did not match request.", path="end_date"))
    recommendation_entries = payload.get("accepted_recommendations")
    if not isinstance(recommendation_entries, list):
        issues.append(_issue(code="memory_locator_missing_recommendations", message="memory_locator must list accepted_recommendations.", path="accepted_recommendations"))
        return issues
    expected_dates = set(agent_context_cli._expected_dates(start_date, end_date))
    seen_entries = set()
    for index, entry in enumerate(recommendation_entries):
        if not isinstance(entry, dict):
            issues.append(_issue(code="malformed_recommendation_entry", message="Each accepted recommendation entry must be an object.", path=f"accepted_recommendations[{index}]"))
            continue
        entry_date = entry.get("date")
        if entry_date not in expected_dates:
            issues.append(_issue(code="memory_locator_wrong_scope", message="accepted recommendation date was outside request range.", path=f"accepted_recommendations[{index}].date"))
        dedupe_key = (entry_date, entry.get("recommendation_artifact_path"))
        if dedupe_key in seen_entries:
            issues.append(_issue(code="duplicate_recommendation_entry", message="accepted recommendation entries must be unique by date and recommendation_artifact_path.", path=f"accepted_recommendations[{index}]"))
        seen_entries.add(dedupe_key)
    return issues


def _recommendation_resolution_window_entry_issues(*, entry: Any) -> list[dict[str, str]]:
    if not isinstance(entry, dict):
        return [_issue(code="malformed_recommendation_entry", message="accepted recommendation entry must be an object.", path="accepted_recommendations")]
    issues = []
    if not isinstance(entry.get("date"), str) or agent_context_cli._parse_iso_date(entry["date"]) is None:
        issues.append(_issue(code="malformed_recommendation_entry", message="accepted recommendation date must be YYYY-MM-DD.", path="date"))
    if not isinstance(entry.get("recommendation_artifact_path"), str) or not entry.get("recommendation_artifact_path", "").strip():
        issues.append(_issue(code="malformed_recommendation_entry", message="accepted recommendation entry must include recommendation_artifact_path.", path="recommendation_artifact_path"))
    if "judgment_artifact_path" in entry and entry.get("judgment_artifact_path") is not None and (not isinstance(entry.get("judgment_artifact_path"), str) or not entry.get("judgment_artifact_path", "").strip()):
        issues.append(_issue(code="malformed_recommendation_entry", message="judgment_artifact_path must be a non-empty string when present.", path="judgment_artifact_path"))
    return issues


def _recommendation_feedback_window_locator_issues(*, payload: Any, user_id: str, start_date: str, end_date: str) -> list[dict[str, str]]:
    if not isinstance(payload, dict):
        return [_issue(code="invalid_memory_locator_payload", message="memory_locator payload must be an object.", path="$")]
    issues: list[dict[str, str]] = []
    if payload.get("artifact_type") != RECOMMENDATION_FEEDBACK_WINDOW_MEMORY_ARTIFACT_TYPE:
        issues.append(
            _issue(
                code="memory_locator_wrong_type",
                message=f"Expected artifact_type={RECOMMENDATION_FEEDBACK_WINDOW_MEMORY_ARTIFACT_TYPE}.",
                path="artifact_type",
            )
        )
    if payload.get("user_id") != user_id:
        issues.append(_issue(code="memory_locator_wrong_scope", message="memory_locator user_id did not match request.", path="user_id"))
    if payload.get("start_date") != start_date:
        issues.append(_issue(code="memory_locator_wrong_scope", message="memory_locator start_date did not match request.", path="start_date"))
    if payload.get("end_date") != end_date:
        issues.append(_issue(code="memory_locator_wrong_scope", message="memory_locator end_date did not match request.", path="end_date"))
    pair_entries = payload.get("accepted_feedback_pairs")
    if not isinstance(pair_entries, list):
        issues.append(
            _issue(
                code="memory_locator_missing_feedback_pairs",
                message="memory_locator must list accepted_feedback_pairs.",
                path="accepted_feedback_pairs",
            )
        )
        return issues
    expected_dates = set(agent_context_cli._expected_dates(start_date, end_date))
    seen_dates: set[str] = set()
    for index, entry in enumerate(pair_entries):
        if not isinstance(entry, dict):
            issues.append(_issue(code="malformed_feedback_pair", message="Each accepted feedback pair must be an object.", path=f"accepted_feedback_pairs[{index}]"))
            continue
        entry_date = entry.get("date")
        if entry_date not in expected_dates:
            issues.append(_issue(code="memory_locator_wrong_scope", message="accepted feedback pair date was outside request range.", path=f"accepted_feedback_pairs[{index}].date"))
        if entry_date in seen_dates:
            issues.append(_issue(code="duplicate_feedback_pair_date", message="accepted feedback pair dates must be unique.", path=f"accepted_feedback_pairs[{index}].date"))
        if isinstance(entry_date, str):
            seen_dates.add(entry_date)
    return issues


def _recommendation_feedback_window_pair_entry_issues(*, entry: Any) -> list[dict[str, str]]:
    if not isinstance(entry, dict):
        return [_issue(code="malformed_feedback_pair", message="accepted feedback pair must be an object.", path="accepted_feedback_pairs")]
    issues: list[dict[str, str]] = []
    if not isinstance(entry.get("date"), str) or agent_context_cli._parse_iso_date(entry["date"]) is None:
        issues.append(_issue(code="malformed_feedback_pair", message="accepted feedback pair date must be YYYY-MM-DD.", path="date"))
    if not isinstance(entry.get("recommendation_artifact_path"), str) or not entry.get("recommendation_artifact_path", "").strip():
        issues.append(_issue(code="malformed_feedback_pair", message="accepted feedback pair must include recommendation_artifact_path.", path="recommendation_artifact_path"))
    if not isinstance(entry.get("judgment_artifact_path"), str) or not entry.get("judgment_artifact_path", "").strip():
        issues.append(_issue(code="malformed_feedback_pair", message="accepted feedback pair must include judgment_artifact_path.", path="judgment_artifact_path"))
    return issues


def _recommendation_feedback_window_error(
    *,
    memory_locator: str,
    code: str,
    message: str,
    semantic_issues: list[dict[str, str]],
    request_validation: dict[str, Any],
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ok": False,
        "artifact_path": memory_locator,
        "retrieval": None,
        "validation": {
            "is_valid": False,
            "schema_issues": [],
            "semantic_issues": semantic_issues,
            "request_echo": request_validation["request_echo"],
        },
        "error": {
            "code": code,
            "message": message,
            "retryable": False,
            "details": details,
        },
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
