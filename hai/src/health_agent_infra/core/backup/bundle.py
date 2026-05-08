"""Backup bundle implementation (v0.1.14 W-BACKUP).

Backup format: gzipped tarball with this layout::

    health-agent-infra-backup-v<schema>-<timestamp>.tar.gz
        ├── manifest.json     (BackupManifest)
        ├── state.db          (SQLite DB file)
        └── jsonl/
            ├── proposal_log.jsonl
            ├── recommendation_log.jsonl
            ├── ... (every JSONL audit log under base_dir)

Restore policy: refuse on schema-version mismatch. The user can
either downgrade the wheel or run ``hai state migrate`` against
the restored DB after upgrading the wheel.
"""

from __future__ import annotations

import json
import sqlite3
import tarfile
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


_MANIFEST_NAME = "manifest.json"
_DB_NAME_IN_BUNDLE = "state.db"
_JSONL_DIR_IN_BUNDLE = "jsonl"


class BackupError(RuntimeError):
    """Raised on a malformed bundle or restore-time invariant failure."""


class SchemaMismatchError(BackupError):
    """Raised when the bundle's schema version does not match the
    installed wheel's head version. The error message names both
    versions and a recovery hint."""


@dataclass(frozen=True)
class BackupManifest:
    """Backup metadata. Stored as ``manifest.json`` in the bundle."""

    bundle_format_version: str
    """Bundle layout version. Bumps when the bundle layout itself
    changes (NOT the SQLite schema). v0.1.14 ships ``"1"``."""

    hai_version: str
    """The ``health-agent-infra`` wheel version that wrote the bundle."""

    schema_version: int
    """The SQLite schema head version when the bundle was written.
    Restore refuses if this doesn't match the installed wheel's head."""

    created_at: str
    """ISO-8601 UTC timestamp."""

    state_db_size_bytes: int
    jsonl_files: list[str]
    """Sorted list of JSONL audit log basenames included in the bundle."""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_backup(
    *,
    state_db_path: Path,
    base_dir: Path,
    dest: Path,
    hai_version: str,
    now: Optional[datetime] = None,
) -> BackupManifest:
    """Write a versioned tarball at ``dest``.

    The tarball contains ``state.db``, every JSONL audit log under
    ``base_dir``, and a ``manifest.json``. ``dest`` is the full
    output path (a ``.tar.gz`` extension is conventional but not
    enforced).
    """

    now = now or datetime.now(timezone.utc)

    if not state_db_path.exists():
        raise BackupError(
            f"state DB does not exist at {state_db_path}; nothing to back up"
        )

    # Read schema version from the DB so the manifest carries it.
    schema_version = _read_schema_head(state_db_path)

    # Discover JSONL files under base_dir. We only include files at
    # the top level + nested under domain-specific folders. We do
    # NOT include arbitrary user files.
    jsonl_basenames: list[str] = []
    if base_dir.exists():
        for entry in sorted(base_dir.iterdir()):
            if entry.is_file() and entry.suffix == ".jsonl":
                jsonl_basenames.append(entry.name)

    manifest = BackupManifest(
        bundle_format_version="1",
        hai_version=hai_version,
        schema_version=schema_version,
        created_at=now.isoformat(),
        state_db_size_bytes=state_db_path.stat().st_size,
        jsonl_files=sorted(jsonl_basenames),
    )

    dest.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(dest, "w:gz") as tf:
        # Manifest (write to a temp file so we can add via path).
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as mfh:
            json.dump(manifest.to_dict(), mfh, indent=2, sort_keys=True)
            mfh_path = Path(mfh.name)
        try:
            tf.add(mfh_path, arcname=_MANIFEST_NAME)
        finally:
            mfh_path.unlink(missing_ok=True)

        # State DB.
        tf.add(state_db_path, arcname=_DB_NAME_IN_BUNDLE)

        # JSONL files.
        for basename in jsonl_basenames:
            src = base_dir / basename
            tf.add(src, arcname=f"{_JSONL_DIR_IN_BUNDLE}/{basename}")

    return manifest


