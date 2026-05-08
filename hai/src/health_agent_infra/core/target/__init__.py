"""Target ledger (W50). User-authored target rows with archive +
supersession discipline. Outcomes never auto-mutate targets — they may
propose target *review* later (post-v0.1.8) but must not auto-change a
target value."""

from health_agent_infra.core.target.store import (
    TargetRecord,
    TargetValidationError,
    add_target,
    archive_target,
    commit_target,
    list_active_target,
    list_target,
    supersede_target,
)

__all__ = [
    "TargetRecord",
    "TargetValidationError",
    "add_target",
    "archive_target",
    "commit_target",
    "list_active_target",
    "list_target",
    "supersede_target",
]
