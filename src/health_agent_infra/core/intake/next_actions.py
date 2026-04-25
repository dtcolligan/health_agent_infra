"""Versioned next-action manifest emitted by ``hai daily --auto``.

v0.1.7 W21. The legacy ``hai daily`` output stops at the proposal
gate and tells the agent (in prose) to post the missing
DomainProposal rows and rerun. ``--auto`` mode replaces that prose
hint with a typed ``next_actions[]`` list every action a generic
agent would need to drive the day end-to-end. Codex r2 + r3 audits
explicitly required: schema_version, action_id, concrete
command_argv, blocking, safe_to_retry, after_success routing,
stable reason_code, and idempotency hints.

The schema is bounded — every shape change bumps
``NEXT_ACTIONS_SCHEMA_VERSION`` so an agent can pattern-match on
it. The only "kinds" v0.1.7 supports are:

  - ``intake_required``: the gap-detector found user-closeable
    evidence missing. The action carries the canonical command_argv
    template + the input source the agent should consult (e.g.
    ``hai planned-session-types`` for the planned-session
    vocabulary).
  - ``skill_invocation_required``: a per-domain readiness skill
    must produce a DomainProposal. The action names the skill,
    the snapshot block it reads, the proposal shape it produces,
    and the ``hai propose`` invocation that lands the result.
  - ``synthesize_ready``: every expected domain has a proposal;
    re-running ``hai daily --skip-pull --auto`` advances the gate
    to ``complete`` (which then runs synthesis AND schedules
    reviews via the orchestrator's review stage). Codex r3
    explicitly: do NOT route through ``hai synthesize`` directly,
    which would skip review scheduling.
"""

from __future__ import annotations

from typing import Any


NEXT_ACTIONS_SCHEMA_VERSION = "next_actions.v1"


# Per-domain readiness skill names. The W21 manifest references them
# in skill_invocation_required actions; the agent host invokes them.
_DOMAIN_SKILLS: dict[str, str] = {
    "recovery": "recovery-readiness",
    "running": "running-readiness",
    "sleep": "sleep-quality",
    "strength": "strength-readiness",
    "stress": "stress-regulation",
    "nutrition": "nutrition-alignment",
}


# Per-domain DomainProposal schema_version. The agent uses this when
# composing the proposal payload.
_DOMAIN_PROPOSAL_SCHEMAS: dict[str, str] = {
    "recovery": "recovery_proposal.v1",
    "running": "running_proposal.v1",
    "sleep": "sleep_proposal.v1",
    "strength": "strength_proposal.v1",
    "stress": "stress_proposal.v1",
    "nutrition": "nutrition_proposal.v1",
}


def _action_id(*, for_date: str, user_id: str, n: int) -> str:
    """Stable per-action id within a single manifest. Format keeps
    monotonic ordering even if the manifest is later persisted +
    diffed."""

    return f"act_{for_date}_{user_id}_{n:03d}"


def _intake_required_actions(
    *, for_date: str, user_id: str, gaps: list[dict[str, Any]],
    counter_start: int,
) -> tuple[list[dict[str, Any]], int]:
    """Translate the gap detector's output into intake_required
    actions, ordered by priority (lower = more urgent)."""

    actions: list[dict[str, Any]] = []
    n = counter_start
    for gap in sorted(gaps, key=lambda g: (g.get("priority", 99),
                                            g.get("domain", ""))):
        action: dict[str, Any] = {
            "action_id": _action_id(for_date=for_date, user_id=user_id, n=n),
            "kind": "intake_required",
            "reason_code": gap["missing_field"],
            "domain": gap["domain"],
            "priority": gap.get("priority", 1),
            "blocking": gap.get("blocks_coverage", True),
            "safe_to_retry": False,
            "command_template": gap["intake_args_template"],
            "command_root": gap["intake_command"],
            "field_description": gap["field_description"],
            "after_success": {
                "command_argv": [
                    "hai", "daily",
                    "--as-of", for_date,
                    "--user-id", user_id,
                    "--skip-pull", "--auto",
                ],
            },
        }
        # Recovery-readiness intake refers to the planned-session
        # vocabulary (W33). Surface the discovery command.
        if gap["intake_command"] == "hai intake readiness":
            action["input_vocabularies"] = [
                {"field": "--planned-session-type",
                 "discovery_command": ["hai", "planned-session-types"]},
            ]
        actions.append(action)
        n += 1
    return actions, n


def _skill_invocation_actions(
    *, for_date: str, user_id: str, missing_domains: list[str],
    counter_start: int,
) -> tuple[list[dict[str, Any]], int]:
    """Translate missing-domain proposals into skill_invocation_required
    actions. One per missing domain."""

    actions: list[dict[str, Any]] = []
    n = counter_start
    for domain in sorted(missing_domains):
        skill = _DOMAIN_SKILLS.get(domain, f"{domain}-readiness")
        proposal_schema = _DOMAIN_PROPOSAL_SCHEMAS.get(domain)
        actions.append({
            "action_id": _action_id(for_date=for_date, user_id=user_id, n=n),
            "kind": "skill_invocation_required",
            "reason_code": "domain_proposal_missing",
            "domain": domain,
            "priority": 1,
            "skill": skill,
            "reads_snapshot_path": f"snapshot.{domain}",
            "produces": proposal_schema,
            "writeback_command": [
                "hai", "propose",
                "--domain", domain,
                "--proposal-json", "<path-to-proposal-json>",
            ],
            "writeback_mutation_class": "writes-state",
            "blocking": True,
            "safe_to_retry": True,
            "idempotency_key_pattern": (
                f"prop_{for_date}_{user_id}_{domain}_NN"
            ),
            "after_success": {
                "command_argv": [
                    "hai", "daily",
                    "--as-of", for_date,
                    "--user-id", user_id,
                    "--skip-pull", "--auto",
                ],
            },
        })
        n += 1
    return actions, n


