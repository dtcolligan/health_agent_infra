"""Live model-backed pilot runner for GovernedAgentBench (Option B).

Wires the locked Together roster condition into the pilot orchestrator and
runs the model-backed sweep.

THIS SPENDS REAL MONEY: it calls the Together API for every turn, billed
against the USD 100 per-condition cap that the orchestrator enforces
between turns. Requires ``TOGETHER_API_KEY`` in the environment.

Use ``--dry-run`` to print the resolved run configuration without any API
call, and ``--smoke`` for a single cheap validation call (one task,
``full_contract``, n=1) before committing the full sweep.

DR-9 model escalation is evaluated post-hoc from the completed 7B evidence
by ``results/dr9_switch.py``; this runner performs no mid-run prelude or
live switch, because no real-time prelude is implemented (PILOT_PROTOCOL.md
§8). Running the full 7B sweep first yields a superset of the prelude's
evidence at n=3.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

from governed_agent_bench.harness.together import together_default_condition
from governed_agent_bench.pilot_orchestrator import (
    DEFAULT_RUNS_ROOT,
    PilotConfig,
    default_pilot_config,
    run_pilot,
    together_model_turn_factory,
)

TOGETHER_API_KEY_ENV = "TOGETHER_API_KEY"
SMOKE_TASK_ID = "gab_l1_doctor_status_route"


def tracked_changes() -> list[str]:
    """Porcelain lines for uncommitted tracked changes (untracked excluded)."""

    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line for line in out.splitlines() if line and not line.startswith("??")]


def build_config(smoke: bool) -> PilotConfig:
    """Locked full-sweep config, or a single-cell smoke config."""

    if not smoke:
        return default_pilot_config()
    # Smoke runs are isolated under their own subroot so they never advance
    # the headline runs/pilot/latest symlink, and carry a tiny explicit cap.
    return PilotConfig(
        runs_root=DEFAULT_RUNS_ROOT / "_smoke",
        task_ids=(SMOKE_TASK_ID,),
        mode_order=("full_contract",),
        replication_n=1,
        cost_cap_usd=1.0,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the GovernedAgentBench Option B model-backed pilot.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="single task, full_contract, n=1 (cheap live validation call)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the resolved config and exit; makes no API call",
    )
    args = parser.parse_args(argv)

    condition = together_default_condition()
    config = build_config(args.smoke)

    print("GovernedAgentBench live pilot")
    print(f"  condition    : {condition['condition_id']} ({condition['model_id']})")
    print(f"  provider     : {condition['provider']}")
    print(f"  modes        : {', '.join(config.mode_order)}")
    print(f"  tasks        : {len(config.task_ids)}")
    print(f"  replication  : n={config.replication_n}")
    print(f"  cost cap     : USD {config.cost_cap_usd:.0f} per condition")
    print(f"  runs root    : {config.runs_root}")
    print(f"  mode         : {'SMOKE' if args.smoke else 'FULL SWEEP'}")

    if args.dry_run:
        print("dry-run: no API call made.")
        return 0

    if not os.environ.get(TOGETHER_API_KEY_ENV, "").strip():
        print(
            f"ERROR: {TOGETHER_API_KEY_ENV} is not set. Refusing to run.",
            file=sys.stderr,
        )
        return 2

    if not args.smoke:
        dirty = tracked_changes()
        if dirty:
            print(
                "WARNING: uncommitted tracked changes; the run-dir git sha "
                "will not reflect them. Commit before a paper-claim run:",
                file=sys.stderr,
            )
            for line in dirty:
                print(f"  {line}", file=sys.stderr)

    try:
        result = run_pilot(
            systems=[condition],
            model_turn_factory=together_model_turn_factory,
            config=config,
        )
    except FileExistsError as exc:
        print(
            f"ERROR: run dir already exists (same UTC minute + HEAD): {exc}",
            file=sys.stderr,
        )
        return 3
    except subprocess.CalledProcessError as exc:
        print(
            f"ERROR: could not resolve git HEAD for the run id: {exc}",
            file=sys.stderr,
        )
        return 4

    print(f"run_outcome     = {result.run_outcome}")
    print(f"run_dir         = {result.run_dir}")
    print(f"latest_advanced = {result.latest_advanced}")
    return 0 if result.run_outcome == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
