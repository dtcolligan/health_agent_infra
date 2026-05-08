"""Tests for v0.1.10 W-A — typed threshold coercer helpers.

The helpers replace bare ``int()`` / ``float()`` / ``bool()`` calls
against config leaves, eliminating the bool-as-int silent-coercion
class of bug surfaced in v0.1.9 backlog B1 and reproduced in
``audit_findings.md`` F-A-01.
"""

from __future__ import annotations

import pytest

from health_agent_infra.core.config import (
    ConfigCoerceError,
    coerce_bool,
    coerce_float,
    coerce_int,
)


# ---------------------------------------------------------------------------
# coerce_int
# ---------------------------------------------------------------------------

class TestCoerceInt:
    def test_accepts_int(self) -> None:
        assert coerce_int(5, name="t") == 5
        assert coerce_int(0, name="t") == 0
        assert coerce_int(-3, name="t") == -3

    def test_accepts_whole_float(self) -> None:
        assert coerce_int(5.0, name="t") == 5
        assert coerce_int(-3.0, name="t") == -3

    def test_accepts_numeric_string(self) -> None:
        assert coerce_int("5", name="t") == 5
        assert coerce_int("-3", name="t") == -3

    def test_rejects_bool_true(self) -> None:
        with pytest.raises(ConfigCoerceError, match="bool True"):
            coerce_int(True, name="threshold_x")

    def test_rejects_bool_false(self) -> None:
        with pytest.raises(ConfigCoerceError, match="bool False"):
            coerce_int(False, name="threshold_x")

    def test_rejects_fractional_float(self) -> None:
        with pytest.raises(ConfigCoerceError, match="fractional float"):
            coerce_int(5.5, name="t")

    def test_rejects_non_numeric_string(self) -> None:
        with pytest.raises(ConfigCoerceError, match="non-numeric string"):
            coerce_int("not_a_number", name="t")

    def test_rejects_none(self) -> None:
        with pytest.raises(ConfigCoerceError, match="NoneType"):
            coerce_int(None, name="t")

    def test_rejects_list(self) -> None:
        with pytest.raises(ConfigCoerceError, match="list"):
            coerce_int([1, 2], name="t")

    def test_error_includes_threshold_name(self) -> None:
        with pytest.raises(ConfigCoerceError, match="my_specific_name"):
            coerce_int(True, name="my_specific_name")


# ---------------------------------------------------------------------------
# coerce_float
# ---------------------------------------------------------------------------

class TestCoerceFloat:
    def test_accepts_float(self) -> None:
        assert coerce_float(5.5, name="t") == 5.5
        assert coerce_float(0.0, name="t") == 0.0

    def test_accepts_int(self) -> None:
        assert coerce_float(5, name="t") == 5.0
        assert coerce_float(-3, name="t") == -3.0

    def test_accepts_numeric_string(self) -> None:
        assert coerce_float("5.5", name="t") == 5.5
        assert coerce_float("0.7", name="t") == 0.7

    def test_rejects_bool_true(self) -> None:
        with pytest.raises(ConfigCoerceError, match="bool True"):
            coerce_float(True, name="t")

    def test_rejects_bool_false(self) -> None:
        with pytest.raises(ConfigCoerceError, match="bool False"):
            coerce_float(False, name="t")

    def test_rejects_non_numeric_string(self) -> None:
        with pytest.raises(ConfigCoerceError, match="non-numeric string"):
            coerce_float("nope", name="t")


# ---------------------------------------------------------------------------
# coerce_bool
# ---------------------------------------------------------------------------

class TestCoerceBool:
    def test_accepts_bool_true(self) -> None:
        assert coerce_bool(True, name="t") is True

    def test_accepts_bool_false(self) -> None:
        assert coerce_bool(False, name="t") is False

    def test_accepts_string_true(self) -> None:
        assert coerce_bool("true", name="t") is True
        assert coerce_bool("True", name="t") is True
        assert coerce_bool("TRUE", name="t") is True

    def test_accepts_string_false(self) -> None:
        assert coerce_bool("false", name="t") is False
        assert coerce_bool("False", name="t") is False

    def test_accepts_1_and_0_strings(self) -> None:
        assert coerce_bool("1", name="t") is True
        assert coerce_bool("0", name="t") is False

    def test_rejects_int(self) -> None:
        with pytest.raises(ConfigCoerceError, match="int"):
            coerce_bool(1, name="t")

    def test_rejects_float(self) -> None:
        with pytest.raises(ConfigCoerceError, match="float"):
            coerce_bool(1.0, name="t")

    def test_rejects_other_strings(self) -> None:
        with pytest.raises(ConfigCoerceError, match="non-boolean string"):
            coerce_bool("yes", name="t")
        with pytest.raises(ConfigCoerceError, match="non-boolean string"):
            coerce_bool("no", name="t")
