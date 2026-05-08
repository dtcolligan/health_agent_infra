"""W39 — `hai config validate` + `hai config diff`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main


def _write_config(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_config_validate_no_file_returns_ok(tmp_path: Path, capsys):
    cfg = tmp_path / "thresholds.toml"  # does not exist
    rc = cli_main(["config", "validate", "--path", str(cfg)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["source_exists"] is False


def test_config_validate_clean_file_returns_ok(tmp_path: Path, capsys):
    cfg = _write_config(
        tmp_path / "thresholds.toml",
        "[policy.review_summary]\nwindow_days = 14\n",
    )
    rc = cli_main(["config", "validate", "--path", str(cfg)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"


def test_config_validate_malformed_toml_returns_user_input(tmp_path: Path, capsys):
    cfg = _write_config(
        tmp_path / "thresholds.toml",
        "[unterminated section\n",
    )
    rc = cli_main(["config", "validate", "--path", str(cfg)])
    assert rc != 0
    err = capsys.readouterr().err
    assert "malformed" in err.lower()


def test_config_validate_type_mismatch_blocks(tmp_path: Path, capsys):
    cfg = _write_config(
        tmp_path / "thresholds.toml",
        '[policy.review_summary]\nwindow_days = "seven"\n',
    )
    rc = cli_main(["config", "validate", "--path", str(cfg)])
    assert rc != 0
    payload = json.loads(capsys.readouterr().out)
    assert any(i["kind"] == "type_mismatch" for i in payload["issues"])


def test_config_validate_unknown_key_warning_by_default(tmp_path: Path, capsys):
    cfg = _write_config(
        tmp_path / "thresholds.toml",
        "[policy.review_summary]\nbogus_key = 5\n",
    )
    rc = cli_main(["config", "validate", "--path", str(cfg)])
    # Default mode: unknown_key issues are surfaced but not blocking.
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert any(
        i["path"] == "policy.review_summary.bogus_key" and i["kind"] == "unknown_key"
        for i in payload["issues"]
    )


def test_config_validate_strict_unknown_key_blocks(tmp_path: Path, capsys):
    cfg = _write_config(
        tmp_path / "thresholds.toml",
        "[policy.review_summary]\nbogus_key = 5\n",
    )
    rc = cli_main(["config", "validate", "--path", str(cfg), "--strict"])
    assert rc != 0


# ---------------------------------------------------------------------------
# Codex P2-3: numeric range checks for [policy.review_summary]
# ---------------------------------------------------------------------------


def test_config_validate_window_days_negative_blocks(tmp_path: Path, capsys):
    cfg = _write_config(
        tmp_path / "thresholds.toml",
        "[policy.review_summary]\nwindow_days = -7\n",
    )
    rc = cli_main(["config", "validate", "--path", str(cfg)])
    assert rc != 0
    payload = json.loads(capsys.readouterr().out)
    assert any(
        i["path"] == "policy.review_summary.window_days"
        and i["kind"] == "range_violation"
        for i in payload["issues"]
    )


def test_config_validate_mixed_lower_above_upper_blocks(tmp_path: Path, capsys):
    cfg = _write_config(
        tmp_path / "thresholds.toml",
        "[policy.review_summary]\n"
        "mixed_token_lower_bound = 0.7\n"
        "mixed_token_upper_bound = 0.3\n",
    )
    rc = cli_main(["config", "validate", "--path", str(cfg)])
    assert rc != 0
    payload = json.loads(capsys.readouterr().out)
    assert any(
        i["kind"] == "range_violation" for i in payload["issues"]
    )


def test_config_validate_mixed_bound_outside_unit_interval_blocks(
    tmp_path: Path, capsys,
):
    cfg = _write_config(
        tmp_path / "thresholds.toml",
        "[policy.review_summary]\nmixed_token_upper_bound = 1.5\n",
    )
    rc = cli_main(["config", "validate", "--path", str(cfg)])
    assert rc != 0
    payload = json.loads(capsys.readouterr().out)
    assert any(
        i["path"] == "policy.review_summary.mixed_token_upper_bound"
        and i["kind"] == "range_violation"
        for i in payload["issues"]
    )


def test_config_validate_rejects_bool_for_numeric_window_days(
    tmp_path: Path, capsys,
):
    """Codex R2-3: `bool` is a subclass of `int` in Python; without an
    explicit guard, `window_days = true` would silently coerce to 1
    and bypass both type_mismatch and range_violation checks."""

    cfg = _write_config(
        tmp_path / "thresholds.toml",
        "[policy.review_summary]\nwindow_days = true\n",
    )
    rc = cli_main(["config", "validate", "--path", str(cfg)])
    assert rc != 0
    payload = json.loads(capsys.readouterr().out)
    assert any(
        i["path"] == "policy.review_summary.window_days"
        and i["kind"] == "type_mismatch"
        for i in payload["issues"]
    )


def test_config_validate_rejects_bool_for_numeric_threshold(
    tmp_path: Path, capsys,
):
    cfg = _write_config(
        tmp_path / "thresholds.toml",
        "[policy.review_summary]\nrecent_negative_threshold = false\n",
    )
    rc = cli_main(["config", "validate", "--path", str(cfg)])
    assert rc != 0
    payload = json.loads(capsys.readouterr().out)
    assert any(
        i["path"] == "policy.review_summary.recent_negative_threshold"
        and i["kind"] == "type_mismatch"
        for i in payload["issues"]
    )


def test_config_validate_rejects_bool_for_mixed_bound(tmp_path: Path, capsys):
    cfg = _write_config(
        tmp_path / "thresholds.toml",
        "[policy.review_summary]\nmixed_token_upper_bound = true\n",
    )
    rc = cli_main(["config", "validate", "--path", str(cfg)])
    assert rc != 0
    payload = json.loads(capsys.readouterr().out)
    assert any(
        i["path"] == "policy.review_summary.mixed_token_upper_bound"
        and i["kind"] == "type_mismatch"
        for i in payload["issues"]
    )


def test_config_validate_negative_threshold_blocks(tmp_path: Path, capsys):
    cfg = _write_config(
        tmp_path / "thresholds.toml",
        "[policy.review_summary]\nrecent_negative_threshold = -1\n",
    )
    rc = cli_main(["config", "validate", "--path", str(cfg)])
    assert rc != 0


def test_config_diff_lists_overridden_keys_and_unknown(tmp_path: Path, capsys):
    cfg = _write_config(
        tmp_path / "thresholds.toml",
        "[policy.review_summary]\nwindow_days = 14\nbogus_key = 5\n",
    )
    rc = cli_main(["config", "diff", "--path", str(cfg)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    diffs_by_path = {d["path"]: d for d in payload["diffs"]}
    assert diffs_by_path["policy.review_summary.window_days"]["override"] == 14
    assert diffs_by_path["policy.review_summary.window_days"]["effective"] == 14
    assert diffs_by_path["policy.review_summary.window_days"]["default"] == 7
    assert diffs_by_path["policy.review_summary.bogus_key"]["key_known"] is False
