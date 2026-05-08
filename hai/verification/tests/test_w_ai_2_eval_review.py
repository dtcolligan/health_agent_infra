"""W-AI-2 (v0.1.17 §2.D) — `hai eval review` CLI surface.

Acceptance per PLAN §2.D commit gate (items 1-7):
  1. `list --corpus all` returns whatever corpus exists at commit time.
  2. `tag --scenario-id <id> --tag <t>` writes triage state.
  3. `dismiss --scenario-id <id> --reason <text>` marks dismissed.
  4. `export --output <p>` emits JSON (default) / CSV.
  5. Capabilities manifest entry annotated correctly.
  6. Round-trip test (tag → list → dismiss → list → export).
  7. Snapshot regeneration lockstep — checked at the cycle ship gate.

Tests use HAI_EVAL_REVIEW_STATE env var to redirect the per-user state
file to a tmp path so the suite is hermetic.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.evals import review as eval_review


def _run(*argv: str) -> tuple[int, str, str]:
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    try:
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = cli_main(list(argv))
    except SystemExit as exc:
        rc = int(exc.code) if isinstance(exc.code, int) else 2
    return rc, out_buf.getvalue(), err_buf.getvalue()


@pytest.fixture
def isolated_review_state(tmp_path, monkeypatch):
    """Redirect the eval_review.json persistence path to tmp."""

    state_path = tmp_path / "eval_review.json"
    monkeypatch.setenv("HAI_EVAL_REVIEW_STATE", str(state_path))
    return state_path


# ---------------------------------------------------------------------------
# Acceptance test 1 — list returns at-commit corpus
# ---------------------------------------------------------------------------


def test_list_corpus_all_returns_live_corpus(isolated_review_state):
    """`hai eval review list --corpus all` walks the fixture tree."""

    rc, out, err = _run("eval", "review", "list", "--corpus", "all")
    assert rc == exit_codes.OK, f"list failed: rc={rc}, stderr={err[:200]}"
    payload = json.loads(out)
    assert payload["corpus"] == "all"
    assert payload["count"] >= 35, (
        f"expected ≥35 scenarios in 'all' corpus, got {payload['count']}"
    )
    # Every row carries the expected shape.
    for row in payload["rows"]:
        assert "scenario_id" in row
        assert "kind" in row
        assert "domain" in row
        assert row["triage_state"] is None or row["triage_state"] in (
            "tagged", "dismissed"
        )


def test_list_filters_by_corpus_subset(isolated_review_state):
    """--corpus 'scenarios' excludes judge_adversarial."""

    rc_s, out_s, _ = _run("eval", "review", "list", "--corpus", "scenarios")
    rc_a, out_a, _ = _run("eval", "review", "list", "--corpus", "all")
    assert rc_s == rc_a == exit_codes.OK
    s_count = json.loads(out_s)["count"]
    a_count = json.loads(out_a)["count"]
    assert s_count < a_count, (
        f"'scenarios' subset ({s_count}) should be smaller than 'all' "
        f"({a_count})"
    )


# ---------------------------------------------------------------------------
# Acceptance test 2 — tag writes state
# ---------------------------------------------------------------------------


def test_tag_writes_triage_state(isolated_review_state):
    """`tag --scenario-id <id> --tag <t>` writes to eval_review.json."""

    rc, out, err = _run(
        "eval", "review", "tag",
        "--scenario-id", "rec_001_rested_baseline",
        "--tag", "review-after-runtime-fix",
        "--note", "compound-signal review",
    )
    assert rc == exit_codes.OK, f"tag failed: rc={rc}, stderr={err[:200]}"
    entry = json.loads(out)
    assert entry["scenario_id"] == "rec_001_rested_baseline"
    assert entry["state"] == "tagged"
    assert entry["tag"] == "review-after-runtime-fix"
    assert entry["note"] == "compound-signal review"
    assert isolated_review_state.exists()


def test_tag_unknown_scenario_id_returns_user_input(isolated_review_state):
    """Tagging a scenario_id that doesn't exist → USER_INPUT exit."""

    rc, out, err = _run(
        "eval", "review", "tag",
        "--scenario-id", "no_such_scenario",
        "--tag", "spurious",
    )
    assert rc == exit_codes.USER_INPUT
    assert "unknown scenario_id" in err


