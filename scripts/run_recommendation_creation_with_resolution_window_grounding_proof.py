from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ROOT = REPO_ROOT / "artifacts" / "protocol_layer_proof" / "2026-04-11-recommendation-creation-with-resolution-window-grounding"
SOURCE_WINDOW = REPO_ROOT / "artifacts" / "protocol_layer_proof" / "2026-04-11-recommendation-resolution-window" / "success_envelope.json"
SOURCE_CONTEXT = REPO_ROOT / "tests" / "fixtures" / "agent_readable_daily_context" / "generated_fixture_day_context.json"


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_json(command: list[str], expected_returncode: int) -> dict:
    completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != expected_returncode:
        raise RuntimeError(f"unexpected return code {completed.returncode}:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    if completed.stderr.strip():
        raise RuntimeError(completed.stderr)
    return json.loads(completed.stdout)


def _reset_bundle_dir() -> None:
    BUNDLE_ROOT.mkdir(parents=True, exist_ok=True)
    for path in BUNDLE_ROOT.iterdir():
        if path.is_file() or path.is_symlink():
            path.unlink()
        else:
            shutil.rmtree(path)


def _success_payload(context_path: Path, window_path: Path) -> dict:
    return {
        "user_id": "user_dom",
        "date": "2026-04-11",
        "context_artifact_path": str(context_path),
        "context_artifact_id": "agent_context_user_dom_2026-04-11",
        "resolution_window_artifact_path": str(window_path),
        "recommendation_id": "rec_20260411_recovery_01",
        "summary": "Keep today light and prioritize recovery basics.",
        "rationale": "Same-day low-energy context plus the recent window show repeated useful lower-load guidance.",
        "evidence_refs": ["subjective_voice_20260409", "manual_gym_session_20260409"],
        "confidence_score": 0.82,
        "policy_basis": {
            "window_dates_considered": ["2026-04-04", "2026-04-10"],
            "prior_recommendation_refs": [
                {
                    "recommendation_id": "rec_window_20260407_walk_01",
                    "date": "2026-04-07",
                    "resolution_status": "pending_judgment",
                }
            ],
            "policy_note": "Carry forward the recent lower-load pattern without introducing hidden memory.",
        },
    }


def main() -> int:
    _reset_bundle_dir()

    context = _load_json(SOURCE_CONTEXT)
    context["user_id"] = "user_dom"
    context["date"] = "2026-04-11"
    context["context_id"] = "agent_context_user_dom_2026-04-11"
    context_path = BUNDLE_ROOT / "agent_readable_daily_context_2026-04-11.json"
    _write_json(context_path, context)

    window_path = BUNDLE_ROOT / "resolution_window_success.json"
    shutil.copyfile(SOURCE_WINDOW, window_path)

    success_payload = _success_payload(context_path=context_path, window_path=window_path)
    success_payload_path = BUNDLE_ROOT / "recommendation_create_success_payload.json"
    _write_json(success_payload_path, success_payload)

    success_envelope = _run_json(
        [sys.executable, "-m", "health_model.agent_recommendation_cli", "create", "--output-dir", str(BUNDLE_ROOT), "--payload-path", str(success_payload_path)],
        expected_returncode=0,
    )
    _write_json(BUNDLE_ROOT / "success_envelope.json", success_envelope)

    missing_window_payload = dict(success_payload)
    missing_window_payload["resolution_window_artifact_path"] = str(BUNDLE_ROOT / "missing_window.json")
    missing_window_payload_path = BUNDLE_ROOT / "recommendation_create_missing_window_payload.json"
    _write_json(missing_window_payload_path, missing_window_payload)
    missing_window_envelope = _run_json(
        [sys.executable, "-m", "health_model.agent_recommendation_cli", "create", "--output-dir", str(BUNDLE_ROOT), "--payload-path", str(missing_window_payload_path)],
        expected_returncode=1,
    )
    _write_json(BUNDLE_ROOT / "fail_missing_window_envelope.json", missing_window_envelope)

    inconsistent_payload = json.loads(json.dumps(success_payload))
    inconsistent_payload["policy_basis"]["prior_recommendation_refs"][0]["resolution_status"] = "judged"
    inconsistent_payload_path = BUNDLE_ROOT / "recommendation_create_inconsistent_policy_payload.json"
    _write_json(inconsistent_payload_path, inconsistent_payload)

    before_rejection = {
        "dated_artifact_path": str(BUNDLE_ROOT / "agent_recommendation_2026-04-11.json"),
        "latest_artifact_path": str(BUNDLE_ROOT / "agent_recommendation_latest.json"),
        "dated_sha256": _sha256(BUNDLE_ROOT / "agent_recommendation_2026-04-11.json"),
        "latest_sha256": _sha256(BUNDLE_ROOT / "agent_recommendation_latest.json"),
    }
    _write_json(BUNDLE_ROOT / "non_mutation_before_rejection.json", before_rejection)

    inconsistent_envelope = _run_json(
        [sys.executable, "-m", "health_model.agent_recommendation_cli", "create", "--output-dir", str(BUNDLE_ROOT), "--payload-path", str(inconsistent_payload_path)],
        expected_returncode=1,
    )
    _write_json(BUNDLE_ROOT / "fail_inconsistent_policy_basis_envelope.json", inconsistent_envelope)

    after_rejection = {
        "dated_artifact_path": str(BUNDLE_ROOT / "agent_recommendation_2026-04-11.json"),
        "latest_artifact_path": str(BUNDLE_ROOT / "agent_recommendation_latest.json"),
        "dated_sha256": _sha256(BUNDLE_ROOT / "agent_recommendation_2026-04-11.json"),
        "latest_sha256": _sha256(BUNDLE_ROOT / "agent_recommendation_latest.json"),
    }
    _write_json(BUNDLE_ROOT / "non_mutation_after_rejection.json", after_rejection)
    _write_json(
        BUNDLE_ROOT / "non_mutation_proof.json",
        {
            "ok": before_rejection == after_rejection,
            "before": before_rejection,
            "after": after_rejection,
        },
    )

    manifest = {
        "slice": "protocol_proof.recommendation_creation_with_resolution_window_grounding",
        "frozen_command": "python3 scripts/run_recommendation_creation_with_resolution_window_grounding_proof.py",
        "replay_commands": [
            "python3 scripts/run_recommendation_creation_with_resolution_window_grounding_proof.py",
            "python3 -m unittest tests.test_agent_recommendation_cli tests.test_agent_contract_cli",
            f"python3 -m health_model.agent_recommendation_cli create --output-dir {BUNDLE_ROOT} --payload-path {success_payload_path}",
            f"python3 -m health_model.agent_recommendation_cli create --output-dir {BUNDLE_ROOT} --payload-path {missing_window_payload_path}",
            f"python3 -m health_model.agent_recommendation_cli create --output-dir {BUNDLE_ROOT} --payload-path {inconsistent_payload_path}",
        ],
        "artifacts": [
            "agent_readable_daily_context_2026-04-11.json",
            "resolution_window_success.json",
            "recommendation_create_success_payload.json",
            "success_envelope.json",
            "recommendation_create_missing_window_payload.json",
            "fail_missing_window_envelope.json",
            "recommendation_create_inconsistent_policy_payload.json",
            "fail_inconsistent_policy_basis_envelope.json",
            "non_mutation_before_rejection.json",
            "non_mutation_after_rejection.json",
            "non_mutation_proof.json",
        ],
        "smoke_checks": [
            "success artifact includes same-day context linkage and resolution-window linkage",
            "missing resolution-window input fails closed inspectably",
            "inconsistent policy basis fails closed inspectably",
            "rejected create is non-mutating",
        ],
    }
    _write_json(BUNDLE_ROOT / "proof_manifest.json", manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
