"""Offline tests for the Fireworks deployment lifecycle manager.

No network: a fake transport scripts control-plane responses. The load-bearing
tests are the money-safety invariants — teardown fires on a crash, retries
through a transitional 400, a raising log callback can't orphan a GPU, and the
orphan sweep force-deletes leftovers.
"""

from __future__ import annotations

import pytest

from governed_agent_bench.scripts.fireworks_deployments import (
    FireworksDeploymentError,
    create_deployment,
    deployment,
    estimate_uptime_cost_usd,
    sweep_orphans,
    wait_until_ready,
)

_NOSLEEP = lambda _s: None  # noqa: E731 - test helper


class FakeTransport:
    """Scripts control-plane responses and records (method, url, body) calls.

    Models deletion: once a DELETE succeeds (200/204), later single-deployment
    GETs return 404 so drain-confirm resolves. ``get_states`` is consumed one per
    poll GET so a deployment can transition CREATING -> READY.
    """

    def __init__(self, *, get_states=None, delete_status=200, create_status=200,
                 deployments=None, delete_statuses=None):
        self.calls = []
        self._get_states = list(get_states or ["READY"])
        self._delete_status = delete_status
        self._delete_statuses = list(delete_statuses) if delete_statuses else None
        self._create_status = create_status
        self._deployments = deployments or []
        self._deleted = False

    def __call__(self, method, url, *, api_key, body=None, timeout=60.0):
        self.calls.append((method, url, body))
        if method == "POST":
            return self._create_status, {"name": url}
        if method == "GET":
            if url.rstrip("/").endswith("/deployments"):
                return 200, {"deployments": self._deployments}
            if self._deleted:
                return 404, {"error": {"message": "not found"}}
            state = self._get_states.pop(0) if self._get_states else "READY"
            return 200, {"state": state}
        if method == "DELETE":
            status = (
                self._delete_statuses.pop(0)
                if self._delete_statuses else self._delete_status
            )
            if status in (200, 204):
                self._deleted = True
            return status, {}
        raise AssertionError(f"unexpected method {method}")


def _delete_urls(t):
    return [url for method, url, _ in t.calls if method == "DELETE"]


# --- create / validate ------------------------------------------------------ #


def test_create_builds_url_and_body():
    t = FakeTransport()
    create_deployment(
        "acct", "accounts/fireworks/models/qwen2p5-7b-instruct", "gab-q7b",
        api_key="k", accelerator_type="NVIDIA_H100_80GB", transport=t,
    )
    method, url, body = t.calls[0]
    assert method == "POST"
    assert "deploymentId=gab-q7b" in url and "validateOnly" not in url
    assert body["minReplicaCount"] == 0
    assert body["acceleratorType"] == "NVIDIA_H100_80GB"
    assert body["autoscalingPolicy"]["scaleToZeroWindow"] == "300s"


def test_validate_only_sets_query_flag():
    t = FakeTransport()
    create_deployment(
        "acct", "accounts/fireworks/models/x", "gab-x",
        api_key="k", accelerator_type="NVIDIA_H100_80GB",
        validate_only=True, transport=t,
    )
    assert "validateOnly=true" in t.calls[0][1]


def test_create_error_raises_with_message():
    def err_transport(method, url, *, api_key, body=None, timeout=60.0):
        return 400, {"error": {"message": "accelerator_type must be specified"}}

    with pytest.raises(FireworksDeploymentError, match="accelerator_type"):
        create_deployment("acct", "accounts/fireworks/models/x", "gab-x",
                          api_key="k", transport=err_transport)


# --- wait_until_ready ------------------------------------------------------- #


def test_wait_until_ready_polls_then_returns_invocation():
    t = FakeTransport(get_states=["CREATING", "CREATING", "READY"])
    inv = wait_until_ready("acct", "gab-x", api_key="k",
                           poll_interval=0.0, sleeper=_NOSLEEP, transport=t)
    assert inv == "accounts/acct/deployments/gab-x"


def test_wait_until_ready_raises_on_failed_state():
    t = FakeTransport(get_states=["CREATING", "FAILED"])
    with pytest.raises(FireworksDeploymentError, match="FAILED"):
        wait_until_ready("acct", "gab-x", api_key="k",
                         poll_interval=0.0, sleeper=_NOSLEEP, transport=t)


