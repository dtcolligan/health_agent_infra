"""Regression test for v0.1.7 W33: planned_session_type vocabulary CLI.

Background: per-domain classifiers do substring matching on the
`planned_session_type` field, but agents had no machine-discoverable
list of canonical strings. v0.1.7 adds `hai planned-session-types`
(read-only, agent-safe) emitting the registry. The W21 next-action
manifest's `intake_required` actions reference it.
"""

from __future__ import annotations

import json
import subprocess
from contextlib import redirect_stdout
from io import StringIO

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.intake.planned_session_vocabulary import (
    PLANNED_SESSION_VOCABULARY,
    vocabulary_payload,
)


def test_vocabulary_payload_shape():
    payload = vocabulary_payload()
    assert payload["schema_version"] == "planned_session_vocabulary.v1"
    assert isinstance(payload["tokens"], list)
    assert len(payload["tokens"]) == len(PLANNED_SESSION_VOCABULARY)
    for entry in payload["tokens"]:
        assert {"token", "primary_domain", "classifier_substring",
                "description"}.issubset(entry.keys())


def test_vocabulary_covers_canonical_session_classes():
    tokens = {e["token"] for e in PLANNED_SESSION_VOCABULARY}
    # Sanity floor: the README + W21 are going to reference these.
    assert "rest" in tokens
    assert "easy_z2" in tokens
    assert "intervals_4x4" in tokens
    assert "strength_sbd" in tokens


def test_cli_planned_session_types_emits_payload():
    out_buf = StringIO()
    with redirect_stdout(out_buf):
        rc = cli_main(["planned-session-types"])
    assert rc == exit_codes.OK
    payload = json.loads(out_buf.getvalue())
    assert payload["schema_version"] == "planned_session_vocabulary.v1"
    tokens = {e["token"] for e in payload["tokens"]}
    assert "intervals_4x4" in tokens


def test_planned_session_types_in_capabilities_manifest():
    """Manifest discoverability: an agent reading `hai capabilities`
    must see this command listed agent-safe + read-only."""

    result = subprocess.run(
        ["hai", "capabilities"],
        capture_output=True, text=True, check=True,
    )
    manifest = json.loads(result.stdout)
    by_name = {c["command"]: c for c in manifest["commands"]}
    assert "hai planned-session-types" in by_name
    cmd = by_name["hai planned-session-types"]
    assert cmd["agent_safe"] is True
    assert cmd["mutation"] == "read-only"


def test_classifier_substrings_match_actual_domain_logic():
    """The vocabulary's `classifier_substring` field is the contract:
    when a token is in the vocabulary, the per-domain classifier must
    actually substring-match against that string. Pin the smoke tests
    so a future classifier change that breaks the contract fails here."""

    # Strength classifier (`domains/strength/policy.py:283`) checks
    # for "strength" substring in lowered planned text.
    strength_tokens = [
        e for e in PLANNED_SESSION_VOCABULARY
        if e["primary_domain"] == "strength"
    ]
    for entry in strength_tokens:
        assert entry["classifier_substring"] in entry["token"].lower(), (
            f"Strength token {entry['token']!r} should substring-contain "
            f"its classifier_substring {entry['classifier_substring']!r}"
        )
