"""W-DOMAIN-SYNC (v0.1.14): contract test that the six-domain
registries scattered across the runtime stay in sync.

Per reconciliation L2 + Codex F-PLAN-09, the project enumerates the
canonical six domains in multiple sites for performance / typing /
schema reasons. The risk is that a future cycle adds a domain in
one site and forgets others; mismatches surface as silent skips
or `unknown domain` errors at runtime.

This test pins the canonical set and asserts each enumerated site
agrees. `_DOMAIN_ACTION_REGISTRY` (synthesis_policy) is intentionally
Phase-A-only — it doesn't enumerate every domain — and is exempted
explicitly.
"""

from __future__ import annotations

import pytest


# Canonical six-domain set per AGENTS.md "Six Domains".
CANONICAL_DOMAINS: frozenset[str] = frozenset(
    {"recovery", "running", "sleep", "stress", "strength", "nutrition"}
)


def test_canonical_six_domains():
    """Sanity: AGENTS.md governance invariant pins six domains."""

    assert len(CANONICAL_DOMAINS) == 6


def test_writeback_proposal_supported_domains_match_canonical():
    """``core/writeback/proposal.py::SUPPORTED_DOMAINS`` must equal canonical."""

    from health_agent_infra.core.writeback.proposal import SUPPORTED_DOMAINS

    assert SUPPORTED_DOMAINS == CANONICAL_DOMAINS


def test_writeback_proposal_schema_versions_cover_canonical():
    """Per-domain schema_version entry exists for every canonical domain."""

    from health_agent_infra.core.writeback.proposal import (
        PROPOSAL_SCHEMA_VERSIONS,
    )

    assert set(PROPOSAL_SCHEMA_VERSIONS.keys()) == set(CANONICAL_DOMAINS)


def test_writeback_proposal_action_enums_cover_canonical():
    """Per-domain action enum exists for every canonical domain."""

    from health_agent_infra.core.writeback.proposal import DOMAIN_ACTION_ENUMS

    assert set(DOMAIN_ACTION_ENUMS.keys()) == set(CANONICAL_DOMAINS)


def test_synthesis_expected_domains_match_canonical():
    """``core/synthesis.py`` expected-domain set covers canonical six."""

    import re
    from pathlib import Path

    src = Path(
        "src/health_agent_infra/core/synthesis.py"
    ).read_text(encoding="utf-8")
    # Locate the expected-domain literal — pinned by the synthesis
    # missing_expected_proposals invariant.
    match = re.search(
        r'"recovery", "running", "sleep", "stress", "strength", "nutrition"',
        src,
    )
    assert match is not None, (
        "synthesis.py expected-domain literal "
        '("recovery", "running", "sleep", "stress", "strength", "nutrition") '
        "not found at the canonical site; the W-DOMAIN-SYNC contract is "
        "broken — re-align the literal or update this test."
    )


def test_intake_gaps_covers_canonical_six_domains():
    """``core/intake/gaps.py`` enumerates the canonical six domains."""

    import re
    from pathlib import Path

    src = Path(
        "src/health_agent_infra/core/intake/gaps.py"
    ).read_text(encoding="utf-8")
    match = re.search(
        r'\("recovery", "running", "sleep", "strength", "stress", "nutrition"\)',
        src,
    )
    assert match is not None, (
        "intake/gaps.py canonical-domain enumeration not found; "
        "W-DOMAIN-SYNC contract broken."
    )


def test_domain_tables_registry_includes_canonical_six_via_strength_gym_alias():
    """``core/state/snapshot.py::_DOMAIN_TABLES`` is a snapshot-read alias
    registry, not a canonical-domain registry. By longstanding
    convention (`snapshot.py:522` `strength_today, strength_mx =
    gym_today, gym_mx`), the read-side uses ``gym`` as the alias for
    the canonical ``strength`` domain. This test pins both the canonical
    cover and the alias mapping so future renames don't silently
    diverge."""

    from health_agent_infra.core.state.snapshot import _DOMAIN_TABLES

    canonical_with_alias = (set(CANONICAL_DOMAINS) - {"strength"}) | {"gym"}
    missing = canonical_with_alias - set(_DOMAIN_TABLES.keys())
    assert missing == set(), (
        f"_DOMAIN_TABLES missing canonical domain(s) (counting `gym` as "
        f"the read-side alias for `strength`): {sorted(missing)}"
    )
    # Explicit pin: gym alias must continue to map to the resistance-
    # training table; if this changes, snapshot.py:522 must change
    # alongside.
    assert _DOMAIN_TABLES["gym"] == "accepted_resistance_training_state_daily"


def test_domain_action_registry_phase_a_only_exemption():
    """``synthesis_policy._DOMAIN_ACTION_REGISTRY`` is intentionally
    Phase-A-only. It does NOT enumerate every canonical domain — it
    enumerates only the domains that participate in Phase-A action
    selection. This test pins the exemption explicitly so a future
    reader doesn't "fix" the registry into a six-domain shape and
    silently break the Phase-A semantics."""

    from health_agent_infra.core.synthesis_policy import (
        _DOMAIN_ACTION_REGISTRY,
    )

    # The registry is intentionally Phase-A-only. The exemption is
    # that it MAY be a strict subset of CANONICAL_DOMAINS — having
    # fewer keys is correct (Phase-A applies to a subset of
    # domains). Having MORE keys would mean a domain was added to
    # the registry that isn't in the canonical six, which is wrong.
    extra = set(_DOMAIN_ACTION_REGISTRY.keys()) - set(CANONICAL_DOMAINS)
    assert extra == set(), (
        f"_DOMAIN_ACTION_REGISTRY has non-canonical domain(s) "
        f"{sorted(extra)}; the registry must be a subset of the "
        f"canonical six. Extending the canonical six is a separate "
        f"governance change that needs an AGENTS.md edit."
    )
