"""WS-2b: the live-HAI D-17 probe is isolated; static gaps are honest.

Runs a real hermetic HAI subprocess (slow, like the offline-repro
tests). Proves D-17 on observed markers for the reachable mechanism
and asserts the unreachable ones are honestly recorded, not faked.
"""

from __future__ import annotations

import sys
from pathlib import Path


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.results.live_isolation import (  # noqa: E402
    EXPECTED_LIVE_LABELS,
    build_live_isolation_matrix,
)


def test_live_refusal_probe_is_isolated(tmp_path: Path) -> None:
    matrix = build_live_isolation_matrix(tmp_path)

    assert matrix["schema_version"] == "governed_agent_bench.live_isolation.v1"
    assert matrix["evidence_tier"] == "live_runtime_probe"
    assert matrix["scope_note"]
    assert matrix["live_count"] == len(EXPECTED_LIVE_LABELS)
    assert matrix["all_live_isolated"] is True
    assert matrix["static_only"] == []
    assert set(matrix["live_labels"]) == set(EXPECTED_LIVE_LABELS)

    live = [r for r in matrix["rows"] if r["status"] == "LIVE"]
    assert {r["label"] for r in live} == set(EXPECTED_LIVE_LABELS)
    for row in live:
        assert row["live_isolated"] is True, row
        assert row["off_markers"], row
        assert not row["full_markers"], row
        assert row["full_overall_pass"] is True, row
        assert row["off_overall_pass"] is False, row
        assert set(row["expected_changed_metrics"]).issubset(
            row["changed_metrics"]
        ), row

    static = [r for r in matrix["rows"] if r["status"] == "STATIC_ONLY"]
    assert static == []
    assert build_live_isolation_matrix(tmp_path) == matrix
