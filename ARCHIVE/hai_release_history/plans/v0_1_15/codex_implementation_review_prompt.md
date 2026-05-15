# Codex Implementation Review — v0.1.15 (Phase 1+2 only; Phase 3 to follow)

> **Why this round.** v0.1.15 Phase 1 + Phase 2 are complete on `main`
> (10 commits since `f593b5a` D14-close, 6 atomic implementation commits
> for the 6 in-scope W-ids). The D14 pre-cycle plan-audit chain settled
> at PLAN_COHERENT_WITH_REVISIONS round 4 (close-in-place; halving
> signature 12 → 7 → 3 → 2). Phase 0 (D11) bug-hunt cleared with 1
> revises-scope finding (F-PHASE0-01) addressed via Option A revision +
> D14 round 4. Pre-implementation gate fired green; Q2 candidate
> (the named foreign-user candidate) on file.
>
> **Phase 3 (W-2U-GATE recorded session) has NOT yet fired.** This
> review is **scoped to Phase 1+2 implementation** — the runtime/code/
> skill changes that close W-GYM-SETID + F-PV14-01 + W-A + W-C + W-D
> arm-1 + W-E. The W-2U-GATE recorded session is a separate audit
> surface that runs after the named foreign-user candidate performs the gate session against
> the candidate-package wheel; its findings will surface in a separate
> Phase-3-specific review (or the v0.1.16 cycle if deferred).
>
> **Branch posture.** All 6 implementation commits landed directly on
> `main` (the maintainer's daily-driver loop dogfoods through `main`
> rather than feature branches). RELEASE_PROOF + REPORT have NOT yet
> been authored; those land after the Phase 3 gate session per the
> v0.1.15 PLAN §6 ship-gate sequencing.
>
> **What you're auditing.** That the 6 W-ids' shipped code actually
> delivers what PLAN.md §2 promised, that the suite + type-check + bandit
> gates pass, that no defect is hiding in the diff, and that the
> known scope nuances (e.g., snapshot.py W-A wire that PLAN §2.E
> "no call-graph changes outside domains/nutrition/" might cover) are
> honestly disposed.
>
> **Empirical norm:** 2-3 rounds, settling at the `5 → 2 → 1-nit` shape
> for substantive cycles per AGENTS.md.
>
> **You are starting fresh.** This prompt and the artifacts it cites
> are everything you need; do not assume context from a prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd                         # /Users/domcolligan/health_agent_infra
git branch --show-current   # main
git log --oneline -12       # the 6 v0.1.15 W-id commits + Phase-0 + D14-r4 + cycle-open
git status                  # clean (or maintainer's anthropic_personal_guidance_report.md untracked — pre-existing)
```

Expected commit chain (most-recent first; SHAs verified via `git log` at audit-prompt-authoring time):

```
0fd5179  v0.1.15 W-E: merge-human-inputs skill consumes W-A presence block …
70d4f76  v0.1.15 W-D arm-1: nutrition classifier suppresses to insufficient_data …
b47552c  v0.1.15 W-C: hai target nutrition 4-row macro convenience over existing target table …
77ecb3c  v0.1.15 W-A: hai intake gaps adds present block + is_partial_day + target_status enum …
df44cb5  v0.1.15 F-PV14-01: CSV-fixture pull default-deny against canonical state DB …
485bae7  v0.1.15 W-GYM-SETID: gym_set PK includes exercise slug to prevent multi-exercise collisions …
f593b5a  v0.1.15 D14 closed at round 4 (F-R4-01 W-C contract tightening + F-R4-02 stale-prose cluster) …
5cd5864  v0.1.15 Q2 closed: W-2U-GATE candidate named (the named foreign-user candidate); cycle proceeds path (a)
917d70a  v0.1.15 Phase 0 + D14 round-4 ready (F-PHASE0-01 Option A …)
0bd534e  v0.1.15 cycle-open session prompt …
38d4cb3  v0.1.15 D14 close-in-place at round 3 + v0.1.16/v0.1.17 workspace stubs …
```

If anything mismatches, stop and surface. The dual-repo discriminator
(stale checkout HEAD `2811669` under `/Users/domcolligan/Documents/`
must be ignored) still applies — see AGENTS.md "Active repo path"
preamble.

---

## Step 1 — Read orientation artifacts (in order)

1. **`AGENTS.md`** — operating contract. No new D-entries this cycle
   (the F-PHASE0-01 revision was scope-recovery, not a settled
   decision). Read **"Patterns the cycles have validated"** —
   provenance discipline, summary-surface sweep, honest partial-
   closure naming.
2. **`reporting/plans/v0_1_15/PLAN.md`** — round-4 final cycle
   contract. §2 is the per-WS contract surface this audit verifies
   against.
3. **`reporting/plans/v0_1_15/audit_findings.md`** — Phase 0 findings
   (1 revises-scope F-PHASE0-01 + 3 nits). §6 records the maintainer's
   F-PHASE0-01 Option A choice + the disposition table.
4. **`reporting/plans/v0_1_15/pre_implementation_gate_decision.md`** —
   gate decision record (Q1 = Option A; Q2 = candidate the named foreign-user candidate
   on file path (a)).
5. **`reporting/plans/v0_1_15/codex_plan_audit_round_4_response.md`**
   + **`_response_response.md`** — round-4 close (F-R4-01 + F-R4-02
   both AGREED + applied).

Then open the diff between HEAD and the round-4 close commit:

```bash
git diff f593b5a..HEAD -- src/ verification/
git diff f593b5a..HEAD -- reporting/docs/agent_cli_contract.md \
    reporting/plans/v0_1_15/PLAN.md \
    reporting/plans/v0_1_17/README.md \
    reporting/plans/tactical_plan_v0_1_x.md
