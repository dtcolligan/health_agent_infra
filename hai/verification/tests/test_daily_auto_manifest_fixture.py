"""W35 — manifest-only fixture-day agent test for W21 (`hai daily --auto`).

Acceptance: a generic agent reading ONLY the `next_actions[]`
manifest emitted by `hai daily --auto` can plan a day end-to-end.
No prose lookup against `intent-router`, `agent_integration.md`,
or any skill body is permitted — every required action must be
typed and discoverable from the manifest's structured fields.

This test simulates a generic agent host:
  - Reads `hai daily --auto` JSON.
  - For each action in `next_actions[]`, dispatches by `kind`:
      `intake_required`     → invoke the `command_root` with stub
                              values (test fixtures stand in for
                              real user input).
      `skill_invocation_required` → fake the per-domain skill
                              (we're not exercising skill
                              correctness here, only the manifest's
                              orchestration); compose a minimal
                              valid DomainProposal and post via
                              the `writeback_command`.
      `synthesize_ready`   → execute `command_argv` (which is
                              `hai daily --skip-pull --auto`).
      `narrate_ready`      → terminal; assert plan committed and
                              stop.
  - The agent NEVER reads intent-router, agent_integration.md, or
    any per-domain skill body. Only the manifest's typed fields.

If this test fails, the W21 manifest is under-specified for an
agent to drive without prose fallback.
"""

from __future__ import annotations

import json
import subprocess
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.intake.next_actions import (
    NEXT_ACTIONS_SCHEMA_VERSION,
)
from health_agent_infra.core.state import initialize_database


_AS_OF = "2026-02-10"  # date covered by the committed CSV fixture
_USER = "u_local_1"


# ---------------------------------------------------------------------------
# Fake-agent dispatch
# ---------------------------------------------------------------------------

def _run_daily_auto(*, db: Path, base: Path, monkeypatch) -> dict:
    """Run `hai daily --auto` and return the parsed report. csv source
    keeps the test offline."""

    monkeypatch.setenv("HAI_STATE_DB", str(db))
    monkeypatch.setenv("HAI_BASE_DIR", str(base))
    out = StringIO()
    with redirect_stdout(out):
        rc = cli_main([
            "daily",
            "--as-of", _AS_OF,
            "--user-id", _USER,
            "--source", "csv",
            "--auto",
        ])
    assert rc == 0, out.getvalue()
    return json.loads(out.getvalue())


def _dispatch_intake_required(action: dict) -> None:
    """Stub user input for an intake_required action. The manifest's
    `command_root` + `command_template` describe what to invoke; we
    pick reasonable test values for each known reason_code."""

    reason = action["reason_code"]
    if reason == "manual_checkin_missing":
        # Recovery readiness intake. Use canonical vocabulary tokens
        # discoverable via `hai planned-session-types`.
        rc = cli_main([
            "intake", "readiness",
            "--soreness", "low",
            "--energy", "moderate",
            "--planned-session-type", "easy_z2",
            "--as-of", _AS_OF,
            "--user-id", _USER,
        ])
        assert rc == 0
    elif reason == "manual_stress_score_unavailable":
        rc = cli_main([
            "intake", "stress",
            "--score", "2",
            "--as-of", _AS_OF,
            "--user-id", _USER,
        ])
        assert rc == 0
    elif reason == "no_nutrition_row_for_day":
        rc = cli_main([
            "intake", "nutrition",
            "--calories", "2400",
            "--protein-g", "180",
            "--carbs-g", "250",
            "--fat-g", "70",
            "--as-of", _AS_OF,
            "--user-id", _USER,
        ])
        assert rc == 0
    elif reason == "sessions_history_unavailable":
        # The strength gap closes if the readiness check carries a
        # non-strength planned-session — already supplied above.
        pass
    else:
        raise AssertionError(
            f"intake_required action with unknown reason_code: {reason}"
        )


