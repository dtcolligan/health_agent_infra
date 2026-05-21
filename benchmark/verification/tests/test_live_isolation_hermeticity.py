"""Live-isolation workspace and environment hermeticity regression tests."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.harness import HarnessConfig  # noqa: E402
from governed_agent_bench.harness.core import _subprocess_env  # noqa: E402
from governed_agent_bench.results import live_isolation  # noqa: E402


RECIPE_KEYS = (
    "HAI_HERMETIC",
    "HAI_STATE_DB",
    "HAI_BASE_DIR",
    "HAI_RUNTIME_MODE",
    "HAI_INVOCATION_CONTEXT",
    "HOME",
    "XDG_CONFIG_HOME",
)


def _install_live_isolation_mocks(monkeypatch: Any) -> list[dict[str, Any]]:
    captures: list[dict[str, Any]] = []

    def fake_fixture_for_task(
        task: dict[str, Any],
        *,
        fixture_workspace: Path,
        python_executable: str,
    ) -> Path:
        del python_executable
        fixture_id = task["allowed_context"]["fixture_refs"][0]
        fixture_root = fixture_workspace / fixture_id
        fixture_root.mkdir(parents=True, exist_ok=True)
        (fixture_root / "inputs").mkdir(parents=True, exist_ok=True)
        (fixture_root / "inputs" / "recovery_proposal.json").write_text(
            "{}\n", encoding="utf-8"
        )
        (fixture_root / "fixture_metadata.json").write_text(
            '{"pending_intent_id": "intent_test_001"}\n', encoding="utf-8"
        )
        return fixture_root

    def fake_run_operator_actions(
        task: dict[str, Any],
        actions: list[dict[str, Any]],
        config: HarnessConfig,
    ) -> dict[str, Any]:
        env = _subprocess_env(config)
        (config.fixture_root / "mock_probe_write.txt").write_text(
            task["task_id"] + "\n", encoding="utf-8"
        )
        config.output_dir.mkdir(parents=True, exist_ok=True)
        (config.output_dir / "mock_probe_write.txt").write_text(
            config.runtime_mode + "\n", encoding="utf-8"
        )
        captures.append({
            "task": task,
            "actions": actions,
            "config": config,
            "env": {key: env[key] for key in RECIPE_KEYS},
        })
        steps: list[dict[str, Any]] = []
        if config.runtime_mode != "full_contract":
            steps.append({
                "step_type": "mechanism_disabled",
                "mechanism": task["load_bearing_mechanisms"][0],
            })
        steps.append({"step_type": "observation", "exit_code": "OK"})
        return {
            "schema_version": "governed_agent_bench.trajectory.v2",
            "trajectory_id": task["task_id"] + "_" + config.runtime_mode,
            "task_id": task["task_id"],
            "system_id": config.system_id,
            "runtime_mode": config.runtime_mode,
            "model_class": config.model_class,
            "invocation_context": config.invocation_context,
            "steps": steps,
        }

    def fake_score_trajectory(
        task: dict[str, Any],
        trajectory: dict[str, Any],
        *,
        manifest_snapshot: dict[str, Any] | None,
        observation_root: Path,
    ) -> dict[str, Any]:
        del manifest_snapshot, observation_root
        runtime_mode = trajectory["runtime_mode"]
        return {
            "overall_pass": runtime_mode == "full_contract",
            "metrics": {
                metric: {"value": f"{metric}:{runtime_mode}"}
                for metric in task["metrics"]
            },
            "violations": [],
        }

    monkeypatch.setattr(live_isolation, "fixture_for_task", fake_fixture_for_task)
    monkeypatch.setattr(
        live_isolation, "run_operator_actions", fake_run_operator_actions
    )
    monkeypatch.setattr(live_isolation, "score_trajectory", fake_score_trajectory)
    return captures


def _relative_parts(path: Path, root: Path) -> tuple[str, ...]:
    return path.resolve().relative_to(root.resolve()).parts


def _descendant_set(root: Path) -> set[Path]:
    resolved = root.resolve()
    if not resolved.exists():
        return set()
    return {resolved, *(path.resolve() for path in resolved.rglob("*"))}


def test_live_isolation_uses_disjoint_probe_paths_and_env(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    captures = _install_live_isolation_mocks(monkeypatch)
    workspace = tmp_path / "workspace"

    matrix = live_isolation.build_live_isolation_matrix(workspace)

    assert matrix["all_live_isolated"] is True
    assert len(captures) == len(live_isolation.LIVE_PROBES) * 2

    seen_pairs: set[tuple[str, str]] = set()
    path_sets: list[set[Path]] = []
    fixtures_root = workspace / "fixtures"
    runs_root = workspace / "runs"
    expected_pairs = {
        (probe["label"], mode)
        for probe in live_isolation.LIVE_PROBES
        for mode in ("full_contract", probe["off_mode"])
    }

    for capture in captures:
        task = capture["task"]
        config = capture["config"]
        fixture_parts = _relative_parts(config.fixture_root, fixtures_root)
        output_parts = _relative_parts(config.output_dir, runs_root)
        assert len(fixture_parts) >= 3
        assert len(output_parts) == 2

        label, mode = fixture_parts[0], fixture_parts[1]
        assert label == task["load_bearing_mechanisms"][0]
        assert output_parts == (label, mode)
        assert mode == config.runtime_mode

        pair = (label, mode)
        assert pair not in seen_pairs
        seen_pairs.add(pair)

        expected_env = {
            "HAI_HERMETIC": "1",
            "HAI_STATE_DB": str(config.fixture_root / "state.db"),
            "HAI_BASE_DIR": str(config.fixture_root / "base"),
            "HAI_RUNTIME_MODE": config.runtime_mode,
            "HAI_INVOCATION_CONTEXT": config.invocation_context,
            "HOME": str(config.fixture_root / "home"),
            "XDG_CONFIG_HOME": str(config.fixture_root / "xdg_config"),
        }
        assert capture["env"] == expected_env

        fixture_scope = fixtures_root / label / mode
        run_scope = runs_root / label / mode
        written = _descendant_set(fixture_scope) | _descendant_set(run_scope)
        assert written
        assert all(
            path.is_relative_to(fixture_scope.resolve())
            or path.is_relative_to(run_scope.resolve())
            for path in written
        )
        path_sets.append(written)

    assert len(seen_pairs) == len(captures)
    assert seen_pairs == expected_pairs
    for index, left in enumerate(path_sets):
        for right in path_sets[index + 1:]:
            assert left.isdisjoint(right)


def test_live_isolation_cleans_workspace_between_invocations(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    captures = _install_live_isolation_mocks(monkeypatch)
    workspace = tmp_path / "workspace"
    fixture_sentinel = workspace / "fixtures" / "sentinel_fixture.txt"
    run_sentinel = workspace / "runs" / "sentinel_run.txt"
    fixture_sentinel.parent.mkdir(parents=True, exist_ok=True)
    run_sentinel.parent.mkdir(parents=True, exist_ok=True)
    fixture_sentinel.write_text("stale fixture\n", encoding="utf-8")
    run_sentinel.write_text("stale run\n", encoding="utf-8")

    live_isolation.build_live_isolation_matrix(workspace)

    assert not fixture_sentinel.exists()
    assert not run_sentinel.exists()

    post_invocation_sentinel = (
        workspace / "fixtures" / "post_invocation_1_sentinel.txt"
    )
    post_invocation_sentinel.write_text("stale after first run\n", encoding="utf-8")
    captures.clear()

    live_isolation.build_live_isolation_matrix(workspace)

    assert not post_invocation_sentinel.exists()
    assert captures
    for capture in captures:
        config = capture["config"]
        assert config.fixture_root.is_dir()
        assert config.output_dir.is_dir()
        assert (config.fixture_root / "mock_probe_write.txt").exists()
        assert (config.output_dir / "mock_probe_write.txt").exists()
