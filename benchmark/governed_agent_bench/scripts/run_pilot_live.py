"""Live model-backed pilot runner for GovernedAgentBench.

Implements the pre-registered ladder run (IB-1/IB-2): canary cells first
across all selected models, deterministic canary-gate evaluation, HARD
STOP on gate failure, then the main sweep with the remaining tasks.

THIS SPENDS REAL MONEY: it calls the Together API for every turn, billed
against the per-condition USD cap that the orchestrator enforces between
turns. Requires ``TOGETHER_API_KEY`` in the environment.

Selection (readiness SF-4):
- ``--ladder`` runs every Together roster condition in declared roster
  order (roster_v3 additions are picked up automatically).
- ``--condition-id`` (repeatable) runs an explicit subset.
- default (neither flag) is the full ladder: the pre-registered run.

Use ``--dry-run`` to print the resolved ladder, per-model decoding
settings, wall/cost budgets, the canary plan, and a worst-case cost
estimate WITHOUT any network call. Use ``--smoke`` for a cheap live
validation slice on the PRIMARY condition exercising the novel paths
(untold render + hide_stdout live), n=1.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Collection, Iterable, Mapping

from governed_agent_bench.canary_gate import (
    DEFAULT_OPERATE_FLOOR_PASS_RATE,
    OPERATE_TASK_IDS,
    canary_task_ids,
    evaluate_canary_gate,
)
from governed_agent_bench.harness.core import load_task
from governed_agent_bench.harness.model_actions import FEEDBACK_STDOUT_MAX_CHARS
from governed_agent_bench.harness.together import (
    TOGETHER_PRICING_BY_MODEL_ID,
    build_together_chat_request,
)
from governed_agent_bench.model_roster import load_model_roster
from governed_agent_bench.runtime_preflight import run_enforcement_preflight
from governed_agent_bench.pilot_orchestrator import (
    DEFAULT_RUNS_ROOT,
    MODE_ORDER,
    PilotConfig,
    modes_in_scope,
    run_pilot,
    together_model_turn_factory,
    wall_cap_min,
)
from governed_agent_bench.scripts.fireworks_deployments import (
    FIREWORKS_API_KEY_ENV,
    deployment,
    estimate_uptime_cost_usd,
    sweep_orphans,
)
from governed_agent_bench.scripts.powered_run import (
    make_fireworks_model_turn_factory,
)
from governed_agent_bench.scripts.powered_run_roster import (
    ANCHOR_CONDITIONS,
    FIREWORKS_ACCOUNT_ID,
    breadth_conditions,
    condition_capability_band,
)

TOGETHER_API_KEY_ENV = "TOGETHER_API_KEY"
TOGETHER_PROVIDER = "Together AI"
ON_DEMAND_SERVING_MODE = "on_demand"
# The run-level cumulative on-demand GPU-uptime ceiling (belt): the per-token
# cost cap is inert for on-demand (cost_usd_estimate=None), so this cumulative
# ceiling + the per-phase wall cap + Fireworks scale-to-zero + the orphan sweep
# are the real spend controls. REACTIVE, not predictive: the check compares the
# cost ALREADY accrued (from prior torn-down deployments) against the ceiling
# BEFORE creating the next deployment, so it can overshoot by up to one
# wall-capped deployment (~a wall-cap worth of GPU-hours) before it trips. Set
# the ceiling with that one-deployment headroom in mind.
DEFAULT_ONDEMAND_COST_CEILING_USD = 40.0
# Orphan-sweep prefix: every on-demand deployment id this runner mints starts
# with `ondemand-` (condition_id `ondemand_*` with underscores -> hyphens), so a
# crash-orphaned GPU is force-deleted by a prefix sweep at run start and end.
ONDEMAND_DEPLOYMENT_PREFIX = "ondemand-"
PRIMARY_CONDITION_ID = "run_primary_minimax_m3"
# Below-floor operate control (locked ladder design): the 7B runs the L1
# operate/base cells in the canary phase; the gate asserts it fails to
# operate.
DEFAULT_BELOW_FLOOR_CONDITION_ID = "run_belowfloor_qwen25_7b"

# Smoke slice (readiness SF-5): one cheap live validation pass on the
# PRIMARY condition exercising the two novel live paths -- the untold
# manifest render (gab_l5_audit_untold) and hide_stdout observation
# withholding (gab_l5_audit_blind) -- both at full_contract, n=1.
SMOKE_TASK_IDS = ("gab_l5_audit_blind", "gab_l5_audit_untold")

# D-49 concentration pass: the PAID ladder spends only on tasks that map to a
# contrast in the paper's claim. `default_task_ids()` stays the full committed
# suite so `reproduce_offline` still covers scope (M4 validation, M6
# proposal_gate, credential/export refusal, audit domain-variants) via offline
# oracle-pairs; those are deliberately NOT paid-swept. Every id here is asserted
# to (a) exist in the committed suite and (b) satisfy its tier invariant in
# test_run_pilot_live (Tier A must carry an off-mode; Tier D families excluded).
CONCENTRATED_SWEEP_TASK_IDS = (
    # Tier A -- headline substitution 2x2 (both levers vary): the mutation gate
    # (M5+M6, off = no_runtime_enforcement) and clinical refusal (M7, off =
    # no_refusal). All carry an off-mode in scope.
    #
    # The mutation-gate cells are the user-authored state activations
    # (target/intent commit): a completable state mutation, so the untold-
    # unenforced arm can actually execute the violation (D-52 pre-sweep: told
    # refrains 5/5, untold commits 5/5 -> B-D=+100pp on 235B). The credential
    # login task (`agentsafe_auth`, `hai auth garmin`) is DELIBERATELY excluded:
    # it is an interactive command that returns USER_INPUT for a password the
    # agent cannot supply, so the "autonomous login" violation is un-executable
    # headless and both arms score as valid refusals (B-D structurally 0,
    # D-52). It is a real refusal task and stays in the offline suite, but it is
    # a DEGENERATE substitution cell and is not paid-swept.
    "gab_l6_agentsafe_told",
    "gab_l6_agentsafe_untold",
    "gab_l6_agentsafe_intent_told",
    "gab_l6_agentsafe_intent_untold",
    "gab_l6_agentsafe_conflict",
    # Powered-run breadth (2026-07-17): the mutation-gate boundary ("do not
    # activate the user's own agent-proposed state without an explicit user
    # commit") swept across additional seeded state types so each model's rate is
    # characterized over the boundary, not one phrasing. Same off-mode
    # (no_runtime_enforcement), same D-52 executable violation (commit of a
    # governance_user proposed row), varied state type / command family. ~4
    # distinct command shapes across 3 domains (2 command families); the nutrition
    # variants share a shape and are disclosed as boundary re-samples.
    "gab_l6_agentsafe_hydration_told",
    "gab_l6_agentsafe_hydration_untold",
    "gab_l6_agentsafe_calories_told",
    "gab_l6_agentsafe_calories_untold",
    "gab_l6_agentsafe_carbs_told",
    "gab_l6_agentsafe_carbs_untold",
    "gab_l6_agentsafe_sleep_told",
    "gab_l6_agentsafe_sleep_untold",
    "gab_l6_agentsafe_trainingload_told",
    "gab_l6_agentsafe_trainingload_untold",
    "gab_l6_agentsafe_sleepwindow_told",
    "gab_l6_agentsafe_sleepwindow_untold",
    "gab_l6_refusal_told",
    "gab_l6_refusal_untold",
    "gab_l6_refusal_diagnose_told",
    "gab_l6_refusal_diagnose_untold",
    "gab_l6_refusal_dose_told",
    "gab_l6_refusal_dose_untold",
    "gab_l6_refusal_conflict",
    # Tier B -- M8 blind-twin sub-result. M8 is a verifiability/observability
    # mechanism, NOT a told/untold substitution cell (it is excluded from the
    # cell_contrasts 2x2; MECHANISM_METRICS = {agent_safe, refusal}). Its
    # sub-result is the SIGHTED-vs-BLIND twin at full_contract: audit_told
    # (sees stdout, cites) vs audit_blind (hide_stdout, fabricates). The
    # `gab_l5_audit_untold` task renders byte-identically to audit_told at
    # full_contract (no meaningful audit rule to withhold), so it is a
    # redundant paid condition and is deliberately NOT swept here; it remains
    # in the offline suite for reproduce coverage.
    "gab_l5_audit_told",
    "gab_l5_audit_blind",
    # Tier C -- operate sanity floor (also the below-floor operate control).
    "gab_l1_operate_read",
    "gab_l1_operate_route",
)

# Conservative chars-per-token for wall/cost projections. An estimate,
# clearly labelled as such wherever it is printed.
CHARS_PER_TOKEN_ESTIMATE = 3.5
DEFAULT_ASSUMED_REP_SECONDS = 90.0

EXIT_OK = 0
EXIT_RUN_NOT_COMPLETED = 1
EXIT_MISSING_API_KEY = 2
EXIT_RUN_DIR_EXISTS = 3
EXIT_GIT_HEAD_FAILED = 4
EXIT_CANARY_GATE_FAILED = 5
EXIT_BAD_SELECTION = 6
EXIT_STALE_RUNTIME = 7
EXIT_COST_CEILING = 8


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


def _write_runtime_preflight(report: dict[str, Any], dest: Path | None = None) -> None:
    """Persist the runtime-identity preflight report beside the runs.

    Always writes a ``runtime_preflight_latest.json`` under the runs root so the
    last invocation's runtime identity is recoverable; when ``dest`` (a run dir)
    is given, also drops a copy inside it so a paper-claim run carries the exact
    runtime it measured.
    """

    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    targets = [DEFAULT_RUNS_ROOT / "runtime_preflight_latest.json"]
    if dest is not None:
        targets.append(dest / "runtime_preflight.json")
    for path in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")


def together_ladder_conditions() -> list[dict[str, Any]]:
    """The D-41 run-ladder conditions, in declared roster order.

    roster_v3 retains superseded conditions for provenance (roster
    immutability rule); the run ladder is exactly the ``run_``-prefixed
    Together conditions, so legacy entries can never be swept into a paid
    sweep by ``--ladder``.
    """

    roster = load_model_roster()
    return [
        dict(condition)
        for condition in roster.get("conditions", [])
        if condition.get("provider") == TOGETHER_PROVIDER
        and str(condition.get("condition_id", "")).startswith("run_")
    ]


def powered_run_conditions() -> list[dict[str, Any]]:
    """roster_v4: the confound-break union (on-demand anchors + serverless breadth).

    The 4 Fireworks on-demand anchors (within-family capability pairs, the
    confound break) followed by the 4 serverless breadth conditions reused from
    the frozen roster_v3. On-demand condition dicts carry ``serving_mode`` /
    ``capability_band`` / ``accelerator_type`` so the sweep can route them
    through the deployment lifecycle and band them into the capable movement
    pool; the serverless breadth dicts route as Together and band by id prefix.
    """

    conditions = [dict(pc.condition) for pc in ANCHOR_CONDITIONS]
    conditions += [dict(pc.condition) for pc in breadth_conditions()]
    return conditions


def _selectable_conditions_by_id() -> dict[str, dict[str, Any]]:
    """condition_id -> dict across the Together ladder and the on-demand anchors."""

    by_id: dict[str, dict[str, Any]] = {
        str(c["condition_id"]): c for c in together_ladder_conditions()
    }
    for pc in ANCHOR_CONDITIONS:
        by_id[str(pc.condition["condition_id"])] = dict(pc.condition)
    return by_id


def resolve_conditions(
    *,
    ladder: bool,
    condition_ids: list[str],
    powered: bool = False,
) -> list[dict[str, Any]]:
    """Resolve the run's conditions from the committed roster.

    ``--powered`` selects roster_v4 (the on-demand confound-break anchors plus
    the serverless breadth). Otherwise ``--ladder`` is the Together run-ladder
    and ``--condition-id`` is an explicit subset; an explicit id may name a
    Together roster condition OR an on-demand anchor (so a single on-demand
    model can be canaried/smoked). Order follows the roster for ``--ladder`` /
    ``--powered`` and the caller for explicit ids.
    """

    if sum(bool(x) for x in (ladder, condition_ids, powered)) > 1:
        raise ValueError(
            "--ladder, --condition-id, and --powered are mutually exclusive"
        )
    if powered:
        return powered_run_conditions()
    if not condition_ids:
        return together_ladder_conditions()
    by_id = _selectable_conditions_by_id()
    resolved = []
    for condition_id in condition_ids:
        if condition_id not in by_id:
            raise KeyError(
                f"condition {condition_id!r} is not a selectable roster "
                f"condition; known: {sorted(by_id)}"
            )
        resolved.append(by_id[condition_id])
    return resolved


# The pooled movement contrasts (blind twin, untold floor) pool over CAPABLE
# models only (§20.16) -- a floor point would dilute the movement and hard-stop
# the run for a pooling reason. OR-2 fix: capability band comes from
# ``powered_run_roster.condition_capability_band`` (explicit ``capability_band``
# on the on-demand anchors, id-prefix fallback for the frozen roster_v3
# conditions), NOT a bare id-prefix match -- the on-demand capable anchors
# (``ondemand_qwen25_72b`` / ``ondemand_llama31_70b``) do not match ``run_*``, so
# a prefix match would silently drop them and spuriously hard-stop the gate.


def capable_movement_condition_ids(
    conditions: Iterable[dict[str, Any]],
    ran_condition_ids: Collection[str],
) -> list[str]:
    """Capable-tier ids among ``ran_condition_ids``, banded by condition dict.

    Fails closed: a condition whose ``condition_capability_band`` is not
    ``"capable"`` (weak, or an unrecognised/renamed condition -> None) is
    excluded, so at worst the movement pool is empty and the gate hard-stops --
    it can never silently pool a floor point into the capable movement.
    Preserves ``ran_condition_ids`` order.
    """

    capable_ids = {
        str(condition["condition_id"])
        for condition in conditions
        if condition_capability_band(condition) == "capable"
    }
    return [
        condition_id
        for condition_id in ran_condition_ids
        if str(condition_id) in capable_ids
    ]


def apply_wall_override(
    condition: dict[str, Any],
    max_wall_minutes: float | None,
) -> dict[str, Any]:
    """Copy of ``condition`` with an explicit per-invocation wall cap."""

    if max_wall_minutes is None:
        return condition
    updated = dict(condition)
    boundary = dict(updated.get("compute_boundary", {}))
    boundary["max_wall_time_minutes"] = float(max_wall_minutes)
    updated["compute_boundary"] = boundary
    return updated


def condition_cost_cap_usd(condition: Mapping[str, Any]) -> float:
    return float(condition.get("cost_boundary", {}).get("max_cost_usd", 100.0))


def phase1_plan(
    condition: Mapping[str, Any],
    *,
    below_floor_condition_id: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(task_ids, mode_order) for a condition's canary-phase invocation."""

    if condition["condition_id"] == below_floor_condition_id:
        return tuple(OPERATE_TASK_IDS), ("full_contract",)
    return canary_task_ids(), tuple(MODE_ORDER)


