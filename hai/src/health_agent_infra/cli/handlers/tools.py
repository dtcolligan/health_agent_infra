"""``hai tools`` group — admin / demo / research / exercise / memory / planned-session-types.

Owns: ``hai memory set/list/archive``, ``hai exercise search``,
``hai research topics/search``, ``hai planned-session-types``,
``hai demo start/end/cleanup``. Plus the demo-mode gate ``_demo_gate``
and memory-private helpers ``_memory_id_for`` / ``_memory_entry_to_dict`` /
``_memory_counts``.

W-29.2.6 split: extracted from cli/__init__.py 5 fragmented ranges
(memory cluster 1853-2112, exercise_search 3662-3743, research+planned
5803-5866, demo 5895-5992, _demo_gate 8447-8518). The fragmented
layout reflects the file's organic accretion; tools.py consolidates
them under one operator-mode-tool roof per v0.1.13 boundary table §11.

Cross-handler imports: ``_emit_json``, ``_load_json_arg``, ``_coerce_dt``,
``_intent_open_db``, ``_w57_user_gate``, ``_derive_command_id``,
``DEFAULT_CLAUDE_SKILLS_DIR`` lazy-imported at call time from
health_agent_infra.cli to avoid module-load circularity (some symbols
are defined later in cli/__init__.py).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import uuid
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

from health_agent_infra.core import exit_codes
from health_agent_infra.core.paths import resolve_base_dir

# `_emit_json` is defined in cli/__init__.py before line ~1853; partial-module
# import resolves cleanly at module-load time.
from health_agent_infra.cli import _emit_json  # noqa: E402


def _memory_id_for(
    *,
    user_id: str,
    category: str,
    now: datetime,
) -> str:
    """Deterministic, sortable memory id: ``umem_<user>_<category>_<ts>``.

    Uses microsecond resolution so rapid reruns from a test or script
    don't collide. Callers may pass ``--memory-id`` to override for
    scripted reruns that want replay-idempotency.
    """

    suffix = now.strftime("%Y%m%dT%H%M%S%f")
    return f"umem_{user_id}_{category}_{suffix}"


def cmd_memory_set(args: argparse.Namespace) -> int:
    """Append one user-memory entry (goal / preference / constraint / context).

    Always inserts a fresh row — to change a preference the operator
    runs ``archive`` on the old entry and ``set`` for the replacement.
    This keeps the write surface honest: every change is visible as a
    distinct row + archive timestamp, no silent overwrites.
    """

    from health_agent_infra.core.memory import (
        UserMemoryEntry,
        UserMemoryValidationError,
        insert_memory_entry,
        validate_category,
    )
    from health_agent_infra.core.memory.schemas import (
        validate_domain,
        validate_value,
    )
    from health_agent_infra.core.state import open_connection, resolve_db_path

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"hai memory set requires an initialized state DB; not found "
            f"at {db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    try:
        category = validate_category(args.category)
        validate_value(args.value)
        domain = validate_domain(args.domain)
    except UserMemoryValidationError as exc:
        print(
            f"hai memory set rejected: invariant={exc.invariant}: {exc}",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    now = datetime.now(timezone.utc)
    memory_id = args.memory_id or _memory_id_for(
        user_id=args.user_id, category=category, now=now,
    )
    entry = UserMemoryEntry(
        memory_id=memory_id,
        user_id=args.user_id,
        category=category,
        value=args.value,
        key=args.key,
        domain=domain,
        created_at=now,
        archived_at=None,
        source=args.source,
        ingest_actor=args.ingest_actor,
    )

    conn = open_connection(db_path)
    try:
        inserted = insert_memory_entry(conn, entry)
    finally:
        conn.close()

    _emit_json({
        "inserted": inserted,
        "memory_id": entry.memory_id,
        "user_id": entry.user_id,
        "category": entry.category,
        "key": entry.key,
        "value": entry.value,
        "domain": entry.domain,
        "created_at": entry.created_at.isoformat(),
        "archived_at": None,
        "source": entry.source,
        "ingest_actor": entry.ingest_actor,
    })
    return exit_codes.OK


def cmd_memory_list(args: argparse.Namespace) -> int:
    """List user-memory entries, optionally filtered by user / category.

    Emits a JSON object with ``entries`` (array) + ``counts`` (category
    totals). The default excludes archived rows; ``--include-archived``
    returns everything so an operator can audit their own memory
    history.
    """

    from health_agent_infra.core.memory import (
        UserMemoryValidationError,
        build_user_memory_bundle,
        list_memory_entries,
    )
    from health_agent_infra.core.memory.projector import bundle_to_dict
    from health_agent_infra.core.state import open_connection, resolve_db_path

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"hai memory list requires an initialized state DB; not found "
            f"at {db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    conn = open_connection(db_path)
    try:
        try:
            if args.include_archived or args.category:
                # Raw list surface — supports category filter + archived.
                entries = list_memory_entries(
                    conn,
                    user_id=args.user_id,
                    category=args.category,
                    include_archived=args.include_archived,
                )
                payload = {
                    "user_id": args.user_id,
                    "category": args.category,
                    "include_archived": args.include_archived,
                    "entries": [_memory_entry_to_dict(e) for e in entries],
                    "counts": _memory_counts(entries),
                }
            else:
                # Default: active-now bundle. Matches the snapshot /
                # explain shape so the same consumer code can parse
                # both outputs.
                if args.user_id is None:
                    # Bundle surface needs a user_id; without it, fall
                    # back to the raw list with no filter.
                    entries = list_memory_entries(
                        conn, user_id=None, include_archived=False,
                    )
                    payload = {
                        "user_id": None,
                        "category": None,
                        "include_archived": False,
                        "entries": [_memory_entry_to_dict(e) for e in entries],
                        "counts": _memory_counts(entries),
                    }
                else:
                    bundle = build_user_memory_bundle(
                        conn, user_id=args.user_id, as_of=None,
                    )
                    payload = {
                        "user_id": args.user_id,
                        "category": None,
                        "include_archived": False,
                        **bundle_to_dict(bundle),
                    }
        except UserMemoryValidationError as exc:
            print(
                f"hai memory list rejected: invariant={exc.invariant}: {exc}",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
    finally:
        conn.close()

    _emit_json(payload)
    return exit_codes.OK


def cmd_memory_archive(args: argparse.Namespace) -> int:
    """Soft-delete a user-memory entry by stamping ``archived_at``.

    Exits 2 when ``--memory-id`` is unknown. Re-archiving an already-
    archived entry is a no-op (returns ``archived=False``) — the CLI
    reports this honestly instead of erroring, since the desired end
    state is already satisfied.
    """

    from health_agent_infra.core.memory import (
        archive_memory_entry,
        read_memory_entry,
    )
    from health_agent_infra.core.state import open_connection, resolve_db_path

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"hai memory archive requires an initialized state DB; not "
            f"found at {db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    conn = open_connection(db_path)
    try:
        existing = read_memory_entry(conn, memory_id=args.memory_id)
        if existing is None:
            print(
                f"hai memory archive: no entry with memory_id="
                f"{args.memory_id!r}",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
        archived = archive_memory_entry(conn, memory_id=args.memory_id)
        refreshed = read_memory_entry(conn, memory_id=args.memory_id)
    finally:
        conn.close()

    payload = {
        "archived": archived,
        "memory_id": args.memory_id,
    }
    if refreshed is not None:
        payload["archived_at"] = (
            refreshed.archived_at.isoformat()
            if refreshed.archived_at else None
        )
    _emit_json(payload)
    return exit_codes.OK


def _memory_entry_to_dict(entry) -> dict[str, Any]:
    return {
        "memory_id": entry.memory_id,
        "user_id": entry.user_id,
        "category": entry.category,
        "key": entry.key,
        "value": entry.value,
        "domain": entry.domain,
        "created_at": entry.created_at.isoformat(),
        "archived_at": (
            entry.archived_at.isoformat() if entry.archived_at else None
        ),
        "source": entry.source,
        "ingest_actor": entry.ingest_actor,
    }


def _memory_counts(entries) -> dict[str, int]:
    from health_agent_infra.core.memory.schemas import USER_MEMORY_CATEGORIES

    # mypy v0.1.12 W-H2: widen to dict[str, int] explicitly so the
    # synthetic "total" key doesn't trip the Literal-keyed inference.
    out: dict[str, int] = {category: 0 for category in USER_MEMORY_CATEGORIES}
    for entry in entries:
        out[entry.category] = out.get(entry.category, 0) + 1
    out["total"] = len(entries)
    return out


def cmd_exercise_search(args: argparse.Namespace) -> int:
    """Rank top taxonomy hits for a free-text exercise name.

    Code-owned ranking + scoring (see
    ``domains.strength.taxonomy_match``). The strength-intake skill
    calls this CLI when it needs to disambiguate a user-supplied
    exercise reference; the CLI surface never evaluates heuristics in
    markdown.

    Output shape::

        {
            "query": "<input>",
            "hits": [
                {
                    "exercise_id": "back_squat",
                    "canonical_name": "Back Squat",
                    "aliases": ["back squat", "squat", ...],
                    "primary_muscle_group": "quads",
                    "secondary_muscle_groups": ["glutes", "core"],
                    "category": "compound",
                    "equipment": "barbell",
                    "score": 100,
                    "match_reason": "exact_canonical"
                },
                ...
            ]
        }
    """

    from health_agent_infra.core.state import open_connection, resolve_db_path
    from health_agent_infra.domains.strength.taxonomy_match import (
        search_exercises,
    )

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"state DB not found at {db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    conn = open_connection(db_path)
    try:
        hits = search_exercises(args.query, conn=conn, limit=args.limit)
    finally:
        conn.close()

    _emit_json({
        "query": args.query,
        "hits": [
            {
                "exercise_id": h.exercise_id,
                "canonical_name": h.canonical_name,
                "aliases": list(h.aliases),
                "primary_muscle_group": h.primary_muscle_group,
                "secondary_muscle_groups": list(h.secondary_muscle_groups),
                "category": h.category,
                "equipment": h.equipment,
                "score": h.score,
                "match_reason": h.match_reason,
            }
            for h in hits
        ],
    })
    return exit_codes.OK


# ---------------------------------------------------------------------------
# hai daily — one-shot morning orchestration of the real runtime
# ---------------------------------------------------------------------------

# Six v1 domains. Kept in lockstep with
# ``core.writeback.proposal.SUPPORTED_DOMAINS``; duplicated here only so the
# CLI can validate the ``--domains`` flag without importing proposal.py at
# module import time (other subcommands resolve validator state lazily).
_DAILY_SUPPORTED_DOMAINS: frozenset[str] = frozenset({
    "recovery", "running", "sleep", "stress", "strength", "nutrition",
})




def cmd_research_topics(args: argparse.Namespace) -> int:
    """List the allowlisted research topics. Read-only, agent-safe."""

    from health_agent_infra.core.research import ALLOWLISTED_TOPICS

    _emit_json({"topics": sorted(ALLOWLISTED_TOPICS)})
    return exit_codes.OK


def cmd_research_search(args: argparse.Namespace) -> int:
    """Retrieve sources for one allowlisted topic. Read-only,
    agent-safe, no network. Mirrors :func:`retrieve` but exposes
    only the topic-token interface — never accepts user state, never
    flips the privacy-violation booleans."""

    from health_agent_infra.core.research import (
        RetrievalQuery,
        retrieve,
    )

    query = RetrievalQuery(topic=args.topic)
    result = retrieve(query)
    payload = {
        "topic": result.topic,
        "abstain_reason": result.abstain_reason,
        "sources": [
            {
                "source_id": s.source_id,
                "title": s.title,
                "source_class": s.source_class,
                "origin_path": s.origin_path,
                "excerpt": s.excerpt,
            }
            for s in result.sources
        ],
    }
    _emit_json(payload)
    return exit_codes.OK


# ---------------------------------------------------------------------------
# hai planned-session-types (v0.1.7 W33)
# ---------------------------------------------------------------------------
# Read-only surface that exposes the canonical planned_session_type
# vocabulary an agent / user should pass to `hai intake readiness
# --planned-session-type`. The list is documentation, not enforcement —
# per-domain classifiers do substring matching — but having a
# machine-discoverable canonical set lets agents avoid free-text drift.


def cmd_planned_session_types(args: argparse.Namespace) -> int:
    from health_agent_infra.core.intake.planned_session_vocabulary import (
        vocabulary_payload,
    )

    _emit_json(vocabulary_payload())
    return exit_codes.OK


# ---------------------------------------------------------------------------
# hai capabilities — emit the agent contract manifest
# ---------------------------------------------------------------------------




def cmd_demo_start(args: argparse.Namespace) -> int:
    """Open a new demo session.

    Refuses with USER_INPUT if a session is already active. Creates
    a scratch root, writes a marker, and prints the marker payload
    as JSON for the agent / user to confirm.
    """
    from health_agent_infra.core.demo.session import (
        DemoMarkerError,
        open_session,
    )

    persona: Optional[str]
    if getattr(args, "blank", False):
        persona = None
    else:
        persona = getattr(args, "persona", None)

    try:
        marker = open_session(persona=persona)
    except DemoMarkerError as exc:
        print(
            f"hai demo start: {exc}\n"
            f"If a stale demo session is active, run `hai demo end` "
            f"first; if the marker is corrupt, run `hai demo cleanup`.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    print(
        f"[demo session opened — marker_id {marker.marker_id}, "
        f"scratch root {marker.scratch_root}]",
        file=sys.stderr,
    )
    _emit_json({
        "status": "started",
        **marker.to_dict(),
    })
    return exit_codes.OK


def cmd_demo_end(args: argparse.Namespace) -> int:
    """Close the active demo session.

    Removes the marker file. Idempotent: closing when no session is
    active is a successful no-op. v0.1.11 W-Va leaves the scratch
    root on disk; W-Vb adds archive-on-end.
    """
    from health_agent_infra.core.demo.session import close_session

    marker = close_session()
    if marker is None:
        print("hai demo end: no active demo session to close.", file=sys.stderr)
        _emit_json({"status": "no_session"})
        return exit_codes.OK

    print(
        f"[demo session closed — marker_id {marker.marker_id}, "
        f"scratch root {marker.scratch_root} (left on disk; "
        f"W-Vb will add archive-on-end)]",
        file=sys.stderr,
    )
    _emit_json({
        "status": "closed",
        "marker_id": marker.marker_id,
        "scratch_root": str(marker.scratch_root),
    })
    return exit_codes.OK


def cmd_demo_cleanup(args: argparse.Namespace) -> int:
    """Remove orphan/corrupt demo markers (safety net).

    Allowed even when the marker is present-but-invalid (fail-closed
    escape hatch per Codex F-PLAN-03). Returns the marker_ids
    cleaned (or empty list if no orphan found).
    """
    from health_agent_infra.core.demo.session import cleanup_orphans

    cleaned = cleanup_orphans()
    if not cleaned:
        print(
            "hai demo cleanup: no orphan markers found.",
            file=sys.stderr,
        )
    else:
        print(
            f"hai demo cleanup: removed {len(cleaned)} marker(s): "
            f"{', '.join(cleaned)}",
            file=sys.stderr,
        )
    _emit_json({
        "status": "cleaned",
        "removed_marker_ids": cleaned,
    })
    return exit_codes.OK




def _demo_gate(args: argparse.Namespace) -> Optional[int]:
    """Demo-mode gate (W-Va).

    Returns ``None`` when the command may proceed; an exit-code int
    when the command is refused or the marker is invalid. Emits the
    stderr banner on the proceed path when a demo is active.
    """

    from health_agent_infra.core.demo.session import (
        DemoMarkerError,
        require_valid_marker_or_refuse,
    )
    from health_agent_infra.core.demo.refusal import (
        CLEANUP_ONLY_COMMANDS,
        evaluate_demo_refusal,
    )
    from health_agent_infra.cli import _derive_command_id

    command_id = _derive_command_id(args.func)

    # Cleanup-only commands run regardless of marker validity (the
    # fail-closed escape hatch). They handle the marker themselves.
    if command_id in CLEANUP_ONLY_COMMANDS:
        return None

    # Validate the marker. Fail-closed: an invalid marker refuses
    # every command except the cleanup pair above.
    try:
        marker = require_valid_marker_or_refuse()
    except DemoMarkerError as exc:
        print(f"hai: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT

    # No marker → normal mode. Skip the gate.
    if marker is None:
        return None

    # Marker is valid. Consult the refusal matrix.
    decision = evaluate_demo_refusal(command_id, args)
    if not decision.allowed:
        print(
            f"hai: refused under demo session [{decision.category}]: "
            f"{decision.reason}",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    # Allowed. Emit the banner once before the handler runs.
    persona_label = marker.persona if marker.persona else "unpopulated"
    print(
        f"[demo session active — marker_id {marker.marker_id}, "
        f"scratch root {marker.scratch_root}, persona: {persona_label}, "
        f"started: {marker.started_at}]",
        file=sys.stderr,
    )

    # Stale-session surfacing (>24h since started_at).
    try:
        from datetime import datetime as _dt
        started = _dt.fromisoformat(marker.started_at)
        delta = _dt.now(timezone.utc) - started
        if delta.total_seconds() > 24 * 3600:
            print(
                "hai: stale demo session — run 'hai demo end' or "
                "'hai demo cleanup' to clear",
                file=sys.stderr,
            )
    except (ValueError, TypeError):
        pass

    return None




