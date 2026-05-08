"""Stand-in for the markdown skill layer — produces minimal DomainProposals
from a state snapshot.

The real skill layer (markdown protocols under
``src/health_agent_infra/skills/``) authors rationale prose, uncertainty
prose, and review questions. The dogfood harness is testing classifier
+ synthesizer behaviour under diverse personas — not the prose surface
— so this module composes a minimum-viable proposal per domain that
satisfies the synthesizer's validator without inventing band values
or rule firings (which the runtime owns).

Action mapping is policy-aware: ``forced_action`` from policy_result
wins; otherwise we map the domain's status field to a sensible default
action token. The mapping is intentionally conservative — when in doubt,
``defer_decision_insufficient_signal``.
"""

from __future__ import annotations

import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any, Optional


# Per-domain action enums must stay in sync with
# ``core/validate.ALLOWED_ACTIONS_BY_DOMAIN``. v0.1.11 W-S (Codex
# F-CDX-IR-06): the harness no longer hardcodes the enum surface.
# A drift contract test (`test_persona_harness_contract.py`)
# asserts every default + status-mapped action below is in the
# domain's authoritative enum.

_DOMAIN_DEFAULT_ACTION = {
    "recovery": "proceed_with_planned_session",
    "running": "proceed_with_planned_run",
    "sleep": "maintain_schedule",
    "stress": "maintain_routine",
    "strength": "proceed_with_planned_session",
    "nutrition": "maintain_targets",
}


def _verify_default_actions_against_runtime() -> None:
    """Boot-time assertion that every default action is a valid token.

    Runs at import time so a renamed action surfaces as a clear
    ImportError rather than a downstream ``hai propose`` validation
    failure. Mirrors the W-S contract test but at the harness's own
    boundary.
    """
    from health_agent_infra.core.validate import ALLOWED_ACTIONS_BY_DOMAIN

    for domain, action in _DOMAIN_DEFAULT_ACTION.items():
        if action not in ALLOWED_ACTIONS_BY_DOMAIN.get(domain, frozenset()):
            raise ImportError(
                f"persona harness drift: domain={domain!r} default "
                f"action {action!r} is not in "
                f"ALLOWED_ACTIONS_BY_DOMAIN[{domain!r}]. "
                f"Update verification/dogfood/synthetic_skill.py "
                f"or the validator enum."
            )


_verify_default_actions_against_runtime()

# Status field per domain → action token (must be a valid action enum)
_STATUS_TO_ACTION = {
    "recovery": {
        "supportive": "proceed_with_planned_session",
        "restorative": "rest_day_recommended",
        "neutral": "proceed_with_planned_session",
        "limiting": "downgrade_session_to_mobility_only",
        "insufficient": "defer_decision_insufficient_signal",
        "unknown": "defer_decision_insufficient_signal",
    },
    "running": {
        "ready": "proceed_with_planned_run",
        "limited": "downgrade_to_easy_aerobic",
        "insufficient": "defer_decision_insufficient_signal",
        "unknown": "defer_decision_insufficient_signal",
    },
    "sleep": {
        "adequate": "maintain_schedule",
        "deficit": "sleep_debt_repayment_day",
        "minor_deficit": "earlier_bedtime_target",
        "insufficient": "defer_decision_insufficient_signal",
        "unknown": "defer_decision_insufficient_signal",
    },
    "stress": {
        "manageable": "maintain_routine",
        "elevated": "schedule_decompression_time",
        "insufficient": "defer_decision_insufficient_signal",
        "unknown": "defer_decision_insufficient_signal",
    },
    "strength": {
        "ready": "proceed_with_planned_session",
        "limited": "downgrade_to_moderate_load",
        "thin_history": "proceed_with_planned_session",
        "insufficient": "defer_decision_insufficient_signal",
        "unknown": "defer_decision_insufficient_signal",
    },
    "nutrition": {
        "adequate": "maintain_targets",
        "deficit": "increase_protein_intake",
        "extreme_deficiency": "escalate_for_user_review",
        "insufficient": "defer_decision_insufficient_signal",
        "unknown": "defer_decision_insufficient_signal",
    },
}

_DOMAIN_STATUS_FIELD = {
    "recovery": "recovery_status",
    "running": "running_readiness_status",
    "sleep": "sleep_status",
    "stress": "stress_state",
    "strength": "strength_status",
    "nutrition": "nutrition_status",
}


