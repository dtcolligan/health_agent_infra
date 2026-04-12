from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


def ingest_export(receipt_path: Path, batch_dir: Path) -> dict:
    batch_dir.mkdir(parents=True, exist_ok=True)
    receipt_copy = batch_dir / receipt_path.name
    shutil.copy2(receipt_path, receipt_copy)
    return {
        "receipt_path": receipt_copy,
        "raw_format": receipt_path.suffix.lstrip(".") or "csv",
        "receipt_hash": hashlib.sha256(receipt_copy.read_bytes()).hexdigest(),
    }
