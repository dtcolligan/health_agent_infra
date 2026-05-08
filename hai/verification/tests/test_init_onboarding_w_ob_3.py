"""W-OB-3 (v0.1.18 §2.C) — `--guided` prompt content review tests.

Acceptance per PLAN.md §2.C:

  2. Refusal-path tests:
     (a) user provides empty input (Enter / no-input) at intent prompt →
         flow treats as skipped; intent_count stays 0; post-prompt
         summary names the gap. (Note: no literal `skip` keyword;
         empty-input affordance only.)
     (b) Ctrl-C mid-target prompt → already covered by
         `test_guided_keyboardinterrupt_*` in
         `test_init_onboarding_flow.py`.
     (c) Re-run resume after partial → already covered by
         `test_guided_rerun_skips_completed_steps`.
  6. Post-prompt summary surfaces a content-only "next action" hint
     pointing the user at `hai today` or `hai daily`. (Per OQ-5:
     content addition, no new flow step.)

Cross-references:
- W-OB-4a finding F-OB-4A-02 informed this test surface — empty-input
  refusal at the focus prompt is a real path the dogfood pass exercised.
- The existing W-AA gate (`test_init_onboarding_flow.py`) covers the
  full-run + Ctrl-C + resume cases; this file extends with skip-input
  affordance + `next_action_hint` content.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from health_agent_infra.core.init import (
    ScriptedPrompts,
    run_guided_onboarding,
)
from health_agent_infra.core.pull.auth import CredentialStore
from health_agent_infra.core.state import initialize_database


USER = "u_w_ob_3"


# ---------------------------------------------------------------------------
# Fakes — mirror test_init_onboarding_flow.py
# ---------------------------------------------------------------------------


class _FakeKeyring:
    def __init__(self) -> None:
        self._data: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self._data.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self._data[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        self._data.pop((service, username), None)


def _fake_store() -> CredentialStore:
    return CredentialStore(backend=_FakeKeyring(), env={})


def _stub_pull_runner(**kwargs):
    return {"status": "ok", "for_date": str(kwargs["as_of"])}


def _stub_today_renderer(**kwargs):
    return {
        "status": "no_plan_yet",
        "for_date": str(kwargs["as_of"]),
        "user_id": kwargs["user_id"],
    }


# ---------------------------------------------------------------------------
# Acceptance 2(a) — empty-input refusal at focus prompt
# ---------------------------------------------------------------------------


def test_guided_empty_input_at_focus_prompt_skips_intent(tmp_path):
    """User presses Enter at "Primary training focus" → intent rows
    stay zero. The orchestrator records ``intent_skipped: True`` and
    moves on to the target prompts."""

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    prompts = ScriptedPrompts(
        responses=[
            # step 4 — auth (skip)
            None,  # athlete id (Enter pressed → empty)
            # step 5 — intent + targets
            None,  # focus prompt (Enter pressed)
            None,  # kcal target (Enter pressed)
            None,  # protein target (Enter pressed)
            None,  # sleep target (Enter pressed)
        ]
    )

    result = run_guided_onboarding(
        db_path=db_path,
        user_id=USER,
        prompts=prompts,
        credential_store=_fake_store(),
        pull_runner=_stub_pull_runner,
        today_renderer=_stub_today_renderer,
    )

    # Auth skipped (no creds).
    assert result.auth_intervals_icu["status"] == "user_skipped"
    # Intent + target authoring: empty-input refusal at focus → skipped.
    assert result.intent_target["status"] == "user_skipped"
    assert result.intent_target.get("intent_ids") == []
    assert result.intent_target.get("target_ids") == []

    # No active intent rows in DB.
    conn = sqlite3.connect(str(db_path))
    try:
        intent_count = conn.execute(
            "SELECT COUNT(*) FROM intent_item WHERE user_id = ? AND status = 'active'",
            (USER,),
        ).fetchone()[0]
        target_count = conn.execute(
            "SELECT COUNT(*) FROM target WHERE user_id = ? AND status = 'active'",
            (USER,),
        ).fetchone()[0]
    finally:
        conn.close()
    assert intent_count == 0
    assert target_count == 0

    # Overall status reflects skips.
    assert result.overall_status == "ok_with_skips"


# ---------------------------------------------------------------------------
# Acceptance 2(a) variant — empty input at single target prompt
# ---------------------------------------------------------------------------


def test_guided_empty_input_at_target_prompt_skips_only_that_target(tmp_path):
    """User answers focus + kcal but presses Enter on protein + sleep.
    Result: intent + 1 target authored; protein/sleep skipped."""

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    prompts = ScriptedPrompts(
        responses=[
            None,            # auth athlete id (skip)
            "running",       # focus
            "2400",          # kcal answered
            None,            # protein (Enter pressed)
            None,            # sleep (Enter pressed)
        ]
    )

    result = run_guided_onboarding(
        db_path=db_path,
        user_id=USER,
        prompts=prompts,
        credential_store=_fake_store(),
        pull_runner=_stub_pull_runner,
        today_renderer=_stub_today_renderer,
    )

    assert result.intent_target["status"] == "authored"
    assert len(result.intent_target["intent_ids"]) == 1
    assert len(result.intent_target["target_ids"]) == 1  # kcal only


# ---------------------------------------------------------------------------
# Acceptance 6 — next_action_hint content
# ---------------------------------------------------------------------------


def test_guided_full_run_emits_next_action_hint_pointing_at_hai_daily(tmp_path):
    """Successful onboarding (creds + intent + target authored) →
    next_action_hint points at `hai daily` directly."""

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    prompts = ScriptedPrompts(
        responses=[
            "i123456",       # athlete id
            "test_api_key",  # api key
            "running",       # focus
            "2400",          # kcal
            "140",           # protein
            "8",             # sleep
        ]
    )

    result = run_guided_onboarding(
        db_path=db_path,
        user_id=USER,
        prompts=prompts,
        credential_store=_fake_store(),
        pull_runner=_stub_pull_runner,
        today_renderer=_stub_today_renderer,
    )

    assert result.next_action_hint != ""
    assert "hai daily" in result.next_action_hint
    # When everything is configured, hint is direct (no remediation).
    assert "intervals.icu credentials" not in result.next_action_hint
    assert "training intent" not in result.next_action_hint


def test_guided_skip_auth_emits_next_action_hint_with_credentials_remediation(tmp_path):
    """User skipped auth but answered intent + targets → next_action_hint
    surfaces credentials remediation before hai daily."""

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    prompts = ScriptedPrompts(
        responses=[
            None,            # athlete id (skip → no auth)
            "running",       # focus
            "2400",          # kcal
            "140",           # protein
            "8",             # sleep
        ]
    )

    result = run_guided_onboarding(
        db_path=db_path,
        user_id=USER,
        prompts=prompts,
        credential_store=_fake_store(),
        pull_runner=_stub_pull_runner,
        today_renderer=_stub_today_renderer,
    )

    assert result.next_action_hint != ""
    assert "hai auth intervals-icu" in result.next_action_hint
    assert "hai daily" in result.next_action_hint


def test_guided_skip_everything_emits_re_run_guided_hint(tmp_path):
    """User skipped auth AND intent → next_action_hint suggests re-running
    `hai init --guided`."""

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    prompts = ScriptedPrompts(
        responses=[
            None,  # athlete id (skip)
            None,  # focus (skip)
            None,  # kcal (skip)
            None,  # protein (skip)
            None,  # sleep (skip)
        ]
    )

    result = run_guided_onboarding(
        db_path=db_path,
        user_id=USER,
        prompts=prompts,
        credential_store=_fake_store(),
        pull_runner=_stub_pull_runner,
        today_renderer=_stub_today_renderer,
    )

    assert result.next_action_hint != ""
    assert "hai init --guided" in result.next_action_hint


def test_guided_creds_plus_intent_but_all_targets_skipped_routes_to_target_remediation(tmp_path):
    """F-IR-04 (D15 IR R1) regression: pre-fix the post-prompt hint
    branched on `intent_target.status` alone, which returns "authored"
    when ANY row was authored — even if only intent landed and all
    target prompts were skipped. The hint then incorrectly said
    "Run `hai daily`" while `check_onboarding_readiness` would still
    WARN on missing targets.

    Post-fix: with creds + focus answered + all 3 target prompts
    skipped, the hint must NOT point at `hai daily`. It should call
    out the target gap and route to `hai target set`."""

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    prompts = ScriptedPrompts(
        responses=[
            "i123456",       # athlete id
            "test_api_key",  # api key
            "running",       # focus answered
            None,            # kcal target SKIPPED
            None,            # protein target SKIPPED
            None,            # sleep target SKIPPED
        ]
    )

    result = run_guided_onboarding(
        db_path=db_path,
        user_id=USER,
        prompts=prompts,
        credential_store=_fake_store(),
        pull_runner=_stub_pull_runner,
        today_renderer=_stub_today_renderer,
    )

    # Verify the precondition the bug surfaced on: status is "authored"
    # (intent landed) but target_ids is empty.
    assert result.intent_target["status"] == "authored"
    assert len(result.intent_target["intent_ids"]) == 1
    assert result.intent_target["target_ids"] == []

    # Hint must NOT point at hai daily — onboarding readiness is
    # incomplete (missing target).
    assert "hai daily" not in result.next_action_hint or "then run `hai daily`" in result.next_action_hint
    assert "hai target set" in result.next_action_hint


def test_guided_creds_plus_intent_skipped_but_targets_authored_routes_to_intent_remediation(tmp_path):
    """Symmetric F-IR-04 regression: creds + targets answered + intent
    skipped → hint must route to `hai intent training add-session`,
    not `hai daily`."""

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    prompts = ScriptedPrompts(
        responses=[
            "i123456",       # athlete id
            "test_api_key",  # api key
            None,            # focus SKIPPED
            "2400",          # kcal target answered
            "140",           # protein target answered
            "8",             # sleep target answered
        ]
    )

    result = run_guided_onboarding(
        db_path=db_path,
        user_id=USER,
        prompts=prompts,
        credential_store=_fake_store(),
        pull_runner=_stub_pull_runner,
        today_renderer=_stub_today_renderer,
    )

    assert result.intent_target["status"] == "authored"
    assert result.intent_target["intent_ids"] == []
    assert len(result.intent_target["target_ids"]) == 3

    assert "hai intent training add-session" in result.next_action_hint


def test_guided_next_action_hint_in_to_dict(tmp_path):
    """`to_dict` includes the hint so the upstream cmd_init JSON
    report surfaces it without reshaping."""

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    prompts = ScriptedPrompts(
        responses=[
            "i123456", "test_api_key",
            "running", "2400", "140", "8",
        ]
    )

    result = run_guided_onboarding(
        db_path=db_path,
        user_id=USER,
        prompts=prompts,
        credential_store=_fake_store(),
        pull_runner=_stub_pull_runner,
        today_renderer=_stub_today_renderer,
    )

    d = result.to_dict()
    assert "next_action_hint" in d
    assert d["next_action_hint"] == result.next_action_hint
