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
