"""v0.1.10 W-D — running_activity projector input validation.

Replaces bare ``KeyError`` failures from missing required fields with
typed ``ActivityProjectorInputError`` so the contract is discoverable
to test, ops, and adapter authors.

Reproduces F-C-01 + F-C-02 from ``audit_findings.md``.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager

import pytest

from health_agent_infra.core.state.projectors.running_activity import (
    ActivityProjectorInputError,
    project_activity,
)


@contextmanager
def _conn():
    """In-memory connection — schema doesn't matter, validator runs first.

    Wrapped as a context manager so the connection is always closed on
    exit (W-N-broader: bare ``sqlite3.connect()`` plus inline use leaks
    when the validator raises before the test gets a chance to close).
    """

    conn = sqlite3.connect(":memory:")
    try:
        yield conn
    finally:
        conn.close()


def _minimal_valid_activity() -> dict:
    return {
        "activity_id": "test_001",
        "user_id": "u_local_1",
        "as_of_date": "2026-04-27",
        "raw_json": "{}",
        "activity_type": "Run",
        "distance_m": 5000.0,
        "elapsed_time_s": 1800,
    }


class TestActivityProjectorValidation:
    def test_missing_user_id_raises_typed_error(self) -> None:
        activity = _minimal_valid_activity()
        del activity["user_id"]
        with pytest.raises(ActivityProjectorInputError, match="user_id"):
            with _conn() as conn:
                project_activity(conn, activity=activity)

    def test_missing_activity_id_raises_typed_error(self) -> None:
        activity = _minimal_valid_activity()
        del activity["activity_id"]
        with pytest.raises(ActivityProjectorInputError, match="activity_id"):
            with _conn() as conn:
                project_activity(conn, activity=activity)

    def test_missing_raw_json_raises_typed_error(self) -> None:
        activity = _minimal_valid_activity()
        del activity["raw_json"]
        with pytest.raises(ActivityProjectorInputError, match="raw_json"):
            with _conn() as conn:
                project_activity(conn, activity=activity)

    def test_missing_as_of_date_raises_typed_error(self) -> None:
        activity = _minimal_valid_activity()
        del activity["as_of_date"]
        with pytest.raises(ActivityProjectorInputError, match="as_of_date"):
            with _conn() as conn:
                project_activity(conn, activity=activity)

    def test_multiple_missing_keys_listed_in_error(self) -> None:
        activity = {"activity_type": "Run"}
        with pytest.raises(ActivityProjectorInputError) as exc_info:
            with _conn() as conn:
                project_activity(conn, activity=activity)
        msg = str(exc_info.value)
        # All four required keys should appear in the missing list
        for key in ("activity_id", "user_id", "as_of_date", "raw_json"):
            assert key in msg

    def test_non_dict_payload_raises_typed_error(self) -> None:
        with pytest.raises(ActivityProjectorInputError, match="must be a dict"):
            with _conn() as conn:
                project_activity(conn, activity="not_a_dict")  # type: ignore[arg-type]

    def test_does_not_swallow_unrelated_errors(self) -> None:
        """Validation runs first, but a complete payload should still
        surface DB errors normally — i.e. validation doesn't mask
        downstream issues."""

        # The in-memory DB has no `running_activity` table, so the
        # SQL execution will raise OperationalError. We just want to
        # confirm the validator passes a valid payload through.
        activity = _minimal_valid_activity()
        with pytest.raises(sqlite3.OperationalError):
            with _conn() as conn:
                project_activity(conn, activity=activity)