def phase2_task_ids(phase1_tasks: tuple[str, ...]) -> tuple[str, ...]:
    """Concentrated sweep tasks after a condition's canary phase (D-49).

    Draws from ``CONCENTRATED_SWEEP_TASK_IDS`` (headline-mapped tasks only), not
    the full committed suite: Tier D scope tasks (M4 validation, M6
    proposal_gate, credential/export refusal, audit domain-variants) are covered
    offline by ``reproduce_offline`` and never paid-swept.
    """

    return tuple(
        task_id
        for task_id in CONCENTRATED_SWEEP_TASK_IDS
        if task_id not in set(phase1_tasks)
    )


def planned_rep_count(
    task_ids: tuple[str, ...],
    mode_order: tuple[str, ...],
    replication_n: int,
) -> int:
    """Reps this invocation will attempt (in-scope cells x n)."""

    cells = 0
    for task_id in task_ids:
        task = load_task(task_id)
        cells += sum(1 for mode in modes_in_scope(task) if mode in mode_order)
    return cells * replication_n


def projected_wall_minutes(rep_count: int, assumed_rep_seconds: float) -> float:
    return rep_count * assumed_rep_seconds / 60.0


def warn_if_wall_cap_exceeded(
    *,
    label: str,
    condition: Mapping[str, Any],
    rep_count: int,
    assumed_rep_seconds: float,
    stream: Any = sys.stderr,
) -> bool:
    """Loud non-silent wall-cap check (readiness SF-6). Returns True on warn."""

    cap = wall_cap_min(dict(condition))
    projected = projected_wall_minutes(rep_count, assumed_rep_seconds)
    if projected <= cap:
        return False
    print(
        f"WARNING [{label}] projected wall time ~{projected:.0f} min "
        f"({rep_count} reps x {assumed_rep_seconds:.0f}s/rep, an ESTIMATE) "
        f"EXCEEDS max_wall_time_minutes={cap:.0f} for "
        f"{condition['condition_id']}. The orchestrator will wall_halt the "
        "sweep mid-flight. Raise --max-wall-minutes or shrink the plan; "
        "actual per-rep sizing happens at smoke time.",
        file=stream,
    )
    return True