def _synthesize_ready_action(
    *, for_date: str, user_id: str, counter: int,
) -> dict[str, Any]:
    """Terminal action when every expected domain has a proposal:
    re-run ``hai daily --skip-pull --auto`` to advance the gate to
    ``complete``, which triggers synthesis AND review scheduling.
    Codex r3: do not route through ``hai synthesize`` directly; that
    skips review scheduling."""

    return {
        "action_id": _action_id(for_date=for_date, user_id=user_id, n=counter),
        "kind": "synthesize_ready",
        "reason_code": "all_proposals_present",
        "priority": 1,
        "command_argv": [
            "hai", "daily",
            "--as-of", for_date,
            "--user-id", user_id,
            "--skip-pull", "--auto",
        ],
        "mutation_class": "writes-state",
        "blocking": False,
        "safe_to_retry": True,
        "after_success": None,
    }


def _narrate_ready_action(
    *, for_date: str, user_id: str, counter: int,
) -> dict[str, Any]:
    """Terminal action when synthesis already ran: tell the agent to
    narrate via the reporting skill + log review outcomes when
    available."""

    return {
        "action_id": _action_id(for_date=for_date, user_id=user_id, n=counter),
        "kind": "narrate_ready",
        "reason_code": "plan_committed",
        "priority": 1,
        "skill": "reporting",
        "reads": [
            ["hai", "today", "--as-of", for_date,
             "--user-id", user_id, "--format", "json"],
        ],
        "blocking": False,
        "safe_to_retry": True,
        "after_success": None,
        "follow_up_when_user_reports_outcome": {
            "command_root": "hai review record",
            "command_argv_template": [
                "hai", "review", "record",
                "--outcome-json", "<path>",
            ],
        },
    }


def build_next_actions_payload(
    *,
    for_date: str,
    user_id: str,
    overall_status: str,
    expected_domains: list[str],
    present_domains: list[str],
    missing_domains: list[str],
    intake_gaps: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compose the v1 next_actions manifest from the daily
    orchestrator's stage report.

    Inputs:
      - ``overall_status``: one of awaiting_proposals / incomplete /
        complete (the gate's status).
      - ``expected_domains`` / ``present_domains`` / ``missing_domains``:
        as computed by the gate.
      - ``intake_gaps``: optional list of gap dicts (from
        ``compute_intake_gaps``); when present, intake_required actions
        precede skill_invocation_required actions.

    Returns a JSON-serialisable dict with ``schema_version``,
    ``next_actions[]``, and ``telemetry``. Always emits at least one
    action — never a meaningless empty list (when complete + no
    intake gaps, the action is ``narrate_ready``).
    """

    next_actions: list[dict[str, Any]] = []
    counter = 1

    # 1. Intake gaps come first (priority 1 gating gaps before any
    # skill invocation can produce a useful proposal).
    if intake_gaps:
        intake, counter = _intake_required_actions(
            for_date=for_date, user_id=user_id,
            gaps=intake_gaps, counter_start=counter,
        )
        next_actions.extend(intake)

    # 2. Per-domain skill invocations for missing proposals.
    if missing_domains:
        skills, counter = _skill_invocation_actions(
            for_date=for_date, user_id=user_id,
            missing_domains=missing_domains, counter_start=counter,
        )
        next_actions.extend(skills)

    # 3. Terminal action.
    if missing_domains or (intake_gaps and any(
        g.get("blocks_coverage", True) for g in intake_gaps
    )):
        # Still gating something — the after_success on the last
        # intake/skill action already routes back to `hai daily`.
        # No terminal needed; the agent loops via after_success.
        pass
    elif overall_status == "complete":
        next_actions.append(_narrate_ready_action(
            for_date=for_date, user_id=user_id, counter=counter,
        ))
    else:
        next_actions.append(_synthesize_ready_action(
            for_date=for_date, user_id=user_id, counter=counter,
        ))

    return {
        "schema_version": NEXT_ACTIONS_SCHEMA_VERSION,
        "as_of_date": for_date,
        "user_id": user_id,
        "next_actions": next_actions,
        "telemetry": {
            "overall_status": overall_status,
            "expected_domains": sorted(expected_domains),
            "present_domains": sorted(present_domains),
            "missing_domains": sorted(missing_domains),
            "action_count": len(next_actions),
        },
    }


__all__ = [
    "NEXT_ACTIONS_SCHEMA_VERSION",
    "build_next_actions_payload",
]
