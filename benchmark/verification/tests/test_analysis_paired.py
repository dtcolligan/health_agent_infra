"""Tests for the within-family paired capability analysis (analysis.paired)."""

from __future__ import annotations

from governed_agent_bench.analysis.frame import CAPABLE, WEAK, AnalysisFrame, AnalysisRow
from governed_agent_bench.analysis.paired import (
    collapse_to_lineage,
    default_lineage_of,
    family_differences,
    paired_report,
    signflip_permutation_p,
)


def _cellB_rows(
    family: str, cap_k: int, cap_n: int, weak_k: int, weak_n: int
) -> list[AnalysisRow]:
    """Cell-B (told + unenforced) rows for one family's capable and weak member."""

    rows: list[AnalysisRow] = []
    for i in range(cap_n):
        rows.append(AnalysisRow(
            scenario_id="commit", task_id="gab_l6_agentsafe_told",
            model_id=f"{family}-big", model_family=family, provider="Fireworks",
            capability_band=CAPABLE, told=True, enforced=False, salience=0,
            safe=(i < cap_k),
        ))
    for i in range(weak_n):
        rows.append(AnalysisRow(
            scenario_id="commit", task_id="gab_l6_agentsafe_told",
            model_id=f"{family}-small", model_family=family, provider="Fireworks",
            capability_band=WEAK, told=True, enforced=False, salience=0,
            safe=(i < weak_k),
        ))
    return rows


def test_family_differences_are_within_family_cellB_deltas() -> None:
    # Capable self-enforces (3/3 safe), weak violates (0/3) -> delta = +1.0.
    frame = AnalysisFrame(_cellB_rows("qwen2.5", cap_k=3, cap_n=3, weak_k=0, weak_n=3))
    diffs = family_differences(frame)
    assert len(diffs) == 1
    assert diffs[0].family == "qwen2.5"
    assert diffs[0].lineage == "qwen"
    assert diffs[0].delta == 1.0


def test_family_excluded_when_missing_a_band() -> None:
    # A family with only a capable member cannot form a within-family difference.
    rows = [r for r in _cellB_rows("mistral", 3, 3, 0, 3) if r.capability_band == CAPABLE]
    assert family_differences(AnalysisFrame(rows)) == []


def test_permutation_floor_when_all_families_agree() -> None:
    # Four families, each a clean +1.0 crossover -> observed mean is the unique
    # extreme -> exact p == 1/2**4 == the floor. This is the F=4 power limit that
    # a fifth/sixth pair relaxes.
    rows: list[AnalysisRow] = []
    for fam in ("qwen2.5", "qwen3", "llama3.1", "mistral"):
        rows += _cellB_rows(fam, cap_k=4, cap_n=4, weak_k=0, weak_n=4)
    deltas = [d.delta for d in family_differences(AnalysisFrame(rows))]
    result = signflip_permutation_p(deltas)
    assert result["n"] == 4
    assert result["p_one_sided"] == 0.0625
    assert result["p_floor"] == 0.0625


def test_permutation_p_rises_with_a_discordant_family() -> None:
    # Three families +1.0, one reversed -1.0 -> p climbs off the floor (the
    # discordant-family sensitivity the design's buffer is for).
    deltas = [1.0, 1.0, 1.0, -1.0]
    result = signflip_permutation_p(deltas)
    assert result["p_one_sided"] == 0.3125  # C(4,3)+C(4,4) = 5 of 16
    assert result["p_one_sided"] > result["p_floor"]


def test_permutation_null_no_effect_is_p_one() -> None:
    # No within-family effect (all deltas 0) -> every arrangement ties -> p == 1.0.
    assert signflip_permutation_p([0.0, 0.0, 0.0])["p_one_sided"] == 1.0
    assert signflip_permutation_p([])["p_one_sided"] == 1.0


def test_lineage_collapse_averages_same_lineage_generations() -> None:
    # qwen2.5 and qwen3 both map to the "qwen" lineage and are averaged so the two
    # Qwen generation pairs count once (the conservative unit).
    frame = AnalysisFrame(
        _cellB_rows("qwen2.5", 4, 4, 0, 4)   # delta +1.0
        + _cellB_rows("qwen3", 3, 4, 1, 4)   # delta +0.5
        + _cellB_rows("llama3.1", 4, 4, 0, 4)  # delta +1.0
    )
    diffs = family_differences(frame)
    lineage = dict(collapse_to_lineage(diffs))
    assert lineage["qwen"] == 0.75  # (1.0 + 0.5) / 2
    assert lineage["llama"] == 1.0
    assert default_lineage_of("llama3.3") == "llama"


def test_paired_report_separates_pair_and_lineage_units() -> None:
    rows: list[AnalysisRow] = []
    for fam in ("qwen2.5", "qwen3", "llama3.1", "mistral"):
        rows += _cellB_rows(fam, cap_k=4, cap_n=4, weak_k=0, weak_n=4)
    report = paired_report(AnalysisFrame(rows))
    assert report["n_families"] == 4
    assert report["n_lineages"] == 3  # qwen2.5 + qwen3 collapse to one
    # Pair-level (4 units) beats lineage-level (3 units) on attainable floor.
    assert report["pair_level"]["permutation"]["p_floor"] == 0.0625
    assert report["lineage_level"]["permutation"]["p_floor"] == 0.125
