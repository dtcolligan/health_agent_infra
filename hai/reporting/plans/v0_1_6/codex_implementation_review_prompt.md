# Codex Implementation Review — v0.1.6

> **Why round 3.** Round 1 audited the wrong branch (`main`). Round
> 2 validated the cross-checked findings on the correct branch
> (`v0.1.4-release`) and added 7 new structural findings. Round 3
> reviews the **implementation**: 13 workstreams shipped against the
> consolidated punch list. Your job is to confirm each fix delivers
> what it claims, find regressions or new bugs introduced by the
> changes, and surface anything the implementation overlooked.
>
> This is not another audit pass. It is a ship-readiness review of a
> ~1100-line diff against a specific punch list.

---

## Step 0 — Confirm you're in the right tree (again)

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: v0.1.4-release
git log --oneline -1
# expect: ff77aff v0.1.5: sync release QA + handoff docs to v0.1.5 reality
git status --short | head -20
# expect: ~14 modified + ~5 new untracked files in
#         src/, safety/tests/, scripts/, reporting/plans/v0_1_6/
```

If any of those don't match, **stop and surface the discrepancy**.

## Step 1 — Read the artifacts in order

All four artifacts are in `reporting/plans/v0_1_6/`. Read them in
this order so the implementation makes sense:

1. **`codex_audit_response_round2.md`** — your round-2 findings on
   `v0.1.4-release`. The 19-item punch list at the bottom is what the
   implementation targeted.
2. **`internal_audit_response.md`** — the maintainer's parallel
   audit + the "Reconciliation: maintainer's draft `PLAN.md` vs this
   audit" table.
3. **`PLAN.md`** — the consolidated v0.1.6 plan. Section 7 ("Round-2
   audit integration — final consolidated plan") is the merged plan.
   Section 6 ("Implementation log") at the bottom is the
   workstream-by-workstream commit log of what was actually shipped
   today, with file:line citations for each change.
4. **`codex_audit_prompt_round2.md`** — the round-2 brief, for
   structural reference.

## What was shipped (recap from the implementation log)

Thirteen workstreams landed today on `v0.1.4-release`. Each addresses
one or more findings from your round-2 punch list:

- **W11** (Codex B2 / "[P0] File-backed JSON args can throw
  tracebacks"): `_load_json_arg` helper at `cli.py:111`; 6 call
  sites migrated (incl. `cmd_pull` + `cmd_clean` you flagged as
  missed); top-level `main()` exception guard at `cli.py:5712`.
  +13 regression tests in `safety/tests/test_cli_json_arg_handling.py`.
- **W12** (Codex B3 / "[P0] hai review record can fork truth"):
  `core/writeback/outcome.py` — new `validate_review_outcome_dict`
  with 11 named invariants; strict-bool check on
  `followed_recommendation`; CLI rejects with
  `invariant=followed_recommendation_must_be_bool` before any write.
  +36 regression tests in `safety/tests/test_review_outcome_validation.py`.
- **W10 + W4** (Codex B1 / "[P0] hai daily accepts partial-domain
  proposal sets"): `cli.py:3494` — gate flipped from
  `bool(proposals)` to `not missing_expected`; three statuses
  (awaiting_proposals / incomplete / complete); the locking test at
  `safety/tests/test_cli_daily.py:272` was flipped from "asserts
  subset is complete" to "asserts subset is incomplete"; happy-path
  companion added; `--domains` help text rewritten.
- **W2** (Codex B6 / "[P1] hai intake gaps misleading zero"):
  `cmd_intake_gaps` refuses without `--evidence-json`; OK path emits
  `"computed": true`. New regression test.
- **W7** (Codex F3 / "[P1] --base-dir required across agent-facing
  write commands"): `core/paths.py` — `DEFAULT_BASE_DIR` +
  `resolve_base_dir`; 11 argparse declarations + 11 handler call
  sites migrated. +8 regression tests in
  `safety/tests/test_default_base_dir.py`.
- **W3 + W18** (Codex B7 / "[P1] Skill/docs commands drift from
  parser reality"): `scripts/check_skill_cli_drift.py` validator;
  `safety/tests/test_skill_cli_drift.py` wires it as CI gate;
  fixed intent-router (review-record + memory-list) and reporting
  skill (`--since`) drift.
- **W1** (Codex B5 / "[P1] hai state reproject can violate FK"):
  `core/state/projector.py` — `ReprojectOrphansError` +
  `cascade_synthesis` parameter; CLI `--cascade-synthesis` flag;
  +3 regression tests appended to
  `safety/tests/test_reproject_proposal_recovery.py`.
- **W13** (Codex B4 / "[P1] hai synthesize --bundle-only bypasses
  no-proposals contract"): bundle-only refuses when `proposal_log`
  has no rows for `(for_date, user_id)`. +1 regression test.
- **W15** (Codex C2 / "[P1] cmd_propose can report success after
  JSONL append while projection silently failed"): `cmd_propose`
  no longer routes through `_dual_write_project`; does its own
  projection inline; `ProposalReplaceRequired` is fatal USER_INPUT;
  any other projection failure is fatal INTERNAL with a
  "JSONL durable, run reproject" stderr; new `db_projection_status`
  field on stdout payload. +3 regression tests in
  `safety/tests/test_propose_dual_write_contract.py`.
- **W17** (Codex C4 / "[P1] expert-explainer permits arbitrary
  python3 -c"): new `hai research topics` + `hai research search
  --topic <t>` (read-only, agent-safe); `Bash(python3 -c *)`
  removed from `expert-explainer`'s allowed-tools; skill body
  rewritten to use the new CLI. +6 regression tests.
- **W19** (Codex C6 / "[P2] Reproject determinism overstated"):
  contract description updated to "deterministic modulo projection
  timestamps."
- **W20** (Codex C7 / "[P2] Migration gap detection can miss absent
  lower migrations"): `applied_schema_versions` +
  `detect_schema_version_gaps` in `core/state/store.py`;
  `hai doctor` surfaces gaps as warn ahead of legacy
  "pending migrations" check. +5 regression tests.
- **W5** (Codex F2 / "[P1] intervals.icu/Garmin default story not
  aligned"): `_resolve_pull_source` now defaults to `intervals_icu`
  when credentials are configured (else `csv`); `--live` and
  `--source` help text updated; 1 existing test renamed + flipped,
  1 new test for the no-auth fallback path.
- **W9** (Codex F1 / "[P2] README/tour/integration docs need a
  final post-fix sweep"): three new README sections — "Where your
  data lives," "How `hai daily` actually completes," "Calibration
  timeline" (with cold-start asymmetry doc folded in). Install +
  "Recording your day" rewritten to reflect intervals.icu default,
  optional `--base-dir`, nutrition daily-total semantics,
  planned-session vocabulary, strict-bool review payload requirement.

**Test count:** 1844 → 1921 (+77 new tests, 4 skipped). All passing.

## Your scope this round

### Job A — Per-workstream verification

For each workstream above, verify the implementation actually
delivers what it claims:

- The cited file:line shows the change.
- The change matches the documented behaviour.
- The regression test(s) cited actually pass on `v0.1.4-release`.
- The change does not regress anything else.

If a workstream's claim is overstated or under-delivers, say so
explicitly with file:line evidence.

### Job B — Find new bugs the diff introduced

A 1124-line diff has surface area. Look for:

- **API contract regressions.** Did any agent-facing behaviour silently
  change in a way the docs / capabilities manifest doesn't describe?
- **Test-flip correctness.** The B1 fix flipped a locking test
  (`test_cli_daily.py:272`). Verify the new assertion actually pins
  the new behaviour, not just any behaviour. Same for the W5 test
  rename.
- **Default changes that may surprise.** W5 flipped the `hai pull`
  default from `csv` to `intervals_icu` (when auth configured);
  W7 flipped `--base-dir` from required to optional. Are there
  callers / docs / tests that assumed the old defaults and silently
  changed semantics?
- **Cross-workstream interactions.** W10 (proposal-completeness gate)
  + W13 (bundle-only refusal) + W15 (cmd_propose dual-write contract)
  all touch the synthesis path. Are their semantics consistent?
- **`main()` exception guard scope.** W11 added the guard. Verify it
  doesn't swallow exceptions that the codebase expects to propagate
  (e.g. `argparse.ArgumentError`, `SystemExit`). The implementation
  passes `SystemExit` through unchanged and treats `KeyboardInterrupt`
  as USER_INPUT — confirm that's correct.
- **The new `hai research` surface.** W17 added two new agent-safe
  commands. Verify the capabilities manifest reflects them, the
  retrieval boundary is actually local-only (no `import urllib`
  paths leaking), and the privacy invariants on `RetrievalQuery`
  are honoured.

### Job C — Find what's still missing

The implementation log calls out workstreams deferred to v0.1.7 (W6,
W8, W14 deeper, W16). For each deferred item, judge whether the
deferral is reasonable or whether it should ship in v0.1.6. Also
look for:

- **Things both audits + the implementation missed.** Walk the
  `cli.py` diff. Any new code path with no test coverage? Any
  invariant claim in the diff comments that isn't enforced by
  validation?
- **Test gaps in the new code.** The 5 new test files cover the
  documented behaviours. Are there edge cases (e.g. a
  `--cascade-synthesis` with no JSONL files) that aren't covered?
- **Documentation drift introduced.** The README rewrite is large.
  Any inconsistency between the README and the actual CLI / capabilities
  manifest? Any claim in the README that doesn't match the
  shipped tests?
- **Capabilities manifest correctness.** The contract doc was
  regenerated twice (after W17 added `hai research`, and after W19
  changed the reproject description). Verify
  `reporting/docs/agent_cli_contract.md` matches what
  `hai capabilities --markdown` emits today.

### Non-goals

- Don't re-audit the codebase from scratch — your round-2 report is
  the baseline.
- Don't propose new workstreams beyond what's needed to ship v0.1.6
  (anything larger goes to "deferred to v0.1.7" in your output).
- Don't suggest cosmetic refactors with no behavioural impact.
- Don't request unrelated test coverage expansions outside the
  v0.1.6 surface.

## Output format

Save your response to:

**`reporting/plans/v0_1_6/codex_implementation_review_response.md`**

Structure (sections in this order; "No findings" is acceptable for
any section that genuinely has none):

```markdown
# Codex Implementation Review — v0.1.6 Response

