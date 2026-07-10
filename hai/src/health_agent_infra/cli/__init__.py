"""`hai` CLI — thin subcommands over the deterministic runtime.

Subcommands:

    hai pull      — acquire Garmin evidence for a date, emit JSON
    hai clean     — normalize evidence into CleanedEvidence + RawSummary JSON
    hai propose   — append a DomainProposal to proposal_log
    hai synthesize — atomically commit the per-domain proposals as a daily plan
    hai review    — schedule review events, record outcomes, summarize history
    hai setup-skills — copy the packaged skills/ directory to ~/.claude/skills/

All judgment (state classification, policy, recommendation shaping) lives in
the markdown skills shipped with this package. This CLI is a tooling surface
for an agent to call; it does not reason about evidence.
"""

from __future__ import annotations

import argparse
import json
import uuid
import os
import shutil
import sqlite3
import sys
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Literal, Optional

from health_agent_infra import __version__ as _PACKAGE_VERSION
from health_agent_infra.core import exit_codes
from health_agent_infra.core.paths import resolve_base_dir
from health_agent_infra.core.capabilities import (
    annotate_choice_metadata,
    annotate_contract,
    build_manifest,
)
from health_agent_infra.core.capabilities.render import (
    render_human,
    render_markdown,
)
from health_agent_infra.core.clean import build_raw_summary, clean_inputs
from health_agent_infra.core.config import (
    ConfigError,
    load_thresholds,
    scaffold_thresholds_toml,
    user_config_path,
)
from health_agent_infra.core.pull.auth import (
    CredentialStore,
    KeyringUnavailableError,
)
from health_agent_infra.core.hermetic import (
    HermeticModeError,
    require_hermetic_recipe,
)
from health_agent_infra.core.runtime_mode import (
    RuntimeModeError,
    require_runtime_mode_allowed,
)
from health_agent_infra.core.pull.garmin import (
    GarminRecoveryReadinessAdapter,
    default_manual_readiness,
)
from health_agent_infra.core.pull.garmin_live import (
    GarminLiveAdapter,
    GarminLiveError,
    build_default_client,
)
from health_agent_infra.core.pull.intervals_icu import (
    IntervalsIcuAdapter,
    IntervalsIcuError,
    build_default_client as build_intervals_icu_client,
)
from health_agent_infra.core.review.outcomes import (
    ReLinkResolution,
    persist_review_event,
    record_review_outcome,
    resolve_review_relink,
    summarize_review_history,
)
from health_agent_infra.core.schemas import (
    ReviewEvent,
    ReviewOutcome,
)


from importlib.resources import as_file, files

PACKAGE_ROOT = Path(__file__).resolve().parent
# Skills ship inside the package at hai/src/health_agent_infra/skills/. Resolved
# via importlib.resources so `hai setup-skills` works in both editable and
# installed-wheel modes. Callers use ``_skills_source()`` as a context manager
# to materialise a real filesystem path (needed for shutil.copytree).
DEFAULT_CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"


def _skills_source():
    """Context manager yielding a filesystem Path to the packaged skills/ dir."""

    return as_file(files("health_agent_infra").joinpath("skills"))


def _coerce_date(value: str | None) -> date:
    if value is None:
        return datetime.now(timezone.utc).date()
    return date.fromisoformat(value)


