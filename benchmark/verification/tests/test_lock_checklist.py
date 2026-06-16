"""Lock-day checklist runner tests."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.lock_checklist import (  # noqa: E402
    _extract_checklist_rows,
    build_lock_checklist_report,
    write_lock_checklist_report,
)


NOW = datetime(2026, 6, 22, 10, 0, tzinfo=timezone.utc)


def _verified_provider_report() -> dict[str, object]:
    return {
        "schema_version": "governed_agent_bench.provider_probe.v1",
        "overall_status": "verified_live",
        "conditions": [],
    }


def test_extract_checklist_rows_from_synthetic_section() -> None:
    text = """# Protocol

## §14 Lock Procedure

- [ ] First row starts here
      and continues here.
- [ ] Second row.

## Locked Hashes
"""

    rows = _extract_checklist_rows(text)

    assert rows == [
        "First row starts here and continues here.",
        "Second row.",
    ]


def test_lock_checklist_report_uses_mocked_provider_probe() -> None:
    report = build_lock_checklist_report(
        now_utc=NOW,
        live_provider_probe=True,
        provider_report_builder=_verified_provider_report,
    )

    assert report["schema_version"] == "governed_agent_bench.lock_checklist.v1"
    assert report["generated_at_utc"] == "2026-06-22T10:00:00Z"
    assert report["no_lock_doc_mutation"] is True
    assert report["mechanical_checks"]["provider_probe"]["status"] == "pass"
    assert report["mechanical_checks"]["lock_hashes"]["status"] == "pass"
    assert report["mechanical_checks"]["l7_turn_budget"]["status"] == "pass"
    assert report["mechanical_checks"]["safety_subset"]["status"] == "pass"
    assert report["mechanical_checks"]["schema_json_parse"]["status"] == "pass"
    assert report["overall_status"] == "pending_operator_confirmation"
    assert any(
        row["status"] == "pending_operator_confirmation"
        for row in report["checklist_rows"]
    )


def test_lock_checklist_writer_emits_json_and_markdown(tmp_path: Path) -> None:
    output = write_lock_checklist_report(
        output_dir=tmp_path,
        now_utc=NOW,
        live_provider_probe=True,
        provider_report_builder=_verified_provider_report,
    )

    json_path = Path(output["json_path"])
    markdown_path = Path(output["markdown_path"])
    assert json_path.exists()
    assert markdown_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")
    assert payload["overall_status"] == output["overall_status"]
    assert "Lock Checklist" in markdown
    assert "Mechanical Checks" in markdown
