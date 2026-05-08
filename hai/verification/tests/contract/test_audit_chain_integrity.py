"""D1 test coverage #10 — audit-chain integrity after any CLI sequence.

These are structural invariants on the persisted state that must
hold after any combination of ``hai propose`` / ``hai synthesize``
(including ``--supersede``) + ``hai review record``. The tests seed a
realistic multi-step journey via the CLI, then assert against the
final DB rows.

Invariants covered:

1. Every ``proposal_id`` in a ``daily_plan.proposal_ids_json`` array
   resolves to a ``proposal_log`` row.
2. Every ``recommendation_log.daily_plan_id`` resolves to a
   ``daily_plan`` row.
3. Every ``review_outcome`` row points to a canonical-leaf rec OR
   to a re-linked one that carries ``re_link_note`` (D1).
4. Every ``proposal_log`` chain walks forward consistently — no
   double-linking of a single leaf, no cycles, exactly one
   canonical leaf per ``(for_date, user_id, domain)``.
5. Every ``daily_plan`` chain walks forward consistently — at most
   one canonical leaf per ``(for_date, user_id)``.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from .conftest import ContractEnv, seed_six_domain_daily


AS_OF = date(2026, 4, 22)
USER = "u_contract"


# ---------------------------------------------------------------------------
# Invariant #1 — every proposal_ids_json entry resolves
# ---------------------------------------------------------------------------


def test_every_proposal_ids_json_entry_resolves_in_proposal_log(
    contract_env: ContractEnv,
):
    """After a fresh six-domain synth, every proposal_id listed on
    every daily_plan must exist in proposal_log."""

    seed_six_domain_daily(contract_env, as_of=AS_OF, user_id=USER)

    plans = contract_env.sql(
        "SELECT daily_plan_id, proposal_ids_json FROM daily_plan"
    )
    assert plans, "seeded synthesis produced no daily_plan rows"

    unresolved: list[tuple[str, str]] = []
    for plan_id, proposal_ids_json in plans:
        ids = json.loads(proposal_ids_json)
        for pid in ids:
            row = contract_env.sql_one(
                "SELECT proposal_id FROM proposal_log WHERE proposal_id = ?",
                pid,
            )
            if row is None:
                unresolved.append((plan_id, pid))
    assert not unresolved, (
        f"proposal_ids_json references unknown proposal_log ids: {unresolved}"
    )


def test_proposal_ids_json_stable_after_supersede(contract_env: ContractEnv):
    """After ``hai synthesize --supersede``, both the v1 and v2 plans
    list proposal ids that still resolve. The superseded plan's
    proposals MUST stay resolvable so ``hai explain`` on the v1 plan
    renders its original proposals (D1 bug #3).
    """

    seed_six_domain_daily(contract_env, as_of=AS_OF, user_id=USER)
    contract_env.run_hai(
        "synthesize", "--as-of", str(AS_OF), "--user-id", USER,
        "--supersede",
    )

    plans = contract_env.sql(
        "SELECT daily_plan_id, proposal_ids_json FROM daily_plan "
        "ORDER BY daily_plan_id"
    )
    # Two plans now: canonical + _v2.
    assert len(plans) == 2
    for plan_id, proposal_ids_json in plans:
        for pid in json.loads(proposal_ids_json):
            row = contract_env.sql_one(
                "SELECT proposal_id FROM proposal_log WHERE proposal_id = ?",
                pid,
            )
            assert row is not None, (
                f"supersede orphaned proposal {pid!r} from plan {plan_id!r}"
            )


# ---------------------------------------------------------------------------
# Invariant #2 — every recommendation_log.daily_plan_id resolves
# ---------------------------------------------------------------------------


def test_every_recommendation_log_daily_plan_id_resolves(
    contract_env: ContractEnv,
):
    seed_six_domain_daily(contract_env, as_of=AS_OF, user_id=USER)

    orphans = contract_env.sql(
        "SELECT r.recommendation_id, r.daily_plan_id FROM recommendation_log r "
        "LEFT JOIN daily_plan p ON r.daily_plan_id = p.daily_plan_id "
        "WHERE r.daily_plan_id IS NOT NULL AND p.daily_plan_id IS NULL"
    )
    assert orphans == [], (
        f"recommendation_log rows point at non-existent daily_plan_id: {orphans}"
    )


# ---------------------------------------------------------------------------
# Invariant #3 — review_outcome points to canonical leaf OR re-linked
# ---------------------------------------------------------------------------


def test_review_outcome_never_orphans_on_superseded_plan(
    contract_env: ContractEnv,
):
    """D1 §review record behaviour: a review outcome recorded against
    a rec whose plan has been superseded must either re-link to the
    leaf's matching-domain rec (with re_link_note populated) or
    refuse to write. This contract test asserts the DB never settles
    into an orphan state under any realistic CLI sequence."""

    # v1 synth.
    seed_six_domain_daily(contract_env, as_of=AS_OF, user_id=USER)
    v1_rec_id = f"rec_{AS_OF}_{USER}_recovery_01"

    # Schedule + record a review before supersede.
    v1_rec = contract_env.sql_one(
        "SELECT payload_json FROM recommendation_log WHERE recommendation_id = ?",
        v1_rec_id,
    )
    v1_payload = json.loads(v1_rec[0])
    rec_file = contract_env.tmp_root / "v1_rec.json"
    rec_file.write_text(json.dumps(v1_payload), encoding="utf-8")
    contract_env.run_hai(
        "review", "schedule",
        "--recommendation-json", str(rec_file),
        "--base-dir", str(contract_env.base_dir),
    )

    # Now supersede — creates v2; v1 becomes a superseded leaf.
    contract_env.run_hai(
        "synthesize", "--as-of", str(AS_OF), "--user-id", USER,
        "--supersede",
    )

    # Record an outcome against the v1 rec; re-link must fire.
    outcome_payload = {
        "review_event_id": v1_payload["follow_up"]["review_event_id"],
        "recommendation_id": v1_rec_id,
        "user_id": USER,
        "domain": "recovery",
        "followed_recommendation": True,
        "self_reported_improvement": True,
        "free_text": None,
    }
    outcome_file = contract_env.tmp_root / "outcome.json"
    outcome_file.write_text(json.dumps(outcome_payload), encoding="utf-8")
    contract_env.run_hai(
        "review", "record",
        "--outcome-json", str(outcome_file),
        "--base-dir", str(contract_env.base_dir),
    )

    # Invariant: the outcome's recommendation_id points at a
    # canonical-leaf rec (one whose daily_plan_id's plan has
    # superseded_by_plan_id IS NULL), OR it carries re_link_note
    # and the original target is captured in
    # re_linked_from_recommendation_id.
    orphans = contract_env.sql(
        """
        SELECT o.recommendation_id,
               o.re_linked_from_recommendation_id,
               o.re_link_note,
               p.superseded_by_plan_id
        FROM review_outcome o
        JOIN recommendation_log r
          ON o.recommendation_id = r.recommendation_id
        JOIN daily_plan p
          ON r.daily_plan_id = p.daily_plan_id
        WHERE p.superseded_by_plan_id IS NOT NULL
          AND o.re_link_note IS NULL
        """
    )
    assert orphans == [], (
        f"review_outcome on superseded plan without re_link_note: {orphans}"
    )


# ---------------------------------------------------------------------------
# Invariant #4 — proposal_log chain walks consistently
# ---------------------------------------------------------------------------


def test_proposal_log_has_exactly_one_canonical_leaf_per_chain_key(
    contract_env: ContractEnv,
):
    """Every ``(for_date, user_id, domain)`` chain key must have
    exactly one row with ``superseded_by_proposal_id IS NULL``. A
    zero-leaf group indicates a broken forward-link; a multi-leaf
    group indicates a double-linking bug."""

    # Seed a chain: v1 + replace with v2 for recovery.
    seed_six_domain_daily(contract_env, as_of=AS_OF, user_id=USER)
    v2 = {
        "schema_version": "recovery_proposal.v1",
        "proposal_id": f"prop_{AS_OF}_{USER}_recovery_02",
        "user_id": USER,
        "for_date": str(AS_OF),
        "domain": "recovery",
        "action": "downgrade_session_to_mobility_only",
        "action_detail": None,
        "rationale": ["soreness_high"],
        "confidence": "moderate",
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": "r_baseline", "decision": "allow", "note": "ok"},
        ],
        "bounded": True,
    }
    v2_path = contract_env.tmp_root / "prop_recovery_v2.json"
    v2_path.write_text(json.dumps(v2))
    contract_env.run_hai(
        "propose", "--domain", "recovery",
        "--proposal-json", str(v2_path),
        "--base-dir", str(contract_env.base_dir),
        "--replace",
    )

    leaf_counts = contract_env.sql(
        "SELECT for_date, user_id, domain, "
        "COUNT(*) FILTER (WHERE superseded_by_proposal_id IS NULL) AS leaves "
        "FROM proposal_log GROUP BY for_date, user_id, domain"
    )
    for for_date, user_id, domain, leaves in leaf_counts:
        assert leaves == 1, (
            f"proposal chain ({for_date}, {user_id}, {domain}) has "
            f"{leaves} leaves — expected exactly 1"
        )


def test_proposal_log_has_no_cycles(contract_env: ContractEnv):
    """Follow ``superseded_by_proposal_id`` from every row; the walk
    must terminate at a leaf (NULL) without revisiting any row."""

    seed_six_domain_daily(contract_env, as_of=AS_OF, user_id=USER)

    rows = contract_env.sql(
        "SELECT proposal_id, superseded_by_proposal_id FROM proposal_log"
    )
    forward = {pid: nxt for pid, nxt in rows}

    for pid in forward:
        seen = set()
        cursor = pid
        while cursor is not None:
            if cursor in seen:
                pytest.fail(
                    f"proposal_log forward-link cycle starting at {pid!r}: "
                    f"revisited {cursor!r}"
                )
            seen.add(cursor)
            cursor = forward.get(cursor)


# ---------------------------------------------------------------------------
# Invariant #5 — daily_plan chain walks consistently
# ---------------------------------------------------------------------------


def test_daily_plan_has_exactly_one_canonical_leaf_per_chain_key(
    contract_env: ContractEnv,
):
    seed_six_domain_daily(contract_env, as_of=AS_OF, user_id=USER)
    contract_env.run_hai(
        "synthesize", "--as-of", str(AS_OF), "--user-id", USER,
        "--supersede",
    )

    counts = contract_env.sql(
        "SELECT for_date, user_id, "
        "COUNT(*) FILTER (WHERE superseded_by_plan_id IS NULL) AS leaves "
        "FROM daily_plan GROUP BY for_date, user_id"
    )
    for for_date, user_id, leaves in counts:
        assert leaves == 1, (
            f"daily_plan chain ({for_date}, {user_id}) has {leaves} "
            f"leaves — expected exactly 1"
        )


def test_daily_plan_has_no_cycles(contract_env: ContractEnv):
    seed_six_domain_daily(contract_env, as_of=AS_OF, user_id=USER)
    contract_env.run_hai(
        "synthesize", "--as-of", str(AS_OF), "--user-id", USER,
        "--supersede",
    )

    rows = contract_env.sql(
        "SELECT daily_plan_id, superseded_by_plan_id FROM daily_plan"
    )
    forward = {pid: nxt for pid, nxt in rows}

    for pid in forward:
        seen = set()
        cursor = pid
        while cursor is not None:
            if cursor in seen:
                pytest.fail(
                    f"daily_plan forward-link cycle at {pid!r}: "
                    f"revisited {cursor!r}"
                )
            seen.add(cursor)
            cursor = forward.get(cursor)
