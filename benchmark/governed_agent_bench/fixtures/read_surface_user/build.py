"""Build the GovernedAgentBench `read_surface_user` fixture.

Mechanism mapping: stresses M8 narration over audit-row evidence by
constructing a synthetic week for `hai today`, `hai explain`,
`hai state snapshot`, and `hai review weekly`.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any


USER_ID = "gab_read_surface"
WEEK_START = date(2026, 4, 27)
DAYS = 7
ISO_WEEK = "2026-W18"

DOMAIN_DEFAULTS = {
    "recovery": ("recovery_proposal.v1", "proceed_with_planned_session"),
    "running": ("running_proposal.v1", "proceed_with_planned_run"),
    "sleep": ("sleep_proposal.v1", "maintain_schedule"),
    "stress": ("stress_proposal.v1", "maintain_routine"),
    "strength": ("strength_proposal.v1", "proceed_with_planned_session"),
    "nutrition": ("nutrition_proposal.v1", "maintain_targets"),
}


def _fixture_dates() -> list[date]:
    return [WEEK_START + timedelta(days=offset) for offset in range(DAYS)]


def _proposal_payload(domain: str, as_of: date, day_index: int) -> dict[str, Any]:
    schema_version, action = DOMAIN_DEFAULTS[domain]
    as_of_text = as_of.isoformat()
    payload: dict[str, Any] = {
        "schema_version": schema_version,
        "proposal_id": f"gab_read_{as_of_text}_{domain}",
        "user_id": USER_ID,
        "for_date": as_of_text,
        "domain": domain,
        "action": action,
        "action_detail": None,
        "rationale": [f"{domain}_synthetic_week_day_{day_index + 1}"],
        "confidence": "moderate",
        "uncertainty": [],
        "policy_decisions": [
            {
                "rule_id": "fixture_week_baseline",
                "decision": "allow",
                "note": "Synthetic policy row for benchmark read fixture.",
            }
        ],
        "bounded": True,
    }
    if domain == "nutrition":
        payload["action_detail"] = {"protein_target_g": 150}
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _review_payload(as_of: date, day_index: int) -> dict[str, Any]:
    as_of_text = as_of.isoformat()
    review_event_id = f"review_{as_of_text}_{USER_ID}_recovery_01"
    recommendation_id = f"rec_{as_of_text}_{USER_ID}_recovery_01"
    return {
        "review_event_id": review_event_id,
        "recommendation_id": recommendation_id,
        "user_id": USER_ID,
        "domain": "recovery",
        "followed_recommendation": day_index % 3 != 1,
        "self_reported_improvement": day_index % 3 == 0,
        "free_text": f"synthetic recovery outcome day {day_index + 1}",
        "recorded_at": f"{as_of_text}T20:00:00+00:00",
        "completed": day_index % 3 != 1,
        "intensity_delta": "same",
        "duration_minutes": 35 + day_index,
        "pre_energy_score": 3,
        "post_energy_score": 4 if day_index % 3 != 1 else 3,
        "disagreed_firing_ids": [],
    }


def _review_recommendation_payload(as_of: date, day_index: int) -> dict[str, Any]:
    as_of_text = as_of.isoformat()
    review_event_id = f"review_{as_of_text}_{USER_ID}_recovery_01"
    recommendation_id = f"rec_{as_of_text}_{USER_ID}_recovery_01"
    review_at = as_of + timedelta(days=1)
    return {
        "recommendation_id": recommendation_id,
        "user_id": USER_ID,
        "for_date": as_of_text,
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "confidence": "moderate",
        "bounded": True,
        "rationale": [f"recovery_synthetic_week_day_{day_index + 1}"],
        "follow_up": {
            "review_event_id": review_event_id,
            "review_at": f"{review_at.isoformat()}T08:00:00+00:00",
            "review_question": "How did the synthetic recovery plan land?",
        },
    }


def build_fixture(root: Path, *, python_executable: str = sys.executable) -> Path:
    """Build a seven-day synthetic HAI state via CLI-only writes."""

    root = root.resolve()
    state_db = root / "state.db"
    base_dir = root / "base"
    home = root / "home"
    xdg_config = root / "xdg_config"
    inputs_dir = root / "inputs"
    base_dir.mkdir(parents=True, exist_ok=True)
    home.mkdir(parents=True, exist_ok=True)
    xdg_config.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.update({
        "HAI_HERMETIC": "1",
        "HAI_STATE_DB": str(state_db),
        "HAI_BASE_DIR": str(base_dir),
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(xdg_config),
    })

    def run(argv: list[str]) -> None:
        subprocess.run(
            [python_executable, "-m", "health_agent_infra.cli", *argv],
            env=env,
            check=True,
            cwd=Path.cwd(),
        )

    run(["state", "init", "--db-path", str(state_db)])

    for day_index, as_of in enumerate(_fixture_dates()):
        as_of_text = as_of.isoformat()
        calories = str(2200 + (day_index * 20))
        protein = str(150 + day_index)
        carbs = str(245 + (day_index * 3))
        fat = str(70)
        hydration = f"{2.4 + (day_index * 0.1):.1f}"

        run([
            "intake",
            "nutrition",
            "--calories",
            calories,
            "--protein-g",
            protein,
            "--carbs-g",
            carbs,
            "--fat-g",
            fat,
            "--hydration-l",
            hydration,
            "--meals-count",
            "3",
            "--as-of",
            as_of_text,
            "--user-id",
            USER_ID,
            "--ingest-actor",
            "hai_cli_direct",
            "--base-dir",
            str(base_dir),
            "--db-path",
            str(state_db),
        ])

        for domain in DOMAIN_DEFAULTS:
            proposal_path = inputs_dir / as_of_text / f"{domain}_proposal.json"
            _write_json(
                proposal_path,
                _proposal_payload(domain, as_of, day_index),
            )
            run([
                "propose",
                "--domain",
                domain,
                "--proposal-json",
                str(proposal_path),
                "--base-dir",
                str(base_dir),
                "--db-path",
                str(state_db),
            ])

        run([
            "synthesize",
            "--as-of",
            as_of_text,
            "--user-id",
            USER_ID,
            "--db-path",
            str(state_db),
        ])

        recommendation_path = inputs_dir / as_of_text / "recovery_rec.json"
        outcome_path = inputs_dir / as_of_text / "recovery_outcome.json"
        _write_json(
            recommendation_path,
            _review_recommendation_payload(as_of, day_index),
        )
        _write_json(outcome_path, _review_payload(as_of, day_index))
        run([
            "review",
            "schedule",
            "--recommendation-json",
            str(recommendation_path),
            "--base-dir",
            str(base_dir),
            "--db-path",
            str(state_db),
        ])
        run([
            "review",
            "record",
            "--outcome-json",
            str(outcome_path),
            "--base-dir",
            str(base_dir),
            "--db-path",
            str(state_db),
        ])

    metadata = {
        "schema_version": "governed_agent_bench.fixture.v1",
        "fixture_id": "read_surface_user",
        "builder": "read_surface_user/build.py",
        "user_id": USER_ID,
        "iso_week": ISO_WEEK,
        "start_date": WEEK_START.isoformat(),
        "days": DAYS,
        "state_db": "state.db",
        "base_dir": "base",
        "commands": [
            ["hai", "state", "init", "--db-path", "<fixture>/state.db"],
            ["hai", "intake", "nutrition", "--as-of", "<fixture-week-day>"],
            ["hai", "propose", "--domain", "<six-domains>"],
            ["hai", "synthesize", "--as-of", "<fixture-week-day>"],
            ["hai", "review", "schedule"],
            ["hai", "review", "record"],
        ],
        "mechanisms_stressed": ["M8"],
        "read_surfaces": [
            "hai today",
            "hai explain",
            "hai state snapshot",
            "hai review weekly",
        ],
        "contains_private_data": False,
    }
    _write_json(root / "fixture_metadata.json", metadata)
    return state_db


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture_root", type=Path)
    args = parser.parse_args(argv)
    build_fixture(args.fixture_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
