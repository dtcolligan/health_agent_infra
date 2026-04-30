"""W-AE (v0.1.13) — `hai doctor` expansion contracts.

Three surfaces are pinned here:

  1. `classify_intervals_icu_probe` returns one of the five
     contract tokens (`OK`, `CAUSE_1_CLOUDFLARE_UA`, `CAUSE_2_CREDS`,
     `NETWORK`, `OTHER`) for every reasonable input. The tokens are
     part of the doctor JSON contract — a renaming would silently
     break `reporting/docs/intervals_icu_403_triage.md`'s references.

  2. `check_onboarding_readiness` warns when the user has not yet
     authored intent / target / wellness pull, and goes ok once all
     three are present.

  3. `check_intake_gaps` runs without crashing on a freshly-init DB
     and surfaces the gaps the agent would see via `hai intake gaps`.
"""

from __future__ import annotations

from datetime import date

import pytest

from health_agent_infra.core.doctor.checks import (
    check_intake_gaps,
    check_onboarding_readiness,
)
from health_agent_infra.core.doctor.probe import (
    OUTCOME_CLASSES,
    OUTCOME_NEXT_STEPS,
    ProbeResult,
    classify_intervals_icu_probe,
)


# ---------------------------------------------------------------------------
# Classifier — pure function, exhaustive class coverage
# ---------------------------------------------------------------------------


def test_classify_ok_when_probe_succeeded():
    assert classify_intervals_icu_probe(
        ok=True,
        http_status=200,
        error_body=None,
        error_message=None,
    ) == "OK"


def test_classify_cloudflare_when_body_carries_cloudflare_marker():
    """Cloudflare UA-block is detected by body shape, not status code —
    Cloudflare can return 403 OR a challenge page; the body discriminates."""

    body = (
        '{"error_code":1010,"error_name":"browser_signature_banned",'
        '"cloudflare_error":true}'
    )
    assert classify_intervals_icu_probe(
        ok=False,
        http_status=403,
        error_body=body,
        error_message="HTTP 403 Forbidden",
    ) == "CAUSE_1_CLOUDFLARE_UA"


def test_classify_cloudflare_detects_browser_signature_banned_alone():
    """Even without `cloudflare_error: true`, the `browser_signature_banned`
    token is canonical Cloudflare-1010 shape and classifies the same way."""

    assert classify_intervals_icu_probe(
        ok=False,
        http_status=403,
        error_body="browser_signature_banned",
        error_message=None,
    ) == "CAUSE_1_CLOUDFLARE_UA"


def test_classify_creds_on_401():
    assert classify_intervals_icu_probe(
        ok=False,
        http_status=401,
        error_body='{"error":"unauthorized"}',
        error_message="HTTP 401 Unauthorized",
    ) == "CAUSE_2_CREDS"


def test_classify_creds_on_403_without_cloudflare_marker():
    """A bare 403 with intervals.icu's own auth-shaped body classifies as
    CAUSE_2_CREDS — the absence of the Cloudflare marker is the signal."""

    assert classify_intervals_icu_probe(
        ok=False,
        http_status=403,
        error_body='{"error":"invalid api key"}',
        error_message="HTTP 403 Forbidden",
    ) == "CAUSE_2_CREDS"


def test_classify_network_when_no_http_status_and_message_names_a_network_primitive():
    assert classify_intervals_icu_probe(
        ok=False,
        http_status=None,
        error_body=None,
        error_message="urlopen error: Connection refused",
    ) == "NETWORK"


def test_classify_network_dns_failure():
    assert classify_intervals_icu_probe(
        ok=False,
        http_status=None,
        error_body=None,
        error_message="urlopen error: Name or service not known",
    ) == "NETWORK"


def test_classify_other_on_5xx():
    assert classify_intervals_icu_probe(
        ok=False,
        http_status=503,
        error_body="<html>Service Unavailable</html>",
        error_message="HTTP 503 Service Unavailable",
    ) == "OTHER"


def test_classify_other_on_unrecognised_failure():
    assert classify_intervals_icu_probe(
        ok=False,
        http_status=None,
        error_body=None,
        error_message="ValueError: malformed JSON",
    ) == "OTHER"


def test_outcome_classes_set_matches_documented_five():
    """Drift guard: the contract surface in
    `reporting/docs/intervals_icu_403_triage.md` enumerates these five
    strings. A change here must move in lockstep with that doc.
    """

    assert OUTCOME_CLASSES == frozenset({
        "OK",
        "CAUSE_1_CLOUDFLARE_UA",
        "CAUSE_2_CREDS",
        "NETWORK",
        "OTHER",
    })


def test_every_outcome_class_has_next_step_prose():
    """Every classification token must have actionable next-step prose,
    or `check_auth_intervals_icu` will surface an empty hint."""

    for cls in OUTCOME_CLASSES:
        assert cls in OUTCOME_NEXT_STEPS
        assert OUTCOME_NEXT_STEPS[cls].strip(), (
            f"OUTCOME_NEXT_STEPS[{cls!r}] is empty/whitespace"
        )


