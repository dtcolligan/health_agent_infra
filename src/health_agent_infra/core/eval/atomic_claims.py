"""Atomic-claim parser — W-FACT-ATOM step 1 (v0.2.0 §2.E).

The structural inverse of ``core/review/render.py``. W52's render
layer collapses typed :class:`WeeklyAtom` rows into uniform
``- <atom_text>`` markdown bullets, stripping atom_id / atom_type /
locator_set / audit_refs. This parser recovers
``(atom_text, atom_type, derivation_path)`` triples from the rendered
markdown deterministically (regex + structural-bullet splitting; no
LLM, per PLAN §2.E + AGENTS.md "Do Not Do" — agents do not
autonomously mutate state).

Provenance NOT recovered. ``locator_set`` + ``audit_refs`` live on
the in-memory :class:`WeeklyProseBundle` and on the JSON render's
per-atom payload (``render.render_json``). They are NOT in the
markdown surface, so this parser cannot recover them. PLAN §2.E
acceptance #2 names the recovered triple as
``(atom_text, atom_type, derivation_path)``; W58D's gate logic pairs
parsed atoms back to provenance via the in-memory bundle / JSON path,
not via markdown.

Atom-type classification rules. Mirror the prose-builder's tagging
heuristics at ``core/review/prose_builder.py`` lines 85-94 and the
section builders' typing decisions:

* **comparative** when the text contains a Phase A / Phase B framing
  marker (``"Rules that shaped the recommendation"`` /
  ``"Rules that adjusted the result after the skill ran"``) or a
  comparison-operator token (``> < <= >= ↑ ↓``,
  ``"more than" / "less than"`` / ``"above the" / "below the"``).
  Comparative wins over quantitative when both shapes appear — the
  comparison IS the factual claim.
* **quantitative** when the text contains a numeric token
  (``\\b\\d+\\b``) or a month-name token (``January..December``).
* **qualitative** otherwise (framing / disposition prose with no
  factual past-week content).

derivation_path mapping. Mirror W52's emission rules:

* ``comparative`` → ``comparison``
* ``quantitative`` → ``aggregate``
* ``qualitative`` → ``literal``

This pairing is empirically true across every emit site in
``prose_builder.py``: every quantitative atom is built with
``derivation_path="aggregate"``; every comparative atom with
``derivation_path="comparison"``; every qualitative atom with
``derivation_path="literal"``.

Determinism contract (PLAN §2.E acceptance #3). Same input markdown
→ same atom list across runs. Achieved by deterministic line-by-line
walk + sorted token tables + no ``datetime.now()``. Tested across 3
consecutive runs in ``verification/tests/test_atomic_claims.py``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Atom-type classifier patterns
# ---------------------------------------------------------------------------


_NUMERIC_RE = re.compile(r"\b\d+\b")
"""Numeric token marker — quantitative if no comparative shape wins."""


_DATE_MONTH_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\b"
)
"""Month-name token marker — quantitative if no comparative shape wins."""


_PHASE_RULE_PHRASES: tuple[str, ...] = (
    "rules that shaped the recommendation",
    "rules that adjusted the result after the skill ran",
)
"""Phase A / Phase B framing markers — W52 emits these as comparative."""


_COMPARISON_TOKENS: tuple[str, ...] = (
    # Word-boundary phrases (with leading/trailing space anchors so
    # we don't false-positive on "above" inside a longer word).
    " more than ",
    " less than ",
    " greater than ",
    " fewer than ",
    " above the ",
    " below the ",
    # Bare directional phrases (still space-anchored).
    " above ",
    " below ",
    # Arrow + operator tokens.
    "↑",
    "↓",
    "→",
    "<=",
    ">=",
    "<",
    ">",
)
"""Comparison tokens that signal a comparative atom. The leading and
trailing spaces on word phrases prevent false positives like
``"abovehead"`` (no such token exists in W52 prose, but the anchor
makes the rule robust against future edits).
"""


_DEFERRED_SUFFIX = " (deferred)"


_KNOWN_DOMAINS: frozenset[str] = frozenset({
    "recovery", "running", "sleep", "stress", "strength", "nutrition",
})


# ---------------------------------------------------------------------------
# Markdown line patterns
# ---------------------------------------------------------------------------


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_BULLET_RE = re.compile(r"^-\s+(.+?)\s*$")


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TypedAtom:
    """Atomic claim recovered from W52-rendered markdown.

    PLAN §2.E acceptance triple: ``(atom_text, atom_type,
    derivation_path)``. ``section_id`` is recovered from the
    enclosing markdown heading so downstream consumers (W58D) can
    pair atoms back to W52 sections without re-walking the bundle.

    ``locator_set`` + ``audit_refs`` are intentionally NOT modelled
    here — they live on the in-memory :class:`WeeklyAtom` and on the
    JSON render. The markdown surface does not carry them.
    """

    atom_text: str
    atom_type: str  # ``quantitative`` | ``comparative`` | ``qualitative``
    derivation_path: str  # ``aggregate`` | ``comparison`` | ``literal``
    section_id: Optional[str] = None

    def to_dict(self) -> dict[str, object]:
        return {
            "atom_text": self.atom_text,
            "atom_type": self.atom_type,
            "derivation_path": self.derivation_path,
            "section_id": self.section_id,
        }


# ---------------------------------------------------------------------------
# Classifiers
# ---------------------------------------------------------------------------


def classify_atom_type(atom_text: str) -> str:
    """Return one of ``{quantitative, comparative, qualitative}``.

    Priority: ``comparative`` > ``quantitative`` > ``qualitative``.
    Comparative wins when Phase A/B framing or a comparison-operator
    token is present, even when numerics also appear — the comparison
    is the structural claim and W58D validates the relation, not the
    numeric. The ordering matches W52's prose-builder tagging at
    ``prose_builder.py:438-452`` (firings → comparative even when
    numerics appear in the rule_id parenthesis).
    """

    lower = atom_text.lower()
    for phrase in _PHASE_RULE_PHRASES:
        if phrase in lower:
            return "comparative"
    # Surround with spaces so word-anchored tokens match at line ends.
    padded = f" {lower} "
    for token in _COMPARISON_TOKENS:
        if token in padded:
            return "comparative"
    if _NUMERIC_RE.search(atom_text):
        return "quantitative"
    if _DATE_MONTH_RE.search(atom_text):
        return "quantitative"
    return "qualitative"


def derivation_path_for(atom_type: str) -> str:
    """Map an atom_type to its derivation_path tag.

    Mirrors W52's prose-builder emission rules:
      * ``comparative`` → ``comparison``
      * ``quantitative`` → ``aggregate``
      * ``qualitative`` → ``literal``
    """

    if atom_type == "comparative":
        return "comparison"
    if atom_type == "quantitative":
        return "aggregate"
    return "literal"


# ---------------------------------------------------------------------------
# Section-id recovery
# ---------------------------------------------------------------------------


def _section_id_from_title(title: str, heading_level: int) -> str:
    """Map a markdown heading title to W52's stable section_id.

    W52's render uses h1 for the header section (``Weekly review —
    <iso_week>``) and h2 for body sections (``<Domain>``,
    ``Data quality``, ``Cadence``, ``Notes``). Domain sections may
    carry ``" (deferred)"`` suffix when the domain is fork-deferred
    (per ``prose_builder.py:482``); the suffix is stripped before
    routing.
    """

    title_normalised = title
    if title_normalised.endswith(_DEFERRED_SUFFIX):
        title_normalised = title_normalised[: -len(_DEFERRED_SUFFIX)]
    title_normalised = title_normalised.strip()
    lower = title_normalised.lower()

    if heading_level == 1 and lower.startswith("weekly review"):
        return "header"
    if lower == "data quality":
        return "data_quality"
    if lower == "cadence":
        return "cadence"
    if lower == "notes":
        return "footer"
    if lower in _KNOWN_DOMAINS:
        return f"domain_{lower}"
    # Unknown headings are surfaced as ``unknown_<slug>`` so downstream
    # consumers can detect drift (e.g., a future W52 section that
    # this parser hasn't been taught about).
    slug = lower.replace(" ", "_")
    return f"unknown_{slug}"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def parse_atoms_from_markdown(markdown: str) -> list[TypedAtom]:
    """Parse W52-rendered markdown into typed atoms.

    Walks the markdown line-by-line, recovering section context from
    h1 / h2 headings and atom_text from each ``- `` bullet within a
    section. Each bullet becomes a :class:`TypedAtom` whose
    ``atom_type`` is classified via :func:`classify_atom_type` and
    whose ``derivation_path`` is derived via
    :func:`derivation_path_for`.

    Lines that are not headings or bullets (blank lines, blockquotes,
    paragraph text on the abstain branch) are skipped without
    raising. The W52 render layer never wraps an atom across multiple
    lines (atoms are single-sentence by prose-builder contract), so a
    line-based walk is sufficient.

    Determinism: the implementation is purely deterministic — same
    input string → same output list across runs and processes. There
    is no stochastic seeding and no ``datetime.now()``.

    Empty / abstain markdown (no ``- `` bullets) returns an empty
    list. This is the correct answer for the abstain branch: per
    F-PHASE0-02 + F-PLAN-03, abstain-branch metadata is validated via
    deterministic substitution from coverage, not via claim cards or
    the factuality gate.
    """

    atoms: list[TypedAtom] = []
    current_section_id: Optional[str] = None

    for line in markdown.splitlines():
        head_match = _HEADING_RE.match(line)
        if head_match is not None:
            level = len(head_match.group(1))
            title = head_match.group(2)
            current_section_id = _section_id_from_title(title, level)
            continue
        bullet_match = _BULLET_RE.match(line)
        if bullet_match is not None:
            atom_text = bullet_match.group(1)
            atom_type = classify_atom_type(atom_text)
            atoms.append(TypedAtom(
                atom_text=atom_text,
                atom_type=atom_type,
                derivation_path=derivation_path_for(atom_type),
                section_id=current_section_id,
            ))
            continue
        # Non-heading, non-bullet line: skip silently. This covers
        # blank lines, blockquote disposition footers (e.g., the
        # multi-canonical-day note at ``render.py:134``), and the
        # abstain branch's paragraph lines.

    return atoms