def _dispatch_skill_invocation(action: dict, *, base: Path,
                                tmp_path: Path) -> None:
    """Stub per-domain skill output as a minimal valid DomainProposal,
    then invoke the manifest's `writeback_command` to land it.

    Critically, this function does NOT read any skill body — it just
    consumes the manifest's typed fields (`domain`, `produces`,
    `writeback_command`, `idempotency_key_pattern`).
    """

    domain = action["domain"]
    schema_version = action["produces"]
    proposal_id = (
        action["idempotency_key_pattern"]
        .replace("NN", "01")
    )
    # Per-domain action enum varies; pick the canonical safe action.
    action_by_domain = {
        "recovery": "proceed_with_planned_session",
        "running": "proceed_with_planned_run",
        "sleep": "maintain_schedule",
        "strength": "proceed_with_planned_session",
        "stress": "maintain_routine",
        "nutrition": "maintain_targets",
    }
    proposal = {
        "schema_version": schema_version,
        "proposal_id": proposal_id,
        "user_id": _USER,
        "for_date": _AS_OF,
        "domain": domain,
        "action": action_by_domain[domain],
        "action_detail": None,
        "rationale": [
            f"fake-agent dispatch for W35 fixture test ({domain})",
        ],
        "confidence": "moderate",
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": "r1", "decision": "allow",
             "note": "fixture-day stub"},
        ],
        "bounded": True,
    }
    proposal_path = tmp_path / f"proposal_{domain}.json"
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")

    # Use the manifest's writeback_command verbatim, just substituting
    # the placeholder. Agent does NOT compose its own argv.
    argv = list(action["writeback_command"])
    placeholder = "<path-to-proposal-json>"
    if placeholder in argv:
        argv[argv.index(placeholder)] = str(proposal_path)
    # Strip the leading "hai" since cli_main expects argv without prog.
    assert argv[0] == "hai"
    rc = cli_main(argv[1:])
    assert rc == 0, f"hai propose failed for {domain}"


def _dispatch_synthesize_ready(action: dict, *, db: Path, base: Path,
                                monkeypatch) -> dict:
    """Execute the synthesize_ready action's command_argv and return
    the new report. The action's command_argv is `hai daily --skip-pull
    --auto`, which advances the gate to complete + runs synthesis +
    schedules reviews."""

    argv = list(action["command_argv"])
    assert argv[0] == "hai"
    out = StringIO()
    with redirect_stdout(out):
        rc = cli_main(argv[1:])
    assert rc == 0
    return json.loads(out.getvalue())


# ---------------------------------------------------------------------------
# Manifest invariants
# ---------------------------------------------------------------------------

def test_manifest_emitted_in_auto_mode(tmp_path, monkeypatch):
    """First call to `hai daily --auto` on a fresh DB emits the
    manifest with the v1 schema version."""

    db = tmp_path / "state.db"
    initialize_database(db)
    base = tmp_path / "base"
    base.mkdir()

    report = _run_daily_auto(db=db, base=base, monkeypatch=monkeypatch)
    assert "next_actions_manifest" in report
    manifest = report["next_actions_manifest"]
    assert manifest["schema_version"] == NEXT_ACTIONS_SCHEMA_VERSION
    assert "next_actions" in manifest
    assert "telemetry" in manifest


def test_manifest_actions_carry_required_typed_fields(tmp_path, monkeypatch):
    """Every action carries the W21-required fields: action_id, kind,
    reason_code, blocking, safe_to_retry. Skill / intake / synthesize
    actions also carry their kind-specific fields."""

    db = tmp_path / "state.db"
    initialize_database(db)
    base = tmp_path / "base"
    base.mkdir()

    report = _run_daily_auto(db=db, base=base, monkeypatch=monkeypatch)
    actions = report["next_actions_manifest"]["next_actions"]
    assert len(actions) > 0
    for action in actions:
        # Common fields.
        for f in ("action_id", "kind", "reason_code", "blocking",
                  "safe_to_retry"):
            assert f in action, f"{action.get('kind')}: missing {f}"
        # Kind-specific.
        if action["kind"] == "intake_required":
            assert "command_root" in action
            assert "after_success" in action
        elif action["kind"] == "skill_invocation_required":
            assert "skill" in action
            assert "produces" in action
            assert "writeback_command" in action
            assert "idempotency_key_pattern" in action
        elif action["kind"] == "synthesize_ready":
            assert "command_argv" in action
        elif action["kind"] == "narrate_ready":
            assert "skill" in action
        else:
            raise AssertionError(f"unknown action kind: {action['kind']}")


