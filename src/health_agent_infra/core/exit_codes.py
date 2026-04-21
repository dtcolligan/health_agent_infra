"""CLI exit-code taxonomy.

A small, frozen classification so agents and shell callers can react to
non-zero exits programmatically without parsing stderr.

Five codes. They cover the four failure classes the CLI actually
distinguishes plus the success case:

- ``OK`` (0) — the command completed as intended.
- ``USER_INPUT`` (1) — the invocation itself was wrong: missing or
  conflicting flags, unreadable user-supplied JSON, missing credentials
  the caller was expected to provide, or a state precondition the caller
  controls (``hai state init`` hasn't been run yet).
- ``TRANSIENT`` (2) — an external dependency failed in a way a retry
  might fix: a vendor 5xx, a rate limit, a network blip. The caller can
  back off and try again.
- ``NOT_FOUND`` (3) — the target identifier is well-formed but the
  runtime has no record of it. Most often: an unknown ``daily_plan_id``.
- ``INTERNAL`` (4) — a runtime invariant tripped that should not be
  reachable from normal inputs (e.g. a Phase B rule with a missing
  target registry entry). Indicates a bug, not a caller error.

TRANSIENT keeps its historical value of ``2`` deliberately. Every prior
caller that treated "non-zero" as "retry" kept working when we moved
user-input errors down to ``1`` and transient errors stayed at ``2``;
shifting TRANSIENT would have broken those retry loops.

Migration scope is documented in
``reporting/docs/cli_exit_codes.md`` — only a handful of handlers are
on the taxonomy as of M1; the rest still return the legacy mix of ``0``
and ``2`` until their follow-up PRs land.
"""

from __future__ import annotations

from typing import Final


OK: Final[int] = 0
USER_INPUT: Final[int] = 1
TRANSIENT: Final[int] = 2
NOT_FOUND: Final[int] = 3
INTERNAL: Final[int] = 4
