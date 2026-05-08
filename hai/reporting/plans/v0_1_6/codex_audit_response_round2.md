# Codex Audit — Round 2 Response

## Step 0 confirmation

Confirmed before auditing:

- `pwd`: `/Users/domcolligan/health_agent_infra`
- `git branch --show-current`: `v0.1.4-release`
- `git log --oneline -1`: `ff77aff v0.1.5: sync release QA + handoff docs to v0.1.5 reality`

I ignored `/Users/domcolligan/Documents/health_agent_infra/`.

One requested artifact was unavailable in this checkout: the brief asks for the prior round-1 response as one of the inputs, but `reporting/plans/v0_1_6/` contains `PLAN.md`, `codex_audit_prompt.md`, `codex_audit_prompt_round2.md`, and `internal_audit_response.md`, not `codex_audit_response.md`; `find reporting -name '*audit*response*.md'` found only `reporting/plans/v0_1_6/internal_audit_response.md`. I audited against the round-2 brief's enumerated B1-B7 claims instead (`reporting/plans/v0_1_6/codex_audit_prompt_round2.md:111-141`).

## Validation of internal audit's reproductions (Job A)

### B1. hai daily partial-domain gate

Status: REPRODUCED

Evidence: `cmd_daily` computes `present_domains` and `missing_expected`, but the actual gate is still `gate_ok = bool(proposals)` and the status is `"complete"` whenever any proposal exists (`src/health_agent_infra/cli.py:3490-3502`). The no-proposal path is the only blocked path (`src/health_agent_infra/cli.py:3503-3514`). The `--domains` help says it filters proposal-gate reporting; it does not make synthesis a scoped operation (`src/health_agent_infra/cli.py:5356-5362`). The existing test locks the broken behavior by seeding only recovery/running proposals, passing `--domains recovery,sleep`, and asserting synthesis still ran with two recommendations (`safety/tests/test_cli_daily.py:272-304`).

Disagreement: None on substance. This is a release-blocking invariant bug if the architecture keeps claiming a complete governed daily commit.

### B2. JSON crash bugs in cmd_propose / cmd_writeback / cmd_review_record / cmd_review_schedule + missing main() guard

Status: PARTIALLY REPRODUCED - broader and narrower than claimed

Evidence: `cmd_propose` loads JSON before any guard (`src/health_agent_infra/cli.py:914`). `cmd_review_schedule` and `cmd_review_record` do the same (`src/health_agent_infra/cli.py:1658`, `src/health_agent_infra/cli.py:1688`). `main()` still just parses and dispatches `args.func(args)` with no top-level exception guard (`src/health_agent_infra/cli.py:5655-5657`). The codebase already has the right local pattern in `cmd_synthesize` for `--drafts-json`, where `json.JSONDecodeError` and `OSError` are caught and turned into governed `USER_INPUT` exits (`src/health_agent_infra/cli.py:1127-1137`).

Disagreement: `cmd_writeback` is stale; `hai writeback` was removed in v0.1.4 (`reporting/plans/v0_1_4/acceptance_criteria.md:42`), and there is no `cmd_writeback` in current `cli.py`. The claim also missed two live bad-JSON/path crash surfaces: `cmd_pull` manual readiness JSON (`src/health_agent_infra/cli.py:173`) and `cmd_clean` evidence JSON (`src/health_agent_infra/cli.py:481`).

### B3. Truth-fork in cmd_review_record

Status: REPRODUCED

Evidence: `cmd_review_record` passes `data["followed_recommendation"]` directly into `record_review_outcome` (`src/health_agent_infra/cli.py:1784-1788`). `record_review_outcome` constructs `ReviewOutcome` and writes `outcome.to_dict()` to JSONL without runtime type validation (`src/health_agent_infra/core/review/outcomes.py:154-174`). The dataclass annotation says `followed_recommendation: bool`, but dataclasses do not enforce it (`src/health_agent_infra/core/schemas.py:335-342`). The state projector writes `_bool_to_int(outcome.followed_recommendation)` (`src/health_agent_infra/core/state/projector.py:267-291`), and `_bool_to_int` uses ordinary Python truthiness (`src/health_agent_infra/core/state/projectors/_shared.py:20-27`).

Disagreement: None.

