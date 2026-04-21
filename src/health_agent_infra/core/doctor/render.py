"""Human-readable renderer for :class:`DoctorReport`.

Pure function of the report dict; no I/O. The CLI layer picks between
this and ``json.dumps`` based on the ``--json`` flag.
"""

from __future__ import annotations

from typing import Any

from health_agent_infra.core.doctor.checks import DoctorReport


_STATUS_GLYPH: dict[str, str] = {
    "ok": "[OK]",
    "warn": "[WARN]",
    "fail": "[FAIL]",
}


def render_text(report: DoctorReport) -> str:
    """Return a multi-line plain-text rendering suitable for terminals.

    Format: one "## <check>" heading per check, with the status glyph
    on the heading line and the rest of the fields indented. Ordering
    matches the insertion order of ``report.checks`` so the output is
    deterministic.
    """

    lines: list[str] = []
    lines.append(f"hai doctor — v{report.version}")
    lines.append(f"overall: {_STATUS_GLYPH.get(report.overall_status, '[?]')} "
                 f"{report.overall_status}")
    lines.append("")

    for name, result in report.checks.items():
        lines.extend(_render_check(name, result))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_check(name: str, result: dict[str, Any]) -> list[str]:
    status = result.get("status", "?")
    glyph = _STATUS_GLYPH.get(status, "[?]")
    header = f"## {name}  {glyph} {status}"
    body: list[str] = [header]

    # Per-check special-case rendering for the fields that benefit
    # from structured display. Everything else falls through to the
    # generic "key: value" line.
    if name == "sources":
        body.extend(_render_sources(result))
        return body
    if name == "today":
        body.extend(_render_today(result))
        return body

    for key, value in result.items():
        if key == "status":
            continue
        if key == "domains" and isinstance(value, list):
            body.append(f"  {key}: {', '.join(value)}")
            continue
        if key == "missing" and isinstance(value, list):
            body.append(f"  missing: {', '.join(value)}")
            continue
        body.append(f"  {key}: {value}")
    return body


def _render_sources(result: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if "reason" in result:
        lines.append(f"  reason: {result['reason']}")
    if "hint" in result:
        lines.append(f"  hint: {result['hint']}")
    sources = result.get("sources") or {}
    if not sources:
        if "reason" not in result:
            lines.append("  (no sync history yet)")
        return lines
    for source, info in sorted(sources.items()):
        stale = info.get("staleness_hours")
        stale_str = "unknown" if stale is None else f"{stale:.1f}h"
        lines.append(
            f"  {source}: last={info.get('last_successful_sync_at')} "
            f"stale={stale_str}"
        )
    return lines


def _render_today(result: dict[str, Any]) -> list[str]:
    if "reason" in result:
        lines = [f"  reason: {result['reason']}"]
        if "hint" in result:
            lines.append(f"  hint: {result['hint']}")
        return lines
    return [
        f"  for_date: {result.get('for_date')}",
        f"  user_id: {result.get('user_id')}",
        f"  proposals: {result.get('proposals')}",
        f"  recommendations: {result.get('recommendations')}",
        f"  pending_reviews: {result.get('pending_reviews')}",
    ]
