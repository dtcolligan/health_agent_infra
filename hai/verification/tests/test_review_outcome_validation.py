"""Regression test for the v0.1.6 review-outcome validation boundary.

Background: the audit cycle (Codex r1 + internal + Codex r2) found
that ``hai review record`` was NOT a real determinism boundary. The
CLI handler called ``json.loads()`` and passed the result straight
into ``record_review_outcome()`` without runtime type validation.
The JSONL audit row preserved the raw payload
(``"followed_recommendation": "definitely"``); the SQLite projector
coerced via ``_bool_to_int()`` (Python truthiness, so ``"definitely"
→ 1``). The audit chain disagreed with itself across storage layers.

This test pins the v0.1.6 fix: the new
``validate_review_outcome_dict`` enforces strict bool semantics on
``followed_recommendation`` (and other typed fields) before any
write. Truthy strings, truthy ints, and missing fields all refuse
with named invariants.
"""

from __future__ import annotations

import pytest

from health_agent_infra.core.writeback.outcome import (
    INTENSITY_DELTA_ENUM,
    REQUIRED_OUTCOME_FIELDS,
    ReviewOutcomeValidationError,
    validate_review_outcome_dict,
)


# ---------------------------------------------------------------------------
# Happy path — minimal valid payload + full enrichment payload both pass
# ---------------------------------------------------------------------------

def _minimal_valid() -> dict:
    return {
        "review_event_id": "rev_2026-04-25_u_recovery",
        "recommendation_id": "rec_2026-04-24_u_recovery_01",
        "user_id": "u",
        "followed_recommendation": True,
    }


def test_minimal_valid_payload_passes():
    validate_review_outcome_dict(_minimal_valid())


def test_full_enrichment_payload_passes():
    payload = {
        **_minimal_valid(),
        "domain": "recovery",
        "self_reported_improvement": False,
        "free_text": "felt rough",
        "completed": True,
        "intensity_delta": "harder",
        "duration_minutes": 47,
        "pre_energy_score": 3,
        "post_energy_score": 4,
        "disagreed_firing_ids": ["fire_1", "fire_2"],
    }
    validate_review_outcome_dict(payload)


# ---------------------------------------------------------------------------
# The truth-fork: strict-bool enforcement on followed_recommendation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_value,expected_invariant", [
    ("definitely", "followed_recommendation_must_be_bool"),
    ("yes", "followed_recommendation_must_be_bool"),
    (1, "followed_recommendation_must_be_bool"),
    (0, "followed_recommendation_must_be_bool"),
    ("true", "followed_recommendation_must_be_bool"),
    (None, "followed_recommendation_must_be_bool"),
])
def test_followed_recommendation_must_be_strict_bool(bad_value, expected_invariant):
    """The whole point of this validator is to refuse the silent
    JSONL-vs-SQLite divergence. Truthy strings, truthy ints, falsy
    ints, and None all fail."""

    payload = {**_minimal_valid(), "followed_recommendation": bad_value}
    with pytest.raises(ReviewOutcomeValidationError) as exc_info:
        validate_review_outcome_dict(payload)
    assert exc_info.value.invariant == expected_invariant


def test_self_reported_improvement_must_be_bool_or_null():
    payload = {**_minimal_valid(), "self_reported_improvement": "maybe"}
    with pytest.raises(ReviewOutcomeValidationError) as exc_info:
        validate_review_outcome_dict(payload)
    assert exc_info.value.invariant == (
        "self_reported_improvement_must_be_bool_or_null"
    )


def test_self_reported_improvement_null_is_fine():
    payload = {**_minimal_valid(), "self_reported_improvement": None}
    validate_review_outcome_dict(payload)


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("missing_field", sorted(REQUIRED_OUTCOME_FIELDS))
def test_each_required_field_is_required(missing_field):
    payload = _minimal_valid()
    del payload[missing_field]
    with pytest.raises(ReviewOutcomeValidationError) as exc_info:
        validate_review_outcome_dict(payload)
    assert exc_info.value.invariant == "required_fields_present"
    assert missing_field in str(exc_info.value)


def test_non_dict_payload_fails():
    with pytest.raises(ReviewOutcomeValidationError) as exc_info:
        validate_review_outcome_dict(["not", "a", "dict"])
    assert exc_info.value.invariant == "required_fields_present"