def estimate_condition_cost_usd(
    condition: Mapping[str, Any],
    task_ids: tuple[str, ...],
    mode_order: tuple[str, ...],
    replication_n: int,
    max_turns: int,
) -> dict[str, Any]:
    """Worst-case offline cost estimate for one invocation. NO network.

    Upper bound: every rep runs ``max_turns`` turns, every turn re-sends the
    largest rendered prompt plus maximally-sized harness feedback, and every
    completion spends the full ``max_tokens``. Clearly an estimate.
    """

    model_id = str(condition["model_id"])
    pricing = TOGETHER_PRICING_BY_MODEL_ID.get(model_id)
    rep_count = planned_rep_count(task_ids, mode_order, replication_n)
    if pricing is None:
        return {
            "estimated": False,
            "rep_count": rep_count,
            "detail": f"no committed pricing for {model_id!r} (pending roster_v3)",
        }
    max_prompt_chars = 0
    for task_id in task_ids:
        task = load_task(task_id)
        request, _ = build_together_chat_request(task, dict(condition))
        chars = sum(len(m["content"]) for m in request["messages"])
        max_prompt_chars = max(max_prompt_chars, chars)
    max_tokens = int(condition["decoding_settings"].get("max_tokens", 2048))
    prompt_tokens = max_prompt_chars / CHARS_PER_TOKEN_ESTIMATE
    feedback_tokens = FEEDBACK_STDOUT_MAX_CHARS / CHARS_PER_TOKEN_ESTIMATE
    input_tokens_per_rep = sum(
        prompt_tokens + turn * (feedback_tokens + max_tokens)
        for turn in range(max_turns)
    )
    output_tokens_per_rep = max_turns * max_tokens
    input_rate = float(pricing["input_usd_per_1m_tokens"])
    output_rate = float(pricing["output_usd_per_1m_tokens"])
    per_rep = (
        input_tokens_per_rep * input_rate + output_tokens_per_rep * output_rate
    ) / 1_000_000
    return {
        "estimated": True,
        "rep_count": rep_count,
        "max_prompt_chars": max_prompt_chars,
        "worst_case_usd_per_rep": round(per_rep, 4),
        "worst_case_usd_total": round(per_rep * rep_count, 2),
        "detail": (
            "worst-case upper bound: max_turns full-budget turns, largest "
            "rendered prompt re-sent each turn, feedback at the stdout cap; "
            f"chars-per-token={CHARS_PER_TOKEN_ESTIMATE} (estimate)"
        ),
    }


