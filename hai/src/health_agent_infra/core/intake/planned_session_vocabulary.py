"""Canonical vocabulary for the ``planned_session_type`` field on
``hai intake readiness``.

Background (v0.1.7 W33 / v0.1.6 W8 revived). The
``planned_session_type`` field accepts free-text — the per-domain
classifiers do loose substring matching, not strict enum enforcement
(see e.g. ``domains/strength/policy.py:283`` — "strength" substring
test). That's a deliberate choice: a user typing ``strength_back_biceps``
is correctly classified as a strength session even though that exact
string isn't in any registry. But it leaves an agent without a
machine-discoverable list of canonical strings to choose from.

This module is the registry. The CLI ``hai planned-session-types
--json`` emits its content; the W21 next-action manifest's
``intake_required`` action references it. Documenting these strings
is purely advisory — passing a non-canonical string still classifies
via the substring rules; the canonical set just gives an agent the
strongest signal.

Updates: when a domain classifier adds a new pattern (or clarifies
the substring rule), add the canonical examples here. The
``hai capabilities`` manifest's ``hai planned-session-types``
description points readers at this file.
"""

from __future__ import annotations

from typing import Any


# Canonical session-type tokens, grouped by primary domain. The
# substring the per-domain classifier looks for is in
# ``classifier_substring``. Examples are not exhaustive — they're the
# strings most likely to be useful to an agent composing a readiness
# call.
PLANNED_SESSION_VOCABULARY: list[dict[str, Any]] = [
    {
        "token": "rest",
        "primary_domain": "recovery",
        "classifier_substring": "rest",
        "description": "Explicit rest day. Tells running + strength + "
                       "stress classifiers no training is planned; "
                       "recovery still emits a recommendation.",
    },
    # Running family — substring "easy" / "tempo" / "intervals" / "long" /
    # "race" / "recovery_run".
    {
        "token": "easy_z2",
        "primary_domain": "running",
        "classifier_substring": "easy",
        "description": "Easy aerobic run, Zone 2. The default low-stress run.",
    },
    {
        "token": "tempo",
        "primary_domain": "running",
        "classifier_substring": "tempo",
        "description": "Tempo / threshold run.",
    },
    {
        "token": "intervals_4x4",
        "primary_domain": "running",
        "classifier_substring": "intervals",
        "description": "Hard intervals (e.g. 4×4 minutes Z4). Recovery "
                       "+ readiness gates may downgrade this on poor "
                       "signal.",
    },
    {
        "token": "long",
        "primary_domain": "running",
        "classifier_substring": "long",
        "description": "Long endurance run.",
    },
    {
        "token": "race",
        "primary_domain": "running",
        "classifier_substring": "race",
        "description": "Race day. Recovery rules treat as the most "
                       "load-sensitive session class.",
    },
    {
        "token": "recovery_run",
        "primary_domain": "running",
        "classifier_substring": "recovery",
        "description": "Active-recovery jog.",
    },
    # Strength family — substring "strength" matches all variants.
    {
        "token": "strength_sbd",
        "primary_domain": "strength",
        "classifier_substring": "strength",
        "description": "Squat / bench / deadlift compound day.",
    },
    {
        "token": "strength_lower",
        "primary_domain": "strength",
        "classifier_substring": "strength",
        "description": "Lower-body focus (squat / hip thrust / "
                       "deadlift accessory).",
    },
    {
        "token": "strength_upper",
        "primary_domain": "strength",
        "classifier_substring": "strength",
        "description": "Upper-body focus (bench / row / overhead).",
    },
    {
        "token": "strength_back_biceps",
        "primary_domain": "strength",
        "classifier_substring": "strength",
        "description": "Pull day (back + biceps focus).",
    },
    {
        "token": "strength_push",
        "primary_domain": "strength",
        "classifier_substring": "strength",
        "description": "Push day (chest / shoulders / triceps focus).",
    },
    {
        "token": "strength_accessory",
        "primary_domain": "strength",
        "classifier_substring": "strength",
        "description": "Light accessory / mobility-heavy session.",
    },
    # Cross-training (treated as non-running for running gate; non-strength
    # for strength gate).
    {
        "token": "cross_train",
        "primary_domain": "running",
        "classifier_substring": "cross",
        "description": "Cycling / swim / other non-impact training.",
    },
    {
        "token": "mobility",
        "primary_domain": "recovery",
        "classifier_substring": "mobility",
        "description": "Mobility / yoga / stretching only.",
    },
]


def vocabulary_payload() -> dict[str, Any]:
    """Return the JSON-serialisable shape for the CLI / manifest."""

    return {
        "schema_version": "planned_session_vocabulary.v1",
        "tokens": list(PLANNED_SESSION_VOCABULARY),
        "notes": [
            "Tokens are canonical — passing a token from this list "
            "guarantees the per-domain classifier interprets it "
            "consistently.",
            "Per-domain classifiers use substring matching, not "
            "strict enum enforcement. Strings outside this list "
            "still classify (e.g. 'strength_back_biceps' substring-"
            "matches 'strength'), but the agent loses the canonical "
            "guarantee.",
            "The W21 next-action manifest's `intake_required` "
            "actions for `manual_checkin_missing` SHOULD cite a "
            "token from this list when prompting the user.",
        ],
    }


__all__ = [
    "PLANNED_SESSION_VOCABULARY",
    "vocabulary_payload",
]
