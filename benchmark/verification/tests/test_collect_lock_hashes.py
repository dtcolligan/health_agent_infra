"""Pilot-lock hash collection script tests."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from governed_agent_bench.scripts import collect_lock_hashes


REPO_ROOT = Path(__file__).resolve().parents[3]
TASK_ROOT = REPO_ROOT / "benchmark/governed_agent_bench/tasks"
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


def _run_script(tmp_path: Path) -> dict[str, Any]:
    output_json = tmp_path / "lock_hashes.json"
    exit_code = collect_lock_hashes.main(["--output-json", str(output_json)])
    assert exit_code == 0
    return json.loads(output_json.read_text(encoding="utf-8"))


def _filesystem_task_files() -> list[str]:
    paths: list[str] = []
    for lane in ("l1", "l2", "l5", "l6", "l7"):
        for path in sorted((TASK_ROOT / lane).glob("*.json")):
            if path.name.startswith("README"):
                continue
            paths.append(str(path.relative_to(REPO_ROOT)))
    return paths


def test_script_produces_20_embedded_input_entries(tmp_path: Path) -> None:
    payload = _run_script(tmp_path)

    assert len(payload["fixed_files"]) == 4
    assert len(payload["task_files"]) == 16
    assert payload["total_count"] == 20
    assert "benchmark/governed_agent_bench/PILOT_PROTOCOL.md" not in payload["fixed_files"]


def test_each_hash_is_valid_sha256_hex(tmp_path: Path) -> None:
    payload = _run_script(tmp_path)

    for sha256_hex in (
        *payload["fixed_files"].values(),
        *payload["task_files"].values(),
    ):
        assert SHA256_HEX_RE.fullmatch(sha256_hex)


def test_task_file_keys_match_filesystem(tmp_path: Path) -> None:
    payload = _run_script(tmp_path)

    assert sorted(payload["task_files"]) == _filesystem_task_files()


def test_script_exits_nonzero_when_file_missing(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    output_json = tmp_path / "lock_hashes.json"
    monkeypatch.setattr(
        collect_lock_hashes,
        "FIXED_FILES",
        (
            "benchmark/governed_agent_bench/does_not_exist.json",
            *collect_lock_hashes.FIXED_FILES[1:],
        ),
    )

    exit_code = collect_lock_hashes.main(["--output-json", str(output_json)])

    assert exit_code == 1
    assert not output_json.exists()
