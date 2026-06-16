"""M7 benign negative-control corpus regression tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BENCHMARK_ROOT.parent
HAI_SRC = REPO_ROOT / "hai" / "src"
for path in (BENCHMARK_ROOT, HAI_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from health_agent_infra.core.refusal.clinical import (  # noqa: E402
    BANNED_CLINICAL_PHRASES,
    scan_clinical_phrases,
)


CORPUS_PATH = (
    BENCHMARK_ROOT
    / "governed_agent_bench"
    / "refusal_negative_controls"
    / "m7_benign_negative_controls.jsonl"
)
EXPECTED_FAMILIES = {"L1", "L2", "L5", "L6", "L7"}
EXPECTED_SURFACES = {"final", "refusal", "structured_json", "json_exempt"}


def _load_corpus() -> list[dict[str, Any]]:
    entries = []
    for line_no, raw in enumerate(CORPUS_PATH.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise AssertionError(f"{CORPUS_PATH}:{line_no}: entry must be object")
        entries.append(payload)
    return entries


def test_m7_negative_control_corpus_is_stratified_and_public_safe() -> None:
    entries = _load_corpus()

    assert len(entries) >= 84
    ids = [str(entry["id"]) for entry in entries]
    assert len(ids) == len(set(ids))
    assert {entry["stratum"].split("_", 1)[0] for entry in entries} == EXPECTED_FAMILIES
    assert {entry["surface"] for entry in entries} == EXPECTED_SURFACES
    assert any("_wellness" in str(entry["stratum"]) for entry in entries)
    assert any(entry["surface"] == "refusal" for entry in entries)
    assert any(entry["surface"] == "final" for entry in entries)
    assert any(entry["surface"] == "json_exempt" for entry in entries)

    for entry in entries:
        assert {"id", "stratum", "surface", "text", "rationale"} <= set(entry)
        assert isinstance(entry["text"], str) and entry["text"].strip()
        text_blob = json.dumps(entry, sort_keys=True)
        assert "mock-api-key" not in text_blob
        assert "TOGETHER_API_KEY" not in text_blob
        assert "FIREWORKS_API_KEY" not in text_blob
        assert "ANTHROPIC_API_KEY" not in text_blob


def test_m7_detector_has_zero_clinical_claim_hits_on_negative_controls() -> None:
    entries = _load_corpus()

    assert "diagnosis" in BANNED_CLINICAL_PHRASES
    assert "medical advice" in BANNED_CLINICAL_PHRASES
    for entry in entries:
        haystack = "\n".join(
            str(entry[key]) for key in ("stratum", "surface", "text", "rationale")
        )
        matches = scan_clinical_phrases(haystack)
        assert matches == (), (entry["id"], [match.to_dict() for match in matches])
