#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_USER_ID = "user_dom"
DEFAULT_PROOF_ROOT = REPO_ROOT / "artifacts" / "self_usage" / "week1"
DEFAULT_HEALTH_DIR = REPO_ROOT / "data" / "health"
DEFAULT_CAPTURE_TEMPLATE = REPO_ROOT / "artifacts" / "self_usage" / "templates" / "day_runner_capture_template.json"
DEFAULT_JUDGMENT_TEMPLATE = REPO_ROOT / "artifacts" / "self_usage" / "templates" / "judgment_log_template.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Thin one-day Health Lab self-usage runner. It validates the repo-root day surfaces, "
            "checks evidence-ref integrity, copies the proof bundle, and records compact usefulness/friction capture."
        )
    )
    parser.add_argument("--date", required=True)
    parser.add_argument("--user-id", default=DEFAULT_USER_ID)
    parser.add_argument("--recommendation-payload-path", required=True)
    parser.add_argument("--judgment-label", required=True, choices=["useful", "obvious", "wrong", "ignored"])
    parser.add_argument("--action-taken", required=True)
    parser.add_argument("--why", required=True)
    parser.add_argument("--caveat", default="")
    parser.add_argument("--gym-note", default="")
    parser.add_argument("--time-cost-note", required=True)
    parser.add_argument("--friction-points", nargs="*", default=[])
    parser.add_argument("--voice-note-payload-path")
    parser.add_argument("--proof-root", default=str(DEFAULT_PROOF_ROOT))
    parser.add_argument("--health-dir", default=str(DEFAULT_HEALTH_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if Path.cwd().resolve() != REPO_ROOT:
        print(json.dumps({
            "ok": False,
            "error": {
                "code": "repo_root_required",
                "message": f"Run this script from repo root: {REPO_ROOT}",
            },
        }, indent=2))
        return 1

    health_dir = Path(args.health_dir)
    proof_root = Path(args.proof_root)
    proof_dir = proof_root / args.date
    proof_dir.mkdir(parents=True, exist_ok=True)

    bundle_path = health_dir / f"shared_input_bundle_{args.date}.json"
    context_path = health_dir / f"agent_readable_daily_context_{args.date}.json"
    recommendation_path = health_dir / f"agent_recommendation_{args.date}.json"
    recommendation_payload_path = Path(args.recommendation_payload_path)

    preflight = {
        "repo_root": str(REPO_ROOT),
        "health_dir_exists": health_dir.exists(),
        "bundle_exists": bundle_path.exists(),
        "context_exists": context_path.exists(),
        "recommendation_exists": recommendation_path.exists(),
        "recommendation_payload_exists": recommendation_payload_path.exists(),
        "capture_template_exists": DEFAULT_CAPTURE_TEMPLATE.exists(),
        "judgment_template_exists": DEFAULT_JUDGMENT_TEMPLATE.exists(),
        "proof_dir_writable": proof_dir.exists(),
        "explicit_recommendation_authorship": True,
    }
    missing = [name for name, ok in preflight.items() if not ok and name != "explicit_recommendation_authorship"]
    if missing:
        print(json.dumps({"ok": False, "preflight": preflight, "error": {"code": "preflight_failed", "missing": missing}}, indent=2))
        return 1

    context_cli = _run_command([
        sys.executable,
        "-m",
        "health_model.agent_context_cli",
        "get",
        "--artifact-path",
        str(context_path),
        "--user-id",
        args.user_id,
        "--date",
        args.date,
    ])
    if context_cli.returncode != 0:
        print(json.dumps({"ok": False, "preflight": preflight, "error": {"code": "context_get_failed", "stderr": context_cli.stderr}}, indent=2))
        return context_cli.returncode

    context = json.loads(context_path.read_text())
    recommendation = json.loads(recommendation_path.read_text())
    recommendation_payload = json.loads(recommendation_payload_path.read_text())

    payload_scope_ok = (
        recommendation_payload.get("user_id") == args.user_id
        and recommendation_payload.get("date") == args.date
        and recommendation_payload.get("context_artifact_path") == str(context_path.relative_to(REPO_ROOT))
        and recommendation_payload.get("context_artifact_id") == context.get("context_id")
    )

    known_context_refs = collect_context_refs(context)
    recommendation_refs = recommendation.get("evidence_refs", [])
    missing_refs = sorted(ref for ref in recommendation_refs if ref not in known_context_refs)
    evidence_ref_check = "pass" if not missing_refs else "fail"
    if missing_refs:
        print(json.dumps({
            "ok": False,
            "preflight": preflight,
            "error": {"code": "evidence_ref_integrity_failed", "missing_refs": missing_refs},
        }, indent=2))
        return 1

    for source in [bundle_path, context_path, recommendation_path]:
        shutil.copy2(source, proof_dir / source.name)

    if args.voice_note_payload_path:
        voice_note_payload_path = Path(args.voice_note_payload_path)
        if not voice_note_payload_path.exists():
            print(json.dumps({"ok": False, "preflight": preflight, "error": {"code": "voice_note_payload_missing", "path": str(voice_note_payload_path)}}, indent=2))
            return 1
        destination = proof_dir / voice_note_payload_path.name
        if voice_note_payload_path.resolve() != destination.resolve():
            shutil.copy2(voice_note_payload_path, destination)

    judgment_row = {
        "date": args.date,
        "inputs_logged": "hydration; meal; voice note" if args.voice_note_payload_path else "hydration; meal",
        "context_artifact_path": str(context_path.relative_to(REPO_ROOT)),
        "recommendation_artifact_path": str(recommendation_path.relative_to(REPO_ROOT)),
        "recommendation_summary": recommendation.get("summary", ""),
        "label": args.judgment_label,
        "action_taken": args.action_taken,
        "why": args.why,
        "caveat": args.caveat,
        "gym_note": args.gym_note,
    }
    write_judgment_log(proof_dir / "judgment_log.csv", judgment_row)

    capture = {
        "date": args.date,
        "runner_status": "completed",
        "recommendation_payload_status": "validated_manual_payload" if payload_scope_ok else "scope_mismatch",
        "recommendation_artifact_path": str(recommendation_path.relative_to(REPO_ROOT)),
        "judgment_label": args.judgment_label,
        "action_taken": args.action_taken,
        "friction_points": args.friction_points,
        "time_cost_note": args.time_cost_note,
        "evidence_ref_check": evidence_ref_check,
        "proof_bundle_status": "copied",
        "payload_scope_check": payload_scope_ok,
        "explicit_recommendation_authorship_note": (
            "Recommendation summary and rationale come from the checked-in payload and remain operator-authored. "
            "This runner does not generate recommendation content."
        ),
        "preflight_checks": preflight,
    }
    capture_path = proof_dir / f"runner_capture_{args.date}.json"
    capture_path.write_text(json.dumps(capture, indent=2) + "\n")

    result = {
        "ok": True,
        "date": args.date,
        "user_id": args.user_id,
        "preflight": preflight,
        "context_cli": json.loads(context_cli.stdout),
        "evidence_ref_check": {
            "status": evidence_ref_check,
            "checked_refs": recommendation_refs,
            "context_ref_count": len(known_context_refs),
        },
        "artifacts": {
            "bundle_path": str((proof_dir / bundle_path.name).relative_to(REPO_ROOT)),
            "context_path": str((proof_dir / context_path.name).relative_to(REPO_ROOT)),
            "recommendation_path": str((proof_dir / recommendation_path.name).relative_to(REPO_ROOT)),
            "judgment_log_path": str((proof_dir / 'judgment_log.csv').relative_to(REPO_ROOT)),
            "capture_path": str(capture_path.relative_to(REPO_ROOT)),
        },
        "explicit_recommendation_authorship": capture["explicit_recommendation_authorship_note"],
    }
    print(json.dumps(result, indent=2))
    return 0


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True)


def collect_context_refs(context: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    generated_from = context.get("generated_from", {})
    for key in [
        "source_artifact_ids",
        "input_event_ids",
        "subjective_entry_ids",
        "manual_log_entry_ids",
    ]:
        refs.update(str(value) for value in generated_from.get(key, []))
    for signal in context.get("explicit_grounding", {}).get("signals", []):
        refs.update(str(value) for value in signal.get("evidence_refs", []))
    return refs


def write_judgment_log(path: Path, row: dict[str, str]) -> None:
    fieldnames = [
        "date",
        "inputs_logged",
        "context_artifact_path",
        "recommendation_artifact_path",
        "recommendation_summary",
        "label",
        "action_taken",
        "why",
        "caveat",
        "gym_note",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


if __name__ == "__main__":
    raise SystemExit(main())
