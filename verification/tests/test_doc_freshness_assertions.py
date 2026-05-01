"""W-AC freshness assertions.

Catches the most common form of stale public-facing doc drift: a doc
naming an older version as "current" or "shipped" past the actual
package version. v0.1.12 reconciliation C1 caught
``ROADMAP.md`` saying "v0.1.8 current" three releases late;
this test prevents that recurring.

Origin: v0.1.12 W-AC (PLAN.md §2.1).
"""

from __future__ import annotations

import re
from importlib import metadata
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _package_version_tuple() -> tuple[int, ...]:
    """Return the live package version as a comparable tuple.

    ``health-agent-infra==0.1.12`` -> ``(0, 1, 12)``.
    """
    raw = metadata.version("health-agent-infra")
    parts = raw.split(".")
    return tuple(int(p) for p in parts if p.isdigit())


def _parse_version(token: str) -> tuple[int, ...] | None:
    """Parse a ``v0.1.11`` token into ``(0, 1, 11)``; None if malformed."""
    cleaned = token.lstrip("vV")
    parts = cleaned.split(".")
    if not parts or not all(p.isdigit() for p in parts):
        return None
    return tuple(int(p) for p in parts)


# Each entry is (path-relative-to-repo, regex describing a "version-as-current"
# claim). The first capturing group MUST be the version token (e.g. "0.1.11").
# A doc may name an older version as historical context ("v0.1.9 added X") —
# those phrasings are out of scope. We only flag patterns that *assert*
# currency: "current", "shipped (current)", "in flight (current)", etc.
_FRESHNESS_PATTERNS: tuple[tuple[str, str], ...] = (
    # ROADMAP.md historically said "v0.1.8 current."
    ("ROADMAP.md", r"\*\*v(\d+\.\d+\.\d+)\s+current\.\*\*"),
)


@pytest.mark.parametrize("rel_path,pattern", _FRESHNESS_PATTERNS)
def test_doc_does_not_name_older_version_as_current(
    rel_path: str, pattern: str
) -> None:
    """No public-facing doc may name a version older than the package
    version as "current".

    A drift here is the trust hazard a second user hits first — the doc
    says the project is at v0.1.X when it has shipped v0.1.X+N.
    """
    path = REPO_ROOT / rel_path
    if not path.exists():
        pytest.skip(f"{rel_path} not present in repo; skipping freshness check")

    body = path.read_text(encoding="utf-8")
    matches = re.findall(pattern, body)

    if not matches:
        # Doc has no "current" claim at all — that's fine; nothing to assert.
        return

    pkg_version = _package_version_tuple()
    stale: list[str] = []
    for token in matches:
        parsed = _parse_version(token)
        if parsed is None:
            continue
        if parsed < pkg_version:
            stale.append(f"v{token}")

    assert not stale, (
        f"{rel_path} names older version(s) as current: {stale}. "
        f"Package version is v{'.'.join(str(p) for p in pkg_version)}. "
        f"Update {rel_path} to reflect the shipped state."
    )


# ---------------------------------------------------------------------------
# v0.1.14 W-FRESH-EXT — W-id reference freshness across summary surfaces
# ---------------------------------------------------------------------------

# v0.1.14 W-FRESH-EXT extension: scan summary surfaces for v0.1.14 W-id
# references and confirm they match the active cycle's PLAN.md catalogue.
# This catches the v0.1.13 → v0.1.14 reconciliation pattern where a CP
# referenced a W-id that didn't (yet) exist in PLAN.md.
#
# The check is deliberately scoped to the **current cycle's PLAN** and a
# small set of summary surfaces (ROADMAP, tactical_plan, strategic_plan).
# Historical references in audit-chain artifacts (codex_*_response*.md,
# RELEASE_PROOF.md, REPORT.md) are immutable history and exempt.

_CURRENT_CYCLE_PLAN = REPO_ROOT / "reporting/plans/v0_1_14/PLAN.md"

