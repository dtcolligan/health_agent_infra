"""Local SQLite state store — schema, migrations, and connection management.

Phase 7A.1 substrate. Projector, dual-write, read CLIs, and snapshot logic
arrive in later phases. This module is not imported by any subcommand beyond
``hai state init`` and ``hai state migrate`` until 7A.2.
"""

from health_agent_infra.state.projector import (
    ReprojectBaseDirError,
    project_recommendation,
    project_review_event,
    project_review_outcome,
    reproject_from_jsonl,
)
from health_agent_infra.state.snapshot import (
    available_domains,
    build_snapshot,
    read_domain,
)
from health_agent_infra.state.store import (
    DEFAULT_DB_PATH,
    apply_pending_migrations,
    current_schema_version,
    initialize_database,
    open_connection,
    resolve_db_path,
)

__all__ = [
    "DEFAULT_DB_PATH",
    "ReprojectBaseDirError",
    "apply_pending_migrations",
    "available_domains",
    "build_snapshot",
    "current_schema_version",
    "initialize_database",
    "open_connection",
    "project_recommendation",
    "project_review_event",
    "project_review_outcome",
    "read_domain",
    "reproject_from_jsonl",
    "resolve_db_path",
]
