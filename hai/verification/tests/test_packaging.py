"""Packaging verification (Phase 7 step 3).

Pins the invariants needed for a clean ``pip install health_agent_infra`` —
the things that silently rot if ``pyproject.toml`` drifts from the
runtime without anyone noticing until publish:

- The ``hai`` console script entry point is declared and resolves to
  ``health_agent_infra.cli:main``.
- The version reported by ``hai --version`` / ``health_agent_infra
  .__version__`` matches the distribution metadata when installed,
  and falls back to the documented ``0.0.0+unregistered`` sentinel
  when the test suite runs from a bare source checkout.
- The non-Python resources the runtime loads at runtime (SQL
  migrations, SKILL.md files, strength taxonomy seed, committed
  Garmin CSV) are actually packaged — i.e. ``importlib.resources``
  can resolve them.

These tests intentionally do not validate PyPI presence, wheel
signatures, or any network-facing concern — those belong to Phase 7
step 4 (actual release).
"""

from __future__ import annotations

import json
import tomllib
from importlib import metadata, resources
from pathlib import Path

import pytest

from health_agent_infra import __version__ as _PACKAGE_VERSION

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HAI_ROOT = _REPO_ROOT / "hai"
_PYPROJECT = _REPO_ROOT / "pyproject.toml"
_UNREGISTERED_SENTINEL = "0.0.0+unregistered"


def _pyproject_data() -> dict:
    with _PYPROJECT.open("rb") as fh:
        return tomllib.load(fh)


def _distribution_installed() -> bool:
    try:
        metadata.distribution("health_agent_infra")
    except metadata.PackageNotFoundError:
        return False
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def test_hai_console_script_entry_point_registered():
    """``pip install`` must create a ``hai`` binary pointing at ``cli:main``.

    Skipped when the package is not pip-installed (source-only test runs
    have no distribution metadata to inspect).
    """
    if not _distribution_installed():
        pytest.skip("health_agent_infra not pip-installed; no entry_points metadata")
    eps = metadata.entry_points(group="console_scripts")
    hai_eps = [ep for ep in eps if ep.name == "hai"]
    assert len(hai_eps) == 1, f"expected exactly one 'hai' console script, got {hai_eps}"
    assert hai_eps[0].value == "health_agent_infra.cli:main"


def test_pyproject_declares_hai_console_script():
    """pyproject.toml is checked-in; the declaration must stay authoritative."""
    data = _pyproject_data()
    scripts = data.get("project", {}).get("scripts", {})
    assert scripts.get("hai") == "health_agent_infra.cli:main"


# ---------------------------------------------------------------------------
# Version consistency
# ---------------------------------------------------------------------------


def test_pyproject_version_matches_package_version_when_installed():
    """Installed distribution must agree with pyproject on the version
    string. This is the guard that keeps ``hai --version`` honest after
    a bump.
    """
    declared = _pyproject_data()["project"]["version"]
    if not _distribution_installed():
        # Uninstalled source runs advertise the sentinel — verify the
        # fallback path rather than asserting equality against pyproject.
        assert _PACKAGE_VERSION == _UNREGISTERED_SENTINEL
        return
    assert metadata.version("health_agent_infra") == declared
    assert _PACKAGE_VERSION == declared


def test_package_version_is_non_empty_and_well_formed():
    assert _PACKAGE_VERSION
    # Either a PEP 440 release or the documented fallback sentinel.
    assert _PACKAGE_VERSION == _UNREGISTERED_SENTINEL or _PACKAGE_VERSION[0].isdigit()


# ---------------------------------------------------------------------------
# Packaged resources — things the runtime loads via importlib.resources
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "relpath",
    [
        "core/state/migrations/001_initial.sql",
        "core/state/migrations/006_nutrition_macros_only.sql",
        "skills/daily-plan-synthesis/SKILL.md",
        "skills/recovery-readiness/SKILL.md",
        "skills/nutrition-alignment/SKILL.md",
        "domains/strength/taxonomy_seed.csv",
        "data/garmin/export/daily_summary_export.csv",
        "evals/scenarios/recovery/rec_001_rested_baseline.json",
        "evals/scenarios/synthesis/syn_001_no_firings_baseline.json",
        "evals/rubrics/domain.md",
        "evals/rubrics/synthesis.md",
    ],
)
def test_packaged_resource_is_resolvable(relpath: str):
    """Runtime loads these files via ``importlib.resources.files``.
    If the package-data globs drift out of pyproject, the install still
    succeeds but these reads fail at runtime. Guard with a cheap test.
    """
    root = resources.files("health_agent_infra")
    target = root.joinpath(*relpath.split("/"))
    assert target.is_file(), f"packaged resource missing from distribution: {relpath}"


