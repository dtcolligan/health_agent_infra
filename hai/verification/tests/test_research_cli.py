"""Regression test for v0.1.6 W17 / Codex C4: bounded local-only
research CLI replaces the `python3 -c` pattern in expert-explainer.

The skill's privacy invariant ("no network, local-only retrieval") is
now enforced by the permission matcher, not just by skill prose.
``Bash(python3 -c *)`` was removed from ``allowed-tools``;
``Bash(hai research topics *)`` and ``Bash(hai research search *)``
take its place.
"""

from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes


def test_research_topics_lists_allowlist():
    out_buf = StringIO()
    with redirect_stdout(out_buf):
        rc = cli_main(["research", "topics"])
    assert rc == exit_codes.OK
    payload = json.loads(out_buf.getvalue())
    assert "topics" in payload
    assert "sleep_debt" in payload["topics"]
    # Topics are sorted.
    assert payload["topics"] == sorted(payload["topics"])


def test_research_search_returns_sources_for_known_topic():
    out_buf = StringIO()
    with redirect_stdout(out_buf):
        rc = cli_main(["research", "search", "--topic", "sleep_debt"])
    assert rc == exit_codes.OK
    payload = json.loads(out_buf.getvalue())
    assert payload["topic"] == "sleep_debt"
    assert payload["abstain_reason"] is None
    assert len(payload["sources"]) > 0
    for s in payload["sources"]:
        assert {"source_id", "title", "source_class",
                "origin_path", "excerpt"}.issubset(s.keys())


def test_research_search_abstains_for_unknown_topic():
    out_buf = StringIO()
    with redirect_stdout(out_buf):
        rc = cli_main(["research", "search", "--topic", "not_real_topic"])
    assert rc == exit_codes.OK
    payload = json.loads(out_buf.getvalue())
    assert payload["topic"] == "not_real_topic"
    assert payload["abstain_reason"] is not None
    assert "allowlist" in payload["abstain_reason"]
    assert payload["sources"] == []


def test_research_surface_does_not_accept_user_context():
    """The CLI exposes only --topic; there is no flag to attach user
    state. The privacy-violation booleans on RetrievalQuery
    (user_context_sent, operator_initiated) are not configurable
    through this surface — verifying via the parser that no such
    flag exists."""

    import subprocess
    result = subprocess.run(
        ["hai", "research", "search", "--help"],
        capture_output=True, text=True,
    )
    assert "--user-context" not in result.stdout
    assert "--operator-initiated" not in result.stdout
    # Only --topic and the standard help flag should be present.
    assert "--topic" in result.stdout


def test_research_commands_appear_in_capabilities_manifest():
    """The capabilities manifest must list both commands so agents can
    discover them via `hai capabilities`."""

    import subprocess
    result = subprocess.run(
        ["hai", "capabilities"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    manifest = json.loads(result.stdout)
    cmd_names = {c["command"] for c in manifest["commands"]}
    assert "hai research topics" in cmd_names
    assert "hai research search" in cmd_names

    # Both must be agent-safe + read-only.
    by_name = {c["command"]: c for c in manifest["commands"]}
    for name in ("hai research topics", "hai research search"):
        assert by_name[name]["agent_safe"] is True
        assert by_name[name]["mutation"] == "read-only"


def test_expert_explainer_skill_no_longer_grants_python3_c():
    """The privacy boundary is now enforced by allowed-tools, not just
    by skill prose. python3 -c must not be on the permission list."""

    skill_path = (
        Path(__file__).resolve().parents[2]
        / "src" / "health_agent_infra" / "skills"
        / "expert-explainer" / "SKILL.md"
    )
    text = skill_path.read_text(encoding="utf-8")
    # Find the allowed-tools line (frontmatter).
    allowed_line = next(
        line for line in text.splitlines()
        if line.startswith("allowed-tools:")
    )
    assert "python3 -c" not in allowed_line
    assert "hai research" in allowed_line
