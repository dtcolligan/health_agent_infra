# Codex External Audit — v0.1.18 PLAN.md (D14 round 2)

> **Why round 2.** Round 1 closed PLAN_COHERENT_WITH_REVISIONS with 7 findings (F-PLAN-01 through F-PLAN-07). All 7 accepted; PLAN revised in lockstep across §1.1, §1.2, §1.3, §2.B, §2.C, §2.D, §2.E, §2.F, §2.G, §3, §4, §5, §6, §7, §8. The disposition trail is in `codex_plan_audit_response_response.md`. Round 2's job: **verify the multi-surface sweep landed cleanly without introducing second-order contradictions** (the canonical AGENTS.md "Patterns the cycles have validated" round-2 failure mode: revision in section X doesn't propagate to downstream section Y, or a new acceptance item conflicts with another section's contract).
>
> **Round-1 finding catalogue (for context):**
>
> 1. **F-PLAN-01** — W-OB-7 handler inventory off by 2 (6 → 8); seam-shape claim wrong (`sqlite3.connect` → `open_connection`); `hai state init` provenance wrong (`state.py:239,273` is `cmd_state_migrate`, not `cmd_state_init`).
> 2. **F-PLAN-02** — W-OB-5 `next_action` example contradicted post-W-OB-2 shape (`hai init --guided` → `hai init`) and live manifest (`agent_safe: true` → `agent_safe: false`).
> 3. **F-PLAN-03** — W-OB-5 migration-behind acceptance item silently widened `onboarding_readiness` scope; doctor checks split between `check_onboarding_readiness` and `check_state_db`.
> 4. **F-PLAN-04** — W-OB-4 sequenced before W-OB-2 cannot validate the post-W-OB-2 default-flip; PyPI install reference at pre-ship gate is misleading. Split into W-OB-4a (Phase 1 upgrade dogfood) + W-OB-4b (Phase 2 post-W-OB-2 local-wheel smoke).
> 5. **F-PLAN-05** — "parallelizable with v0.2.0" claim wrong; v0.1.18 sits upstream of v0.2.0 via v0.1.19. Inherited from v0.1.17 PLAN where the claim was correct.
> 6. **F-PLAN-06** — `test_guided_onboarding.py` cited but doesn't exist; actual file is `test_init_onboarding_flow.py`.
> 7. **F-PLAN-07** — §6 ship gates missing post-W-OB-2 wheel-smoke gate, scenario-2 packaged-upgrade success gate, post-W-OB-2 `next_action.command` shape gate.
>
> **All 7 OQs settled at round 1** (per §8 dispositions). No deferred OQ goes into round 2.
>
> **Empirical round-2 expectation per AGENTS.md.** Round 1 caught 7 findings; norm is `10 → 5 → 3 → 0` halving signature; round 2 prediction is **2-4 findings**. The most likely failure mode: summary-surface-sweep gaps where a round-1 revision didn't propagate to a downstream surface. Specifically watch for the W-OB-4 → W-OB-4a/W-OB-4b split (six surfaces moved in lockstep — §1.2 catalogue, §1.3 sequencing, §2.D body, §5 effort arithmetic, §6 ship gates, §8 OQ); the W-OB-7 6→8 handler change (§1.1 thread 2, §2.G files-of-record, §2.G acceptance items, §4 risk 8); and the W-OB-5 onboarding-only → multi-check scope widening.
>
> **You are starting fresh.** This prompt and the artifacts it cites are everything you need; do not assume context from a prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main, OR cycle/v0.1.18 if branched
git log --oneline -5
# expect top: a recent commit landing the round-1 PLAN revisions +
#         response_response, OR untracked PLAN.md if revisions
#         have not yet been committed (read working-tree state).
ls reporting/plans/v0_1_18/
# expect: README.md, audit_findings.md, PLAN.md, codex_plan_audit_prompt.md,
#         codex_plan_audit_response.md, codex_plan_audit_response_response.md,
#         codex_plan_audit_round_2_prompt.md (this file).
```

If any don't match, **stop and surface the discrepancy**. Ignore any tree under `/Users/domcolligan/Documents/`.

---

## Step 1 — Read the orientation artifacts

In order:

1. **`reporting/plans/v0_1_18/codex_plan_audit_response.md`** — round 1 findings catalogue. The 7 findings + per-W-id verdicts + tier ratification + closure recommendation.
2. **`reporting/plans/v0_1_18/codex_plan_audit_response_response.md`** — maintainer + Claude triage. Per-finding accept-and-revise dispositions; OQ resolutions; the round-2 prediction the audit author left.
3. **`reporting/plans/v0_1_18/PLAN.md`** — the artifact under review (round-1-revised). Read end-to-end, but pay special attention to the surfaces called out in the **"What's different from round 1"** list below.
4. **AGENTS.md "Patterns the cycles have validated"** — provenance discipline + summary-surface sweep. Round 2's bias is toward catching second-order propagation failures.
5. **(reference for round-1 spot-checks)** `cli/handlers/intake.py` (8 handlers), `core/state/store.py` (`open_connection` line 64, `apply_pending_migrations` line 243), `cli/handlers/state.py:46-52` (`cmd_state_init` → `initialize_database`), `core/doctor/checks.py:84,470` (`check_state_db`, `check_onboarding_readiness`), `verification/tests/test_init_onboarding_flow.py`, `tactical_plan_v0_1_x.md:52` (v0.2.0 dependency), `cli_capabilities_v0_1_13.json` (`hai init` agent_safe value).

---

## Step 2 — What's different from round 1

The PLAN-author applied 7 revision passes. Round 2 verifies the multi-surface sweep is internally consistent. Specific surfaces touched:

### Revision 1 — W-OB-4 split into W-OB-4a + W-OB-4b (per F-PLAN-04)

**Surfaces that should reflect the split:**
- §1.2 catalogue table (now should have W-OB-4a and W-OB-4b rows, not W-OB-4)
- §1.3 sequencing (Phase 1 has W-OB-4a; Phase 2 has W-OB-4b after W-OB-2)
- §2.D body rewritten with two named sub-passes
- §5 effort arithmetic (W-OB-4a + W-OB-4b each 0.5d)
- §6 ship gates (new explicit rows for W-OB-4a + W-OB-4b)
- §4 risks register (risk 3 references W-OB-4a, risk 9 references both)

### Revision 2 — W-OB-7 inventory 6 → 8 handlers (per F-PLAN-01)

**Surfaces that should reflect the count + seam-shape correction:**
- §1.1 thread-2 paragraph (new seam shape: `open_connection` → `open_connection_with_migrations`)
- §2.G files-of-record (eight handlers enumerated with line numbers)
- §2.G fix-shape diff (`open_connection` not `sqlite3.connect`)
- §2.G per-handler classification table
- §2.G acceptance items 2-3 (all eight handlers; 9-case test surface)
- §4 risk 8 (8 handlers, not 6)
- §5 effort arithmetic (8 callers, 9-case test)

### Revision 3 — W-OB-5 scope widened from onboarding_readiness-only to multi-check (per F-PLAN-03)

**Surfaces that should reflect the widening:**
- §2.E source paragraph (multiple checks gain `next_action`)
- §2.E files-of-record (multiple checks in `core/doctor/checks.py`)
- §2.E `next_action` example (corrected per F-PLAN-02: `hai init`, `agent_safe: false`)
- §2.E schema invariants (post-W-OB-2 shape; manifest-consistency invariant)
- §2.E acceptance items (multi-check coverage; manifest-consistency test)
- §2.E "What this WS does NOT do" (decision logic unchanged; runtime-only, not manifest)

### Revision 4 — v0.2.0 sequencing claim corrected (per F-PLAN-05)

**Surfaces that should reflect the corrected claim:**
- §1 metadata block (theme paragraph: "Sequenced upstream of v0.2.0 via v0.1.19")
- §7 cross-cycle boundary (v0.1.18 → v0.1.19 → v0.2.0 chain)

### Revision 5 — W-OB-3 test file fix (per F-PLAN-06)

**Surfaces that should reflect the fix:**
- §2.C files-of-record (`test_init_onboarding_flow.py`)
- §2.C acceptance item 2 (empty-input affordance, not literal `skip` keyword)
- §4 risk 2 (`test_init_onboarding_flow.py`)

### Revision 6 — §6 ship gates additions (per F-PLAN-07)

**New rows in §6:**
- W-OB-4a upgrade scenario `hai intake weight` succeeds
- W-OB-4b post-W-OB-2 local-wheel smoke proves default-flip
- W-OB-5 `next_action.command` post-W-OB-2 shape test
- W-OB-5 `next_action.agent_safe` manifest consistency test
- W-OB-7 8-handler parity test
- Release-blocker gate list updated with the new W-OB-4b + W-OB-7 8-handler entries

### Revision 7 — OQ dispositions settled (per Codex round-1 OQ replies)

**§8 marks all 7 OQs as ✅ Settled D14 R1** with each disposition propagated:
- OQ-1 → core/state/store.py (not cli/shared.py)
- OQ-2 → both opt-out paths tested with isatty=True (5 test cases not 4)
- OQ-3 → priority order documented
- OQ-4 → runtime-only, no manifest delta (drops §2.E.5 acceptance item)
- OQ-5 → content-only post-prompt hint
- OQ-6 → user-facing CHANGELOG wording
- OQ-7 → reserve W-OB-6; specific RELEASE_PROOF wording if unfired

---

## Step 3 — The audit questions (round 2)

### Q1 — Multi-surface sweep verification (canonical R2 failure mode)

For each of the 7 revisions above, did the change propagate to **every** surface that should reflect it? Specifically:

- **Q1.1.** **W-OB-4 split.** Does §1.2 catalogue have separate W-OB-4a and W-OB-4b rows? Does §1.3 sequencing place W-OB-4a in Phase 1 and W-OB-4b in Phase 2 after W-OB-2? Does §5 split effort arithmetic? Does §6 have explicit ship-gate rows for both? Does §4 risk 3 reference W-OB-4a (not W-OB-4)?
- **Q1.2.** **W-OB-7 8 handlers.** Does §1.1 thread-2 reference the corrected seam shape? Does §2.G enumerate all 8? Does §4 risk 8 say "8 well-shaped handlers" (not "6")? Does §5 say "8 callers"?
- **Q1.3.** **W-OB-5 scope widening.** Does §2.E reference checks beyond `check_onboarding_readiness`? Does the example block use `hai init` not `hai init --guided`? `agent_safe: false` not `true`? Does §2.E acceptance drop the `doctor_check_schema` manifest item per OQ-4?
- **Q1.4.** **v0.2.0 sequencing.** Does §1 metadata theme paragraph remove the "parallelizable with v0.2.0" claim? Does §7 name the v0.1.18 → v0.1.19 → v0.2.0 chain?
- **Q1.5.** **§3 closure-side updates.** Does §3 still contain the old "manifest schema delta worth naming" hedge, or is it cleanly aligned with OQ-4 ("no manifest schema delta")?
- **Q1.6.** **§9 provenance.** Does §9 acknowledge round-1 closure with the 7-finding count + reference to the response_response?

### Q2 — Acceptance bite (round-1 additions)

The round-1 revisions added several new acceptance items + ship gates. Verify each is **mechanically testable**:

- **Q2.1.** §2.E acceptance item 3: `next_action.agent_safe` matches live capabilities manifest. Is the test concretely scoped (loads `hai capabilities --json`, walks every emitted `next_action.command`, asserts equality), or vague?
- **Q2.2.** §2.G acceptance item 3: 9-case test (8 per-handler + 1 reproducer). Does the per-handler list cover all 8 with the right intake-command-line invocation each? Specifically: is `cmd_intake_gaps` testable without complex synthetic state setup?
- **Q2.3.** §6 release-blocker gate "W-OB-4b post-W-OB-2 local-wheel smoke proves default-flip on TTY." How is this asserted at ship-gate time — by reading `dogfood_findings.md` for an explicit "default-flip witnessed" claim, or by re-running the wheel build + test under CI?
- **Q2.4.** §2.B acceptance item 3 (5-case test). Does case (iv-flag) actually use `--non-interactive` as a CLI flag plus mock `isatty()==True`, or does it accidentally test the env var path?

### Q3 — New round-2-only contradictions

Did the revisions introduce contradictions that didn't exist in round 1?

- **Q3.1.** W-OB-4b is now a release-blocker (per §1.2 Severity column + §6 release-blocker list). But §2.D's "What W-OB-4a + W-OB-4b do NOT do" says "Do not commit code." Is "release-blocker dogfood pass that produces no commits" a coherent gate, or does it muddy the ship-gate semantics?
- **Q3.2.** §2.G says "Helper is **additive** — does NOT replace `open_connection` globally." But §2.G acceptance item 2 says "**All eight `cmd_intake_*` handlers** use `open_connection_with_migrations` instead of `open_connection`." That's a partial replacement (intake-only). Is the partial-replacement scope clear enough that an implementer wouldn't accidentally extend it to other handlers (e.g. `hai propose`, `hai synthesize`)?
- **Q3.3.** §2.E widens `next_action` to "every check that emits `hint`." But §2.E acceptance item 1 says "where the hint maps to a concrete command (vs prose like 'investigate manually')." Is the boundary "concrete command vs prose" sharp enough? What if a hint says "check `hai doctor` output for context" — is that a concrete command (`hai doctor`) or prose?
- **Q3.4.** §6 lists `W-OB-4b post-W-OB-2 local-wheel smoke` as release-blocker, but §2.D scenario uses a locally built wheel — there's no automatic CI gate that builds the wheel and runs the smoke. Is the release-blocker honest if it requires a maintainer-driven manual run?

### Q4 — Provenance / external-source skepticism (round-2 spot-checks)

- **Q4.1.** §2.G claims 8 `cmd_intake_*` handlers at lines `gym=62, exercise=300, nutrition=420, stress=643, note=790, readiness=903, gaps=980, weight=1184`. Verify with `grep -n "^def cmd_intake_" src/health_agent_infra/cli/handlers/intake.py`.
- **Q4.2.** §2.G claims `open_connection` at `core/state/store.py:64` and `apply_pending_migrations` at line 243. Verify both.
- **Q4.3.** §2.G claims `cmd_state_init` at `cli/handlers/state.py:46-52` reaches migrations through `initialize_database` (which calls `apply_pending_migrations` at `core/state/store.py:335`). Verify all three line numbers.
- **Q4.4.** §2.E claims `check_onboarding_readiness` at `core/doctor/checks.py:470` and `check_state_db` at line 84. Verify both. Verify `check_state_db` emits `pending_migrations` in its result dict (PLAN claims line 146).
- **Q4.5.** §2.C claims `test_init_onboarding_flow.py` exists and is the W-AA gate. Verify.
- **Q4.6.** §2.E example claims `hai init` is `agent_safe: false`. Verify against `verification/tests/snapshots/cli_capabilities_v0_1_13.json` (or whatever the post-v0.1.17 snapshot is at HEAD).
- **Q4.7.** §1 honesty boundary cites tactical_plan §5G dependency on v0.1.19 → v0.2.0 chain. Verify `tactical_plan_v0_1_x.md:52`.

### Q5 — What round 2 should NOT find

Out-of-scope for round 2 (already settled at round 1):

- Tier classification (settled substantive on the W-OB-2 release-blocker leg).
- All 7 OQ dispositions (settled).
- W-OB-7 absorption shape (W-OB-7 discrete fix, not W-OB-5 absorption — settled at cycle-open).
- The cycle's high-level theme + thesis (settled).

If round 2 wants to reopen any of these, surface as an explicit reopening request, not as a finding.

---

## Step 4 — Output shape

Write findings to `reporting/plans/v0_1_18/codex_plan_audit_round_2_response.md`:

```markdown
# Codex Plan Audit Response — v0.1.18 PLAN.md (D14 round 2)

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS | PLAN_INCOHERENT