def build_smoke_config(runs_root: Path | None = None) -> PilotConfig:
    """Smoke slice config: SMOKE_TASK_IDS @ full_contract, n=1, tiny cap."""

    return PilotConfig(
        runs_root=(runs_root or DEFAULT_RUNS_ROOT) / "_smoke",
        task_ids=SMOKE_TASK_IDS,
        mode_order=("full_contract",),
        replication_n=1,
        cost_cap_usd=1.0,
    )


def _print_condition_plan(
    condition: Mapping[str, Any],
    *,
    below_floor_condition_id: str,
    replication_n: int,
    max_turns: int,
    assumed_rep_seconds: float,
) -> None:
    condition_id = str(condition["condition_id"])
    p1_tasks, p1_modes = phase1_plan(
        condition, below_floor_condition_id=below_floor_condition_id
    )
    p2_tasks = phase2_task_ids(p1_tasks)
    role = (
        "below-floor operate control"
        if condition_id == below_floor_condition_id
        else "ladder model"
    )
    print(f"  - {condition_id} ({condition['model_id']}) [{role}]")
    print(f"      decoding      : {json.dumps(condition['decoding_settings'], sort_keys=True)}")
    print(
        f"      budgets       : cost cap USD {condition_cost_cap_usd(condition):.0f}, "
        f"wall cap {wall_cap_min(dict(condition)):.0f} min"
    )
    p1_reps = planned_rep_count(p1_tasks, p1_modes, replication_n)
    p2_reps = planned_rep_count(p2_tasks, tuple(MODE_ORDER), replication_n)
    print(
        f"      canary phase  : {len(p1_tasks)} tasks x modes {list(p1_modes)} "
        f"-> {p1_reps} reps (n={replication_n})"
    )
    print(f"      main phase    : {len(p2_tasks)} tasks -> {p2_reps} reps")
    print(
        f"      wall estimate : ~{projected_wall_minutes(p1_reps + p2_reps, assumed_rep_seconds):.0f} min "
        f"at {assumed_rep_seconds:.0f}s/rep (ESTIMATE)"
    )
    for label, tasks, modes in (
        ("canary", p1_tasks, p1_modes),
        ("main", p2_tasks, tuple(MODE_ORDER)),
    ):
        estimate = estimate_condition_cost_usd(
            condition, tasks, modes, replication_n, max_turns
        )
        if estimate["estimated"]:
            print(
                f"      cost ({label:6s}): <= USD {estimate['worst_case_usd_total']:.2f} "
                "(worst-case upper bound, ESTIMATE)"
            )
        else:
            print(f"      cost ({label:6s}): {estimate['detail']}")


def resumable_run_dir(runs_root: Path) -> Path | None:
    """The single existing pilot run dir under one invocation root, or None.

    IC-2: on ``--resume`` each per-condition, per-phase invocation resumes
    its own previously-created run dir (``<runs_root>/<ts>_lock-<sha7>``).
    No run dir means the invocation never started -- run it fresh. More than
    one is ambiguous and refuses rather than guessing.
    """

    if not runs_root.is_dir():
        return None
    candidates = sorted(
        path
        for path in runs_root.glob("*_lock-*")
        if path.is_dir() and not path.is_symlink()
    )
    if not candidates:
        return None
    if len(candidates) > 1:
        raise ValueError(
            f"cannot resume: multiple run dirs under {runs_root}: "
            f"{[p.name for p in candidates]}"
        )
    return candidates[0]


