"""Clinical-claim refusal at runtime output boundaries."""

from __future__ import annotations

import re
from dataclasses import dataclass
from importlib import resources
from typing import Mapping

from health_agent_infra.core.refusal.envelope import (
    build_mechanism_disabled_marker,
    build_refusal_envelope,
)
from health_agent_infra.core.runtime_mode import (
    current_runtime_mode,
    mechanisms_off_for_mode,
)


_PHRASE_RESOURCE = "banned_clinical_phrases.txt"
_REFUSAL_KIND = "clinical_claim"
_MECHANISM = "refusal"


def _load_banned_phrases() -> tuple[str, ...]:
    text = (
        resources.files(__package__)
        .joinpath(_PHRASE_RESOURCE)
        .read_text(encoding="utf-8")
    )
    phrases = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        phrases.append(line.lower())
    return tuple(sorted(frozenset(phrases)))


BANNED_CLINICAL_PHRASES: tuple[str, ...] = _load_banned_phrases()


def _phrase_pattern(phrase: str) -> re.Pattern[str]:
    parts = [re.escape(part) for part in phrase.split()]
    body = r"\s+".join(parts)
    return re.compile(rf"(?<!\w){body}(?!\w)", re.IGNORECASE)


_PHRASE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (_phrase_pattern(phrase), phrase) for phrase in BANNED_CLINICAL_PHRASES
)


@dataclass(frozen=True)
class ClinicalPhraseMatch:
    """One banned clinical phrase occurrence in a runtime output."""

    phrase: str
    line_no: int
    column: int
    excerpt: str

    def to_dict(self) -> dict[str, object]:
        return {
            "phrase": self.phrase,
            "line_no": self.line_no,
            "column": self.column,
            "excerpt": self.excerpt,
        }


@dataclass(frozen=True)
class ClinicalOutputDecision:
    """Decision produced by scanning a runtime output path."""

    allowed: bool
    matches: tuple[ClinicalPhraseMatch, ...]
    refusal_envelope: dict[str, object] | None = None
    mechanism_disabled_marker: dict[str, object] | None = None


class ClinicalRefusalError(ValueError):
    """Raised when clinical output refusal blocks a user-facing payload."""

    def __init__(self, envelope: dict[str, object]) -> None:
        self.envelope = envelope
        super().__init__(str(envelope))


def scan_clinical_phrases(text: str) -> tuple[ClinicalPhraseMatch, ...]:
    """Return banned clinical phrase matches in deterministic order."""

    matches: list[tuple[int, ClinicalPhraseMatch]] = []
    for pattern, phrase in _PHRASE_PATTERNS:
        for match in pattern.finditer(text):
            line_no, column = _line_column(text, match.start())
            matches.append((
                match.start(),
                ClinicalPhraseMatch(
                    phrase=phrase,
                    line_no=line_no,
                    column=column,
                    excerpt=_excerpt(text, match.start(), match.end()),
                ),
            ))
    matches.sort(key=lambda item: item[0])
    return tuple(match for _, match in matches)


def evaluate_clinical_output(
    text: str,
    *,
    output_path: str,
    env: Mapping[str, str] | None = None,
) -> ClinicalOutputDecision:
    """Scan output text and return the refusal or bypass decision."""

    matches = scan_clinical_phrases(text)
    if not matches:
        return ClinicalOutputDecision(allowed=True, matches=())

    runtime_mode = current_runtime_mode(env)
    if _MECHANISM in mechanisms_off_for_mode(runtime_mode):
        return ClinicalOutputDecision(
            allowed=True,
            matches=matches,
            mechanism_disabled_marker=build_mechanism_disabled_marker(
                mechanism=_MECHANISM,
                runtime_mode=runtime_mode,
                output_path=output_path,
                reason="clinical-claim refusal disabled by runtime mode",
                details={"matches": [m.to_dict() for m in matches]},
            ),
        )

    envelope = build_refusal_envelope(
        refusal_kind=_REFUSAL_KIND,
        mechanism=_MECHANISM,
        code="clinical_claim_in_output",
        message=(
            "runtime refused output containing clinical or diagnosis-shaped "
            "language"
        ),
        output_path=output_path,
        details={"matches": [m.to_dict() for m in matches]},
    )
    return ClinicalOutputDecision(
        allowed=False,
        matches=matches,
        refusal_envelope=envelope,
    )


def enforce_clinical_output(
    text: str,
    *,
    output_path: str,
    env: Mapping[str, str] | None = None,
) -> ClinicalOutputDecision:
    """Raise ``ClinicalRefusalError`` unless a scanned output is allowed."""

    decision = evaluate_clinical_output(text, output_path=output_path, env=env)
    if not decision.allowed:
        assert decision.refusal_envelope is not None
        raise ClinicalRefusalError(decision.refusal_envelope)
    return decision


def _line_column(text: str, offset: int) -> tuple[int, int]:
    line_no = text.count("\n", 0, offset) + 1
    last_nl = text.rfind("\n", 0, offset)
    column = offset - last_nl
    return line_no, column


def _excerpt(text: str, start: int, end: int) -> str:
    excerpt_start = max(0, start - 40)
    excerpt_end = min(len(text), end + 40)
    return text[excerpt_start:excerpt_end].replace("\n", " ").strip()


__all__ = [
    "BANNED_CLINICAL_PHRASES",
    "ClinicalOutputDecision",
    "ClinicalPhraseMatch",
    "ClinicalRefusalError",
    "enforce_clinical_output",
    "evaluate_clinical_output",
    "scan_clinical_phrases",
]
