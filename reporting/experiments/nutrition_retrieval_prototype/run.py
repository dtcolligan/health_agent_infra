"""
Runs queries.json against the SR Legacy slice and prints top-5 candidates
per query. Manual scoring is recorded in findings.md; this script just
produces the raw retrieval output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from search import load_foods, top_k


HERE = Path(__file__).parent


def main() -> int:
    foods = load_foods(str(HERE / "usda_sr_legacy_food.csv"))
    print(f"loaded {len(foods)} foods from SR Legacy slice", file=sys.stderr)

    queries_doc = json.loads((HERE / "queries.json").read_text())

    output = {"slice_size": len(foods), "results": []}
    for q in queries_doc["queries"]:
        ranked = top_k(q["query"], foods, k=5)
        output["results"].append(
            {
                "id": q["id"],
                "query": q["query"],
                "bucket": q["bucket"],
                "expected_intent": q["expected_intent"],
                "top5": [
                    {
                        "rank": i + 1,
                        "score": round(score, 4),
                        "fdc_id": f.fdc_id,
                        "description": f.description,
                    }
                    for i, (score, f) in enumerate(ranked)
                ],
            }
        )

    out_path = HERE / "results.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"wrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
