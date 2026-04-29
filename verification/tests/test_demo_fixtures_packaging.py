"""W-Vb fixture-packaging contract test.

Origin: v0.1.12 W-Vb (PLAN.md §2.3); reconciliation C3.

Validates the packaging surface only — not end-to-end persona-replay
(which is deferred to v0.1.13). The two assertions:

1. ``importlib.resources`` can resolve the packaged fixture path.
   This is what proves the fixture is reachable from a clean wheel
   install (the round-1/round-2/round-3 audit chain unanimously
   flagged that the prior demo flow imported from
   ``verification/dogfood``, which is repo-only).

2. The skeleton fixture has the documented schema_version + scope
   marker. Future fixtures override ``v0_1_12_scope`` to ``"full"``
   when v0.1.13 W-Vb extends the surface; the loader will then
   route through the full apply path.
"""

from __future__ import annotations

from importlib import resources

import pytest

from health_agent_infra.core.demo.fixtures import (
    DemoFixtureError,
    apply_fixture,
    load_fixture,
    slug_or_none,
)


def test_packaged_fixture_path_resolvable_via_importlib_resources() -> None:
    """The fixture lives at a packaged module path, not a repo path.

    A clean ``pip install health_agent_infra`` followed by importing
    ``health_agent_infra.demo.fixtures`` must succeed and expose
    ``p1.json`` as a readable resource. This is the load-bearing
    invariant the v0.1.11 demo broke (C3); v0.1.12 W-Vb closes it.
    """
    package = "health_agent_infra.demo.fixtures"
    p1 = resources.files(package).joinpath("p1_dom_baseline.json")
    assert p1.is_file(), (
        f"packaged fixture p1_dom_baseline.json not reachable via "
        f"importlib.resources at {package} — the wheel is missing the "
        f"demo/fixtures payload, or pyproject.toml package-data lacks "
        f"the demo/fixtures/*.json entry."
    )

    body = p1.read_text(encoding="utf-8")
    assert body.strip(), "p1_dom_baseline.json is empty"


def test_load_fixture_returns_skeleton_p1() -> None:
    """The loader returns a parsed dict with the expected v0.1.12
    skeleton-only marker."""
    fixture = load_fixture("p1_dom_baseline")
    assert isinstance(fixture, dict)
    assert fixture["schema_version"] == "demo_persona_fixture.v0"
    assert fixture["persona_slug"] == "p1_dom_baseline"
    assert fixture["v0_1_12_scope"] == "skeleton-only"
    # The deferral list is the contract the v0.1.13 W-Vb extension
    # will satisfy — keep this assertion in sync if v0.1.13 changes
    # the file's published skeleton.
    assert "v0_1_13_scope_pending" in fixture


def test_load_fixture_raises_on_missing_slug() -> None:
    """An unknown persona slug raises a clean error, not a generic
    FileNotFoundError, so the CLI can surface the right message."""
    with pytest.raises(DemoFixtureError) as excinfo:
        load_fixture("p99_does_not_exist")
    assert "p99_does_not_exist" in str(excinfo.value)


def test_load_fixture_rejects_empty_slug() -> None:
    with pytest.raises(DemoFixtureError):
        load_fixture("")


def test_apply_fixture_skeleton_returns_deferred_marker(tmp_path) -> None:
    """v0.1.12 fixture application is a no-op-with-marker; the marker
    documents the deferral to v0.1.13 so the demo flow can surface
    the partial-closure status to the user."""
    fixture = load_fixture("p1_dom_baseline")
    db_path = tmp_path / "scratch.db"
    base_dir = tmp_path / "scratch_base"

    result = apply_fixture(
        fixture, db_path=db_path, base_dir_path=base_dir,
    )
    assert result["applied"] is False
    assert result["scope"] == "skeleton-only"
    assert result["deferred_to"] == "v0.1.13"
    assert "v0.1.13" in result["message"]


def test_slug_or_none_normalises_blank_inputs() -> None:
    assert slug_or_none(None) is None
    assert slug_or_none("") is None
    assert slug_or_none("   ") is None
    assert slug_or_none("p1_dom_baseline") == "p1_dom_baseline"
    assert slug_or_none("  p1  ") == "p1"
