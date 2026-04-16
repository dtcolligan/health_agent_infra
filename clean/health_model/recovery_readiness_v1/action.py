"""ACTION layer.

Performs the bounded local writeback for a TrainingRecommendation.
Per policy rule R6 (writeback_locality), this only appends to local
recommendation-log JSONL files. No external writes. Idempotent on
recommendation_id.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from health_model.recovery_readiness_v1.schemas import (
    PolicyDecision,
    TrainingRecommendation,
)


@dataclass
class ActionRecord:
    recommendation_id: str
    writeback_path: str
    plan_note_path: str
    idempotency_key: str
    performed_at: datetime
    policy_decisions: list[PolicyDecision]

    def to_dict(self) -> dict:
        return {
            "recommendation_id": self.recommendation_id,
            "writeback_path": self.writeback_path,
            "plan_note_path": self.plan_note_path,
            "idempotency_key": self.idempotency_key,
            "performed_at": self.performed_at.isoformat(),
            "policy_decisions": [
                {"rule_id": d.rule_id, "decision": d.decision, "note": d.note}
                for d in self.policy_decisions
            ],
        }


ALLOWED_RELATIVE_ROOT = "recovery_readiness_v1"


def perform_writeback(
    recommendation: TrainingRecommendation,
    *,
    base_dir: Path,
    now: Optional[datetime] = None,
) -> ActionRecord:
    """Append the recommendation to a local log and daily plan note.

    Raises ValueError if `base_dir` resolves outside the allowed relative root,
    enforcing policy rule R6 (writeback_locality) at the I/O boundary.
    """

    now = now or datetime.now(timezone.utc)
    base_dir = base_dir.resolve()
    if ALLOWED_RELATIVE_ROOT not in base_dir.parts:
        raise ValueError(
            f"writeback base_dir {base_dir} is outside the allowed "
            f"local writeback root '.../{ALLOWED_RELATIVE_ROOT}/...'"
        )

    log_path = base_dir / "recommendation_log.jsonl"
    plan_note_path = base_dir / f"daily_plan_{recommendation.for_date.isoformat()}.md"

    base_dir.mkdir(parents=True, exist_ok=True)

    if not _already_written(log_path, recommendation.recommendation_id):
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(recommendation.to_dict(), sort_keys=True) + "\n")

    _append_plan_note(plan_note_path, recommendation, now)

    return ActionRecord(
        recommendation_id=recommendation.recommendation_id,
        writeback_path=str(log_path),
        plan_note_path=str(plan_note_path),
        idempotency_key=recommendation.recommendation_id,
        performed_at=now,
        policy_decisions=list(recommendation.policy_decisions),
    )


def _already_written(log_path: Path, recommendation_id: str) -> bool:
    if not log_path.exists():
        return False
    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("recommendation_id") == recommendation_id:
                return True
    return False


def _append_plan_note(path: Path, rec: TrainingRecommendation, now: datetime) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    marker = f"<!-- {rec.recommendation_id} -->"
    if marker in existing:
        return
    detail_str = json.dumps(rec.action_detail, sort_keys=True) if rec.action_detail else ""
    entry = [
        f"{marker}",
        f"## {rec.for_date.isoformat()} — {rec.action}",
        "",
        f"- confidence: {rec.confidence}",
        f"- rationale: {', '.join(rec.rationale)}",
        f"- uncertainty: {', '.join(rec.uncertainty) if rec.uncertainty else '(none)'}",
    ]
    if detail_str:
        entry.append(f"- detail: `{detail_str}`")
    entry.append(f"- review_at: {rec.follow_up.review_at.isoformat()}")
    entry.append(f"- issued_at: {now.isoformat()}")
    entry.append("")
    with path.open("a", encoding="utf-8") as fh:
        if existing and not existing.endswith("\n"):
            fh.write("\n")
        fh.write("\n".join(entry) + "\n")
