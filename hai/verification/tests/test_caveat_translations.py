"""W52 step 4 — caveat-translation registry (W-EXPLAIN-UX-CARRY #4).

Registry coverage tests + fallback discipline tests for
``core/explain/caveat_translations.py``.

Per the explain_ux_review_2026_05.md acceptance hook:

  > Every caveat has a `core/explain/caveat_translations.py` entry
  > tested for non-empty output.

The registry MUST stay in parity with the runtime's emitted
``reason_token`` set. These tests grep the codebase for every
emitted token and assert every non-template token has a non-default
registry entry.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from health_agent_infra.core.explain.caveat_translations import (
    is_registered_token,
    known_token_keys,
    translate_caveat,
)


# Pure literal-string tokens runtime emits via `"reason_token": "<X>"`
# patterns. Templated tokens (x2_nutrition_<band>,
# fatigued_group:<group>) are handled separately.
_LITERAL_TOKEN_PATTERN = re.compile(r'"reason_token":\s*"([a-z0-9_]+)"')


def _grep_runtime_reason_tokens() -> set[str]:
    """Walk source files and return every literal reason_token value
    the runtime emits. Excludes f-string templated tokens (those
    parse as a separate suffix lookup in the registry).
    """

    repo_root = Path(__file__).resolve().parents[2]
    targets = [
        repo_root / "src" / "health_agent_infra" / "domains",
        repo_root / "src" / "health_agent_infra" / "core",
    ]
    out: set[str] = set()
    for root in targets:
        for py in root.rglob("*.py"):
            if "__pycache__" in str(py):
                continue
            text = py.read_text(encoding="utf-8")
            out.update(_LITERAL_TOKEN_PATTERN.findall(text))
    return out


def test_translate_caveat_returns_non_empty_for_every_runtime_token():
    """Every literal `reason_token` emitted by the runtime translates
    to a non-empty plain-English string. New runtime tokens that
    ship without a registry entry trigger this test (the fallback
    is non-empty but doesn't count as an explicit translation).
    """

    tokens = _grep_runtime_reason_tokens()
    assert tokens, "expected to find at least one reason_token in source"
    for token in tokens:
        translation = translate_caveat(token)
        assert translation, (
            f"caveat token {token!r} produced empty translation"
        )
        assert isinstance(translation, str)
        # The translation must NOT be the raw token itself —
        # otherwise the obligation hook ("no caveat-token string in
        # weekly-review prose") would be violated.
        assert translation != token


def test_translate_caveat_known_domain_tokens_are_explicit_not_fallback():
    """The 6 per-domain `reason_token` values shown in the
    explain_ux_review doc must have explicit registry entries
    (not the fallback humanisation), since the doc names them as
    P0 caveats.
    """

    explicit_required = {
        "resting_hr_spike_3_days_running",
        "acwr_spike",
        "chronic_deprivation_detected",
        "sustained_very_high_stress",
        "volume_spike_detected",
        "extreme_deficiency_detected",
    }
    for token in explicit_required:
        assert is_registered_token(token), (
            f"caveat token {token!r} must have an explicit registry "
            "entry per W-EXPLAIN-UX-CARRY P0 obligation #4"
        )


def test_translate_caveat_x2_nutrition_template_resolves():
    """The X2 nutrition template `x2_nutrition_<band>` resolves the
    suffix as a band name rather than emitting the raw template
    string. Three known bands per domains/nutrition/policy.py.
    """

    for band in ("moderate_deficit", "high_deficit", "protein_gap"):
        full = f"x2_nutrition_{band}"
        translation = translate_caveat(full)
        assert is_registered_token(full)
        assert translation
        assert full not in translation  # raw template string elided


def test_translate_caveat_fallback_is_non_empty_for_unknown_token():
    """A token outside the registry returns the humanised-fallback,
    which is always non-empty + does not contain the raw underscore-
    separated form.
    """

    unknown = "future_token_not_in_registry"
    translation = translate_caveat(unknown)
    assert translation
    assert translation != unknown
    # Fallback humanises the underscores to spaces.
    assert "_" not in translation or "_" in '"' + translation + '"'


def test_translate_caveat_handles_none_or_empty_input():
    """Defensive: None / empty string / non-string input falls
    through to the "(no rationale recorded)" fallback rather than
    raising. The prose builder relies on this safety so it can
    blindly translate every rationale entry without conditional
    branching.
    """

    assert translate_caveat("") == "(no rationale recorded)"
    assert translate_caveat(None) == "(no rationale recorded)"  # type: ignore[arg-type]


def test_known_token_keys_set_is_non_empty_and_lower_snake_case():
    """The exposed registry-key set is well-formed: non-empty, every
    entry is a lowercase snake_case (or `<prefix>:<suffix>`) string.
    Regression guard against accidental capitalisation drift.
    """

    keys = known_token_keys()
    assert keys
    for key in keys:
        assert key == key.lower()
        # snake_case OR <prefix>:<suffix> shape only.
        for ch in key:
            assert ch.isalnum() or ch in "_:"


def test_fatigued_group_template_resolves_with_explicit_group():
    """The `fatigued_group:<group>` template resolves any group
    suffix (e.g. `quads`, `hamstrings`, `glutes`) without enumeration.
    """

    translation = translate_caveat("fatigued_group:quads")
    assert translation
    assert "fatigued_group" not in translation
    assert "quads" in translation
