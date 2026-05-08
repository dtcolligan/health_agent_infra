# Phase 0 — Preflight Findings

- Date: 2026-04-17
- Agent: Claude Code (Opus 4.7, this session)
- Branch: `rebuild`
- Artifacts: `reporting/artifacts/phase_0/run_20260417T151457Z/`
- Status: **Phase 1 delay gate NOT tripped. Proceed to Phase 0.5.**

## What ran

One end-to-end recovery-readiness loop, agent-driven, against the packaged Garmin CSV fixture:

```
hai state init       → 15 data tables + schema_migrations created, 0 friction
hai pull             → evidence.json, 0 friction once date was correct
hai clean            → cleaned.json + projected rows, 0 friction on valid input
hai state snapshot   → snapshot.json with correct missingness tokens
[agent reads skill]  → classified state, applied 6 policy gates, composed TrainingRecommendation
hai writeback        → persisted to recommendation_log.jsonl + daily_plan_2026-04-08.md (retry 2 of 2)
hai review schedule  → persisted to review_events.jsonl, 0 friction
```

Final DB state: 1 row each in `source_daily_garmin`, `accepted_recovery_state_daily`, `accepted_running_state_daily`, `recommendation_log`, `review_event`. All artifacts validate; idempotency key on `(for_date, user_id)` works.

## What worked

1. **`hai state init` / `hai state migrate`** — clean output, JSON-structured, no surprises. Both migrations (001, 002) applied without intervention.
2. **Snapshot missingness tokens** — `unavailable_at_source:acute_load,acwr_ratio,chronic_load` was legible and mapped cleanly to uncertainty tokens. This pattern is worth preserving through the Phase 1 snapshot reshape.
3. **R4 (review_required) error reporting** — exit=2 with a clean, agent-parseable stderr message: `writeback rejected: invariant=review_at_within_24h: ... delta=-9 days, 15:36:58`. This is exactly what the skill-to-code contract should look like.
4. **Idempotency + writeback artifacts** — `recommendation_log.jsonl` (audit) + `daily_plan_<date>.md` (human-readable) generated automatically from a single `hai writeback` call. The markdown note is surprisingly useful.
5. **`--use-default-manual-readiness`** — correct escape hatch for offline/agent runs where no interactive subjective input is available. Defaults produced reasonable values (`soreness=moderate`, `energy=moderate`, `planned_session_type=moderate`).

## Friction surfaced

### F1. Default `hai pull` date silently produces empty evidence against stale fixture
**Severity**: medium. Not blocking, but unfriendly for first-time agents.

`hai pull` without `--date` defaults to today (2026-04-17). The packaged CSV fixture covers 2026-02-05 to 2026-04-08. The first run produced an evidence JSON with every signal NULL and exit=0, no stderr. I only realized by inspecting the JSON and seeing `sleep_hours=None` etc.

**Fix**: `hai pull` should emit a stderr note when the requested date is outside the fixture's date range (e.g., `warning: no evidence for 2026-04-17; fixture covers 2026-02-05 to 2026-04-08`). Or `hai pull` should default to the latest fixture date when source=csv.

### F2. `hai writeback --base-dir` help text is misleading
**Severity**: low. Caused one retry.

Help says: `Writeback root (must contain 'recovery_readiness_v1')`. I read this as "pass the parent dir that contains a subdir named recovery_readiness_v1." The actual contract is "pass a path whose final component is (or is under a path with) `recovery_readiness_v1`." The error message was a Python traceback (see F3), not a clean message.

**Fix**: help should read: `Writeback root; must be the 'recovery_readiness_v1' subdirectory itself (or a path under it).` And the error should be a clean validation message, not a traceback.

### F3. Error-surface inconsistency between schema validation and path validation
**Severity**: medium. An agent relying on a parse-stderr strategy has to handle both clean messages and Python tracebacks.

- R4 invariant failure → exit=2, clean stderr, no traceback.
- Writeback path validation failure → exit=1, full Python traceback, `ValueError: writeback base_dir ... is outside the allowed local writeback root`.

An agent that expects consistent error shapes will misclassify the second as an unrecoverable crash. Phase 1 should unify error surfaces — all validation failures should produce clean, agent-parseable stderr.

