"""Run-directory layout detection and rep-artifact loading (readiness SF-1).

Two on-disk layouts exist for scored benchmark runs and BOTH must feed the
same analyzers (cell_contrasts, evidence tables):

* FLAT (rule baseline / offline repro)::

      run_dir/scores/<name>.score.json
      run_dir/trajectories/<trajectory_id>.json

  Observation artifacts referenced by trajectory steps (``stdout_ref`` /
  ``stderr_ref``) are relative to ``run_dir/trajectories``.

* NESTED (paid pilot, ``pilot_orchestrator.write_rep_artifacts``)::

      run_dir/conditions/<system_id>/runtime_mode_<mode>/tasks/<task_id>/
          rep_XX.trajectory.json
          rep_XX.score.json
          rep_XX.ledger.json
          rep_XX.done            # completion sentinel
          observations/...       # per-step stdout/stderr artifacts

  Observation artifacts are relative to the rep's TASK directory (the
  harness ``output_dir`` for a pilot rep is the task dir), NOT to any
  run-level ``trajectories/`` directory. Loading a nested rep with the flat
  observation root silently scores against zero observations (the scorer
  skips unreadable refs), so ``observation_root`` is carried per rep.

Sentinel semantics mirror the pilot orchestrator's completion contract
(previously enforced inside ``pilot_evidence``): a score without ``.done``
is a hard error, a ``.done`` without a score is a hard error, and a rep
with neither (a partial rep) is skipped.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence


LAYOUT_FLAT = "flat"
LAYOUT_NESTED = "nested"

# Deterministic runtime-mode ordering shared by the analyzers.
MODE_SORT_ORDER = (
    "full_contract",
    "no_validation",
    "no_agent_safe",
    "no_proposal_gate",
    "no_refusal",
    "no_audit_chain",
    "no_runtime_enforcement",
)


@dataclass(frozen=True)
class RepRecord:
    """One completed, cross-checked rep with its per-rep observation root."""

    layout: str
    system_id: str
    runtime_mode: str
    task_id: str
    rep_label: str
    score: dict[str, Any]
    trajectory: dict[str, Any]
    ledger: dict[str, Any] | None
    observation_root: Path
    score_path: Path
    task_dir: Path | None
    mode_dir: Path | None
    system_dir: Path | None


def detect_run_layout(run_dir: Path) -> str:
    """Detect which layout a run directory uses."""

    if (run_dir / "conditions").is_dir():
        return LAYOUT_NESTED
    if (run_dir / "scores").is_dir():
        return LAYOUT_FLAT
    raise ValueError(
        f"unrecognised run layout: {run_dir} has neither a conditions/ "
        "(nested pilot) nor a scores/ (flat rule-baseline) directory"
    )


def load_rep_records(run_dir: Path) -> list[RepRecord]:
    """Load every completed rep from a run dir in either layout."""

    layout = detect_run_layout(run_dir)
    if layout == LAYOUT_NESTED:
        records = list(iter_nested_rep_records(run_dir))
    else:
        records = list(_iter_flat_rep_records(run_dir))
    if not records:
        raise ValueError(f"no completed scored reps found under {run_dir}")
    return records


def iter_nested_condition_dirs(
    run_dir: Path,
) -> Iterator[tuple[str, Path, str, Path]]:
    """Yield (system_id, system_dir, runtime_mode, mode_dir) sorted.

    Every ``runtime_mode_*`` directory is yielded, including ones with no
    completed reps, so callers that validate per-condition artifacts
    (condition_index / condition_summary) keep full coverage.
    """

    conditions_dir = run_dir / "conditions"
    if not conditions_dir.is_dir():
        raise ValueError(
            f"required artifact directory not found: {conditions_dir}"
        )
    for system_dir in sorted(
        path for path in conditions_dir.iterdir() if path.is_dir()
    ):
        mode_dirs = sorted(
            (path for path in system_dir.glob("runtime_mode_*") if path.is_dir()),
            key=lambda path: _mode_sort_key(
                path.name.removeprefix("runtime_mode_")
            ),
        )
        for mode_dir in mode_dirs:
            yield (
                system_dir.name,
                system_dir,
                mode_dir.name.removeprefix("runtime_mode_"),
                mode_dir,
            )


def iter_nested_rep_records(run_dir: Path) -> Iterator[RepRecord]:
    """Walk the nested pilot layout with .done-sentinel respect."""

    for system_id, system_dir, runtime_mode, mode_dir in (
        iter_nested_condition_dirs(run_dir)
    ):
        tasks_dir = mode_dir / "tasks"
        if not tasks_dir.exists():
            continue
        for score_path in sorted(tasks_dir.glob("*/rep_*.score.json")):
            rep_label = score_path.name.removesuffix(".score.json")
            task_dir = score_path.parent
            done_path = task_dir / f"{rep_label}.done"
            if not done_path.exists():
                raise ValueError(
                    f"{score_path}: completed score missing .done sentinel"
                )
            ledger_path = task_dir / f"{rep_label}.ledger.json"
            trajectory_path = task_dir / f"{rep_label}.trajectory.json"
            score = load_json_object(score_path)
            ledger = load_json_object(ledger_path)
            trajectory = load_json_object(trajectory_path)
            assert_rep_artifact_match(
                score=score,
                ledger=ledger,
                trajectory=trajectory,
                score_path=score_path,
                trajectory_path=trajectory_path,
                ledger_path=ledger_path,
                expected_system_id=system_id,
                expected_runtime_mode=runtime_mode,
                expected_task_id=task_dir.name,
                expected_rep_label=rep_label,
            )
            yield RepRecord(
                layout=LAYOUT_NESTED,
                system_id=system_id,
                runtime_mode=runtime_mode,
                task_id=task_dir.name,
                rep_label=rep_label,
                score=score,
                trajectory=trajectory,
                ledger=ledger,
                # Pilot observation artifacts are written relative to the
                # rep's task dir (harness output_dir == task_dir).
                observation_root=task_dir,
                score_path=score_path,
                task_dir=task_dir,
                mode_dir=mode_dir,
                system_dir=system_dir,
            )
        for done_path in sorted(tasks_dir.glob("*/rep_*.done")):
            score_path = done_path.with_suffix(".score.json")
            if not score_path.exists():
                raise ValueError(
                    f"{done_path}: .done sentinel missing score artifact"
                )


def _iter_flat_rep_records(run_dir: Path) -> Iterator[RepRecord]:
    scores_dir = run_dir / "scores"
    trajectory_dir = run_dir / "trajectories"
    for score_path in sorted(scores_dir.glob("*.score.json")):
        score = load_json_object(score_path)
        trajectory_path = trajectory_dir / f"{score['trajectory_id']}.json"
        trajectory = load_json_object(trajectory_path)
        assert_score_trajectory_match(score, trajectory, score_path=score_path)
        yield RepRecord(
            layout=LAYOUT_FLAT,
            system_id=str(score["system_id"]),
            runtime_mode=str(score["runtime_mode"]),
            task_id=str(score["task_id"]),
            rep_label=score_path.name.removesuffix(".score.json"),
            score=score,
            trajectory=trajectory,
            ledger=None,
            observation_root=trajectory_dir,
            score_path=score_path,
            task_dir=None,
            mode_dir=None,
            system_dir=None,
        )


def assert_score_trajectory_match(
    score: Mapping[str, Any],
    trajectory: Mapping[str, Any],
    *,
    score_path: Path,
) -> None:
    """Cross-check the identity fields shared by a score and its trajectory."""

    checks = {
        "trajectory_id": trajectory["trajectory_id"],
        "task_id": trajectory["task_id"],
        "system_id": trajectory["system_id"],
        "runtime_mode": trajectory["runtime_mode"],
        "model_class": trajectory["model_class"],
    }
    for key, expected in checks.items():
        if score[key] != expected:
            raise ValueError(f"{score_path}: score/trajectory mismatch for {key}")
    if score["manifest_version"] != trajectory["manifest_snapshot_id"]:
        raise ValueError(
            f"{score_path}: score manifest_version does not match trajectory"
        )


def assert_rep_artifact_match(
    *,
    score: Mapping[str, Any],
    ledger: Mapping[str, Any],
    trajectory: Mapping[str, Any],
    score_path: Path,
    trajectory_path: Path,
    ledger_path: Path,
    expected_system_id: str,
    expected_runtime_mode: str,
    expected_task_id: str,
    expected_rep_label: str,
) -> None:
    """Nested-layout cross-artifact consistency checks (from pilot_evidence)."""

    require_keys(
        score,
        (
            "task_id",
            "trajectory_id",
            "system_id",
            "runtime_mode",
            "model_class",
            "manifest_version",
            "scorer_version",
            "scorer_config_hash",
            "overall_pass",
            "metrics",
        ),
        score_path,
    )
    require_keys(
        trajectory,
        (
            "trajectory_id",
            "task_id",
            "system_id",
            "runtime_mode",
            "model_class",
            "manifest_snapshot_id",
        ),
        trajectory_path,
    )
    require_keys(
        ledger,
        ("system_id", "runtime_mode", "task_id", "rep_label", "disposition"),
        ledger_path,
    )
    expected = {
        "system_id": expected_system_id,
        "runtime_mode": expected_runtime_mode,
        "task_id": expected_task_id,
    }
    for key, value in expected.items():
        if score[key] != value or trajectory[key] != value or ledger[key] != value:
            raise ValueError(f"{score_path}: artifact mismatch for {key}")
    if ledger["rep_label"] != expected_rep_label:
        raise ValueError(f"{score_path}: ledger rep_label mismatch")
    if score["trajectory_id"] != trajectory["trajectory_id"]:
        raise ValueError(f"{score_path}: score/trajectory_id mismatch")
    if score["manifest_version"] != trajectory["manifest_snapshot_id"]:
        raise ValueError(f"{score_path}: score/trajectory manifest mismatch")


def load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"required artifact not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def require_keys(
    payload: Mapping[str, Any],
    keys: Sequence[str],
    path: Path,
) -> None:
    missing = [key for key in keys if key not in payload]
    if missing:
        raise ValueError(f"{path}: missing required keys {missing!r}")


def _mode_sort_key(runtime_mode: str) -> tuple[int, str]:
    try:
        return (MODE_SORT_ORDER.index(runtime_mode), runtime_mode)
    except ValueError:
        return (len(MODE_SORT_ORDER), runtime_mode)
