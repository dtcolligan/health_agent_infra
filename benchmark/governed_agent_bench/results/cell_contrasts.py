"""2x2 cell labelling and per-mechanism contrast computation (M1).

The paper's central quantities are the per-mechanism 2x2 cell contrasts
(PAPER.md "Experimental Design"). Each benchmark rep occupies one cell of

    |                        | full_contract (enforced) | no_MX (off)          |
    | contract_arm = told    | A: deployment baseline   | B: told-not-enforced |
    | contract_arm = untold  | C: enforced-not-told     | D: neither (floor)   |

and the informative per-mechanism contrasts are

    B - D  effect of telling (contract-in-prompt axis, runtime off)
    C - D  effect of enforcing (runtime axis, contract withheld)
    A - B  marginal value of enforcement GIVEN told (the redundancy headline)

FIRST-ATTEMPT SCORING. A blocked action returns an error, so the runtime's
enforcement surface effectively "tells" the agent the constraint late; cell C
then converges toward cell B after first contact. Axis attribution therefore
must be read on FIRST-ATTEMPT behaviour -- the leading window of a trajectory up
to and including the first runtime enforcement contact -- while converged
multi-turn behaviour is reported separately.

First enforcement contact is derived from the EXISTING trajectory structure: it
is the first ``observation`` step carrying a non-``OK`` ``exit_code`` (the
runtime returning a block / redirect to an agent action). No trajectory-schema
or harness change is required to reconstruct it offline.
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from typing import Any, Mapping, Sequence

from governed_agent_bench.harness import (
    load_manifest_snapshot,
    load_task,
)
from governed_agent_bench.scorer import score_trajectory

from .pilot_evidence import MECHANISM_IDS, MECHANISM_OFF_MODES


CELL_CONTRASTS_SCHEMA_VERSION = "governed_agent_bench.cell_contrasts.v1"

FULL_CONTRACT = "full_contract"
NO_RUNTIME_ENFORCEMENT = "no_runtime_enforcement"

# Canonical load-bearing metric(s) per mechanism, mirroring the H1 metric
# mapping in pilot_evidence so the offline free-baseline machinery and the
# model-backed pilot read the same signal per mechanism.
MECHANISM_METRICS: dict[str, list[tuple[str, str]]] = {
    "validation": [
        ("valid_command_rate", "higher_is_better"),
        ("hallucinated_command_rate", "lower_is_better"),
    ],
    "agent_safe": [
        ("unsafe_action_rate", "lower_is_better"),
    ],
    "proposal_gate": [
        ("unsafe_action_rate", "lower_is_better"),
    ],
    "refusal": [
        ("clinical_claim_rate", "lower_is_better"),
        ("refusal_accuracy", "higher_is_better"),
    ],
    "audit_chain": [
        ("audit_reference_faithfulness", "higher_is_better"),
        ("unsupported_narration_rate", "lower_is_better"),
    ],
}

# The three informative contrasts, expressed as (minuend_cell, subtrahend_cell).
CONTRASTS: dict[str, tuple[str, str]] = {
    "B_vs_D": ("B", "D"),
    "C_vs_D": ("C", "D"),
    "A_vs_B": ("A", "B"),
}

_CELL_ORDER = ("A", "B", "C", "D")

# The base 2x2 holds moderators fixed and uses ONLY the canonical told/untold
# pair per mechanism. Moderator and drift variants are broken out so the
# headline A-vs-B is not averaged over pressure/verifiability/staleness. The
# paper runs the 2x2 UNDER each moderator (PAPER.md Experimental Design), not
# pooled across them. Classification is by task tag.
BASE_CONDITION = "base"
# Moderator conditions map to the paper's moderators; both are told-arm, so they
# populate cells A/B only (a told A/B under the manipulation, compared against
# the base told A/B).
MODERATOR_CONDITIONS = ("goal_conflict", "blind")
_TAG_TO_CONDITION = {
    "goal_conflict": "goal_conflict",   # benign completion-pressure moderator
    "blind_observation": "blind",       # constraint-verifiability moderator
    "drift": "drift",                   # stale-manifest condition (not a moderator)
    "stale_manifest": "drift",
}


def contract_arm_of(task: Mapping[str, Any]) -> str:
    """Return the task's contract arm, defaulting to ``told``."""

    arm = task.get("contract_arm", "told")
    return "untold" if arm == "untold" else "told"


def condition_of(task: Mapping[str, Any]) -> str:
    """Classify a task into its 2x2 condition bucket from its tags.

    ``base`` is the canonical told/untold pair with the moderator held fixed.
    ``goal_conflict`` and ``blind`` are the paper's moderators; ``drift`` is the
    distinct stale-manifest condition. Anything without a recognised variant tag
    is ``base``.
    """

    tags = set(task.get("tags", []))
    for tag, condition in _TAG_TO_CONDITION.items():
        if tag in tags:
            return condition
    return BASE_CONDITION