def test_wait_until_ready_tolerates_transient_get_errors():
    # A single GET failure must NOT abort (which would delete a CREATING deploy).
    calls = {"n": 0}

    def flaky(method, url, *, api_key, body=None, timeout=60.0):
        calls["n"] += 1
        if calls["n"] == 1:
            raise FireworksDeploymentError("transient 500")
        return 200, {"state": "READY"}

    inv = wait_until_ready("acct", "gab-x", api_key="k",
                           poll_interval=0.0, sleeper=_NOSLEEP, transport=flaky)
    assert inv.endswith("gab-x")


# --- deployment() lifecycle ------------------------------------------------- #


def _run(t, *, on_event=None, body=None, validate_only=False):
    with deployment("acct", "accounts/fireworks/models/x", "gab-x",
                    api_key="k", accelerator_type="NVIDIA_H100_80GB",
                    on_event=on_event, transport=t, sleeper=_NOSLEEP,
                    validate_only=validate_only) as handle:
        if body:
            body(handle)
        return handle


def test_deployment_happy_path_creates_and_deletes():
    t = FakeTransport(get_states=["READY"])
    events = []
    _run(t, on_event=lambda k, d: events.append(k))
    methods = [c[0] for c in t.calls]
    assert methods[0] == "POST" and "DELETE" in methods
    assert "deleted" in events


def test_delete_passes_ignore_checks():
    t = FakeTransport(get_states=["READY"])
    _run(t)
    assert all("ignore_checks=true" in u for u in _delete_urls(t))
    assert _delete_urls(t)


def test_deployment_deletes_even_when_body_raises():
    # THE money-safety invariant: a crash inside the with-block still tears down.
    t = FakeTransport(get_states=["READY"])

    def boom(_h):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        _run(t, body=boom)
    assert _delete_urls(t), "deployment was not torn down"


def test_create_failure_does_not_attempt_teardown_but_propagates():
    # If create fails, there is nothing provisioned; error propagates, no DELETE.
    t = FakeTransport(create_status=400)
    with pytest.raises(FireworksDeploymentError):
        _run(t)
    assert not _delete_urls(t)


def test_emit_exception_does_not_break_teardown():
    # A raising log callback must NEVER orphan the GPU.
    t = FakeTransport(get_states=["READY"])

    def raising_cb(_k, _d):
        raise ValueError("log sink down")

    _run(t, on_event=raising_cb)  # must not raise
    assert _delete_urls(t), "teardown skipped because a callback raised"


def test_teardown_retries_through_transitional_400():
    # First two DELETEs 400 (transitional), third 200 → deleted after retries.
    t = FakeTransport(get_states=["READY"], delete_statuses=[400, 400, 200])
    events = {}
    _run(t, on_event=lambda k, d: events.setdefault(k, d))
    assert "deleted" in events
    assert events["deleted"]["attempts"] == 3
    assert len(_delete_urls(t)) == 3


def test_teardown_emits_reconcile_after_exhausting_retries():
    t = FakeTransport(get_states=["READY"], delete_status=500)
    events = {}
    _run(t, on_event=lambda k, d: events.setdefault(k, d))
    assert "delete_failed" in events
    assert "MANUAL TEARDOWN NEEDED" in events["delete_failed"]["reconcile"]


def test_validate_only_context_does_not_poll_or_delete():
    t = FakeTransport()
    h = _run(t, validate_only=True)
    assert h.validate_only is True
    assert [c[0] for c in t.calls] == ["POST"]  # no GET poll, no DELETE


# --- orphan sweep ----------------------------------------------------------- #


def test_orphan_sweep_force_deletes_only_prefixed():
    t = FakeTransport(deployments=[
        {"name": "accounts/acct/deployments/ondemand-qwen25-7b-abc", "state": "READY"},
        {"name": "accounts/acct/deployments/some-other-thing", "state": "READY"},
    ])
    swept = sweep_orphans("acct", prefix="ondemand-", api_key="k",
                          transport=t, sleeper=_NOSLEEP)
    assert swept == ["ondemand-qwen25-7b-abc"]
    assert _delete_urls(t) == [
        "https://api.fireworks.ai/v1/accounts/acct/deployments/"
        "ondemand-qwen25-7b-abc?ignore_checks=true"
    ]


def test_orphan_sweep_empty_when_nothing_matches():
    t = FakeTransport(deployments=[])
    assert sweep_orphans("acct", api_key="k", transport=t, sleeper=_NOSLEEP) == []


# --- cost ------------------------------------------------------------------- #


def test_cost_estimate_uses_worst_rate_for_unknown_gpu():
    assert estimate_uptime_cost_usd(3600, "NVIDIA_H100_80GB") == pytest.approx(7.0)
    assert estimate_uptime_cost_usd(3600, "MYSTERY_GPU") >= 7.0
