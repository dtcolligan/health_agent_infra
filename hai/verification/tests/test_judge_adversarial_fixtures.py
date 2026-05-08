"""W-AI judge-adversarial fixture corpus contract (v0.1.14).

Acceptance: ≥10 fixtures per category for prompt-injection /
source-conflict / bias-probe. Pin shape so v0.2.2 W58J consumers
can rely on the index.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
JA_ROOT = (
    REPO_ROOT
    / "src"
    / "health_agent_infra"
    / "evals"
    / "scenarios"
    / "judge_adversarial"
)


def test_judge_adversarial_index_exists_and_parses():
    index_path = JA_ROOT / "index.json"
    assert index_path.exists()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index["schema_version"] == "judge_adversarial_index.v1"
    assert set(index["categories"].keys()) == {
        "prompt_injection", "source_conflict", "bias_probe",
    }


@pytest.mark.parametrize("category", [
    "prompt_injection", "source_conflict", "bias_probe",
])
def test_each_category_has_at_least_ten_fixtures(category):
    cat_dir = JA_ROOT / category
    assert cat_dir.is_dir()
    fixtures = sorted(cat_dir.glob("*.json"))
    assert len(fixtures) >= 10, (
        f"category {category!r} has {len(fixtures)} fixtures; "
        f"W-AI contract requires ≥10"
    )


def test_every_fixture_has_required_shape():
    for category in ("prompt_injection", "source_conflict", "bias_probe"):
        for path in (JA_ROOT / category).glob("*.json"):
            body = json.loads(path.read_text(encoding="utf-8"))
            assert body["schema_version"] == "judge_adversarial_fixture.v1", (
                f"{path.name}: bad schema_version {body.get('schema_version')!r}"
            )
            assert body["category"] == category, (
                f"{path.name}: category mismatch (file in {category}/, "
                f"declared as {body['category']!r})"
            )
            for required in ("fixture_id", "description", "input", "expected"):
                assert required in body, f"{path.name}: missing {required!r}"
            inp = body["input"]
            for required in ("claim_text", "evidence_locators", "context"):
                assert required in inp, (
                    f"{path.name}: input missing {required!r}"
                )
            exp = body["expected"]
            assert exp["verdict_class"] in {
                "supported", "unsupported", "ambiguous",
            }
            assert isinstance(exp["rationale_keywords_present"], list)
            assert isinstance(exp["rationale_keywords_absent"], list)


def test_every_fixture_filename_matches_fixture_id():
    for category in ("prompt_injection", "source_conflict", "bias_probe"):
        for path in (JA_ROOT / category).glob("*.json"):
            body = json.loads(path.read_text(encoding="utf-8"))
            assert path.stem == body["fixture_id"], (
                f"{path}: fixture_id {body['fixture_id']!r} doesn't match "
                f"filename {path.stem!r}"
            )


def test_index_listing_matches_filesystem():
    index = json.loads((JA_ROOT / "index.json").read_text(encoding="utf-8"))
    for category, listed_ids in index["categories"].items():
        on_disk = sorted(p.stem for p in (JA_ROOT / category).glob("*.json"))
        assert sorted(listed_ids) == on_disk, (
            f"category {category!r}: index lists {sorted(listed_ids)} "
            f"but filesystem has {on_disk}"
        )
