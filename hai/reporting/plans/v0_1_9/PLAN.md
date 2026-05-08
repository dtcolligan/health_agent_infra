# v0.1.9 Plan - hardening + governance closure

> **Provenance.** Drafted 2026-04-26 after a parallel ultra-review by
> Claude (this conversation) and Codex caught overlapping P0/P1 issues
> not covered by v0.1.8. The merged finding set is the basis of the
> hardening workstreams below. Roadmap-committed items (W52, W53, W58)
> remain deferred until after this hardening release; v0.1.9 ships the
> governance / provenance / safety closures below.
>
> **Status.** Implemented and release-prep ready after Codex
> implementation review follow-up. B1-B8 are the complete v0.1.9 scope.

---

## 0. Goals & non-goals

### Goals (v0.1.9)

1. **Close the W57 governance gap.** Today, agent-safe archive can
   deactivate user state. Make every intent/target activation /
   deactivation path runtime-gated and explicitly user-driven.
2. **Make the safety closure fail-loud everywhere.** Skill-overlay
   silent ignores and validator under-validation become explicit
   `SynthesisError` / `RecommendationValidationError` paths with stable
   invariant ids.
3. **Eliminate direct-`hai synthesize` divergence from `hai daily`.**
   The two paths must produce identical Phase A firings against the
   same persisted state, must reject incomplete domain sets, and must
   never plan over stale or absent accepted-state rows.
4. **Make pull/clean provenance deterministic.** Replaying identical
   evidence produces identical raw provenance rows; `hai daily` writes
   to `sync_run_log` the same way `hai pull` does.
5. **Refresh safety-skill prose** so it matches the shipped six-domain
   action enums and X-rule tier semantics.
6. **Preserve scope discipline.** Do not close W52 weekly review, W53
   insight ledger, or W58 LLM-judge factuality in this release; they
   land after the hardening release is committed.

### Non-goals (v0.1.9)

- No `cli.py` split. AGENTS.md W29 stays deferred.
- No new pull adapters. RAW_DAILY_ROW_COLUMNS Garmin coupling is
  acknowledged debt; not in scope this cycle.
- No micronutrient or food-taxonomy work.
- No autonomous plan generation. The W57 closure tightens — does not
  loosen — agent authority.
- No MCP server, no UI.

### Guardrails

- **Every governance fix gets a contract test.** A finding that the
  manifest claims `agent_safe=False` but no runtime gate enforces it
  is the kind of bug that closed v0.1.8 with a real W57 leak. The
  cycle exit criterion is: every W57-affected handler has both a
  manifest assertion and a runtime-gate assertion.
- **Every fail-soft path made fail-loud carries a stable invariant id.**
  The `invariant=` discipline established in v0.1.4 stays; new ids land
  with their tests.
- **No new write path bypasses the three-state audit chain.**

---

## 1. Audit integration

