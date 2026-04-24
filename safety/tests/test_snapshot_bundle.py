"""Contract tests for the Phase 1 snapshot bundle shape.

``hai state snapshot`` is the contract surface the agent reads from.
These tests lock two shapes against accidental drift:

- **v1.0 shape** (no `--evidence-json`): every domain block has
  `today`, `history`, `missingness` (or equivalent per-domain keys).
  Existing behaviour; regression guard.
- **v1.1 full-bundle shape** (with `--evidence-json`): the recovery
  block additionally has `evidence`, `raw_summary`, `classified_state`,
  `policy_result`. Other domain blocks keep v1.0 shape until their own
  classify/policy lands.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.state import initialize_database
from health_agent_infra.core import exit_codes


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return db_path


def _write_clean_bundle(tmp_path: Path, **overrides) -> Path:
    """A minimal `hai clean`-shaped bundle suitable for --evidence-json."""

    bundle = {
        "cleaned_evidence": {
            "as_of_date": "2026-04-17",
            "user_id": "u_local_1",
            "sleep_hours": 8.0,
            "resting_hr": 52.0,
            "hrv_ms": 80.0,
            "soreness_self_report": "low",
        },
        "raw_summary": {
            "as_of_date": "2026-04-17",
            "user_id": "u_local_1",
            "resting_hr_baseline": 52.0,
            "resting_hr_ratio_vs_baseline": 1.0,
            "hrv_ratio_vs_baseline": 1.0,
            "trailing_7d_training_load": 400.0,
            "training_load_baseline": 400.0,
            "training_load_ratio_vs_baseline": 1.0,
            "resting_hr_spike_days": 0,
        },
    }
    for key, value in overrides.items():
        if key in bundle["cleaned_evidence"]:
            bundle["cleaned_evidence"][key] = value
        else:
            bundle["raw_summary"][key] = value
    path = tmp_path / "cleaned.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# v1.0 shape — no --evidence-json
# ---------------------------------------------------------------------------

def test_snapshot_v1_0_recovery_block_has_three_keys(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17",
        "--user-id", "u_local_1",
        "--db-path", str(db),
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert set(payload["recovery"].keys()) == {"today", "history", "missingness", "cold_start", "history_days"}


def test_snapshot_v1_0_running_block_unchanged(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
    ])
    payload = json.loads(capsys.readouterr().out)
    # v0.1.4: running block carries per-session activities_today +
    # activities_history lists, sourced from the running_activity table
    # that was added with migration 017. Empty lists when no intervals.icu
    # pull has run against the profile, so v1.0 consumers that only
    # read today/history still work.
    assert set(payload["running"].keys()) == {
        "today", "history", "missingness", "cold_start", "history_days",
        "activities_today", "activities_history",
    }
    assert payload["running"]["activities_today"] == []
    assert payload["running"]["activities_history"] == []


# ---------------------------------------------------------------------------
# v1.1 full-bundle — with --evidence-json
# ---------------------------------------------------------------------------

def test_snapshot_full_bundle_recovery_has_five_phase_1_keys(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(tmp_path)
    rc = cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)

    # v1.0 keys preserved.
    assert {"today", "history", "missingness"}.issubset(payload["recovery"].keys())
    # v1.1 additions.
    assert {"evidence", "raw_summary", "classified_state", "policy_result"}.issubset(
        payload["recovery"].keys()
    )


def test_snapshot_classified_state_has_all_recovery_band_keys(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    classified = payload["recovery"]["classified_state"]

    assert set(classified.keys()) == {
        "sleep_debt_band",
        "resting_hr_band",
        "hrv_band",
        "training_load_band",
        "soreness_band",
        "coverage_band",
        "recovery_status",
        "readiness_score",
        "uncertainty",
    }
    assert classified["coverage_band"] == "full"
    assert classified["recovery_status"] == "recovered"
    assert isinstance(classified["uncertainty"], list)


def test_snapshot_policy_result_has_four_keys(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    policy = payload["recovery"]["policy_result"]

    assert set(policy.keys()) == {
        "policy_decisions",
        "forced_action",
        "forced_action_detail",
        "capped_confidence",
    }
    assert len(policy["policy_decisions"]) == 3  # R1 + R5 + R6 always fire
    rule_ids = {d["rule_id"] for d in policy["policy_decisions"]}
    assert rule_ids == {
        "require_min_coverage",
        "no_high_confidence_on_sparse_signal",
        "resting_hr_spike_escalation",
    }


def test_snapshot_full_bundle_evidence_matches_input(tmp_path: Path, capsys):
    """The evidence block echoes the input bundle verbatim — it's the
    audit trail of what classify+policy saw.
    """

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(tmp_path, sleep_hours=6.5)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    assert payload["recovery"]["evidence"]["sleep_hours"] == 6.5
    assert payload["recovery"]["classified_state"]["sleep_debt_band"] == "moderate"


def test_snapshot_full_bundle_surfaces_policy_force_when_sparse(tmp_path: Path, capsys):
    """Contract test for a policy-forcing case: no training-load data
    triggers sparse coverage, which R5 softens confidence for.
    """

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(
        tmp_path,
        trailing_7d_training_load=None,
        training_load_baseline=None,
        training_load_ratio_vs_baseline=None,
    )
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    assert payload["recovery"]["classified_state"]["coverage_band"] == "sparse"
    assert payload["recovery"]["policy_result"]["capped_confidence"] == "moderate"


# ---------------------------------------------------------------------------
# Other domains — unchanged even when evidence-json is supplied
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("domain,expected_keys", [
    # Running + nutrition have their own classify/policy now (Phase 2
    # step 3 + Phase 5 step 4 respectively). "gym" remains the legacy
    # top-level key that mirrors the strength block's raw read — it
    # does not receive classify/policy expansion even under
    # --evidence-json, so this parametrize locks its minimal shape.
    ("gym", {"today", "history", "missingness"}),
])
def test_snapshot_other_domains_unchanged_with_evidence_json(
    tmp_path: Path, capsys, domain: str, expected_keys: set[str]
):
    """Domains without their own classify/policy yet keep v1.0 shape.
    A snapshot with --evidence-json must not accidentally expand them.
    """

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    assert set(payload[domain].keys()) == expected_keys


def test_snapshot_nutrition_block_expands_with_evidence_json(
    tmp_path: Path, capsys,
):
    """Phase 5 step 4: nutrition is now a first-class domain block when
    a snapshot is built with ``--evidence-json``. The block gains
    ``signals`` + ``classified_state`` + ``policy_result`` on top of
    the v1.0 ``today``/``history``/``missingness`` shape."""

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)

    expected = {
        "today", "history", "missingness", "cold_start", "history_days",
        "signals", "classified_state", "policy_result",
    }
    assert set(payload["nutrition"].keys()) == expected

    classified = payload["nutrition"]["classified_state"]
    # No accepted row was seeded in this fixture → insufficient coverage.
    assert classified["coverage_band"] == "insufficient"
    # Micronutrient coverage honestly surfaces the v1 data limit.
    assert classified["micronutrient_coverage"] in (
        "unavailable_at_source", "unknown",
    )
    policy = payload["nutrition"]["policy_result"]
    # R-coverage fires on the empty-row day.
    assert policy["forced_action"] == "defer_decision_insufficient_signal"


# ---------------------------------------------------------------------------
# Running block — additive expansion under --evidence-json (Phase 2 step 3)
# ---------------------------------------------------------------------------

def _write_clean_bundle_with_running(tmp_path: Path, **overrides) -> Path:
    """Same as _write_clean_bundle but adds running-relevant raw_summary keys."""

    bundle = {
        "cleaned_evidence": {
            "as_of_date": "2026-04-17",
            "user_id": "u_local_1",
            "sleep_hours": 8.0,
            "resting_hr": 52.0,
            "hrv_ms": 80.0,
            "soreness_self_report": "low",
        },
        "raw_summary": {
            "as_of_date": "2026-04-17",
            "user_id": "u_local_1",
            "resting_hr_baseline": 52.0,
            "resting_hr_ratio_vs_baseline": 1.0,
            "hrv_ratio_vs_baseline": 1.0,
            "trailing_7d_training_load": 400.0,
            "training_load_baseline": 400.0,
            "training_load_ratio_vs_baseline": 1.0,
            "resting_hr_spike_days": 0,
            # Running-relevant raw_summary keys.
            "garmin_acwr_ratio": 1.1,
            "training_readiness_component_mean_pct": 75.0,
        },
    }
    for key, value in overrides.items():
        if key in bundle["cleaned_evidence"]:
            bundle["cleaned_evidence"][key] = value
        else:
            bundle["raw_summary"][key] = value
    path = tmp_path / "cleaned_running.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    return path


def test_snapshot_running_block_v1_0_keys_preserved_under_evidence_json(
    tmp_path: Path, capsys,
):
    """Additive expansion guarantee: today/history/missingness still present."""

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle_with_running(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    assert {"today", "history", "missingness"}.issubset(payload["running"].keys())


def test_snapshot_running_block_adds_signals_classified_policy_under_evidence_json(
    tmp_path: Path, capsys,
):
    """The Phase 2 step 3 expansion adds signals/classified_state/policy_result;
    v0.1.4 adds activities_today/activities_history from migration 017."""

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle_with_running(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    assert set(payload["running"].keys()) == {
        "today", "history", "missingness", "cold_start", "history_days",
        "activities_today", "activities_history",
        "signals", "classified_state", "policy_result",
    }


def test_snapshot_running_block_unchanged_without_evidence_json(
    tmp_path: Path, capsys,
):
    """No --evidence-json => running block is v1.0 + v0.1.4 activity lists
    (which are always present but empty when no intervals.icu pull has run)."""

    db = _init_db(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
    ])
    payload = json.loads(capsys.readouterr().out)
    assert set(payload["running"].keys()) == {
        "today", "history", "missingness", "cold_start", "history_days",
        "activities_today", "activities_history",
    }


def test_snapshot_running_signals_keys_match_classify_input_contract(
    tmp_path: Path, capsys,
):
    """signals dict must carry exactly the keys classify_running_state reads,
    so a future classify-side rename surfaces here as a contract violation
    rather than at agent-prompt time."""

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle_with_running(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    signals = payload["running"]["signals"]
    assert set(signals.keys()) == {
        "weekly_mileage_m",
        "weekly_mileage_baseline_m",
        "recent_hard_session_count_7d",
        "acwr_ratio",
        "training_readiness_pct",
        "sleep_debt_band",
        "resting_hr_band",
        # v0.1.4 structural signals from running_activity.
        "z4_plus_seconds_today",
        "z4_plus_seconds_7d",
        "last_hard_session_days_ago",
        "today_interval_summary",
        "activity_count_14d",
    }


def test_snapshot_running_signals_carry_acwr_and_training_readiness_from_raw_summary(
    tmp_path: Path, capsys,
):
    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle_with_running(
        tmp_path,
        garmin_acwr_ratio=1.4,
        training_readiness_component_mean_pct=55.0,
    )
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    signals = payload["running"]["signals"]
    assert signals["acwr_ratio"] == 1.4
    assert signals["training_readiness_pct"] == 55.0


def test_snapshot_running_signals_pull_recovery_bands_for_cross_domain_peek(
    tmp_path: Path, capsys,
):
    """sleep_debt_band + resting_hr_band on signals echo recovery's
    classified_state — that's the cross-domain peek the running domain
    consumes (no separate Garmin re-pull)."""

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle_with_running(tmp_path, sleep_hours=6.5)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    recovery = payload["recovery"]["classified_state"]
    signals = payload["running"]["signals"]
    assert signals["sleep_debt_band"] == recovery["sleep_debt_band"]
    assert signals["resting_hr_band"] == recovery["resting_hr_band"]
    assert signals["sleep_debt_band"] == "moderate"  # 6.5h sleep → moderate


def test_snapshot_running_classified_state_has_all_running_band_keys(
    tmp_path: Path, capsys,
):
    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle_with_running(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    classified = payload["running"]["classified_state"]
    assert set(classified.keys()) == {
        "weekly_mileage_trend_band",
        "hard_session_load_band",
        "freshness_band",
        "recovery_adjacent_band",
        "coverage_band",
        "running_readiness_status",
        "readiness_score",
        "uncertainty",
    }
    assert isinstance(classified["uncertainty"], list)


def test_snapshot_running_policy_result_has_three_decisions(
    tmp_path: Path, capsys,
):
    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle_with_running(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    policy = payload["running"]["policy_result"]
    assert set(policy.keys()) == {
        "policy_decisions",
        "forced_action",
        "forced_action_detail",
        "capped_confidence",
    }
    rule_ids = {d["rule_id"] for d in policy["policy_decisions"]}
    assert rule_ids == {
        "require_min_coverage",
        "no_high_confidence_on_sparse_signal",
        "acwr_spike_escalation",
    }


def test_snapshot_running_policy_escalates_on_acwr_spike(
    tmp_path: Path, capsys,
):
    """ACWR ≥ 1.5 in raw_summary forces escalate via the running R-rule."""

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle_with_running(tmp_path, garmin_acwr_ratio=1.6)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    assert payload["running"]["classified_state"]["freshness_band"] == "overreaching"
    assert payload["running"]["policy_result"]["forced_action"] == "escalate_for_user_review"


def test_snapshot_running_expansion_does_not_modify_recovery_block_keys(
    tmp_path: Path, capsys,
):
    """Adding running expansion must leave recovery's full-bundle key set
    exactly as Phase 1 froze it."""

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle_with_running(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    assert set(payload["recovery"].keys()) == {
        "today", "history", "missingness", "cold_start", "history_days",
        "evidence", "raw_summary", "classified_state", "policy_result",
    }


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

def test_snapshot_evidence_json_missing_file_fails_clean(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(tmp_path / "does_not_exist.json"),
    ])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "not found" in err


def test_snapshot_evidence_json_missing_required_keys_fails_clean(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"foo": "bar"}), encoding="utf-8")
    rc = cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bad),
    ])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "cleaned_evidence" in err or "raw_summary" in err


# ---------------------------------------------------------------------------
# Sleep + stress block — additive expansion under --evidence-json
# (Phase 3 step 5)
# ---------------------------------------------------------------------------

def test_snapshot_sleep_block_v1_0_keys_without_evidence_json(
    tmp_path: Path, capsys,
):
    """Additive expansion guarantee: today/history/missingness still
    present when no evidence bundle is supplied."""

    db = _init_db(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
    ])
    payload = json.loads(capsys.readouterr().out)
    assert set(payload["sleep"].keys()) == {"today", "history", "missingness", "cold_start", "history_days"}


def test_snapshot_stress_block_v1_0_keys_without_evidence_json(
    tmp_path: Path, capsys,
):
    """Stress block v1.0 carries convenience keys today_garmin /
    today_manual / today_body_battery in addition to the standard
    three, regardless of evidence_bundle presence."""

    db = _init_db(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
    ])
    payload = json.loads(capsys.readouterr().out)
    assert set(payload["stress"].keys()) == {
        "today", "history", "missingness", "cold_start", "history_days",
        "today_garmin", "today_manual", "today_body_battery",
    }


def test_snapshot_sleep_block_adds_signals_classified_policy_with_evidence_json(
    tmp_path: Path, capsys,
):
    """Phase 3 step 5: sleep block gains signals / classified_state /
    policy_result under --evidence-json, matching running's shape."""

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    assert set(payload["sleep"].keys()) == {
        "today", "history", "missingness", "cold_start", "history_days",
        "signals", "classified_state", "policy_result",
    }


