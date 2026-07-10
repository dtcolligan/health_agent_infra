"""``hai target`` handler group — W50 target ledger.

Owns: ``hai target set``, ``hai target list``, ``hai target commit``,
``hai target archive``, ``hai target nutrition`` (v0.1.15 W-C add).

W-29.2.3 split: extracted from ``cli/__init__.py`` lines 2382-2754
(section header + 5 handler bodies + the now-dead
``_NUTRITION_MACRO_TARGETS`` constant). The constant is preserved
verbatim here for byte-stable extraction; W-29.3 cleanup may delete
it as confirmed-unreferenced.

Cross-handler helpers used: ``_intent_open_db`` (DB-open helper shared
with intent group), ``_w57_user_gate`` (governance gate shared with
intent commit/archive). Both lazy-imported at call time from
``health_agent_infra.cli`` to avoid module-load circularity.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import date, datetime, timezone
from typing import Any

from health_agent_infra.core import exit_codes


# v0.1.15 W-C — `hai target nutrition` macro-group convenience command.
# Round-4 F-PHASE0-01 Option A: extends the existing `target` table
# (migration 020 + the migration-025 CHECK extension for carbs_g +
# fat_g) rather than building a parallel nutrition_target table.
# Tightened per Codex F-R4-01: explicit source/status pairing, atomic
# 4-row insert via add_targets_atomic, natural-key idempotency.
_NUTRITION_MACRO_TARGETS: tuple[tuple[str, str, str], ...] = (
    ("calories_kcal", "kcal", "kcal"),
    ("protein_g",     "g",    "protein_g"),
    ("carbs_g",       "g",    "carbs_g"),
    ("fat_g",         "g",    "fat_g"),
)


def cmd_target_set(args: argparse.Namespace) -> int:
    """`hai target set` — insert a target row (no implicit archive).

    Replacement of an existing target should go through an explicit
    `supersede_target` path; the simple `set` path appends rather than
    replaces, matching the W50 archive/supersession discipline.
    """

    from datetime import date as _date

    from health_agent_infra.cli import (
        _agent_active_insert_gate,
        _emit_json,
        _intent_open_db,
    )
    from health_agent_infra.core.target import add_target
    from health_agent_infra.core.target.store import TargetValidationError

    # WP-RUNTIME-FIX-002: an agent may not create an active target row directly
    # via `target set --status active`; activation is the user-gated commit path.
    gate = _agent_active_insert_gate(args, command="hai target set")
    if gate is not None:
        return gate

    conn, db_path = _intent_open_db(args)  # same DB-open helper
    if conn is None:
        sys.stderr.write(
            f"hai target: no state DB at {db_path}. Run `hai init` first.\n"
        )
        return exit_codes.USER_INPUT

    try:
        try:
            value: Any
            if args.value_json is not None:
                decoded = json.loads(args.value_json)
                value = decoded.get("value", decoded) if isinstance(decoded, dict) else decoded
            else:
                value = args.value
                # Convert numeric values when callers passed --value with a
                # number-shaped string. JSON-decoding the bare value gives
                # us int/float/bool when applicable; falls back to the
                # original string on parse failure.
                try:
                    value = json.loads(args.value)
                except (ValueError, TypeError):
                    pass

            effective_from = _date.fromisoformat(args.effective_from)
            effective_to = (
                _date.fromisoformat(args.effective_to)
                if args.effective_to else None
            )
            review_after = (
                _date.fromisoformat(args.review_after)
                if args.review_after else None
            )

            record = add_target(
                conn,
                user_id=args.user_id,
                domain=args.domain,
                target_type=args.target_type,
                value=value,
                unit=args.unit,
                effective_from=effective_from,
                effective_to=effective_to,
                review_after=review_after,
                lower_bound=args.lower_bound,
                upper_bound=args.upper_bound,
                status=args.status,
                reason=args.reason or "",
                source=args.source,
                ingest_actor=args.ingest_actor,
            )
        except TargetValidationError as exc:
            sys.stderr.write(f"hai target: {exc}\n")
            return exit_codes.USER_INPUT
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"hai target: --value-json malformed: {exc}\n")
            return exit_codes.USER_INPUT

        _emit_json(record.to_row())
        return exit_codes.OK
    finally:
        conn.close()


def cmd_target_list(args: argparse.Namespace) -> int:
    """`hai target list` — list active rows that cover today (default)
    or every row when ``--all`` is set."""

    from datetime import date as _date

    from health_agent_infra.cli import _emit_json, _intent_open_db
    from health_agent_infra.core.target import (
        list_active_target,
        list_target,
    )

    conn, db_path = _intent_open_db(args)
    if conn is None:
        sys.stderr.write(
            f"hai target: no state DB at {db_path}. Run `hai init` first.\n"
        )
        return exit_codes.USER_INPUT

    try:
        if getattr(args, "all", False):
            records = list_target(
                conn,
                user_id=args.user_id,
                domain=getattr(args, "domain", None),
                status=getattr(args, "status", None),
                target_type=getattr(args, "target_type", None),
            )
        else:
            as_of = (
                _date.fromisoformat(args.as_of)
                if getattr(args, "as_of", None)
                else _date.today()
            )
            records = list_active_target(
                conn,
                user_id=args.user_id,
                as_of_date=as_of,
                domain=getattr(args, "domain", None),
            )
        _emit_json([r.to_row() for r in records])
        return exit_codes.OK
    finally:
        conn.close()


def cmd_target_commit(args: argparse.Namespace) -> int:
    """`hai target commit --target-id ID` — promote a `proposed`
    target row to `active`. The W57-required user-gated commit path
    for agent-proposed rows."""

    from health_agent_infra.cli import _emit_json, _intent_open_db, _w57_user_gate

    gate = _w57_user_gate(args, command="hai target commit")
    if gate is not None:
        return gate

    from health_agent_infra.core.target import commit_target

    conn, db_path = _intent_open_db(args)
    if conn is None:
        sys.stderr.write(
            f"hai target: no state DB at {db_path}. Run `hai init` first.\n"
        )
        return exit_codes.USER_INPUT

    try:
        ok = commit_target(
            conn, target_id=args.target_id, user_id=args.user_id,
        )
        if not ok:
            sys.stderr.write(
                f"hai target commit: no proposed target_id={args.target_id} "
                f"for user_id={args.user_id} (already active, archived, or "
                f"missing).\n"
            )
            return exit_codes.USER_INPUT
        _emit_json({"target_id": args.target_id, "status": "active"})
        return exit_codes.OK
    finally:
        conn.close()


def cmd_target_archive(args: argparse.Namespace) -> int:
    """`hai target archive --target-id ID` — flip status to archived.
    The W57-required user-gated deactivation path for currently-active
    or proposed rows."""

    from health_agent_infra.cli import _emit_json, _intent_open_db, _w57_user_gate

    gate = _w57_user_gate(args, command="hai target archive")
    if gate is not None:
        return gate

    from health_agent_infra.core.target import archive_target

    conn, db_path = _intent_open_db(args)
    if conn is None:
        sys.stderr.write(
            f"hai target: no state DB at {db_path}. Run `hai init` first.\n"
        )
        return exit_codes.USER_INPUT

    try:
        ok = archive_target(
            conn, target_id=args.target_id, user_id=args.user_id,
        )
        if not ok:
            sys.stderr.write(
                f"hai target archive: no target_id={args.target_id} "
                f"for user_id={args.user_id}.\n"
            )
            return exit_codes.USER_INPUT
        _emit_json({"target_id": args.target_id, "status": "archived"})
        return exit_codes.OK
    finally:
        conn.close()


def cmd_target_nutrition(args: argparse.Namespace) -> int:
    """`hai target nutrition` — write 4 atomic macro target rows.

    Source/status pairing per the W57 invariant, decided by the runtime
    invocation context (WP-RUNTIME-FIX-003), not the caller-supplied
    ``--ingest-actor`` string:

      * agent-classified caller (``HAI_INVOCATION_CONTEXT=agent`` /
        ``rule_baseline``) → ``source='agent_proposed'``, ``status='proposed'``.
        The user must promote each row via ``hai target commit --target-id
        <id>``. (When ``agent_safe`` is ablated by runtime mode, the active
        insert proceeds with a ``mechanism_disabled`` marker so an off-cell
        violation can execute.)
      * user caller → ``source='user_authored'``, ``status='active'``.

    Natural-key idempotency: re-invocation with identical args
    (same kcal/protein/carbs/fat values, same phase, same effective_from,
    same source) is a no-op — the existing matching rows are returned.
    Different ``--phase`` values produce distinct natural keys (the
    ``reason`` column carries ``"<phase>: ..."`` as a query-friendly
    convention).
    """

    from datetime import datetime, timezone

    from health_agent_infra.cli import _emit_json, _intent_open_db
    from health_agent_infra.core.refusal import (
        build_mechanism_disabled_marker,
        envelope_to_json,
    )
    from health_agent_infra.core.runtime_mode import (
        current_runtime_mode,
        mechanism_is_disabled,
    )
    from health_agent_infra.core.target.store import (
        TargetRecord,
        TargetValidationError,
        add_targets_atomic,
    )

    conn, db_path = _intent_open_db(args)
    if conn is None:
        sys.stderr.write(
            f"hai target: no state DB at {db_path}. Run `hai init` first.\n"
        )
        return exit_codes.USER_INPUT

    try:
        effective_from = (
            date.fromisoformat(args.effective_from)
            if args.effective_from
            else date.today()
        )
        phase_token = (args.phase or "default").strip()
        reason_extra = (args.reason or "").strip()
        reason_str = (
            f"{phase_token}: {reason_extra}"
            if reason_extra
            else f"{phase_token}: hai target nutrition macro group"
        )

        # Source/status pairing per the W57 invariant (WP-RUNTIME-FIX-003).
        # Agent-vs-user is decided by the RUNTIME invocation context, NOT a
        # caller-supplied --ingest-actor string: the old `agent_actors` check
        # let an agent mint active user-state simply by omitting --ingest-actor
        # (default 'cli' -> user_authored/active), a W57 side door that
        # bypassed the gate the sibling `target set` / intent add-session paths
        # enforce. An agent-classified caller may only PROPOSE macros;
        # activation is user-gated. When agent_safe is ablated by runtime mode
        # the active insert proceeds (with a mechanism_disabled marker) so the
        # off cell can execute the violation, matching _agent_active_insert_gate.
        from health_agent_infra.core.refusal.agent_safe import (
            AGENT_CLASSIFIED_INVOCATION_CONTEXTS,
            current_invocation_context,
        )

        context = current_invocation_context()
        is_agent = context in AGENT_CLASSIFIED_INVOCATION_CONTEXTS
        if is_agent and not mechanism_is_disabled("agent_safe"):
            source = "agent_proposed"
            status = "proposed"
        else:
            if is_agent:
                # agent_safe ablated: record the bypass, then allow the active
                # insert so an off-cell violation actually executes.
                sys.stderr.write(
                    envelope_to_json(
                        build_mechanism_disabled_marker(
                            mechanism="agent_safe",
                            runtime_mode=current_runtime_mode(),
                            output_path="hai target nutrition",
                            reason="agent_safe active-insert gate disabled by runtime mode",
                            details={
                                "command": "hai target nutrition",
                                "invocation_context": context,
                            },
                        )
                    )
                    + "\n"
                )
            source = "user_authored"
            status = "active"

        macro_values = {
            "calories_kcal": args.kcal,
            "protein_g":     args.protein_g,
            "carbs_g":       args.carbs_g,
            "fat_g":         args.fat_g,
        }
        macro_units = {
            "calories_kcal": "kcal",
            "protein_g":     "g",
            "carbs_g":       "g",
            "fat_g":         "g",
        }

        # Natural-key idempotency check: query for existing matching
        # rows scoped to (user_id, domain='nutrition', target_type IN
        # macros, status, effective_from, reason LIKE '<phase>:%').
        # If 4 rows exist with identical value_json, return them.
        existing_rows = conn.execute(
            "SELECT target_id, target_type, value_json FROM target "
            "WHERE user_id=? AND domain='nutrition' AND status=? "
            "AND date(effective_from)=date(?) "
            "AND target_type IN ('calories_kcal','protein_g','carbs_g','fat_g') "
            "AND reason LIKE ? "
            "AND superseded_by_target_id IS NULL",
            (
                args.user_id, status, effective_from.isoformat(),
                f"{phase_token}:%",
            ),
        ).fetchall()
        if len(existing_rows) == 4:
            existing_by_type = {
                r["target_type"]: r for r in existing_rows
            }
            all_match = True
            for tt, val in macro_values.items():
                row = existing_by_type.get(tt)
                if row is None:
                    all_match = False
                    break
                decoded = json.loads(row["value_json"]).get("value")
                if decoded != val:
                    all_match = False
                    break
            if all_match:
                # Idempotent no-op: return the existing rows.
                _emit_json({
                    "user_id": args.user_id,
                    "domain": "nutrition",
                    "phase": phase_token,
                    "effective_from": effective_from.isoformat(),
                    "rows_written": 0,
                    "rows_existing": 4,
                    "target_ids": sorted(
                        r["target_id"] for r in existing_rows
                    ),
                    "idempotent_skip": True,
                })
                return exit_codes.OK

        # Build the 4 records.
        when = datetime.now(timezone.utc)
        records = []
        for target_type, value in macro_values.items():
            records.append(TargetRecord(
                target_id=f"target_{uuid.uuid4().hex[:12]}",
                user_id=args.user_id,
                domain="nutrition",
                target_type=target_type,
                status=status,
                value=value,
                unit=macro_units[target_type],
                lower_bound=None,
                upper_bound=None,
                effective_from=effective_from,
                effective_to=None,
                review_after=None,
                reason=reason_str,
                source=source,
                ingest_actor=args.ingest_actor,
                created_at=when,
                supersedes_target_id=None,
                superseded_by_target_id=None,
            ))

        try:
            add_targets_atomic(conn, records=records)
        except TargetValidationError as exc:
            sys.stderr.write(f"hai target nutrition: {exc}\n")
            return exit_codes.USER_INPUT

        _emit_json({
            "user_id": args.user_id,
            "domain": "nutrition",
            "phase": phase_token,
            "effective_from": effective_from.isoformat(),
            "rows_written": 4,
            "rows_existing": 0,
            "target_ids": sorted(r.target_id for r in records),
            "source": source,
            "status": status,
            "idempotent_skip": False,
        })
        return exit_codes.OK
    finally:
        conn.close()
