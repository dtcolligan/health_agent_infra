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
