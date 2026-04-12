from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ROOT = (
    REPO_ROOT
    / "artifacts"
    / "protocol_layer_proof"
    / "2026-04-11-recommendation-resolution-window-selective-transition"
)
SOURCE_WINDOW_ROOT = REPO_ROOT / "artifacts" / "protocol_layer_proof" / "2026-04-11-recommendation-resolution-window"

WINDOW_START = "2026-04-04"
WINDOW_END = "2026-04-10"
TARGET_DATE = "2026-04-07"
TARGET_RECOMMENDATION_FILE = "agent_recommendation_2026-04-07.json"
TARGET_JUDGMENT_FILE = "recommendation_judgment_2026-04-07.json"
TARGET_JUDGMENT_LATEST_FILE = "recommendation_judgment_latest.json"
NO_RECOMMENDATION_GAPS = ["2026-04-05", "2026-04-06", "2026-04-08", "2026-04-09"]
NEIGHBOR_DATES = ["2026-04-04", "2026-04-10"]


def _bundle_rel(*parts: str) -> str:
    return str(Path("artifacts") / "protocol_layer_proof" / "2026-04-11-recommendation-resolution-window-selective-transition" / Path(*parts))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_json(command: list[str], expected_returncode: int) -> dict:
    completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != expected_returncode:
        raise RuntimeError(
            f"unexpected return code {completed.returncode}:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    if completed.stderr.strip():
        raise RuntimeError(completed.stderr)
    return json.loads(completed.stdout)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _reset_bundle_dir() -> None:
    BUNDLE_ROOT.mkdir(parents=True, exist_ok=True)
    for path in BUNDLE_ROOT.iterdir():
        if path.is_file() or path.is_symlink():
            path.unlink()
        else:
            shutil.rmtree(path)


def _copy_recommendation(date: str) -> dict:
    filename = f"agent_recommendation_{date}.json"
    source = SOURCE_WINDOW_ROOT / filename
    target = BUNDLE_ROOT / filename
    shutil.copyfile(source, target)
    return _load_json(target)


def _copy_rewritten_neighbor_judgment(date: str) -> dict:
    filename = f"recommendation_judgment_{date}.json"
    payload = _load_json(SOURCE_WINDOW_ROOT / filename)
    payload["recommendation_artifact_path"] = _bundle_rel(f"agent_recommendation_{date}.json")
    _write_json(BUNDLE_ROOT / filename, payload)
    return payload


def _resolution_command(memory_file: str, request_id: str, requested_at: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "health_model.agent_retrieval_cli",
        "recommendation-resolution-window",
        "--user-id",
        "user_dom",
        "--start-date",
        WINDOW_START,
        "--end-date",
        WINDOW_END,
        "--memory-locator",
        _bundle_rel(memory_file),
        "--request-id",
        request_id,
        "--requested-at",
        requested_at,
        "--include-conflicts",
        "false",
        "--include-missingness",
        "true",
    ]


def _feedback_command(memory_file: str, request_id: str, requested_at: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "health_model.agent_retrieval_cli",
        "recommendation-feedback-window",
        "--user-id",
        "user_dom",
        "--start-date",
        WINDOW_START,
        "--end-date",
        WINDOW_END,
        "--memory-locator",
        _bundle_rel(memory_file),
        "--request-id",
        request_id,
        "--requested-at",
        requested_at,
    ]


def _writeback_command(payload_file: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "health_model.agent_memory_write_cli",
        "recommendation-judgment",
        "--output-dir",
        str(BUNDLE_ROOT),
        "--payload-path",
        str(BUNDLE_ROOT / payload_file),
    ]


def _index_by_date(entries: list[dict]) -> dict[str, dict]:
    return {entry["date"]: entry for entry in entries}


def _ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    _reset_bundle_dir()

    recommendations = {
        "2026-04-04": _copy_recommendation("2026-04-04"),
        TARGET_DATE: _copy_recommendation(TARGET_DATE),
        "2026-04-10": _copy_recommendation("2026-04-10"),
    }
    neighbor_judgments = {
        "2026-04-04": _copy_rewritten_neighbor_judgment("2026-04-04"),
        "2026-04-10": _copy_rewritten_neighbor_judgment("2026-04-10"),
    }

    target_recommendation_rel = _bundle_rel(TARGET_RECOMMENDATION_FILE)
    target_judgment_rel = _bundle_rel(TARGET_JUDGMENT_FILE)
    target_judgment_latest_rel = _bundle_rel(TARGET_JUDGMENT_LATEST_FILE)

    resolution_before_memory = {
        "artifact_type": "recommendation_resolution_window_memory",
        "user_id": "user_dom",
        "start_date": WINDOW_START,
        "end_date": WINDOW_END,
        "accepted_recommendations": [
            {
                "date": "2026-04-04",
                "recommendation_artifact_path": _bundle_rel("agent_recommendation_2026-04-04.json"),
                "judgment_artifact_path": _bundle_rel("recommendation_judgment_2026-04-04.json"),
            },
            {
                "date": TARGET_DATE,
                "recommendation_artifact_path": target_recommendation_rel,
            },
            {
                "date": "2026-04-10",
                "recommendation_artifact_path": _bundle_rel("agent_recommendation_2026-04-10.json"),
                "judgment_artifact_path": _bundle_rel("recommendation_judgment_2026-04-10.json"),
            },
        ],
    }
    resolution_after_memory = {
        **resolution_before_memory,
        "accepted_recommendations": [
            {
                "date": "2026-04-04",
                "recommendation_artifact_path": _bundle_rel("agent_recommendation_2026-04-04.json"),
                "judgment_artifact_path": _bundle_rel("recommendation_judgment_2026-04-04.json"),
            },
            {
                "date": TARGET_DATE,
                "recommendation_artifact_path": target_recommendation_rel,
                "judgment_artifact_path": target_judgment_rel,
            },
            {
                "date": "2026-04-10",
                "recommendation_artifact_path": _bundle_rel("agent_recommendation_2026-04-10.json"),
                "judgment_artifact_path": _bundle_rel("recommendation_judgment_2026-04-10.json"),
            },
        ],
    }
    feedback_after_memory = {
        "artifact_type": "recommendation_feedback_window_memory",
        "operation": "retrieve.recommendation_feedback_window",
        "user_id": "user_dom",
        "start_date": WINDOW_START,
        "end_date": WINDOW_END,
        "accepted_feedback_pairs": [
            {
                "date": "2026-04-04",
                "recommendation_artifact_path": _bundle_rel("agent_recommendation_2026-04-04.json"),
                "judgment_artifact_path": _bundle_rel("recommendation_judgment_2026-04-04.json"),
            },
            {
                "date": TARGET_DATE,
                "recommendation_artifact_path": target_recommendation_rel,
                "judgment_artifact_path": target_judgment_rel,
            },
            {
                "date": "2026-04-10",
                "recommendation_artifact_path": _bundle_rel("agent_recommendation_2026-04-10.json"),
                "judgment_artifact_path": _bundle_rel("recommendation_judgment_2026-04-10.json"),
            },
        ],
    }

    target_recommendation = recommendations[TARGET_DATE]
    writeback_success_request = {
        "user_id": "user_dom",
        "date": TARGET_DATE,
        "recommendation_artifact_path": target_recommendation_rel,
        "recommendation_artifact_id": target_recommendation["recommendation_id"],
        "judgment_id": "judgment_window_selective_transition_20260407_01",
        "judgment_label": "useful",
        "action_taken": "Took the lighter walking-focused day and kept the session to mobility and easy movement.",
        "why": "The pending recommendation matched the low-readiness context without changing the already-judged neighboring days.",
        "written_at": "2026-04-07T20:15:00+01:00",
        "request_id": "req_window_selective_transition_writeback_success_20260407_01",
        "requested_at": "2026-04-07T20:14:00+01:00",
        "caveat": "This frozen proof stays bounded to one selective transition inside one seven-day window.",
        "time_cost_note": "Under 10 minutes including payload review.",
        "friction_points": ["manual payload confirmation"],
    }
    writeback_rejected_request = {
        **writeback_success_request,
        "judgment_id": "judgment_window_selective_transition_rejected_20260407_01",
        "recommendation_artifact_id": "wrong_recommendation_id",
        "request_id": "req_window_selective_transition_writeback_rejected_20260407_01",
    }

    _write_json(BUNDLE_ROOT / "recommendation_resolution_window_before_memory.json", resolution_before_memory)
    _write_json(BUNDLE_ROOT / "recommendation_resolution_window_after_memory.json", resolution_after_memory)
    _write_json(BUNDLE_ROOT / "recommendation_feedback_window_after_memory.json", feedback_after_memory)
    _write_json(BUNDLE_ROOT / "writeback_success_request.json", writeback_success_request)
    _write_json(BUNDLE_ROOT / "writeback_rejected_request.json", writeback_rejected_request)

    resolution_before = _run_json(
        _resolution_command(
            "recommendation_resolution_window_before_memory.json",
            "req_window_selective_transition_resolution_before_2026_04_11",
            "2026-04-11T14:30:00+01:00",
        ),
        expected_returncode=0,
    )
    _write_json(BUNDLE_ROOT / "resolution_window_before.json", resolution_before)

    writeback_success = _run_json(_writeback_command("writeback_success_request.json"), expected_returncode=0)
    _write_json(BUNDLE_ROOT / "writeback_success_envelope.json", writeback_success)

    resolution_after = _run_json(
        _resolution_command(
            "recommendation_resolution_window_after_memory.json",
            "req_window_selective_transition_resolution_after_2026_04_11",
            "2026-04-11T14:32:00+01:00",
        ),
        expected_returncode=0,
    )
    _write_json(BUNDLE_ROOT / "resolution_window_after.json", resolution_after)

    feedback_after = _run_json(
        _feedback_command(
            "recommendation_feedback_window_after_memory.json",
            "req_window_selective_transition_feedback_after_2026_04_11",
            "2026-04-11T14:33:00+01:00",
        ),
        expected_returncode=0,
    )
    _write_json(BUNDLE_ROOT / "feedback_window_after.json", feedback_after)

    before_evidence = resolution_before["retrieval"]["evidence"]
    after_evidence = resolution_after["retrieval"]["evidence"]
    before_by_date = _index_by_date(before_evidence["per_recommendation"])
    after_by_date = _index_by_date(after_evidence["per_recommendation"])

    _ensure(before_evidence["recommendation_items"] == 3, "before state must contain exactly three recommendation items")
    _ensure(before_evidence["judged_items"] == 2, "before state must contain exactly two judged items")
    _ensure(before_evidence["pending_judgment_items"] == 1, "before state must contain exactly one pending item")
    _ensure(after_evidence["judged_items"] == 3, "after state must contain exactly three judged items")
    _ensure(after_evidence["pending_judgment_items"] == 0, "after state must contain zero pending items")
    _ensure(before_by_date[TARGET_DATE]["resolution_status"] == "pending_judgment", "target must start pending")
    _ensure(after_by_date[TARGET_DATE]["resolution_status"] == "judged", "target must end judged")

    target_before = before_by_date[TARGET_DATE]
    target_after = after_by_date[TARGET_DATE]
    changed_dates = [
        date
        for date in sorted(before_by_date)
        if before_by_date[date] != after_by_date[date]
    ]

    gap_dates_before = [gap["date"] for gap in resolution_before["retrieval"]["important_gaps"]]
    gap_dates_after = [gap["date"] for gap in resolution_after["retrieval"]["important_gaps"]]
    _ensure(gap_dates_before == NO_RECOMMENDATION_GAPS, "before-state no-recommendation gaps must match the bounded fixture")
    _ensure(gap_dates_after == NO_RECOMMENDATION_GAPS, "after-state no-recommendation gaps must remain unchanged")

    neighbor_stability_proof = {
        "proof": "selective_transition_mutates_only_target_pending_recommendation",
        "window": {
            "start_date": WINDOW_START,
            "end_date": WINDOW_END,
        },
        "target": {
            "date": TARGET_DATE,
            "recommendation_id": target_recommendation["recommendation_id"],
            "recommendation_artifact_path": target_recommendation_rel,
            "before_resolution_status": target_before["resolution_status"],
            "after_resolution_status": target_after["resolution_status"],
            "after_judgment_artifact_path": target_judgment_rel,
            "after_judgment_id": target_after["judgment"]["judgment_id"],
        },
        "before_counts": {
            "recommendation_items": before_evidence["recommendation_items"],
            "judged_items": before_evidence["judged_items"],
            "pending_judgment_items": before_evidence["pending_judgment_items"],
        },
        "after_counts": {
            "recommendation_items": after_evidence["recommendation_items"],
            "judged_items": after_evidence["judged_items"],
            "pending_judgment_items": after_evidence["pending_judgment_items"],
        },
        "changed_dates": changed_dates,
        "only_target_date_changed": changed_dates == [TARGET_DATE],
        "neighbor_entries": [],
        "no_recommendation_gaps": {
            "before": gap_dates_before,
            "after": gap_dates_after,
            "unchanged": gap_dates_before == gap_dates_after == NO_RECOMMENDATION_GAPS,
        },
        "cross_step_linkage": {
            "resolution_before_request_id": resolution_before["validation"]["request_echo"]["request_id"],
            "writeback_success_request_id": writeback_success["validation"]["request_echo"]["request_id"],
            "resolution_after_request_id": resolution_after["validation"]["request_echo"]["request_id"],
            "feedback_after_request_id": feedback_after["validation"]["request_echo"]["request_id"],
            "target_judgment_artifact_path": target_judgment_rel,
        },
    }

    for date in NEIGHBOR_DATES:
        before_entry = before_by_date[date]
        after_entry = after_by_date[date]
        expected_judgment = neighbor_judgments[date]
        neighbor_proof = {
            "date": date,
            "recommendation_id": before_entry["recommendation"]["recommendation_id"],
            "before_resolution_status": before_entry["resolution_status"],
            "after_resolution_status": after_entry["resolution_status"],
            "recommendation_stable": before_entry["recommendation"] == after_entry["recommendation"],
            "judgment_stable": before_entry["judgment"] == after_entry["judgment"],
            "judgment_artifact_path_matches_bundle": (
                before_entry["judgment"]["recommendation_artifact_path"]
                == after_entry["judgment"]["recommendation_artifact_path"]
                == expected_judgment["recommendation_artifact_path"]
            ),
            "linkage_stable": before_entry["linkage"] == after_entry["linkage"],
            "entry_stable": before_entry == after_entry,
        }
        neighbor_stability_proof["neighbor_entries"].append(neighbor_proof)
        _ensure(neighbor_proof["entry_stable"], f"neighbor entry {date} must remain unchanged")

    _ensure(neighbor_stability_proof["only_target_date_changed"], "only the target recommendation date may change")

    feedback_evidence = feedback_after["retrieval"]["evidence"]
    feedback_by_date = _index_by_date(feedback_evidence["per_day"])
    _ensure(feedback_evidence["days_with_feedback"] == 3, "feedback window must show three linked feedback pairs after writeback")
    _ensure(sorted(feedback_by_date) == ["2026-04-04", TARGET_DATE, "2026-04-10"], "feedback window must contain the full linked trio")
    _ensure(
        feedback_by_date[TARGET_DATE]["judgment"]["recommendation_artifact_id"] == target_recommendation["recommendation_id"],
        "feedback target judgment must point to the target recommendation id",
    )
    _ensure(
        feedback_by_date[TARGET_DATE]["linkage"]["supplied_recommendation_artifact_path"] == target_recommendation_rel,
        "feedback target linkage must point to the target recommendation path",
    )
    _ensure(
        [gap["date"] for gap in feedback_after["retrieval"]["important_gaps"]] == NO_RECOMMENDATION_GAPS,
        "feedback gaps must remain unchanged after writeback",
    )
    neighbor_stability_proof["feedback_linkage_truth"] = {
        "days_with_feedback": feedback_evidence["days_with_feedback"],
        "target_feedback_date": TARGET_DATE,
        "target_recommendation_id": feedback_by_date[TARGET_DATE]["recommendation"]["recommendation_id"],
        "target_judgment_id": feedback_by_date[TARGET_DATE]["judgment"]["judgment_id"],
        "target_judgment_artifact_path_matches": (
            feedback_after["retrieval"]["generated_from"]["accepted_feedback_pairs"][1]["judgment_artifact_path"] == target_judgment_rel
        ),
        "feedback_gap_dates": [gap["date"] for gap in feedback_after["retrieval"]["important_gaps"]],
    }
    _write_json(BUNDLE_ROOT / "neighbor_stability_proof.json", neighbor_stability_proof)

    dated_path = BUNDLE_ROOT / TARGET_JUDGMENT_FILE
    latest_path = BUNDLE_ROOT / TARGET_JUDGMENT_LATEST_FILE
    before_rejection = {
        "dated_artifact_path": target_judgment_rel,
        "latest_artifact_path": target_judgment_latest_rel,
        "dated_bytes": len(dated_path.read_bytes()),
        "dated_sha256": _sha256(dated_path),
        "latest_bytes": len(latest_path.read_bytes()),
        "latest_sha256": _sha256(latest_path),
    }

    writeback_rejected = _run_json(_writeback_command("writeback_rejected_request.json"), expected_returncode=1)
    _write_json(BUNDLE_ROOT / "writeback_rejected_envelope.json", writeback_rejected)

    after_rejection = {
        "dated_bytes": len(dated_path.read_bytes()),
        "dated_sha256": _sha256(dated_path),
        "latest_bytes": len(latest_path.read_bytes()),
        "latest_sha256": _sha256(latest_path),
    }
    non_mutation_proof = {
        "proof": "rejected_writeback_does_not_mutate_selective_transition_artifacts",
        "request_id": writeback_rejected["validation"]["request_echo"]["request_id"],
        "error_code": writeback_rejected["error"]["code"],
        "artifact_state_before_rejection": before_rejection,
        "artifact_state_after_rejection": after_rejection,
        "dated_artifact_unchanged": before_rejection["dated_sha256"] == after_rejection["dated_sha256"],
        "latest_artifact_unchanged": before_rejection["latest_sha256"] == after_rejection["latest_sha256"],
    }
    _ensure(non_mutation_proof["dated_artifact_unchanged"], "rejected writeback must not mutate the dated target judgment")
    _ensure(non_mutation_proof["latest_artifact_unchanged"], "rejected writeback must not mutate the latest target judgment")
    _write_json(BUNDLE_ROOT / "non_mutation_proof.json", non_mutation_proof)

    linkage_summary = {
        "window_start_date": WINDOW_START,
        "window_end_date": WINDOW_END,
        "target_recommendation_date": TARGET_DATE,
        "target_recommendation_id": target_recommendation["recommendation_id"],
        "target_recommendation_artifact_path": target_recommendation_rel,
        "target_judgment_artifact_path": target_judgment_rel,
        "neighbor_dates": NEIGHBOR_DATES,
        "gap_dates": NO_RECOMMENDATION_GAPS,
        "cross_step_requests": {
            "resolution_before": resolution_before["validation"]["request_echo"]["request_id"],
            "writeback_success": writeback_success["validation"]["request_echo"]["request_id"],
            "resolution_after": resolution_after["validation"]["request_echo"]["request_id"],
            "feedback_after": feedback_after["validation"]["request_echo"]["request_id"],
            "writeback_rejected": writeback_rejected["validation"]["request_echo"]["request_id"],
        },
    }
    _write_json(BUNDLE_ROOT / "linkage_summary.json", linkage_summary)

    manifest = {
        "date": "2026-04-11",
        "slice": "protocol_proof.recommendation_resolution_window_selective_transition",
        "frozen_command": "python3 scripts/run_recommendation_resolution_window_selective_transition_proof.py",
        "inputs": [
            "agent_recommendation_2026-04-04.json",
            "agent_recommendation_2026-04-07.json",
            "agent_recommendation_2026-04-10.json",
            "recommendation_judgment_2026-04-04.json",
            "recommendation_judgment_2026-04-10.json",
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
            "neighbor_stability_proof.json",
            "writeback_rejected_envelope.json",
            "non_mutation_proof.json",
            "linkage_summary.json",
        ],
        "cross_step_linkage_references": {
            "target_recommendation_id": target_recommendation["recommendation_id"],
            "target_recommendation_artifact_path": target_recommendation_rel,
            "target_judgment_artifact_path": target_judgment_rel,
            "resolution_before_output": "resolution_window_before.json",
            "writeback_success_output": "writeback_success_envelope.json",
            "resolution_after_output": "resolution_window_after.json",
            "feedback_after_output": "feedback_window_after.json",
            "neighbor_stability_output": "neighbor_stability_proof.json",
            "non_mutation_output": "non_mutation_proof.json",
            "linkage_summary_output": "linkage_summary.json",
        },
        "deterministic_replay_commands": [
            "python3 scripts/run_recommendation_resolution_window_selective_transition_proof.py",
            "python3 -m health_model.agent_retrieval_cli recommendation-resolution-window --user-id user_dom --start-date 2026-04-04 --end-date 2026-04-10 --memory-locator artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-window-selective-transition/recommendation_resolution_window_before_memory.json --request-id req_window_selective_transition_resolution_before_2026_04_11 --requested-at 2026-04-11T14:30:00+01:00 --include-conflicts false --include-missingness true",
            "python3 -m health_model.agent_memory_write_cli recommendation-judgment --output-dir artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-window-selective-transition --payload-path artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-window-selective-transition/writeback_success_request.json",
            "python3 -m health_model.agent_retrieval_cli recommendation-resolution-window --user-id user_dom --start-date 2026-04-04 --end-date 2026-04-10 --memory-locator artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-window-selective-transition/recommendation_resolution_window_after_memory.json --request-id req_window_selective_transition_resolution_after_2026_04_11 --requested-at 2026-04-11T14:32:00+01:00 --include-conflicts false --include-missingness true",
            "python3 -m health_model.agent_retrieval_cli recommendation-feedback-window --user-id user_dom --start-date 2026-04-04 --end-date 2026-04-10 --memory-locator artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-window-selective-transition/recommendation_feedback_window_after_memory.json --request-id req_window_selective_transition_feedback_after_2026_04_11 --requested-at 2026-04-11T14:33:00+01:00",
            "python3 -m health_model.agent_memory_write_cli recommendation-judgment --output-dir artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-window-selective-transition --payload-path artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-window-selective-transition/writeback_rejected_request.json",
        ],
        "deterministic_replay_tests": [
            "python3 -m unittest tests.test_agent_retrieval_cli tests.test_agent_memory_write_cli tests.test_agent_contract_cli",
        ],
        "smoke_checks": [
            "pre-write window contains target pending item, neighboring judged items, and explicit no-recommendation gaps",
            "successful writeback succeeds via writeback.recommendation_judgment for the 2026-04-07 target only",
            "post-write resolution shows only the target transition from pending_judgment to judged",
            "neighbor_stability_proof shows 2026-04-04 and 2026-04-10 judged entries unchanged",
            "neighbor_stability_proof shows 2026-04-05, 2026-04-06, 2026-04-08, and 2026-04-09 remain explicit no-recommendation gaps",
            "post-write feedback truthfully returns the linked 2026-04-04, 2026-04-07, and 2026-04-10 recommendation/judgment pairs",
            "rejected writeback returns ok=false with code=recommendation_artifact_id_mismatch and non_mutation_proof confirms no further artifact mutation",
            "deterministic replay commands and tests are frozen in this manifest",
        ],
    }
    _write_json(BUNDLE_ROOT / "proof_manifest.json", manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