def cell_label(contract_arm: str, runtime_mode: str) -> str:
    """Label a rep's 2x2 cell from its contract arm and runtime mode.

    ``full_contract`` is the enforced column; any single-mechanism-off mode is
    the off column. ``no_runtime_enforcement`` disables every mechanism at once
    (not the single load-bearing one), so it is the sanity floor rather than a
    2x2 cell and is labelled coherently as ``sanity_floor``.
    """

    if runtime_mode == NO_RUNTIME_ENFORCEMENT:
        return "sanity_floor"
    told = contract_arm != "untold"
    enforced = runtime_mode == FULL_CONTRACT
    if enforced and told:
        return "A"
    if not enforced and told:
        return "B"
    if enforced and not told:
        return "C"
    return "D"


def first_attempt_step_count(steps: Sequence[Mapping[str, Any]]) -> int:
    """Number of leading steps forming the first-attempt window.

    The window ends at (and includes) the first runtime enforcement contact:
    the first ``observation`` step whose ``exit_code`` is not ``OK`` (the
    runtime returning a block / redirect to an agent action). If no such
    observation exists the whole trajectory is first-attempt -- the agent
    either succeeded cleanly or self-refused without ever being blocked.
    """

    for index, step in enumerate(steps):
        if step.get("step_type") != "observation":
            continue
        exit_code = step.get("exit_code")
        if exit_code not in (None, "OK"):
            return index + 1
    return len(steps)


def build_cell_contrasts(run_dir: Path) -> dict[str, Any]:
    """Build the per-mechanism A/B/C/D cell + contrast report for a run dir."""

    reps = _load_reps(run_dir)
    mechanisms = {
        mechanism: _mechanism_report(mechanism, reps)
        for mechanism in MECHANISM_METRICS
    }
    sanity_reps = [rep for rep in reps if rep["cell"] == "sanity_floor"]
    return {
        "schema_version": CELL_CONTRASTS_SCHEMA_VERSION,
        "source_run_dir": str(run_dir),
        "rep_count": len(reps),
        "windows": ["first_attempt", "converged"],
        "cell_definition": {
            "A": "told + full_contract (deployment baseline / enforced)",
            "B": "told + mechanism-off (told-not-enforced / self-enforce)",
            "C": "untold + full_contract (enforced-not-told)",
            "D": "untold + mechanism-off (neither / violation floor)",
            "sanity_floor": "no_runtime_enforcement (all mechanisms off)",
        },
        "contrasts": {
            name: f"{hi} - {lo}" for name, (hi, lo) in CONTRASTS.items()
        },
        "mechanisms": mechanisms,
        "sanity_floor": {
            "runtime_mode": NO_RUNTIME_ENFORCEMENT,
            "rep_count": len(sanity_reps),
            "task_ids": sorted({rep["task_id"] for rep in sanity_reps}),
        },
    }


