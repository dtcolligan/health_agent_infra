"""W-FCC contract: ``hai today``'s capabilities row exposes the
``strength_status`` enum surface, and the manifest enumeration matches
the classifier source-of-truth.

Origin: v0.1.12 W-FCC (PLAN.md §2.9); F-C-05 deferred from v0.1.11.

The classifier emits ``strength_status`` as one of a fixed set of
strings. The set was previously documented only in a docstring
inside ``domains/strength/classify.py``; this test pins it as part
of the agent-CLI contract.
"""

from __future__ import annotations

import json
import subprocess
import sys

from health_agent_infra.domains.strength.classify import STRENGTH_STATUS_VALUES


def _capabilities_manifest() -> dict:
    """Render ``hai capabilities --json`` and parse it.

    Uses subprocess to mirror real agent invocation (where the manifest
    is loaded as bytes, not by importing the walker directly). Catches
    the case where the parser-build sequence doesn't actually attach
    the enum surface."""

    result = subprocess.run(
        [sys.executable, "-m", "health_agent_infra.cli", "capabilities", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_hai_today_capabilities_row_exposes_strength_status_enum() -> None:
    """The ``hai today`` capabilities row must include
    ``output_schema.OK.enum_surface.strength_status``, and the listed
    values must match the classifier's authoritative tuple."""

    manifest = _capabilities_manifest()
    rows = [r for r in manifest["commands"] if r["command"] == "hai today"]
    assert len(rows) == 1, (
        f"expected exactly one 'hai today' capabilities row, got "
        f"{len(rows)}"
    )

    row = rows[0]
    output_schema = row.get("output_schema")
    assert output_schema is not None, (
        "hai today capabilities row missing 'output_schema' — W-FCC "
        "regressed?"
    )

    ok_schema = output_schema.get("OK")
    assert ok_schema is not None, "OK exit-code schema missing"

    enum_surface = ok_schema.get("enum_surface")
    assert enum_surface is not None, (
        "hai today output_schema.OK.enum_surface missing — W-FCC "
        "regressed?"
    )

    surface_values = enum_surface.get("strength_status")
    assert surface_values is not None, (
        "enum_surface.strength_status missing"
    )
    assert tuple(surface_values) == STRENGTH_STATUS_VALUES, (
        f"manifest enum surface drifted from classifier source of "
        f"truth: manifest={surface_values!r} vs "
        f"classifier={STRENGTH_STATUS_VALUES!r}. "
        f"Update both sites together — `STRENGTH_STATUS_VALUES` in "
        f"domains/strength/classify.py is the load-bearing definition."
    )


def test_strength_status_values_constant_is_exhaustive() -> None:
    """Sanity: every value the classifier *can* assign to
    ``strength_status`` appears in ``STRENGTH_STATUS_VALUES``. This
    catches a future classifier change that adds a new state without
    updating the constant — the manifest contract test would still
    pass (manifest matches constant), but the constant would no longer
    reflect reality."""

    # The classifier's possible outputs are the literal strings it
    # returns from ``_strength_status``. We assert the constant covers
    # the v0.1.12 set explicitly.
    expected = {
        "progressing",
        "maintaining",
        "undertrained",
        "overreaching",
        "unknown",
    }
    assert set(STRENGTH_STATUS_VALUES) == expected, (
        f"STRENGTH_STATUS_VALUES drifted from documented enum: "
        f"got {set(STRENGTH_STATUS_VALUES)}, expected {expected}. "
        f"If the classifier added a value, update both this test and "
        f"`STRENGTH_STATUS_VALUES` in domains/strength/classify.py."
    )