def test_snapshot_stress_block_adds_signals_classified_policy_with_evidence_json(
    tmp_path: Path, capsys,
):
    """Phase 3 step 5: stress block gains signals / classified_state /
    policy_result under --evidence-json. Convenience keys stay put."""

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    assert set(payload["stress"].keys()) == {
        "today", "history", "missingness", "cold_start", "history_days",
        "today_garmin", "today_manual", "today_body_battery",
        "signals", "classified_state", "policy_result",
    }


def test_snapshot_sleep_signals_carry_expected_keys(tmp_path: Path, capsys):
    """signals dict contract matches classify_sleep_state input shape so
    a rename there surfaces here as a contract violation rather than at
    skill-prompt time."""

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    signals = payload["sleep"]["signals"]
    assert set(signals.keys()) == {
        "sleep_hours",
        "sleep_score_overall",
        "sleep_awake_min",
        "sleep_start_variance_minutes",
        "sleep_history_hours_last_7",
    }


def test_snapshot_sleep_signals_fall_back_to_evidence_sleep_hours(
    tmp_path: Path, capsys,
):
    """No accepted-sleep row yet (empty DB) → sleep_hours pulled from
    the evidence bundle so the classifier stays lit."""

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(tmp_path, sleep_hours=6.5)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    assert payload["sleep"]["signals"]["sleep_hours"] == 6.5
    # 6.5h is below the "mild" cutoff of 7h → moderate debt band.
    assert payload["sleep"]["classified_state"]["sleep_debt_band"] == "moderate"


