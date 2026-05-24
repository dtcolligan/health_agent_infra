"""Scoped golden fingerprints for offline reproducibility scoring artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BENCHMARK_ROOT.parent
GOLDEN_PATH = (
    BENCHMARK_ROOT / "governed_agent_bench" / "REPRODUCIBILITY_GOLDEN.json"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def normalize_for_hashing(file_path: Path, output_dir: Path) -> bytes:
    """Normalize absolute output-dir paths before hashing text artifacts."""

    resolved_output_dir = output_dir.resolve()
    text = file_path.read_text(encoding="utf-8")
    replacements = [
        f"/private{resolved_output_dir}",
        str(resolved_output_dir),
    ]
    if str(resolved_output_dir).startswith("/private/"):
        replacements.append(str(resolved_output_dir)[len("/private"):])
    for token in replacements:
        text = text.replace(token, "<OUTPUT_DIR>")
    return text.encode("utf-8")


def _bytes_for_hashing(
    file_path: Path,
    output_dir: Path,
    *,
    normalize_absolute_paths: bool,
) -> bytes:
    if normalize_absolute_paths:
        return normalize_for_hashing(file_path, output_dir)
    return file_path.read_bytes()


def _load_golden() -> dict[str, Any]:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def test_reproducer_scoring_artifacts_match_golden_fingerprints(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "offline_repro"
    env = os.environ.copy()
    env["PYTHONPATH"] = "benchmark"
    result = subprocess.run(
        [
            sys.executable,
            "benchmark/governed_agent_bench/reproduce_offline.py",
            "--output-dir",
            str(output_dir),
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        "offline reproducer failed\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    golden = _load_golden()
    mismatches: list[str] = []
    for entry in golden["hashed_files"]:
        relative_path = entry["path"]
        produced_path = output_dir / relative_path
        actual = hashlib.sha256(
            _bytes_for_hashing(
                produced_path,
                output_dir,
                normalize_absolute_paths=entry["normalize_absolute_paths"],
            )
        ).hexdigest()
        expected = entry["sha256"]
        if actual != expected:
            mismatches.append(
                f"MISMATCH: {relative_path}\n"
                f"  expected: {expected}\n"
                f"  actual:   {actual}"
            )

    assert not mismatches, "\n\n".join(mismatches)


def test_golden_file_schema_valid() -> None:
    golden = _load_golden()
    required_keys = {
        "schema_version",
        "generated_at_utc",
        "git_sha",
        "reproducer_command",
        "expected_wall_time_seconds_observed",
        "baseline_hardware",
        "hashed_files",
        "excluded_from_hashing",
    }

    assert required_keys.issubset(golden)
    assert golden["schema_version"] == (
        "governed_agent_bench.reproducibility_golden.v2"
    )
    assert golden["hashed_files"]
    for entry in golden["hashed_files"]:
        assert {"path", "normalize_absolute_paths", "sha256"}.issubset(entry)
        assert isinstance(entry["path"], str) and entry["path"]
        assert isinstance(entry["normalize_absolute_paths"], bool)
        assert SHA256_RE.fullmatch(entry["sha256"])
    assert golden["excluded_from_hashing"]
