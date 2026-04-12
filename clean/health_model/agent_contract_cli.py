from __future__ import annotations

import argparse
import json
import sys
from typing import Any


CONTRACT_ID = "health_lab_agent_contract"
CONTRACT_VERSION = "2026-04-11"
SHARED_ARGS = {
    "bundle_path": {
        "flag": "--bundle-path",
        "type": "string",
        "required": True,
        "description": "Path to the persisted shared input bundle JSON.",
    },
    "output_dir": {
        "flag": "--output-dir",
        "type": "string",
        "required": True,
        "description": "Directory where generated daily context artifacts are written.",
    },
    "user_id": {
        "flag": "--user-id",
        "type": "string",
        "required": True,
        "description": "Scoped Health Lab user identifier.",
    },
    "date": {
        "flag": "--date",
        "type": "date",
        "required": True,
        "description": "ISO date for the requested daily scope, YYYY-MM-DD.",
    },
    "collected_at": {
        "flag": "--collected-at",
        "type": "datetime",
        "required": True,
        "description": "ISO 8601 timestamp for when the source data was collected.",
    },
    "ingested_at": {
        "flag": "--ingested-at",
        "type": "datetime",
        "required": True,
        "description": "ISO 8601 timestamp for when Health Lab ingested the source data.",
    },
    "raw_location": {
        "flag": "--raw-location",
        "type": "string",
        "required": True,
        "description": "Stable raw-location reference for the input record.",
    },
    "confidence_score": {
        "flag": "--confidence-score",
        "type": "float",
        "required": True,
        "description": "Confidence score in the closed interval [0.0, 1.0].",
    },
    "completeness_state": {
        "flag": "--completeness-state",
        "type": "enum",
        "required": True,
        "accepted_values": ["partial", "complete", "corrected"],
        "description": "Completeness marker for the submitted manual entry.",
    },
    "source_name": {
        "flag": "--source-name",
        "type": "string",
        "required": False,
        "description": "Optional source name override for manual submissions.",
    },
}

RETRIEVAL_COMMON_ARGS = {
    "artifact_path": {
        "name": "artifact_path",
        "flag": "--artifact-path",
        "type": "string",
        "required": True,
        "description": "Path to one scoped read-only artifact when retrieval is backed by a local artifact file.",
    },
    "recommendation_artifact_path": {
        "name": "recommendation_artifact_path",
        "flag": "--recommendation-artifact-path",
        "type": "string",
        "required": True,
        "description": "Path to one scoped read-only agent_recommendation artifact.",
    },
    "judgment_artifact_path": {
        "name": "judgment_artifact_path",
        "flag": "--judgment-artifact-path",
        "type": "string",
        "required": True,
        "description": "Path to one scoped read-only recommendation_judgment artifact.",
    },
    "memory_locator": {
        "name": "memory_locator",
        "flag": "--memory-locator",
        "type": "string",
        "required": True,
        "description": "External user-owned memory reference or locator. Health Lab does not host the backing store.",
    },
    "request_id": {
        "name": "request_id",
        "flag": "--request-id",
        "type": "string",
        "required": True,
        "description": "Required non-empty request identifier. Daily retrieval ops validate it and echo it back under validation.request_echo.",
    },
    "requested_at": {
        "name": "requested_at",
        "flag": "--requested-at",
        "type": "datetime",
        "required": True,
        "description": "Required ISO 8601 timestamp with timezone information. Daily retrieval ops validate it and echo it back under validation.request_echo.",
    },
    "start_date": {
        "name": "start_date",
        "flag": "--start-date",
        "type": "date",
        "required": True,
        "description": "Inclusive ISO start date for range-scoped retrieval, YYYY-MM-DD.",
    },
    "end_date": {
        "name": "end_date",
        "flag": "--end-date",
        "type": "date",
        "required": True,
        "description": "Inclusive ISO end date for range-scoped retrieval, YYYY-MM-DD.",
    },
    "timezone": {
        "name": "timezone",
        "flag": "--timezone",
        "type": "string",
        "required": False,
        "description": "Optional timezone hint for interpreting requested scope.",
    },
    "max_evidence_items": {
        "name": "max_evidence_items",
        "flag": "--max-evidence-items",
        "type": "integer",
        "required": False,
        "description": "Optional cap on returned evidence items.",
    },
    "include_conflicts": {
        "name": "include_conflicts",
        "flag": "--include-conflicts",
        "type": "enum",
        "required": False,
        "accepted_values": ["true", "false"],
        "description": "Whether to include surfaced conflicts in the retrieval response.",
    },
    "include_missingness": {
        "name": "include_missingness",
        "flag": "--include-missingness",
        "type": "enum",
        "required": False,
        "accepted_values": ["true", "false"],
        "description": "Whether to include explicit missingness notes in the retrieval response.",
    },
}