```

Six implementation commits (`485bae7..0fd5179`); each is one W-id
atomic per CLAUDE.md cadence. The total surface added by these six
commits: **~1900 lines of source + ~2400 lines of test code, +43
new acceptance tests across 6 new test files**. Suite: 2624 pass,
3 skipped (was 2580 at f593b5a — +44 net pass).

---

## Step 2 — Audit questions

### Q-IR-W-GYM-SETID — gym_set PK collision fix (commit 485bae7)

**Q-IR-1.a** Does `domains/strength/intake.py:96-107` (the new
`deterministic_set_id(session_id, exercise_name_slug, set_number)`)
match PLAN §2.A's "Fix shape — prospective only" pseudo-code? The
PLAN cited `_norm` from `core/state/projectors/strength.py:66`; the
implementation imports `_norm_token` from `domains/strength/intake.py:190`
which has the same `.strip().casefold()` shape. Is the function-name
divergence acceptable, or should the implementation import the
projector's `_norm` directly to match PLAN literal text?

**Q-IR-1.b** Migration 024 (`024_gym_set_id_with_exercise_slug.sql`)
uses an in-place UPDATE strategy with an OLD-format predicate
(`set_id = 'set_' || session_id || '_' || printf('%03d', set_number)`)
to skip custom-id correction rows. Codex's W-GYM-SETID acceptance
test 2 at PLAN §2.A says "supersession chains preserved by replaying
`supersedes_set_id` against the new derivation in-SQL" — does the
migration's two-step UPDATE (first `supersedes_set_id`, then `set_id`)
correctly preserve every supersession chain? The test
`test_migration_024_rewrites_existing_set_ids_with_supersession_intact`
seeds a correction row with an opaque set_id; does the migration's
custom-id-preservation behavior match the PLAN's intent (the PLAN
didn't explicitly carve out custom set_ids — should it have)?

**Q-IR-1.c** PLAN §2.A acceptance test 5 names a `hai backup` round-
trip test. The shipped test
`test_backup_roundtrip_preserves_gym_set_post_migration` uses `--dest`
on `hai backup` (not `--output` as a first attempt assumed); the
test passes. Does the round-trip actually exercise migration 024
behavior, or does it just confirm rows survive a tar-and-restore
(which would survive any migration)? Spot-check.

### Q-IR-F-PV14-01 — CSV-fixture pull isolation (commit df44cb5)

**Q-IR-2.a** PLAN §2.C contract names FOUR clauses: (1) CSV adapter
default-deny, (2) symmetric `--db-path` / `--base-dir` override rule,
(3) capabilities-manifest source-type tagging, (4) `hai stats` /
`hai doctor` >48h WARN. The implementation explicitly handles
clauses 1, 3, 4 — clause 2 is implicitly covered by the canonical-DB
detection (the guard fires only when BOTH `--db-path` is unset AND
`HAI_STATE_DB` is unset, so explicit user override of either escapes
the guard). Is that implicit handling sufficient for PLAN §2.C's
"symmetric override rule" intent, or should the implementation add
an explicit tier-mismatch refusal (the broader symmetry rule from
the source finding `post_v0_1_14/carry_over_findings.md` F-PV14-01
proposed-fix item 4)?

**Q-IR-2.b** The `--allow-fixture-into-real-state` flag is wired on
`hai pull` only. Other surfaces that read CSV fixtures via
`load_recovery_readiness_inputs` (e.g., `hai daily` when source
resolves to csv) — do they get the same default-deny treatment, or
is the guard only at the `hai pull` entry point? Spot-check
`cmd_daily` for a parallel path.

**Q-IR-2.c** The capabilities-manifest tagging (`source_type='fixture'`
on csv, `source_type='live'` on garmin_live + intervals_icu) added
new `reliability='reliable'` fields to csv + intervals_icu so the
walker's required-field check passes. The pre-PV14-01 contract was
"absence of entry == reliable-by-default"; the new shape moves
intervals_icu + csv from absent to present-with-`reliability=reliable`.
This is a capabilities-manifest schema change — does it conflict with
AGENTS.md "Settled Decisions" D124-135 ("Capabilities-manifest schema
freeze scheduled for v0.2.3")? The schema-freeze hasn't fired yet, so
additions are allowed; verify the change is additive and doesn't
remove or rename existing fields.

### Q-IR-W-A — intake gaps presence block (commit 77ecb3c)

**Q-IR-3.a** PLAN §2.B output contract names the `present` block with
5 sub-keys (`nutrition / gym / readiness / sleep / weigh_in`) plus
`is_partial_day` + `is_partial_day_reason` + `target_status`. Verify
the shipped `compute_presence_block` in
`src/health_agent_infra/core/intake/presence.py` emits all 8 keys
and that the per-domain shapes (logged + identifier + count fields)
match the F-AV-01 example in PLAN §2.B (round-4 typed contract,
not the original findings-doc example which the SUPERSEDED header
notes is now stale).

**Q-IR-3.b** The `target_status` query at `presence.py:compute_target_status`
does TWO queries (active-window then broader-historical) per call.
Is that the most efficient shape, or should it be a single query
with conditional grouping? The query is only run once per `hai intake
gaps` invocation, so performance is not a concern; but verify the
two queries return consistent results across edge cases (e.g., row
with `status='archived'` only — the broader query returns 1, so
target_status='absent'; the active-window returns 0, so the row
is correctly NOT classified as 'present'). Test
`test_target_status_absent_when_row_exists_but_does_not_cover_today`
covers this.

**Q-IR-3.c** The `is_partial_day` check at `presence.py:is_partial_day`
defaults `expected_meals=3`. PLAN §2.B says "default `18:00` user-local"
for cutoff but doesn't specify expected_meals. Is `3` the right
default, or should it be configurable via thresholds.toml in v0.1.15?
The `DEFAULT_EXPECTED_MEALS = 3` constant is module-level (grep-able);
PLAN says "Cutoff configurable via thresholds; default `18:00`
user-local" — the cutoff is hard-coded too. Should both be wired
through `core.config.load_thresholds()` in this cycle, or is module-
constant acceptable for v0.1.15?

### Q-IR-W-C — hai target nutrition (commit b47552c)

**Q-IR-4.a** PLAN §2.D round-4 contract was tightened by Codex
F-R4-01 to require: source/status explicit pairing; atomic helper;
natural-key duplicate-detection idempotency; `_VALID_TARGET_TYPE`
extension. The shipped implementation:

  - `add_targets_atomic` at `core/target/store.py:230-280` — single
    BEGIN IMMEDIATE / COMMIT; pre-validates every record before
    acquiring lock.
  - `cmd_target_nutrition` source/status: `agent_actors = {"claude_agent_v1"}`
    (hard-coded). Should this be a configurable list (e.g., from
    thresholds.toml or a constant in `core.target`) so future agents
    don't need a code edit?
  - Natural-key idempotency: queries `(user_id, domain='nutrition',
    status, effective_from, target_type IN macros, reason LIKE
    '<phase>:%')` for 4 rows with identical `value_json`. Test
    `test_hai_target_nutrition_idempotent_on_identical_reinvocation`
    asserts 3 invocations produce 4 rows — verifies idempotency end-
    to-end. Does the natural key correctly survive a row-validation
    edge case (e.g., user adds a 5th row manually with the same
    natural key — does the idempotency check fire correctly)?
  - `_VALID_TARGET_TYPE` extended in `core/target/store.py:39-45` to
    include `carbs_g` + `fat_g`.

  Is the implementation faithful to PLAN §2.D's tightened contract?

**Q-IR-4.b** Migration 025 uses recreate-and-copy (the standard
SQLite idiom for CHECK extension). The maintainer's live state has
3 nutrition target rows (`calories_kcal=3300` archived, `=3100`
active, `protein_g=160` active). Does migration 025 preserve them
byte-stable? The shipped acceptance test 1 verifies SQL CHECK +
Python set extension; does it also verify existing-row preservation?
(Looking at `test_migration_025_extends_target_type_check_and_python_set`
— it checks the extension but NOT existing-row preservation.
Is that an acceptance-criterion-weak gap?)

**Q-IR-4.c** PLAN §2.D round-4 numbered the migration "024" but
W-GYM-SETID claimed 024 first; W-C lands at 025. The PLAN was
updated in commit b47552c (and v0.1.17 README updated in lockstep).
Verify no other doc surface still says "migration 024" in W-C
context.

### Q-IR-W-D arm-1 — nutrition partial-day suppression (commit 70d4f76)

**Q-IR-5.a** PLAN §2.E acceptance test 5 says "No call-graph changes
to anything outside `domains/nutrition/`." The implementation extended
`derive_nutrition_signals` (in-scope) AND wired the W-A presence
block computation in `core/state/snapshot.py:888` (out-of-scope by
strict reading). Without the snapshot wire, the production daily
pipeline would never trigger the suppression — the suppression
would be classifier-only with no caller passing the W-A signals.
Is the snapshot.py extension acceptable, or should it have been
deferred and disposed under PLAN §2.E acceptance 5?

**Q-IR-5.b** The classifier short-circuit at
`domains/nutrition/classify.py:309-330` returns a `ClassifiedNutritionState`
with `nutrition_status='insufficient_data'` (a NEW enum value not
listed in the module docstring's `NutritionStatus` enum at
classify.py:35-39). Is the new enum value documented somewhere
audit-trail-visible, or does the docstring + downstream consumers
(skill, X9 Phase-B X-rule) need updates to recognize it?

**Q-IR-5.c** Test
`test_snapshot_wiring_passes_w_a_signals_into_nutrition_classifier`
seeds raw nutrition + accepted_nutrition + zero target rows, then
invokes `build_snapshot` with `now_local=10:17`. Verifies
`nutrition_status='insufficient_data'`. Does the test exercise the
end-to-end snapshot path correctly, or does it bypass the
`compute_presence_block` invocation in some way?

### Q-IR-W-E — merge-human-inputs skill (commit 0fd5179)

**Q-IR-6.a** The skill update adds Step 1b ("choose framing from
the W-A `present` block"). PLAN §2.F acceptance 1 says skill must
"branch on `present.{nutrition, gym, readiness, sleep}.logged`" —
the test
`test_skill_consumes_w_a_present_block_for_4_domains` asserts the
4 domain references via regex. Does the skill prose actually
operationalize the branching (i.e., a host agent reading the skill
can act on the signals), or does it just mention them?

**Q-IR-6.b** PLAN §2.F acceptance 2 says skill must NOT branch on
`present.weigh_in.logged`. The test
`test_skill_does_not_branch_on_weigh_in_logged` asserts no `if/when
present.weigh_in.logged ==/is true` patterns. The skill prose
explicitly says "Do NOT branch on `present.weigh_in.logged` in
v0.1.15" with reasoning. Is the wording strong enough to prevent
a future contributor from adding the check before W-B ships?

**Q-IR-6.c** PLAN §2.F acceptance 3 covers an OPTIONAL `morning-
ritual` skill. The implementation deferred it (per PLAN's "optional
(medium)" framing + OQ-1 + Codex round-2 ratification). Should the
deferral be named in the IR response as a known-not-shipped item, or
is the OQ-1 ratification sufficient documentation?

### Q-IR-cross-cutting

**Q-IR-X.a Ship gates.** Run:

```bash
uv run pytest verification/tests -q          # expect 2624 pass, 3 skipped
uvx mypy src/health_agent_infra              # expect Success: no issues found
uvx bandit -ll -r src/health_agent_infra     # expect 0 high/medium new findings
uv run hai capabilities --json | jq .hai_version  # 0.1.14.1 (NOT yet bumped to 0.1.15)
uv run hai capabilities --markdown | diff - reporting/docs/agent_cli_contract.md  # expect identical
```

Pyproject.toml version is still `0.1.14.1` — the version bump to
0.1.15 happens at the RELEASE_PROOF authoring step (post-Phase-3).
Is that the right ordering, or should the version bump have happened
at Phase 1 implementation?

**Q-IR-X.b Settled-decision integrity.** No new D-entries this
cycle. The F-PHASE0-01 Option A revision did NOT modify AGENTS.md
"Settled Decisions" — the F-PHASE0-01 disposition was a PLAN-scope
revision, not a governance change. Verify AGENTS.md "Settled
Decisions" D-entries 1-15 are unchanged from the round-4 PLAN
close commit `f593b5a`.

**Q-IR-X.c Provenance discipline.** Spot-verify on-disk claims:
PLAN §2.A `cmd_state_reproject at cli.py:4111` (verified Phase 0);
PLAN §2.A `--cascade-synthesis at cli.py:8526` (verified Phase 0);
PLAN §2.A `_norm at core/state/projectors/strength.py:66` (verified
Phase 0). Spot-check the v0.1.15 implementation commits added no new
fabricated citations (e.g., the round-4 §2.D "F-R4-01" disposition
contract paragraph — does it cite real source line ranges?).

**Q-IR-X.d Cross-cutting code quality.** Unused new imports in
the 6 commits? Lazy imports inside hot loops? New error paths fail
open or fail closed correctly? Specifically:
  - `cmd_target_nutrition` — does the duplicate-detection-then-insert
    have a TOCTOU window where two concurrent invocations both miss
    the natural-key check and both write 4 rows?
  - `compute_presence_block` opens a connection separately from
    the gaps-derivation conn; is that a meaningful TOCTOU exposure
    or acceptable read-only divergence?
  - Migration 024 + 025 both run inside `apply_pending_migrations`'s
    BEGIN EXCLUSIVE; verify they don't issue inner BEGIN/COMMIT
    statements that would conflict.

**Q-IR-X.e Absences.** Did any of the 6 commits change anything
the cycle didn't say it shipped? Specifically:
  - W-GYM-SETID side fix to `tactical_plan_v0_1_x.md` (carries-forward
    → carry-forward terminology) + `test_doc_freshness_assertions.py`
    allowlist additions (v0.1.16, v0.1.17, carry-over). Were those
    folded honestly, or do they constitute scope creep?
  - F-PV14-01 side fixes to 3 existing tests
    (`test_pull_explicit_csv_source_uses_committed_fixture`,
    `test_pull_default_falls_back_to_csv_when_no_intervals_auth`,
    `test_intake_readiness_output_feeds_hai_pull`) added
    `--allow-fixture-into-real-state` to opt them into pre-PV14
    behavior. Verify the test intent is preserved (probing CSV
    path, not probing the guard).
  - W-C side fix renumbering migration 024 → 025 in PLAN §2.D +
    v0.1.17 README. Verify no stale "migration 024 (W-C)" references
    remain.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_15/codex_implementation_review_response.md`:

