"""W-29 §2.A acceptance item 7: cli/handlers/ module LOC ceiling.

Every handler-group module under ``hai/src/health_agent_infra/cli/handlers/``
must stay under 2500 LOC. The ceiling matches the v0.1.13 boundary-table
CP1 contract; it gives ~1300 LOC headroom against the largest current
group (inspect at ~1200 LOC at v0.1.17 ship; recommend + intake at
~1100). Future cycles that approach the ceiling sub-split per the
v0.1.13 boundary table's "may further split" footnote (e.g.
``intake_food.py`` for nutrition + exercise; ``intake_subjective.py``
for stress + readiness + note + gaps).

This test is mechanical insurance against silent LOC accretion. If it
fails, the fix is not to bump the ceiling — it's to sub-split the
offending module.
"""

from __future__ import annotations

from pathlib import Path

import pytest


_HANDLERS_DIR = (
    Path(__file__).resolve().parents[2]
    / "src" / "health_agent_infra" / "cli" / "handlers"
)

# CP1 contract from v0.1.13 W-29-prep boundary table.
_LOC_CEILING = 2500


def _handler_modules() -> list[Path]:
    """Every ``.py`` under ``cli/handlers/`` except ``__init__.py``
    (the package marker, no handler bodies)."""

    return sorted(
        p for p in _HANDLERS_DIR.glob("*.py") if p.name != "__init__.py"
    )


def test_handler_modules_exist():
    """Sanity: at least 11 handler-group modules per W-29 boundary
    refresh §(b). If this drops, a module was renamed or deleted."""

    modules = _handler_modules()
    assert len(modules) >= 11, (
        f"expected ≥11 handler-group modules under {_HANDLERS_DIR}, "
        f"got {len(modules)}: {[m.name for m in modules]}"
    )


def test_no_handler_module_exceeds_loc_ceiling():
    """Per W-29 §2.A acceptance item 7: refuse any handler-group
    module ≥2500 LOC."""

    breaches: list[tuple[str, int]] = []
    for module in _handler_modules():
        loc = sum(1 for _ in module.read_text(encoding="utf-8").splitlines())
        if loc >= _LOC_CEILING:
            breaches.append((module.name, loc))

    if breaches:
        msg = "\n".join(f"  - {name}: {loc} LOC" for name, loc in breaches)
        pytest.fail(
            f"W-29 LOC-ceiling breach (≥{_LOC_CEILING}):\n{msg}\n"
            f"Sub-split per v0.1.13 boundary table (e.g. intake → "
            f"intake_food + intake_subjective)."
        )


def test_loc_ceiling_constant_matches_plan():
    """Pin the ceiling against drift. v0.1.13 boundary-table CP1 +
    v0.1.17 W-29 §2.A item 7 both name 2500 LOC."""

    assert _LOC_CEILING == 2500
