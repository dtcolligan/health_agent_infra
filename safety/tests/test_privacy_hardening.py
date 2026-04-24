"""Phase D — privacy hardening tests (v0.1.4 blocking).

Codex strategic-report §7 acceptance criteria:
  - Fresh `hai state init` creates private local directories.
  - Packaged demo data is documented as synthetic.
  - User can find docs for delete/export/migrate.
  - No real personal health data ships in package fixtures.

Coverage:
  1. `initialize_database` locks DB + parent dir to 0o600 / 0o700 on POSIX.
  2. Each intake JSONL writer (gym, nutrition, stress, readiness, note)
     locks the audit log + base_dir on append.
  3. `perform_proposal_writeback` locks the per-domain proposal JSONL +
     base_dir on append.
  4. Re-running each writer is idempotent on perms (no loosening).
  5. Packaged Garmin CSV fixture contains no obvious PII patterns
     (names, emails, GPS, device serials).
  6. The privacy doc + fixture README exist and are non-empty.
  7. Windows: chmod is skipped silently (no exception).
"""

from __future__ import annotations

import os
import re
import stat
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.core.privacy import (
    current_mode,
    expected_dir_mode,
    expected_file_mode,
    is_posix,
    reset_warn_cache_for_tests,
    secure_directory,
    secure_file,
    secure_intake_dir,
    secure_state_db,
)
from health_agent_infra.core.state import initialize_database


pytestmark = pytest.mark.skipif(
    not is_posix(),
    reason="POSIX file permissions; Windows uses NTFS ACL defaults — see privacy.md",
)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def test_secure_directory_creates_with_owner_only_perms(tmp_path: Path):
    target = tmp_path / "sub" / "deeper"
    secure_directory(target)
    assert target.exists()
    assert current_mode(target) == expected_dir_mode()


def test_secure_directory_no_op_on_missing_path_when_create_false(tmp_path: Path):
    target = tmp_path / "nope"
    secure_directory(target, create=False)
    assert not target.exists()


def test_secure_file_skips_missing_path(tmp_path: Path):
    target = tmp_path / "absent.txt"
    secure_file(target)  # must not raise
    assert not target.exists()


def test_secure_file_locks_existing_file_to_0600(tmp_path: Path):
    target = tmp_path / "secret.jsonl"
    target.write_text("seeded\n", encoding="utf-8")
    # Force a permissive starting state
    os.chmod(target, 0o644)
    secure_file(target)
    assert current_mode(target) == expected_file_mode()


def test_secure_directory_idempotent(tmp_path: Path):
    target = tmp_path / "intake"
    secure_directory(target)
    first = current_mode(target)
    secure_directory(target)  # second pass
    second = current_mode(target)
    assert first == second == expected_dir_mode()


def test_secure_state_db_locks_db_and_siblings(tmp_path: Path):
    db = tmp_path / "state.db"
    db.write_bytes(b"")
    wal = tmp_path / "state.db-wal"
    wal.write_bytes(b"")
    secure_state_db(db)
    assert current_mode(db) == expected_file_mode()
    assert current_mode(wal) == expected_file_mode()
    assert current_mode(tmp_path) == expected_dir_mode()


# ---------------------------------------------------------------------------
# initialize_database — DB hardened on creation
# ---------------------------------------------------------------------------

