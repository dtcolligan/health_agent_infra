from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ROOT = REPO_ROOT / "artifacts" / "protocol_layer_proof" / "2026-04-11-recommendation-resolution-transition"
SOURCE_RECOMMENDATION = REPO_ROOT / "artifacts" / "protocol_layer_proof" / "2026-04-11-recommendation-resolution-window" / "agent_recommendation_2026-04-07.json"
TARGET_RECOMMENDATION_REL = "artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition/agent_recommendation_2026-04-07.json"
TARGET_JUDGMENT_REL = "artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition/recommendation_judgment_2026-04-07.json"
TARGET_JUDGMENT_LATEST_REL = "artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition/recommendation_judgment_latest.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_json(command: list[str], expected_returncode: int) -> dict:
    completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != expected_returncode:
        raise RuntimeError(f"unexpected return code {completed.returncode}:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    if completed.stderr.strip():
        raise RuntimeError(completed.stderr)
    return json.loads(completed.stdout)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> int:
    BUNDLE_ROOT.mkdir(parents=True, exist_ok=True)
    for path in BUNDLE_ROOT.iterdir():
        if path.is_file() or path.is_symlink():
            path.unlink()
        else:
            shutil.rmtree(path)

    shutil.copyfile(SOURCE_RECOMMENDATION, BUNDLE_ROOT / "agent_recommendation_2026-04-07.json")
    recommendation = json.loads((BUNDLE_ROOT / "agent_recommendation_2026-04-07.json").read_text())

    resolution_before_locator = {
        "artifact_type": "recommendation_resolution_window_memory",
        "user_id": "user_dom",
        "start_date": "2026-04-04",
        "end_date": "2026-04-10",
        "accepted_recommendations": [
            {
                "date": "2026-04-07",
                "recommendation_artifact_path": TARGET_RECOMMENDATION_REL,
            }
        ],
    }
    resolution_after_locator = {
        **resolution_before_locator,
        "accepted_recommendations": [
            {
                "date": "2026-04-07",
                "recommendation_artifact_path": TARGET_RECOMMENDATION_REL,
                "judgment_artifact_path": TARGET_JUDGMENT_REL,
            }
        ],
    }
    feedback_after_locator = {
        "artifact_type": "recommendation_feedback_window_memory",
        "operation": "retrieve.recommendation_feedback_window",
        "user_id": "user_dom",
        "start_date": "2026-04-04",
        "end_date": "2026-04-10",
        "accepted_feedback_pairs": [
            {
                "date": "2026-04-07",
                "recommendation_artifact_path": TARGET_RECOMMENDATION_REL,
                "judgment_artifact_path": TARGET_JUDGMENT_REL,
            }
        ],
    }
    success_payload = {
        "user_id": "user_dom",
        "date": "2026-04-07",
        "recommendation_artifact_path": TARGET_RECOMMENDATION_REL,
        "recommendation_artifact_id": recommendation["recommendation_id"],
        "judgment_id": "judgment_transition_20260407_01",
        "judgment_label": "useful",
        "action_taken": "Took the lighter walking-focused day and skipped higher intensity work.",
        "why": "The recommendation matched the low-readiness context and was easy to apply the same day.",
        "written_at": "2026-04-07T20:15:00+01:00",
        "request_id": "req_transition_writeback_success_20260407_01",
        "requested_at": "2026-04-07T20:14:00+01:00",
        "caveat": "This proof slice is intentionally limited to one same-day judgment transition.",
        "time_cost_note": "Under 10 minutes including payload review.",
        "friction_points": ["manual payload confirmation"]
    }
    rejected_payload = {
        **success_payload,
        "judgment_id": "judgment_transition_rejected_20260407_01",
        "recommendation_artifact_id": "wrong_recommendation_id",
        "request_id": "req_transition_writeback_rejected_20260407_01",
    }

    _write_json(BUNDLE_ROOT / "recommendation_resolution_window_before_memory.json", resolution_before_locator)
    _write_json(BUNDLE_ROOT / "recommendation_resolution_window_after_memory.json", resolution_after_locator)
    _write_json(BUNDLE_ROOT / "recommendation_feedback_window_after_memory.json", feedback_after_locator)
    _write_json(BUNDLE_ROOT / "writeback_success_request.json", success_payload)
    _write_json(BUNDLE_ROOT / "writeback_rejected_request.json", rejected_payload)

    resolution_before = _run_json(
        [
            sys.executable,
            "-m",
            "health_model.agent_retrieval_cli",
            "recommendation-resolution-window",
            "--user-id",
            "user_dom",
            "--start-date",
            "2026-04-04",
            "--end-date",
            "2026-04-10",
            "--memory-locator",
            str((BUNDLE_ROOT / "recommendation_resolution_window_before_memory.json").relative_to(REPO_ROOT)),
            "--request-id",
            "req_transition_resolution_before_2026_04_11",
            "--requested-at",
            "2026-04-11T14:10:00+01:00",
            "--include-conflicts",
            "false",
            "--include-missingness",
            "true",
        ],
        expected_returncode=0,
    )
    _write_json(BUNDLE_ROOT / "resolution_window_before.json", resolution_before)

    writeback_success = _run_json(
        [
            sys.executable,
            "-m",
            "health_model.agent_memory_write_cli",
            "recommendation-judgment",
            "--output-dir",
            str(BUNDLE_ROOT),
            "--payload-path",
            str(BUNDLE_ROOT / "writeback_success_request.json"),
        ],
        expected_returncode=0,
    )
    _write_json(BUNDLE_ROOT / "writeback_success_envelope.json", writeback_success)

    resolution_after = _run_json(
        [
            sys.executable,
            "-m",
            "health_model.agent_retrieval_cli",
            "recommendation-resolution-window",
            "--user-id",
            "user_dom",
            "--start-date",
            "2026-04-04",
            "--end-date",
            "2026-04-10",
            "--memory-locator",
            str((BUNDLE_ROOT / "recommendation_resolution_window_after_memory.json").relative_to(REPO_ROOT)),
            "--request-id",
            "req_transition_resolution_after_2026_04_11",
            "--requested-at",
            "2026-04-11T14:12:00+01:00",
            "--include-conflicts",
            "false",
            "--include-missingness",
            "true",
        ],
        expected_returncode=0,
    )
    _write_json(BUNDLE_ROOT / "resolution_window_after.json", resolution_after)

    feedback_after = _run_json(
        [
            sys.executable,
            "-m",
            "health_model.agent_retrieval_cli",
            "recommendation-feedback-window",
            "--user-id",
            "user_dom",
            "--start-date",
            "2026-04-04",
            "--end-date",
            "2026-04-10",
            "--memory-locator",
            str((BUNDLE_ROOT / "recommendation_feedback_window_after_memory.json").relative_to(REPO_ROOT)),
            "--request-id",
            "req_transition_feedback_after_2026_04_11",
            "--requested-at",
            "2026-04-11T14:13:00+01:00",
        ],
        expected_returncode=0,
    )
    _write_json(BUNDLE_ROOT / "feedback_window_after.json", feedback_after)

    dated_path = BUNDLE_ROOT / "recommendation_judgment_2026-04-07.json"
    latest_path = BUNDLE_ROOT / "recommendation_judgment_latest.json"
    before_rejection = {
        "dated_artifact_path": TARGET_JUDGMENT_REL,
        "latest_artifact_path": TARGET_JUDGMENT_LATEST_REL,
        "dated_sha256": _sha256(dated_path),
        "latest_sha256": _sha256(latest_path),
        "dated_bytes": len(dated_path.read_bytes()),
        "latest_bytes": len(latest_path.read_bytes()),
    }

    writeback_rejected = _run_json(
        [
            sys.executable,
            "-m",
            "health_model.agent_memory_write_cli",
            "recommendation-judgment",
            "--output-dir",
            str(BUNDLE_ROOT),
            "--payload-path",
            str(BUNDLE_ROOT / "writeback_rejected_request.json"),
        ],
        expected_returncode=1,
    )
    _write_json(BUNDLE_ROOT / "writeback_rejected_envelope.json", writeback_rejected)

    after_rejection = {
        "dated_sha256": _sha256(dated_path),
        "latest_sha256": _sha256(latest_path),
        "dated_bytes": len(dated_path.read_bytes()),
        "latest_bytes": len(latest_path.read_bytes()),
    }
    non_mutation_proof = {
        "proof": "rejected_writeback_does_not_mutate_successful_transition_artifacts",
        "request_id": writeback_rejected["validation"]["request_echo"]["request_id"],
        "error_code": writeback_rejected["error"]["code"],
        "artifact_state_before_rejection": before_rejection,
        "artifact_state_after_rejection": after_rejection,
        "dated_artifact_unchanged": before_rejection["dated_sha256"] == after_rejection["dated_sha256"],
        "latest_artifact_unchanged": before_rejection["latest_sha256"] == after_rejection["latest_sha256"],
    }
    _write_json(BUNDLE_ROOT / "non_mutation_proof.json", non_mutation_proof)

    linkage_summary = {
        "target_recommendation_date": "2026-04-07",
        "recommendation_artifact_path": TARGET_RECOMMENDATION_REL,
        "recommendation_id": recommendation["recommendation_id"],
        "before_resolution_request_id": resolution_before["validation"]["request_echo"]["request_id"],
        "successful_writeback_request_id": writeback_success["validation"]["request_echo"]["request_id"],
        "written_judgment_artifact_path": TARGET_JUDGMENT_REL,
        "after_resolution_request_id": resolution_after["validation"]["request_echo"]["request_id"],
        "after_feedback_request_id": feedback_after["validation"]["request_echo"]["request_id"],
        "rejected_writeback_request_id": writeback_rejected["validation"]["request_echo"]["request_id"],
    }
    _write_json(BUNDLE_ROOT / "linkage_summary.json", linkage_summary)

    manifest = {
        "date": "2026-04-11",
        "slice": "protocol_proof.recommendation_resolution_transition",
        "frozen_command": "python3 scripts/run_recommendation_resolution_transition_proof.py",
        "inputs": [
            "agent_recommendation_2026-04-07.json",
            "recommendation_resolution_window_before_memory.json",
            "recommendation_resolution_window_after_memory.json",
            "recommendation_feedback_window_after_memory.json",
            "writeback_success_request.json",
            "writeback_rejected_request.json",
        ],
        "outputs": [
            "resolution_window_before.json",
            "writeback_success_envelope.json",
            "recommendation_judgment_2026-04-07.json",
            "recommendation_judgment_latest.json",
            "resolution_window_after.json",
            "feedback_window_after.json",
            "writeback_rejected_envelope.json",
            "non_mutation_proof.json",
            "linkage_summary.json",
        ],
        "deterministic_replay_commands": [
            "python3 scripts/run_recommendation_resolution_transition_proof.py",
            "python3 -m health_model.agent_retrieval_cli recommendation-resolution-window --user-id user_dom --start-date 2026-04-04 --end-date 2026-04-10 --memory-locator artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition/recommendation_resolution_window_before_memory.json --request-id req_transition_resolution_before_2026_04_11 --requested-at 2026-04-11T14:10:00+01:00 --include-conflicts false --include-missingness true",
            "python3 -m health_model.agent_memory_write_cli recommendation-judgment --output-dir artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition --payload-path artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition/writeback_success_request.json",
            "python3 -m health_model.agent_retrieval_cli recommendation-resolution-window --user-id user_dom --start-date 2026-04-04 --end-date 2026-04-10 --memory-locator artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition/recommendation_resolution_window_after_memory.json --request-id req_transition_resolution_after_2026_04_11 --requested-at 2026-04-11T14:12:00+01:00 --include-conflicts false --include-missingness true",
            "python3 -m health_model.agent_retrieval_cli recommendation-feedback-window --user-id user_dom --start-date 2026-04-04 --end-date 2026-04-10 --memory-locator artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition/recommendation_feedback_window_after_memory.json --request-id req_transition_feedback_after_2026_04_11 --requested-at 2026-04-11T14:13:00+01:00",
            "python3 -m health_model.agent_memory_write_cli recommendation-judgment --output-dir artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition --payload-path artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition/writeback_rejected_request.json"
        ],
        "smoke_checks": [
            "before-state shows pending_judgment for 2026-04-07",
            "successful writeback returns ok=true and writes recommendation_judgment_2026-04-07.json",
            "post-write resolution reclassifies 2026-04-07 as judged",
            "post-write feedback returns the same linked recommendation plus judgment pair",
            "rejected writeback returns ok=false with code=recommendation_artifact_id_mismatch",
            "non_mutation_proof shows dated and latest judgment artifacts unchanged after rejection"
        ],
    }
    _write_json(BUNDLE_ROOT / "proof_manifest.json", manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
