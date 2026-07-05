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


# --------------------------------------------------------------------------- #
# IB-7: untold-leak lock gate (locked decision 10)
# --------------------------------------------------------------------------- #


def test_untold_leak_scan_passes_on_committed_suite() -> None:
    from governed_agent_bench.lock_checklist import _check_untold_leak_scan

    check = _check_untold_leak_scan()

    assert check["status"] == "pass"
    assert check["template_id"] == "deployment_full_v2"
    assert check["tasks"], "the suite has untold tasks; the scan must see them"
    scanned_ids = {row["task_id"] for row in check["tasks"]}
    assert "gab_l6_agentsafe_untold" in scanned_ids
    assert "gab_l6_proposalgate_untold" in scanned_ids
    for row in check["tasks"]:
        assert row["status"] == "pass", row
        assert row["leaked_tokens"] == [], row


def test_untold_leak_scan_is_wired_into_the_checklist_report() -> None:
    report = build_lock_checklist_report(
        now_utc=NOW,
        live_provider_probe=True,
        provider_report_builder=_verified_provider_report,
    )

    assert report["mechanical_checks"]["untold_leak_scan"]["status"] == "pass"
    assert "context_window_budget" in report["mechanical_checks"]


# --------------------------------------------------------------------------- #
# IB-3: context-window budget lock gate
# --------------------------------------------------------------------------- #


def _roster_condition_stub(condition_id: str, **overrides: object) -> dict[str, object]:
    condition: dict[str, object] = {
        "condition_id": condition_id,
        "prompt_id": "deployment_full_v2",
        "decoding_settings": {"temperature": 0, "max_tokens": 2048},
    }
    condition.update(overrides)
    return condition


def test_context_window_budget_pending_without_context_window_field() -> None:
    from governed_agent_bench.lock_checklist import _check_context_window_budget

    check = _check_context_window_budget(
        roster={"conditions": [_roster_condition_stub("no_window_yet")]}
    )

    assert check["status"] == "pending"
    row = check["conditions"][0]
    assert row["status"] == "pending"
    assert "pending roster_v3" in row["detail"]


def test_context_window_budget_pass_and_fail_math() -> None:
    from governed_agent_bench.lock_checklist import (
        CHARS_PER_TOKEN_ESTIMATE,
        MAX_TURNS,
        _check_context_window_budget,
    )
    from governed_agent_bench.harness.model_actions import FEEDBACK_STDOUT_MAX_CHARS

    roomy = _roster_condition_stub("roomy", context_window=262_144)
    tight = _roster_condition_stub("tight", context_window=8_192)
    check = _check_context_window_budget(
        roster={"conditions": [roomy, tight]}
    )

    assert check["status"] == "fail"
    rows = {row["condition_id"]: row for row in check["conditions"]}
    assert rows["roomy"]["status"] == "pass"
    assert rows["tight"]["status"] == "fail"
    # Re-derive the pre-registered formula against the emitted numbers.
    row = rows["roomy"]
    expected = row["base_prompt_chars"] / CHARS_PER_TOKEN_ESTIMATE + MAX_TURNS * (
        2048 + FEEDBACK_STDOUT_MAX_CHARS / CHARS_PER_TOKEN_ESTIMATE
    )
    assert abs(row["estimated_worst_case_tokens"] - expected) < 1.0
    assert row["budget_tokens"] == 262_144 - 2048
    assert rows["roomy"]["max_turns"] == MAX_TURNS


def test_context_window_budget_on_committed_roster_is_pending_not_fail() -> None:
    """roster_v2 has no context_window fields yet: the gate must tolerate
    absence as pending, never fail the checklist on a missing field."""

    from governed_agent_bench.lock_checklist import _check_context_window_budget

    check = _check_context_window_budget()

    assert check["status"] in {"pending", "pass"}
    assert all(row["status"] != "fail" for row in check["conditions"])
