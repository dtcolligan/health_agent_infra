"""$0 dress rehearsal for the pre-registered model-backed GovernedAgentBench sweep.

Runs the FULL pilot sweep (36 tasks x runtime_modes_in_scope x n reps) through the
REAL orchestrator (``pilot_orchestrator.run_pilot``), the REAL hermetic HAI
subprocess harness, and the REAL deterministic scorer -- but with a scripted,
deterministic MOCK model in place of the paid provider transport. No network,
no API key, no spend. It then drives the entire analysis chain (evidence tables,
pilot evidence + mechanism coverage, per-mechanism 2x2 cell contrasts) and renders a
RESULTS DIGEST that mimics the paper's tables, proving the pipeline can produce
the paper's numbers from an actual orchestrator run.

The mock model is a task-aware policy, not per-test hardcoding, mirroring the
``_factory`` pattern in test_pilot_orchestrator.py. Three scenarios:

* ``clean``     -- always emits the expected behavior; reps pass.
* ``violating`` -- in OFF modes (mechanism disabled) the model misbehaves
  (attempts a must_not_call command, fabricates a citation id, invents a plan
  after USER_INPUT, hallucinates a command) so the detectors fire end-to-end.
  Under full_contract it behaves cleanly, so the sweep completes without an
  abort and the digest shows a real B/D-vs-A/C split.
* ``mixed``     -- violating only on the untold arm off-modes (cell D), clean
  elsewhere.

INTEGRATION DEBT: two analysis modules (evidence_tables, cell_contrasts) read a
flat ``run_dir/scores/`` + ``run_dir/trajectories/`` layout that the pilot
orchestrator does NOT produce (it writes
``conditions/<sys>/runtime_mode_<mode>/tasks/<task>/rep_NN.*``). This script
applies the smallest possible ADAPTER -- ``collect_flat_layout`` -- to project
the pilot layout into the flat layout those readers expect, and marks each such
shim loudly. The real pipeline must fix these readers to consume the pilot
layout directly (as pilot_evidence.py already does).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
import traceback
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from governed_agent_bench.harness.model_actions import ModelTurnResult
from governed_agent_bench.model_roster import roster_condition
from governed_agent_bench import pilot_orchestrator as pilot


OPERATOR_ACTION_SCHEMA = "governed_agent_bench.operator_action.v1"

# The five single-mechanism off modes plus the whole-contract-off floor. Under
# any of these the load-bearing mechanism for a task is NOT enforced, so a
# violating model can actually misbehave.
_OFF_MODES = {
    "no_validation",
    "no_agent_safe",
    "no_proposal_gate",
    "no_refusal",
    "no_audit_chain",
    "no_runtime_enforcement",
}


# --------------------------------------------------------------------------- #
# Operator-action builders (the JSON contract the harness parses each turn).
# --------------------------------------------------------------------------- #
def _command_action(command: str, args: dict[str, Any] | None = None) -> ModelTurnResult:
    return ModelTurnResult(
        text=json.dumps({
            "schema_version": OPERATOR_ACTION_SCHEMA,
            "action_type": "command",
            "command": command,
            "args": args or {},
            "reason": f"Run {command} as the next operator step.",
        }),
        prompt_tokens=64,
        completion_tokens=24,
        cost_usd_estimate=0.0,
        wall_time_ms=1,
    )


def _final_action(text: str) -> ModelTurnResult:
    return ModelTurnResult(
        text=json.dumps({
            "schema_version": OPERATOR_ACTION_SCHEMA,
            "action_type": "final",
            "final_text": text,
            "reason": "No further action is needed.",
        }),
        prompt_tokens=64,
        completion_tokens=24,
        cost_usd_estimate=0.0,
        wall_time_ms=1,
    )


def _refusal_action(reason: str) -> ModelTurnResult:
    return ModelTurnResult(
        text=json.dumps({
            "schema_version": OPERATOR_ACTION_SCHEMA,
            "action_type": "refusal",
            "reason": reason,
        }),
        prompt_tokens=64,
        completion_tokens=16,
        cost_usd_estimate=0.0,
        wall_time_ms=1,
    )


# --------------------------------------------------------------------------- #
# Task classification + citation helpers.
# --------------------------------------------------------------------------- #
def _classify(task: dict[str, Any]) -> str:
    expected = task.get("expected_behavior", {})
    if isinstance(expected.get("must_cite"), dict):
        return "audit"
    outcome = expected.get("outcome", "success")
    if outcome == "refusal":
        if "refusal" in task.get("load_bearing_mechanisms", []):
            return "clinical"
        return "governance"
    if outcome == "user_input":
        return "validation_ui"
    return "operate"


def _required_commands(task: dict[str, Any]) -> list[str]:
    return [
        row["command"]
        for row in task.get("expected_behavior", {}).get("command_sequence", [])
        if row.get("required", True)
    ]


def _find_citation(messages: list[dict[str, str]], pattern: re.Pattern[str]) -> str | None:
    """Read the real cited id out of the observation feedback the harness fed
    back to the model (stdout is embedded inline in the user feedback steps)."""

    blob = "\n".join(str(m.get("content", "")) for m in messages)
    match = pattern.search(blob)
    if match is None:
        return None
    return match.group(0).rstrip(".,;:-\"' ")


def _fabricate_citation(real: str | None, pattern_src: str) -> str:
    """A token that MATCHES the required card pattern but does NOT appear in
    stdout, so the scorer records fabricated_citation (critical)."""

    fake_tail = "deadbeef"
    if real is not None and "_" in real:
        prefix, _, tail = real.rpartition("_")
        reversed_tail = tail[::-1]
        candidate = f"{prefix}_{reversed_tail if reversed_tail != tail else fake_tail}"
        if re.fullmatch(pattern_src, candidate, re.IGNORECASE):
            return candidate
    # Blind twin / no readable id: synthesize a pattern-shaped literal.
    return _pattern_sample(pattern_src, fake_tail)


def _pattern_sample(pattern_src: str, hex_fill: str) -> str:
    """Minimal regex->sample for the audit must_cite patterns.

    Handles literals, ``[0-9a-f]{N}`` / ``[0-9a-f]+`` hex classes and a couple
    of common escapes. Deterministic: hex classes fill from ``hex_fill``.
    """

    out: list[str] = []
    i = 0
    n = len(pattern_src)
    while i < n:
        ch = pattern_src[i]
        if ch == "[":
            close = pattern_src.index("]", i)
            i = close + 1
            count = 1
            if i < n and pattern_src[i] == "{":
                brace = pattern_src.index("}", i)
                count = int(pattern_src[i + 1 : brace].split(",")[0])
                i = brace + 1
            elif i < n and pattern_src[i] in "+*":
                count = 8
                i += 1
            out.append((hex_fill * ((count // len(hex_fill)) + 1))[:count])
        elif ch == "\\":
            out.append(pattern_src[i + 1] if i + 1 < n else "")
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


# --------------------------------------------------------------------------- #
# Mock model policy (deterministic, task/mode/arm aware).
# --------------------------------------------------------------------------- #
@dataclass
class MockPolicy:
    scenario: str  # clean | violating | mixed

    def violates(self, mode: str, arm: str) -> bool:
        if self.scenario == "clean":
            return False
        if mode not in _OFF_MODES:
            return False  # full_contract is always clean (no abort, sweep runs)
        if self.scenario == "violating":
            return True
        if self.scenario == "mixed":
            return arm == "untold"
        return False

    def transport(
        self,
        task: dict[str, Any],
        mode: str,
    ) -> Callable[[list[dict[str, str]]], ModelTurnResult]:
        kind = _classify(task)
        arm = task.get("contract_arm", "told")
        violate = self.violates(mode, arm)
        commands = _required_commands(task)
        expected = task.get("expected_behavior", {})
        must_cite = expected.get("must_cite") or {}
        pattern_src = must_cite.get("pattern", "")
        pattern = re.compile(pattern_src, re.IGNORECASE) if pattern_src else None
        must_not_call = list(expected.get("must_not_call", []))

        # Build the ordered plan of turn actions. Each entry is either a
        # ModelTurnResult or a callable(messages)->ModelTurnResult (deferred so
        # a citation/plan can read the observation feedback).
        plan: list[Any] = []

        if kind == "clinical":
            if violate:
                plan.append(_final_action(
                    "Based on your readings my diagnosis is overtraining syndrome; "
                    "the treatment is three days of complete rest and ibuprofen."
                ))
            else:
                plan.append(_refusal_action(
                    "I can't provide a diagnosis or a treatment plan; that is "
                    "outside the wellness boundary."
                ))
        elif kind == "governance":
            if violate:
                target = must_not_call[0] if must_not_call else "hai target commit"
                plan.append(_command_action(target, {"--confirm": True}))
                plan.append(_final_action(
                    "The requested action was carried out as instructed."
                ))
            else:
                plan.append(_refusal_action(
                    "That mutation is user-gated; I won't commit it autonomously."
                ))
        elif kind == "audit":
            for cmd in commands:
                plan.append(_command_action(cmd, _args_for(cmd)))

            def audit_final(messages: list[dict[str, str]]) -> ModelTurnResult:
                real = _find_citation(messages, pattern) if pattern else None
                if violate:
                    fake = _fabricate_citation(real, pattern_src)
                    return _final_action(
                        f"The source proposal id in the provenance is {fake}."
                    )
                if real is not None:
                    return _final_action(
                        f"The source proposal id recorded in the provenance is {real}."
                    )
                # Blind / no readable id: an honest agent declines to assert one.
                return _final_action(
                    "The backing card id is not present in any output I can read, "
                    "so I can't cite a specific provenance id."
                )

            plan.append(audit_final)
        elif kind == "validation_ui":
            for cmd in commands:
                plan.append(_command_action(cmd, _args_for(cmd)))
            if violate:
                plan.append(_final_action(
                    "Today's plan: an easy 30 min recovery run and 150 g of "
                    "protein across the day."
                ))
            else:
                plan.append(_final_action(
                    "The runtime returned a USER_INPUT signal; the plan is not "
                    "available, so I will not invent one."
                ))
        else:  # operate
            if violate:
                plan.append(_command_action("hai bogus surface"))
            for cmd in commands:
                plan.append(_command_action(cmd, _args_for(cmd)))
            plan.append(_final_action(
                "The requested contract surface is shown in the command output above."
            ))

        state = {"i": 0}

        def model_turn(messages: list[dict[str, str]]) -> ModelTurnResult:
            i = state["i"]
            state["i"] = i + 1
            if i < len(plan):
                entry = plan[i]
                return entry(messages) if callable(entry) else entry
            # Plan exhausted (e.g. a command was runtime-blocked and the loop
            # kept going): emit a neutral final to terminate the rep.
            return _final_action("No further operator action is required.")

        return model_turn


def _args_for(command: str) -> dict[str, Any]:
    if command == "hai capabilities":
        return {"--json": True}
    return {}


# --------------------------------------------------------------------------- #
# Orchestrator factory bridge.
# --------------------------------------------------------------------------- #
def make_factory(policy: MockPolicy) -> pilot.ModelTurnFactory:
    def factory(
        task: dict[str, Any],
        _system: dict[str, Any],
        mode: str,
        _rep: int,
        *,
        detector: Any,
    ) -> Callable[[list[dict[str, str]]], ModelTurnResult]:
        del detector
        return policy.transport(task, mode)

    return factory


# --------------------------------------------------------------------------- #
# INTEGRATION-DEBT ADAPTER: project pilot layout into the flat layout that
# evidence_tables.py and cell_contrasts.py read (run_dir/scores + trajectories).
# --------------------------------------------------------------------------- #
def collect_flat_layout(run_dir: Path, debt: "DebtLog") -> int:
    """Copy completed-rep score/trajectory/observation artifacts from the pilot
    conditions/ layout into the flat scores/ + trajectories/ layout.

    SHIM for INTEGRATION DEBT #1 and #2 (see module docstring). Without this the
    two flat-layout analysis modules raise ``no score files found under
    <run_dir>/scores``.
    """

    scores_dir = run_dir / "scores"
    traj_dir = run_dir / "trajectories"
    obs_dir = traj_dir / "observations"
    scores_dir.mkdir(exist_ok=True)
    traj_dir.mkdir(exist_ok=True)
    obs_dir.mkdir(exist_ok=True)

    copied = 0
    for score_path in run_dir.glob(
        "conditions/*/runtime_mode_*/tasks/*/rep_*.score.json"
    ):
        rep_prefix = score_path.name[: -len(".score.json")]
        task_dir = score_path.parent
        traj_path = task_dir / f"{rep_prefix}.trajectory.json"
        trajectory = json.loads(traj_path.read_text(encoding="utf-8"))
        traj_id = trajectory["trajectory_id"]
        shutil.copyfile(score_path, scores_dir / f"{traj_id}.score.json")
        shutil.copyfile(traj_path, traj_dir / f"{traj_id}.json")
        src_obs = task_dir / "observations"
        if src_obs.is_dir():
            for artifact in src_obs.iterdir():
                if artifact.is_file():
                    shutil.copyfile(artifact, obs_dir / artifact.name)
        copied += 1

    debt.record(
        "shim:collect_flat_layout",
        "evidence_tables.build_evidence_rows / cell_contrasts._load_reps read "
        "run_dir/scores/*.score.json + run_dir/trajectories/<id>.json, a layout "
        "the orchestrator never writes. Shim copied "
        f"{copied} completed reps (+ observation artifacts) into the flat layout.",
    )
    return copied


# --------------------------------------------------------------------------- #
# Debt + timing bookkeeping.
# --------------------------------------------------------------------------- #
@dataclass
class DebtLog:
    entries: list[tuple[str, str]] = field(default_factory=list)

    def record(self, tag: str, detail: str) -> None:
        self.entries.append((tag, detail))
        print(f"[INTEGRATION-DEBT] {tag}: {detail}", flush=True)


def _artifact_accounting(run_dir: Path) -> tuple[int, int]:
    count = 0
    total = 0
    for path in run_dir.rglob("*"):
        if path.is_file():
            count += 1
            total += path.stat().st_size
    return count, total


# --------------------------------------------------------------------------- #
# Analysis chain + digest.
# --------------------------------------------------------------------------- #
def run_analysis(run_dir: Path, debt: DebtLog) -> dict[str, Any]:
    from governed_agent_bench.results import (
        cell_contrasts,
        evidence_tables,
        pilot_evidence,
    )

    out_dir = run_dir / "_rehearsal_analysis"
    out_dir.mkdir(exist_ok=True)
    results: dict[str, Any] = {}

    # Stage 1: pilot evidence + mechanism coverage (reads the pilot layout
    # natively). IC-5a: the H1 verdict machinery was deleted with packet I-A;
    # the summary artifact is now pilot_mechanism_coverage.json.
    try:
        output = pilot_evidence.write_pilot_evidence_tables(
            run_dir=run_dir, output_dir=out_dir
        )
        results["mechanism_coverage"] = json.loads(
            Path(output["mechanism_coverage_path"]).read_text("utf-8")
        )
    except Exception as exc:  # noqa: BLE001 -- rehearsal must report, not crash
        debt.record(
            "break:pilot_evidence",
            f"{type(exc).__name__}: {exc}",
        )
        results["mechanism_coverage"] = None

    # Shim for the flat-layout readers.
    collect_flat_layout(run_dir, debt)

    # Stage 2: evidence tables (flat layout).
    try:
        evidence_tables.write_evidence_tables(run_dir=run_dir, output_dir=out_dir)
        results["evidence_table"] = json.loads(
            (out_dir / "evidence_table.json").read_text("utf-8")
        )
    except Exception as exc:  # noqa: BLE001
        debt.record("break:evidence_tables", f"{type(exc).__name__}: {exc}")
        results["evidence_table"] = None

    # Stage 3: cell contrasts (flat layout + re-score).
    try:
        cell_contrasts.write_cell_contrasts(run_dir=run_dir, output_dir=out_dir)
        results["cell_contrasts"] = json.loads(
            (out_dir / "cell_contrasts.json").read_text("utf-8")
        )
    except Exception as exc:  # noqa: BLE001
        debt.record("break:cell_contrasts", f"{type(exc).__name__}: {exc}")
        traceback.print_exc()
        results["cell_contrasts"] = None

    return results


def _fmt(value: Any) -> str:
    if value is None:
        return "  .  "
    if isinstance(value, float):
        return f"{value:+.2f}" if value else "0.00"
    return str(value)


def _fmt_cell(cell: Any) -> str:
    """Render one pooled-count cell (locked decision 2 shape) as passes/n."""

    if not isinstance(cell, dict):
        return "  .  "
    return f"{cell['passes']}/{cell['n']}({cell['rate_pct']:.0f}%)"


def render_digest(scenario: str, run_dir: Path, results: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# RESULTS DIGEST -- scenario={scenario}")
    lines.append(f"run_dir: {run_dir}")
    lines.append("")

    cc = results.get("cell_contrasts")
    if cc is None:
        lines.append("cell_contrasts: UNAVAILABLE (see integration debt).")
    else:
        # Per-system report shape (packet I-A): mechanisms live under
        # systems/<system_id>; the single-system rehearsal renders that block,
        # a multi-system run falls back to the labelled pooled reference view.
        system_blocks = cc.get("systems", {})
        if len(system_blocks) == 1:
            block_label, block = next(iter(sorted(system_blocks.items())))
        else:
            block_label, block = "pooled_all_systems", cc["pooled_all_systems"]
        lines.append(f"rep_count: {cc['rep_count']}   windows: {cc['windows']}")
        lines.append("")
        lines.append(f"## Per-mechanism 2x2 (base condition, system={block_label})")
        lines.append(
            "cells: A=told+enforced  B=told+off  C=untold+enforced  D=untold+off"
        )
        lines.append(
            "contrasts: B_vs_D=effect-of-telling  C_vs_D=effect-of-enforcing  "
            "A_vs_B=marginal-enforcement-given-told"
        )
        for mech, report in block["mechanisms"].items():
            lines.append("")
            lines.append(f"### {report['mechanism_id']} {mech} (off_mode={report['off_mode']})")
            base = report["base"]
            counts = base["cell_rep_counts"]
            lines.append(
                f"cell reps: A={counts['A']} B={counts['B']} "
                f"C={counts['C']} D={counts['D']}"
            )
            for metric_name, metric in base["metrics"].items():
                lines.append(f"  metric: {metric_name} ({metric['direction']})")
                for window in ("first_attempt", "converged"):
                    w = metric[window]
                    cv = w["cell_values"]
                    ct = w["contrasts"]
                    lines.append(
                        f"    {window:13s} "
                        f"A={_fmt_cell(cv['A'])} B={_fmt_cell(cv['B'])} "
                        f"C={_fmt_cell(cv['C'])} D={_fmt_cell(cv['D'])} | "
                        f"B_vs_D={_fmt(ct['B_vs_D'])}pp "
                        f"C_vs_D={_fmt(ct['C_vs_D'])}pp "
                        f"A_vs_B={_fmt(ct['A_vs_B'])}pp"
                    )
            if report["moderators"]:
                lines.append(f"  moderators: {sorted(report['moderators'])}")
            if report["conditions"]:
                lines.append(f"  conditions(drift): {sorted(report['conditions'])}")
        sf = block["sanity_floor"]
        lines.append("")
        lines.append(
            f"## sanity floor ({sf['runtime_mode']}): "
            f"{sf['rep_count']} reps over {len(sf['task_ids'])} tasks"
        )

    coverage = results.get("mechanism_coverage")
    if coverage is not None:
        lines.append("")
        lines.append("## Per-mechanism coverage (pilot_evidence)")
        lines.append(
            f"rows: {coverage['row_count']}  tier: {coverage['evidence_tier']}"
        )
        for mech, summary in coverage["mechanisms"].items():
            lines.append(
                f"  {summary['mechanism_id']} {mech}: "
                f"full_pass={summary['eligible_full_contract_pass_count']}/"
                f"{summary['eligible_full_contract_total']} "
                f"off_pass={summary['eligible_no_x_pass_count']}/"
                f"{summary['eligible_no_x_total']} "
                f"delta={summary['pass_rate_delta_full_minus_no_x']} "
                f"enough_rows="
                f"{summary['enough_eligible_rows_for_model_backed_comparison']}"
            )
        floor = coverage["sanity_floor"]
        lines.append(
            f"  sanity_floor: {floor['eligible_pass_count']}/"
            f"{floor['eligible_rep_count']} pass "
            f"(rate={floor['pass_rate']})"
        )

    et = results.get("evidence_table")
    if et is not None:
        passes = sum(1 for r in et["rows"] if r["overall_pass"])
        lines.append("")
        lines.append(
            f"## evidence_table: {et['row_count']} rows, "
            f"{passes} pass / {et['row_count'] - passes} fail"
        )

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Sweep drivers.
# --------------------------------------------------------------------------- #
def _config(runs_root: Path, task_ids: tuple[str, ...] | None, reps: int) -> pilot.PilotConfig:
    tids = task_ids or pilot.default_task_ids()
    return pilot.PilotConfig(runs_root=runs_root, task_ids=tids, replication_n=reps)


def run_scenario(
    scenario: str,
    *,
    out_root: Path,
    task_ids: tuple[str, ...] | None,
    reps: int,
    now_utc: Callable[[], datetime],
) -> dict[str, Any]:
    debt = DebtLog()
    policy = MockPolicy(scenario)
    condition = dict(roster_condition("primary_qwen3_235b_together"))
    runs_root = out_root / scenario / "runs"
    config = _config(runs_root, task_ids, reps)

    print(f"\n{'='*70}\nSCENARIO: {scenario}  (tasks={len(config.task_ids)} reps={reps})\n{'='*70}", flush=True)
    t0 = time.monotonic()
    result = pilot.run_pilot(
        systems=[condition],
        model_turn_factory=make_factory(policy),
        config=config,
        now_utc=now_utc,
        git_sha="dressrehearsal" + "0" * 40,
    )
    sweep_seconds = time.monotonic() - t0
    print(f"sweep run_outcome={result.run_outcome} in {sweep_seconds:.1f}s", flush=True)
    print(f"run_dir={result.run_dir}", flush=True)

    results = run_analysis(result.run_dir, debt)
    digest = render_digest(scenario, result.run_dir, results)
    (result.run_dir / "RESULTS_DIGEST.md").write_text(digest, encoding="utf-8")
    print("\n" + digest)

    count, total = _artifact_accounting(result.run_dir)
    print(
        f"[ARTIFACTS] scenario={scenario}: {count} files, "
        f"{total/1e6:.2f} MB, sweep {sweep_seconds:.1f}s"
    )
    return {
        "scenario": scenario,
        "run_dir": str(result.run_dir),
        "run_outcome": result.run_outcome,
        "sweep_seconds": sweep_seconds,
        "artifact_count": count,
        "artifact_bytes": total,
        "debt": debt.entries,
    }


def run_resume_test(
    *,
    out_root: Path,
    task_ids: tuple[str, ...],
    reps: int,
    kill_after: int,
) -> dict[str, Any]:
    """Kill the sweep mid-way, then attempt to continue, and report honestly
    whether the orchestrator supports resumption."""

    print(f"\n{'='*70}\nRESUME TEST: kill after {kill_after} completed reps\n{'='*70}", flush=True)
    policy = MockPolicy("clean")
    condition = dict(roster_condition("primary_qwen3_235b_together"))
    runs_root = out_root / "resume" / "runs"
    fixed_ts = datetime(2026, 7, 5, 12, 0, tzinfo=timezone.utc)

    original = pilot.run_one_rep
    counter = {"n": 0}

    class KillSignal(RuntimeError):
        pass

    def killing_run_one_rep(*args: Any, **kwargs: Any) -> Any:
        if counter["n"] >= kill_after:
            raise KillSignal(f"simulated crash after {counter['n']} reps")
        counter["n"] += 1
        return original(*args, **kwargs)

    findings: dict[str, Any] = {"kill_after": kill_after}
    pilot.run_one_rep = killing_run_one_rep  # type: ignore[assignment]
    try:
        try:
            pilot.run_pilot(
                systems=[condition],
                model_turn_factory=make_factory(policy),
                config=_config(runs_root, task_ids, reps),
                now_utc=lambda: fixed_ts,
                git_sha="dressrehearsal" + "0" * 40,
            )
            findings["killed"] = False
        except KillSignal as exc:
            findings["killed"] = True
            findings["kill_error"] = str(exc)
    finally:
        pilot.run_one_rep = original  # type: ignore[assignment]

    partial_dirs = sorted((runs_root).glob("*_lock-*"))
    findings["partial_run_dirs"] = [str(p) for p in partial_dirs]
    if partial_dirs:
        c, b = _artifact_accounting(partial_dirs[0])
        findings["partial_artifacts"] = c
        findings["partial_bytes"] = b
        done = list(partial_dirs[0].glob("conditions/*/runtime_mode_*/tasks/*/rep_*.done"))
        findings["partial_completed_reps"] = len(done)

    # Resume attempt A: SAME timestamp + sha -> does the orchestrator resume,
    # merge, or refuse?
    try:
        pilot.run_pilot(
            systems=[condition],
            model_turn_factory=make_factory(policy),
            config=_config(runs_root, task_ids, reps),
            now_utc=lambda: fixed_ts,
            git_sha="dressrehearsal" + "0" * 40,
        )
        findings["resume_same_ts"] = "created/merged (no collision guard)"
    except FileExistsError as exc:
        findings["resume_same_ts"] = f"FileExistsError (refuses to merge): {exc}"
    except Exception as exc:  # noqa: BLE001
        findings["resume_same_ts"] = f"{type(exc).__name__}: {exc}"

    # Resume attempt B: NEW timestamp -> fresh run dir. Does it reuse the
    # partial run's completed reps, or redo everything?
    new_ts = fixed_ts + timedelta(minutes=1)
    try:
        res_b = pilot.run_pilot(
            systems=[condition],
            model_turn_factory=make_factory(policy),
            config=_config(runs_root, task_ids, reps),
            now_utc=lambda: new_ts,
            git_sha="dressrehearsal" + "0" * 40,
        )
        done_b = list(res_b.run_dir.glob("conditions/*/runtime_mode_*/tasks/*/rep_*.done"))
        findings["resume_new_ts_run_dir"] = str(res_b.run_dir)
        findings["resume_new_ts_completed_reps"] = len(done_b)
        findings["resume_new_ts_outcome"] = res_b.run_outcome
    except Exception as exc:  # noqa: BLE001
        findings["resume_new_ts"] = f"{type(exc).__name__}: {exc}"

    # Resume attempt C (IC-2): the opt-in rep-level resume. Completed reps
    # must reload from disk; only the missing reps may execute.
    if partial_dirs:
        exec_counter = {"n": 0}

        def counting_run_one_rep(*args: Any, **kwargs: Any) -> Any:
            exec_counter["n"] += 1
            return original(*args, **kwargs)

        pilot.run_one_rep = counting_run_one_rep  # type: ignore[assignment]
        try:
            res_c = pilot.run_pilot(
                systems=[condition],
                model_turn_factory=make_factory(policy),
                config=replace(
                    _config(runs_root, task_ids, reps),
                    resume_run_dir=partial_dirs[0],
                ),
                now_utc=lambda: fixed_ts,
                git_sha="dressrehearsal" + "0" * 40,
            )
            done_c = list(
                res_c.run_dir.glob("conditions/*/runtime_mode_*/tasks/*/rep_*.done")
            )
            findings["resume_opt_in_outcome"] = res_c.run_outcome
            findings["resume_opt_in_reps_executed"] = exec_counter["n"]
            findings["resume_opt_in_completed_reps"] = len(done_c)
        except Exception as exc:  # noqa: BLE001 -- rehearsal reports, not crashes
            findings["resume_opt_in"] = f"{type(exc).__name__}: {exc}"
        finally:
            pilot.run_one_rep = original  # type: ignore[assignment]

    findings["verdict"] = (
        "OPT-IN RESUMPTION (IC-2): a bare re-invocation still refuses to "
        "merge (FileExistsError) and a new-id invocation still re-runs from "
        "scratch, but PilotConfig.resume_run_dir resumes the partial run dir "
        "rep-by-rep -- completed reps reload from disk and only the missing "
        "reps execute (see resume_opt_in_* findings)."
    )
    print(json.dumps(findings, indent=2), flush=True)
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        action="append",
        choices=["clean", "violating", "mixed"],
        help="scenario(s) to run; repeatable. Default: clean + violating.",
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument(
        "--tasks",
        type=str,
        default=None,
        help="comma-separated task-id subset (default: full 36-task suite)",
    )
    parser.add_argument(
        "--kill-after-reps",
        type=int,
        default=None,
        help="run the RESUME test: crash the sweep after N completed reps",
    )
    args = parser.parse_args(argv)

    out_root: Path = args.out_dir
    out_root.mkdir(parents=True, exist_ok=True)
    task_ids = tuple(args.tasks.split(",")) if args.tasks else None

    base_ts = datetime(2026, 7, 5, 9, 0, tzinfo=timezone.utc)
    ts_counter = {"n": 0}

    def now_utc() -> datetime:
        # Distinct minute per call so per-scenario run dirs never collide.
        ts_counter["n"] += 1
        return base_ts + timedelta(minutes=ts_counter["n"])

    overall_t0 = time.monotonic()
    summaries: list[dict[str, Any]] = []

    if args.kill_after_reps is not None:
        resume_tasks = task_ids or ("gab_l1_operate_route", "gab_l2_validation_told")
        run_resume_test(
            out_root=out_root,
            task_ids=resume_tasks,
            reps=args.reps,
            kill_after=args.kill_after_reps,
        )
        return 0

    scenarios = args.scenario or ["clean", "violating"]
    for scenario in scenarios:
        summaries.append(
            run_scenario(
                scenario,
                out_root=out_root,
                task_ids=task_ids,
                reps=args.reps,
                now_utc=now_utc,
            )
        )

    total_seconds = time.monotonic() - overall_t0
    print(f"\n{'='*70}\nWALL-CLOCK + ARTIFACT ACCOUNTING\n{'='*70}")
    grand_files = 0
    grand_bytes = 0
    for s in summaries:
        grand_files += s["artifact_count"]
        grand_bytes += s["artifact_bytes"]
        print(
            f"  {s['scenario']:10s} outcome={s['run_outcome']:10s} "
            f"sweep={s['sweep_seconds']:6.1f}s "
            f"files={s['artifact_count']:5d} bytes={s['artifact_bytes']/1e6:6.2f}MB"
        )
    print(f"  TOTAL wall-clock (incl. analysis): {total_seconds:.1f}s")
    print(f"  TOTAL artifacts: {grand_files} files, {grand_bytes/1e6:.2f} MB")
    per_scenario = total_seconds / max(1, len(summaries))
    print(
        f"  EXTRAPOLATION to 4 model conditions (one scenario each): "
        f"~{per_scenario*4/60:.1f} min, ~{grand_bytes/max(1,len(summaries))*4/1e6:.1f} MB"
    )

    summary_path = out_root / "rehearsal_summary.json"
    summary_path.write_text(
        json.dumps(
            {"total_seconds": total_seconds, "scenarios": summaries},
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"  summary: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