### B4. --bundle-only bypasses no-proposals gate

Status: REPRODUCED

Evidence: `cmd_synthesize` exits through the `args.bundle_only` branch before the normal synthesis path and does not check proposal count (`src/health_agent_infra/cli.py:1107-1123`). `build_synthesis_bundle` reads proposals and returns them without enforcing non-empty input (`src/health_agent_infra/core/synthesis.py:675-683`). The current bundle-only test seeds a proposal first and asserts that one proposal is present, so it does not cover the empty-proposal case (`safety/tests/test_cli_synthesize.py:1223-1252`).

Disagreement: None.

### B5. hai state reproject FK orphan crash

Status: REPRODUCED

Evidence: `reproject_from_jsonl` enters `BEGIN EXCLUSIVE`, deletes `proposal_log` directly when the group is present, and the nearby comment says synthesis-side tables have no inbound FK dependency on `proposal_log` (`src/health_agent_infra/core/state/projector.py:1213-1258`). That comment is false for the current schema: `planned_recommendation.proposal_id` is `NOT NULL REFERENCES proposal_log (proposal_id)` (`src/health_agent_infra/core/state/migrations/011_planned_recommendation.sql:61-64`).

Disagreement: None on the bug. I agree with demoting urgency below B1/B2/B3 if users can avoid manual reproject, but the code path itself is wrong.

### B6. hai intake gaps misleading zero without --evidence-json

Status: REPRODUCED

Evidence: `cmd_intake_gaps` allows `args.evidence_json` to be absent, builds a snapshot with `evidence_bundle=None`, calls `compute_intake_gaps`, and emits `"gap_count": len(gaps)` with no `"computed"` or refusal signal (`src/health_agent_infra/cli.py:2740-2795`). `compute_intake_gaps` explicitly returns `[]` for snapshots without `classified_state` and says callers are expected to pass a full snapshot (`src/health_agent_infra/core/intake/gaps.py:224-234`). The CLI test only covers the evidence-json path (`safety/tests/test_intake_gaps.py:302-360`); the lean-snapshot zero behavior is only unit-tested as a helper behavior (`safety/tests/test_intake_gaps.py:138-149`).

Disagreement: None.

### B7. intent-router schema drift on hai review record

Status: REPRODUCED

Evidence: `intent-router` documents a direct-flag `hai review record --domain <d> --recommendation-id <rec_id> --followed-recommendation <0|1> ... [--completed 0|1] [--pre-energy-score] [--post-energy-score] [--disagreed-firing-ids]` flow (`src/health_agent_infra/skills/intent-router/SKILL.md:141-153`). The actual parser requires `--outcome-json`, `--base-dir`, and `--db-path` for `review record` (`src/health_agent_infra/cli.py:4833-4837`), and the override flags are `--completed yes|no`, `--intensity-delta`, `--duration-minutes`, `--pre-energy`, `--post-energy`, and `--disagreed-firings` (`src/health_agent_infra/cli.py:4841-4868`). The drift is not isolated: `agent_integration.md` says next-morning review uses `hai review record --domain <d>` (`reporting/docs/agent_integration.md:75-76`), README advertises `hai review schedule | record | summary [--domain <d>]` (`README.md:228`), and the tour mixes `--outcome-json` with `--domain recovery` (`reporting/docs/tour.md:184`).

Disagreement: None.

### Stale findings (recovery legacy path; classify/policy hard-limiting)

Recovery legacy path: FIXED SINCE ROUND 1. `recovery-readiness` now allows `Bash(hai propose *)` (`src/health_agent_infra/skills/recovery-readiness/SKILL.md:4`) and instructs agents to emit `RecoveryProposal` through `hai propose --domain recovery --proposal-json ... --base-dir <root>` (`src/health_agent_infra/skills/recovery-readiness/SKILL.md:84-90`).

Classify/policy hard-limiting: STALE BUT THE INTERNAL AUDIT'S WORDING IS OFF. The current CLI does not expose legacy `hai classify` / `hai policy` commands; a parser comment says they were removed in v0.1.4 and subsumed by `hai state snapshot --evidence-json`, which emits `classified_state` and `policy_result` for every domain (`src/health_agent_infra/cli.py:5552-5556`). The v0.1.4 acceptance notes likewise say `hai writeback` was removed and user-facing docs were scrubbed (`reporting/plans/v0_1_4/acceptance_criteria.md:42`).

