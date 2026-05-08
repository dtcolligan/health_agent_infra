"""W-S / F-DEMO-02: domain_proposal_contracts in capabilities manifest.

`hai capabilities --json` now exposes a top-level
`domain_proposal_contracts` block enumerating each domain's
proposal schema_version + action enum + required fields. Agents
composing proposals from scratch consume this rather than greping
schemas.py.

Asserts:
- Every domain in ALLOWED_ACTIONS_BY_DOMAIN appears in the
  manifest block.
- The action enum matches the runtime's ALLOWED_ACTIONS_BY_DOMAIN.
- The schema_version matches the per-domain schema constant.
- W30 preserved: this is an additive top-level block, not a
  schema-freeze check.
"""

from __future__ import annotations

import pytest

from health_agent_infra.cli import build_parser
from health_agent_infra.core.capabilities import build_manifest
from health_agent_infra.core.validate import ALLOWED_ACTIONS_BY_DOMAIN


@pytest.fixture(scope="module")
def manifest():
    return build_manifest(build_parser())


def test_top_level_block_present(manifest):
    assert "domain_proposal_contracts" in manifest


def test_every_domain_present(manifest):
    block = manifest["domain_proposal_contracts"]
    for domain in ALLOWED_ACTIONS_BY_DOMAIN:
        assert domain in block, (
            f"domain={domain!r} missing from "
            f"manifest.domain_proposal_contracts"
        )


def test_action_enum_matches_runtime(manifest):
    block = manifest["domain_proposal_contracts"]
    for domain, allowed in ALLOWED_ACTIONS_BY_DOMAIN.items():
        manifest_actions = set(block[domain]["action_enum"])
        assert manifest_actions == set(allowed), (
            f"action enum drift for domain={domain!r}: "
            f"manifest={sorted(manifest_actions)}, "
            f"runtime={sorted(allowed)}"
        )


def test_schema_versions_match_domain_registry(manifest):
    """Each domain's schema_version field must match the canonical
    registry in core/intake/next_actions._DOMAIN_PROPOSAL_SCHEMAS."""
    from health_agent_infra.core.intake.next_actions import (
        _DOMAIN_PROPOSAL_SCHEMAS,
    )

    block = manifest["domain_proposal_contracts"]
    for domain, expected_version in _DOMAIN_PROPOSAL_SCHEMAS.items():
        assert block[domain]["schema_version"] == expected_version


def test_required_fields_present(manifest):
    """Every per-domain block lists the DomainProposal envelope's
    required fields. Backwards-compat note: this is documentation,
    not a schema-freeze check."""
    block = manifest["domain_proposal_contracts"]
    expected_required = {
        "schema_version",
        "proposal_id",
        "user_id",
        "for_date",
        "domain",
        "action",
        "rationale",
        "confidence",
        "policy_decisions",
    }
    for domain, contract in block.items():
        actual_required = set(contract["required_fields"])
        assert actual_required == expected_required, (
            f"required_fields drift for domain={domain!r}: "
            f"got {sorted(actual_required)}, "
            f"expected {sorted(expected_required)}"
        )


def test_top_level_manifest_schema_version_unchanged_per_W30(manifest):
    """W30: the manifest schema is NOT frozen by adding this block.
    The top-level schema_version field stays at v1."""
    assert manifest["schema_version"] == "agent_cli_contract.v1"
