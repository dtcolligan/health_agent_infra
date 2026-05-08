"""LLM-judge harness scaffold (v0.1.14 W-AJ).

**Scope.** Define the invocation interface that v0.2.2 W58J's actual
LLM-as-judge implementation will plug into. No model is invoked in
v0.1.14. The reference implementation here is ``NoOpJudge``, which
returns deterministic stub responses.

**Why pre-staged.** v0.2.2 W58J ships an LLM judge that runs in
*shadow* mode (logs decisions but doesn't block). Before that, we
need the surrounding code (eval runner, claim block, weekly review)
to be aware of the judge's existence. v0.1.14 adds the type seam;
v0.2.2 adds the model.

**Bias-aware.** v0.2.2 also lands W-JUDGE-BIAS (CALM-style bias
panel per Ye et al. 2025 ICLR — `Justice or Prejudice? Quantifying
Biases in LLM-as-a-Judge`). The interface here pre-allocates a
``bias_panel_results`` field on ``JudgeResponse`` so v0.2.2 doesn't
have to migrate consumers; today the field is always empty.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


JudgeVerdict = str  # "supported" | "unsupported" | "ambiguous" | "skipped"

VALID_VERDICTS: frozenset[JudgeVerdict] = frozenset(
    {"supported", "unsupported", "ambiguous", "skipped"}
)


@dataclass(frozen=True)
class JudgeRequest:
    """Input to the judge: a single atomic claim + its evidence.

    Per W-AL `core/eval/calibration_schema.py` decomposition: a
    weekly-review (or ad-hoc) prose passage is decomposed into atomic
    claims; each atomic claim becomes one ``JudgeRequest``.
    """

    claim_id: str
    """Stable identifier for the claim being judged."""

    claim_text: str
    """The atomic-claim prose, e.g. 'Resting HR was 67 bpm on
    2026-04-30.'"""

    evidence_locators: list[dict[str, Any]] = field(default_factory=list)
    """W-PROV-1 source-row locators that should support the claim.
    Empty list means the claim is unsupported by construction."""

    context: dict[str, Any] = field(default_factory=dict)
    """Optional extra context (user goal, surrounding prose, etc.).
    Implementation-defined; ``NoOpJudge`` ignores it."""


@dataclass(frozen=True)
class JudgeResponse:
    """Output of the judge for one ``JudgeRequest``."""

    claim_id: str
    verdict: JudgeVerdict
    """One of VALID_VERDICTS."""

    confidence: float
    """[0.0, 1.0]. Implementation-defined semantics; ``NoOpJudge``
    returns 0.0 (no confidence because no model ran)."""

    rationale: str
    """Free-text explanation of the verdict. Empty for skipped."""

    invoked_at: str
    """ISO-8601 UTC timestamp of when the judge was called."""

    model_id: Optional[str] = None
    """Identifier of the underlying model. ``NoOpJudge`` uses
    ``"noop"``; v0.2.2 W58J will use a real model id like
    ``"claude-haiku-4-5-20251001"``."""

    bias_panel_results: list[dict[str, Any]] = field(default_factory=list)
    """W-JUDGE-BIAS pre-allocation. Each entry is one bias-probe
    result: ``{probe_id, axis, score, ...}``. Empty in v0.1.14."""


class JudgeHarness(ABC):
    """Abstract base. v0.2.2 W58J's real model-backed judge subclasses
    this. v0.1.14 ships ``NoOpJudge`` as the reference shape.

    Implementations must be **stateless** with respect to the model
    backend (no in-flight request retained across `judge` calls). If
    a backend needs auth / pooling, hold those resources on the
    instance, not on the call.
    """

    @abstractmethod
    def judge(self, request: JudgeRequest) -> JudgeResponse:
        """Evaluate a single atomic claim. Always returns a response;
        on internal error, return a ``skipped`` verdict with the error
        in ``rationale``."""

    def judge_batch(
        self, requests: list[JudgeRequest]
    ) -> list[JudgeResponse]:
        """Default implementation: serial calls. Subclasses MAY
        override to batch the model invocation (v0.2.2 W58J probably
        will)."""

        return [self.judge(req) for req in requests]


class NoOpJudge(JudgeHarness):
    """Reference implementation. Returns deterministic stub responses.

    **Verdict policy.** A request with at least one ``evidence_locator``
    returns ``ambiguous`` (we can't tell without a model); zero
    locators returns ``unsupported`` (deterministic — no evidence
    means unsupported). ``confidence`` is always 0.0 because no
    actual judgement happened.

    The eval substrate uses this in v0.1.14 to verify the harness
    surface end-to-end (request schema, response schema, ``judge_batch``
    plumbing) without committing to a model.
    """

    MODEL_ID = "noop"

    def judge(self, request: JudgeRequest) -> JudgeResponse:
        if not request.evidence_locators:
            verdict: JudgeVerdict = "unsupported"
            rationale = (
                "no evidence_locators supplied; judge cannot evaluate"
            )
        else:
            verdict = "ambiguous"
            rationale = (
                "NoOpJudge returns ambiguous on locator-bearing claims; "
                "v0.2.2 W58J replaces this with model-backed evaluation"
            )
        return JudgeResponse(
            claim_id=request.claim_id,
            verdict=verdict,
            confidence=0.0,
            rationale=rationale,
            invoked_at=datetime.now(timezone.utc).isoformat(),
            model_id=self.MODEL_ID,
            bias_panel_results=[],
        )
