"""W-S: persona harness drift guards (Codex F-CDX-IR-06).

The synthetic skill in `verification/dogfood/synthetic_skill.py`
maps domain status fields → action tokens. A renamed action token
in the runtime would silently mismatch and downstream tests would
fail with a less-clear `hai propose` validation error.

This contract test asserts the harness's emitted action surface is
a subset of `core.validate.ALLOWED_ACTIONS_BY_DOMAIN`. Runs cheap
+ fast in `verification/tests/`.
"""

from __future__ import annotations

import pytest

from health_agent_infra.core.validate import ALLOWED_ACTIONS_BY_DOMAIN

import sys
from pathlib import Path

# verification/dogfood/ isn't a python package; add the repo root to
# sys.path so we can import the synthetic skill module directly.
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from verification.dogfood.synthetic_skill import (  # noqa: E402
    _DOMAIN_DEFAULT_ACTION,
    _STATUS_TO_ACTION,
)


def test_every_domain_in_default_action_table_is_in_runtime_enum():
    for domain in _DOMAIN_DEFAULT_ACTION:
        assert domain in ALLOWED_ACTIONS_BY_DOMAIN, (
            f"harness defines a default action for domain={domain!r} "
            f"but ALLOWED_ACTIONS_BY_DOMAIN has no such domain."
        )


def test_every_domain_in_status_to_action_table_is_in_runtime_enum():
    for domain in _STATUS_TO_ACTION:
        assert domain in ALLOWED_ACTIONS_BY_DOMAIN, (
            f"harness defines status mappings for domain={domain!r} "
            f"but ALLOWED_ACTIONS_BY_DOMAIN has no such domain."
        )


def test_every_default_action_is_a_valid_runtime_token():
    """Every action the harness *defaults* to must be in the
    runtime's enum for that domain."""
    for domain, action in _DOMAIN_DEFAULT_ACTION.items():
        allowed = ALLOWED_ACTIONS_BY_DOMAIN[domain]
        assert action in allowed, (
            f"harness default for domain={domain!r} is "
            f"action={action!r}, which is NOT in {sorted(allowed)}"
        )


def test_every_status_mapped_action_is_a_valid_runtime_token():
    """Every action the harness emits via _STATUS_TO_ACTION must
    be in the runtime's enum for that domain."""
    for domain, status_map in _STATUS_TO_ACTION.items():
        allowed = ALLOWED_ACTIONS_BY_DOMAIN[domain]
        for status, action in status_map.items():
            assert action in allowed, (
                f"harness status mapping {domain}.{status!r} → "
                f"{action!r} is NOT in {sorted(allowed)}"
            )


def test_every_runtime_domain_appears_in_harness_default_table():
    """Counter-direction drift: a new domain in the runtime should
    grow the harness's default-action table."""
    for domain in ALLOWED_ACTIONS_BY_DOMAIN:
        assert domain in _DOMAIN_DEFAULT_ACTION, (
            f"runtime declares ALLOWED_ACTIONS_BY_DOMAIN[{domain!r}] "
            f"but the harness has no default action mapping. "
            f"Update verification/dogfood/synthetic_skill.py."
        )
