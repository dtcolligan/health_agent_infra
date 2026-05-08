# Codex Implementation Review — v0.1.9 Hardening Cycle

> **Why this round.** v0.1.9 is a hardening cycle, not a feature
> cycle. It was driven by two parallel ultra-reviews (yours +
> Claude's, both run 2026-04-26) that surfaced overlapping P0/P1
> findings against the v0.1.8-shipped surface. The maintainer
> implemented the merged finding set in one session across eight
> batches (B1–B8). Implementation is complete in the working tree
> but **not committed**. Your job is to confirm each fix delivers
> what it claims, find regressions or new bugs introduced by the
> ~1.4kloc of changes, and surface anything the implementation
> overlooked. Verdict gates the commit.
>
> This is not another audit pass. It is a ship-readiness review of
> a specific punch list against an uncommitted working tree.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main
git log --oneline -1
# expect: 04a3d31 docs: sharpen public project presentation
git status --short | wc -l
# expect: ~22 lines (modified + new files across src/, verification/tests/, reporting/, docs)
ls reporting/plans/v0_1_9/
# expect: BACKLOG.md, PLAN.md, codex_audit_prompt.md (this file)
```

If any don't match, **stop and surface the discrepancy**. Ignore
`/Users/domcolligan/Documents/health_agent_infra/`.

## Step 1 — Read the artifacts

In order:

1. **`reporting/plans/v0_1_9/PLAN.md`** — the cycle plan. § 1
   ("Audit integration") names what each parallel review caught;
   § 2 ("Workstream catalogue") gives the per-batch contract,
   files touched, and acceptance tests; § 4 names the cycle's
   acceptance criteria.
2. **`reporting/plans/v0_1_9/BACKLOG.md`** — items deferred from
   v0.1.8 + roadmap-committed items. v0.1.9 explicitly does NOT
   close W52 / W53 / W58 (those land after the hardening batches
   pass review).
3. **`reporting/plans/v0_1_8/codex_implementation_review_response_round4.md`**
   — your last v0.1.8 review (verdict was SHIP). v0.1.9 builds on
   that baseline; nothing v0.1.8-shipped should regress.
4. **`AGENTS.md`** — the operating contract. § "Governance
   Invariants" calls out W57 explicitly (v0.1.9 B1 closes the
   archive-side leak). § "Settled Decisions" names what stays
   deferred (cli.py split, RAW_DAILY_ROW_COLUMNS coupling).
5. **`reporting/docs/non_goals.md`** — anchors v0.1.9's scope
   discipline. The cycle adds NO new features; it only tightens.

## What was shipped (recap from the cycle plan)

Eight batches landed today on `main` (uncommitted). Each addresses
findings from the merged review:

- **B1 (W57 closure on archive + commit handlers)** — Codex's
  flagship P0. Pre-v0.1.9 `hai intent archive` and `hai target
  archive` were `agent_safe=True` and could deactivate active
  user-state rows directly via `UPDATE status='archived'`,
  violating AGENTS.md W57. Fixed: both flipped to
  `agent_safe=False`; new `_w57_user_gate` runtime helper at
  `cli.py:2198` adds a stdin-tty / `--confirm` gate to all four
  W57 handlers (intent commit, intent archive, target commit,
  target archive); `--confirm` flag added to all four parsers;
  manifest descriptions updated to call out W57. Tests:
  `verification/tests/contract/test_w57_runtime_gate.py`
  (10 new). Existing 4 ledger tests updated to pass `--confirm`.
- **B2 (skill overlay fail-loud)** — both reviews flagged. Pre-
  v0.1.9 `_overlay_skill_drafts` silently dropped attempts to
  edit `action` / `action_detail` / `confidence` /
  `daily_plan_id`. Fixed: now raises
  `SynthesisError(invariant="skill_overlay_out_of_lane")` BEFORE
  the transaction opens, on any out-of-lane key, unknown
  `recommendation_id`, or runtime-owned follow_up field. Atomic
  rollback by construction. Tests: 7 new in
  `verification/tests/test_synthesis_safety_closure.py`. One
  pre-existing test that pinned the fail-soft contract was
  inverted.
- **B3 (validator hardening)** — Codex caught: validators
  accepted `rationale="raw string"` (not `list[str]`). Claude
  caught: the banned-token sweep was duplicated across
  `core/validate.py` and `core/writeback/proposal.py`. Fixed:
  shared `iter_text_surfaces` + `check_banned_tokens_in_surfaces`
  helpers; new strict shape checks `rationale_list_of_strings`,
  `uncertainty_list_of_strings`, `policy_decision_shape`,
  `review_question_string`. Both validators call the same
  helpers. Empty rationale lists remain valid (defer-only
  proposals, eval fixtures); type-safety is the contract, not
  non-empty. Tests:
  `verification/tests/test_validator_shape_hardening.py`
  (18 new).
- **B4 (direct synthesize correctness)** — Codex's two parity
  findings.
  - 4a: `run_synthesis` only refused on zero proposals; could
    commit a partial-domain plan despite the manifest's
    `proposal_log_has_row_for_each_target_domain` precondition.
    Fixed: `run_synthesis(expected_domains=...)` parameter;
    `cmd_synthesize` defaults to v1 six-domain set;
    `--domains ''` opts out (matches pre-v0.1.9 permissive
    behaviour for tests). Invariant id:
    `missing_expected_proposals`.
  - 4b: `build_snapshot` only populated `classified_state` when
    given an `evidence_bundle`. Direct `hai synthesize` (no
    bundle) saw bare per-domain blocks; X1 read
    `sleep.classified_state.sleep_debt_band` and silently no-op'd
    on the direct path. Fixed: classify+policy now run on every
    snapshot regardless of bundle presence. Without a bundle,
    `cleaned`/`raw_summary` default to empty dicts, classifiers
    degrade individual bands to `unknown` for ratio-dependent
    fields, but `classified_state` + `policy_result` are always
    populated. `evidence` + `raw_summary` keys are only attached
    when the caller actually supplied them — audit honesty.
    Tests:
    `verification/tests/contract/test_b4_synthesize_parity.py`
    (6 new). Five pre-existing snapshot-shape tests updated for
    the new always-classified contract.
- **B5 (pull/clean provenance)** — Codex's three provenance
  findings + Claude's intervals.icu activities flag.
  - 5a: `hai daily` bypassed `sync_run_log`. Fixed:
    `_daily_pull_and_project` now calls `_open_sync_row` /
    `_close_sync_row_*` the same way `cmd_pull` does;
    `_run_first_pull_backfill` had its redundant sync-row
    management removed (the helper now owns it).
  - 5b: `_project_clean_into_state` swallowed DB failures as
    warnings. Fixed: now returns
    `{status, export_batch_id, error, error_type}`; `cmd_clean`
    exits `INTERNAL` on projection failure; `cmd_daily` raises
    `RuntimeError` and surfaces the failure as a `failed` clean
    stage with `INTERNAL` exit.
  - 5c: `hai clean` minted a fresh wall-clock `export_batch_id`
    per run. Fixed: new `_evidence_hash(raw_row, activities)` →
    `sha256(canonical_json)[:16]`. Replays of identical evidence
    produce identical `source_daily_garmin` rows.
  - 5d: intervals.icu adapter swallowed `/activities` errors but
    didn't set `last_pull_partial=True`. Fixed.
  - Tests: `verification/tests/test_b5_pull_clean_provenance.py`
    (6 new). Three pre-existing `test_state_clean_projection.py`
    tests updated to assert fail-closed.
- **B6 (safety skill prose)** — Codex caught: SKILL.md said "no
  nutrition advice" while nutrition v1 emits bounded macro
  actions; said "any policy block must defer" while X-rule block
  tier escalates. Fixed: rewrote the relevant sections in
  `src/health_agent_infra/skills/safety/SKILL.md` to distinguish
  R-rule coverage block (→ defer) from X-rule block tier
  (→ escalate), and medical nutrition advice (refused) from
  bounded macro alignment within the v1 nutrition action enum
  (in scope).
- **B7 (PLAN.md)** — `reporting/plans/v0_1_9/PLAN.md` written
  with the unified scope reconciling both reviews.
- **B8 (P2 hygiene)** — Phase B coverage test in
  `test_synthesis_policy.py` asserts every `PHASE_B_EVALUATORS`
  entry has a `PHASE_B_TARGETS` registry row. Dead code in
  `_nutrition_deficit_and_protein` removed. README's "How
  `hai daily` actually completes" promoted above install + tightened
  with v0.1.9 fail-closed wording.

**Test count.** 2089 passed (start of session) → 2127 passed,
2 skipped. +38 net new tests, all green.

**Files touched.** 9 source files, 6 test files (3 updated +
3 new), 1 SKILL.md, 1 README, 1 contract doc regenerated, 1
new PLAN.md, 4 new test files (2 in `contract/`, 2 at top
level).

## Your scope this round

### Job A — Per-batch verification

For each batch B1–B8, verify the implementation actually delivers
what it claims:

- The cited file:line shows the change.
- The change matches the documented behaviour.
- The regression test(s) cited actually pass.
- The change does not regress anything else.

If a batch's claim is overstated or under-delivers, say so
explicitly with file:line evidence.

Specific contract checks worth scrutinizing:

- **B1 — W57 runtime gate semantics.** `_w57_user_gate` accepts
  `--confirm` OR interactive stdin (`sys.stdin.isatty()`). Is
  this the right contract for a single-user local-first system,
  or should it be stricter (e.g. always require `--confirm`,
  even from a tty)? Verify the manifest descriptions match the
  runtime behaviour. Confirm there's no regression in
  `cmd_intent_supersede` / `cmd_target_supersede` (those were
  not in B1 scope — should they have been? supersede of an
  active row arguably is also W57-affected).
- **B2 — fail-loud reject scope.** The new gate rejects on
  `action`, `action_detail`, `confidence`, `daily_plan_id`,
  `policy_decisions`, `bounded`, `schema_version`, etc. — i.e.
  every key NOT in the allow-list. Verify this matches the
  agent contract documented in `daily-plan-synthesis/SKILL.md`.
  Specifically: is `recommendation_id` correctly in the
  allow-list as a match key (and not editable)? Is the
  unknown-`recommendation_id` rejection correct, or should
  unknown drafts be allowed-and-ignored (the pre-v0.1.9
  contract)?
- **B3 — empty rationale.** I deliberately allowed empty
  `rationale=[]` because (a) Codex asked for type safety not
  non-empty, (b) eval-runner fixtures rely on it, (c) defer-only
  proposals legitimately omit rationale. Push back if you think
  non-empty should be the contract — but if so, name how the
  eval runner should adapt.
- **B4 — `classified_state` always present.** Pre-v0.1.9 the
  presence of `classified_state` was a signal "evidence was
  supplied." Now it's always present. Are there callers (skills,
  reporting modules, `hai today` rendering, `hai stats`) that
  used `"classified_state" in block` as an evidence-presence
  check? Walk the diff for any false-positive that this change
  introduces. Also verify the X1 / X2 / X3 / X4 / X5 / X6 / X7 /
  X9 actually fire identically across `hai daily` and direct
  `hai synthesize` for matching state — the parity test only
  pins one case.
- **B5 — evidence hash collision risk.** `_evidence_hash` takes
  `sha256(canonical_json)[:16]`. 16 hex chars = 64 bits.
  Birthday-collision risk over a single user's lifetime is
  vanishingly small, but verify there's no documented
  expectation that `export_batch_id` is unique across users or
  globally. Also: does `json.dumps(..., default=str)` produce
  truly canonical output, or are there datetime / Decimal /
  custom-type edge cases that could make two
  semantically-identical pulls hash differently?
- **B5 — `_daily_pull_and_project` raises `RuntimeError` for
  projection failure** (not a typed exception). The handler
  catches it and emits `INTERNAL`. Is `RuntimeError` the right
  type, or should this be a domain-specific exception? Confirm
  no other `RuntimeError` from a different code path could be
  misclassified as a clean-projection failure.
- **B6 — safety SKILL.md changes.** Verify the new prose is
  consistent with what the recovery / running / sleep / strength
  / stress / nutrition skills actually emit. Specifically: does
  the "X-rule block tier replaces action with escalate" claim
  hold for X1b / X3b / X6b, or does the actual block-tier
  mutation differ across those rules?
- **B8 — Phase B coverage test.** Verify the test would actually
  fail if a hypothetical new Phase B rule landed without a
  `PHASE_B_TARGETS` entry — i.e. the test logic isn't accidentally
  satisfied by today's single-rule state.

### Job B — Find new bugs the diff introduced

A ~1.4kloc diff has surface area. Look for:

- **Manifest drift.** Two regenerations of
  `reporting/docs/agent_cli_contract.md` (after B1 and B4). Verify
  the committed doc matches `hai capabilities --markdown` today,
  and that the new `--confirm` flags + `--domains` flag on
  `hai synthesize` render correctly.
- **Test-flip correctness.** B2 inverted
  `test_synthesize_ignores_skill_attempt_to_change_action`;
  B5 flipped three `test_state_clean_projection.py` tests from
  `rc == 0` to `rc == INTERNAL`; B4 updated five snapshot-shape
  tests. Verify each flip pins the new behaviour, not "any
  behaviour."
- **Default changes that may surprise.** B4's
  `cmd_synthesize` change makes `hai synthesize` (no
  `--domains`) require all six v1 domain proposals. Pre-v0.1.9
  it accepted any non-zero proposal set. Are there test
  fixtures, eval scenarios, or doc examples that assumed the
  old permissive behaviour and silently break under v0.1.9?
  (The eval runner calls `run_synthesis` directly with
  `expected_domains=None` — that path is preserved. The CLI
  path is the one that changed.)
- **Cross-batch interactions.** B2 (overlay fail-loud) +
  B3 (validator shape) + B4 (always-classified snapshot) all
  touch the synthesis path. Are their semantics consistent?
  Specifically: does B3's strict `rationale_list_of_strings`
  on the recommendation surface trip on the mechanical-draft
  path when the proposal had `rationale=[]`?
- **Sync-row symmetry.** B5 wired `_daily_pull_and_project`
  through `_open_sync_row` / `_close_sync_row_*`. Confirm the
  call signatures match `cmd_pull`'s usage exactly — same
  `mode` values, same `source` labels, same close-counts
  semantics. The `_run_first_pull_backfill` change removed its
  own sync-row management; verify nothing else depends on the
  prior dual-row behaviour.
- **`build_snapshot` import cycles.** B4 widened the always-run
  classify+policy block. The runtime-package imports are still
  inside the `if True:` block (deliberately — comment cites the
  cycle). Verify there's no new import path that triggers a
  cycle when `build_snapshot` is called from a context that
  pre-v0.1.9 stayed at the v1.0 minimal shape.
- **`_w57_user_gate` reachability.** Verify the gate fires
  consistently — i.e. there's no code path that calls
  `commit_intent` / `commit_target` / `archive_intent` /
  `archive_target` directly (bypassing `cmd_intent_*` / 
  `cmd_target_*`). The `core/intent/store.py` and
  `core/target/store.py` functions are still public; if any
  test or other CLI handler calls them directly, the gate is
  bypassed.

### Job C — Find what's still missing

The cycle plan deferred several items to v0.2 (cli.py split,
RAW_DAILY_ROW_COLUMNS coupling) and skipped a few P2 items
(coverage map, drift validator inline-backtick coverage, pull→clean
shape validator). Judge whether each deferral is reasonable, or
whether it should ship in v0.1.9.

Also look for:

- **Things both reviews + the implementation missed.** Walk the
  diff. Any new code path with no test coverage? Any invariant
  claim in a comment that isn't enforced by validation?
- **Test gaps in new code.** The 4 new test files cover the
  documented behaviours. Are there edge cases (e.g.
  `_w57_user_gate` with both `--confirm` and a tty, or
  `_evidence_hash` with raw_row containing a non-JSON-safe
  object) that aren't covered?
- **Documentation drift.** README's "How `hai daily` actually
  completes" was rewritten. Any inconsistency between the new
  README wording and the actual CLI / capabilities manifest?
- **Capabilities manifest correctness.** The four W57 handlers'
  manifest descriptions changed. Verify
  `reporting/docs/agent_cli_contract.md` matches what
  `hai capabilities --markdown` emits today.

### Non-goals

- Don't re-audit v0.1.8-shipped work — your r4 review is the
  baseline.
- Don't propose new workstreams beyond what's needed to ship
  v0.1.9 (anything larger goes to v0.2 in your output).
- Don't suggest cosmetic refactors with no behavioural impact.
- Don't request unrelated test coverage expansions outside the
  v0.1.9 surface.
- Don't push to ship roadmap-committed items (W52 / W53 / W58)
  in v0.1.9 — they land post-hardening.

## Output format

Save your response to:

**`reporting/plans/v0_1_9/codex_audit_response.md`**

Structure (sections in this order; "No findings" is acceptable
for any section that genuinely has none):

```markdown
# Codex Implementation Review — v0.1.9 Response

## Step 0 confirmation
<branch + commit + working-tree shape you saw>

## Per-batch verification (Job A)

For each of B1, B2, B3, B4, B5, B6, B7, B8:

### B<N>. <one-line summary>
Status: VERIFIED / OVERSTATED / UNDER-DELIVERED / REGRESSION_INTRODUCED
Evidence: <file:line you actually looked at>
Notes: <one or two sentences if needed>

## New bugs introduced (Job B)
For each: severity (P0/P1/P2), evidence (file:line), recommended
fix, effort (S/M/L), risk if shipped without fix.

## Things still missing (Job C)
Gaps in the implementation that v0.1.9 should still close before
shipping. Same shape as Job B findings.

## Deferred items — agree or disagree
For each of the cycle's deferred items (cli.py split, RAW_DAILY_ROW_COLUMNS
coupling, COVERAGE.md, pull→clean shape validator, drift validator
inline-backtick coverage): agree with deferral / push to ship in
v0.1.9 with rationale.

## Documentation / capabilities-manifest correctness
Specific drifts between README, contract doc, skills, AGENTS.md,
and the actual CLI surface as it exists today.

## Cross-batch consistency check
B2 + B3 + B4 all touch the synthesis path. Are their semantics
consistent? B5 + B1 both add runtime gates — same posture? Call
out any interaction that surprised you.

## Ship verdict
A single line: `SHIP / SHIP_WITH_FIXES / DO_NOT_SHIP`. If
`SHIP_WITH_FIXES`, list the must-fix items with severity.
```

## Tone

Same as round 4 of v0.1.8: direct, file:line cited, "uncertain"
or "DEFERRED — DIDN'T INVESTIGATE" when you can't verify, no
hedging theatre. The maintainer is going to commit + tag v0.1.9
off the back of this; be wrong out loud rather than vaguely
defensible.

## Closing

This round gates the v0.1.9 commit. Anything that should block
goes in "Ship verdict." Anything else is for v0.2 follow-up.
The roadmap-committed items (W52 weekly review, W53 insight
ledger, W58 LLM-judge factuality) land in their own commits
after this audit passes.
