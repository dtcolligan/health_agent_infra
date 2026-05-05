"""v0.1.17 IR-R1 F-IR-05 — wheel-content smoke for the W-29 cli split.

Round-1 IR caught: the v0.1.17 wheel built from the maintainer's tree
shipped ``health_agent_infra/cli.py`` (the pre-W-29 monolith, picked
up from a stale ``build/lib/`` cache) alongside the new
``health_agent_infra/cli/__init__.py`` package. Python's import
resolver picks the package over the module, so the artifact still
imported correctly — but it shipped 385 KB of dead source. This
smoke refuses any wheel under ``dist/`` that contains a top-level
``health_agent_infra/cli.py`` (the W-29 split's anti-pattern).

Skipped when ``dist/`` is empty or absent: the suite must stay
runnable without a pre-build step. Pre-publish, the maintainer should
``rm -rf build/ dist/ src/health_agent_infra.egg-info`` before
``uvx --from build python -m build`` to avoid setuptools picking up
stale caches.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
DIST_DIR = REPO_ROOT / "dist"


def _list_wheels() -> list[Path]:
    if not DIST_DIR.exists():
        return []
    return sorted(DIST_DIR.glob("health_agent_infra-*.whl"))


@pytest.mark.parametrize("wheel_path", _list_wheels(),
                         ids=lambda p: p.name)
def test_wheel_does_not_ship_pre_split_cli_module(wheel_path: Path) -> None:
    """No ``health_agent_infra/cli.py`` at the top of the package tree.

    Acceptable: ``health_agent_infra/cli/__init__.py`` (the W-29 split
    package). Forbidden: ``health_agent_infra/cli.py`` (the pre-split
    monolith re-shipped from a stale build cache).
    """

    with zipfile.ZipFile(wheel_path) as zf:
        names = zf.namelist()

    pkg_root_cli_module = "health_agent_infra/cli.py"
    pkg_root_cli_init = "health_agent_infra/cli/__init__.py"

    # Pre-W-29 wheels (≤v0.1.15.1) have cli.py and no cli/ package —
    # legitimate older artifacts. Skip them; the smoke is W-29-or-later.
    if pkg_root_cli_init not in names:
        pytest.skip(
            f"{wheel_path.name} is pre-W-29 (no cli/__init__.py); "
            f"smoke only applies to W-29-split wheels (v0.1.17+)."
        )

    assert pkg_root_cli_module not in names, (
        f"{wheel_path.name}: ships both health_agent_infra/cli.py AND "
        f"the cli/ package. cli.py is the pre-W-29 monolith picked up "
        f"from a stale build/lib cache. Pre-publish: "
        f"`rm -rf build/ dist/ src/health_agent_infra.egg-info` "
        f"and rebuild with "
        f"`uvx --from build python -m build --wheel --sdist`."
    )


def test_dist_directory_is_optional() -> None:
    """The smoke is dist-driven: no dist/ → no parametrize → no
    fixtures → silent pass. Document the contract explicitly so future
    maintainers don't add a defensive `assert dist exists` here."""

    # No assertion; documenting contract via docstring + presence of test.
    pass