**Round:** 2

## Findings

### F-PLAN-R2-01. <short title>

**Q-bucket:** Q1 / Q2 / Q3 / Q4
**Severity:** plan-incoherence | sizing-mistake | dependency-error |
acceptance-criterion-weak | hidden-coupling | settled-decision-conflict |
absence | provenance-gap | summary-surface-sweep-gap | nit
**Reference:** PLAN.md § X.Y, line N (or "absent")
**Argument:** <why this is a finding, with citations>
**Recommended response:** <revise as follows / accept and note as known limitation / disagree>

### F-PLAN-R2-02. ...

## Round-1-revision verification

For each of the 7 revisions, mark VERIFIED / GAPS-FOUND / NOT-PROPAGATED.

| Revision | Status | Note |
|---|---|---|
| Rev 1 — W-OB-4 split | ... | ... |
| Rev 2 — W-OB-7 8 handlers | ... | ... |
| Rev 3 — W-OB-5 scope widening | ... | ... |
| Rev 4 — v0.2.0 sequencing | ... | ... |
| Rev 5 — W-OB-3 test file | ... | ... |
| Rev 6 — §6 ship gate adds | ... | ... |
| Rev 7 — OQ dispositions | ... | ... |

## Closure recommendation

Verdict + named must-fix revisions list (if any) + recommended next-round budget.