def write_cell_contrasts(
    *,
    run_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Write the cell-contrast report as a deterministic JSON artifact."""

    report = build_cell_contrasts(run_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "cell_contrasts.json"
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "schema_version": "governed_agent_bench.cell_contrasts_output.v1",
        "rep_count": report["rep_count"],
        "json_path": json_path.as_posix(),
    }


def _load_reps(run_dir: Path) -> list[dict[str, Any]]:
    """Load every scored rep with its first-attempt and converged metrics."""

    score_paths = sorted((run_dir / "scores").glob("*.score.json"))
    if not score_paths:
        raise ValueError(f"no score files found under {run_dir / 'scores'}")
    trajectory_dir = run_dir / "trajectories"
    reps: list[dict[str, Any]] = []
    for score_path in score_paths:
        score = _load_json(score_path)
        trajectory_path = trajectory_dir / f"{score['trajectory_id']}.json"
        trajectory = _load_json(trajectory_path)
        task = load_task(score["task_id"])
        reps.append(
            _rep_from_artifacts(
                score=score,
                trajectory=trajectory,
                task=task,
                observation_root=trajectory_dir,
            )
        )
    return reps


def _rep_from_artifacts(
    *,
    score: Mapping[str, Any],
    trajectory: Mapping[str, Any],
    task: Mapping[str, Any],
    observation_root: Path,
) -> dict[str, Any]:
    arm = contract_arm_of(task)
    runtime_mode = str(trajectory["runtime_mode"])
    converged_metrics = _metric_values(score.get("metrics", {}))
    first_attempt_metrics = _first_attempt_metric_values(
        task=task,
        trajectory=trajectory,
        observation_root=observation_root,
    )
    return {
        "task_id": str(score["task_id"]),
        "runtime_mode": runtime_mode,
        "contract_arm": arm,
        "cell": cell_label(arm, runtime_mode),
        "condition": condition_of(task),
        "load_bearing_mechanisms": [
            str(value) for value in task.get("load_bearing_mechanisms", [])
        ],
        "first_attempt": first_attempt_metrics,
        "converged": converged_metrics,
    }


def _first_attempt_metric_values(
    *,
    task: Mapping[str, Any],
    trajectory: Mapping[str, Any],
    observation_root: Path,
) -> dict[str, float]:
    steps = list(trajectory.get("steps", []))
    window = first_attempt_step_count(steps)
    if window >= len(steps):
        # No post-contact steps: first-attempt == converged. Re-scoring the
        # full trajectory would reproduce the committed score exactly, so skip
        # the work and re-derive from the persisted score at the caller when
        # cheaper. Here we still re-score to keep one code path.
        truncated = dict(trajectory)
    else:
        truncated = dict(trajectory)
        truncated["steps"] = steps[:window]
    rescored = score_trajectory(
        dict(task),
        truncated,
        manifest_snapshot=load_manifest_snapshot(
            str(trajectory["manifest_snapshot_id"])
        ),
        observation_root=observation_root,
    )
    return _metric_values(rescored.get("metrics", {}))


def _metric_values(metrics: Mapping[str, Any]) -> dict[str, float]:
    values: dict[str, float] = {}
    for name, metric in metrics.items():
        if not isinstance(metric, Mapping):
            continue
        value = metric.get("value")
        if isinstance(value, bool):
            values[name] = 1.0 if value else 0.0
        elif isinstance(value, (int, float)):
            values[name] = float(value)
    return values


def _mechanism_report(
    mechanism: str,
    reps: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Per-mechanism report: a base 2x2 that holds moderators fixed, plus
    moderator and drift breakouts with the same cell/contrast structure.

    The base 2x2 uses only the canonical told/untold pair (condition ``base``),
    so the headline A-vs-B is not contaminated by goal-conflict pressure,
    verifiability manipulation, or manifest drift. Each moderator/condition
    variant is a told-arm probe, so it populates cells A/B only.
    """

    off_mode = MECHANISM_OFF_MODES[mechanism]
    in_scope_modes = {FULL_CONTRACT, off_mode}
    mechanism_reps = [
        rep
        for rep in reps
        if mechanism in rep["load_bearing_mechanisms"]
        and rep["runtime_mode"] in in_scope_modes
        and rep["cell"] in _CELL_ORDER
    ]
    by_condition: dict[str, list[Mapping[str, Any]]] = {}
    for rep in mechanism_reps:
        condition = str(rep.get("condition", BASE_CONDITION))
        by_condition.setdefault(condition, []).append(rep)

    moderators: dict[str, Any] = {}
    conditions: dict[str, Any] = {}
    for condition, condition_reps in sorted(by_condition.items()):
        if condition == BASE_CONDITION:
            continue
        block = _cell_block(condition_reps, mechanism)
        if condition in MODERATOR_CONDITIONS:
            moderators[condition] = block
        else:
            conditions[condition] = block

    return {
        "mechanism_id": MECHANISM_IDS[mechanism],
        "mechanism": mechanism,
        "off_mode": off_mode,
        "base": _cell_block(by_condition.get(BASE_CONDITION, []), mechanism),
        "moderators": moderators,
        "conditions": conditions,
    }


def _cell_block(
    reps: Sequence[Mapping[str, Any]],
    mechanism: str,
) -> dict[str, Any]:
    """Build one 2x2 cell/contrast block from a homogeneous set of reps."""

    cells = {
        cell: sorted({rep["task_id"] for rep in reps if rep["cell"] == cell})
        for cell in _CELL_ORDER
    }
    cell_rep_counts = {
        cell: sum(1 for rep in reps if rep["cell"] == cell)
        for cell in _CELL_ORDER
    }
    metrics = {
        metric_name: _metric_contrast(reps, metric_name, direction)
        for metric_name, direction in MECHANISM_METRICS[mechanism]
    }
    return {
        "cell_task_ids": cells,
        "cell_rep_counts": cell_rep_counts,
        "metrics": metrics,
    }


def _metric_contrast(
    reps: Sequence[Mapping[str, Any]],
    metric_name: str,
    direction: str,
) -> dict[str, Any]:
    windows: dict[str, Any] = {}
    for window in ("first_attempt", "converged"):
        cell_values = {
            cell: _cell_median(reps, cell, window, metric_name)
            for cell in _CELL_ORDER
        }
        contrasts = {
            name: _delta(cell_values[hi], cell_values[lo])
            for name, (hi, lo) in CONTRASTS.items()
        }
        windows[window] = {
            "cell_values": cell_values,
            "contrasts": contrasts,
        }
    return {
        "direction": direction,
        "first_attempt": windows["first_attempt"],
        "converged": windows["converged"],
    }


def _cell_median(
    reps: Sequence[Mapping[str, Any]],
    cell: str,
    window: str,
    metric_name: str,
) -> float | None:
    values = [
        float(rep[window][metric_name])
        for rep in reps
        if rep["cell"] == cell and metric_name in rep[window]
    ]
    if not values:
        return None
    return round(float(median(values)), 12)


def _delta(high: float | None, low: float | None) -> float | None:
    if high is None or low is None:
        return None
    return round(high - low, 12)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"required artifact not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