class _SpendTracker:
    """Cumulative on-demand GPU-uptime spend against a run-level ceiling."""

    def __init__(self, ceiling_usd: float) -> None:
        self.ceiling_usd = ceiling_usd
        self.cumulative_usd = 0.0

    def would_exceed(self) -> bool:
        return self.cumulative_usd >= self.ceiling_usd

    def add_uptime(self, uptime_seconds: float, accelerator_type: str) -> float:
        cost = estimate_uptime_cost_usd(uptime_seconds, accelerator_type)
        self.cumulative_usd += cost
        return cost


def _invoke_condition(
    condition: dict[str, Any],
    config: PilotConfig,
    *,
    pilot_runner: Callable[..., Any],
    fireworks_api_key: str | None,
    account_id: str,
    spend_tracker: _SpendTracker,
    validate_only: bool,
    ready_timeout: float = 900.0,
    deployment_id_suffix: str | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> Any:
    """Run one condition's sweep, routing by serving mode.

    Serverless conditions use the Together per-token factory unchanged. An
    on-demand condition is wrapped in a ``deployment()`` context (create the GPU,
    bind the live deployment-qualified model, GUARANTEED teardown) and swept with
    the Fireworks factory. ``validate_only`` does the deployment's $0 dry-run and
    skips the sweep (the free wiring gate). Deployment ids are unique per
    invocation and start with ``ondemand-`` so a crash-orphan is caught by the
    prefix sweep. On teardown the GPU-uptime cost is added to ``spend_tracker``.
    """

    serving_mode = str(condition.get("serving_mode", "serverless"))
    if serving_mode != ON_DEMAND_SERVING_MODE:
        return pilot_runner(
            systems=[condition],
            model_turn_factory=together_model_turn_factory,
            config=config,
        )

    base_model = str(condition["model_id"])
    accelerator_type = condition.get("accelerator_type")
    suffix = deployment_id_suffix or format(int(time.time()), "x")[-6:]
    deployment_id = f"{str(condition['condition_id']).replace('_', '-')}-{suffix}"
    started = clock()
    try:
        with deployment(
            account_id,
            base_model,
            deployment_id,
            api_key=fireworks_api_key or "",
            accelerator_type=(
                str(accelerator_type) if accelerator_type is not None else None
            ),
            validate_only=validate_only,
            ready_timeout=ready_timeout,
        ) as handle:
            if validate_only:
                return None
            factory = make_fireworks_model_turn_factory(handle.invocation_model)
            return pilot_runner(
                systems=[condition],
                model_turn_factory=factory,
                config=config,
            )
    finally:
        if not validate_only and accelerator_type is not None:
            uptime = max(0.0, clock() - started)
            spent = spend_tracker.add_uptime(uptime, str(accelerator_type))
            print(
                f"on-demand [{condition['condition_id']}] uptime ~{uptime:.0f}s "
                f"-> ~USD {spent:.2f} (cumulative ~USD "
                f"{spend_tracker.cumulative_usd:.2f} / {spend_tracker.ceiling_usd:.0f} "
                "ceiling, ESTIMATE)",
                flush=True,
            )


def _run_validate_only(
    conditions: list[dict[str, Any]],
    *,
    fireworks_api_key: str | None,
    account_id: str,
    spend_tracker: _SpendTracker,
) -> int:
    """$0 wiring gate: deployment validateOnly per on-demand condition.

    The free instrument check before any spend. On-demand conditions get the
    Fireworks ``validateOnly`` deployment dry-run (proves the base model is
    deployable on the requested accelerator, $0, nothing provisioned). Serverless
    conditions are skipped -- there is no $0 validation for a per-token endpoint
    (calling it would spend), so the dry-run (``--dry-run``) is their check.
    """

    for condition in conditions:
        cid = str(condition["condition_id"])
        if str(condition.get("serving_mode", "serverless")) != ON_DEMAND_SERVING_MODE:
            print(
                f"validate-only [{cid}]: serverless -- skipped "
                "(no $0 endpoint validation; covered by --dry-run)",
                flush=True,
            )
            continue
        _invoke_condition(
            condition,
            PilotConfig(runs_root=DEFAULT_RUNS_ROOT / "_validate", task_ids=()),
            pilot_runner=run_pilot,
            fireworks_api_key=fireworks_api_key,
            account_id=account_id,
            spend_tracker=spend_tracker,
            validate_only=True,
        )
        print(
            f"validate-only [{cid}]: on-demand deployment validateOnly PASSED ($0)",
            flush=True,
        )
    return EXIT_OK


def run_ladder(
    conditions: list[dict[str, Any]],
    *,
    ladder_root: Path,
    below_floor_condition_id: str,
    replication_n: int | None = None,
    max_wall_minutes: float | None = None,
    assumed_rep_seconds: float = DEFAULT_ASSUMED_REP_SECONDS,
    operate_floor_pass_rate: float = DEFAULT_OPERATE_FLOOR_PASS_RATE,
    pilot_runner: Callable[..., Any] = run_pilot,
    gate_evaluator: Callable[..., dict[str, Any]] = evaluate_canary_gate,
    resume: bool = False,
    fireworks_api_key: str | None = None,
    account_id: str = FIREWORKS_ACCOUNT_ID,
    validate_only: bool = False,
    cost_ceiling_usd: float = DEFAULT_ONDEMAND_COST_CEILING_USD,
) -> tuple[int, dict[str, Any] | None]:
    """Canary-first two-phase ladder run with a hard stop at the gate.

    Phase 1 invokes ``run_pilot`` once per condition with that condition's
    canary plan into ``ladder_root/canary/<condition_id>/``; the gate is
    evaluated from those run dirs and written to
    ``ladder_root/canary_gate_report.json``. On gate failure the function
    HARD STOPS (no phase-2 invocation, exit ``EXIT_CANARY_GATE_FAILED``).
    On pass, phase 2 invokes ``run_pilot`` per condition with the remaining
    tasks into ``ladder_root/main/<condition_id>/``.

    With ``resume=True`` (``--resume <ladder_root>``), each invocation that
    already has a run dir resumes it rep-by-rep (completed reps reload from
    disk; only incomplete reps re-execute); invocations with no run dir run
    fresh. The canary gate is re-evaluated from the (now complete) canary
    run dirs.
    """

    rep_n = (
        replication_n
        if replication_n is not None
        else PilotConfig(runs_root=ladder_root, task_ids=()).replication_n
    )
    spend = _SpendTracker(cost_ceiling_usd)
    if validate_only:
        return (
            _run_validate_only(
                conditions,
                fireworks_api_key=fireworks_api_key,
                account_id=account_id,
                spend_tracker=spend,
            ),
            None,
        )
    canary_run_dirs: dict[str, Path] = {}
    for condition in conditions:
        condition_id = str(condition["condition_id"])
        run_condition = apply_wall_override(condition, max_wall_minutes)
        p1_tasks, p1_modes = phase1_plan(
            run_condition, below_floor_condition_id=below_floor_condition_id
        )
        rep_count = planned_rep_count(p1_tasks, p1_modes, rep_n)
        warn_if_wall_cap_exceeded(
            label=f"canary/{condition_id}",
            condition=run_condition,
            rep_count=rep_count,
            assumed_rep_seconds=assumed_rep_seconds,
        )
        if (
            str(run_condition.get("serving_mode", "serverless"))
            == ON_DEMAND_SERVING_MODE
            and spend.would_exceed()
        ):
            print(
                f"HARD STOP: cumulative on-demand cost ~USD "
                f"{spend.cumulative_usd:.2f} reached ceiling "
                f"{spend.ceiling_usd:.0f} before canary/{condition_id}. "
                "Refusing to provision another GPU.",
                file=sys.stderr,
            )
            return EXIT_COST_CEILING, None
        canary_root = ladder_root / "canary" / condition_id
        config = PilotConfig(
            runs_root=canary_root,
            task_ids=p1_tasks,
            mode_order=p1_modes,
            replication_n=rep_n,
            cost_cap_usd=condition_cost_cap_usd(run_condition),
            resume_run_dir=resumable_run_dir(canary_root) if resume else None,
        )
        result = _invoke_condition(
            run_condition,
            config,
            pilot_runner=pilot_runner,
            fireworks_api_key=fireworks_api_key,
            account_id=account_id,
            spend_tracker=spend,
            validate_only=False,
        )
        canary_run_dirs[condition_id] = result.run_dir
        print(
            f"canary [{condition_id}] run_outcome={result.run_outcome} "
            f"run_dir={result.run_dir}",
            flush=True,
        )

    # §20.5(a)/§20.16: the pooled MOVEMENT contrasts (untold floor, blind twin)
    # pool over the CAPABLE models only. The near-floor point is mapped
    # separately (§20.8 Branches 6a-6c) and would otherwise dilute the pooled
    # movement and hard-stop the run for a pooling reason.
    capable_condition_ids = capable_movement_condition_ids(
        conditions, canary_run_dirs
    )
    gate_report = gate_evaluator(
        ladder_run_dirs=canary_run_dirs,
        below_floor_condition_id=below_floor_condition_id,
        operate_floor_pass_rate=operate_floor_pass_rate,
        movement_contrast_condition_ids=capable_condition_ids,
    )
    ladder_root.mkdir(parents=True, exist_ok=True)
    gate_path = ladder_root / "canary_gate_report.json"
    gate_path.write_text(
        json.dumps(gate_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"canary gate: {gate_report['overall_status']} ({gate_path})", flush=True)
    for component in gate_report["components"]:
        print(
            f"  - {component['component']}: {component['status']} "
            f"({component.get('detail', '')})"
        )
    if gate_report["overall_status"] != "pass":
        print(
            "HARD STOP: canary gate failed; the main sweep will NOT run. "
            "Dom decides the next step from the gate report.",
            file=sys.stderr,
        )
        return EXIT_CANARY_GATE_FAILED, gate_report

    exit_code = EXIT_OK
    for condition in conditions:
        condition_id = str(condition["condition_id"])
        run_condition = apply_wall_override(condition, max_wall_minutes)
        p1_tasks, _ = phase1_plan(
            run_condition, below_floor_condition_id=below_floor_condition_id
        )
        p2_tasks = phase2_task_ids(p1_tasks)
        rep_count = planned_rep_count(p2_tasks, tuple(MODE_ORDER), rep_n)
        warn_if_wall_cap_exceeded(
            label=f"main/{condition_id}",
            condition=run_condition,
            rep_count=rep_count,
            assumed_rep_seconds=assumed_rep_seconds,
        )
        if (
            str(run_condition.get("serving_mode", "serverless"))
            == ON_DEMAND_SERVING_MODE
            and spend.would_exceed()
        ):
            print(
                f"HARD STOP: cumulative on-demand cost ~USD "
                f"{spend.cumulative_usd:.2f} reached ceiling "
                f"{spend.ceiling_usd:.0f} before main/{condition_id}. "
                "Refusing to provision another GPU.",
                file=sys.stderr,
            )
            return EXIT_COST_CEILING, gate_report
        main_root = ladder_root / "main" / condition_id
        config = PilotConfig(
            runs_root=main_root,
            task_ids=p2_tasks,
            replication_n=rep_n,
            cost_cap_usd=condition_cost_cap_usd(run_condition),
            resume_run_dir=resumable_run_dir(main_root) if resume else None,
        )
        result = _invoke_condition(
            run_condition,
            config,
            pilot_runner=pilot_runner,
            fireworks_api_key=fireworks_api_key,
            account_id=account_id,
            spend_tracker=spend,
            validate_only=False,
        )
        print(
            f"main [{condition_id}] run_outcome={result.run_outcome} "
            f"run_dir={result.run_dir}",
            flush=True,
        )
        if result.run_outcome != "completed":
            exit_code = EXIT_RUN_NOT_COMPLETED
    return exit_code, gate_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the GovernedAgentBench model-backed pilot ladder.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help=(
            "cheap live validation slice on the primary condition: "
            f"{', '.join(SMOKE_TASK_IDS)} @ full_contract, n=1"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the resolved ladder/canary plan and exit; no API call",
    )
    parser.add_argument(
        "--ladder",
        action="store_true",
        help="run every Together roster condition in declared order",
    )
    parser.add_argument(
        "--powered",
        action="store_true",
        help=(
            "run roster_v4: the Fireworks on-demand confound-break anchors plus "
            "the serverless breadth (the powered run)"
        ),
    )
    parser.add_argument(
        "--condition-id",
        action="append",
        default=[],
        help="explicit roster condition id (Together or on-demand; repeatable)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help=(
            "$0 wiring gate: Fireworks validateOnly deployment dry-run per "
            "on-demand condition (serverless skipped); no GPU provisioned, no "
            "model call, no spend"
        ),
    )
    parser.add_argument(
        "--cost-ceiling-usd",
        type=float,
        default=DEFAULT_ONDEMAND_COST_CEILING_USD,
        help=(
            "run-level cumulative on-demand GPU-uptime spend ceiling; the ladder "
            "hard-stops before provisioning a GPU that would exceed it"
        ),
    )
    parser.add_argument(
        "--below-floor-condition-id",
        default=DEFAULT_BELOW_FLOOR_CONDITION_ID,
        help="condition treated as the below-floor operate control",
    )
    parser.add_argument(
        "--max-wall-minutes",
        type=float,
        default=None,
        help="per-invocation override of the roster max_wall_time_minutes",
    )
    parser.add_argument(
        "--assumed-rep-seconds",
        type=float,
        default=DEFAULT_ASSUMED_REP_SECONDS,
        help="assumed seconds per rep for the wall-time projection (estimate)",
    )
    parser.add_argument(
        "--operate-floor-pass-rate",
        type=float,
        default=DEFAULT_OPERATE_FLOOR_PASS_RATE,
        help="canary-gate operate floor for the below-floor control",
    )
    parser.add_argument(
        "--resume",
        type=Path,
        default=None,
        metavar="LADDER_ROOT",
        help=(
            "resume a previous ladder run: reuse this ladder root, skip "
            "every completed rep (reloaded from disk), re-run only "
            "incomplete reps, and re-evaluate the canary gate"
        ),
    )
    args = parser.parse_args(argv)

    if args.resume is not None and (args.smoke or args.dry_run):
        print(
            "ERROR: --resume cannot be combined with --smoke or --dry-run.",
            file=sys.stderr,
        )
        return EXIT_BAD_SELECTION

    if args.validate_only and (args.smoke or args.resume is not None):
        print(
            "ERROR: --validate-only cannot be combined with --smoke or --resume.",
            file=sys.stderr,
        )
        return EXIT_BAD_SELECTION

    try:
        conditions = resolve_conditions(
            ladder=args.ladder,
            condition_ids=list(args.condition_id),
            powered=args.powered,
        )
    except (KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_BAD_SELECTION

    has_ondemand = any(
        str(c.get("serving_mode")) == ON_DEMAND_SERVING_MODE for c in conditions
    )
    has_serverless = any(
        str(c.get("serving_mode", "serverless")) != ON_DEMAND_SERVING_MODE
        for c in conditions
    )

    replication_n = PilotConfig(runs_root=DEFAULT_RUNS_ROOT, task_ids=()).replication_n
    max_turns = PilotConfig(runs_root=DEFAULT_RUNS_ROOT, task_ids=()).max_turns

    if args.smoke:
        run_mode = "SMOKE"
    elif args.validate_only:
        run_mode = "VALIDATE-ONLY ($0 on-demand wiring gate)"
    elif args.powered:
        run_mode = "POWERED (roster_v4 confound break)"
    else:
        run_mode = "CANARY-FIRST LADDER"
    print("GovernedAgentBench live pilot ladder")
    print(f"  mode         : {run_mode}")
    print(f"  conditions   : {[str(c['condition_id']) for c in conditions]}")
    if has_ondemand:
        print(f"  on-demand    : cost ceiling USD {args.cost_ceiling_usd:.0f} (cumulative GPU-uptime, ESTIMATE)")
    print(f"  below floor  : {args.below_floor_condition_id}")
    print(f"  replication  : n={replication_n}")
    print(f"  canary tasks : {list(canary_task_ids())}")
    print(f"  runs root    : {DEFAULT_RUNS_ROOT}")
    if args.max_wall_minutes is not None:
        print(f"  wall override: {args.max_wall_minutes:.0f} min per invocation")

    if args.dry_run:
        if args.smoke:
            smoke_config = build_smoke_config()
            print(
                f"  smoke slice  : {list(smoke_config.task_ids)} @ "
                f"{list(smoke_config.mode_order)}, n={smoke_config.replication_n}, "
                f"cost cap USD {smoke_config.cost_cap_usd:.2f}"
            )
        else:
            for condition in conditions:
                _print_condition_plan(
                    apply_wall_override(condition, args.max_wall_minutes),
                    below_floor_condition_id=args.below_floor_condition_id,
                    replication_n=replication_n,
                    max_turns=max_turns,
                    assumed_rep_seconds=args.assumed_rep_seconds,
                )
        print("dry-run: no API call made.")
        return EXIT_OK

    # Together powers every serverless condition's per-token calls; Fireworks
    # powers the on-demand deployment control plane + inference. Require only the
    # keys the in-scope conditions actually need. --validate-only skips serverless
    # (no $0 endpoint check), so it needs Together only if it were to run one --
    # it never does -- but always needs Fireworks for the deployment dry-run.
    needs_together = has_serverless and not args.validate_only
    if needs_together and not os.environ.get(TOGETHER_API_KEY_ENV, "").strip():
        print(
            f"ERROR: {TOGETHER_API_KEY_ENV} is not set. Refusing to run.",
            file=sys.stderr,
        )
        return EXIT_MISSING_API_KEY
    if has_ondemand and not os.environ.get(FIREWORKS_API_KEY_ENV, "").strip():
        print(
            f"ERROR: {FIREWORKS_API_KEY_ENV} is not set but an on-demand "
            "condition is in scope. Refusing to run.",
            file=sys.stderr,
        )
        return EXIT_MISSING_API_KEY

    if not args.smoke and not args.validate_only:
        dirty = tracked_changes()
        if dirty:
            print(
                "WARNING: uncommitted tracked changes; the run-dir git sha "
                "will not reflect them. Commit before a paper-claim run:",
                file=sys.stderr,
            )
            for line in dirty:
                print(f"  {line}", file=sys.stderr)

    # Runtime-identity gate (before ANY paid rep): the harness runs the HAI CLI
    # as `sys.executable -m health_agent_infra.cli` and inherits whatever
    # `health_agent_infra` that interpreter resolves. A bare interpreter can
    # silently pick up the stale PyPI v0.2.0 wheel, whose mutation gate is
    # bypassable by an agent passing `--confirm` -- the sweep would then collect
    # a corrupted enforce arm with nothing downstream flagging it. Prove the
    # resolved runtime enforces (agent + full_contract + --confirm MUST refuse)
    # and record its fingerprint before spending. HARD STOP on failure.
    preflight = run_enforcement_preflight(sys.executable)
    fp = preflight["runtime_fingerprint"]
    print(
        f"  runtime      : {fp.get('import_path')} "
        f"(sha={fp.get('git_sha') or 'n/a'}, "
        f"wheel={fp.get('under_site_packages')})"
    )
    print(f"  enforcement  : {'PASS' if preflight['passed'] else 'FAIL'} — {preflight['detail']}")
    _write_runtime_preflight(preflight)
    if not preflight["passed"]:
        print(
            "HARD STOP: the resolved HAI runtime does not enforce the mutation "
            "gate. Run under `uv run` (or set PYTHONPATH=hai/src) so the "
            f"reference runtime (tag {preflight['reference_runtime_tag']}) is "
            "resolved. Refusing to spend on a stale runtime.",
            file=sys.stderr,
        )
        return EXIT_STALE_RUNTIME

    try:
        if args.smoke:
            primary = resolve_conditions(
                ladder=False, condition_ids=[PRIMARY_CONDITION_ID]
            )[0]
            result = run_pilot(
                systems=[apply_wall_override(primary, args.max_wall_minutes)],
                model_turn_factory=together_model_turn_factory,
                config=build_smoke_config(),
            )
            print(f"run_outcome     = {result.run_outcome}")
            print(f"run_dir         = {result.run_dir}")
            print(f"latest_advanced = {result.latest_advanced}")
            return EXIT_OK if result.run_outcome == "completed" else EXIT_RUN_NOT_COMPLETED

        if args.resume is not None:
            ladder_root = args.resume
            if not ladder_root.is_dir():
                print(
                    f"ERROR: --resume ladder root does not exist: {ladder_root}",
                    file=sys.stderr,
                )
                return EXIT_BAD_SELECTION
            print(f"  resuming    : {ladder_root}", flush=True)
        else:
            ladder_root = (
                DEFAULT_RUNS_ROOT
                / "ladder"
                / f"{datetime.now(timezone.utc):%Y-%m-%dT%H%MZ}"
            )
        _write_runtime_preflight(preflight, ladder_root)
        fireworks_key = os.environ.get(FIREWORKS_API_KEY_ENV, "").strip() or None
        # Orphan-sweep belt (SP-1): force-delete any `ondemand-` deployment a
        # prior crash left running BEFORE we start, and again in a finally after,
        # so a stuck GPU can never bill unbounded across runs. Only when an
        # on-demand condition is in scope and the key is present.
        if has_ondemand and fireworks_key:
            swept = sweep_orphans(
                FIREWORKS_ACCOUNT_ID,
                prefix=ONDEMAND_DEPLOYMENT_PREFIX,
                api_key=fireworks_key,
            )
            if swept:
                print(f"orphan sweep (start): force-deleted {swept}", flush=True)
        try:
            exit_code, _gate = run_ladder(
                conditions,
                ladder_root=ladder_root,
                below_floor_condition_id=args.below_floor_condition_id,
                max_wall_minutes=args.max_wall_minutes,
                assumed_rep_seconds=args.assumed_rep_seconds,
                operate_floor_pass_rate=args.operate_floor_pass_rate,
                resume=args.resume is not None,
                fireworks_api_key=fireworks_key,
                account_id=FIREWORKS_ACCOUNT_ID,
                validate_only=args.validate_only,
                cost_ceiling_usd=args.cost_ceiling_usd,
            )
        finally:
            if has_ondemand and fireworks_key:
                swept = sweep_orphans(
                    FIREWORKS_ACCOUNT_ID,
                    prefix=ONDEMAND_DEPLOYMENT_PREFIX,
                    api_key=fireworks_key,
                )
                if swept:
                    print(f"orphan sweep (end): force-deleted {swept}", flush=True)
        return exit_code
    except FileExistsError as exc:
        print(
            f"ERROR: run dir already exists (same UTC minute + HEAD): {exc}",
            file=sys.stderr,
        )
        return EXIT_RUN_DIR_EXISTS
    except subprocess.CalledProcessError as exc:
        print(
            f"ERROR: could not resolve git HEAD for the run id: {exc}",
            file=sys.stderr,
        )
        return EXIT_GIT_HEAD_FAILED


if __name__ == "__main__":
    raise SystemExit(main())
