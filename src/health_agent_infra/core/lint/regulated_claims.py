"""W-LINT (v0.1.13) — regulated-claim lint.

Block clinical / regulatory phrasing in user-facing prose. Two surfaces:

  1. **Static scan** of packaged skill content. Runs in CI via the
     `test_regulated_claim_lint` test surface; a violation in a
     packaged SKILL.md fails the build. Authors of new skills hit
     this check before merge.

  2. **Runtime check** at the CLI rendering boundary. The
     `runtime_check(text)` function runs the strict regime regardless
     of provenance — even if an allowlisted skill quoted a term in a
     properly-cited block, when that block crosses into CLI prose it
     gets blocked. The skill's own SKILL.md may pass static lint
     under the exception path; its runtime output may not.

Why two regimes? The `expert-explainer` skill exists specifically to
quote bounded definitional language ("the literature defines body
battery as ..."). Its SKILL.md needs to describe that scope. But
when the runtime asks the skill to compose a recommendation
rationale, the runtime layer should not surface those words to a
user — the rationale is first-person agent prose, not literature
quotation.

Per the v0.1.13 PLAN F-PLAN-09, the exception path requires four
constraints to ALL hold (allowlisted skill + citation + quoted
context + non-rendered surface). Constraint 4 is enforced by the
runtime_check; constraints 1-3 are enforced by `scan_skill_text`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Term taxonomy
# ---------------------------------------------------------------------------

# Terms that must not appear in user-facing prose unless the four-
# constraint exception path applies. Lower-cased; matching is whole-
# word, case-insensitive. Multi-word terms are matched as phrases.
#
# Some overlap with the existing R2 banned-token list at
# `core.validate.BANNED_TOKENS` (diagnose, diagnosis, disease) is
# intentional — R2 enforces at the proposal/recommendation validator
# boundary; W-LINT enforces at the static-skill + CLI-rendering
# boundary. Both regimes catching the same word is a feature: defence
# in depth.
REGULATED_TERMS: frozenset[str] = frozenset({
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

# Packaged skills whose SKILL.md content gets the exception path.
# v0.1.13 ship-set: `expert-explainer` only (the one packaged skill
# whose explicit purpose is bounded definitional / quoted explanation
# per `reporting/docs/grounded_expert_scope.md`). Code-owned research
# surfaces under `core/research/` are NOT allowlisted because they
# are CLI/runtime surfaces and run strict regime per constraint (4).
ALLOWLISTED_SKILLS: frozenset[str] = frozenset({
    "expert-explainer",
})

# Phrases that signal a quoted / attributed / definitional context.
# When a regulated term appears within ATTRIBUTION_WINDOW characters
# of any of these phrases, the term passes constraint (3). Quoted
# strings (surrounded by ASCII or smart quotes) also pass.
ATTRIBUTION_HINTS: tuple[str, ...] = (
    "defines",
    "definition",
    "the literature",
    "according to",
    "as defined by",
    "the term",
    "is used by",
    "is the term",
    "wikipedia",
    "ICD-",
    "DSM-",
)

# Citation pattern: `[source_id]` with snake_case payload.
# Matches what the `expert-explainer` skill emits per its protocol.
_CITATION_PATTERN = re.compile(r"\[[a-z0-9_]+\]")

# Quoted-string pattern: ASCII single/double quote OR smart-quote pairs.
_QUOTED_PATTERN = re.compile(r"""['"“”‘’]""")

# Distance (in characters) within which an attribution hint or
# citation must appear to count as same-block.
ATTRIBUTION_WINDOW = 200

# File-wide opt-out pragma: when this comment appears anywhere in
# the scanned text, the static scan treats the whole file as a
# meta-document and emits no violations. Reserved for documents
# whose explicit purpose is enumerating regulated terms (safety
# scope statements, "never use X" lists, definitional skill protocol
# docs). Author opts in deliberately; the pragma is auditable on
# diff. Runtime check (CLI rendering boundary) ignores this pragma —
# meta-documents never get rendered to the user.
META_DOCUMENT_PRAGMA = "<!-- regulated-claim-lint: meta-document -->"


# ---------------------------------------------------------------------------
# Violation + error types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RegulatedClaimViolation:
    """One regulated-term occurrence that failed the lint."""

    term: str
    line_no: int
    column: int
    reason: str
    """Stable ID:
       - 'strict_regime' (no exception path)
       - 'no_allowlisted_skill' (constraint 1 failed)
       - 'no_citation' (constraint 2 failed)
       - 'no_quoted_context' (constraint 3 failed)
    """
    excerpt: str

    def __str__(self) -> str:
        return (
            f"line {self.line_no}:{self.column} — regulated term "
            f"{self.term!r} ({self.reason}); excerpt: {self.excerpt!r}"
        )


class RegulatedClaimError(ValueError):
    """Raised by `runtime_check` when text crossing the CLI rendering
    boundary contains a regulated-term violation. Carries the list of
    violations so callers can surface a USER_INPUT-flavoured message."""

    def __init__(self, violations: list[RegulatedClaimViolation]) -> None:
        self.violations = violations
        msg_lines = [
            f"regulated-claim lint blocked CLI render "
            f"({len(violations)} violation(s)):",
        ]
        msg_lines.extend(f"  - {v}" for v in violations)
        super().__init__("\n".join(msg_lines))


# ---------------------------------------------------------------------------
# Term-matching primitives
# ---------------------------------------------------------------------------


def _term_pattern(term: str) -> re.Pattern[str]:
    """Whole-word, case-insensitive pattern for a single term.

    Multi-word terms ("medical advice") are matched as a single
    phrase with `\\s+` between the words to tolerate double-spacing
    or line-wrap whitespace.
    """

    parts = [re.escape(p) for p in term.split()]
    body = r"\s+".join(parts)
    return re.compile(rf"\b{body}\b", re.IGNORECASE)


_TERM_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (_term_pattern(t), t) for t in sorted(REGULATED_TERMS)
)


