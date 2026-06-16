"""Result table builders for GovernedAgentBench."""

from .evidence_tables import (
    EVIDENCE_TABLE_SCHEMA_VERSION,
    build_evidence_rows,
    write_evidence_tables,
)
from .figures import FIGURE_SCHEMA_VERSION, write_result_figures
from .error_taxonomy import (
    ERROR_TAXONOMY_SCHEMA_VERSION,
    build_error_taxonomy,
    write_error_taxonomy,
)
from .pilot_evidence import (
    PILOT_EVIDENCE_TABLE_SCHEMA_VERSION,
    PILOT_H1_SUMMARY_SCHEMA_VERSION,
    build_pilot_evidence_rows,
    build_pilot_evidence_table,
    build_pilot_h1_mechanism_summary,
    write_pilot_evidence_tables,
)
from .dr9_switch import (
    DR9_SWITCH_DECISION_SCHEMA_VERSION,
    build_dr9_switch_decision,
    write_dr9_switch_decision,
)

__all__ = [
    "EVIDENCE_TABLE_SCHEMA_VERSION",
    "ERROR_TAXONOMY_SCHEMA_VERSION",
    "FIGURE_SCHEMA_VERSION",
    "DR9_SWITCH_DECISION_SCHEMA_VERSION",
    "PILOT_EVIDENCE_TABLE_SCHEMA_VERSION",
    "PILOT_H1_SUMMARY_SCHEMA_VERSION",
    "build_error_taxonomy",
    "build_evidence_rows",
    "build_dr9_switch_decision",
    "build_pilot_evidence_rows",
    "build_pilot_evidence_table",
    "build_pilot_h1_mechanism_summary",
    "write_error_taxonomy",
    "write_result_figures",
    "write_evidence_tables",
    "write_dr9_switch_decision",
    "write_pilot_evidence_tables",
]
