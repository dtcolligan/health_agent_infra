"""W-D13-SYM contract: every threshold read in domain ``policy.py`` files
must go through a ``coerce_*`` helper.

Origin: v0.1.12 W-D13-SYM (PLAN.md §2.6); reconciliation L1.

The threshold-injection seam (D13, AGENTS.md) is defended at *load
time* by ``core.config._validate_threshold_types`` — that catches the
common case where a user TOML supplies ``True`` for what should be an
int. But a future caller that constructs threshold dicts in-memory
and bypasses ``load_thresholds`` would silently coerce bool-as-int at
the consumer site unless the consumer site itself routes the read
through ``coerce_*``.

This test asserts the consumer-site defence is uniform across all six
domains. v0.1.11 ship had strength + nutrition correct;
recovery + running + sleep + stress reading raw. v0.1.12 W-D13-SYM
fixed the four asymmetric domains; this test prevents recurrence.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

DOMAINS_DIR = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "health_agent_infra"
    / "domains"
)
POLICY_FILES = sorted(DOMAINS_DIR.glob("*/policy.py"))


def _is_coerce_call(node: ast.AST) -> bool:
    """True if `node` is a ``coerce_int(...)`` / ``coerce_float(...)`` /
    ``coerce_bool(...)`` call expression."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in {"coerce_int", "coerce_float", "coerce_bool"}
    if isinstance(func, ast.Attribute):
        return func.attr in {"coerce_int", "coerce_float", "coerce_bool"}
    return False


def _is_policy_subscript(node: ast.AST) -> bool:
    """True if `node` is a ``t["policy"][...]...`` chain — i.e. any
    Subscript whose root traverses through the literal ``"policy"``
    key on a Name/Subscript chain."""
    if not isinstance(node, ast.Subscript):
        return False
    cursor: ast.AST = node
    while isinstance(cursor, ast.Subscript):
        slc = cursor.slice
        if (
            isinstance(slc, ast.Constant)
            and isinstance(slc.value, str)
            and slc.value == "policy"
        ):
            return True
        cursor = cursor.value
    return False


def _has_uncoerced_policy_reads(tree: ast.AST) -> list[tuple[int, str]]:
    """Return [(lineno, source-snippet)] for every ``t["policy"][...]``
    read that is *not* the immediate argument of a ``coerce_*`` call.

    "Immediate argument" means: the policy subscript IS one of the call's
    positional args. A read assigned to a variable and then *manually*
    coerce-wrapped elsewhere is allowed (the call still exists), but a
    read that is consumed directly without any coerce wrapping is the
    bug we're catching.
    """

    coerced_ids: set[int] = set()
    for node in ast.walk(tree):
        if _is_coerce_call(node):
            for arg in node.args:
                if _is_policy_subscript(arg):
                    coerced_ids.add(id(arg))

    flagged: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not _is_policy_subscript(node):
            continue
        if id(node) in coerced_ids:
            continue
        # Allow reads that just bind a sub-dict for downstream coerce
        # calls (e.g. `cfg = t["policy"]["nutrition"]` followed by
        # `coerce_float(cfg[...])`). We detect this by checking whether
        # the subscript chain ends at the *first* "policy" hop without
        # selecting a leaf threshold key. A leaf-key read like
        # `t["policy"]["recovery"]["r6_..."]` chains 3 deep; a sub-dict
        # bind chains 2 deep.
        depth = 0
        cursor: ast.AST = node
        while isinstance(cursor, ast.Subscript):
            depth += 1
            cursor = cursor.value
        if depth <= 2:
            # Sub-dict binding, not a leaf threshold read.
            continue
        flagged.append((node.lineno, ast.unparse(node)))
    return flagged


@pytest.mark.parametrize(
    "policy_file",
    POLICY_FILES,
    ids=lambda p: p.parent.name,
)
def test_domain_policy_threshold_reads_use_coerce(policy_file: Path) -> None:
    """Every leaf ``t["policy"][<domain>][<key>]`` read in a domain
    ``policy.py`` must be the immediate argument of a ``coerce_*``
    helper call.

    Closes reconciliation L1 (v0.1.12 W-D13-SYM) and is the standing
    contract that protects the D13 threshold-injection seam at the
    consumer site.
    """
    tree = ast.parse(policy_file.read_text(encoding="utf-8"))
    flagged = _has_uncoerced_policy_reads(tree)
    assert not flagged, (
        f"{policy_file.relative_to(DOMAINS_DIR.parents[2])} has "
        f"{len(flagged)} threshold read(s) that bypass `coerce_*`:\n"
        + "\n".join(f"  line {ln}: {src}" for ln, src in flagged)
        + "\n\nWrap each in `coerce_int(...)`, `coerce_float(...)`, or "
        "`coerce_bool(...)` per the strength/nutrition pattern. "
        "See domains/strength/policy.py for the canonical shape."
    )


def test_all_six_domains_present() -> None:
    """Sanity: the contract must cover every shipped domain. A 7th-domain
    expansion that forgets a `policy.py` would silently bypass this test
    parametrisation otherwise."""
    found = {p.parent.name for p in POLICY_FILES}
    expected = {"recovery", "running", "sleep", "strength", "stress", "nutrition"}
    assert found == expected, (
        f"Expected exactly {expected} domain policy.py files; "
        f"found {found}. New domain or removed domain — update this "
        f"contract test if intentional."
    )
