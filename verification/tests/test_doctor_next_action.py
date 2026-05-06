"""W-OB-5 (v0.1.18 §2.E) — `hai doctor` actionability tests.

Acceptance per PLAN.md §2.E:

  1. ``next_action`` field added to every doctor check that emits ``hint``
     today, where the hint maps to a concrete command. Coverage at
     minimum: ``check_onboarding_readiness``, ``check_state_db``,
     ``check_auth_intervals_icu``, ``check_auth_garmin``, ``check_skills``.
     PASS results omit ``next_action``.
  2. ``next_action.command`` references the post-W-OB-2 default-flipped
     shape (``hai init``, NOT ``hai init --guided``).
  3. ``next_action.agent_safe`` matches the live capabilities-manifest
     entry for the cited command. (Manifest-consistency assertion.)
  4. ``next_action.interactive`` is True for any TTY-requiring command.
  5. ``_render_onboarding_readiness`` includes the ``next_action.purpose``
     line in human-readable rendering.
  6. Tests cover at least three checks: WARN-with-next-action,
     PASS-without-next-action, FAIL-with-next-action, manifest-consistency.

Cross-references:
- F-OB-4A-02 (umbrella-command preference for multi-missing case) is
  enforced by ``test_onboarding_readiness_multi_missing_uses_umbrella``.
- F-OB-4A-01 (cross-cycle field-naming convention with ``hai daily``) is
  documented but not test-enforced — convention alignment is judgment-only.
- F-PLAN-02 (post-W-OB-2 command shape) is enforced by
  ``test_next_action_command_post_w_ob_2_shape``.
- OQ-4 (runtime-only, no manifest delta) is enforced by absence of
  schema additions to ``hai capabilities --json`` (no test needed; the
  existing `test_capabilities_manifest_schema.py` would catch a regression).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.doctor.checks import (
    _NEXT_ACTION_REGISTRY,
    check_auth_garmin,
    check_auth_intervals_icu,
    check_onboarding_readiness,
    check_skills,
    check_state_db,
)
from health_agent_infra.core.doctor.render import (
    _render_next_action_lines,
    _render_onboarding_readiness,
)
from health_agent_infra.core.pull.auth import CredentialStore
from health_agent_infra.core.state import initialize_database


USER = "u_w_ob_5"


# ---------------------------------------------------------------------------
# Acceptance 6 — WARN-with-next-action across at least 3 checks
# ---------------------------------------------------------------------------


def test_state_db_warn_no_db_emits_next_action(tmp_path):
    db_path = tmp_path / "no_such.db"
    result = check_state_db(db_path)

    assert result["status"] == "warn"
    assert "next_action" in result
    assert result["next_action"]["command"] == "hai init"
    assert "purpose" in result["next_action"]
    assert "agent_safe" in result["next_action"]
    assert "interactive" in result["next_action"]


def test_onboarding_readiness_no_db_emits_next_action(tmp_path):
    db_path = tmp_path / "no_such.db"
    result = check_onboarding_readiness(
        db_path, user_id=USER, as_of_date=date.today(),
    )

    assert result["status"] == "warn"
    assert "next_action" in result
    assert result["next_action"]["command"] == "hai init"


class _FakeKeyring:
    def __init__(self) -> None:
        self._data: dict[tuple[str, str], str] = {}

    def get_password(self, service, username):
        return self._data.get((service, username))

    def set_password(self, service, username, password):
        self._data[(service, username)] = password

    def delete_password(self, service, username):
        self._data.pop((service, username), None)


def test_auth_intervals_icu_warn_no_creds_emits_next_action():
    store = CredentialStore(backend=_FakeKeyring(), env={})
    result = check_auth_intervals_icu(store)

    assert result["status"] == "warn"
    assert "next_action" in result
    assert result["next_action"]["command"] == "hai auth intervals-icu"
    assert result["next_action"]["interactive"] is True


def test_auth_garmin_warn_no_creds_emits_next_action():
    store = CredentialStore(backend=_FakeKeyring(), env={})
    result = check_auth_garmin(store)

    assert result["status"] == "warn"
    assert "next_action" in result
    assert result["next_action"]["command"] == "hai auth garmin"
    assert result["next_action"]["interactive"] is True


def test_skills_warn_missing_dest_emits_next_action(tmp_path):
    skills_dest = tmp_path / "skills_does_not_exist"
    result = check_skills(skills_dest, packaged_names=["skill_a", "skill_b"])

    assert result["status"] == "warn"
    assert "next_action" in result
    assert result["next_action"]["command"] == "hai setup-skills"


# ---------------------------------------------------------------------------
# Acceptance 1 — PASS results omit next_action
# ---------------------------------------------------------------------------


def test_state_db_ok_omits_next_action(tmp_path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    result = check_state_db(db_path)

    assert result["status"] == "ok"
    assert "next_action" not in result


# ---------------------------------------------------------------------------
# Acceptance 2 + F-PLAN-02 — post-W-OB-2 command shape
# ---------------------------------------------------------------------------


def test_next_action_command_post_w_ob_2_shape(tmp_path):
    """Missing-intent case in onboarding_readiness must reference
    `hai init` (not `hai init --guided`) — under W-OB-2 the bare command
    auto-promotes on TTY."""

    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    # Bare DB — no intent, no target, no wellness_pull.
    result = check_onboarding_readiness(
        db_path, user_id=USER, as_of_date=date.today(),
    )

    assert result["status"] == "warn"
    assert "next_action" in result
    # Multi-missing → umbrella `hai init` per F-OB-4A-02.
    assert result["next_action"]["command"] == "hai init"
    # Specifically NOT `hai init --guided`.
    assert "--guided" not in result["next_action"]["command"]


# ---------------------------------------------------------------------------
# Acceptance 3 — manifest-consistency invariant
# ---------------------------------------------------------------------------


def test_next_action_agent_safe_matches_live_manifest(tmp_path):
    """Every command in _NEXT_ACTION_REGISTRY whose `command` field is
    a registered top-level CLI command must have `agent_safe` matching
    the live `hai capabilities --json` entry. Per F-PLAN-02 round-1
    correction: the registry is authoritative for the structured field;
    this test ensures the hardcoded values don't drift from the manifest."""

    import io
    from contextlib import redirect_stdout

    out_buf = io.StringIO()
    try:
        with redirect_stdout(out_buf):
            cli_main(["capabilities", "--json"])
    except SystemExit:
        pass
    manifest = json.loads(out_buf.getvalue())

    manifest_by_command = {c["command"]: c for c in manifest["commands"]}

    drift: list[str] = []
    for command, descriptor in _NEXT_ACTION_REGISTRY.items():
        # Some registry entries are sub-flag-bearing forms (e.g.
        # "hai pull --source intervals_icu", "hai intent training
        # add-session"); reduce to the leaf command for manifest lookup.
        leaf = command
        if leaf not in manifest_by_command:
            # Try progressive trimming: "hai foo bar baz" → "hai foo bar" → "hai foo".
            parts = command.split()
            for stop in range(len(parts), 0, -1):
                candidate = " ".join(parts[:stop])
                if candidate in manifest_by_command:
                    leaf = candidate
                    break
        manifest_entry = manifest_by_command.get(leaf)
        if manifest_entry is None:
            drift.append(
                f"registry references {command!r} but manifest has no "
                f"matching command (tried: {command} ... {leaf})"
            )
            continue
        manifest_agent_safe = manifest_entry.get("agent_safe")
        if descriptor["agent_safe"] != manifest_agent_safe:
            drift.append(
                f"{command}: registry agent_safe={descriptor['agent_safe']} "
                f"but live manifest {leaf!r} agent_safe={manifest_agent_safe}"
            )

    assert not drift, (
        "next_action registry drifted from live capabilities manifest:\n  "
        + "\n  ".join(drift)
    )