```markdown
# Codex Implementation Review — v0.1.15 (Phase 1+2)

**Verdict:** SHIP | SHIP_WITH_NOTES | SHIP_WITH_FIXES
**Round:** 1

## Verification summary
- Tree state: …
- Test surface: 2624 passed / 3 skipped (verified via `uv run pytest`).
- Ship gates: …

## Findings

### F-IR-01. <short title>
**Q-bucket:** Q-IR-W-X-Y / Q-IR-X.Z
**Severity:** correctness-bug | security | scope-mismatch | provenance-gap | acceptance-weak | nit
**Reference:** <commit SHA / file:line> or "absent"
**Argument:** …
**Recommended response:** …

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-GYM-SETID | … | … |
| F-PV14-01 | … | … |
| W-A | … | … |
| W-C | … | … |
| W-D arm-1 | … | … |
| W-E | … | … |

## Open questions for maintainer
```

Each finding triageable. Vague feedback is not a finding; "PLAN §2.D
contract paragraph says X but commit b47552c shipped Y per
`core/target/store.py:Z`" is.

---

## Step 4 — Verdict scale

- **SHIP** — Phase 1+2 merge-ready; Phase 3 gate session can fire
  immediately. No further work on Phase 1+2 surface.
- **SHIP_WITH_NOTES** — Phase 1+2 merge-ready; named follow-ups
  carry to v0.1.16 (named-deferred per the PLAN §2.G P1 rules) or
  v0.1.17. Notes enumerate every non-blocking finding.
