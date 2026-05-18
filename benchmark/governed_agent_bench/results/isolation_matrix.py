"""Deterministic, offline static isolation-matrix generator (D-17).

Evaluates every per-mechanism and composite hand-authored oracle pair
against the D-17 mode-aware scorer criterion and emits
isolation_matrix.json. No model calls. This is static scorer/coverage
evidence, not standalone live mechanism-causality evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from governed_agent_bench.oracles import (
    COMPOSITE_OFF_MODE,
    COMPOSITE_PROOF_CASES,
    MECHANISM_OFF_MODES,
    isolation_verdict,
    iter_mechanism_cases,
)

SCHEMA_VERSION = "governed_agent_bench.isolation_matrix.v1"


def build_isolation_matrix() -> dict[str, Any]:
    rows: list[dict[str, Any]] = [
        isolation_verdict(
            case, label=mechanism, off_mode=MECHANISM_OFF_MODES[mechanism]
        )
        for mechanism, case in iter_mechanism_cases()
    ]
    rows.extend(
        isolation_verdict(case, label="composite", off_mode=COMPOSITE_OFF_MODE)
        for case in COMPOSITE_PROOF_CASES
    )
    rows.sort(key=lambda row: (row["label"], row["task_id"], row["off_mode"]))

    per_label: dict[str, dict[str, int]] = {}
    for row in rows:
        bucket = per_label.setdefault(row["label"], {"total": 0, "isolated": 0})
        bucket["total"] += 1
        bucket["isolated"] += 1 if row["isolated"] else 0

    return {
        "schema_version": SCHEMA_VERSION,
        "evidence_tier": "static_oracle_pairs",
        "scope_note": (
            "Hand-authored full/off oracle pairs check scorer sensitivity, "
            "declared coverage, and contamination handling. Live mechanism "
            "causality is reported separately by live_isolation.py."
        ),
        "model_calls": False,
        "row_count": len(rows),
        "all_isolated": all(row["isolated"] for row in rows),
        "all_static_oracle_pairs_isolated": all(row["isolated"] for row in rows),
        "per_label": dict(sorted(per_label.items())),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    matrix = build_isolation_matrix()
    path = out / "isolation_matrix.json"
    path.write_text(
        json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "artifact": str(path),
                "row_count": matrix["row_count"],
                "all_isolated": matrix["all_isolated"],
                "model_calls": matrix["model_calls"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if matrix["all_isolated"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
