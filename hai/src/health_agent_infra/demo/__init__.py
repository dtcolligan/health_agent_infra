"""Packaged demo data — fixtures consumed by ``hai demo start --persona``.

Origin: v0.1.12 W-Vb (PLAN.md §2.3); reconciliation C3.

The fixture data lives **inside the wheel**, not under
``verification/dogfood/`` — the latter is repo-only and not present in
a clean ``pip install health-agent-infra`` install. This package is
the one the CLI imports at runtime.

The end-to-end persona-replay flow (``hai demo start --persona p1``
seeds proposals so ``hai daily`` reaches synthesis) is **deferred to
v0.1.13** per the v0.1.12 W-Vb partial-closure scope. v0.1.12 ships
the packaging path + loader + skeleton fixture for one persona; the
v0.1.13 cycle authors the full per-persona DomainProposal sets.
"""

from __future__ import annotations
