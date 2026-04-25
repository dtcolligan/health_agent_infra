"""Skill ↔ CLI drift regression test (W3 in the v0.1.6 plan).

Wraps ``scripts/check_skill_cli_drift.py`` and asserts a clean run.
A failure means a SKILL.md mentions a flag the CLI doesn't have on
the command it's named with — exactly the class of bug that bit a
real user session in 2026-04-25 (intent-router said
``hai review record --completed 0|1`` while the CLI takes
``--outcome-json`` + ``--completed yes|no``).

If this test fails: read the validator's stdout from the failure
trace, fix the SKILL.md (or, if the CLI surface changed, update the
SKILL.md to match), and re-run.

The validator only inspects fenced code blocks — inline-backtick
mentions of ``hai foo --bar`` aren't covered. Maintainers should
keep inline references conservative; if a third drift surfaces in
prose-only references, extend the validator to include them.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "check_skill_cli_drift.py"


def test_skill_cli_drift_validator_reports_clean():
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, (
        "Skill ↔ CLI drift detected. Validator stdout:\n"
        f"{proc.stdout}\n"
        f"--- stderr ---\n{proc.stderr}"
    )
    assert "OK: no skill ↔ CLI drift detected." in proc.stdout
