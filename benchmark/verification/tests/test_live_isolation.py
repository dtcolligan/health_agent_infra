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
    STATIC_ONLY,
    build_live_isolation_matrix,
)


def test_live_refusal_probe_is_isolated(tmp_path: Path) -> None:
    matrix = build_live_isolation_matrix(tmp_path)

    assert matrix["schema_version"] == "governed_agent_bench.live_isolation.v1"
    assert matrix["evidence_tier"] == "live_runtime_probe"
    assert matrix["scope_note"]
    assert matrix["live_count"] >= 1
    assert matrix["all_live_isolated"] is True

    live = [r for r in matrix["rows"] if r["status"] == "LIVE"]
    assert any(r["label"] == "refusal" for r in live)
    for row in live:
        assert row["live_isolated"] is True, row
        assert row["off_markers"], row
        assert not row["full_markers"], row

    static = [r for r in matrix["rows"] if r["status"] == "STATIC_ONLY"]
    assert {r["label"] for r in static} == set(STATIC_ONLY)
    for row in static:
        assert row["reason"], row
        assert row["live_isolated"] is None, row
