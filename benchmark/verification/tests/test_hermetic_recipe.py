"""WP-HRN-002: benchmark-mode environment recipe."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest


def _run_hai(recipe, *argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "health_agent_infra.cli", *argv],
        env=recipe.env,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_hermetic_recipe_allows_read_only_capabilities(
    hermetic_env_factory,
) -> None:
    recipe = hermetic_env_factory()

    result = _run_hai(recipe, "capabilities", "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema_version"].startswith("agent_cli_contract.")
    assert not (recipe.home / ".health_agent").exists()
    assert not (recipe.home / ".local" / "share" / "health_agent_infra").exists()


def test_hermetic_recipe_refuses_live_network_pull(
    hermetic_env_factory,
) -> None:
    recipe = hermetic_env_factory()

    result = _run_hai(
        recipe,
        "pull",
        "--source",
        "intervals_icu",
        "--as-of",
        "2026-04-23",
    )

    assert result.returncode != 0
    assert "hermetic mode refuses network access" in result.stderr
    assert not recipe.state_db.exists()


def test_benchmark_recipe_is_all_or_nothing(hermetic_env_factory) -> None:
    with pytest.raises(AssertionError) as excinfo:
        hermetic_env_factory(include_hermetic=False)

    assert "HAI_HERMETIC" in str(excinfo.value)
