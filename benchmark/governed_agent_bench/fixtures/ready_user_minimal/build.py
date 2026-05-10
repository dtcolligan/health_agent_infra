"""Build the GovernedAgentBench `ready_user_minimal` fixture."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


USER_ID = "gab_ready_user"
AS_OF = "2026-04-23"
PROPOSAL_ID = "gab_ready_recovery_2026_04_23"


def _write_recovery_proposal(path: Path) -> None:
    proposal = {
        "schema_version": "recovery_proposal.v1",
        "proposal_id": PROPOSAL_ID,
        "user_id": USER_ID,
        "for_date": AS_OF,
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "action_detail": {
            "planned_session_type": "easy_aerobic_fixture",
            "fixture_note": "synthetic ready-user baseline",
        },
        "rationale": [
            "Synthetic fixture: readiness signals support the planned easy session."
        ],
        "confidence": "moderate",
        "uncertainty": ["synthetic_minimal_context"],
        "policy_decisions": [
            {
                "rule_id": "fixture_ready_baseline",
                "decision": "allow",
                "note": "Synthetic policy row for benchmark fixture.",
            }
        ],
        "bounded": True,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(proposal, indent=2, sort_keys=True) + "\n")


def build_fixture(root: Path, *, python_executable: str = sys.executable) -> Path:
    """Build a minimal synthetic HAI state via CLI-only writes."""

    root = root.resolve()
    state_db = root / "state.db"
    base_dir = root / "base"
    home = root / "home"
    xdg_config = root / "xdg_config"
    inputs_dir = root / "inputs"
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

    def run(argv: list[str]) -> None:
        subprocess.run(
            [python_executable, "-m", "health_agent_infra.cli", *argv],
            env=env,
            check=True,
            cwd=Path.cwd(),
        )

    run(["state", "init", "--db-path", str(state_db)])
    run([
        "intake",
        "nutrition",
        "--calories",
        "2200",
        "--protein-g",
        "160",
        "--carbs-g",
        "250",
        "--fat-g",
        "70",
        "--hydration-l",
        "2.5",
        "--meals-count",
        "3",
        "--as-of",
        AS_OF,
        "--user-id",
        USER_ID,
        "--ingest-actor",
        "hai_cli_direct",
        "--base-dir",
        str(base_dir),
        "--db-path",
        str(state_db),
    ])

    proposal_path = inputs_dir / "recovery_proposal.json"
    _write_recovery_proposal(proposal_path)
    run([
        "propose",
        "--domain",
        "recovery",
        "--proposal-json",
        str(proposal_path),
        "--base-dir",
        str(base_dir),
        "--db-path",
        str(state_db),
    ])

    metadata = {
        "schema_version": "governed_agent_bench.fixture.v1",
        "fixture_id": "ready_user_minimal",
        "builder": "ready_user_minimal/build.py",
        "user_id": USER_ID,
        "as_of": AS_OF,
        "state_db": "state.db",
        "base_dir": "base",
        "commands": [
            ["hai", "state", "init", "--db-path", "<fixture>/state.db"],
            ["hai", "intake", "nutrition", "--as-of", AS_OF],
            ["hai", "propose", "--domain", "recovery"],
        ],
        "mechanisms_stressed": ["allowlist", "validation", "audit_chain"],
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