def _coerce_dt(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _load_json_arg(
    path_value: str | None, *, arg_name: str, command_label: str,
) -> tuple[Any, int | None]:
    """Load a CLI-provided JSON-file argument into a Python object.

    Returns ``(data, None)`` on success or ``(None, exit_code)`` on
    failure. The exit code is ``USER_INPUT`` for both missing-file and
    malformed-JSON cases — both are caller-controlled inputs the
    command can't proceed without. A clear stderr line names the
    command, the flag, and the underlying error so an agent can route
    on it without parsing prose.

    This is the single consolidated implementation the v0.1.6 audit
    surfaced as missing — every CLI handler that takes a
    ``--*-json`` argument should route through here so bad paths /
    malformed JSON exit cleanly with USER_INPUT instead of escaping
    as an uncaught Python traceback.
    """

    if not path_value:
        print(
            f"{command_label}: {arg_name} is required.",
            file=sys.stderr,
        )
        return None, exit_codes.USER_INPUT
    try:
        raw = Path(path_value).read_text(encoding="utf-8")
    except OSError as exc:
        print(
            f"{command_label}: could not read {arg_name} "
            f"({path_value}): {exc}",
            file=sys.stderr,
        )
        return None, exit_codes.USER_INPUT
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as exc:
        print(
            f"{command_label}: {arg_name} is not valid JSON "
            f"({path_value}): {exc}",
            file=sys.stderr,
        )
        return None, exit_codes.USER_INPUT


def _emit_json(obj: Any) -> None:
    def default(o):
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        raise TypeError(f"not serializable: {type(o).__name__}")

    print(json.dumps(obj, default=default, indent=2, sort_keys=True))


# ---------------------------------------------------------------------------
# hai pull
# ---------------------------------------------------------------------------

class _DailyPullRefusal(Exception):
    """Raised by `_daily_pull_and_project` when the F-PV14-01 guard
    refuses a CSV-fixture pull against the canonical state DB. Caught
    by `_run_daily` and converted into the standard refused-stage
    report shape so the daily orchestrator never silently bypasses
    the guard."""

    def __init__(self, exit_code: int) -> None:
        self.exit_code = exit_code
        super().__init__(
            f"hai daily refused by F-PV14-01 CSV-canonical guard "
            f"(exit_code={exit_code})"
        )


# ---------------------------------------------------------------------------
# hai pull / hai clean — evidence acquisition (pull_clean group)
# ---------------------------------------------------------------------------
# W-29.2.9: handler bodies live in cli/handlers/pull_clean.py.
# Re-exports include _PROJECTION_RESULT_* constants used by intake
# helpers still in cli/__init__.py and PULL_SOURCE_CHOICE_METADATA
# referenced by build_parser.
from health_agent_infra.cli.handlers.pull_clean import (  # noqa: E402
    PULL_SOURCE_CHOICE_METADATA,
    _GARMIN_LIVE_WARNING,
    _PROJECTION_RESULT_FAILED,
    _PROJECTION_RESULT_OK,
    _PROJECTION_RESULT_SKIPPED_DB_ABSENT,
    _autoread_manual_readiness,
    _build_intervals_icu_adapter,
    _build_live_adapter,
    _close_sync_row_failed,
    _close_sync_row_ok,
    _enrich_raw_row_with_activity_aggregate,
    _evidence_hash,
    _f_pv14_csv_canonical_guard,
    _intervals_icu_configured,
    _open_sync_row,
    _project_clean_into_state,
    _resolve_pull_source,
    _sync_if_db,
    cmd_clean,
    cmd_pull,
)
def _dual_write_project(db_path_arg, project_fn, label: str) -> None:
    """Run a projector against the resolved state DB.

    Fails soft: if the DB doesn't exist or the projector raises, we print a
    stderr warning and return. The JSONL write is the audit boundary; the DB
    is a queryable projection that ``hai state reproject`` can rebuild.
    ``project_fn`` receives the open connection.
    """

    from health_agent_infra.core.state import open_connection, resolve_db_path

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        print(
            f"note: state DB projection skipped ({db_path} not found). "
            f"JSONL audit record is durable. Run `hai state init` to enable "
            f"DB dual-write.",
            file=sys.stderr,
        )
        return

    conn = open_connection(db_path)
    try:
        project_fn(conn)
    except Exception as exc:  # noqa: BLE001 — any DB failure becomes a warning
        print(
            f"warning: {label} projection into state DB failed: {exc}. "
            f"JSONL record is durable; run `hai state reproject --base-dir "
            f"<base-dir>` to recover.",
            file=sys.stderr,
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# hai auth garmin / hai auth status
# ---------------------------------------------------------------------------
# W-29.2: handler bodies live in cli/handlers/auth.py. Re-imported here so
# build_parser() can attach them via add_parser/set_defaults(func=...) without
# changing the parser-tree shape (manifest byte-stable per §2.A item 4).
from health_agent_infra.cli.handlers.auth import (  # noqa: E402
    _backend_kind,
    _credential_store_for,
    _print_keychain_acl_hint,
    cmd_auth_garmin,
    cmd_auth_intervals_icu,
    cmd_auth_remove,
    cmd_auth_status,
)

# ---------------------------------------------------------------------------
# hai propose / synthesize / daily — recommend group
# ---------------------------------------------------------------------------
# W-29.2.11: handler bodies live in cli/handlers/recommend.py.
from health_agent_infra.cli.handlers.recommend import (  # noqa: E402
    _daily_pull_and_project,
    _parse_daily_domains,
    _read_proposal_projection_meta,
    _run_daily,
    _schedule_reviews_for_daily_plan,
    cmd_daily,
    cmd_propose,
    cmd_synthesize,
)

# ---------------------------------------------------------------------------
# hai explain / today / stats / doctor / capabilities — inspect group
# ---------------------------------------------------------------------------
# W-29.2.8: handler bodies live in cli/handlers/inspect.py.
from health_agent_infra.cli.handlers.inspect import (  # noqa: E402
    _build_daily_explain_block,
    _daily_streak_from_events,
    _emit_baselines_stats,
    _emit_data_quality_stats,
    _emit_funnel_stats,
    _emit_outcomes_stats,
    _render_baselines_text,
    _render_data_quality_text,
    _render_funnel_text,
    _render_outcomes_text,
    _render_stats_text,
    _worst_status,
    cmd_capabilities,
    cmd_doctor,
    cmd_explain,
    cmd_stats,
    cmd_today,
)
from health_agent_infra.cli.handlers.tools import (  # noqa: E402
    _DAILY_SUPPORTED_DOMAINS,
    _demo_gate,
    _memory_counts,
    _memory_entry_to_dict,
    _memory_id_for,
    cmd_demo_cleanup,
    cmd_demo_end,
    cmd_demo_start,
    cmd_exercise_search,
    cmd_memory_archive,
    cmd_memory_list,
    cmd_memory_set,
    cmd_planned_session_types,
    cmd_research_search,
    cmd_research_topics,
)


# ---------------------------------------------------------------------------
# hai review
# ---------------------------------------------------------------------------
# W-29.2.2: handler bodies live in cli/handlers/review.py.
from health_agent_infra.cli.handlers.review import (  # noqa: E402
    cmd_review_record,
    cmd_review_schedule,
    cmd_review_summary,
    cmd_review_weekly,
)


# ---------------------------------------------------------------------------
# v0.1.8 W49 — intent ledger commands (`hai intent ...`)
# ---------------------------------------------------------------------------
# W-29.2.5: handler bodies + W57 gate live in cli/handlers/intent.py.
# Re-exported here so target.py + tests importing _intent_open_db /
# _w57_user_gate from health_agent_infra.cli keep resolving.
from health_agent_infra.cli.handlers.intent import (  # noqa: E402
    _add_intent_common,
    _agent_active_insert_gate,
    _intent_open_db,
    _intent_record_to_dict,
    _w57_user_gate,
    cmd_intent_archive,
    cmd_intent_commit,
    cmd_intent_list,
    cmd_intent_sleep_set_window,
    cmd_intent_training_add_session,
    cmd_intent_training_list,
)


# ---------------------------------------------------------------------------
# v0.1.8 W50 — target ledger commands (`hai target ...`)
# ---------------------------------------------------------------------------
# W-29.2.3: handler bodies live in cli/handlers/target.py.
from health_agent_infra.cli.handlers.target import (  # noqa: E402
    cmd_target_archive,
    cmd_target_commit,
    cmd_target_list,
    cmd_target_nutrition,
    cmd_target_set,
)


# cmd_review_summary moved to cli/handlers/review.py at W-29.2.2.


# ---------------------------------------------------------------------------
# hai intake — typed user inputs (intake group)
# ---------------------------------------------------------------------------
# W-29.2.10: handler bodies live in cli/handlers/intake.py.
# Re-exports include the choice-enum constants used by build_parser.
from health_agent_infra.cli.handlers.intake import (  # noqa: E402
    ENERGY_CHOICES,
    EXERCISE_CATEGORY_CHOICES,
    EXERCISE_EQUIPMENT_CHOICES,
    INTENSITY_DELTA_CHOICES,
    SORENESS_CHOICES,
    _project_context_note_into_state,
    _project_gym_submission_into_state,
    _project_nutrition_submission_into_state,
    _project_readiness_submission_into_state,
    _project_stress_submission_into_state,
    _resolve_prior_nutrition_submission,
    cmd_intake_exercise,
    cmd_intake_gaps,
    cmd_intake_gym,
    cmd_intake_note,
    cmd_intake_nutrition,
    cmd_intake_readiness,
    cmd_intake_stress,
    cmd_intake_weight,  # W-B (v0.1.17 §2.H) — body-comp intake
)
from health_agent_infra.cli.handlers.state import (  # noqa: E402
    cmd_backup,
    cmd_export,
    cmd_restore,
    cmd_state_init,
    cmd_state_migrate,
    cmd_state_read,
    cmd_state_reproject,
    cmd_state_snapshot,
    cmd_sync_purge,  # F-PV14-02 (v0.1.17 Phase 3); OQ-1 cohabits with state group
)


# ---------------------------------------------------------------------------
# hai setup-skills
# ---------------------------------------------------------------------------


def _load_cleaned_bundle(path_str: str) -> tuple[dict, dict, Optional[str]]:
    """Load a `hai clean` output JSON. Returns (evidence, raw_summary, error)."""

    path = Path(path_str).expanduser()
    if not path.exists():
        return {}, {}, f"evidence-json not found at {path}"
    try:
        bundle = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, {}, f"evidence-json is not valid JSON ({exc})"
    if "cleaned_evidence" not in bundle or "raw_summary" not in bundle:
        return {}, {}, (
            "evidence-json missing cleaned_evidence or raw_summary; "
            "did you pass the output of `hai clean`?"
        )
    return bundle["cleaned_evidence"], bundle["raw_summary"], None


# ---------------------------------------------------------------------------
# hai config / hai init / hai setup-skills handler group
# ---------------------------------------------------------------------------
# W-29.2.7: handler bodies live in cli/handlers/config_init.py.
# Re-exports include _walk_keys/_lookup/_MISSING/_review_summary_range_issues
# (used by cmd_config_validate + cmd_config_diff) and the init/onboarding
# helpers used by cmd_init.
from health_agent_infra.cli.handlers.config_init import (  # noqa: E402
    _MISSING,
    _lookup,
    _onboarding_default_pull_runner,
    _onboarding_default_today_renderer,
    _review_summary_range_issues,
    _run_first_pull_backfill,
    _run_guided_onboarding,
    _run_interactive_auth,
    _walk_keys,
    cmd_config_diff,
    cmd_config_init,
    cmd_config_show,
    cmd_config_validate,
    cmd_init,
    cmd_setup_skills,
)


# cmd_exercise_search moved to cli/handlers/tools.py at W-29.2.6.
# cmd_daily + _run_daily + helpers moved to cli/handlers/recommend.py at W-29.2.11.
# ---------------------------------------------------------------------------


# cmd_doctor + cmd_stats + helpers moved to cli/handlers/inspect.py at W-29.2.8.
def _register_eval_subparser(sub: argparse._SubParsersAction) -> None:
    """Register ``hai eval`` against the packaged eval framework.

    The framework lives inside the wheel at
    ``health_agent_infra.evals`` (runner + cli + scenarios + rubrics
    as package data). Registration is unconditional — the same surface
    is available in source checkouts and wheel installs.
    """

    from health_agent_infra.evals.cli import register_eval_subparser

    register_eval_subparser(sub)


# ---------------------------------------------------------------------------
# hai research — bounded local-only retrieval surface (v0.1.6 W17)
# ---------------------------------------------------------------------------
# Replaces the `python3 -c "from health_agent_infra.core.research import ..."`
# pattern the expert-explainer skill was using. Codex r2 (C4) flagged that
# `Bash(python3 -c *)` in the skill's allowed-tools is broader than the
# skill's "no network, local-only" privacy invariant: an agent obeying
# allowed-tools could legally `python3 -c "import urllib.request; ..."`
# without violating the permission grant. Moving retrieval onto a typed
# CLI shrinks the privacy boundary to a single, audit-traceable surface.


# cmd_research_* + cmd_planned_session_types moved to cli/handlers/tools.py at W-29.2.6.
# cmd_capabilities moved to cli/handlers/inspect.py at W-29.2.8.
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hai", description="Health Agent Infra CLI")
    parser.add_argument(
        "--version",
        action="version",
        version=f"hai {_PACKAGE_VERSION}",
        help="Print the installed package version and exit",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_pull = sub.add_parser("pull", help="Pull Garmin evidence for a date")
    # v0.1.11 W-Y (per Codex F-DEMO-03): `--as-of` is the canonical
    # civil-date flag across `hai daily / today / intake / explain`;
    # `--date` is the legacy spelling on `hai pull`. Both accepted
    # this cycle; `--date` deprecated and removed in v0.1.13 per the
    # tactical plan.
    p_pull.add_argument(
        "--date", "--as-of",
        dest="date",
        default=None,
        help=(
            "Civil date, ISO-8601 (default today UTC). "
            "`--as-of` is the canonical alias; `--date` retained for "
            "backwards compatibility (deprecated, removed in v0.1.13)."
        ),
    )
    p_pull.add_argument("--user-id", default="u_local_1")
    p_pull.add_argument("--manual-readiness-json", default=None,
                        help="Path to a JSON file with manual readiness fields")
    p_pull.add_argument("--use-default-manual-readiness", action="store_true",
                        help="Use a neutral manual readiness default (for offline runs)")
    p_pull.add_argument("--live", action="store_true",
                        help="Legacy flag: equivalent to --source garmin_live. "
                             "Garmin Connect is rate-limited and unreliable "
                             "for live scraping; prefer `--source "
                             "intervals_icu` (the maintainer's declared "
                             "supported live source as of v0.1.6).")
    p_pull_source = p_pull.add_argument(
        "--source",
        choices=("csv", "garmin_live", "intervals_icu"),
        default=None,
        help="Evidence source. csv reads the committed fixture; garmin_live "
             "scrapes Garmin Connect (best-effort: rate-limited, "
             "unreliable); intervals_icu pulls from Intervals.icu's "
             "wellness API — stable and the supported live source "
             "today, but scoped to what that service exposes "
             "(HRV + RHR + sleep + load; no per-session running "
             "granularity yet). Default (v0.1.6): intervals_icu when "
             "credentials are configured, else csv.",
    )
    annotate_choice_metadata(p_pull_source, PULL_SOURCE_CHOICE_METADATA)
    p_pull.add_argument("--history-days", type=int, default=14,
                        help="Trailing window size for resting_hr / hrv / "
                             "training_load series (live pull only). Matches "
                             "the CSV adapter default.")
    p_pull.add_argument("--db-path", default=None,
                        help="State DB path for sync_run_log writes. Best-effort — "
                             "if the DB is absent, the pull still runs but the "
                             "sync row is skipped. Default: `$HAI_STATE_DB` or "
                             "`~/.local/share/health_agent_infra/state.db`.")
    p_pull.add_argument(
        "--allow-fixture-into-real-state",
        action="store_true",
        help=(
            "Permit `--source csv` (committed CSV fixture) to write "
            "into the canonical state DB. Default-deny per F-PV14-01 "
            "(v0.1.15) — fixture data in the canonical DB corrupts "
            "user state. Use a `hai demo start` session or an "
            "explicit --db-path / HAI_STATE_DB override instead "
            "where possible."
        ),
    )
    p_pull.set_defaults(func=cmd_pull)
    annotate_contract(
        p_pull,
        mutation="writes-sync-log",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT", "TRANSIENT"),
        agent_safe=True,
        description=(
            "Acquire evidence for a date and emit cleaned evidence JSON. "
            "Source resolution (v0.1.6): explicit `--source` > legacy "
            "`--live` (= garmin_live) > intervals.icu when credentials "
            "are configured > csv fixture fallback. Garmin live is "
            "best-effort (rate-limited); intervals.icu is the supported "
            "live source. Writes a sync_run_log row; does not touch the "
            "main state tables."
        ),
    )

    p_auth = sub.add_parser("auth", help="Credential management for external sources")
    auth_sub = p_auth.add_subparsers(dest="auth_command", required=True)

    p_auth_garmin = auth_sub.add_parser(
        "garmin",
        help="Store Garmin credentials in the OS keyring (interactive by default)",
    )
    p_auth_garmin.add_argument("--email", default=None,
                               help="Garmin account email (prompts if omitted)")
    p_auth_garmin.add_argument("--password-stdin", action="store_true",
                               help="Read the Garmin password from a single "
                                    "line on stdin (for non-interactive use)")
    p_auth_garmin.add_argument("--password-env", default=None,
                               help="Read the Garmin password from the named "
                                    "environment variable")
    p_auth_garmin.set_defaults(func=cmd_auth_garmin)
    annotate_contract(
        p_auth_garmin,
        mutation="writes-credentials",
        idempotent="yes",  # replacing stored credentials with same pair is a no-op
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=False,  # interactive password prompt
        description=(
            "Store Garmin credentials in the OS keyring. Interactive by "
            "default; operator-only (requires a live password)."
        ),
    )

    p_auth_intervals_icu = auth_sub.add_parser(
        "intervals-icu",
        help="Store Intervals.icu credentials in the OS keyring (interactive by default)",
    )
    p_auth_intervals_icu.add_argument("--athlete-id", default=None,
                                      help="Intervals.icu athlete id (prompts if omitted)")
    p_auth_intervals_icu.add_argument("--api-key-stdin", action="store_true",
                                      help="Read the Intervals.icu API key from a "
                                           "single line on stdin (for non-interactive use)")
    p_auth_intervals_icu.add_argument("--api-key-env", default=None,
                                      help="Read the Intervals.icu API key from the "
                                           "named environment variable")
    p_auth_intervals_icu.set_defaults(func=cmd_auth_intervals_icu)
    annotate_contract(
        p_auth_intervals_icu,
        mutation="writes-credentials",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=False,
        description=(
            "Store Intervals.icu credentials in the OS keyring. "
            "Interactive by default; operator-only (requires a live API key)."
        ),
    )

    p_auth_status = auth_sub.add_parser(
        "status",
        help="Report whether credentials are configured (presence only, no secrets)",
    )
    p_auth_status.set_defaults(func=cmd_auth_status)
    annotate_contract(
        p_auth_status,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK",),
        agent_safe=True,
        description=(
            "Report whether Garmin and Intervals.icu credentials are "
            "configured. Presence only — never emits the secret itself."
        ),
    )

    p_auth_remove = auth_sub.add_parser(
        "remove",
        help="Remove stored credentials from the OS keyring (idempotent)",
    )
    p_auth_remove.add_argument(
        "--source",
        required=True,
        choices=("garmin", "intervals-icu", "all"),
        help=(
            "Which credential set to remove. 'all' removes both Garmin "
            "and Intervals.icu keyring entries. Env-var-supplied "
            "credentials are never touched."
        ),
    )
    p_auth_remove.set_defaults(func=cmd_auth_remove)
    annotate_contract(
        p_auth_remove,
        mutation="writes-credentials",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK",),
        agent_safe=False,
        description=(
            "Remove stored credentials from the OS keyring. "
            "Idempotent — removing absent credentials is a no-op. "
            "Env-var-supplied credentials are never touched."
        ),
    )

    p_clean = sub.add_parser("clean", help="Normalize pulled evidence + raw summary")
    p_clean.add_argument("--evidence-json", required=True,
                         help="Path to a JSON file produced by `hai pull`")
    p_clean.add_argument("--db-path", default=None,
                         help="State DB path (default: $HAI_STATE_DB or platform default). "
                              "If the DB is absent, projection is skipped with a stderr note; "
                              "stdout is unchanged.")
    p_clean.set_defaults(func=cmd_clean)
    annotate_contract(
        p_clean,
        mutation="writes-state",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Normalize pulled evidence into CleanedEvidence + RawSummary "
            "JSON and project accepted state rows. Best-effort projection "
            "when --db-path is absent."
        ),
    )

    p_prop = sub.add_parser(
        "propose",
        help="Validate and persist a DomainProposal JSON to proposal_log",
    )
    # Source choices from the validator's SUPPORTED_DOMAINS so the
    # parser and the invariant can never drift — any new supported
    # domain appears here automatically.
    from health_agent_infra.core.writeback.proposal import (
        SUPPORTED_DOMAINS as _PROPOSAL_DOMAINS,
    )
    p_prop.add_argument("--domain", required=True,
                        choices=sorted(_PROPOSAL_DOMAINS),
                        help="Domain whose proposal is being written")
    p_prop.add_argument("--proposal-json", required=True,
                        help="Path to a JSON file matching DomainProposal shape")
    p_prop.add_argument("--base-dir", required=False, default=None,
                        help="Writeback root; <domain>_proposals.jsonl will be appended here. "
                             "Default: $HAI_BASE_DIR or ~/.health_agent.")
    p_prop.add_argument("--db-path", default=None,
                        help="State DB path (default: `$HAI_STATE_DB` or `~/.local/share/health_agent_infra/state.db`)")
    p_prop.add_argument(
        "--replace", action="store_true", default=False,
        help=(
            "Revise an existing canonical proposal for "
            "(for_date, user_id, domain). Without --replace, a second "
            "propose for the same chain key exits USER_INPUT. With "
            "--replace, a new revision is inserted and the prior leaf's "
            "superseded_by_proposal_id is updated in a single "
            "transaction. If the new payload is byte-identical to the "
            "current leaf, --replace is a no-op. "
            "See hai/reporting/plans/v0_1_4/D1_re_author_semantics.md."
        ),
    )
    p_prop.set_defaults(func=cmd_propose)
    annotate_contract(
        p_prop,
        mutation="writes-state",
        idempotent="yes-with-replace",  # revision chain under --replace
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Validate a DomainProposal and append it to proposal_log. "
            "One of the three determinism boundaries the runtime "
            "enforces."
        ),
        preconditions=[
            "state_db_initialized",
            "proposal_json_validates_against_domain_schema",
        ],
        output_schema={
            "OK": {
                "shape": "JSON confirmation of the persisted proposal.",
                "json_keys": [
                    "proposal_id", "domain", "for_date", "user_id",
                    "revision", "superseded_by_proposal_id",
                ],
                "notes": (
                    "revision=1 on first-write; >1 after --replace. "
                    "superseded_by_proposal_id is NULL on the canonical "
                    "leaf."
                ),
            },
        },
    )

    p_syn = sub.add_parser(
        "synthesize",
        help="Read proposals + snapshot, run X-rules, atomically commit daily_plan + recommendations + firings",
    )
    p_syn.add_argument("--as-of", required=True,
                       help="Civil date to synthesize for, ISO-8601 YYYY-MM-DD")
    p_syn.add_argument("--user-id", required=True,
                       help="User whose proposals to reconcile")
    p_syn.add_argument("--drafts-json", default=None,
                       help="Optional JSON array of skill-authored draft recommendations. "
                            "When present, overlays rationale + uncertainty + review_question "
                            "onto the mechanical drafts. action / action_detail / confidence "
                            "are runtime-owned after Phase A and cannot be changed by the skill.")
    p_syn.add_argument("--supersede", action="store_true",
                       help="Keep the prior canonical plan and write a fresh suffixed "
                            "plan id. Default is atomic replacement.")
    p_syn.add_argument("--bundle-only", action="store_true",
                       help="Emit the synthesis bundle (snapshot + proposals + "
                            "Phase A firings) as JSON and exit. Read-only — "
                            "does not commit. This is the skill seam: the "
                            "daily-plan-synthesis skill reads the bundle, "
                            "composes a rationale overlay, and feeds it back "
                            "via a second call with --drafts-json.")
    p_syn.add_argument("--agent-version", default="claude_agent_v1",
                       help="Agent version string to record on every row "
                            "(not part of the canonical plan idempotency key)")
    p_syn.add_argument("--domains", default=None,
                       help="CSV-encoded expected-domain set (e.g. "
                            "'recovery,running'). When provided, synthesis "
                            "refuses to commit unless every named domain has "
                            "a canonical-leaf proposal in proposal_log. When "
                            "omitted, defaults to the v1 six-domain set "
                            "(recovery, running, sleep, stress, strength, "
                            "nutrition). Pass --domains '' to bypass the gate "
                            "entirely (matches pre-v0.1.9 permissive "
                            "behavior — discouraged for agent calls).")
    p_syn.add_argument("--db-path", default=None,
                       help="State DB path (default: `$HAI_STATE_DB` or `~/.local/share/health_agent_infra/state.db`)")
    p_syn.set_defaults(func=cmd_synthesize)
    annotate_contract(
        p_syn,
        mutation="writes-state",
        idempotent="yes-with-supersede",
        json_output="default",
        exit_codes=("OK", "USER_INPUT", "INTERNAL"),
        agent_safe=True,
        description=(
            "Run synthesis end-to-end inside one atomic SQLite "
            "transaction: daily_plan + x_rule_firings + "
            "planned_recommendation + recommendation_log. --supersede "
            "versions the plan instead of replacing it."
        ),
        preconditions=[
            "state_db_initialized",
            "proposal_log_has_row_for_each_target_domain",
            "state_snapshot_available_for_as_of",
        ],
        output_schema={
            "OK": {
                "shape": "JSON SynthesisResult confirmation.",
                "json_keys": [
                    "daily_plan_id", "recommendation_ids",
                    "proposal_ids", "phase_a_firings",
                    "phase_b_firings", "superseded_prior",
                ],
                "notes": (
                    "superseded_prior is NULL on canonical-replace "
                    "commits and set to the prior leaf's daily_plan_id "
                    "when --supersede was passed."
                ),
            },
        },
    )

    p_explain = sub.add_parser(
        "explain",
        help=(
            "Read-only audit-chain reconstruction for a committed plan: "
            "proposals, X-rule firings, final recommendations, "
            "supersession linkage, and review records."
        ),
    )
    p_explain.add_argument(
        "--daily-plan-id", default=None,
        help="Exact plan id to explain (e.g. 'plan_2026-04-17_u_local_1' "
             "or its '_v<N>' supersession variants). Mutually exclusive "
             "with --for-date / --user-id.",
    )
    p_explain.add_argument(
        # v0.1.11 W-Y (Codex F-DEMO-03): `--as-of` canonical alias.
        # `--for-date` retained for backwards compatibility; both
        # land on the same `for_date` dest. `--for-date` deprecated
        # and removed in v0.1.13 per the tactical plan.
        "--for-date", "--as-of",
        dest="for_date",
        default=None,
        help="Civil date of the canonical plan to explain, ISO-8601. "
             "Pair with --user-id. `--as-of` is the canonical alias; "
             "`--for-date` retained for backwards compatibility "
             "(deprecated, removed in v0.1.13).",
    )
    p_explain.add_argument(
        "--user-id", default=None,
        help="User whose canonical plan to explain. Pair with --for-date.",
    )
    # D3 §hai explain --operator — the dense text report is an operator/
    # debug surface, distinct from the user-facing ``hai today``. The
    # canonical flag is ``--operator`` as of v0.1.4; ``--text`` stays as
    # a deprecated alias for one release cycle so scripts don't break
    # mid-upgrade.
    p_explain.add_argument(
        "--operator", action="store_true",
        help="Render the bundle as a dense plain-text operator report "
             "instead of JSON. For end-user prose, use `hai today`.",
    )
    p_explain.add_argument(
        "--text", action="store_true",
        help="Deprecated alias for --operator. Will be removed in a "
             "future release; update scripts to use --operator.",
    )
    p_explain.add_argument(
        "--plan-version",
        choices=("latest", "first", "all"),
        default="latest",
        help=(
            "Which plan in a supersede chain to explain when "
            "--for-date is used. 'latest' (default) resolves the "
            "canonical leaf. 'first' returns the chain head. 'all' "
            "emits the full chain as a JSON array (or sequential "
            "text blocks with --text). Incompatible with "
            "--daily-plan-id, which already pins a specific plan. "
            "See hai/reporting/plans/v0_1_4/D1_re_author_semantics.md."
        ),
    )
    p_explain.add_argument("--db-path", default=None,
                           help="State DB path (default: `$HAI_STATE_DB` or `~/.local/share/health_agent_infra/state.db`)")
    p_explain.set_defaults(func=cmd_explain)
    annotate_contract(
        p_explain,
        mutation="read-only",
        idempotent="n/a",
        json_output="opt-out",  # JSON default; --operator (or deprecated --text) suppresses
        exit_codes=("OK", "USER_INPUT", "NOT_FOUND"),
        agent_safe=True,
        description=(
            "Reconstruct the full audit chain (planned / adapted / "
            "firings / performed) for a committed plan, including each "
            "recommendation's evidence card and its provenance (source "
            "proposal ids). Strictly read-only — never recomputes "
            "runtime state."
        ),
    )

    p_today = sub.add_parser(
        "today",
        help=(
            "Read today's plan in plain language. First-class non-agent-"
            "mediated user surface — no SQLite reading required."
        ),
    )
    p_today.add_argument(
        "--as-of", default=None,
        help="Civil date to read, ISO-8601. Default: today UTC.",
    )
    p_today.add_argument(
        "--user-id", default="u_local_1",
        help="User whose plan to read (default: u_local_1).",
    )
    p_today.add_argument(
        "--format", default=None, choices=("markdown", "plain", "json"),
        help=(
            "Output format. Defaults to 'markdown' on a TTY, 'plain' "
            "otherwise. 'json' emits the structured section shape."
        ),
    )
    p_today.add_argument(
        "--domain", default=None,
        choices=("recovery", "running", "sleep", "strength", "stress", "nutrition"),
        help="Narrow output to a single domain section.",
    )
    p_today.add_argument(
        "--db-path", default=None,
        help="State DB path (same semantics as other state commands).",
    )
    p_today.add_argument(
        "--verbose", action="store_true",
        help=(
            "Print classified-state internals alongside the plan. "
            "Currently surfaces strength_status; v0.1.13+ may extend."
        ),
    )
    p_today.set_defaults(func=cmd_today)
    # W-FCC (v0.1.12): import STRENGTH_STATUS_VALUES at parser-build time
    # so the capabilities manifest carries the enum surface as
    # data, not as documentation. The contract test
    # ``test_capabilities_strength_status_enum_surface`` keeps the
    # manifest in sync with the classifier.
    from health_agent_infra.domains.strength.classify import (
        STRENGTH_STATUS_VALUES,
    )
    annotate_contract(
        p_today,
        mutation="read-only",
        idempotent="n/a",
        json_output="opt-in",  # markdown/plain default; --format json opts in
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Render today's canonical plan in plain language — the "
            "non-agent-mediated user surface. Read-only."
        ),
        preconditions=[
            "state_db_initialized",
            "daily_plan_exists_for_as_of",
        ],
        output_schema={
            "OK": {
                "shape": "one of markdown|plain text (default) or a JSON "
                         "object with top_matter + summary + sections[].",
                "json_keys": [
                    "as_of_date", "user_id", "daily_plan_id",
                    "top_matter", "summary", "sections",
                ],
                "notes": "JSON format only emitted when --format json.",
                "enum_surface": {
                    "strength_status": list(STRENGTH_STATUS_VALUES),
                },
                "verbose_surface": (
                    "When --verbose is passed, a 'classified state' "
                    "footer is prepended showing strength_status (one of "
                    "the values in enum_surface.strength_status) and "
                    "other internal classifier outputs as v0.1.13+ "
                    "extends."
                ),
            },
        },
    )

    # --- hai memory (Phase D) ---
    from health_agent_infra.core.memory.schemas import USER_MEMORY_CATEGORIES

    p_memory = sub.add_parser(
        "memory",
        help=(
            "Explicit user memory — goals, preferences, constraints, "
            "and durable context notes. Local SQLite state, read by "
            "`hai state snapshot` and `hai explain`."
        ),
    )
    memory_sub = p_memory.add_subparsers(dest="memory_command", required=True)

    p_mset = memory_sub.add_parser(
        "set",
        help="Append one user-memory entry (append-only; use `archive` "
             "+ `set` to replace).",
    )
    p_mset.add_argument(
        "--category", required=True,
        choices=sorted(USER_MEMORY_CATEGORIES),
        help="Memory kind: goal | preference | constraint | context.",
    )
    p_mset.add_argument(
        "--value", required=True,
        help="Durable content (e.g. 'build strength through June', "
             "'no early-morning hard runs'). Non-empty.",
    )
    p_mset.add_argument(
        "--key", default=None,
        help="Optional short handle within the category "
             "(e.g. 'primary_goal', 'injury_left_knee').",
    )
    p_mset.add_argument(
        "--domain", default=None,
        help="Optional scoping domain (recovery | running | sleep | "
             "stress | strength | nutrition). Global if omitted.",
    )
    p_mset.add_argument(
        "--user-id", default="u_local_1",
        help="User the memory attaches to (default: u_local_1).",
    )
    p_mset.add_argument(
        "--memory-id", default=None,
        help="Optional explicit memory_id (default: "
             "deterministic `umem_<user>_<category>_<timestamp>`).",
    )
    p_mset.add_argument(
        "--source", default="user_manual",
        help="Fact origin (default: user_manual).",
    )
    p_mset.add_argument(
        "--ingest-actor", default="hai_cli_direct",
        choices=("hai_cli_direct", "claude_agent_v1"),
        help="Transport identity (default: hai_cli_direct).",
    )
    p_mset.add_argument(
        "--db-path", default=None,
        help="State DB path (default: `$HAI_STATE_DB` or `~/.local/share/health_agent_infra/state.db`).",
    )
    p_mset.set_defaults(func=cmd_memory_set)
    annotate_contract(
        p_mset,
        mutation="writes-memory",
        idempotent="no",  # append-only user_memory rows
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Append a user_memory entry (goal / preference / constraint "
            "/ context). Append-only — replace by archiving the old row "
            "and setting a new one."
        ),
    )

    p_mlist = memory_sub.add_parser(
        "list",
        help="List user-memory entries (active only by default).",
    )
    p_mlist.add_argument(
        "--user-id", default=None,
        help="Restrict to one user (default: every user).",
    )
    p_mlist.add_argument(
        "--category", default=None,
        choices=sorted(USER_MEMORY_CATEGORIES),
        help="Restrict to one category (default: every category).",
    )
    p_mlist.add_argument(
        "--include-archived", action="store_true",
        help="Also return archived entries (default: exclude).",
    )
    p_mlist.add_argument("--db-path", default=None)
    p_mlist.set_defaults(func=cmd_memory_list)
    annotate_contract(
        p_mlist,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "List user_memory entries active at a given date, grouped "
            "by category."
        ),
    )

    p_march = memory_sub.add_parser(
        "archive",
        help="Stamp `archived_at` on an active entry. Soft-delete; the "
             "row stays on disk so `list --include-archived` can audit.",
    )
    p_march.add_argument(
        "--memory-id", required=True,
        help="Memory id to archive.",
    )
    p_march.add_argument("--db-path", default=None)
    p_march.set_defaults(func=cmd_memory_archive)
    annotate_contract(
        p_march,
        mutation="writes-memory",
        idempotent="yes",  # re-archiving an already-archived row is a no-op
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Mark a user_memory entry archived (soft delete). The row "
            "itself stays for audit; read surfaces filter it out."
        ),
    )

    p_review = sub.add_parser("review", help="Review scheduling + outcome persistence")
    review_sub = p_review.add_subparsers(dest="review_command", required=True)

    p_rs = review_sub.add_parser("schedule", help="Persist a pending review event for a recommendation")
    p_rs.add_argument("--recommendation-json", required=True)
    p_rs.add_argument("--base-dir", required=False, default=None,
                      help="Writeback root for review_events.jsonl. "
                           "Default: $HAI_BASE_DIR or ~/.health_agent.")
    p_rs.add_argument("--db-path", default=None,
                      help="State DB path (default: `$HAI_STATE_DB` or `~/.local/share/health_agent_infra/state.db`)")
    p_rs.set_defaults(func=cmd_review_schedule)
    annotate_contract(
        p_rs,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Persist a pending review_event for a recommendation "
            "(used to schedule the next-day review question)."
        ),
    )

    p_rr = review_sub.add_parser("record", help="Record a review outcome")
    p_rr.add_argument("--outcome-json", required=True)
    p_rr.add_argument("--base-dir", required=False, default=None,
                      help="Writeback root for review_outcomes.jsonl. "
                           "Default: $HAI_BASE_DIR or ~/.health_agent.")
    p_rr.add_argument("--db-path", default=None,
                      help="State DB path (default: `$HAI_STATE_DB` or `~/.local/share/health_agent_infra/state.db`)")
    # M4 enrichment flags. All optional; each overrides the same key in
    # --outcome-json when both are provided. Omitted flags + JSON-absent
    # fields land NULL in the DB, which is the pre-M4 shape.
    p_rr.add_argument(
        "--completed", choices=("yes", "no"), default=None,
        help="Whether the user completed the recommended session.",
    )
    p_rr.add_argument(
        "--intensity-delta",
        choices=INTENSITY_DELTA_CHOICES, default=None,
        help=(
            "Intensity the user applied relative to the recommendation. "
            "Ordinals used by summary aggregation: "
            "much_lighter=-2, lighter=-1, same=0, harder=1, much_harder=2."
        ),
    )
    p_rr.add_argument(
        "--duration-minutes", type=int, default=None,
        help="Actual session duration in whole minutes.",
    )
    p_rr.add_argument(
        "--pre-energy", type=int, choices=range(1, 6), default=None,
        help="Self-reported energy score before the session, 1–5.",
    )
    p_rr.add_argument(
        "--post-energy", type=int, choices=range(1, 6), default=None,
        help="Self-reported energy score after the session, 1–5.",
    )
    p_rr.add_argument(
        "--disagreed-firings", default=None,
        help=(
            "Comma-separated x_rule_firing.firing_id list the user "
            "marked as 'should not have fired'. Empty string records an "
            "explicit empty list (the question was asked, no disagreement)."
        ),
    )
    p_rr.set_defaults(func=cmd_review_record)
    annotate_contract(
        p_rr,
        mutation="writes-state",
        idempotent="no",  # append-only review_outcome rows
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Record a review_outcome against a review_event. Carries "
            "the migration-010 enrichment columns (completed, "
            "intensity_delta, pre/post_energy, disagreed_firing_ids)."
        ),
        preconditions=[
            "review_event_exists_for_event_id",
            "recommendation_exists_for_recommendation_id",
        ],
        output_schema={
            "OK": {
                "shape": "JSON confirmation of the persisted outcome.",
                "json_keys": [
                    "review_event_id", "recommendation_id", "user_id",
                    "domain", "followed_recommendation",
                    "self_reported_improvement",
                    "re_linked_from_recommendation_id", "re_link_note",
                ],
                "notes": (
                    "When the target rec's plan has been superseded, "
                    "recommendation_id is the leaf rec and "
                    "re_linked_from_recommendation_id is the original. "
                    "Refusal (leaf has no matching-domain rec) exits "
                    "USER_INPUT with no write."
                ),
            },
        },
    )

    p_rsum = review_sub.add_parser("summary", help="Summarize outcome history counts")
    p_rsum.add_argument("--base-dir", required=False, default=None,
                        help="Writeback root to read review_outcomes.jsonl from. "
                             "Default: $HAI_BASE_DIR or ~/.health_agent.")
    p_rsum.add_argument("--user-id", default=None)
    p_rsum.add_argument("--domain", default=None,
                        help="Restrict counts to a single domain "
                             "(e.g. 'recovery' or 'running'). Omitted = all domains.")
    p_rsum.set_defaults(func=cmd_review_summary)
    annotate_contract(
        p_rsum,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Summarize review_outcome counts (followed / not-followed, "
            "per-domain tallies)."
        ),
    )

    # v0.2.0 W52 — `hai review weekly` aggregation surface.
    p_rweek = review_sub.add_parser(
        "weekly",
        help=(
            "Aggregate the past week's plan evidence and render a "
            "human-readable (markdown) or machine-readable (JSON) "
            "review."
        ),
    )
    p_rweek.add_argument(
        "--week", required=True,
        help="ISO week of shape 'YYYY-Www' (e.g. '2026-W18').",
    )
    output_group = p_rweek.add_mutually_exclusive_group()
    output_group.add_argument(
        "--json", dest="json", action="store_true",
        help="Emit JSON output (default: markdown).",
    )
    output_group.add_argument(
        "--markdown", dest="json", action="store_false",
        help="Emit markdown output (default).",
    )
    p_rweek.set_defaults(json=False)
    p_rweek.add_argument(
        "--user-id", default="u_local_1",
        help="User identifier (default: 'u_local_1').",
    )
    p_rweek.add_argument(
        "--coverage-threshold", type=int, default=None,
        help=(
            "Override the partial-week abstain threshold (days with "
            "canonical plans needed to render quantitative prose). "
            "Default reads from thresholds.toml "
            "policy.review_weekly.coverage_threshold_days (5)."
        ),
    )
    p_rweek.add_argument(
        "--include-history", action="store_true",
        help=(
            "Include superseded weekly_claim_card rows alongside "
            "canonical-latest in --json output. Valid only with "
            "--json (markdown shows canonical-latest only)."
        ),
    )
    p_rweek.add_argument(
        "--db-path", default=None,
        help="State DB path (default: $HAI_STATE_DB or platform default).",
    )
    p_rweek.add_argument(
        "--bypass-factuality-gate",
        action="store_true",
        help=(
            "DEVELOPER-ONLY override — disables the v0.2.0 W58D "
            "deterministic factuality gate. The default path runs the "
            "gate over every quantitative + comparative atom in the "
            "rendered prose; if any atom fails to resolve against "
            "source state the command exits INTERNAL and names the "
            "blocked atom on stderr. With this flag set the gate is "
            "skipped and a WARN is logged. Agents MUST NOT use this "
            "flag — its presence on a render is an audit-chain hazard."
        ),
    )
    p_rweek.set_defaults(func=cmd_review_weekly)
    annotate_contract(
        p_rweek,
        mutation="writes-state",
        idempotent="no",
        json_output="opt-in",
        exit_codes=("OK", "USER_INPUT", "INTERNAL"),
        agent_safe=True,
        description=(
            "Render the weekly review surface — markdown or JSON — "
            "from the canonical (non-superseded) plan evidence for "
            "the requested ISO week. Emits an abstain branch when "
            "fewer than the threshold of days have canonical plans. "
            "On the non-abstain path also persists weekly_claim_card "
            "rows (one per quantitative + comparative atomic claim) "
            "for downstream W58D factuality validation; cards are "
            "append-only so re-running with corrected data adds "
            "rows and the canonical-latest view returns the newest set."
        ),
    )

    # ---------------------------------------------------------------------
    # v0.1.8 W49 — `hai intent ...` ledger commands.
    #
    # Subparser layout matches PLAN.md § 2 W49:
    #   hai intent training add-session
    #   hai intent training list
    #   hai intent sleep set-window
    #   hai intent list
    #   hai intent archive
    # ---------------------------------------------------------------------
    p_intent = sub.add_parser(
        "intent",
        help="User-authored intent ledger (training plans, sleep windows, rest days, travel, constraints).",
    )
    intent_sub = p_intent.add_subparsers(dest="intent_command", required=True)

    def _intent_common_flags(p) -> None:
        p.add_argument("--db-path", default=None,
                       help="Override state DB path (default: $HAI_STATE_DB or platform default).")
        p.add_argument("--user-id", default="u_local_1",
                       help="User scope (default: u_local_1).")

    def _intent_add_flags(p) -> None:
        _intent_common_flags(p)
        p.add_argument("--scope-start", required=True,
                       help="ISO civil date the intent's window starts on.")
        p.add_argument("--scope-end", default=None,
                       help="ISO civil date the window ends on (defaults to scope-start for day-scoped intent).")
        p.add_argument("--scope-type", choices=("day", "week", "date_range"), default="day",
                       help="Window type. Default: day.")
        p.add_argument("--status", choices=("proposed", "active"), default="active",
                       help="Initial row status. Agent-proposed rows MUST land as 'proposed' and require explicit user confirm before flipping to 'active'.")
        p.add_argument("--priority", choices=("low", "normal", "high"), default="normal")
        p.add_argument("--flexibility", choices=("fixed", "flexible", "optional"), default="flexible")
        p.add_argument("--reason", default="",
                       help="Why this intent exists (free text; goes into the audit trail).")
        p.add_argument("--source", default="user_authored",
                       help="Provenance: 'user_authored' (default) or 'agent_proposed'.")
        p.add_argument("--ingest-actor", default="cli",
                       help="What inserted the row (default: cli).")
        p.add_argument("--payload-json", default=None,
                       help="Optional JSON-encoded structured detail (action, distance, weights, etc.).")

    # hai intent training {add-session, list}
    p_intent_training = intent_sub.add_parser(
        "training", help="Training-session intent shortcuts."
    )
    intent_training_sub = p_intent_training.add_subparsers(
        dest="intent_training_command", required=True,
    )

    p_it_add = intent_training_sub.add_parser(
        "add-session",
        help="Record a planned training session (running by default; pass --domain strength for strength).",
    )
    _intent_add_flags(p_it_add)
    p_it_add.add_argument("--domain", choices=("running", "strength"), default="running",
                          help="Training domain (default: running).")
    p_it_add.add_argument(
        "--intent-type", default="training_session",
        help="Override intent_type (default: training_session).",
    )
    p_it_add.set_defaults(func=cmd_intent_training_add_session)
    annotate_contract(
        p_it_add,
        mutation="writes-state",
        idempotent="no",  # one row per call
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Insert a user-authored training-session intent into the W49 intent ledger.",
    )

    p_it_list = intent_training_sub.add_parser(
        "list",
        help="List training-domain intent rows (active by default; --all returns every row).",
    )
    _intent_common_flags(p_it_list)
    p_it_list.add_argument("--as-of", default=None,
                           help="Civil date to test active-window membership against (default: today).")
    p_it_list.add_argument("--all", action="store_true",
                           help="Return every training intent row, not just active.")
    p_it_list.add_argument("--status", default=None,
                           help="When --all is set, filter by status.")
    p_it_list.set_defaults(func=cmd_intent_training_list)
    annotate_contract(
        p_it_list,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="List training intent rows from the W49 ledger.",
    )

    # hai intent sleep set-window
    p_intent_sleep = intent_sub.add_parser(
        "sleep", help="Sleep-window intent shortcuts."
    )
    intent_sleep_sub = p_intent_sleep.add_subparsers(
        dest="intent_sleep_command", required=True,
    )
    p_isw = intent_sleep_sub.add_parser(
        "set-window",
        help="Record a planned sleep window (e.g. 22:30 → 06:30).",
    )
    _intent_add_flags(p_isw)
    p_isw.add_argument("--domain", default="sleep",
                       help="Defaults to sleep; override only if you really mean it.")
    p_isw.add_argument(
        "--intent-type", default="sleep_window",
        help="Override intent_type (default: sleep_window).",
    )
    p_isw.set_defaults(func=cmd_intent_sleep_set_window)
    annotate_contract(
        p_isw,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Insert a sleep-window intent into the W49 intent ledger.",
    )

    # hai intent list
    p_il = intent_sub.add_parser(
        "list",
        help="List intent rows (default: active rows whose scope window covers today).",
    )
    _intent_common_flags(p_il)
    p_il.add_argument("--as-of", default=None,
                      help="Civil date to test active-window membership against (default: today).")
    p_il.add_argument("--domain", default=None,
                      help="Restrict to a single v1 domain.")
    p_il.add_argument("--all", action="store_true",
                      help="Return every intent row, not just active.")
    p_il.add_argument("--status", default=None,
                      help="When --all is set, filter by status.")
    p_il.set_defaults(func=cmd_intent_list)
    annotate_contract(
        p_il,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="List intent rows from the W49 ledger; default-active.",
    )

    # hai intent commit (W57 / Codex P1-2 fix)
    p_ic = intent_sub.add_parser(
        "commit",
        help="Promote a 'proposed' intent row to 'active'. The W57-required user-gated path for agent-proposed rows.",
    )
    _intent_common_flags(p_ic)
    p_ic.add_argument("--intent-id", required=True,
                      help="Intent id to promote (must currently be 'proposed').")
    p_ic.add_argument("--confirm", action="store_true",
                      help="Required for non-interactive callers (e.g. agents). "
                           "Confirms the W57 user-gated mutation. Interactive "
                           "stdin invocations are accepted without --confirm.")
    p_ic.set_defaults(func=cmd_intent_commit)
    annotate_contract(
        p_ic,
        mutation="writes-state",
        idempotent="yes-with-supersede",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=False,
        description=(
            "Promote a proposed intent row to active. Marked NOT "
            "agent-safe: agents that proposed the row must NOT auto-"
            "promote it; only an explicit user invocation may run "
            "this command."
        ),
    )

    # hai intent archive (W57 — archive of an active row IS deactivation)
    p_ia = intent_sub.add_parser(
        "archive",
        help="Archive an intent row (status='archived'). Row remains visible to the audit chain. The W57-required user-gated path for deactivating active or proposed rows.",
    )
    _intent_common_flags(p_ia)
    p_ia.add_argument("--intent-id", required=True,
                      help="Intent id to archive.")
    p_ia.add_argument("--confirm", action="store_true",
                      help="Required for non-interactive callers (e.g. agents). "
                           "Confirms the W57 user-gated mutation. Interactive "
                           "stdin invocations are accepted without --confirm.")
    p_ia.set_defaults(func=cmd_intent_archive)
    annotate_contract(
        p_ia,
        mutation="writes-state",
        idempotent="yes-with-supersede",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=False,
        description=(
            "Archive a W49 intent row (status='archived'). Marked NOT "
            "agent-safe: archiving an active or proposed row IS user-"
            "state deactivation per AGENTS.md W57. Agents that proposed "
            "the row must NOT auto-archive it; only an explicit user "
            "invocation may run this command."
        ),
    )

    # ---------------------------------------------------------------------
    # v0.1.8 W50 — `hai target ...` ledger commands.
    # ---------------------------------------------------------------------
    p_target = sub.add_parser(
        "target",
        help="User-authored target ledger (hydration, protein, calories, sleep, training-load aims).",
    )
    target_sub = p_target.add_subparsers(dest="target_command", required=True)

    def _target_common_flags(p) -> None:
        p.add_argument("--db-path", default=None,
                       help="Override state DB path.")
        p.add_argument("--user-id", default="u_local_1",
                       help="User scope (default: u_local_1).")

    p_ts = target_sub.add_parser(
        "set",
        help="Persist a new target row. Replacements use supersede; this command always appends.",
    )
    _target_common_flags(p_ts)
    p_ts.add_argument("--domain", required=True,
                      help="Wellness domain the target belongs to (e.g. nutrition, sleep, running).")
    p_ts.add_argument("--target-type", required=True,
                      choices=("hydration_ml", "protein_g", "calories_kcal",
                               # v0.1.15 W-C: macro-group target types.
                               "carbs_g", "fat_g",
                               "sleep_duration_h", "sleep_window", "training_load",
                               "other"),
                      help="One of the v1 target types.")
    p_ts.add_argument("--value", default=None,
                      help="Scalar target value (number or string). Use --value-json for richer structures.")
    p_ts.add_argument("--value-json", default=None,
                      help="JSON-encoded structured value (overrides --value when both are present).")
    p_ts.add_argument("--unit", required=True,
                      help="Unit string (e.g. 'ml', 'g', 'kcal', 'h').")
    p_ts.add_argument("--lower-bound", type=float, default=None,
                      help="Optional lower acceptable bound.")
    p_ts.add_argument("--upper-bound", type=float, default=None,
                      help="Optional upper acceptable bound.")
    p_ts.add_argument("--effective-from", required=True,
                      help="ISO civil date the target becomes active.")
    p_ts.add_argument("--effective-to", default=None,
                      help="ISO civil date the target stops being active (open-ended when omitted).")
    p_ts.add_argument("--review-after", default=None,
                      help="ISO civil date the target should be reviewed.")
    p_ts.add_argument("--status", choices=("proposed", "active"), default="active",
                      help="Initial row status. Agent-proposed rows MUST land as 'proposed'.")
    p_ts.add_argument("--reason", default="",
                      help="Why this target exists.")
    p_ts.add_argument("--source", default="user_authored",
                      help="'user_authored' (default) or 'agent_proposed'.")
    p_ts.add_argument("--ingest-actor", default="cli",
                      help="What inserted the row (default: cli).")
    p_ts.set_defaults(func=cmd_target_set)
    annotate_contract(
        p_ts,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Insert a wellness target into the W50 target ledger. Wellness support, not a medical prescription.",
    )

    p_tl = target_sub.add_parser(
        "list",
        help="List target rows (default: active rows that cover today).",
    )
    _target_common_flags(p_tl)
    p_tl.add_argument("--as-of", default=None,
                      help="Civil date to test active-window membership against (default: today).")
    p_tl.add_argument("--domain", default=None,
                      help="Restrict to a single wellness domain.")
    p_tl.add_argument("--target-type", default=None,
                      help="Restrict to a single target_type.")
    p_tl.add_argument("--status", default=None,
                      help="When --all is set, filter by status.")
    p_tl.add_argument("--all", action="store_true",
                      help="Return every target row, not just active.")
    p_tl.set_defaults(func=cmd_target_list)
    annotate_contract(
        p_tl,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="List target rows from the W50 ledger; default-active.",
    )

    # hai target commit (W57 / Codex P1-2 fix)
    p_tc = target_sub.add_parser(
        "commit",
        help="Promote a 'proposed' target row to 'active'. The W57-required user-gated path for agent-proposed rows.",
    )
    _target_common_flags(p_tc)
    p_tc.add_argument("--target-id", required=True,
                      help="Target id to promote (must currently be 'proposed').")
    p_tc.add_argument("--confirm", action="store_true",
                      help="Required for non-interactive callers (e.g. agents). "
                           "Confirms the W57 user-gated mutation. Interactive "
                           "stdin invocations are accepted without --confirm.")
    p_tc.set_defaults(func=cmd_target_commit)
    annotate_contract(
        p_tc,
        mutation="writes-state",
        idempotent="yes-with-supersede",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=False,
        description=(
            "Promote a proposed target row to active. Marked NOT "
            "agent-safe: agents that proposed the row must NOT auto-"
            "promote it; only an explicit user invocation may run "
            "this command."
        ),
    )

    # hai target archive (W57 — archive of an active row IS deactivation)
    p_ta = target_sub.add_parser(
        "archive",
        help="Archive a target row (status='archived'). Non-destructive. The W57-required user-gated path for deactivating active or proposed rows.",
    )
    _target_common_flags(p_ta)
    p_ta.add_argument("--target-id", required=True,
                      help="Target id to archive.")
    p_ta.add_argument("--confirm", action="store_true",
                      help="Required for non-interactive callers (e.g. agents). "
                           "Confirms the W57 user-gated mutation. Interactive "
                           "stdin invocations are accepted without --confirm.")
    p_ta.set_defaults(func=cmd_target_archive)
    annotate_contract(
        p_ta,
        mutation="writes-state",
        idempotent="yes-with-supersede",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=False,
        description=(
            "Archive a W50 target row (status='archived'). Marked NOT "
            "agent-safe: archiving an active or proposed row IS user-"
            "state deactivation per AGENTS.md W57. Agents that proposed "
            "the row must NOT auto-archive it; only an explicit user "
            "invocation may run this command."
        ),
    )

    # v0.1.15 W-C — `hai target nutrition` macro-group convenience.
    p_tn = target_sub.add_parser(
        "nutrition",
        help=(
            "Write 4 atomic nutrition macro target rows (kcal + "
            "protein_g + carbs_g + fat_g) in a single transaction. "
            "Convenience wrapper over the existing W50 target ledger."
        ),
    )
    _target_common_flags(p_tn)
    p_tn.add_argument("--kcal", type=int, required=True,
                      help="Daily calorie target (integer, kcal).")
    p_tn.add_argument("--protein-g", type=int, required=True,
                      help="Daily protein target (integer, grams).")
    p_tn.add_argument("--carbs-g", type=int, required=True,
                      help="Daily carbohydrate target (integer, grams).")
    p_tn.add_argument("--fat-g", type=int, required=True,
                      help="Daily fat target (integer, grams).")
    p_tn.add_argument("--phase", default="default",
                      help="Phase label (e.g. 'cut', 'maintain', 'bulk'). "
                           "Captured in the rows' reason as a query convention "
                           "(`reason LIKE '<phase>:%%'`); free-text token.")
    p_tn.add_argument("--effective-from", default=None,
                      help="ISO civil date the targets become active. "
                           "Default: today.")
    p_tn.add_argument("--reason", default=None,
                      help="Optional free-text reason appended after the "
                           "phase label in the rows' reason column.")
    p_tn.add_argument("--ingest-actor", default="cli",
                      help="Set to a named agent identifier (e.g. "
                           "'claude_agent_v1') for agent-proposed rows; "
                           "otherwise leave at 'cli' for user-authored "
                           "rows. The W57 invariant at "
                           "core/target/store.py:160-168 derives "
                           "source/status pairing from this value.")
    p_tn.set_defaults(func=cmd_target_nutrition)
    annotate_contract(
        p_tn,
        mutation="writes-state",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Write 4 atomic nutrition macro target rows (calories_kcal "
            "+ protein_g + carbs_g + fat_g) in a single BEGIN IMMEDIATE "
            "/ COMMIT. Source/status pairing per W57: agent-actor → "
            "agent_proposed/proposed; otherwise user_authored/active. "
            "Natural-key idempotency: identical re-invocation is a "
            "no-op. Agent-safe because both paths respect W57; the "
            "agent-path rows still require per-row `hai target commit` "
            "before they go active."
        ),
    )

    p_intake = sub.add_parser("intake", help="Typed human-input intake surfaces")
    intake_sub = p_intake.add_subparsers(dest="intake_command", required=True)

    p_ig = intake_sub.add_parser(
        "gym",
        help="Log a gym session (or one set) as raw user-reported evidence",
    )
    # Per-set mode
    p_ig.add_argument("--session-id", default=None,
                      help="Stable identifier for the session; multiple invocations "
                           "with the same id accumulate sets under one session")
    p_ig.add_argument("--session-name", default=None,
                      help="Human-readable label (e.g. 'Bench day')")
    p_ig.add_argument("--notes", default=None,
                      help="Free-text notes for the session header")
    p_ig.add_argument("--exercise", default=None,
                      help="Exercise name for this set (e.g. 'Bench Press')")
    p_ig.add_argument("--set-number", type=int, default=None,
                      help="1-based set ordinal within the session")
    p_ig.add_argument("--weight-kg", type=float, default=None,
                      help="Weight lifted in kilograms (omit for bodyweight)")
    p_ig.add_argument("--reps", type=int, default=None,
                      help="Reps completed in this set")
    p_ig.add_argument("--rpe", type=float, default=None,
                      help="Rate of perceived exertion (1-10). Optional.")
    # Bulk mode
    p_ig.add_argument("--session-json", default=None,
                      help="Path to a JSON file with {session_id, session_name?, "
                           "as_of_date?, notes?, sets: [...]}. Bulk alternative to "
                           "per-set flags.")
    # Common
    p_ig.add_argument("--as-of", default=None,
                      help="Civil date this session belongs to (ISO-8601, "
                           "default today UTC)")
    p_ig.add_argument("--user-id", default="u_local_1")
    p_ig.add_argument("--ingest-actor", default="hai_cli_direct",
                      choices=("hai_cli_direct", "claude_agent_v1"),
                      help="Transport identity. 'hai_cli_direct' for typed-by-user; "
                           "'claude_agent_v1' when the agent mediates.")
    p_ig.add_argument("--base-dir", required=False, default=None,
                      help="Intake root (where gym_sessions.jsonl will be appended). "
                           "Default: $HAI_BASE_DIR or ~/.health_agent.")
    p_ig.add_argument("--db-path", default=None,
                      help="State DB path (default: `$HAI_STATE_DB` or `~/.local/share/health_agent_infra/state.db`)")
    p_ig.set_defaults(func=cmd_intake_gym)
    annotate_contract(
        p_ig,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Record a gym session (sets + exercises) as typed human-input.",
    )

    p_ie = intake_sub.add_parser(
        "exercise",
        help="Add a user-defined exercise-taxonomy row for future matching",
    )
    p_ie.add_argument("--name", required=True,
                      help="Canonical display name for the new lift")
    p_ie.add_argument("--primary-muscle-group", required=True,
                      help="Primary muscle group label stored on the taxonomy row")
    p_ie.add_argument("--category", required=True,
                      choices=EXERCISE_CATEGORY_CHOICES,
                      help="Taxonomy category: compound | isolation")
    p_ie.add_argument("--equipment", required=True,
                      choices=EXERCISE_EQUIPMENT_CHOICES,
                      help="Equipment bucket used in exercise search")
    p_ie.add_argument("--exercise-id", default=None,
                      help="Optional explicit taxonomy id. Defaults to a "
                           "deterministic snake_case slug of --name")
    p_ie.add_argument("--aliases", default=None,
                      help="Optional comma- or pipe-separated aliases")
    p_ie.add_argument("--secondary-muscle-groups", default=None,
                      help="Optional comma- or pipe-separated secondary groups")
    p_ie.add_argument("--db-path", default=None,
                      help="State DB path (default: platformdirs user_data_dir)")
    p_ie.set_defaults(func=cmd_intake_exercise)
    annotate_contract(
        p_ie,
        mutation="writes-state",
        idempotent="yes",  # upserts the taxonomy entry by slug
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Upsert an exercise taxonomy entry.",
    )

    p_in = intake_sub.add_parser(
        "nutrition",
        help="Log a day's nutrition aggregate (calories + macros) as raw "
             "user-reported evidence. Re-running for the same day is a "
             "correction (supersedes chain + corrected_at).",
    )
    p_in.add_argument("--calories", type=float, required=True,
                      help="Total calories consumed that day")
    p_in.add_argument("--protein-g", type=float, required=True,
                      help="Total protein in grams")
    p_in.add_argument("--carbs-g", type=float, required=True,
                      help="Total carbohydrates in grams")
    p_in.add_argument("--fat-g", type=float, required=True,
                      help="Total fat in grams")
    p_in.add_argument("--hydration-l", type=float, default=None,
                      help="Total hydration in litres. Optional.")
    p_in.add_argument("--meals-count", type=int, default=None,
                      help="Number of distinct meals. Optional.")
    p_in.add_argument("--as-of", default=None,
                      help="Civil date this intake belongs to (ISO-8601, "
                           "default today UTC)")
    p_in.add_argument("--user-id", default="u_local_1")
    p_in.add_argument("--ingest-actor", default="hai_cli_direct",
                      choices=("hai_cli_direct", "claude_agent_v1"))
    p_in.add_argument("--base-dir", required=False, default=None,
                      help="Intake root (nutrition_intake.jsonl lands here). "
                           "Default: $HAI_BASE_DIR or ~/.health_agent.")
    p_in.add_argument("--db-path", default=None,
                      help="State DB path (same semantics as other intake cmds)")
    p_in.add_argument("--replace", action="store_true",
                      help="v0.1.7 W34: required when an existing same-day "
                           "nutrition row exists. Without it, hai intake "
                           "nutrition refuses with USER_INPUT to prevent "
                           "silent supersede chains. Nutrition is a daily "
                           "total, not per-meal — use this flag only when "
                           "deliberately correcting the prior daily entry.")
    p_in.set_defaults(func=cmd_intake_nutrition)
    annotate_contract(
        p_in,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Record a macros-only nutrition intake entry.",
    )

    p_is = intake_sub.add_parser(
        "stress",
        help="Log a subjective stress score (1-5) for a day. Re-running "
             "for the same day is a correction.",
    )
    p_is.add_argument("--score", type=int, choices=(1, 2, 3, 4, 5),
                      required=True,
                      help="Subjective stress band: 1=very low, 5=very high")
    p_is.add_argument("--tags", default=None,
                      help="Comma-separated tags (e.g. 'work,deadline')")
    p_is.add_argument("--as-of", default=None,
                      help="Civil date this score belongs to (ISO-8601, "
                           "default today UTC)")
    p_is.add_argument("--user-id", default="u_local_1")
    p_is.add_argument("--ingest-actor", default="hai_cli_direct",
                      choices=("hai_cli_direct", "claude_agent_v1"))
    p_is.add_argument("--base-dir", required=False, default=None,
                      help="Intake root (stress_manual.jsonl lands here). "
                           "Default: $HAI_BASE_DIR or ~/.health_agent.")
    p_is.add_argument("--db-path", default=None)
    p_is.set_defaults(func=cmd_intake_stress)
    annotate_contract(
        p_is,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Record a manual stress observation (used when Garmin stress is absent).",
    )

    p_inote = intake_sub.add_parser(
        "note",
        help="Log a free-text context note. Append-only; no corrections.",
    )
    p_inote.add_argument("--text", required=True,
                         help="Free-text note body. Cannot be empty.")
    p_inote.add_argument("--tags", default=None,
                         help="Comma-separated tags")
    p_inote.add_argument("--recorded-at", default=None,
                         help="Optional ISO-8601 timestamp; defaults to now UTC")
    p_inote.add_argument("--as-of", default=None,
                         help="Civil date this note belongs to (default today UTC)")
    p_inote.add_argument("--user-id", default="u_local_1")
    p_inote.add_argument("--ingest-actor", default="hai_cli_direct",
                         choices=("hai_cli_direct", "claude_agent_v1"))
    p_inote.add_argument("--base-dir", required=False, default=None,
                         help="Intake root (context_notes.jsonl lands here). "
                              "Default: $HAI_BASE_DIR or ~/.health_agent.")
    p_inote.add_argument("--db-path", default=None)
    p_inote.set_defaults(func=cmd_intake_note)
    annotate_contract(
        p_inote,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Attach a free-text context note to a day.",
    )

    p_ir = intake_sub.add_parser(
        "readiness",
        help="Record a typed manual-readiness entry (writes to state)",
    )
    p_ir.add_argument("--soreness", required=True, choices=SORENESS_CHOICES,
                      help="Subjective soreness band: low | moderate | high")
    p_ir.add_argument("--energy", required=True, choices=ENERGY_CHOICES,
                      help="Subjective energy band: low | moderate | high")
    p_ir.add_argument("--planned-session-type", required=True,
                      help="Planned session type. Free text per the "
                           "loose substring matching in per-domain "
                           "classifiers, but agents should prefer the "
                           "canonical vocabulary discoverable via "
                           "`hai planned-session-types --json` (e.g. "
                           "easy_z2, intervals_4x4, strength_sbd, rest).")
    p_ir.add_argument("--active-goal", default=None,
                      help="Optional active training goal (free text)")
    p_ir.add_argument("--as-of", default=None,
                      help="As-of date the intake pertains to (ISO-8601, default today UTC)")
    p_ir.add_argument("--user-id", default="u_local_1",
                      help="User this intake attaches to (default: u_local_1)")
    p_ir.add_argument("--base-dir", required=False, default=None,
                      help="Intake root (readiness_manual.jsonl lands here). "
                           "Default: $HAI_BASE_DIR or ~/.health_agent.")
    p_ir.add_argument("--db-path", default=None,
                      help="State DB path (defaults to HAI_STATE_DB or ~/.health_agent/state.db)")
    p_ir.add_argument("--ingest-actor", default="hai_cli_direct",
                      choices=("hai_cli_direct", "claude_agent_v1"),
                      help="Transport identity for provenance (default: hai_cli_direct)")
    p_ir.set_defaults(func=cmd_intake_readiness)
    annotate_contract(
        p_ir,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Record a manual readiness self-report entry.",
    )

    p_igaps = intake_sub.add_parser(
        "gaps",
        help=(
            "Enumerate user-closeable intake gaps in the snapshot. "
            "Structured surface for agent-driven prompting — the agent "
            "reads this, composes one consolidated question in its own "
            "voice, and routes the user's answer through the right "
            "hai intake <X> commands."
        ),
    )
    p_igaps.add_argument(
        "--as-of", default=None,
        help="Civil date to inspect, ISO-8601. Default: today UTC.",
    )
    p_igaps.add_argument(
        "--user-id", default="u_local_1",
        help="User whose snapshot to inspect (default: u_local_1).",
    )
    p_igaps.add_argument(
        "--evidence-json", default=None,
        help=(
            "Path to `hai clean` output. Pull-evidence path. The "
            "snapshot is expanded with per-domain classified_state + "
            "policy_result before gap detection. Mutually exclusive "
            "with --from-state-snapshot."
        ),
    )
    p_igaps.add_argument(
        "--from-state-snapshot",
        action="store_true",
        dest="from_state_snapshot",
        help=(
            "v0.1.11 W-W: derive gaps from the latest accepted state "
            "without fresh evidence. The session-start protocol "
            "fallback when `hai pull` is broken or skipped. Refuses "
            "if the latest successful pull is older than the "
            "staleness threshold (default 48h, configurable via "
            "thresholds.toml gap_detection.snapshot_staleness_max_hours). "
            "Pass --allow-stale-snapshot to override. Output gaps "
            "carry `derived_from: state_snapshot` and `snapshot_read_at`."
        ),
    )
    p_igaps.add_argument(
        "--allow-stale-snapshot",
        action="store_true",
        dest="allow_stale_snapshot",
        help=(
            "Override the staleness gate. Each gap then carries a "
            "`staleness_warning` field for audit-chain clarity."
        ),
    )
    p_igaps.add_argument("--db-path", default=None, help="State DB path.")
    p_igaps.set_defaults(func=cmd_intake_gaps)
    annotate_contract(
        p_igaps,
        mutation="read-only",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Return the list of user-closeable intake gaps in the snapshot. "
            "Read-only; no side effects."
        ),
    )

    # W-B (v0.1.17 §2.H) — body-composition intake.
    p_iw = intake_sub.add_parser(
        "weight",
        help=(
            "Record a body-composition measurement (weight + optional "
            "body-fat percent). User-authored only — agent_safe=False."
        ),
    )
    p_iw.add_argument(
        "--kg", required=True, type=float,
        help="Weight in kg. Must be in (20, 250).",
    )
    p_iw.add_argument(
        "--body-fat-pct", default=None, type=float,
        help=(
            "Optional body-fat percentage (range 0-75 when given)."
        ),
    )
    p_iw.add_argument(
        "--measured-at", default=None,
        help="When the measurement happened (ISO-8601). Default: current UTC.",
    )
    p_iw.add_argument(
        "--as-of", default=None,
        help=(
            "Civil date the measurement is associated with (YYYY-MM-DD). "
            "Default: civil date of --measured-at."
        ),
    )
    p_iw.add_argument(
        "--notes", default=None,
        help="Optional free-text note (e.g. 'fasted morning post-bathroom').",
    )
    p_iw.add_argument(
        "--user-id", default="u_local_1",
        help="User this measurement attaches to (default: u_local_1).",
    )
    p_iw.add_argument(
        "--ingest-actor", default="cli",
        help=(
            "Per-record provenance label (default: cli). Not a security "
            "boundary — agents respect agent_safe=False at the manifest."
        ),
    )
    p_iw.add_argument(
        "--base-dir", default=None,
        help=(
            "Intake root (body_comp_intake.jsonl lands here). "
            "Default: $HAI_BASE_DIR or ~/.health_agent."
        ),
    )
    p_iw.add_argument(
        "--db-path", default=None,
        help="State DB path (default: $HAI_STATE_DB or "
             "~/.local/share/health_agent_infra/state.db).",
    )
    p_iw.set_defaults(func=cmd_intake_weight)
    annotate_contract(
        p_iw,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=False,
        description=(
            "W-B (v0.1.17 §2.H): record a body-composition measurement. "
            "Append-only (multiple measurements per day are valid). "
            "Source enum is fixed to 'user_authored'; agent-proposal "
            "path is post-v0.2.x scope."
        ),
    )

    p_state = sub.add_parser("state", help="Local SQLite state store management")
    state_sub = p_state.add_subparsers(dest="state_command", required=True)

    p_si = state_sub.add_parser("init", help="Create the state DB and apply pending migrations")
    p_si.add_argument("--db-path", default=None,
                      help="Path to state.db (default: $HAI_STATE_DB or ~/.local/share/health_agent_infra/state.db)")
    p_si.set_defaults(func=cmd_state_init)
    annotate_contract(
        p_si,
        mutation="writes-state",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK",),
        agent_safe=True,
        description=(
            "Create the local SQLite state DB and apply all pending "
            "migrations. Idempotent — safe to call repeatedly."
        ),
    )

    p_sm = state_sub.add_parser("migrate", help="Apply pending migrations against an existing state DB")
    p_sm.add_argument("--db-path", default=None,
                      help="Path to state.db (default: $HAI_STATE_DB or ~/.local/share/health_agent_infra/state.db)")
    p_sm.set_defaults(func=cmd_state_migrate)
    annotate_contract(
        p_sm,
        mutation="writes-state",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Apply any pending schema migrations to an already-"
            "initialized state DB."
        ),
    )

    p_sread = state_sub.add_parser(
        "read",
        help="Per-domain read (introspection): rows from one canonical table within a date range",
    )
    p_sread.add_argument("--domain", required=True,
                         help="One of: recovery, running, gym, nutrition, stress, notes, "
                              "recommendations, reviews, goals")
    p_sread.add_argument("--since", required=True,
                         help="Inclusive civil-date lower bound, ISO-8601")
    p_sread.add_argument("--until", default=None,
                         help="Inclusive civil-date upper bound (default: same as --since)")
    p_sread.add_argument("--user-id", default=None,
                         help="Filter to a single user (default: no filter)")
    p_sread.add_argument("--db-path", default=None)
    p_sread.set_defaults(func=cmd_state_read)
    annotate_contract(
        p_sread,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Read a per-domain accepted-state row for a given date.",
    )

    p_ssnap = state_sub.add_parser(
        "snapshot",
        help="Cross-domain snapshot: the primary read surface the agent consumes",
    )
    p_ssnap.add_argument("--as-of", required=True,
                         help="Civil date to snapshot, ISO-8601")
    p_ssnap.add_argument("--user-id", required=True,
                         help="User whose state to snapshot")
    p_ssnap.add_argument("--lookback-days", type=int, default=14,
                         help="Days of history to include (default: 14)")
    p_ssnap.add_argument("--db-path", default=None)
    p_ssnap.add_argument("--evidence-json", default=None,
                         help="Optional path to a `hai clean` output JSON. When "
                              "present, the recovery block is expanded to the "
                              "full Phase 1 bundle shape (evidence + raw_summary "
                              "+ classified_state + policy_result). When absent, "
                              "the recovery block keeps its v1.0 shape.")
    p_ssnap.set_defaults(func=cmd_state_snapshot)
    annotate_contract(
        p_ssnap,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Emit the cross-domain state snapshot the synthesis / skills "
            "layer consumes for a (for_date, user_id) pair."
        ),
    )

    p_sr = state_sub.add_parser(
        "reproject",
        help="Rebuild projected tables from JSONL audit logs, scoped to the "
             "log groups present under --base-dir (recommendation/review, "
             "gym, nutrition).",
    )
    p_sr.add_argument("--base-dir", required=False, default=None,
                      help="Writeback/intake root. Default: $HAI_BASE_DIR or "
                           "~/.health_agent. Recognised audit files: "
                           "recommendation_log.jsonl, review_events.jsonl, "
                           "review_outcomes.jsonl, gym_sessions.jsonl, "
                           "nutrition_intake.jsonl. Only the groups whose "
                           "files are present get truncated and rebuilt.")
    p_sr.add_argument("--db-path", default=None,
                      help="State DB path (default: $HAI_STATE_DB or platform default)")
    p_sr.add_argument("--allow-empty-reproject", action="store_true",
                      help="Allow reproject to truncate the projection tables even when "
                           "the base-dir contains none of the expected JSONL audit logs. "
                           "Refuses by default to guard against typo-driven data loss.")
    p_sr.add_argument("--cascade-synthesis", action="store_true",
                      help="Permit reproject to delete synthesis-side rows "
                           "(planned_recommendation, daily_plan, x_rule_firing) when "
                           "they would otherwise block the rebuild via FK constraints. "
                           "Refuses by default because those tables are not "
                           "JSONL-derived — they're computed by `hai synthesize`. "
                           "If you pass this flag, re-run `hai synthesize` afterwards "
                           "to repopulate them.")
    p_sr.set_defaults(func=cmd_state_reproject)
    annotate_contract(
        p_sr,
        mutation="writes-state",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Rebuild the accepted_*_state_daily tables from the raw "
            "evidence JSONL. Deterministic modulo projection timestamps "
            "— content/keys/links replay identically across runs, but "
            "projected_at / corrected_at columns reflect the wall-clock "
            "of the rebuild. Safe to re-run."
        ),
    )

    # v0.1.17 F-PV14-02 — `hai sync purge` surgical sync_run_log cleanup.
    # Top-level `hai sync ...` namespace (per W-29 boundary refresh OQ-1,
    # the handler co-locates with state.py rather than a separate
    # cli/handlers/sync.py module). agent_safe=False — maintainer-side
    # surgical surface; an agent honoring the manifest will not invoke.
    p_sync = sub.add_parser(
        "sync",
        help="Sync-row maintenance (sync_run_log surgical operations)",
    )
    sync_sub = p_sync.add_subparsers(dest="sync_command", required=True)
    p_sync_purge = sync_sub.add_parser(
        "purge",
        help=(
            "Surgically delete sync_run_log rows that match the selectors. "
            "Refuses if more than 5 rows match. Recommend `hai backup` first."
        ),
    )
    p_sync_purge.add_argument(
        "--source", required=True,
        help="Source name to purge (e.g. garmin, garmin_live, intervals_icu).",
    )
    p_sync_purge.add_argument(
        "--for-date", default=None,
        help="Civil date the sync was for (ISO-8601), if filtering on for_date.",
    )
    p_sync_purge.add_argument(
        "--started-after", default=None,
        help=(
            "Only consider rows whose started_at is strictly after this "
            "ISO-8601 timestamp."
        ),
    )
    p_sync_purge.add_argument(
        "--user-id", default=None,
        help="Filter to one user_id (default: all users for the source).",
    )
    p_sync_purge.add_argument(
        "--db-path", default=None,
        help="Path to state.db (default: $HAI_STATE_DB or "
             "~/.local/share/health_agent_infra/state.db).",
    )
    p_sync_purge.add_argument(
        "--dry-run", action="store_true",
        help="List the rows that would be purged without committing the delete.",
    )
    p_sync_purge.set_defaults(func=cmd_sync_purge)
    annotate_contract(
        p_sync_purge,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=False,
        description=(
            "F-PV14-02 (v0.1.17): surgically delete contaminated rows from "
            "sync_run_log. Refuses if selectors resolve to >5 rows. Writes "
            "a runtime_event_log audit row tagged `sync purge` on commit. "
            "agent_safe=False — operator-side surgical tool."
        ),
    )

    # v0.1.14 W-BACKUP — backup / restore / export top-level subcommands.
    p_backup = sub.add_parser(
        "backup",
        help="Write a versioned backup tarball of state DB + JSONL audit logs.",
    )
    p_backup.add_argument(
        "--dest", default=None,
        help="Output tarball path. Default: ./hai-backup-<UTC>.tar.gz",
    )
    p_backup.add_argument(
        "--db-path", default=None,
        help="State DB path (default: $HAI_STATE_DB or platform default).",
    )
    p_backup.add_argument(
        "--base-dir", default=None,
        help="Writeback/intake root (JSONL logs). Default: $HAI_BASE_DIR or "
             "~/.health_agent.",
    )
    p_backup.set_defaults(func=cmd_backup)
    annotate_contract(
        p_backup,
        mutation="read-only",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Versioned tarball of state.db + JSONL audit logs + "
            "manifest. Read-only on local state. See "
            "hai/docs/backup_and_recovery.md for the recovery contract."
        ),
    )

    p_restore = sub.add_parser(
        "restore",
        help="Restore from a backup tarball; refuses on schema mismatch.",
    )
    p_restore.add_argument(
        "--bundle", required=True,
        help="Path to a backup tarball produced by `hai backup`.",
    )
    p_restore.add_argument(
        "--db-path", default=None,
        help="State DB path (overwritten on restore).",
    )
    p_restore.add_argument(
        "--base-dir", default=None,
        help="Writeback/intake root (JSONL logs overwritten on restore).",
    )
    p_restore.set_defaults(func=cmd_restore)
    annotate_contract(
        p_restore,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=False,
        description=(
            "Restore state.db + JSONL audit logs from a `hai backup` "
            "tarball. Refuses if the bundle's schema_version does not "
            "match the installed wheel's head. Overwrites the "
            "destination — back up first if it has data."
        ),
    )

    p_export = sub.add_parser(
        "export",
        help="Emit a unified JSONL stream of every audit log under base_dir.",
    )
    p_export.add_argument(
        "--dest", default=None,
        help="Output path. If omitted, writes to stdout.",
    )
    p_export.add_argument(
        "--base-dir", default=None,
        help="Writeback/intake root (JSONL logs). Default: $HAI_BASE_DIR.",
    )
    p_export.set_defaults(func=cmd_export)
    annotate_contract(
        p_export,
        mutation="read-only",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK",),
        agent_safe=True,
        description=(
            "Single JSONL stream of every audit log under base_dir, "
            "with each line carrying a `_log` envelope tag. "
            "Read-only consolidation; not net-new functionality."
        ),
    )

    p_daily = sub.add_parser(
        "daily",
        help=(
            "One-shot morning orchestration over the existing runtime "
            "(pull → clean → snapshot → proposal-gate → synthesize → "
            "schedule reviews). Stops honestly at the agent seam when "
            "proposals are not yet in proposal_log."
        ),
    )
    p_daily.add_argument("--base-dir", required=False, default=None,
                         help="Writeback/intake root. review_events.jsonl "
                              "is appended here after synthesis. "
                              "Default: $HAI_BASE_DIR or ~/.health_agent.")
    p_daily.add_argument("--as-of", default=None,
                         help="Civil date to orchestrate for, ISO-8601. "
                              "Default: today UTC.")
    p_daily.add_argument("--user-id", default="u_local_1",
                         help="User whose daily pipeline to orchestrate.")
    p_daily.add_argument("--db-path", default=None,
                         help="State DB path (default: `$HAI_STATE_DB` or "
                              "`~/.local/share/health_agent_infra/state.db`).")
    p_daily.add_argument("--live", action="store_true",
                         help="Legacy flag: equivalent to --source garmin_live. "
                              "Garmin Connect's login surface is rate-limited "
                              "and unreliable for live scraping; prefer "
                              "`--source intervals_icu` (the v0.1.6+ "
                              "supported live source).")
    p_daily_source = p_daily.add_argument(
        "--source",
        choices=("csv", "garmin_live", "intervals_icu"),
        default=None,
        help="Evidence source for the pull stage. Same semantics as "
             "`hai pull --source`. Default (v0.1.6+): intervals_icu "
             "when credentials are configured, else csv.",
    )
    annotate_choice_metadata(p_daily_source, PULL_SOURCE_CHOICE_METADATA)
    p_daily.add_argument(
        "--allow-fixture-into-real-state",
        action="store_true",
        help=(
            "Permit `--source csv` (committed CSV fixture) to write "
            "into the canonical state DB during the daily pull stage. "
            "Default-deny per F-PV14-01 (v0.1.15) — fixture data in "
            "the canonical DB corrupts user state. Use a `hai demo "
            "start` session or an explicit --db-path / HAI_STATE_DB "
            "override instead where possible. (F-IR-02 round-1 IR "
            "fix: previously only `hai pull` enforced this guard; "
            "the daily orchestrator was a bypass surface.)"
        ),
    )
    p_daily.add_argument("--history-days", type=int, default=14,
                         help="Trailing window for live pull series "
                              "(matches `hai pull --history-days`).")
    p_daily.add_argument("--skip-pull", action="store_true",
                         help="Skip the pull + clean stages. Assumes "
                              "state already populated for --as-of.")
    p_daily.add_argument("--domains", default=None,
                         help="Optional CSV subset of expected domains "
                              "(recovery, running, sleep, stress, "
                              "strength, nutrition). Default: all 6. "
                              "Narrows the proposal-completeness gate: "
                              "synthesis is blocked until every domain "
                              "in this set has a proposal. Use this to "
                              "say `I'm only planning for these N "
                              "domains today` and unblock the gate "
                              "without posting unused proposals. "
                              "Synthesis still runs over every proposal "
                              "present in proposal_log for (for_date, "
                              "user_id), which may be a superset of "
                              "this list if other domains were proposed.")
    p_daily.add_argument("--agent-version", default="claude_agent_v1",
                         help="Agent version string stamped on "
                              "committed rows.")
    p_daily.add_argument("--supersede", action="store_true",
                         help="Keep prior canonical plan and write a "
                              "fresh _v<N> id. Default is atomic replace.")
    p_daily.add_argument(
        "--re-propose-all", action="store_true", dest="re_propose_all",
        help=(
            "v0.1.13 W-FBC-2 (closure of F-B-04, option A default per "
            "hai/reporting/docs/archive/cycle_artifacts/"
            "supersede_domain_coverage.md): operator "
            "belt-and-braces signal that every domain's proposal "
            "should have been freshly authored in this synthesis "
            "cycle. Synthesis appends a per-domain "
            "`<domain>_proposal_carryover_under_re_propose_all` token "
            "to any recommendation whose proposal envelope was "
            "authored outside the freshness window (default 60s) — "
            "the audit-chain signal that the operator's intent was "
            "observably not honored for that domain. The token "
            "surfaces in `hai today` rationale prose and "
            "`hai explain` recommendation rows. Also surfaces in "
            "the daily report JSON as "
            "`re_propose_all_requested: true`."
        ),
    )
    p_daily.add_argument("--skip-reviews", action="store_true",
                         help="Skip review-event scheduling after "
                              "synthesis.")
    p_daily.add_argument("--auto", action="store_true",
                         help="v0.1.7 W21: emit a versioned "
                              "next_actions[] manifest alongside the "
                              "stage report. Each action carries a "
                              "concrete command_argv, kind, "
                              "reason_code, blocking, safe_to_retry, "
                              "and after_success routing — so an "
                              "agent can drive the full daily loop "
                              "without consulting the intent-router "
                              "skill prose. Schema is "
                              "next_actions.v1.")
    # v0.1.8 W43 — `--explain` adds a per-stage explain block to the
    # JSON output without mutating any default behaviour.
    p_daily.add_argument(
        "--explain", action="store_true",
        help=(
            "v0.1.8 W43: with --auto, attach a per-stage explain block "
            "to the JSON output (pull / clean / snapshot / gaps / "
            "proposal_gate / synthesize). Reads already-computed data; "
            "never recomputes, mutates, or fabricates fields."
        ),
    )
    p_daily.set_defaults(func=cmd_daily)
    annotate_contract(
        p_daily,
        mutation="writes-state",
        idempotent="yes-with-supersede",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Morning orchestrator: deterministic stages run end-to-end "
            "(pull → clean → snapshot → gaps → proposal_gate). The "
            "agent then invokes the 6 per-domain readiness skills, "
            "posts DomainProposal rows via `hai propose --domain <d>`, "
            "and re-runs `hai daily` to advance the gate to `complete` "
            "and trigger synthesis. `--domains <csv>` narrows the "
            "expected set for partial-day planning."
        ),
        preconditions=[
            "state_db_initialized",
            "intervals_icu_or_garmin_credentials_optional",
        ],
        output_schema={
            "OK": {
                "shape": "JSON report of the orchestration run.",
                "json_keys": [
                    "as_of_date", "user_id", "base_dir", "db_path",
                    "expected_domains", "stages", "overall_status",
                ],
                "overall_status_values": [
                    "complete", "incomplete", "awaiting_proposals",
                    "failed",
                ],
                "notes": (
                    "v0.1.6: the proposal gate has three pre-synthesis "
                    "statuses. `awaiting_proposals` = zero proposals; "
                    "`incomplete` = some proposals but missing >=1 "
                    "expected domain (synthesis blocked, hint names "
                    "the missing domains); `complete` = every expected "
                    "domain has a proposal (synthesis runs). On the "
                    "first two, the agent must post the missing "
                    "DomainProposal rows OR narrow `--domains` and "
                    "rerun. `failed` is reserved for synthesis errors "
                    "after the gate."
                ),
            },
        },
    )

    p_setup = sub.add_parser("setup-skills", help="Copy packaged skills/ into ~/.claude/skills/")
    p_setup.add_argument("--dest", default=str(DEFAULT_CLAUDE_SKILLS_DIR))
    p_setup.add_argument("--force", action="store_true",
                         help="Overwrite existing skill directories of the same name")
    p_setup.set_defaults(func=cmd_setup_skills)
    annotate_contract(
        p_setup,
        mutation="writes-skills-dir",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK",),
        agent_safe=True,
        description=(
            "Copy the packaged skills/ tree to ~/.claude/skills/ so "
            "Claude Code discovers them."
        ),
    )

    p_init = sub.add_parser(
        "init",
        help=(
            "First-run setup: scaffold thresholds, init state DB + apply "
            "migrations, copy skills, report Garmin auth status. "
            "Pass --guided for the full first-time-user onboarding flow "
            "(prompts for intervals.icu creds + intent/target authoring "
            "+ first wellness pull). Idempotent; safe to rerun."
        ),
    )
    p_init.add_argument("--thresholds-path", default=None,
                        help="Override thresholds TOML destination "
                             "(default: platformdirs user_config_dir).")
    p_init.add_argument("--db-path", default=None,
                        help="Override state DB path (default: "
                             "$HAI_STATE_DB or platform default).")
    p_init.add_argument("--skills-dest", default=str(DEFAULT_CLAUDE_SKILLS_DIR),
                        help="Destination for skills/ (default: ~/.claude/skills/).")
    p_init.add_argument("--skip-skills", action="store_true",
                        help="Skip copying skills (useful when the agent "
                             "harness is not Claude Code).")
    p_init.add_argument("--force", action="store_true",
                        help="Overwrite an existing thresholds TOML and "
                             "existing skills directories of the same name.")
    p_init.add_argument("--with-auth", action="store_true",
                        help="After the non-interactive setup, prompt for "
                             "Garmin credentials and store them in the OS "
                             "keyring (equivalent to running `hai auth "
                             "garmin` afterward). Requires a TTY.")
    p_init.add_argument("--with-first-pull", action="store_true",
                        help="After setup (and --with-auth, if used), do "
                             "a single live-adapter pull for today so "
                             "`hai daily` has state to reason over. One "
                             "network call, configurable history window "
                             "via --history-days. Requires Garmin creds.")
    p_init.add_argument("--history-days", type=int, default=1,
                        help="How many days of historical context the "
                             "first-pull adapter fetches (default: 1 → "
                             "~5 Garmin API calls). Larger windows give "
                             "richer baselines but risk rate-limiting: "
                             "each extra day adds ~5 API calls. Ignored "
                             "without --with-first-pull.")
    p_init.add_argument("--user-id", default="u_local_1",
                        help="User id to record against the backfill's "
                             "sync_run_log rows (default: u_local_1).")
    p_init.add_argument("--guided", action="store_true",
                        help="Run the full first-time-user onboarding flow "
                             "(W-AA): after the non-interactive setup, prompt "
                             "for intervals.icu credentials, author initial "
                             "intent + target rows, run a first wellness "
                             "pull, and surface today's plan. Idempotent; "
                             "skips steps that already have state.")
    p_init.add_argument("--non-interactive", action="store_true",
                        help="Opt out of the v0.1.18 W-OB-2 default-flip "
                             "(interactive `hai init` default). Without this "
                             "flag, when stdin is a TTY AND onboarding state "
                             "is incomplete, `hai init` auto-promotes to the "
                             "`--guided` flow. Equivalent to setting "
                             "HAI_INIT_NON_INTERACTIVE=1. CI / agent harnesses "
                             "calling `hai init` without TTY are already "
                             "opted out implicitly via the TTY check.")
    p_init.set_defaults(func=cmd_init)
    annotate_contract(
        p_init,
        mutation="interactive",
        idempotent="no",
        json_output="none",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=False,  # interactive wizard
        description="First-run wizard: state init, config scaffolding, auth setup.",
    )

    p_doctor = sub.add_parser(
        "doctor",
        help=(
            "Read-only runtime diagnostics: config, state DB, Garmin "
            "auth, and skills install. Exits 0 for ok/warn, 2 for fail."
        ),
    )
    p_doctor.add_argument("--thresholds-path", default=None,
                          help="Override thresholds TOML path (default: "
                               "platformdirs user_config_dir).")
    p_doctor.add_argument("--db-path", default=None,
                          help="Override state DB path (default: "
                               "$HAI_STATE_DB or platform default).")
    p_doctor.add_argument("--skills-dest", default=str(DEFAULT_CLAUDE_SKILLS_DIR),
                          help="Skills destination to inspect (default: "
                               "~/.claude/skills/).")
    p_doctor.add_argument("--user-id", default="u_local_1",
                          help="Which user's sync history + today counts to "
                               "report. Default: u_local_1.")
    p_doctor.add_argument("--as-of", default=None,
                          help="Anchor date for freshness + today counts, "
                               "ISO-8601. Default: today (UTC).")
    p_doctor.add_argument("--json", action="store_true",
                          help="Emit the structured report dict as JSON "
                               "instead of the human-readable text view.")
    p_doctor.add_argument(
        "--deep", action="store_true",
        help=(
            "Run live API probes against the configured credential "
            "surfaces (intervals.icu wellness fetch, etc.). Closes the "
            "diagnostic-trust gap Codex F-DEMO-01 surfaced — a present "
            "credential is not the same as an accepted credential. "
            "Default off so the cheap path stays cheap. Routes to a "
            "fixture stub (no network) when a demo session is active "
            "(W-X / Q-3 + W-Va integration)."
        ),
    )
    p_doctor.set_defaults(func=cmd_doctor)
    annotate_contract(
        p_doctor,
        mutation="read-only",
        idempotent="n/a",
        json_output="opt-in",  # text default, JSON via flag
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Report runtime health: DB present, migrations up to date, "
            "per-source freshness, today's accepted counts."
        ),
    )

    p_stats = sub.add_parser(
        "stats",
        help=(
            "Summarise local sync + command-invocation history from the "
            "state DB. Read-only, never leaves the device."
        ),
    )
    p_stats.add_argument("--db-path", default=None,
                         help="Override state DB path (default: "
                              "$HAI_STATE_DB or platform default).")
    p_stats.add_argument("--user-id", default="u_local_1",
                         help="Whose sync freshness to report. "
                              "Default: u_local_1.")
    p_stats.add_argument("--limit", type=int, default=7,
                         help="Number of recent runtime_event_log rows "
                              "to include (default: 7).")
    p_stats.add_argument("--json", action="store_true",
                         help="Emit the structured report dict as JSON "
                              "instead of the human-readable text view.")
    # v0.1.8 W38 — opt into the code-owned outcome summary view (W48).
    # Mutually exclusive with the default sync/events report. ``--domain``
    # narrows to one of the six v1 domains; omit to receive the per-
    # domain breakdown plus aggregate roll-up. ``--since`` overrides the
    # configured rolling window (``policy.review_summary.window_days``).
    p_stats.add_argument(
        "--outcomes",
        action="store_true",
        help=(
            "Mode: emit the code-owned review-outcome summary (W48) "
            "instead of the default sync/events report. Combine with "
            "--domain and --since to narrow the window."
        ),
    )
    p_stats.add_argument(
        "--domain",
        choices=("recovery", "running", "sleep", "stress", "strength", "nutrition"),
        default=None,
        help=(
            "Restrict --outcomes view to a single v1 domain. Omit to "
            "receive the per-domain breakdown plus aggregate roll-up."
        ),
    )
    p_stats.add_argument(
        "--since",
        type=int,
        default=None,
        help=(
            "Override the rolling window for --outcomes / --data-quality "
            "(days). Default: 7 for outcomes; for data-quality, the most "
            "recent N days are returned."
        ),
    )
    # v0.1.8 W51 — `hai stats --data-quality` reads from the
    # data_quality_daily ledger (or projects from snapshot for today
    # when missing).
    p_stats.add_argument(
        "--data-quality",
        action="store_true",
        help=(
            "Mode: emit the data-quality ledger view (W51). Combine "
            "with --domain and --since to narrow."
        ),
    )
    # v0.1.8 W40 — `hai stats --baselines`. Mode: emit the snapshot's
    # observed-vs-threshold/band view per domain so the user can sanity-
    # check what the runtime is looking at without reading SQL.
    p_stats.add_argument(
        "--baselines",
        action="store_true",
        help=(
            "Mode: emit observed values, configured thresholds, "
            "resulting bands, coverage, missingness, and cold-start "
            "state for each v1 domain (W40)."
        ),
    )
    # v0.1.8 W46 — `hai stats --funnel` reads runtime_event_log
    # context_json to surface daily-pipeline outcomes over a window.
    p_stats.add_argument(
        "--funnel",
        action="store_true",
        help=(
            "Mode: emit the daily-pipeline funnel — per-day "
            "overall_status, missing-domain frequency, and proposal-"
            "gate counts (W46)."
        ),
    )
    p_stats.set_defaults(func=cmd_stats)
    annotate_contract(
        p_stats,
        mutation="read-only",
        idempotent="n/a",
        json_output="opt-in",  # text default, JSON via flag
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Summarise sync_run_log (last pull per source) + "
            "runtime_event_log (recent commands, daily streak) from the "
            "user's local DB. With --outcomes, emits the code-owned "
            "review-outcome summary (W48) instead. No telemetry leaves "
            "the device."
        ),
    )

    # D4 ADR (hai/reporting/plans/v0_1_4/adr_classify_policy_cli.md): the
    # legacy `hai classify` / `hai policy` recovery-only debug CLIs
    # were removed in v0.1.4. Their behaviour is subsumed by
    # `hai state snapshot --evidence-json`, which emits
    # classified_state + policy_result for every domain in one call.

    p_config = sub.add_parser("config", help="Inspect or scaffold runtime thresholds")
    config_sub = p_config.add_subparsers(dest="config_command", required=True)

    p_ci = config_sub.add_parser(
        "init",
        help="Scaffold a thresholds.toml at the user config path (platformdirs)",
    )
    p_ci.add_argument("--path", default=None,
                      help="Override destination path (default: platformdirs user_config_dir)")
    p_ci.add_argument("--force", action="store_true",
                      help="Overwrite an existing thresholds.toml")
    p_ci.set_defaults(func=cmd_config_init)
    annotate_contract(
        p_ci,
        mutation="writes-config",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Scaffold a default thresholds.toml at the user-config path.",
    )

    p_cs = config_sub.add_parser(
        "show",
        help="Print the merged effective thresholds (defaults + user overrides)",
    )
    p_cs.add_argument("--path", default=None,
                      help="Override source path (default: platformdirs user_config_dir)")
    p_cs.set_defaults(func=cmd_config_show)
    annotate_contract(
        p_cs,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Print the effective merged threshold configuration (defaults + overrides).",
    )

    # v0.1.8 W39 — config validate / diff.
    p_cv = config_sub.add_parser(
        "validate",
        help="Parse the user thresholds TOML and report unknown / mistyped keys.",
    )
    p_cv.add_argument("--path", default=None,
                      help="Override source path.")
    p_cv.add_argument("--strict", action="store_true",
                      help="Treat unknown leaf keys as blocking errors.")
    p_cv.set_defaults(func=cmd_config_validate)
    annotate_contract(
        p_cv,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Validate user thresholds.toml against DEFAULT_THRESHOLDS shape.",
    )

    p_cd = config_sub.add_parser(
        "diff",
        help="Show user overrides vs defaults vs effective values, leaf by leaf.",
    )
    p_cd.add_argument("--path", default=None,
                      help="Override source path.")
    p_cd.set_defaults(func=cmd_config_diff)
    annotate_contract(
        p_cd,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Diff user thresholds.toml against DEFAULT_THRESHOLDS, leaf by leaf.",
    )

    p_exercise = sub.add_parser(
        "exercise",
        help="Exercise-taxonomy helpers (search, lookup)",
    )
    exercise_sub = p_exercise.add_subparsers(dest="exercise_command", required=True)

    p_esearch = exercise_sub.add_parser(
        "search",
        help="Rank top taxonomy matches for a free-text exercise name",
    )
    p_esearch.add_argument("--query", required=True,
                           help="Free-text exercise name to resolve")
    p_esearch.add_argument("--limit", type=int, default=10,
                           help="Max hits to return (default 10)")
    p_esearch.add_argument("--db-path", default=None,
                           help="Path to state DB (default: platformdirs user_data_dir)")
    p_esearch.set_defaults(func=cmd_exercise_search)
    annotate_contract(
        p_esearch,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Rank top exercise-taxonomy matches for a free-text query.",
    )

    _register_eval_subparser(sub)

    # v0.1.6 W17: bounded local-only retrieval CLI replacing the
    # `python3 -c` pattern in expert-explainer's allowed-tools.
    p_research = sub.add_parser(
        "research",
        help="Bounded local-only retrieval against the allowlisted "
             "research source registry. Read-only; no network.",
    )
    research_sub = p_research.add_subparsers(
        dest="research_command", required=True,
    )
    p_rt = research_sub.add_parser(
        "topics",
        help="List the allowlisted research topics.",
    )
    p_rt.set_defaults(func=cmd_research_topics)
    annotate_contract(
        p_rt,
        mutation="read-only",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK",),
        agent_safe=True,
        description=(
            "List the allowlisted topics the bounded retrieval surface "
            "recognises. Read-only."
        ),
    )

    p_rs = research_sub.add_parser(
        "search",
        help="Retrieve sources for one allowlisted topic. "
             "Read-only; no network.",
    )
    p_rs.add_argument(
        "--topic", required=True,
        help="Topic token (must be on the allowlist; see "
             "`hai research topics`).",
    )
    p_rs.set_defaults(func=cmd_research_search)
    annotate_contract(
        p_rs,
        mutation="read-only",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK",),
        agent_safe=True,
        description=(
            "Retrieve sources for one allowlisted research topic. "
            "Mirrors core.research.retrieve but exposes only the "
            "topic-token interface — the privacy-violation booleans "
            "are not configurable. Read-only; no network."
        ),
    )

    # v0.1.7 W33: machine-discoverable planned_session_type vocabulary.
    p_psv = sub.add_parser(
        "planned-session-types",
        help="Emit the canonical vocabulary for the "
             "--planned-session-type field on `hai intake readiness`. "
             "Read-only; the per-domain classifiers do substring "
             "matching, but this list is the canonical set agents "
             "should prefer.",
    )
    p_psv.set_defaults(func=cmd_planned_session_types)
    annotate_contract(
        p_psv,
        mutation="read-only",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK",),
        agent_safe=True,
        description=(
            "Emit the canonical planned_session_type vocabulary "
            "(token + classifier_substring + description per "
            "entry). Source registry: "
            "core/intake/planned_session_vocabulary.py."
        ),
    )

    p_caps = sub.add_parser(
        "capabilities",
        help="Emit the agent-CLI-contract manifest (JSON by default; "
             "--markdown for the contract doc; --human for a "
             "new-user one-page overview)",
    )
    p_caps.add_argument(
        "--markdown", action="store_true",
        help="Render the manifest as the contract markdown doc on stdout "
             "instead of JSON. Used by the doc regenerator.",
    )
    p_caps.add_argument(
        "--human", action="store_true",
        help="Render a one-page user-readable overview grouped by "
             "workflow stage. Skips the schema-annotation columns; "
             "for the agent-facing manifest use --json (default).",
    )
    # v0.1.6 (Codex r3 P1 fix): the README, intent-router skill, and
    # generated contract preamble all instruct agents to invoke
    # `hai capabilities --json`. JSON is the default emit, but until
    # this flag landed, passing `--json` exited argparse error 2 — a
    # silent agent footgun. Accept `--json` as a no-op alias for the
    # default JSON output.
    p_caps.add_argument(
        "--json", action="store_true",
        help="No-op alias: JSON is already the default emit. Provided "
             "so agents and docs can pass `--json` explicitly without "
             "argparse rejecting the flag.",
    )
    p_caps.set_defaults(func=cmd_capabilities)
    annotate_contract(
        p_caps,
        mutation="read-only",
        idempotent="n/a",
        json_output="opt-out",  # JSON default; --markdown suppresses
        exit_codes=("OK",),
        agent_safe=True,
        description=(
            "Emit the agent-CLI-contract manifest describing every "
            "subcommand's mutation class, idempotency, JSON output, and "
            "exit codes. The authoritative surface the routing skill "
            "consumes."
        ),
    )

    # hai demo — demo-mode session lifecycle (W-Va, v0.1.11).
    p_demo = sub.add_parser(
        "demo",
        help="Manage a demo session (scratch DB + isolated base_dir).",
        description=(
            "Open / close / clean up a demo session. While a session "
            "is active, every CLI command routes to a per-session "
            "scratch root so the real ~/.health_agent tree, real "
            "state.db, and real thresholds.toml stay byte-identical."
        ),
    )
    p_demo_sub = p_demo.add_subparsers(dest="demo_subcommand", required=True)

    p_demo_start = p_demo_sub.add_parser(
        "start",
        help="Open a new demo session (refuses if one is already active).",
    )
    p_demo_start.add_argument(
        "--persona",
        default=None,
        help=(
            "Persona slug. v0.1.12 W-Vb (partial closure): the "
            "packaged skeleton fixture for the slug loads from "
            "`health_agent_infra.demo.fixtures.<slug>` and the demo "
            "marker records a `fixture_application` entry, but "
            "proposal pre-population (so `hai daily` reaches "
            "synthesis) is deferred to v0.1.13 W-Vb. Use "
            "`--blank` for an explicitly-empty session."
        ),
    )
    p_demo_start.add_argument(
        "--blank",
        action="store_true",
        help="Force an empty session (no persona). Default behaviour today.",
    )
    p_demo_start.set_defaults(func=cmd_demo_start)
    annotate_contract(
        p_demo_start,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Open a new demo session. Creates a scratch root at "
            "/tmp/hai_demo_<id>/ with state.db, health_agent_root/, "
            "and config/thresholds.toml. Writes a marker file at "
            "the demo-session location ($XDG_CACHE_HOME/hai/ or "
            "~/.cache/hai/). Refuses with USER_INPUT if a session is "
            "already active."
        ),
    )

    p_demo_end = p_demo_sub.add_parser(
        "end",
        help="Close the active demo session (removes the marker).",
    )
    p_demo_end.set_defaults(func=cmd_demo_end)
    annotate_contract(
        p_demo_end,
        mutation="writes-state",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK",),
        agent_safe=True,
        description=(
            "Close the active demo session. Removes the marker so "
            "subsequent CLI invocations route to real persistence. "
            "v0.1.11 W-Va leaves the scratch root in place; W-Vb "
            "adds archive-on-end behaviour."
        ),
    )

    p_demo_cleanup = p_demo_sub.add_parser(
        "cleanup",
        help="Remove an orphan/stale demo marker (safety net).",
    )
    p_demo_cleanup.set_defaults(func=cmd_demo_cleanup)
    annotate_contract(
        p_demo_cleanup,
        mutation="writes-state",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK",),
        agent_safe=True,
        description=(
            "Remove an orphan / corrupt demo marker so the CLI can "
            "return to normal mode. Allowed even when the marker is "
            "invalid (the fail-closed escape hatch)."
        ),
    )

    return parser


