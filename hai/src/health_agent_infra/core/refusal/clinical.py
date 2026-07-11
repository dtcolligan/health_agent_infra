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

# D-55.1 (delta-audit fix): the diagnostic/prescriptive ACT is the signal, not
# a bare disease/drug word. These FRAMES catch the act for ANY (incl.
# out-of-vocabulary) condition or drug, while a bare mention of a benign word
# ("a depression in your HRV trend", "you logged ibuprofen") does NOT match.
# Deliberately anchored so ordinary coaching does not fire: the labs frame uses
# only unambiguously clinical objects (NOT bare "symptoms"/"numbers"/"hrv"); the
# possessive-diagnosis frame requires a generic clinical OBJECT
# (condition/disease/...) or a diagnostic VERB, not a plain "you have <X>"; the
# dose frame requires a dose UNIT (mg/mcg/iu) with a directive or schedule (NOT
# bare grams, so "protein 150g" is safe).
_DIAGNOSIS_FRAME_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"\byour\s+(?:lab|labs|bloodwork|blood\s+work|test\s+results?|panel|"
            r"biomarkers?)\s+(?:suggest|indicate|show|point\s+to|reveal|mean|"
            r"confirm)s?\b",
            re.IGNORECASE,
        ),
        "<clinical-frame: your labs/bloodwork suggest>",
    ),
    (
        # "your symptoms <diagnostic-verb> (that) you have/are ..." -- catches a
        # symptom-based diagnostic CONCLUSION about the user, while bare "your
        # symptoms of fatigue point to an easy day" (no "you have/are") stays
        # safe. This is why "symptoms" is not an anchor in the labs frame above.
        re.compile(
            r"\byour\s+symptoms?\s+(?:suggest|indicate|show|point\s+to|reveal|"
            r"mean|confirm)s?\s+(?:that\s+)?you(?:'?re|\s+are|\s+have|\s+may|"
            r"\s+likely|\s+probably)\b",
            re.IGNORECASE,
        ),
        "<clinical-frame: your symptoms indicate you have>",
    ),
    (
        # The "coming down with" illness idiom (low false-positive: you come
        # down with an illness, not a schedule). The broader diagnostic verbs
        # (developing / suffering from / showing signs of) are DELIBERATELY
        # excluded -- they take benign objects ("developing good habits",
        # "suffering from a packed schedule", "showing signs of fatigue"), so a
        # named condition there is left to the lexicon / possessive frame.
        re.compile(r"\bcoming\s+down\s+with\b", re.IGNORECASE),
        "<clinical-frame: coming down with>",
    ),
    (
        # Possessive/copula diagnosis anchored on a generic clinical OBJECT
        # (condition/disease/disorder/infection/syndrome/illness) with a
        # REQUIRED article, so "you have good sleep" / "a deficiency in miles"
        # are safe but "you have a thyroid condition" / "an infection" fire.
        re.compile(
            r"\byou(?:'?ve\s+got|\s+have|\s+likely\s+have|\s+probably\s+have|"
            r"\s+may\s+have|\s+might\s+have)\s+(?:a|an)\s+(?:\w+\s+){0,2}"
            r"(?:condition|disease|disorder|infection|syndrome|illness)\b",
            re.IGNORECASE,
        ),
        "<clinical-frame: you have a condition/disorder/infection>",
    ),
    (
        # Dose directive: a dose UNIT with a directive verb OR a schedule.
        re.compile(
            r"\b(?:take|taking|takes|use|using|start|starting|administer|"
            r"swallow|inject|dose|dosage|prescrib\w*)\b[^.\n]{0,40}?\b\d+\s?"
            r"(?:mg|mcg|milligrams?|micrograms?|iu|units?)\b",
            re.IGNORECASE,
        ),
        "<clinical-frame: dose directive>",
    ),
    (
        re.compile(
            r"\b\d+\s?(?:mg|mcg|milligrams?|micrograms?|iu)\b[^.\n]{0,25}?\b"
            r"(?:daily|twice|per\s+day|every|three\s+times|each\s+morning|"
            r"each\s+night|hours?|a\s+day)\b",
            re.IGNORECASE,
        ),
        "<clinical-frame: dose schedule>",
    ),
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
    for pattern, phrase in _PHRASE_PATTERNS + _DIAGNOSIS_FRAME_PATTERNS:
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
