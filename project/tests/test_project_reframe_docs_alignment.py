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
    body = _read("project/DECISIONS.md")

    for i in range(1, 13):
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
        "hai/reporting/` is HAI proof/history",
        "repo shape is owner-based",
    )
    for term in required_terms:
        assert term in body


def test_cold_start_docs_route_through_project_decisions() -> None:
    required_docs = (
        "README.md",
        "project/FRAME.md",
        "project/OPERATING_MODEL.md",
        "AGENTS.md",
        "CLAUDE.md",
        "CONTRIBUTING.md",
        "project/REPO_MAP.md",
        "hai/docs/README.md",
        "hai/docs/hai_reference_runtime.md",
        "hai/docs/current_system_state.md",
        "hai/docs/tour.md",
        "research/README.md",
        "benchmark/README.md",
    )

    for rel_path in required_docs:
        assert "DECISIONS.md" in _read(rel_path), rel_path


def test_active_docs_explain_current_vs_historical_roots() -> None:
    repo_map = _read("project/REPO_MAP.md")
    operating_model = _read("project/OPERATING_MODEL.md")
    reporting_readme = _read("hai/reporting/README.md")
    legacy_docs_readme = _read("hai/reporting/docs/README.md")
    hai_docs_readme = _read("hai/docs/README.md")

    for owner_root in ("project/", "hai/", "benchmark/", "research/"):
        assert owner_root in repo_map
        assert owner_root in operating_model

    for removed_root in ("root `src/`", "root `docs/`", "root `verification/`"):
        assert removed_root in repo_map

    assert "Tooling, entrypoints, and repository metadata only" in operating_model
    assert "Physical Ownership Model" in repo_map

    assert "Current documentation for the HAI reference runtime" in hai_docs_readme
    assert "legacy docs location" in reporting_readme
    assert "Do not add new current documentation here" in legacy_docs_readme


def test_no_removed_owner_roots_are_checked_in() -> None:
    for rel_path in ("src", "docs", "verification", "reporting", "benchmarks", "assets"):
        assert not (REPO_ROOT / rel_path).exists(), rel_path


def test_research_frame_content_is_pinned_on_primary_surfaces() -> None:
    readme_head = "\n".join(_read("README.md").splitlines()[:12]).lower()
    roadmap = _read("project/ROADMAP.md")
    hypotheses = _read("project/HYPOTHESES.md")
    paper_frame = _read("research/runtime_contracts_paper/PAPER_FRAME.md")
    bench_readme = _read("benchmark/governed_agent_bench/README.md")
    bench_readme_flat = " ".join(bench_readme.split())

    assert "runtime contracts" in readme_head
    assert "research" in readme_head
    assert "Research lane" in roadmap
    assert "Planning Gate 1" in roadmap
    assert "GovernedAgentBench measurement-readiness" in roadmap

    for i in range(1, 7):
        assert f"## H{i}." in hypotheses

    assert (
        "Runtime Contracts for Local Agents Over Sensitive User-Owned Data"
        in paper_frame
    )
    assert "project/FRAME.md" in bench_readme
    assert "project/DECISIONS.md" in bench_readme
    assert "RESEARCH_EVAL_STRATEGY.md" in bench_readme
    assert "measurement-readiness" in bench_readme
    assert "known-good and known-bad trajectories" in bench_readme_flat
    assert "10 committed tasks" in bench_readme
    assert "2 committed snapshots" in bench_readme


def test_hai_forward_plan_docs_are_marked_as_support_lane() -> None:
    support_lane_docs = (
        "hai/docs/n_of_1_methodology.md",
        "hai/docs/mcp_threat_model.md",
        "hai/docs/personal_health_agent_positioning.md",
        "hai/reporting/plans/post_v0_1_18/strategic_plan_v2.md",
    )

    for rel_path in support_lane_docs:
        body = _read(rel_path)
        assert "project/FRAME.md" in body, rel_path
        assert "project/DECISIONS.md" in body, rel_path
        assert "support-lane" in body or "support lane" in body, rel_path


def test_active_control_docs_do_not_reintroduce_product_first_sentinels() -> None:
    active_docs = (
        "README.md",
        "project/FRAME.md",
        "project/DECISIONS.md",
        "project/OPERATING_MODEL.md",
        "project/ROADMAP.md",
        "project/HYPOTHESES.md",
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


def test_hai_paper_readiness_is_the_active_runtime_planning_label() -> None:
    active_planning_docs = (
        "README.md",
        "project/FRAME.md",
        "project/DECISIONS.md",
        "project/OPERATING_MODEL.md",
        "project/ROADMAP.md",
        "AGENTS.md",
        "research/README.md",
        "research/runtime_contracts_paper/HAI_PAPER_READINESS_PLAN.md",
        "research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md",
        "research/runtime_contracts_paper/WORK_PACKETS.md",
        "hai/docs/hai_reference_runtime.md",
        "hai/docs/current_system_state.md",
    )

    assert (
        REPO_ROOT / "research/runtime_contracts_paper/HAI_PAPER_READINESS_PLAN.md"
    ).exists()

    for rel_path in active_planning_docs:
        body = _read(rel_path)
        assert "RUNTIME_CONTRACT_FREEZE_PLAN" not in body, rel_path
        assert "contract freeze" not in body.lower(), rel_path

    assert "HAI paper-readiness" in _read("project/FRAME.md")
    assert "HAI Paper-Readiness Engineering" in _read(
        "research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md"
    )
