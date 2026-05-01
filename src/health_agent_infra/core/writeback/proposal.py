"""Proposal writeback (Phase 2 step 4).

Append-only JSONL audit + DB projection for ``DomainProposal``-shaped
payloads emitted by the six per-domain readiness skills (recovery,
running, sleep, stress, strength, nutrition).

Parallel to :mod:`health_agent_infra.core.writeback.recommendation` but
for proposals, with three differences:

  1. Proposals have no ``follow_up`` (reviews schedule from
     recommendations, not proposals — see ``DOMAIN_PROPOSAL_FIELDS``).
  2. Proposals have no ``daily_plan_id`` at write time (synthesis
     assigns it atomically in :mod:`health_agent_infra.core.synthesis`).
  3. The writeback validator rejects any payload carrying either
     ``follow_up`` or ``daily_plan_id`` — the shapes must not collide.

The JSONL audit file is keyed per-domain: ``<base_dir>/<domain>_proposals.jsonl``.
Re-running ``hai propose`` on a proposal_id that already exists is a no-op
at both the JSONL and DB layer (idempotent by construction).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional


from health_agent_infra.core.schemas import DOMAIN_PROPOSAL_FIELDS


# v1 supports six domains on the proposal surface: recovery + running
# (Phase 1/2) plus sleep + stress (Phase 3) plus strength (Phase 4) plus
# nutrition (Phase 5, macros-only per the Phase 2.5 retrieval-gate
# outcome). Strength's classify + policy + schemas shipped in Phase 4
# and its synthesis_policy action registry entry is first-class; this
# validator entry completes the proposal write surface so `hai daily`
# can talk to a real 6-domain governed runtime.
SUPPORTED_DOMAINS: frozenset[str] = frozenset({
    "recovery", "running", "sleep", "stress", "strength", "nutrition",
})


PROPOSAL_SCHEMA_VERSIONS: dict[str, str] = {
    "running": "running_proposal.v1",
    "recovery": "recovery_proposal.v1",
    "sleep": "sleep_proposal.v1",
    "stress": "stress_proposal.v1",
    "strength": "strength_proposal.v1",
    "nutrition": "nutrition_proposal.v1",
}


DOMAIN_ACTION_ENUMS: dict[str, frozenset[str]] = {
    "running": frozenset({
        "proceed_with_planned_run",
        "downgrade_intervals_to_tempo",
        "downgrade_to_easy_aerobic",
        "cross_train_instead",
        "rest_day_recommended",
        "defer_decision_insufficient_signal",
        "escalate_for_user_review",
    }),
    "recovery": frozenset({
        "proceed_with_planned_session",
        "downgrade_hard_session_to_zone_2",
        "downgrade_session_to_mobility_only",
        "rest_day_recommended",
        "defer_decision_insufficient_signal",
        "escalate_for_user_review",
    }),
    # Sleep: no escalate action in v1 enum — R-chronic-deprivation forces
    # ``sleep_debt_repayment_day`` and records the escalate tier on the
    # policy decision record instead. See domains/sleep/schemas.py.
    "sleep": frozenset({
        "maintain_schedule",
        "prioritize_wind_down",
        "sleep_debt_repayment_day",
        "earlier_bedtime_target",
        "defer_decision_insufficient_signal",
    }),
    "stress": frozenset({
        "maintain_routine",
        "add_low_intensity_recovery",
        "schedule_decompression_time",
        "escalate_for_user_review",
        "defer_decision_insufficient_signal",
    }),
    # Strength v1 enum sourced from domains/strength/schemas.py ::
    # STRENGTH_ACTION_KINDS. Kept in lockstep with that tuple; the
    # test_cli_propose strength coverage pins this contract.
    "strength": frozenset({
        "proceed_with_planned_session",
        "downgrade_to_technique_or_accessory",
        "downgrade_to_moderate_load",
        "rest_day_recommended",
        "defer_decision_insufficient_signal",
        "escalate_for_user_review",
    }),
    # Nutrition v1 macros-only collapse — see domains/nutrition/schemas.py
    # for the rationale behind the collapse (Phase 2.5 retrieval gate
    # failed; no meal-level micronutrient evidence in v1).
    "nutrition": frozenset({
        "maintain_targets",
        "increase_protein_intake",
        "increase_hydration",
        "reduce_calorie_deficit",
        "defer_decision_insufficient_signal",
        "escalate_for_user_review",
    }),
}


ALLOWED_CONFIDENCE: frozenset[str] = frozenset({"low", "moderate", "high"})


# Fields that must NEVER appear on a proposal payload. These are
# recommendation-only and represent either skills stepping outside
# their lane (daily_plan_id = synthesis's job) or schema collision
# (follow_up = recommendation's job).
FORBIDDEN_PROPOSAL_FIELDS: frozenset[str] = frozenset({
    "follow_up",
    "daily_plan_id",
    "recommendation_id",
})


class ProposalValidationError(ValueError):
    """Raised when a proposal dict violates a code-enforced invariant."""

    def __init__(self, invariant: str, message: str) -> None:
        super().__init__(message)
        self.invariant = invariant


def validate_proposal_dict(data: Any, *, expected_domain: Optional[str] = None) -> None:
    """Validate a proposal dict against the frozen contract.

    Raises :class:`ProposalValidationError` on the first violation. The
    ``invariant`` attribute names the rule that failed so tests can
    pattern-match without parsing prose.

    Invariant ids:
      - ``required_fields_present`` — every field in
        ``DOMAIN_PROPOSAL_FIELDS`` must be present.
      - ``forbidden_fields_absent`` — no ``follow_up`` / ``daily_plan_id``
        / ``recommendation_id``.
      - ``domain_supported`` — domain ∈ :data:`SUPPORTED_DOMAINS`.
      - ``domain_match`` — if ``expected_domain`` is provided (from the
        CLI's ``--domain`` flag), the payload domain must match.
      - ``schema_version`` — matches the per-domain v1 string.
      - ``action_enum`` — action ∈ the domain's action enum.
      - ``confidence_enum`` — low | moderate | high.
      - ``bounded_true`` — ``bounded`` is True.
      - ``policy_decisions_present`` — non-empty list.
      - ``for_date_iso`` — parseable ISO date string.
    """

    if not isinstance(data, dict):
        raise ProposalValidationError(
            "required_fields_present",
            f"expected dict, got {type(data).__name__}",
        )

    missing = set(DOMAIN_PROPOSAL_FIELDS) - set(data.keys())
    # proposal_id is not in DOMAIN_PROPOSAL_FIELDS check... actually, it is.
    # Let's do the check by name.
    required = {"schema_version", "proposal_id", "user_id", "for_date", "domain",
                "action", "action_detail", "rationale", "confidence",
                "uncertainty", "policy_decisions", "bounded"}
    missing = required - set(data.keys())
    if missing:
        raise ProposalValidationError(
            "required_fields_present",
            f"missing required fields: {sorted(missing)}",
        )

    forbidden_present = FORBIDDEN_PROPOSAL_FIELDS & set(data.keys())
    if forbidden_present:
        raise ProposalValidationError(
            "forbidden_fields_absent",
            f"proposal carries recommendation-only fields: "
            f"{sorted(forbidden_present)}. Proposals never have follow_up, "
            f"daily_plan_id, or recommendation_id.",
        )

    domain = data["domain"]
    if domain not in SUPPORTED_DOMAINS:
        raise ProposalValidationError(
            "domain_supported",
            f"domain {domain!r} not in supported set {sorted(SUPPORTED_DOMAINS)}",
        )
    if expected_domain is not None and expected_domain != domain:
        raise ProposalValidationError(
            "domain_match",
            f"--domain={expected_domain!r} does not match payload domain "
            f"{domain!r}",
        )

    expected_schema = PROPOSAL_SCHEMA_VERSIONS[domain]
    if data["schema_version"] != expected_schema:
        raise ProposalValidationError(
            "schema_version",
            f"expected schema_version={expected_schema!r} for domain "
            f"{domain!r}, got {data['schema_version']!r}",
        )

    allowed_actions = DOMAIN_ACTION_ENUMS[domain]
    action = data["action"]
    if action not in allowed_actions:
        raise ProposalValidationError(
            "action_enum",
            f"action {action!r} not in {domain!r} enum {sorted(allowed_actions)}",
        )

    confidence = data["confidence"]
    if confidence not in ALLOWED_CONFIDENCE:
        raise ProposalValidationError(
            "confidence_enum",
            f"confidence {confidence!r} not in {sorted(ALLOWED_CONFIDENCE)}",
        )

    if data["bounded"] is not True:
        raise ProposalValidationError(
            "bounded_true",
            f"bounded must be True, got {data['bounded']!r}",
        )

    policy_decisions = data["policy_decisions"]
    if not isinstance(policy_decisions, list) or len(policy_decisions) < 1:
        raise ProposalValidationError(
            "policy_decisions_present",
            f"policy_decisions must be a non-empty list; got {policy_decisions!r}",
        )

    try:
        date.fromisoformat(data["for_date"])
    except (TypeError, ValueError) as exc:
        raise ProposalValidationError(
            "for_date_iso",
            f"for_date must be ISO-8601 YYYY-MM-DD; got {data['for_date']!r} ({exc})",
        )

    # v0.1.9 B3 — strict text shape on rationale / uncertainty /
    # policy_decisions. Pre-v0.1.9 the validator only checked presence;
    # Codex 2026-04-26 confirmed string values for rationale/uncertainty
    # passed today. Shared with the recommendation validator so both
    # surfaces enforce identical shape.
    from health_agent_infra.core.validate import (
        check_banned_tokens_in_surfaces,
        check_policy_decisions_shape,
        check_rationale_shape,
        check_uncertainty_shape,
    )

    check_rationale_shape(data, error_cls=ProposalValidationError)
    check_uncertainty_shape(data, error_cls=ProposalValidationError)
    check_policy_decisions_shape(data, error_cls=ProposalValidationError)

    # Phase A safety closure (v0.1.4) — banned diagnosis-shaped tokens must
    # be rejected at the proposal seam, not only at the recommendation
    # seam. v0.1.9 B3 routes both validators through one shared sweep
    # (``check_banned_tokens_in_surfaces``) so a future surface added in
    # one place is automatically covered in the other.
    check_banned_tokens_in_surfaces(
        data,
        include_follow_up=False,  # proposals carry no follow_up by contract
        error_cls=ProposalValidationError,
    )

    # v0.1.14 W-PROV-1 — optional source-row locators. Additive,
    # backwards-compatible: proposals without `evidence_locators`
    # continue to validate. When present, every entry must satisfy
    # the W-PROV-1 contract (reporting/docs/source_row_provenance.md).
    if "evidence_locators" in data:
        from health_agent_infra.core.provenance.locator import (
            LocatorValidationError,
            validate_locator,
        )
        locators = data["evidence_locators"]
        if not isinstance(locators, list):
            raise ProposalValidationError(
                "evidence_locators_shape",
                f"evidence_locators must be a list; "
                f"got {type(locators).__name__}",
            )
        for idx, loc in enumerate(locators):
            try:
                validate_locator(loc)
            except LocatorValidationError as exc:
                raise ProposalValidationError(
                    "evidence_locators_entry",
                    f"evidence_locators[{idx}] invalid "
                    f"({exc.invariant}): {exc}",
                ) from exc


@dataclass
class ProposalRecord:
    proposal_id: str
    domain: str
    writeback_path: str
    idempotency_key: str
    performed_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "domain": self.domain,
            "writeback_path": self.writeback_path,
            "idempotency_key": self.idempotency_key,
            "performed_at": self.performed_at.isoformat(),
        }


def proposal_log_filename(domain: str) -> str:
    """JSONL filename per domain. Kept as a function so tests don't hard-code."""

    return f"{domain}_proposals.jsonl"


def perform_proposal_writeback(
    proposal: dict[str, Any],
    *,
    base_dir: Path,
    now: Optional[datetime] = None,
) -> ProposalRecord:
    """Append a validated proposal to its per-domain JSONL audit log.

    Idempotent on ``proposal_id`` (re-running silently no-ops at the
    JSONL layer; the caller sees the same ``ProposalRecord``).

    The caller is expected to have run :func:`validate_proposal_dict`
    already; this function trusts its input.
    """

    from health_agent_infra.core.privacy import secure_directory, secure_file

    now = now or datetime.now(timezone.utc)
    domain = proposal["domain"]
    proposal_id = proposal["proposal_id"]

    base_dir = base_dir.resolve()
    secure_directory(base_dir, create=True)
    log_path = base_dir / proposal_log_filename(domain)

    if not _already_written(log_path, proposal_id):
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(proposal, sort_keys=True) + "\n")
    secure_file(log_path)

    return ProposalRecord(
        proposal_id=proposal_id,
        domain=domain,
        writeback_path=str(log_path),
        idempotency_key=proposal_id,
        performed_at=now,
    )


def _already_written(log_path: Path, proposal_id: str) -> bool:
    if not log_path.exists():
        return False
    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("proposal_id") == proposal_id:
                return True
    return False
