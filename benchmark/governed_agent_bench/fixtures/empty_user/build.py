"""Build the GovernedAgentBench `empty_user` fixture."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def build_fixture(root: Path, *, python_executable: str = sys.executable) -> Path:
    """Initialize an empty HAI state DB under the benchmark hermetic recipe."""

    root = root.resolve()
    state_db = root / "state.db"
    base_dir = root / "base"
    home = root / "home"
    xdg_config = root / "xdg_config"
    base_dir.mkdir(parents=True, exist_ok=True)
    home.mkdir(parents=True, exist_ok=True)
    xdg_config.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.update({
        "HAI_HERMETIC": "1",
        "HAI_STATE_DB": str(state_db),
        "HAI_BASE_DIR": str(base_dir),
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(xdg_config),
    })

    command = [
        python_executable,
        "-m",
        "health_agent_infra.cli",
        "state",
        "init",
        "--db-path",
        str(state_db),
    ]
    subprocess.run(command, env=env, check=True, cwd=Path.cwd())

    metadata = {
        "schema_version": "governed_agent_bench.fixture.v1",
        "fixture_id": "empty_user",
        "builder": "empty_user/build.py",
        "commands": [["hai", "state", "init", "--db-path", "<fixture>/state.db"]],
        "state_db": "state.db",
        "base_dir": "base",
        "mechanisms_stressed": ["allowlist", "validation", "hermetic_setup"],
        "contains_private_data": False,
    }
    (root / "fixture_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return state_db


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture_root", type=Path)
    args = parser.parse_args(argv)
    build_fixture(args.fixture_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
