"""W-AD (v0.1.13) — every USER_INPUT exit site carries actionable next-step prose.

Contract: every `return exit_codes.USER_INPUT` in cli.py must be
preceded by a `print(..., file=sys.stderr)` whose message contains at
least one **actionable verb** (run / set / remove / check / edit /
retry / etc.). The user who hits a USER_INPUT exit must learn what
they could have done differently.

This test scans cli.py source AST-level, finds every USER_INPUT exit
return, and inspects the same function's preceding stderr prints.
A site that returns USER_INPUT without an accompanying actionable
message in the same function fails — merge-blocking.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


_CLI_PATH = (
    Path(__file__).resolve().parents[2]
    / "src" / "health_agent_infra" / "cli.py"
)


# Verbs that count as "actionable next-step." If a stderr print mentions
# any of these, we accept the site as user-actionable. Phrasings like
# "must be" / "should be" are weaker — we keep them OFF this list so
# the test stays sharp.
_ACTIONABLE_VERB_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(rf"\b{verb}\b", re.IGNORECASE)
    for verb in (
        "run",
        "set",
        "remove",
        "check",
        "edit",
        "retry",
        "use",
        "pass",
        "supply",
        "provide",
        "configure",
        "regenerate",
        "rerun",
        "see",
        "specify",
        "add",
        "delete",
        "replace",
        "update",
        "fix",
        "install",
        "verify",
        "review",
        "create",
        "init",
        "migrate",
        "clear",
        "reset",
        "drop",
        "rename",
        "rebuild",
        "reauthenticate",
        "reauth",
        "consult",
        "follow",
        "import",
        "bump",
        "load",
    )
)


def _has_actionable_verb(text: str) -> bool:
    return any(p.search(text) for p in _ACTIONABLE_VERB_PATTERNS)


def _extract_string_literals(node: ast.AST) -> list[str]:
    """Recursively collect every string literal under `node`. Includes
    Constant strings, joined parts of f-strings, and concatenated
    multi-line string literals."""

    out: list[str] = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            out.append(sub.value)
        elif isinstance(sub, ast.JoinedStr):
            for v in sub.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    out.append(v.value)
    return out


def _is_print_to_stderr(call: ast.Call) -> bool:
    """`print(..., file=sys.stderr)` OR `sys.stderr.write(...)` detection.

    cli.py uses both idioms — print is more common but several handlers
    use stderr.write directly (often when the message is multi-line or
    constructed via concat).
    """

    # `print(..., file=sys.stderr)`
    if isinstance(call.func, ast.Name) and call.func.id == "print":
        for kw in call.keywords:
            if kw.arg != "file":
                continue
            v = kw.value
            if (
                isinstance(v, ast.Attribute)
                and v.attr == "stderr"
                and isinstance(v.value, ast.Name)
                and v.value.id == "sys"
            ):
                return True
        return False

    # `sys.stderr.write(...)`
    if isinstance(call.func, ast.Attribute):
        a = call.func
        if (
            a.attr == "write"
            and isinstance(a.value, ast.Attribute)
            and a.value.attr == "stderr"
            and isinstance(a.value.value, ast.Name)
            and a.value.value.id == "sys"
        ):
            return True
    return False


def _collect_user_input_exit_sites(tree: ast.Module) -> list[tuple[ast.FunctionDef, ast.Return]]:
    """Find every `return exit_codes.USER_INPUT` and the enclosing function."""

    sites: list[tuple[ast.FunctionDef, ast.Return]] = []
    for func in ast.walk(tree):
        if not isinstance(func, ast.FunctionDef):
            continue
        for node in ast.walk(func):
            if not isinstance(node, ast.Return) or node.value is None:
                continue
            v = node.value
            # Pattern: `exit_codes.USER_INPUT`
            if (
                isinstance(v, ast.Attribute)
                and v.attr == "USER_INPUT"
                and isinstance(v.value, ast.Name)
                and v.value.id == "exit_codes"
            ):
                sites.append((func, node))
    return sites


def _function_stderr_messages(func: ast.FunctionDef) -> list[str]:
    """Extract every literal that gets passed to `print(..., file=sys.stderr)`
    inside `func`. Returns concatenated strings per print call."""

    msgs: list[str] = []
    for node in ast.walk(func):
        if isinstance(node, ast.Call) and _is_print_to_stderr(node):
            literals = []
            for arg in node.args:
                literals.extend(_extract_string_literals(arg))
            if literals:
                msgs.append(" ".join(literals))
    return msgs


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------


def test_cli_py_has_user_input_exit_sites():
    """Sanity: the audit surface is non-empty. If this fails, the
    grep / AST visitor changed and the rest of the test is meaningless."""

    tree = ast.parse(_CLI_PATH.read_text(encoding="utf-8"))
    sites = _collect_user_input_exit_sites(tree)
    assert len(sites) >= 100, f"only found {len(sites)} USER_INPUT sites"


# ---------------------------------------------------------------------------
# The contract
# ---------------------------------------------------------------------------


def test_every_user_input_exit_site_has_actionable_prose_in_function():
    """Every USER_INPUT exit must have at least one stderr print in the
    same function that includes an actionable verb. The grep is at
    function granularity (not statement-level proximity) because cli
    handlers commonly compose: validate-then-explain-then-exit."""

    tree = ast.parse(_CLI_PATH.read_text(encoding="utf-8"))
    sites = _collect_user_input_exit_sites(tree)

    failures: list[str] = []
    seen_funcs: set[str] = set()
    for func, ret_node in sites:
        if func.name in seen_funcs:
            # We only need to fail once per function; the prose
            # surface is per-function.
            continue
        seen_funcs.add(func.name)

        msgs = _function_stderr_messages(func)
        if not msgs:
            failures.append(
                f"{func.name} (line {func.lineno}): no stderr print at all "
                f"despite {sum(1 for f, _ in sites if f.name == func.name)} "
                f"USER_INPUT exit(s)"
            )
            continue
        if not any(_has_actionable_verb(m) for m in msgs):
            failures.append(
                f"{func.name} (line {func.lineno}): no actionable verb in "
                f"stderr prose; messages: {[m[:80] for m in msgs[:3]]}"
            )

    if failures:
        pytest.fail(
            f"W-AD: {len(failures)} cli.py handler(s) emit USER_INPUT "
            f"without actionable next-step prose:\n"
            + "\n".join(f"  - {f}" for f in failures[:15])
            + (f"\n  ... ({len(failures) - 15} more)" if len(failures) > 15 else "")
        )
