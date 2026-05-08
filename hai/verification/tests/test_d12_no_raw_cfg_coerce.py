"""D12 invariant guard — no raw int/float/bool(cfg…) in the runtime.

Per AGENTS.md "Settled Decisions" (D12, v0.1.10): every threshold-
consumer in ``hai/src/health_agent_infra/`` must go through
``core.config.coerce_int / coerce_float / coerce_bool``. Bool-as-int
silent coercion (``True`` is an instance of ``int``) is the highest-
impact silent-bug class the project has hit, and W-A landed the
helpers specifically to close it.

The Codex implementation review for v0.1.10 (F-CDX-IR-02) caught
that the original W-A sweep missed several sites
(``synthesis_policy.py`` x4/x5/x6a/x6b, ``garmin_live.py`` retry
config). This test prevents that class of regression by failing
whenever a raw ``(int|float|bool)(cfg…)`` or ``(int|float|bool)
(thresholds…)`` call lands.

Tests that *intentionally* exercise the helper edge cases live in
``test_config_coerce.py``; they don't trip this guard because the
guard scans ``src/`` only.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


_RUNTIME_ROOT = Path(__file__).resolve().parents[2] / "src" / "health_agent_infra"

# Match patterns like ``int(cfg.get(...))``, ``float(cfg["x"])``,
# ``bool(thresholds.get(...))``. Word-boundary on the cast guards
# against matching ``coerce_int``, ``_as_int``, ``my_int``, etc.
_FORBIDDEN_PATTERN = re.compile(
    r"(?<![A-Za-z_])(?:int|float|bool)\((?:cfg|thresholds)\b"
)


def _python_files() -> list[Path]:
    return sorted(p for p in _RUNTIME_ROOT.rglob("*.py") if "__pycache__" not in p.parts)


def test_no_raw_cfg_threshold_coercion_in_runtime() -> None:
    """No ``(int|float|bool)(cfg…)`` or ``(int|float|bool)(thresholds…)``
    calls remain in the runtime tree. Use ``coerce_int`` /
    ``coerce_float`` / ``coerce_bool`` from ``core.config`` instead."""

    violations: list[str] = []
    for path in _python_files():
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _FORBIDDEN_PATTERN.search(line):
                rel = path.relative_to(_RUNTIME_ROOT.parents[1])
                violations.append(f"{rel}:{lineno}: {line.strip()}")

    if violations:
        pytest.fail(
            "D12 violation — raw int/float/bool(cfg…) or (thresholds…) "
            "calls found. Use core.config.coerce_int / coerce_float / "
            "coerce_bool. Sites:\n  " + "\n  ".join(violations)
        )