### F4. Skill ambiguity on `review_at` anchor date
**Severity**: low. Caused one retry (the R4 failure above).

`recovery-readiness/SKILL.md` §Follow-up says: *"Set `review_at` to next morning at `07:00:00+00:00`."* It does not say *next morning after what* (`for_date` vs `issued_at`). R4 enforces "within 24h of `issued_at`" — that's the anchor. Only obvious at writeback time.

This matters specifically when `issued_at != for_date` (e.g., replaying historical evidence as in Phase 0). In normal operation they align and the ambiguity never surfaces.

**Fix**: skill copy should read *"next morning after `issued_at`, at 07:00:00+00:00"*. Phase 1 skill rewrite folds this in.

### F5. Skill cognitive load validates the Phase 1 classify/policy extraction
**Severity**: informational. Supports the plan.

At 315 lines, the recovery-readiness skill was **manageable but dense**. Reasoning through it required cross-referencing three sections (classification tables → policy rules → rationale tokens) for every decision. A straight `ClassifiedRecoveryState` dataclass returned by `classify.py`, plus a `PolicyResult` from `policy.py`, would remove ~60% of that cognitive load — all the threshold lookups and rule firings become pre-computed inputs to the skill rather than work the skill performs.

This is direct evidence for the code-vs-skill boundary the plan commits to. Proceed with Phase 1 as specified.

## Delay-gate evaluation

Per the revised plan's Phase 1 delay gate, the following would delay Phase 1:

| Trigger | Observed? | Notes |
|---|---|---|
| Any `hai writeback` that fails schema validation with no agent-visible error (silent drop) | **No** | R4 failure was clearly reported (exit=2, clean stderr). Path failure was loud via traceback (exit=1). Neither was silent. |
| Any step that required >2 retries for the agent to complete | **No** | Writeback required exactly 2 retries (review_at fix + base-dir fix). At the threshold, not over. |
| Any case where the agent could not recover from a malformed intermediate artifact without human intervention | **No** | Both error modes were self-correctable from the error message. |

**Verdict: PROCEED.** No delay-gate triggers fired.

## Contradicted / unverified plan assumptions

1. **Plan assumption**: *"Installation verified on a clean venv (`pip install -e .`; `hai setup-skills`)"*.
   **Reality**: this run reused an existing venv that already had `hai` installed (and already-deployed skills). **Clean-venv install was not actually tested.** Before Phase 7 polish, run the install flow from scratch in an empty venv to verify `pip install -e .` + `hai setup-skills` work end-to-end.

2. **Plan claim**: *"CSV fixture retained for tests/demos"*. True, but the fixture is time-anchored and stale by ~9 days against today. Phase 2's live pull will fix this for daily use, but tests and demos will drift. Worth a small automation (regenerate fixture or slide dates on install).

3. **Plan assumption**: *"recovery-readiness SKILL.md is ~280 lines"* (pre-revision). Actual: 315 lines. (Already corrected in the revised plan.)

## Recommendations for Phase 0.5 (synthesis prototype)

Two things from this run to carry forward:

1. **Use `2026-04-08` as the prototype's test date.** It's the last date with full fixture coverage and produces a non-trivial classification (sparse coverage, vendor-disagreement, moderate confidence). Good single-domain input to build the 2-domain prototype on.
2. **The `daily_plan_2026-04-08.md` markdown artifact pattern** is worth copying for the synthesis prototype's output. Machine-auditable JSONL + human-readable markdown from one command is a nice pattern.

## Recommendations for Phase 1 (beyond the plan's existing scope)

1. **Unify error surfaces** (F3). All CLI validation failures should exit=2 with clean stderr. No tracebacks leak to agents.
2. **Rewrite help copy for `--base-dir`** (F2). Concrete wording above.
3. **Add fixture-date-out-of-range warning to `hai pull`** (F1). Not expensive; prevents silent null cascades.
4. **Phase 1 skill rewrite should resolve the `review_at` anchor ambiguity** (F4). Already in scope, flagging the specific line.

---

**Next action**: begin Phase 0.5 (synthesis prototype). Plan-file reference: `reporting/plans/comprehensive_rebuild_plan.md` §Phase 0.5.
