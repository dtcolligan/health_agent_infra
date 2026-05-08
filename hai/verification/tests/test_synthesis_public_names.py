"""Registry tests for X-rule public names.

These pin the contract between ``X_RULE_PUBLIC_NAMES`` in
``core/synthesis_policy.py`` and the evaluator tuples (``PHASE_A_EVALUATORS``
/ ``PHASE_B_EVALUATORS``) so a new rule with no public name fails the
suite at add time rather than silently rendering as an internal id.

Coverage check derives expected ids from function names
(``evaluate_x1a → X1a`` / ``evaluate_x3b → X3b`` / ``evaluate_x9 → X9``)
which matches how the rule evaluators populate ``XRuleFiring.rule_id``.
"""

from __future__ import annotations

import re

import pytest

from health_agent_infra.core.synthesis_policy import (
    PHASE_A_EVALUATORS,
    PHASE_B_EVALUATORS,
    XRuleFiring,
    X_RULE_DESCRIPTIONS,
    X_RULE_PUBLIC_NAMES,
    description_for,
    public_name_for,
)


def _expected_rule_ids() -> list[str]:
    """Derive the expected rule-id set from the evaluator tuples.

    ``evaluate_x3b`` → ``X3b`` (case-preserving via the internal id
    convention: first letter uppercase, suffix lowercase).
    """

    ids: list[str] = []
    for fn in PHASE_A_EVALUATORS + PHASE_B_EVALUATORS:
        suffix = fn.__name__[len("evaluate_"):]
        # "x1a" → "X1a", "x3b" → "X3b", "x9" → "X9".
        ids.append(suffix[0].upper() + suffix[1:])
    return ids


def test_every_evaluator_has_a_registry_entry():
    """Every rule the runtime can emit must have a public name.

    Pinning this stops us from merging a new evaluator without
    adding a row to ``X_RULE_PUBLIC_NAMES`` and the x_rules.md table.
    """

    expected = set(_expected_rule_ids())
    missing = expected - set(X_RULE_PUBLIC_NAMES)
    assert not missing, (
        f"X-rule evaluators with no public name registered: {sorted(missing)}"
    )


def test_public_names_are_unique():
    """Two rules cannot share a public name — collisions would make the
    slug useless as a handle."""

    names = list(X_RULE_PUBLIC_NAMES.values())
    assert len(names) == len(set(names)), (
        f"duplicate public name in X_RULE_PUBLIC_NAMES: {names}"
    )


_SLUG_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


@pytest.mark.parametrize(
    "rule_id,public_name",
    sorted(X_RULE_PUBLIC_NAMES.items()),
)
def test_public_name_is_a_valid_slug(rule_id, public_name):
    assert _SLUG_RE.match(public_name), (
        f"public name for {rule_id!r} is not a valid kebab slug: "
        f"{public_name!r}"
    )


def test_spot_checks():
    assert public_name_for("X1a") == "sleep-debt-softens-hard"
    assert public_name_for("X9") == "training-intensity-bumps-protein"


def test_unknown_rule_ids_return_none():
    assert public_name_for("X999_future") is None
    assert public_name_for("") is None


def _make_firing(rule_id: str) -> XRuleFiring:
    return XRuleFiring(
        rule_id=rule_id,
        tier="soften",
        affected_domain="recovery",
        trigger_note="synthetic",
        recommended_mutation=None,
        source_signals={},
        phase="A",
    )


def test_to_dict_carries_public_name_for_registered_rule():
    firing = _make_firing("X1a")
    assert firing.to_dict()["public_name"] == "sleep-debt-softens-hard"


def test_to_dict_carries_none_for_experimental_rule():
    firing = _make_firing("X_experimental")
    assert firing.to_dict()["public_name"] is None


# ---------------------------------------------------------------------------
# Sentence-form human explanations (Phase 3 of the agent-operable runtime
# plan). Each rule must have a sentence alongside its slug so narration
# is never "just the internal id."
# ---------------------------------------------------------------------------


def test_every_rule_has_a_sentence_description():
    """Every rule in X_RULE_PUBLIC_NAMES must have a paired
    X_RULE_DESCRIPTIONS entry. Pinning the two maps keeps the
    machine-readable slug and the human sentence in lockstep — adding
    a rule without a sentence becomes a merge-blocking failure."""

    missing = set(X_RULE_PUBLIC_NAMES) - set(X_RULE_DESCRIPTIONS)
    assert not missing, (
        f"X-rules with a public_name but no human_explanation: "
        f"{sorted(missing)}. Add entries to X_RULE_DESCRIPTIONS in "
        f"core/synthesis_policy.py."
    )

    extra = set(X_RULE_DESCRIPTIONS) - set(X_RULE_PUBLIC_NAMES)
    assert not extra, (
        f"X_RULE_DESCRIPTIONS has entries with no matching public_name: "
        f"{sorted(extra)}. Either remove them or add them to "
        f"X_RULE_PUBLIC_NAMES."
    )


def test_every_evaluator_has_a_sentence():
    """The coverage surface the agent sees — an evaluator that emits a
    firing must have a narratable sentence. Mirrors
    test_every_evaluator_has_a_registry_entry above."""

    expected = set(_expected_rule_ids())
    missing = expected - set(X_RULE_DESCRIPTIONS)
    assert not missing, (
        f"X-rule evaluators with no human_explanation: {sorted(missing)}"
    )


@pytest.mark.parametrize(
    "rule_id,sentence",
    sorted(X_RULE_DESCRIPTIONS.items()),
)
def test_sentence_is_nonempty_and_ends_with_terminator(rule_id, sentence):
    """Sentences must be real prose — not empty, not slug-shaped, and
    punctuated so a skill can concatenate them into a paragraph."""

    assert sentence, f"empty description for {rule_id!r}"
    assert sentence.strip()[-1] in ".!?", (
        f"description for {rule_id!r} does not end with a terminator: "
        f"{sentence!r}"
    )
    # A slug is hyphen-heavy lowercase; a sentence has spaces.
    assert " " in sentence, (
        f"description for {rule_id!r} looks like a slug, not a sentence: "
        f"{sentence!r}"
    )


def test_description_for_spot_checks():
    # Spot-check two known sentences so an accidental rename of a
    # production sentence also fails the suite (not just the map
    # coverage).
    assert description_for("X1a").startswith("Sleep debt is moderate")
    assert description_for("X9").startswith("Training is hard today")


def test_description_for_unknown_rule_returns_none():
    assert description_for("X999_future") is None
    assert description_for("") is None


def test_to_dict_carries_human_explanation_for_registered_rule():
    firing = _make_firing("X1a")
    out = firing.to_dict()
    assert out["human_explanation"] is not None
    assert out["human_explanation"].startswith("Sleep debt is moderate")


def test_to_dict_carries_none_human_explanation_for_experimental_rule():
    firing = _make_firing("X_experimental")
    assert firing.to_dict()["human_explanation"] is None
