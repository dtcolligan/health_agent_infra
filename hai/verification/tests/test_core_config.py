"""Tests for Phase 1 step 2 — config-driven thresholds.

Scope:
  - DEFAULT_THRESHOLDS has the expected namespaced shape.
  - `load_thresholds(path=None)` returns defaults when no user file exists.
  - `load_thresholds(path=...)` deep-merges user TOML over defaults.
  - Malformed TOML raises ConfigError with a useful message.
  - `hai config init` writes the scaffold, refuses to overwrite without
    --force, overwrites with --force.
  - `hai config show` prints the merged effective config as JSON.

Out of scope: the platformdirs-resolved path (integration-y and platform
dependent). Tests that touch the user_config_path default are skipped in
favour of explicit --path arguments.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.config import (
    DEFAULT_THRESHOLDS,
    ConfigError,
    load_thresholds,
    scaffold_thresholds_toml,
    user_config_path,
)


# ---------------------------------------------------------------------------
# DEFAULT_THRESHOLDS shape
# ---------------------------------------------------------------------------

def test_default_thresholds_has_expected_top_level_sections():
    # M6 added "pull" (garmin_live retry knobs); prior PRs cemented
    # classify / policy / synthesis. v0.1.11 W-W added "gap_detection".
    # This set grows when a new config surface lands — the test should
    # be updated alongside the section.
    assert set(DEFAULT_THRESHOLDS.keys()) == {
        "classify", "policy", "synthesis", "pull", "gap_detection",
    }


def test_default_thresholds_recovery_bands_present():
    recovery = DEFAULT_THRESHOLDS["classify"]["recovery"]
    assert set(recovery.keys()) >= {
        "sleep_debt_band",
        "resting_hr_band",
        "hrv_band",
        "training_load_band",
        "readiness_score_penalty",
    }


def test_default_thresholds_sleep_band_matches_skill_doc():
    bands = DEFAULT_THRESHOLDS["classify"]["recovery"]["sleep_debt_band"]
    assert bands["none_min_hours"] == 7.5
    assert bands["mild_min_hours"] == 7.0
    assert bands["moderate_min_hours"] == 6.0


def test_default_thresholds_x_rules_include_prototype_rules():
    xr = DEFAULT_THRESHOLDS["synthesis"]["x_rules"]
    assert "x1a" in xr
    assert "x3b" in xr
    assert "x6a" in xr
    assert xr["x3b"]["acwr_ratio_min"] == 1.5
    assert xr["x6a"]["body_battery_max"] == 30


# ---------------------------------------------------------------------------
# load_thresholds
# ---------------------------------------------------------------------------

def test_load_thresholds_returns_defaults_when_no_file(tmp_path: Path):
    missing = tmp_path / "nonexistent.toml"
    result = load_thresholds(path=missing)
    assert result == DEFAULT_THRESHOLDS
    assert result is not DEFAULT_THRESHOLDS  # should be a deep copy


def test_load_thresholds_returns_independent_copy(tmp_path: Path):
    missing = tmp_path / "nonexistent.toml"
    result = load_thresholds(path=missing)
    result["classify"]["recovery"]["sleep_debt_band"]["none_min_hours"] = 99.0
    # Default must not have been mutated.
    assert (
        DEFAULT_THRESHOLDS["classify"]["recovery"]["sleep_debt_band"]["none_min_hours"]
        == 7.5
    )


def test_load_thresholds_deep_merges_user_overrides(tmp_path: Path):
    user_toml = tmp_path / "thresholds.toml"
    user_toml.write_text(
        "[classify.recovery.sleep_debt_band]\n"
        "none_min_hours = 8.0\n"
        "# mild and moderate omitted; should fall through to defaults\n",
        encoding="utf-8",
    )
    merged = load_thresholds(path=user_toml)
    sd = merged["classify"]["recovery"]["sleep_debt_band"]
    assert sd["none_min_hours"] == 8.0   # overridden
    assert sd["mild_min_hours"] == 7.0    # inherited
    assert sd["moderate_min_hours"] == 6.0  # inherited


def test_load_thresholds_preserves_unrelated_sections(tmp_path: Path):
    """A partial override does not wipe out unrelated branches."""

    user_toml = tmp_path / "thresholds.toml"
    user_toml.write_text(
        "[synthesis.x_rules.x3b]\n"
        "acwr_ratio_min = 1.6\n",
        encoding="utf-8",
    )
    merged = load_thresholds(path=user_toml)

    # Overridden branch: new value.
    assert merged["synthesis"]["x_rules"]["x3b"]["acwr_ratio_min"] == 1.6
    # Untouched branches: defaults.
    assert "classify" in merged
    assert merged["classify"]["recovery"]["sleep_debt_band"]["none_min_hours"] == 7.5
    assert merged["synthesis"]["x_rules"]["x1a"]["sleep_debt_trigger_band"] == "moderate"


def test_load_thresholds_user_list_replaces_default_list(tmp_path: Path):
    """Lists are treated as leaves — a user-provided list replaces wholesale."""

    user_toml = tmp_path / "thresholds.toml"
    user_toml.write_text(
        "[synthesis.x_rules.x7]\n"
        "stress_trigger_bands = [\"very_high\"]\n",  # single-item override
        encoding="utf-8",
    )
    merged = load_thresholds(path=user_toml)
    assert merged["synthesis"]["x_rules"]["x7"]["stress_trigger_bands"] == ["very_high"]


def test_load_thresholds_raises_on_malformed_toml(tmp_path: Path):
    bad = tmp_path / "bad.toml"
    bad.write_text("this is [ not valid TOML = = =", encoding="utf-8")
    with pytest.raises(ConfigError) as exc_info:
        load_thresholds(path=bad)
    assert str(bad) in str(exc_info.value)


# ---------------------------------------------------------------------------
# scaffold template
# ---------------------------------------------------------------------------

def test_scaffold_thresholds_toml_is_parseable_and_yields_defaults(tmp_path: Path):
    """Scaffold file must load cleanly and produce exactly the defaults.

    That way `hai config init` produces a file that's effective-equivalent
    to having no file at all, so users can delete sections they don't
    want to override.
    """

    out = tmp_path / "scaffold.toml"
    out.write_text(scaffold_thresholds_toml(), encoding="utf-8")
    merged = load_thresholds(path=out)
    assert merged == DEFAULT_THRESHOLDS


def test_scaffold_thresholds_toml_includes_running_sections():
    """Phase 2 step 3: `hai config init` must scaffold the new running
    sections so users can override them without hand-authoring TOML."""

    text = scaffold_thresholds_toml()
    required_sections = [
        "[classify.running.weekly_mileage_trend_band]",
        "[classify.running.hard_session_load_band]",
        "[classify.running.freshness_band]",
        "[classify.running.recovery_adjacent_band]",
        "[classify.running.readiness_score_penalty]",
        "[policy.running]",
    ]
    missing = [s for s in required_sections if s not in text]
    assert not missing, f"scaffold TOML missing running sections: {missing}"


# ---------------------------------------------------------------------------
# user_config_path
# ---------------------------------------------------------------------------

def test_user_config_path_returns_platformdirs_path():
    path = user_config_path()
    assert path.name == "thresholds.toml"
    assert "hai" in path.parts


# ---------------------------------------------------------------------------
# CLI — hai config init
# ---------------------------------------------------------------------------

def test_cli_config_init_writes_scaffold(tmp_path: Path, capsys):
    dest = tmp_path / "thresholds.toml"
    rc = cli_main(["config", "init", "--path", str(dest)])
    assert rc == 0
    assert dest.exists()
    payload = json.loads(capsys.readouterr().out)
    assert payload["written"] == str(dest)
    assert "overwrote" in payload

    merged = load_thresholds(path=dest)
    assert merged == DEFAULT_THRESHOLDS


def test_cli_config_init_refuses_existing_without_force(tmp_path: Path, capsys):
    dest = tmp_path / "thresholds.toml"
    dest.write_text("# existing\n", encoding="utf-8")
    rc = cli_main(["config", "init", "--path", str(dest)])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "already exists" in err
    # File unchanged.
    assert dest.read_text() == "# existing\n"


def test_cli_config_init_force_overwrites(tmp_path: Path, capsys):
    dest = tmp_path / "thresholds.toml"
    dest.write_text("# existing\n", encoding="utf-8")
    rc = cli_main(["config", "init", "--path", str(dest), "--force"])
    assert rc == 0
    # File has been replaced with the scaffold content.
    assert "# Health Agent Infra" in dest.read_text()


# ---------------------------------------------------------------------------
# CLI — hai config show
# ---------------------------------------------------------------------------

def test_cli_config_show_with_no_user_file(tmp_path: Path, capsys):
    missing = tmp_path / "nonexistent.toml"
    rc = cli_main(["config", "show", "--path", str(missing)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["source_exists"] is False
    assert payload["source_path"] == str(missing)
    assert payload["effective_thresholds"] == DEFAULT_THRESHOLDS


def test_cli_config_show_with_user_override(tmp_path: Path, capsys):
    user_toml = tmp_path / "thresholds.toml"
    user_toml.write_text(
        "[synthesis.x_rules.x6a]\n"
        "body_battery_max = 25\n",
        encoding="utf-8",
    )
    rc = cli_main(["config", "show", "--path", str(user_toml)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["source_exists"] is True
    assert (
        payload["effective_thresholds"]["synthesis"]["x_rules"]["x6a"]["body_battery_max"]
        == 25
    )


def test_cli_config_show_fails_cleanly_on_malformed_toml(tmp_path: Path, capsys):
    bad = tmp_path / "bad.toml"
    bad.write_text("lol = = not toml", encoding="utf-8")
    rc = cli_main(["config", "show", "--path", str(bad)])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "config error" in err
    assert str(bad) in err
