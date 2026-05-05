"""``hai config + init + setup-skills`` handler group.

Owns: ``hai init``, ``hai setup-skills``, ``hai config init/show/validate/diff``.
Plus the validate/diff helpers ``_walk_keys`` / ``_lookup`` / ``_MISSING`` /
``_review_summary_range_issues`` (verified at W-29.2.2 to be config-side, not
review-side, despite the misleading name), and the init helpers
``_run_interactive_auth`` / ``_run_first_pull_backfill`` / ``_run_guided_onboarding``
/ ``_onboarding_default_pull_runner`` / ``_onboarding_default_today_renderer``.

W-29.2.7 split: extracted from cli/__init__.py 2 ranges (3090-3418 config
commands + 4020-4600 init/setup-skills/onboarding cluster).

Cross-handler imports: many cli-private symbols (``_emit_json``,
``_credential_store_for``, ``_skills_source``, ``DEFAULT_CLAUDE_SKILLS_DIR``,
``CredentialStore``, ``DEFAULT_THRESHOLDS``, etc.) lazy-imported at call
time from ``health_agent_infra.cli`` to avoid module-load circularity.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

import tomllib

from health_agent_infra.core import exit_codes
from health_agent_infra.core.config import (
    ConfigError,
    load_thresholds,
    scaffold_thresholds_toml,
    user_config_path,
)
from health_agent_infra.core.paths import resolve_base_dir
from health_agent_infra.core.pull.garmin_live import GarminLiveError
from health_agent_infra.core.pull.intervals_icu import IntervalsIcuError

# Cli-private symbols defined in cli/__init__.py before line ~3090;
# partial-module imports resolve cleanly at module-load time.
from health_agent_infra.cli import (  # noqa: E402
    DEFAULT_CLAUDE_SKILLS_DIR,
    _PACKAGE_VERSION,
    _credential_store_for,
    _emit_json,
    _skills_source,
    cmd_auth_garmin,
)


def cmd_config_init(args: argparse.Namespace) -> int:
    dest = Path(args.path).expanduser() if args.path else user_config_path()
    if dest.exists() and not args.force:
        print(
            f"config file already exists at {dest}; pass --force to overwrite",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(scaffold_thresholds_toml(), encoding="utf-8")
    _emit_json({"written": str(dest), "overwrote": bool(args.force and dest.exists())})
    return exit_codes.OK


def cmd_config_show(args: argparse.Namespace) -> int:
    path = Path(args.path).expanduser() if args.path else None
    try:
        merged = load_thresholds(path=path)
    except ConfigError as exc:
        print(
            f"config error: {exc}\n"
            f"Edit the thresholds file or regenerate it via "
            f"`hai config init --force`.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT
    effective_path = path if path is not None else user_config_path()
    _emit_json({
        "source_path": str(effective_path),
        "source_exists": effective_path.exists(),
        "effective_thresholds": merged,
    })
    return exit_codes.OK


# ---------------------------------------------------------------------------
# v0.1.8 W39 — config validate / diff / set
# ---------------------------------------------------------------------------


def _walk_keys(d: dict, prefix: tuple = ()) -> list[tuple[tuple, Any]]:
    """Flatten a nested dict into ``(path_tuple, leaf_value)`` pairs.

    Lists are treated as leaves (matches `_deep_merge` semantics).
    """

    out: list[tuple[tuple, Any]] = []
    for k, v in d.items():
        if isinstance(v, dict):
            out.extend(_walk_keys(v, prefix + (k,)))
        else:
            out.append((prefix + (k,), v))
    return out


def _lookup(d: dict, path: tuple) -> Any:
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return _MISSING
        cur = cur[k]
    return cur


_MISSING = object()


def _review_summary_range_issues(user_overrides: dict) -> list[dict[str, Any]]:
    """Per-key local range checks for [policy.review_summary] keys.

    Returns a list of issue dicts with kind='range_violation' that the
    main validator concatenates to its other findings. Range violations
    are always blocking (not gated on --strict) — they would produce
    misbehaving W48 tokens at use time, not just an unknown surface.
    """

    block = (
        user_overrides.get("policy", {}).get("review_summary", {})
        if isinstance(user_overrides.get("policy"), dict)
        else {}
    )
    if not isinstance(block, dict):
        return []

    out: list[dict[str, Any]] = []

    def _flag(path: str, detail: str) -> None:
        out.append({
            "path": path, "kind": "range_violation", "detail": detail,
        })

    # Codex R2-3 helper: bool is a subclass of int in Python, so a
    # naked `isinstance(v, (int, float))` accepts True/False. Range
    # checks must reject bools as range-violation candidates so they
    # surface via the upstream `type_mismatch` path instead.
    def _is_real_number(v: Any) -> bool:
        return isinstance(v, (int, float)) and not isinstance(v, bool)

    if "window_days" in block:
        v = block["window_days"]
        if _is_real_number(v) and v < 1:
            _flag(
                "policy.review_summary.window_days",
                f"must be >= 1; got {v}",
            )
    if "min_denominator" in block:
        v = block["min_denominator"]
        if _is_real_number(v) and v < 0:
            _flag(
                "policy.review_summary.min_denominator",
                f"must be >= 0; got {v}",
            )
    for key in ("recent_negative_threshold", "recent_positive_threshold"):
        if key in block:
            v = block[key]
            if _is_real_number(v) and v < 0:
                _flag(
                    f"policy.review_summary.{key}",
                    f"must be >= 0; got {v}",
                )
    lower = block.get("mixed_token_lower_bound")
    upper = block.get("mixed_token_upper_bound")
    for key, val in (
        ("mixed_token_lower_bound", lower),
        ("mixed_token_upper_bound", upper),
    ):
        # _is_real_number() guarantees val is int|float at runtime, but
        # it's not a TypeGuard so mypy still sees Optional. Cast inside
        # the gated branch. v0.1.12 W-H2.
        if _is_real_number(val):
            assert val is not None  # narrows to int|float
            if not (0 <= val <= 1):
                _flag(
                    f"policy.review_summary.{key}",
                    f"must be in [0, 1]; got {val}",
                )
    # F-A-06 fix per W-H1: mypy can't narrow lower/upper to non-None
    # via `_is_real_number()` because that helper isn't a TypeGuard.
    # Add a defensive None check so the > comparison sees only floats.
    if (
        _is_real_number(lower)
        and _is_real_number(upper)
        and lower is not None
        and upper is not None
        and lower > upper
    ):
        _flag(
            "policy.review_summary.mixed_token_lower_bound",
            f"must be <= mixed_token_upper_bound ({upper}); got {lower}",
        )
    return out


def cmd_config_validate(args: argparse.Namespace) -> int:
    """`hai config validate` — parse the user's TOML and report
    structural / type problems against ``DEFAULT_THRESHOLDS``.

    Exit code mapping:

      - OK: file is clean (or doesn't exist — not an error).
      - USER_INPUT: file exists but is malformed, or has unknown leaf
        keys when ``--strict`` is set, or has a leaf type that doesn't
        match the corresponding default.
    """

    from health_agent_infra.core.config import DEFAULT_THRESHOLDS

    path = Path(args.path).expanduser() if args.path else user_config_path()
    if not path.exists():
        _emit_json({
            "source_path": str(path),
            "source_exists": False,
            "status": "ok",
            "issues": [],
        })
        return exit_codes.OK

    import tomllib
    try:
        with path.open("rb") as fh:
            user_overrides = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        sys.stderr.write(
            f"hai config validate: malformed TOML at {path}: {exc}\n"
            f"Edit the file to fix the syntax, or regenerate it via "
            f"`hai config init --force`.\n"
        )
        _emit_json({
            "source_path": str(path),
            "source_exists": True,
            "status": "malformed",
            "issues": [{"path": "<root>", "kind": "toml_parse_error", "detail": str(exc)}],
        })
        return exit_codes.USER_INPUT

    issues: list[dict[str, Any]] = []
    for path_tuple, value in _walk_keys(user_overrides):
        default_value = _lookup(DEFAULT_THRESHOLDS, path_tuple)
        dotted = ".".join(path_tuple)
        if default_value is _MISSING:
            issues.append({
                "path": dotted,
                "kind": "unknown_key",
                "detail": "key not present in DEFAULT_THRESHOLDS",
            })
            continue
        # Compare scalar leaf types. Both being numeric (int/float) is
        # allowed because TOML's integer/float distinction shouldn't
        # break a user who wrote `0` instead of `0.0`.
        # Codex R2-3 fix: `bool` is a subclass of `int` in Python, so
        # `isinstance(True, (int, float))` is True. Without the explicit
        # bool guard a user could land `window_days = true` and have it
        # silently coerced to `1`. Bools must only match bool defaults.
        if isinstance(default_value, bool) and not isinstance(value, bool):
            issues.append({
                "path": dotted,
                "kind": "type_mismatch",
                "detail": f"expected bool; got {type(value).__name__}",
            })
        elif (
            isinstance(default_value, (int, float))
            and not isinstance(default_value, bool)
            and (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
            )
        ):
            issues.append({
                "path": dotted,
                "kind": "type_mismatch",
                "detail": f"expected number; got {type(value).__name__}",
            })
        elif isinstance(default_value, str) and not isinstance(value, str):
            issues.append({
                "path": dotted,
                "kind": "type_mismatch",
                "detail": f"expected str; got {type(value).__name__}",
            })
        elif isinstance(default_value, list) and not isinstance(value, list):
            issues.append({
                "path": dotted,
                "kind": "type_mismatch",
                "detail": f"expected list; got {type(value).__name__}",
            })

    # v0.1.8 W39 / Codex P2-3 fix: per-key local range checks for
    # the [policy.review_summary] block. PLAN.md § 2 W39 promised
    # "numeric values satisfy local range checks where possible";
    # the v0.1.8 ship omitted these. Add the obvious bounds for the
    # W48 token thresholds so a user can't land window_days=-7 or
    # mixed_token_lower_bound > mixed_token_upper_bound silently.
    issues.extend(_review_summary_range_issues(user_overrides))

    strict = bool(getattr(args, "strict", False))
    has_blocking = any(
        i["kind"] in ("toml_parse_error", "type_mismatch", "range_violation")
        or (strict and i["kind"] == "unknown_key")
        for i in issues
    )

    _emit_json({
        "source_path": str(path),
        "source_exists": True,
        "status": "issues" if issues else "ok",
        "issues": issues,
        "strict": strict,
    })
    return exit_codes.USER_INPUT if has_blocking else exit_codes.OK


def cmd_config_diff(args: argparse.Namespace) -> int:
    """`hai config diff` — list user-overridden keys with default vs
    user vs effective values."""

    from health_agent_infra.core.config import DEFAULT_THRESHOLDS

    path = Path(args.path).expanduser() if args.path else user_config_path()
    try:
        merged = load_thresholds(path=path)
    except ConfigError as exc:
        sys.stderr.write(
            f"hai config diff: {exc}\n"
            f"Edit the thresholds file to fix the schema, or regenerate it "
            f"via `hai config init --force`.\n"
        )
        return exit_codes.USER_INPUT

    if not path.exists():
        _emit_json({
            "source_path": str(path),
            "source_exists": False,
            "diffs": [],
        })
        return exit_codes.OK

    import tomllib
    try:
        with path.open("rb") as fh:
            user_overrides = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        sys.stderr.write(
            f"hai config diff: malformed TOML at {path}: {exc}\n"
            f"Edit the file to fix the syntax, or regenerate via "
            f"`hai config init --force`.\n"
        )
        return exit_codes.USER_INPUT

    diffs: list[dict[str, Any]] = []
    for path_tuple, override_value in _walk_keys(user_overrides):
        default_value = _lookup(DEFAULT_THRESHOLDS, path_tuple)
        effective_value = _lookup(merged, path_tuple)
        diffs.append({
            "path": ".".join(path_tuple),
            "default": (
                None if default_value is _MISSING else default_value
            ),
            "override": override_value,
            "effective": (
                None if effective_value is _MISSING else effective_value
            ),
            "key_known": default_value is not _MISSING,
        })

    _emit_json({
        "source_path": str(path),
        "source_exists": True,
        "diffs": diffs,
    })
    return exit_codes.OK


def cmd_setup_skills(args: argparse.Namespace) -> int:
    dest = Path(args.dest).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    with _skills_source() as skills_source:
        if not skills_source.exists():
            print(
                f"skills/ not found at {skills_source}\n"
                f"Reinstall the package (`pipx install --force "
                f"health-agent-infra`) and retry; the bundled skills "
                f"directory is missing from the wheel.",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
        for skill_dir in skills_source.iterdir():
            if not skill_dir.is_dir():
                continue
            target = dest / skill_dir.name
            if target.exists():
                if not args.force:
                    print(f"skipping existing skill: {target} (pass --force to overwrite)")
                    continue
                shutil.rmtree(target)
            shutil.copytree(skill_dir, target)
            copied.append(str(target))
    _emit_json({"copied": copied, "dest": str(dest)})
    return exit_codes.OK


# ---------------------------------------------------------------------------
# hai init — first-run setup wizard (idempotent, non-interactive)
# ---------------------------------------------------------------------------


def cmd_init(args: argparse.Namespace) -> int:
    """First-run setup for the actual v1 product. Idempotent and safe to
    rerun.

    Three pieces of real v1 setup happen here, each re-using the same
    underlying surface the single-purpose subcommands call:

        1. Thresholds TOML (``hai config init`` path + scaffolder).
        2. State DB + migrations (``hai state init`` — creates file,
           applies any pending migration, no-op at head).
        3. Skills copied to the Claude skills directory (``hai
           setup-skills`` — skips existing unless ``--force``).

    Garmin credentials are reported as a status only. ``hai init`` stays
    non-interactive so agents and tests can drive it; the existing
    ``hai auth garmin`` command owns interactive credential entry.

    No nutrition / meal-level setup — v1 nutrition is macros-only and
    nothing here needs scaffolding per the Phase 2.5 retrieval gate.
    """

    from health_agent_infra.core.state import (
        current_schema_version,
        initialize_database,
        open_connection,
        resolve_db_path,
    )

    report: dict[str, Any] = {
        "version": _PACKAGE_VERSION,
        "steps": {},
    }

    # 1. thresholds TOML
    thresholds_path = (
        Path(args.thresholds_path).expanduser()
        if args.thresholds_path
        else user_config_path()
    )
    if thresholds_path.exists() and not args.force:
        report["steps"]["config"] = {
            "status": "already_present",
            "path": str(thresholds_path),
        }
    else:
        thresholds_path.parent.mkdir(parents=True, exist_ok=True)
        overwrote = thresholds_path.exists()
        thresholds_path.write_text(scaffold_thresholds_toml(), encoding="utf-8")
        report["steps"]["config"] = {
            "status": "overwrote" if overwrote else "created",
            "path": str(thresholds_path),
        }

    # 2. state DB + migrations
    db_path = resolve_db_path(args.db_path)
    db_existed_before = db_path.exists()
    version_before = 0
    if db_existed_before:
        conn = open_connection(db_path)
        try:
            version_before = current_schema_version(conn)
        finally:
            conn.close()
    resolved, applied = initialize_database(db_path)
    if not db_existed_before:
        db_status = "created"
    elif applied:
        db_status = "migrated"
    else:
        db_status = "already_at_head"
    report["steps"]["state_db"] = {
        "status": db_status,
        "path": str(resolved),
        "schema_version_before": version_before,
        "applied_migrations": [
            {"version": v, "filename": f} for v, f in applied
        ],
    }

    # 3. skills copy (idempotent unless --force)
    if args.skip_skills:
        report["steps"]["skills"] = {"status": "skipped"}
    else:
        dest = Path(args.skills_dest).expanduser()
        dest.mkdir(parents=True, exist_ok=True)
        copied: list[str] = []
        already: list[str] = []
        with _skills_source() as skills_source:
            if not skills_source.exists():
                report["steps"]["skills"] = {
                    "status": "failed",
                    "dest": str(dest),
                    "error": f"skills/ not found at {skills_source}",
                }
            else:
                for skill_dir in skills_source.iterdir():
                    if not skill_dir.is_dir():
                        continue
                    target = dest / skill_dir.name
                    if target.exists():
                        if not args.force:
                            already.append(str(target))
                            continue
                        shutil.rmtree(target)
                    shutil.copytree(skill_dir, target)
                    copied.append(str(target))
                report["steps"]["skills"] = {
                    "status": "ran",
                    "dest": str(dest),
                    "copied": copied,
                    "already_present": already,
                }

    # 4. Garmin auth — report presence only, never prompt. The operator
    # runs `hai auth garmin` separately for credential entry, or passes
    # --with-auth (step 5) for one-shot interactive onboarding.
    store = _credential_store_for(args)
    auth_status = store.garmin_status()
    configured = bool(auth_status["credentials_available"])
    report["steps"]["auth_garmin"] = {
        "status": "configured" if configured else "missing",
        "credentials_available": configured,
        "hint": (
            None
            if configured
            else (
                "run `hai auth garmin` to store credentials in the OS "
                "keyring, or pass --with-auth to prompt interactively, "
                "or set HAI_GARMIN_EMAIL + HAI_GARMIN_PASSWORD for "
                "non-interactive use"
            )
        ),
    }

    # 5. optional: interactive Garmin auth. Off by default so agents and
    # tests can drive `hai init` non-interactively; opt in with --with-auth
    # for human onboarding.
    if getattr(args, "with_auth", False):
        report["steps"]["interactive_auth"] = _run_interactive_auth(
            args, already_configured=configured,
        )

    # 6. optional: first-pull today via the live adapter. One adapter call
    # (not a loop), `history_days`-wide window (default 1 → 5 API calls).
    # See _run_first_pull_backfill's docstring for why the 0.1.1 loop was
    # replaced.
    if getattr(args, "with_first_pull", False):
        # Re-check credentials: step 5 may have just populated them.
        store_now = _credential_store_for(args)
        creds_now = bool(store_now.garmin_status()["credentials_available"])
        report["steps"]["first_pull"] = _run_first_pull_backfill(
            args,
            db_path=resolved,
            user_id=getattr(args, "user_id", "u_local_1"),
            history_days=int(getattr(args, "history_days", 1) or 1),
            credentials_available=creds_now,
        )

    # 7. W-AA (v0.1.13) — guided onboarding: prompts for intervals.icu
    # creds, authors initial intent + target rows, runs a first pull
    # via the intervals.icu adapter, and surfaces today's plan. Each
    # step is naturally idempotent so a Ctrl-C mid-flow leaves state
    # consistent and a re-run reaches the first incomplete step.
    guided_status: Optional[str] = None
    if getattr(args, "guided", False):
        guided_report = _run_guided_onboarding(
            args,
            db_path=resolved,
            user_id=getattr(args, "user_id", "u_local_1"),
            history_days=int(getattr(args, "history_days", 1) or 1),
        )
        report["steps"]["guided"] = guided_report
        # Two surface fields name the guided flow's outcome: the
        # KeyboardInterrupt-handler returns ``status: "interrupted"``
        # at the top level; the orchestrator's normal path returns
        # ``overall_status`` (one of ok / ok_with_skips / partial). v0.1.13
        # IR round 1 F-IR-02 closure: surface those non-ok shapes via
        # exit-code USER_INPUT so callers (CI scripts, doctor sweeps,
        # other agents) can detect incomplete onboarding without
        # parsing the JSON. The actionable next-step prose is already
        # in the JSON envelope.
        guided_status = (
            guided_report.get("status")
            or guided_report.get("overall_status")
        )

    _emit_json(report)
    if guided_status in {"interrupted", "partial"}:
        # W-AD interlock: every USER_INPUT exit carries an actionable
        # next-step prose hint to stderr. The JSON body already
        # carries ``guided["hint"]`` with the canonical wording; the
        # stderr surface is the same hint in human-readable form so
        # CI scripts and operators that don't parse JSON still see
        # the right next step.
        guided_block = report["steps"].get("guided") or {}
        hint = guided_block.get("hint") or (
            "rerun `hai init --guided` to resume from the first "
            "incomplete step"
        )
        if guided_status == "interrupted":
            print(
                f"hai init: guided onboarding interrupted. {hint}",
                file=sys.stderr,
            )
        else:  # "partial"
            print(
                "hai init: guided onboarding partially failed. "
                "Check the JSON report for per-step status; rerun "
                "`hai init --guided` to retry the failed step(s).",
                file=sys.stderr,
            )
        return exit_codes.USER_INPUT
    return exit_codes.OK


def _run_interactive_auth(
    args: argparse.Namespace, *, already_configured: bool,
) -> dict[str, Any]:
    """Prompt for Garmin credentials; hand them to ``cmd_auth_garmin``.

    Prompts are written by this wrapper (to stderr) rather than by
    ``cmd_auth_garmin``'s own ``input()`` / ``getpass()``. Reason: we
    redirect ``cmd_auth_garmin``'s stdout to suppress its JSON emission
    (so ``hai init`` stays a single-document stream), and Python's
    ``input()`` writes its prompt to stdout — which would get swallowed
    by the same redirect, leaving the user staring at a blank cursor.
    Routing prompts to stderr keeps them visible and leaves stdout
    unambiguous.

    The collected email + password are passed to ``cmd_auth_garmin`` via
    ``--email`` and ``--password-env`` so no further prompting happens
    downstream; the env var is scrubbed on exit.

    No-op if credentials are already present.
    """

    if already_configured:
        return {"status": "already_configured"}

    import getpass as _getpass
    import io
    import os as _os
    from contextlib import redirect_stdout

    sys.stderr.write("Garmin email: ")
    sys.stderr.flush()
    try:
        email = input().strip()
    except EOFError:
        return {"status": "user_skipped", "reason": "no input (EOF on email)"}
    if not email:
        return {"status": "user_skipped", "reason": "empty email"}
    try:
        password = _getpass.getpass("Garmin password: ")
    except EOFError:
        return {"status": "user_skipped", "reason": "no input (EOF on password)"}
    if not password:
        return {"status": "user_skipped", "reason": "empty password"}

    env_name = "_HAI_INIT_WITH_AUTH_PW"
    _os.environ[env_name] = password
    try:
        auth_args = argparse.Namespace(
            email=email,
            password_stdin=False,
            password_env=env_name,
            _credential_store_override=getattr(
                args, "_credential_store_override", None,
            ),
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cmd_auth_garmin(auth_args)
    finally:
        _os.environ.pop(env_name, None)

    if rc == exit_codes.OK:
        return {"status": "configured"}
    if rc == exit_codes.USER_INPUT:
        return {"status": "user_skipped", "exit_code": int(rc)}
    return {"status": "failed", "exit_code": int(rc)}


def _run_first_pull_backfill(
    args: argparse.Namespace,
    *,
    db_path: Path,
    user_id: str,
    history_days: int,
    credentials_available: bool,
) -> dict[str, Any]:
    """Pull + project today's state via a single live-adapter call.

    **Why one call, not a loop.** Each ``fetch_day`` makes ~5 Garmin
    API requests, and the adapter internally fetches a `history_days`
    window of days. So one ``adapter.load(today)`` with
    `history_days=1` = 5 requests; with the default `history_days=14`
    it's 70 requests. A multi-day backfill loop calling ``adapter.load``
    N times (the 0.1.1 design) produced N*5*14 requests — hundreds in a
    burst — which reliably triggered Garmin's rate limiter and left
    many users unable to complete setup.

    The replacement: one call, small default history window, explicit
    opt-in for larger. The historical-series arrays (resting_hr, hrv,
    training_load) come from the same call's history window, so wider
    windows still surface baseline context when the user wants it —
    they just incur a bigger burst.
    """

    if not credentials_available:
        return {
            "status": "skipped",
            "reason": (
                "no Garmin credentials available; run `hai auth garmin` "
                "(or pass --with-auth) before --with-first-pull"
            ),
        }
    if not db_path.exists():
        return {
            "status": "skipped",
            "reason": f"state DB not found at {db_path}",
        }
    if history_days < 1:
        return {
            "status": "skipped",
            "reason": f"invalid --history-days: {history_days}",
        }

    today = datetime.now(timezone.utc).date()

    # _daily_pull_and_project reads args.history_days when building the
    # live adapter, so routing the config through that attribute is how
    # the history window reaches the adapter without broadening the
    # helper's signature.
    pull_args = argparse.Namespace(
        live=True,
        db_path=str(db_path),
        user_id=user_id,
        history_days=history_days,
    )

    # v0.1.9 B5: ``_daily_pull_and_project`` now manages its own
    # sync_run_log row (fixing the daily-bypasses-provenance gap Codex
    # caught). This caller no longer opens a parallel sync row — that
    # would produce two rows per first-pull. Errors flow through
    # ``_daily_pull_and_project``'s own ``_close_sync_row_failed`` call.
    from health_agent_infra.cli import _daily_pull_and_project
    try:
        source_name, projected, _ = _daily_pull_and_project(
            pull_args, as_of=today, user_id=user_id, db_path=db_path,
        )
    except GarminLiveError as exc:
        return {
            "status": "failed",
            "date": today.isoformat(),
            "history_days": history_days,
            "approx_api_calls": 5 * history_days,
            "error_class": type(exc).__name__,
            "error": str(exc),
            "hint": (
                "429 / rate-limit errors are common on Garmin's API. "
                "Wait 30–60 minutes before retrying; consider "
                "--history-days 1 (5 requests) to minimise burst size."
            ),
        }

    return {
        "status": "ok",
        "date": today.isoformat(),
        "history_days": history_days,
        "approx_api_calls": 5 * history_days,
        "source": source_name,
        "projected_raw_daily": bool(projected),
    }


def _run_guided_onboarding(
    args: argparse.Namespace,
    *,
    db_path: Path,
    user_id: str,
    history_days: int,
) -> dict[str, Any]:
    """W-AA (v0.1.13) — orchestrator wrapper for `hai init --guided`.

    Threads the runtime-side helpers (intervals.icu adapter,
    `hai today` rendering, credential store) into the
    `core.init.run_guided_onboarding` orchestrator. Test injection
    points are deliberately narrow: the orchestrator owns prompts
    + idempotency; the CLI side owns the adapter + render code.
    """

    from health_agent_infra.core.init import (
        StdinPrompts,
        run_guided_onboarding,
    )

    # Test seam: tests can attach a `_guided_prompts_override` to args
    # to skip stdin/getpass entirely. Production callers always go
    # through StdinPrompts.
    prompts = getattr(args, "_guided_prompts_override", None) or StdinPrompts()

    # Test seam: tests can attach a `_guided_pull_runner_override` to
    # bypass the live intervals.icu adapter. Production callers go
    # through `_daily_pull_and_project`.
    pull_runner = getattr(args, "_guided_pull_runner_override", None) or (
        lambda **kw: _onboarding_default_pull_runner(args, **kw)
    )

    today_renderer = getattr(args, "_guided_today_renderer_override", None) or (
        lambda **kw: _onboarding_default_today_renderer(args, **kw)
    )

    credential_store = _credential_store_for(args)

    try:
        result = run_guided_onboarding(
            db_path=db_path,
            user_id=user_id,
            history_days=history_days,
            prompts=prompts,
            credential_store=credential_store,
            pull_runner=pull_runner,
            today_renderer=today_renderer,
        )
    except KeyboardInterrupt:
        # Step is mid-prompt or mid-DB-write; the latter is wrapped in
        # `conn.commit()` so SQLite's transaction guarantees keep state
        # consistent. Surface a partial report so the JSON envelope is
        # honest about where the flow stopped.
        return {
            "status": "interrupted",
            "hint": (
                "Onboarding interrupted; rerun `hai init --guided` to "
                "resume from the first incomplete step."
            ),
        }

    return result.to_dict()


def _onboarding_default_pull_runner(
    args: argparse.Namespace,
    *,
    db_path: Path,
    user_id: str,
    as_of: date,
    history_days: int,
) -> dict[str, Any]:
    """Production pull runner — calls `_daily_pull_and_project` with
    `--source intervals_icu` semantics."""

    pull_args = argparse.Namespace(
        live=False,
        source="intervals_icu",
        db_path=str(db_path),
        user_id=user_id,
        history_days=history_days,
        _credential_store_override=getattr(
            args, "_credential_store_override", None,
        ),
    )

    from health_agent_infra.cli import _daily_pull_and_project
    try:
        source_name, projected, _ = _daily_pull_and_project(
            pull_args, as_of=as_of, user_id=user_id, db_path=db_path,
        )
    except IntervalsIcuError as exc:
        return {
            "status": "failed",
            "error_class": type(exc).__name__,
            "error": str(exc),
            "hint": (
                "Run `hai doctor --deep` to classify the failure into "
                "one of {OK, CAUSE_1_CLOUDFLARE_UA, CAUSE_2_CREDS, "
                "NETWORK, OTHER}. See "
                "reporting/docs/intervals_icu_403_triage.md."
            ),
        }
    except RuntimeError as exc:
        return {
            "status": "failed",
            "error_class": "RuntimeError",
            "error": str(exc),
        }

    return {
        "status": "ok",
        "source": source_name,
        "for_date": as_of.isoformat(),
        "projected_raw_daily": bool(projected),
        "history_days": history_days,
    }


def _onboarding_default_today_renderer(
    args: argparse.Namespace,
    *,
    db_path: Path,
    user_id: str,
    as_of: date,
) -> dict[str, Any]:
    """Production today-renderer — reads the canonical leaf for the
    target date and reports whether a plan is present + the streak
    state. Does NOT print to stdout (the cmd_init JSON report is the
    single output stream); the user runs `hai today` separately to
    actually see the rendered prose."""

    from health_agent_infra.core.explain import (
        ExplainNotFoundError,
        load_bundle_for_date,
    )
    from health_agent_infra.core.state import open_connection

    conn = open_connection(db_path)
    try:
        try:
            bundle = load_bundle_for_date(
                conn, for_date=as_of, user_id=user_id, plan_version="latest",
            )
        except ExplainNotFoundError:
            return {
                "status": "no_plan_yet",
                "for_date": as_of.isoformat(),
                "hint": (
                    "ask your agent to plan today, or run "
                    "`hai daily` after proposals are posted."
                ),
            }
        try:
            from health_agent_infra.cli.handlers.inspect import _daily_streak_from_events
            streak_days = _daily_streak_from_events(conn)
        except Exception:  # noqa: BLE001
            streak_days = None
    finally:
        conn.close()

    plan_id = (
        bundle.get("daily_plan", {}).get("plan_id")
        if isinstance(bundle, dict)
        else None
    )
    return {
        "status": "plan_ready",
        "for_date": as_of.isoformat(),
        "plan_id": plan_id,
        "streak_days": streak_days,
        "hint": "run `hai today` to read the plan in plain language.",
    }
