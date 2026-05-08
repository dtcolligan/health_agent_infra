"""Free-text context note intake — typed parsing + JSONL audit append.

Notes are append-only and have no chain semantics. Each invocation
creates a new note_id; multiple notes per day are independent rows.
There is no "accepted" projection — context_note IS the canonical state
(notes are free-text by nature, no aggregate to derive).

Design echo: state_model_v1.md §1 lists context_note as raw evidence
(user-reported), no accepted layer above it. Snapshot's `notes.recent`
reads context_note directly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional


CONTEXT_NOTES_JSONL = "context_notes.jsonl"


@dataclass
class ContextNote:
    """One free-text user note. Append-only — no corrections in v1."""

    note_id: str
    user_id: str
    as_of_date: date
    recorded_at: datetime
    text: str
    tags: Optional[list[str]]
    ingest_actor: str

    def to_jsonl_line(self) -> dict:
        return {
            "note_id": self.note_id,
            "user_id": self.user_id,
            "as_of_date": self.as_of_date.isoformat(),
            "recorded_at": self.recorded_at.isoformat(),
            "text": self.text,
            "tags": list(self.tags) if self.tags else None,
            "source": "user_manual",
            "ingest_actor": self.ingest_actor,
        }


def append_note_jsonl(note: ContextNote, *, base_dir: Path) -> Path:
    from health_agent_infra.core.privacy import secure_directory, secure_file

    secure_directory(base_dir, create=True)
    path = base_dir / CONTEXT_NOTES_JSONL
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(note.to_jsonl_line(), sort_keys=True) + "\n")
    secure_file(path)
    return path