# ---------------------------------------------------------------------------
# String fields
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field,invariant", [
    ("review_event_id", "review_event_id_str"),
    ("recommendation_id", "recommendation_id_str"),
    ("user_id", "user_id_str"),
])
def test_string_fields_must_be_non_empty_strings(field, invariant):
    for bad in ("", 42, None, ["list"], {"k": "v"}):
        payload = {**_minimal_valid(), field: bad}
        with pytest.raises(ReviewOutcomeValidationError) as exc_info:
            validate_review_outcome_dict(payload)
        assert exc_info.value.invariant == invariant


# ---------------------------------------------------------------------------
# Enrichment field type checks
# ---------------------------------------------------------------------------

def test_completed_must_be_bool_when_present():
    payload = {**_minimal_valid(), "completed": "yes"}
    with pytest.raises(ReviewOutcomeValidationError) as exc_info:
        validate_review_outcome_dict(payload)
    assert exc_info.value.invariant == "completed_must_be_bool_or_null"


def test_intensity_delta_must_be_in_enum():
    payload = {**_minimal_valid(), "intensity_delta": "way_harder"}
    with pytest.raises(ReviewOutcomeValidationError) as exc_info:
        validate_review_outcome_dict(payload)
    assert exc_info.value.invariant == "intensity_delta_enum"


@pytest.mark.parametrize("good", sorted(INTENSITY_DELTA_ENUM))
def test_intensity_delta_each_enum_value_passes(good):
    payload = {**_minimal_valid(), "intensity_delta": good}
    validate_review_outcome_dict(payload)


def test_duration_minutes_rejects_bool():
    """``isinstance(True, int)`` is True in Python; the validator
    must use a strict-bool check to reject booleans on int-typed
    fields."""

    payload = {**_minimal_valid(), "duration_minutes": True}
    with pytest.raises(ReviewOutcomeValidationError) as exc_info:
        validate_review_outcome_dict(payload)
    assert exc_info.value.invariant == "duration_minutes_int_or_null"


@pytest.mark.parametrize("bad", [0, 6, -1, 100, "3", True, 2.5])
def test_pre_energy_score_must_be_int_in_range(bad):
    payload = {**_minimal_valid(), "pre_energy_score": bad}
    with pytest.raises(ReviewOutcomeValidationError) as exc_info:
        validate_review_outcome_dict(payload)
    assert exc_info.value.invariant == "pre_energy_score_in_range"


def test_disagreed_firing_ids_rejects_non_string_elements():
    payload = {**_minimal_valid(), "disagreed_firing_ids": ["ok", 42]}
    with pytest.raises(ReviewOutcomeValidationError) as exc_info:
        validate_review_outcome_dict(payload)
    assert exc_info.value.invariant == (
        "disagreed_firing_ids_list_of_str_or_null"
    )


def test_disagreed_firing_ids_empty_list_is_fine():
    """Empty list = 'I was asked, no disagreements' (different from
    None which would be 'not asked')."""

    payload = {**_minimal_valid(), "disagreed_firing_ids": []}
    validate_review_outcome_dict(payload)


# ---------------------------------------------------------------------------
# CLI integration — the full handler refuses with USER_INPUT
# ---------------------------------------------------------------------------

def test_cmd_review_record_refuses_truthy_string_with_named_invariant(
    tmp_path,
):
    import json
    from contextlib import redirect_stderr
    from io import StringIO
    from health_agent_infra.cli import main as cli_main
    from health_agent_infra.core import exit_codes

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({
        "review_event_id": "r1",
        "recommendation_id": "rec1",
        "user_id": "u",
        "followed_recommendation": "definitely",
    }), encoding="utf-8")

    err_buf = StringIO()
    with redirect_stderr(err_buf):
        rc = cli_main([
            "review", "record",
            "--outcome-json", str(bad),
            "--base-dir", str(tmp_path),
        ])
    assert rc == exit_codes.USER_INPUT
    stderr = err_buf.getvalue()
    assert "invariant=followed_recommendation_must_be_bool" in stderr
    # The payload must NOT have been written to JSONL.
    jsonl = tmp_path / "review_outcomes.jsonl"
    assert not jsonl.exists() or jsonl.read_text() == ""
