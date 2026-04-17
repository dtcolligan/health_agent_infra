"""Core layer — cross-domain primitives shared by every domain module.

Currently scoped to configuration. Phase 1 will migrate schemas, validate,
writeback, review, state, and pull into this package. Imports from `core`
should never reach back into `domains/*`; the dependency direction is strictly
domains → core, never the reverse.
"""

from health_agent_infra.core.config import (
    DEFAULT_THRESHOLDS,
    load_thresholds,
    user_config_path,
)

__all__ = ["DEFAULT_THRESHOLDS", "load_thresholds", "user_config_path"]
