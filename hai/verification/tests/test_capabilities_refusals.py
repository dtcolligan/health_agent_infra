"""WP-MAN-003: refusal taxonomy in capabilities manifest."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

from health_agent_infra.cli import main as cli_main


_REFUSAL_TRIGGER_TESTS = {
    "clinical_claim": "hai/verification/tests/test_refusal_clinical.py",
    "agent_safe_violation": "hai/verification/tests/test_dispatch_agent_safe.py",
}


def _manifest() -> dict[str, object]:
    out = io.StringIO()
    with redirect_stdout(out):
        rc = cli_main(["capabilities", "--json"])
    assert rc == 0
    return json.loads(out.getvalue())


def test_refusals_taxonomy_lists_real_runtime_envelopes() -> None:
    refusals = _manifest()["refusals"]
    by_kind = {row["kind"]: row for row in refusals}

    assert set(by_kind) == {"clinical_claim", "agent_safe_violation"}
    assert by_kind["clinical_claim"]["mechanism"] == "refusal"
    assert (
        by_kind["clinical_claim"]["trigger"]
        == "diagnosis/treatment/prescribing/autonomous medical decision content "
        "in command output"
    )
    assert by_kind["agent_safe_violation"]["mechanism"] == "agent_safe"
    assert (
        by_kind["agent_safe_violation"]["trigger"]
        == "agent-classified caller invoking an agent_safe=false command"
    )
    for row in refusals:
        assert row["envelope_shape_ref"] == "schemas/refusal_envelope.v1.json"


def test_every_refusal_kind_has_trigger_test_registered() -> None:
    kinds = {row["kind"] for row in _manifest()["refusals"]}

    assert kinds == set(_REFUSAL_TRIGGER_TESTS)
    for path in _REFUSAL_TRIGGER_TESTS.values():
        assert path
