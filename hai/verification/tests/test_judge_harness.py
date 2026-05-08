"""W-AJ + W-AL substrate tests (v0.1.14).

Pin the invocation interface and calibration schema. v0.2.2 W58J
inherits these contracts; this test catches any drift.
"""

from __future__ import annotations

import pytest

from health_agent_infra.core.eval import (
    AtomicClaim,
    CalibrationReport,
    CalibrationSchemaError,
    JudgeRequest,
    JudgeResponse,
    NoOpJudge,
    decompose_into_atomic_claims,
    validate_calibration_report,
)
from health_agent_infra.core.eval.judge_harness import VALID_VERDICTS


# ---------------------------------------------------------------------------
# W-AJ — judge harness invocation interface
# ---------------------------------------------------------------------------

def test_noop_judge_returns_unsupported_when_no_locators():
    judge = NoOpJudge()
    req = JudgeRequest(
        claim_id="c1",
        claim_text="Resting HR was elevated.",
        evidence_locators=[],
    )
    resp = judge.judge(req)
    assert resp.claim_id == "c1"
    assert resp.verdict == "unsupported"
    assert resp.confidence == 0.0
    assert resp.model_id == "noop"
    assert resp.bias_panel_results == []


def test_noop_judge_returns_ambiguous_when_locators_present():
    judge = NoOpJudge()
    req = JudgeRequest(
        claim_id="c2",
        claim_text="Resting HR was 67 bpm on 2026-04-30.",
        evidence_locators=[
            {
                "table": "accepted_recovery_state_daily",
                "pk": {"as_of_date": "2026-04-30", "user_id": "u_local_1"},
                "column": "resting_hr",
                "row_version": "2026-04-30T19:26:05Z",
            }
        ],
    )
    resp = judge.judge(req)
    assert resp.verdict == "ambiguous"
    assert "v0.2.2" in resp.rationale  # surfaces the upgrade path


def test_noop_judge_batch_returns_one_response_per_request():
    judge = NoOpJudge()
    reqs = [
        JudgeRequest(claim_id=f"c{i}", claim_text="x", evidence_locators=[])
        for i in range(5)
    ]
    resps = judge.judge_batch(reqs)
    assert len(resps) == 5
    assert {r.claim_id for r in resps} == {f"c{i}" for i in range(5)}
    for r in resps:
        assert r.verdict in VALID_VERDICTS


def test_judge_response_has_bias_panel_field_pre_allocated():
    """v0.2.2 W-JUDGE-BIAS pre-allocates the field; v0.1.14 leaves it
    empty but the attribute must exist."""

    judge = NoOpJudge()
    resp = judge.judge(JudgeRequest(claim_id="c", claim_text="x", evidence_locators=[]))
    assert hasattr(resp, "bias_panel_results")
    assert resp.bias_panel_results == []


# ---------------------------------------------------------------------------
# W-AL — calibration schema + decomposer
# ---------------------------------------------------------------------------

def test_decompose_handles_single_sentence():
    claims = decompose_into_atomic_claims(
        "Resting HR was 67 bpm.", prose_id="p"
    )
    assert len(claims) == 1
    assert claims[0].text == "Resting HR was 67 bpm."
    assert claims[0].claim_id == "p_atom_000"


def test_decompose_handles_multiple_sentences():
    prose = "HR was 67. HRV was 50. Sleep was 7 hours."
    claims = decompose_into_atomic_claims(prose, prose_id="p")
    assert len(claims) == 3
    assert claims[0].text.startswith("HR was 67")
    assert claims[2].text.startswith("Sleep was 7 hours")


def test_decompose_handles_question_marks_and_exclamations():
    claims = decompose_into_atomic_claims(
        "Did HR rise? Yes! And HRV fell.", prose_id="p"
    )
    assert len(claims) == 3


def test_decompose_handles_empty_prose():
    assert decompose_into_atomic_claims("", prose_id="p") == []
    assert decompose_into_atomic_claims("   \n\n  ", prose_id="p") == []


def test_decompose_attaches_no_locators_in_v0_1_14():
    """v0.1.14 W-AL is schema-only; no semantic decomposition + no
    locator attachment. v0.2.0 W-FACT-ATOM owns the smarter shape."""

    claims = decompose_into_atomic_claims(
        "HR was 67. HRV was 50.", prose_id="p"
    )
    for c in claims:
        assert c.evidence_locators == []


def test_calibration_report_to_dict_roundtrips():
    report = CalibrationReport(
        prose_id="weekly_2026-W17",
        source_prose="HR was 67.",
        atomic_claims=[
            AtomicClaim(
                claim_id="weekly_2026-W17_atom_000",
                text="HR was 67.",
                span=(0, 11),
                evidence_locators=[],
            )
        ],
    )
    d = report.to_dict()
    assert d["schema_version"] == "calibration_report.v1"
    assert d["prose_id"] == "weekly_2026-W17"
    assert len(d["atomic_claims"]) == 1
    assert d["atomic_claims"][0]["text"] == "HR was 67."


def test_validate_calibration_report_rejects_unknown_schema_version():
    bad = {
        "schema_version": "calibration_report.v999",
        "prose_id": "p",
        "source_prose": "x",
        "atomic_claims": [],
    }
    with pytest.raises(CalibrationSchemaError) as exc_info:
        validate_calibration_report(bad)
    assert exc_info.value.invariant == "schema_version"


def test_validate_calibration_report_rejects_missing_required_field():
    bad = {
        "schema_version": "calibration_report.v1",
        "prose_id": "p",
        # source_prose missing
        "atomic_claims": [],
    }
    with pytest.raises(CalibrationSchemaError) as exc_info:
        validate_calibration_report(bad)
    assert exc_info.value.invariant == "required_fields"


def test_validate_calibration_report_rejects_malformed_claim():
    bad = {
        "schema_version": "calibration_report.v1",
        "prose_id": "p",
        "source_prose": "x",
        "atomic_claims": [{"claim_id": "c"}],  # missing text/span
    }
    with pytest.raises(CalibrationSchemaError) as exc_info:
        validate_calibration_report(bad)
    assert exc_info.value.invariant == "claim_field"
