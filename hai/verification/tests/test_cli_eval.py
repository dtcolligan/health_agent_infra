"""Tests for `hai eval run` CLI wrappers.

Exercises the subparser registration path on the real ``hai``
dispatcher and confirms argument plumbing + exit codes. Scenario
content is mocked via a temporary scenarios dir.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.evals.runner import SCENARIOS_ROOT  # noqa: F401
from health_agent_infra.core import exit_codes


@pytest.fixture()
def isolated_scenarios_dir(tmp_path, monkeypatch):
    """Redirect the eval runner's SCENARIOS_ROOT to a temporary dir so
    the CLI tests don't read real scenario content while they exercise
    plumbing.
    """

    scratch = tmp_path / "evals" / "scenarios"
    for domain in ("recovery", "running", "sleep", "stress", "strength",
                   "nutrition", "synthesis"):
        (scratch / domain).mkdir(parents=True, exist_ok=True)

    import health_agent_infra.evals.runner as runner_mod
    monkeypatch.setattr(runner_mod, "SCENARIOS_ROOT", scratch)

    return scratch


def _write_scenario(scratch: Path, domain: str, scenario: dict) -> Path:
    path = scratch / domain / f"{scenario['scenario_id']}.json"
    path.write_text(json.dumps(scenario, indent=2))
    return path


def _passing_recovery_scenario() -> dict:
    return {
        "scenario_id": "cli_test_rec_rested",
        "kind": "domain",
        "domain": "recovery",
        "description": "rested baseline",
        "input": {
            "evidence": {
                "as_of_date": "2026-04-17",
                "user_id": "u_eval",
                "sleep_hours": 8.0,
                "resting_hr": 52.0,
                "hrv_ms": 80.0,
                "soreness_self_report": "low",
            },
            "raw_summary": {
                "as_of_date": "2026-04-17",
                "user_id": "u_eval",
                "resting_hr_baseline": 52.0,
                "resting_hr_ratio_vs_baseline": 1.0,
                "hrv_ratio_vs_baseline": 1.0,
                "trailing_7d_training_load": 400.0,
                "training_load_baseline": 400.0,
                "training_load_ratio_vs_baseline": 1.0,
                "resting_hr_spike_days": 0,
            },
        },
        "expected": {
            "classified": {"sleep_debt_band": "none"},
            "policy": {"forced_action": None, "capped_confidence": None},
        },
    }


def _failing_recovery_scenario() -> dict:
    s = _passing_recovery_scenario()
    s["scenario_id"] = "cli_test_rec_fails_on_purpose"
    s["expected"]["classified"]["sleep_debt_band"] = "elevated"
    return s


class TestCliDomainRun:
    def test_domain_run_emits_pass_count(
        self, isolated_scenarios_dir, capsys,
    ) -> None:
        _write_scenario(isolated_scenarios_dir, "recovery",
                        _passing_recovery_scenario())
        rc = cli_main(["eval", "run", "--domain", "recovery"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "1/1 passed" in out
        assert "cli_test_rec_rested" in out

    def test_domain_run_failing_scenario_returns_1(
        self, isolated_scenarios_dir, capsys,
    ) -> None:
        _write_scenario(isolated_scenarios_dir, "recovery",
                        _failing_recovery_scenario())
        rc = cli_main(["eval", "run", "--domain", "recovery"])
        assert rc == 1
        out = capsys.readouterr().out
        assert "FAIL" in out
        assert "classified_bands" in out

    def test_domain_run_json_output(
        self, isolated_scenarios_dir, capsys,
    ) -> None:
        _write_scenario(isolated_scenarios_dir, "recovery",
                        _passing_recovery_scenario())
        rc = cli_main(["eval", "run", "--domain", "recovery", "--json"])
        assert rc == 0
        out = capsys.readouterr().out
        payload = json.loads(out)
        assert payload["total"] == 1
        assert payload["passed"] == 1
        assert payload["failed"] == 0
        assert payload["scores"][0]["scenario_id"] == "cli_test_rec_rested"

    def test_no_scenarios_found_returns_2(
        self, isolated_scenarios_dir, capsys,
    ) -> None:
        rc = cli_main(["eval", "run", "--domain", "recovery"])
        assert rc == exit_codes.USER_INPUT
        err = capsys.readouterr().err
        assert "no scenarios found" in err

    def test_synthesis_and_domain_are_mutually_exclusive(
        self, isolated_scenarios_dir,
    ) -> None:
        with pytest.raises(SystemExit):
            cli_main(["eval", "run", "--domain", "recovery", "--synthesis"])

    def test_unknown_domain_rejected_by_argparse(
        self, isolated_scenarios_dir,
    ) -> None:
        with pytest.raises(SystemExit):
            cli_main(["eval", "run", "--domain", "not_a_domain"])
