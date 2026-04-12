from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_CONTEXT = REPO_ROOT / "tests" / "fixtures" / "agent_readable_daily_context" / "generated_fixture_day_context.json"
OUTPUT_ROOT = REPO_ROOT / "artifacts" / "flagship_loop_proof" / "2026-04-09"
PAYLOAD_DIR = REPO_ROOT / "artifacts" / "flagship_loop_proof" / "payloads"
POSITIVE_PAYLOAD_PATH = PAYLOAD_DIR / "recommendation_positive_payload_2026-04-09.json"
NEGATIVE_PAYLOAD_PATH = PAYLOAD_DIR / "recommendation_negative_payload_2026-04-09.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_cli(*args: str, expected_returncode: int) -> dict:
    completed = subprocess.run(
        [sys.executable, "-m", "health_model.agent_recommendation_cli", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != expected_returncode:
        raise RuntimeError(completed.stderr or completed.stdout)
    if completed.stderr.strip():
        raise RuntimeError(completed.stderr)
    return json.loads(completed.stdout)


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for path in OUTPUT_ROOT.iterdir():
        if path.is_file() or path.is_symlink():
            path.unlink()
        else:
            shutil.rmtree(path)

    shutil.copyfile(FIXTURE_CONTEXT, OUTPUT_ROOT / "agent_readable_daily_context_2026-04-09.json")

    positive_result = _run_cli(
        "create",
        "--output-dir",
        str(OUTPUT_ROOT),
        "--payload-path",
        str(POSITIVE_PAYLOAD_PATH),
        expected_returncode=0,
    )

    dated_path = Path(positive_result["artifact_path"])
    latest_path = Path(positive_result["latest_artifact_path"])
    before = {
        "dated_path": str(dated_path.relative_to(REPO_ROOT)),
        "latest_path": str(latest_path.relative_to(REPO_ROOT)),
        "dated_sha256": _sha256(dated_path),
        "latest_sha256": _sha256(latest_path),
        "dated_bytes": dated_path.read_bytes().__len__(),
        "latest_bytes": latest_path.read_bytes().__len__(),
    }

    negative_result = _run_cli(
        "create",
        "--output-dir",
        str(OUTPUT_ROOT),
        "--payload-path",
        str(NEGATIVE_PAYLOAD_PATH),
        expected_returncode=1,
    )

    after = {
        "dated_sha256": _sha256(dated_path),
        "latest_sha256": _sha256(latest_path),
        "dated_bytes": dated_path.read_bytes().__len__(),
        "latest_bytes": latest_path.read_bytes().__len__(),
    }

    preservation = {
        "proof": "negative_case_preserves_preexisting_recommendation_artifacts",
        "negative_payload_path": str(NEGATIVE_PAYLOAD_PATH.relative_to(REPO_ROOT)),
        "negative_error_code": negative_result["error"]["code"],
        "negative_ok": negative_result["ok"],
        "artifact_state_before": before,
        "artifact_state_after": after,
        "byte_identical_preserved": before["dated_sha256"] == after["dated_sha256"] and before["latest_sha256"] == after["latest_sha256"],
    }

    (OUTPUT_ROOT / "positive_result.json").write_text(json.dumps(positive_result, indent=2, sort_keys=True) + "\n")
    (OUTPUT_ROOT / "negative_fail_closed_result.json").write_text(json.dumps(negative_result, indent=2, sort_keys=True) + "\n")
    (OUTPUT_ROOT / "negative_artifact_state_preservation.json").write_text(json.dumps(preservation, indent=2, sort_keys=True) + "\n")

    manifest = {
        "frozen_command": "python3 scripts/run_flagship_loop_proof_audit.py",
        "fixture_context_path": str(FIXTURE_CONTEXT.relative_to(REPO_ROOT)),
        "positive_payload_path": str(POSITIVE_PAYLOAD_PATH.relative_to(REPO_ROOT)),
        "negative_payload_path": str(NEGATIVE_PAYLOAD_PATH.relative_to(REPO_ROOT)),
        "produced_artifacts": [
            "artifacts/flagship_loop_proof/2026-04-09/agent_readable_daily_context_2026-04-09.json",
            "artifacts/flagship_loop_proof/2026-04-09/agent_recommendation_2026-04-09.json",
            "artifacts/flagship_loop_proof/2026-04-09/agent_recommendation_latest.json",
            "artifacts/flagship_loop_proof/2026-04-09/positive_result.json",
            "artifacts/flagship_loop_proof/2026-04-09/negative_fail_closed_result.json",
            "artifacts/flagship_loop_proof/2026-04-09/negative_artifact_state_preservation.json",
        ],
        "negative_case_preserved_bytes": preservation["byte_identical_preserved"],
    }
    (OUTPUT_ROOT / "proof_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