_FRESHNESS_W_ID_SURFACES: tuple[str, ...] = (
    "ROADMAP.md",
    "reporting/plans/tactical_plan_v0_1_x.md",
    "reporting/plans/strategic_plan_v1.md",
)

# Pattern matches the W-id catalogue rows in PLAN.md §1.2. Capture-group 1
# is the W-id token (e.g., 'W-PROV-1', 'W-EXPLAIN-UX', 'W-2U-GATE').
_PLAN_W_ID_ROW_RE = re.compile(
    r"^\|\s*§2\.[A-Z]+\s*\|\s*~?~?\*?\*?(W-[A-Z0-9-]+)",
    re.MULTILINE,
)


def _current_cycle_w_ids() -> set[str]:
    """Parse v0.1.14 PLAN.md §1.2 catalogue rows and return the W-id set."""

    if not _CURRENT_CYCLE_PLAN.exists():
        return set()
    body = _CURRENT_CYCLE_PLAN.read_text(encoding="utf-8")
    return set(_PLAN_W_ID_ROW_RE.findall(body))


def test_current_cycle_plan_has_at_least_one_w_id():
    """Sanity: parser actually finds W-ids in the current cycle's PLAN.md."""

    ids = _current_cycle_w_ids()
    # 13 W-ids post-W-2U-GATE-defer (was 14 at D14 close); allow ≥10 to
    # tolerate honest partial closures during the cycle.
    assert len(ids) >= 10, (
        f"v0.1.14 PLAN.md §1.2 catalogue parsed {len(ids)} W-ids: "
        f"{sorted(ids)}. The W-FRESH-EXT contract requires at least 10."
    )


def test_v0_1_14_w_id_in_summary_surface_implies_in_plan_catalogue():
    """A W-id named in a summary surface (ROADMAP / tactical / strategic)
    should match the current cycle's PLAN.md catalogue if it's named as
    a v0.1.14 surface item.

    This is a soft check — we don't fail on every named W-id (historical
    references are legitimate). We DO fail when a summary surface
    explicitly tags a W-id as v0.1.14 scope but the W-id doesn't appear
    in v0.1.14 PLAN.md §1.2.
    """

    plan_w_ids = _current_cycle_w_ids()
    if not plan_w_ids:
        pytest.skip("PLAN.md §1.2 not parseable; skipping cross-check")

    for rel_path in _FRESHNESS_W_ID_SURFACES:
        path = REPO_ROOT / rel_path
        if not path.exists():
            continue
        body = path.read_text(encoding="utf-8")
        # Find lines that explicitly tag a W-id as v0.1.14 scope.
        # Pattern: a line containing both "v0.1.14" and a W-id token.
        for line in body.splitlines():
            if "v0.1.14" not in line:
                continue
            # Extract every W-id-shaped token on this line.
            tokens = re.findall(r"\bW-[A-Z0-9-]+\b", line)
            for tok in tokens:
                # Honest-deferral / inherited tokens are immune — they
                # legitimately reference a W-id outside the current
                # PLAN catalogue (e.g., "W-2U-GATE deferred to v0.1.15").
                if any(
                    kw in line.lower() for kw in (
                        "deferred", "defer to", "inherited",
                        "carry-forward", "carry forward", "v0.1.15",
                        "v0.1.13", "v0.2.0", "post-",
                        "pull-forward", "pull forward",
                        "pulled forward", "pulled-forward",
                        "shipped",
                    )
                ):
                    continue
                # Otherwise, the token must be in the current PLAN.
                if tok not in plan_w_ids:
                    pytest.fail(
                        f"{rel_path}: line names {tok!r} in v0.1.14 "
                        f"context but PLAN.md §1.2 catalogue does not "
                        f"contain it. Either update PLAN.md to include "
                        f"{tok}, mark this reference as deferred / "
                        f"inherited, or remove the v0.1.14 tag.\n"
                        f"  line: {line.strip()[:200]!r}"
                    )