- **SHIP_WITH_FIXES** — fix-and-reland before Phase 3 gate. Notes
  enumerate every blocking finding. Round 2 review after maintainer
  addresses.
- **DO_NOT_SHIP** — only on correctness/security bug warranting
  commit reverts. Phase 3 gate is held until resolution.

For most substantive cycles, `SHIP_WITH_NOTES` with a small named-
deferral set is the natural shape.

---

## Step 5 — Out of scope

- **Phase 3 W-2U-GATE recorded session.** The gate hasn't fired
  yet. Findings about the candidate package, the install record,
  the recorded transcript, or the in-session P0/P1 disposition are
  premature for this round.
- **RELEASE_PROOF.md / REPORT.md.** Not yet authored; those land
  after Phase 3 closes.
- **PyPI publish.** Held until RELEASE_PROOF + Phase 3 sign-off.
- **D14 plan-audit chain itself.** Closed at round 4.
- **Strategic-plan / tactical-plan content beyond the deltas the
  6 implementation commits applied.**
- **The named-deferrals themselves** (W-29 → v0.1.17; W-B → v0.1.17;
  W-D arm-2 → v0.1.17; F-PV14-02 → v0.1.17; W-AH-2 / W-AI-2 / W-AM-2
  / W-Vb-4 → v0.1.17) — they have destination cycles. Findings only
  about deferrals that should NOT be deferred.

