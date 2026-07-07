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
    "benchmark/governed_agent_bench/scorer_config.paper_v1.json",
    "benchmark/governed_agent_bench/model_roster.md",
    # deployment_full_v3 is the run template (§20.14); v2 is retained for the
    # legacy conditions, so both are pinned.
    "benchmark/governed_agent_bench/prompts/deployment_full_v3.md",
    "benchmark/governed_agent_bench/prompts/deployment_full_v2.md",
    "benchmark/governed_agent_bench/manifests/hai_0_2_0.json",
)


def _discover_task_files() -> tuple[str, ...]:
    """Glob the current suite, so the lock follows the task set rather than a
    hand-maintained list (the suite is rebuilt for the specify-vs-enforce
    framing; a hardcoded list would silently drift)."""

    task_root = REPO_ROOT / "benchmark/governed_agent_bench/tasks"
    return tuple(
        str(path.relative_to(REPO_ROOT))
        for path in sorted(task_root.glob("l[1-7]/gab_*.json"))
    )

TASK_FILES: tuple[str, ...] = _discover_task_files()


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
    """Return hashes for lock inputs embedded in the pilot manifest.

    ``PILOT_PROTOCOL.md`` is intentionally excluded because embedding a file's
    own final SHA-256 inside that same file is circular. Record the protocol
    file hash in external lock evidence after the commit is assembled.
    """

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
