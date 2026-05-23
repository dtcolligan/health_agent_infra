"""Benchmark package mypy enforcement."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_mypy_benchmark_package_clean() -> None:
    if shutil.which("uvx") is None:
        pytest.skip("uvx unavailable; cannot run benchmark mypy enforcement")

    env = os.environ.copy()
    env["MYPYPATH"] = "benchmark:hai/src"
    result = subprocess.run(
        [
            "uvx",
            "mypy",
            "--explicit-package-bases",
            "benchmark/governed_agent_bench",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "benchmark/governed_agent_bench mypy failed\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
