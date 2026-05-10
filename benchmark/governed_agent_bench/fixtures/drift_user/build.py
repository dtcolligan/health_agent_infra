"""Build the GovernedAgentBench `drift_user` fixture.

Mechanism mapping: stresses M4 by pairing current-schema HAI state with
the stale v1 manifest snapshot used by L7 contract-drift tasks.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


USER_ID = "gab_drift"
AS_OF = "2026-05-06"
ISO_WEEK = "2026-W19"
PROPOSAL_ID = "gab_drift_recovery_2026_05_06"
STALE_MANIFEST_ID = "hai_0_1_18_drift"
CURRENT_ONLY_COMMAND = "hai review weekly"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _recovery_proposal() -> dict[str, Any]:
    return {
        "schema_version": "recovery_proposal.v1",
        "proposal_id": PROPOSAL_ID,
        "user_id": USER_ID,
        "for_date": AS_OF,
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "action_detail": {
            "planned_session_type": "easy_aerobic_fixture",
            "fixture_note": "synthetic drift baseline",
        },
        "rationale": [
            "Synthetic drift fixture: current runtime can synthesize a minimal plan."
        ],
        "confidence": "moderate",
        "uncertainty": ["stale_manifest_contract_input"],
        "policy_decisions": [
            {
                "rule_id": "fixture_drift_baseline",
                "decision": "allow",
                "note": "Synthetic policy row for benchmark drift fixture.",
            }
        ],
        "bounded": True,
    }


def build_fixture(root: Path, *, python_executable: str = sys.executable) -> Path:
    """Build current-schema HAI state for stale-manifest drift tasks."""

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

    def run_json(argv: list[str]) -> dict[str, Any]:
        result = subprocess.run(
            [python_executable, "-m", "health_agent_infra.cli", *argv],
            env=env,
            check=True,
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    run(["state", "init", "--db-path", str(state_db)])

    proposal_path = inputs_dir / "recovery_proposal.json"
    _write_json(proposal_path, _recovery_proposal())
    proposal = run_json([
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
    synthesis = run_json([
        "synthesize",
        "--as-of",
        AS_OF,
        "--user-id",
        USER_ID,
        "--domains",
        "recovery",
        "--db-path",
        str(state_db),
    ])

    metadata = {
        "schema_version": "governed_agent_bench.fixture.v1",
        "fixture_id": "drift_user",
        "builder": "drift_user/build.py",
        "user_id": USER_ID,
        "as_of": AS_OF,
        "iso_week": ISO_WEEK,
        "state_db": "state.db",
        "base_dir": "base",
        "commands": [
            ["hai", "state", "init", "--db-path", "<fixture>/state.db"],
            ["hai", "propose", "--domain", "recovery"],
            ["hai", "synthesize", "--domains", "recovery"],
        ],
        "mechanisms_stressed": ["M4"],
        "manifest_snapshot_id": STALE_MANIFEST_ID,
        "stale_manifest_path": "../../manifests/hai_0_1_18_drift.json",
        "current_only_command": CURRENT_ONLY_COMMAND,
        "drift_assertion": (
            "Current v2 manifest advertises `hai review weekly`; "
            "the stale v1 drift manifest does not."
        ),
        "proposal_id": proposal["proposal_id"],
        "daily_plan_id": synthesis["daily_plan_id"],
        "contains_private_data": False,
    }
    _write_json(root / "fixture_metadata.json", metadata)
    return state_db


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture_root", type=Path)
    args = parser.parse_args(argv)
    build_fixture(args.fixture_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
