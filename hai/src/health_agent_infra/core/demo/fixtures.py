"""Packaged-fixture loader for ``hai demo start --persona``.

Origin: v0.1.12 W-Vb (skeleton + boundary-stop apply); v0.1.13 W-Vb
flips ``apply_fixture()`` from a no-op-with-marker to a proposal-write
branch so ``hai demo start --persona <slug> && hai daily`` reaches a
``synthesized`` daily plan end-to-end.

The loader resolves a persona slug to a packaged JSON fixture under
``health_agent_infra.demo.fixtures``. Uses ``importlib.resources`` so
a clean wheel install can locate the fixture without referring to the
repo layout.

Fixture schema ``demo_persona_fixture.v1``::

    {
      "schema_version": "demo_persona_fixture.v1",
      "persona_slug":  "<slug>",
      "scope":         "full",
      "description":   "<archetype prose>",
      "domain_proposals": [
        {
          "domain":          "recovery|running|sleep|stress|strength|nutrition",
          "schema_version":  "<domain>_proposal.v1",
          "action":          "<domain action enum>",
          "action_detail":   null | <str>,
          "rationale":       [<str>, ...],
          "confidence":      "low|moderate|high",
          "uncertainty":     [<str>, ...],
          "policy_decisions":[ {"rule_id": <str>, "decision": <str>, "note": <str>}, ... ],
          "bounded":         true
        },
        ...  (one per domain)
      ]
    }

The fixture file omits the runtime-determined fields ``proposal_id``,
``for_date``, and ``user_id``. ``apply_fixture()`` fills these in based
on the target date (default ``date.today()``) and the demo session's
``user_id`` so a single fixture file is portable across days.
"""

from __future__ import annotations

import json
from datetime import date as date_type
from importlib import resources
from pathlib import Path
from typing import Any, Optional


class DemoFixtureError(RuntimeError):
    """Raised when the loader cannot resolve, parse, or apply a fixture."""


_REQUIRED_FIXTURE_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "persona_slug",
    "scope",
    "domain_proposals",
})

_REQUIRED_PROPOSAL_TEMPLATE_FIELDS: frozenset[str] = frozenset({
    "domain",
    "schema_version",
    "action",
    "rationale",
    "confidence",
    "uncertainty",
    "policy_decisions",
    "bounded",
})

FIXTURE_SCHEMA_VERSION = "demo_persona_fixture.v1"


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
            f"Ship the fixture under hai/src/health_agent_infra/demo/fixtures/ "
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
    for_date: Optional[date_type] = None,
) -> dict[str, Any]:
    """Apply a fixture to the demo's scratch DB + base_dir.

    v0.1.13 W-Vb scope: walks ``fixture["domain_proposals"]`` and writes
    each entry through the canonical proposal write path (per-domain
    JSONL audit log + ``proposal_log`` projection) so a subsequent
    ``hai daily`` finds a complete proposal set and reaches synthesis.

    The fixture's proposal templates omit ``proposal_id``, ``for_date``,
    and ``user_id``; this function fills those in from ``user_id`` and
    ``for_date`` (default ``date.today()``).

    Returns:
        A dict matching the schema:
            {
              "applied": bool,
              "scope":   "full" | "skeleton-only",
              "persona_slug": str,
              "deferred_to": str | None,
              "for_date":  str (ISO),
              "user_id":   str,
              "proposals_written": int,
            }
    """

    persona_slug = fixture.get("persona_slug") or "<unknown>"
    scope = fixture.get("scope", fixture.get("v0_1_12_scope", "skeleton-only"))

    if scope != "full":
        return {
            "applied": False,
            "scope": scope,
            "persona_slug": persona_slug,
            "deferred_to": "v0.1.13",
            "message": (
                f"persona fixture {persona_slug!r} is not a full-scope "
                f"fixture (scope={scope!r}); refusing to seed proposals."
            ),
        }

    _validate_fixture_shape(fixture)

    target_date = for_date if for_date is not None else date_type.today()
    target_for_date_iso = target_date.isoformat()

    db_path_p = Path(db_path)
    base_dir_p = Path(base_dir_path)

    if not db_path_p.exists():
        raise DemoFixtureError(
            f"apply_fixture requires an initialized scratch DB at "
            f"{db_path_p}; demo session-open should have created it. "
            f"Refusing to seed proposals against a missing DB."
        )

    written: list[str] = []
    seen_domains: set[str] = set()

    # Lazy imports — avoid pulling synthesis/projection surfaces into the
    # demo-fixture module's import graph for the no-persona blank-session
    # path, and dodge any circular import via state.store -> demo.session.
    from health_agent_infra.core.state import (  # noqa: PLC0415
        ProposalReplaceRequired,
        open_connection,
        project_proposal,
    )
    from health_agent_infra.core.writeback.proposal import (  # noqa: PLC0415
        ProposalValidationError,
        perform_proposal_writeback,
        validate_proposal_dict,
    )

    for template in fixture["domain_proposals"]:
        domain = template["domain"]
        if domain in seen_domains:
            raise DemoFixtureError(
                f"fixture {persona_slug!r} has duplicate proposal "
                f"templates for domain {domain!r}; expected exactly one "
                f"per domain."
            )
        seen_domains.add(domain)

        payload = _materialise_proposal(
            template,
            persona_slug=persona_slug,
            for_date_iso=target_for_date_iso,
            user_id=user_id,
        )

        try:
            validate_proposal_dict(payload, expected_domain=domain)
        except ProposalValidationError as exc:
            raise DemoFixtureError(
                f"fixture {persona_slug!r} domain {domain!r} produced an "
                f"invalid proposal payload "
                f"(invariant={exc.invariant}): {exc}"
            ) from exc

        # JSONL audit first (durability boundary), then DB projection.
        # Mirrors cmd_propose's contract.
        perform_proposal_writeback(payload, base_dir=base_dir_p)

        conn = open_connection(db_path_p)
        try:
            try:
                project_proposal(conn, payload, replace=False)
            except ProposalReplaceRequired:
                # A demo scratch DB on a fresh session should never have
                # an existing canonical leaf for the target key; if it
                # somehow does, treat as a fixture-application error.
                raise DemoFixtureError(
                    f"fixture {persona_slug!r} domain {domain!r}: "
                    f"existing canonical proposal for "
                    f"({target_for_date_iso}, {user_id}, {domain}) "
                    f"in scratch DB. Refusing to silently revise."
                )
        finally:
            conn.close()

        written.append(payload["proposal_id"])

    return {
        "applied": True,
        "scope": "full",
        "persona_slug": persona_slug,
        "deferred_to": None,
        "for_date": target_for_date_iso,
        "user_id": user_id,
        "proposals_written": len(written),
        "proposal_ids": written,
    }


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


