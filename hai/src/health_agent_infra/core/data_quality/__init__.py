"""Data Quality Ledger (W51). First-class user surface answering
"was this recommendation data-limited?" Per-source / per-domain rows
are populated by ``project_data_quality_for_date`` so callers can
query without reconstructing the snapshot."""

from health_agent_infra.core.data_quality.projector import (
    DOMAINS,
    project_data_quality_for_date,
    read_data_quality_rows,
)

__all__ = [
    "DOMAINS",
    "project_data_quality_for_date",
    "read_data_quality_rows",
]