## Validation of internal audit's new findings (Job B)

### Cold-start asymmetry across 6 domains

Status: PARTIALLY REPRODUCED

Evidence: The snapshot layer computes cold-start status centrally for all six domains (`src/health_agent_infra/core/state/snapshot.py:35`, `src/health_agent_infra/core/state/snapshot.py:41-72`, `src/health_agent_infra/core/state/snapshot.py:122-133`). Only running, strength, and stress policy evaluators accept `cold_start_context` and implement relaxation helpers (`src/health_agent_infra/domains/running/policy.py:150-154`, `src/health_agent_infra/domains/running/policy.py:233-273`, `src/health_agent_infra/domains/strength/policy.py:185-188`, `src/health_agent_infra/domains/strength/policy.py:269-302`, `src/health_agent_infra/domains/stress/policy.py:178-182`, `src/health_agent_infra/domains/stress/policy.py:255-285`). Recovery, sleep, and nutrition policy entrypoints do not accept `cold_start_context` (`src/health_agent_infra/domains/recovery/policy.py:150`, `src/health_agent_infra/domains/sleep/policy.py:169`, `src/health_agent_infra/domains/nutrition/policy.py:178`).

Disagreement: Do not blindly "make all six symmetric." Nutrition non-relaxation appears intentional and tested: `test_nutrition_cold_start_non_relaxation.py` says nutrition never gets cold-start relaxation and asserts insufficient nutrition evidence still defers (`safety/tests/test_nutrition_cold_start_non_relaxation.py:1-17`, `safety/tests/test_nutrition_cold_start_non_relaxation.py:63-83`). The right fix is a policy matrix that documents per-domain decisions, not necessarily a six-domain relaxation clone.

### Date-flag naming inconsistency (--as-of vs --for-date vs --date)

Status: REPRODUCED

Evidence: The parser uses `--date` for `hai pull` (`src/health_agent_infra/cli.py:4281`), `--as-of` for `hai synthesize` (`src/health_agent_infra/cli.py:4491`), `--for-date` for `hai explain` (`src/health_agent_infra/cli.py:4566`), `--as-of` for `hai today` (`src/health_agent_infra/cli.py:4628`), `--as-of` across intake commands (`src/health_agent_infra/cli.py:4962`, `src/health_agent_infra/cli.py:5037`, `src/health_agent_infra/cli.py:5068`, `src/health_agent_infra/cli.py:5098`, `src/health_agent_infra/cli.py:5129`, `src/health_agent_infra/cli.py:5162`), `--as-of` for `state snapshot` (`src/health_agent_infra/cli.py:5260`), `--as-of` for `daily` (`src/health_agent_infra/cli.py:5331`), and `--as-of` for `doctor` (`src/health_agent_infra/cli.py:5498`).

Disagreement: None. Keep aliases for one release if renaming.

### Threshold constant duplication

Status: PARTIALLY REPRODUCED

Evidence: The 14-day cold-start cutoff is not duplicated as executable cutoff logic in three policy files; it is centralized as `COLD_START_THRESHOLD_DAYS = 14` (`src/health_agent_infra/core/state/snapshot.py:35`) and applied in snapshot construction (`src/health_agent_infra/core/state/snapshot.py:122-133`). The three policy files duplicate `history_days<14` only in user-facing/audit note strings (`src/health_agent_infra/domains/running/policy.py:268-270`, `src/health_agent_infra/domains/strength/policy.py:293-295`, `src/health_agent_infra/domains/stress/policy.py:276-279`). The 28-day chronic/load windows are duplicated as executable logic: running slices a trailing 28-day window and divides by 4 (`src/health_agent_infra/domains/running/signals.py:167-174`), and strength defines/uses 7-day and 28-day windows with `rows[-28:]`, `rows[-7:]`, and `/ 4.0` (`src/health_agent_infra/domains/strength/signals.py:51-58`, `src/health_agent_infra/domains/strength/signals.py:80-87`). Strength classifier docs also encode the 7d/28d model (`src/health_agent_infra/domains/strength/classify.py:12-23`).

