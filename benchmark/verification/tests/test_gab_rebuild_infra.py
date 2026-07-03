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
