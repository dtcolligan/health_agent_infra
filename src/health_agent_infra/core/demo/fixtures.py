"""Packaged-fixture loader for ``hai demo start --persona``.

Origin: v0.1.12 W-Vb (PLAN.md §2.3); reconciliation C3 closure.

The loader resolves a persona slug to a packaged JSON fixture under
``health_agent_infra.demo.fixtures``. Uses ``importlib.resources`` so
a clean wheel install can locate the fixture without referring to the
repo layout.

**v0.1.12 scope (partial closure of W-Vb).** The loader exists, the
packaged path is registered in ``pyproject.toml`` package-data, and
the fixture file format is documented. The end-to-end persona-replay
flow — pre-populating proposals so ``hai daily`` reaches synthesis —
is deferred to v0.1.13. v0.1.12 fixtures are skeleton-only;
``apply_fixture()`` is a no-op-with-marker today.
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Any, Optional


class DemoFixtureError(RuntimeError):
    """Raised when the loader cannot resolve or parse a fixture."""


def load_fixture(persona_slug: str) -> dict[str, Any]:
    """Load the packaged fixture JSON for ``persona_slug``.

    The file must live at ``health_agent_infra/demo/fixtures/<slug>.json``
    and be valid JSON. Raises ``DemoFixtureError`` if absent or malformed.
    """

    if not persona_slug or not isinstance(persona_slug, str):
        raise DemoFixtureError(
            f"persona_slug must be a non-empty string; got {persona_slug!r}"
        )

    package = "health_agent_infra.demo.fixtures"
    filename = f"{persona_slug}.json"
    try:
        body = resources.files(package).joinpath(filename).read_text(
            encoding="utf-8",
        )
    except (FileNotFoundError, ModuleNotFoundError) as exc:
        raise DemoFixtureError(
            f"no packaged fixture for persona slug {persona_slug!r}; "
            f"expected at {package}/{filename}. "
            f"Ship the fixture under src/health_agent_infra/demo/fixtures/ "
            f"(this dir IS in pyproject.toml package-data)."
        ) from exc

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise DemoFixtureError(
            f"fixture {filename} is not valid JSON: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise DemoFixtureError(
            f"fixture {filename} must be a JSON object at the top level; "
            f"got {type(data).__name__}"
        )
    return data


def apply_fixture(
    fixture: dict[str, Any],
    *,
    db_path: Any,
    base_dir_path: Any,
    user_id: str = "u_local_1",
) -> dict[str, Any]:
    """Apply a fixture to the demo's scratch DB + base_dir.

    **v0.1.12 partial-closure scope.** Returns a no-op result with the
    fixture's ``v0_1_12_scope`` marker so the demo flow can surface
    "fixture loaded but proposals not yet seeded; v0.1.13 W-Vb will
    populate" to the user. The actual proposal pre-population work
    (constructing valid DomainProposal rows for each domain so
    ``hai daily`` reaches synthesis) lives in the v0.1.13 cycle.

    Returns:
        A dict matching the schema:
            {
              "applied": bool,
              "scope": "skeleton-only" | "full",
              "persona_slug": str,
              "deferred_to": str | None,
            }
    """

    persona_slug = fixture.get("persona_slug") or "<unknown>"
    scope = fixture.get("v0_1_12_scope", "skeleton-only")

    if scope == "skeleton-only":
        return {
            "applied": False,
            "scope": "skeleton-only",
            "persona_slug": persona_slug,
            "deferred_to": "v0.1.13",
            "message": (
                f"persona fixture {persona_slug!r} loaded; full "
                f"persona-replay (proposal pre-population) deferred to "
                f"v0.1.13 per PLAN.md §2.3 W-Vb partial-closure scope."
            ),
        }

    # Future: scope == "full" branches here in v0.1.13. Walk
    # fixture["domain_proposals"] and post via the propose path,
    # walk fixture["intake_seed"] and post via the intake commands,
    # etc. Today this branch is unreachable because no fixture sets
    # v0_1_12_scope to anything other than "skeleton-only".
    raise DemoFixtureError(
        f"fixture scope {scope!r} not supported in v0.1.12. "
        f"Full persona-replay lands at v0.1.13 W-Vb."
    )


def slug_or_none(slug: Optional[str]) -> Optional[str]:
    """Coerce a CLI-supplied slug to a non-empty string or None.

    Helper used by ``open_session()`` to decide whether to attempt
    fixture loading at all. ``--persona ""`` and ``--blank`` (which
    sets persona to None upstream) both resolve to None here.
    """

    if slug is None:
        return None
    cleaned = slug.strip()
    return cleaned or None
