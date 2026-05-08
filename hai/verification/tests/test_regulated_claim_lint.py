"""W-LINT (v0.1.13) — regulated-claim lint contracts.

Surfaces pinned:

  1. **Static scan green on packaged skills.** Every packaged
     `SKILL.md` passes the lint under its own provenance (allowlisted
     skills get the exception path; everyone else runs strict).
     A new skill that ships with a regulated-term violation fails
     here — merge-blocking.

  2. **Runtime check is strict regardless of skill provenance.**
     Even an allowlisted-skill's properly-cited block fails the
     runtime check when it crosses the CLI rendering boundary.
     (F-PLAN-09 constraint 4.)

  3. **Exception path is bounded by the four constraints**
     (`test_regulated_claim_exception_bounded`):
       (a) non-allowlisted skill quoting w/ citation → fails
           ('no_allowlisted_skill').
       (b) allowlisted skill quoting WITHOUT citation → fails
           ('no_citation').
       (c) allowlisted skill quoting in first-person framing → fails
           ('no_quoted_context').
       (d) allowlisted skill + cited + quoted → passes.

  4. **Term coverage matches the documented set.** Drift guard so a
     refactor doesn't silently shrink the banned set.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from health_agent_infra.core.lint import (
    ALLOWLISTED_SKILLS,
    META_DOCUMENT_PRAGMA,
    REGULATED_TERMS,
    RegulatedClaimError,
    runtime_check,
    scan_skill_text,
)


_SKILLS_ROOT = Path(__file__).parent.parent.parent / "src" / "health_agent_infra" / "skills"


# ---------------------------------------------------------------------------
# Term coverage
# ---------------------------------------------------------------------------


def test_term_coverage_matches_v0_1_13_plan():
    """Drift guard: PLAN §2.C W-LINT names this set verbatim."""

    assert REGULATED_TERMS == frozenset({
        "abnormal hrv",
        "biomarker",
        "clinical-grade",
        "cure",
        "diagnose",
        "diagnosis",
        "disease",
        "medical advice",
        "risk score",
        "therapy",
        "treatment",
    })


def test_allowlisted_skills_v0_1_13_ship_set():
    """v0.1.13 ship-set is `expert-explainer` only. Adding a skill
    here is a code-review concern (the skill must justify quoting
    regulated terms in its purpose)."""

    assert ALLOWLISTED_SKILLS == frozenset({"expert-explainer"})


# ---------------------------------------------------------------------------
# Static scan on packaged skills
# ---------------------------------------------------------------------------


def test_packaged_skills_pass_static_lint_under_their_own_provenance():
    """Walk every packaged SKILL.md. Allowlisted skills run the
    exception path; everyone else runs strict. A violation is
    merge-blocking."""

    skill_dirs = sorted(p for p in _SKILLS_ROOT.iterdir() if p.is_dir())
    assert skill_dirs, f"no skills found at {_SKILLS_ROOT}"

    failures: list[str] = []
    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        text = skill_md.read_text(encoding="utf-8")
        violations = scan_skill_text(
            text,
            source_skill=skill_dir.name,
            allow_exception=True,
        )
        if violations:
            failures.append(
                f"{skill_dir.name}/SKILL.md: "
                + "; ".join(str(v) for v in violations[:3])
            )
    assert not failures, "regulated-claim lint failures:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# Runtime check — strict regardless of provenance
# ---------------------------------------------------------------------------


def test_runtime_check_passes_clean_text():
    runtime_check(
        "Today's plan: maintain training routine; sleep window 22:00–07:00."
    )


def test_runtime_check_fails_on_regulated_term_in_first_person():
    with pytest.raises(RegulatedClaimError) as exc_info:
        runtime_check("You should consult medical advice before training today.")
    assert any(v.term == "medical advice" for v in exc_info.value.violations)


def test_runtime_check_fails_even_on_well_cited_quoted_text():
    """F-PLAN-09 constraint 4 — runtime always strict regardless of
    skill provenance. Even a perfectly-cited expert-explainer-style
    block fails when it crosses the CLI rendering boundary."""

    # Same text that would pass `scan_skill_text` under
    # source_skill='expert-explainer'.
    text = (
        'According to [state_model_sleep_debt_band], the term "sleep_debt" '
        "is the term used by this system as defined by the literature; "
        'the literature also defines "biomarker" as the broader category.'
    )
    with pytest.raises(RegulatedClaimError) as exc_info:
        runtime_check(text)
    assert any(v.term == "biomarker" for v in exc_info.value.violations)


# ---------------------------------------------------------------------------
# Static-scan exception path is bounded
# ---------------------------------------------------------------------------


def test_regulated_claim_exception_bounded():
    """The four-constraint exception path: violating ANY constraint
    must produce a violation. Only the all-four-hold case passes."""

    well_formed_text = (
        'According to [state_model_sleep_debt_band], the term "biomarker" '
        "is defined by the literature as a measurable indicator of a "
        "biological state. This system does not compute biomarkers."
    )

    # (a) Non-allowlisted skill — fails on constraint 1.
    violations_a = scan_skill_text(
        well_formed_text,
        source_skill="reporting",  # NOT in allowlist
        allow_exception=True,
    )
    assert violations_a, "non-allowlisted skill should fail constraint 1"
    assert all(v.reason == "no_allowlisted_skill" for v in violations_a)

    # (b) Allowlisted skill but NO citation — fails on constraint 2.
    no_citation_text = (
        'The literature defines "biomarker" as a measurable indicator. '
        "This system does not compute biomarkers."
    )
    violations_b = scan_skill_text(
        no_citation_text,
        source_skill="expert-explainer",
        allow_exception=True,
    )
    assert violations_b, "allowlisted skill without citation should fail constraint 2"
    assert any(v.reason == "no_citation" for v in violations_b)

    # (c) Allowlisted skill + citation but FIRST-PERSON framing
    # (no quote / attribution context) — fails on constraint 3.
    first_person_text = (
        "[state_model_sleep_debt_band] We compute biomarkers for the user. "
        "Our biomarker engine produces a risk score."
    )
    violations_c = scan_skill_text(
        first_person_text,
        source_skill="expert-explainer",
        allow_exception=True,
    )
    assert violations_c, "first-person framing should fail constraint 3"
    assert any(v.reason == "no_quoted_context" for v in violations_c)

    # (d) All four constraints hold → permitted. The same text that
    # passed (a) when the skill was wrong now passes when allowed.
    violations_d = scan_skill_text(
        well_formed_text,
        source_skill="expert-explainer",
        allow_exception=True,
    )
    assert not violations_d, (
        f"four-constraint-hold case should pass; "
        f"got: {[str(v) for v in violations_d]}"
    )


# ---------------------------------------------------------------------------
# Allow-exception False (force strict)
# ---------------------------------------------------------------------------


def test_allow_exception_false_forces_strict_even_for_allowlisted_skill():
    """When the caller explicitly opts out of the exception path
    (e.g. the runtime check), allowlisted skills get no special
    treatment."""

    well_formed_text = (
        'According to [state_model_sleep_debt_band], the term "biomarker" '
        "is defined by the literature as a measurable indicator."
    )
    violations = scan_skill_text(
        well_formed_text,
        source_skill="expert-explainer",
        allow_exception=False,
    )
    assert violations
    assert all(v.reason == "strict_regime" for v in violations)


# ---------------------------------------------------------------------------
# Multi-word phrase detection
# ---------------------------------------------------------------------------


def test_multi_word_phrase_caught_across_whitespace():
    """`medical  advice` (double space) and `medical\\nadvice` (line
    wrap) should both match."""

    for sample in (
        "Get medical advice from a clinician.",
        "Get medical  advice from a clinician.",
        "Get medical\nadvice from a clinician.",
    ):
        with pytest.raises(RegulatedClaimError):
            runtime_check(sample)


def test_substring_does_not_falsely_match():
    """`riskscore` (no space) should NOT match `risk score` —
    whole-word matching only."""

    runtime_check("My riskscore_metric is fine, biom-market data clean.")


# ---------------------------------------------------------------------------
# META_DOCUMENT_PRAGMA — opt-in scope-statement skill files
# ---------------------------------------------------------------------------


def test_meta_document_pragma_suppresses_static_lint():
    """A SKILL.md whose explicit purpose is enumerating banned terms
    (e.g. safety, reporting, expert-explainer) opts in via the
    pragma. Without the pragma, the same text is a violation."""

    text = (
        'Never use diagnosis-shaped language: "diagnosis", "diagnose", '
        '"disease", "treatment".'
    )
    # Without pragma — strict surfaces violations.
    violations = scan_skill_text(text, source_skill="reporting")
    assert violations

    # With pragma — silently suppressed.
    text_with_pragma = META_DOCUMENT_PRAGMA + "\n\n" + text
    violations = scan_skill_text(text_with_pragma, source_skill="reporting")
    assert not violations


def test_meta_document_pragma_bounded_to_allowlist():
    """v0.1.13 IR round 1 F-IR-04: an arbitrary skill cannot suppress
    the static scan by adding the pragma comment. Bypass requires
    BOTH the pragma AND a source skill in
    ``META_DOCUMENT_ALLOWLIST``.

    Three failure modes covered:
      (a) pragma + non-allowlisted skill → still scanned.
      (b) pragma + source_skill=None → still scanned (no skill claim
          means no allowlist match).
      (c) pragma + invented future-skill name → still scanned.
    """

    from health_agent_infra.core.lint import META_DOCUMENT_ALLOWLIST

    text_with_pragma = (
        META_DOCUMENT_PRAGMA + "\n\n"
        'Never use diagnosis-shaped language: "diagnosis", "disease".'
    )

    # (a) Non-allowlisted but real skill — still scanned.
    non_meta_real_skills = ["nutrition-alignment", "intent-router", "writeback-protocol"]
    for skill_name in non_meta_real_skills:
        assert skill_name not in META_DOCUMENT_ALLOWLIST, (
            f"test fixture stale: {skill_name} is in the meta-doc "
            f"allowlist; pick a different non-meta skill"
        )
        violations = scan_skill_text(
            text_with_pragma, source_skill=skill_name,
        )
        assert violations, (
            f"pragma + {skill_name!r} should NOT bypass; pragma is "
            f"only honored for allowlisted meta-document skills"
        )

    # (b) source_skill=None — pragma alone is insufficient.
    violations_none = scan_skill_text(text_with_pragma, source_skill=None)
    assert violations_none, (
        "pragma + source_skill=None should NOT bypass; bypass requires "
        "an explicit allowlisted source claim"
    )

    # (c) Invented future-skill name — pragma alone is insufficient.
    violations_invented = scan_skill_text(
        text_with_pragma, source_skill="newly-invented-future-skill",
    )
    assert violations_invented, (
        "pragma + invented-skill-name should NOT bypass; allowlist "
        "must be deliberately edited to add new meta-document skills"
    )

    # Sanity: each of the 3 allowlisted skills DOES bypass under
    # the pragma. The bound is on the source check, not the pragma.
    for skill_name in sorted(META_DOCUMENT_ALLOWLIST):
        violations_allowed = scan_skill_text(
            text_with_pragma, source_skill=skill_name,
        )
        assert not violations_allowed, (
            f"{skill_name!r} is in META_DOCUMENT_ALLOWLIST; pragma "
            f"should bypass scan but got {violations_allowed!r}"
        )


def test_meta_document_pragma_does_not_suppress_runtime_check():
    """The runtime CLI-boundary check ignores the pragma — meta-
    documents never get rendered to the user, so the pragma is
    static-only by design (F-PLAN-09 constraint 4)."""

    text = (
        META_DOCUMENT_PRAGMA + "\n\n"
        "You should consult medical advice."
    )
    with pytest.raises(RegulatedClaimError):
        runtime_check(text)


def test_v0_1_13_meta_document_skills_carry_pragma():
    """The three v0.1.13 ship-set meta-document skills (safety,
    reporting, expert-explainer) carry the pragma. Adding a new
    skill that needs the pragma must update this test deliberately."""

    expected_with_pragma = {"safety", "reporting", "expert-explainer"}
    for name in expected_with_pragma:
        skill_md = _SKILLS_ROOT / name / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8")
        assert META_DOCUMENT_PRAGMA in text, (
            f"{name}/SKILL.md is documented as a meta-document skill "
            f"but is missing the pragma {META_DOCUMENT_PRAGMA!r}; "
            f"add it just below the YAML frontmatter."
        )
