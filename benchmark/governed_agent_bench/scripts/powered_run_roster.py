"""roster_v4: the powered-run model roster (driver-owned operational spec).

The powered run is a SEPARATELY pre-registered experiment (two-stage design), so
its roster lives here + in its pre-registration, not in the frozen paper-v1
``model_roster.md`` (which is hash-pinned and whose schema cannot carry the
``capability_band`` / ``accelerator`` fields the analysis and deployment manager
need). The four serverless breadth conditions ARE reused from ``model_roster.md``
via ``roster_condition`` so their vendor-verified decoding is single-sourced.

Two tiers:
  * ANCHOR (Fireworks on-demand) -- the confound break. Within-family capability
    pairs: Qwen2.5 {72B, 7B} and Llama3.1 {70B, 8B}. Same family, same provider,
    same serving mode -> family x capability crossed cleanly. Each is a single
    NVIDIA_H100_80GB (worldSize=1), brought up and torn down per model.
  * BREADTH (serverless) -- generalization across families. The roster_v3
    conditions: MiniMax-M3 + Llama-3.3-70B (capable), Qwen3.5-9B + Qwen2.5-7B
    (weak).

Each entry carries the analysis axes (capability_band, model_family) the tidy
frame needs; the driver stamps them onto every row.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governed_agent_bench.harness.fireworks import SYNTHETIC_DATA_BOUNDARY
from governed_agent_bench.model_roster import roster_condition

FIREWORKS_ACCOUNT_ID = "dtcolligan7"
FIREWORKS_ACCELERATOR = "NVIDIA_H100_80GB"

# Vendor-recommended decoding, single-sourced per family. Seed sentinel (not a
# fixed int) so the n replicates per cell vary stochastically rather than
# collapsing to one identical draw.
_SEED_SENTINEL = "provider_does_not_support_seed"
_QWEN25_DECODING = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0,
    "max_tokens": 2048,
    "seed": _SEED_SENTINEL,
}
_LLAMA31_DECODING = {
    "temperature": 0.6,
    "top_p": 0.9,
    "max_tokens": 2048,
    "seed": _SEED_SENTINEL,
}

# The mutation-gate substitution modes under the D-48 design: the gate is M5+M6
# combined and its ONLY clean off-mode is `no_runtime_enforcement` (the all-off
# floor). Two distinct retirements, do not conflate them: (1) the per-mechanism
# `no_agent_safe` / `no_proposal_gate` splits REMAIN valid runtime modes in
# SUPPORTED_RUNTIME_MODES, but D-48 retired them as SUBSTITUTION off-modes
# (leaky / arm-dependent-confound), so they must not appear here as gate modes;
# (2) the `no_agent_safe_no_proposal_gate` composite was fully removed from
# SUPPORTED_RUNTIME_MODES by the revert and no longer exists. The actual swept
# modes are MODE_ORDER intersected with each task's `runtime_modes_in_scope`, so
# this field is roster metadata only; it is pinned to the D-48 design so the
# metadata cannot misrepresent the experiment.
_MUTATION_GATE_MODES = (
    "full_contract",
    "no_runtime_enforcement",
)


@dataclass(frozen=True)
class PoweredCondition:
    """A roster_v4 entry: the harness condition dict + its analysis axes."""

    condition: dict[str, Any]
    capability_band: str  # "capable" | "weak"
    model_family: str
    provider: str
    serving_mode: str  # "on_demand" | "serverless"
    base_model: str | None  # on-demand base model id (None for serverless)
    accelerator_type: str | None


def _ondemand_condition(
    *,
    condition_id: str,
    base_model: str,
    decoding: dict[str, Any],
    capability_band: str,
    model_family: str,
    parameter_count: str,
    quantization: str,
) -> PoweredCondition:
    """Build one Fireworks on-demand condition dict + its analysis axes.

    ``model_id`` is the base model; the driver overrides the wire model with the
    live deployment-qualified string (``request_model``) at call time. Extra
    analysis keys are ignored by the adapter (runtime dict, not schema-validated).
    The identity/boundary fields (parameter_count, quantization,
    provider_snapshot_date, compute/cost boundary) are required by
    ``model_identity_from_roster_condition`` and the pilot manifest.
    """

    system_id = f"{condition_id}_v1"
    condition = {
        "condition_id": condition_id,
        "system_id": system_id,
        "model_class": "cloud",
        "model_family": model_family,
        "model_id": base_model,
        "provider": "Fireworks AI",
        "provider_snapshot_date": "2026-07-17",
        "parameter_count": parameter_count,
        "quantization": quantization,
        "context_window": 32768,
        "data_boundary": SYNTHETIC_DATA_BOUNDARY,
        "decoding_settings": decoding,
        "prompt_id": "deployment_full_v3",
        "manifest_id": "hai_0_2_0",
        "runtime_modes": list(_MUTATION_GATE_MODES),
        "compute_boundary": {
            "hardware": f"Fireworks AI on-demand {FIREWORKS_ACCELERATOR} (single GPU)",
            "runtime": "Fireworks AI chat completions API (on-demand deployment)",
            # Per-invocation (per-phase) wall cap. On-demand cost is GPU-time and
            # the per-token cost cap is inert (cost=None), so this wall cap +
            # scale-to-zero + the run-level cumulative ceiling are the real spend
            # controls. 120 min at ~$7/GPU-h ~= $14 per phase, well above a normal
            # canary/main phase's need but bounding a runaway.
            "max_wall_time_minutes": 120,
            "network_access": True,
        },
        "cost_boundary": {
            "budget_type": "approved_cloud_budget",
            "max_cost_usd": 40.0,
            "billing_boundary": (
                "Fireworks on-demand GPU-second billing; deployment brought up "
                "and torn down per model. D-06 aggregate ceiling."
            ),
        },
        # analysis / operational axes (adapter ignores unknown keys):
        "capability_band": capability_band,
        "serving_mode": "on_demand",
        "accelerator_type": FIREWORKS_ACCELERATOR,
        "cloud_approval": {
            "approval_id": f"powered_run_ondemand_{condition_id}",
            "approved_by": "Dom",
            "approved_at": "2026-07-17",
            "approved_scope": (
                "Powered-run confound break (roster_v4). Fireworks on-demand "
                "single-GPU (NVIDIA_H100_80GB). Synthetic GAB fixtures only."
            ),
        },
    }
    return PoweredCondition(
        condition=condition,
        capability_band=capability_band,
        model_family=model_family,
        provider="Fireworks AI",
        serving_mode="on_demand",
        base_model=base_model,
        accelerator_type=FIREWORKS_ACCELERATOR,
    )


# --- ANCHOR: on-demand within-family capability pairs ----------------------- #

ANCHOR_CONDITIONS: tuple[PoweredCondition, ...] = (
    _ondemand_condition(
        condition_id="ondemand_qwen25_72b",
        base_model="accounts/fireworks/models/qwen2p5-72b-instruct",
        decoding=_QWEN25_DECODING,
        capability_band="capable",
        model_family="qwen2.5",
        parameter_count="72.7B (72706203648)",
        quantization="FP8 (Fireworks on-demand single-GPU serving)",
    ),
    _ondemand_condition(
        condition_id="ondemand_qwen25_7b",
        base_model="accounts/fireworks/models/qwen2p5-7b-instruct",
        decoding=_QWEN25_DECODING,
        capability_band="weak",
        model_family="qwen2.5",
        parameter_count="8.1B (8078167552)",
        quantization="Fireworks on-demand serving (provider-selected precision)",
    ),
    _ondemand_condition(
        condition_id="ondemand_llama31_70b",
        base_model="accounts/fireworks/models/llama-v3p1-70b-instruct",
        decoding=_LLAMA31_DECODING,
        capability_band="capable",
        model_family="llama3.1",
        parameter_count="70.6B (70553706496)",
        quantization="FP8 (Fireworks on-demand single-GPU serving)",
    ),
    _ondemand_condition(
        condition_id="ondemand_llama31_8b",
        base_model="accounts/fireworks/models/llama-v3p1-8b-instruct",
        decoding=_LLAMA31_DECODING,
        capability_band="weak",
        model_family="llama3.1",
        parameter_count="8.8B (8835567616)",
        quantization="Fireworks on-demand serving (provider-selected precision)",
    ),
)

# --- BREADTH: serverless conditions reused from the frozen roster_v3 --------- #

# (condition_id in model_roster.md, capability_band, model_family)
_BREADTH_SPEC = (
    ("run_primary_minimax_m3", "capable", "minimax-m3"),
    ("run_capable_llama33_70b", "capable", "llama3.3"),
    ("run_nearfloor_qwen35_9b", "weak", "qwen3.5"),
    ("run_belowfloor_qwen25_7b", "weak", "qwen2.5"),
)


def breadth_conditions() -> tuple[PoweredCondition, ...]:
    """Load the serverless breadth conditions from the frozen roster."""

    out = []
    for condition_id, band, family in _BREADTH_SPEC:
        cond = roster_condition(condition_id)
        out.append(
            PoweredCondition(
                condition=cond,
                capability_band=band,
                model_family=family,
                provider=str(cond.get("provider", "Together AI")),
                serving_mode="serverless",
                base_model=None,
                accelerator_type=None,
            )
        )
    return tuple(out)


def anchor_by_id(condition_id: str) -> PoweredCondition:
    """Return one anchor condition by id (for the smoke / staged runs)."""

    for pc in ANCHOR_CONDITIONS:
        if pc.condition["condition_id"] == condition_id:
            return pc
    raise KeyError(f"no anchor condition {condition_id!r}")


def condition_capability_band(condition: dict[str, Any]) -> str | None:
    """Capability band for ANY run condition (roster_v3 or roster_v4).

    roster_v4 on-demand conditions carry an explicit ``capability_band``. The
    frozen roster_v3 conditions encode the band in the condition_id prefix
    (run_primary/run_capable = capable; run_nearfloor/run_belowfloor = weak).
    Returns None for an unrecognised condition so the caller fails closed rather
    than silently pooling a floor point into the capable movement (the OR-2 fix:
    the canary gate's capable-only movement pool must include the on-demand
    capable models, whose ids do NOT match the run_ prefixes).
    """

    band = condition.get("capability_band")
    if band in ("capable", "weak"):
        return band
    cid = str(condition.get("condition_id", ""))
    if cid.startswith(("run_primary", "run_capable")):
        return "capable"
    if cid.startswith(("run_nearfloor", "run_belowfloor")):
        return "weak"
    return None


def band_family_index() -> dict[str, tuple[str, str]]:
    """Map system_id -> (capability_band, model_family) for the analysis adapter."""

    index: dict[str, tuple[str, str]] = {}
    for pc in ANCHOR_CONDITIONS + tuple(breadth_conditions()):
        index[str(pc.condition["system_id"])] = (pc.capability_band, pc.model_family)
    return index


__all__ = [
    "ANCHOR_CONDITIONS",
    "FIREWORKS_ACCELERATOR",
    "FIREWORKS_ACCOUNT_ID",
    "PoweredCondition",
    "anchor_by_id",
    "band_family_index",
    "breadth_conditions",
    "condition_capability_band",
]
