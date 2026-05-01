"""Backup / restore / export module (v0.1.14 W-BACKUP).

Three operations:

- :func:`make_backup` — write a versioned tarball containing the
  state DB + JSONL audit logs + capabilities snapshot + version
  stamp.
- :func:`restore_backup` — restore from a tarball; verify migration
  version compatibility; refuse on schema mismatch.
- :func:`export_jsonl` — consolidate existing partial export
  surfaces into a single structured stream.

See ``reporting/docs/recovery.md`` for the recovery contract.
"""

from health_agent_infra.core.backup.bundle import (
    BackupError,
    BackupManifest,
    SchemaMismatchError,
    export_jsonl,
    make_backup,
    read_manifest,
    restore_backup,
)


__all__ = [
    "BackupError",
    "BackupManifest",
    "SchemaMismatchError",
    "export_jsonl",
    "make_backup",
    "read_manifest",
    "restore_backup",
]