Disagreement: The internal audit overstates the 14-day duplication. Fix the notes to interpolate the central constant, but treat the 28-day windows as the real config/constants cleanup.

### Test coverage gaps for the P0 bugs

Status: REPRODUCED

Evidence: B1 has a regression test that encodes the broken behavior instead of rejecting it (`safety/tests/test_cli_daily.py:272-304`). JSON-crash coverage is explicitly narrow: `test_cli_exit_codes.py` says it covers only migrated handlers and does not include propose/review bad JSON paths (`safety/tests/test_cli_exit_codes.py:1-8`). B4's bundle-only test seeds a proposal before asserting bundle shape, so it misses the zero-proposal bypass (`safety/tests/test_cli_synthesize.py:1223-1252`). B6 lacks a CLI refusal test for absent `--evidence-json`; the CLI coverage uses evidence JSON (`safety/tests/test_intake_gaps.py:302-360`) and the no-classified-state zero is only helper-level behavior (`safety/tests/test_intake_gaps.py:138-149`). The docs integrity tests intentionally strip flag patterns and validate command identity only, so they cannot catch B7-class flag drift (`safety/tests/test_docs_integrity.py:120-163`, especially `safety/tests/test_docs_integrity.py:143-147`; body refs are command-level only at `safety/tests/test_docs_integrity.py:166-189`).

Disagreement: The "zero direct regression test" claim is directionally right for the broken invariants, but B1 is worse than a gap: there is an affirmative test that must be changed.

## What both audits missed (Job C)

### C1. JSON crash surface is wider than B2

Severity: P0

Evidence: In addition to `cmd_propose`, `cmd_review_schedule`, and `cmd_review_record`, `cmd_pull` directly loads `--manual-readiness-json` before a local JSON/OSError guard (`src/health_agent_infra/cli.py:173`), and `cmd_clean` directly loads `--evidence-json` (`src/health_agent_infra/cli.py:481`). `main()` has no top-level guard (`src/health_agent_infra/cli.py:5655-5657`).

Recommended fix: Build one `_load_json_arg(path, arg_name=...)` helper and route all file-backed JSON CLI arguments through it; add a top-level `main()` exception guard that preserves governed exit semantics while still surfacing an internal error class.

Effort: M

Risk if unfixed: Agents still get Python tracebacks and shell-level failure shapes after B2's named call sites are fixed.

### C2. cmd_propose can append JSONL and then report success even if DB projection rejects the proposal

Severity: P1

Evidence: `cmd_propose` preflights duplicate canonical leaves before writing (`src/health_agent_infra/cli.py:927-952`), appends the JSONL audit record with `perform_proposal_writeback` (`src/health_agent_infra/cli.py:954-956`), then projects to SQLite (`src/health_agent_infra/cli.py:958-971`). The local comment says `ProposalReplaceRequired` should be a hard CLI failure (`src/health_agent_infra/cli.py:958-971`), but `_dual_write_project` catches all projection exceptions, prints a warning, and returns (`src/health_agent_infra/cli.py:681-713`). `cmd_propose` then emits success JSON and returns OK (`src/health_agent_infra/cli.py:1001-1002`).

Recommended fix: Make `ProposalReplaceRequired` fatal in `cmd_propose` even when it happens during projection, or perform the duplicate-leaf check and projection under the same DB transaction/lock before reporting success. Preserve the JSONL audit record only if it is explicitly marked rejected/projection_failed.

Effort: M

Risk if unfixed: A race or out-of-band DB state can leave JSONL and SQLite disagreeing while the CLI says the proposal landed.

### C3. daily-plan-synthesis allowed-tools may not match its own examples

Severity: P1 if Claude Code allowed-tools matching is prefix/order sensitive; otherwise P2 docs-test gap

Evidence: The skill frontmatter allows `Bash(hai synthesize --bundle-only *)` and `Bash(hai synthesize --drafts-json *)` (`src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:4`). The body examples put required flags first and `--bundle-only`/`--drafts-json` later: `hai synthesize --as-of <today> --user-id <u> --bundle-only` and `hai synthesize --as-of <date> --user-id <u> --drafts-json <path>` (`src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:17`, `src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:91`). The docs integrity test strips flag patterns, so it will not catch this (`safety/tests/test_docs_integrity.py:143-147`).