def test_pyproject_package_data_globs_cover_all_non_python_files():
    """Every committed non-Python file under ``hai/src/health_agent_infra/``
    must match at least one ``[tool.setuptools.package-data]`` glob —
    otherwise setuptools silently drops it from the wheel.
    """
    pkg_root = _HAI_ROOT / "src" / "health_agent_infra"
    declared = _pyproject_data()["tool"]["setuptools"]["package-data"]["health_agent_infra"]

    # setuptools package-data globs are relative to the package root and
    # use fnmatch semantics. Convert each to a pathlib rglob shape so we
    # can test coverage.
    def _covered(relpath: Path) -> bool:
        for pattern in declared:
            # setuptools expands ``**`` recursively — Path.match treats
            # ``**`` as a single component, so fall back to glob().
            for match in pkg_root.glob(pattern):
                if match.resolve() == (pkg_root / relpath).resolve():
                    return True
        return False

    missing: list[str] = []
    for candidate in pkg_root.rglob("*"):
        if not candidate.is_file():
            continue
        if candidate.suffix in {".py", ".pyc"}:
            continue
        if "__pycache__" in candidate.parts:
            continue
        rel = candidate.relative_to(pkg_root)
        if not _covered(rel):
            missing.append(str(rel))

    assert not missing, (
        "Non-Python files committed under hai/src/health_agent_infra/ but "
        "not matched by any [tool.setuptools.package-data] glob — these "
        f"will be silently dropped from the wheel:\n  " + "\n  ".join(missing)
    )


# ---------------------------------------------------------------------------
# Wheel-installed surface — `hai eval run` works outside the repo root
# ---------------------------------------------------------------------------
#
# The v0.1.0 release registered `hai eval` conditionally by walking for a
# repo-local `hai/verification/evals/` tree. In a wheel install outside a checkout,
# the subcommand was silently missing — a concrete shipped-truth gap
# between docs and the installed package. The framework now lives inside
# the wheel at `health_agent_infra.evals`, and these tests lock that
# behaviour so it cannot regress.
#
# The `cli.py` surface and argparse registration are identical in source
# and wheel installs, so an in-process invocation from a working
# directory outside the repo is a faithful stand-in for the wheel-only
# surface. Running an actual `subprocess` against a throw-away venv
# would exercise the same path at much higher cost.


def _run_hai_cli(argv, *, cwd=None):
    """In-process `hai` invocation with a scoped sys.argv + cwd.

    Matches the shell entry point at `health_agent_infra.cli:main` so the
    registered subparsers are the same ones a wheel install exposes.
    Captures stdout via capsys-compatible redirection by the caller;
    this helper only changes cwd + argv.
    """

    import os
    from health_agent_infra.cli import main as cli_main

    prev_cwd = os.getcwd()
    if cwd is not None:
        os.chdir(cwd)
    try:
        return cli_main(argv)
    finally:
        os.chdir(prev_cwd)


def test_hai_eval_subcommand_is_registered_unconditionally(capsys):
    """`hai eval --help` must succeed with no repo-relative lookup path.

    Acceptance criterion from post_v0_1_roadmap Phase A: installed
    package behavior and public docs agree on `hai eval`. If this test
    fails, someone reverted `_register_eval_subparser` to a conditional
    lookup and the CLI-vs-docs gap is back.
    """
    with pytest.raises(SystemExit) as excinfo:
        _run_hai_cli(["eval", "--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert "run" in out  # `hai eval run` subcommand must be listed


def test_hai_eval_run_works_from_outside_repo_root(tmp_path, capsys):
    """`hai eval run --domain recovery` must succeed when cwd is not the
    repo root. This is the direct repro for the v0.1.0 shipped-truth gap
    that drove Phase A of the post-release roadmap."""
    rc = _run_hai_cli(
        ["eval", "run", "--domain", "recovery", "--json"],
        cwd=tmp_path,
    )
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["kind"] == "domain"
    assert payload["domain"] == "recovery"
    assert payload["total"] >= 3
    assert payload["failed"] == 0


def test_hai_eval_run_synthesis_works_from_outside_repo_root(tmp_path, capsys):
    """Same guard as above, for the synthesis-kind path."""
    rc = _run_hai_cli(
        ["eval", "run", "--synthesis", "--json"],
        cwd=tmp_path,
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kind"] == "synthesis"
    assert payload["total"] >= 10
    assert payload["failed"] == 0