def derive_action(
    domain: str,
    classified_state: dict[str, Any],
    policy_result: dict[str, Any],
) -> tuple[str, str]:
    """Return (action, confidence).

    ``forced_action`` from policy_result wins over status-derived action.
    ``capped_confidence`` is honoured. Otherwise we pick a default
    confidence of ``moderate`` — the stand-in does not claim high
    confidence.
    """

    forced = policy_result.get("forced_action")
    if forced:
        action = forced
    else:
        status_field = _DOMAIN_STATUS_FIELD.get(domain)
        status_value = (
            classified_state.get(status_field) if status_field else None
        )
        action = (
            _STATUS_TO_ACTION.get(domain, {}).get(status_value)
            or _DOMAIN_DEFAULT_ACTION.get(domain, "defer_decision_insufficient_signal")
        )

    capped = policy_result.get("capped_confidence")
    confidence = capped if capped else "moderate"
    return action, confidence


def build_proposal(
    domain: str,
    snapshot: dict[str, Any],
    user_id: str,
    for_date: date,
) -> dict[str, Any]:
    """Construct a minimal-but-valid DomainProposal dict for ``hai propose``."""

    domain_block = snapshot.get(domain, {}) or {}
    classified = domain_block.get("classified_state") or {}
    policy = domain_block.get("policy_result") or {}
    missing = domain_block.get("missingness") or {}

    action, confidence = derive_action(domain, classified, policy)

    # Rationale prose — minimal stand-in
    rationale = [
        f"harness-stand-in for {domain}: action={action}, confidence={confidence}",
    ]

    # Uncertainty: pull from missingness tokens (string keys) + classified_state.uncertainty
    uncertainty: list[str] = []
    if isinstance(missing, dict):
        for key in missing.keys():
            if key in {"present", "pending_user_input"}:
                continue
            uncertainty.append(str(key))
    if isinstance(classified.get("uncertainty"), list):
        for u in classified["uncertainty"]:
            if u not in uncertainty:
                uncertainty.append(str(u))
    if not uncertainty:
        uncertainty = ["dogfood_harness_synthetic_proposal"]

    # Policy decisions — convert decisions list from policy_result
    policy_decisions: list[dict[str, Any]] = []
    for pd in policy.get("policy_decisions") or []:
        if isinstance(pd, dict) and pd.get("rule_id"):
            policy_decisions.append(
                {
                    "rule_id": str(pd["rule_id"]),
                    "decision": str(pd.get("decision", "no_op")),
                    "note": str(pd.get("note", "")) if pd.get("note") else None,
                }
            )

    # Codex F-IR-04 fix: source the schema version from the canonical
    # registry rather than hardcoding the literal. A future schema-
    # version bump would otherwise update the manifest + validator
    # but leave the persona harness emitting the stale string.
    from health_agent_infra.core.intake.next_actions import (  # noqa: PLC0415
        _DOMAIN_PROPOSAL_SCHEMAS,
    )

    proposal_id = f"prop_{for_date.isoformat()}_{user_id}_{domain}_01"
    return {
        "schema_version": _DOMAIN_PROPOSAL_SCHEMAS[domain],
        "proposal_id": proposal_id,
        "user_id": user_id,
        "for_date": for_date.isoformat(),
        "domain": domain,
        "action": action,
        "action_detail": policy.get("forced_action_detail") or {},
        "rationale": rationale,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "policy_decisions": policy_decisions,
        "bounded": True,
    }


def post_proposals_for_persona(
    snapshot_path: Path,
    workdir: Path,
    user_id: str,
    for_date: date,
    db_path: Path,
    base_dir: Path,
    env: dict[str, str],
) -> list[dict[str, Any]]:
    """For each expected domain, build + post a proposal via `hai propose`.

    Returns the list of subprocess result rows for audit-trail purposes.
    """

    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for domain in [
        "nutrition",
        "recovery",
        "running",
        "sleep",
        "strength",
        "stress",
    ]:
        proposal = build_proposal(domain, snapshot, user_id, for_date)
        proposal_path = workdir / f"proposal_{domain}.json"
        proposal_path.write_text(json.dumps(proposal, indent=2), encoding="utf-8")

        proc = subprocess.run(
            [
                "uv", "run", "hai", "propose",
                "--domain", domain,
                "--proposal-json", str(proposal_path),
                "--db-path", str(db_path),
                "--base-dir", str(base_dir),
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        rows.append(
            {
                "step": f"propose_{domain}",
                "rc": proc.returncode,
                "ok": proc.returncode == 0,
                "stderr": proc.stderr.strip()[:300] if proc.stderr else None,
                "stdout_head": proc.stdout.strip()[:300] if proc.stdout else None,
            }
        )
    return rows


__all__ = ["build_proposal", "derive_action", "post_proposals_for_persona"]
