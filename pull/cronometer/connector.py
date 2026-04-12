from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .fetch_exports import ingest_export
from .parse_exports import parse_daily_nutrition_export
from .provenance import build_nutrition_daily, build_provenance_record
from .runtime_state import load_state, save_state
from .source_records import build_source_record
from .sync_window import planned_dates


def _row_hash(row: dict) -> str:
    return hashlib.sha256(json.dumps(row, sort_keys=True).encode("utf-8")).hexdigest()


def run_connector(
    receipt_path: Path,
    state_path: Path,
    output_dir: Path,
    work_dir: Path,
    *,
    account_id: str = "local_cronometer_account",
    stop_after_days: int | None = None,
    resume: bool = False,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    state = load_state(state_path)
    ingested_at = datetime.now(timezone.utc).isoformat()
    batch_dir = work_dir / receipt_path.stem
    receipt = ingest_export(receipt_path, batch_dir)
    parsed = parse_daily_nutrition_export(receipt["receipt_path"], account_id=account_id)
    target_dates = planned_dates(sorted(parsed.rows_by_date), last_successful_day=state.get("last_successful_day"))
    run_id = f"cronometer:{receipt['receipt_hash'][:12]}"
    state.setdefault("slice_status", {}).setdefault(run_id, {})
    processed_dates: list[str] = []

    for day in target_dates:
        row = parsed.rows_by_date[day]
        row_hash = _row_hash(row)
        if resume and state["slice_status"][run_id].get(day) == "completed":
            continue
        if state.get("day_hashes", {}).get(day) == row_hash:
            state["slice_status"][run_id][day] = "completed"
            continue
        state["slice_status"][run_id][day] = "in_progress"
        save_state(state_path, state)
        raw_location = receipt["receipt_path"].as_posix()
        source_record = build_source_record(date=day, raw_location=raw_location, receipt_hash=receipt["receipt_hash"], ingested_at=ingested_at)
        provenance_record = build_provenance_record(source_record_id=source_record["source_record_id"], raw_location=raw_location)
        nutrition_daily = build_nutrition_daily(
            date=day,
            source_record_id=source_record["source_record_id"],
            provenance_record_id=provenance_record["provenance_record_id"],
            row=row,
        )
        day_dir = output_dir / day
        day_dir.mkdir(parents=True, exist_ok=True)
        (day_dir / "source_record.json").write_text(json.dumps(source_record, indent=2), encoding="utf-8")
        (day_dir / "provenance_record.json").write_text(json.dumps(provenance_record, indent=2), encoding="utf-8")
        (day_dir / "nutrition_daily.json").write_text(json.dumps(nutrition_daily, indent=2), encoding="utf-8")
        state.setdefault("day_hashes", {})[day] = row_hash
        state["slice_status"][run_id][day] = "completed"
        processed_dates.append(day)
        save_state(state_path, state)
        if stop_after_days is not None and len(processed_dates) >= stop_after_days:
            state.setdefault("runs", []).append({"run_id": run_id, "status": "interrupted", "receipt_path": raw_location})
            save_state(state_path, state)
            return {
                "run_id": run_id,
                "processed_dates": processed_dates,
                "target_dates": target_dates,
                "interrupted": True,
                "receipt_path": raw_location,
            }

    if target_dates:
        state["last_successful_day"] = max(target_dates)
    state["last_receipt_hash"] = receipt["receipt_hash"]
    state.setdefault("runs", []).append({"run_id": run_id, "status": "completed", "receipt_path": receipt["receipt_path"].as_posix()})
    save_state(state_path, state)
    return {
        "run_id": run_id,
        "processed_dates": processed_dates,
        "target_dates": target_dates,
        "interrupted": False,
        "receipt_path": receipt["receipt_path"].as_posix(),
    }
