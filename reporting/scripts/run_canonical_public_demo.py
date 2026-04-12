from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO_ROOT / "artifacts" / "public_demo" / "generated"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "voice_note_intake" / "daily_voice_note_input.json"
RECOMMENDATION_PAYLOAD_PATH = REPO_ROOT / "artifacts" / "public_demo" / "payloads" / "recommendation_payload_2026-04-09.json"
BUNDLE_PATH = OUTPUT_ROOT / "shared_input_bundle_2026-04-09.json"
CONTEXT_PATH = OUTPUT_ROOT / "agent_readable_daily_context_2026-04-09.json"
EXPECTED_ARTIFACTS = [
    OUTPUT_ROOT / "shared_input_bundle_2026-04-09.json",
    OUTPUT_ROOT / "agent_readable_daily_context_2026-04-09.json",
    OUTPUT_ROOT / "agent_readable_daily_context_latest.json",
    OUTPUT_ROOT / "agent_recommendation_2026-04-09.json",
    OUTPUT_ROOT / "agent_recommendation_latest.json",
]


def _reset_output_dir() -> None:
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


def _run_step(name: str, *args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"{name} failed with exit code {completed.returncode}\n"
            f"stdout:\n{completed.stdout.strip()}\n\n"
            f"stderr:\n{completed.stderr.strip()}"
        )
    if completed.stderr.strip():
        raise RuntimeError(f"{name} wrote unexpected stderr:\n{completed.stderr.strip()}")
    return json.loads(completed.stdout)


def main() -> int:
    _reset_output_dir()

    contract = _run_step("contract describe", "-m", "health_model.agent_contract_cli", "describe")
    bundle = _run_step(
        "bundle init",
        "-m",
        "health_model.agent_bundle_cli",
        "init",
        "--bundle-path",
        str(BUNDLE_PATH),
        "--user-id",
        "user_dom",
        "--date",
        "2026-04-09",
    )
    voice_note = _run_step(
        "voice-note submit",
        "-m",
        "health_model.agent_voice_note_cli",
        "submit",
        "--bundle-path",
        str(BUNDLE_PATH),
        "--output-dir",
        str(OUTPUT_ROOT),
        "--user-id",
        "user_dom",
        "--date",
        "2026-04-09",
        "--payload-path",
        str(FIXTURE_PATH),
    )
    context = _run_step(
        "context get",
        "-m",
        "health_model.agent_context_cli",
        "get",
        "--artifact-path",
        str(CONTEXT_PATH),
        "--user-id",
        "user_dom",
        "--date",
        "2026-04-09",
    )
    recommendation = _run_step(
        "recommendation create",
        "-m",
        "health_model.agent_recommendation_cli",
        "create",
        "--output-dir",
        str(OUTPUT_ROOT),
        "--payload-path",
        str(RECOMMENDATION_PAYLOAD_PATH),
    )

    missing = [str(path.relative_to(REPO_ROOT)) for path in EXPECTED_ARTIFACTS if not path.exists()]
    if missing:
        raise RuntimeError(f"wrapper completed but expected artifacts were missing: {missing}")

    summary = {
        "ok": True,
        "command": f"{Path(sys.executable).name} scripts/run_canonical_public_demo.py",
        "generated_dir": str(OUTPUT_ROOT.relative_to(REPO_ROOT)),
        "generated_artifacts": [str(path.relative_to(REPO_ROOT)) for path in EXPECTED_ARTIFACTS],
        "steps": {
            "contract_describe": contract.get("contract_id") or contract,
            "bundle_init": bundle.get("bundle_path") or bundle,
            "voice_note_submit": voice_note.get("dated_artifact_path") or voice_note,
            "context_get": context.get("artifact_path") or context,
            "recommendation_create": recommendation.get("artifact_path") or recommendation,
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
