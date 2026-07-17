"""Offline tests for the powered-run driver (roster_v4 + fireworks factory).

No network: a fake transport returns canned Fireworks responses. Confirms the
factory sends the LIVE deployment-qualified wire model and maps provider
responses/refusals to the right ModelTurnResult, and that roster_v4 forms the
within-family capability pairs that break the confound.
"""

from __future__ import annotations

import pytest

from governed_agent_bench.harness.core import load_task
from governed_agent_bench.harness.retry import OutageDetector
from governed_agent_bench.scripts.powered_run import make_fireworks_model_turn_factory
from governed_agent_bench.scripts.powered_run_roster import (
    ANCHOR_CONDITIONS,
    anchor_by_id,
    band_family_index,
)

_WIRE = "accounts/dtcolligan7/deployments/ondemand-qwen25-7b"
_TASK_ID = "gab_l6_agentsafe_told"


class _FakeTransport:
    def __init__(self, response):
        self._response = response
        self.seen_model = None

    def complete(self, request, *, api_key, timeout_seconds):
        self.seen_model = request["model"]
        return self._response


def _good_response():
    return {
        "choices": [
            {"message": {"content": '{"action":"final","final":"done"}'},
             "finish_reason": "stop"}
        ],
        "usage": {"prompt_tokens": 12, "completion_tokens": 6, "total_tokens": 18},
    }


def _factory_turn(transport, *, env):
    task = load_task(_TASK_ID)
    condition = anchor_by_id("ondemand_qwen25_7b").condition
    factory = make_fireworks_model_turn_factory(
        _WIRE, transport=transport, env=env
    )
    model_turn = factory(task, condition, "no_agent_safe", 0, detector=OutageDetector())
    return model_turn([{"role": "user", "content": "hi"}])


def test_factory_sends_live_deployment_wire_model():
    t = _FakeTransport(_good_response())
    _factory_turn(t, env={"FIREWORKS_API_KEY": "k"})
    assert t.seen_model == _WIRE  # NOT the roster base model id


def test_factory_happy_path_parses_result():
    t = _FakeTransport(_good_response())
    result = _factory_turn(t, env={"FIREWORKS_API_KEY": "k"})
    assert "done" in result.text
    assert result.prompt_tokens == 12 and result.completion_tokens == 6
    assert result.cost_usd_estimate is None  # on-demand: GPU-time billed


def test_factory_maps_provider_refusal():
    # Error outcomes are harness-injected sentinel turns (kept out of the model's
    # own history); the kind rides in the text prefix.
    resp = {"choices": [{"message": {"content": ""}, "finish_reason": "content_filter"}]}
    result = _factory_turn(_FakeTransport(resp), env={"FIREWORKS_API_KEY": "k"})
    assert result.harness_injected is True
    assert result.text.startswith("__GAB_PROVIDER_FILTERED__")


def test_factory_missing_key_is_adapter_error():
    result = _factory_turn(_FakeTransport(_good_response()), env={})
    assert result.harness_injected is True
    assert result.text.startswith("__GAB_ADAPTER_ERROR__")


def test_roster_v4_forms_within_family_capability_pairs():
    fams: dict[str, set[str]] = {}
    for pc in ANCHOR_CONDITIONS:
        fams.setdefault(pc.model_family, set()).add(pc.capability_band)
    spanning = {f for f, bands in fams.items() if bands == {"capable", "weak"}}
    # The confound break: four within-family pairs across three lineages (Qwen
    # 2.5/3, Llama3.1, Mistral), each with a capable AND a weak member, so
    # capability is not collinear with any single family.
    assert {"qwen2.5", "qwen3", "llama3.1", "mistral"}.issubset(spanning)
    assert len(spanning) == 4  # every anchor family is a complete pair


def test_band_family_index_covers_anchor_and_breadth():
    index = band_family_index()
    assert len(index) == 12  # 8 anchor (4 pairs) + 4 breadth
    assert index["ondemand_qwen25_72b_v1"] == ("capable", "qwen2.5")
    assert index["ondemand_mistral_7b_v1"] == ("weak", "mistral")
