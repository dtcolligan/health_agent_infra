"""Daily evidence-card projector — W-EVCARD-DAILY (v0.2.0 §2.B).

Builds and persists ``recommendation_evidence_card.v1`` rows. One card
per row in ``recommendation_log``. Schema reference:
``reporting/plans/future_strategy_2026-04-29/review_codex.md:1480-1545``.

Architecture invariant (W-PROV-1 + F-PHASE0-12 reaffirmed):
``payload_json["provenance"]["accepted_state_rows"]`` and
``payload_json["provenance"]["raw_source_refs"]`` carry
``SourceRowLocator``-shaped dicts and validate against the
W-PROV-1 whitelist. Write-side audit-chain references (proposal_log,
planned_recommendation, recommendation_log, x_rule_firing,
data_quality_daily) live in separate fields under ``provenance`` and
are validated as plain primary keys, NOT as ``SourceRowLocator``
instances.

The card is written INSIDE the synthesis transaction post-
recommendation_log + planned_recommendation rows; rollback if any
insert fails. The contract is enforced by ``synthesis.run_synthesis``
calling :func:`project_evidence_card` with ``commit_after=False``.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Optional

from health_agent_infra.core.provenance.locator import (
    LocatorValidationError,
    validate_locator,
)
from health_agent_infra.core.state.projectors._shared import _now_iso


EVIDENCE_CARD_SCHEMA_VERSION = "recommendation_evidence_card.v1"


class EvidenceCardValidationError(ValueError):
    """Raised when an evidence-card payload violates the schema contract."""

    def __init__(self, invariant: str, message: str) -> None:
        super().__init__(message)
        self.invariant = invariant


def validate_evidence_card_payload(payload: Any) -> None:
    """Validate a ``recommendation_evidence_card.v1`` payload dict.

    Raises :class:`EvidenceCardValidationError` on the first violation.
    The payload must be a dict carrying the six W-EVCARD-DAILY lanes
    and a provenance lane structured per F-PHASE0-12.

    Locators inside ``provenance.accepted_state_rows`` and
    ``provenance.raw_source_refs`` validate via the W-PROV-1
    contract; audit-chain ID lists are validated as plain string /
    integer arrays.
    """

    if not isinstance(payload, dict):
        raise EvidenceCardValidationError(
            "shape", f"payload must be dict; got {type(payload).__name__}"
        )

    # Required top-level lanes per the schema sketch.
    required_lanes = {"decision", "evidence", "provenance"}
    missing = required_lanes - set(payload.keys())
    if missing:
        raise EvidenceCardValidationError(
            "required_lanes",
            f"payload missing required lanes: {sorted(missing)}",
        )

    provenance = payload["provenance"]
    if not isinstance(provenance, dict):
        raise EvidenceCardValidationError(
            "provenance_shape",
            f"provenance lane must be dict; got {type(provenance).__name__}",
        )

    # Locator-shaped lanes — validate every entry per W-PROV-1.
    for lane in ("accepted_state_rows", "raw_source_refs"):
        entries = provenance.get(lane, [])
        if not isinstance(entries, list):
            raise EvidenceCardValidationError(
                f"{lane}_shape",
                f"provenance.{lane} must be a list; "
                f"got {type(entries).__name__}",
            )
        for idx, loc in enumerate(entries):
            try:
                validate_locator(loc)
            except LocatorValidationError as exc:
                raise EvidenceCardValidationError(
                    f"{lane}_entry",
                    f"provenance.{lane}[{idx}] invalid: {exc}",
                ) from exc

    # Audit-chain ID list lanes — validated as plain PK arrays. Per
    # F-PHASE0-12, these are NOT SourceRowLocator instances.
    pk_array_lanes = (
        "proposal_log",
        "planned_recommendation",
        "recommendation_log",
        "x_rule_firing",
    )
    for lane in pk_array_lanes:
        entries = provenance.get(lane, [])
        if not isinstance(entries, list):
            raise EvidenceCardValidationError(
                f"{lane}_shape",
                f"provenance.{lane} must be a list; "
                f"got {type(entries).__name__}",
            )
        for idx, val in enumerate(entries):
            if not isinstance(val, (str, int)):
                raise EvidenceCardValidationError(
                    f"{lane}_entry",
                    f"provenance.{lane}[{idx}] must be str/int; "
                    f"got {type(val).__name__}",
                )

    # data_quality_daily uses a composite PK (object) shape.
    dq_entries = provenance.get("data_quality_daily", [])
    if not isinstance(dq_entries, list):
        raise EvidenceCardValidationError(
            "data_quality_daily_shape",
            f"provenance.data_quality_daily must be a list; "
            f"got {type(dq_entries).__name__}",
        )
    for idx, entry in enumerate(dq_entries):
        if not isinstance(entry, dict):
            raise EvidenceCardValidationError(
                "data_quality_daily_entry",
                f"provenance.data_quality_daily[{idx}] must be dict; "
                f"got {type(entry).__name__}",
            )


def build_evidence_card_payload(
    recommendation: dict,
    *,
    accepted_state_rows: Optional[list[dict[str, Any]]] = None,
    raw_source_refs: Optional[list[dict[str, Any]]] = None,
    proposal_log_ids: Optional[list[str]] = None,
    planned_ids: Optional[list[str]] = None,
    recommendation_log_ids: Optional[list[str]] = None,
    x_rule_firing_ids: Optional[list[int]] = None,
    data_quality_daily: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Construct a ``recommendation_evidence_card.v1`` payload for the
    given recommendation row.

    Source-row locators (already validated at the recommendation /
    proposal layer per W-PROV-1) split into the
    ``accepted_state_rows`` lane (W-PROV-2 emission output) and the
    ``raw_source_refs`` lane (any cited source-table rows; today
    populated only by recovery R6's spike-window emission).
    """

    payload: dict[str, Any] = {
        "schema_version": EVIDENCE_CARD_SCHEMA_VERSION,
        "decision": {
            "action": recommendation.get("action"),
            "action_detail": recommendation.get("action_detail"),
            "confidence": recommendation.get("confidence"),
            "domain": recommendation.get("domain"),
        },
        "evidence": {
            "uncertainty": list(recommendation.get("uncertainty") or []),
            "rationale": list(recommendation.get("rationale") or []),
        },
        "provenance": {
            "accepted_state_rows": list(accepted_state_rows or []),
            "raw_source_refs": list(raw_source_refs or []),
            "proposal_log": list(proposal_log_ids or []),
            "planned_recommendation": list(planned_ids or []),
            "recommendation_log": list(recommendation_log_ids or []),
            "x_rule_firing": list(x_rule_firing_ids or []),
            "data_quality_daily": list(data_quality_daily or []),
        },
    }
    validate_evidence_card_payload(payload)
    return payload


