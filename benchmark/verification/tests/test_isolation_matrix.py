"""WS-2: the D-17 static isolation matrix is total, deterministic, offline."""

from __future__ import annotations

import sys
from pathlib import Path


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.oracles import (  # noqa: E402
    COMPOSITE_PROOF_CASES,
    iter_mechanism_cases,
)
from governed_agent_bench.results.isolation_matrix import (  # noqa: E402
    build_isolation_matrix,
)


def test_isolation_matrix_every_pair_isolated() -> None:
    matrix = build_isolation_matrix()

    assert matrix["model_calls"] is False
    assert matrix["evidence_tier"] == "static_oracle_pairs"
    assert matrix["scope_note"]
    assert matrix["row_count"] == len(iter_mechanism_cases()) + len(
        COMPOSITE_PROOF_CASES
    )
    assert matrix["all_isolated"] is True
    assert matrix["all_static_oracle_pairs_isolated"] is True
    for row in matrix["rows"]:
        assert row["isolated"], row
        assert row["contaminated"] is False, row
        assert row["full_overall_pass"] is True, row
        assert row["off_overall_pass"] is False, row
    for label, bucket in matrix["per_label"].items():
        assert bucket["total"] == bucket["isolated"], (label, bucket)


def test_isolation_matrix_is_deterministic() -> None:
    assert build_isolation_matrix() == build_isolation_matrix()
