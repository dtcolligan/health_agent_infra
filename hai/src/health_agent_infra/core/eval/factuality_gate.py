"""Deterministic factuality gate — W58D (v0.2.0 §2.F).

PLAN §2.F gate logic. For each atomic claim from W-FACT-ATOM:

  1. If atom_type ∈ {quantitative, comparative}:
       a. Resolve atom to a (claim_id, locator_set, audit_refs,
          user_id) tuple.
       b. For each locator: assert locator validates per W-PROV-1
          AND the resolved row exists at the cited row_version.
       c. For each audit_ref: assert the referenced primary key
          exists in the cited audit-chain table.
       d. For each ``x_rule_firing`` audit_ref (when ``user_id`` is
          set): assert the firing_id is NOT in any of that user's
          ``review_outcome.disagreed_firing_ids`` lists. The user
          explicitly marking a firing as "I don't think this rule
          should have fired" is a structural disagreement; a claim
          citing such a firing is a known-stale fact.
       e. If any locator, audit_ref, or x-rule-conflict check fails:
          BLOCK.
       f. If all resolve: PASS the atom.
  2. If atom_type == qualitative: pass through (gate does not
     validate — these are framing / disposition prose with no
     factual past-week content per F-PLAN-10).
  3. Aggregate: weekly review render is BLOCKED if any atom is
     blocked.

Two-lane provenance per F-PHASE0-12 + F-PLAN-12:
  * **Source-row locators** are read-side evidence/accepted-state
    pointers validated via the W-PROV-1 contract
    (``core/provenance/locator.py``).
  * **Audit-chain refs** are write-side primary keys in the
    audit-chain tables (daily_plan, recommendation_log, proposal_log,
    x_rule_firing, runtime_event_log, sync_run_log) validated by
    plain PK existence query.

The two lanes are intentionally separate — the locator whitelist
explicitly excludes audit-chain tables (locator.py:21-26), and the
audit-chain whitelist below explicitly excludes accepted-state
tables. Mixing them would let a write-side PK be cited as a
"locator" or vice versa, breaking the provenance contract.

Step 1 ships the gate logic skeleton. Tests are synthetic
in-memory atoms covering the four block reasons + the qualitative
SKIP path. Step 6 wires the gate to the real corpus
(``evals/scenarios/factuality/``).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from health_agent_infra.core.provenance.locator import (
    _ROW_VERSION_COLUMN,
    LocatorValidationError,
    resolve_locator,
    validate_locator,
)


# ---------------------------------------------------------------------------
# Audit-chain table whitelist
# ---------------------------------------------------------------------------


_AUDIT_CHAIN_TABLES_PK: dict[str, str] = {
    "daily_plan": "daily_plan_id",
    "recommendation_log": "recommendation_id",
    "proposal_log": "proposal_id",
    "x_rule_firing": "firing_id",
    "runtime_event_log": "event_id",
    "sync_run_log": "sync_id",
}
"""Audit-chain tables with their single-column primary keys.

Distinct from W-PROV-1's locator whitelist
(``core/provenance/locator.py:_ALLOWED_TABLES_PK``) — locator entries
are read-side evidence/accepted-state tables; audit-chain entries
are write-side mutation logs. F-PHASE0-12 + F-PLAN-12 name the
two-lane separation invariant. Adding a new audit-chain table here
without also gating it through the audit-chain consumer requires
PLAN approval.
"""


# ---------------------------------------------------------------------------
# Outcome enums
# ---------------------------------------------------------------------------


class GateOutcome(str, Enum):
    """Per-claim gate outcome."""

    PASS = "pass"
    BLOCK = "block"
    SKIP = "skip"  # qualitative atoms — gate does not validate


class BlockReason(str, Enum):
    """Why a claim was blocked. Matches PLAN §2.F sub-categories
    (modulo the two W58D-specific additions ``LOCATOR_ROW_VERSION_DRIFT``
    and ``AUDIT_REF_ORPHAN``)."""

    LOCATOR_INVALID = "locator_invalid"
    """Locator dict is malformed (table not in whitelist, pk shape
    wrong, missing required field, etc.). Detected by
    :func:`validate_locator`."""

    LOCATOR_ROW_MISSING = "locator_row_missing"
    """Locator validates but the row at its primary key no longer
    exists in the cited table — typically a deletion or a rebuild."""

    LOCATOR_ROW_VERSION_DRIFT = "locator_row_version_drift"
    """Locator validates and the row exists, but the row's current
    ``row_version`` column does not match the cited row_version
    (PLAN §2.F sub-category 4: source-row drift / supersession)."""

    SOURCE_SIGNAL_CONFLICT = "source_signal_conflict"
    """Locator cites a ``column`` whose value is missing or NULL on
    the resolved row (PLAN §2.F sub-category 3). Two sub-cases:
      * Column does not exist on the row schema (cited column was
        renamed or never existed).
      * Column exists but the value is NULL (the source signal the
        atom claims to draw from is absent).
    Both are deterministic detectors — the column either is or isn't
    on the row, and its value either is or isn't NULL."""

    AUDIT_REF_ORPHAN = "audit_ref_orphan"
    """Audit-chain primary key is not present in its cited table
    (PLAN §2.F sub-category 5)."""

    X_RULE_CONFLICT_USER_DISAGREED = "x_rule_conflict_user_disagreed"
    """Audit_ref to an ``x_rule_firing`` whose firing_id appears in
    the cited user's ``review_outcome.disagreed_firing_ids`` list
    (PLAN §2.F sub-category 2). The user explicitly marked the rule
    as "should not have fired" — a claim citing it is a known-stale
    fact even though the firing_id resolves to a real row."""

    UNKNOWN_ATOM_TYPE = "unknown_atom_type"
    """Atom type is not in {quantitative, comparative, qualitative}.
    Fail-closed default (defensive: bad atoms shouldn't reach the
    gate, but we don't silently pass them if they do)."""


# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClaimGateInput:
    """One claim's input to the gate.

    ``atom_text`` + ``atom_type`` are the structural identity (also
    pinned by W-FACT-ATOM). ``locator_set`` + ``audit_refs`` are the
    provenance the gate validates. ``claim_id`` is optional; when
    present it threads through into :class:`ClaimGateResult` so
    callers can correlate gate output with their input.

    ``user_id`` is required to exercise the
    :attr:`BlockReason.X_RULE_CONFLICT_USER_DISAGREED` lane (PLAN
    §2.F sub-category 2). Without ``user_id`` the gate skips the
    disagreement check — a structural choice consistent with v0.1.x
    callers that don't yet thread user identity through the eval
    surface.
    """

    atom_text: str
    atom_type: str
    locator_set: list[dict[str, Any]] = field(default_factory=list)
    audit_refs: dict[str, list[Any]] = field(default_factory=dict)
    claim_id: Optional[str] = None
    user_id: Optional[str] = None


@dataclass(frozen=True)
class ClaimGateResult:
    """Outcome of gating one claim. Carries enough detail for the
    weekly-review CLI to surface a blocked-atom error message
    naming the atom and the reason."""

    claim_id: Optional[str]
    atom_text: str
    atom_type: str
    outcome: GateOutcome
    block_reason: Optional[BlockReason] = None
    block_detail: Optional[str] = None


@dataclass(frozen=True)
class FactualityGateOutcome:
    """Aggregate outcome over a list of claim inputs.

    ``all_passed`` is the gate's bundle-level decision: BLOCKED if any
    quantitative or comparative atom failed to resolve, PASSED
    otherwise. Skipped (qualitative) atoms do not affect this
    decision.
    """

    results: list[ClaimGateResult]
    total: int
    passed: int
    blocked: int
    skipped: int

    @property
    def all_passed(self) -> bool:
        return self.blocked == 0

    def first_block(self) -> Optional[ClaimGateResult]:
        """Return the first blocked result, or None if all passed.

        Used by ``hai review weekly`` to format the stderr message
        when the gate blocks: the first block is the most actionable
        signal (gate stops at the first failure within an atom; the
        first failed atom is the one to surface)."""

        for r in self.results:
            if r.outcome == GateOutcome.BLOCK:
                return r
        return None


# ---------------------------------------------------------------------------
# Locator + audit-ref resolution
# ---------------------------------------------------------------------------


