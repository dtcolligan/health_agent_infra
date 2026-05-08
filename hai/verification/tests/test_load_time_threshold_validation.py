"""Load-time threshold-type validation (F-CDX-IR-R2-01).

Codex round-2 review caught that the W-A coercer helpers protected
threshold reads at the call site but missed direct numeric leaf
consumers — ``protein_ratio < cfg["low_max_ratio"]``,
``float(targets["protein_target_g"])``, ``calorie_deficit -
cfg["penalty"]``. Because Python bools are numeric, a TOML override
of ``low_max_ratio = true`` would silently flow through as ``1``
even after the W-A sweep.

The architectural fix: validate threshold types **at load time**
against ``DEFAULT_THRESHOLDS``. Consumers never see a bool-shaped
numeric value regardless of how they read the leaf.

These tests exercise the validator itself + verify the exact
silent-coercion class Codex named is now blocked.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from health_agent_infra.core.config import (
    ConfigCoerceError,
    DEFAULT_THRESHOLDS,
    _is_strict_bool,
    _validate_threshold_types,
    load_thresholds,
)


# ---------------------------------------------------------------------------
# _is_strict_bool — must distinguish bool from int
# ---------------------------------------------------------------------------


def test_strict_bool_accepts_bools() -> None:
    assert _is_strict_bool(True) is True
    assert _is_strict_bool(False) is True


def test_strict_bool_rejects_ints() -> None:
    """The whole point: True is an int subclass; the helper must
    distinguish them."""

    assert _is_strict_bool(1) is False
    assert _is_strict_bool(0) is False
    assert _is_strict_bool(-1) is False


def test_strict_bool_rejects_floats_strings_none() -> None:
    assert _is_strict_bool(1.0) is False
    assert _is_strict_bool("True") is False
    assert _is_strict_bool(None) is False


# ---------------------------------------------------------------------------
# _validate_threshold_types — leaf-by-leaf
# ---------------------------------------------------------------------------


def _validate(merged: dict, default: dict) -> None:
    _validate_threshold_types(merged=merged, default=default)


class TestBoolOnNumericRejection:
    """The headline bug: a TOML override of ``true`` against a
    numeric default must raise."""

    def test_true_against_int_default_rejected(self) -> None:
        with pytest.raises(ConfigCoerceError, match="expected int"):
            _validate({"x": True}, {"x": 5})

    def test_false_against_int_default_rejected(self) -> None:
        with pytest.raises(ConfigCoerceError, match="expected int"):
            _validate({"x": False}, {"x": 5})

    def test_true_against_float_default_rejected(self) -> None:
        with pytest.raises(ConfigCoerceError, match="expected float"):
            _validate({"x": True}, {"x": 1.5})

    def test_false_against_float_default_rejected(self) -> None:
        with pytest.raises(ConfigCoerceError, match="expected float"):
            _validate({"x": False}, {"x": 1.5})

    def test_int_against_bool_default_rejected(self) -> None:
        with pytest.raises(ConfigCoerceError, match="expected bool"):
            _validate({"x": 1}, {"x": True})


class TestTypeMatchingPasses:
    def test_int_override_int_default_passes(self) -> None:
        _validate({"x": 9}, {"x": 5})

    def test_int_override_float_default_passes(self) -> None:
        """TOML allows writing ``1`` for a float default; accept it."""

        _validate({"x": 9}, {"x": 1.5})

    def test_float_override_float_default_passes(self) -> None:
        _validate({"x": 2.5}, {"x": 1.5})

    def test_bool_override_bool_default_passes(self) -> None:
        _validate({"x": False}, {"x": True})

    def test_str_override_str_default_passes(self) -> None:
        _validate({"x": "b"}, {"x": "a"})

    def test_list_override_list_default_passes(self) -> None:
        _validate({"x": [1, 2]}, {"x": [3]})


class TestStringNumericRejection:
    def test_string_against_int_default_rejected(self) -> None:
        with pytest.raises(ConfigCoerceError, match="expected int"):
            _validate({"x": "5"}, {"x": 5})

    def test_string_against_float_default_rejected(self) -> None:
        with pytest.raises(ConfigCoerceError, match="expected float"):
            _validate({"x": "1.5"}, {"x": 1.5})


class TestStructuralRejection:
    def test_dict_against_int_rejected(self) -> None:
        with pytest.raises(ConfigCoerceError, match="expected int"):
            _validate({"x": {"y": 5}}, {"x": 5})

    def test_int_against_dict_rejected(self) -> None:
        with pytest.raises(ConfigCoerceError, match="expected mapping"):
            _validate({"x": 5}, {"x": {"y": 5}})

    def test_list_against_int_rejected(self) -> None:
        with pytest.raises(ConfigCoerceError, match="expected int"):
            _validate({"x": [1, 2]}, {"x": 5})


class TestNoneDefaultIsUnvalidated:
    """A None default expresses no policy; any override is allowed."""

    def test_none_default_accepts_anything(self) -> None:
        _validate({"x": True}, {"x": None})
        _validate({"x": 5}, {"x": None})
        _validate({"x": "anything"}, {"x": None})


class TestDeepNestingTraversal:
    def test_violation_at_depth_3_caught_with_dotted_path(self) -> None:
        default = {"a": {"b": {"c": 1.5}}}
        merged = {"a": {"b": {"c": True}}}
        with pytest.raises(ConfigCoerceError, match="'a\\.b\\.c'"):
            _validate(merged, default)

    def test_unrelated_branch_unaffected(self) -> None:
        default = {"a": {"x": 5}, "b": {"y": 1.5}}
        merged = {"a": {"x": 9}, "b": {"y": 2.5}}
        _validate(merged, default)

    def test_partial_override_does_not_remove_default_keys(self) -> None:
        """User overrides only the keys they care about; missing keys
        stay defaulted; validator only checks merged-tree leaves."""

        default = {"a": {"x": 5, "y": 1.5}}
        merged = {"a": {"x": 9, "y": 1.5}}
        _validate(merged, default)


# ---------------------------------------------------------------------------
# Integration — load_thresholds end-to-end against a real TOML
# ---------------------------------------------------------------------------


def test_load_thresholds_rejects_bool_on_numeric_leaf(tmp_path: Path) -> None:
    """The exact regression Codex round 2 identified — a user
    TOML override of ``true`` against a numeric default must fail
    at load time, not silently flow through as ``1``."""

    toml = tmp_path / "thresholds.toml"
    toml.write_text(
        '[policy.nutrition]\n'
        'r_extreme_deficiency_min_meals_count = true\n',
        encoding="utf-8",
    )
    with pytest.raises(ConfigCoerceError, match="expected int"):
        load_thresholds(toml)


def test_load_thresholds_rejects_bool_on_float_leaf(tmp_path: Path) -> None:
    toml = tmp_path / "thresholds.toml"
    toml.write_text(
        '[policy.nutrition]\n'
        'r_extreme_deficiency_min_calorie_deficit_kcal = true\n',
        encoding="utf-8",
    )
    with pytest.raises(ConfigCoerceError, match="expected float"):
        load_thresholds(toml)


def test_load_thresholds_accepts_valid_numeric_override(tmp_path: Path) -> None:
    toml = tmp_path / "thresholds.toml"
    toml.write_text(
        '[policy.nutrition]\n'
        'r_extreme_deficiency_min_meals_count = 3\n',
        encoding="utf-8",
    )
    merged = load_thresholds(toml)
    assert merged["policy"]["nutrition"][
        "r_extreme_deficiency_min_meals_count"
    ] == 3


def test_load_thresholds_accepts_valid_bool_override(tmp_path: Path) -> None:
    """When a default IS bool, an override of ``true``/``false`` must
    still pass — the validator rejects type changes, not bools per se."""

    toml = tmp_path / "thresholds.toml"
    toml.write_text(
        '[pull.garmin_live]\n'
        'retry_on_rate_limit = false\n',
        encoding="utf-8",
    )
    merged = load_thresholds(toml)
    assert merged["pull"]["garmin_live"]["retry_on_rate_limit"] is False


def test_default_thresholds_self_validate() -> None:
    """``DEFAULT_THRESHOLDS`` must validate cleanly against itself —
    if this ever fails, a maintainer added a default whose nested
    types aren't internally consistent."""

    _validate_threshold_types(
        merged=DEFAULT_THRESHOLDS, default=DEFAULT_THRESHOLDS,
    )
