"""``hai pull`` + ``hai clean`` handler group — evidence acquisition.

Owns: ``hai pull``, ``hai clean``. Plus the F-PV14-01 CSV-canonical guard,
sync-row helpers, adapter builders, source resolver, clean helpers, the
``_PROJECTION_RESULT_*`` constants, and ``PULL_SOURCE_CHOICE_METADATA``.

W-29.2.9 split: extracted from cli/__init__.py 187-1152.
``_dual_write_project`` stays in cli/__init__.py because it's used by
state.py + intent.py + intake helpers (cross-group; W-29.3 cleanup may
move to cli/shared.py).

Test-infra note: tests that monkeypatch private symbols owned by this
module (``_build_live_adapter``, ``_build_intervals_icu_adapter``,
``_intervals_icu_configured``, ``CredentialStore`` *as a name*, etc.)
must target ``health_agent_infra.cli.handlers.pull_clean.X`` — patching
``cli_mod.X`` only affects the cli re-export binding, not this module's
local binding. CLASS-attribute patches (e.g.
``monkeypatch.setattr(cli_mod.CredentialStore, "default", ...)``)
continue to work because the class object is identity-shared across
all import sites.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import uuid
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from health_agent_infra.core import exit_codes
from health_agent_infra.core.clean import build_raw_summary, clean_inputs
from health_agent_infra.core.config import ConfigError, load_thresholds
from health_agent_infra.core.paths import resolve_base_dir
from health_agent_infra.core.pull.auth import (
    CredentialStore,
    KeyringUnavailableError,
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

# `_emit_json` + `_coerce_*` + `_load_json_arg` defined in cli/__init__.py
# before line 187. `_dual_write_project` stays in cli/__init__.py per
# W-29.2.9 boundary (cross-group usage).
from health_agent_infra.cli import (  # noqa: E402
    _coerce_date,
    _coerce_dt,
    _emit_json,
    _load_json_arg,
)


def _f_pv14_csv_canonical_guard(
    args: argparse.Namespace, *, source: str, command_label: str,
) -> Optional[int]:
    """F-PV14-01 (v0.1.15) shared guard: refuse a CSV-fixture write into
    the canonical state DB unless the user explicitly opted in.

    Centralised per F-IR-02 round-1 IR fix so both `cmd_pull` and
    `_daily_pull_and_project` enforce the same default-deny posture
    (the v0.1.14 carry-over contamination shape was canonical-DB
    pollution; the daily orchestrator is the path most likely to be
    used in a foreign-user gate, so it must not silently bypass the
    guard).

    Returns ``None`` when the call is permitted, ``USER_INPUT`` when
    the guard refuses. Escape paths:

      1. ``source != "csv"`` — guard never fires for live sources.
      2. Explicit ``--allow-fixture-into-real-state`` flag.
      3. Active ``hai demo`` session marker.
      4. Explicit ``--db-path`` arg (user named the target → opted in).
      5. ``HAI_STATE_DB`` env-var override (env-level user intent).
    """

    if source != "csv":
        return None

    from health_agent_infra.core.demo.session import is_demo_active

    explicit_db_path = getattr(args, "db_path", None) is not None
    env_db_path = bool(os.environ.get("HAI_STATE_DB"))
    allow_fixture = getattr(args, "allow_fixture_into_real_state", False)
    if (
        not explicit_db_path
        and not env_db_path
        and not allow_fixture
        and not is_demo_active()
    ):
        print(
            f"{command_label} --source csv refused: writing CSV-fixture "
            "data into the canonical state DB corrupts user state.\n"
            "Run inside a `hai demo start` session, OR pass "
            "--allow-fixture-into-real-state to confirm, OR set "
            "--db-path / HAI_STATE_DB to a non-canonical destination. "
            "(F-PV14-01, v0.1.15.)",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT
    return None


def cmd_pull(args: argparse.Namespace) -> int:
    as_of = _coerce_date(args.date)
    source = _resolve_pull_source(args)

    # F-PV14-01 default-deny: refuse before opening the sync row so the
    # acceptance "zero rows in sync_run_log" holds. The carry-over
    # evidence (post_v0_1_14/carry_over_findings.md F-PV14-01) showed
    # fixture-shaped sync rows landing in the canonical DB on 2026-05-01
    # because `core/pull/garmin.py`'s CSV adapter wrote through the same
    # `_open_sync_row` path live pulls use, with no demo-marker check.
    refused = _f_pv14_csv_canonical_guard(
        args, source=source, command_label="hai pull",
    )
    if refused is not None:
        return refused

    # Mode still tracks csv vs live for sync_run_log — both live sources
    # share the "live" label so existing freshness checks don't need to
    # grow a new enum value.
    mode = "csv" if source == "csv" else "live"
    source_label = {
        "csv": GarminRecoveryReadinessAdapter.source_name,
        "garmin_live": "garmin_live",
        "intervals_icu": "intervals_icu",
    }[source]

    sync_id = _open_sync_row(
        getattr(args, "db_path", None),
        source=source_label,
        user_id=args.user_id,
        mode=mode,
        for_date=as_of,
    )

    # F-A-03 fix per W-H1: the adapter variable holds whichever of the
    # three adapter classes the user picked; mypy can't infer a common
    # type across these branches because the classes don't share an ABC.
    # Annotating as Any (the actual call surface — they all expose
    # `.load(as_of) -> PullResult`) lets the existing duck-typing work
    # without a heavier protocol refactor (deferred to v0.1.12 W-H2).
    adapter: Any
    if source == "csv":
        adapter = GarminRecoveryReadinessAdapter()
    elif source == "garmin_live":
        try:
            adapter = _build_live_adapter(args)
        except GarminLiveError as exc:
            _close_sync_row_failed(args.db_path, sync_id, exc)
            print(
                f"live pull error: {exc}\n"
                f"Check credentials with `hai auth status`; if those look "
                f"OK, run `hai doctor --deep` to probe the live API.",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
    else:  # intervals_icu
        try:
            adapter = _build_intervals_icu_adapter(args)
        except IntervalsIcuError as exc:
            _close_sync_row_failed(args.db_path, sync_id, exc)
            print(
                f"intervals.icu pull error: {exc}\n"
                f"Check credentials with `hai auth status`; run "
                f"`hai doctor --deep` to classify the live-API "
                f"failure (see `reporting/docs/intervals_icu_403_triage.md`).",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT

    try:
        pull = adapter.load(as_of)
    except (GarminLiveError, IntervalsIcuError) as exc:
        _close_sync_row_failed(args.db_path, sync_id, exc)
        print(f"live pull error: {exc}", file=sys.stderr)
        return exit_codes.TRANSIENT

    manual = None
    if args.manual_readiness_json:
        manual, err = _load_json_arg(
            args.manual_readiness_json,
            arg_name="--manual-readiness-json",
            command_label="hai pull",
        )
        if err is not None:
            return err
    elif args.use_default_manual_readiness:
        manual = default_manual_readiness(as_of)
    else:
        # D2 §pull adapter integration: auto-read same-day
        # manual_readiness_raw when no explicit override is passed. The
        # --manual-readiness-json file path and --use-default-manual-readiness
        # flag both remain explicit overrides that win against the DB.
        manual = _autoread_manual_readiness(
            getattr(args, "db_path", None),
            user_id=args.user_id,
            as_of=as_of,
        )

    # rows_pulled: 1 if we got a daily summary row; 0 otherwise. This
    # maps "one logical day's evidence = one row" without pretending the
    # per-metric arrays are independent rows.
    rows = 1 if pull.get("raw_daily_row") is not None else 0
    # M6: the live adapter exposes partial-pull telemetry on its
    # instance so the pull dict's key set stays byte-identical to the
    # CSV adapter. The CSV adapter has no partial concept, so attribute
    # absence means "ok" by default.
    partial = getattr(adapter, "last_pull_partial", False)
    sync_status: Literal["ok", "partial", "failed"] = (
        "partial" if partial else "ok"
    )
    _close_sync_row_ok(
        args.db_path,
        sync_id,
        rows_pulled=rows,
        rows_accepted=rows,
        duplicates_skipped=0,
        status=sync_status,
    )

    payload = {
        "as_of_date": as_of.isoformat(),
        "user_id": args.user_id,
        "source": adapter.source_name,
        "pull": pull,
        "manual_readiness": manual,
    }
    _emit_json(payload)
    return exit_codes.OK


# ---------------------------------------------------------------------------
# Sync-log CLI shim — best-effort wrappers around core/state/sync_log
#
# All three helpers silently skip if the DB file is absent. Sync logging
# is lighter-weight telemetry than the accepted-state projections
# (which emit stderr warnings on failure) — an operator who hasn't run
# `hai state init` shouldn't see stderr noise every time they pull.
# ---------------------------------------------------------------------------


def _autoread_manual_readiness(
    db_path_arg,
    *,
    user_id: str,
    as_of: date,
) -> Optional[dict]:
    """Return the canonical same-day readiness row from the state DB, or None.

    Called by ``hai pull`` when neither ``--manual-readiness-json``
    nor ``--use-default-manual-readiness`` is set. Silent on DB-absent
    (pre-``hai state init`` users) and on pre-migration-015 DBs — the
    caller treats both as "no readiness to propagate."
    """

    from health_agent_infra.core.state import (
        open_connection,
        read_latest_manual_readiness,
        resolve_db_path,
    )

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        return None
    conn = open_connection(db_path)
    try:
        return read_latest_manual_readiness(
            conn, user_id=user_id, as_of_date=as_of,
        )
    finally:
        conn.close()


def _open_sync_row(
    db_path_arg,
    *,
    source: str,
    user_id: str,
    mode: str,
    for_date,
):
    from health_agent_infra.core.state import (
        begin_sync,
        open_connection,
        resolve_db_path,
    )

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        return None
    conn = open_connection(db_path)
    try:
        return begin_sync(
            conn,
            source=source,
            user_id=user_id,
            mode=mode,
            for_date=for_date,
        )
    except sqlite3.OperationalError:
        # Pre-migration-008 DB: skip quietly.
        return None
    finally:
        conn.close()


def _close_sync_row_ok(
    db_path_arg,
    sync_id,
    *,
    rows_pulled,
    rows_accepted,
    duplicates_skipped,
    status: Literal["ok", "partial", "failed"] = "ok",
) -> None:
    if sync_id is None:
        return
    from health_agent_infra.core.state import (
        complete_sync,
        open_connection,
        resolve_db_path,
    )

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        return
    conn = open_connection(db_path)
    try:
        complete_sync(
            conn,
            sync_id,
            rows_pulled=rows_pulled,
            rows_accepted=rows_accepted,
            duplicates_skipped=duplicates_skipped,
            status=status,
        )
    except sqlite3.OperationalError:
        return
    finally:
        conn.close()


def _close_sync_row_failed(db_path_arg, sync_id, exc: BaseException) -> None:
    if sync_id is None:
        return
    from health_agent_infra.core.state import (
        fail_sync,
        open_connection,
        resolve_db_path,
    )

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        return
    conn = open_connection(db_path)
    try:
        fail_sync(
            conn,
            sync_id,
            error_class=type(exc).__name__,
            error_message=str(exc),
        )
    except sqlite3.OperationalError:
        return
    finally:
        conn.close()


def _sync_if_db(
    db_path_arg,
    *,
    source: str,
    user_id: str,
    mode: str,
    for_date=None,
):
    """Context manager: write a sync_run_log row if the DB exists, else no-op.

    Yields a mutable dict the caller fills in before exit
    (``run["rows_pulled"] = N`` etc.). Exceptions re-raise after the
    row is closed with ``fail_sync``. When the DB is absent or predates
    migration 008 the yielded dict has no ``sync_id`` and nothing is
    written.
    """

    from contextlib import contextmanager

    @contextmanager
    def _cm():
        sync_id = _open_sync_row(
            db_path_arg,
            source=source,
            user_id=user_id,
            mode=mode,
            for_date=for_date,
        )
        run: dict = {
            "sync_id": sync_id,
            "rows_pulled": None,
            "rows_accepted": None,
            "duplicates_skipped": None,
            "status": "ok",
        }
        try:
            yield run
        except Exception as exc:
            _close_sync_row_failed(db_path_arg, sync_id, exc)
            raise
        else:
            _close_sync_row_ok(
                db_path_arg,
                sync_id,
                rows_pulled=run.get("rows_pulled"),
                rows_accepted=run.get("rows_accepted"),
                duplicates_skipped=run.get("duplicates_skipped"),
                status=run.get("status", "ok"),
            )

    return _cm()


def _build_live_adapter(args: argparse.Namespace):
    """Resolve credentials → live client → adapter, or raise GarminLiveError.

    Pulled into a helper so tests can monkeypatch the client-building step
    while exercising the real CLI arg parsing and credential flow.

    M6: the adapter + client share a :class:`RetryConfig` derived from
    the merged thresholds. A user TOML ``[pull.garmin_live]`` section
    tunes attempts / backoff / rate-limit behavior without code edits.
    """

    from health_agent_infra.core.pull.garmin_live import (
        retry_config_from_thresholds,
    )

    store = CredentialStore.default()
    credentials = store.load_garmin()
    if credentials is None:
        raise GarminLiveError(
            "no Garmin credentials found. Run `hai auth garmin` or set "
            "HAI_GARMIN_EMAIL + HAI_GARMIN_PASSWORD."
        )
    try:
        thresholds = load_thresholds()
    except ConfigError:
        # Malformed TOML is a config-level concern hai doctor surfaces;
        # for a pull, fall back to packaged defaults rather than failing.
        thresholds = None
    retry_cfg = retry_config_from_thresholds(thresholds)
    client = build_default_client(credentials, retry_config=retry_cfg)
    history_days = getattr(args, "history_days", 14)
    return GarminLiveAdapter(
        client=client,
        history_days=history_days,
        retry_config=retry_cfg,
    )


def _build_intervals_icu_adapter(args: argparse.Namespace) -> IntervalsIcuAdapter:
    """Resolve Intervals.icu credentials → client → adapter, or raise IntervalsIcuError."""

    store = CredentialStore.default()
    credentials = store.load_intervals_icu()
    if credentials is None:
        raise IntervalsIcuError(
            "no Intervals.icu credentials found. Run `hai auth intervals-icu` "
            "or set HAI_INTERVALS_ATHLETE_ID + HAI_INTERVALS_API_KEY."
        )
    client = build_intervals_icu_client(credentials)
    history_days = getattr(args, "history_days", 14)
    user_id = getattr(args, "user_id", "u_local_1") or "u_local_1"
    return IntervalsIcuAdapter(
        client=client, history_days=history_days, user_id=user_id,
    )


# v0.1.14.1 W-GARMIN-MANIFEST-SIGNAL: per-choice metadata for the
# ``--source`` flag on ``hai pull`` and ``hai daily``. Single source of
# truth so both annotation sites can't drift. Read by the capabilities
# walker; surfaced under ``flags[].choice_metadata`` in the manifest.
PULL_SOURCE_CHOICE_METADATA: dict[str, dict[str, Any]] = {
    "csv": {
        # F-PV14-01 (v0.1.15): tag the CSV adapter explicitly as a
        # fixture so an agent driving the CLI knows the path is the
        # committed packaged export, not a live wearable feed. Pairs
        # with the cmd_pull default-deny guard against writing fixture
        # rows into the canonical state DB.
        "reliability": "reliable",
        "source_type": "fixture",
        "data_origin": "packaged-csv-export",
        "writes_to_canonical_db_default": False,
        "escape_paths": (
            "hai demo start | --allow-fixture-into-real-state | "
            "--db-path | HAI_STATE_DB"
        ),
    },
    "garmin_live": {
        "source_type": "live",
        "reliability": "unreliable",
        "reason": "rate-limited / Cloudflare-blocked (HTTP 429 / 403)",
        "prefer_instead": "intervals_icu",
    },
    "intervals_icu": {
        "reliability": "reliable",
        "source_type": "live",
    },
}

# v0.1.14.1: stderr warning string emitted when the resolved pull
# source is ``garmin_live``. Kept as a module constant so tests can
# assert against it without duplicating prose.
_GARMIN_LIVE_WARNING = (
    "WARN [hai pull]: Garmin live is rate-limited and frequently "
    "fails (HTTP 429 / Cloudflare 403). intervals.icu is the "
    "maintainer-supported live source. See AGENTS.md \"Settled "
    "Decisions\" and `hai capabilities --json` "
    "(commands[hai pull].flags[--source].choice_metadata)."
)


def _resolve_pull_source(args: argparse.Namespace) -> str:
    """Pick the pull source.

    Resolution order (v0.1.6 W5):

      1. Explicit ``--source <s>`` — wins unconditionally.
      2. Legacy ``--live`` flag — preserved for back-compat; equivalent
         to ``--source garmin_live``.
      3. Auto-default — when neither flag is passed: if intervals.icu
         credentials are configured, use ``intervals_icu`` (the
         maintainer's declared supported live source); else fall back
         to ``csv`` (the committed fixture, useful for offline runs
         and tests).

    Garmin live is not in the auto-default chain because Garmin
    Connect's login surface is rate-limited and unreliable for live
    scraping (the 2026-04-25 user session reproduced 429s from
    mobile + portal + Cloudflare in succession). Users who want
    Garmin live must opt in explicitly via ``--source garmin_live``
    or ``--live``.

    v0.1.14.1 W-GARMIN-MANIFEST-SIGNAL: when the resolved source is
    ``garmin_live``, emit a stderr warning at resolution time so
    callers (especially programmatic agents that bypassed the help
    text and the capabilities manifest) get the unreliability signal
    even if the upstream login subsequently succeeds. The warning does
    not gate the call; it is purely diagnostic.
    """

    explicit = getattr(args, "source", None)
    if explicit is not None:
        resolved = explicit
    elif getattr(args, "live", False):
        resolved = "garmin_live"
    elif _intervals_icu_configured():
        # Auto-default: intervals.icu when configured, else csv. Keep
        # the check cheap (credential presence, no network) so this
        # resolution adds no perceptible latency.
        resolved = "intervals_icu"
    else:
        resolved = "csv"

    if resolved == "garmin_live":
        print(_GARMIN_LIVE_WARNING, file=sys.stderr)

    return resolved


def _intervals_icu_configured() -> bool:
    """Return True when intervals.icu credentials are reachable.

    Probes the credential store; never resolves a network host. Used
    by ``_resolve_pull_source`` to make intervals.icu the implicit
    default when the user has set up auth.
    """

    try:
        store = CredentialStore.default()
        return store.load_intervals_icu() is not None
    except Exception:  # noqa: BLE001 — auth backend hiccup → fall back to csv
        return False


# ---------------------------------------------------------------------------
# hai clean
# ---------------------------------------------------------------------------

def cmd_clean(args: argparse.Namespace) -> int:

    pulled, err = _load_json_arg(
        args.evidence_json,
        arg_name="--evidence-json",
        command_label="hai clean",
    )
    if err is not None:
        return err
    as_of = _coerce_date(pulled["as_of_date"])
    user_id = pulled["user_id"]
    pull = pulled["pull"]
    manual = pulled.get("manual_readiness")

    activities = pull.get("activities", []) or []

    # Enrich the daily rollup with structural aggregates from activities.
    # Before v0.1.4, the intervals.icu adapter only hit /wellness.json, so
    # distance_m / moderate_intensity_min / vigorous_intensity_min came back
    # null from the wellness stream — running domain saw no session coverage
    # and deferred every day. With /activities wired up, we aggregate
    # today's sessions into the raw_row before clean_inputs reads it, so
    # the existing Phase 1 classifier receives real numbers.
    raw_row = pull.get("raw_daily_row")
    if raw_row is not None and activities:
        _enrich_raw_row_with_activity_aggregate(
            raw_row=raw_row,
            activities=[a for a in activities if a.get("as_of_date") == as_of.isoformat()],
        )

    evidence = clean_inputs(
        user_id=user_id,
        as_of_date=as_of,
        garmin_sleep=pull.get("sleep"),
        garmin_resting_hr_recent=pull.get("resting_hr", []),
        garmin_hrv_recent=pull.get("hrv", []),
        garmin_training_load_7d=pull.get("training_load", []),
        manual_readiness=manual,
    )
    summary = build_raw_summary(
        user_id=user_id,
        as_of_date=as_of,
        garmin_sleep=pull.get("sleep"),
        garmin_resting_hr_recent=pull.get("resting_hr", []),
        garmin_hrv_recent=pull.get("hrv", []),
        garmin_training_load_7d=pull.get("training_load", []),
        raw_daily_row=raw_row,
    )

    projection_status = None
    if raw_row is not None:
        projection_result = _project_clean_into_state(
            args.db_path,
            as_of_date=as_of,
            user_id=user_id,
            raw_row=raw_row,
            activities=activities,
        )
        projection_status = projection_result["status"]
        # v0.1.9 B5: fail closed when the projection raised. Pre-v0.1.9
        # the function silently warned and let cmd_clean exit OK, which
        # meant `hai daily` could plan over stale state without anyone
        # knowing. Codex 2026-04-26 caught this.
        if projection_status == _PROJECTION_RESULT_FAILED:
            sys.stderr.write(
                f"hai clean exit non-OK: clean projection into state DB "
                f"failed ({projection_result['error_type']}: "
                f"{projection_result['error']}). The cleaned-evidence "
                f"JSON is still emitted on stdout but downstream "
                f"`hai daily` / `hai state snapshot` callers will see "
                f"stale or absent accepted-state rows.\n"
            )
            _emit_json({
                "cleaned_evidence": evidence.to_dict(),
                "raw_summary": summary.to_dict(),
                "projection_status": projection_status,
                "projection_error": projection_result["error"],
            })
            return exit_codes.INTERNAL

    _emit_json({
        "cleaned_evidence": evidence.to_dict(),
        "raw_summary": summary.to_dict(),
        "projection_status": projection_status,
    })
    return exit_codes.OK


def _enrich_raw_row_with_activity_aggregate(
    *, raw_row: dict, activities: list[dict],
) -> None:
    """Fill the running fields on ``raw_row`` from today's activities.

    Mutates ``raw_row`` in place. The aggregator returns
    ``accepted_running_state_daily``-shaped keys (``total_distance_m``,
    intensity minutes); the raw daily row uses the Garmin-shaped
    ``distance_m`` key — so we remap that one explicitly. Wellness
    columns stay authoritative for non-running metrics.
    """

    from health_agent_infra.core.state import aggregate_activities_to_daily_rollup

    agg = aggregate_activities_to_daily_rollup(activities)
    mapping = {
        "distance_m": "total_distance_m",
        "moderate_intensity_min": "moderate_intensity_min",
        "vigorous_intensity_min": "vigorous_intensity_min",
    }
    for raw_key, agg_key in mapping.items():
        if agg.get(agg_key) is not None:
            raw_row[raw_key] = agg[agg_key]


_PROJECTION_RESULT_SKIPPED_DB_ABSENT = "skipped_db_absent"
_PROJECTION_RESULT_OK = "ok"
_PROJECTION_RESULT_FAILED = "failed"


def _evidence_hash(raw_row: dict, activities: Optional[list[dict]]) -> str:
    """Deterministic 16-hex-char hash of the cleaned evidence.

    Used as the ``export_batch_id`` so replays of identical evidence
    produce identical raw provenance rows (idempotent at the source-row
    layer). v0.1.9 B5 fix for the wall-clock ``export_batch_id`` Codex
    flagged: pre-v0.1.9 every replay minted a new id, so a re-pulled
    day created a new ``source_daily_garmin`` row instead of resolving
    to the existing one.
    """

    import hashlib

    payload = {
        "raw_row": raw_row,
        "activities": activities or [],
    }
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _project_clean_into_state(
    db_path_arg,
    *,
    as_of_date: date,
    user_id: str,
    raw_row: dict,
    activities: Optional[list[dict]] = None,
) -> dict:
    """Project Garmin raw row + accepted-state rows into the state DB.

    Returns a structured status dict (v0.1.9 B5 — pre-v0.1.9 the
    function returned ``None`` and swallowed DB failures as warnings,
    so ``hai daily`` could plan over stale or absent accepted-state
    rows without the caller knowing). Shape::

        {
          "status": "ok" | "skipped_db_absent" | "failed",
          "export_batch_id": "<hex>" | None,
          "error": str | None,
          "error_type": str | None,
        }

    Callers (cmd_clean, cmd_daily) can inspect ``status`` to decide
    whether to proceed or exit non-zero.

    **Atomicity contract.** All INSERT/UPDATE operations land in a
    single ``BEGIN IMMEDIATE`` transaction: either every row commits, or
    none do. A failure mid-projection rolls back, leaving the DB in the
    same shape it was before ``hai clean`` started. Without this, a
    partial failure could persist source_daily_garmin while both accepted
    tables stayed empty — and unlike review, `hai clean` has no JSONL
    audit log, so there would be no reproject path.

    **Scope.** Garmin-sourced daily fields + intervals.icu-sourced
    per-activity rows land here. Manual stress, nutrition, gym, notes
    flow through their own ``hai intake`` commands (7C) with their own
    raw-evidence tables; they never enter accepted state via ``hai clean``.

    **Fail-soft at the CLI boundary.** DB absent or transaction rolled back
    ⇒ stderr warning and return. stdout is unaffected. Same pattern as
    ``_dual_write_project``, adapted for the three-table recovery path.
    """

    from health_agent_infra.core.state import (
        open_connection,
        project_accepted_recovery_state_daily,
        project_accepted_running_state_daily,
        project_accepted_sleep_state_daily,
        project_accepted_stress_state_daily,
        project_activity,
        project_source_daily_garmin,
        resolve_db_path,
    )

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        print(
            f"note: state DB projection skipped ({db_path} not found). "
            f"`hai clean` stdout is still emitted. Run `hai state init` to "
            f"enable DB dual-write.",
            file=sys.stderr,
        )
        return {
            "status": _PROJECTION_RESULT_SKIPPED_DB_ABSENT,
            "export_batch_id": None,
            "error": None,
            "error_type": None,
        }

    # v0.1.9 B5: export_batch_id is now derived deterministically from
    # the cleaned evidence content rather than wall-clock time. Replays
    # of identical evidence collapse to one source_daily_garmin row;
    # corrections (genuinely new Garmin numbers) hash differently and
    # land as a fresh row, preserving the supersession model.
    export_batch_id = f"live_{_evidence_hash(raw_row, activities)}"
    source_row_id = f"{export_batch_id}:0"

    conn = open_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            project_source_daily_garmin(
                conn,
                as_of_date=as_of_date,
                user_id=user_id,
                raw_row=raw_row,
                export_batch_id=export_batch_id,
                commit_after=False,
            )
            project_accepted_recovery_state_daily(
                conn,
                as_of_date=as_of_date,
                user_id=user_id,
                raw_row=raw_row,
                source_row_ids=[source_row_id],
                commit_after=False,
            )
            # v0.1.10 W-D / F-C-03 fix: merge per-activity aggregates for
            # as_of_date into raw_row before projecting daily running
            # state. Without this, intervals.icu users see "running
            # deferred — insufficient signal" every day even when they
            # have logged activities, because the daily summary CSV
            # lacks total_distance_m + intensity minutes. The aggregator
            # was already implemented (running_activity.aggregate_*) but
            # never wired into the clean flow.
            from health_agent_infra.core.state import (
                aggregate_activities_to_daily_rollup,
            )

            # Aggregator output → projector's raw_row key names.
            # The projector reads `raw_row.get("distance_m")` not
            # `total_distance_m`. Map field names so the merged keys
            # actually flow through the projection.
            _ROLLUP_TO_RAW = {
                "total_distance_m": "distance_m",
                "moderate_intensity_min": "moderate_intensity_min",
                "vigorous_intensity_min": "vigorous_intensity_min",
            }

            today_activities = [
                a for a in activities or []
                if a.get("as_of_date") == as_of_date.isoformat()
            ]
            today_rollup: Optional[dict[str, Any]] = None
            if today_activities:
                today_rollup = aggregate_activities_to_daily_rollup(today_activities)
                # Merge non-None rollup fields into raw_row. Don't
                # overwrite values that were already populated by the
                # daily summary — trust the upstream daily totals when
                # both sources exist.
                for rollup_key, raw_key in _ROLLUP_TO_RAW.items():
                    value = today_rollup.get(rollup_key)
                    if value is not None and raw_row.get(raw_key) in (None, 0):
                        raw_row[raw_key] = value

            project_accepted_running_state_daily(
                conn,
                as_of_date=as_of_date,
                user_id=user_id,
                raw_row=raw_row,
                source_row_ids=[source_row_id],
                commit_after=False,
                # v0.1.11 W-R (Codex F-C-03): pass the rollup so the
                # projector can populate session_count + total_duration_s
                # AND stamp derivation_path='activity_rollup' when per-
                # activity data was used.
                rollup=today_rollup,
            )

            # v0.1.10 W-D extension: also backfill accepted_running_state_daily
            # rows for historical dates present in `activities`. Otherwise
            # `running.history` stays empty and the running classifier sees
            # cold_start: True even after logging weeks of runs. Each
            # historical date gets an isolated rollup → projection.
            if activities:
                by_date: dict[str, list[dict[str, Any]]] = {}
                for a in activities:
                    d = a.get("as_of_date")
                    if not d or d == as_of_date.isoformat():
                        continue
                    by_date.setdefault(d, []).append(a)
                for hist_date_iso, hist_acts in by_date.items():
                    try:
                        from datetime import date as _date_cls
                        hist_date = _date_cls.fromisoformat(hist_date_iso)
                    except (TypeError, ValueError):
                        continue
                    rollup = aggregate_activities_to_daily_rollup(hist_acts)
                    hist_raw_row: dict[str, Any] = {}
                    for rollup_key, raw_key in _ROLLUP_TO_RAW.items():
                        value = rollup.get(rollup_key)
                        if value is not None:
                            hist_raw_row[raw_key] = value
                    if not hist_raw_row:
                        continue
                    # Synthetic source_row_id for historical activity
                    # backfill — distinguishes from the today-summary
                    # source row.
                    hist_source_row_id = (
                        f"running_activity_rollup:{hist_date_iso}:"
                        f"{user_id}"
                    )
                    project_accepted_running_state_daily(
                        conn,
                        as_of_date=hist_date,
                        user_id=user_id,
                        raw_row=hist_raw_row,
                        source_row_ids=[hist_source_row_id],
                        ingest_actor="intervals_icu_activity_rollup",
                        commit_after=False,
                        # v0.1.11 W-R: backfilled historical rows are
                        # always rollup-derived; stamp derivation_path
                        # accordingly + carry the session_count.
                        rollup=rollup,
                    )
            project_accepted_sleep_state_daily(
                conn,
                as_of_date=as_of_date,
                user_id=user_id,
                raw_row=raw_row,
                source_row_ids=[source_row_id],
                commit_after=False,
            )
            project_accepted_stress_state_daily(
                conn,
                as_of_date=as_of_date,
                user_id=user_id,
                raw_row=raw_row,
                source_row_ids=[source_row_id],
                commit_after=False,
            )
            if activities:
                for a in activities:
                    project_activity(
                        conn, activity=a, commit_after=False,
                    )
            # v0.1.8 W51 — project data_quality_daily for as_of_date as
            # part of the same atomic clean-write transaction. Codex P1-1
            # fix: data-quality projection MUST live on a write path, not
            # on `hai stats --data-quality` which is contractually
            # read-only. We build an in-memory snapshot for the side
            # effect (no second DB write) and let the projector upsert
            # the per-(domain, source) rows.
            try:
                from health_agent_infra.core.data_quality.projector import (
                    project_data_quality_for_date,
                )
                from health_agent_infra.core.state import build_snapshot

                snapshot = build_snapshot(
                    conn,
                    as_of_date=as_of_date,
                    user_id=user_id,
                    now_local=datetime.now(),
                )
                project_data_quality_for_date(
                    conn, snapshot=snapshot, commit_after=False,
                )
            except Exception as exc:  # noqa: BLE001 — see Codex R2-1
                # Codex round-2 R2-1 fix: data-quality projection is
                # best-effort (we never block the accepted-state clean
                # commit on it), but failures must be visible — a
                # silently-skipped projector means stats --data-quality
                # returns empty without explanation. Surface to stderr
                # while letting the outer transaction commit the
                # accepted-state writes that already happened.
                print(
                    f"warning: data-quality projection failed for "
                    f"as_of_date={as_of_date.isoformat()} "
                    f"user_id={user_id}: {type(exc).__name__}: {exc}. "
                    f"Accepted-state writes proceed; "
                    f"`hai stats --data-quality` will report empty "
                    f"rows for this date until the projection is "
                    f"re-run.",
                    file=sys.stderr,
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    except Exception as exc:  # noqa: BLE001 — surface failure to caller
        print(
            f"warning: clean projection into state DB failed and was rolled "
            f"back: {exc}. `hai clean` output is still durable on stdout.",
            file=sys.stderr,
        )
        try:
            conn.close()
        except Exception:
            pass
        return {
            "status": _PROJECTION_RESULT_FAILED,
            "export_batch_id": export_batch_id,
            "error": str(exc),
            "error_type": type(exc).__name__,
        }
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return {
        "status": _PROJECTION_RESULT_OK,
        "export_batch_id": export_batch_id,
        "error": None,
        "error_type": None,
    }