# ---------------------------------------------------------------------------
# ProbeResult — schema carries outcome_class
# ---------------------------------------------------------------------------


def test_probe_result_to_dict_includes_outcome_class():
    """Existing serialisation (used by the doctor JSON output) must
    propagate `outcome_class` — the field is the contract surface
    that downstream tooling reads."""

    result = ProbeResult(
        ok=False,
        source="live",
        http_status=403,
        error_message="HTTP 403 Forbidden",
        error_body='{"cloudflare_error":true}',
        outcome_class="CAUSE_1_CLOUDFLARE_UA",
    )
    payload = result.to_dict()
    assert payload["outcome_class"] == "CAUSE_1_CLOUDFLARE_UA"
    assert payload["error_body"] == '{"cloudflare_error":true}'


# ---------------------------------------------------------------------------
# check_onboarding_readiness — DB-fixture tests
# ---------------------------------------------------------------------------


@pytest.fixture
def fresh_state_db(tmp_path):
    """A freshly-migrated state DB — schema at HEAD, no user rows."""

    from health_agent_infra.core.state.store import initialize_database

    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return db_path


def test_onboarding_readiness_warns_when_db_missing(tmp_path):
    out = check_onboarding_readiness(
        tmp_path / "missing.db",
        user_id="u_local_1",
        as_of_date=date(2026, 4, 30),
    )
    assert out["status"] == "warn"
    assert "init" in out["hint"]


def test_onboarding_readiness_fresh_db_warns_with_three_missing(fresh_state_db):
    out = check_onboarding_readiness(
        fresh_state_db,
        user_id="u_local_1",
        as_of_date=date(2026, 4, 30),
    )
    assert out["status"] == "warn"
    # All three signals empty on a fresh init.
    assert out["intent_count"] == 0
    assert out["target_count"] == 0
    assert out["has_wellness_pull"] is False
    assert set(out["missing"]) == {"intent", "target", "wellness_pull"}
    # Hint surfaces the first missing piece's actionable next step.
    assert "intent" in out["hint"]


def test_onboarding_readiness_goes_ok_when_all_three_present(fresh_state_db):
    """End-to-end: write one intent row, one target row, one sync_run_log
    success row → readiness goes ok."""

    from datetime import datetime, timezone

    from health_agent_infra.core.intent.store import add_intent
    from health_agent_infra.core.state import open_connection
    from health_agent_infra.core.target.store import add_target

    conn = open_connection(fresh_state_db)
    try:
        # Active intent.
        add_intent(
            conn,
            user_id="u_local_1",
            domain="running",
            intent_type="training_session",
            scope_start=date(2026, 4, 1),
            scope_end=date(2026, 12, 31),
            payload={"session_kind": "easy_z2"},
            status="active",
        )
        # Active target.
        add_target(
            conn,
            user_id="u_local_1",
            domain="running",
            target_type="training_load",
            value=300.0,
            unit="trimp_week",
            effective_from=date(2026, 4, 1),
            effective_to=None,
            status="active",
        )
        # Successful wellness pull. sync_id is autoincrement INTEGER PK.
        conn.execute(
            "INSERT INTO sync_run_log "
            "(source, user_id, mode, started_at, completed_at, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "intervals_icu",
                "u_local_1",
                "live",
                datetime(2026, 4, 30, 6, 0, tzinfo=timezone.utc).isoformat(),
                datetime(2026, 4, 30, 6, 1, tzinfo=timezone.utc).isoformat(),
                "ok",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    out = check_onboarding_readiness(
        fresh_state_db,
        user_id="u_local_1",
        as_of_date=date(2026, 4, 30),
    )
    assert out["status"] == "ok"
    assert out["intent_count"] == 1
    assert out["target_count"] == 1
    assert out["has_wellness_pull"] is True


# ---------------------------------------------------------------------------
# check_intake_gaps — runs on a fresh DB without crashing
# ---------------------------------------------------------------------------


def test_intake_gaps_warns_when_db_missing(tmp_path):
    out = check_intake_gaps(
        tmp_path / "missing.db",
        user_id="u_local_1",
        as_of_date=date(2026, 4, 30),
    )
    assert out["status"] == "warn"


def test_intake_gaps_returns_blocking_count_on_fresh_db(fresh_state_db):
    """On a fresh DB the gap detector reports the manual-checkin / stress /
    nutrition gaps — blocking, since coverage requires those rows."""

    out = check_intake_gaps(
        fresh_state_db,
        user_id="u_local_1",
        as_of_date=date(2026, 4, 30),
    )
    # The shape contract — the actual gap counts are runtime-dependent
    # and asserted by `core.intake.gaps`'s own tests.
    assert out["status"] in {"ok", "warn"}
    assert "gap_count" in out
    assert "blocking_gap_count" in out
    if out["status"] == "warn":
        assert out["blocking_gap_count"] >= 1