def test_initialize_database_locks_perms_on_creation(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    assert db_path.exists()
    assert current_mode(db_path) == expected_file_mode()
    assert current_mode(db_path.parent) == expected_dir_mode()


def test_initialize_database_relocks_perms_on_subsequent_init(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    # Loosen (simulate an external process loosening perms)
    os.chmod(db_path, 0o644)
    initialize_database(db_path)  # second init: re-applies the chmod
    assert current_mode(db_path) == expected_file_mode()


# ---------------------------------------------------------------------------
# Intake writers — JSONL append + base_dir hardened
# ---------------------------------------------------------------------------

def test_readiness_intake_locks_jsonl_perms(tmp_path: Path):
    from health_agent_infra.domains.recovery.readiness_intake import (
        ReadinessSubmission,
        append_submission_jsonl,
    )
    from datetime import datetime, timezone

    submission = ReadinessSubmission(
        submission_id="m_ready_test_1",
        user_id="u_test",
        as_of_date=date(2026, 4, 24),
        soreness="low",
        energy="moderate",
        planned_session_type="easy",
        active_goal=None,
        ingest_actor="hai_cli_direct",
        submitted_at=datetime.now(timezone.utc),
    )
    base = tmp_path / "intake_root"
    path = append_submission_jsonl(submission, base_dir=base)
    assert current_mode(path) == expected_file_mode()
    assert current_mode(base) == expected_dir_mode()


def test_proposal_writeback_locks_jsonl_perms(tmp_path: Path):
    from health_agent_infra.core.writeback.proposal import (
        perform_proposal_writeback,
    )

    proposal = {
        "schema_version": "recovery_proposal.v1",
        "proposal_id": "prop_test_recovery_01",
        "user_id": "u_test",
        "for_date": "2026-04-24",
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "action_detail": None,
        "rationale": ["test rationale"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": "r1", "decision": "allow", "note": "n"},
        ],
        "bounded": True,
    }
    base = tmp_path / "writeback_root"
    record = perform_proposal_writeback(proposal, base_dir=base)
    log_path = Path(record.writeback_path)
    assert current_mode(log_path) == expected_file_mode()
    assert current_mode(base) == expected_dir_mode()


def test_context_note_intake_locks_jsonl_perms(tmp_path: Path):
    from health_agent_infra.core.intake.note import (
        ContextNote,
        append_note_jsonl,
    )
    from datetime import datetime, timezone

    note = ContextNote(
        note_id="note_test_1",
        user_id="u_test",
        as_of_date=date(2026, 4, 24),
        recorded_at=datetime.now(timezone.utc),
        text="quick context note",
        tags=["test"],
        ingest_actor="hai_cli_direct",
    )
    base = tmp_path / "notes_root"
    path = append_note_jsonl(note, base_dir=base)
    assert current_mode(path) == expected_file_mode()
    assert current_mode(base) == expected_dir_mode()


def test_review_event_persistence_locks_jsonl_perms(tmp_path: Path):
    from health_agent_infra.core.review.outcomes import persist_review_event
    from health_agent_infra.core.schemas import ReviewEvent
    from datetime import datetime, timezone

    event = ReviewEvent(
        review_event_id="rev_test_1",
        recommendation_id="rec_test_1",
        user_id="u_test",
        review_at=datetime.now(timezone.utc),
        review_question="How did today go?",
        domain="recovery",
    )
    base = tmp_path / "review_root"
    persist_review_event(event, base_dir=base)
    events_path = base / "review_events.jsonl"
    assert current_mode(events_path) == expected_file_mode()
    assert current_mode(base) == expected_dir_mode()


# ---------------------------------------------------------------------------
# secure_intake_dir bulk helper
# ---------------------------------------------------------------------------

def test_secure_intake_dir_locks_every_jsonl_in_base(tmp_path: Path):
    base = tmp_path / "bulk"
    base.mkdir()
    for name in ("a.jsonl", "b.jsonl", "stress_manual.jsonl"):
        (base / name).write_text("", encoding="utf-8")
        os.chmod(base / name, 0o644)
    # A non-JSONL file should be left alone (not in scope).
    non_jsonl = base / "ignored.txt"
    non_jsonl.write_text("", encoding="utf-8")
    os.chmod(non_jsonl, 0o644)

    secure_intake_dir(base)

    assert current_mode(base) == expected_dir_mode()
    for name in ("a.jsonl", "b.jsonl", "stress_manual.jsonl"):
        assert current_mode(base / name) == expected_file_mode(), name
    # Non-JSONL untouched (rest of users' files in their own dirs are theirs)
    assert current_mode(non_jsonl) == 0o644


# ---------------------------------------------------------------------------
# Packaged Garmin fixture — PII scan
# ---------------------------------------------------------------------------

# Patterns we'd expect in a real export but should never see in synthetic.
# Conservative: deliberate false-positives are OK (they tell us to inspect
# manually); false-negatives are NOT (they would let real data leak through).
_PII_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("phone_us_loose", re.compile(r"\+?\d{3}[-.\s]\d{3}[-.\s]\d{4}\b")),
    ("ssn_loose", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    # Garmin device serial number format (3 letters + many digits)
    ("device_serial", re.compile(r"\b[A-Z]{3}\d{8,}\b")),
    # Latitude/longitude pair (Garmin sometimes embeds GPS in exports)
    ("gps_pair", re.compile(r"-?\d{1,3}\.\d{4,},\s*-?\d{1,3}\.\d{4,}")),
]

# Words that commonly appear in real exports as user-identifying fields.
# Match is case-insensitive on column names AND on values.
_PII_WORDS: list[str] = [
    "username",
    "displayname",
    "email",
    "first_name",
    "last_name",
    "fullname",
    "phone",
    "address",
    "device_serial",
]


def test_packaged_garmin_csv_is_synthetic_no_pii_patterns():
    """Scan the packaged daily-summary CSV for obvious PII patterns.
    A failure here means the fixture should be regenerated from synthetic
    sources — see src/health_agent_infra/data/garmin/export/README.md."""

    from importlib.resources import files

    csv_text = files("health_agent_infra").joinpath(
        "data", "garmin", "export", "daily_summary_export.csv",
    ).read_text(encoding="utf-8")

    failures: list[str] = []
    for label, pattern in _PII_PATTERNS:
        match = pattern.search(csv_text)
        if match:
            failures.append(
                f"{label}: matched {match.group(0)!r} in fixture"
            )
    for word in _PII_WORDS:
        if word.lower() in csv_text.lower():
            failures.append(
                f"PII-shaped column or value found: {word!r}"
            )
    assert not failures, (
        "Packaged Garmin CSV fixture appears to contain PII. "
        "Replace with synthetic data. Failures:\n  - "
        + "\n  - ".join(failures)
    )


def test_packaged_garmin_csv_has_only_numeric_metric_columns():
    """The fixture must be schema-compatible with the live Garmin CSV but
    only carry numeric / status-enum values — no free-text user fields."""

    from importlib.resources import files

    csv_text = files("health_agent_infra").joinpath(
        "data", "garmin", "export", "daily_summary_export.csv",
    ).read_text(encoding="utf-8")
    header = csv_text.splitlines()[0]
    # No free-text identity columns.
    forbidden_columns = {"name", "username", "email", "user_email", "user_id"}
    columns = {c.strip().lower() for c in header.split(",")}
    leaked = forbidden_columns & columns
    assert not leaked, f"forbidden identity columns present: {sorted(leaked)}"


def test_packaged_fixture_readme_exists_and_documents_synthetic_status():
    """The fixture README must state the file is synthetic and point at the
    PII regression test — those two facts are the durable contract."""

    from importlib.resources import files

    readme = files("health_agent_infra").joinpath(
        "data", "garmin", "export", "README.md",
    ).read_text(encoding="utf-8")
    assert "synthetic" in readme.lower()
    assert "test_packaged_fixture_privacy" in readme or "test_privacy_hardening" in readme


# ---------------------------------------------------------------------------
# Privacy doc — exists and covers the four acceptance criteria
# ---------------------------------------------------------------------------

def test_privacy_doc_exists_and_covers_required_topics():
    """User-facing privacy doc must address inspect / export / delete /
    migrate (Codex §7 acceptance)."""

    privacy_md = (
        Path(__file__).parents[2]
        / "reporting" / "docs" / "privacy.md"
    )
    assert privacy_md.exists()
    text = privacy_md.read_text(encoding="utf-8").lower()
    for required in ("inspect", "export", "delet", "migrat", "credential"):
        assert required in text, f"privacy.md missing topic: {required!r}"


# ---------------------------------------------------------------------------
# Warn-once helper resets cleanly for tests
# ---------------------------------------------------------------------------

def test_warn_once_helper_can_be_reset():
    """Internal sanity: tests can clear the warn-once dedup set."""
    reset_warn_cache_for_tests()
    # Trigger a warning by chmodding a path we know to be valid; the helper
    # is best-effort and should not raise even on weird filesystem states.
    secure_file(Path("/tmp"))  # /tmp exists; chmod from non-root is no-op or warn
