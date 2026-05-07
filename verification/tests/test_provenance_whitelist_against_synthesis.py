"""W-PROV-2 whitelist introspection regression — guard against drift
between ``core/provenance/locator.py:_ALLOWED_TABLES_PK`` and
``core/synthesis.py:_ACCEPTED_STATE_TABLES``.

PLAN §2.A acceptance #5 + #6 + F-PHASE0-12. The two private constants
encode the same architectural invariant (the set of accepted-state
tables across the six domains) and must agree. F-PLAN-01 caught a
non-existent ``accepted_strength_state_daily`` table name in PLAN
authoring before this regression existed; the goal here is that no
future drift can land silently.

Also asserts the negative side of the W-PROV-1 contract: no write-side
audit-chain table is permitted in the whitelist.
"""

from __future__ import annotations

import pytest

from health_agent_infra.core.provenance.locator import (
    LocatorValidationError,
    _ALLOWED_TABLES_PK,
    validate_locator,
)
from health_agent_infra.core.synthesis import _ACCEPTED_STATE_TABLES


# ---------------------------------------------------------------------------
# Positive: every accepted-state table in synthesis is whitelisted with
# the canonical (as_of_date, user_id) PK shape.
# ---------------------------------------------------------------------------


def test_every_accepted_state_table_is_whitelisted():
    expected = {table for (table, _domain) in _ACCEPTED_STATE_TABLES}
    whitelisted_accepted = {
        t for t in _ALLOWED_TABLES_PK if t.startswith("accepted_")
    }
    missing = expected - whitelisted_accepted
    extra = whitelisted_accepted - expected
    assert not missing, (
        f"_ACCEPTED_STATE_TABLES contains {sorted(missing)} not present "
        f"in _ALLOWED_TABLES_PK; W-PROV-2 whitelist is missing entries"
    )
    assert not extra, (
        f"_ALLOWED_TABLES_PK contains accepted_* tables {sorted(extra)} "
        f"not declared in _ACCEPTED_STATE_TABLES; whitelist drift"
    )


def test_accepted_state_tables_use_canonical_pk_shape():
    canonical_pk = ("as_of_date", "user_id")
    for table, _domain in _ACCEPTED_STATE_TABLES:
        actual = _ALLOWED_TABLES_PK[table]
        assert actual == canonical_pk, (
            f"{table!r} PK is {actual}, expected {canonical_pk}; "
            f"the W-PROV-2 emission paths assume the canonical shape"
        )


# ---------------------------------------------------------------------------
# Negative: no write-side audit-chain table is permitted in the whitelist.
# Self-citation is meaningless and a classification bug per
# source_row_provenance.md:42-46. Audit-chain refs belong in evidence-card
# payload, NOT in SourceRowLocator instances.
# ---------------------------------------------------------------------------


_FORBIDDEN_AUDIT_CHAIN_TABLES = (
    "recommendation_log",
    "proposal_log",
    "daily_plan",
    "planned_recommendation",
    "intent_item",
    "target",
    "x_rule_firing",
    "review_outcome",
    "review_event",
    "data_quality_daily",
    "runtime_event_log",
    "sync_run_log",
)


@pytest.mark.parametrize("table", _FORBIDDEN_AUDIT_CHAIN_TABLES)
def test_audit_chain_table_is_not_whitelisted(table: str) -> None:
    assert table not in _ALLOWED_TABLES_PK, (
        f"{table!r} is a write-side audit-chain table; the W-PROV-1 "
        f"contract forbids it from the locator whitelist. Audit-chain "
        f"references belong in evidence-card payload lanes "
        f"(W-EVCARD-DAILY / W-EVCARD-WEEKLY), not in SourceRowLocator."
    )


@pytest.mark.parametrize("table", _FORBIDDEN_AUDIT_CHAIN_TABLES)
def test_validate_locator_rejects_audit_chain_table(table: str) -> None:
    bad = {
        "table": table,
        "pk": {"id": "x"},
        "row_version": "2026-05-07T00:00:00Z",
    }
    with pytest.raises(LocatorValidationError) as exc_info:
        validate_locator(bad)
    assert exc_info.value.invariant == "table_whitelist", (
        f"validate_locator rejected {table!r} but on the wrong invariant: "
        f"{exc_info.value.invariant!r}"
    )