# ---------------------------------------------------------------------------
# Acceptance test 3 — dismiss + filtering
# ---------------------------------------------------------------------------


def test_dismiss_marks_state_and_filters_from_default_list(isolated_review_state):
    """`dismiss` marks a scenario; default `list` hides it; --include-dismissed
    surfaces it again."""

    rc, _, err = _run(
        "eval", "review", "dismiss",
        "--scenario-id", "rec_003_sparse_coverage_caps_confidence",
        "--reason", "cleared after CDX review",
    )
    assert rc == exit_codes.OK, f"dismiss: rc={rc}, stderr={err[:200]}"

    # Default list hides it.
    rc, out, _ = _run("eval", "review", "list")
    assert rc == exit_codes.OK
    sids = {r["scenario_id"] for r in json.loads(out)["rows"]}
    assert "rec_003_sparse_coverage_caps_confidence" not in sids

    # --include-dismissed surfaces it.
    rc, out, _ = _run("eval", "review", "list", "--include-dismissed")
    assert rc == exit_codes.OK
    rows = json.loads(out)["rows"]
    target = next(
        r for r in rows if r["scenario_id"] == "rec_003_sparse_coverage_caps_confidence"
    )
    assert target["triage_state"] == "dismissed"
    assert target["triage_reason"] == "cleared after CDX review"


# ---------------------------------------------------------------------------
# Acceptance test 4 — export to JSON + CSV
# ---------------------------------------------------------------------------


def test_export_json(tmp_path, isolated_review_state):
    _run("eval", "review", "tag",
         "--scenario-id", "rec_001_rested_baseline",
         "--tag", "needs-review")
    out_path = tmp_path / "export.json"
    rc, out, err = _run(
        "eval", "review", "export",
        "--output", str(out_path), "--format", "json",
    )
    assert rc == exit_codes.OK
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "eval_review.v1"
    assert "rec_001_rested_baseline" in payload["entries"]


def test_export_csv(tmp_path, isolated_review_state):
    _run("eval", "review", "tag",
         "--scenario-id", "rec_001_rested_baseline",
         "--tag", "needs-review")
    out_path = tmp_path / "export.csv"
    rc, _, err = _run(
        "eval", "review", "export",
        "--output", str(out_path), "--format", "csv",
    )
    assert rc == exit_codes.OK, f"export csv: rc={rc}, stderr={err[:200]}"
    csv_text = out_path.read_text(encoding="utf-8")
    assert "scenario_id" in csv_text
    assert "rec_001_rested_baseline" in csv_text


# ---------------------------------------------------------------------------
# Acceptance test 5 — capabilities manifest annotations
# ---------------------------------------------------------------------------


def test_capabilities_manifest_registers_eval_review_subcommands():
    """Every `hai eval review` subcommand carries the expected
    contract annotation in the manifest."""

    rc, out, _ = _run("capabilities", "--json")
    assert rc == exit_codes.OK
    manifest = json.loads(out)
    review_cmds = {
        c["command"]: c
        for c in manifest["commands"]
        if c["command"].startswith("hai eval review ")
    }
    assert set(review_cmds) == {
        "hai eval review list",
        "hai eval review show",
        "hai eval review tag",
        "hai eval review dismiss",
        "hai eval review export",
    }
    # Mutating subcommands declare writes-state; read-only ones don't.
    assert review_cmds["hai eval review tag"]["mutation"] == "writes-state"
    assert review_cmds["hai eval review dismiss"]["mutation"] == "writes-state"
    assert review_cmds["hai eval review list"]["mutation"] == "read-only"
    assert review_cmds["hai eval review show"]["mutation"] == "read-only"
    assert review_cmds["hai eval review export"]["mutation"] == "read-only"


# ---------------------------------------------------------------------------
# Acceptance test 6 — round trip
# ---------------------------------------------------------------------------


