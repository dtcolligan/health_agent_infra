"""Persona pipeline runner.

For each ``PersonaSpec``:

    1. Create an isolated temp directory + state DB at
       ``/tmp/hai_persona_<id>/``.
    2. Run ``hai state init`` against the persona DB.
    3. Seed: ``hai memory set`` for body comp / goals / training pattern,
       ``hai target set`` + ``hai target commit`` for kcal + protein
       targets, plus per-persona intake history (strength, running,
       cross, nutrition, readiness, stress).
    4. Render the synthetic Garmin CSV into a per-persona export dir,
       run ``hai pull --source csv`` against it, then ``hai clean``.
    5. Run ``hai daily``, then ``hai today`` and ``hai explain``.
    6. Capture the structured output into a per-persona findings JSON.

Strict isolation: every subprocess runs with ``HAI_STATE_DB`` set to
the persona DB path, plus ``HAI_BASE_DIR`` set to the persona's temp
intake root, so the runner never touches the maintainer's real state.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional

from .personas import ALL_PERSONAS, PersonaSpec
from .personas.base import (
    StrengthSession,
    RunSession,
    NutritionDay,
    render_garmin_csv,
    synthesise_wearable_history,
)


@dataclass
class PersonaRunResult:
    """Captured output from one persona's pipeline run."""

    persona_id: str
    persona_label: str
    as_of_date: str
    db_path: str
    setup_steps: list[dict[str, Any]] = field(default_factory=list)
    pull_status: Optional[dict[str, Any]] = None
    clean_status: Optional[dict[str, Any]] = None
    daily_status: Optional[dict[str, Any]] = None
    today_text: Optional[str] = None
    explain_summary: Optional[dict[str, Any]] = None
    actions_per_domain: dict[str, str] = field(default_factory=dict)
    findings: list[dict[str, Any]] = field(default_factory=list)
    crashes: list[dict[str, Any]] = field(default_factory=list)


def _run(
    cmd: list[str],
    *,
    env: dict[str, str],
    timeout: int = 30,
    capture_json: bool = False,
) -> tuple[int, str, str]:
    """Run a subprocess and return (returncode, stdout, stderr)."""

    try:
        proc = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return 124, exc.stdout or "", exc.stderr or "timeout"
    return proc.returncode, proc.stdout, proc.stderr


def _persona_env(spec: PersonaSpec, db_path: Path, base_dir: Path) -> dict[str, str]:
    """Build the env-var dict for subprocess calls — strict isolation."""

    env = os.environ.copy()
    env["HAI_STATE_DB"] = str(db_path)
    env["HAI_BASE_DIR"] = str(base_dir)
    return env


