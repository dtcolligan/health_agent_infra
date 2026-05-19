"""Model-agnostic harness primitives for GovernedAgentBench."""

from .core import (
    HarnessConfig,
    HarnessError,
    action_to_argv,
    load_json,
    load_manifest_snapshot,
    load_task,
    render_prompt,
    run_operator_action,
    run_operator_actions,
)
from .model_actions import (
    harness_config_for_roster_condition,
    model_identity_from_roster_condition,
    parse_model_action,
    run_model_response_action,
)

__all__ = [
    "HarnessConfig",
    "HarnessError",
    "action_to_argv",
    "harness_config_for_roster_condition",
    "load_json",
    "load_manifest_snapshot",
    "load_task",
    "model_identity_from_roster_condition",
    "parse_model_action",
    "render_prompt",
    "run_model_response_action",
    "run_operator_action",
    "run_operator_actions",
]