Recommended fix: Either broaden allowed-tools to `Bash(hai synthesize *)` for this skill or rewrite examples to match the allowed pattern; extend W3's validator to test allowed-tools patterns against canonical examples.

Effort: S

Risk if unfixed: The synthesis skill may block its own documented command, depending on allowed-tools matching semantics. I did not execute Claude Code's permission matcher, so this part is UNCERTAIN.

### C4. expert-explainer permits arbitrary python3 -c despite claiming local-only bounded retrieval

Severity: P1

Evidence: `expert-explainer` allows `Bash(python3 -c *)` (`src/health_agent_infra/skills/expert-explainer/SKILL.md:4`). The same skill claims the allowed-tools block pins the workflow to `hai explain` / `hai state snapshot` and never resolves an external host (`src/health_agent_infra/skills/expert-explainer/SKILL.md:131-143`). The retrieval module itself promises no network imports (`src/health_agent_infra/core/research/retrieval.py:15-18`), and tests check network imports in `retrieval.py` / `sources.py` but cannot constrain arbitrary Python executed through the skill (`safety/tests/test_expert_research.py:135-174`).

Recommended fix: Add a first-class local retrieval CLI command, then remove `Bash(python3 -c *)` from the skill. If Python is kept, the skill's privacy invariant must be weakened because the tool permission is broader than the prose contract.

Effort: M

Risk if unfixed: The privacy/no-network boundary depends on skill discipline instead of the permission surface.

### C5. reporting skill has another stale review summary flag

Severity: P1

Evidence: `reporting` instructs `hai review summary --user-id <id> --since <date>` (`src/health_agent_infra/skills/reporting/SKILL.md:47-50`). The actual `review summary` parser accepts `--base-dir`, `--user-id`, and `--domain`, but no `--since` (`src/health_agent_infra/cli.py:4911-4917`). Existing docs integrity checks only resolve command identity and strip flag patterns (`safety/tests/test_docs_integrity.py:143-147`, `safety/tests/test_docs_integrity.py:166-189`).

Recommended fix: Include this in W3's drift sweep and make the validator fail unknown flags in skill examples.

Effort: S

Risk if unfixed: Reporting agents follow a documented command that cannot parse.

### C6. Reproject determinism is weaker than the contract if timestamp columns count

Severity: P2

Evidence: The CLI contract calls `hai state reproject` a deterministic projection (`reporting/docs/agent_cli_contract.md:94`), and the parser contract description repeats deterministic projection from JSONL audit logs (`src/health_agent_infra/cli.py:5313-5316`). The projector stamps wall-clock time through `_now_iso()` (`src/health_agent_infra/core/state/projectors/_shared.py:16-17`), including reprojected recommendation/planned rows (`src/health_agent_infra/core/state/projector.py:1366-1367`) and review events (`src/health_agent_infra/core/state/projector.py:1396`). Roundtrip tests knowingly strip volatile timestamp columns before comparison (`safety/tests/test_migrations_roundtrip.py:70-78`, `safety/tests/test_migrations_roundtrip.py:140-153`).

Recommended fix: Either document "deterministic modulo projection/audit timestamps" or derive projection timestamps deterministically from source records or an explicit replay timestamp.

Effort: S

Risk if unfixed: Reprojection can produce different SQLite rows across runs while docs imply bit-for-bit determinism.

### C7. Schema migration gap detection relies on MAX(version), so missing lower migrations can be hidden

Severity: P2

Evidence: `current_schema_version` returns `MAX(version)` from `schema_migrations` (`src/health_agent_infra/core/state/store.py:74-83`). Pending migration selection skips any migration whose version is `<= current` (`src/health_agent_infra/core/state/store.py:201-207`). Doctor compares the current max version to the packaged head, not the exact applied set (`src/health_agent_infra/core/doctor/checks.py:103-129`).

Recommended fix: Treat the applied migration set as a contiguous set. `migrate` and `doctor` should detect missing packaged versions below head and report/repair/refuse explicitly.

Effort: S

Risk if unfixed: A manually edited or partially failed DB with version gaps can look current while missing schema objects.

## Reaction to PLAN.md workstreams

