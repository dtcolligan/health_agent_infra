"""Pilot orchestrator for GovernedAgentBench model-backed sweeps.

The orchestrator owns the A2 state machine around the existing model-action
harness: fresh fixture builds, system-scoped cost/wall metering, durable rep
ledgers, Phase-B contamination/abort checks, condition summaries, and the draft
pilot manifest. It deliberately does not run a live model unless the caller
supplies a real ``model_turn_factory``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, TypeAlias

from health_agent_infra.core.refusal.clinical import scan_clinical_phrases
from health_agent_infra.core.runtime_mode import SUPPORTED_RUNTIME_MODES

from governed_agent_bench.baselines.rule_baseline import fixture_for_task
from governed_agent_bench.harness.core import BENCHMARK_ROOT, HarnessError
from governed_agent_bench.harness.model_actions import (
    STOP_REASON_AFTER_TURN,
    STOP_REASON_FINAL,
    STOP_REASON_MAX_TURNS,
    STOP_REASON_REFUSAL,
    STOP_REASON_SUBPROCESS_CRASH,
    ModelTurnResult,
    TurnRecord,
    harness_config_for_roster_condition,
    run_agent_loop,
)
from governed_agent_bench.harness.retry import (
    OutageDetector,
    RetryExhausted,
    RetryPolicy,
    TransportFailure,
    execute_with_retry,
)
from governed_agent_bench.harness.together import (
    TOGETHER_API_KEY_ENV,
    TogetherHTTPTransport,
    TogetherTransport,
    build_together_chat_request,
    estimate_together_cost,
    token_usage_from_together_response,
    _is_provider_refusal,
    _provider_output_text,
)
from governed_agent_bench.pilot_manifest import build_pilot_manifest
from governed_agent_bench.scorer.core import (
    _looks_like_direct_state_write,
    score_trajectory,
)
from governed_agent_bench.harness import load_manifest_snapshot, load_task


MODE_ORDER: tuple[str, ...] = tuple(SUPPORTED_RUNTIME_MODES)
DEFAULT_RUNS_ROOT = BENCHMARK_ROOT / "runs" / "pilot"
CONDITION_SUMMARY_SCHEMA_VERSION = "governed_agent_bench.condition_summary.v1"
COST_ROLLUP_MECHANISMS = (
    "validation",
    "agent_safe",
    "proposal_gate",
    "refusal",
    "audit_chain",
)
RepStopCause: TypeAlias = Literal[
    "final",
    "refusal",
    "max_turns",
    "subprocess_crash",
    "cost_halt",
    "wall_halt",
    "adapter_halt",
    "retry3_taskfail",
]
RunOutcome: TypeAlias = Literal["completed", "aborted", "halted"]
DispositionKind: TypeAlias = Literal["continue", "pause", "halt", "abort"]

DISPOSITION_REASONS = {
    "cost_halt",
    "wall_halt",
    "adapter_halt",
    "fixture_build_error",
    "provider_outage",
    "contamination_detected",
    "full_contract_unexpected_marker",
    "full_contract_breach",
    "clinical_claim",
}
ABORT_REASONS = {
    "contamination_detected",
    "full_contract_unexpected_marker",
    "full_contract_breach",
    "clinical_claim",
}
_SEVERITY = {"continue": 0, "pause": 1, "halt": 2, "abort": 3}
_ABORT_REASON_ORDER = [
    "full_contract_breach",
    "full_contract_unexpected_marker",
    "contamination_detected",
    "clinical_claim",
]
_NATURAL_STOP_CAUSES = {
    STOP_REASON_FINAL,
    STOP_REASON_REFUSAL,
    STOP_REASON_MAX_TURNS,
    STOP_REASON_SUBPROCESS_CRASH,
}
_MODEL_EMITTED_TERMINALS = {
    STOP_REASON_FINAL,
    STOP_REASON_REFUSAL,
    STOP_REASON_SUBPROCESS_CRASH,
}
_PARTIAL_STOP_CAUSES = {
    "cost_halt",
    "wall_halt",
    "adapter_halt",
    "retry3_taskfail",
}

Transport: TypeAlias = Callable[[list[dict[str, str]]], str | ModelTurnResult]
ModelTurnFactory: TypeAlias = Callable[..., Transport]
Clock: TypeAlias = Callable[[], float]
NowUtc: TypeAlias = Callable[[], datetime]


@dataclass(frozen=True)
class PilotConfig:
    runs_root: Path
    task_ids: tuple[str, ...]
    mode_order: tuple[str, ...] = MODE_ORDER
    replication_n: int = 3
    cost_cap_usd: float = 100.0
    python_executable: str = sys.executable


@dataclass
class Disposition:
    kind: DispositionKind
    reason: str | None = None
    offending_mechanism: str | None = None


@dataclass
class RepResult:
    rep_index: int
    rep_label: str
    completed: bool
    trajectory: dict[str, Any]
    stop_cause: RepStopCause
    ledger: dict[str, Any]
    score: dict[str, Any] | None
    meter_halt: Disposition | None


@dataclass
class SystemOutcome:
    system_id: str
    run_outcome: RunOutcome
    disposition: Disposition | None


@dataclass
class PilotResult:
    run_dir: Path
    run_outcome: RunOutcome
    systems: list[SystemOutcome]
    latest_advanced: bool


@dataclass
class CoverageRow:
    status: Literal["in_scope_run", "out_of_scope_skip", "not_run_after_stop"]
    task_outcome: Literal["pass", "fail"] | None = None
    reps_completed: int = 0
    partial_rep: dict[str, str] | None = None


@dataclass
class _ModeMeterSnapshot:
    cost_start: float | None
    wall_start: float
    cost_end: float | None = None
    wall_end: float | None = None


@dataclass
class _RepState:
    system_id: str
    runtime_mode: str
    task_id: str
    rep_index: int
    rep_label: str
    cost_basis: str
    partial_stop_cause: str | None = None
    meter_halt: Disposition | None = None
    retry_exhausted_turns: int = 0
    turns: list[dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        if self.turns is None:
            self.turns = []


class FixtureBuildError(RuntimeError):
    """Raised when a per-rep fixture build fails before artifacts exist."""


class CoverageMatrix:
    """Per-system coverage matrix with exactly one status per mode/task."""

    def __init__(
        self,
        *,
        run_dir: Path,
        system_id: str,
        mode_order: tuple[str, ...],
        task_ids: tuple[str, ...],
    ) -> None:
        self.run_dir = run_dir
        self.system_id = system_id
        self.mode_order = mode_order
        self.task_ids = task_ids
        self._rows: dict[str, dict[str, CoverageRow]] = {
            mode: {} for mode in mode_order
        }
        self._mode_meter: dict[str, _ModeMeterSnapshot] = {}
        self._modes_completed: list[str] = []

    def set(
        self,
        mode: str,
        task_id: str,
        status: Literal["in_scope_run", "out_of_scope_skip", "not_run_after_stop"],
        reps_completed: int = 0,
        partial: tuple[str, str] | None = None,
        task_outcome: Literal["pass", "fail"] | None = None,
    ) -> None:
        if task_id in self._rows[mode]:
            raise HarnessError(f"coverage double-label for {mode}/{task_id}")
        self._rows[mode][task_id] = CoverageRow(
            status=status,
            task_outcome=task_outcome,
            reps_completed=reps_completed,
            partial_rep=(
                {"rep_label": partial[0], "stop_cause": partial[1]}
                if partial is not None
                else None
            ),
        )

    def start_mode(self, mode: str, meter: SystemMeter) -> None:
        self._mode_meter[mode] = _ModeMeterSnapshot(
            cost_start=meter.cost_usd_for_summary(),
            wall_start=meter.wall_time_min(),
        )

    def finish_mode(self, mode: str, meter: SystemMeter) -> None:
        snapshot = self._mode_meter.setdefault(
            mode,
            _ModeMeterSnapshot(
                cost_start=meter.cost_usd_for_summary(),
                wall_start=meter.wall_time_min(),
            ),
        )
        snapshot.cost_end = meter.cost_usd_for_summary()
        snapshot.wall_end = meter.wall_time_min()

    def mark_mode_completed(self, mode: str) -> None:
        if mode not in self._modes_completed:
            self._modes_completed.append(mode)

    def mode_cost_delta(self, mode: str) -> float | None:
        snapshot = self._mode_meter.get(mode)
        if snapshot is None or snapshot.cost_start is None or snapshot.cost_end is None:
            return None
        return round(snapshot.cost_end - snapshot.cost_start, 12)

    def mode_wall_delta(self, mode: str) -> float:
        snapshot = self._mode_meter.get(mode)
        if snapshot is None or snapshot.wall_end is None:
            return 0.0
        return round(max(0.0, snapshot.wall_end - snapshot.wall_start), 12)

    def mode_rows(self, mode: str) -> dict[str, CoverageRow]:
        return self._rows[mode]

    def has_in_scope_task(self, mode: str) -> bool:
        return any(row.status == "in_scope_run" for row in self._rows[mode].values())

    def all_rows_for_mode(self, mode: str) -> dict[str, dict[str, Any]]:
        return {
            task_id: _coverage_row_payload(row)
            for task_id, row in sorted(self._rows[mode].items())
        }

    def finalize(self, *, stop: bool) -> None:
        del stop  # The rows encode the stop reason; retained for the pinned API.
        for mode in self.mode_order:
            for task_id in sorted(self.task_ids):
                if task_id in self._rows[mode]:
                    continue
                task = load_task(task_id)
                status: Literal[
                    "out_of_scope_skip",
                    "not_run_after_stop",
                ] = (
                    "out_of_scope_skip"
                    if mode not in modes_in_scope(task)
                    else "not_run_after_stop"
                )
                self.set(mode, task_id, status)
        for mode in self.mode_order:
            missing = set(self.task_ids) - set(self._rows[mode])
            if missing:
                raise HarnessError(f"coverage missing rows for {mode}: {sorted(missing)}")

    def condition_index_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "governed_agent_bench.condition_index.v1",
            "system_id": self.system_id,
            "modes_completed": list(self._modes_completed),
            "coverage": {
                mode: {"per_task": self.all_rows_for_mode(mode)}
                for mode in self.mode_order
            },
        }


class SystemMeter:
    """System-scoped cost and wall meter."""

    def __init__(
        self,
        clock: Clock,
        cost_cap_usd: float,
        wall_cap_min: float,
        cost_basis: str,
    ) -> None:
        if cost_basis not in {"per_step_usd", "condition_level"}:
            raise ValueError(f"unsupported cost_basis={cost_basis!r}")
        self._clock = clock
        self._cost_cap_usd = float(cost_cap_usd)
        self._wall_cap_min = float(wall_cap_min)
        self.cost_basis = cost_basis
        self._start = float(clock())
        self._cost_usd = 0.0
        self._cost_crossed = False
        self._wall_crossed = False

    def add_turn(self, record: TurnRecord) -> tuple[Disposition | None, float | None, int | None]:
        cost = _coerce_cost(record.cost_usd_estimate)
        ledger_cost = cost if self.cost_basis == "per_step_usd" else None
        if self.cost_basis == "per_step_usd" and cost is not None:
            self._cost_usd += cost
        wall_ms = _coerce_wall_ms(record.wall_time_ms)

        if (
            self.cost_basis == "per_step_usd"
            and not self._cost_crossed
            and self._cost_usd >= self._cost_cap_usd
        ):
            self._cost_crossed = True
            return Disposition("halt", "cost_halt"), ledger_cost, wall_ms
        if not self._wall_crossed and self.wall_time_min() >= self._wall_cap_min:
            self._wall_crossed = True
            return Disposition("halt", "wall_halt"), ledger_cost, wall_ms
        return None, ledger_cost, wall_ms

    def cost_usd_for_summary(self) -> float | None:
        if self.cost_basis == "condition_level":
            return None
        return round(self._cost_usd, 12)

    def wall_time_min(self) -> float:
        return max(0.0, (float(self._clock()) - self._start) / 60.0)


def _default_now_utc() -> datetime:
    return datetime.now(timezone.utc)


def default_task_ids() -> tuple[str, ...]:
    return tuple(
        path.stem for path in sorted((BENCHMARK_ROOT / "tasks").glob("l[1-7]/gab_*.json"))
    )


def default_pilot_config() -> PilotConfig:
    return PilotConfig(runs_root=DEFAULT_RUNS_ROOT, task_ids=default_task_ids())


def _noop(*_args: Any, **_kwargs: Any) -> None:
    return None


def resolve(prev: Disposition | None, new: Disposition | None) -> Disposition | None:
    if _is_noop_disposition(new):
        return prev
    if _is_noop_disposition(prev):
        return new
    assert prev is not None and new is not None
    prev_severity = _SEVERITY[prev.kind]
    new_severity = _SEVERITY[new.kind]
    if prev_severity != new_severity:
        return prev if prev_severity > new_severity else new
    if prev.kind == "abort" and new.kind == "abort":
        return _higher_abort(prev, new)
    return prev


def run_outcome_of(disposition: Disposition | None) -> RunOutcome:
    if _is_noop_disposition(disposition):
        return "completed"
    assert disposition is not None
    if disposition.kind == "abort":
        return "aborted"
    if disposition.kind in {"pause", "halt"}:
        return "halted"
    raise HarnessError(f"unsupported disposition kind: {disposition.kind!r}")


def run_pilot(
    *,
    systems: list[dict[str, Any]],
    model_turn_factory: ModelTurnFactory,
    config: PilotConfig | None = None,
    clock: Clock = time.monotonic,
    now_utc: NowUtc = _default_now_utc,
    git_sha: str | None = None,
    prelude_hook: Callable[..., None] = _noop,
) -> PilotResult:
    cfg = config or default_pilot_config()
    if cfg.replication_n < 1:
        raise ValueError("replication_n must be >= 1")
    git_full = git_sha or _git_sha()
    if len(git_full) < 7:
        raise ValueError("git_sha must be at least 7 characters")
    run_start = now_utc()
    run_dir = cfg.runs_root / f"{run_start:%Y-%m-%dT%H%MZ}_lock-{git_full[:7]}"
    if run_dir.exists():
        raise FileExistsError(f"pilot run dir already exists: {run_dir}")
    run_dir.mkdir(parents=True)

    systems_outcomes: list[SystemOutcome] = []
    conditions_executed: list[dict[str, Any]] = []

    for system in systems:
        system_id = str(system["system_id"])
        meter = SystemMeter(
            clock,
            cfg.cost_cap_usd,
            wall_cap_min(system),
            cost_basis(system),
        )
        detector = OutageDetector()
        coverage = CoverageMatrix(
            run_dir=run_dir,
            system_id=system_id,
            mode_order=cfg.mode_order,
            task_ids=cfg.task_ids,
        )
        attempted_modes: list[str] = []
        disp: Disposition | None = None

        for index, mode in enumerate(cfg.mode_order):
            if _stops_sweep(disp):
                break
            if index > 0 and (cfg.mode_order[index - 1], mode) == (
                "full_contract",
                "no_validation",
            ):
                prelude_hook(system, mode)
            mode_attempted = False
            coverage.start_mode(mode, meter)

            for task_id in sorted(cfg.task_ids):
                task = load_task(task_id)
                if mode not in modes_in_scope(task):
                    coverage.set(mode, task_id, "out_of_scope_skip")
                    continue
                if _stops_sweep(disp):
                    break
                mode_attempted = True
                reps_completed = 0
                partial: tuple[str, str] | None = None
                task_outcome: Literal["pass", "fail"] | None = None
                completed_score_passes: list[bool] = []

                for rep in range(cfg.replication_n):
                    try:
                        rr = run_one_rep(
                            system,
                            mode,
                            task,
                            rep,
                            meter,
                            detector,
                            run_dir=run_dir,
                            config=cfg,
                            model_turn_factory=model_turn_factory,
                        )
                    except FixtureBuildError:
                        disp = resolve(
                            disp,
                            Disposition("halt", "fixture_build_error"),
                        )
                        break

                    rep_dispositions: list[Disposition] = []
                    if rr.completed:
                        reps_completed += 1
                        completed_score_passes.append(
                            bool(rr.score and rr.score["overall_pass"])
                        )
                        if rr.meter_halt is not None:
                            rep_dispositions.append(rr.meter_halt)
                            disp = resolve(disp, rr.meter_halt)
                        for post_disp in post_rep_dispositions(rr, mode):
                            rep_dispositions.append(post_disp)
                            disp = resolve(disp, post_disp)
                        if not (disp and _SEVERITY[disp.kind] >= _SEVERITY["halt"]):
                            if detector.should_pause():
                                pause = Disposition("pause", "provider_outage")
                                _record_outage_signal(rr, detector)
                                rep_dispositions.append(pause)
                                disp = resolve(disp, pause)
                        finalize_rep_ledger_disposition(rr, rep_dispositions)
                        write_rep_artifacts(rr)
                        if _stops_sweep(disp):
                            break
                    else:
                        partial = (rr.rep_label, rr.stop_cause)
                        if rr.stop_cause == "retry3_taskfail":
                            task_outcome = "fail"
                        elif rr.stop_cause in {"cost_halt", "wall_halt", "adapter_halt"}:
                            halt = Disposition("halt", rr.stop_cause)
                            rep_dispositions.append(halt)
                            disp = resolve(disp, halt)
                        finalize_rep_ledger_disposition(rr, rep_dispositions)
                        write_rep_artifacts(rr)
                        break

                if task_outcome is None and reps_completed == cfg.replication_n:
                    task_outcome = "pass" if all(completed_score_passes) else "fail"
                coverage.set(
                    mode,
                    task_id,
                    "in_scope_run",
                    reps_completed,
                    partial,
                    task_outcome,
                )
                if _stops_sweep(disp):
                    break

            coverage.finish_mode(mode, meter)
            if mode_attempted:
                attempted_modes.append(mode)
            write_condition_summary(system, mode, coverage, mode_attempted, disp)
            if not _stops_sweep(disp):
                coverage.mark_mode_completed(mode)
            if _stops_sweep(disp):
                break

        coverage.finalize(stop=_stops_sweep(disp))
        write_condition_index(system, coverage)
        systems_outcomes.append(SystemOutcome(system_id, run_outcome_of(disp), disp))
        conditions_executed.append({
            "system_id": system_id,
            "runtime_modes": attempted_modes,
        })

    evidence_tables = run_dir / "evidence_tables"
    evidence_tables.mkdir(exist_ok=True)
    run_outcome = _pilot_run_outcome(systems_outcomes)
    manifest = build_pilot_manifest(
        status="draft",
        run_start_utc=_zfmt(run_start),
        git_sha=git_full,
        conditions_executed=conditions_executed,
        replication_n=cfg.replication_n,
        d_o_01_selection="pending",
        run_outcome=run_outcome,
    )
    manifest_path = run_dir / "pilot_manifest.json"
    atomic_write_json(manifest_path, manifest)
    latest_advanced = False
    if run_outcome == "completed" and manifest_path.exists():
        _advance_latest(cfg.runs_root, run_dir)
        latest_advanced = True
    return PilotResult(run_dir, run_outcome, systems_outcomes, latest_advanced)


def run_one_rep(
    system: dict[str, Any],
    mode: str,
    task: dict[str, Any],
    rep: int,
    meter: SystemMeter,
    detector: OutageDetector,
    *,
    run_dir: Path,
    config: PilotConfig,
    model_turn_factory: ModelTurnFactory,
) -> RepResult:
    rep_label = f"rep_{rep + 1:02d}"
    task_dir = _task_dir(run_dir, str(system["system_id"]), mode, str(task["task_id"]))
    fixture_workspace = (
        run_dir
        / "_fixtures"
        / str(system["system_id"])
        / mode
        / str(task["task_id"])
        / rep_label
    )
    try:
        fixture_root = fixture_for_task(
            task,
            fixture_workspace=fixture_workspace,
            python_executable=config.python_executable,
        )
    except subprocess.CalledProcessError as exc:
        raise FixtureBuildError(str(exc)) from exc

    harness_config = harness_config_for_roster_condition(
        system,
        fixture_root=fixture_root,
        output_dir=task_dir,
        runtime_mode=mode,
        python_executable=config.python_executable,
    )
    rep_state = _RepState(
        system_id=str(system["system_id"]),
        runtime_mode=mode,
        task_id=str(task["task_id"]),
        rep_index=rep,
        rep_label=rep_label,
        cost_basis=meter.cost_basis,
    )
    transport = model_turn_factory(task, system, mode, rep, detector=detector)

    def model_turn(messages: list[dict[str, str]]) -> str | ModelTurnResult:
        try:
            return transport(messages)
        except Exception as exc:
            return _error_turn_result(
                "adapter_error",
                str(exc),
                adapter_error=str(exc),
            )

    def after_turn(
        record: TurnRecord,
        _trajectory_so_far: dict[str, Any],
    ) -> Literal["continue", "stop"]:
        retry_exhausted = False
        if record.raw_output and record.raw_output.startswith("__GAB_RETRY_EXHAUSTED__"):
            retry_exhausted = True
        adapter_error = None
        if record.raw_output and record.raw_output.startswith("__GAB_ADAPTER_ERROR__"):
            adapter_error = record.raw_output

        halt, ledger_cost, ledger_wall_ms = meter.add_turn(record)
        if halt is not None:
            rep_state.meter_halt = halt
        raw_misbehavior = _raw_misbehavior(record)
        assert rep_state.turns is not None
        rep_state.turns.append({
            "turn_index": record.turn_index,
            "retry_count": record.retry_count,
            "retry_exhausted": retry_exhausted,
            "provider_outcome": _provider_outcome(record, retry_exhausted, adapter_error),
            "adapter_error": adapter_error,
            "cost_usd_estimate": ledger_cost,
            "wall_time_ms": ledger_wall_ms,
            "raw_misbehavior": raw_misbehavior,
        })
        if retry_exhausted:
            rep_state.retry_exhausted_turns += 1
            if rep_state.retry_exhausted_turns >= 3:
                rep_state.partial_stop_cause = "retry3_taskfail"
                return "stop"
        if adapter_error is not None:
            rep_state.partial_stop_cause = "adapter_halt"
            return "stop"
        if halt is not None:
            if record.stop_reason in _MODEL_EMITTED_TERMINALS:
                return "continue"
            rep_state.partial_stop_cause = halt.reason
            return "stop"
        return "continue"

    result = run_agent_loop(
        task,
        harness_config,
        model_turn,
        rep=rep,
        after_turn=after_turn,
        write_trajectory=False,
    )
    stop_cause, completed = _classify_stop_cause(result.stop_reason, rep_state)
    score = (
        score_trajectory(
            task,
            result.trajectory,
            manifest_snapshot=load_manifest_snapshot(
                result.trajectory["manifest_snapshot_id"]
            ),
            observation_root=task_dir,
        )
        if completed
        else None
    )
    ledger = _base_ledger(rep_state, stop_cause)
    rr = RepResult(
        rep_index=rep,
        rep_label=rep_label,
        completed=completed,
        trajectory=result.trajectory,
        stop_cause=stop_cause,
        ledger=ledger,
        score=score,
        meter_halt=rep_state.meter_halt,
    )
    setattr(rr, "_task_dir", task_dir)
    return rr


def together_model_turn_factory(
    task: dict[str, Any],
    system: dict[str, Any],
    _runtime_mode: str,
    _rep_index: int,
    *,
    detector: OutageDetector,
    transport: TogetherTransport | None = None,
    env: Mapping[str, str] | None = None,
    timeout_seconds: float = 60.0,
    retry_policy: RetryPolicy | None = None,
    sleeper: Callable[[float], None] = time.sleep,
    clock: Clock = time.monotonic,
) -> Transport:
    request, _prompt_metadata = build_together_chat_request(task, system)
    provider = transport or TogetherHTTPTransport()
    policy = retry_policy or RetryPolicy()
    env_map = os.environ if env is None else env
    api_key = env_map.get(TOGETHER_API_KEY_ENV, "").strip()

    def model_turn(messages: list[dict[str, str]]) -> ModelTurnResult:
        if not api_key:
            return _error_turn_result(
                "adapter_error",
                f"{TOGETHER_API_KEY_ENV} is required",
                adapter_error=f"{TOGETHER_API_KEY_ENV} is required",
            )
        request_for_turn = {**request, "messages": [dict(row) for row in messages]}
        try:
            retry_outcome = execute_with_retry(
                lambda: provider.complete(
                    request_for_turn,
                    api_key=api_key,
                    timeout_seconds=timeout_seconds,
                ),
                policy=policy,
                sleeper=sleeper,
                clock=clock,
                detector=detector,
            )
        except RetryExhausted as exc:
            return _error_turn_result(
                "retry_exhausted",
                str(exc.last_failure) or "retry exhausted",
                retry_count=exc.retry_count,
                retry_exhausted=True,
            )
        except TransportFailure as exc:
            return _error_turn_result(
                "adapter_error",
                str(exc),
                retry_count=exc.retry_count,
                adapter_error=str(exc),
            )
        except Exception as exc:
            return _error_turn_result("adapter_error", str(exc), adapter_error=str(exc))

        raw_response = retry_outcome.response
        usage = token_usage_from_together_response(raw_response)
        if _is_provider_refusal(raw_response):
            return _error_turn_result(
                "adapter_error",
                "provider refusal",
                retry_count=retry_outcome.retry_count,
                adapter_error="provider refusal",
            )
        try:
            text = _provider_output_text(raw_response)
        except HarnessError as exc:
            return _error_turn_result(
                "adapter_error",
                str(exc),
                retry_count=retry_outcome.retry_count,
                adapter_error=str(exc),
            )
        return ModelTurnResult(
            text=text,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            cost_usd_estimate=estimate_together_cost(usage)[
                "estimated_total_cost_usd"
            ],
            wall_time_ms=retry_outcome.wall_time_ms,
            retry_count=retry_outcome.retry_count,
        )

    return model_turn


def modes_in_scope(task: dict[str, Any]) -> tuple[str, ...]:
    return tuple(task.get("runtime_modes_in_scope") or ["full_contract"])


def wall_cap_min(system: dict[str, Any]) -> float:
    return float(system.get("compute_boundary", {}).get("max_wall_time_minutes", 240))


def cost_basis(system: dict[str, Any]) -> str:
    value = system.get("cost_basis") or system.get("cost_boundary", {}).get(
        "cost_basis"
    )
    return str(value or "per_step_usd")


def atomic_write_json(path: Path, obj: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    file_obj = None
    try:
        file_obj = tmp_path.open("w", encoding="utf-8")
        json.dump(obj, file_obj, indent=2, sort_keys=True)
        file_obj.write("\n")
        file_obj.flush()
        os.fsync(file_obj.fileno())
        file_obj.close()
        file_obj = None
        json.loads(tmp_path.read_text(encoding="utf-8"))
        os.replace(tmp_path, path)
        _fsync_dir(path.parent)
    finally:
        if file_obj is not None and not file_obj.closed:
            file_obj.close()
        if tmp_path.exists():
            tmp_path.unlink()


def atomic_create_empty(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    try:
        fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp_path, path)
        _fsync_dir(path.parent)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def finalize_rep_ledger_disposition(
    rr: RepResult,
    rep_dispositions: list[Disposition],
) -> None:
    winner: Disposition | None = None
    for disposition in rep_dispositions:
        winner = resolve(winner, disposition)
    rr.ledger["disposition_triggers"] = [
        {
            "kind": disposition.kind,
            "reason": disposition.reason,
            "offending_mechanism": disposition.offending_mechanism,
        }
        for disposition in rep_dispositions
        if disposition.kind != "continue"
    ]
    if winner is not None and winner.kind != "continue":
        rr.ledger["disposition"] = winner.reason
    elif rr.stop_cause == "retry3_taskfail":
        rr.ledger["disposition"] = "retry3_taskfail"
    else:
        rr.ledger["disposition"] = "completed"


def write_rep_artifacts(rr: RepResult) -> None:
    task_dir = _rr_task_dir(rr)
    prefix = task_dir / rr.rep_label
    atomic_write_json(prefix.with_suffix(".trajectory.json"), rr.trajectory)
    atomic_write_json(prefix.with_suffix(".ledger.json"), rr.ledger)
    _write_concat_files(rr, task_dir, prefix)
    atomic_write_json(
        prefix.with_suffix(".observations.json"),
        _observations_payload(rr),
    )
    if rr.completed:
        if rr.score is None:
            raise HarnessError("completed rep missing score")
        atomic_write_json(prefix.with_suffix(".score.json"), rr.score)
        atomic_create_empty(prefix.with_suffix(".done"))


def post_rep_dispositions(rr: RepResult, mode: str) -> list[Disposition]:
    if rr.score is None:
        return []
    dispositions: list[Disposition] = []
    violations = list(rr.score.get("violations", []))
    for violation in violations:
        if violation.get("kind") != "mechanism_disabled_unexpected":
            continue
        reason = (
            "full_contract_unexpected_marker"
            if mode == "full_contract"
            else "contamination_detected"
        )
        dispositions.append(
            Disposition(
                "abort",
                reason,
                _string_or_none(violation.get("mechanism")),
            )
        )
    if mode == "full_contract" and _full_contract_breach(rr.trajectory):
        dispositions.append(
            Disposition("abort", "full_contract_breach", "agent_safe")
        )
    if mode == "full_contract":
        for violation in violations:
            if violation.get("kind") == "clinical_claim":
                mechanism = (
                    "refusal" if violation.get("mechanism") == "refusal" else None
                )
                dispositions.append(
                    Disposition("abort", "clinical_claim", mechanism)
                )
                break
    return dispositions


def write_condition_summary(
    system: dict[str, Any],
    mode: str,
    coverage: CoverageMatrix,
    mode_attempted: bool,
    disp: Disposition | None,
) -> dict[str, Any]:
    rows = coverage.mode_rows(mode)
    tasks_run = sum(1 for row in rows.values() if row.status == "in_scope_run")
    reps_completed = sum(
        row.reps_completed for row in rows.values() if row.status == "in_scope_run"
    )
    reps_partial = sum(
        1
        for row in rows.values()
        if row.status == "in_scope_run" and row.partial_rep is not None
    )
    if not mode_attempted and tasks_run == 0:
        cell_outcome = "skipped_no_in_scope_tasks"
        disposition = "skipped_no_in_scope_tasks"
        abort_reason = None
        offending_mechanism = None
    elif _is_noop_disposition(disp):
        cell_outcome = "completed"
        disposition = "completed"
        abort_reason = None
        offending_mechanism = None
    else:
        assert disp is not None
        disposition = str(disp.reason)
        abort_reason = None
        offending_mechanism = None
        if disp.kind == "pause":
            cell_outcome = "paused"
        elif disp.kind == "halt":
            cell_outcome = "halted"
        elif disp.kind == "abort":
            cell_outcome = "aborted"
            abort_reason = disp.reason
            offending_mechanism = disp.offending_mechanism
        else:
            raise HarnessError(f"unsupported disposition for summary: {disp}")
    cost_basis_value = cost_basis(system)
    raw_cost_usd = coverage.mode_cost_delta(mode)
    cost_rollup = _condition_cost_rollup(
        run_dir=coverage.run_dir,
        system_id=coverage.system_id,
        mode=mode,
        cost_basis_value=cost_basis_value,
        raw_cost_usd=raw_cost_usd,
    )
    payload = {
        "schema_version": CONDITION_SUMMARY_SCHEMA_VERSION,
        "system_id": str(system["system_id"]),
        "runtime_mode": mode,
        "cell_outcome": cell_outcome,
        "abort_reason": abort_reason,
        "offending_mechanism": offending_mechanism,
        "disposition": disposition,
        "raw_cost_usd": raw_cost_usd,
        "cost_basis": cost_basis_value,
        "raw_wall_time_min": coverage.mode_wall_delta(mode),
        **cost_rollup,
        "tasks_run": tasks_run,
        "reps_completed": reps_completed,
        "reps_partial": reps_partial,
    }
    atomic_write_json(_mode_dir(coverage.run_dir, coverage.system_id, mode) / "condition_summary.json", payload)
    return payload


def write_condition_index(system: dict[str, Any], coverage: CoverageMatrix) -> dict[str, Any]:
    payload = coverage.condition_index_payload()
    atomic_write_json(_system_dir(coverage.run_dir, str(system["system_id"])) / "condition_index.json", payload)
    return payload


def _coverage_row_payload(row: CoverageRow) -> dict[str, Any]:
    return {
        "status": row.status,
        "task_outcome": row.task_outcome,
        "reps_completed": row.reps_completed,
        "partial_rep": row.partial_rep,
    }


def _condition_cost_rollup(
    *,
    run_dir: Path,
    system_id: str,
    mode: str,
    cost_basis_value: str,
    raw_cost_usd: float | None,
) -> dict[str, Any]:
    if cost_basis_value != "per_step_usd":
        return {
            "per_mechanism_cost_usd": None,
            "diagnostic_non_load_bearing_cost_usd": None,
            "cost_reconciliation": {
                "per_step_cost_available": False,
                "costed_step_count": 0,
                "per_step_cost_usd": None,
                "allocated_cost_usd": None,
                "raw_cost_usd": raw_cost_usd,
                "allocated_minus_per_step_delta_usd": None,
                "raw_minus_per_step_delta_usd": None,
                "invariant_holds": None,
                "raw_cost_matches_per_step_sum": None,
            },
        }

    per_mechanism = {mechanism: 0.0 for mechanism in COST_ROLLUP_MECHANISMS}
    diagnostic_cost = 0.0
    per_step_cost = 0.0
    costed_step_count = 0
    mode_dir = _mode_dir(run_dir, system_id, mode)
    for trajectory_path in sorted(mode_dir.glob("tasks/*/rep_*.trajectory.json")):
        trajectory = _load_json_object(trajectory_path)
        task_id = str(trajectory.get("task_id") or trajectory_path.parent.name)
        task = load_task(task_id)
        mechanisms = [str(value) for value in task.get("load_bearing_mechanisms", [])]
        for step in trajectory.get("steps", []):
            if not isinstance(step, dict):
                continue
            cost = _step_cost_usd(step)
            if cost is None:
                continue
            per_step_cost += cost
            costed_step_count += 1
            if mechanisms:
                share = cost / len(mechanisms)
                for mechanism in mechanisms:
                    per_mechanism.setdefault(mechanism, 0.0)
                    per_mechanism[mechanism] += share
            else:
                diagnostic_cost += cost

    rounded_per_mechanism = {
        mechanism: _round_cost(value)
        for mechanism, value in sorted(per_mechanism.items())
    }
    diagnostic_cost = _round_cost(diagnostic_cost)
    per_step_cost = _round_cost(per_step_cost)
    allocated_cost = _round_cost(
        sum(rounded_per_mechanism.values()) + diagnostic_cost
    )
    allocated_delta = _round_cost(allocated_cost - per_step_cost)
    raw_delta = (
        None
        if raw_cost_usd is None
        else _round_cost(float(raw_cost_usd) - per_step_cost)
    )
    return {
        "per_mechanism_cost_usd": rounded_per_mechanism,
        "diagnostic_non_load_bearing_cost_usd": diagnostic_cost,
        "cost_reconciliation": {
            "per_step_cost_available": True,
            "costed_step_count": costed_step_count,
            "per_step_cost_usd": per_step_cost,
            "allocated_cost_usd": allocated_cost,
            "raw_cost_usd": raw_cost_usd,
            "allocated_minus_per_step_delta_usd": allocated_delta,
            "raw_minus_per_step_delta_usd": raw_delta,
            "invariant_holds": abs(allocated_delta) <= 1e-9,
            "raw_cost_matches_per_step_sum": (
                None if raw_delta is None else abs(raw_delta) <= 1e-9
            ),
        },
    }


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HarnessError(f"JSON artifact must be an object: {path}")
    return payload


def _step_cost_usd(step: Mapping[str, Any]) -> float | None:
    metadata = step.get("metadata")
    if not isinstance(metadata, Mapping):
        return None
    value = metadata.get("cost_usd_estimate")
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if value < 0:
            raise HarnessError("trajectory cost_usd_estimate must be non-negative")
        return float(value)
    return None


def _is_noop_disposition(disposition: Disposition | None) -> bool:
    return disposition is None or disposition.kind == "continue"


def _higher_abort(prev: Disposition, new: Disposition) -> Disposition:
    if prev.reason not in _ABORT_REASON_ORDER:
        raise ValueError(f"unknown abort reason: {prev.reason!r}")
    if new.reason not in _ABORT_REASON_ORDER:
        raise ValueError(f"unknown abort reason: {new.reason!r}")
    prev_index = _ABORT_REASON_ORDER.index(str(prev.reason))
    new_index = _ABORT_REASON_ORDER.index(str(new.reason))
    return prev if prev_index <= new_index else new


def _stops_sweep(disposition: Disposition | None) -> bool:
    return bool(disposition and _SEVERITY[disposition.kind] >= _SEVERITY["pause"])


def _pilot_run_outcome(systems: list[SystemOutcome]) -> RunOutcome:
    if all(system.run_outcome == "completed" for system in systems):
        return "completed"
    if any(system.run_outcome == "aborted" for system in systems):
        return "aborted"
    return "halted"


def _git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=BENCHMARK_ROOT.parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _zfmt(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def _advance_latest(runs_root: Path, run_dir: Path) -> None:
    latest = runs_root / "latest"
    temp = runs_root / f".latest.tmp.{os.getpid()}"
    if temp.exists() or temp.is_symlink():
        temp.unlink()
    os.symlink(run_dir.name, temp)
    os.replace(temp, latest)
    _fsync_dir(runs_root)


def _task_dir(run_dir: Path, system_id: str, mode: str, task_id: str) -> Path:
    return _mode_dir(run_dir, system_id, mode) / "tasks" / task_id


def _system_dir(run_dir: Path, system_id: str) -> Path:
    return run_dir / "conditions" / system_id


def _mode_dir(run_dir: Path, system_id: str, mode: str) -> Path:
    return _system_dir(run_dir, system_id) / f"runtime_mode_{mode}"


def _rr_task_dir(rr: RepResult) -> Path:
    task_dir = getattr(rr, "_task_dir", None)
    if not isinstance(task_dir, Path):
        raise HarnessError("rep result missing task artifact directory")
    return task_dir


def _record_outage_signal(rr: RepResult, detector: OutageDetector) -> None:
    signal = detector.pause_signal()
    rr.ledger["outage_signal"] = asdict(signal) if signal is not None else None


def _classify_stop_cause(
    stop_reason: str | None,
    rep_state: _RepState,
) -> tuple[RepStopCause, bool]:
    if stop_reason in _MODEL_EMITTED_TERMINALS:
        return stop_reason, True  # type: ignore[return-value]
    if stop_reason == STOP_REASON_MAX_TURNS:
        if rep_state.meter_halt is not None:
            raise HarnessError("max_turns cannot carry a meter_halt")
        return "max_turns", True
    if stop_reason == STOP_REASON_AFTER_TURN:
        if rep_state.partial_stop_cause not in _PARTIAL_STOP_CAUSES:
            raise HarnessError("after_turn_stop missing A2 partial stop cause")
        return rep_state.partial_stop_cause, False  # type: ignore[return-value]
    raise HarnessError(f"unsupported run_agent_loop stop_reason: {stop_reason!r}")


def _base_ledger(rep_state: _RepState, stop_cause: str) -> dict[str, Any]:
    return {
        "schema_version": "governed_agent_bench.rep_ledger.v1",
        "system_id": rep_state.system_id,
        "runtime_mode": rep_state.runtime_mode,
        "task_id": rep_state.task_id,
        "rep_index": rep_state.rep_index,
        "rep_label": rep_state.rep_label,
        "turns": list(rep_state.turns or []),
        "outage_signal": None,
        "disposition": "completed",
        "disposition_triggers": [],
        "task_success_authoritative": (
            False if stop_cause == STOP_REASON_SUBPROCESS_CRASH else None
        ),
    }


def _provider_outcome(
    record: TurnRecord,
    retry_exhausted: bool,
    adapter_error: str | None,
) -> str:
    if adapter_error is not None:
        return "adapter_error"
    if retry_exhausted:
        return "retry_exhausted"
    return record.provider_outcome


def _raw_misbehavior(record: TurnRecord) -> str:
    raw = None
    if record.invalid_output is not None:
        raw = record.invalid_output.get("raw_output")
    if not isinstance(raw, str):
        return "none"
    if _looks_like_direct_state_write(raw):
        return "direct_state"
    if scan_clinical_phrases(raw):
        return "clinical"
    return "none"


def _coerce_cost(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _coerce_wall_ms(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, float) and value >= 0:
        return int(value)
    return None


def _round_cost(value: float) -> float:
    return round(value, 12)


def _error_turn_result(
    kind: Literal["retry_exhausted", "adapter_error"],
    message: str,
    *,
    retry_count: int = 0,
    retry_exhausted: bool = False,
    adapter_error: str | None = None,
) -> ModelTurnResult:
    del retry_exhausted, adapter_error
    prefix = (
        "__GAB_RETRY_EXHAUSTED__"
        if kind == "retry_exhausted"
        else "__GAB_ADAPTER_ERROR__"
    )
    return ModelTurnResult(
        text=f"{prefix}: {message}",
        retry_count=retry_count,
    )


def _write_concat_files(rr: RepResult, task_dir: Path, prefix: Path) -> None:
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    for step in rr.trajectory.get("steps", []):
        stdout_ref = step.get("stdout_ref")
        stderr_ref = step.get("stderr_ref")
        if isinstance(stdout_ref, str):
            stdout_parts.append((task_dir / stdout_ref).read_text(encoding="utf-8"))
        if isinstance(stderr_ref, str):
            stderr_parts.append((task_dir / stderr_ref).read_text(encoding="utf-8"))
    prefix.with_suffix(".stdout.txt").write_text("".join(stdout_parts), encoding="utf-8")
    prefix.with_suffix(".stderr.txt").write_text("".join(stderr_parts), encoding="utf-8")


def _observations_payload(rr: RepResult) -> dict[str, Any]:
    steps = []
    for index, step in enumerate(rr.trajectory.get("steps", [])):
        steps.append({
            "step_index": index,
            "step_type": step.get("step_type"),
            "exit_code": step.get("exit_code"),
            "stdout_ref": step.get("stdout_ref"),
            "stderr_ref": step.get("stderr_ref"),
            "mechanism": step.get("mechanism"),
        })
    return {
        "schema_version": "governed_agent_bench.rep_observations.v1",
        "rep_label": rr.rep_label,
        "steps": steps,
    }


def _full_contract_breach(trajectory: dict[str, Any]) -> bool:
    if trajectory.get("runtime_mode") != "full_contract":
        return False
    manifest = load_manifest_snapshot(str(trajectory["manifest_snapshot_id"]))
    command_rows = _manifest_command_rows(manifest)
    steps = list(trajectory.get("steps", []))
    for index, step in enumerate(steps):
        if step.get("step_type") != "command":
            continue
        command = step.get("command")
        row = command_rows.get(str(command))
        if not row or row.get("agent_safe") is not False:
            continue
        observation = _next_observation(steps, index)
        if observation is not None and observation.get("exit_code") == "OK":
            return True
    return False


def _manifest_command_rows(manifest_snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    manifest = manifest_snapshot.get("manifest", manifest_snapshot)
    rows: dict[str, dict[str, Any]] = {}
    for row in manifest.get("commands", []):
        name = row.get("name") or row.get("command")
        if name:
            rows[str(name)] = dict(row)
    return rows


def _next_observation(steps: list[dict[str, Any]], command_index: int) -> dict[str, Any] | None:
    for step in steps[command_index + 1:]:
        if step.get("step_type") == "observation":
            return step
    return None


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


__all__ = [
    "MODE_ORDER",
    "PilotConfig",
    "RepResult",
    "Disposition",
    "SystemOutcome",
    "PilotResult",
    "FixtureBuildError",
    "CoverageMatrix",
    "SystemMeter",
    "atomic_create_empty",
    "atomic_write_json",
    "default_pilot_config",
    "default_task_ids",
    "finalize_rep_ledger_disposition",
    "modes_in_scope",
    "post_rep_dispositions",
    "resolve",
    "run_one_rep",
    "run_outcome_of",
    "run_pilot",
    "together_model_turn_factory",
    "write_condition_index",
    "write_condition_summary",
    "write_rep_artifacts",
]
