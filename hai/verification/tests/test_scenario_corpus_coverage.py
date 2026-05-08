"""W-AH-2 (v0.1.17 §2.C) — scenario-corpus coverage gate.

Walks ``hai/src/health_agent_infra/evals/scenarios/`` and refuses if any
domain falls below the per-domain floor. Per PLAN §2.C target shape:

  - 20 fixtures per domain (recovery / running / sleep / strength /
    nutrition / stress)
  - 12 fixtures for synthesis
  - judge_adversarial is W-AI's corpus, not counted toward W-AH

This test is the W-AH-2 ship gate's structural counterpart to the
``hai eval run --scenario-set all`` 100%-pass-rate gate.
"""

from __future__ import annotations

from pathlib import Path

import pytest


_SCENARIOS_ROOT = (
    Path(__file__).resolve().parents[2]
    / "src" / "health_agent_infra" / "evals" / "scenarios"
)

_PER_DOMAIN_FLOOR: int = 20
_SYNTHESIS_FLOOR: int = 12


def _count_fixtures(domain: str) -> int:
    """Count fixture JSONs in a domain dir, excluding index.json."""

    domain_dir = _SCENARIOS_ROOT / domain
    if not domain_dir.exists():
        return 0
    return sum(
        1 for p in domain_dir.glob("*.json") if p.name != "index.json"
    )


def test_per_domain_floor():
    """Each of the six domains has ≥20 fixtures."""

    for domain in (
        "recovery", "running", "sleep", "strength", "nutrition", "stress",
    ):
        count = _count_fixtures(domain)
        assert count >= _PER_DOMAIN_FLOOR, (
            f"domain {domain!r}: {count} fixtures, below per-domain floor "
            f"of {_PER_DOMAIN_FLOOR}"
        )


def test_synthesis_floor():
    """Synthesis has ≥12 fixtures."""

    count = _count_fixtures("synthesis")
    assert count >= _SYNTHESIS_FLOOR, (
        f"synthesis: {count} fixtures, below floor of {_SYNTHESIS_FLOOR}"
    )


def test_total_corpus_meets_target():
    """The full domain + synthesis corpus is ≥132 fixtures (per PLAN §2.C
    target distribution: 6×20 + 12 = 132)."""

    total = sum(
        _count_fixtures(d) for d in (
            "recovery", "running", "sleep", "strength",
            "nutrition", "stress", "synthesis",
        )
    )
    assert total >= 132, (
        f"total fixture corpus: {total}, below target of 132 "
        f"(6 domains × 20 + 12 synthesis)"
    )


def test_judge_adversarial_excluded_from_w_ah_count():
    """Sanity: judge_adversarial fixtures live in their own dir and
    don't count toward W-AH per PLAN §2.C."""

    ja_dir = _SCENARIOS_ROOT / "judge_adversarial"
    assert ja_dir.exists(), "judge_adversarial dir missing"
    # Has subdirs for bias_probe / prompt_injection / source_conflict.
    sub_count = sum(
        1 for p in ja_dir.iterdir() if p.is_dir()
    )
    assert sub_count >= 3, (
        f"judge_adversarial expected ≥3 subdirs, got {sub_count}"
    )
