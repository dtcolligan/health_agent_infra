# Claude Code Session — Open the v0.1.15 cycle

You are starting a fresh Claude Code session to open and execute the v0.1.15 cycle of `health-agent-infra`. D14 plan-audit closed in-place at round 3 (commit `38d4cb3`); the next phase is **Phase 0 (D11) bug-hunt**, then pre-implementation gate, then Phase 1 implementation.

This prompt is the entry point. It is a session-opening *briefing*, not a content prescription — the canonical contract is `AGENTS.md`, `reporting/plans/v0_1_15/PLAN.md`, and the planning-tree templates. Read those before acting.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main, OR a cycle/work branch the maintainer named (e.g. cycle/v0.1.15)
git log --oneline -3
# expect: top commit "v0.1.15 D14 close-in-place at round 3..." (38d4cb3 or later);
# next commit "post-v0.1.14.1 doc-freshness sweep..." (5660fd7);
# next commit "v0.1.14.1 hardening..." (856e689).
ls reporting/plans/v0_1_15/
# expect: PLAN.md, README.md, audit-prompt + audit-response chain × 3 rounds, this file
```

If any don't match — particularly if `pwd` resolves to `/Users/domcolligan/Documents/health_agent_infra/` (the stale checkout, head at `2811669`) — **stop and surface the discrepancy to the maintainer**. AGENTS.md "Authoritative orientation" preamble names this constraint durably.

---

## Step 1 — Read the orientation artifacts

Read in order. The reading is non-trivial because the cycle bundles a scope-restructure (round-0 → round-1 cuts) plus three D14 audit rounds plus pulled-forward v0.1.16 work — there's a lot of cross-doc context an auditor or implementer needs to hold.

1. **`AGENTS.md`** — operating contract. Pay attention to:
   - "Active repo path" preamble (durable dual-repo guard).
   - "Code Vs Skill" invariant — Python owns determinism; skills own judgment.
   - "Governance Invariants" — W57 (target/intent commit gate; W-C is W57-gated).
   - "Settled Decisions" D124-135 (W-29 destination is **v0.1.17**, not v0.1.15).
   - "Do Not Do" line ~417 — cli.py split scheduled for v0.1.17.
   - "Patterns the cycles have validated."
2. **`reporting/plans/strategic_plan_v1.md`** — vision (no edits this cycle).
3. **`reporting/plans/tactical_plan_v0_1_x.md`** — release-by-release plan. **§5B** is the v0.1.15 detail (combined gate cycle), **§5C** is v0.1.16 (empirical post-gate), **§5D** is v0.1.17 (maintainability + eval consolidation).
4. **`reporting/plans/v0_1_15/PLAN.md`** — the cycle's authoritative scope. **D14 closed in-place at round 3.** All 7 W-ids + per-WS contracts + sequencing + ship gates + risks are here. §1.4 has the round-0 → round-1 disposition table; §8 documents the closed OQs (1-9) + Codex round-3 ratifications.
5. **`reporting/plans/v0_1_15/README.md`** — entry point + reading order.
6. **`reporting/plans/v0_1_15/codex_plan_audit_round_3_response.md`** — Codex's round-3 verdict (PLAN_COHERENT_WITH_REVISIONS, close-in-place). Context for what was fixed.
7. **`reporting/plans/v0_1_15/codex_plan_audit_round_3_response_response.md`** — maintainer's round-3 triage.
8. **`reporting/plans/post_v0_1_14/agent_state_visibility_findings.md`** — original F-AV-01..05 findings. **The doc has a SUPERSEDED header note** redirecting to PLAN §2.B as the source of truth for W-A's contract; treat the in-doc F-AV-01 example as historical only.
9. **`reporting/plans/post_v0_1_14/carry_over_findings.md`** — F-PV14-01 detail (in scope) + F-PV14-02 (deferred to v0.1.17).
10. **`reporting/plans/v0_1_14/RELEASE_PROOF.md`** §carry-overs — provenance for W-2U-GATE inheritance.
11. **`reporting/plans/v0_1_16/README.md`** — empirical-by-design next cycle. **Do not pull forward into v0.1.15.**
12. **`reporting/plans/v0_1_17/README.md`** — maintainability + eval consolidation cycle. **Do not pull forward into v0.1.15.** Specifically, W-29 cli.py split lives there, NOT here.

Cross-reference: `pwd` returns the active repo, `git log -3` matches the expected chain, every file the PLAN cites resolves. Surface broken cross-refs as findings.

---

## Step 2 — Phase 0 (D11) bug-hunt (your first deliverable)

Substantive cycles require Phase 0 per AGENTS.md D11. The bug-hunt scope for v0.1.15:

- **Internal sweep** — re-read v0.1.15 PLAN.md against the active source tree. For each W-id (W-GYM-SETID, W-A, F-PV14-01, W-C, W-D arm-1, W-E, W-2U-GATE), spot-check that the cited source line ranges still resolve, that the proposed fix shape is implementable as written, and that no scope leaked from v0.1.16/v0.1.17. Document any drift in `reporting/plans/v0_1_15/audit_findings.md`.
- **Audit-chain probe** — verify that v0.1.14.1's `sync_run_log` + `recommendation_log` + `daily_plan` chains are queryable from main (per AGENTS.md "Patterns the cycles have validated"). Specifically: run `hai explain --as-of 2026-04-30 --user-id u_local_1 --operator` and confirm the bundle renders. Document any audit-chain gaps in `audit_findings.md`.
- **12-persona matrix** — run `verification/dogfood/` persona harness against the post-v0.1.14.1 state model. Per PLAN §6, P7..P12 may be skipped (they're v0.1.17 W-Vb-4 scope), but P1..P6 must run. Document persona-replay findings.
- **Codex external bug-hunt audit** (optional per maintainer) — only fire if the maintainer asks. Default: skip; it's a substantive-tier *option*, not a requirement when D14 ran 3 rounds.

**Phase 0 deliverable:** `reporting/plans/v0_1_15/audit_findings.md` consolidating each finding with `cycle_impact` tag (`revises-scope` / `aborts-cycle` / `nit` / `none`).

**Phase 0 acceptance:** zero `aborts-cycle` findings, OR escalation to maintainer if any aborts-cycle surfaces. `revises-scope` findings loop back to D14 (re-author PLAN section + re-run round-4 audit). `nit` and `none` proceed to pre-implementation gate.

**Estimated effort:** 1-2 days for an experienced session.

---

## Step 3 — Pre-implementation gate

After Phase 0 closes, fire the pre-implementation gate per AGENTS.md cycle pattern:

1. **Foreign-user candidate check.** Per PLAN §4 risk 6: "named candidate must be on file by Phase 0 close." If no candidate is on file at this point, **escalate to the maintainer** with the three-option decision tree: (a) hold cycle open, (b) downgrade to non-shipping candidate-package cycle, (c) defer the gate to v0.1.18. Do NOT proceed to Phase 1 implementation without the maintainer's path choice.
2. **Audit-findings review.** Re-read `audit_findings.md`. Any finding tagged `revises-scope` requires PLAN.md revision + a fresh D14 round-4 audit before Phase 1 opens.
3. **OQ ratification check.** PLAN §8 lists OQ-7/8/9 as "ratify at round-3 close" — confirm the maintainer accepted the Codex round-3 opinions. The default ratifications in §8 are: OQ-7 suppress, OQ-8 commit SHA only, OQ-9 §4.6 procedure with mid-Phase-3 abort sentence. If maintainer wants to override any, surface and revise PLAN.

**Pre-implementation gate deliverable:** `reporting/plans/v0_1_15/pre_implementation_gate_decision.md` recording the candidate-on-file decision + audit-findings disposition + OQ ratification state.

---

## Step 4 — Phase 1 implementation (sequenced per PLAN §1.3)

Phase 1 (parallelizable, lands first):
- **W-GYM-SETID** — gym set-id PK collision fix. Touches `domains/strength/intake.py:96-105`, `cli.py:cmd_intake_gym`, new migration in `core/state/migrations/`. Required fixture at `verification/tests/fixtures/multi_exercise_session.jsonl`. **Per PLAN §4 risk 3:** maintainer pre-gate operator procedure exists separately for recovering already-dropped sets from JSONL via `hai state reproject --cascade-synthesis`; this is NOT the migration's responsibility.
- **W-A** — `hai intake gaps` extension with `present` block + `is_partial_day` (time-only) + `target_status` enum. Pure read-side; capabilities manifest update.
- **F-PV14-01** — CSV-fixture pull isolation marker. Touches `core/pull/garmin.py:43`, `cli.py:183/267`, capabilities manifest source-type tagging.
- **W-C** — `hai target nutrition` daily macro target commit. New table + migration + W57 gate.

Phase 2 (after W-A):
- **W-D arm-1** — partial-day suppression. Reads W-A's `is_partial_day` + `target_status`. Arm-2 (projection) deferred to v0.1.17.
- **W-E** — `merge-human-inputs` skill update consuming W-A presence tokens; optional `morning-ritual` skill. Per F-PLAN-R2-04 + supersede note in `agent_state_visibility_findings.md`, the in-doc F-AV-01 example is historical; PLAN §2.B is the source of truth.

Phase 3 (gate ship-claim):
- **W-2U-GATE** — recorded foreign-machine session. **Acceptance-1 threshold is load-bearing:** one full session reaches `synthesized` with at most one brief in-session question to the maintainer. Multiple interventions or any maintainer keyboard time = failure (P0). Build candidate package per PLAN §2.G shape (wheel + sdist from final v0.1.15 branch commit, commit SHA in install record, no gate-candidate tag).

**Per-WS commit cadence:** atomic commits per W-id; PLAN §2's per-WS contracts are the acceptance criteria; tests-first for each (lock invariants before implementation).

**Implementation review (D15 IR):** after Phase 1+2 complete, fire the Codex implementation review prompt (template at `reporting/plans/_templates/codex_implementation_review_prompt.template.md`). Empirical norm 3 rounds: 5 → 2 → 1-nit → SHIP / SHIP_WITH_NOTES.

---

## Step 5 — Operating discipline (durable across the cycle)

These rules apply throughout the session. Most come from agent-feedback memory written during the v0.1.15 scope-restructure session (2026-05-02/03):

- **Verify the active repo at every session boundary.** `pwd` + `git log -1` before reading or writing planning/source files. Stale checkout at `/Users/domcolligan/Documents/health_agent_infra/` must be ignored.
- **Verify CLI surface before recommending operator procedures.** Run `hai <cmd> --help` before writing any plan/risk/runbook prose that names a `hai` invocation. The "selective `hai restore`" finding in F-PLAN-R2-06 cost a round of audit; don't repeat it.
- **Read state before asking the user.** When the user provides input that the runtime should already know, check `hai state read --domain <d>` first.
- **Cross-check runtime classifications against `hai target list`.** The nutrition classifier's `calorie_balance_band` is config-driven, not target-aware (until W-C ships). Don't echo `surplus` against a deficit-vs-target intake.
- **Auto-pull wearable data when missing.** `hai pull --source intervals_icu` without asking when recovery/sleep telemetry is missing.
- **Dom prefers one-line `git commit -m` messages on this project.** No heredoc bodies.
- **Plan-and-execute cadence.** Tests first; phase-numbered atomic commits; hard gates between phases. No skipping Phase 0 because D14 closed.
- **Lead with the verdict.** Cite sources. Separate verified facts from inference. Avoid flattery.

---

## Step 6 — When to escalate to the maintainer

Stop and ask the maintainer when:
- Phase 0 surfaces an `aborts-cycle` finding.
- No foreign-user candidate is on file at Phase 0 close.
- A `revises-scope` Phase 0 finding requires a PLAN.md change (loop back to D14 round 4).
- Implementation hits a Phase-2 dependency that wasn't documented in PLAN §1.3 (e.g., W-A's `target_status` query needs a schema element W-C didn't provide).
- The recorded gate session breaches the acceptance-1 threshold (P0). Stop the session, fix the cause, re-record.
- More than 3 rounds of D15 IR don't converge — surfaces cycle-too-large risk per AGENTS.md substantive-cycle norm.

For everything else within scope, **execute autonomously per the PLAN**. The cycle pattern is well-trod; your job is to follow it, not re-invent it.

---

## Step 7 — Out of scope for this session

- v0.1.16 PLAN authoring (empirical-by-design; PLAN authors only after v0.1.15's gate session).
- v0.1.17 work (W-29 cli.py split, eval substrate, W-B, W-D arm-2). Pulling these forward is the exact failure mode the round-0 self-audit cut.
- v0.2.x scope.
- AGENTS.md governance edits beyond the W-29-close edit at v0.1.15 ship.

---

## Step 8 — Deliverables checklist (across the cycle, not this session alone)

By the time v0.1.15 ships:
- [ ] `audit_findings.md` (Phase 0 close)
- [ ] `pre_implementation_gate_decision.md`
- [ ] Per-WS implementation commits (7 W-ids, atomic)
- [ ] Foreign-user candidate package (wheel + sdist + install record)
- [ ] Recorded gate-session transcript at `reporting/plans/v0_1_15/foreign_machine_session_<YYYY-MM-DD>.md`
- [ ] State DB snapshot at `verification/dogfood/foreign_user/state_snapshot/<YYYY-MM-DD>/`
- [ ] Install record at `verification/dogfood/foreign_user/install_record_<YYYY-MM-DD>.json`
- [ ] D15 IR rounds (1-3) with response files
- [ ] `RELEASE_PROOF.md`
- [ ] `REPORT.md`
- [ ] AGENTS.md D124-135 W-29 status update at ship (still scheduled v0.1.17, but the ship date should be recorded)
- [ ] AUDIT.md + CHANGELOG entries
- [ ] PyPI publish

You will not finish all of this in one session. **Your immediate goal: close Phase 0 cleanly + fire the pre-implementation gate + start Phase 1 if time allows.**

Begin.