def read_manifest(bundle_path: Path) -> BackupManifest:
    """Read and parse the ``manifest.json`` from a bundle without
    extracting anything else. Used by the CLI to print a summary
    pre-restore.
    """

    with tarfile.open(bundle_path, "r:gz") as tf:
        try:
            member = tf.getmember(_MANIFEST_NAME)
        except KeyError as exc:
            raise BackupError(
                f"bundle {bundle_path.name} missing {_MANIFEST_NAME!r}; "
                f"not a valid health-agent-infra backup"
            ) from exc
        fh = tf.extractfile(member)
        if fh is None:
            raise BackupError(f"could not read {_MANIFEST_NAME} from bundle")
        data = json.loads(fh.read().decode("utf-8"))
    try:
        return BackupManifest(**data)
    except TypeError as exc:
        raise BackupError(f"manifest.json malformed: {exc}") from exc


def restore_backup(
    *,
    bundle_path: Path,
    state_db_path: Path,
    base_dir: Path,
    expected_schema_version: int,
) -> BackupManifest:
    """Restore a bundle into ``state_db_path`` + ``base_dir``.

    Refuses with :class:`SchemaMismatchError` if the bundle's
    schema version doesn't match ``expected_schema_version``.
    Overwrites the existing state DB; the caller is responsible
    for backing up first if the destination is non-empty.
    """

    if not bundle_path.exists():
        raise BackupError(f"bundle does not exist: {bundle_path}")

    manifest = read_manifest(bundle_path)

    if manifest.schema_version != expected_schema_version:
        raise SchemaMismatchError(
            f"bundle schema_version={manifest.schema_version} does not match "
            f"installed wheel head={expected_schema_version}. Restore "
            f"refuses by default. Either install a wheel matching the "
            f"bundle's schema (was hai_version={manifest.hai_version!r}) or "
            f"restore against an empty DB and run `hai state migrate` "
            f"to bring the bundle's data forward."
        )

    # F-IR-04: validate every manifest jsonl_files entry is a plain
    # filename ending in `.jsonl`. The bundle is untrusted input on
    # restore; without this check, a malicious manifest entry like
    # `../outside.jsonl` would write outside base_dir.
    for entry in manifest.jsonl_files:
        if (
            not isinstance(entry, str)
            or entry == ""
            or Path(entry).name != entry
            or not entry.endswith(".jsonl")
        ):
            raise BackupError(
                f"bundle manifest contains an unsafe jsonl_files entry "
                f"{entry!r}. Entries must be plain filenames ending in "
                f"`.jsonl` (no path separators, no `..`, no absolute "
                f"paths). Restore refusing rather than risk writing "
                f"outside base_dir."
            )

    # F-IR-R2-01 + F-IR-R3-01: validate bundle completeness BEFORE
    # any destination mutation, including directory creation. Round-1
    # cleared stale destination logs first, then discovered missing
    # tar members — leaving the destination mutated by a refused
    # restore. Round-2 added an in-memory preflight pass for tar
    # members but still mkdir'd destination parents before that pass;
    # round-3 (F-IR-R3-01) closed the gap. The shape below preflight-
    # reads every required member into memory (state.db + every
    # manifest-listed jsonl), and only performs ANY destination
    # mutation (mkdir, stale clearing, payload writes) once every
    # member is confirmed present and every dest path is safe.

    with tarfile.open(bundle_path, "r:gz") as tf:
        # Preflight 1: state.db must exist and be readable.
        try:
            db_member = tf.getmember(_DB_NAME_IN_BUNDLE)
        except KeyError as exc:
            raise BackupError(
                f"bundle missing {_DB_NAME_IN_BUNDLE!r}; refusing "
                f"before any destination mutation"
            ) from exc
        db_fh = tf.extractfile(db_member)
        if db_fh is None:
            raise BackupError(
                f"could not read {_DB_NAME_IN_BUNDLE} from bundle; "
                f"refusing before any destination mutation"
            )
        db_payload = db_fh.read()

        # Preflight 2: every manifest-listed jsonl member must exist
        # AND be readable. Per maintainer disposition (Codex round-2
        # OQ): manifest entries are the bundle's contract; absence
        # is malformed and refuses the whole restore.
        jsonl_payloads: dict[str, bytes] = {}
        for basename in manifest.jsonl_files:
            arcname = f"{_JSONL_DIR_IN_BUNDLE}/{basename}"
            try:
                jl_member = tf.getmember(arcname)
            except KeyError as exc:
                raise BackupError(
                    f"bundle manifest lists {basename!r} but tar "
                    f"member {arcname!r} is missing; refusing before "
                    f"any destination mutation"
                ) from exc
            jl_fh = tf.extractfile(jl_member)
            if jl_fh is None:
                raise BackupError(
                    f"could not read {arcname!r} from bundle; refusing "
                    f"before any destination mutation"
                )
            jsonl_payloads[basename] = jl_fh.read()

    # Preflight 3: every destination write path stays under base_dir
    # (defence-in-depth alongside the earlier basename validation).
    base_dir_resolved = base_dir.resolve()
    for basename in manifest.jsonl_files:
        dest = (base_dir / basename).resolve()
        try:
            dest.relative_to(base_dir_resolved)
        except ValueError as exc:
            raise BackupError(
                f"bundle restore would write outside base_dir "
                f"({dest} not under {base_dir_resolved}); refusing "
                f"before any destination mutation"
            ) from exc

    # Preflight passed. From here, every write is committed; refusal
    # paths above ensured no destination mutation occurs on
    # malformed bundles. Directory creation moves below the preflight
    # gate per F-IR-R3-01.
    state_db_path.parent.mkdir(parents=True, exist_ok=True)
    base_dir.mkdir(parents=True, exist_ok=True)

    # F-IR-05: clear stale `*.jsonl` files at the destination so
    # restore is a true point-in-time restore. Existing JSONL files
    # not present in the bundle's manifest would otherwise leak
    # between backups (older state.db + newer audit logs is incoherent).
    bundle_logs = set(manifest.jsonl_files)
    for existing in sorted(base_dir.iterdir()):
        if (
            existing.is_file()
            and existing.suffix == ".jsonl"
            and existing.name not in bundle_logs
        ):
            existing.unlink()

    # state.db
    with state_db_path.open("wb") as out:
        out.write(db_payload)

    # JSONL files
    for basename, payload in jsonl_payloads.items():
        dest = base_dir / basename
        with dest.open("wb") as out:
            out.write(payload)

    return manifest