def project_evidence_card(
    conn: sqlite3.Connection,
    *,
    card_id: str,
    daily_plan_id: str,
    recommendation_id: str,
    user_id: str,
    for_date: str,
    domain: str,
    payload: dict[str, Any],
    planned_id: Optional[str] = None,
    proposal_id: Optional[str] = None,
    source: str = "claude_agent_v1",
    ingest_actor: str = "claude_agent_v1",
    agent_version: Optional[str] = None,
    computed_at: Optional[str] = None,
    commit_after: bool = True,
) -> None:
    """Insert a ``recommendation_evidence_card`` row.

    The ``payload`` dict is validated against the ``v1`` schema before
    insert; an invalid payload raises
    :class:`EvidenceCardValidationError` and the synthesis transaction
    rolls back, never persisting a partial card.
    """

    validate_evidence_card_payload(payload)
    conn.execute(
        """
        INSERT INTO recommendation_evidence_card (
            card_id, daily_plan_id, recommendation_id, planned_id,
            proposal_id, user_id, for_date, domain,
            schema_version, payload_json, computed_at,
            source, ingest_actor, agent_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            card_id,
            daily_plan_id,
            recommendation_id,
            planned_id,
            proposal_id,
            user_id,
            for_date,
            domain,
            EVIDENCE_CARD_SCHEMA_VERSION,
            json.dumps(payload, sort_keys=True),
            computed_at or _now_iso(),
            source,
            ingest_actor,
            agent_version,
        ),
    )
    if commit_after:
        conn.commit()
