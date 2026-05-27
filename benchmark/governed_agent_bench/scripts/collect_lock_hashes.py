"""Collect pilot-lock SHA-256 fingerprints for GovernedAgentBench."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "governed_agent_bench.lock_hashes.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_JSON = (
    REPO_ROOT / "benchmark/governed_agent_bench/scripts/lock_hashes.json"
)

FIXED_FILES: tuple[str, ...] = (
    "benchmark/governed_agent_bench/PILOT_PROTOCOL.md",
    "benchmark/governed_agent_bench/scorer_config.paper_v1.json",
    "benchmark/governed_agent_bench/model_roster.md",
    "benchmark/governed_agent_bench/prompts/deployment_full_v1.md",
    "benchmark/governed_agent_bench/manifests/hai_0_2_0.json",
    "benchmark/governed_agent_bench/safety_constrained_subset.json",
)

TASK_FILES: tuple[str, ...] = (
    "benchmark/governed_agent_bench/tasks/l1/gab_l1_capabilities_route.json",
    "benchmark/governed_agent_bench/tasks/l1/gab_l1_doctor_status_route.json",
    "benchmark/governed_agent_bench/tasks/l1/gab_l1_explain_route.json",
    "benchmark/governed_agent_bench/tasks/l1/gab_l1_today_json_route.json",
    "benchmark/governed_agent_bench/tasks/l2/gab_l2_empty_today_user_input.json",
    "benchmark/governed_agent_bench/tasks/l2/gab_l2_governance_intent_list.json",
    "benchmark/governed_agent_bench/tasks/l2/gab_l2_governance_pending_list.json",
    "benchmark/governed_agent_bench/tasks/l2/gab_l2_recover_user_input.json",
    "benchmark/governed_agent_bench/tasks/l5/gab_l5_audit_card_reference.json",
    "benchmark/governed_agent_bench/tasks/l5/gab_l5_explain_evidence_summary.json",
    "benchmark/governed_agent_bench/tasks/l5/gab_l5_explain_recovery_audit.json",
    "benchmark/governed_agent_bench/tasks/l5/gab_l5_today_audit_summary.json",
    "benchmark/governed_agent_bench/tasks/l5/gab_l5_today_faithful_summary.json",
    "benchmark/governed_agent_bench/tasks/l6/gab_l6_block_agent_commit.json",
    "benchmark/governed_agent_bench/tasks/l6/gab_l6_block_agent_intent_commit.json",
    "benchmark/governed_agent_bench/tasks/l6/gab_l6_block_agent_target_commit.json",
    "benchmark/governed_agent_bench/tasks/l6/gab_l6_block_commit_under_no_runtime.json",
    "benchmark/governed_agent_bench/tasks/l6/gab_l6_block_dual_commit.json",
    "benchmark/governed_agent_bench/tasks/l6/gab_l6_block_intent_proposal_commit.json",
    "benchmark/governed_agent_bench/tasks/l6/gab_l6_block_proposal_commit.json",
    "benchmark/governed_agent_bench/tasks/l6/gab_l6_refuse_credential_request.json",
    "benchmark/governed_agent_bench/tasks/l6/gab_l6_refuse_diagnosis_request.json",
    "benchmark/governed_agent_bench/tasks/l6/gab_l6_refuse_forbidden_export.json",
    "benchmark/governed_agent_bench/tasks/l6/gab_l6_refuse_under_no_runtime.json",
    "benchmark/governed_agent_bench/tasks/l6/gab_l6_refuse_unsafe_protocol.json",
    "benchmark/governed_agent_bench/tasks/l7/gab_l7_stale_capabilities_drift.json",
    "benchmark/governed_agent_bench/tasks/l7/gab_l7_stale_missing_weekly_command.json",
    "benchmark/governed_agent_bench/tasks/l7/gab_l7_stale_v1_manifest_shape.json",
)


class MissingLockFileError(RuntimeError):
    """Raised when the pilot-lock fingerprint list references missing files."""

    def __init__(self, missing_paths: list[str]) -> None:
        self.missing_paths = missing_paths
        super().__init__("missing lock files: " + ", ".join(missing_paths))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_sha(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        check=True,
        text=True,
    )
    return result.stdout.strip()


def _hash_group(relative_paths: tuple[str, ...], repo_root: Path) -> dict[str, str]:
    return {
        relative_path: _sha256_file(repo_root / relative_path)
        for relative_path in relative_paths
    }


def build_lock_hashes_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Return the lock-hash sidecar payload for the fixed pilot file set."""

    missing_paths = [
        relative_path
        for relative_path in (*FIXED_FILES, *TASK_FILES)
        if not (repo_root / relative_path).is_file()
    ]
    if missing_paths:
        raise MissingLockFileError(missing_paths)

    fixed_files = _hash_group(FIXED_FILES, repo_root)
    task_files = _hash_group(TASK_FILES, repo_root)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "git_sha": _git_sha(repo_root),
        "fixed_files": fixed_files,
        "task_files": task_files,
        "total_count": len(fixed_files) + len(task_files),
    }


def markdown_table(payload: dict[str, Any]) -> str:
    """Render the lock hashes in the PILOT_PROTOCOL.md §14 table shape."""

    rows = ["| File | SHA-256 (at lock) |", "|---|---|"]
    all_hashes = {
        **payload["fixed_files"],
        **payload["task_files"],
    }
    for relative_path, sha256_hex in all_hashes.items():
        rows.append(f"| `{relative_path}` | `{sha256_hex}` |")
    return "\n".join(rows)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute SHA-256 fingerprints for the pilot-lock file set."
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help="Path for the generated lock_hashes.json sidecar.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        payload = build_lock_hashes_payload()
    except MissingLockFileError as error:
        for missing_path in error.missing_paths:
            print(f"missing required lock file: {missing_path}", file=sys.stderr)
        return 1
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"failed to collect lock hashes: {error}", file=sys.stderr)
        return 1

    print(markdown_table(payload))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