def setup_persona_state(
    spec: PersonaSpec,
    db_path: Path,
    base_dir: Path,
    as_of: date,
) -> list[dict[str, Any]]:
    """Run init + memory + target + intake seeds. Return per-step status."""

    env = _persona_env(spec, db_path, base_dir)
    steps: list[dict[str, Any]] = []

    # state init
    rc, out, err = _run(["uv", "run", "hai", "state", "init"], env=env)
    steps.append(
        {
            "step": "state_init",
            "rc": rc,
            "ok": rc == 0,
            "stderr": err.strip()[:300] if err else None,
        }
    )

    # memory writes
    memories = [
        ("context", "body_weight_kg", str(spec.weight_kg)),
        ("context", "height_cm", str(spec.height_cm)),
        ("context", "biological_sex", spec.sex_at_birth),
        ("context", "age", str(spec.age)),
        ("context", "activity_level", spec.activity_level),
        ("goal", "primary_goal", spec.goal_description),
        (
            "context",
            "training_pattern",
            f"{spec.weekly_strength_count} strength + {spec.weekly_running_count} running per week",
        ),
    ]
    if spec.sleep_window_target:
        memories.append(
            (
                "context",
                "sleep_window_target",
                f"{spec.sleep_window_target[0]}-{spec.sleep_window_target[1]}",
            )
        )

    for category, key, value in memories:
        rc, out, err = _run(
            [
                "uv", "run", "hai", "memory", "set",
                "--category", category,
                "--key", key,
                "--value", value,
                "--ingest-actor", "claude_agent_v1",
            ],
            env=env,
        )
        steps.append(
            {
                "step": f"memory_set_{category}_{key}",
                "rc": rc,
                "ok": rc == 0,
                "stderr": err.strip()[:200] if err else None,
            }
        )

    # target propose + commit (kcal + protein)
    if spec.daily_kcal_target is not None:
        steps.extend(
            _propose_and_commit_target(
                env,
                domain="nutrition",
                target_type="calories_kcal",
                value=spec.daily_kcal_target,
                unit="kcal",
                effective_from=as_of,
                reason=f"TDEE estimate for {spec.label}",
            )
        )
    if spec.daily_protein_target_g is not None:
        steps.extend(
            _propose_and_commit_target(
                env,
                domain="nutrition",
                target_type="protein_g",
                value=spec.daily_protein_target_g,
                unit="g",
                effective_from=as_of,
                reason=f"Persona protein target for {spec.label}",
            )
        )

    # intake — readiness for as_of
    rc, out, err = _run(
        [
            "uv", "run", "hai", "intake", "readiness",
            "--soreness", spec.today_soreness,
            "--energy", spec.today_energy,
            "--planned-session-type", spec.today_planned_session,
            "--as-of", as_of.isoformat(),
            "--ingest-actor", "claude_agent_v1",
        ],
        env=env,
    )
    steps.append(
        {
            "step": "intake_readiness",
            "rc": rc,
            "ok": rc == 0,
            "stderr": err.strip()[:200] if err else None,
        }
    )

    # intake — stress for as_of
    rc, out, err = _run(
        [
            "uv", "run", "hai", "intake", "stress",
            "--score", str(spec.today_stress_score),
            "--as-of", as_of.isoformat(),
            "--ingest-actor", "claude_agent_v1",
        ],
        env=env,
    )
    steps.append(
        {
            "step": "intake_stress",
            "rc": rc,
            "ok": rc == 0,
            "stderr": err.strip()[:200] if err else None,
        }
    )

    # intake — historical strength sessions (bulk via --session-json)
    for i, sess in enumerate(spec.recorded_strength_history):
        sess_date = (as_of - timedelta(days=sess.date_offset_days)).isoformat()
        # Convert total volume into 4 plausible sets at typical rep ranges.
        avg_weight_per_rep = sess.total_volume_kg / 20.0  # 4×5 = 20 reps
        session_json_path = base_dir / f"gym_session_{spec.persona_id}_{i}.json"
        session_json_path.parent.mkdir(parents=True, exist_ok=True)
        session_json_path.write_text(
            json.dumps(
                {
                    "session_id": f"persona_{spec.persona_id}_gym_{i}",
                    "session_name": sess.session_type,
                    "as_of_date": sess_date,
                    "notes": f"persona harness — synthetic {sess.session_type} session",
                    "sets": [
                        {
                            "exercise_name": "Squat" if "lower" in sess.session_type else "Bench Press",
                            "set_number": j + 1,
                            "weight_kg": round(avg_weight_per_rep, 1),
                            "reps": 5,
                            "rpe": sess.rpe_avg,
                        }
                        for j in range(4)
                    ],
                }
            ),
            encoding="utf-8",
        )
        rc, out, err = _run(
            [
                "uv", "run", "hai", "intake", "gym",
                "--session-json", str(session_json_path),
                "--ingest-actor", "claude_agent_v1",
            ],
            env=env,
        )
        steps.append(
            {
                "step": f"intake_gym_{sess_date}",
                "rc": rc,
                "ok": rc == 0,
                "stderr": err.strip()[:200] if err else None,
            }
        )

    # intake — historical nutrition
    for nut in spec.recorded_nutrition_history:
        nut_date = (as_of - timedelta(days=nut.date_offset_days)).isoformat()
        rc, out, err = _run(
            [
                "uv", "run", "hai", "intake", "nutrition",
                "--calories", str(nut.calories),
                "--protein-g", str(nut.protein_g),
                "--carbs-g", str(nut.carbs_g),
                "--fat-g", str(nut.fat_g),
                "--as-of", nut_date,
                "--ingest-actor", "claude_agent_v1",
            ],
            env=env,
        )
        steps.append(
            {
                "step": f"intake_nutrition_{nut_date}",
                "rc": rc,
                "ok": rc == 0,
                "stderr": err.strip()[:200] if err else None,
            }
        )

    return steps