def _validate_fixture_shape(fixture: dict[str, Any]) -> None:
    """Check the v1 fixture envelope before walking proposals."""

    missing = _REQUIRED_FIXTURE_FIELDS - set(fixture.keys())
    if missing:
        raise DemoFixtureError(
            f"fixture missing required top-level fields: {sorted(missing)}"
        )

    if fixture["schema_version"] != FIXTURE_SCHEMA_VERSION:
        raise DemoFixtureError(
            f"fixture schema_version "
            f"{fixture['schema_version']!r} not supported; expected "
            f"{FIXTURE_SCHEMA_VERSION!r}"
        )

    proposals = fixture["domain_proposals"]
    if not isinstance(proposals, list) or not proposals:
        raise DemoFixtureError(
            f"fixture domain_proposals must be a non-empty list; "
            f"got {type(proposals).__name__}"
        )

    for idx, template in enumerate(proposals):
        if not isinstance(template, dict):
            raise DemoFixtureError(
                f"fixture domain_proposals[{idx}] must be a JSON object; "
                f"got {type(template).__name__}"
            )
        missing = _REQUIRED_PROPOSAL_TEMPLATE_FIELDS - set(template.keys())
        if missing:
            raise DemoFixtureError(
                f"fixture domain_proposals[{idx}] missing required "
                f"fields: {sorted(missing)}"
            )


def _materialise_proposal(
    template: dict[str, Any],
    *,
    persona_slug: str,
    for_date_iso: str,
    user_id: str,
) -> dict[str, Any]:
    """Fill in the runtime-determined fields a fixture template omits.

    Returns a fresh dict so the template is not mutated; callers chain
    this into ``validate_proposal_dict`` then the writeback path.
    """

    domain = template["domain"]
    proposal_id = f"prop_{for_date_iso}_{user_id}_{domain}_01"

    payload: dict[str, Any] = {
        "schema_version": template["schema_version"],
        "proposal_id": proposal_id,
        "user_id": user_id,
        "for_date": for_date_iso,
        "domain": domain,
        "action": template["action"],
        "action_detail": template.get("action_detail"),
        "rationale": list(template.get("rationale") or []),
        "confidence": template["confidence"],
        "uncertainty": list(template.get("uncertainty") or []),
        "policy_decisions": list(template.get("policy_decisions") or []),
        "bounded": template["bounded"],
    }
    return payload
