"""Strength intake surfaces — gym sessions + user taxonomy extension.

Two input shapes land at the same typed ``GymSessionSubmission``:

  - Per-set CLI flags: ``hai intake gym --session-id ... --exercise ...
    --set-number ... --weight-kg ... --reps ...`` — one set per invocation.
  - Bulk JSON: ``hai intake gym --session-json <path>`` — whole session at
    once, with a ``sets`` array.

The JSONL audit log at ``<base_dir>/gym_sessions.jsonl`` is the durable
source of truth for gym intake; the DB is a queryable projection
(``gym_session`` + ``gym_set`` + ``accepted_resistance_training_state_daily``)
that ``hai state reproject --base-dir`` can rebuild at any time from the
JSONL (per state_model_v1.md §2 + §3).

Each JSONL line captures one set submission with its session metadata
inline (session_id, session_name, as_of_date, etc.). Session attributes
are duplicated across every line for the session — that's fine for an
append-only log, and it makes reproject a straightforward line-by-line
replay.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from health_agent_infra.domains.strength.signals import MUSCLE_GROUPS


GYM_SESSIONS_JSONL = "gym_sessions.jsonl"


@dataclass
class GymSet:
    """One set within a gym session — raw evidence."""

    set_number: int
    exercise_name: str
    weight_kg: Optional[float]
    reps: Optional[int]
    rpe: Optional[float] = None
    supersedes_set_id: Optional[str] = None


@dataclass
class GymSessionSubmission:
    """One submission of a gym session (header + sets).

    A single invocation of ``hai intake gym`` produces exactly one of these.
    Per-set mode produces a submission with a single-element ``sets`` list;
    bulk mode produces one with many.
    """

    session_id: str
    user_id: str
    as_of_date: date
    session_name: Optional[str]
    notes: Optional[str]
    sets: list[GymSet]
    submission_id: str
    ingest_actor: str
    submitted_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_jsonl_lines(self) -> list[dict]:
        """One dict per set, session metadata inline on each."""

        return [
            {
                "submission_id": self.submission_id,
                "session_id": self.session_id,
                "user_id": self.user_id,
                "as_of_date": self.as_of_date.isoformat(),
                "session_name": self.session_name,
                "notes": self.notes,
                "set_number": s.set_number,
                "exercise_name": s.exercise_name,
                "weight_kg": s.weight_kg,
                "reps": s.reps,
                "rpe": s.rpe,
                "supersedes_set_id": s.supersedes_set_id,
                "source": "user_manual",
                "ingest_actor": self.ingest_actor,
                "submitted_at": self.submitted_at.isoformat(),
            }
            for s in self.sets
        ]


def deterministic_set_id(session_id: str, set_number: int) -> str:
    """Idempotent set_id: same (session_id, set_number) ⇒ same set_id.

    Re-running ``hai intake gym`` with identical args hits the PK and becomes
    a no-op. Corrections must pass an explicit ``--supersedes-set-id`` plus a
    new set_id via bulk JSON (7C.1 doesn't expose per-set correction flags
    on the CLI; that lands later if the flow hits friction).
    """

    return f"set_{session_id}_{set_number:03d}"


def parse_bulk_session_json(payload: dict) -> dict:
    """Light validation of the bulk ``--session-json`` payload shape.

    Returns the normalised dict. Raises ``ValueError`` on missing required
    keys or malformed sets. Caller wraps into ``GymSessionSubmission``.
    """

    required = {"session_id", "sets"}
    missing = required - payload.keys()
    if missing:
        raise ValueError(
            f"--session-json missing required keys: {sorted(missing)}"
        )
    sets = payload["sets"]
    if not isinstance(sets, list):
        raise ValueError("--session-json 'sets' must be a list")
    if not sets:
        raise ValueError("--session-json 'sets' must not be empty")
    for idx, s in enumerate(sets):
        if not isinstance(s, dict):
            raise ValueError(f"sets[{idx}] must be an object")
        for k in ("set_number", "exercise_name"):
            if k not in s:
                raise ValueError(f"sets[{idx}] missing required key: {k!r}")
        if not isinstance(s["set_number"], int):
            raise ValueError(f"sets[{idx}].set_number must be an integer")
        if not isinstance(s["exercise_name"], str) or not s["exercise_name"].strip():
            raise ValueError(f"sets[{idx}].exercise_name must be a non-empty string")
    return payload


def append_submission_jsonl(
    submission: GymSessionSubmission,
    *,
    base_dir: Path,
) -> Path:
    """Append one line per set to ``<base_dir>/gym_sessions.jsonl``.

    The JSONL is the durable audit boundary: this write happens BEFORE any
    DB projection so a later DB failure is recoverable via
    ``hai state reproject --base-dir``.
    """

    from health_agent_infra.core.privacy import secure_directory, secure_file

    secure_directory(base_dir, create=True)
    path = base_dir / GYM_SESSIONS_JSONL
    with path.open("a", encoding="utf-8") as fh:
        for line in submission.to_jsonl_lines():
            fh.write(json.dumps(line, sort_keys=True) + "\n")
    secure_file(path)
    return path


# ---------------------------------------------------------------------------
# User-defined exercise taxonomy intake
# ---------------------------------------------------------------------------


def normalize_exercise_id(value: str) -> str:
    """Return a stable snake_case taxonomy id from free text.

    ``hai intake exercise`` accepts an optional explicit ``--exercise-id``.
    When omitted, we derive one deterministically from the canonical name so
    re-running the same command is idempotent.
    """

    norm = re.sub(r"[^a-z0-9]+", "_", value.strip().casefold()).strip("_")
    if not norm:
        raise ValueError("exercise_id/name must contain at least one letter or digit")
    return norm


def _norm_token(value: str) -> str:
    return value.strip().casefold()


def _split_multi(value: Optional[str]) -> tuple[str, ...]:
    if value is None or not value.strip():
        return ()
    parts = re.split(r"[|,]", value)
    out: list[str] = []
    seen: set[str] = set()
    for raw in parts:
        token = raw.strip()
        if not token:
            continue
        key = _norm_token(token)
        if key in seen:
            continue
        seen.add(key)
        out.append(token)
    return tuple(out)


def _join_pipe(values: tuple[str, ...]) -> Optional[str]:
    return "|".join(values) if values else None


def build_manual_taxonomy_row(
    *,
    canonical_name: str,
    primary_muscle_group: str,
    category: str,
    equipment: str,
    exercise_id: Optional[str] = None,
    aliases: Optional[str] = None,
    secondary_muscle_groups: Optional[str] = None,
) -> dict[str, Optional[str]]:
    """Normalise `hai intake exercise` flags into one taxonomy row dict."""

    canonical = canonical_name.strip()
    if not canonical:
        raise ValueError("--name must be a non-empty string")
    primary = primary_muscle_group.strip()
    if not primary:
        raise ValueError("--primary-muscle-group must be a non-empty string")
    if primary not in MUSCLE_GROUPS:
        raise ValueError(
            "--primary-muscle-group must be one of: "
            + ", ".join(MUSCLE_GROUPS)
        )

    eid = normalize_exercise_id(exercise_id if exercise_id else canonical)

    alias_values = tuple(
        token for token in _split_multi(aliases)
        if _norm_token(token) != _norm_token(canonical)
    )
    secondary_values = _split_multi(secondary_muscle_groups)
    unknown_secondary = [g for g in secondary_values if g not in MUSCLE_GROUPS]
    if unknown_secondary:
        raise ValueError(
            "--secondary-muscle-groups contains unknown values: "
            + ", ".join(unknown_secondary)
        )

    return {
        "exercise_id": eid,
        "canonical_name": canonical,
        "aliases": _join_pipe(alias_values),
        "primary_muscle_group": primary,
        "secondary_muscle_groups": _join_pipe(secondary_values),
        "category": category,
        "equipment": equipment,
        "source": "user_manual",
    }
