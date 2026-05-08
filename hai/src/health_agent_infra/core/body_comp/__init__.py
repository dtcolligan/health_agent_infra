"""W-B (v0.1.17 §2.H) — body-composition measurement store.

User-authored body-comp intake. v1 is measurement-only (no targets,
no wearable pull, no agent-proposal path). Future cycles can extend.
"""

from health_agent_infra.core.body_comp.store import (
    BodyCompRecord,
    BodyCompValidationError,
    add_body_comp,
    list_body_comp,
)

__all__ = [
    "BodyCompRecord",
    "BodyCompValidationError",
    "add_body_comp",
    "list_body_comp",
]
