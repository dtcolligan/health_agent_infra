"""Regression test for v0.1.6 W13: ``hai synthesize --bundle-only``
must refuse when proposal_log has no rows for (for_date, user_id).

Background (Codex r2 B4): the bundle-only branch was bypassing the
same "no proposals" gate that the commit path enforces, returning
``{"snapshot", "proposals": [], "phase_a_firings": []}`` silently.
That contradicts the architecture doc's "every determinism boundary
rejects loudly." Bundle-only is the post-proposal skill-overlay seam,
not a pre-proposal inspection surface — refuse with USER_INPUT when
called against an empty proposal set.
"""

from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import initialize_database


def test_bundle_only_refuses_when_no_proposals(tmp_path: Path):
    db = tmp_path / "state.db"
    initialize_database(db)

    err_buf = StringIO()
    with redirect_stderr(err_buf):
        rc = cli_main([
            "synthesize",
            "--as-of", "2026-04-25",
            "--user-id", "u_test",
            "--bundle-only",
            "--db-path", str(db),
        ])
    assert rc == exit_codes.USER_INPUT
    stderr = err_buf.getvalue()
    assert "--bundle-only requires at least one DomainProposal" in stderr
    assert "u_test" in stderr
    assert "post-proposal skill overlay seam" in stderr
