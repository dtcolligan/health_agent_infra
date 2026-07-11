"""Result table builders for GovernedAgentBench."""

from .cell_contrasts import (
    CELL_CONTRASTS_SCHEMA_VERSION,
    build_cell_contrasts,
    build_cell_contrasts_pooled,
    cell_label,
    condition_of,
    contract_arm_of,
    first_attempt_step_count,
    ladder_condition_run_dirs,
    write_cell_contrasts,
    write_cell_contrasts_pooled,
)
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
    PILOT_MECHANISM_COVERAGE_SCHEMA_VERSION,
    build_pilot_evidence_rows,
    build_pilot_evidence_table,
    build_pilot_mechanism_coverage,
    write_pilot_evidence_tables,
)
from .run_layout import (
    RepRecord,
    detect_run_layout,
    load_rep_records,
)

__all__ = [
    "CELL_CONTRASTS_SCHEMA_VERSION",
    "EVIDENCE_TABLE_SCHEMA_VERSION",
    "ERROR_TAXONOMY_SCHEMA_VERSION",
    "FIGURE_SCHEMA_VERSION",
    "PILOT_EVIDENCE_TABLE_SCHEMA_VERSION",
    "PILOT_MECHANISM_COVERAGE_SCHEMA_VERSION",
    "RepRecord",
    "build_cell_contrasts",
    "build_cell_contrasts_pooled",
    "build_error_taxonomy",
    "build_evidence_rows",
    "cell_label",
    "condition_of",
    "contract_arm_of",
    "first_attempt_step_count",
    "ladder_condition_run_dirs",
    "write_cell_contrasts",
    "write_cell_contrasts_pooled",
    "build_pilot_evidence_rows",
    "build_pilot_evidence_table",
    "build_pilot_mechanism_coverage",
    "detect_run_layout",
    "load_rep_records",
    "write_error_taxonomy",
    "write_result_figures",
    "write_evidence_tables",
    "write_pilot_evidence_tables",
]