def _derive_command_id(func) -> str:
    """Map a handler callable to its command id (handler name minus 'cmd_')."""
    name = getattr(func, "__name__", "")
    return name[4:] if name.startswith("cmd_") else name


def _agent_safe_gate(args: argparse.Namespace) -> Optional[int]:
    """Dispatch-time enforcement of manifest ``agent_safe`` annotations."""

    from health_agent_infra.core.refusal import (
        AgentSafeRefusalError,
        InvocationContextError,
        enforce_agent_safe_invocation,
        envelope_to_json,
    )

    command_id = _derive_command_id(args.func)
    command = f"hai {command_id.replace('_', ' ')}".strip()
    agent_safe = bool(getattr(args, "_contract_agent_safe", True))
    try:
        decision = enforce_agent_safe_invocation(
            command=command,
            agent_safe=agent_safe,
        )
    except AgentSafeRefusalError as exc:
        print(envelope_to_json(exc.envelope), file=sys.stderr)
        return exit_codes.USER_INPUT
    except InvocationContextError as exc:
        print(
            f"hai: {exc}. Set HAI_INVOCATION_CONTEXT to 'user', "
            "'agent', or 'rule_baseline'.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    if decision.mechanism_disabled_marker is not None:
        print(envelope_to_json(decision.mechanism_disabled_marker), file=sys.stderr)
    return None


# _demo_gate moved to cli/handlers/tools.py at W-29.2.6.
def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    try:
        gate = _demo_gate(args)
        if gate is not None:
            return gate
        require_runtime_mode_allowed()
        require_hermetic_recipe()
        agent_gate = _agent_safe_gate(args)
        if agent_gate is not None:
            return agent_gate
        return args.func(args)
    except SystemExit:
        # argparse error path uses SystemExit(2); pass through unchanged.
        raise
    except KeyboardInterrupt:
        # Ctrl-C — exit cleanly without a traceback.
        print("\nhai: interrupted by user", file=sys.stderr)
        return exit_codes.USER_INPUT
    except (HermeticModeError, RuntimeModeError) as exc:
        print(f"hai: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT
    except Exception as exc:
        # Top-level safety net (added in v0.1.6 per Codex r2 / internal
        # audit). No CLI handler should escape as a raw Python traceback;
        # an agent calling `hai` should always see one of the documented
        # exit codes (`hai/docs/cli_exit_codes.md`). When this
        # path fires it indicates either a missed local guard in a
        # handler (file it as a bug) or a genuine internal invariant
        # tripping (also a bug). We surface the exception type + message
        # on stderr but suppress the traceback by default; rerun with
        # `HAI_DEBUG_TRACEBACK=1` to see the full trace.
        import os as _os
        import traceback as _traceback
        if _os.environ.get("HAI_DEBUG_TRACEBACK"):
            _traceback.print_exc(file=sys.stderr)
        print(
            f"hai: internal error ({type(exc).__name__}): {exc}",
            file=sys.stderr,
        )
        print(
            "hai: rerun with HAI_DEBUG_TRACEBACK=1 for the full traceback.",
            file=sys.stderr,
        )
        return exit_codes.INTERNAL


if __name__ == "__main__":
    sys.exit(main())
