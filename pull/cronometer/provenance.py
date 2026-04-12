from __future__ import annotations

import hashlib


def build_provenance_record(*, source_record_id: str, raw_location: str) -> dict:
    token = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()[:16]
    return {
        "artifact_family": "provenance_record",
        "provenance_record_id": f"provenance_nutrition_daily_{token}",
        "source_record_id": source_record_id,
        "derivation_method": "food_import_normalization",
        "supporting_refs": [raw_location, f"{raw_location}#daily-nutrition"],
        "parser_version": "cronometer-export-daily-nutrition-v1",
        "conflict_status": "none",
    }


def build_nutrition_daily(*, date: str, source_record_id: str, provenance_record_id: str, row: dict) -> dict:
    token = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()[:16]
    return {
        "artifact_family": "nutrition_daily",
        "date": date,
        "nutrition_daily_id": f"nutrition_daily_{token}",
        "source_name": "cronometer",
        "source_record_id": source_record_id,
        "provenance_record_id": provenance_record_id,
        "conflict_status": "none",
        **row,
    }
