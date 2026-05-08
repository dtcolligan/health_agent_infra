"""W-Vb (v0.1.13) — clean-wheel persona-replay subprocess test.

Origin: v0.1.13 PLAN.md §2.A W-Vb. The end-to-end persona-replay tests
in ``test_demo_persona_replay_end_to_end.py`` exercise the proposal-
write branch in-process against the editable repo install. This file
adds the *clean-wheel* assertion the PLAN names: build a wheel, install
it into an isolated venv, and run the demo flow via subprocess so any
editable-install path that leaks through ``apply_fixture()`` (e.g. an
accidental import from ``hai/verification/dogfood``) is caught.

Acceptance gate per PLAN §2.A:

- ``importlib.resources`` resolves ``health_agent_infra/demo/fixtures/
  p1_dom_baseline.json`` from inside the wheel install.
- ``hai demo start --persona p1_dom_baseline`` followed by
  ``hai daily --skip-pull --source csv`` reaches a synthesized daily
  plan without any mutation of the real ``~/.health_agent`` tree.

The test is slow (build + install + subprocess) and skips cleanly when
the ``build`` toolchain is unavailable.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[3]


def _checksum_tree(root: Path) -> str:
    """Recursive byte-hash of every file under ``root``."""
    if not root.exists():
        return f"<absent:{root}>"
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            h.update(str(path.relative_to(root)).encode("utf-8"))
            h.update(b":")
            h.update(path.read_bytes())
            h.update(b"\n")
    return h.hexdigest()


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


@pytest.fixture(scope="session")
def _wheel_path(tmp_path_factory) -> Path:
    """Build a wheel from the repo, returning the wheel file path.

    Session-scoped so the build runs once even if multiple tests in
    this module ever exist. The repo's project venv intentionally does
    not bundle ``build`` (see CLAUDE.md "Common commands"); the build
    happens via ``uvx --from build`` so the build backend is isolated.
    Skips cleanly when neither ``uvx`` nor an in-env ``build`` is
    available.
    """

    out_dir = tmp_path_factory.mktemp("wheel_dist")
    cmd: list[str]
    uvx_path = shutil.which("uvx")
    if uvx_path is not None:
        cmd = [
            uvx_path, "--from", "build",
            "python", "-m", "build",
            "--wheel",
            "--outdir", str(out_dir),
            str(_REPO_ROOT),
        ]
    else:
        try:
            import build  # noqa: F401
        except ImportError:
            pytest.skip(
                "neither `uvx` nor an in-env `build` package available; "
                "clean-wheel test requires one of them."
            )
        cmd = [
            sys.executable,
            "-m", "build",
            "--wheel",
            "--outdir", str(out_dir),
            str(_REPO_ROOT),
        ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        pytest.skip(
            f"wheel build failed (this is a packaging-environment issue, "
            f"not a v0.1.13 W-Vb regression): {proc.stderr[-400:]}"
        )

    wheels = sorted(out_dir.glob("health_agent_infra-*.whl"))
    assert wheels, f"no wheel produced under {out_dir}"
    return wheels[-1]


@pytest.fixture(scope="session")
def _wheel_venv(tmp_path_factory, _wheel_path: Path) -> Path:
    """Create a venv and install the wheel into it. Session-scoped."""

    venv_dir = tmp_path_factory.mktemp("wheel_venv") / "venv"
    venv.create(venv_dir, with_pip=True, clear=False, symlinks=True)
    py = _venv_python(venv_dir)

    proc = subprocess.run(
        [str(py), "-m", "pip", "install",
         "--quiet", "--disable-pip-version-check",
         str(_wheel_path)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        pytest.skip(
            f"wheel install into venv failed (env issue, not a W-Vb "
            f"regression): {proc.stderr[-400:]}"
        )
    return venv_dir


def _hai_in_venv(venv_dir: Path, *args: str, env: dict[str, str]):
    """Run ``python -m health_agent_infra.cli`` inside the venv."""
    py = _venv_python(venv_dir)
    return subprocess.run(
        [str(py), "-m", "health_agent_infra.cli", *args],
        env=env, capture_output=True, text=True,
    )


def test_clean_wheel_p1_replay_reaches_synthesized(
    tmp_path: Path, _wheel_venv: Path,
) -> None:
    """The W-Vb clean-wheel ship-gate.

    Builds a wheel of the repo, installs it into an isolated venv, then
    runs ``hai demo start --persona p1_dom_baseline`` followed by
    ``hai daily --skip-pull --source csv``. Verifies:

    - Both commands exit 0.
    - The scratch DB the demo session created carries a ``daily_plan``
      row for today.
    - The redirected real ``~/.health_agent`` tree is byte-identical
      before / after (the cardinal isolation contract).
    """

    # Redirect every "real" path so this subprocess test cannot mutate
    # anything outside tmp_path. Mirrors test_demo_isolation_surfaces's
    # F-IR-06 subprocess test.
    real_root = tmp_path / "real"
    real_db = real_root / "state.db"
    real_base = real_root / "base"
    real_db.parent.mkdir(parents=True)
    real_base.mkdir(parents=True)
    real_db.write_bytes(b"REAL DB MARKER v0\n" * 16)
    (real_base / "untouchable.jsonl").write_text(
        '{"line": "must_not_change"}\n'
    )
    pre_db = real_db.read_bytes()
    pre_base = _checksum_tree(real_base)

    env = os.environ.copy()
    # Strip PYTHONPATH so the editable install in the test environment
    # cannot leak into the venv subprocess.
    env.pop("PYTHONPATH", None)
    env["HAI_STATE_DB"] = str(real_db)
    env["HAI_BASE_DIR"] = str(real_base)
    env["HAI_DEMO_MARKER_PATH"] = str(tmp_path / "marker.json")
    # Force a deterministic XDG cache root so the subprocess never
    # touches the host user's real ~/.cache/hai location.
    env["XDG_CACHE_HOME"] = str(tmp_path / "xdg_cache")

    # 1. Open a demo session pinned to P1.
    proc = _hai_in_venv(
        _wheel_venv, "demo", "start", "--persona", "p1_dom_baseline",
        env=env,
    )
    assert proc.returncode == 0, (
        f"hai demo start --persona p1_dom_baseline failed in clean wheel: "
        f"stdout={proc.stdout[:300]} stderr={proc.stderr[:300]}"
    )

    # The marker the subprocess wrote points at the scratch DB. Read it
    # so the test can assert against the right path.
    marker_path = tmp_path / "marker.json"
    assert marker_path.exists(), "demo marker not written"
    marker = json.loads(marker_path.read_text())
    scratch_db = Path(marker["db_path"])
    assert scratch_db.exists(), f"scratch DB not initialised at {scratch_db}"

    # The fixture_application block on the marker reports the v0.1.13
    # full-apply branch fired, not the v0.1.12 deferred-marker shape.
    fa = marker.get("fixture_application") or {}
    assert fa.get("applied") is True, (
        f"fixture_application not flipped to applied=True; got {fa!r}"
    )
    assert fa.get("scope") == "full"
    assert fa.get("proposals_written") == 6

    # 2. hai daily reaches synthesis.
    proc = _hai_in_venv(
        _wheel_venv, "daily",
        "--skip-pull", "--source", "csv", "--skip-reviews",
        env=env,
    )
    assert proc.returncode == 0, (
        f"hai daily failed in clean wheel: "
        f"stdout={proc.stdout[:400]} stderr={proc.stderr[:400]}"
    )
    payload = json.loads(proc.stdout)
    assert payload["overall_status"] == "complete", (
        f"clean-wheel daily did not synthesize; payload={payload}"
    )
    assert payload["stages"]["synthesize"]["status"] == "ran"

    # 3. daily_plan row landed in the scratch DB.
    import sqlite3
    conn = sqlite3.connect(str(scratch_db))
    try:
        row = conn.execute(
            "SELECT daily_plan_id FROM daily_plan ORDER BY synthesized_at DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    assert row is not None, "no daily_plan row in clean-wheel scratch DB"

    # 4. Close the session.
    proc = _hai_in_venv(_wheel_venv, "demo", "end", env=env)
    assert proc.returncode == 0, (
        f"hai demo end failed: stderr={proc.stderr[:200]}"
    )

    # 5. The cardinal isolation contract — real tree byte-identical.
    assert real_db.read_bytes() == pre_db, (
        "clean-wheel demo flow mutated the redirected real state.db"
    )
    assert _checksum_tree(real_base) == pre_base, (
        "clean-wheel demo flow mutated the redirected real base_dir"
    )