# ---------------------------------------------------------------------------
# F-OB-4A-02 — umbrella-command preference for multi-missing case
# ---------------------------------------------------------------------------


def test_onboarding_readiness_multi_missing_uses_umbrella(tmp_path):
    """When intent + target + wellness_pull are ALL missing, prefer the
    umbrella `hai init` command rather than per-component (per
    F-OB-4A-02 dogfood finding)."""

    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    result = check_onboarding_readiness(
        db_path, user_id=USER, as_of_date=date.today(),
    )

    assert result["status"] == "warn"
    assert set(result["missing"]) == {"intent", "target", "wellness_pull"}
    assert result["next_action"]["command"] == "hai init"


def test_onboarding_readiness_single_missing_uses_per_component(tmp_path):
    """When only ONE precondition is missing (post-init drift), the
    per-component command is the targeted fix."""

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    # Seed intent + target + wellness pull, leaving only target missing
    # for the test variant. Actually we'll seed intent + wellness_pull
    # only, leaving target as the single missing case.
    from health_agent_infra.core.intent import add_intent
    from health_agent_infra.core.state import open_connection

    today = date.today()

    conn = open_connection(db_path)
    try:
        add_intent(
            conn,
            user_id=USER,
            domain="running",
            intent_type="training_session",
            scope_start=today,
            scope_type="day",
            status="active",
            priority="normal",
            flexibility="flexible",
            payload={"focus": "running"},
            reason="seed for test",
            source="user_authored",
            ingest_actor="cli",
        )
        conn.execute(
            "INSERT INTO sync_run_log (user_id, source, mode, "
            "for_date, status, started_at, completed_at) "
            "VALUES (?, ?, 'live', ?, 'ok', datetime('now'), datetime('now'))",
            (USER, "intervals_icu", today.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()

    result = check_onboarding_readiness(
        db_path, user_id=USER, as_of_date=today,
    )

    assert result["status"] == "warn"
    assert result["missing"] == ["target"]
    assert result["next_action"]["command"] == "hai target set"


# ---------------------------------------------------------------------------
# Acceptance 5 — _render_onboarding_readiness shows next_action.purpose
# ---------------------------------------------------------------------------


def test_render_onboarding_readiness_includes_next_action_purpose():
    """The human-readable rendering must include a `next:` line
    citing the `next_action.purpose`."""

    result = {
        "status": "warn",
        "intent_count": 0,
        "target_count": 0,
        "has_wellness_pull": False,
        "missing": ["intent", "target", "wellness_pull"],
        "hint": "no active intent rows ...",
        "next_action": {
            "command": "hai init",
            "purpose": "scaffold config + state DB + skills, ...",
            "agent_safe": False,
            "interactive": True,
        },
    }
    lines = _render_onboarding_readiness(result)
    rendered = "\n".join(lines)
    assert "next:" in rendered
    assert "scaffold config" in rendered


def test_render_next_action_lines_helper_omits_when_no_purpose():
    """Defensive: helper handles missing purpose gracefully."""

    assert _render_next_action_lines({}) == []
    assert _render_next_action_lines({"command": "hai init"}) == []
