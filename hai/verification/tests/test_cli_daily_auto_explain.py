"""W43 — `hai daily --auto --explain` thick JSON.

Pins:

  1. Plain `hai daily` does NOT include an ``explain`` key.
  2. `hai daily --auto` (no --explain) does NOT include an ``explain`` key.
  3. `hai daily --auto --explain` DOES include an ``explain`` key with
     per-stage blocks + ``schema_version='daily_explain.v1'``.
  4. The explain block reads already-computed fields — no recomputation
     in the CLI helper.
"""

from __future__ import annotations

import json
from pathlib import Path

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.state import initialize_database


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def test_plain_daily_does_not_emit_explain(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    cli_main([
        "daily",
        "--db-path", str(db),
        "--as-of", "2026-04-22",
        "--source", "csv",
        "--skip-pull",
    ])
    payload = json.loads(capsys.readouterr().out)
    assert "explain" not in payload


def test_auto_without_explain_does_not_emit_explain(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    cli_main([
        "daily", "--auto",
        "--db-path", str(db),
        "--as-of", "2026-04-22",
        "--source", "csv",
        "--skip-pull",
    ])
    payload = json.loads(capsys.readouterr().out)
    assert "explain" not in payload


def test_auto_explain_attaches_per_stage_block(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    cli_main([
        "daily", "--auto", "--explain",
        "--db-path", str(db),
        "--as-of", "2026-04-22",
        "--source", "csv",
        "--skip-pull",
    ])
    payload = json.loads(capsys.readouterr().out)
    assert "explain" in payload
    explain = payload["explain"]
    assert explain["schema_version"] == "daily_explain.v1"
    assert "pull" in explain
    assert "clean" in explain
    assert "snapshot" in explain
    assert "gaps" in explain
    assert "proposal_gate" in explain
    assert "synthesize" in explain
    # overall_status is always populated.
    assert explain["overall_status"] is not None


def test_auto_explain_snapshot_block_carries_w48_signals(
    tmp_path: Path, capsys,
):
    """Codex P2-1: explain.snapshot must populate domains_present,
    missingness_per_domain, classified_bands_per_domain, and
    review_summary_tokens_per_domain — not just emit keys with None
    values."""

    db = _init_db(tmp_path)
    cli_main([
        "daily", "--auto", "--explain",
        "--db-path", str(db),
        "--as-of", "2026-04-22",
        "--source", "csv",
        "--skip-pull",
    ])
    payload = json.loads(capsys.readouterr().out)
    snap = payload["explain"]["snapshot"]

    # Codex P2-1: domains_present must not be None on a daily run that
    # built a snapshot.
    assert snap["domains_present"] is not None, (
        "explain.snapshot.domains_present is None — the populator and "
        "the explain-builder are not aligned (Codex P2-1)"
    )
    assert isinstance(snap["domains_present"], list)
    # Per-domain missingness must be a dict keyed by domain name.
    assert isinstance(snap["missingness_per_domain"], dict)
    # Per-domain bands + review_summary tokens must be dicts.
    assert isinstance(snap["classified_bands_per_domain"], dict)
    assert isinstance(snap["review_summary_tokens_per_domain"], dict)
    # On an empty DB, every domain's review_summary will report
    # `outcome_pattern_insufficient_denominator` — assert one example
    # to prove the signal is wired through.
    if "recovery" in snap["review_summary_tokens_per_domain"]:
        assert (
            "outcome_pattern_insufficient_denominator"
            in snap["review_summary_tokens_per_domain"]["recovery"]
        )
