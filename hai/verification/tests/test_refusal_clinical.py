"""WP-REFUSE-001: clinical-claim refusal lives in runtime code."""

from __future__ import annotations

import io
import json
import sqlite3
from contextlib import closing, redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.hermetic import (
    HAI_BASE_DIR_ENV,
    HAI_HERMETIC_ENV,
    HAI_STATE_DB_ENV,
)
from health_agent_infra.core.refusal import (
    BANNED_CLINICAL_PHRASES,
    ClinicalRefusalError,
    enforce_clinical_output,
    evaluate_clinical_output,
    scan_clinical_phrases,
)
from health_agent_infra.core.runtime_mode import (
    HAI_RUNTIME_MODE_ENV,
    NO_REFUSAL,
)
from health_agent_infra.core.schemas import canonical_daily_plan_id
from health_agent_infra.core.state import initialize_database


def test_clinical_phrase_resource_covers_existing_boundary_terms() -> None:
    assert "diagnosis" in BANNED_CLINICAL_PHRASES
    assert "medical advice" in BANNED_CLINICAL_PHRASES
    assert "treatment" in BANNED_CLINICAL_PHRASES


def test_scan_clinical_phrases_is_whole_phrase_and_case_insensitive() -> None:
    matches = scan_clinical_phrases(
        "Conditional training is fine.\nSeek MEDICAL   ADVICE today."
    )

    assert [m.phrase for m in matches] == ["medical advice"]
    assert matches[0].line_no == 2
    assert matches[0].column == 6


def test_full_contract_refuses_clinical_output_with_envelope() -> None:
    with pytest.raises(ClinicalRefusalError) as exc_info:
        enforce_clinical_output(
            "Today looks like an infection pattern.",
            output_path="unit-test-output",
        )

    envelope = exc_info.value.envelope
    assert envelope["schema_version"] == "refusal_envelope.v1"
    assert envelope["step_type"] == "refusal"
    assert envelope["refusal_kind"] == "clinical_claim"
    assert envelope["mechanism"] == "refusal"
    assert envelope["output_path"] == "unit-test-output"
    assert envelope["details"]["matches"][0]["phrase"] == "infection"


def test_no_refusal_mode_allows_output_with_disabled_marker() -> None:
    decision = evaluate_clinical_output(
        "This mentions medical advice.",
        output_path="unit-test-output",
        env={HAI_RUNTIME_MODE_ENV: NO_REFUSAL},
    )

    assert decision.allowed is True
    assert decision.mechanism_disabled_marker is not None
    marker = decision.mechanism_disabled_marker
    assert marker["schema_version"] == "mechanism_disabled_marker.v1"
    assert marker["step_type"] == "mechanism_disabled"
    assert marker["mechanism"] == "refusal"
    assert marker["runtime_mode"] == NO_REFUSAL
    assert marker["details"]["matches"][0]["phrase"] == "medical advice"


def _seed_today_plan_with_rationale(
    db: Path,
    *,
    user: str,
    as_of: date,
    rationale: str,
) -> None:
    plan_id = canonical_daily_plan_id(as_of, user)
    rec_id = f"rec_{as_of.isoformat()}_{user}_recovery_01"
    payload = {
        "recommendation_id": rec_id,
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "confidence": "moderate",
        "rationale": [rationale],
        "uncertainty": [],
        "follow_up": {
            "review_question": "How did today's recovery plan land?",
        },
    }
    with closing(sqlite3.connect(db)) as conn:
        conn.execute(
            """
            INSERT INTO daily_plan (
                daily_plan_id, user_id, for_date, synthesized_at,
                recommendation_ids_json, proposal_ids_json,
                x_rules_fired_json, synthesis_meta_json,
                source, ingest_actor, validated_at, projected_at
            ) VALUES (?, ?, ?, ?, ?, '[]', '[]', NULL,
                      'test', 'test', ?, ?)
            """,
            (
                plan_id,
                user,
                as_of.isoformat(),
                "2026-04-23T07:00:00+00:00",
                json.dumps([rec_id]),
                "2026-04-23T07:00:00+00:00",
                "2026-04-23T07:00:00+00:00",
            ),
        )
        conn.execute(
            """
            INSERT INTO recommendation_log (
                recommendation_id, user_id, for_date, issued_at,
                action, confidence, bounded, payload_json,
                source, ingest_actor, produced_at, validated_at,
                projected_at, domain, daily_plan_id
            ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, 'test', 'test',
                      ?, ?, ?, ?, ?)
            """,
            (
                rec_id,
                user,
                as_of.isoformat(),
                "2026-04-23T07:00:00+00:00",
                "proceed_with_planned_session",
                "moderate",
                json.dumps(payload),
                "2026-04-23T07:00:00+00:00",
                "2026-04-23T07:00:00+00:00",
                "2026-04-23T07:00:00+00:00",
                "recovery",
                plan_id,
            ),
        )
        conn.commit()


def _run_today(db: Path, *, user: str, as_of: date) -> tuple[int, str, str]:
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        rc = cli_main([
            "today",
            "--as-of", as_of.isoformat(),
            "--user-id", user,
            "--db-path", str(db),
            "--format", "plain",
        ])
    return rc, stdout_buf.getvalue(), stderr_buf.getvalue()


def test_hai_today_refuses_clinical_phrase_before_stdout(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    initialize_database(db)
    user = "u_refusal"
    as_of = date(2026, 4, 23)
    _seed_today_plan_with_rationale(
        db,
        user=user,
        as_of=as_of,
        rationale="You should seek medical advice before training.",
    )

    rc, stdout, stderr = _run_today(db, user=user, as_of=as_of)

    assert rc == exit_codes.USER_INPUT
    assert stdout == ""
    envelope = json.loads(stderr.removeprefix("hai: ").strip())
    assert envelope["schema_version"] == "refusal_envelope.v1"
    assert envelope["refusal_kind"] == "clinical_claim"
    assert envelope["details"]["matches"][0]["phrase"] == "medical advice"


def test_hai_today_no_refusal_passes_with_disabled_marker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    db = tmp_path / "state.db"
    initialize_database(db)
    user = "u_refusal_off"
    as_of = date(2026, 4, 23)
    _seed_today_plan_with_rationale(
        db,
        user=user,
        as_of=as_of,
        rationale="You should seek medical advice before training.",
    )
    monkeypatch.setenv(HAI_RUNTIME_MODE_ENV, NO_REFUSAL)
    monkeypatch.setenv(HAI_HERMETIC_ENV, "1")
    monkeypatch.setenv(HAI_STATE_DB_ENV, str(db))
    monkeypatch.setenv(HAI_BASE_DIR_ENV, str(tmp_path / "base"))

    rc, stdout, stderr = _run_today(db, user=user, as_of=as_of)

    assert rc == exit_codes.OK
    assert "medical advice" in stdout
    marker = json.loads(stderr.strip())
    assert marker["schema_version"] == "mechanism_disabled_marker.v1"
    assert marker["step_type"] == "mechanism_disabled"
    assert marker["mechanism"] == "refusal"