def _find_occurrences(text: str) -> list[tuple[str, int, int]]:
    """Return `(term, start_offset, end_offset)` per occurrence in `text`."""

    out: list[tuple[str, int, int]] = []
    for pattern, term in _TERM_PATTERNS:
        for m in pattern.finditer(text):
            out.append((term, m.start(), m.end()))
    out.sort(key=lambda x: x[1])
    return out


def _line_column(text: str, offset: int) -> tuple[int, int]:
    """Convert a character offset to 1-based (line, column)."""

    line_no = text.count("\n", 0, offset) + 1
    last_nl = text.rfind("\n", 0, offset)
    column = offset - last_nl  # 1-based when last_nl is -1 → offset+1
    return line_no, column


# ---------------------------------------------------------------------------
# Constraint checks (used in exception-path mode)
# ---------------------------------------------------------------------------


def _has_citation_within_window(text: str, start: int, end: int) -> bool:
    window_start = max(0, start - ATTRIBUTION_WINDOW)
    window_end = min(len(text), end + ATTRIBUTION_WINDOW)
    return bool(_CITATION_PATTERN.search(text[window_start:window_end]))


def _is_in_quoted_or_attributed_context(text: str, start: int, end: int) -> bool:
    window_start = max(0, start - ATTRIBUTION_WINDOW)
    window_end = min(len(text), end + ATTRIBUTION_WINDOW)
    window = text[window_start:window_end]

    # Attribution-phrase check (case-insensitive).
    lower = window.lower()
    for hint in ATTRIBUTION_HINTS:
        if hint.lower() in lower:
            return True

    # Quoted-string check: at least one quote glyph on each side of
    # the term within the window. Crude but adequate; the static
    # scan errs on the side of refusal when in doubt.
    pre = text[window_start:start]
    post = text[end:window_end]
    if _QUOTED_PATTERN.search(pre) and _QUOTED_PATTERN.search(post):
        return True

    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scan_skill_text(
    text: str,
    *,
    source_skill: Optional[str] = None,
    allow_exception: bool = True,
) -> list[RegulatedClaimViolation]:
    """Static scan of skill content. Returns the list of violations.

    Args:
        text: SKILL.md (or any skill-authored prose) to scan.
        source_skill: skill name (e.g. ``"expert-explainer"``). When
            None, runs strict regime (no exception path).
        allow_exception: when False, force strict regime even for
            allowlisted skills. Used by `runtime_check` so the CLI
            rendering boundary always runs strict per F-PLAN-09
            constraint (4).

    The exception path applies only when ALL of:
      1. ``source_skill`` is in ``ALLOWLISTED_SKILLS``.
      2. The term occurrence has a citation (``[source_id]``) within
         ``ATTRIBUTION_WINDOW`` characters.
      3. The term appears in a quoted/attributed/definitional
         context.
      4. ``allow_exception`` is True.

    A violation reports the first failed constraint (1 → no_allowlisted_skill,
    2 → no_citation, 3 → no_quoted_context); when no exception is
    available at all, the reason is 'strict_regime'.
    """

    # Meta-document pragma — file-wide opt-out for skills whose explicit
    # purpose is enumerating regulated terms (safety scope statements,
    # negation lists, definitional protocol docs). Honoured only by the
    # static scan; the runtime CLI-boundary check ignores it because
    # meta-documents never get rendered to a user.
    if allow_exception and META_DOCUMENT_PRAGMA in text:
        return []

    eligible_for_exception = (
        allow_exception
        and source_skill is not None
        and source_skill in ALLOWLISTED_SKILLS
    )

    violations: list[RegulatedClaimViolation] = []
    for term, start, end in _find_occurrences(text):
        line_no, col = _line_column(text, start)
        # Excerpt: ±40 chars around the term, single-line.
        excerpt_start = max(0, start - 40)
        excerpt_end = min(len(text), end + 40)
        excerpt = text[excerpt_start:excerpt_end].replace("\n", " ").strip()

        if not eligible_for_exception:
            reason = (
                "strict_regime"
                if not allow_exception or source_skill is None
                else "no_allowlisted_skill"
            )
            violations.append(RegulatedClaimViolation(
                term=term, line_no=line_no, column=col,
                reason=reason, excerpt=excerpt,
            ))
            continue

        # Exception path — check constraints 2 and 3 in order so the
        # reported reason names the first-failed constraint.
        if not _has_citation_within_window(text, start, end):
            violations.append(RegulatedClaimViolation(
                term=term, line_no=line_no, column=col,
                reason="no_citation", excerpt=excerpt,
            ))
            continue
        if not _is_in_quoted_or_attributed_context(text, start, end):
            violations.append(RegulatedClaimViolation(
                term=term, line_no=line_no, column=col,
                reason="no_quoted_context", excerpt=excerpt,
            ))
            continue
        # All constraints hold — silently allowed.

    return violations


def runtime_check(text: str) -> None:
    """CLI rendering-boundary check. Always strict regime.

    Raises ``RegulatedClaimError`` when ``text`` contains any
    regulated-term occurrence. The exception is the contract surface:
    callers in cli.py catch it and exit USER_INPUT, never silently
    rewrite or strip the offending text.

    Per F-PLAN-09 constraint (4), this check runs regardless of
    the source skill's allowlist status — even allowlisted SKILL.md
    text passes static scan but its runtime output, IF rendered,
    fails this check. That's intentional: rationale prose is
    first-person agent voice, not literature quotation.
    """

    violations = scan_skill_text(text, source_skill=None, allow_exception=False)
    if violations:
        raise RegulatedClaimError(violations)
