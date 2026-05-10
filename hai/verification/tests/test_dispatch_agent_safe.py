"""WP-DISPATCH-001: dispatch-time agent_safe enforcement."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.hermetic import (
    HAI_BASE_DIR_ENV,
    HAI_HERMETIC_ENV,
    HAI_STATE_DB_ENV,
)
from health_agent_infra.core.refusal import (
    HAI_INVOCATION_CONTEXT_ENV,
    INVOCATION_CONTEXT_AGENT,
    INVOCATION_CONTEXT_RULE_BASELINE,
    INVOCATION_CONTEXT_USER,
)
from health_agent_infra.core.runtime_mode import (
    HAI_RUNTIME_MODE_ENV,
    NO_AGENT_SAFE,
)


def _run_cli(argv: list[str]) -> tuple[int, str, str]:
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        rc = cli_main(argv)
    return rc, stdout_buf.getvalue(), stderr_buf.getvalue()


def test_agent_context_refuses_agent_safe_false_before_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(HAI_INVOCATION_CONTEXT_ENV, INVOCATION_CONTEXT_AGENT)

    rc, stdout, stderr = _run_cli([
        "intent",
        "commit",
        "--intent-id",
        "intent_fixture_1",
    ])

    assert rc == exit_codes.USER_INPUT
    assert stdout == ""
    envelope = json.loads(stderr.strip())
    assert envelope["schema_version"] == "refusal_envelope.v1"
    assert envelope["step_type"] == "refusal"
    assert envelope["refusal_kind"] == "agent_safe_violation"
    assert envelope["mechanism"] == "agent_safe"
    assert envelope["output_path"] == "hai intent commit"
    assert envelope["details"]["agent_safe"] is False


def test_rule_baseline_context_is_agent_classified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        HAI_INVOCATION_CONTEXT_ENV,
        INVOCATION_CONTEXT_RULE_BASELINE,
    )

    rc, stdout, stderr = _run_cli([
        "intent",
        "commit",
        "--intent-id",
        "intent_fixture_1",
    ])

    assert rc == exit_codes.USER_INPUT
    assert stdout == ""
    envelope = json.loads(stderr.strip())
    assert envelope["refusal_kind"] == "agent_safe_violation"
    assert envelope["details"]["invocation_context"] == (
        INVOCATION_CONTEXT_RULE_BASELINE
    )


def test_user_context_still_reaches_w57_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(HAI_INVOCATION_CONTEXT_ENV, INVOCATION_CONTEXT_USER)

    rc, stdout, stderr = _run_cli([
        "intent",
        "commit",
        "--intent-id",
        "intent_fixture_1",
    ])

    assert rc == exit_codes.USER_INPUT
    assert stdout == ""
    assert "refusal_envelope.v1" not in stderr
    assert "AGENTS.md W57 requires an explicit user commit" in stderr


def test_unset_context_defaults_to_user_authority() -> None:
    rc, _, stderr = _run_cli([
        "intent",
        "commit",
        "--intent-id",
        "intent_fixture_1",
    ])

    assert rc == exit_codes.USER_INPUT
    assert "refusal_envelope.v1" not in stderr
    assert "AGENTS.md W57 requires an explicit user commit" in stderr


def test_no_agent_safe_bypasses_dispatch_but_w57_still_fires(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv(HAI_INVOCATION_CONTEXT_ENV, INVOCATION_CONTEXT_AGENT)
    monkeypatch.setenv(HAI_RUNTIME_MODE_ENV, NO_AGENT_SAFE)
    monkeypatch.setenv(HAI_HERMETIC_ENV, "1")
    monkeypatch.setenv(HAI_STATE_DB_ENV, str(tmp_path / "state.db"))
    monkeypatch.setenv(HAI_BASE_DIR_ENV, str(tmp_path / "base"))

    rc, stdout, stderr = _run_cli([
        "intent",
        "commit",
        "--intent-id",
        "intent_fixture_1",
    ])

    assert rc == exit_codes.USER_INPUT
    assert stdout == ""
    first_line, rest = stderr.split("\n", 1)
    marker = json.loads(first_line)
    assert marker["schema_version"] == "mechanism_disabled_marker.v1"
    assert marker["step_type"] == "mechanism_disabled"
    assert marker["mechanism"] == "agent_safe"
    assert marker["runtime_mode"] == NO_AGENT_SAFE
    assert "AGENTS.md W57 requires an explicit user commit" in rest


def test_invalid_invocation_context_is_user_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(HAI_INVOCATION_CONTEXT_ENV, "scheduler")

    rc, stdout, stderr = _run_cli(["capabilities", "--json"])

    assert rc == exit_codes.USER_INPUT
    assert stdout == ""
    assert HAI_INVOCATION_CONTEXT_ENV in stderr