def export_jsonl(
    *,
    base_dir: Path,
    output_stream,
) -> int:
    """Write a unified JSONL stream of every audit log under base_dir.

    Each line carries an envelope ``{"_log": "<basename>", ...payload}``
    so a downstream consumer can demultiplex without needing the
    file boundaries. Returns the count of lines written.
    """

    written = 0
    if not base_dir.exists():
        return 0
    for entry in sorted(base_dir.iterdir()):
        if not (entry.is_file() and entry.suffix == ".jsonl"):
            continue
        with entry.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    # Skip malformed lines rather than fail the whole
                    # export; the audit chain is append-only and a
                    # truncated tail line is plausible.
                    continue
                if not isinstance(obj, dict):
                    continue
                obj_with_log = {"_log": entry.name, **obj}
                output_stream.write(json.dumps(obj_with_log, sort_keys=True) + "\n")
                written += 1
    return written


def _read_schema_head(state_db_path: Path) -> int:
    """Read the ``schema_migrations`` head version from a state DB."""

    conn = sqlite3.connect(state_db_path)
    try:
        cur = conn.execute(
            "SELECT MAX(version) FROM schema_migrations"
        )
        row = cur.fetchone()
        if row is None or row[0] is None:
            raise BackupError(
                f"state DB at {state_db_path} has no schema_migrations rows; "
                f"is it initialised?"
            )
        return int(row[0])
    finally:
        conn.close()
