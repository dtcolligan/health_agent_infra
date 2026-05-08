from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


PARSER_VERSION = "garmin-export-runtime-hardening-v1"


@dataclass(frozen=True)
class SliceKey:
    family: str
    key: str

    @property
    def id(self) -> str:
        return f"{self.family}:{self.key}"


@dataclass(frozen=True)
class FileManifestEntry:
    name: str
    path: str
    sha256: str
    rows: int
    coverage: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BatchManifest:
    batch_id: str
    receipt_type: str
    receipt_path: str
    receipt_sha256: str
    parser_version: str
    files: list[FileManifestEntry]


@dataclass(frozen=True)
class ConnectorPaths:
    state_path: Path
    output_dir: Path
    work_dir: Path