Two parallel ultra-reviews ran 2026-04-26: Claude (in-conversation,
this file's author) and Codex (separate session). Combined findings:

**Both reviews flagged** (highest confidence):

- Skill-overlay silently swallows out-of-lane edits → B2.
- Validators don't enforce list[str] shape on text fields → B3.
- (Different angles, same area) Pull/clean provenance + shape
  validation → B5 (Codex emphasis on `sync_run_log` + idempotent
  `export_batch_id`; Claude emphasis on adapter-shape contract).

**Codex caught, Claude missed:**

- W57 violation in `hai intent archive` / `hai target archive`
  (`agent_safe=True` + UPDATE `status='archived'`) → B1.
- Direct `hai synthesize` doesn't enforce expected-domain
  completeness → B4a.
- Direct `hai synthesize` uses degraded snapshot (no
  `evidence_bundle`); X1 sleep-debt parity bug → B4b.
- `_project_clean_into_state` fails open on DB projection failure
  → B5b.
- Safety skill is stale vs nutrition v1 macro-actions and X-rule
  block-tier escalate semantics → B6.
- `data_quality_daily.coverage_band` can be null on the normal clean
  path → B8.

**Claude caught, Codex missed:**

- `hai intent commit` / `hai target commit` correctly marked
  `agent_safe=False` but have no runtime gate (process-level honor
  system) → bundled into B1 for symmetry.
- Banned-token sweep duplicated across two validators
  (`core/validate.py` and `core/writeback/proposal.py`) → B3.
- intervals.icu adapter swallows /activities errors without setting
  `last_pull_partial=True` → B5c.
- Dead-code branch in `_nutrition_deficit_and_protein` → B8.
- No coverage test that every Phase B rule has a `PHASE_B_TARGETS`
  entry → B8.

The merged set is what this plan implements.

---

## 2. Workstream catalogue

### B1 — W57 closure on archive + commit handlers (P0)

**Problem.** `hai intent archive` and `hai target archive` are
declared `agent_safe=True` in the capabilities manifest (cli.py:6807,
cli.py:6937) and call `archive_intent` / `archive_target`, which
directly UPDATE `status='archived'` on rows including currently-active
ones. AGENTS.md W57 is unambiguous: agents cannot deactivate user
state without an explicit user commit. Archive-of-active *is*
deactivation.

Symmetrically, `hai intent commit` / `hai target commit` are correctly
declared `agent_safe=False` but the runtime executes for any caller —
the manifest flag is informational. A jailbroken or
contract-non-conforming agent that calls these via `Bash` succeeds.

**Fix.**

1. Flip `agent_safe=True` → `agent_safe=False` on `intent archive` and
   `target archive` parsers. Update the description string to mirror
   the commit handlers' wording about "agents must NOT auto-archive".
2. Add a runtime gate to all four handlers (`cmd_intent_commit`,
   `cmd_intent_archive`, `cmd_target_commit`, `cmd_target_archive`):
   require either `--confirm` or interactive stdin
   (`sys.stdin.isatty()`). If neither, exit `USER_INPUT` with an
   explicit message naming W57.
3. Add `--confirm` flag to the same four parsers.

**Tests.**

- `test_capabilities_w57_archive_not_agent_safe` — assert all four
  handlers carry `agent_safe=False` in the rendered manifest.
- `test_w57_runtime_gate_rejects_non_tty_no_confirm` — invoke the
  four handlers with stdin redirected from `/dev/null` and no
  `--confirm`; assert exit `USER_INPUT` and no row state change.
- `test_w57_runtime_gate_accepts_confirm_flag` — same invocations
  with `--confirm`; assert state transition lands.

**Files.**

- `src/health_agent_infra/cli.py` — manifest annotations + handlers.
- `verification/tests/contract/test_w57_runtime_gate.py` — new file.
- `verification/tests/test_capabilities_flags_contract.py` —
  add the four-handler manifest assertion.

---

### B2 — Skill-overlay fail-loud (P0)

**Problem.** `_overlay_skill_drafts` (`core/synthesis.py:249`) silently
drops attempts to mutate `action`, `action_detail`, `confidence`, or
`daily_plan_id`. Documented as a feature ("silently ignored") but is
the one fail-soft path in an otherwise fail-loud safety closure. Skill
drift, malformed overlay drafts, or prompt injection becomes invisible.

**Fix.**

1. Define `_OVERLAY_ALLOWED_KEYS = frozenset({"recommendation_id",
   "rationale", "uncertainty", "follow_up"})` and within `follow_up`
   only `review_question` is settable.
2. On any skill draft entry, raise `SynthesisError` with invariant id
   `skill_overlay_out_of_lane` if the draft contains a key outside
   the allow-list, or if `recommendation_id` doesn't match a
   mechanical-draft id.
3. Maintain back-compat: drafts that simply *omit* the allow-listed
   fields remain valid (mechanical draft stands).

**Tests.** Six new tests in `test_synthesis_safety_closure.py`:

- `test_skill_overlay_action_edit_rejects`
- `test_skill_overlay_action_detail_edit_rejects`
- `test_skill_overlay_confidence_edit_rejects`
- `test_skill_overlay_daily_plan_id_edit_rejects`
- `test_skill_overlay_unknown_recommendation_id_rejects`
- `test_skill_overlay_review_question_only_allowed_inside_follow_up`

Each asserts atomic rollback: pre and post `_table_counts` identical.

**Files.**

- `src/health_agent_infra/core/synthesis.py`
- `verification/tests/test_synthesis_safety_closure.py`

---

### B3 — Validator hardening (P1)

**Problem.** Both proposal and recommendation validators check that
`rationale` and `uncertainty` are *present*, not that they're
`list[str]`. Confirmed by Codex: a string value passes today. The
banned-token sweep is duplicated across `core/validate.py` and
`core/writeback/proposal.py`; surface flattening is copy-pasted, so
adding a new audit text surface requires lock-step edits.

**Fix.**

1. Extract `_iter_text_surfaces(data, *, surfaces) -> Iterable[str]`
   into a shared module (likely a new
   `core/validate_helpers.py` or extend `core/validate.py`).
2. Both validators call it with their respective surface tuples.
3. Add strict shape checks with new invariant ids:
   - `rationale_list_of_strings` — `rationale` must be `list` whose
     items are all `str`. Empty lists remain valid for defer-only
     proposals and evaluation fixtures; the v0.1.9 contract is type
     safety, not non-empty prose.
   - `uncertainty_list_of_strings` — `uncertainty` must be `list` whose
     items are all `str` (may be empty).
   - `policy_decision_shape` — every `policy_decisions[i]` must be a
     dict with `rule_id: str`, `decision: str`, and optional `note:
     str`. Reject if `note` is non-string.
   - `review_question_string` — `follow_up.review_question`, when
     present, must be a non-empty `str`.

**Tests.** Add to `test_synthesis_safety_closure.py` and
`test_propose_dual_write_contract.py`:

- Each new invariant id gets a positive (rejects bad shape) and
  negative (accepts good shape) test.
- One test asserting both validators reject the same malformed
  payload — pins lockstep behavior.

**Files.**

- `src/health_agent_infra/core/validate.py` — refactor + new checks.
- `src/health_agent_infra/core/writeback/proposal.py` — refactor +
  new checks.
- New tests as above.

---

### B4 — Direct synthesize correctness (P1)

**Problem (4a).** `run_synthesis` only rejects empty proposal sets
(`core/synthesis.py:401`). It does not enforce expected-domain
completeness. The capabilities manifest claims a `proposal_log_has_
row_for_each_target_domain` precondition for `hai synthesize`, but the
runtime doesn't check it. `hai daily` has the gate; direct synthesize
does not.

**Problem (4b).** `run_synthesis` and `build_synthesis_bundle` call
`build_snapshot(conn, as_of_date=for_date, user_id=user_id,
lookback_days=14)` without `evidence_bundle`. Per
`core/state/snapshot.py:383`, `classified_state` only appears when an
evidence bundle is supplied. X1 reads
`sleep.classified_state.sleep_debt_band` first
(`synthesis_policy.py:312`); without the classified bundle it falls
back to a recovery-block echo, which is also absent on a
`build_snapshot` without `evidence_bundle`. Net: direct synthesize can
miss sleep-debt softening/blocking that `hai daily` would apply.

**Fix.**

1. Move the expected-domain gate from `cmd_daily` into `run_synthesis`.
   Accept an optional `expected_domains: frozenset[str]` (default: all
   six v1 domains). Reject with `SynthesisError(invariant=
   "missing_expected_proposals")` listing which domains have no
   canonical-leaf proposal.
2. Reconstruct the classified snapshot inside `build_snapshot` when
   called without `evidence_bundle` by reading the persisted
   `accepted_*_state_daily` rows + running the per-domain classifier
   over them. This makes `build_snapshot` consistently produce a
   `classified_state` block whether the caller supplied an
   `evidence_bundle` or not.
3. Add an ADR at `reporting/plans/v0_1_9/adr_snapshot_consistency.md`
   documenting the choice between (a) reconstructing on-demand from
   accepted rows vs (b) persisting the classified bundle in a new
   table. Decision favors (a) because accepted state is already the
   canonical source of truth; persisting classified bundles would
   create a second source.

**Tests.**

- `test_direct_synthesize_rejects_missing_expected_domain` — seed five
  of six proposals; assert invariant `missing_expected_proposals`.
- `test_direct_synthesize_x1_parity_with_daily` — seed accepted-state
  rows including elevated sleep debt + a hard running proposal; run
  `hai daily` end-to-end and `hai synthesize` directly; assert the
  same Phase A firings (X1a or X1b on running) appear in both
  `daily_plan` rows.
- `test_synthesize_bundle_only_classified_state_present` — assert
  `build_synthesis_bundle` returns a snapshot whose `recovery`,
  `sleep`, etc. blocks include `classified_state`.

**Files.**

- `src/health_agent_infra/core/synthesis.py`
- `src/health_agent_infra/core/state/snapshot.py`
- `src/health_agent_infra/cli.py` (`cmd_daily` simplification —
  delegate to `run_synthesis`'s gate).
- New parity test under `verification/tests/contract/`.
- New ADR.

---

### B5 — Pull/clean provenance + fail-closed (P1)

**Problem (5a).** `hai pull` writes `sync_run_log`
(cli.py:185). `hai daily` calls adapters directly (cli.py:4216) and
bypasses the same provenance path. Source freshness then drifts
between the two entry points.

**Problem (5b).** `_project_clean_into_state` swallows DB projection
failures as warnings (cli.py:808). In `hai daily`, that means planning
can proceed against stale or absent accepted-state rows without the
caller knowing.

**Problem (5c).** `hai clean` invents a fresh `export_batch_id` from
wall-clock time on every projection (cli.py:709). Replaying the same
evidence creates a new raw provenance row each run.

**Problem (5d, mine).** `IntervalsIcuAdapter._fetch_activities_safe`
catches `IntervalsIcuError` and appends to `last_pull_failed_days` but
does not set `last_pull_partial=True`. Running domain reads as
"no sessions today" rather than "sessions unknown".

**Fix.**

1. Compute a deterministic evidence hash at pull time (sha256 of the
   normalized evidence dict). Carry it through `pull → clean →
   project` as the `export_batch_id`. Replays of identical evidence
   become idempotent at the raw-provenance layer.
2. `hai daily` invokes the same `_open_sync_row` /
   `_close_sync_row_*` path that `hai pull` does. Refactor the
   shared logic into a small helper if needed.
3. `_project_clean_into_state` returns a structured
   `ProjectionResult(domains_projected, errors_by_domain)`.
   `cmd_clean` exits `USER_INPUT` (or a new `INTERNAL_DEGRADED` if
   we want a separate code) when any domain failed. `cmd_daily`
   refuses to proceed when projection had errors, surfacing the
   per-domain error list.
4. Set `self.last_pull_partial = True` in
   `IntervalsIcuAdapter._fetch_activities_safe` when activities fetch
   fails.

**Tests.**

- `test_clean_idempotent_on_replay` — clean the same evidence twice;
  assert one raw provenance row, not two.
- `test_clean_projection_failure_fails_closed` — inject a projection
  failure; assert `cmd_clean` exits non-OK and `cmd_daily` refuses to
  plan.
- `test_daily_writes_sync_run_log` — assert a `hai daily` run produces
  a `sync_run_log` row with the same shape as `hai pull` does.
- `test_intervals_icu_activities_failure_flags_partial` — replay
  client raises on activities; assert `last_pull_partial=True` and
  the failure sentinel is in `last_pull_failed_days`.

**Files.**

- `src/health_agent_infra/core/pull/intervals_icu.py`
- `src/health_agent_infra/cli.py` (`cmd_pull`, `cmd_clean`,
  `cmd_daily`, `_project_clean_into_state`)
- New tests across pull, clean, daily.

---

### B6 — Safety skill prose update (P1)

**Problem.** `skills/safety/SKILL.md` says:

- "**Not nutrition advice.** ... you do not recommend calories,
  macros, or timing." — But the shipped nutrition action enum
  (`maintain_targets`, `increase_protein_intake`, `increase_hydration`,
  `reduce_calorie_deficit`) emits exactly those bounded macro
  recommendations.
- "If the policy layer emits any `block` decision, the final action
  must be `defer_decision_insufficient_signal` with `{"reason":
  "policy_block"}`." — But X-rule block-tier firings (X1b, X3b, X6b)
  can escalate, and R6 (recovery RHR-spike) escalates too.

The first claim contradicts the shipped product; the second
conflates R-rule coverage-blocks with X-rule block tiers and ignores
escalation entirely.

**Fix.** Rewrite the relevant SKILL.md sections to say:

1. **Nutrition.** The system does not recommend medical nutrition
   advice (clinical macros for therapeutic protocols, supplementation,
   timing strategies for medical conditions). It DOES emit bounded
   wellness-level macro alignment within the v1 nutrition action enum
   (protein, hydration, calorie deficit). The line is "wellness
   bounded by the user's own targets" vs "clinical prescription".
2. **Block tier.** Distinguish:
   - R-rule coverage block (`require_min_coverage`) → defer with
     `defer_decision_insufficient_signal`.
   - X-rule block tier (X1b, X3b, X6b) → escalate to
     `escalate_for_user_review` (or domain-specific escalate action).
   - R6 RHR-spike → escalate.
3. Update the "Audit expectations" section to reference the
   six-domain `policy_decisions[]` shape, not just R1-R6 (which are
   recovery-only).

**Tests.**

- `test_safety_skill_prose_matches_shipped_actions` — assert every
  action token mentioned in `skills/safety/SKILL.md` exists in the
  union of v1 action enums per `core/validate.py`. (Catches future
  drift in the same direction.)

**Files.**

- `src/health_agent_infra/skills/safety/SKILL.md`
- `verification/tests/test_safety_skill_prose.py` — new.

---

### B7 — v0.1.9 cycle scaffolding (this file)

This document. Lands first as a draft; updates as audit rounds run.

---

### B8 — P2 hygiene batch

Bundled small fixes:

- **#12 data_quality coverage_band null** — feed full classified
  snapshot to `data_quality_daily` projection. Trivial after B4
  (snapshot is consistently classified).
- **#13 README daily provenance** — narrow wording until B5 lands;
  swap to the strong claim once daily writes `sync_run_log`.
- **#14 Phase B coverage test** — `test_every_phase_b_rule_has_targets`
  in `test_synthesis_policy.py`.
- **#15 Pull→clean shape validator** — `validate_pulled_evidence` at
  the `cmd_clean` boundary. Bundles with B5's evidence-hash work.
- **#16 Dead code in `_nutrition_deficit_and_protein`** — collapse
  the helper into `evaluate_x2` or make the helper actually compute
  the fallback.
- **#17 Skill-CLI drift validator inline-backtick coverage** —
  extend `scripts/check_skill_cli_drift.py`.
- **#19 README "How daily completes" promotion** — move above install.
- **#20 `verification/COVERAGE.md`** — invariant-id-keyed coverage map.

Deferred to v0.2:

- **#18 cli.py split.** AGENTS.md W29 says deferred. Reflag in v0.2
  retro.
- **#21 RAW_DAILY_ROW_COLUMNS Garmin coupling.** Not unblocking; new
  pull adapter is a v0.2 product decision per `non_goals.md`.

---

## 3. Deferred roadmap items

These remain post-v0.1.9 work even though the multi-release roadmap
originally named them for v0.1.9:

- **W52: `hai review weekly`** — code-owned weekly aggregation.
- **W53: Insight proposal ledger** — `insight_proposal` + `insight`
  tables.
- **W58: LLM-judge factuality gate** — Prometheus-2-7B pinned by SHA.

They stay tracked from `multi_release_roadmap.md § 4 v0.1.9` and the
backlog, but this hardening release does not implement them.

---

## 4. Acceptance criteria

The cycle ships when:

1. All B1-B6 tests are green.
2. The capabilities manifest and the `agent_safe` posture for the four
   W57 handlers (intent/target × commit/archive) match.
3. `hai daily` and `hai synthesize` produce identical Phase A
   firings against the same persisted state in the parity test.
4. `hai clean` on the same evidence twice produces one raw
   provenance row, not two.
5. Codex audit round 1 returns `SHIP_WITH_NOTES` or better against the
   prompt at `reporting/plans/v0_1_9/codex_audit_prompt.md` (to be
   drafted after implementation).
6. `RELEASE_PROOF.md` lands with the post-implementation evidence.

---

## 5. Implementation order

```
B7 (this file)  ──┐
B1 (W57 closure) ─┼─ batch 1 (low risk, governance-critical)
B2 (overlay)     ─┘
B3 (validators)  ─── batch 2 (refactor + new shape checks)
B4 (synthesize)  ─┐
B5 (pull/clean)  ─┼─ batch 3 (correctness — needs ADR for B4)
B6 (safety prose)─┘
B8 (hygiene)     ─── batch 4 (after B4 + B5 land)
```

W52/W53/W58 land in their own commits *after* the cycle's hardening
work passes Codex review.
