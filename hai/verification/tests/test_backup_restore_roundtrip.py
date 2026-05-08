"""W-BACKUP roundtrip: state.db + JSONL audit logs survive
backup → wipe → restore with identical content.

v0.1.14 cycle. Schema-mismatch refusal also pinned.
"""

from __future__ import annotations

import io
import json
import sqlite3
from pathlib import Path

import pytest

from health_agent_infra.core.backup import (
    BackupError,
    SchemaMismatchError,
    export_jsonl,
    make_backup,
    read_manifest,
    restore_backup,
)
from health_agent_infra.core.state.store import (
    apply_pending_migrations,
    open_connection,
)


def _seed_state_db_with_one_row(db_path: Path) -> int:
    conn = open_connection(db_path)
    apply_pending_migrations(conn)
    head = conn.execute(
        "SELECT MAX(version) FROM schema_migrations"
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO accepted_recovery_state_daily ("
        "  as_of_date, user_id, resting_hr, hrv_ms, "
        "  acute_load, chronic_load, acwr_ratio, "
        "  training_readiness_component_mean_pct, derived_from, "
        "  source, ingest_actor, projected_at, corrected_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("2026-04-30", "u_local_1", 60.0, 50.0, 100.0, 95.0, 1.05, 0.7,
         "[]", "garmin", "garmin_csv_adapter",
         "2026-04-30T19:26:05.234Z", None),
    )
    conn.commit()
    conn.close()
    return int(head)


def _seed_jsonl(base_dir: Path) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / "recommendation_log.jsonl").write_text(
        json.dumps({"recommendation_id": "rec_1", "for_date": "2026-04-30"})
        + "\n",
        encoding="utf-8",
    )
    (base_dir / "review_outcomes.jsonl").write_text(
        json.dumps({"review_event_id": "rev_1", "outcome": "ok"}) + "\n",
        encoding="utf-8",
    )


def _read_recovery_row_count(db_path: Path) -> int:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM accepted_recovery_state_daily"
        ).fetchone()[0]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Backup-side
# ---------------------------------------------------------------------------

def test_make_backup_writes_tarball_with_manifest(tmp_path):
    state_db = tmp_path / "state.db"
    head = _seed_state_db_with_one_row(state_db)
    base_dir = tmp_path / "audit"
    _seed_jsonl(base_dir)

    dest = tmp_path / "out.tar.gz"
    manifest = make_backup(
        state_db_path=state_db,
        base_dir=base_dir,
        dest=dest,
        hai_version="0.1.14-test",
    )
    assert dest.exists()
    assert manifest.schema_version == head
    assert manifest.bundle_format_version == "1"
    assert manifest.hai_version == "0.1.14-test"
    assert "recommendation_log.jsonl" in manifest.jsonl_files
    assert "review_outcomes.jsonl" in manifest.jsonl_files


def test_make_backup_refuses_when_state_db_missing(tmp_path):
    with pytest.raises(BackupError, match="does not exist"):
        make_backup(
            state_db_path=tmp_path / "nope.db",
            base_dir=tmp_path / "audit",
            dest=tmp_path / "out.tar.gz",
            hai_version="0.1.14-test",
        )


def test_read_manifest_roundtrips_metadata(tmp_path):
    state_db = tmp_path / "state.db"
    _seed_state_db_with_one_row(state_db)
    base_dir = tmp_path / "audit"
    _seed_jsonl(base_dir)

    dest = tmp_path / "out.tar.gz"
    written = make_backup(
        state_db_path=state_db,
        base_dir=base_dir,
        dest=dest,
        hai_version="0.1.14-test",
    )
    read = read_manifest(dest)
    assert read.to_dict() == written.to_dict()


# ---------------------------------------------------------------------------
# Restore-side
# ---------------------------------------------------------------------------

def test_restore_roundtrip_state_db_and_jsonl(tmp_path):
    # Source side
    src_db = tmp_path / "src" / "state.db"
    src_db.parent.mkdir(parents=True, exist_ok=True)
    head = _seed_state_db_with_one_row(src_db)
    src_audit = tmp_path / "src" / "audit"
    _seed_jsonl(src_audit)

    bundle = tmp_path / "bundle.tar.gz"
    make_backup(
        state_db_path=src_db,
        base_dir=src_audit,
        dest=bundle,
        hai_version="0.1.14-test",
    )

    # Destination side (empty)
    dst_db = tmp_path / "dst" / "state.db"
    dst_audit = tmp_path / "dst" / "audit"

    restore_backup(
        bundle_path=bundle,
        state_db_path=dst_db,
        base_dir=dst_audit,
        expected_schema_version=head,
    )

    assert dst_db.exists()
    assert _read_recovery_row_count(dst_db) == 1
    assert (dst_audit / "recommendation_log.jsonl").exists()
    assert (dst_audit / "review_outcomes.jsonl").exists()
    rec_line = (dst_audit / "recommendation_log.jsonl").read_text(
        encoding="utf-8"
    ).strip()
    assert json.loads(rec_line)["recommendation_id"] == "rec_1"


