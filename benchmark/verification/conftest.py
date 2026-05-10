"""Benchmark verification fixtures."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pytest


@dataclass(frozen=True)
class HermeticRecipe:
    env: dict[str, str]
    home: Path
    state_db: Path
    base_dir: Path


def _assert_benchmark_hermetic_env(env: dict[str, str]) -> None:
    missing = [
        name
        for name in ("HAI_HERMETIC", "HAI_STATE_DB", "HAI_BASE_DIR", "HOME")
        if not env.get(name)
    ]
    if missing:
        raise AssertionError(
            "benchmark hermetic recipe missing: " + ", ".join(missing)
        )
    if env["HAI_HERMETIC"] != "1":
        raise AssertionError("benchmark hermetic recipe requires HAI_HERMETIC=1")


@pytest.fixture
def hermetic_env_factory(tmp_path: Path) -> Callable[..., HermeticRecipe]:
    def factory(
        *,
        include_hermetic: bool = True,
        validate: bool = True,
    ) -> HermeticRecipe:
        fixture_root = tmp_path / "fixture"
        home = tmp_path / "home"
        state_db = fixture_root / "state.db"
        base_dir = fixture_root / "base"
        env = os.environ.copy()
        env.update({
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(fixture_root / "xdg_config"),
            "HAI_STATE_DB": str(state_db),
            "HAI_BASE_DIR": str(base_dir),
        })
        if include_hermetic:
            env["HAI_HERMETIC"] = "1"
        else:
            env.pop("HAI_HERMETIC", None)
        if validate:
            _assert_benchmark_hermetic_env(env)
        return HermeticRecipe(
            env=env,
            home=home,
            state_db=state_db,
            base_dir=base_dir,
        )

    return factory
