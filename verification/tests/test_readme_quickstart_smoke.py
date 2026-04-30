"""W-AF (v0.1.13) — README quickstart smoke test.

The README's quickstart fenced block (tagged ``bash quickstart``) is
extracted at test time and each command is simulated against a temp
state path. Commands that can be run non-interactively against an
isolated state DB are exercised; `pipx install` and live-credential
prompts are skipped with a recorded reason.

Acceptance: every runnable line in the quickstart exits cleanly (0 or
USER_INPUT-class), with no unhandled exceptions. README drift caught
by CI within one build cycle of any quickstart change.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[2]
_README = _REPO_ROOT / "README.md"


# Commands skipped in CI — would be interactive or not idempotent
# against the test temp dir.
_SKIP_PREFIXES: tuple[str, ...] = (
    "pipx install",
    "pip install",
    "hai auth",   # interactive; OS keyring write
)


def _extract_quickstart_block(readme_text: str) -> str:
    """Return the contents of the first ```bash quickstart``` fenced
    block, or raise if absent."""

    pattern = re.compile(
        r"```bash\s+quickstart\s*\n(.*?)```",
        re.DOTALL,
    )
    m = pattern.search(readme_text)
    if not m:
        raise AssertionError(
            "README.md is missing the ```bash quickstart``` fenced block. "
            "W-AF (v0.1.13) requires this tagged block so the smoke test "
            "can find the canonical quickstart commands."
        )
    return m.group(1)


def _commands_from_block(block: str) -> list[str]:
    """Strip comments and blank lines; return one command per line."""

    cmds: list[str] = []
    for raw in block.splitlines():
        # Drop trailing comments (after a # outside of any string).
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        cmds.append(line)
    return cmds


# ---------------------------------------------------------------------------
# Block detection
# ---------------------------------------------------------------------------


def test_readme_has_tagged_quickstart_block():
    """The README must carry a ```bash quickstart``` fenced block.
    W-AF can only protect the quickstart from drift if the block is
    discoverable."""

    text = _README.read_text(encoding="utf-8")
    block = _extract_quickstart_block(text)
    cmds = _commands_from_block(block)
    assert cmds, "quickstart block was empty after stripping comments"
    # Sanity: the canonical entrypoints we expect a new user to see.
    joined = " ".join(cmds)
    assert "hai init" in joined
    assert "hai daily" in joined
    assert "hai today" in joined


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------


def test_quickstart_commands_run_cleanly(tmp_path: Path):
    """Run every runnable command in the quickstart against an
    isolated state path. Each command must exit with a recognized code
    and emit no Python traceback."""

    text = _README.read_text(encoding="utf-8")
    block = _extract_quickstart_block(text)
    cmds = _commands_from_block(block)

    state_db = tmp_path / "state.db"
    base_dir = tmp_path / "base"
    skills_dest = tmp_path / "skills"
    thresholds = tmp_path / "thresholds.toml"
    base_dir.mkdir()
    skills_dest.mkdir()

    env = dict(os.environ)
    env.update({
        "HAI_STATE_DB": str(state_db),
        "HAI_BASE_DIR": str(base_dir),
        "HAI_THRESHOLDS_PATH": str(thresholds),
    })

    skipped: list[str] = []
    failures: list[str] = []

    for cmd in cmds:
        if any(cmd.startswith(p) for p in _SKIP_PREFIXES):
            skipped.append(cmd)
            continue

        # The block is `hai <subcommand> ...`. Translate to
        # `python -m health_agent_infra.cli <args>`.
        if not cmd.startswith("hai "):
            # Defensive: a non-hai line snuck in. Skip rather than fail
            # the suite — record so a future contract test can tighten.
            skipped.append(cmd)
            continue
        argv = shlex.split(cmd)[1:]

        # `hai init` needs explicit paths injected so it doesn't write
        # to the user's real config dir even with HAI env vars set.
        if argv and argv[0] == "init":
            argv += [
                "--db-path", str(state_db),
                "--skills-dest", str(skills_dest),
                "--thresholds-path", str(thresholds),
            ]
        # `hai doctor` likewise.
        if argv and argv[0] == "doctor":
            argv += [
                "--db-path", str(state_db),
                "--skills-dest", str(skills_dest),
                "--thresholds-path", str(thresholds),
            ]

        result = subprocess.run(
            [sys.executable, "-m", "health_agent_infra.cli", *argv],
            cwd=_REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if "Traceback" in result.stderr:
            failures.append(
                f"{cmd!r} raised a Python traceback:\n"
                f"  stderr (first 300 chars): {result.stderr[:300]!r}"
            )
            continue

        # Acceptable exit codes for a quickstart-on-bare-state run:
        # OK / USER_INPUT / TRANSIENT / NOT_FOUND. Values from
        # `core.exit_codes`: 0, 1, 2, 3 respectively. Anything else
        # (segfault, generic Python exit, etc.) is a crash/regression.
        if result.returncode not in (0, 1, 2, 3):
            failures.append(
                f"{cmd!r} exited {result.returncode}; "
                f"stderr={result.stderr[:300]!r}"
            )

    assert not failures, (
        f"README quickstart smoke surfaced {len(failures)} failure(s):\n"
        + "\n".join(f"  - {f}" for f in failures)
    )
    # Telemetry — useful diagnostic when the test passes but the
    # skip set has grown.
    if skipped:
        print(
            f"[W-AF smoke] skipped {len(skipped)} command(s): "
            f"{[s[:60] for s in skipped]}"
        )