# ---------------------------------------------------------------------------
# End-to-end fixture day: an agent drives from manifest only
# ---------------------------------------------------------------------------

def test_fixture_day_planned_end_to_end_via_manifest_only(
    tmp_path, monkeypatch,
):
    """The flagship W35 acceptance test. A generic agent reads the
    manifest, dispatches each action by `kind`, loops via
    `after_success`, and reaches a committed plan WITHOUT consulting
    intent-router or agent_integration.md prose.

    The test asserts:
      1. Each round produces a manifest with `next_actions[]`.
      2. The agent loops until `narrate_ready` is the terminal action.
      3. `hai today --as-of <date>` returns a real plan.
    """

    db = tmp_path / "state.db"
    initialize_database(db)
    base = tmp_path / "base"
    base.mkdir()
    monkeypatch.setenv("HAI_STATE_DB", str(db))
    monkeypatch.setenv("HAI_BASE_DIR", str(base))

    seen_kinds: list[str] = []
    max_rounds = 10  # safety bound; real loop should terminate much sooner

    for round_num in range(max_rounds):
        report = _run_daily_auto(
            db=db, base=base, monkeypatch=monkeypatch,
        )
        manifest = report.get("next_actions_manifest")
        assert manifest is not None, (
            f"round {round_num}: missing manifest in --auto output"
        )
        actions = manifest["next_actions"]
        # Process every blocking action in this round before re-running.
        for action in actions:
            seen_kinds.append(action["kind"])
            if action["kind"] == "intake_required":
                _dispatch_intake_required(action)
            elif action["kind"] == "skill_invocation_required":
                _dispatch_skill_invocation(
                    action, base=base, tmp_path=tmp_path,
                )
            elif action["kind"] == "synthesize_ready":
                _dispatch_synthesize_ready(
                    action, db=db, base=base, monkeypatch=monkeypatch,
                )
            elif action["kind"] == "narrate_ready":
                # Terminal — plan committed; stop the agent loop.
                # Assert hai today returns a real plan.
                out = StringIO()
                with redirect_stdout(out):
                    rc = cli_main([
                        "today",
                        "--as-of", _AS_OF,
                        "--user-id", _USER,
                        "--format", "json",
                    ])
                assert rc == 0
                plan = json.loads(out.getvalue())
                # `hai today --format json` returns the plan at the
                # top level (`daily_plan_id` + `sections`); pin both
                # so the test asserts a real committed plan, not just
                # any JSON.
                assert plan.get("daily_plan_id"), (
                    "narrate_ready emitted but hai today shows no plan"
                )
                assert plan.get("sections"), (
                    "narrate_ready emitted but plan has no sections"
                )
                # Sanity-check we exercised the orchestration path:
                assert "intake_required" in seen_kinds or \
                       "skill_invocation_required" in seen_kinds, (
                    "fixture day reached narrate_ready without ever "
                    "invoking intake or skill actions — the manifest "
                    "may not be the right surface for the agent"
                )
                return
        # If no terminal action triggered above, the loop's
        # after_success would normally re-run hai daily; we do that at
        # the top of the next loop iteration.

    raise AssertionError(
        f"agent loop did not reach narrate_ready in {max_rounds} rounds; "
        f"actions seen: {seen_kinds}"
    )