## Step 0 confirmation
<branch + commit + working-tree shape you saw>

## Per-workstream verification (Job A)

For each workstream W1, W2, W3+W18, W4, W5, W7, W9, W10, W11, W12,
W13, W15, W17, W19, W20:

### W<N>. <one-line summary>
Status: VERIFIED / OVERSTATED / UNDER-DELIVERED / REGRESSION_INTRODUCED
Evidence: <file:line you actually looked at>
Notes: <one or two sentences if needed>

## New bugs introduced (Job B)
For each: severity, evidence (file:line), recommended fix, effort
(S/M/L), risk if shipped.

## Things still missing (Job C)
Gaps in the implementation that v0.1.6 should still close before
shipping. Same shape as Job B findings.

## Deferred items — agree or disagree
For each of W6, W8, W14 (deeper), W16: agree with deferral / push to
ship in v0.1.6 with rationale.

## Documentation / capabilities-manifest correctness
Specific drifts between README, contract doc, skills, and the actual
CLI surface as it exists today.

## Ship verdict
A single line: `SHIP / SHIP_WITH_FIXES / DO_NOT_SHIP`. If
`SHIP_WITH_FIXES`, list the must-fix items with severity.
```

## Tone

Same as round 2: direct, file:line cited, "uncertain" or
"DEFERRED — DIDN'T INVESTIGATE" when you can't verify, no hedging
theatre. The maintainer is going to commit + tag v0.1.6 off the back
of this; be wrong out loud rather than vaguely defensible.

## Closing

Round 3 is the final review before commit. Anything that should
block the v0.1.6 tag goes in "Ship verdict." Anything else is for
v0.1.7 follow-up.