---

## Step 6 — Cycle pattern

```
D14 plan-audit (rounds 1-4) ✓
Phase 0 (D11) ✓
Pre-implementation gate (Q1 + Q2 closed) ✓
Phase 1 implementation (W-GYM-SETID + F-PV14-01 + W-A + W-C) ✓ 4 commits
Phase 2 implementation (W-D arm-1 + W-E) ✓ 2 commits
Codex implementation review (Phase 1+2) ← you are here
  → SHIP_WITH_FIXES → maintainer + new commits
  → SHIP / SHIP_WITH_NOTES → proceed to Phase 3
Phase 3 W-2U-GATE recorded session (the named foreign-user candidate)
  → RELEASE_PROOF + REPORT authored
  → version bump 0.1.14.1 → 0.1.15 in pyproject.toml
  → PyPI publish (per reference_release_toolchain.md)
```

Estimated: 1-2 sessions per IR round.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_15/codex_implementation_review_response.md`
  (new) — your findings.
- `reporting/plans/v0_1_15/codex_implementation_review_round_N_response.md`
  (subsequent rounds, if any).

**No code changes.** No source commits. No state mutations. The
maintainer applies any agreed fixes; you do not edit source directly.

If you find a correctness/security bug warranting `DO_NOT_SHIP`,
name it explicitly and stop the review for maintainer adjudication.
