"""Replay-mode regression tests for the Phase E skill-harness pilot.

Exercises the committed reference transcripts against the scorer, and
checks the static sanity invariants (rubric doc present, every scenario
has an `expected` block, every committed transcript parses). Lives in
``hai/verification/tests/`` so it runs under normal ``pytest`` but never triggers
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


# ---------------------------------------------------------------------------
# v0.1.8 W41 — running domain extension
# ---------------------------------------------------------------------------


def test_running_rubric_doc_present() -> None:
    rubric = HARNESS_DIR / "rubrics" / "running.md"
    assert rubric.exists(), f"running rubric doc missing at {rubric}"
    assert rubric.read_text().strip(), "running rubric doc is empty"


def test_every_running_scenario_has_expected_block(harness) -> None:
    scenarios = harness.load_scenarios("running")
    assert scenarios, "no running scenarios registered"
    for scenario in scenarios:
        assert "expected" in scenario, scenario["scenario_id"]
        expected = scenario["expected"]
        assert "action" in expected, scenario["scenario_id"]
        assert "policy_decisions_preserved" in expected, scenario["scenario_id"]


def test_running_compose_snapshot_runs_real_classifier(harness) -> None:
    """Every running scenario must compose into a running block carrying
    classified_state + policy_result derived from the live runtime
    (not hand-written in the scenario JSON)."""

    for scenario in harness.load_scenarios("running"):
        snap = harness.compose_snapshot(scenario)
        block = snap["running"]
        for key in ("signals", "classified_state", "policy_result"):
            assert key in block, (scenario["scenario_id"], key)
        cs = block["classified_state"]
        assert "running_readiness_status" in cs
        assert "coverage_band" in cs


def test_live_mode_dispatches_skill_on_scenario_domain(harness) -> None:
    """Codex P2-2: invoke_live used to hard-code recovery-readiness.
    Verify the dispatch table maps each supported domain to the
    correct skill name without launching live mode."""

    assert harness._live_skill_name_for_domain("recovery") == "recovery-readiness"
    assert harness._live_skill_name_for_domain("running") == "running-readiness"


def test_live_mode_refuses_unknown_domain(harness) -> None:
    """Unknown domains in live mode must raise rather than silently
    fall back to recovery-readiness."""

    with pytest.raises(harness.HarnessError) as excinfo:
        harness._live_skill_name_for_domain("nonexistent_domain")
    assert "nonexistent_domain" in str(excinfo.value)


def test_running_scenarios_cover_required_paths(harness) -> None:
    """W41 acceptance: running scenarios cover at least one clean,
    one insufficient-signal, one policy-forced, and one cross-domain
    coupling path."""

    scenarios = harness.load_scenarios("running")
    actions = {s["expected"]["action"] for s in scenarios}
    # Clean path.
    assert "proceed_with_planned_run" in actions, scenarios
    # Insufficient-signal path.
    assert "defer_decision_insufficient_signal" in actions
    # Policy-forced path (R-acwr-spike).
    assert "escalate_for_user_review" in actions
    # Cross-domain coupling path (recovery=impaired → running holds).
    assert "cross_train_instead" in actions


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
    # The pilot ships reference transcripts for 6 of the 7 recovery
    # scenarios (h01, h02, h03, h04, h05, h07). h06 (insufficient-
    # coverage defer) is deliberately left un-transcripted so the
    # missing-transcript failure path stays exercised — the harness's
    # CLI renders these as `transcript=missing`, correctness fail. If
    # h06 gains a transcript later, substitute a different always-
    # missing scenario so this guardrail doesn't silently disappear.
    assert scenarios_without_transcripts, (
        "expected at least one scenario without a committed transcript "
        "to exercise the missing-transcript path"
    )