def test_restore_refuses_on_schema_mismatch(tmp_path):
    src_db = tmp_path / "src" / "state.db"
    src_db.parent.mkdir(parents=True, exist_ok=True)
    head = _seed_state_db_with_one_row(src_db)
    src_audit = tmp_path / "src" / "audit"
    _seed_jsonl(src_audit)

    bundle = tmp_path / "bundle.tar.gz"
    make_backup(
        state_db_path=src_db,
        base_dir=src_audit,
        dest=bundle,
        hai_version="0.1.14-test",
    )

    # Pretend the wheel's head is one ahead of the bundle's.
    with pytest.raises(SchemaMismatchError) as exc_info:
        restore_backup(
            bundle_path=bundle,
            state_db_path=tmp_path / "dst.db",
            base_dir=tmp_path / "dst-audit",
            expected_schema_version=head + 1,
        )
    msg = str(exc_info.value)
    assert "schema_version" in msg
    assert str(head) in msg


def test_restore_refuses_on_missing_bundle(tmp_path):
    with pytest.raises(BackupError, match="does not exist"):
        restore_backup(
            bundle_path=tmp_path / "nope.tar.gz",
            state_db_path=tmp_path / "dst.db",
            base_dir=tmp_path / "dst-audit",
            expected_schema_version=1,
        )


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def test_export_jsonl_writes_unified_stream(tmp_path):
    base_dir = tmp_path / "audit"
    _seed_jsonl(base_dir)

    out = io.StringIO()
    count = export_jsonl(base_dir=base_dir, output_stream=out)

    assert count == 2
    lines = [json.loads(line) for line in out.getvalue().splitlines() if line]
    log_names = {line["_log"] for line in lines}
    assert log_names == {
        "recommendation_log.jsonl",
        "review_outcomes.jsonl",
    }


def test_export_jsonl_skips_malformed_lines(tmp_path):
    base_dir = tmp_path / "audit"
    base_dir.mkdir(parents=True)
    (base_dir / "log.jsonl").write_text(
        '{"a": 1}\nnot json at all\n{"b": 2}\n', encoding="utf-8"
    )

    out = io.StringIO()
    count = export_jsonl(base_dir=base_dir, output_stream=out)
    assert count == 2  # 2 valid lines; 1 malformed dropped


# ---------------------------------------------------------------------------
# F-IR-04: malicious-bundle path-traversal refusal
# ---------------------------------------------------------------------------

def _build_malicious_bundle(tmp_path, jsonl_entry: str):
    """Build a bundle whose manifest declares an unsafe jsonl_files entry.

    Used to verify ``restore_backup`` refuses traversal attempts.
    """

    import tarfile
    import tempfile

    src_db = tmp_path / "src" / "state.db"
    src_db.parent.mkdir(parents=True, exist_ok=True)
    head = _seed_state_db_with_one_row(src_db)
    src_audit = tmp_path / "src" / "audit"
    src_audit.mkdir(parents=True, exist_ok=True)

    bundle = tmp_path / "malicious.tar.gz"
    bad_manifest = {
        "bundle_format_version": "1",
        "hai_version": "0.1.14-malicious",
        "schema_version": head,
        "created_at": "2026-05-01T00:00:00+00:00",
        "state_db_size_bytes": src_db.stat().st_size,
        "jsonl_files": [jsonl_entry],
    }
    with tarfile.open(bundle, "w:gz") as tf:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as mfh:
            json.dump(bad_manifest, mfh, sort_keys=True)
            mfh_path = Path(mfh.name)
        try:
            tf.add(mfh_path, arcname="manifest.json")
        finally:
            mfh_path.unlink(missing_ok=True)
        tf.add(src_db, arcname="state.db")
    return bundle, head


def test_restore_refuses_jsonl_entry_with_path_traversal(tmp_path):
    bundle, head = _build_malicious_bundle(tmp_path, "../outside.jsonl")
    with pytest.raises(BackupError, match="unsafe jsonl_files"):
        restore_backup(
            bundle_path=bundle,
            state_db_path=tmp_path / "dst" / "state.db",
            base_dir=tmp_path / "dst" / "audit",
            expected_schema_version=head,
        )


