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
from health_agent_infra.state import initialize_database


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
    assert set(payload["recovery"].keys()) == {"today", "history", "missingness"}


def test_snapshot_v1_0_running_block_unchanged(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    cli_main([
        "state", "snapshot",
        "--as-of", "2026-04-17", "--user-id", "u_local_1",
        "--db-path", str(db),
    ])
    payload = json.loads(capsys.readouterr().out)
    assert set(payload["running"].keys()) == {"today", "history", "missingness"}


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
    ("running", {"today", "history", "missingness"}),
    ("gym", {"today", "history", "missingness"}),
    ("nutrition", {"today", "history", "missingness"}),
])
def test_snapshot_other_domains_unchanged_with_evidence_json(
    tmp_path: Path, capsys, domain: str, expected_keys: set[str]
):
    """Other domains keep v1.0 shape until their own classify/policy lands.
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
    assert rc == 2
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
    assert rc == 2
    err = capsys.readouterr().err
    assert "cleaned_evidence" in err or "raw_summary" in err
