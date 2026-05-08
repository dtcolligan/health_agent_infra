"""Persona-driven dogfood harness.

Permanent regression infrastructure for `health_agent_infra`. Each
persona module under ``personas/`` builds a synthetic user shape and
drives the `hai` pipeline against an isolated state DB. The harness
exists to surface classifier-assumption bugs that single-user dogfood
flows cannot.

See ``reporting/plans/v0_1_10/PRE_AUDIT_PLAN.md`` § 5 for the design.

Isolation invariants:
    - Each persona uses ``/tmp/hai_persona_<id>.db`` as its state DB.
    - The harness never reads or writes the maintainer's real state DB.
    - Subprocess invocations of ``hai`` always pass ``HAI_STATE_DB``
      explicitly via env so a misconfigured local default cannot leak.
"""

from __future__ import annotations
