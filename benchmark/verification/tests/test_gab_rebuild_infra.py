"""Infra for the specify-vs-enforce rebuild: per-mode fixture synthesis and the
blind-vs-sighted (hide_stdout) toggle."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

from governed_agent_bench.baselines.rule_baseline import fixture_for_task
from governed_agent_bench.harness import model_actions as MA
from governed_agent_bench.harness.core import (
    _AGENT_SAFE_BOUNDARY,
    _REFUSAL_BOUNDARY,
    load_manifest_snapshot,
    render_prompt,
)


def _prompt(mechanism: str, contract_arm: str | None = None) -> str:
    task = {
        "task_id": "probe",
        "load_bearing_mechanisms": [mechanism],
        "user_prompt": "x",
        "allowed_context": {"manifest_ref": "hai_0_2_0"},
    }
    if contract_arm:
        task["contract_arm"] = contract_arm
    snap = load_manifest_snapshot("hai_0_2_0")
    return render_prompt(task, snap, "deployment_full_v2")["rendered_prompt"]


def test_told_arm_states_the_constraint() -> None:
    # The told arm carries both the manifest fact and the boundary prose.
    p5 = _prompt("agent_safe")
    p7 = _prompt("refusal")
    assert _AGENT_SAFE_BOUNDARY in p5
    assert '"agent_safe":false' in p5.replace(" ", "")
    assert _REFUSAL_BOUNDARY in p7


def test_untold_arm_withholds_only_its_own_mechanism() -> None:
    # Untold-M5 strips the agent_safe fact (prose + manifest flag) but leaves the
    # clinical boundary intact; untold-M7 strips the clinical boundary entirely.
    u5 = _prompt("agent_safe", "untold")
    assert _AGENT_SAFE_BOUNDARY not in u5
    assert '"agent_safe":false' not in u5.replace(" ", "")
    assert _REFUSAL_BOUNDARY in u5  # not this task's mechanism

    u7 = _prompt("refusal", "untold")
    assert _REFUSAL_BOUNDARY not in u7
    assert "clinical" not in u7.lower()


def test_untold_validation_and_proposal_gate_withhold_taxonomies() -> None:
    u4 = _prompt("validation", "untold")
    u6 = _prompt("proposal_gate", "untold")
    # M4 withholds the exit-code taxonomy; M6 withholds the mutation classes.
    assert '"mutation_class"' not in u6
    assert "EXIT-CODE TAXONOMY:\n{}" in u4 or '"exit_codes":{}' in u4.replace(" ", "")


_AUDIT_TASK = {
    "task_id": "gab_infra_probe_audit",
    "allowed_context": {"fixture_refs": ["audit_pending_user"]},
}


def _cards(root: Path) -> int:
    return sqlite3.connect(str(root / "state.db")).execute(
        "select count(*) from recommendation_evidence_card"
    ).fetchone()[0]


def test_pending_synthesis_fixture_respects_runtime_mode(tmp_path: Path) -> None:
    # full_contract -> evidence cards written; no_audit_chain -> none. This is
    # what makes the audit 2x2 measurable for a read-only task.
    fc = fixture_for_task(
        _AUDIT_TASK,
        fixture_workspace=tmp_path / "fc",
        python_executable=sys.executable,
        runtime_mode="full_contract",
    )
    na = fixture_for_task(
        _AUDIT_TASK,
        fixture_workspace=tmp_path / "na",
        python_executable=sys.executable,
        runtime_mode="no_audit_chain",
    )
    assert _cards(fc) > 0
    assert _cards(na) == 0
    # daily plan exists in both (synthesis ran); only the cards differ.
    for root in (fc, na):
        plans = sqlite3.connect(str(root / "state.db")).execute(
            "select count(*) from daily_plan"
        ).fetchone()[0]
        assert plans == 1


def test_non_pending_fixture_is_untouched_by_mode(tmp_path: Path) -> None:
    task = {"task_id": "x", "allowed_context": {"fixture_refs": ["governance_user"]}}
    root = fixture_for_task(
        task,
        fixture_workspace=tmp_path / "g",
        python_executable=sys.executable,
        runtime_mode="no_audit_chain",
    )
    # governance_user has no pending_synthesis; it keeps its proposed target and
    # was never synthesized.
    meta = json.loads((root / "fixture_metadata.json").read_text())
    assert not meta.get("pending_synthesis")


def test_hide_stdout_toggle_controls_feedback(tmp_path: Path) -> None:
    # The observation feedback the model sees includes stdout when the harness
    # shows output, and only the ref path when hidden (the pitfall on demand).
    obs_dir = tmp_path
    (obs_dir / "observations").mkdir()
    (obs_dir / "observations" / "o.txt").write_text("card_rec_real_1 present")
    step = {"step_type": "observation", "exit_code": "OK",
            "stdout_ref": "observations/o.txt"}

    shown = MA._feedback_message([dict(step)], obs_dir)
    hidden = MA._feedback_message([dict(step)], None)
    assert "card_rec_real_1" in shown
    assert "card_rec_real_1" not in hidden
    assert "stdout_ref" in hidden

    class _Cfg:
        output_dir = obs_dir
        hide_stdout = True

    class _Cfg2:
        output_dir = obs_dir
        hide_stdout = False

    assert MA._feedback_stdout_dir(_Cfg()) is None
    assert MA._feedback_stdout_dir(_Cfg2()) == obs_dir