def _propose_and_commit_target(
    env: dict[str, str],
    *,
    domain: str,
    target_type: str,
    value: int,
    unit: str,
    effective_from: date,
    reason: str,
) -> list[dict[str, Any]]:
    """Propose then commit a target. Returns two step rows."""

    steps: list[dict[str, Any]] = []
    rc, out, err = _run(
        [
            "uv", "run", "hai", "target", "set",
            "--domain", domain,
            "--target-type", target_type,
            "--value", str(value),
            "--unit", unit,
            "--effective-from", effective_from.isoformat(),
            "--status", "proposed",
            "--source", "agent_proposed",
            "--reason", reason,
            "--ingest-actor", "claude_agent_v1",
        ],
        env=env,
    )
    target_id: Optional[str] = None
    if rc == 0:
        try:
            payload = json.loads(out)
            target_id = payload.get("target_id")
        except (ValueError, TypeError):
            pass
    steps.append(
        {
            "step": f"target_set_{target_type}",
            "rc": rc,
            "ok": rc == 0,
            "target_id": target_id,
            "stderr": err.strip()[:200] if err else None,
        }
    )
    if target_id:
        rc2, out2, err2 = _run(
            [
                "uv", "run", "hai", "target", "commit",
                "--target-id", target_id,
                "--confirm",
            ],
            env=env,
        )
        steps.append(
            {
                "step": f"target_commit_{target_type}",
                "rc": rc2,
                "ok": rc2 == 0,
                "target_id": target_id,
                "stderr": err2.strip()[:200] if err2 else None,
            }
        )
    return steps


def render_persona_pull_csv(
    spec: PersonaSpec,
    export_dir: Path,
    as_of: date,
) -> None:
    """Write the synthetic Garmin daily-summary CSV for this persona."""

    export_dir.mkdir(parents=True, exist_ok=True)
    rows = synthesise_wearable_history(spec, as_of)
    csv_text = render_garmin_csv(rows, as_of)
    out_path = export_dir / "daily_summary_export.csv"
    out_path.write_text(csv_text, encoding="utf-8")


