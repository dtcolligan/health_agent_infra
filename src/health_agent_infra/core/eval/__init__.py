"""Eval substrate (v0.1.14 W-AJ + W-AL).

W-AJ: LLM-judge harness scaffold (`judge_harness.py`).
  Stable invocation interface for v0.2.2 W58J to plug into.
  No model invocation in v0.1.14; the reference implementation is
  ``NoOpJudge`` which returns deterministic stubs.

W-AL: Calibration eval schema (`calibration_schema.py`).
  FActScore-aware atomic-claim decomposition. Schema/report-shape
  only in v0.1.14; correlation work deferred to v0.5+ per
  reconciliation A2.
"""

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
    "decompose_into_atomic_claims",
    "validate_calibration_report",
]