def test_restore_refuses_jsonl_entry_with_absolute_path(tmp_path):
    bundle, head = _build_malicious_bundle(tmp_path, "/etc/evil.jsonl")
    with pytest.raises(BackupError, match="unsafe jsonl_files"):
        restore_backup(
            bundle_path=bundle,
            state_db_path=tmp_path / "dst" / "state.db",
            base_dir=tmp_path / "dst" / "audit",
            expected_schema_version=head,
        )


def test_restore_refuses_jsonl_entry_with_separator(tmp_path):
    bundle, head = _build_malicious_bundle(tmp_path, "nested/log.jsonl")
    with pytest.raises(BackupError, match="unsafe jsonl_files"):
        restore_backup(
            bundle_path=bundle,
            state_db_path=tmp_path / "dst" / "state.db",
            base_dir=tmp_path / "dst" / "audit",
            expected_schema_version=head,
        )


def test_restore_refuses_jsonl_entry_without_jsonl_extension(tmp_path):
    bundle, head = _build_malicious_bundle(tmp_path, "credentials.txt")
    with pytest.raises(BackupError, match="unsafe jsonl_files"):
        restore_backup(
            bundle_path=bundle,
            state_db_path=tmp_path / "dst" / "state.db",
            base_dir=tmp_path / "dst" / "audit",
            expected_schema_version=head,
        )


# ---------------------------------------------------------------------------
# F-IR-05: stale-extra-log clearing for point-in-time restore
# ---------------------------------------------------------------------------

def _build_bundle_missing_member(tmp_path, *, drop_db: bool, drop_jsonl: bool):
    """Build a bundle whose tar is missing required members but whose
    manifest still references them. Used for F-IR-R2-01 preflight tests.
    """

    import tarfile
    import tempfile

    src_db = tmp_path / "src" / "state.db"
    src_db.parent.mkdir(parents=True, exist_ok=True)
    head = _seed_state_db_with_one_row(src_db)
    src_audit = tmp_path / "src" / "audit"
    _seed_jsonl(src_audit)

    bundle = tmp_path / "incomplete.tar.gz"
    manifest = {
        "bundle_format_version": "1",
        "hai_version": "0.1.14-incomplete",
        "schema_version": head,
        "created_at": "2026-05-01T00:00:00+00:00",
        "state_db_size_bytes": src_db.stat().st_size,
        "jsonl_files": ["recommendation_log.jsonl", "review_outcomes.jsonl"],
    }
    with tarfile.open(bundle, "w:gz") as tf:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as mfh:
            json.dump(manifest, mfh, sort_keys=True)
            mfh_path = Path(mfh.name)
        try:
            tf.add(mfh_path, arcname="manifest.json")
        finally:
            mfh_path.unlink(missing_ok=True)
        if not drop_db:
            tf.add(src_db, arcname="state.db")
        if not drop_jsonl:
            for log in src_audit.glob("*.jsonl"):
                tf.add(log, arcname=f"jsonl/{log.name}")
        else:
            # Drop only review_outcomes.jsonl so the manifest-vs-tar
            # mismatch is one specific listed log.
            tf.add(
                src_audit / "recommendation_log.jsonl",
                arcname="jsonl/recommendation_log.jsonl",
            )
    return bundle, head


def test_restore_refuses_malformed_bundle_without_creating_destination_dirs(tmp_path):
    """F-IR-R3-01: a refused restore must not create destination
    directories. Tightens the no-destination-mutation contract from
    'no data mutation' (round 2) to literal 'no mutation, including
    mkdir'."""

    bundle, head = _build_bundle_missing_member(
        tmp_path, drop_db=True, drop_jsonl=False,
    )
    # Deliberately do NOT pre-create dst dirs.
    dst_db = tmp_path / "fresh_dst" / "state.db"
    dst_audit = tmp_path / "fresh_dst" / "audit"
    assert not dst_db.parent.exists()
    assert not dst_audit.exists()

    with pytest.raises(BackupError, match="state.db"):
        restore_backup(
            bundle_path=bundle,
            state_db_path=dst_db,
            base_dir=dst_audit,
            expected_schema_version=head,
        )

    # Literal "no destination mutation": parent dirs were never created.
    assert not dst_db.parent.exists(), (
        "F-IR-R3-01: state_db_path.parent was created before bundle "
        "preflight refused"
    )
    assert not dst_audit.exists(), (
        "F-IR-R3-01: base_dir was created before bundle preflight refused"
    )