def run_pipeline(
    spec: PersonaSpec,
    as_of: date,
    workdir: Path,
) -> PersonaRunResult:
    """Drive one persona through pull → clean → daily → today."""

    db_path = workdir / "state.db"
    base_dir = workdir / "intake_root"
    base_dir.mkdir(parents=True, exist_ok=True)
    pull_json_path = workdir / "pull.json"
    today_text_path = workdir / "today.txt"

    result = PersonaRunResult(
        persona_id=spec.persona_id,
        persona_label=spec.label,
        as_of_date=as_of.isoformat(),
        db_path=str(db_path),
    )

    # Setup
    try:
        result.setup_steps = setup_persona_state(spec, db_path, base_dir, as_of)
    except Exception as exc:  # pragma: no cover — surfaces as a finding
        result.crashes.append(
            {"phase": "setup", "exc_type": type(exc).__name__, "msg": str(exc)}
        )
        return result

    env = _persona_env(spec, db_path, base_dir)

    # Pull (skip for manual_only personas — no wearable evidence)
    if spec.data_source != "manual_only":
        # We bypass `hai pull` (which reads a fixed CSV path) and call
        # the adapter programmatically with the persona's export dir,
        # then save the pull dict to JSON the same way `hai pull` would.
        try:
            pull_payload = _programmatic_pull(spec, as_of)
            pull_json_path.write_text(
                json.dumps(pull_payload, default=str), encoding="utf-8"
            )
            result.pull_status = {"ok": True, "path": str(pull_json_path)}
        except Exception as exc:
            result.pull_status = {
                "ok": False,
                "exc_type": type(exc).__name__,
                "msg": str(exc),
            }
            result.crashes.append(
                {"phase": "pull", "exc_type": type(exc).__name__, "msg": str(exc)}
            )
            return result

        # Clean
        rc, out, err = _run(
            [
                "uv", "run", "hai", "clean",
                "--evidence-json", str(pull_json_path),
                "--db-path", str(db_path),
            ],
            env=env,
            timeout=60,
        )
        result.clean_status = {
            "ok": rc == 0,
            "rc": rc,
            "stderr": err.strip()[:500] if err else None,
        }
        if rc != 0:
            result.crashes.append(
                {"phase": "clean", "rc": rc, "stderr": err.strip()[:500]}
            )

    # Snapshot — gives skill stand-in classified_state + policy_result per domain.
    # NOTE: snapshot's --evidence-json expects the OUTPUT of `hai clean`, not
    # the pull JSON. We re-run clean to capture stdout, write it, and pass.
    snapshot_path = workdir / "snapshot.json"
    cleaned_evidence_path: Optional[Path] = None
    if pull_json_path.exists():
        cleaned_evidence_path = workdir / "cleaned_evidence.json"
        rc_clean2, out_clean2, _ = _run(
            [
                "uv", "run", "hai", "clean",
                "--evidence-json", str(pull_json_path),
                "--db-path", str(db_path),
            ],
            env=env,
            timeout=60,
        )
        if rc_clean2 == 0 and out_clean2:
            cleaned_evidence_path.write_text(out_clean2, encoding="utf-8")
        else:
            cleaned_evidence_path = None
    snap_args = [
        "uv", "run", "hai", "state", "snapshot",
        "--as-of", as_of.isoformat(),
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
    ]
    if cleaned_evidence_path and cleaned_evidence_path.exists():
        snap_args.extend(["--evidence-json", str(cleaned_evidence_path)])
    rc_snap, out_snap, err_snap = _run(snap_args, env=env, timeout=60)
    if rc_snap == 0 and out_snap:
        snapshot_path.write_text(out_snap, encoding="utf-8")
    else:
        result.crashes.append(
            {"phase": "snapshot", "rc": rc_snap, "stderr": err_snap.strip()[:500]}
        )

    # Synthetic skill — post minimal DomainProposal rows for each domain
    if snapshot_path.exists():
        from .synthetic_skill import post_proposals_for_persona

        propose_rows = post_proposals_for_persona(
            snapshot_path=snapshot_path,
            workdir=workdir,
            user_id="u_local_1",
            for_date=as_of,
            db_path=db_path,
            base_dir=base_dir,
            env=env,
        )
        result.setup_steps.extend(propose_rows)

    # Daily
    rc, out, err = _run(
        [
            "uv", "run", "hai", "daily",
            "--as-of", as_of.isoformat(),
            "--user-id", "u_local_1",
            "--skip-pull",
        ],
        env=env,
        timeout=60,
    )
    result.daily_status = {
        "ok": rc == 0,
        "rc": rc,
        "stderr": err.strip()[:500] if err else None,
    }
    if rc != 0:
        result.crashes.append(
            {"phase": "daily", "rc": rc, "stderr": err.strip()[:500]}
        )
        return result

    # Today (rendered text)
    rc, out, err = _run(
        ["uv", "run", "hai", "today", "--user-id", "u_local_1"],
        env=env,
    )
    if rc == 0:
        result.today_text = out
        today_text_path.write_text(out, encoding="utf-8")

    # Explain (structured)
    rc, out, err = _run(
        [
            "uv", "run", "hai", "explain",
            "--for-date", as_of.isoformat(),
            "--user-id", "u_local_1",
        ],
        env=env,
    )
    if rc == 0 and out:
        try:
            payload = json.loads(out)
            recs = payload.get("recommendations", [])
            for r in recs:
                result.actions_per_domain[r.get("domain", "?")] = r.get("action", "?")
            result.explain_summary = {
                "plan_id": payload.get("plan", {}).get("daily_plan_id"),
                "n_proposals": len(payload.get("proposals", [])),
                "n_planned": len(payload.get("planned_recommendations", [])),
                "n_recommendations": len(recs),
                "n_reviews": len(payload.get("reviews", [])),
                "x_rules_fired": payload.get("plan", {}).get("x_rules_fired", []),
            }
        except (ValueError, TypeError) as exc:
            result.crashes.append(
                {"phase": "explain_parse", "exc_type": type(exc).__name__, "msg": str(exc)}
            )

    # Findings synthesis
    result.findings.extend(_synthesise_findings(spec, result))

    return result


