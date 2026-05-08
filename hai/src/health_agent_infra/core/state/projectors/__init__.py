"""Per-domain projection writers.

Phase 3 step 2 split the projection logic out of the monolithic
``core/state/projector.py`` into per-domain modules. Each module owns the
write path into its domain's ``accepted_*_state_daily`` table; shared
helpers (timestamps, boolean coercion, per-dimension ``derived_from``
hygiene) live in :mod:`._shared`.

``core/state/projector.py`` now acts as the orchestrator/delegator —
external callers continue to import from ``core.state`` or
``core.state.projector`` unchanged.
"""

from health_agent_infra.core.state.projectors.recovery import (
    project_accepted_recovery_state_daily,
)
from health_agent_infra.core.state.projectors.sleep import (
    project_accepted_sleep_state_daily,
)
from health_agent_infra.core.state.projectors.strength import (
    project_accepted_resistance_training_state_daily,
)
from health_agent_infra.core.state.projectors.stress import (
    merge_manual_stress_into_accepted_recovery,
    merge_manual_stress_into_accepted_stress,
    project_accepted_stress_state_daily,
)

__all__ = [
    "merge_manual_stress_into_accepted_recovery",
    "merge_manual_stress_into_accepted_stress",
    "project_accepted_recovery_state_daily",
    "project_accepted_resistance_training_state_daily",
    "project_accepted_sleep_state_daily",
    "project_accepted_stress_state_daily",
]
