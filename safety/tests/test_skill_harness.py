"""Replay-mode regression tests for the Phase E skill-harness pilot.

Exercises the committed reference transcripts against the scorer, and
checks the static sanity invariants (rubric doc present, every scenario
has an `expected` block, every committed transcript parses). Lives in
``safety/tests/`` so it runs under normal ``pytest`` but never triggers
live mode — the harness's live backend is opt-in via an env flag that
these tests deliberately never set.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


HARNESS_DIR = Path(__file__).resolve().parents[1] / "evals" / "skill_harness"


@pytest.fixture(scope="module")
def harness():
    """Import the harness runner from its out-of-package location."""

    runner_path = HARNESS_DIR / "runner.py"
    spec = importlib.util.spec_from_file_location(
        "hai_skill_harness_runner", runner_path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_rubric_doc_present() -> None:
    rubric = HARNESS_DIR / "rubrics" / "recovery.md"
    assert rubric.exists(), f"rubric doc missing at {rubric}"
    assert rubric.read_text().strip(), "rubric doc is empty"


def test_every_scenario_has_expected_block(harness) -> None:
    scenarios = harness.load_scenarios("recovery")
    assert scenarios, "no recovery scenarios registered"
    for scenario in scenarios:
        assert "expected" in scenario, scenario["scenario_id"]
        expected = scenario["expected"]
        assert "action" in expected, scenario["scenario_id"]
        assert "policy_decisions_preserved" in expected, scenario["scenario_id"]


def test_compose_snapshot_runs_real_classifier(harness) -> None:
    """Compose a snapshot for each scenario and assert the recovery block
    carries the keys the skill reads — i.e. the harness is actually
    exercising the shipped classify + policy code."""

    for scenario in harness.load_scenarios("recovery"):
        snap = harness.compose_snapshot(scenario)
        block = snap["recovery"]
        for key in ("evidence", "raw_summary", "classified_state", "policy_result"):
            assert key in block, (scenario["scenario_id"], key)
        cs = block["classified_state"]
        assert "recovery_status" in cs
        assert "coverage_band" in cs


def test_replay_scores_committed_transcripts(harness) -> None:
    """Replay the committed reference transcripts and assert correctness
    passes + rubric mean is 2.0 (reference transcripts are authored to
    be perfect scores). If the scorer ever starts failing these, either
    the runtime contracts moved or the references need updating."""

    scenarios = harness.load_scenarios("recovery")
    scored_any = False
    for scenario in scenarios:
        transcript = harness.load_latest_transcript(scenario["scenario_id"])
        if transcript is None:
            continue
        score = harness.score_transcript(scenario, transcript)
        scored_any = True
        assert score.correctness_passed, (
            f"{scenario['scenario_id']}: correctness failed "
            f"— transcript source={transcript.source}, "
            f"correctness={ {k: v.verdict for k, v in score.correctness.items()} }, "
            f"diffs={ {k: v.detail for k, v in score.correctness.items() if v.verdict == 'fail'} }",
        )
        assert score.rubric_mean == 2.0, (
            f"{scenario['scenario_id']}: rubric mean {score.rubric_mean!r} "
            f"!= 2.0 — rubric={score.rubric}",
        )
    assert scored_any, (
        "no committed reference transcripts were scored; did the pilot "
        "lose its scenarios/recovery/transcripts/ tree?"
    )


def test_live_mode_gated_by_env(harness, monkeypatch) -> None:
    """`invoke_live` must refuse to run unless HAI_SKILL_HARNESS_LIVE=1.
    pytest itself must never trigger live mode, so this guard is
    load-bearing."""

    monkeypatch.delenv("HAI_SKILL_HARNESS_LIVE", raising=False)
    scenario = harness.load_scenarios("recovery")[0]
    with pytest.raises(harness.HarnessError) as excinfo:
        harness.invoke_live(scenario)
    assert "HAI_SKILL_HARNESS_LIVE" in str(excinfo.value)


def test_missing_transcript_scenario_is_not_silent(harness) -> None:
    """Scenarios without any transcript must score as a non-pass — the
    pilot would otherwise claim green for branches no one exercised."""

    scenarios_without_transcripts = []
    for scenario in harness.load_scenarios("recovery"):
        transcript = harness.load_latest_transcript(scenario["scenario_id"])
        if transcript is None:
            scenarios_without_transcripts.append(scenario["scenario_id"])
    # The pilot ships with transcripts for exactly h01, h05, h07; any
    # other scenario must currently be in the missing set. The harness's
    # CLI renders these as `transcript=missing`, correctness fail.
    assert scenarios_without_transcripts, (
        "expected at least one scenario without a committed transcript "
        "to exercise the missing-transcript path"
    )