def _programmatic_pull(spec: PersonaSpec, as_of: date) -> dict[str, Any]:
    """Stand in for `hai pull` — synthesise the same dict shape directly.

    The runtime expects a pull payload with at least
    ``raw_daily_row``, ``hrv``, ``sleep``, ``resting_hr``,
    ``training_load``, ``activities`` keys. We populate them from the
    synthetic wearable history without reaching for any vendor SDK.
    """

    rows = synthesise_wearable_history(spec, as_of)
    today_row = next((r for r in rows if r.date_offset_days == 0), None)

    raw_daily_row: Optional[dict[str, Any]] = None
    if today_row is not None:
        raw_daily_row = {
            "date": as_of.isoformat(),
            "steps": today_row.steps,
            "resting_hr": today_row.resting_hr,
            "moderate_intensity_min": today_row.moderate_intensity_min,
            "vigorous_intensity_min": today_row.vigorous_intensity_min,
            "all_day_stress": today_row.all_day_stress,
            "body_battery": today_row.body_battery,
            "sleep_score_overall": today_row.sleep_score,
            "acute_load": today_row.acute_load,
            "chronic_load": today_row.chronic_load,
            "health_hrv_value": today_row.hrv_ms,
        }

    # Real intervals.icu pull shape (verified against
    # /tmp/pull_2026-04-27.json):
    #   - pull.sleep: dict (today only) with duration_hours + record_id
    #   - pull.hrv: list of {date, record_id, rmssd_ms}
    #   - pull.resting_hr: list of {bpm, date, record_id}
    #   - pull.training_load: list of {date, load, record_id}
    #   - pull.activities: list of {activity_type, as_of_date, ...}
    #   - pull.raw_daily_row: dict for today
    hrv_series = [
        {
            "date": (as_of - timedelta(days=r.date_offset_days)).isoformat(),
            "record_id": f"persona_{spec.persona_id}_hrv_{r.date_offset_days}",
            "rmssd_ms": r.hrv_ms,
        }
        for r in rows
        if r.hrv_ms is not None
    ]
    rhr_series = [
        {
            "bpm": r.resting_hr,
            "date": (as_of - timedelta(days=r.date_offset_days)).isoformat(),
            "record_id": f"persona_{spec.persona_id}_rhr_{r.date_offset_days}",
        }
        for r in rows
        if r.resting_hr is not None
    ]
    today_sleep: Optional[dict[str, Any]] = None
    if today_row and today_row.sleep_hours is not None:
        today_sleep = {
            "duration_hours": today_row.sleep_hours,
            "record_id": f"persona_{spec.persona_id}_sleep_today",
        }
    load_series = [
        {
            "date": (as_of - timedelta(days=r.date_offset_days)).isoformat(),
            "load": r.acute_load,
            "record_id": f"persona_{spec.persona_id}_load_{r.date_offset_days}",
        }
        for r in rows
        if r.acute_load is not None
    ]

    activities: list[dict[str, Any]] = []
    for run in spec.recorded_run_history:
        run_date = (as_of - timedelta(days=run.date_offset_days)).isoformat()
        activities.append(
            {
                # Required by projector — direct dict access:
                "activity_id": f"persona_{spec.persona_id}_run_{run.date_offset_days}",
                "user_id": "u_local_1",
                "source": "intervals_icu",
                "raw_json": "{}",
                # Common fields read by projector via .get():
                "activity_type": "Run",
                "as_of_date": run_date,
                "start_date_utc": run_date + "T08:00:00Z",
                "start_date_local": run_date + "T08:00:00",
                "external_id": f"persona_{spec.persona_id}_ext_{run.date_offset_days}",
                "name": "Persona run",
                "average_hr": run.avg_hr,
                "max_hr": run.avg_hr + 15,
                "athlete_max_hr": 200,
                "distance_m": run.distance_m,
                "elapsed_time_s": run.duration_s,
                "moving_time_s": run.duration_s,
                "feel": run.feel,
                "calories": run.distance_m * 0.07,
                "trimp": run.duration_s / 60.0,
                "icu_training_load": run.duration_s / 60.0,
                "hr_load": run.duration_s / 60.0,
                "hr_load_type": "HRSS",
                "hr_zone_times_s": [run.duration_s, 0, 0, 0, 0, 0, 0],
                "hr_zones_bpm": [120, 140, 160, 175, 185, 195, 200],
                "interval_summary": [],
                "warmup_time_s": 0,
                "cooldown_time_s": 0,
                "average_cadence_spm": 85.0,
                "average_speed_mps": run.distance_m / run.duration_s if run.duration_s else None,
                "max_speed_mps": (run.distance_m / run.duration_s * 1.2) if run.duration_s else None,
                "average_stride_m": 1.0,
                "pace_s_per_m": run.duration_s / run.distance_m if run.distance_m else None,
                "lap_count": 1,
                "total_elevation_gain_m": 0,
                "total_elevation_loss_m": 0,
                "icu_rpe": run.feel,
                "session_rpe": run.feel,
                "device_name": "persona-harness-synthetic",
            }
        )

    return {
        "as_of_date": as_of.isoformat(),
        "user_id": "u_local_1",
        "source": "intervals_icu" if spec.data_source != "garmin" else "garmin",
        "manual_readiness": {
            "energy": spec.today_energy,
            "soreness": spec.today_soreness,
            "planned_session_type": spec.today_planned_session,
            "submission_id": f"persona_{spec.persona_id}_readiness_{as_of.isoformat()}",
        },
        "pull": {
            "raw_daily_row": raw_daily_row,
            "hrv": hrv_series,
            "resting_hr": rhr_series,
            "sleep": today_sleep,
            "training_load": load_series,
            "activities": activities,
        },
    }


