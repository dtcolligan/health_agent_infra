"""Guard the post-reframe project documentation contract.

The 2026-05 runtime-contract reframe is now a project invariant, not
conversation memory. These tests intentionally check only high-signal
signposts: cold-start docs must route readers through the decision log,
the decision log must contain every locked D-PROJ item, and the active
folder split must be visible from the docs that future agents read first.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_project_decision_log_contains_locked_reframe_decisions() -> None:
    body = _read("PROJECT_DECISIONS.md")

    for i in range(1, 12):
        assert f"D-PROJ-{i:03d}" in body

    required_terms = (
        "runtime-contract research repo",
        "sensitive user-owned data",
        "GovernedAgentBench",
        "Runtime Contracts for Local Agents Over Sensitive User-Owned Data",
        "conservative and measurement-first",
        "No diagnosis",
        "local prompt-only models",
        "does not require all six HAI domains",
        "Documentation alignment",
        "reporting/` is proof/history",
    )
    for term in required_terms:
        assert term in body


def test_cold_start_docs_route_through_project_decisions() -> None:
    required_docs = (
        "README.md",
        "PROJECT_FRAME.md",
        "PROJECT_OPERATING_MODEL.md",
        "AGENTS.md",
        "CLAUDE.md",
        "CONTRIBUTING.md",
        "REPO_MAP.md",
        "docs/README.md",
        "docs/hai/README.md",
        "docs/hai/hai_reference_runtime.md",
        "docs/hai/current_system_state.md",
        "docs/hai/tour.md",
        "research/README.md",
        "benchmarks/README.md",
    )

    for rel_path in required_docs:
        assert "PROJECT_DECISIONS.md" in _read(rel_path), rel_path


def test_active_docs_explain_current_vs_historical_roots() -> None:
    repo_map = _read("REPO_MAP.md")
    operating_model = _read("PROJECT_OPERATING_MODEL.md")
    reporting_readme = _read("reporting/README.md")
    legacy_docs_readme = _read("reporting/docs/README.md")
    hai_docs_readme = _read("docs/hai/README.md")

    for root in ("research/", "benchmarks/", "docs/hai/", "reporting/"):
        assert root in repo_map
        assert root in operating_model

    assert "Current documentation for the HAI reference runtime" in hai_docs_readme
    assert "legacy docs location" in reporting_readme
    assert "Do not add new current documentation here" in legacy_docs_readme


def test_research_frame_content_is_pinned_on_primary_surfaces() -> None:
    readme_head = "\n".join(_read("README.md").splitlines()[:12]).lower()
    roadmap = _read("ROADMAP.md")
    hypotheses = _read("HYPOTHESES.md")
    paper_frame = _read("research/runtime_contracts_paper/PAPER_FRAME.md")
    bench_readme = _read("benchmarks/governed_agent_bench/README.md")

    assert "runtime contracts" in readme_head
    assert "research" in readme_head
    assert "Research lane" in roadmap
    assert "Documentation alignment gate" in roadmap
    assert "GovernedAgentBench MVP" in roadmap

    for i in range(1, 7):
        assert f"## H{i}." in hypotheses

    assert (
        "Runtime Contracts for Local Agents Over Sensitive User-Owned Data"
        in paper_frame
    )
    assert "PROJECT_FRAME.md" in bench_readme
    assert "PROJECT_DECISIONS.md" in bench_readme
    assert "RESEARCH_EVAL_STRATEGY.md" in bench_readme
    assert "0 committed tasks" in bench_readme
    assert "0 frozen manifests" in bench_readme


def test_hai_forward_plan_docs_are_marked_as_support_lane() -> None:
    support_lane_docs = (
        "docs/hai/n_of_1_methodology.md",
        "docs/hai/mcp_threat_model.md",
        "docs/hai/personal_health_agent_positioning.md",
        "reporting/plans/post_v0_1_18/strategic_plan_v2.md",
    )

    for rel_path in support_lane_docs:
        body = _read(rel_path)
        assert "PROJECT_FRAME.md" in body, rel_path
        assert "PROJECT_DECISIONS.md" in body, rel_path
        assert "support-lane" in body or "support lane" in body, rel_path


def test_active_control_docs_do_not_reintroduce_product_first_sentinels() -> None:
    active_docs = (
        "README.md",
        "PROJECT_FRAME.md",
        "PROJECT_DECISIONS.md",
        "PROJECT_OPERATING_MODEL.md",
        "ROADMAP.md",
        "HYPOTHESES.md",
        "CONTRIBUTING.md",
    )
    banned = (
        "consumer health product",
        "HAI is the whole project",
        "This repository is a HAI product repo",
        "health-agent-first",
    )

    for rel_path in active_docs:
        body = _read(rel_path)
        for phrase in banned:
            assert phrase not in body, f"{rel_path}: {phrase}"