If no findings: PLAN_COHERENT, recommend cycle opens with Phase 0 (D11) bug-hunt.
If 1-3 nit-class findings: PLAN_COHERENT_WITH_REVISIONS, close-in-place.
If 4+ findings or any plan-incoherence: PLAN_COHERENT_WITH_REVISIONS or PLAN_INCOHERENT, round 3.
```

---

## Step 5 — Verdict scale

- **PLAN_COHERENT** — open the cycle as written. Phase 0 bug-hunt next.
- **PLAN_COHERENT_WITH_REVISIONS** — open after named revisions land. If revisions are nit-class (text-only, no scope shift), close-in-place is acceptable; round 3 not required.
- **PLAN_INCOHERENT** — do not open. Re-author named sections; round 3.

---

## Step 6 — Out of scope

- Tier classification (settled substantive at round 1).
- All 7 round-1 OQ dispositions (settled).
- W-OB-7 absorption shape (settled at cycle-open).
- Cycle theme + thesis (settled at PLAN-author).
- v0.1.19 / v0.2.0 work (downstream cycles).
- Code changes (Phase 0 not started).

If a finding wants to reopen a settled item, the finding must explicitly justify the reopening with new evidence, not just a different opinion.

---

## Step 7 — Cycle pattern

```
Round 1: PLAN_COHERENT_WITH_REVISIONS (7 findings) — closed
Round 2 (this audit): expected 1-3 findings, predicted summary-surface
    sweep gaps; verdict likely PLAN_COHERENT or COHERENT_WITH_REVISIONS
    close-in-place
Round 3: only if round 2 surfaces new substantial findings
```

Estimated review duration: 0.5-1 session.

---

## Step 8 — Files this audit may modify

- `reporting/plans/v0_1_18/codex_plan_audit_round_2_response.md` (new) — your findings.
- `reporting/plans/v0_1_18/PLAN.md` (revisions, if warranted) — maintainer + Claude apply revisions.
- `reporting/plans/v0_1_18/codex_plan_audit_round_3_prompt.md` (only if R2 verdict requires R3).

**No code changes.** No test runs. No state mutations.
