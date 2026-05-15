"""Alignment tests for the runtime-first reframe (round-2 closeout).

Per F-CDX-RFR-R2-01 and F-CDX-RFR-R2-02, the runtime-first reframe is
the canonical experimental design. Active project documentation must
not reintroduce:

- the `no_runtime_enforcement_enforcement` typo from the round-1 closeout;
- bare `no_runtime` outside historical or audit-prose contexts;
- prompt-axis condition strings that imply varying the prompt across
  conditions (`with_manifest`, `without_manifest`,
  `local_prompt_only`, `cloud_prompt_only`, `prompt-only baseline`,
  `manifest-grounded prompting`).

Audit responses, audit prompts, historical plans, this test file, and
memory files are allowed to mention these strings as quoted prose. All
other markdown under the repo is treated as active doc and must not
contain operative prompt-axis instructions.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _allowed(path: Path) -> bool:
    """Return True if `path` is exempt from the forbidden-string sweep."""
    parts = path.parts
    rel = path.relative_to(REPO_ROOT).as_posix()

    # The test file itself.
    if path.resolve() == Path(__file__).resolve():
        return True

    # Audit prompts, audit responses, and the maintainer's response
    # companion files. These exist to discuss the strings in question.
    name = path.name
    if name.startswith("codex_") and (
        "audit_prompt" in name
        or "audit_response" in name
        or "audit_response_response" in name
    ):
        return True

    # Historical plans (provenance only).
    if "hai/reporting/plans/historical" in rel:
        return True

    # Archived historical provenance (framing-v2, paper planning, release
    # history, project decisions, HAI docs from product era). All under
    # the top-level `ARCHIVE/` lane introduced 2026-05-15 in the repo
    # consolidation.
    if rel.startswith("ARCHIVE/") or "/ARCHIVE/" in rel:
        return True

    # Round-2 closeout artifacts that intentionally name the strings.
    if name in {
        "ROUND_2_CLOSEOUT.md",
        "codex_runtime_first_reframe_audit_response_round_2_response.md",
    }:
        return True

    # Memory files outside the repo (.claude/projects).
    if "/.claude/" in str(path):
        return True

    # Hidden directories (.git, .pytest_cache, etc.)
    if any(part.startswith(".") and part not in {".", ".."} for part in parts):
        return True

    return False


def _markdown_files() -> list[Path]:
    return sorted(
        p for p in REPO_ROOT.rglob("*.md") if not _allowed(p)
    )


# ---- F-CDX-RFR-R2-01: runtime-mode naming ---------------------------------


def test_no_double_enforcement_typo() -> None:
    """The round-2 typo `no_runtime_enforcement_enforcement` is banned.

    Allowed: lines that explicitly call the string a typo or eradicated
    (e.g., closeout prose in `project/DECISIONS.md` D-PROJ-018).
    """
    offenders: list[tuple[str, int, str]] = []
    for path in _markdown_files():
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            if "no_runtime_enforcement_enforcement" not in line:
                continue
            if _window_has_marker(
                lines,
                idx,
                ("typo", "eradicated", "eradicate", "is banned"),
                radius=2,
            ):
                continue
            offenders.append(
                (path.relative_to(REPO_ROOT).as_posix(), idx + 1, line.strip())
            )
    assert not offenders, (
        "no_runtime_enforcement_enforcement reintroduced in active docs:\n"
        + "\n".join(f"  {p}:{l}: {ln}" for p, l, ln in offenders)
    )


_RETIRED_BLOCK_HEADERS = (
    "forbidden",
    "retired",
    "anti-pattern",
    "anti-patterns",
    "round-2 reframe note",
    "do not do",
    "do not use",
    "explicitly out of scope",
    "round-2 corrected",
    "previously",
    "superseded",
)


def _line_in_retired_block(lines: list[str], idx: int) -> bool:
    """Return True if the line at `idx` is under a 'Forbidden' / 'Retired' /
    'Anti-pattern' / similar markdown header within ~30 lines back, with no
    intervening header that re-opens an active section.
    """
    for back in range(idx - 1, max(idx - 30, -1), -1):
        line = lines[back].strip().lower()
        if line.startswith("##") or line.startswith("**"):
            return any(marker in line for marker in _RETIRED_BLOCK_HEADERS)
        if line.startswith("- ") or line.startswith("* "):
            # bullet inside an existing block; keep walking
            continue
    return False


def _window_has_marker(
    lines: list[str], idx: int, markers: tuple[str, ...], radius: int = 3
) -> bool:
    """Return True if any marker appears in lines [idx-radius, idx+radius].

    The window is joined with single spaces (not newlines) so that markers
    can span line boundaries — e.g. "No `with_manifest`" on a line break is
    still recognised as the negative-context phrase "no `with_manifest`".
    """
    lo = max(0, idx - radius)
    hi = min(len(lines), idx + radius + 1)
    window = " ".join(lines[lo:hi]).lower()
    return any(marker in window for marker in markers)


_RENAME_MARKERS = (
    "renamed",
    "rename",
    "renames",
    "v1 token",
    "previously",
    "previously named",
    "instead of",
    "updated to",
    "old",
    "historical",
    "retired",
    "no longer",
    "v1 →",
    "v1 to v2",
    "round-2 reframe",
)


def test_no_bare_no_runtime_in_active_docs() -> None:
    """Bare `no_runtime` (the v1 token) is retired in v2.

    Allowed: `no_runtime_enforcement` (the v2 token), the rename
    callout, or `no_runtime` inside a code block that is explicitly
    tagged historical/retired.
    """
    bad_pattern = re.compile(r"\bno_runtime\b(?!_enforcement)")
    offenders: list[tuple[str, int, str]] = []
    for path in _markdown_files():
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            if not bad_pattern.search(line):
                continue
            if _window_has_marker(lines, idx, _RENAME_MARKERS, radius=3):
                continue
            if _line_in_retired_block(lines, idx):
                continue
            offenders.append(
                (path.relative_to(REPO_ROOT).as_posix(), idx + 1, line.strip())
            )
    assert not offenders, (
        "Bare `no_runtime` (v1 token) reintroduced in active docs:\n"
        + "\n".join(f"  {p}:{l}: {ln}" for p, l, ln in offenders)
    )


# ---- F-CDX-RFR-R2-02: prompt-axis residue --------------------------------


PROMPT_AXIS_FORBIDDEN = [
    "local_prompt_only",
    "cloud_prompt_only",
    "with_manifest",
    "without_manifest",
    "prompt-only baseline",
    "manifest-grounded prompting",
]


_PROMPT_AXIS_NEGATIVE_MARKERS = (
    "forbidden",
    "retired",
    "superseded",
    "no longer",
    "do not use",
    "are dropped",
    "are intentionally dropped",
    "are not a condition",
    "is not a condition",
    "no \"with",
    "no 'with",
    "no `with",
    "no with_manifest",
    "no without_manifest",
    "no `without",
    "specifically forbidden",
    "old prompt-axis",
    "old prompt-condition",
    "pre-reframe",
    "the old",
    "are retired",
    "is retired",
    "same as",
    "previously",
    "predates",
    "never use",
    "anti-pattern",
    "rename",
    "no `with_manifest` vs",
    "ablation in v1",
    "ablation. ",
    "is held constant",
    "prompt is held constant",
    "round-2 reframe",
    "no manifest withholding",
    "withholding the manifest",
    "sandbagged baseline",
    "returns no harness hits",
    "code search for",
)


@pytest.mark.parametrize("forbidden", PROMPT_AXIS_FORBIDDEN)
def test_no_prompt_axis_strings_in_active_docs(forbidden: str) -> None:
    """Prompt-axis condition strings must not appear in active docs.

    The headline experiment varies `runtime_mode`, not the prompt
    (D-PROJ-014). Strings that imply prompt-axis comparisons are
    forbidden outside audit prose, retired/forbidden callout blocks,
    and historical plans.
    """
    offenders: list[tuple[str, int, str]] = []
    for path in _markdown_files():
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            if forbidden not in line:
                continue
            if _window_has_marker(
                lines, idx, _PROMPT_AXIS_NEGATIVE_MARKERS, radius=3
            ):
                continue
            if _line_in_retired_block(lines, idx):
                continue
            offenders.append(
                (path.relative_to(REPO_ROOT).as_posix(), idx + 1, line.strip())
            )
    assert not offenders, (
        f"Prompt-axis forbidden string `{forbidden}` reintroduced in active docs:\n"
        + "\n".join(f"  {p}:{l}: {ln}" for p, l, ln in offenders)
    )