def test_restore_refuses_missing_state_db_without_mutating_destination(tmp_path):
    """F-IR-R2-01: a bundle missing state.db must not delete stale
    destination logs before refusing."""

    bundle, head = _build_bundle_missing_member(
        tmp_path, drop_db=True, drop_jsonl=False,
    )
    dst_db = tmp_path / "dst" / "state.db"
    dst_audit = tmp_path / "dst" / "audit"
    dst_audit.mkdir(parents=True, exist_ok=True)
    stale = dst_audit / "stale.jsonl"
    stale.write_text(
        json.dumps({"stale": True}) + "\n", encoding="utf-8"
    )

    with pytest.raises(BackupError, match="state.db"):
        restore_backup(
            bundle_path=bundle,
            state_db_path=dst_db,
            base_dir=dst_audit,
            expected_schema_version=head,
        )

    # Destination unmutated.
    assert stale.exists(), (
        "F-IR-R2-01: stale destination log was deleted before restore "
        "verified bundle completeness"
    )
    assert not dst_db.exists()


def test_restore_refuses_manifest_listed_jsonl_missing_from_tar(tmp_path):
    """F-IR-R2-01: a manifest-listed JSONL member that is absent from
    the tar must refuse before mutation; the same-named stale log at
    the destination must not be left in place."""

    bundle, head = _build_bundle_missing_member(
        tmp_path, drop_db=False, drop_jsonl=True,
    )
    dst_db = tmp_path / "dst" / "state.db"
    dst_audit = tmp_path / "dst" / "audit"
    dst_audit.mkdir(parents=True, exist_ok=True)
    # Pre-populate the SAME-NAMED stale log at destination — pre-fix
    # this would have been left in place because it's in the manifest's
    # bundle_logs set so the stale-clearing loop skipped it.
    stale_same_name = dst_audit / "review_outcomes.jsonl"
    stale_same_name.write_text(
        json.dumps({"old_run": True}) + "\n", encoding="utf-8"
    )

    with pytest.raises(BackupError, match="review_outcomes.jsonl"):
        restore_backup(
            bundle_path=bundle,
            state_db_path=dst_db,
            base_dir=dst_audit,
            expected_schema_version=head,
        )

    # Destination unmutated.
    assert not dst_db.exists()
    # Stale same-name still has its old content (refusal happened
    # before any mutation).
    contents = json.loads(stale_same_name.read_text(encoding="utf-8").strip())
    assert contents == {"old_run": True}, (
        "F-IR-R2-01: same-named stale log was modified despite "
        "refused restore"
    )


def test_restore_clears_stale_jsonl_files_not_in_bundle(tmp_path):
    """Restore is a point-in-time operation. Stale audit logs at the
    destination that are not present in the bundle's manifest must be
    removed; otherwise an older state.db + newer JSONL leftovers
    silently mix two timelines."""

    src_db = tmp_path / "src" / "state.db"
    src_db.parent.mkdir(parents=True, exist_ok=True)
    head = _seed_state_db_with_one_row(src_db)
    src_audit = tmp_path / "src" / "audit"
    _seed_jsonl(src_audit)  # writes recommendation_log.jsonl + review_outcomes.jsonl

    bundle = tmp_path / "bundle.tar.gz"
    make_backup(
        state_db_path=src_db,
        base_dir=src_audit,
        dest=bundle,
        hai_version="0.1.14-test",
    )

    dst_db = tmp_path / "dst" / "state.db"
    dst_audit = tmp_path / "dst" / "audit"
    dst_audit.mkdir(parents=True, exist_ok=True)
    # Pre-populate destination with a NEWER stale log not in the bundle.
    stale = dst_audit / "stale_extra.jsonl"
    stale.write_text(
        json.dumps({"stale": True}) + "\n", encoding="utf-8"
    )
    # Also place a non-jsonl file that should NOT be cleared.
    keepsake = dst_audit / "config.toml"
    keepsake.write_text("# keep me\n", encoding="utf-8")

    restore_backup(
        bundle_path=bundle,
        state_db_path=dst_db,
        base_dir=dst_audit,
        expected_schema_version=head,
    )

    # Bundle's logs are present.
    assert (dst_audit / "recommendation_log.jsonl").exists()
    assert (dst_audit / "review_outcomes.jsonl").exists()
    # Stale jsonl is gone.
    assert not stale.exists()
    # Non-jsonl is untouched.
    assert keepsake.exists()