- W1 - Reproject FK fix: Agree with the technical framing and acceptance criteria (`reporting/plans/v0_1_6/PLAN.md:143-163`). Sequencing after the P0 boundary fixes is acceptable because manual reproject has a workaround, but it should still ship in v0.1.6.
- W2 - Gaps computed honesty: Agree with refusal without `--evidence-json`, `"computed": true`, and tests (`reporting/plans/v0_1_6/PLAN.md:165-178`). Sequence it after B1/B2/B3 if release-blocker capacity is constrained.
- W3 - Skill/CLI schema drift sweep: Agree, but broaden it. The proposed validator already targets flags and choice hints (`reporting/plans/v0_1_6/PLAN.md:180-194`); it also needs allowed-tools pattern checks, `daily-plan-synthesis` flag order (`src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:4`, `src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:17`), and `reporting`'s stale `--since` (`src/health_agent_infra/skills/reporting/SKILL.md:47-50`).
- W4 - `hai daily` honesty: Disagree with framing if it stays mostly docs/`--auto`; B1 proves the gate is wrong in code (`src/health_agent_infra/cli.py:3490-3502`). The contract/hint docs in W4 are useful after the gate is fixed (`reporting/plans/v0_1_6/PLAN.md:196-210`).
- W5 - intervals.icu default: I did not re-audit live-source behavior. The workstream is plausible from the empirical session recap (`reporting/plans/v0_1_6/codex_audit_prompt_round2.md:100-101`) and the plan's acceptance criteria (`reporting/plans/v0_1_6/PLAN.md:212-224`), but DEFERRED - DIDN'T INVESTIGATE adapter/auth code.
- W6 - Nutrition daily-total UX honesty: Agree as a UX/documentation fix (`reporting/plans/v0_1_6/PLAN.md:226-238`). It is not a structural P0.
- W7 - Default `--base-dir`: Agree with the default resolution goal (`reporting/plans/v0_1_6/PLAN.md:240-251`). Coordinate with B2's JSON helper so path/error reporting stays consistent.
- W8 - `planned_session_type` vocabulary: Agree with documenting canonical values and surfacing unknown strings (`reporting/plans/v0_1_6/PLAN.md:253-264`). Put it after W3 so the skill docs remain validated.
- W9 - README rewrite: Agree as the final pass after behavior changes land (`reporting/plans/v0_1_6/PLAN.md:266-278`). Do not use README edits to paper over B1/B2/B3.
- W10 - Proposal-completeness gate: Agree and make it P0; internal audit's W10 is the code fix for B1 (`reporting/plans/v0_1_6/internal_audit_response.md:561-562`, `src/health_agent_infra/cli.py:3490-3502`).
- W11 - JSON-arg load + main guard: Agree and make it P0, but include `cmd_pull` and `cmd_clean`, and remove `cmd_writeback` from the target list (`reporting/plans/v0_1_6/internal_audit_response.md:562`, `src/health_agent_infra/cli.py:173`, `src/health_agent_infra/cli.py:481`, `reporting/plans/v0_1_4/acceptance_criteria.md:42`).
- W12 - Review-outcome validation: Agree and make it P0 (`reporting/plans/v0_1_6/internal_audit_response.md:563`, `src/health_agent_infra/cli.py:1784-1788`, `src/health_agent_infra/core/state/projectors/_shared.py:20-27`).
- W13 - Bundle-only no-proposals refusal: Agree as P1 unless `--bundle-only` is a public agent contract in v0.1.6 (`reporting/plans/v0_1_6/internal_audit_response.md:564`, `src/health_agent_infra/cli.py:1107-1123`).
- W14 - Cold-start symmetry/config constants: Agree as P2 only with nuance: document intentional nutrition non-relaxation and fix actual 28-day duplication; do not claim the 14-day cutoff is executable logic duplicated in three files (`reporting/plans/v0_1_6/internal_audit_response.md:565`, `src/health_agent_infra/core/state/snapshot.py:35`, `safety/tests/test_nutrition_cold_start_non_relaxation.py:1-17`).

Proposed sequencing: Internal audit's sequence `W11 -> W12 -> W10 -> W2 -> W3 -> W7 -> W1 -> W13 -> W4+W5 -> W6 -> W8 -> W14 -> W9` is broadly right (`reporting/plans/v0_1_6/internal_audit_response.md:567-568`). My deltas: fold `cmd_pull`/`cmd_clean` into W11, include allowed-tools checks and reporting skill drift in W3, and do W4's docs only after W10's code gate.