def _resolve_locator_with_drift(
    conn: sqlite3.Connection,
    locator: dict[str, Any],
) -> tuple[bool, Optional[BlockReason], Optional[str]]:
    """Validate + resolve a locator and check for ``row_version`` drift.

    Returns ``(ok, block_reason, detail)``. ``ok=True`` iff the
    locator validates, the row exists, AND (when the table has a
    canonical row-version column per ``locator._ROW_VERSION_COLUMN``)
    the cited ``row_version`` matches the current row's value at
    that column.

    The drift check resolves the comparison column per the
    ``_ROW_VERSION_COLUMN`` mapping rather than expecting the row
    to carry a literal ``row_version`` column. Real accepted-state
    rows expose ``projected_at``, not ``row_version``; the mapping
    makes that explicit so the drift lane fires against the real
    schema (v0.2.0 IR R1 F-IR-01 caught the prior bug where the
    drift check ran against ``row.get("row_version")``, returning
    ``None`` on real schema rows and silently passing every stale
    locator). Tables with no canonical row-version column (e.g.,
    ``source_daily_garmin`` today) skip the drift comparison and
    the locator passes once row resolution succeeds.

    PLAN §2.F sub-category 4 names the drift case as a separate
    block reason from row-missing so corpus authors can author both
    failure modes independently.
    """

    try:
        validate_locator(locator)
    except LocatorValidationError as e:
        return (
            False,
            BlockReason.LOCATOR_INVALID,
            f"{e.invariant}: {e}",
        )

    row = resolve_locator(conn, locator)
    if row is None:
        pk = locator.get("pk", {})
        return (
            False,
            BlockReason.LOCATOR_ROW_MISSING,
            f"row at pk {dict(pk)} no longer exists in "
            f"{locator['table']}",
        )

    cited_row_version = locator.get("row_version")
    row_version_col = _ROW_VERSION_COLUMN.get(locator["table"])
    actual_row_version = (
        row.get(row_version_col) if row_version_col is not None else None
    )
    if (
        cited_row_version is not None
        and actual_row_version is not None
        and cited_row_version != str(actual_row_version)
    ):
        return (
            False,
            BlockReason.LOCATOR_ROW_VERSION_DRIFT,
            f"cited row_version {cited_row_version!r} does not "
            f"match current {actual_row_version!r} on row "
            f"{dict(locator['pk'])} of {locator['table']}",
        )

    cited_column = locator.get("column")
    if cited_column is not None:
        if cited_column not in row:
            return (
                False,
                BlockReason.SOURCE_SIGNAL_CONFLICT,
                f"cited column {cited_column!r} not on row schema for "
                f"{locator['table']} (renamed or never existed)",
            )
        if row[cited_column] is None:
            return (
                False,
                BlockReason.SOURCE_SIGNAL_CONFLICT,
                f"cited column {cited_column!r} is NULL on row "
                f"{dict(locator['pk'])} of {locator['table']} — the "
                f"source signal the atom draws from is absent",
            )

    return (True, None, None)


def _check_x_rule_user_disagreement(
    conn: sqlite3.Connection,
    user_id: str,
    firing_id: Any,
) -> tuple[bool, Optional[BlockReason], Optional[str]]:
    """Check whether ``firing_id`` is in any of ``user_id``'s
    ``review_outcome.disagreed_firing_ids`` lists.

    Returns ``(ok, block_reason, detail)``. ``ok=True`` iff the
    firing is NOT in any disagreement list. The ``review_outcome``
    column is JSON-encoded TEXT (per migration 010); legacy NULL
    values mean "the disagreement question was never asked" and
    are treated as no-disagreement (``ok=True``).

    Comparison is string-equality after ``str()`` coercion on both
    sides — the ``firing_id`` typed as ``int`` in
    :class:`WeeklyXRuleFiring` may surface as either ``int`` or
    JSON-stringified ``str`` depending on the writer.
    """

    try:
        rows = conn.execute(
            "SELECT disagreed_firing_ids FROM review_outcome "
            "WHERE user_id = ? AND disagreed_firing_ids IS NOT NULL",
            (user_id,),
        ).fetchall()
    except sqlite3.OperationalError:
        # review_outcome table missing — treat as no-disagreement.
        # The gate is fail-closed on locator/audit-ref schemas, but
        # the disagreement signal is opt-in (a missing table means
        # the user has logged no outcomes, not that we should block).
        return (True, None, None)

    cited = str(firing_id)
    for row in rows:
        raw = row[0] if not hasattr(row, "keys") else row["disagreed_firing_ids"]
        if not raw:
            continue
        try:
            disagreed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(disagreed, list):
            continue
        if any(str(d) == cited for d in disagreed):
            return (
                False,
                BlockReason.X_RULE_CONFLICT_USER_DISAGREED,
                f"firing_id {firing_id!r} appears in user {user_id!r}'s "
                f"disagreed_firing_ids review_outcome history",
            )
    return (True, None, None)


def _resolve_audit_ref(
    conn: sqlite3.Connection,
    table: str,
    pk_value: Any,
) -> tuple[bool, Optional[BlockReason], Optional[str]]:
    """Verify that a primary key exists in an audit-chain table.

    Returns ``(ok, block_reason, detail)``. Fails closed if the table
    is not in the audit-chain whitelist or if the PK does not
    resolve. Operational errors (e.g., the table doesn't exist in
    this DB) also fail closed.
    """

    if table not in _AUDIT_CHAIN_TABLES_PK:
        return (
            False,
            BlockReason.AUDIT_REF_ORPHAN,
            f"audit-chain table {table!r} not in W58D whitelist "
            f"{sorted(_AUDIT_CHAIN_TABLES_PK)}",
        )

    pk_col = _AUDIT_CHAIN_TABLES_PK[table]
    try:
        row = conn.execute(
            f"SELECT 1 FROM {table} WHERE {pk_col} = ? LIMIT 1",  # nosec B608 — table from whitelist, pk_col is metadata-derived
            (pk_value,),
        ).fetchone()
    except sqlite3.OperationalError as e:
        return (
            False,
            BlockReason.AUDIT_REF_ORPHAN,
            f"audit-chain table {table!r} unavailable: {e}",
        )
    if row is None:
        return (
            False,
            BlockReason.AUDIT_REF_ORPHAN,
            f"audit-ref {pk_col}={pk_value!r} not found in {table}",
        )
    return (True, None, None)


