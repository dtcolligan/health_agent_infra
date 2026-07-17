"""Fireworks on-demand deployment lifecycle manager for the powered run.

The confound break needs weak/capable members of the SAME family (Qwen2.5
{72B,7B}, Llama3.1 {70B,8B}), which exist only as on-demand base models on
Fireworks, not serverless. This module brings such a model up, hands the caller
the deployment-qualified model string to invoke, and GUARANTEES teardown.

This is OPERATIONAL tooling for a live paid run. It is deliberately NOT imported
by the offline-reproduce path or the scorer -- those stay network-free. It lives
in scripts/ beside the other live-run operators (run_pilot_live,
check_model_availability).

Spend safety (three independent layers):
  1. ``deployment()`` context manager deletes in a ``finally`` so a crash mid-run
     cannot orphan a live GPU.
  2. Deployments are created with ``minReplicaCount=0`` and a short
     ``scaleToZeroWindow`` so the GPU scales to zero (billing stops) when idle,
     even if teardown is somehow skipped; Fireworks also auto-deletes a
     0-min-replica deployment after 7 days of no traffic.
  3. ``validate_only=True`` dry-runs a create request against the real API for
     $0, so the whole path is testable before a single GPU is provisioned.

Control-plane REST (verified against docs 2026-07-17):
  POST   /v1/accounts/{acct}/deployments?deploymentId=<id>[&validateOnly=true]
  GET    /v1/accounts/{acct}/deployments/{id}
  DELETE /v1/accounts/{acct}/deployments/{id}
Invoke a ready deployment at chat/completions with model
  accounts/{acct}/deployments/{id}
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Iterator, Mapping

CONTROL_PLANE_BASE = "https://api.fireworks.ai/v1"
FIREWORKS_API_KEY_ENV = "FIREWORKS_API_KEY"

# GPU-hour reference (USD), snapshot 2026-06-03 from harness.fireworks. Used only
# to estimate/track spend, never to bill; the actual accelerator is recorded live.
GPU_HOUR_USD: dict[str, float] = {
    "NVIDIA_H100_80GB": 7.0,
    "NVIDIA_H200_141GB": 7.0,
    "NVIDIA_B200_180GB": 10.0,
    "NVIDIA_B300_288GB": 12.0,
    "NVIDIA_A100_80GB": 4.5,
}

_READY = "READY"
_FAILED_STATES = frozenset({"FAILED", "DELETING", "DELETED"})


class FireworksDeploymentError(RuntimeError):
    """Raised on a control-plane error or a deployment that fails to become ready."""


@dataclass(frozen=True)
class DeploymentHandle:
    """A live (or validated) on-demand deployment."""

    account_id: str
    deployment_id: str
    base_model: str
    invocation_model: str
    accelerator_type: str | None
    validate_only: bool


def _control_request(
    method: str,
    url: str,
    *,
    api_key: str,
    body: Mapping[str, Any] | None = None,
    timeout: float = 60.0,
) -> tuple[int, dict[str, Any]]:
    """Issue one control-plane request; return (status, parsed_json)."""

    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "GovernedAgentBench/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw) if raw.strip() else {}
            return resp.status, parsed if isinstance(parsed, dict) else {"_raw": parsed}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"error": {"message": raw[:300]}}
        return exc.code, parsed if isinstance(parsed, dict) else {"error": {"message": raw[:300]}}
    except (urllib.error.URLError, TimeoutError) as exc:
        raise FireworksDeploymentError(f"control-plane transport error: {exc}") from exc


# Injectable control-plane transport signature (for offline tests): matches
# ``_control_request`` -> (status, parsed_json).
Transport = Callable[..., tuple[int, dict[str, Any]]]


def create_deployment(
    account_id: str,
    base_model: str,
    deployment_id: str,
    *,
    api_key: str,
    min_replica: int = 0,
    max_replica: int = 1,
    scale_to_zero_window: str = "300s",
    accelerator_type: str | None = None,
    deployment_shape: str | None = None,
    validate_only: bool = False,
    timeout: float = 60.0,
    transport: Transport = _control_request,
) -> dict[str, Any]:
    """POST a deployment create. ``validate_only`` dry-runs for $0.

    Defaults encode spend safety: minReplicaCount=0 + a 5-minute scaleToZeroWindow
    so an idle GPU scales to zero. ``accelerator_type`` is REQUIRED by the API for
    non-embedding engines (verified live 2026-07-17); the 4 anchor models each fit
    a single NVIDIA_H100_80GB (worldSize=1, FP8), so the roster pins that per model.
    """

    query = f"deploymentId={deployment_id}"
    if validate_only:
        query += "&validateOnly=true"
    url = f"{CONTROL_PLANE_BASE}/accounts/{account_id}/deployments?{query}"
    body: dict[str, Any] = {
        "baseModel": base_model,
        "minReplicaCount": min_replica,
        "maxReplicaCount": max_replica,
        "autoscalingPolicy": {"scaleToZeroWindow": scale_to_zero_window},
    }
    if accelerator_type is not None:
        body["acceleratorType"] = accelerator_type
    if deployment_shape is not None:
        body["deploymentShape"] = deployment_shape
    status, payload = transport(
        "POST", url, api_key=api_key, body=body, timeout=timeout
    )
    if status not in (200, 201):
        message = (payload.get("error") or {}).get("message", json.dumps(payload)[:300])
        raise FireworksDeploymentError(
            f"create deployment {deployment_id!r} for {base_model!r} failed "
            f"(HTTP {status}): {message}"
        )
    return payload


def get_deployment(
    account_id: str,
    deployment_id: str,
    *,
    api_key: str,
    timeout: float = 30.0,
    transport: Transport = _control_request,
) -> dict[str, Any]:
    """GET a single deployment resource (for state polling)."""

    url = f"{CONTROL_PLANE_BASE}/accounts/{account_id}/deployments/{deployment_id}"
    status, payload = transport("GET", url, api_key=api_key, timeout=timeout)
    if status != 200:
        message = (payload.get("error") or {}).get("message", json.dumps(payload)[:300])
        raise FireworksDeploymentError(
            f"get deployment {deployment_id!r} failed (HTTP {status}): {message}"
        )
    return payload


def delete_deployment(
    account_id: str,
    deployment_id: str,
    *,
    api_key: str,
    timeout: float = 60.0,
    transport: Transport = _control_request,
) -> tuple[int, dict[str, Any]]:
    """DELETE a deployment. Returns (status, payload); never raises on 404.

    ``ignore_checks=true`` is REQUIRED: Fireworks blocks deletion of a deployment
    that received inference in the last hour ("pass ignore_checks to skip this
    check", HTTP 400) -- and we always sweep the deployment right before deleting
    it, so without this every teardown 400s and leans on scale-to-zero + manual
    cleanup. Verified against the live API 2026-07-17.
    """

    url = (
        f"{CONTROL_PLANE_BASE}/accounts/{account_id}/deployments/{deployment_id}"
        "?ignore_checks=true"
    )
    return transport("DELETE", url, api_key=api_key, timeout=timeout)


def wait_until_ready(
    account_id: str,
    deployment_id: str,
    *,
    api_key: str,
    poll_interval: float = 10.0,
    timeout: float = 900.0,
    sleeper: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    transport: Transport = _control_request,
    max_consecutive_get_errors: int = 3,
) -> str:
    """Poll until the deployment is READY; return its invocation model string.

    Raises if it enters a failed/deleting state or the timeout elapses. A
    transient GET error does NOT abort (which would trigger a delete of a
    still-CREATING deployment and orphan it): up to ``max_consecutive_get_errors``
    consecutive GET failures are tolerated before giving up. ``sleeper`` / ``clock``
    are injectable so tests need no real waits.
    """

    deadline = clock() + timeout
    invocation = f"accounts/{account_id}/deployments/{deployment_id}"
    get_errors = 0
    while True:
        try:
            payload = get_deployment(
                account_id, deployment_id, api_key=api_key, transport=transport
            )
            get_errors = 0
        except FireworksDeploymentError:
            get_errors += 1
            if get_errors > max_consecutive_get_errors or clock() >= deadline:
                raise
            sleeper(poll_interval)
            continue
        state = str(payload.get("state", "")).upper()
        if state == _READY:
            return invocation
        if state in _FAILED_STATES:
            raise FireworksDeploymentError(
                f"deployment {deployment_id!r} entered state {state!r} before READY"
            )
        if clock() >= deadline:
            raise FireworksDeploymentError(
                f"deployment {deployment_id!r} not READY within {timeout:.0f}s "
                f"(last state {state!r})"
            )
        sleeper(poll_interval)


def list_deployments(
    account_id: str,
    *,
    api_key: str,
    timeout: float = 30.0,
    transport: Transport = _control_request,
) -> list[dict[str, Any]]:
    """List every deployment on the account (for the orphan sweep)."""

    url = f"{CONTROL_PLANE_BASE}/accounts/{account_id}/deployments"
    status, payload = transport("GET", url, api_key=api_key, timeout=timeout)
    if status != 200:
        raise FireworksDeploymentError(f"list deployments failed (HTTP {status})")
    deployments = payload.get("deployments")
    return list(deployments) if isinstance(deployments, list) else []


def _safe_emit(
    on_event: Callable[[str, dict[str, Any]], None] | None,
) -> Callable[[str, dict[str, Any]], None]:
    """Wrap an event callback so a raising callback can never break teardown."""

    base = on_event or (lambda _kind, _data: None)

    def emit(kind: str, data: dict[str, Any]) -> None:
        try:
            base(kind, data)
        except Exception:  # noqa: BLE001 - a log sink must never orphan a GPU
            pass

    return emit


def _confirm_drained(
    account_id: str,
    deployment_id: str,
    *,
    api_key: str,
    transport: Transport,
    sleeper: Callable[[float], None],
    attempts: int = 6,
    interval: float = 8.0,
) -> bool:
    """Best-effort poll until the deployment is gone (HTTP 404)."""

    url = f"{CONTROL_PLANE_BASE}/accounts/{account_id}/deployments/{deployment_id}"
    for _ in range(attempts):
        try:
            status, _payload = transport("GET", url, api_key=api_key, timeout=30.0)
        except FireworksDeploymentError:
            return True  # transport error resolving a delete: treat as gone
        if status == 404:
            return True
        sleeper(interval)
    return False


def _teardown(
    account_id: str,
    deployment_id: str,
    *,
    api_key: str,
    transport: Transport,
    emit: Callable[[str, dict[str, Any]], None],
    uptime_s: float | None,
    max_attempts: int = 5,
    sleeper: Callable[[float], None] = time.sleep,
) -> bool:
    """DELETE with exponential backoff, then confirm drain. Never raises.

    A transitional 400 (which ``ignore_checks`` does NOT cure) resolves in a few
    seconds, so retry rather than orphaning. Emits ``deleted`` (with a drain flag)
    on success, else ``delete_failed`` with a reconcile string. Returns success.
    """

    last_status: int | None = None
    last_payload: dict[str, Any] = {}
    for attempt in range(max_attempts):
        try:
            status, payload = delete_deployment(
                account_id, deployment_id, api_key=api_key, transport=transport
            )
        except FireworksDeploymentError as exc:
            status, payload = -1, {"error": {"message": str(exc)}}
        last_status, last_payload = status, payload
        if status in (200, 204, 404):
            drained = _confirm_drained(
                account_id, deployment_id, api_key=api_key,
                transport=transport, sleeper=sleeper,
            )
            emit("deleted", {
                "deployment_id": deployment_id,
                "uptime_seconds": uptime_s,
                "drained": drained,
                "attempts": attempt + 1,
            })
            return True
        if attempt < max_attempts - 1:
            sleeper(min(60.0, 5.0 * (2 ** attempt)))
    emit("delete_failed", {
        "deployment_id": deployment_id,
        "http_status": last_status,
        "payload": last_payload,
        "uptime_seconds": uptime_s,
        "attempts": max_attempts,
        "reconcile": (
            f"MANUAL TEARDOWN NEEDED: DELETE /v1/accounts/{account_id}"
            f"/deployments/{deployment_id}?ignore_checks=true "
            "(scale-to-zero caps bleed; sweep_orphans() clears it)"
        ),
    })
    return False


def sweep_orphans(
    account_id: str,
    *,
    prefix: str = "ondemand-",
    api_key: str,
    transport: Transport = _control_request,
    on_event: Callable[[str, dict[str, Any]], None] | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> list[str]:
    """Force-delete every deployment whose id starts with ``prefix``.

    The belt against a crashed run: call at run START (kill anything a prior crash
    orphaned, since a resumed run mints a fresh id and can't find the old one) and
    run END (catch any teardown that ultimately failed). Returns the swept ids.
    """

    emit = _safe_emit(on_event)
    swept: list[str] = []
    for dep in list_deployments(
        account_id, api_key=api_key, transport=transport
    ):
        dep_id = str(dep.get("name", "")).rsplit("/", 1)[-1]
        if not dep_id or not dep_id.startswith(prefix):
            continue
        emit("orphan_found", {"deployment_id": dep_id, "state": dep.get("state")})
        _teardown(
            account_id, dep_id, api_key=api_key, transport=transport,
            emit=emit, uptime_s=None, sleeper=sleeper,
        )
        swept.append(dep_id)
    return swept


@contextmanager
def deployment(
    account_id: str,
    base_model: str,
    deployment_id: str,
    *,
    api_key: str,
    validate_only: bool = False,
    accelerator_type: str | None = None,
    ready_timeout: float = 900.0,
    scale_to_zero_window: str = "300s",
    on_event: Callable[[str, dict[str, Any]], None] | None = None,
    transport: Transport = _control_request,
    sleeper: Callable[[float], None] = time.sleep,
) -> Iterator[DeploymentHandle]:
    """Bring a model up, yield its invocation handle, and GUARANTEE teardown.

    Money-safety invariants (each a fixed audit finding):
    - ``create_deployment`` runs INSIDE the try, so a failure or callback error in
      the create->ready window still reaches the teardown ``finally``.
    - Every event callback is wrapped (``_safe_emit``) so a raising log sink can
      never escape and orphan the GPU.
    - Teardown (``_teardown``) retries with backoff through transitional 400s and
      confirms drain; a terminal failure emits a reconcile string, and
      ``sweep_orphans`` is the run-level belt for that case.

    With ``validate_only=True`` this does a $0 dry-run: it validates the create
    request and yields a handle without provisioning, polling, or teardown.
    """

    emit = _safe_emit(on_event)
    start = time.monotonic()
    created = False
    try:
        create_deployment(
            account_id,
            base_model,
            deployment_id,
            api_key=api_key,
            accelerator_type=accelerator_type,
            scale_to_zero_window=scale_to_zero_window,
            validate_only=validate_only,
            transport=transport,
        )
        created = True
        if validate_only:
            emit("validated", {"deployment_id": deployment_id, "base_model": base_model})
            yield DeploymentHandle(
                account_id=account_id,
                deployment_id=deployment_id,
                base_model=base_model,
                invocation_model=f"accounts/{account_id}/deployments/{deployment_id}",
                accelerator_type=accelerator_type,
                validate_only=True,
            )
            return
        emit("creating", {"deployment_id": deployment_id, "base_model": base_model})
        invocation = wait_until_ready(
            account_id,
            deployment_id,
            api_key=api_key,
            timeout=ready_timeout,
            transport=transport,
        )
        emit("ready", {"deployment_id": deployment_id, "invocation_model": invocation})
        yield DeploymentHandle(
            account_id=account_id,
            deployment_id=deployment_id,
            base_model=base_model,
            invocation_model=invocation,
            accelerator_type=accelerator_type,
            validate_only=False,
        )
    finally:
        # Tear down only a REAL provisioned deployment (validate_only provisions
        # nothing; a failed create leaves nothing to delete).
        if created and not validate_only:
            _teardown(
                account_id, deployment_id, api_key=api_key, transport=transport,
                emit=emit, uptime_s=time.monotonic() - start, sleeper=sleeper,
            )


def estimate_uptime_cost_usd(uptime_seconds: float, accelerator_type: str) -> float:
    """Rough USD for a deployment's active uptime at the reference GPU rate.

    A ceiling estimate: real billing is GPU-second and pauses on scale-to-zero,
    so this over-counts idle windows. Unknown accelerators fall back to the
    most expensive reference rate so an estimate is never optimistic.
    """

    rate = GPU_HOUR_USD.get(accelerator_type, max(GPU_HOUR_USD.values()))
    return (uptime_seconds / 3600.0) * rate


__all__ = [
    "CONTROL_PLANE_BASE",
    "DeploymentHandle",
    "FireworksDeploymentError",
    "create_deployment",
    "delete_deployment",
    "deployment",
    "estimate_uptime_cost_usd",
    "get_deployment",
    "list_deployments",
    "sweep_orphans",
    "wait_until_ready",
]
