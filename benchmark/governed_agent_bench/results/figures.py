"""Deterministic SVG figure generation from evidence tables."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any


FIGURE_SCHEMA_VERSION = "governed_agent_bench.figures.v1"
BAR_COLOR = "#2563eb"
FAIL_COLOR = "#d97706"
TEXT_COLOR = "#111827"
GRID_COLOR = "#d1d5db"


def write_result_figures(
    *,
    evidence_table_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Write deterministic SVG summary figures from an evidence table."""

    table = json.loads(evidence_table_path.read_text(encoding="utf-8"))
    rows = table["rows"]
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = [
        _write_grouped_pass_figure(
            rows,
            group_key="runtime_mode",
            output_path=output_dir / "pass_by_runtime_mode.svg",
            title="Pass Rate By Runtime Mode",
        ),
        _write_grouped_pass_figure(
            rows,
            group_key="level",
            output_path=output_dir / "pass_by_level.svg",
            title="Pass Rate By Task Level",
        ),
    ]
    manifest = {
        "schema_version": FIGURE_SCHEMA_VERSION,
        "source_evidence_table": evidence_table_path.as_posix(),
        "figure_count": len(figures),
        "figures": figures,
    }
    (output_dir / "figures_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _write_grouped_pass_figure(
    rows: list[dict[str, Any]],
    *,
    group_key: str,
    output_path: Path,
    title: str,
) -> dict[str, Any]:
    groups = _group_pass_counts(rows, group_key)
    svg = _bar_chart_svg(title=title, groups=groups)
    output_path.write_text(svg, encoding="utf-8")
    return {
        "figure_id": output_path.stem,
        "path": output_path.as_posix(),
        "group_key": group_key,
        "group_count": len(groups),
    }


def _group_pass_counts(
    rows: list[dict[str, Any]],
    group_key: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row[group_key]), []).append(row)
    return [
        {
            "label": label,
            "total": len(items),
            "passed": sum(1 for item in items if item["overall_pass"] is True),
        }
        for label, items in sorted(grouped.items())
    ]


def _bar_chart_svg(
    *,
    title: str,
    groups: list[dict[str, Any]],
) -> str:
    width = 880
    left = 220
    right = 40
    top = 64
    row_height = 38
    height = top + (row_height * max(len(groups), 1)) + 52
    chart_width = width - left - right
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
        f'<text x="{left}" y="32" font-family="Arial, sans-serif" '
        f'font-size="22" fill="{TEXT_COLOR}">{escape(title)}</text>',
    ]
    for tick in range(0, 101, 25):
        x = left + chart_width * tick / 100
        lines.append(
            f'<line x1="{x:.1f}" y1="{top - 22}" x2="{x:.1f}" '
            f'y2="{height - 36}" stroke="{GRID_COLOR}" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{x:.1f}" y="{height - 14}" text-anchor="middle" '
            f'font-family="Arial, sans-serif" font-size="12" '
            f'fill="{TEXT_COLOR}">{tick}%</text>'
        )
    for index, group in enumerate(groups):
        y = top + index * row_height
        total = max(int(group["total"]), 1)
        passed = int(group["passed"])
        failed = total - passed
        pass_rate = passed / total
        pass_width = chart_width * pass_rate
        fail_width = chart_width - pass_width
        lines.append(
            f'<text x="{left - 12}" y="{y + 20}" text-anchor="end" '
            f'font-family="Arial, sans-serif" font-size="13" '
            f'fill="{TEXT_COLOR}">{escape(group["label"])}</text>'
        )
        lines.append(
            f'<rect x="{left}" y="{y}" width="{pass_width:.1f}" height="24" '
            f'fill="{BAR_COLOR}"/>'
        )
        if failed:
            lines.append(
                f'<rect x="{left + pass_width:.1f}" y="{y}" '
                f'width="{fail_width:.1f}" height="24" fill="{FAIL_COLOR}"/>'
            )
        lines.append(
            f'<text x="{left + chart_width + 8}" y="{y + 17}" '
            f'font-family="Arial, sans-serif" font-size="12" '
            f'fill="{TEXT_COLOR}">{passed}/{total}</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"
