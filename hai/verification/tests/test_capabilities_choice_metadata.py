"""v0.1.14.1 W-GARMIN-MANIFEST-SIGNAL — per-choice metadata in the
capabilities manifest.

Contracts pinned:

  1. ``annotate_choice_metadata`` validates eagerly:
       - rejects unknown reliability values
       - rejects metadata for choices not declared on the action
       - rejects entries missing the required ``reliability`` field
       - rejects non-dict metadata at top level or per-choice
  2. The walker round-trips attached metadata into the manifest under
     ``flags[].choice_metadata``.
  3. ``hai pull`` and ``hai daily`` carry the
     ``garmin_live -> reliability=unreliable`` signal in their
     ``--source`` flag entry — the structural fix for the agent-contract
     trap that produced the 2026-05-02 incident.
  4. Choices without an entry carry no ``choice_metadata`` key (absence
     is itself the signal — consumers default to "reliable").
"""

from __future__ import annotations

import argparse

import pytest

from health_agent_infra.cli import build_parser
from health_agent_infra.core.capabilities import (
    ContractAnnotationError,
    RELIABILITY_VALUES,
    annotate_choice_metadata,
    walk_parser,
)


# ---------------------------------------------------------------------------
# Validation — annotate_choice_metadata rejects bad shapes eagerly
# ---------------------------------------------------------------------------


def _build_action_with_choices() -> argparse.Action:
    p = argparse.ArgumentParser()
    return p.add_argument("--src", choices=("a", "b", "c"))


def test_rejects_unknown_reliability_value():
    action = _build_action_with_choices()
    with pytest.raises(ContractAnnotationError, match="reliability"):
        annotate_choice_metadata(
            action, {"a": {"reliability": "flaky"}}
        )


def test_rejects_metadata_for_undeclared_choice():
    action = _build_action_with_choices()
    with pytest.raises(ContractAnnotationError, match="not a declared choice"):
        annotate_choice_metadata(
            action, {"z": {"reliability": "reliable"}}
        )


def test_rejects_missing_reliability_field():
    action = _build_action_with_choices()
    with pytest.raises(ContractAnnotationError, match="missing required"):
        annotate_choice_metadata(
            action, {"a": {"reason": "no reliability key"}}
        )


def test_rejects_non_dict_top_level():
    action = _build_action_with_choices()
    with pytest.raises(ContractAnnotationError, match="must be a dict"):
        annotate_choice_metadata(action, ["a", "b"])  # type: ignore[arg-type]


def test_rejects_non_dict_entry():
    action = _build_action_with_choices()
    with pytest.raises(ContractAnnotationError, match="must be a dict"):
        annotate_choice_metadata(action, {"a": "unreliable"})  # type: ignore[dict-item]


def test_accepts_known_reliability_values():
    for value in RELIABILITY_VALUES:
        action = _build_action_with_choices()
        annotate_choice_metadata(action, {"a": {"reliability": value}})


# ---------------------------------------------------------------------------
# Round-trip — walker surfaces attached metadata into manifest
# ---------------------------------------------------------------------------


def test_walker_round_trips_choice_metadata():
    """A flag with attached metadata renders ``choice_metadata`` in the
    manifest entry; flags without attached metadata do not."""

    parent = argparse.ArgumentParser(prog="testroot")
    sub = parent.add_subparsers(dest="cmd")
    leaf = sub.add_parser("probe")

    annotated = leaf.add_argument(
        "--src", choices=("good", "bad"), default=None,
    )
    annotate_choice_metadata(
        annotated,
        {"bad": {"reliability": "unreliable", "reason": "test fixture"}},
    )
    leaf.add_argument("--plain", choices=("x", "y"), default=None)
    leaf.set_defaults(
        func=lambda args: 0,
        _contract_mutation="read-only",
        _contract_idempotent="yes",
        _contract_json_output="default",
        _contract_exit_codes=("OK",),
        _contract_agent_safe=True,
        _contract_description="test fixture",
        _contract_output_schema=None,
        _contract_preconditions=None,
    )

    rows = walk_parser(parent, prog="testroot")
    [row] = rows
    flags_by_name = {f["name"]: f for f in row["flags"]}

    src = flags_by_name["--src"]
    assert "choice_metadata" in src
    assert src["choice_metadata"]["bad"]["reliability"] == "unreliable"
    assert src["choice_metadata"]["bad"]["reason"] == "test fixture"

    plain = flags_by_name["--plain"]
    assert "choice_metadata" not in plain, (
        "absence of metadata is itself the signal — empty/missing key, not "
        "an empty dict"
    )


# ---------------------------------------------------------------------------
# Production parser — garmin_live signal is wired on hai pull + hai daily
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("command", ["hai pull", "hai daily"])
def test_pull_source_carries_garmin_live_unreliable_signal(command: str):
    """The trap-closing assertion: agents reading the manifest see
    garmin_live as structurally unreliable, not just verbally."""

    parser = build_parser()
    rows = walk_parser(parser)
    [row] = [r for r in rows if r["command"] == command]

    flags_by_name = {f["name"]: f for f in row["flags"]}
    source = flags_by_name["--source"]

    assert "choice_metadata" in source, (
        f"{command} --source must carry choice_metadata "
        f"(v0.1.14.1 W-GARMIN-MANIFEST-SIGNAL)"
    )
    garmin = source["choice_metadata"].get("garmin_live")
    assert garmin is not None, (
        f"{command} --source choice_metadata missing 'garmin_live' entry"
    )
    assert garmin["reliability"] == "unreliable"
    assert "intervals_icu" in garmin.get("prefer_instead", "")
    # v0.1.15 F-PV14-01: csv + intervals_icu now carry source_type tags
    # (`fixture` vs `live`) so an agent driving the CLI can distinguish
    # the committed fixture path from the live wearable feeds. Both
    # remain `reliability='reliable'`. This replaces the prior
    # absence-as-signal contract for these two sources; garmin_live
    # still uniquely carries `reliability='unreliable'`.
    assert source["choice_metadata"]["csv"]["source_type"] == "fixture"
    assert source["choice_metadata"]["intervals_icu"]["source_type"] == "live"
    assert source["choice_metadata"]["garmin_live"]["source_type"] == "live"