# ---------------------------------------------------------------------------
# Per-claim gate
# ---------------------------------------------------------------------------


def gate_claim(
    conn: sqlite3.Connection,
    claim: ClaimGateInput,
) -> ClaimGateResult:
    """Gate one claim per PLAN §2.F gate logic.

    Qualitative atoms pass through (``GateOutcome.SKIP``). Quantitative
    + comparative atoms validate every locator + every audit_ref;
    the FIRST failure stops the gate and produces a BLOCK result with
    the appropriate :class:`BlockReason`. Vacuous claims (no
    locators, no audit_refs) pass — the cycle thesis lets the corpus
    author choose how strict the validation surface is by populating
    or omitting provenance.
    """

    if claim.atom_type == "qualitative":
        return ClaimGateResult(
            claim_id=claim.claim_id,
            atom_text=claim.atom_text,
            atom_type=claim.atom_type,
            outcome=GateOutcome.SKIP,
        )

    if claim.atom_type not in ("quantitative", "comparative"):
        return ClaimGateResult(
            claim_id=claim.claim_id,
            atom_text=claim.atom_text,
            atom_type=claim.atom_type,
            outcome=GateOutcome.BLOCK,
            block_reason=BlockReason.UNKNOWN_ATOM_TYPE,
            block_detail=f"unknown atom_type {claim.atom_type!r}",
        )

    for locator in claim.locator_set:
        ok, reason, detail = _resolve_locator_with_drift(conn, locator)
        if not ok:
            return ClaimGateResult(
                claim_id=claim.claim_id,
                atom_text=claim.atom_text,
                atom_type=claim.atom_type,
                outcome=GateOutcome.BLOCK,
                block_reason=reason,
                block_detail=detail,
            )

    for table, pks in claim.audit_refs.items():
        for pk in pks:
            ok, reason, detail = _resolve_audit_ref(conn, table, pk)
            if not ok:
                return ClaimGateResult(
                    claim_id=claim.claim_id,
                    atom_text=claim.atom_text,
                    atom_type=claim.atom_type,
                    outcome=GateOutcome.BLOCK,
                    block_reason=reason,
                    block_detail=detail,
                )
            # X-rule-conflict lane (PLAN §2.F sub-category 2): only
            # firings the user has explicitly disagreed with are
            # blocked here. Requires ``user_id`` on the claim; absent
            # it, the lane is a no-op (the structural check needs a
            # user identity to look up the disagreement history).
            if (
                table == "x_rule_firing"
                and claim.user_id is not None
            ):
                ok2, reason2, detail2 = _check_x_rule_user_disagreement(
                    conn, claim.user_id, pk,
                )
                if not ok2:
                    return ClaimGateResult(
                        claim_id=claim.claim_id,
                        atom_text=claim.atom_text,
                        atom_type=claim.atom_type,
                        outcome=GateOutcome.BLOCK,
                        block_reason=reason2,
                        block_detail=detail2,
                    )

    return ClaimGateResult(
        claim_id=claim.claim_id,
        atom_text=claim.atom_text,
        atom_type=claim.atom_type,
        outcome=GateOutcome.PASS,
    )


# ---------------------------------------------------------------------------
# Bundle-level gate
# ---------------------------------------------------------------------------


def run_factuality_gate(
    conn: sqlite3.Connection,
    claims: list[ClaimGateInput],
) -> FactualityGateOutcome:
    """Gate a list of claims and aggregate the result.

    Per PLAN §2.F gate logic step 8: the bundle-level outcome
    blocks if any atom blocks. Skipped (qualitative) atoms do not
    affect the bundle-level decision.
    """

    results = [gate_claim(conn, c) for c in claims]
    passed = sum(1 for r in results if r.outcome == GateOutcome.PASS)
    blocked = sum(1 for r in results if r.outcome == GateOutcome.BLOCK)
    skipped = sum(1 for r in results if r.outcome == GateOutcome.SKIP)
    return FactualityGateOutcome(
        results=results,
        total=len(results),
        passed=passed,
        blocked=blocked,
        skipped=skipped,
    )
