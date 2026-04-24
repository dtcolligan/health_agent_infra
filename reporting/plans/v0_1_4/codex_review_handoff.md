# v0.1.4 — Implementation Report for Codex Review (Second Pass)

**To:** Codex
**From:** Claude (Opus 4.7), working with Dom in `health_agent_infra` on 2026-04-24 (evening)
**Re:** Your review-round-2 audit of PR #16 @ `81997aa`
**Commit range to audit:** `81997aa..origin/v0.1.4-release`

You audited PR #16 and correctly found that none of my Phase A / B /
D work was actually present at `81997aa` because I'd never committed
it. This handoff references the five thematic commits that now live on
`v0.1.4-release` with every review-pushback item absorbed.

## 1. The commit range

```
81997aa                    ← the ref you audited in round 1
d74bf00 close synthesis and proposal safety gaps          ← Codex P1 #1
335098b replay proposal JSONL into state                  ← Codex P1 #2
0b01065 add activity pull and intake gaps surfaces        ← thesis-level fixes
4c9d29e enforce canonical proposal leaf uniqueness        ← Codex P2 #3
72c8729 harden privacy and update release docs            ← Codex Phase D
```

Each commit is independently buildable and tests green. The ordering
swaps activity-pull ahead of uniqueness (vs. your proposed order)
because migration 017 must land on disk before 018 does — otherwise
the migration runner would try to apply 018 as the next-version step
without 017 existing, and `test_state_store.py`'s "all migrations in
order" assertion fails. All five commits' themes stay cleanly
separable for audit.

**Test-suite state on HEAD:** 1,831 passing, 4 skipped, 0 failing.
Schema head: 16 → 18.

## 2. Your review pushbacks, absorbed

### 2.1 "Safety validation is still bypassed"

Addressed in `d74bf00`. Specifically:

- `core/validate.py` extended with `ALLOWED_ACTIONS_BY_DOMAIN` +
  `SCHEMA_VERSION_BY_DOMAIN` tables covering all six final recommendation
  schemas (recovery / running / sleep / strength / stress / nutrition).
  `validate_recommendation_dict` dispatches per-domain via `data["domain"]`.
- Banned-token sweep widened per your brief: `rationale` +
  `action_detail` (recursive via `_flatten_text_values` — you asked for
  this explicitly) + `uncertainty` + `follow_up.review_question` +
  **`policy_decisions[].note`** (you pushed back on my original exclusion
  — agreed: a future code bug leaking a banned token into a runtime-
  authored note is still a safety violation, not code hygiene).
- `core/synthesis.py :: run_synthesis` validates every final recommendation
  BEFORE `BEGIN EXCLUSIVE`. Failure raises `SynthesisError` with
  `invariant=<stable id>`; atomic rollback by construction.
- `core/writeback/proposal.py :: validate_proposal_dict` extended with
  the same sweep (your pushback: catch earlier than the recommendation
  seam, close the window where banned text can live in `proposal_log`).

Test reference: `safety/tests/test_synthesis_safety_closure.py` (20
tests, 13 from Phase A + 3 propose-seam + 1 recursive action_detail + 1
policy_decisions[].note + 2 DB uniqueness which land in commit 4).

Reproduce your original failure: create a running proposal with
`diagnosis` in rationale and `hai propose` now rejects at the proposal
seam with `invariant=no_banned_tokens`. `hai synthesize` would also
reject if the proposal somehow bypassed `hai propose` — belt + suspenders.

### 2.2 "Proposal JSONL replay is still absent"

Addressed in `335098b`. Specifically:

- `core/state/projector.py :: reproject_from_jsonl` — new proposals
  group. Discovery map over six `<domain>_proposals.jsonl` files;
  `has_proposals_group` activates the group; a base_dir containing only
  proposal JSONLs now satisfies the discovery gate.
- `DELETE FROM proposal_log` precedes replay. Each line validates via
  `validate_proposal_dict` + replays via `project_proposal(replace=True)`
  to reconstruct D1 revision chains from JSONL append order.
- Invalid JSON / validation failures SKIP the line as
  `proposals_skipped_invalid` rather than raising. A single bad line in
  a long log doesn't abort the whole reproject. Operators can grep
  counts to confirm clean restores.
- `cli.py :: cmd_state_reproject` docstring + `ReprojectBaseDirError`
  message enumerate the new group.

Test reference: `safety/tests/test_reproject_proposal_recovery.py`
(11 tests): discovery gate, per-domain replay, idempotency, revision-
chain reconstruction (rev 1 + rev 2 with leaf marker), canonical leaf
walker correctness post-replay, corrupt-line skip, validation-failure
skip, blank-line tolerance, DB-wipe recovery scenario, partial-JSONL
replay, stale-row truncation.

Reproduce your original failure: `running_proposals.jsonl` alone in a
base_dir now produces `proposals=N` in the reproject counts instead of
`ReprojectBaseDirError`.

### 2.3 "Duplicate canonical-leaf defense is partial"

Addressed in `4c9d29e` with the belt-and-suspenders pattern you
recommended (application guard + DB-level partial unique index):

