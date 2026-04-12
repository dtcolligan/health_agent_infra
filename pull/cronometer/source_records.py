from __future__ import annotations


def build_source_record(*, date: str, raw_location: str, receipt_hash: str, ingested_at: str) -> dict:
    return {
        "artifact_family": "source_record",
        "source_record_id": f"nutrition:cronometer:day:{date}",
        "source_name": "cronometer",
        "source_type": "imported_food_pipeline",
        "entry_lane": "pull",
        "raw_location": raw_location,
        "raw_format": "csv",
        "effective_date": date,
        "collected_at": None,
        "ingested_at": ingested_at,
        "hash_or_version": receipt_hash[:16],
        "native_record_type": "daily-nutrition",
        "native_record_id": date,
    }
