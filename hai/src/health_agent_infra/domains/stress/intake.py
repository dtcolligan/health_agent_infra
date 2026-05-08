"""Manual subjective stress intake — typed parsing + JSONL audit append.

Closes the provenance loop deferred in the 7A.3 patch. ``hai clean``
no longer accepts ``manual_stress_score`` as a direct argument
(state_model_v1.md §3 violation: a user-reported fact must land in raw
evidence first). 7C.3 wires the proper path:

    hai intake stress → JSONL audit → stress_manual_raw (raw)
                                   → accepted_recovery_state_daily.manual_stress_score (merge)

Re-running for the same ``(as_of_date, user_id)`` is a **correction**:
new submission supersedes the prior tail; the accepted recovery row
UPSERTs ``manual_stress_score`` and ``corrected_at``.

Chain resolution reads from the JSONL (the durable boundary) — same
discipline as nutrition (7C.2 patch). DB-absent writes still produce
correct correction chains.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional


STRESS_MANUAL_JSONL = "stress_manual.jsonl"


@dataclass
class StressSubmission:
    """One subjective stress submission (1–5 score + optional tags)."""

    submission_id: str
    user_id: str
    as_of_date: date
    score: int
    tags: Optional[list[str]]
    ingest_actor: str
    submitted_at: datetime
    supersedes_submission_id: Optional[str] = None

    def to_jsonl_line(self) -> dict:
        return {
            "submission_id": self.submission_id,
            "user_id": self.user_id,
            "as_of_date": self.as_of_date.isoformat(),
            "score": self.score,
            "tags": list(self.tags) if self.tags else None,
            "source": "user_manual",
            "ingest_actor": self.ingest_actor,
            "submitted_at": self.submitted_at.isoformat(),
            "supersedes_submission_id": self.supersedes_submission_id,
        }


def append_submission_jsonl(
    submission: StressSubmission,
    *,
    base_dir: Path,
) -> Path:
    from health_agent_infra.core.privacy import secure_directory, secure_file

    secure_directory(base_dir, create=True)
    path = base_dir / STRESS_MANUAL_JSONL
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
    """JSONL-rooted chain resolver — same pattern as nutrition (7C.2 patch).

    Reads the durable audit log to find the tail-of-chain submission_id
    for ``(as_of_date, user_id)``. Independent of DB state, so DB-absent
    writes still build correct correction chains.
    """

    path = base_dir / STRESS_MANUAL_JSONL
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