## Reaction to internal_audit_response.md

Agree: B1 is P0/release-blocking if the architecture keeps promising atomic six-domain commits; the internal audit calls out that `gate_ok = bool(proposals)` allows a 1-of-6 complete plan (`reporting/plans/v0_1_6/internal_audit_response.md:23-27`), and the code confirms it (`src/health_agent_infra/cli.py:3490-3502`).

Agree with correction: B2 is P0, but the named target list is stale/incomplete. `cmd_writeback` is gone (`reporting/plans/v0_1_4/acceptance_criteria.md:42`); `cmd_pull` and `cmd_clean` are live unguarded JSON readers (`src/health_agent_infra/cli.py:173`, `src/health_agent_infra/cli.py:481`).

Agree: B3 is P0 data integrity, not just CLI validation polish. The internal audit describes the JSONL/SQLite truth fork (`reporting/plans/v0_1_6/internal_audit_response.md:33-37`), and current code still has no runtime boolean validation (`src/health_agent_infra/cli.py:1784-1788`, `src/health_agent_infra/core/state/projectors/_shared.py:20-27`).

Agree: demote W1 below B1/B2/B3 because incremental intake still lets users avoid `hai state reproject`; the internal audit makes the same workaround argument (`reporting/plans/v0_1_6/internal_audit_response.md:512-515`). Do not drop it from v0.1.6, because the FK comment is actively false (`src/health_agent_infra/core/state/projector.py:1244-1247`, `src/health_agent_infra/core/state/migrations/011_planned_recommendation.sql:61-64`).

Agree: "atomic six-domain commit" is half-real. Synthesis can be transactional, but proposal completeness and bundle-only no-proposal gates are not enforced (`reporting/plans/v0_1_6/internal_audit_response.md:422-427`, `src/health_agent_infra/cli.py:3490-3502`, `src/health_agent_infra/cli.py:1107-1123`).

Disagree with wording: "14-day cold-start cutoff lives in three files" is wrong as executable logic. It is centralized in snapshot (`src/health_agent_infra/core/state/snapshot.py:35`, `src/health_agent_infra/core/state/snapshot.py:122-133`); the policy files duplicate only explanatory note strings (`src/health_agent_infra/domains/running/policy.py:268-270`, `src/health_agent_infra/domains/strength/policy.py:293-295`, `src/health_agent_infra/domains/stress/policy.py:276-279`).

Depends: cold-start asymmetry should be decided domain-by-domain, not forced symmetric. Nutrition has an explicit non-relaxation test (`safety/tests/test_nutrition_cold_start_non_relaxation.py:1-17`, `safety/tests/test_nutrition_cold_start_non_relaxation.py:63-83`).

## Final severity-ranked punch list for v0.1.6

