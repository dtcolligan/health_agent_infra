"""W-AK (v0.1.13) — declarative persona expected-actions contract.

The persona spec carries a per-domain whitelist (`expected_actions`)
and blacklist (`forbidden_actions`). The harness asserts the actual
recommendation against these. v0.1.14 W58 prep depends on every
persona having a non-empty `expected_actions` so the factuality gate
has a ground-truth shape to compare against.

These tests pin:

  1. Every packaged persona has a non-empty `expected_actions`.
     Either declared inline OR auto-derived in `__post_init__`.
  2. Every domain in the v1 six-domain set is covered by every
     persona's whitelist (no missing domain coverage).
  3. Every action token referenced by a persona's whitelist is in
     `_KNOWN_ACTION_TOKENS` for that domain — typos surface here.
  4. The runner's harness consumes the spec field. (Smoke test on
     a single fabricated persona; full matrix is the dogfood
     `verification.dogfood.runner` invocation.)
"""

from __future__ import annotations

import sys
from pathlib import Path

# verification/dogfood/ isn't a python package; add the repo root to
# sys.path so we can import persona specs directly.
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from health_agent_infra.core.validate import (  # noqa: E402
    ALLOWED_ACTIONS_BY_DOMAIN,
)
from verification.dogfood.personas import ALL_PERSONAS  # noqa: E402


_V1_DOMAINS = frozenset({
    "recovery", "running", "sleep", "stress", "strength", "nutrition",
})


def test_every_persona_has_non_empty_expected_actions():
    for spec in ALL_PERSONAS:
        assert spec.expected_actions, (
            f"persona {spec.persona_id!r} has empty expected_actions; "
            f"either declare an inline override or rely on the "
            f"__post_init__ default in personas/base.py"
        )


def test_every_persona_covers_all_six_v1_domains():
    """Each persona's whitelist must cover every v1 domain. Missing a
    domain means the harness has no contract for that domain on that
    persona — silent gap."""

    for spec in ALL_PERSONAS:
        missing = _V1_DOMAINS - set(spec.expected_actions.keys())
        assert not missing, (
            f"persona {spec.persona_id!r} expected_actions missing "
            f"domains: {sorted(missing)}"
        )


def test_whitelisted_actions_are_known_tokens():
    """A typo in a whitelist (e.g. `proceed_with_session` vs
    `proceed_with_planned_session`) would silently render the contract
    uncheckable. Every token must be in the runtime's authoritative
    `ALLOWED_ACTIONS_BY_DOMAIN` enum — that's the source of truth for
    what actions a domain policy can emit."""

    for spec in ALL_PERSONAS:
        for domain, tokens in spec.expected_actions.items():
            known = set(ALLOWED_ACTIONS_BY_DOMAIN.get(domain, frozenset()))
            unknown = set(tokens) - known
            assert not unknown, (
                f"persona {spec.persona_id!r} expected_actions[{domain!r}] "
                f"contains unknown token(s) {sorted(unknown)}; "
                f"known tokens for {domain!r}: {sorted(known)}"
            )


def test_blacklisted_actions_are_known_tokens():
    """Same drift guard as the whitelist test, but for the negative
    forbidden_actions field."""

    for spec in ALL_PERSONAS:
        for domain, tokens in spec.forbidden_actions.items():
            known = set(ALLOWED_ACTIONS_BY_DOMAIN.get(domain, frozenset()))
            unknown = set(tokens) - known
            assert not unknown, (
                f"persona {spec.persona_id!r} forbidden_actions[{domain!r}] "
                f"contains unknown token(s) {sorted(unknown)}; "
                f"known tokens for {domain!r}: {sorted(known)}"
            )


def test_day_one_personas_default_to_conservative_only():
    """A persona with `history_days == 0` should have
    expected_actions restricted to defer / maintain — proceed /
    downgrade / escalate require signal that day-1 doesn't have."""

    permissive_actions = {
        "proceed_with_planned_session",
        "proceed_with_planned_run",
        "downgrade_hard_session_to_zone_2",
        "downgrade_to_easy_aerobic",
        "rest_day_recommended",
        "escalate_for_user_review",
    }
    for spec in ALL_PERSONAS:
        if spec.history_days != 0:
            continue
        for domain, tokens in spec.expected_actions.items():
            permissive = set(tokens) & permissive_actions
            assert not permissive, (
                f"day-1 persona {spec.persona_id!r} accepts permissive "
                f"actions {sorted(permissive)} on domain {domain!r}; "
                f"day-1 should be defer / maintain only"
            )


def test_runner_harness_records_finding_when_action_outside_whitelist(monkeypatch):
    """Smoke test: fabricate a persona run result with an action
    outside the whitelist; runner emits an `action_outside_persona_whitelist`
    finding."""

    from verification.dogfood.personas import ALL_PERSONAS as _personas
    from verification.dogfood.runner import (
        PersonaRunResult,
        _synthesise_findings,
    )

    from datetime import date

    p1 = next(p for p in _personas if p.persona_id == "p1_dom_baseline")
    # Force-inject an action that is not in the whitelist for nutrition.
    bogus_result = PersonaRunResult(
        persona_id=p1.persona_id,
        persona_label=p1.label,
        as_of_date=date(2026, 4, 30),
        db_path=Path("/tmp/test_persona_w_ak_fake.db"),
    )
    bogus_result.actions_per_domain = {
        "nutrition": "escalate_for_user_review",  # forbidden by default
        "recovery": "proceed_with_planned_session",
        "running": "defer_decision_insufficient_signal",
        "sleep": "maintain_schedule",
        "strength": "defer_decision_insufficient_signal",
        "stress": "maintain_routine",
    }
    bogus_result.daily_status = {"ok": True, "rc": 0}

    findings = _synthesise_findings(p1, bogus_result)
    kinds = {f["kind"] for f in findings}
    # The whitelist excludes `escalate_for_user_review` and the
    # blacklist explicitly forbids it; either finding is acceptable.
    assert (
        "action_outside_persona_whitelist" in kinds
        or "action_in_persona_blacklist" in kinds
    ), (
        f"runner did not emit a W-AK finding for an out-of-whitelist "
        f"action. findings: {findings!r}"
    )
