"""Nutrition intake — typed parsing + JSONL audit append.

One CLI invocation → one ``NutritionSubmission`` → one JSONL line →
one append-only row in ``nutrition_intake_raw`` + one UPSERT into
``accepted_nutrition_state_daily``.

**Corrections.** Nutrition is a daily aggregate ("I ate X calories
today"). Re-running ``hai intake nutrition`` with a different value for
the same ``(as_of_date, user_id)`` is treated as a **correction**, not a
second meal. The CLI auto-detects the prior raw row and stamps
``supersedes_submission_id`` on the new one, preserving the correction
chain per state_model_v1.md §3. The ``accepted_nutrition_state_daily``
row UPSERTs with ``corrected_at`` set.

**JSONL audit boundary.** ``<base_dir>/nutrition_intake.jsonl`` is the
durable record. Written BEFORE any DB operation so a later DB failure
is recoverable via ``hai state reproject --base-dir``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional


NUTRITION_INTAKE_JSONL = "nutrition_intake.jsonl"


@dataclass
class NutritionSubmission:
    """One nutrition intake submission (header + aggregate macros).

    Raw evidence. The accepted canonical state is derived from this row
    via ``project_accepted_nutrition_state_daily``.
    """

    submission_id: str
    user_id: str
    as_of_date: date
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    hydration_l: Optional[float]
    meals_count: Optional[int]
    ingest_actor: str
    submitted_at: datetime
    supersedes_submission_id: Optional[str] = None

    def to_jsonl_line(self) -> dict:
        return {
            "submission_id": self.submission_id,
            "user_id": self.user_id,
            "as_of_date": self.as_of_date.isoformat(),
            "calories": self.calories,
            "protein_g": self.protein_g,
            "carbs_g": self.carbs_g,
            "fat_g": self.fat_g,
            "hydration_l": self.hydration_l,
            "meals_count": self.meals_count,
            "source": "user_manual",
            "ingest_actor": self.ingest_actor,
            "submitted_at": self.submitted_at.isoformat(),
            "supersedes_submission_id": self.supersedes_submission_id,
        }


def append_submission_jsonl(
    submission: NutritionSubmission,
    *,
    base_dir: Path,
) -> Path:
    """Append one line to ``<base_dir>/nutrition_intake.jsonl``.

    This is the durable audit boundary: happens BEFORE any DB projection
    so a later DB failure is recoverable via reproject.
    """

    from health_agent_infra.core.privacy import secure_directory, secure_file

    secure_directory(base_dir, create=True)
    path = base_dir / NUTRITION_INTAKE_JSONL
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(submission.to_jsonl_line(), sort_keys=True) + "\n")
    secure_file(path)
    return path


def latest_submission_id_from_jsonl(
    base_dir: Path,
    *,
    as_of_date: date,
    user_id: str,
) -> Optional[str]:
    """Return the tail-of-chain submission_id from the JSONL, or None.

    The JSONL is the durable source of truth for correction chains
    (state_model_v1.md §3). Resolving from JSONL — not the DB — means a
    DB-absent write still computes a correct ``supersedes_submission_id``,
    so the append-only chain is never broken by a missing queryable view.

    Scan: collect every submission for ``(as_of_date, user_id)``; track
    which ones are superseded (i.e., mentioned as another line's
    ``supersedes_submission_id``); return the latest non-superseded one
    (by file order — line order matches chronological insert order, since
    appends are chronological).
    """

    path = base_dir / NUTRITION_INTAKE_JSONL
    if not path.exists():
        return None

    candidate_ids: list[str] = []
    superseded_ids: set[str] = set()
    iso = as_of_date.isoformat()

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Track supersedes links across ALL lines (even for other days /
        # users) — a malformed log that points a correction across keys
        # is unusual but we respect it for consistency with the DB view.
        prior = data.get("supersedes_submission_id")
        if prior:
            superseded_ids.add(prior)
        # Candidate pool is scoped to the (day, user) we're resolving for.
        if data.get("as_of_date") == iso and data.get("user_id") == user_id:
            sub_id = data.get("submission_id")
            if sub_id:
                candidate_ids.append(sub_id)

    for sub_id in reversed(candidate_ids):
        if sub_id not in superseded_ids:
            return sub_id
    return None