class CliParseError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliParseError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="Describe the stable Health Lab external agent contract as machine-readable JSON.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("describe")
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
    if args.command != "describe":
        raise ValueError(f"Unsupported command: {args.command}")

    return {
        "ok": True,
        "contract": _contract_payload(),
        "validation": {"is_valid": True, "schema_issues": [], "semantic_issues": []},
        "error": None,
    }


def _contract_payload() -> dict[str, Any]:
    return {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "architecture_boundary": {
            "private_memory_layer": "external_to_health_lab",
            "health_lab_role": "protocol_reference_layer_only",
            "hosted_memory_claims": False,
            "embedded_coach_claims": False,
        },
        "discovery": {
            "cli_module": "health_model.agent_contract_cli",
            "command": "describe",
            "read_only": True,
        },
        "supported_operations": {
            "bootstrap.init": {
                "module": "health_model.agent_bundle_cli",
                "command": "init",
                "mode": "write",
                "description": "Create one canonical empty shared-input bundle and fail closed if the target path already exists.",
                "args": [
                    _shared_arg("bundle_path"),
                    _shared_arg("user_id"),
                    _shared_arg("date"),
                ],
            },
            "contract.describe": {
                "module": "health_model.agent_contract_cli",
                "command": "describe",
                "mode": "read",
                "description": "Return this contract description as machine-readable JSON.",
                "args": [],
            },
            "submit.hydration": {
                "module": "health_model.agent_submit_cli",
                "command": "hydration",
                "mode": "write",
                "description": "Append one same-day hydration log and regenerate daily context artifacts.",
                "args": [
                    *(_shared_arg(name) for name in (
                        "bundle_path",
                        "output_dir",
                        "user_id",
                        "date",
                        "collected_at",
                        "ingested_at",
                        "raw_location",
                        "confidence_score",
                        "completeness_state",
                        "source_name",
                    )),
                    {
                        "name": "amount_ml",
                        "flag": "--amount-ml",
                        "type": "float",
                        "required": True,
                        "description": "Hydration amount in millilitres.",
                    },
                    {
                        "name": "beverage_type",
                        "flag": "--beverage-type",
                        "type": "string",
                        "required": False,
                        "description": "Optional beverage type label, for example water.",
                    },
                    {
                        "name": "notes",
                        "flag": "--notes",
                        "type": "string",
                        "required": False,
                        "description": "Optional free-text note.",
                    },
                ],
            },
            "submit.meal": {
                "module": "health_model.agent_submit_cli",
                "command": "meal",
                "mode": "write",
                "description": "Append one same-day meal note and regenerate daily context artifacts.",
                "args": [
                    *(_shared_arg(name) for name in (
                        "bundle_path",
                        "output_dir",
                        "user_id",
                        "date",
                        "collected_at",
                        "ingested_at",
                        "raw_location",
                        "confidence_score",
                        "completeness_state",
                        "source_name",
                    )),
                    {
                        "name": "note_text",
                        "flag": "--note-text",
                        "type": "string",
                        "required": True,
                        "description": "Free-text meal note.",
                    },
                    {
                        "name": "meal_label",
                        "flag": "--meal-label",
                        "type": "string",
                        "required": False,
                        "description": "Optional meal label, for example breakfast, lunch, or dinner.",
                    },
                    {
                        "name": "estimated",
                        "flag": "--estimated",
                        "type": "enum",
                        "required": True,
                        "accepted_values": ["true", "false"],
                        "description": "Whether the meal note is estimated.",
                    },
                    {
                        "name": "notes",
                        "flag": "--notes",
                        "type": "string",
                        "required": False,
                        "description": "Optional free-text note.",
                    },
                ],
            },
            "submit.voice_note": {
                "module": "health_model.agent_voice_note_cli",
                "command": "submit",
                "mode": "write",
                "description": "Append one canonicalized same-day transcribed voice note and regenerate daily context artifacts.",
                "args": [
                    *(_shared_arg(name) for name in ("bundle_path", "output_dir", "user_id", "date")),
                    {
                        "name": "payload_json",
                        "flag": "--payload-json",
                        "type": "json_object",
                        "required": False,
                        "description": "Bounded transcribed voice-note payload as one JSON object string. Exactly one of --payload-json or --payload-path is required.",
                    },
                    {
                        "name": "payload_path",
                        "flag": "--payload-path",
                        "type": "string",
                        "required": False,
                        "description": "Path to one bounded transcribed voice-note JSON payload file. Exactly one of --payload-json or --payload-path is required.",
                    },
                ],
                "consumes": [
                    "shared_input_bundle",
                    "voice_note_submission_payload",
                ],
                "produces": [
                    "shared_input_bundle",
                    "agent_readable_daily_context_dated",
                    "agent_readable_daily_context_latest",
                ],
            },
            "context.get": {
                "module": "health_model.agent_context_cli",
                "command": "get",
                "mode": "read",
                "description": "Read one dated agent-readable daily context artifact.",
                "args": [
                    {
                        "name": "artifact_path",
                        "flag": "--artifact-path",
                        "type": "string",
                        "required": True,
                        "description": "Path to an agent_readable_daily_context JSON artifact.",
                    },
                    {
                        "name": "user_id",
                        "flag": "--user-id",
                        "type": "string",
                        "required": True,
                        "description": "Scoped Health Lab user identifier.",
                    },
                    {
                        "name": "date",
                        "flag": "--date",
                        "type": "date",
                        "required": True,
                        "description": "ISO date expected inside the artifact, YYYY-MM-DD.",
                    },
                ],
            },
            "context.get_latest": {
                "module": "health_model.agent_context_cli",
                "command": "get-latest",
                "mode": "read",
                "description": "Read the latest agent-readable daily context artifact scoped to one user.",
                "args": [
                    {
                        "name": "artifact_path",
                        "flag": "--artifact-path",
                        "type": "string",
                        "required": True,
                        "description": "Path to the latest agent_readable_daily_context JSON artifact.",
                    },
                    {
                        "name": "user_id",
                        "flag": "--user-id",
                        "type": "string",
                        "required": True,
                        "description": "Scoped Health Lab user identifier.",
                    },
                ],
            },
            "retrieve.day_context": {
                "module": "health_model.agent_context_cli",
                "command": "get",
                "mode": "read",
                "description": "Return one scoped agent-readable daily context artifact as the v1 retrieval proof surface, with request metadata validated and echoed under validation.request_echo.",
                "implementation_status": "proof_complete",
                "args": [
                    _shared_arg("user_id"),
                    _shared_arg("date"),
                    _retrieval_arg("artifact_path"),
                    _retrieval_arg("request_id"),
                    _retrieval_arg("requested_at"),
                    _retrieval_arg("include_conflicts"),
                    _retrieval_arg("include_missingness"),
                ],
                "consumes": ["agent_readable_daily_context"],
                "produces": ["retrieval_response_envelope"],
                "response_envelope": "retrieval",
            },
            "retrieve.day_nutrition_brief": {
                "module": "health_model.day_nutrition_brief",
                "command": "retrieve-day-nutrition-brief",
                "mode": "read",
                "description": "Return one bounded day-scoped nutrition brief from an accepted nutrition brief artifact, with request metadata validated and echoed under validation.request_echo.",
                "implementation_status": "proof_complete",
                "args": [
                    _shared_arg("user_id"),
                    _shared_arg("date"),
                    _retrieval_arg("artifact_path"),
                    _retrieval_arg("request_id"),
                    _retrieval_arg("requested_at"),
                    _retrieval_arg("include_conflicts"),
                    _retrieval_arg("include_missingness"),
                ],
                "consumes": ["day_nutrition_brief"],
                "produces": ["retrieval_response_envelope"],
                "response_envelope": "retrieval",
            },
            "retrieve.sleep_review": {
                "module": "health_model.agent_retrieval_cli",
                "command": "sleep-review",
                "mode": "read",
                "description": "Return one bounded one-day sleep evidence review from an accepted day-scoped context artifact, with request metadata validated and echoed under validation.request_echo.",
                "implementation_status": "proof_complete",
                "args": [
                    _shared_arg("user_id"),
                    _shared_arg("date"),
                    _retrieval_arg("artifact_path"),
                    _retrieval_arg("request_id"),
                    _retrieval_arg("requested_at"),
                    _retrieval_arg("include_conflicts"),
                    _retrieval_arg("include_missingness"),
                ],
                "consumes": ["agent_readable_daily_context"],
                "produces": ["retrieval_response_envelope"],
                "response_envelope": "retrieval",
            },
            "retrieve.recommendation": {
                "module": "health_model.agent_retrieval_cli",
                "command": "recommendation",
                "mode": "read",
                "description": "Return one bounded recommendation artifact from an accepted agent_recommendation artifact, with request metadata validated and echoed under validation.request_echo.",
                "implementation_status": "proof_complete",
                "args": [
                    _shared_arg("user_id"),
                    _shared_arg("date"),
                    _retrieval_arg("artifact_path"),
                    _retrieval_arg("request_id"),
                    _retrieval_arg("requested_at"),
                    _retrieval_arg("include_conflicts"),
                    _retrieval_arg("include_missingness"),
                ],
                "consumes": ["agent_recommendation"],
                "produces": ["retrieval_response_envelope"],
                "response_envelope": "retrieval",
            },
            "retrieve.recommendation_judgment": {
                "module": "health_model.agent_retrieval_cli",
                "command": "recommendation-judgment",
                "mode": "read",
                "description": "Return one bounded recommendation judgment artifact from an accepted recommendation_judgment artifact, with request metadata validated and echoed under validation.request_echo.",
                "implementation_status": "proof_complete",
                "args": [
                    _shared_arg("user_id"),
                    _shared_arg("date"),
                    _retrieval_arg("artifact_path"),
                    _retrieval_arg("request_id"),
                    _retrieval_arg("requested_at"),
                    _retrieval_arg("include_conflicts"),
                    _retrieval_arg("include_missingness"),
                ],
                "consumes": ["recommendation_judgment"],
                "produces": ["retrieval_response_envelope"],
                "response_envelope": "retrieval",
            },
            "retrieve.recommendation_feedback": {
                "module": "health_model.agent_retrieval_cli",
                "command": "recommendation-feedback",
                "mode": "read",
                "description": "Return one bounded recommendation plus same-day judgment pair, failing closed unless both artifacts validate and their id and path linkage match.",
                "implementation_status": "proof_complete",
                "args": [
                    _shared_arg("user_id"),
                    _shared_arg("date"),
                    _retrieval_arg("recommendation_artifact_path"),
                    _retrieval_arg("judgment_artifact_path"),
                    _retrieval_arg("request_id"),
                    _retrieval_arg("requested_at"),
                    _retrieval_arg("include_conflicts"),
                    _retrieval_arg("include_missingness"),
                ],
                "consumes": ["agent_recommendation", "recommendation_judgment"],
                "produces": ["retrieval_response_envelope"],
                "response_envelope": "retrieval",
            },
            "retrieve.recommendation_feedback_window": {
                "module": "health_model.agent_retrieval_cli",
                "command": "recommendation-feedback-window",
                "mode": "read",
                "description": "Return one bounded seven-day window of linked recommendation plus same-day judgment pairs aggregated only from a scoped memory locator fixture, failing closed on locator, scope, or linkage violations.",
                "implementation_status": "proof_complete",
                "args": [
                    _shared_arg("user_id"),
                    _retrieval_arg("start_date"),
                    _retrieval_arg("end_date"),
                    _retrieval_arg("memory_locator"),
                    _retrieval_arg("request_id"),
                    _retrieval_arg("requested_at"),
                    _retrieval_arg("timezone"),
                    {
                        "name": "max_feedback_items",
                        "flag": "--max-feedback-items",
                        "type": "integer",
                        "required": False,
                        "description": "Optional cap on returned linked recommendation-feedback items after bounded locator validation.",
                    },
                    _retrieval_arg("include_conflicts"),
                    _retrieval_arg("include_missingness"),
                ],
                "consumes": ["user_owned_private_memory_locator", "agent_recommendation", "recommendation_judgment"],
                "produces": ["retrieval_response_envelope"],
                "response_envelope": "retrieval",
                "range_limit_days": 7,
            },
            "retrieve.recommendation_resolution_window": {
                "module": "health_model.agent_retrieval_cli",
                "command": "recommendation-resolution-window",
                "mode": "read",
                "description": "Return one bounded seven-day window of accepted recommendations from a scoped memory locator fixture, separating judged items, pending_judgment items, and no-recommendation dates while failing closed on locator, scope, or linkage violations.",
                "implementation_status": "proof_complete",
                "args": [
                    _shared_arg("user_id"),
                    _retrieval_arg("start_date"),
                    _retrieval_arg("end_date"),
                    _retrieval_arg("memory_locator"),
                    _retrieval_arg("request_id"),
                    _retrieval_arg("requested_at"),
                    _retrieval_arg("timezone"),
                    {
                        "name": "max_recommendation_items",
                        "flag": "--max-recommendation-items",
                        "type": "integer",
                        "required": False,
                        "description": "Optional cap on returned recommendation resolution items after bounded locator validation.",
                    },
                    _retrieval_arg("include_conflicts"),
                    _retrieval_arg("include_missingness"),
                ],
                "consumes": ["user_owned_private_memory_locator", "agent_recommendation", "recommendation_judgment"],
                "produces": ["retrieval_response_envelope"],
                "response_envelope": "retrieval",
                "range_limit_days": 7,
            },
            "retrieve.weekly_pattern_review": {
                "module": "health_model.agent_context_cli",
                "command": "retrieve-weekly-pattern-review",
                "mode": "read",
                "description": "Return one bounded seven-day weekly pattern review aggregated only from accepted daily context artifacts listed by a bounded memory locator fixture, with request metadata validated and echoed under validation.request_echo.",
                "implementation_status": "proof_complete",
                "args": [
                    _shared_arg("user_id"),
                    _retrieval_arg("start_date"),
                    _retrieval_arg("end_date"),
                    _retrieval_arg("memory_locator"),
                    _retrieval_arg("request_id"),
                    _retrieval_arg("requested_at"),
                    _retrieval_arg("timezone"),
                    _retrieval_arg("max_evidence_items"),
                    _retrieval_arg("include_conflicts"),
                    _retrieval_arg("include_missingness"),
                ],
                "consumes": ["user_owned_private_memory_locator", "agent_readable_daily_context"],
                "produces": ["retrieval_response_envelope"],
                "response_envelope": "retrieval",
                "range_limit_days": 7,
            },
            "recommendation.create": {
                "module": "health_model.agent_recommendation_cli",
                "command": "create",
                "mode": "write",
                "description": "Write one validated day-scoped recommendation artifact grounded in one scoped daily context artifact plus one accepted seven-day recommendation-resolution-window retrieval envelope.",
                "args": [
                    {
                        "name": "output_dir",
                        "flag": "--output-dir",
                        "type": "string",
                        "required": True,
                        "description": "Directory where dated and latest recommendation artifacts are written.",
                    },
                    {
                        "name": "payload_json",
                        "flag": "--payload-json",
                        "type": "json_object",
                        "required": False,
                        "description": "Recommendation payload JSON object string. Exactly one of --payload-json or --payload-path is required.",
                    },
                    {
                        "name": "payload_path",
                        "flag": "--payload-path",
                        "type": "string",
                        "required": False,
                        "description": "Path to one recommendation payload JSON file. Exactly one of --payload-json or --payload-path is required.",
                    },
                ],
                "consumes": ["agent_readable_daily_context", "recommendation_resolution_window_retrieval_envelope"],
                "produces": ["agent_recommendation_dated", "agent_recommendation_latest"],
                "payload_shape": {
                    "required_fields": [
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
                    ],
                    "notes": "All evidence_refs must already exist in the referenced agent_readable_daily_context. recommendation.create also requires one accepted seven-day retrieve.recommendation_resolution_window envelope and policy_basis refs that truthfully match that supplied window artifact.",
                },
            },
            "writeback.recommendation_judgment": {
                "module": "health_model.agent_memory_write_cli",
                "command": "recommendation-judgment",
                "mode": "write",
                "description": "Write one validated same-day recommendation judgment artifact grounded in one scoped recommendation artifact.",
                "implementation_status": "proof_complete",
                "args": [
                    {
                        "name": "output_dir",
                        "flag": "--output-dir",
                        "type": "string",
                        "required": True,
                        "description": "Directory where dated and latest recommendation judgment artifacts are written.",
                    },
                    {
                        "name": "payload_json",
                        "flag": "--payload-json",
                        "type": "json_object",
                        "required": False,
                        "description": "Recommendation judgment payload JSON object string. Exactly one of --payload-json or --payload-path is required.",
                    },
                    {
                        "name": "payload_path",
                        "flag": "--payload-path",
                        "type": "string",
                        "required": False,
                        "description": "Path to one recommendation judgment payload JSON file. Exactly one of --payload-json or --payload-path is required.",
                    },
                ],
                "consumes": ["agent_recommendation"],
                "produces": ["recommendation_judgment_dated", "recommendation_judgment_latest"],
                "payload_shape": {
                    "required_fields": [
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
                        "requested_at"
                    ],
                    "optional_fields": ["caveat", "time_cost_note", "friction_points", "gym_note"],
                    "accepted_judgment_labels": ["useful", "obvious", "wrong", "ignored"],
                    "notes": "The payload user_id/date must match the referenced recommendation artifact scope, request metadata must include timezone-aware requested_at, and failure must be non-mutating.",
                },
                "response_envelope": "writeback",
            },
            "writeback.recommendation_resolution_transition": {
                "module": "health_model.agent_memory_write_cli",
                "command": "recommendation-resolution-transition",
                "mode": "write",
                "description": "Write one updated bounded recommendation-resolution-window locator by attaching one already-written same-day judgment to one targeted pending recommendation entry, and optionally emit the paired feedback-window locator.",
                "implementation_status": "proof_complete",
                "args": [
                    {
                        "name": "output_dir",
                        "flag": "--output-dir",
                        "type": "string",
                        "required": True,
                        "description": "Directory where dated and latest locator artifacts are written.",
                    },
                    {
                        "name": "payload_json",
                        "flag": "--payload-json",
                        "type": "json_object",
                        "required": False,
                        "description": "Recommendation resolution transition payload JSON object string. Exactly one of --payload-json or --payload-path is required.",
                    },
                    {
                        "name": "payload_path",
                        "flag": "--payload-path",
                        "type": "string",
                        "required": False,
                        "description": "Path to one recommendation resolution transition payload JSON file. Exactly one of --payload-json or --payload-path is required.",
                    },
                ],
                "consumes": ["agent_recommendation", "recommendation_judgment", "recommendation_resolution_window_memory"],
                "produces": ["recommendation_resolution_window_memory_dated", "recommendation_resolution_window_memory_latest", "recommendation_feedback_window_memory_dated", "recommendation_feedback_window_memory_latest"],
                "payload_shape": {
                    "required_fields": [
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
                        "requested_at"
                    ],
                    "optional_fields": ["feedback_window_memory_path"],
                    "notes": "The payload must stay within one seven-day locator-scoped window, validate the supplied recommendation and judgment linkage, mutate only the targeted recommendation entry by attaching judgment_artifact_path, and fail closed without mutating written locator artifacts on rejection.",
                },
                "response_envelope": "writeback",
            },
        },
        "accepted_enums": {
            "bundle_commands": ["init"],
            "submit_commands": ["hydration", "meal"],
            "voice_note_commands": ["submit"],
            "voice_note_payload_inputs": ["payload_json", "payload_path"],
            "context_commands": ["get", "get-latest"],
            "retrieval_operations": [
                "retrieve.day_context",
                "retrieve.day_nutrition_brief",
                "retrieve.sleep_review",
                "retrieve.recommendation",
                "retrieve.recommendation_judgment",
                "retrieve.recommendation_feedback",
                "retrieve.recommendation_feedback_window",
                "retrieve.recommendation_resolution_window",
                "retrieve.weekly_pattern_review",
            ],
            "recommendation_commands": ["create"],
            "recommendation_payload_inputs": ["payload_json", "payload_path"],
            "writeback_operations": ["writeback.recommendation_judgment", "writeback.recommendation_resolution_transition"],
            "writeback_payload_inputs": ["payload_json", "payload_path"],
            "judgment_labels": ["useful", "obvious", "wrong", "ignored"],
            "contract_commands": ["describe"],
            "completeness_state": ["partial", "complete", "corrected"],
            "estimated": ["true", "false"],
            "retrieval_boolean_flags": ["true", "false"],
            "retrieval_missingness_states": ["present", "partial", "missing", "not_supported"],
            "retrieval_conflict_states": ["none", "source_conflict", "scope_conflict", "resolution_required"],
        },
        "accepted_scope_fields": [
            "user_id",
            "date",
            "start_date",
            "end_date",
            "artifact_path",
            "memory_locator",
            "request_id",
            "requested_at",
            "timezone",
            "max_evidence_items",
            "max_recommendation_items",
            "include_conflicts",
            "include_missingness",
            "recommendation_artifact_path",
            "judgment_artifact_path",
            "recommendation_artifact_id",
            "judgment_id",
            "judgment_label",
            "action_taken",
            "why",
            "written_at",
            "resolution_window_memory_path",
            "feedback_window_memory_path",
            "judgment_artifact_id",
        ],
        "artifact_types": {
            "consumed": [
                {
                    "artifact_type": "shared_input_bundle",
                    "shape": "persisted shared-input bundle JSON consumed through --bundle-path and bootstrapped by bootstrap.init when starting from zero local state",
                },
                {
                    "artifact_type": "agent_readable_daily_context",
                    "shape": "read-only context JSON consumed through --artifact-path",
                },
                {
                    "artifact_type": "voice_note_submission_payload",
                    "shape": "bounded transcribed voice-note JSON object consumed through --payload-json or --payload-path by submit.voice_note",
                },
            ],
            "produced": [
                {
                    "artifact_type": "shared_input_bundle",
                    "paths": [
                        "{output_dir}/shared_input_bundle_{date}.json",
                    ],
                },
                {
                    "artifact_type": "agent_readable_daily_context",
                    "paths": [
                        "{output_dir}/agent_readable_daily_context_{date}.json",
                        "{output_dir}/agent_readable_daily_context_latest.json",
                    ],
                    "notes": "submit.hydration, submit.meal, and submit.voice_note regenerate both the dated and latest artifacts on success.",
                },
                {
                    "artifact_type": "agent_recommendation",
                    "paths": [
                        "{output_dir}/agent_recommendation_{date}.json",
                        "{output_dir}/agent_recommendation_latest.json",
                    ],
                    "notes": "recommendation.create writes exactly one day-scoped recommendation artifact and fails closed on malformed payloads, scope mismatches, invalid context artifacts, missing or invalid resolution-window artifacts, or ungrounded evidence refs. Produced artifacts preserve both same-day context linkage and explicit policy_basis grounding into the supplied resolution window.",
                },
                {
                    "artifact_type": "recommendation_judgment",
                    "paths": [
                        "{output_dir}/recommendation_judgment_{date}.json",
                        "{output_dir}/recommendation_judgment_latest.json"
                    ],
                    "notes": "writeback.recommendation_judgment writes exactly one same-day recommendation judgment artifact grounded in one recommendation artifact and fails closed on scope mismatch, missing recommendation artifacts, invalid labels, invalid timestamps, or mismatched recommendation ids.",
                },
                {
                    "artifact_type": "recommendation_resolution_window_memory",
                    "paths": [
                        "{output_dir}/recommendation_resolution_window_memory_{start_date}_{end_date}.json",
                        "{output_dir}/recommendation_resolution_window_memory_latest.json"
                    ],
                    "notes": "writeback.recommendation_resolution_transition writes one updated locator artifact for the same bounded seven-day window and mutates only the targeted recommendation entry by attaching the supplied judgment_artifact_path.",
                },
                {
                    "artifact_type": "recommendation_feedback_window_memory",
                    "paths": [
                        "{output_dir}/recommendation_feedback_window_memory_{start_date}_{end_date}.json",
                        "{output_dir}/recommendation_feedback_window_memory_latest.json"
                    ],
                    "notes": "writeback.recommendation_resolution_transition may also emit a paired feedback-window locator for the same bounded window when feedback_window_memory_path is supplied.",
                }
            ],
        },
        "path_conventions": {
            "bundle_path": "{output_dir}/shared_input_bundle_{date}.json",
            "dated_context_artifact": "{output_dir}/agent_readable_daily_context_{date}.json",
            "latest_context_artifact": "{output_dir}/agent_readable_daily_context_latest.json",
            "dated_recommendation_artifact": "{output_dir}/agent_recommendation_{date}.json",
            "latest_recommendation_artifact": "{output_dir}/agent_recommendation_latest.json",
            "dated_recommendation_judgment_artifact": "{output_dir}/recommendation_judgment_{date}.json",
            "latest_recommendation_judgment_artifact": "{output_dir}/recommendation_judgment_latest.json",
            "dated_recommendation_resolution_window_memory_artifact": "{output_dir}/recommendation_resolution_window_memory_{start_date}_{end_date}.json",
            "latest_recommendation_resolution_window_memory_artifact": "{output_dir}/recommendation_resolution_window_memory_latest.json",
            "dated_recommendation_feedback_window_memory_artifact": "{output_dir}/recommendation_feedback_window_memory_{start_date}_{end_date}.json",
            "latest_recommendation_feedback_window_memory_artifact": "{output_dir}/recommendation_feedback_window_memory_latest.json",
        },
        "response_envelopes": {
            "bootstrap.init": {
                "success_keys": ["ok", "bundle_path", "bundle", "validation", "error"],
                "error_keys": ["ok", "bundle_path", "bundle", "validation", "error"],
            },
            "contract.describe": {
                "success_keys": ["ok", "contract", "validation", "error"],
                "error_keys": ["ok", "contract", "validation", "error"],
            },
            "submit": {
                "success_keys": ["ok", "bundle_path", "dated_artifact_path", "latest_artifact_path", "accepted_provenance", "validation", "error"],
                "error_keys": ["ok", "bundle_path", "dated_artifact_path", "latest_artifact_path", "accepted_provenance", "validation", "error"],
            },
            "context": {
                "success_keys": ["ok", "artifact_path", "context", "validation", "error"],
                "error_keys": ["ok", "artifact_path", "context", "validation", "error"],
            },
            "recommendation.create": {
                "success_keys": ["ok", "artifact_path", "latest_artifact_path", "recommendation", "validation", "error"],
                "error_keys": ["ok", "artifact_path", "latest_artifact_path", "recommendation", "validation", "error"],
            },
            "writeback": {
                "success_keys": ["ok", "artifact_path", "latest_artifact_path", "writeback", "validation", "error"],
                "error_keys": ["ok", "artifact_path", "latest_artifact_path", "writeback", "validation", "error"],
                "writeback_keys": [
                    "artifact_type",
                    "user_id",
                    "date",
                    "judgment_id",
                    "judgment_label",
                    "action_taken",
                    "why",
                    "written_at",
                    "request_id",
                    "requested_at",
                    "recommendation_artifact_path",
                    "recommendation_artifact_id",
                    "recommendation_evidence_refs"
                ],
            },
            "retrieval": {
                "success_keys": ["ok", "artifact_path", "retrieval", "validation", "error"],
                "error_keys": ["ok", "artifact_path", "retrieval", "validation", "error"],
                "retrieval_keys": [
                    "operation",
                    "scope",
                    "coverage_status",
                    "generated_from",
                    "evidence",
                    "important_gaps",
                    "conflicts",
                    "unsupported_claims",
                ],
            },
        },
        "proof_artifacts": {
            "human_contract": "docs/retrieval_contract_v1.md",
            "machine_contract": "artifacts/contracts/retrieval_contract_v1.json",
            "memory_write_human_contract": "docs/memory_write_contract_v1.md",
            "memory_write_machine_contract": "artifacts/contracts/memory_write_contract_v1.json",
            "day_context_proof_bundle": "artifacts/protocol_layer_proof/2026-04-11/",
            "day_nutrition_brief_proof_bundle": "artifacts/protocol_layer_proof/2026-04-11-day-nutrition-brief/",
            "sleep_review_proof_bundle": "artifacts/protocol_layer_proof/2026-04-11-sleep-review/",
            "weekly_pattern_review_proof_bundle": "artifacts/protocol_layer_proof/2026-04-11-weekly-pattern-review/",
            "recommendation_retrieval_proof_bundle": "artifacts/protocol_layer_proof/2026-04-11-recommendation-retrieval/",
            "recommendation_judgment_retrieval_proof_bundle": "artifacts/protocol_layer_proof/2026-04-11-recommendation-judgment-retrieval/",
            "recommendation_feedback_retrieval_proof_bundle": "artifacts/protocol_layer_proof/2026-04-11-recommendation-feedback/",
            "recommendation_feedback_window_retrieval_proof_bundle": "artifacts/protocol_layer_proof/2026-04-11-recommendation-feedback-window/",
            "recommendation_resolution_window_retrieval_proof_bundle": "artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-window/",
            "recommendation_creation_with_resolution_window_grounding_proof_bundle": "artifacts/protocol_layer_proof/2026-04-11-recommendation-creation-with-resolution-window-grounding/",
            "recommendation_resolution_transition_writeback_proof_bundle": "artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition-writeback/",
            "contract_describe_writeback_transition_parity_proof_bundle": "artifacts/protocol_layer_proof/2026-04-12-contract-describe-writeback-transition-parity/",
        },
    }


def _shared_arg(name: str) -> dict[str, Any]:
    return {"name": name, **SHARED_ARGS[name]}


def _retrieval_arg(name: str) -> dict[str, Any]:
    return dict(RETRIEVAL_COMMON_ARGS[name])


def _error_response(
    *,
    code: str,
    message: str,
    args: argparse.Namespace | None = None,
    argv: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "contract": None,
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
