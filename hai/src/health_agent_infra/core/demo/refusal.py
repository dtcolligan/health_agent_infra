"""Demo-mode refusal matrix (W-Va).

The cycle plan (PLAN.md § 2.14) enumerates four behaviour buckets
when a demo session is active:

- **Allowed** — runs against scratch state.
- **Refused — live network** — `hai pull` with non-csv source,
  `hai daily` with non-csv source or `--live`.
- **Refused — credentials/keyring** — `hai auth *`, `hai init
  --with-auth`, `hai init --with-first-pull`.
- **Refused — operator/installer** — `hai state init/migrate/
  reproject`, `hai setup-skills`, `hai config init`, `hai intent
  commit/archive`, `hai target commit/archive`.

Plus **cleanup-only** (`hai demo end`, `hai demo cleanup`) which
runs even when the marker is present-but-invalid (fail-closed
escape hatch).

This module owns the policy. The CLI entry point in
``cli.py:main`` consults :func:`evaluate_demo_refusal` after
identifying the subcommand and (if needed) inspecting flags.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RefusalDecision:
    """Outcome of consulting the demo refusal matrix.

    ``allowed = True``  → the command may run; the CLI emits the
                          banner and dispatches.
    ``allowed = False`` → the command is refused; ``reason`` is the
                          user-facing diagnostic and ``category`` is
                          one of "network", "credentials",
                          "operator". The CLI prints to stderr and
                          exits ``USER_INPUT``.
    """

    allowed: bool
    category: Optional[str] = None
    reason: Optional[str] = None


# Commands that can run even when the marker is present-but-invalid.
# These are the fail-closed escape hatches (Codex F-PLAN-03).
CLEANUP_ONLY_COMMANDS: frozenset[str] = frozenset({
    "demo_end",
    "demo_cleanup",
})


# Commands that should never be reached by the demo gate (they're
# pre-marker by definition).
DEMO_GATE_BYPASS: frozenset[str] = frozenset({
    "demo_start",
    "demo_end",
    "demo_cleanup",
    # capabilities is a read-only manifest emitter; safe in any mode.
    "capabilities",
})


# Refused — credentials / keyring. Demo mode never touches the
# keyring or runs auth flows.
_REFUSED_CREDENTIALS: frozenset[str] = frozenset({
    "auth_garmin",
    "auth_intervals_icu",
})


# Refused — operator / installer. State migration, skill installation,
# user-state activation/deactivation are not demo concerns.
_REFUSED_OPERATOR: frozenset[str] = frozenset({
    "state_init",
    "state_migrate",
    "state_reproject",
    "setup_skills",
    "config_init",
    "intent_commit",
    "intent_archive",
    "target_commit",
    "target_archive",
})


def evaluate_demo_refusal(
    command_id: str,
    args: argparse.Namespace,
) -> RefusalDecision:
    """Return the refusal decision for a (command, args) pair under demo mode.

    Args:
        command_id: handler name with ``cmd_`` stripped (e.g. ``"pull"``,
            ``"auth_garmin"``, ``"daily"``). Convention: each
            argparse subparser's ``set_defaults(func=cmd_X)`` is the
            source.
        args: the parsed ``argparse.Namespace``. Inspected for
            flag-dependent decisions (e.g. ``--source`` on pull / daily).

    Returns:
        :class:`RefusalDecision`. The CLI honours it.
    """

    if command_id in DEMO_GATE_BYPASS:
        return RefusalDecision(allowed=True)

    if command_id in _REFUSED_CREDENTIALS:
        return RefusalDecision(
            allowed=False,
            category="credentials",
            reason=(
                f"hai {command_id.replace('_', ' ')} touches the OS keyring "
                f"and is refused while a demo session is active. Run "
                f"'hai demo end' first if you need to manage real credentials."
            ),
        )

    if command_id in _REFUSED_OPERATOR:
        return RefusalDecision(
            allowed=False,
            category="operator",
            reason=(
                f"hai {command_id.replace('_', ' ')} is an operator/installer "
                f"command and is refused while a demo session is active. "
                f"It would mutate real state outside the demo scratch root."
            ),
        )

    # Flag-dependent refusals.
    if command_id == "pull":
        return _evaluate_pull(args)
    if command_id == "daily":
        return _evaluate_daily(args)
    if command_id == "doctor":
        return _evaluate_doctor(args)
    if command_id == "init":
        return _evaluate_init(args)

    # Default: allow. Every read/intake/propose/explain/state-read/
    # memory/list-style command falls through here and runs against
    # the scratch resolvers.
    return RefusalDecision(allowed=True)


def _evaluate_pull(args: argparse.Namespace) -> RefusalDecision:
    """`hai pull` — live sources refused; csv allowed."""
    source = getattr(args, "source", None)
    live = getattr(args, "live", False)
    if live or (source is not None and source != "csv"):
        chosen = "garmin_live" if live else source
        return RefusalDecision(
            allowed=False,
            category="network",
            reason=(
                f"hai pull --source {chosen} is a live network call "
                f"and is refused while a demo session is active. "
                f"Use --source csv (or omit --live) to pull from the "
                f"committed fixture against the scratch DB."
            ),
        )
    return RefusalDecision(allowed=True)


def _evaluate_daily(args: argparse.Namespace) -> RefusalDecision:
    """`hai daily` — live sources refused (same shape as pull)."""
    source = getattr(args, "source", None)
    live = getattr(args, "live", False)
    skip_pull = getattr(args, "skip_pull", False)
    if skip_pull:
        # Skip-pull never goes near the network; allow regardless of source.
        return RefusalDecision(allowed=True)
    if live or (source is not None and source != "csv"):
        chosen = "garmin_live" if live else source
        return RefusalDecision(
            allowed=False,
            category="network",
            reason=(
                f"hai daily --source {chosen} is a live network call "
                f"and is refused while a demo session is active. "
                f"Use --source csv or pass --skip-pull."
            ),
        )
    return RefusalDecision(allowed=True)


def _evaluate_doctor(args: argparse.Namespace) -> RefusalDecision:
    """`hai doctor` — `--deep` allowed only via FixtureProbe (W-X).

    W-Va note: the FixtureProbe path is W-X scope. In the meantime,
    ``--deep`` falls back to LiveProbe in real mode and is allowed
    in demo mode (behaviour: doctor surface returns ok-credentials-
    present without performing a real network call once W-X lands).
    Until W-X lands, allow ``--deep`` in demo mode and let the
    underlying probe code decide; the W-X commit will switch the
    probe surface to FixtureProbe under a demo marker.
    """
    return RefusalDecision(allowed=True)


def _evaluate_init(args: argparse.Namespace) -> RefusalDecision:
    """`hai init` — `--with-auth` / `--with-first-pull` refused."""
    if getattr(args, "with_auth", False):
        return RefusalDecision(
            allowed=False,
            category="credentials",
            reason=(
                "hai init --with-auth opens an interactive credential "
                "prompt and is refused while a demo session is active."
            ),
        )
    if getattr(args, "with_first_pull", False):
        return RefusalDecision(
            allowed=False,
            category="network",
            reason=(
                "hai init --with-first-pull triggers a live wearable "
                "fetch and is refused while a demo session is active."
            ),
        )
    return RefusalDecision(allowed=True)