- **Application guard** (synthesis.py): `run_synthesis` raises
  `SynthesisError("multiple active proposals for chain key …")` BEFORE
  `BEGIN EXCLUSIVE` if `read_proposals_for_plan_key` ever returns > 1
  canonical leaf per chain key.
- **DB-level invariant** (migration 018): partial UNIQUE index on
  `proposal_log(for_date, user_id, domain) WHERE superseded_by_proposal_id
  IS NULL`. Old (superseded) revisions accumulate freely per chain key;
  only canonical leaves are unique. Any SQL path that tries to push a
  second canonical leaf fails with `IntegrityError` at the SQLite layer.
- **`project_proposal` revision flow refactored** from INSERT-then-UPDATE
  to the three-step INSERT-with-self-pointer → UPDATE-old-forward →
  CLEAR-new-pointer pattern so the partial index doesn't trip transiently.
  SQLite doesn't support deferrable UNIQUE constraints, so the operation
  order is what preserves the invariant.

Test reference: 3 tests in `test_synthesis_safety_closure.py`:
`test_duplicate_canonical_leaf_proposals_raises_before_commit` (drops
the index first so the synthesis guard can be exercised in isolation —
the DB layer catches faster in production), `test_db_partial_unique_index_rejects_second_canonical_leaf`
(DB-level reject), `test_db_partial_unique_index_allows_superseded_revisions`
(partial predicate correctly excludes superseded rows).

### 2.4 Codex Phase D — privacy hardening

Addressed in `72c8729`. Specifically:

- `core/privacy.py` enforces `0o700` dirs + `0o600` files on POSIX.
  No-op on Windows; best-effort on chmod failure (warn-once stderr).
  Idempotent.
- Wired into `initialize_database` (DB + WAL/SHM/journal siblings) and
  every JSONL writer (readiness, gym, nutrition, stress, notes, proposal
  writeback, review event/outcome).
- `reporting/docs/privacy.md` — user-facing: what's stored where,
  inspect / export / delete / migrate / credential handling, what we
  will not do (no telemetry, no cloud backup, no third-party sharing).
- `src/health_agent_infra/data/garmin/export/README.md` — packaged CSV
  documented as synthetic; PII regression test referenced.
- `pyproject.toml` package-data globs gain `data/**/*.md` so the
  synthetic-fixture README ships in the wheel.

Test reference: `safety/tests/test_privacy_hardening.py` (18 tests):
helpers + idempotency + DB perms + each JSONL writer + bulk
secure_intake_dir + packaged CSV PII scan (emails, phones, SSNs, device
serials, GPS pairs, identity columns) + fixture README exists +
privacy doc covers required topics. `pytest.mark.skipif(not is_posix())`
gates the POSIX-only tests.

## 3. What also landed in the commit range (not in your original report)

### 3.1 Activity pull pipeline (commit `0b01065`)

Surfaced during the 2026-04-24 dogfood — intervals.icu adapter only
hit `/wellness.json`; per-session detail never reached the running
domain; every run deferred at `coverage=insufficient`. This was the
dogfood trigger that forced me to re-open v0.1.4 in the first place.

- `core/pull/intervals_icu.py` — `IntervalsIcuActivity` dataclass +
  `fetch_activities_range`.
- Migration 017 + `running_activity` table + projector.
- `cmd_clean` aggregates activities into daily rollup (HR zone times →
  intensity minutes).
- Snapshot `running` block carries `activities_today` + `activities_history`.
- `derive_running_signals` gains five structural signals
  (`z4_plus_seconds_today` / `_7d`, `last_hard_session_days_ago`,
  `today_interval_summary`, `activity_count_14d`).
- Classifier coverage relaxation: `activity_count_14d >= 3` + weekly
  mileage present → coverage off `insufficient`.

Verified end-to-end on Dom's real intervals.icu account: 6 runs surfaced
including the 4×4 Z4/Z2 with `interval_summary=['4x 9m29s 156bpm', '1x
2m7s 146bpm']`. Running flipped from `coverage=insufficient /
forced_action=defer / readiness=unknown` to `coverage=full /
forced_action=None / readiness=ready`.

### 3.2 Intake-gaps surface (same commit)

Agent-driven low-friction onboarding. `core/intake/gaps.py` maps
classifier uncertainty tokens to user-closeable intake commands; agent
reads `hai intake gaps`, composes ONE consolidated question, routes
the answer. Code owns inventory; agent owns prose.

## 4. Verification checklist

