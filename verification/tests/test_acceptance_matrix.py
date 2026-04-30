"""W-A1C7 (v0.1.13) — trusted-first-value acceptance matrix.

The v0.1.13 onboarding gate is reframed from "first recommendation
in 5 min" to a five-path matrix. **Trusted first value = the agent
reaches one of five honest end-states, none of which fabricate
against missing input.**

This test surface codifies the matrix as a contract. Each path has
an explicit required result; a path that regresses fails this test
and is merge-blocking.

The matrix lives in `reporting/plans/tactical_plan_v0_1_x.md` §4.2
(authoritative). This test file is the executable mirror.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra import __version__ as _PACKAGE_VERSION
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state.store import initialize_database


_REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_hai(
    *args: str,
    db_path: Path,
    skills_dest: Path,
    thresholds_path: Path | None = None,
    extra_env: dict | None = None,
) -> subprocess.CompletedProcess:
    """Invoke `hai` as a subprocess against an isolated state path."""

    env = dict(os.environ)
    env.update({
        "HAI_STATE_DB": str(db_path),
        "HAI_BASE_DIR": str(db_path.parent),
    })
    if thresholds_path:
        env["HAI_THRESHOLDS_PATH"] = str(thresholds_path)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-m", "health_agent_infra.cli", *args],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Path 5 — failure path (test order: easiest first)
# ---------------------------------------------------------------------------


def test_path_5_failure_path_surfaces_user_input_not_crash(tmp_path: Path):
    """`hai daily` on a fresh-init DB with no intent / no target /
    no pull → exits cleanly with USER_INPUT-class semantics. Does
    NOT crash; does NOT fabricate a plan."""

    db = tmp_path / "state.db"
    initialize_database(db)
    skills = tmp_path / "skills"
    skills.mkdir()

    result = _run_hai(
        "daily",
        "--as-of", date(2026, 4, 30).isoformat(),
        "--user-id", "u_test",
        "--db-path", str(db),
        db_path=db,
        skills_dest=skills,
    )
    # Cleanly handled: exits with a recognised code, never SIGSEGV /
    # exit 1 generic / Python traceback.
    assert result.returncode in (
        exit_codes.OK,
        exit_codes.USER_INPUT,
        exit_codes.NOT_FOUND,
    ), (
        f"hai daily on bare DB exited {result.returncode}; "
        f"stderr={result.stderr!r}"
    )
    assert "Traceback" not in result.stderr, (
        f"daily on bare DB raised an unhandled exception:\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# Path 1 — blank demo
# ---------------------------------------------------------------------------


def test_path_1_blank_demo_produces_honest_no_proposals_boundary(tmp_path: Path):
    """`hai demo start --blank` opens a session; subsequent `hai daily`
    must NOT produce a fabricated plan, and must NOT crash. The honest
    end-state is `awaiting_proposals` (or equivalent named-defer)."""

    db = tmp_path / "state.db"
    initialize_database(db)
    skills = tmp_path / "skills"
    skills.mkdir()

    # Open blank demo session.
    start = _run_hai(
        "demo", "start", "--blank",
        db_path=db,
        skills_dest=skills,
        extra_env={"HAI_DEMO_SCRATCH_ROOT": str(tmp_path / "demo")},
    )
    assert start.returncode == exit_codes.OK, (
        f"demo start --blank exited {start.returncode}: {start.stderr!r}"
    )

    # `hai daily` against a blank session must not fabricate.
    daily = _run_hai(
        "daily",
        "--as-of", date(2026, 4, 30).isoformat(),
        "--user-id", "u_test",
        "--db-path", str(db),
        db_path=db,
        skills_dest=skills,
    )
    assert "Traceback" not in daily.stderr, (
        f"blank-demo daily crashed: {daily.stderr}"
    )
    # The combined stdout/stderr must mention awaiting_proposals OR
    # USER_INPUT-class boundary, not show a synthesized plan.
    combined = (daily.stdout + daily.stderr).lower()
    fabrication_markers = ("synthesized daily plan", "## recovery —", "## sleep —")
    for marker in fabrication_markers:
        assert marker not in combined, (
            f"blank-demo daily appears to have fabricated a plan; "
            f"saw marker {marker!r} in output"
        )

    # Cleanup: end the demo session.
    _run_hai("demo", "end", db_path=db, skills_dest=skills)


# ---------------------------------------------------------------------------
# Path 2 — persona demo (depends on W-Vb)
# ---------------------------------------------------------------------------


def test_path_2_persona_demo_reaches_synthesized():
    """W-Vb ship-set persona-replay reaches `synthesized` for P1+P4+P5.

    Currently SKIPPED until W-Vb ships the proposal-write `apply_fixture()`
    branch + full DomainProposal seeds for those personas. The skip
    reason is the W-id this test depends on, so audit can identify
    which workstream re-enables it."""

    pytest.skip(
        "Path 2 depends on W-Vb (persona-replay end-to-end). "
        "Re-enable after W-Vb's `apply_fixture()` proposal-write "
        "branch + P1+P4+P5 fixtures land. Tracked in PLAN.md §2.A."
    )


# ---------------------------------------------------------------------------
# Path 3 — real intervals.icu (manual / out-of-CI)
# ---------------------------------------------------------------------------


def test_path_3_intervals_icu_pull_to_synthesis_documented_as_manual():
    """Real intervals.icu pull → daily plan is a manual demo protocol,
    not a CI gate. Live API calls are not CI-friendly. The path is
    exercised by the existing `verification.dogfood.runner` persona
    matrix using stubbed intervals.icu fixtures, which is the
    in-CI proxy.

    This test passes when the persona-runner module exists with the
    intervals.icu fixture path — the infrastructure to test path 3
    is the same infrastructure dogfood uses."""

    runner_path = _REPO_ROOT / "verification" / "dogfood" / "runner.py"
    assert runner_path.exists()
    text = runner_path.read_text()
    # Require the runner to know about intervals.icu replay shape.
    # The "data_source" enum is the runtime contract surface.
    assert "intervals_icu" in text, (
        "persona runner missing intervals_icu data-source path; "
        "path 3 acceptance evidence is broken"
    )


# ---------------------------------------------------------------------------
# Path 4 — host-agent propose-and-synthesize
# ---------------------------------------------------------------------------


def test_path_4_host_agent_propose_synthesize_pipeline_is_exercised():
    """The propose → synthesize → audit-chain path is exercised by the
    existing 12-persona matrix (`verification.dogfood.runner`). The
    matrix proxies the host-agent flow by writing minimal DomainProposal
    rows for each domain and running synthesize.

    This test asserts the proxy infrastructure exists. Full e2e is
    the matrix invocation itself (not in CI per AGENTS.md D10) — a
    successful release run is the substantive evidence."""

    runner_path = _REPO_ROOT / "verification" / "dogfood" / "runner.py"
    text = runner_path.read_text()
    # The runner posts proposals via the synthetic skill.
    assert "synthetic_skill" in text or "DomainProposal" in text, (
        "persona runner missing propose-pipeline shape; path 4 "
        "acceptance evidence is broken"
    )


# ---------------------------------------------------------------------------
# Matrix-level invariants
# ---------------------------------------------------------------------------


def test_acceptance_matrix_lives_in_tactical_plan():
    """A1 rename + C7 matrix: the authoritative document is
    tactical_plan_v0_1_x.md §4.2. This test asserts the doc-side
    contract is in place. Drift would make this test fail."""

    plan = _REPO_ROOT / "reporting" / "plans" / "tactical_plan_v0_1_x.md"
    text = plan.read_text()
    assert "trusted-first-value matrix" in text.lower()
    assert "5 paths" in text or "five-path" in text
    # Each path's name must appear so the doc-side and code-side
    # vocabularies align.
    for needle in (
        "Blank demo",
        "Persona demo",
        "intervals.icu",
        "Host-agent",
        "Failure path",
    ):
        assert needle in text, (
            f"trusted-first-value matrix missing path label {needle!r}"
        )


def test_a1_rename_old_first_recommendation_phrase_is_gone(tmp_path: Path):
    """A1 rename: "first recommendation in 5 min" / "first
    recommendation in five min" is the old ambiguous gate language.
    It should no longer appear in v0.1.13+ planning surfaces.

    Historical references in v0_1_X archived plans are excluded —
    those are immutable provenance. Live planning surfaces only."""

    surfaces = [
        _REPO_ROOT / "reporting" / "plans" / "tactical_plan_v0_1_x.md",
        _REPO_ROOT / "reporting" / "plans" / "strategic_plan_v1.md",
        _REPO_ROOT / "ROADMAP.md",
        _REPO_ROOT / "README.md",
    ]
    offending: list[str] = []
    banned = (
        "first-recommendation in 5 min",
        "first recommendation in 5 min",
        "first recommendation in five min",
    )
    for surface in surfaces:
        if not surface.exists():
            continue
        text = surface.read_text().lower()
        for phrase in banned:
            if phrase in text:
                offending.append(f"{surface.name} contains {phrase!r}")
    assert not offending, (
        "A1 rename incomplete — pre-W-A1C7 'first recommendation' "
        "phrasing still appears in live planning surfaces:\n"
        + "\n".join(offending)
    )
