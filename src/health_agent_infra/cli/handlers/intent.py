"""``hai intent`` handler group — W49 intent ledger.

Owns: ``hai intent training add-session``, ``hai intent sleep set-window``,
``hai intent list``, ``hai intent training list``, ``hai intent commit``,
``hai intent archive``. Plus the intent-private helpers ``_intent_open_db``,
``_intent_record_to_dict``, ``_add_intent_common``, and the cross-handler
W57 governance gate ``_w57_user_gate`` (also used by ``cli/handlers/target.py``;
re-exported from ``cli/__init__.py`` so target.py's lazy import keeps
resolving — W-29.2 phase-end will move ``_w57_user_gate`` to
``cli/shared.py`` per boundary-refresh §(c)).

W-29.2.5 split: extracted from ``cli/__init__.py`` lines 2131-2379.
``_emit_json`` is module-level imported from cli (defined earlier in
``cli/__init__.py``, so the partial-module import resolves cleanly).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from health_agent_infra.core import exit_codes
from health_agent_infra.core.paths import resolve_base_dir

# `_emit_json` is defined in cli/__init__.py before the W-29.2.5 import block
# at line ~2126; partial-module import resolves cleanly.
from health_agent_infra.cli import _emit_json  # noqa: E402


def _intent_open_db(args: argparse.Namespace):
    from health_agent_infra.core.state import (
        open_connection,
        resolve_db_path,
    )

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        return None, db_path
    return open_connection(db_path), db_path


def _intent_record_to_dict(record) -> dict[str, Any]:
    """Project an IntentRecord to the JSON shape the CLI emits."""

    return record.to_row()


def _add_intent_common(args: argparse.Namespace, *, defaults: dict[str, Any]) -> int:
    """Shared body for `hai intent training add-session` /
    `hai intent sleep set-window` / generic `hai intent add`. Resolves
    flags, calls add_intent, emits the persisted row as JSON."""

    from datetime import date as _date

    from health_agent_infra.core.intent import add_intent
    from health_agent_infra.core.intent.store import IntentValidationError

    conn, db_path = _intent_open_db(args)
    if conn is None:
        sys.stderr.write(
            f"hai intent: no state DB at {db_path}. Run `hai init` first.\n"
        )
        return exit_codes.USER_INPUT

    try:
        scope_start = _date.fromisoformat(args.scope_start)
        scope_end = (
            _date.fromisoformat(args.scope_end) if args.scope_end else None
        )
        payload: dict[str, Any] = {}
        if getattr(args, "payload_json", None):
            payload = json.loads(args.payload_json)

        try:
            record = add_intent(
                conn,
                user_id=args.user_id,
                domain=defaults.get("domain", args.domain),
                intent_type=defaults.get("intent_type", args.intent_type),
                scope_start=scope_start,
                scope_end=scope_end,
                scope_type=getattr(args, "scope_type", "day"),
                status=getattr(args, "status", "active"),
                priority=getattr(args, "priority", "normal"),
                flexibility=getattr(args, "flexibility", "flexible"),
                payload=payload,
                reason=args.reason or "",
                source=args.source,
                ingest_actor=args.ingest_actor,
            )
        except IntentValidationError as exc:
            sys.stderr.write(f"hai intent: {exc}\n")
            return exit_codes.USER_INPUT

        _emit_json(_intent_record_to_dict(record))
        return exit_codes.OK
    finally:
        conn.close()


def cmd_intent_training_add_session(args: argparse.Namespace) -> int:
    """`hai intent training add-session` — convenience alias for
    domain=running/strength training_session intent. Defaults the
    domain to ``running`` (the most common session-level intent in
    v0.1.8); override via ``--domain strength`` for a strength
    session."""

    return _add_intent_common(
        args,
        defaults={"intent_type": "training_session"},
    )


def cmd_intent_sleep_set_window(args: argparse.Namespace) -> int:
    """`hai intent sleep set-window` — convenience alias for
    domain=sleep sleep_window intent."""

    return _add_intent_common(
        args,
        defaults={"domain": "sleep", "intent_type": "sleep_window"},
    )


def cmd_intent_list(args: argparse.Namespace) -> int:
    """`hai intent list` — list intent rows. Defaults to active rows
    that cover today; ``--all`` returns every row."""

    from datetime import date as _date

    from health_agent_infra.core.intent import (
        list_active_intent,
        list_intent,
    )

    conn, db_path = _intent_open_db(args)
    if conn is None:
        sys.stderr.write(
            f"hai intent: no state DB at {db_path}. Run `hai init` first.\n"
        )
        return exit_codes.USER_INPUT

    try:
        if getattr(args, "all", False):
            records = list_intent(
                conn,
                user_id=args.user_id,
                domain=getattr(args, "domain", None),
                status=getattr(args, "status", None),
            )
        else:
            as_of = (
                _date.fromisoformat(args.as_of)
                if getattr(args, "as_of", None)
                else _date.today()
            )
            records = list_active_intent(
                conn,
                user_id=args.user_id,
                as_of_date=as_of,
                domain=getattr(args, "domain", None),
            )
        _emit_json([_intent_record_to_dict(r) for r in records])
        return exit_codes.OK
    finally:
        conn.close()


def cmd_intent_training_list(args: argparse.Namespace) -> int:
    """`hai intent training list` — alias for `hai intent list
    --domain running`."""

    args.domain = "running"
    return cmd_intent_list(args)


def _w57_user_gate(args: argparse.Namespace, *, command: str) -> Optional[int]:
    """Reject W57-affected mutations from non-interactive callers.

    Returns ``None`` when the call is permitted, ``USER_INPUT`` when
    the gate refuses. AGENTS.md W57 reserves intent/target activation
    AND deactivation for an explicit user commit; agents that propose
    a row may not auto-promote OR auto-archive. The capabilities
    manifest declares these four handlers ``agent_safe=False``, but
    that is informational — this gate is the runtime enforcement.

    Two recognised user gestures:

      - ``--confirm`` flag passed explicitly. Suitable for scripted
        runs where the user has already opted in (e.g. a wrapper
        script the user authored).
      - Interactive stdin (``sys.stdin.isatty()`` is True). Suitable
        for manual command-line use.

    Anything else — agent harnesses without ``--confirm``, piped
    invocations, background jobs — is rejected.
    """

    if getattr(args, "confirm", False):
        return None
    if sys.stdin.isatty():
        return None
    sys.stderr.write(
        f"{command}: refusing to mutate user-state row from a "
        f"non-interactive caller. AGENTS.md W57 requires an explicit "
        f"user commit. Pass --confirm to proceed.\n"
    )
    return exit_codes.USER_INPUT


def cmd_intent_commit(args: argparse.Namespace) -> int:
    """`hai intent commit --intent-id ID` — promote a `proposed`
    intent row to `active`. The W57-required user-gated commit path
    for agent-proposed rows."""

    gate = _w57_user_gate(args, command="hai intent commit")
    if gate is not None:
        return gate

    from health_agent_infra.core.intent import commit_intent

    conn, db_path = _intent_open_db(args)
    if conn is None:
        sys.stderr.write(
            f"hai intent: no state DB at {db_path}. Run `hai init` first.\n"
        )
        return exit_codes.USER_INPUT

    try:
        ok = commit_intent(
            conn, intent_id=args.intent_id, user_id=args.user_id,
        )
        if not ok:
            sys.stderr.write(
                f"hai intent commit: no proposed intent_id={args.intent_id} "
                f"for user_id={args.user_id} (already active, archived, or "
                f"missing).\n"
            )
            return exit_codes.USER_INPUT
        _emit_json({"intent_id": args.intent_id, "status": "active"})
        return exit_codes.OK
    finally:
        conn.close()


def cmd_intent_archive(args: argparse.Namespace) -> int:
    """`hai intent archive --intent-id ID` — flip a row to
    ``status='archived'``. The W57-required user-gated deactivation
    path for currently-active or proposed rows."""

    gate = _w57_user_gate(args, command="hai intent archive")
    if gate is not None:
        return gate

    from health_agent_infra.core.intent import archive_intent

    conn, db_path = _intent_open_db(args)
    if conn is None:
        sys.stderr.write(
            f"hai intent: no state DB at {db_path}. Run `hai init` first.\n"
        )
        return exit_codes.USER_INPUT

    try:
        ok = archive_intent(
            conn,
            intent_id=args.intent_id,
            user_id=args.user_id,
        )
        if not ok:
            sys.stderr.write(
                f"hai intent archive: no intent_id={args.intent_id} "
                f"for user_id={args.user_id}.\n"
            )
            return exit_codes.USER_INPUT
        _emit_json({"intent_id": args.intent_id, "status": "archived"})
        return exit_codes.OK
    finally:
        conn.close()