def test_snapshot_stress_signals_carry_expected_keys(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    signals = payload["stress"]["signals"]
    assert set(signals.keys()) == {
        "garmin_all_day_stress",
        "manual_stress_score",
        "body_battery_end_of_day",
        "body_battery_prev_day",
        "stress_history_garmin_last_7",
    }


def test_snapshot_sleep_classified_state_has_all_sleep_band_keys(
    tmp_path: Path, capsys,
):
    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    classified = payload["sleep"]["classified_state"]
    assert set(classified.keys()) == {
        "sleep_debt_band",
        "sleep_quality_band",
        "sleep_timing_consistency_band",
        "sleep_efficiency_band",
        "coverage_band",
        "sleep_status",
        "sleep_score",
        "sleep_efficiency_pct",
        "uncertainty",
    }


def test_snapshot_stress_classified_state_has_all_stress_band_keys(
    tmp_path: Path, capsys,
):
    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    classified = payload["stress"]["classified_state"]
    assert set(classified.keys()) == {
        "garmin_stress_band",
        "manual_stress_band",
        "body_battery_trend_band",
        "coverage_band",
        "stress_state",
        "stress_score",
        "body_battery_delta",
        "uncertainty",
    }


def test_snapshot_sleep_and_stress_policy_result_four_keys(
    tmp_path: Path, capsys,
):
    """Every policy_result block carries the four canonical fields —
    policy_decisions / forced_action / forced_action_detail /
    capped_confidence. Shape is shared with recovery / running."""

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    for block in ("sleep", "stress"):
        policy = payload[block]["policy_result"]
        assert set(policy.keys()) == {
            "policy_decisions",
            "forced_action",
            "forced_action_detail",
            "capped_confidence",
        }


def test_snapshot_sleep_stress_expansion_does_not_modify_recovery_keys(
    tmp_path: Path, capsys,
):
    """Adding sleep + stress expansion must leave recovery's full-bundle
    key set exactly as Phase 1 froze it."""

    db = _init_db(tmp_path)
    bundle_path = _write_clean_bundle(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
        "--evidence-json", str(bundle_path),
    ])
    payload = json.loads(capsys.readouterr().out)
    assert set(payload["recovery"].keys()) == {
        "today", "history", "missingness", "cold_start", "history_days",
        "evidence", "raw_summary", "classified_state", "policy_result",
    }