1. [P0] `hai daily` accepts partial-domain proposal sets as complete - make completeness `not missing_expected`, add incomplete status, and fix the locking test - M.
2. [P0] File-backed JSON arguments can throw tracebacks - add `_load_json_arg`, cover propose/review/pull/clean/synthesize drafts, and add a top-level `main()` guard - M.
3. [P0] `hai review record` can fork truth between JSONL and SQLite - validate outcome payload types before JSONL/DB writes and enforce in `record_review_outcome` too - M.
4. [P1] `hai state reproject` can violate `planned_recommendation -> proposal_log` FK - add orphan detection plus opt-in dependency-order cascade - M.
5. [P1] `hai synthesize --bundle-only` bypasses the no-proposals contract - refuse empty proposal bundles or mark them explicitly non-computed - S.
6. [P1] `hai intake gaps` returns misleading zero without evidence JSON - refuse without `--evidence-json` and emit `"computed": true` on real runs - S.
7. [P1] Skill/docs commands drift from parser reality - ship W3 validator for flags, choices, allowed-tools patterns, and body examples; fix intent-router/reporting/daily-plan-synthesis drift - M.
8. [P1] `cmd_propose` can report success after JSONL append even when projection rejects - make duplicate/replacement projection failures fatal or explicitly rejected - M.
9. [P1] `expert-explainer` has broader tool permission than its privacy invariant - replace `python3 -c` with a bounded local CLI or weaken the invariant - M.
10. [P1] `--base-dir` is required across agent-facing write commands - add default resolution and consistent help/error paths - M.
11. [P1] intervals.icu/Garmin default source story is not aligned with the supported-source claim - make intervals.icu primary when configured and document Garmin live as best-effort - M.
12. [P1] nutrition daily-total semantics are easy to misuse as per-meal logging - document daily-total behavior and warn on same-day supersede - S.
13. [P1] `planned_session_type` vocabulary is undocumented - publish canonical values and surface unknown strings - S.
14. [P2] Cold-start rules are not explained as a six-domain policy matrix - document which domains relax and why; keep nutrition non-relaxation if intentional - M.
15. [P2] Date flags use `--as-of`, `--for-date`, and `--date` for the same concept - standardize on `--as-of` with deprecated aliases - S.
16. [P2] 28-day windows and cold-start note strings are duplicated - factor real window constants and interpolate the central 14-day value into notes - S.
17. [P2] Reproject determinism is overstated if timestamp columns count - document timestamp volatility or derive deterministic replay timestamps - S.
18. [P2] Migration gap detection can miss absent lower migrations below max version - validate contiguous applied migration set in migrate/doctor - S.
19. [P2] README/tour/integration docs need a final post-fix sweep - rewrite after behavior changes land, not before - S.

## Things both audits got wrong

- `cmd_writeback` is not a live B2 target. It was removed in v0.1.4 (`reporting/plans/v0_1_4/acceptance_criteria.md:42`).
- "14-day cutoff duplicated in three files" is wrong as executable logic. The cutoff is centralized (`src/health_agent_infra/core/state/snapshot.py:35`); only explanatory strings duplicate `history_days<14` (`src/health_agent_infra/domains/running/policy.py:268-270`, `src/health_agent_infra/domains/strength/policy.py:293-295`, `src/health_agent_infra/domains/stress/policy.py:276-279`).
- The stale classify/policy finding should be described as "commands removed/subsumed," not "now accepts all six domains"; the current CLI comment says legacy `hai classify` / `hai policy` were removed and replaced by `hai state snapshot --evidence-json` (`src/health_agent_infra/cli.py:5552-5556`).
- The existing docs integrity test is not a flag-drift safety net. It strips flag patterns intentionally (`safety/tests/test_docs_integrity.py:143-147`) and resolves body refs only at command identity level (`safety/tests/test_docs_integrity.py:166-189`).

## Things both audits didn't ask about but should have

- Whether file-backed JSON error handling is complete across every CLI, not just the four B2 names. It is not: `cmd_pull` and `cmd_clean` are live misses (`src/health_agent_infra/cli.py:173`, `src/health_agent_infra/cli.py:481`).
- Whether dual-write paths can append JSONL and still report success after DB projection failure. `cmd_propose` can, because `_dual_write_project` catches projection exceptions and returns (`src/health_agent_infra/cli.py:681-713`, `src/health_agent_infra/cli.py:954-956`, `src/health_agent_infra/cli.py:1001-1002`).
- Whether allowed-tools frontmatter actually permits the commands shown in skill bodies. `daily-plan-synthesis` is the concrete suspicious case (`src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:4`, `src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:17`, `src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:91`).
- Whether privacy/no-network invariants are enforced by permissions, not just prose. `expert-explainer` currently allows arbitrary `python3 -c` (`src/health_agent_infra/skills/expert-explainer/SKILL.md:4`, `src/health_agent_infra/skills/expert-explainer/SKILL.md:131-143`).
- Whether "deterministic reproject" includes volatile projection timestamps. The tests strip timestamp columns, so the current deterministic claim needs qualification (`reporting/docs/agent_cli_contract.md:94`, `safety/tests/test_migrations_roundtrip.py:70-78`, `safety/tests/test_migrations_roundtrip.py:140-153`).
- Whether `schema_migrations` integrity means exact contiguous set, not just max version. Current code checks max version only (`src/health_agent_infra/core/state/store.py:74-83`, `src/health_agent_infra/core/state/store.py:201-207`, `src/health_agent_infra/core/doctor/checks.py:103-129`).
