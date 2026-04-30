"""W-AA (v0.1.13) — `hai init --guided` orchestrator.

See `core/init/__init__.py` for the high-level contract. This module
defines:

- `PromptInterface` — abstract input source. Production uses
  `StdinPrompts`; tests use `ScriptedPrompts` with a queue of
  pre-canned responses.
- `OnboardingResult` — dataclass returned by `run_guided_onboarding`.
- `run_guided_onboarding(...)` — the orchestrator. Wires the four
  guided steps (auth, intent+target, first pull, surface today) on top
  of an already-initialised state DB (steps 1-3 in `cmd_init` ran
  before this is called).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional, Protocol


class PromptInterface(Protocol):
    """Abstract input source so tests don't have to monkeypatch
    `builtins.input` / `getpass.getpass` globally."""

    def ask(self, prompt: str) -> Optional[str]:
        """Return the user's response, or ``None`` when the user
        skipped (empty input or EOF)."""

    def ask_secret(self, prompt: str) -> Optional[str]:
        """Same as `ask`, but the input is not echoed (e.g. an API
        key). Return ``None`` on skip / EOF."""


class StdinPrompts:
    """Production prompt source — reads from real stdin / getpass.
    Writes prompts to ``sys.stderr`` (the same convention the existing
    ``_run_interactive_auth`` uses) so the JSON report on stdout stays
    a single document."""

    def __init__(self, *, stderr_writer: Optional[Callable[[str], None]] = None) -> None:
        import sys
        self._write = stderr_writer or (lambda s: (sys.stderr.write(s), sys.stderr.flush()))

    def ask(self, prompt: str) -> Optional[str]:
        self._write(prompt)
        try:
            answer = input()
        except EOFError:
            return None
        answer = answer.strip()
        return answer if answer else None

    def ask_secret(self, prompt: str) -> Optional[str]:
        import getpass
        try:
            answer = getpass.getpass(prompt)
        except EOFError:
            return None
        answer = answer.strip()
        return answer if answer else None


@dataclass
class ScriptedPrompts:
    """Test prompt source — pops responses off a FIFO list. Use
    ``None`` for an explicit skip; use a string for an answer. Raises
    ``IndexError`` if the orchestrator asks for more inputs than the
    test scripted, which is how a test fails when the prompt sequence
    drifts."""

    responses: list[Optional[str]] = field(default_factory=list)
    asked: list[str] = field(default_factory=list)

    def ask(self, prompt: str) -> Optional[str]:
        self.asked.append(prompt)
        return self.responses.pop(0)

    def ask_secret(self, prompt: str) -> Optional[str]:
        self.asked.append(prompt)
        return self.responses.pop(0)


# ---------------------------------------------------------------------------
# Result shape — one row per step, mirroring the existing init JSON report
# ---------------------------------------------------------------------------


@dataclass
class OnboardingResult:
    """Per-step outcome dict + a final overall status. The shape
    matches the existing `cmd_init` report so the CLI can splice this
    in under `report["steps"]["guided"]` without reshaping callers."""

    auth_intervals_icu: dict[str, Any] = field(default_factory=dict)
    intent_target: dict[str, Any] = field(default_factory=dict)
    first_pull: dict[str, Any] = field(default_factory=dict)
    surface_today: dict[str, Any] = field(default_factory=dict)
    overall_status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return {
            "auth_intervals_icu": self.auth_intervals_icu,
            "intent_target": self.intent_target,
            "first_pull": self.first_pull,
            "surface_today": self.surface_today,
            "overall_status": self.overall_status,
        }


# ---------------------------------------------------------------------------
# Helpers — kept tiny and pure so the orchestrator below reads as a
# step-by-step sequence rather than a cascade of conditionals.
# ---------------------------------------------------------------------------


def _parse_positive_number(raw: str) -> Optional[float]:
    """Parse a free-text numeric prompt response. Returns ``None``
    when the value is empty, malformed, or non-positive — the caller
    treats that as 'skip this prompt'."""

    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value


def _has_active_intent_for_user(conn: sqlite3.Connection, *, user_id: str) -> bool:
    """Idempotency check for step 5. If the user already has any
    `active` intent row, skip the intent prompt — the user already
    authored their training plan in a previous session."""

    row = conn.execute(
        "SELECT 1 FROM intent_item WHERE user_id = ? AND status = 'active' LIMIT 1",
        (user_id,),
    ).fetchone()
    return row is not None


def _has_active_target_for_user(conn: sqlite3.Connection, *, user_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM target WHERE user_id = ? AND status = 'active' LIMIT 1",
        (user_id,),
    ).fetchone()
    return row is not None


def _has_pull_for_today(
    conn: sqlite3.Connection, *, user_id: str, as_of: date,
) -> bool:
    """Idempotency check for step 6 — does ``sync_run_log`` already
    record a successful pull for the user + date? `sync_run_log` is
    the canonical provenance surface (M2); a successful row there
    means the source-side adapter ran and projection succeeded."""

    row = conn.execute(
        "SELECT 1 FROM sync_run_log "
        "WHERE user_id = ? AND for_date = ? AND status = 'ok' LIMIT 1",
        (user_id, as_of.isoformat()),
    ).fetchone()
    return row is not None


# ---------------------------------------------------------------------------
# Step 4 — intervals.icu credential prompt
# ---------------------------------------------------------------------------


def _step_auth_intervals_icu(
    *,
    prompts: PromptInterface,
    credential_store: Any,
) -> dict[str, Any]:
    """Prompt for athlete id + API key and store via the credential
    store. Skip if credentials are already present."""

    existing = credential_store.load_intervals_icu()
    if existing is not None:
        return {"status": "already_configured"}

    athlete_id = prompts.ask(
        "Intervals.icu athlete id (e.g. i123456) [press Enter to skip]: "
    )
    if not athlete_id:
        return {
            "status": "user_skipped",
            "reason": "no athlete id provided",
            "hint": (
                "run `hai auth intervals-icu` later to add credentials, "
                "or set HAI_INTERVALS_ATHLETE_ID + HAI_INTERVALS_API_KEY"
            ),
        }
    api_key = prompts.ask_secret("Intervals.icu API key: ")
    if not api_key:
        return {
            "status": "user_skipped",
            "reason": "no API key provided",
            "hint": "run `hai auth intervals-icu` later to add credentials",
        }

    try:
        credential_store.store_intervals_icu(athlete_id, api_key)
    except Exception as exc:  # KeyringUnavailableError, ValueError, etc.
        return {
            "status": "failed",
            "error_class": type(exc).__name__,
            "error": str(exc),
            "hint": "set HAI_INTERVALS_ATHLETE_ID + HAI_INTERVALS_API_KEY env vars",
        }

    return {"status": "configured", "athlete_id": athlete_id}


# ---------------------------------------------------------------------------
# Step 5 — initial intent + target authoring
# ---------------------------------------------------------------------------


_FOCUS_DOMAIN = {
    "running": "running",
    "run": "running",
    "strength": "strength",
    "lifting": "strength",
    "mixed": "running",  # mixed athletes default to running session-shape
    "both": "running",
}


def _step_intent_target(
    *,
    conn: sqlite3.Connection,
    prompts: PromptInterface,
    user_id: str,
    as_of: date,
) -> dict[str, Any]:
    """Prompt for primary training focus + daily kcal/protein/sleep
    targets; persist the rows directly via ``add_intent`` /
    ``add_target``. Skip if active rows already exist."""

    from health_agent_infra.core.intent import add_intent
    from health_agent_infra.core.target import add_target

    intent_present = _has_active_intent_for_user(conn, user_id=user_id)
    target_present = _has_active_target_for_user(conn, user_id=user_id)

    if intent_present and target_present:
        return {
            "status": "already_present",
            "hint": "active intent + target rows already exist for this user",
        }

    authored: dict[str, Any] = {"intent_ids": [], "target_ids": []}

    # Intent — primary training focus. One row, scope=day, type=training_session
    # for runners or strength athletes.
    if not intent_present:
        focus_raw = prompts.ask(
            "Primary training focus today (running / strength / mixed) "
            "[Enter to skip]: "
        )
        focus_key = (focus_raw or "").strip().lower()
        domain = _FOCUS_DOMAIN.get(focus_key)
        if domain is not None:
            intent_record = add_intent(
                conn,
                user_id=user_id,
                domain=domain,
                intent_type="training_session",
                scope_start=as_of,
                scope_type="day",
                status="active",
                priority="normal",
                flexibility="flexible",
                payload={"focus": focus_key},
                reason=f"hai init --guided onboarding (focus={focus_key})",
                source="user_authored",
                ingest_actor="cli",
            )
            authored["intent_ids"].append(intent_record.intent_id)
            authored["intent_focus"] = focus_key
        else:
            authored["intent_skipped"] = True

    # Targets — daily kcal + protein + sleep duration. Each independent;
    # the user can skip any of them.
    if not target_present:
        kcal_raw = prompts.ask(
            "Daily calorie target in kcal (e.g. 2400) [Enter to skip]: "
        )
        kcal = _parse_positive_number(kcal_raw or "")
        if kcal is not None:
            kcal_record = add_target(
                conn,
                user_id=user_id,
                domain="nutrition",
                target_type="calories_kcal",
                value=int(round(kcal)),
                unit="kcal",
                effective_from=as_of,
                status="active",
                reason="hai init --guided onboarding",
                source="user_authored",
                ingest_actor="cli",
            )
            authored["target_ids"].append(kcal_record.target_id)

        protein_raw = prompts.ask(
            "Daily protein target in grams (e.g. 140) [Enter to skip]: "
        )
        protein = _parse_positive_number(protein_raw or "")
        if protein is not None:
            protein_record = add_target(
                conn,
                user_id=user_id,
                domain="nutrition",
                target_type="protein_g",
                value=int(round(protein)),
                unit="g",
                effective_from=as_of,
                status="active",
                reason="hai init --guided onboarding",
                source="user_authored",
                ingest_actor="cli",
            )
            authored["target_ids"].append(protein_record.target_id)

        sleep_raw = prompts.ask(
            "Sleep duration target in hours (e.g. 8) [Enter to skip]: "
        )
        sleep_h = _parse_positive_number(sleep_raw or "")
        if sleep_h is not None:
            sleep_record = add_target(
                conn,
                user_id=user_id,
                domain="sleep",
                target_type="sleep_duration_h",
                value=float(sleep_h),
                unit="h",
                effective_from=as_of,
                status="active",
                reason="hai init --guided onboarding",
                source="user_authored",
                ingest_actor="cli",
            )
            authored["target_ids"].append(sleep_record.target_id)

    if not authored["intent_ids"] and not authored["target_ids"]:
        return {
            "status": "user_skipped",
            "reason": "no intent or target prompts answered",
            "hint": (
                "run `hai intent training add-session` and `hai target set` "
                "later to author your training plan"
            ),
            **authored,
        }

    return {"status": "authored", **authored}


# ---------------------------------------------------------------------------
# Step 6 — first wellness pull via intervals.icu
# ---------------------------------------------------------------------------


def _step_first_pull(
    *,
    db_path: Path,
    user_id: str,
    as_of: date,
    history_days: int,
    pull_runner: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """Run the first wellness pull. Idempotent on (user_id, as_of_date).

    The orchestrator does NOT build the adapter itself — that's
    threaded in via ``pull_runner`` so the CLI handler can supply the
    real intervals.icu adapter while tests inject a stubbed one
    (typically ``ReplayWellnessClient``)."""

    return pull_runner(
        db_path=db_path,
        user_id=user_id,
        as_of=as_of,
        history_days=history_days,
    )


# ---------------------------------------------------------------------------
# Step 7 — surface `hai today` cold-start prose
# ---------------------------------------------------------------------------


def _step_surface_today(
    *,
    db_path: Path,
    user_id: str,
    as_of: date,
    today_renderer: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """Render `hai today` and capture the rendered prose in the
    onboarding report. The actual writing-to-stdout happens upstream
    in ``cmd_init``; this step just records what the user will see."""

    return today_renderer(db_path=db_path, user_id=user_id, as_of=as_of)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_guided_onboarding(
    *,
    db_path: Path,
    user_id: str,
    as_of: Optional[date] = None,
    history_days: int = 1,
    prompts: PromptInterface,
    credential_store: Any,
    pull_runner: Callable[..., dict[str, Any]],
    today_renderer: Callable[..., dict[str, Any]],
    skip_pull: bool = False,
    skip_today: bool = False,
) -> OnboardingResult:
    """Run guided onboarding steps 4-7 over an already-initialised
    state DB.

    The caller (``cmd_init``) is responsible for steps 1-3 (thresholds,
    state DB + migrations, skills copy) before invoking this. ``db_path``
    must already point at a head-of-migrations SQLite DB.

    Each step is idempotent. ``KeyboardInterrupt`` mid-step is allowed
    to propagate — the caller catches it and emits a partial report;
    re-running ``hai init --guided`` reaches the first incomplete step.
    """

    from health_agent_infra.core.state import open_connection

    today = as_of or datetime.now(timezone.utc).date()
    result = OnboardingResult()

    # Step 4 — auth (no DB connection needed; credential store owns its own).
    result.auth_intervals_icu = _step_auth_intervals_icu(
        prompts=prompts, credential_store=credential_store,
    )

    # Step 5 — intent + target authoring (DB connection scoped to step).
    conn = open_connection(db_path)
    try:
        result.intent_target = _step_intent_target(
            conn=conn, prompts=prompts, user_id=user_id, as_of=today,
        )
    finally:
        conn.close()

    # Step 6 — first pull (skippable via flag — used when creds were skipped
    # in step 4 so we don't call the live API with no auth).
    creds_present = result.auth_intervals_icu.get("status") in (
        "configured", "already_configured",
    )
    if skip_pull or not creds_present:
        result.first_pull = {
            "status": "skipped",
            "reason": (
                "skip_pull flag set"
                if skip_pull
                else "no intervals.icu credentials available"
            ),
        }
    else:
        # Idempotency — skip if today's row is already projected.
        conn = open_connection(db_path)
        try:
            already_pulled = _has_pull_for_today(
                conn, user_id=user_id, as_of=today,
            )
        finally:
            conn.close()
        if already_pulled:
            result.first_pull = {
                "status": "already_present",
                "for_date": today.isoformat(),
            }
        else:
            result.first_pull = _step_first_pull(
                db_path=db_path,
                user_id=user_id,
                as_of=today,
                history_days=history_days,
                pull_runner=pull_runner,
            )

    # Step 7 — surface today.
    if skip_today:
        result.surface_today = {"status": "skipped", "reason": "skip_today flag set"}
    else:
        result.surface_today = _step_surface_today(
            db_path=db_path,
            user_id=user_id,
            as_of=today,
            today_renderer=today_renderer,
        )

    # Overall status — `ok` if every step is ok / already / configured / skipped
    # by user; `partial` if any step explicitly failed.
    statuses = [
        result.auth_intervals_icu.get("status", ""),
        result.intent_target.get("status", ""),
        result.first_pull.get("status", ""),
        result.surface_today.get("status", ""),
    ]
    if any(s == "failed" for s in statuses):
        result.overall_status = "partial"
    elif any(s == "user_skipped" for s in statuses):
        result.overall_status = "ok_with_skips"
    else:
        result.overall_status = "ok"

    return result
