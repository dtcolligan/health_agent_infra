"""Aggregated read-only diagnostics for ``hai doctor``.

One module because the checks are tiny and share the same
``{name: {status, ...}}`` shape. The public surface is
:func:`build_report` (which runs every check against a resolved
environment) and :func:`render_text` (which formats the report for
human consumption). The CLI layer wires these two together and picks
its output format based on ``--json``.
"""

from health_agent_infra.core.doctor.checks import (
    DoctorReport,
    build_report,
    worst_status,
)
from health_agent_infra.core.doctor.render import render_text


__all__ = [
    "DoctorReport",
    "build_report",
    "render_text",
    "worst_status",
]
