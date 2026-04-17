"""Local SQLite state store — schema, migrations, and connection management.

Phase 7A.1 substrate. Projector, dual-write, read CLIs, and snapshot logic
arrive in later phases. This module is not imported by any subcommand beyond
``hai state init`` and ``hai state migrate`` until 7A.2.
"""

from health_agent_infra.state.projector import (
    ReprojectBaseDirError,
    latest_nutrition_submission_id,
    project_accepted_nutrition_state_daily,
    project_accepted_recovery_state_daily,
    project_accepted_resistance_training_state_daily,
    project_accepted_running_state_daily,
    project_gym_session,
    project_gym_set,
    project_nutrition_intake_raw,
    project_recommendation,
    project_review_event,
    project_review_outcome,
    project_source_daily_garmin,
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
    "latest_nutrition_submission_id",
    "open_connection",
    "project_accepted_nutrition_state_daily",
    "project_accepted_recovery_state_daily",
    "project_accepted_resistance_training_state_daily",
    "project_accepted_running_state_daily",
    "project_gym_session",
    "project_gym_set",
    "project_nutrition_intake_raw",
    "project_recommendation",
    "project_review_event",
    "project_review_outcome",
    "project_source_daily_garmin",
    "read_domain",
    "reproject_from_jsonl",
    "resolve_db_path",
]
