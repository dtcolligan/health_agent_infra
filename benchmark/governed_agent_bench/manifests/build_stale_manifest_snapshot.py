"""Build the stale HAI manifest snapshot used by L7 drift tasks.

The source checkout does not currently have a ``v0.1.18`` tag, so the
snapshot is anchored to the v0.1.18 release-prep commit and the committed
v1 manifest snapshot present at that commit.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SNAPSHOT_SCHEMA_VERSION = "governed_agent_bench.manifest_snapshot.v1"
MANIFEST_VERSION = "agent_cli_contract_v1_drift"
SOURCE_COMMIT = "aa418d5e8fefca86f2d2a66f19975e63e31473c5"
SOURCE_REF_NOTE = "v0.1.18 release-prep commit; no v0.1.18 tag exists in this checkout"
SOURCE_MANIFEST_PATH = "verification/tests/snapshots/cli_capabilities_v0_1_13.json"
GENERATED_BY = (
    "uv run python benchmark/governed_agent_bench/manifests/"
    "build_stale_manifest_snapshot.py"
)


def load_historical_manifest(
    source_commit: str = SOURCE_COMMIT,
    source_manifest_path: str = SOURCE_MANIFEST_PATH,
) -> dict[str, Any]:
    """Load the historical manifest JSON from git object storage."""

    result = subprocess.run(
        ["git", "show", f"{source_commit}:{source_manifest_path}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def build_snapshot(
    manifest: dict[str, Any],
    *,
    generated_at: str | None = None,
    source_commit: str = SOURCE_COMMIT,
    source_manifest_path: str = SOURCE_MANIFEST_PATH,
) -> dict[str, Any]:
    """Wrap a historical manifest in the benchmark provenance envelope."""

    timestamp = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    if timestamp.endswith("+00:00"):
        timestamp = timestamp.removesuffix("+00:00") + "Z"
    return {
        "contract_schema_version": manifest["schema_version"],
        "drift_role": "stale_manifest_for_l7",
        "generated_at": timestamp,
        "generated_by": GENERATED_BY,
        "hai_version": manifest["hai_version"],
        "manifest": manifest,
        "manifest_version": MANIFEST_VERSION,
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "source_commit": source_commit,
        "source_manifest_path": source_manifest_path,
        "source_ref_note": SOURCE_REF_NOTE,
    }


def write_snapshot(
    output_path: Path,
    *,
    generated_at: str | None = None,
    source_commit: str = SOURCE_COMMIT,
    source_manifest_path: str = SOURCE_MANIFEST_PATH,
) -> None:
    """Generate and write the stale snapshot envelope."""

    manifest = load_historical_manifest(source_commit, source_manifest_path)
    snapshot = build_snapshot(
        manifest,
        generated_at=generated_at,
        source_commit=source_commit,
        source_manifest_path=source_manifest_path,
    )
    output_path.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name(f"{MANIFEST_VERSION}.json"),
        help="Destination snapshot path.",
    )
    parser.add_argument(
        "--generated-at",
        default=None,
        help="Optional ISO-8601 timestamp for reproducible regeneration.",
    )
    parser.add_argument(
        "--source-commit",
        default=SOURCE_COMMIT,
        help="Historical git commit that contains the manifest JSON.",
    )
    parser.add_argument(
        "--source-manifest-path",
        default=SOURCE_MANIFEST_PATH,
        help="Path to the historical manifest JSON inside the source commit.",
    )
    args = parser.parse_args()

    write_snapshot(
        args.output,
        generated_at=args.generated_at,
        source_commit=args.source_commit,
        source_manifest_path=args.source_manifest_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