def test_round_trip_tag_list_dismiss_list_export(tmp_path, isolated_review_state):
    """tag → list (sees tag) → dismiss → list (hides) → export round-trip."""

    sid = "rec_001_rested_baseline"

    _run("eval", "review", "tag",
         "--scenario-id", sid, "--tag", "stage-1-review")
    rc, out, _ = _run("eval", "review", "list", "--tag", "stage-1-review")
    assert rc == exit_codes.OK
    rows = json.loads(out)["rows"]
    assert any(r["scenario_id"] == sid for r in rows)

    _run("eval", "review", "dismiss",
         "--scenario-id", sid, "--reason", "no-longer-relevant")
    rc, out, _ = _run("eval", "review", "list", "--tag", "stage-1-review")
    rows = json.loads(out)["rows"]
    assert not any(r["scenario_id"] == sid for r in rows), (
        "dismissed entries with prior tag must be hidden by default"
    )

    out_path = tmp_path / "final.json"
    rc, _, _ = _run("eval", "review", "export",
                    "--output", str(out_path), "--format", "json")
    assert rc == exit_codes.OK
    final = json.loads(out_path.read_text(encoding="utf-8"))
    assert final["entries"][sid]["state"] == "dismissed"
    assert final["entries"][sid]["reason"] == "no-longer-relevant"


# ---------------------------------------------------------------------------
# show — fixture body + overlay
# ---------------------------------------------------------------------------


def test_show_returns_fixture_plus_triage_overlay(isolated_review_state):
    """`show --scenario-id <id>` emits {fixture, triage}. Triage is None
    until tagged/dismissed."""

    rc, out, _ = _run("eval", "review", "show",
                      "--scenario-id", "rec_001_rested_baseline")
    assert rc == exit_codes.OK
    bundle = json.loads(out)
    assert bundle["fixture"]["scenario_id"] == "rec_001_rested_baseline"
    assert bundle["triage"] is None

    _run("eval", "review", "tag",
         "--scenario-id", "rec_001_rested_baseline",
         "--tag", "post-show")
    rc, out, _ = _run("eval", "review", "show",
                      "--scenario-id", "rec_001_rested_baseline")
    bundle = json.loads(out)
    assert bundle["triage"]["tag"] == "post-show"


def test_show_unknown_scenario_returns_not_found(isolated_review_state):
    rc, out, err = _run("eval", "review", "show",
                        "--scenario-id", "no_such_scenario")
    assert rc == exit_codes.NOT_FOUND


# ---------------------------------------------------------------------------
# F-IR-02 — judge_adversarial round-trip via show/tag/dismiss
#
# Round-1 IR caught: `_walk_corpus` listed judge_adversarial fixtures by
# their `fixture_id` (or stem fallback), but `_find_in_corpus` only
# matched `scenario_id`. show/tag/dismiss were broken for that corpus.
# Contract is now: scenario_id ∨ fixture_id ∨ stem.
# ---------------------------------------------------------------------------


def test_show_resolves_judge_adversarial_fixture_id(isolated_review_state):
    rc, out, err = _run("eval", "review", "show",
                        "--scenario-id", "ja_bp_001")
    assert rc == exit_codes.OK, f"show ja_bp_001: rc={rc}, stderr={err[:200]}"
    bundle = json.loads(out)
    assert bundle["fixture"]["fixture_id"] == "ja_bp_001"
    assert bundle["fixture"].get("category") == "bias_probe"


def test_tag_then_dismiss_roundtrip_judge_adversarial(isolated_review_state):
    rc, _, err = _run(
        "eval", "review", "tag",
        "--scenario-id", "ja_bp_001",
        "--tag", "ja-review",
    )
    assert rc == exit_codes.OK, f"tag: rc={rc}, stderr={err[:200]}"

    rc, _, err = _run(
        "eval", "review", "dismiss",
        "--scenario-id", "ja_bp_001",
        "--reason", "judge-corpus stable",
    )
    assert rc == exit_codes.OK, f"dismiss: rc={rc}, stderr={err[:200]}"

    rc, out, _ = _run("eval", "review", "list",
                      "--corpus", "judge_adversarial",
                      "--include-dismissed")
    rows = json.loads(out)["rows"]
    target = next(
        r for r in rows if r["scenario_id"] == "ja_bp_001"
    )
    assert target["triage_state"] == "dismissed"
    assert target["triage_reason"] == "judge-corpus stable"
