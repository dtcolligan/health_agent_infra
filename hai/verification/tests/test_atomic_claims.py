"""W-FACT-ATOM parser tests (v0.2.0 §2.E).

Step 1: classifier coverage + smoke unit tests.
Step 3: ≥98%-precision corpus harness + byte-stable determinism +
W52 in-memory round-trip integration.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from health_agent_infra.core.eval import (
    TypedAtom,
    classify_atom_type,
    derivation_path_for,
    parse_atoms_from_markdown,
)


CORPUS_DIR = (
    Path(__file__).resolve().parents[1].parent
    / "src" / "health_agent_infra" / "evals" / "scenarios" / "atomic_claims"
)


def _load_corpus_fixtures() -> list[dict]:
    """Load every ``ac_*.json`` fixture from the corpus directory."""

    fixtures = []
    for path in sorted(CORPUS_DIR.glob("ac_*.json")):
        fixtures.append(json.loads(path.read_text()))
    return fixtures


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


# ---------------------------------------------------------------------------
# Step 3 — corpus precision + determinism + W52 round-trip integration
# ---------------------------------------------------------------------------


def test_corpus_index_manifest_total_equals_fixture_count():
    """Sanity: ``index.json`` ``total_fixtures`` matches the actual
    on-disk fixture count and the manifest's ``fixtures`` array
    length."""

    manifest = json.loads((CORPUS_DIR / "index.json").read_text())
    on_disk_count = len(list(CORPUS_DIR.glob("ac_*.json")))
    assert manifest["total_fixtures"] == on_disk_count == 30
    assert len(manifest["fixtures"]) == 30


def test_corpus_fixture_categories_cover_every_fixture():
    """Sanity: every fixture in the manifest's ``fixtures`` array has
    a matching entry in the ``categories`` mapping (no orphan IDs).
    """

    manifest = json.loads((CORPUS_DIR / "index.json").read_text())
    fixture_ids = {f["fixture_id"] for f in manifest["fixtures"]}
    flat_category_ids = {
        fid
        for ids in manifest["categories"].values()
        for fid in ids
    }
    assert fixture_ids == flat_category_ids


def test_corpus_precision_meets_98_percent_threshold():
    """PLAN §2.E acceptance #1: parser outputs match expected atoms
    at ≥98% precision over the 30-fixture corpus.

    Precision = correctly-classified parser atoms / total parser
    output atoms. An atom is correctly classified when its
    ``(atom_text, atom_type, derivation_path, section_id)`` tuple
    appears in the fixture's ground-truth ``expected.atoms`` list.
    """

    fixtures = _load_corpus_fixtures()
    total_parsed = 0
    total_correct = 0

    for fixture in fixtures:
        markdown = fixture["input"]["markdown"]
        expected_atoms = fixture["expected"]["atoms"]
        parsed = parse_atoms_from_markdown(markdown)

        expected_keyed = {
            (
                a["atom_text"],
                a["atom_type"],
                a["derivation_path"],
                a["section_id"],
            )
            for a in expected_atoms
        }
        for atom in parsed:
            total_parsed += 1
            key = (
                atom.atom_text,
                atom.atom_type,
                atom.derivation_path,
                atom.section_id,
            )
            if key in expected_keyed:
                total_correct += 1

    # If the corpus had only abstain-branch fixtures the parser would
    # output 0 atoms — guard against a vacuous pass.
    assert total_parsed > 0, "corpus must have at least one parsed atom"
    precision = total_correct / total_parsed
    assert precision >= 0.98, (
        f"parser precision {precision:.4f} ({total_correct}/{total_parsed}) "
        f"below the ≥0.98 threshold required by PLAN §2.E acceptance #1"
    )


def test_corpus_recall_on_quantitative_and_comparative_atoms_is_100_percent():
    """W58D-validatable atoms (quantitative + comparative) must have
    100% recall — every expected quantitative or comparative atom must
    surface in the parser output. This is the gate-correctness contract:
    if the parser drops a quantitative atom, W58D never sees it and
    can't validate it.
    """

    fixtures = _load_corpus_fixtures()
    expected_w58d_atoms: list[tuple[str, ...]] = []
    parsed_w58d_atoms: set[tuple[str, ...]] = set()

    for fixture in fixtures:
        markdown = fixture["input"]["markdown"]
        for a in fixture["expected"]["atoms"]:
            if a["atom_type"] in ("quantitative", "comparative"):
                expected_w58d_atoms.append((
                    a["atom_text"], a["atom_type"],
                    a["derivation_path"], a["section_id"],
                ))
        for atom in parse_atoms_from_markdown(markdown):
            if atom.atom_type in ("quantitative", "comparative"):
                parsed_w58d_atoms.add((
                    atom.atom_text, atom.atom_type,
                    atom.derivation_path, atom.section_id,
                ))

    missing = [
        e for e in expected_w58d_atoms if e not in parsed_w58d_atoms
    ]
    assert not missing, (
        f"parser dropped {len(missing)} W58D-validatable atom(s): "
        f"{missing[:3]}{'...' if len(missing) > 3 else ''}"
    )


def test_parser_output_byte_stable_across_three_runs():
    """PLAN §2.E acceptance #3: same input markdown → same atom list
    across runs. Pin determinism by parsing the same fixture three
    times and asserting full structural equality.
    """

    fixture = json.loads(
        (CORPUS_DIR / "ac_029_high_atom_density.json").read_text()
    )
    markdown = fixture["input"]["markdown"]
    runs = [
        [a.to_dict() for a in parse_atoms_from_markdown(markdown)]
        for _ in range(3)
    ]
    assert runs[0] == runs[1] == runs[2]
    # And: serialised JSON is byte-identical (extra paranoia against
    # dict-ordering or encoding drift).
    serialised = [
        json.dumps(r, sort_keys=True) for r in runs
    ]
    assert serialised[0] == serialised[1] == serialised[2]


def test_atom_text_byte_identical_to_ground_truth():
    """The parser must NOT munge atom text — no whitespace stripping
    beyond the single trailing-space the bullet regex permits, no
    encoding drift, no character substitution.
    """

    fixtures = _load_corpus_fixtures()
    for fixture in fixtures:
        markdown = fixture["input"]["markdown"]
        expected_texts = {
            a["atom_text"] for a in fixture["expected"]["atoms"]
        }
        parsed_texts = {
            a.atom_text for a in parse_atoms_from_markdown(markdown)
        }
        # Every parsed atom's text must appear in the expected set.
        assert parsed_texts <= expected_texts, (
            f"fixture {fixture['fixture_id']}: parser produced atom "
            f"text(s) not in ground truth: "
            f"{parsed_texts - expected_texts}"
        )


def test_full_render_minimal_round_trip_preserves_atom_type():
    """Per-fixture round-trip on the ``full_render_minimal`` category:
    every expected atom is recovered with the same ``atom_type`` tag.
    """

    fixtures = [
        f for f in _load_corpus_fixtures()
        if f["category"] == "full_render_minimal"
    ]
    assert len(fixtures) == 5

    for fixture in fixtures:
        markdown = fixture["input"]["markdown"]
        parsed = parse_atoms_from_markdown(markdown)
        parsed_by_text = {a.atom_text: a for a in parsed}
        for expected in fixture["expected"]["atoms"]:
            atom_text = expected["atom_text"]
            assert atom_text in parsed_by_text, (
                f"{fixture['fixture_id']}: missing atom {atom_text!r}"
            )
            assert parsed_by_text[atom_text].atom_type == expected["atom_type"], (
                f"{fixture['fixture_id']}: atom_type drift on "
                f"{atom_text!r} — expected {expected['atom_type']}, "
                f"got {parsed_by_text[atom_text].atom_type}"
            )


def test_full_render_with_firings_classifies_phase_atoms_as_comparative():
    """For every firings-bearing fixture, atoms whose text starts
    with ``Rules that shaped`` or ``Rules that adjusted`` are
    classified as ``comparative`` (W52's emission tagging).
    """

    fixtures = [
        f for f in _load_corpus_fixtures()
        if f["category"] == "full_render_with_firings"
    ]
    assert len(fixtures) == 5

    for fixture in fixtures:
        markdown = fixture["input"]["markdown"]
        parsed = parse_atoms_from_markdown(markdown)
        phase_atoms = [
            a for a in parsed
            if a.atom_text.startswith("Rules that shaped")
            or a.atom_text.startswith("Rules that adjusted")
        ]
        assert phase_atoms, (
            f"{fixture['fixture_id']}: firings fixture must yield ≥1 "
            f"Phase A/B atom"
        )
        for atom in phase_atoms:
            assert atom.atom_type == "comparative", (
                f"{fixture['fixture_id']}: Phase atom {atom.atom_text!r} "
                f"misclassified as {atom.atom_type}"
            )


def test_abstain_branch_fixtures_yield_zero_atoms():
    """All abstain-branch fixtures must yield zero atoms when parsed
    (per F-PHASE0-02 + F-PLAN-03 — abstain prose is paragraph text,
    not bullets, and contains no claim-card-eligible atoms).
    """

    fixtures = [
        f for f in _load_corpus_fixtures()
        if f["category"] == "abstain_branch"
    ]
    assert len(fixtures) == 3

    for fixture in fixtures:
        assert fixture["expected"]["atom_count"] == 0
        markdown = fixture["input"]["markdown"]
        parsed = parse_atoms_from_markdown(markdown)
        assert parsed == [], (
            f"{fixture['fixture_id']}: abstain branch must yield 0 atoms, "
            f"got {len(parsed)}"
        )


def test_deferred_domain_disposition_classified_as_qualitative():
    """Every deferred-domain fixture's disposition atom (text
    starting with ``"domain "`` and ending with the deictic ``"the
    next provenance cycle"`` phrase) must classify as
    ``qualitative`` after the F-PLAN-10 alignment fix.
    """

    fixtures = [
        f for f in _load_corpus_fixtures()
        if f["category"] == "deferred_domain"
    ]
    assert len(fixtures) == 5

    for fixture in fixtures:
        markdown = fixture["input"]["markdown"]
        parsed = parse_atoms_from_markdown(markdown)
        disposition_atoms = [
            a for a in parsed
            if a.atom_text.startswith("domain ")
            and "insufficient provenance" in a.atom_text
        ]
        assert disposition_atoms, (
            f"{fixture['fixture_id']}: deferred fixture must yield ≥1 "
            f"disposition atom"
        )
        for atom in disposition_atoms:
            assert atom.atom_type == "qualitative", (
                f"{fixture['fixture_id']}: disposition "
                f"{atom.atom_text!r} misclassified as {atom.atom_type}"
            )


def test_w52_in_memory_round_trip_preserves_atom_type():
    """Build a fresh ``WeeklyProseBundle`` in-memory using the W52
    prose builder, render it to markdown, parse the markdown back
    with W-FACT-ATOM, and assert the round-trip preserves
    ``atom_type`` for every atom.

    This test does NOT use the corpus — it constructs a bundle from
    scratch via the same path the live ``hai review weekly`` command
    uses, so it pins the round-trip property end-to-end against the
    actual prose builder (not against frozen corpus output).
    """

    from health_agent_infra.core.review.prose_builder import (
        build_weekly_prose,
    )
    from health_agent_infra.core.review.render import render_markdown
    from health_agent_infra.core.review.weekly import (
        CanonicalPlanRow, DataQualityClassification, WeeklyAggregation,
        WeeklyCoverage, WeeklyDataQualityRollup, WeeklyRecommendation,
        WeeklyRuntimeEventRow, WeeklySyncRunRow, WeeklyXRuleFiring,
    )

    iso_week = "2026-W18"
    user_id = "u_round_trip"
    week_dates = [
        "2026-04-27", "2026-04-28", "2026-04-29",
        "2026-04-30", "2026-05-01",
    ]
    plans = [
        CanonicalPlanRow(
            daily_plan_id=f"plan_{d}", user_id=user_id, for_date=d,
            synthesized_at=f"{d}T07:00:00Z",
            recommendation_ids=[], proposal_ids=[], x_rules_fired=[],
            synthesis_meta=None, superseded_by_plan_id=None,
            superseded_at=None,
        )
        for d in week_dates
    ]
    recs = [
        WeeklyRecommendation(
            recommendation_id=f"rec_{d}_recovery",
            daily_plan_id=f"plan_{d}", user_id=user_id, for_date=d,
            domain="recovery", action="easy_recovery",
            confidence="high", bounded=True,
            issued_at=f"{d}T07:05:00Z",
            payload={"action": "easy_recovery", "domain": "recovery"},
            evidence_locators=[],
        )
        for d in week_dates[:3]
    ]
    firings = [
        WeeklyXRuleFiring(
            firing_id=1, daily_plan_id=f"plan_{week_dates[1]}",
            user_id=user_id, x_rule_id="X1", tier="soften",
            affected_domain="recovery", trigger_note="round-trip",
            mutation=None, source_signals={},
            fired_at=f"{week_dates[1]}T07:00:30Z",
        ),
    ]
    sync_runs = [
        WeeklySyncRunRow(
            sync_id=i + 1, source="intervals_icu", user_id=user_id,
            mode="live", started_at=f"{d}T07:00:00Z",
            completed_at=f"{d}T07:00:30Z", status="ok", for_date=d,
        )
        for i, d in enumerate(week_dates)
    ]
    runtime_events = [
        WeeklyRuntimeEventRow(
            event_id=i + 1, command="hai daily", user_id=user_id,
            started_at=f"{d}T07:00:00Z", completed_at=f"{d}T07:00:30Z",
            status="ok", exit_code=0,
        )
        for i, d in enumerate(week_dates)
    ]
    agg = WeeklyAggregation(
        iso_week=iso_week, user_id=user_id, week_dates=week_dates,
        canonical_plans=plans, recommendations=recs,
        x_rule_firings=firings, review_outcomes=[], evidence_cards=[],
        accepted_state_rows=[], data_quality_rows=[],
        sync_runs=sync_runs, runtime_events=runtime_events,
        intent_rows=[], target_rows=[],
    )
    coverage = WeeklyCoverage(
        weekly_status="ok", iso_week=iso_week,
        days_with_plans=5, coverage_threshold=5,
        populated_dates=list(week_dates), missing_dates=[],
    )
    rollup = WeeklyDataQualityRollup(
        threshold_hours=48, per_sync=[
            DataQualityClassification(
                sync_id=i + 1, source="intervals_icu", mode="live",
                started_at=f"{d}T07:00:00Z", for_date=d,
                gap_hours=0.5, classification="fresh",
            )
            for i, d in enumerate(week_dates)
        ],
        fresh_count=5, stale_pull_count=0,
        retrospective_manual_count=0, unclassifiable_count=0,
    )

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE user_memory ("
        " user_id TEXT NOT NULL, key TEXT NOT NULL, value TEXT,"
        " archived_at TEXT, created_at TEXT NOT NULL)"
    )
    conn.execute(
        "INSERT INTO user_memory VALUES (?, 'primary_goal', ?, NULL, ?)",
        (user_id, "round-trip goal", "2026-04-20T08:00:00Z"),
    )
    conn.commit()

    try:
        bundle = build_weekly_prose(conn, agg, coverage, rollup)
    finally:
        conn.close()

    markdown = render_markdown(bundle)
    parsed = parse_atoms_from_markdown(markdown)
    parsed_by_text = {a.atom_text: a.atom_type for a in parsed}

    # Every W52-emitted atom must be recovered with the same atom_type.
    for section in bundle.sections:
        for atom in section.atoms:
            assert atom.atom_text in parsed_by_text, (
                f"round-trip dropped atom {atom.atom_text!r}"
            )
            assert parsed_by_text[atom.atom_text] == atom.atom_type, (
                f"round-trip atom_type drift on {atom.atom_text!r}: "
                f"W52 emitted {atom.atom_type}, parser said "
                f"{parsed_by_text[atom.atom_text]}"
            )
