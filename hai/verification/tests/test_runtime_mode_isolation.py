"""Runtime-mode isolation checks for scaffold ablations."""

from __future__ import annotations

import io
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
)
from health_agent_infra.core.runtime_mode import (
    HAI_RUNTIME_MODE_ENV,
    NO_AGENT_SAFE,
)


def test_no_agent_safe_does_not_disable_proposal_validation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    bad_proposal = tmp_path / "bad_proposal.json"
    bad_proposal.write_text('{"schema_version": "bad"}', encoding="utf-8")
    monkeypatch.setenv(HAI_INVOCATION_CONTEXT_ENV, INVOCATION_CONTEXT_AGENT)
    monkeypatch.setenv(HAI_RUNTIME_MODE_ENV, NO_AGENT_SAFE)
    monkeypatch.setenv(HAI_HERMETIC_ENV, "1")
    monkeypatch.setenv(HAI_STATE_DB_ENV, str(tmp_path / "state.db"))
    monkeypatch.setenv(HAI_BASE_DIR_ENV, str(tmp_path / "base"))

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        rc = cli_main([
            "propose",
            "--domain",
            "recovery",
            "--proposal-json",
            str(bad_proposal),
            "--base-dir",
            str(tmp_path / "base"),
            "--db-path",
            str(tmp_path / "state.db"),
        ])

    assert rc == exit_codes.USER_INPUT
    assert stdout_buf.getvalue() == ""
    err = stderr_buf.getvalue()
    assert "mechanism_disabled_marker.v1" not in err
    assert "propose rejected: invariant=required_fields_present" in err
