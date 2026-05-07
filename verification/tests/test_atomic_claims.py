"""W-FACT-ATOM parser tests (v0.2.0 §2.E).

Step 1 lands the parser core + classifier + a small set of unit
tests that pin the basic shape. Step 3 grows this file with the
≥98%-precision corpus harness, byte-stable determinism check, and
W52 round-trip integration test.
"""

from __future__ import annotations

from health_agent_infra.core.eval import (
    TypedAtom,
    classify_atom_type,
    derivation_path_for,
    parse_atoms_from_markdown,
)


# ---------------------------------------------------------------------------
# classify_atom_type
# ---------------------------------------------------------------------------


def test_classify_quantitative_on_numeric_token():
    assert classify_atom_type(
        "You ran `hai daily` on 5 of 7 days this week."
    ) == "quantitative"


def test_classify_quantitative_on_month_name_token():
    assert classify_atom_type(
        "On April 28 the recovery recommendation was \"hold\"."
    ) == "quantitative"


def test_classify_comparative_on_phase_a_framing():
    # The exact string the W52 prose builder emits for Phase A
    # firings (prose_builder.py:734-769).
    assert classify_atom_type(
        "Rules that shaped the recommendation: low recovery (X1)."
    ) == "comparative"


def test_classify_comparative_on_phase_b_framing():
    assert classify_atom_type(
        "Rules that adjusted the result after the skill ran: "
        "consecutive low days (X2)."
    ) == "comparative"


def test_classify_comparative_on_comparison_operator_wins_over_numeric():
    # Comparative wins when both shapes appear (priority ordering
    # mirrors W52 prose builder firings emission).
    assert classify_atom_type(
        "Resting heart rate was 7 bpm above the baseline this week."
    ) == "comparative"


def test_classify_qualitative_on_framing_text():
    assert classify_atom_type(
        "This review is informational. Nothing here mutates intent, "
        "targets, or thresholds — that path is user-gated."
    ) == "qualitative"


def test_classify_qualitative_on_deferred_domain_disposition():
    # W52 emits the deferred-domain atom as qualitative
    # (prose_builder.py:470-484).
    assert classify_atom_type(
        "domain stress: insufficient provenance — quantitative and "
        "comparative claims suppressed pending the next provenance cycle"
    ) == "qualitative"


# ---------------------------------------------------------------------------
# derivation_path_for
# ---------------------------------------------------------------------------


def test_derivation_path_mapping_matches_w52_emission():
    assert derivation_path_for("quantitative") == "aggregate"
    assert derivation_path_for("comparative") == "comparison"
    assert derivation_path_for("qualitative") == "literal"


# ---------------------------------------------------------------------------
# parse_atoms_from_markdown — smoke
# ---------------------------------------------------------------------------


def test_parse_atoms_from_minimal_full_render():
    markdown = (
        "# Weekly review — 2026-W18\n"
        "\n"
        "- This review is grounded in plan evidence from the canonical "
        "(non-superseded) version of each day.\n"
        "\n"
        "## Recovery\n"
        "\n"
        "- You received 3 recovery recommendations on April 27, 28, "
        "and 29.\n"
        "\n"
        "## Notes\n"
        "\n"
        "- This review is informational. Nothing here mutates intent, "
        "targets, or thresholds — that path is user-gated.\n"
    )
    atoms = parse_atoms_from_markdown(markdown)
    assert len(atoms) == 3

    # Header bullet — qualitative.
    assert atoms[0].section_id == "header"
    assert atoms[0].atom_type == "qualitative"
    assert atoms[0].derivation_path == "literal"

    # Recovery quantitative — has numeric tokens + dates.
    assert atoms[1].section_id == "domain_recovery"
    assert atoms[1].atom_type == "quantitative"
    assert atoms[1].derivation_path == "aggregate"

    # Footer — qualitative.
    assert atoms[2].section_id == "footer"
    assert atoms[2].atom_type == "qualitative"


def test_parse_atoms_skips_blockquote_lines():
    # The multi-canonical disposition note at render.py:134 starts
    # with `>` and must be skipped (not parsed as a bullet).
    markdown = (
        "# Weekly review — 2026-W18\n"
        "\n"
        "> Multiple plans on this day: surfaced as separate rows in "
        "the per-domain sections below per the F-PHASE0-07 "
        "reconciliation contract.\n"
        "\n"
        "- Plan-grounded review header.\n"
    )
    atoms = parse_atoms_from_markdown(markdown)
    assert len(atoms) == 1
    assert atoms[0].atom_text == "Plan-grounded review header."


def test_parse_atoms_returns_empty_on_abstain_branch_render():
    # The abstain markdown has paragraph lines but no bullets, so
    # the parser correctly returns an empty list. F-PHASE0-02 +
    # F-PLAN-03 — no claim cards on abstain.
    markdown = (
        "# Weekly review — 2026-W18\n"
        "\n"
        "**Insufficient data for this week.**\n"
        "\n"
        "Plans found: 3 of 7 days (threshold: ≥5).\n"
        "Days with plans: 2026-04-30, 2026-05-02, 2026-05-04.\n"
        "Days without plans: 2026-04-27, 2026-04-28, 2026-04-29.\n"
        "\n"
        "Run `hai daily` on past days where you have data, then "
        "re-run this command.\n"
    )
    assert parse_atoms_from_markdown(markdown) == []


def test_parse_atoms_handles_deferred_domain_section():
    # `## <Domain> (deferred)` heading routes to `domain_<lower>`
    # via the `_DEFERRED_SUFFIX` strip path.
    markdown = (
        "## Stress (deferred)\n"
        "\n"
        "- domain stress: insufficient provenance — quantitative and "
        "comparative claims suppressed pending the next provenance cycle\n"
    )
    atoms = parse_atoms_from_markdown(markdown)
    assert len(atoms) == 1
    assert atoms[0].section_id == "domain_stress"
    assert atoms[0].atom_type == "qualitative"


def test_typed_atom_to_dict_contract():
    atom = TypedAtom(
        atom_text="hello",
        atom_type="qualitative",
        derivation_path="literal",
        section_id="footer",
    )
    assert atom.to_dict() == {
        "atom_text": "hello",
        "atom_type": "qualitative",
        "derivation_path": "literal",
        "section_id": "footer",
    }
