"""Manual readiness intake — typed parsing + JSONL audit append.

Per D2 (``reporting/plans/v0_1_4/D2_intake_write_paths.md``), every
``hai intake <X>`` must persist to state. Pre-v0.1.4, readiness was the
one exception — it emitted JSON to stdout for agent composition with
``hai pull --manual-readiness-json`` but never wrote to the DB. That
caused the 2026-04-23 footgun where a user ran ``hai intake readiness``
and reasonably expected the classifier to pick up the new signal on the
next ``hai pull``, and it didn't.

This module mirrors :mod:`health_agent_infra.domains.stress.intake` —
same JSONL-rooted chain-resolution pattern so DB-absent writes still
build correct correction chains.

    hai intake readiness → readiness_manual.jsonl (audit)
                        → manual_readiness_raw (state)
                        → hai pull auto-read on same-day
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional


READINESS_MANUAL_JSONL = "readiness_manual.jsonl"


@dataclass
class ReadinessSubmission:
    """One manual readiness submission.

    The fields mirror the ``manual_readiness_raw`` columns (migration
    015) plus the ``active_goal`` free-text carry-through. Soreness and
    energy are banded low/moderate/high; ``planned_session_type`` is
    free-text (e.g. ``easy``, ``intervals_4x4_z4_z2``, ``rest``).
    """

    submission_id: str
    user_id: str
    as_of_date: date
    soreness: str
    energy: str
    planned_session_type: str
    active_goal: Optional[str]
    ingest_actor: str
    submitted_at: datetime
    supersedes_submission_id: Optional[str] = None

    def to_jsonl_line(self) -> dict:
        return {
            "submission_id": self.submission_id,
            "user_id": self.user_id,
            "as_of_date": self.as_of_date.isoformat(),
            "soreness": self.soreness,
            "energy": self.energy,
            "planned_session_type": self.planned_session_type,
            "active_goal": self.active_goal,
            "source": "user_manual",
            "ingest_actor": self.ingest_actor,
            "submitted_at": self.submitted_at.isoformat(),
            "supersedes_submission_id": self.supersedes_submission_id,
        }

    def to_pull_payload(self) -> dict:
        """Return the shape ``hai pull`` emits under ``manual_readiness``.

        Matches the schema ``--manual-readiness-json`` consumes today
        (``recovery_prep.py`` reads ``soreness`` / ``energy`` /
        ``planned_session_type`` / ``submission_id`` / ``active_goal``).
        Keeps auto-read output byte-compatible with the file-flag path.
        """

        payload = {
            "submission_id": self.submission_id,
            "soreness": self.soreness,
            "energy": self.energy,
            "planned_session_type": self.planned_session_type,
        }
        if self.active_goal:
            payload["active_goal"] = self.active_goal
        return payload


def append_submission_jsonl(
    submission: ReadinessSubmission,
    *,
    base_dir: Path,
) -> Path:
    from health_agent_infra.core.privacy import secure_directory, secure_file

    secure_directory(base_dir, create=True)
    path = base_dir / READINESS_MANUAL_JSONL
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
    """JSONL-rooted chain resolver — same pattern as stress/nutrition.

    Reads the durable audit log to find the tail-of-chain submission_id
    for ``(as_of_date, user_id)``. Independent of DB state, so DB-absent
    writes still build correct correction chains.
    """

    path = base_dir / READINESS_MANUAL_JSONL
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
        prior = data.get("supersedes_submission_id")
        if prior:
            superseded_ids.add(prior)
        if data.get("as_of_date") == iso and data.get("user_id") == user_id:
            sub_id = data.get("submission_id")
            if sub_id:
                candidate_ids.append(sub_id)

    for sub_id in reversed(candidate_ids):
        if sub_id not in superseded_ids:
            return sub_id
    return None
