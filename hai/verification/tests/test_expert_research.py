"""Phase F — grounded-expert prototype tests.

Locks the scope contract from ``hai/docs/grounded_expert_scope.md``:

- every shipped source's origin file exists and carries the declared
  excerpt verbatim (§2, §6);
- retrieval abstains on off-allowlist topics (§4);
- retrieval refuses user-context payloads (§3);
- the retrieval module has no network-library imports (§5);
- bundled eval scenarios resolve against the retrieval surface.

These tests are the fence behind the prototype: a later commit cannot
loosen the scope without also breaking one of them.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from health_agent_infra.core.research import (
    ALLOWLISTED_SOURCE_CLASSES,
    ALLOWLISTED_TOPICS,
    SOURCES,
    PrivacyViolation,
    RetrievalQuery,
    retrieve,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
HAI_ROOT = REPO_ROOT / "hai"
SCENARIO_DIR = HAI_ROOT / "verification" / "evals" / "scenarios" / "expert"


# ---------------------------------------------------------------------------
# Source registry invariants
# ---------------------------------------------------------------------------


def test_every_source_origin_exists() -> None:
    for source in SOURCES:
        path = REPO_ROOT / source.origin_path
        assert path.exists(), (
            f"source {source.source_id!r} declares origin_path "
            f"{source.origin_path!r} but the file does not exist"
        )


def test_every_source_excerpt_is_literal() -> None:
    for source in SOURCES:
        path = REPO_ROOT / source.origin_path
        content = path.read_text()
        assert source.excerpt in content, (
            f"source {source.source_id!r} carries an excerpt that does "
            f"not appear verbatim in {source.origin_path!r}. Either the "
            f"file was reflowed, or the excerpt was invented."
        )


def test_every_source_class_is_allowlisted() -> None:
    for source in SOURCES:
        assert source.source_class in ALLOWLISTED_SOURCE_CLASSES, (
            f"source {source.source_id!r} declares class "
            f"{source.source_class!r} which is not on the allowlist "
            f"{list(ALLOWLISTED_SOURCE_CLASSES)!r}"
        )


def test_every_source_has_at_least_one_topic() -> None:
    for source in SOURCES:
        assert source.topics, (
            f"source {source.source_id!r} has no topics — retrieval "
            f"cannot reach it"
        )


def test_source_ids_are_unique() -> None:
    ids = [s.source_id for s in SOURCES]
    assert len(ids) == len(set(ids)), "duplicate source_id detected"


# ---------------------------------------------------------------------------
# Retrieval surface invariants
# ---------------------------------------------------------------------------


def test_retrieval_returns_sources_for_allowlisted_topic() -> None:
    for topic in ALLOWLISTED_TOPICS:
        result = retrieve(RetrievalQuery(topic=topic))
        assert not result.is_abstain, (
            f"topic {topic!r} is allowlisted but retrieval abstained; "
            f"reason={result.abstain_reason!r}"
        )
        assert result.sources, (
            f"topic {topic!r} returned no sources — the allowlist and "
            f"the source registry have drifted apart"
        )


def test_retrieval_abstains_on_off_allowlist_topic() -> None:
    result = retrieve(RetrievalQuery(topic="sports_drink_recovery"))
    assert result.is_abstain
    assert not result.sources
    assert result.abstain_reason is not None
    assert "allowlist" in result.abstain_reason


def test_retrieval_refuses_user_context_payload() -> None:
    with pytest.raises(PrivacyViolation):
        retrieve(
            RetrievalQuery(
                topic="sleep_debt",
                user_context_sent=True,
                operator_initiated=False,
            )
        )


def test_retrieval_refuses_operator_initiated_off_device_path() -> None:
    # v0.1-F ships no operator-initiated off-device retrieval path;
    # even with both flags set, retrieve() must refuse so nobody can
    # quietly flip on a network send without updating the scope doc.
    with pytest.raises(PrivacyViolation):
        retrieve(
            RetrievalQuery(
                topic="sleep_debt",
                user_context_sent=True,
                operator_initiated=True,
            )
        )


def test_retrieval_module_has_no_network_imports() -> None:
    # §5 rule 5 of the scope doc: no broad web-search behaviour in this
    # phase. Locking the property at source-text level means a future
    # commit that imports `requests` triggers this test instead of
    # silently shipping the regression.
    retrieval_src = (
        HAI_ROOT
        / "src"
        / "health_agent_infra"
        / "core"
        / "research"
        / "retrieval.py"
    ).read_text()
    sources_src = (
        HAI_ROOT
        / "src"
        / "health_agent_infra"
        / "core"
        / "research"
        / "sources.py"
    ).read_text()
    forbidden = (
        "import urllib",
        "from urllib",
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "import socket",
        "from socket",
        "import http.client",
        "from http.client",
    )
    for blob, label in ((retrieval_src, "retrieval.py"), (sources_src, "sources.py")):
        for needle in forbidden:
            assert needle not in blob, (
                f"{label} contains forbidden import {needle!r} — the "
                f"research module must stay network-free per "
                f"grounded_expert_scope.md §5 rule 5"
            )


# ---------------------------------------------------------------------------
# Eval scenarios — bounded explainer questions
# ---------------------------------------------------------------------------


def _load_scenarios() -> list[dict]:
    return sorted(
        (json.loads(p.read_text()) for p in SCENARIO_DIR.glob("*.json")),
        key=lambda s: s["scenario_id"],
    )


def test_scenario_dir_is_populated() -> None:
    scenarios = _load_scenarios()
    assert scenarios, (
        f"no expert scenarios under {SCENARIO_DIR}; Phase F ships at "
        f"least three canonical questions + one abstain case"
    )
    # Phase F ships 3 canonical + 1 abstain = 4 minimum.
    assert len(scenarios) >= 4


def test_every_scenario_sets_cite_or_abstain() -> None:
    for scenario in _load_scenarios():
        assert scenario.get("must_cite_or_abstain") is True, (
            f"scenario {scenario['scenario_id']!r} does not pin "
            f"must_cite_or_abstain; the invariant would not be enforced"
        )


def test_positive_scenarios_retrieve_expected_sources() -> None:
    for scenario in _load_scenarios():
        if scenario.get("expected_abstain"):
            continue
        result = retrieve(RetrievalQuery(topic=scenario["expected_topic"]))
        assert not result.is_abstain, (
            f"scenario {scenario['scenario_id']!r} expected a cited "
            f"answer but retrieval abstained: {result.abstain_reason!r}"
        )
        returned_ids = {s.source_id for s in result.sources}
        for expected_id in scenario.get("expected_source_ids_subset", []):
            assert expected_id in returned_ids, (
                f"scenario {scenario['scenario_id']!r}: expected source "
                f"{expected_id!r} was not returned by retrieval. Got "
                f"{sorted(returned_ids)!r}."
            )


def test_abstain_scenarios_actually_abstain() -> None:
    saw_abstain_scenario = False
    for scenario in _load_scenarios():
        if not scenario.get("expected_abstain"):
            continue
        saw_abstain_scenario = True
        result = retrieve(RetrievalQuery(topic=scenario["expected_topic"]))
        assert result.is_abstain, (
            f"scenario {scenario['scenario_id']!r} expected retrieval to "
            f"abstain but it returned sources {[s.source_id for s in result.sources]!r}"
        )
    assert saw_abstain_scenario, (
        "no abstain scenario present; Phase F needs at least one to "
        "lock the cite-or-abstain fence"
    )


# ---------------------------------------------------------------------------
# Skill / scope-doc invariants
# ---------------------------------------------------------------------------


def test_skill_file_is_read_only() -> None:
    skill_path = (
        HAI_ROOT
        / "src"
        / "health_agent_infra"
        / "skills"
        / "expert-explainer"
        / "SKILL.md"
    )
    assert skill_path.exists()
    body = skill_path.read_text()
    # The skill must never reach for a write surface.
    forbidden_commands = (
        "hai writeback",
        "hai synthesize",
        "hai propose",
        "hai memory set",
        "hai memory archive",
        "hai review record",
    )
    for command in forbidden_commands:
        # The skill can legitimately *reference* these in a "do not call"
        # list but must not show them as invocations. We enforce a
        # stricter rule: they must not appear in the allowed-tools
        # frontmatter or any ``` fenced example.
        front_matter_end = body.find("---", 3)
        front_matter = body[:front_matter_end]
        assert command not in front_matter, (
            f"expert-explainer SKILL.md frontmatter references forbidden "
            f"command {command!r}"
        )


def test_scope_doc_present_and_names_key_sections() -> None:
    scope_path = (
        HAI_ROOT
        / "docs"
        / "grounded_expert_scope.md"
    )
    assert scope_path.exists()
    text = scope_path.read_text()
    # Anchor phrases the rest of Phase F depends on.
    for needle in (
        "Allowed source classes",
        "Privacy rules",
        "Citation policy",
        "Out-of-scope",
    ):
        assert needle in text, (
            f"grounded_expert_scope.md is missing section {needle!r}; "
            f"Phase F's fence relies on that section existing"
        )
