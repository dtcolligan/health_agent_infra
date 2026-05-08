"""``hai inspect`` group — read-only operator surfaces.

Owns: ``hai today``, ``hai explain``, ``hai stats``, ``hai doctor``,
``hai capabilities``. Plus stats helpers ``_emit_outcomes_stats`` /
``_emit_funnel_stats`` / ``_emit_baselines_stats`` / ``_emit_data_quality_stats``,
the corresponding ``_render_*_text`` helpers, ``_daily_streak_from_events``,
``_render_stats_text``, ``_worst_status`` (doctor), and ``_build_daily_explain_block``.

W-29.2.8 split: extracted from cli/__init__.py 3 ranges
(1583-1854 cmd_explain + cmd_today; 3723-4569 doctor/stats cluster +
helpers; 4597-4625 cmd_capabilities).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from health_agent_infra.core import exit_codes
from health_agent_infra.core.capabilities import build_manifest
from health_agent_infra.core.capabilities.render import render_human, render_markdown
from health_agent_infra.core.config import (
    ConfigError,
    load_thresholds,
    user_config_path,
)
from health_agent_infra.core.paths import resolve_base_dir

# `_emit_json` defined in cli/__init__.py before line 1583. `build_parser`
# is defined LATER — lazy-imported inside cmd_capabilities below.
from health_agent_infra.cli import (  # noqa: E402
    DEFAULT_CLAUDE_SKILLS_DIR,
    _PACKAGE_VERSION,
    _coerce_date,
    _coerce_dt,
    _credential_store_for,
    _emit_json,
    _intervals_icu_configured,
    _skills_source,
)
# `_DAILY_SUPPORTED_DOMAINS` lives in cli/handlers/tools.py; importing
# directly from the source module bypasses the W-29.2.6 cli re-export
# block (which loads later than this inspect import block).
from health_agent_infra.cli.handlers.tools import _DAILY_SUPPORTED_DOMAINS  # noqa: E402


def cmd_explain(args: argparse.Namespace) -> int:
    """Reconstruct the audit chain for a committed plan, read-only.

    Two key forms:

    - ``--daily-plan-id <id>`` returns the bundle for an exact plan,
      including ``_v<N>`` superseded variants.
    - ``--for-date <d> --user-id <u>`` returns the canonical plan for
      that key. The bundle's ``supersedes`` / ``superseded_by`` fields
      let a caller walk any supersession chain by reissuing
      ``hai explain --daily-plan-id``.

    Output is JSON by default (machine-readable for agents). Pass
    ``--text`` for the operator-facing report. Nothing in this command
    opens a write transaction.
    """

    from health_agent_infra.core.explain import (
        ExplainNotFoundError,
        bundle_to_dict,
        load_bundle_by_daily_plan_id,
        load_bundle_chain_for_date,
        load_bundle_for_date,
        render_bundle_text,
    )
    from health_agent_infra.core.state import open_connection, resolve_db_path

    if args.daily_plan_id and (args.for_date or args.user_id):
        print(
            "hai explain rejected: pass either --daily-plan-id OR "
            "(--for-date and --user-id), not both.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT
    if not args.daily_plan_id and not (args.for_date and args.user_id):
        print(
            "hai explain rejected: provide --daily-plan-id, or both "
            "--for-date and --user-id.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    # --plan-version is ignored when an exact --daily-plan-id is given;
    # that form always returns the specified plan's bundle.
    if args.daily_plan_id and args.plan_version != "latest":
        print(
            "hai explain rejected: --plan-version is incompatible with "
            "--daily-plan-id; the id already pins the specific plan.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"hai explain requires an initialized state DB; not found at "
            f"{db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    conn = open_connection(db_path)
    try:
        try:
            if args.daily_plan_id:
                bundle = load_bundle_by_daily_plan_id(
                    conn, daily_plan_id=args.daily_plan_id,
                )
                bundles = [bundle]
            elif args.plan_version == "all":
                bundles = load_bundle_chain_for_date(
                    conn,
                    for_date=date.fromisoformat(args.for_date),
                    user_id=args.user_id,
                )
            else:
                bundle = load_bundle_for_date(
                    conn,
                    for_date=date.fromisoformat(args.for_date),
                    user_id=args.user_id,
                    plan_version=args.plan_version,
                )
                bundles = [bundle]
        except ExplainNotFoundError as exc:
            # Well-formed request, no matching row — NOT_FOUND, not user-input.
            print(f"hai explain: {exc}", file=sys.stderr)
            return exit_codes.NOT_FOUND
    finally:
        conn.close()

    # D3: ``--operator`` is canonical; ``--text`` stays as a deprecated
    # alias until the next release. Either flag selects the operator
    # text report. Emit a deprecation hint on stderr when the alias is
    # used so scripts get a nudge during the deprecation window.
    if args.text and not args.operator:
        print(
            "hai explain: --text is deprecated; use --operator. "
            "The alias will be removed in a future release.",
            file=sys.stderr,
        )
    operator_output = args.operator or args.text

    if operator_output:
        for bundle in bundles:
            sys.stdout.write(render_bundle_text(bundle))
    else:
        if args.plan_version == "all" and not args.daily_plan_id:
            _emit_json([bundle_to_dict(b) for b in bundles])
        else:
            _emit_json(bundle_to_dict(bundles[0]))
    return exit_codes.OK


# ---------------------------------------------------------------------------
# hai today — user-facing narration of the canonical plan (D3)
# ---------------------------------------------------------------------------


def cmd_today(args: argparse.Namespace) -> int:
    """Render today's plan in plain language.

    Per D3 (``hai/reporting/plans/v0_1_4/D3_user_surface.md``), ``hai today``
    is the non-agent-mediated user surface for reading the canonical
    plan. It reads the canonical leaf of the supersede chain via
    :func:`load_bundle_for_date` (D1) and renders six per-domain sections
    in the voice the ``reporting`` skill specifies.

    Exit code ``USER_INPUT`` when no plan exists for the target date —
    with a stderr hint pointing the user at ``hai daily`` to produce
    one. Stable output contract for snapshot tests: same plan in the DB
    → byte-identical stdout.
    """

    from health_agent_infra.core.explain import (
        ExplainNotFoundError,
        load_bundle_for_date,
    )
    from health_agent_infra.core.narration import DOMAIN_ORDER, render_today
    from health_agent_infra.core.state import open_connection, resolve_db_path

    if args.domain is not None and args.domain not in DOMAIN_ORDER:
        print(
            f"hai today: --domain {args.domain!r} not in {list(DOMAIN_ORDER)}",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    # Format default: markdown when stdout is a TTY, plain otherwise.
    # Explicit flag wins.
    fmt = args.format
    if fmt is None:
        fmt = "markdown" if sys.stdout.isatty() else "plain"

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"hai today requires an initialized state DB; not found at "
            f"{db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    as_of = _coerce_date(args.as_of)
    conn = open_connection(db_path)
    try:
        try:
            bundle = load_bundle_for_date(
                conn, for_date=as_of, user_id=args.user_id,
                plan_version="latest",
            )
        except ExplainNotFoundError:
            print(
                f"No plan for {as_of.isoformat()}. Run `hai daily` first.",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT

        # D4 cold-start flags — one counting query per domain, <1ms
        # on realistic DB sizes. Threaded into render_today so the
        # nutrition defer message + per-domain footer reflect the
        # user's actual history window. On a cold-start-clean user
        # the renderer silently behaves as pre-D4.
        from health_agent_infra.core.state.snapshot import _cold_start_flags
        cold_start_by_domain = _cold_start_flags(
            conn, user_id=args.user_id, as_of_date=as_of,
        )
        # W-AG (v0.1.13): consecutive-day `hai daily` streak. Threaded
        # through render_today for day-1 vs day-30 prose differentiation.
        # Read inside the same conn open block to avoid a second open.
        try:
            streak_days = _daily_streak_from_events(conn)
        except Exception:  # noqa: BLE001
            # Defensive: streak read failure must never block the plan
            # surface. Pre-W-AG behaviour (streak=None) is the fallback.
            streak_days = None
    finally:
        conn.close()

    output = render_today(
        bundle,
        format=fmt,
        domain_filter=args.domain,
        cold_start_by_domain=cold_start_by_domain,
        streak_days=streak_days,
    )

    # W-LINT (v0.1.13): runtime regulated-claim check at the CLI
    # rendering boundary. Strict regime regardless of source-skill
    # provenance (F-PLAN-09 constraint 4) — even an allowlisted skill
    # whose SKILL.md passes static lint cannot surface a regulated
    # term in rendered prose. JSON format is exempt because it is the
    # agent-facing structured surface, not user-facing text.
    if fmt != "json":
        from health_agent_infra.core.lint import (
            RegulatedClaimError,
            runtime_check,
        )
        try:
            runtime_check(output)
        except RegulatedClaimError as exc:
            print(
                f"hai today: regulated-claim lint blocked the rendered "
                f"output (this is a code bug; the rationale prose passed "
                f"validation but contains a banned phrase). Details:\n"
                f"{exc}",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT

    # W-FCC (v0.1.12 / F-C-05): when --verbose is set, prepend a
    # "classified state" footer surfacing internal classifier outputs.
    # v0.1.12 surfaces only strength_status enum values; future cycles
    # may extend (recovery_status, sleep_status, etc.). The enum surface
    # itself is the load-bearing exposure — `hai capabilities --json`
    # carries the canonical list under
    # ``commands[].output_schema.OK.enum_surface.strength_status``.
    if getattr(args, "verbose", False):
        from health_agent_infra.domains.strength.classify import (
            STRENGTH_STATUS_VALUES,
        )
        if fmt == "json":
            # JSON callers don't get a header — the enum surface lives
            # in capabilities; verbose JSON is a future extension.
            pass
        else:
            header_lines = [
                "## classified state (verbose) — strength_status enum surface",
                "",
                "  strength_status ∈ {"
                + ", ".join(STRENGTH_STATUS_VALUES)
                + "}",
                "",
                "  (See `hai capabilities --json | jq '.commands[] | "
                "select(.command == \"hai today\").output_schema.OK."
                "enum_surface'` for the canonical list. Live "
                "classified-state-of-the-day rendering is v0.1.13+.)",
                "",
                "---",
                "",
            ]
            output = "\n".join(header_lines) + output

    sys.stdout.write(output)
    return exit_codes.OK


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# hai memory — explicit user-memory CRUD (Phase D)
# ---------------------------------------------------------------------------
# W-29.2.6: handler bodies (memory + exercise + research + planned + demo +
# _demo_gate) live in cli/handlers/tools.py.


def _worst_status(statuses: list[str]) -> str:
    order = {"ok": 0, "warn": 1, "fail": 2}
    if not statuses:
        return "ok"
    worst = max(order[s] for s in statuses)
    return {0: "ok", 1: "warn", 2: "fail"}[worst]


def cmd_doctor(args: argparse.Namespace) -> int:
    """Read-only diagnostics against the actual v1 runtime surfaces.

    Seven checks: config, state DB + schema version + size, Garmin
    credentials, skills install, domain registry, per-source sync
    freshness (from sync_run_log, M2), and today's proposal /
    recommendation / pending-review counts (M5).

    Default output is human-readable text. Pass ``--json`` for the
    structured dict an agent can parse.

    Exit code: 0 for ``ok`` or ``warn`` overall; 2 for ``fail``
    (malformed config on disk). ``warn`` is the normal pre-setup state
    so ``hai doctor && hai daily`` isn't blocked by a missing-auth
    warning.
    """

    from health_agent_infra.core.doctor import build_report, render_text
    from health_agent_infra.core.state import resolve_db_path

    thresholds_path = (
        Path(args.thresholds_path).expanduser()
        if args.thresholds_path
        else user_config_path()
    )
    db_path = resolve_db_path(args.db_path)
    skills_dest = Path(args.skills_dest).expanduser()

    with _skills_source() as skills_source:
        packaged_names = (
            sorted(p.name for p in skills_source.iterdir() if p.is_dir())
            if skills_source.exists()
            else []
        )

    as_of_date = _coerce_date(getattr(args, "as_of", None))

    report = build_report(
        version=_PACKAGE_VERSION,
        thresholds_path=thresholds_path,
        db_path=db_path,
        skills_dest=skills_dest,
        packaged_skill_names=packaged_names,
        domain_names=sorted(_DAILY_SUPPORTED_DOMAINS),
        credential_store=_credential_store_for(args),
        user_id=getattr(args, "user_id", "u_local_1"),
        as_of_date=as_of_date,
        # v0.1.11 W-X: --deep adds live/fixture probe results to the
        # auth_* rows. Demo mode routes to FixtureProbe with a hard
        # no-network guarantee per Codex F-PLAN-R2-03.
        deep=getattr(args, "deep", False),
    )

    if getattr(args, "json", False):
        _emit_json(report.to_dict())
    else:
        sys.stdout.write(render_text(report))

    # doctor "fail" means a user-fixable state precondition (DB not
    # initialised, creds missing, etc.) — maps to USER_INPUT per the
    # exit-code taxonomy ("state precondition the caller controls").
    return exit_codes.USER_INPUT if report.overall_status == "fail" else exit_codes.OK


# ---------------------------------------------------------------------------
# hai stats — local, read-only onboarding + engagement signal
# ---------------------------------------------------------------------------


def cmd_stats(args: argparse.Namespace) -> int:
    """Summarise sync_run_log + runtime_event_log for the user's own DB.

    Read-only. Three sections:

      1. Sync freshness — last successful pull per source.
      2. Recent command runs — last N rows from runtime_event_log.
      3. Command + streak summary — counts per command, consecutive-day
         streak for `hai daily` (UTC calendar dates).

    Default output is human-readable text; pass ``--json`` for the
    structured dict. Text stays stable enough for eyeballing; JSON is
    the machine surface.

    No telemetry leaves the device — this command reads local SQLite
    only. The user can paste the JSON into a bug report; nothing here
    is auto-sent anywhere.
    """

    from health_agent_infra.core.state import (
        command_summary,
        latest_successful_sync_per_source,
        open_connection,
        recent_events,
        resolve_db_path,
    )

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        if getattr(args, "json", False):
            _emit_json({
                "db_path": str(db_path),
                "status": "db_missing",
                "hint": "run `hai init` to create the state DB",
            })
        else:
            print(
                f"hai stats: no state DB at {db_path}. "
                f"Run `hai init` first.",
                file=sys.stderr,
            )
        return exit_codes.USER_INPUT

    user_id = getattr(args, "user_id", "u_local_1")
    limit = max(1, int(getattr(args, "limit", 7) or 7))

    # v0.1.8 W38 — early branch when --outcomes is set. Returns the
    # code-owned review-outcome summary (W48) and skips the default
    # sync/events report entirely. No CLI-side arithmetic — every
    # field comes from build_review_summary, which is the single
    # source of truth for outcome aggregation.
    if getattr(args, "outcomes", False):
        return _emit_outcomes_stats(
            db_path=db_path,
            user_id=user_id,
            domain=getattr(args, "domain", None),
            since_days=getattr(args, "since", None),
            as_json=getattr(args, "json", False),
        )

    # v0.1.8 W51 — `hai stats --data-quality`.
    if getattr(args, "data_quality", False):
        return _emit_data_quality_stats(
            db_path=db_path,
            user_id=user_id,
            domain=getattr(args, "domain", None),
            since_days=getattr(args, "since", None) or 7,
            as_json=getattr(args, "json", False),
        )

    # v0.1.8 W40 — `hai stats --baselines`.
    if getattr(args, "baselines", False):
        return _emit_baselines_stats(
            db_path=db_path,
            user_id=user_id,
            domain=getattr(args, "domain", None),
            as_json=getattr(args, "json", False),
        )

    # v0.1.8 W46 — `hai stats --funnel`.
    if getattr(args, "funnel", False):
        return _emit_funnel_stats(
            db_path=db_path,
            user_id=user_id,
            since_days=getattr(args, "since", None) or 14,
            as_json=getattr(args, "json", False),
        )

    conn = open_connection(db_path)
    try:
        freshness = latest_successful_sync_per_source(conn, user_id=user_id)
        recent = recent_events(conn, limit=limit)
        summary = command_summary(conn)
        streak = _daily_streak_from_events(conn)
    finally:
        conn.close()

    # D4 #5 — cred-awareness. If a source's most recent successful
    # sync came from a live adapter and that adapter's credentials
    # are no longer present (user rotated keys, keyring reset,
    # migrated machines), mark the source's freshness entry as
    # `stale_credentials`. The sync timestamp itself stays accurate;
    # this is a UX hint that the next `hai pull --live` will fail.
    cred_store = _credential_store_for(args)
    cred_status_by_source = {
        "garmin_live": cred_store.garmin_status().get(
            "credentials_available", False,
        ),
        "intervals_icu": cred_store.intervals_icu_status().get(
            "credentials_available", False,
        ),
    }

    # F-PV14-01 (v0.1.15) acceptance: surface
    # |started_at - for_date| per source and flag >48h divergence.
    # The contamination shape from the v0.1.14 carry-over evidence had
    # for_date months before started_at (CSV fixture for a 2026-02-10
    # row written 2026-05-01). Same field is consumed by `hai doctor`
    # via core.doctor.checks.check_sources.
    def _for_date_divergence_hours(row: dict[str, Any]) -> Optional[float]:
        started_raw = row.get("started_at")
        for_date_raw = row.get("for_date")
        if not started_raw or not for_date_raw:
            return None
        try:
            started = datetime.fromisoformat(started_raw)
            for_d = date.fromisoformat(for_date_raw)
        except (TypeError, ValueError):
            return None
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        # Divergence in hours: signed (positive when for_date is in the past
        # relative to the run, which is the F-PV14-01 contamination shape).
        delta = started - datetime.combine(
            for_d, time.min, tzinfo=timezone.utc,
        )
        return round(delta.total_seconds() / 3600.0, 2)

    report: dict[str, Any] = {
        "db_path": str(db_path),
        "user_id": user_id,
        "sync_freshness": {
            source: {
                "started_at": row.get("started_at"),
                "completed_at": row.get("completed_at"),
                "status": (
                    "stale_credentials"
                    if (
                        source in cred_status_by_source
                        and cred_status_by_source[source] is False
                        and row.get("status") == "ok"
                    )
                    else row.get("status")
                ),
                "credentials_available": cred_status_by_source.get(source),
                "for_date": row.get("for_date"),
                "mode": row.get("mode"),
                "for_date_divergence_hours": _for_date_divergence_hours(row),
                "for_date_divergence_warn": (
                    (_for_date_divergence_hours(row) or 0.0) > 48.0
                ),
            }
            for source, row in freshness.items()
        },
        "recent_events": [
            {
                "event_id": r["event_id"],
                "command": r["command"],
                "started_at": r["started_at"],
                "completed_at": r["completed_at"],
                "status": r["status"],
                "exit_code": r["exit_code"],
                "duration_ms": r["duration_ms"],
                "error_class": r["error_class"],
                "error_message": r["error_message"],
            }
            for r in recent
        ],
        "command_summary": summary,
        "daily_streak_days": streak,
    }

    if getattr(args, "json", False):
        _emit_json(report)
    else:
        sys.stdout.write(_render_stats_text(report))
    return exit_codes.OK


def _build_daily_explain_block(report: dict[str, Any]) -> dict[str, Any]:
    """v0.1.8 W43 — derive a per-stage explain block from a `hai daily`
    report dict. Reads what the stages already populated; never
    recomputes or fabricates fields.

    The explain block is intentionally a thin re-shaping of
    ``report["stages"]`` so consumers don't have to reach into the
    nested stage dicts to answer common questions. Every value is
    sourced from the corresponding stage dict.
    """

    stages = report.get("stages") or {}

    def _stage(name: str) -> dict[str, Any]:
        return stages.get(name) or {}

    pull = _stage("pull")
    clean = _stage("clean")
    snapshot = _stage("snapshot")
    gaps = _stage("gaps")
    proposal_gate = _stage("proposal_gate")
    synthesize = _stage("synthesize")

    return {
        "schema_version": "daily_explain.v1",
        "as_of_date": report.get("as_of_date"),
        "user_id": report.get("user_id"),
        "overall_status": report.get("overall_status"),
        "pull": {
            "status": pull.get("status"),
            "source": pull.get("source"),
            "auth_reason": pull.get("auth_reason"),
            "freshness_hours": pull.get("freshness_hours"),
        },
        "clean": {
            "status": clean.get("status"),
            "evidence_rows": clean.get("evidence_rows"),
            "sources_merged": clean.get("sources_merged"),
        },
        "snapshot": {
            "status": snapshot.get("status"),
            "domains_present": snapshot.get("domains_present"),
            "missingness_per_domain": snapshot.get("missingness_per_domain"),
            "classified_bands_per_domain": snapshot.get(
                "classified_bands_per_domain"
            ),
            "review_summary_tokens_per_domain": snapshot.get(
                "review_summary_tokens_per_domain"
            ),
        },
        "gaps": {
            "status": gaps.get("status"),
            "gap_tokens": [
                g.get("token") for g in (gaps.get("gaps") or [])
            ],
            "intake_commands": [
                g.get("intake_command") for g in (gaps.get("gaps") or [])
                if g.get("intake_command")
            ],
        },
        "proposal_gate": {
            "status": proposal_gate.get("status"),
            "expected": proposal_gate.get("expected"),
            "present": proposal_gate.get("present"),
            "missing": proposal_gate.get("missing"),
        },
        "synthesize": {
            "status": synthesize.get("status"),
            "phase_a_firings": synthesize.get("phase_a_firings"),
            "phase_b_mutations": synthesize.get("phase_b_mutations"),
        },
    }


def _emit_outcomes_stats(
    *,
    db_path: Path,
    user_id: str,
    domain: Optional[str],
    since_days: Optional[int],
    as_json: bool,
) -> int:
    """v0.1.8 W38 — emit the `hai stats --outcomes` view.

    Wraps the W48 ``build_review_summary`` builder so the CLI can serve
    the same dict to JSON and to a human-readable markdown table. Pure
    visibility — never mutates state and never recomputes anything the
    builder owns.
    """

    from health_agent_infra.core.review.summary import build_review_summary
    from health_agent_infra.core.state import open_connection

    today = datetime.now(timezone.utc).date()
    conn = open_connection(db_path)
    try:
        if domain is not None:
            payload = build_review_summary(
                conn,
                as_of_date=today,
                user_id=user_id,
                domain=domain,
                window_days=since_days,
            )
            payload = {
                "as_of_date": today.isoformat(),
                "user_id": user_id,
                "window_days": payload["window"]["days"],
                "domain": domain,
                "summary": payload,
            }
        else:
            bundle = build_review_summary(
                conn,
                as_of_date=today,
                user_id=user_id,
                window_days=since_days,
            )
            payload = {
                "as_of_date": today.isoformat(),
                "user_id": user_id,
                "window_days": bundle["window_days"],
                "domains": bundle["domains"],
                "aggregate": bundle["aggregate"],
            }
    finally:
        conn.close()

    if as_json:
        _emit_json(payload)
    else:
        sys.stdout.write(_render_outcomes_text(payload))
    return exit_codes.OK


def _render_outcomes_text(payload: dict[str, Any]) -> str:
    """Markdown table view for ``hai stats --outcomes`` on a TTY."""

    lines: list[str] = []
    lines.append(
        f"# Review outcome summary — as of {payload['as_of_date']} "
        f"(window: {payload['window_days']} days, user: {payload['user_id']})"
    )
    lines.append("")

    def _row_for(name: str, summary: dict[str, Any]) -> str:
        rate_followed = summary.get("followed_recommendation_rate")
        rate_improved = summary.get("self_reported_improvement_rate")
        rate_followed_str = (
            f"{rate_followed:.0%}" if rate_followed is not None else "—"
        )
        rate_improved_str = (
            f"{rate_improved:.0%}" if rate_improved is not None else "—"
        )
        tokens = summary.get("tokens", []) or ["—"]
        return (
            f"| {name} | {summary['recorded_outcome_count']} "
            f"| {summary['followed_count']} "
            f"| {rate_followed_str} | {rate_improved_str} "
            f"| {summary['relinked_outcome_count']} "
            f"| {', '.join(tokens)} |"
        )

    lines.append(
        "| Domain | Recorded | Followed | Followed rate | Improved rate | Re-linked | Tokens |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|---:|---|"
    )

    if "summary" in payload:
        lines.append(_row_for(payload["domain"], payload["summary"]))
    else:
        for domain_name in (
            "recovery", "running", "sleep", "stress", "strength", "nutrition",
        ):
            lines.append(_row_for(domain_name, payload["domains"][domain_name]))
        lines.append(_row_for("aggregate", payload["aggregate"]))

    lines.append("")
    return "\n".join(lines) + "\n"


def _emit_funnel_stats(
    *,
    db_path: Path,
    user_id: str,
    since_days: int,
    as_json: bool,
) -> int:
    """v0.1.8 W46 — emit `hai stats --funnel`.

    Reads ``runtime_event_log`` for the last ``since_days`` of `hai
    daily` invocations and aggregates the proposal-gate context that
    `cmd_daily` persists (overall_status / missing_domains).
    """

    from datetime import timedelta as _td

    from health_agent_infra.core.state import open_connection

    today = datetime.now(timezone.utc).date()
    since = today - _td(days=max(0, since_days - 1))

    conn = open_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT event_id, started_at, completed_at, status, exit_code, "
            "       duration_ms, context_json "
            "FROM runtime_event_log "
            "WHERE command = 'daily' "
            "  AND substr(started_at, 1, 10) >= ? "
            "  AND substr(started_at, 1, 10) <= ? "
            "ORDER BY started_at",
            (since.isoformat(), today.isoformat()),
        ).fetchall()
    finally:
        conn.close()

    daily_run_count = len(rows)
    overall_status_histogram: dict[str, int] = {}
    missing_domain_freq: dict[str, int] = {}
    blocking_action_count = 0
    awaiting_proposals = 0
    incomplete = 0
    complete = 0

    for r in rows:
        ctx_text = r["context_json"]
        ctx = {}
        if ctx_text:
            try:
                ctx = json.loads(ctx_text)
            except (TypeError, ValueError):
                ctx = {}
        status = ctx.get("overall_status") or r["status"] or "unknown"
        overall_status_histogram[status] = overall_status_histogram.get(status, 0) + 1
        if status == "awaiting_proposals":
            awaiting_proposals += 1
            blocking_action_count += 1
        elif status == "incomplete":
            incomplete += 1
            blocking_action_count += 1
        elif status == "complete":
            complete += 1
        for missing in (ctx.get("missing_domains") or []):
            missing_domain_freq[missing] = missing_domain_freq.get(missing, 0) + 1

    payload = {
        "as_of_date": today.isoformat(),
        "user_id": user_id,
        "since_days": since_days,
        "daily_run_count": daily_run_count,
        "overall_status_histogram": overall_status_histogram,
        "complete_count": complete,
        "incomplete_count": incomplete,
        "awaiting_proposals_count": awaiting_proposals,
        "blocking_action_count": blocking_action_count,
        "missing_domain_frequency": missing_domain_freq,
    }

    if as_json:
        _emit_json(payload)
    else:
        sys.stdout.write(_render_funnel_text(payload))
    return exit_codes.OK


def _render_funnel_text(payload: dict[str, Any]) -> str:
    lines = [
        f"# Daily-pipeline funnel — last {payload['since_days']} days "
        f"(user: {payload['user_id']})",
        "",
        f"- Total `hai daily` invocations: {payload['daily_run_count']}",
        f"- Complete (synthesis ready): {payload['complete_count']}",
        f"- Incomplete (blocked): {payload['incomplete_count']}",
        f"- Awaiting proposals: {payload['awaiting_proposals_count']}",
        f"- Blocking-action runs: {payload['blocking_action_count']}",
        "",
        "## overall_status histogram",
    ]
    for status, n in sorted(payload["overall_status_histogram"].items()):
        lines.append(f"- {status}: {n}")
    if payload["missing_domain_frequency"]:
        lines.append("")
        lines.append("## Missing domain frequency")
        for domain, n in sorted(payload["missing_domain_frequency"].items()):
            lines.append(f"- {domain}: {n}")
    lines.append("")
    return "\n".join(lines) + "\n"


def _emit_baselines_stats(
    *,
    db_path: Path,
    user_id: str,
    domain: Optional[str],
    as_json: bool,
) -> int:
    """v0.1.8 W40 — emit `hai stats --baselines`.

    Reads the snapshot for ``today``, plus ``thresholds.toml`` for the
    threshold-source paths. Output groups per-domain blocks so the user
    can inspect: observed value(s), threshold values, band, coverage,
    missingness, cold-start state.

    No arithmetic happens in the CLI — every band is the snapshot's
    classification; every threshold is whatever ``load_thresholds()``
    returned. The CLI is a renderer, not a computer.
    """

    from health_agent_infra.core.config import load_thresholds, user_config_path
    from health_agent_infra.core.state import build_snapshot, open_connection

    today = datetime.now(timezone.utc).date()
    thresholds = load_thresholds()
    threshold_path = str(user_config_path())

    conn = open_connection(db_path)
    try:
        snap = build_snapshot(
            conn,
            as_of_date=today,
            user_id=user_id,
            now_local=datetime.now(),
        )
    finally:
        conn.close()

    domains_iter = (domain,) if domain else (
        "recovery", "running", "sleep", "stress", "strength", "nutrition",
    )
    domain_payloads: dict[str, dict[str, Any]] = {}
    for d in domains_iter:
        block = snap.get(d) or {}
        classified = block.get("classified_state") or {}
        today_row = block.get("today") or {}
        domain_payloads[d] = {
            "today": today_row,
            "classified_state": classified,
            "missingness": block.get("missingness"),
            "cold_start": block.get("cold_start", False),
            "history_days": block.get("history_days"),
            "data_quality": block.get("data_quality"),
            # Thresholds for this domain — both classify + policy + synthesis
            # surfaces. The user can inspect what numbers the runtime is
            # actually using to draw band boundaries.
            "thresholds": {
                "classify": thresholds.get("classify", {}).get(d, {}),
                "policy": thresholds.get("policy", {}).get(d, {}),
            },
        }

    payload = {
        "as_of_date": today.isoformat(),
        "user_id": user_id,
        "threshold_source": threshold_path,
        "domains": domain_payloads,
    }

    if as_json:
        _emit_json(payload)
    else:
        sys.stdout.write(_render_baselines_text(payload))
    return exit_codes.OK


def _render_baselines_text(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        f"# Baselines — as of {payload['as_of_date']} "
        f"(user: {payload['user_id']})",
        f"_Threshold source: `{payload['threshold_source']}`_",
        "",
    ]
    for domain, block in payload["domains"].items():
        classified = block.get("classified_state") or {}
        bands = {
            k: v for k, v in classified.items()
            if k.endswith("_band") or k in ("coverage_band", "recovery_status",
                                             "running_readiness_status",
                                             "sleep_status",
                                             "stress_state",
                                             "strength_status",
                                             "nutrition_status")
        }
        lines.append(f"## {domain}")
        if not bands:
            lines.append("_No classified state — domain bundle not loaded._")
        for k, v in sorted(bands.items()):
            lines.append(f"- **{k}**: {v}")
        if block.get("cold_start"):
            lines.append(
                f"- _cold-start window — history_days: {block.get('history_days')}_"
            )
        missing = block.get("missingness")
        if missing:
            lines.append(f"- _missingness_: {missing}")
        lines.append("")
    return "\n".join(lines) + "\n"


def _emit_data_quality_stats(
    *,
    db_path: Path,
    user_id: str,
    domain: Optional[str],
    since_days: int,
    as_json: bool,
) -> int:
    """v0.1.8 W51 — emit `hai stats --data-quality`.

    Strictly read-only per the capability manifest annotation
    (`mutation: read-only`). Reads from ``data_quality_daily`` only;
    never invokes the projector and never writes a row. If no rows
    exist for the requested window (e.g. ``hai clean`` has not run
    for the user yet), returns an empty rows list — surface that
    honestly rather than triggering a hidden write. Codex round-1
    P1-1 + round-2 R2-4 confirmed this is the correct contract.
    """

    from datetime import timedelta as _td

    from health_agent_infra.core.data_quality import read_data_quality_rows
    from health_agent_infra.core.state import open_connection

    today = datetime.now(timezone.utc).date()
    since = today - _td(days=max(0, since_days - 1))

    # v0.1.8 Codex P1-1 fix: this surface is contractually `read-only`
    # (capability manifest annotation). The previous lazy-projection
    # path was a contract violation. Data-quality rows are populated
    # by the `hai clean` write path; an empty result here means
    # `hai clean` hasn't run for the requested window yet — surface
    # that honestly rather than triggering a hidden write.
    conn = open_connection(db_path)
    try:
        rows = read_data_quality_rows(
            conn,
            user_id=user_id,
            since_date=since,
            until_date=today,
            domain=domain,
        )
    finally:
        conn.close()

    payload = {
        "as_of_date": today.isoformat(),
        "user_id": user_id,
        "since_days": since_days,
        "rows": rows,
    }

    if as_json:
        _emit_json(payload)
    else:
        sys.stdout.write(_render_data_quality_text(payload))
    return exit_codes.OK


def _render_data_quality_text(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        f"# Data quality — last {payload['since_days']} days "
        f"(user: {payload['user_id']})",
        "",
        "| Date | Domain | Source | Coverage | Missingness | Cold-start | Source unavail | User pending |",
        "|---|---|---|---|---|---|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['as_of_date']} | {row['domain']} | {row['source']} "
            f"| {row.get('coverage_band') or '—'} "
            f"| {row.get('missingness') or '—'} "
            f"| {row.get('cold_start_window_state') or '—'} "
            f"| {row['source_unavailable']} "
            f"| {row['user_input_pending']} |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def _daily_streak_from_events(conn: sqlite3.Connection) -> int:
    """Consecutive UTC calendar days ending today with ≥1 successful `hai daily`.

    Returns 0 if today doesn't have a successful run. The streak is
    counted backward from today (inclusive) — missing any intervening
    day breaks the chain. Robust to a pre-migration-012 DB: returns 0
    rather than crashing.
    """

    try:
        rows = conn.execute(
            "SELECT DISTINCT substr(started_at, 1, 10) AS day "
            "FROM runtime_event_log "
            "WHERE command = 'daily' AND status = 'ok' "
            "ORDER BY day DESC"
        ).fetchall()
    except sqlite3.OperationalError:
        return 0

    days_with_ok = {row["day"] for row in rows}
    if not days_with_ok:
        return 0

    streak = 0
    today = datetime.now(timezone.utc).date()
    cursor = today
    while cursor.isoformat() in days_with_ok:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _render_stats_text(report: dict[str, Any]) -> str:
    """Human-readable `hai stats` view. Stable enough for eyeballing."""

    lines: list[str] = []
    lines.append(f"hai stats  —  db: {report['db_path']}")
    lines.append(f"             user: {report['user_id']}")
    lines.append("")

    # Sync freshness
    lines.append("Sync freshness (last successful pull per source):")
    fresh = report["sync_freshness"]
    if not fresh:
        lines.append("  (no successful syncs yet — run `hai pull --live` or `hai daily`)")
    else:
        for source in sorted(fresh):
            row = fresh[source]
            started = row.get("started_at") or "—"
            for_date = row.get("for_date") or ""
            suffix = f"  for {for_date}" if for_date else ""
            lines.append(f"  {source:16s} {started}  {row.get('status'):<8s}{suffix}")
    lines.append("")

    # Recent events
    lines.append(f"Recent runs (runtime_event_log, last {len(report['recent_events'])}):")
    events = report["recent_events"]
    if not events:
        lines.append("  (no logged runs yet — `hai daily` starts recording once the DB exists)")
    else:
        for evt in events:
            started = evt.get("started_at") or "—"
            cmd = evt.get("command", "?")
            status = evt.get("status", "?")
            dur = evt.get("duration_ms")
            dur_s = f"{dur} ms" if dur is not None else "—"
            line = f"  {started}  {cmd:<8s} {status:<6s} {dur_s:>8s}"
            if evt.get("error_class"):
                line += f"   {evt['error_class']}: {evt.get('error_message', '')}"
            lines.append(line)
    lines.append("")

    # Command summary + streak
    lines.append("Command summary:")
    summary = report["command_summary"]
    if not summary:
        lines.append("  (no commands logged yet)")
    else:
        for cmd in sorted(summary):
            counts = summary[cmd]
            lines.append(
                f"  {cmd:<10s} ok: {counts.get('ok', 0):<4d} "
                f"failed: {counts.get('failed', 0):<4d} "
                f"total: {counts.get('total', 0)}"
            )
    lines.append("")

    streak = report["daily_streak_days"]
    streak_suffix = " (run `hai daily` today to start one)" if streak == 0 else ""
    lines.append(f"Daily streak: {streak} day(s){streak_suffix}")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------




def cmd_capabilities(args: argparse.Namespace) -> int:
    """Emit the agent-CLI-contract manifest as JSON or markdown.

    The manifest is built by walking the very parser the user just
    invoked, so the output reflects the exact CLI surface this process
    exposes — no risk of the manifest describing a different build.
    """

    from health_agent_infra.cli import build_parser
    manifest = build_manifest(build_parser())
    if getattr(args, "human", False):
        # New-user-facing one-page overview. Workflow-grouped, no
        # schema jargon. JSON manifest stays the agent-facing
        # authoritative surface.
        print(render_human(manifest), end="")
    elif getattr(args, "markdown", False):
        # Text form for operator-facing review; the --json form stays the
        # canonical machine-readable surface.
        print(render_markdown(manifest), end="")
    else:
        _emit_json(manifest)
    return exit_codes.OK


# ---------------------------------------------------------------------------
# hai demo — demo-mode session lifecycle (W-Va, v0.1.11)
# ---------------------------------------------------------------------------


# cmd_demo_* moved to cli/handlers/tools.py at W-29.2.6.
