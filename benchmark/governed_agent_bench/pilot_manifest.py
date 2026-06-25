"""Writer + helpers for the GovernedAgentBench pilot run manifest.

WP-A7. ``pilot_manifest.json`` is the top-level record of one model-backed
pilot run and the spine of the ``PILOT_PROTOCOL.md`` §14 hash lock: the lock
is defined by the SHA-256 set this manifest carries. This module builds a
schema-valid manifest (``governed_agent_bench.pilot_manifest.v1``) from
synthetic or live inputs and is callable independently of the A2 orchestrator,
which has not been built yet.

The writer is file-read-only by design. It loads the committed lock-hash
sidecar (``scripts/lock_hashes.json``, produced by ``collect_lock_hashes.py``)
rather than importing that module's payload builder, which shells out to git
and would break hermetic, synthetic testing. The sidecar intentionally excludes
``PILOT_PROTOCOL.md`` itself; record that file's hash in external lock evidence
after the lock commit is assembled.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BENCHMARK_ROOT = Path(__file__).resolve().parent
DEFAULT_LOCK_HASHES_PATH = BENCHMARK_ROOT / "scripts" / "lock_hashes.json"
SCHEMA_VERSION = "governed_agent_bench.pilot_manifest.v1"

DRAFT = "draft"
LOCKED = "locked"
PENDING_SELECTION = "pending"


def load_lock_hashes(path: Path = DEFAULT_LOCK_HASHES_PATH) -> dict[str, Any]:
    """Return the ``{fixed_files, task_files, total_count}`` hash block.

    Reads the committed sidecar so the per-task SHA-256 rows are sourced from
    the collector's output, never hardcoded here. File-read-only: it does not
    run git or touch the network.
    """

    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "fixed_files": payload["fixed_files"],
        "task_files": payload["task_files"],
        "total_count": payload["total_count"],
    }


def build_pilot_manifest(
    *,
    status: str,
    run_start_utc: str,
    git_sha: str,
    conditions_executed: list[dict[str, Any]],
    replication_n: int,
    d_o_01_selection: str,
    run_outcome: str,
    lock_date: str | None = None,
    lock_commit_sha: str | None = None,
    lock_hashes_path: Path = DEFAULT_LOCK_HASHES_PATH,
) -> dict[str, Any]:
    """Build a schema-valid pilot manifest dict.

    ``status="draft"`` emits only the §12 runtime fields; the §14 lock block is
    omitted. ``status="locked"`` additionally loads the lock-hash sidecar into
    ``locked_hashes`` and requires ``lock_date``, ``lock_commit_sha``, and a
    settled ``d_o_01_selection`` (not ``"pending"``).

    ``d_o_01_selection`` carries a roster condition_id / §14 option name with no
    ``_v1`` suffix (e.g. ``option_b_qwen25_7b_together``). It is a distinct
    namespace from ``conditions_executed[].system_id``, which carries the
    ``_v1`` directory key (e.g. ``option_b_qwen25_7b_together_v1``).
    """

    if status not in (DRAFT, LOCKED):
        raise ValueError(f"status must be {DRAFT!r} or {LOCKED!r}, got {status!r}")

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "run_start_utc": run_start_utc,
        "git_sha": git_sha,
        "replication_n": replication_n,
        "conditions_executed": conditions_executed,
        "d_o_01_selection": d_o_01_selection,
        "run_outcome": run_outcome,
    }

    if status == LOCKED:
        if lock_date is None or lock_commit_sha is None:
            raise ValueError(
                "locked manifest requires lock_date and lock_commit_sha"
            )
        if d_o_01_selection == PENDING_SELECTION:
            raise ValueError(
                "locked manifest requires a settled d_o_01_selection, "
                "not 'pending'"
            )
        manifest["locked_hashes"] = load_lock_hashes(lock_hashes_path)
        manifest["lock_date"] = lock_date
        manifest["lock_commit_sha"] = lock_commit_sha

    return manifest


def write_pilot_manifest(manifest: dict[str, Any], output_path: Path) -> None:
    """Write ``manifest`` as indented JSON with a trailing newline."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