def _synthesise_findings(
    spec: PersonaSpec,
    result: PersonaRunResult,
) -> list[dict[str, Any]]:
    """Compare actual pipeline output against expected behaviour for the spec.

    Returns a list of finding dicts. Each finding is a deviation from
    expected — not necessarily a bug, but a candidate for triage.
    """

    findings: list[dict[str, Any]] = []

    # Setup-step failures
    for step in result.setup_steps:
        if not step.get("ok", False):
            findings.append(
                {
                    "kind": "setup_failure",
                    "severity": "crash",
                    "step": step.get("step"),
                    "rc": step.get("rc"),
                    "stderr": step.get("stderr"),
                }
            )

    # Pipeline crashes
    for crash in result.crashes:
        findings.append(
            {
                "kind": "pipeline_crash",
                "severity": "crash",
                **crash,
            }
        )

    # Daily failed
    if result.daily_status and not result.daily_status.get("ok"):
        findings.append(
            {
                "kind": "daily_failed",
                "severity": "crash",
                "rc": result.daily_status.get("rc"),
                "stderr": result.daily_status.get("stderr"),
            }
        )

    # Domain coverage check — did we get a recommendation for every domain?
    expected_domains = {"recovery", "running", "sleep", "stress", "strength", "nutrition"}
    actual_domains = set(result.actions_per_domain.keys())
    missing = expected_domains - actual_domains
    if missing:
        findings.append(
            {
                "kind": "missing_domain_coverage",
                "severity": "audit-chain-break",
                "missing_domains": sorted(missing),
            }
        )

    # Action sanity per persona — W-AK (v0.1.13) declarative checks.
    # Pre-W-AK behaviour was ad-hoc (hardcoded "escalate is wrong on
    # thin history"); the spec now declares per-domain whitelists +
    # blacklists so the contract is auditable on the persona file.
    actions = result.actions_per_domain
    expected = spec.expected_actions or {}
    forbidden = spec.forbidden_actions or {}

    for domain, action in actions.items():
        # Whitelist check — if the persona declared an expected list
        # for this domain, the action must be in it.
        whitelist = expected.get(domain)
        if whitelist and action not in whitelist:
            findings.append(
                {
                    "kind": "action_outside_persona_whitelist",
                    "severity": "action-mismatch",
                    "domain": domain,
                    "actual_action": action,
                    "expected_actions": list(whitelist),
                    "note": (
                        f"Persona {spec.persona_id!r} declares "
                        f"expected_actions[{domain!r}] = {sorted(whitelist)}; "
                        f"actual action {action!r} is not in that whitelist."
                    ),
                }
            )

        # Blacklist check — declared forbidden actions must not fire.
        blacklist = forbidden.get(domain)
        if blacklist and action in blacklist:
            findings.append(
                {
                    "kind": "action_in_persona_blacklist",
                    "severity": "action-mismatch",
                    "domain": domain,
                    "actual_action": action,
                    "forbidden_actions": list(blacklist),
                    "note": (
                        f"Persona {spec.persona_id!r} declares "
                        f"forbidden_actions[{domain!r}] = {sorted(blacklist)}; "
                        f"actual action {action!r} is in that blacklist."
                    ),
                }
            )

    return findings