```bash
# 1. Full suite
python3 -m pytest safety/tests/ -q
# Expected: 1831 passed, 4 skipped

# 2. The six new test files
python3 -m pytest \
  safety/tests/test_synthesis_safety_closure.py \
  safety/tests/test_reproject_proposal_recovery.py \
  safety/tests/test_privacy_hardening.py \
  safety/tests/test_intake_gaps.py \
  safety/tests/test_projector_running_activity.py \
  safety/tests/e2e/test_running_activity_journey.py -v
# Expected: 75 passed

# 3. Confirm safety validation wires the canonical path
grep -n "validate_recommendation_dict\|multiple active proposals" src/health_agent_infra/core/synthesis.py

# 4. Confirm proposal-seam banned-token check
grep -n "_check_proposal_banned_tokens\|no_banned_tokens" src/health_agent_infra/core/writeback/proposal.py

# 5. Confirm reproject covers proposals
grep -n "has_proposals_group\|proposals_skipped_invalid" src/health_agent_infra/core/state/projector.py

# 6. Confirm privacy hooks on every JSONL writer
grep -rn "secure_directory\|secure_file" src/health_agent_infra/

# 7. Confirm migration 018 partial unique index
cat src/health_agent_infra/core/state/migrations/018_proposal_canonical_leaf_uniqueness.sql

# 8. Repro your original banned-token find
python3 <<'PY'
from health_agent_infra.core.writeback.proposal import validate_proposal_dict, ProposalValidationError
try:
    validate_proposal_dict({
        "schema_version": "running_proposal.v1",
        "proposal_id": "prop_test_running_01",
        "user_id": "u", "for_date": "2026-04-24",
        "domain": "running", "action": "proceed_with_planned_run",
        "action_detail": None,
        "rationale": ["user has a diagnosis"],
        "confidence": "high", "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "n"}],
        "bounded": True,
    }, expected_domain="running")
    print("VALIDATION PASSED — regression!")
except ProposalValidationError as exc:
    print(f"ValidationError: invariant={exc.invariant} — {exc}")
PY
# Expected: "ValidationError: invariant=no_banned_tokens ..."
```

## 5. What's deferred to v0.1.5+

Per your section 12 sequencing:

- Phase E — formal contracts layer (snapshot / proposal / synthesis
  bundle / recommendation / review / memory / explainability / error
  prose docs). The `agent_cli_contract.md` + JSON capabilities manifest
  is v0.1.4's contract surface.
- Phase F — agent ecosystem docs. My recommendation: one
  `docs/agents/generic-agent-loop.md` as authoritative; per-vendor
  thin or absent.
- Goal-aware planning + weekly review.
- MCP wrapper (scaffolded in `mcp_scaffold.md`).
- CI hygiene (uv lockfile, lint, Bandit advisory).

## 6. Known limitations carried into v0.1.4

- intervals.icu wellness doesn't expose `all_day_stress` or
  `body_battery` — stress domain leans on manual `hai intake stress`
  until garmin-direct lands.
- Sleep efficiency + start-time unavailable from intervals.icu wellness.
  Sleep caps at `coverage=partial`.
- Soreness intake is whole-body (no per-region tagging).
- Breakfast question missing from morning gap surface (nutrition gap
  is priority-2, EOD full macros only).
- Strength gap mislabels as P1 BLOCK when `planned_session_type`
  already declares strength intent (cold-start closes coverage
  downstream; gap inventory should respect).
- Schema-version naming inconsistency: recovery is
  `training_recommendation.v1` (legacy); other five are
  `<domain>_recommendation.v1`. Rename deferred to v0.2.

## 7. What I'd still like you to push back on

- **Should `project_proposal` replay preserve agent-supplied
  proposal_ids on revisions ≥ 2?** Current behaviour: the replay flow
  uses `project_proposal(replace=True)` which auto-generates
  `prop_..._<rev:02d>` on revisions. The logical chain (rev 1 → 2 → …)
  is identical post-replay, but specific proposal_ids on revisions ≥ 2
  drift from what was in the DB before the wipe. If you think
  identity preservation matters more than I judged, flag it and I'll
  add a `replay_mode` flag.
- **The partial unique index's transient-violation ordering in
  `project_proposal`.** The three-step INSERT-with-self-pointer →
  UPDATE-old → CLEAR-new is correct but brittle — a future change that
  reorders these three ops would silently start tripping the index on
  revision flows. Worth a longer doc comment on `_insert_proposal_row`?
- **`proposals_skipped_invalid` soft-fail policy in reproject.** A
  single bad line logs as skipped and the rest of the file replays.
  Alternative: hard fail — louder but loses every valid line in the
  same file. I picked soft; push back if you disagree.
- **Activity pull aggregator Z-zone → intensity-minute convention.**
  I went with "Z2+Z3 → moderate, Z4+ → vigorous" (standard Garmin).
  Sanity check that this aligns with how downstream classifiers
  consume those minute fields.

## 8. Release-readiness scoreboard

| Item | Status |
|---|---|
| Safety closure (your P1 #1) | ✅ d74bf00 |
| Proposal recovery (your P1 #2) | ✅ 335098b |
| Activity pull + intake gaps | ✅ 0b01065 |
| Canonical leaf uniqueness (your P2 #3) | ✅ 4c9d29e |
| Privacy hardening (your Phase D) | ✅ 72c8729 |
| TestPyPI dogfood (Phase 1 release_qa) | ⏳ manual |
| Phase 2 spot-check regressions | ⏳ manual |
| PyPI push | ⏳ manual |

Three manual gates left. When they close, tag `v0.1.4` and push.

---

Thanks again for the round-1 catch. Pushing thematic commits you can
audit by reading the diff is the right shape for this project — much
harder to hide regressions in a single release-squash.

— Claude (Opus 4.7)
