"""Calibration-eval schema (v0.1.14 W-AL).

**Scope.** Schema + report-shape only. Per reconciliation A2,
correlation work between calibrated outputs and outcomes is
deferred to v0.5+.

**Origin.** FActScore (Min et al. 2023) introduced atomic-claim
decomposition for factuality scoring; MedHallu (2024) adapted it
to clinical text. v0.2.0 W58D consumes this schema for the
deterministic claim block; v0.2.2 W58J consumes it for the LLM
judge harness.

**v0.1.14 deliverable.** Two types (``AtomicClaim``, ``CalibrationReport``)
plus a stub decomposer that splits prose on sentence boundaries.
The real semantic decomposition lands in v0.2.0 W-FACT-ATOM (which
folds into W58D); this module just pins the schema so the
surrounding code can be written.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


class CalibrationSchemaError(ValueError):
    """Raised when a calibration report violates the schema contract."""

    def __init__(self, invariant: str, message: str) -> None:
        super().__init__(message)
        self.invariant = invariant


@dataclass(frozen=True)
class AtomicClaim:
    """A single atomic claim extracted from a longer prose passage.

    FActScore-style: each claim is a self-contained assertion that
    can be true or false independently of the others. v0.2.0 W-FACT-ATOM
    will replace the v0.1.14 stub decomposer with a semantically-aware
    extractor.
    """

    claim_id: str
    """Stable identifier; v0.1.14 uses ``<prose_id>_atom_<index>``."""

    text: str
    """The atomic claim text."""

    span: tuple[int, int]
    """Character span ``(start, end)`` into the source prose. Inclusive
    start, exclusive end (Python slice semantics)."""

    evidence_locators: list[dict[str, Any]] = field(default_factory=list)
    """W-PROV-1 source-row locators supporting the claim. Empty list
    means the claim has no associated evidence — v0.2.0 W58D will
    block such claims in factuality-gated prose."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "span": list(self.span),
            "evidence_locators": list(self.evidence_locators),
        }


@dataclass(frozen=True)
class CalibrationReport:
    """One run of the calibration eval over a prose passage."""

    prose_id: str
    """Identifier of the source prose (e.g., ``weekly_2026-W17_user_local_1``)."""

    source_prose: str
    """Verbatim source text the report was computed against."""

    atomic_claims: list[AtomicClaim]
    """The decomposed claims."""

    judge_verdicts: list[dict[str, Any]] = field(default_factory=list)
    """v0.2.2 W58J judge response per atomic claim. Empty in v0.1.14
    (no judge runs); the field is pre-allocated so v0.2.2 doesn't
    have to migrate consumers."""

    aggregate_score: float = 0.0
    """[0.0, 1.0] aggregate factuality score over the claims. v0.1.14
    is always 0.0 (no judge ran). v0.2.2 W58J populates this from
    the per-claim verdicts."""

    schema_version: str = "calibration_report.v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "prose_id": self.prose_id,
            "source_prose": self.source_prose,
            "atomic_claims": [c.to_dict() for c in self.atomic_claims],
            "judge_verdicts": list(self.judge_verdicts),
            "aggregate_score": self.aggregate_score,
        }


def validate_calibration_report(d: Any) -> None:
    """Validate a calibration-report dict against the schema contract."""

    if not isinstance(d, dict):
        raise CalibrationSchemaError(
            "shape", f"report must be dict; got {type(d).__name__}"
        )
    required = {
        "schema_version", "prose_id", "source_prose", "atomic_claims",
    }
    missing = required - set(d.keys())
    if missing:
        raise CalibrationSchemaError(
            "required_fields", f"missing: {sorted(missing)}"
        )
    if d["schema_version"] != "calibration_report.v1":
        raise CalibrationSchemaError(
            "schema_version",
            f"unknown schema_version {d['schema_version']!r}",
        )
    if not isinstance(d["atomic_claims"], list):
        raise CalibrationSchemaError(
            "atomic_claims_list", "atomic_claims must be list"
        )
    for idx, claim in enumerate(d["atomic_claims"]):
        if not isinstance(claim, dict):
            raise CalibrationSchemaError(
                "claim_shape", f"atomic_claims[{idx}] must be dict"
            )
        for f in ("claim_id", "text", "span"):
            if f not in claim:
                raise CalibrationSchemaError(
                    "claim_field",
                    f"atomic_claims[{idx}] missing {f!r}",
                )


def decompose_into_atomic_claims(
    prose: str,
    *,
    prose_id: str,
) -> list[AtomicClaim]:
    """Stub decomposer — splits on sentence boundaries.

    v0.1.14 ships this as the reference implementation; v0.2.0
    W-FACT-ATOM replaces it with a semantically-aware extractor
    (FActScore-style atomic-claim splitting that handles compound
    sentences, anaphora, and unit-bearing numerics).

    For now: split on ``.``, ``?``, ``!`` (with whitespace), filter
    empties, return one claim per sentence with no evidence locators.
    """

    if not prose.strip():
        return []

    # Track character spans as we split.
    out: list[AtomicClaim] = []
    pos = 0
    sentence_idx = 0
    for match in re.finditer(r"[^.!?]+[.!?]+\s*", prose):
        text = match.group(0).strip()
        if not text:
            pos = match.end()
            continue
        start = prose.find(text, pos)
        if start == -1:
            pos = match.end()
            continue
        end = start + len(text)
        out.append(
            AtomicClaim(
                claim_id=f"{prose_id}_atom_{sentence_idx:03d}",
                text=text,
                span=(start, end),
                evidence_locators=[],
            )
        )
        pos = end
        sentence_idx += 1

    # Tail without trailing punctuation.
    tail = prose[pos:].strip()
    if tail:
        start = prose.rfind(tail)
        if start == -1:
            start = pos
        end = start + len(tail)
        out.append(
            AtomicClaim(
                claim_id=f"{prose_id}_atom_{sentence_idx:03d}",
                text=tail,
                span=(start, end),
                evidence_locators=[],
            )
        )

    return out