def _preflight_demo_session_check() -> None:
    """v0.1.14 W-FRESH-EXT (F-PHASE0-01 absorption): refuse to run if a
    demo-session marker is active.

    A demo-session marker (whether orphan or valid) makes
    ``resolve_db_path`` / ``resolve_base_dir`` redirect every persona's
    ``hai propose`` / ``hai intake`` / ``hai synthesize`` calls into the
    demo's scratch state. v0.1.14 Phase 0 caught this on a fresh sweep;
    the runner pre-flight prevents recurrence.

    F-IR-03 (Codex IR round 1): the original implementation only
    refused on orphan markers, missing the high-risk **valid active
    marker** case. The fix below refuses on any active marker
    (orphan or valid), naming both kinds in the failure message.

    Raises ``SystemExit(2)`` if any demo session is active. Returns
    silently otherwise.
    """

    from health_agent_infra.core.demo.session import (
        cleanup_orphans,
        get_active_marker,
        is_demo_active,
    )

    if is_demo_active():
        marker = get_active_marker()
        marker_id = marker.marker_id if marker is not None else "<unparseable>"
        print(
            f"verification/dogfood/runner: refusing to start with an "
            f"active demo session (marker_id={marker_id}). The persona "
            f"harness's `hai propose` / `hai intake` calls would be "
            f"silently routed to the demo's scratch state. End the demo "
            f"session via `hai demo end` (if you started it deliberately) "
            f"or `hai demo cleanup` (if it's stale), then re-run.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    # Even when no marker is active by reading the marker file, sweep
    # for unreadable / partially-written markers; refuse if cleanup
    # finds any. This catches the narrow "marker file got corrupted"
    # path that `is_demo_active` returns False for.
    cleaned = cleanup_orphans()
    if cleaned:
        print(
            f"verification/dogfood/runner: refusing to start with stale "
            f"demo-session marker(s) just cleaned: {cleaned}. Re-run "
            f"after confirming no live demo session needed those "
            f"scratch dirs.",
            file=sys.stderr,
        )
        raise SystemExit(2)


def run_all_personas(
    as_of: Optional[date] = None,
    output_dir: Optional[Path] = None,
) -> list[PersonaRunResult]:
    """Drive every persona in ``ALL_PERSONAS`` and return the result list."""

    _preflight_demo_session_check()

    if as_of is None:
        as_of = date.today()
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="hai_dogfood_"))
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[PersonaRunResult] = []
    for spec in ALL_PERSONAS:
        persona_dir = output_dir / spec.persona_id
        if persona_dir.exists():
            shutil.rmtree(persona_dir)
        persona_dir.mkdir(parents=True, exist_ok=True)
        print(f"=== Running {spec.persona_id} — {spec.label} ===", file=sys.stderr)
        result = run_pipeline(spec, as_of, persona_dir)
        results.append(result)

        # Per-persona findings JSON
        out_path = persona_dir / "result.json"
        out_path.write_text(
            json.dumps(asdict(result), indent=2, default=str),
            encoding="utf-8",
        )
        print(
            f"  → {len(result.findings)} finding(s), "
            f"{len(result.crashes)} crash(es) "
            f"(actions: {result.actions_per_domain})",
            file=sys.stderr,
        )

    return results


def write_summary(
    results: list[PersonaRunResult],
    output_path: Path,
) -> None:
    """Write a consolidated cross-persona summary to disk."""

    by_persona = {r.persona_id: asdict(r) for r in results}
    cross_findings: dict[str, list[str]] = {}
    for r in results:
        for f in r.findings:
            kind = f.get("kind", "unknown")
            cross_findings.setdefault(kind, []).append(r.persona_id)

    summary = {
        "n_personas": len(results),
        "total_findings": sum(len(r.findings) for r in results),
        "total_crashes": sum(len(r.crashes) for r in results),
        "findings_by_kind": cross_findings,
        "personas": by_persona,
    }
    output_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/hai_dogfood_run")
    results = run_all_personas(output_dir=out_dir)
    write_summary(results, out_dir / "summary.json")
    print(f"\nWrote summary to {out_dir / 'summary.json'}", file=sys.stderr)
    n_crash = sum(len(r.crashes) for r in results)
    n_find = sum(len(r.findings) for r in results)
    print(f"\nTotal personas: {len(results)}, findings: {n_find}, crashes: {n_crash}", file=sys.stderr)
