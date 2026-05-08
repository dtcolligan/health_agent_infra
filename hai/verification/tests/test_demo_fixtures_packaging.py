"""W-Vb fixture-packaging contract test.

Origin: v0.1.12 W-Vb skeleton (PLAN.md §2.3) + v0.1.13 W-Vb full-apply
flip (PLAN.md §2.A — packaged-fixture path stays; ``apply_fixture()``
becomes a proposal-write branch).

Validates the packaging surface only — not end-to-end persona-replay
(that lives in ``test_demo_persona_replay_end_to_end.py``). Three
assertions:

1. ``importlib.resources`` can resolve the packaged fixture path.
   This is what proves the fixture is reachable from a clean wheel
   install (the v0.1.11/v0.1.12 audit chain unanimously flagged that
   the prior demo flow imported from ``hai/verification/dogfood``, which
   is repo-only).

2. The fixture parses as a dict with the v1 schema header. Future
   fixtures use the same loader.

3. ``apply_fixture()`` round-trips a full-scope fixture into the
   scratch DB's ``proposal_log`` (six rows for the six domains).
"""

from __future__ import annotations

from datetime import date
from importlib import resources
from pathlib import Path

import pytest

from health_agent_infra.core.demo.fixtures import (
    FIXTURE_SCHEMA_VERSION,
    DemoFixtureError,
    apply_fixture,
    load_fixture,
    slug_or_none,
)
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)


def test_packaged_fixture_path_resolvable_via_importlib_resources() -> None:
    """The fixture lives at a packaged module path, not a repo path.

    A clean ``pip install health_agent_infra`` followed by importing
    ``health_agent_infra.demo.fixtures`` must succeed and expose
    ``p1_dom_baseline.json`` as a readable resource. This is the
    load-bearing invariant the v0.1.11 demo broke; v0.1.12 W-Vb closed
    it for the loader and v0.1.13 W-Vb keeps the contract while
    flipping ``apply_fixture()`` to the full-apply branch.
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


def test_load_fixture_returns_v1_p1_full_scope() -> None:
    """The loader returns a parsed dict in the v0.1.13 W-Vb v1 shape:
    ``schema_version: demo_persona_fixture.v1``, ``scope: full``, and
    a non-empty ``domain_proposals`` list with one entry per of the
    six v1 domains."""
    fixture = load_fixture("p1_dom_baseline")
    assert isinstance(fixture, dict)
    assert fixture["schema_version"] == FIXTURE_SCHEMA_VERSION
    assert fixture["persona_slug"] == "p1_dom_baseline"
    assert fixture["scope"] == "full"

    proposals = fixture["domain_proposals"]
    assert isinstance(proposals, list)
    domains = [p["domain"] for p in proposals]
    assert sorted(domains) == sorted([
        "recovery", "running", "sleep", "stress", "strength", "nutrition",
    ]), f"P1 fixture must cover all 6 v1 domains; got {domains}"


def test_load_fixture_raises_on_missing_slug() -> None:
    """An unknown persona slug raises a clean error, not a generic
    FileNotFoundError, so the CLI can surface the right message."""
    with pytest.raises(DemoFixtureError) as excinfo:
        load_fixture("p99_does_not_exist")
    assert "p99_does_not_exist" in str(excinfo.value)


def test_load_fixture_rejects_empty_slug() -> None:
    with pytest.raises(DemoFixtureError):
        load_fixture("")


def test_apply_fixture_full_writes_six_proposals(tmp_path: Path) -> None:
    """The v0.1.13 W-Vb flip: a full-scope fixture lands six rows in
    the scratch DB's ``proposal_log`` and writes one JSONL per domain
    under ``base_dir``. The result dict carries ``applied=True`` +
    ``scope='full'`` + ``proposals_written=6``.
    """
    fixture = load_fixture("p1_dom_baseline")
    db_path = tmp_path / "scratch.db"
    base_dir = tmp_path / "scratch_base"
    base_dir.mkdir()

    # apply_fixture requires an initialised scratch DB (open_session
    # initialises it; this test mirrors that contract).
    initialize_database(db_path)

    target = date(2026, 4, 30)
    result = apply_fixture(
        fixture,
        db_path=db_path,
        base_dir_path=base_dir,
        user_id="u_demo_test",
        for_date=target,
    )
    assert result["applied"] is True
    assert result["scope"] == "full"
    assert result["persona_slug"] == "p1_dom_baseline"
    assert result["deferred_to"] is None
    assert result["proposals_written"] == 6
    assert result["for_date"] == "2026-04-30"
    assert result["user_id"] == "u_demo_test"

    # DB landed all six leaves.
    conn = open_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT domain, action, confidence FROM proposal_log "
            "WHERE for_date = ? AND user_id = ? "
            "  AND superseded_by_proposal_id IS NULL",
            ("2026-04-30", "u_demo_test"),
        ).fetchall()
    finally:
        conn.close()
    assert sorted(r["domain"] for r in rows) == sorted([
        "recovery", "running", "sleep", "stress", "strength", "nutrition",
    ])

    # JSONL audit per domain.
    jsonl_files = sorted(p.name for p in base_dir.iterdir() if p.is_file())
    assert "recovery_proposals.jsonl" in jsonl_files
    assert "nutrition_proposals.jsonl" in jsonl_files


def test_apply_fixture_refuses_when_db_missing(tmp_path: Path) -> None:
    """If the scratch DB has not been initialised, apply_fixture refuses
    rather than silently writing JSONL-only state. open_session always
    initialises the scratch DB before calling apply_fixture, so this
    is a defensive guard for callers that bypass the session helper."""
    fixture = load_fixture("p1_dom_baseline")
    db_path = tmp_path / "absent.db"
    base_dir = tmp_path / "scratch_base"
    base_dir.mkdir()

    with pytest.raises(DemoFixtureError) as excinfo:
        apply_fixture(
            fixture,
            db_path=db_path,
            base_dir_path=base_dir,
        )
    assert "scratch DB" in str(excinfo.value)


def test_slug_or_none_normalises_blank_inputs() -> None:
    assert slug_or_none(None) is None
    assert slug_or_none("") is None
    assert slug_or_none("   ") is None
    assert slug_or_none("p1_dom_baseline") == "p1_dom_baseline"
    assert slug_or_none("  p1  ") == "p1"
