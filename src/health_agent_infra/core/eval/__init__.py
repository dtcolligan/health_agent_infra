"""Eval substrate (v0.1.14 W-AJ + W-AL; v0.2.0 W-FACT-ATOM).

W-AJ: LLM-judge harness scaffold (`judge_harness.py`).
  Stable invocation interface for v0.2.2 W58J to plug into.
  No model invocation in v0.1.14; the reference implementation is
  ``NoOpJudge`` which returns deterministic stubs.

W-AL: Calibration eval schema (`calibration_schema.py`).
  FActScore-aware atomic-claim decomposition. Schema/report-shape
  only in v0.1.14; correlation work deferred to v0.5+ per
  reconciliation A2.

W-FACT-ATOM (v0.2.0): Atomic-claim parser (`atomic_claims.py`).
  Structural inverse of ``core/review/render.py`` — recovers
  ``(atom_text, atom_type, derivation_path)`` triples from W52's
  rendered markdown deterministically. Provides W58D's deterministic
  factuality gate with its parsed-claim input.
"""

from health_agent_infra.core.eval.atomic_claims import (
    TypedAtom,
    classify_atom_type,
    derivation_path_for,
    parse_atoms_from_markdown,
)
from health_agent_infra.core.eval.calibration_schema import (
    AtomicClaim,
    CalibrationReport,
    CalibrationSchemaError,
    decompose_into_atomic_claims,
    validate_calibration_report,
)
from health_agent_infra.core.eval.judge_harness import (
    JudgeHarness,
    JudgeRequest,
    JudgeResponse,
    JudgeVerdict,
    NoOpJudge,
)


__all__ = [
    "AtomicClaim",
    "CalibrationReport",
    "CalibrationSchemaError",
    "JudgeHarness",
    "JudgeRequest",
    "JudgeResponse",
    "JudgeVerdict",
    "NoOpJudge",
    "TypedAtom",
    "classify_atom_type",
    "decompose_into_atomic_claims",
    "derivation_path_for",
    "parse_atoms_from_markdown",
    "validate_calibration_report",
]
