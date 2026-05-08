"""Voice linter for user-facing narration output.

D3 §Voice — the `reporting` skill and `hai today` both produce
end-user prose. This module is the shared gate that catches drift:

- Medical / diagnostic language (same banned-token list
  ``core.validate.BANNED_TOKENS`` already enforces at the payload
  layer — applied here at the prose layer, so a phrasing choice
  can't leak a banned label past the boundary).
- Rule ID leaks — ``R1``, ``R3a``, ``X9``, and the
  ``require_min_coverage``-style rule slugs belong in debug output
  (``hai explain --operator``), not in end-user prose.

The module is deliberately narrow. It asserts *absence* of anti-
patterns, not *presence* of style. Tone (first-person, plain, no
hype) is the reporting skill's own responsibility; a lint-style
check can only catch violations the regex can see.

API:

    lint_narration(text) -> list[LintFinding]

``LintFinding`` is a dataclass. Empty list means the text is clean
against this module's checks. Callers decide how strict to be —
tests assert ``== []``; future CI can assert nothing in the
recovery snippet corpus regresses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from health_agent_infra.core.validate import BANNED_TOKENS


# ``\bR\d+[a-z]?\b`` matches R1, R2, R3a, R12b. ``\bX\d+[a-z]?\b``
# matches X1a, X9, X10. ``\b(require|coverage|forced)_\w+\b`` catches
# the slug family (``require_min_coverage``, ``coverage_insufficient``,
# ``forced_action``). Deliberately loose on the slug side — false
# positives here cost a test re-read; false negatives leak rule IDs
# into the user surface.
_RULE_ID_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bR\d+[a-z]?\b"),
    re.compile(r"\bX\d+[a-z]?\b"),
    re.compile(
        r"\b(require_\w+|forced_action|coverage_(?:ok|insufficient|full))\b"
    ),
)


@dataclass(frozen=True)
class LintFinding:
    """One hit against the narration-voice rules.

    ``category`` is the stable machine key callers can branch on.
    ``match`` is the literal substring (useful for error messages).
    ``span`` is the ``(start, end)`` slice into the input string so
    future callers can render highlights.
    """

    category: str
    match: str
    span: tuple[int, int]


def lint_narration(text: str) -> list[LintFinding]:
    """Return every voice-rule violation in ``text``. Empty list = clean.

    Runs two passes:

    1. **Medical language.** Case-insensitive substring match against
       ``BANNED_TOKENS``. Whole-word matches only (so ``"condition"``
       fires but ``"conditional"`` does not).
    2. **Rule ID leaks.** Regex match against the slug family. The
       patterns are whole-word-boundaried too so a domain name like
       ``"running"`` never triggers.

    The two passes are independent; a single string can accumulate
    hits from both.
    """

    findings: list[LintFinding] = []
    findings.extend(_find_medical_language(text))
    findings.extend(_find_rule_id_leaks(text))
    return findings


def _find_medical_language(text: str) -> Iterable[LintFinding]:
    # Case-insensitive whole-word scan. Compiled on the fly because
    # BANNED_TOKENS is small and this is hot only during tests /
    # dev-loop lints; skipping the cache keeps the module pure.
    for token in sorted(BANNED_TOKENS):
        pattern = re.compile(rf"\b{re.escape(token)}\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            yield LintFinding(
                category="medical_language",
                match=match.group(0),
                span=(match.start(), match.end()),
            )


def _find_rule_id_leaks(text: str) -> Iterable[LintFinding]:
    for pattern in _RULE_ID_PATTERNS:
        for match in pattern.finditer(text):
            yield LintFinding(
                category="rule_id_leak",
                match=match.group(0),
                span=(match.start(), match.end()),
            )
