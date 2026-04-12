from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_PATH = REPO_ROOT / "artifacts" / "synthetic_stress_harness" / "scenarios.json"
OUTPUT_ROOT = REPO_ROOT / "artifacts" / "synthetic_stress_harness" / "latest"


def main() -> int:
    scenarios = json.loads(SCENARIO_PATH.read_text())
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    (OUTPUT_ROOT / "scenario_outputs").mkdir(parents=True, exist_ok=True)

    scenario_results = []
    for scenario in scenarios:
        result = _run_scenario(scenario)
        scenario_results.append(result)
        output_path = OUTPUT_ROOT / "scenario_outputs" / f"{scenario['name']}.json"
        output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    passed = sum(1 for result in scenario_results if result["passed"])
    summary = {
        "ok": passed == len(scenario_results),
        "command": f"{Path(sys.executable).name} scripts/run_synthetic_recommendation_stress_harness.py",
        "scenario_count": len(scenario_results),
        "passed_count": passed,
        "failed_count": len(scenario_results) - passed,
        "results": [
            {
                "name": result["name"],
                "stage": result["stage"],
                "passed": result["passed"],
                "expected": result["expected"],
                "actual": result["actual"],
            }
            for result in scenario_results
        ],
        "artifacts": {
            "scenario_definition_path": str(SCENARIO_PATH.relative_to(REPO_ROOT)),
            "summary_path": str((OUTPUT_ROOT / "stress_harness_summary.json").relative_to(REPO_ROOT)),
            "report_path": str((OUTPUT_ROOT / "stress_harness_report.md").relative_to(REPO_ROOT)),
            "scenario_outputs_dir": str((OUTPUT_ROOT / "scenario_outputs").relative_to(REPO_ROOT)),
        },
    }
    (OUTPUT_ROOT / "stress_harness_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (OUTPUT_ROOT / "stress_harness_report.md").write_text(_build_report(summary, scenario_results))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


def _run_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    scenario_type = scenario["type"]
    if scenario_type == "happy_path":
        return _run_happy_path_scenario(scenario)
    if scenario_type in {"rejection", "rejection_with_non_mutation"}:
        return _run_recommendation_scenario(scenario)
    if scenario_type == "upstream_rejection_with_non_mutation":
        return _run_voice_note_scope_mismatch_scenario(scenario)
    raise ValueError(f"Unsupported scenario type: {scenario_type}")


def _run_happy_path_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "generated"
        bundle_path = output_dir / "shared_input_bundle_2026-04-09.json"
        voice_note_fixture = REPO_ROOT / scenario["fixtures"]["voice_note_payload_path"]

        contract = _run_json_command("contract describe", ["-m", "health_model.agent_contract_cli", "describe"])
        bundle = _run_json_command(
            "bundle init",
            [
                "-m",
                "health_model.agent_bundle_cli",
                "init",
                "--bundle-path",
                str(bundle_path),
                "--user-id",
                "user_dom",
                "--date",
                "2026-04-09",
            ],
        )
        voice_note = _run_json_command(
            "voice-note submit",
            [
                "-m",
                "health_model.agent_voice_note_cli",
                "submit",
                "--bundle-path",
                str(bundle_path),
                "--output-dir",
                str(output_dir),
                "--user-id",
                "user_dom",
                "--date",
                "2026-04-09",
                "--payload-path",
                str(voice_note_fixture),
            ],
        )
        context_path = output_dir / "agent_readable_daily_context_2026-04-09.json"
        context = _run_json_command(
            "context get",
            [
                "-m",
                "health_model.agent_context_cli",
                "get",
                "--artifact-path",
                str(context_path),
                "--user-id",
                "user_dom",
                "--date",
                "2026-04-09",
            ],
        )
        recommendation_payload = dict(scenario["recommendation_template"])
        recommendation_payload["context_artifact_path"] = str(context_path)
        recommendation_payload["context_artifact_id"] = context["stdout"]["context"]["context_id"]
        recommendation = _run_json_command(
            "recommendation create",
            [
                "-m",
                "health_model.agent_recommendation_cli",
                "create",
                "--output-dir",
                str(output_dir),
                "--payload-json",
                json.dumps(recommendation_payload),
            ],
        )

        dated_path = Path(recommendation["stdout"]["artifact_path"])
        latest_path = Path(recommendation["stdout"]["latest_artifact_path"])
        bytes_match = dated_path.read_bytes() == latest_path.read_bytes()
        passed = (
            contract["ok"]
            and bundle["ok"]
            and voice_note["ok"]
            and context["ok"]
            and recommendation["ok"]
            and recommendation["stdout"].get("ok")
            and bytes_match
        )
        return {
            "name": scenario["name"],
            "stage": scenario["stage"],
            "passed": bool(passed),
            "expected": scenario["expected"],
            "actual": {
                "contract_ok": contract["stdout"].get("ok"),
                "bundle_ok": bundle["stdout"].get("ok"),
                "voice_note_ok": voice_note["stdout"].get("ok"),
                "context_ok": context["stdout"].get("ok"),
                "recommendation_ok": recommendation["stdout"].get("ok"),
                "dated_latest_bytes_match": bytes_match,
                "recommendation_artifact_path": recommendation["stdout"].get("artifact_path"),
            },
            "commands": [contract, bundle, voice_note, context, recommendation],
        }


def _run_recommendation_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "generated"
        output_dir.mkdir(parents=True, exist_ok=True)
        payload = dict(scenario["recommendation_template"])

        if "context_artifact_path" in scenario.get("fixtures", {}):
            context_path = REPO_ROOT / scenario["fixtures"]["context_artifact_path"]
            context = json.loads(context_path.read_text())
            payload["context_artifact_path"] = str(context_path)
            payload["context_artifact_id"] = context["context_id"]
        else:
            payload["context_artifact_path"] = str(output_dir / payload["context_artifact_path"])

        original_bytes = None
        if scenario["type"] == "rejection_with_non_mutation":
            seeded = dict(scenario["preexisting_recommendation"])
            seeded["context_artifact_path"] = str(REPO_ROOT / seeded["context_artifact_path"])
            original_bytes = (json.dumps(seeded, indent=2, sort_keys=True) + "\n").encode()
            (output_dir / "agent_recommendation_2026-04-09.json").write_bytes(original_bytes)
            (output_dir / "agent_recommendation_latest.json").write_bytes(original_bytes)

        command = _run_json_command(
            "recommendation create",
            [
                "-m",
                "health_model.agent_recommendation_cli",
                "create",
                "--output-dir",
                str(output_dir),
                "--payload-json",
                json.dumps(payload),
            ],
            expected_returncode=scenario["expected"]["exit_code"],
        )

        dated_path = output_dir / "agent_recommendation_2026-04-09.json"
        latest_path = output_dir / "agent_recommendation_latest.json"
        preserved = True
        if original_bytes is not None:
            preserved = dated_path.read_bytes() == original_bytes and latest_path.read_bytes() == original_bytes

        actual = {
            "ok": command["stdout"].get("ok"),
            "exit_code": command["returncode"],
            "error_code": command["stdout"].get("error", {}).get("code"),
            "artifact_path": command["stdout"].get("artifact_path"),
            "latest_artifact_path": command["stdout"].get("latest_artifact_path"),
            "preexisting_artifacts_preserved": preserved,
        }
        passed = (
            actual["ok"] == scenario["expected"]["ok"]
            and actual["exit_code"] == scenario["expected"]["exit_code"]
            and actual["error_code"] == scenario["expected"]["error_code"]
            and (
                not scenario["expected"].get("preserve_preexisting_artifacts")
                or actual["preexisting_artifacts_preserved"]
            )
        )
        return {
            "name": scenario["name"],
            "stage": scenario["stage"],
            "passed": bool(passed),
            "expected": scenario["expected"],
            "actual": actual,
            "commands": [command],
        }


def _run_voice_note_scope_mismatch_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "generated"
        bundle_path = output_dir / "shared_input_bundle_2026-04-09.json"
        voice_note_fixture = REPO_ROOT / scenario["fixtures"]["voice_note_payload_path"]
        valid_payload = json.loads(voice_note_fixture.read_text())

        bootstrap = _run_json_command(
            "bundle init",
            [
                "-m",
                "health_model.agent_bundle_cli",
                "init",
                "--bundle-path",
                str(bundle_path),
                "--user-id",
                "user_dom",
                "--date",
                "2026-04-09",
            ],
        )
        accepted = _run_json_command(
            "voice-note submit",
            [
                "-m",
                "health_model.agent_voice_note_cli",
                "submit",
                "--bundle-path",
                str(bundle_path),
                "--output-dir",
                str(output_dir),
                "--user-id",
                "user_dom",
                "--date",
                "2026-04-09",
                "--payload-json",
                json.dumps(valid_payload),
            ],
        )
        original_bundle = bundle_path.read_bytes()
        dated_path = output_dir / "agent_readable_daily_context_2026-04-09.json"
        latest_path = output_dir / "agent_readable_daily_context_latest.json"
        original_dated = dated_path.read_bytes()
        original_latest = latest_path.read_bytes()

        mutated_payload = json.loads(json.dumps(valid_payload))
        mutated_payload["derived_events"][0]["effective_date"] = scenario["mutation"]["value"]
        rejected = _run_json_command(
            "voice-note submit",
            [
                "-m",
                "health_model.agent_voice_note_cli",
                "submit",
                "--bundle-path",
                str(bundle_path),
                "--output-dir",
                str(output_dir),
                "--user-id",
                "user_dom",
                "--date",
                "2026-04-09",
                "--payload-json",
                json.dumps(mutated_payload),
            ],
            expected_returncode=scenario["expected"]["exit_code"],
        )

        preserved = (
            bundle_path.read_bytes() == original_bundle
            and dated_path.read_bytes() == original_dated
            and latest_path.read_bytes() == original_latest
        )
        actual = {
            "bootstrap_ok": bootstrap["stdout"].get("ok"),
            "accepted_ok": accepted["stdout"].get("ok"),
            "ok": rejected["stdout"].get("ok"),
            "exit_code": rejected["returncode"],
            "error_code": rejected["stdout"].get("error", {}).get("code"),
            "bundle_and_context_preserved": preserved,
        }
        passed = (
            actual["bootstrap_ok"]
            and actual["accepted_ok"]
            and actual["ok"] == scenario["expected"]["ok"]
            and actual["exit_code"] == scenario["expected"]["exit_code"]
            and actual["error_code"] == scenario["expected"]["error_code"]
            and (
                not scenario["expected"].get("preserve_bundle_and_context")
                or actual["bundle_and_context_preserved"]
            )
        )
        return {
            "name": scenario["name"],
            "stage": scenario["stage"],
            "passed": bool(passed),
            "expected": scenario["expected"],
            "actual": actual,
            "commands": [bootstrap, accepted, rejected],
        }


def _run_json_command(name: str, args: list[str], expected_returncode: int = 0) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = json.loads(completed.stdout) if completed.stdout.strip() else {}
    return {
        "name": name,
        "args": [Path(sys.executable).name, *args],
        "returncode": completed.returncode,
        "expected_returncode": expected_returncode,
        "ok": completed.returncode == expected_returncode and completed.stderr.strip() == "",
        "stdout": stdout,
        "stderr": completed.stderr,
    }


def _build_report(summary: dict[str, Any], scenario_results: list[dict[str, Any]]) -> str:
    lines = [
        "# Synthetic recommendation stress harness",
        "",
        f"Command: `{summary['command']}`",
        "",
        f"Passed {summary['passed_count']} of {summary['scenario_count']} scenarios.",
        "",
        "| Scenario | Stage | Result | Key actual |",
        "| --- | --- | --- | --- |",
    ]
    for result in scenario_results:
        key_actual = json.dumps(result["actual"], sort_keys=True)
        status = "PASS" if result["passed"] else "FAIL"
        lines.append(f"| {result['name']} | {result['stage']} | {status} | `{key_actual}` |")
    lines.append("")
    lines.append(f"Scenario definitions: `{summary['artifacts']['scenario_definition_path']}`")
    lines.append(f"Detailed outputs: `{summary['artifacts']['scenario_outputs_dir']}`")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
