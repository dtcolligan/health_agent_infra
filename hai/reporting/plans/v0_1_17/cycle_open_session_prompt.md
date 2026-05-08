# Claude Code Session — Open the v0.1.17 cycle

You are starting a fresh Claude Code session to open the v0.1.17 cycle of `health-agent-infra`. **No prior cycle work has been done on v0.1.17 itself.** Your immediate goal is to author `PLAN.md` and the Codex D14 plan-audit prompt so the maintainer can launch round-1.

This prompt is the entry point. It is a session-opening *briefing*, not a content prescription — the canonical contract is `AGENTS.md`, the v0.1.17 README, and the planning-tree templates. Read those before acting.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main, OR a cycle/work branch the maintainer named (e.g. cycle/v0.1.17)
git log --oneline -3
# expect top: the v0.1.16-cancellation + v0.1.17/18/19 restructure commit (2026-05-04)
ls reporting/plans/v0_1_17/
# expect: README.md, this file (cycle_open_session_prompt.md). NO PLAN.md yet — you author it.
```

If `pwd` resolves to `/Users/domcolligan/Documents/health_agent_infra/` (the stale checkout, head at `2811669`) — **stop and surface to the maintainer**. AGENTS.md "Active repo path" preamble names this constraint durably.

---

## Step 1 — Read the orientation artifacts (in order)

The cycle inherits 10 W-ids from prior cycles' carry-over registers. Authoring PLAN.md cleanly requires reading the source-of-truth for each, not just the README catalogue row.

1. **`AGENTS.md`** — operating contract. Pay attention to:
   - "Active repo path" preamble.
   - "Code Vs Skill" invariant.
   - "Governance Invariants" (W57 still applies; W-B body-comp intake is not autonomous).
   - "Settled Decisions" — W29/W30 destination (this cycle) + the 2026-05-04 v0.1.16-cancellation chain.
   - "Do Not Do" — the cli.py-split entry; you ARE the cycle that lifts it.
   - "Patterns the cycles have validated" — provenance discipline + summary-surface sweep + honest partial-closure naming + audit-chain settling shapes.
2. **`reporting/plans/strategic_plan_v1.md`** — vision (no edits this cycle).
3. **`reporting/plans/tactical_plan_v0_1_x.md`** — release-by-release plan. **§5C** is the cancelled v0.1.16, **§5D** is THIS cycle, **§5E/§5F** are the post-v0.1.17 cycles. The §5B v0.1.15 update callout dated 2026-05-04 explains the renumber.
4. **`reporting/plans/v0_1_17/README.md`** — the cycle's authoritative provisional scope. 10 W-ids, three-phase sequencing (mechanical → eval substrate → carry-overs).
5. **`reporting/plans/v0_1_15/PLAN.md` §7** — deferred-work register (the source for which v0.1.15 work named this cycle as destination).
6. **`reporting/plans/v0_1_14/RELEASE_PROOF.md` §carry-overs** — provenance for **W-29, W-AH-2, W-AI-2, W-AM-2, W-Vb-4** inheritance into this cycle. (W-AM-2 was absorbed into W-AI-2 at v0.1.14 ship; check the disposition table.)
7. **`reporting/plans/post_v0_1_14/carry_over_findings.md`** — F-PV14-02 (`hai sync purge`) detail.
8. **`reporting/plans/post_v0_1_14/agent_state_visibility_findings.md`** — F-AV-02 (W-B body-comp surface) + F-AV-04 arm-2 (W-D arm-2 partial-day projection) detail. **The doc has a SUPERSEDED header note** for the v0.1.15-shipped portions; only F-AV-02 + F-AV-04-arm-2 remain in scope here.
9. **`reporting/plans/v0_1_15/codex_implementation_review_response.md`** — F-IR-04 (W-C-EQP query-plan stability assertions; named-deferred from v0.1.15 IR round 1).
10. **`reporting/plans/v0_1_13/`** — original W-29-prep boundary audit. The boundary table archived at `reporting/docs/archive/cycle_artifacts/cli_boundary_table.md`; the parser/capabilities byte-stability regression test landed at v0.1.13.
11. **`reporting/plans/v0_1_18/README.md`** + **`v0_1_19/README.md`** — the cycles AFTER this one. **Do not pull their work forward.** v0.1.18 owns onboarding-quality (W-OB-1..6); v0.1.19 owns the foreign-user empirical contract (renumbered from cancelled v0.1.16).
12. **`reporting/plans/v0_1_16/README.md`** — cancellation note. Read for context on why v0.1.17 promoted to next-active 2026-05-04 with the former v0.1.16-must-close precondition retired.

Cross-reference: every file the v0.1.17 README cites resolves on disk. Surface broken cross-refs as findings before authoring PLAN.

---

## Step 2 — Author `reporting/plans/v0_1_17/PLAN.md` (your first deliverable)

Follow the v0.1.14/v0.1.15 PLAN structure (twice-validated):

- **First line:** tier annotation (`Tier: substantive`).
- **§1.1 Theme.** One paragraph naming the ship claim ("internal correctness + maintainer-side cleanup; eval substrate expansion against synthetic + dogfood evidence; mechanical refactor cli.py 9217 → handler-group split"). Note the renumber: this cycle's W-AH-2 ships honestly as "synthetic-coverage expansion," not "foreign-user-validated coverage" — that's v0.1.19's claim.
- **§1.2 Workstream catalogue.** Table with one row per W-id: `§2.X | W-id | Title | Effort | Source | Severity`. Source the rows from the v0.1.17 README provisional table; severity from the originating release-proof.
- **§1.3 Sequencing.** Phase 1 (W-29 + W-30 mechanical foundation) → Phase 2 (W-AH-2 + W-AI-2 + W-AM-2 + W-Vb-4 eval substrate, parallelizable) → Phase 3 (F-PV14-02 + W-B + W-D arm-2 + W-C-EQP carry-overs/projections).
- **§1.4 Disposition table** — for each W-id, the round-0 self-audit outcome (in / cut / partial / fork-defer). At PLAN-author time most are "in" provisionally; D14 may cut some.
- **§2.A..§2.J Per-WS contracts.** For each W-id: (a) source citation, (b) acceptance criteria as testable statements, (c) scope boundaries (what's in / what's deferred), (d) cross-deps, (e) operator-side procedures if any. **W-29 specifically:** byte-stable `hai capabilities --json` manifest before/after split; the parser/capabilities regression test is the ship-claim gate, not a nice-to-have.
- **§3 Ship gates.** Tests, mypy, bandit, capabilities round-trip, persona matrix (P1-P12; W-Vb-4 brings P7-P12 into scope), AUDIT.md + CHANGELOG entries, ship-time freshness checklist from AGENTS.md.
- **§4 Risks register.** Most-likely failure modes with mitigations. Top candidates: W-29 split introducing a subtle import cycle in handler modules; W-AH-2 scenarios encoding wrong contracts (mitigated by running against current synthetic + dogfood matrix); W-B body-comp migration colliding with v0.2.0 schema-group plan.
- **§5 Cross-references.** Hard-link every cited file by relative path.

Empirical norm: the PLAN draft will trigger D14 findings on cross-cutting consistency — that's expected and fine. Don't try to pre-empt every finding; ship a clean draft.

---

## Step 3 — Author the Codex D14 plan-audit prompt

```bash
cp reporting/plans/_templates/codex_plan_audit_prompt.template.md \
   reporting/plans/v0_1_17/codex_plan_audit_prompt.md
```

Customise:
- **"Why this round"** — first substantive cycle since v0.1.12/v0.1.14 (twice-validated 4-round D14 norm). v0.1.13 was 17 W-ids but doc-heavy; v0.1.17 is 10 W-ids but spans cli.py mechanical split + eval substrate expansion + new schema (W-B). Substantial cross-cutting surface.
- **Step 1 reading list** — Step 1 above of *this* file, plus the new PLAN.md.
- **Step 2 audit questions** — customise to v0.1.17's actual workstream catalogue. Specifically probe: (a) does W-29's split preserve `hai capabilities --json` byte-stable; (b) does W-AH-2's scenario expansion encode the *current* runtime contract (post-v0.1.15 W-A presence + W-C target); (c) does W-B body-comp's migration layout cohere with v0.2.0's planned schema additions (CP-PATH-A); (d) does the renumber narrative (former v0.1.16 → v0.1.19) propagate to every PLAN cross-reference.
- **Steps 0/3/4/5/6/7** — keep stable; the template already encodes them.

Hand `PLAN.md` + `codex_plan_audit_prompt.md` to the maintainer for D14 round-1 launch. The maintainer fires Codex; you wait for `codex_plan_audit_response.md` to land.

---

## Step 4 — D14 audit rounds (after maintainer launches round 1)

**Empirical settling shape (twice-validated):** 4 rounds, **10 → 5 → 3 → 0** findings. Budget 2-4 rounds; round 2 typically catches second-order contradictions from round-1 revisions. v0.1.17's catalogue is mostly inherited from prior release-proofs, so cross-cutting consistency findings should be lower than v0.1.12/v0.1.14 — author rounds 2-3 might settle one round earlier. Don't bet on it.

For each round:
1. Read `codex_plan_audit_round_N_response.md` end-to-end.
2. Author `_response_response.md` with per-finding triage: accept (revise PLAN), reject (with citation), defer (named destination).
3. Revise PLAN.md per accepted findings.
4. If round N has *more* findings than N-1, **re-read your own diff** — the round-(N-1) revision likely introduced second-order issues.
5. Hand revised PLAN to maintainer for round-(N+1) launch.

Settling target: `PLAN_COHERENT` (no findings) or `PLAN_COHERENT_WITH_REVISIONS` (close-in-place).

---

## Step 5 — Phase 0 (D11) bug-hunt (after D14 settles)

Substantive cycles require Phase 0. Scope for v0.1.17:

- **Internal sweep.** Re-read v0.1.17 PLAN against the active source tree. For each W-id, spot-check that cited file paths + line ranges still resolve, that the proposed fix shape is implementable, and that no scope leaked from v0.1.18/v0.1.19. Document drift in `audit_findings.md`.
- **Audit-chain probe.** Run `hai explain --as-of <recent-day> --user-id u_local_1 --operator` and confirm bundle renders cleanly against current state. v0.1.15.1's keyring fall-through hardening is in tree; verify intervals.icu pull still works.
- **12-persona matrix.** Run `verification/dogfood/runner /tmp/persona_run`. P1-P6 baseline; P7-P12 in scope this cycle (W-Vb-4 lifts them). Baseline establishes the pre-implementation persona profile; W-Vb-4 acceptance is "all 12 personas reach `synthesized` cleanly."
- **Codex external bug-hunt audit** — *optional* per maintainer. Default skip.

**Phase 0 deliverable:** `reporting/plans/v0_1_17/audit_findings.md`. Each finding tagged `revises-scope` / `aborts-cycle` / `nit` / `none`.

---

## Step 6 — Pre-implementation gate

After Phase 0:
1. **Audit-findings review.** `revises-scope` → loop back to D14 (re-author PLAN section + fresh round). `aborts-cycle` → escalate.
2. **No foreign-user prerequisite.** Unlike v0.1.15, v0.1.17 has no foreign-user candidate-on-file dependency. The original v0.1.16-must-close precondition retired 2026-05-04.
3. **OQ ratification check** — none expected pre-D14, but if PLAN.md surfaced any during authoring, ratify here.

Deliverable: `reporting/plans/v0_1_17/pre_implementation_gate_decision.md`.

---

## Step 7 — Phase 1+2+3 implementation (sequenced per PLAN §1.3)

**Phase 1 — Mechanical foundation:**
- **W-29** — cli.py split (1 main + 1 shared + 11 handler-group, <2500 lines each per v0.1.13 boundary table). Byte-stable `hai capabilities --json`; the parser/capabilities regression test holds across the split. Lands first because every other W-id touching cli.py would create merge friction.
- **W-30** — capabilities-manifest schema-freeze regression test (test only; freeze itself is v0.2.3).

**Phase 2 — Eval substrate (parallelizable):**
- **W-AH-2** — scenario fixture expansion 35 → 120+. Persona-runner reads post-v0.1.15 schema (W-A presence + W-C target).
- **W-AI-2** — `hai eval review` CLI surface.
- **W-AM-2** — 4 fork-deferred escalate-tagged scenarios (sleep / strength / stress / nutrition).
- **W-Vb-4** — persona-replay residual P7-P12 (6 personas).

**Phase 3 — Carry-overs + nice-to-haves:**
- **F-PV14-02** — `hai sync purge` surgical-cleanup CLI. Independent.
- **W-B** — `hai intake weight` body-comp surface + new `body_comp` table + migration. New schema.
- **W-D arm-2** — partial-day nutrition end-of-day projection. Reads `target` table (post-v0.1.15 W-C migration 025).
- **W-C-EQP** — EXPLAIN QUERY PLAN stability assertions for the W-A active-window query against `target` post-migration 025.

**Per-WS commit cadence:** atomic commits per W-id; tests-first for each.

**D15 IR (after Phase 3 complete):** copy `_templates/codex_implementation_review_prompt.template.md`, customise. Empirical norm: 3 rounds, 5 → 2 → 1-nit. Verdict: SHIP or SHIP_WITH_NOTES.

---

## Step 8 — Operating discipline (durable)

- **Verify the active repo at every session boundary.** `pwd` + `git log -1` before any planning/source edit.
- **Provenance discipline.** Verify cited file paths + line numbers + function names + exact strings before citing them. Don't trust prior-round assertions.
- **Summary-surface sweep on partial closure.** If any W-id partial-closes, sweep PLAN.md §1.1/§1.2/§1.3/§2.X/§3/§4 + RELEASE_PROOF + REPORT + CARRY_OVER + tactical plan + CHANGELOG + design docs in lockstep. Missing one is the canonical IR-round-2 finding.
- **Honest partial-closure naming.** `in-cycle (W-X here)` vs `partial-closure → v0.1.18 W-X-2` vs `fork-deferred → v0.1.19 W-X`. Don't dress up partial work.
- **D12 coercer use.** Every `int(cfg)` / `float(cfg)` / `bool(cfg)` for thresholds uses `core.config.coerce_*` helpers. New code that bypasses the helpers is a bug.
- **Read state before asking the user.** `hai state read --domain <d>` first.
- **Lead with verdict.** Cite sources. Separate verified facts from inference. Avoid flattery. (Maintainer working-style memory.)
- **Dom prefers one-line `git commit -m` messages on this project.** No heredoc bodies.
- **Plan-mode triggers** per CLAUDE.md still apply: AGENTS.md "Settled Decisions" edits, large cli.py changes (especially W-29), >2 new test files.

---

## Step 9 — Escalation triggers

Stop and ask the maintainer when:
- Phase 0 surfaces an `aborts-cycle` finding.
- A `revises-scope` finding requires PLAN.md change (loop back to D14 round-N+1).
- W-29 split breaks `hai capabilities --json` byte-stability (release-blocker; maintainer's call on retry shape vs. defer).
- W-AH-2 scenario design surfaces a runtime-contract bug — that's a Phase 0 finding, not silent absorption.
- W-B body-comp migration design conflicts with v0.2.0 schema-group plan (CP-PATH-A).
- More than 4 rounds of D14 don't converge — surfaces cycle-too-large risk.
- More than 3 rounds of D15 IR don't converge — same risk shape.

For everything else within PLAN scope, **execute autonomously**.

---

## Step 10 — Out of scope for this cycle

- **v0.1.18 onboarding work** (W-OB-1..6). README quickstart pivot ALREADY landed pre-cycle (in-flight, 2026-05-04); v0.1.18 PLAN.md will close W-OB-1 at cycle-open. Do NOT do W-OB-2 default-flip here — it depends on the W-29 split landing first.
- **v0.1.19 foreign-user empirical** (W-2U-FIX-P1/P2, W-EXPLAIN-UX-2). Renumbered from cancelled v0.1.16. No transcript exists; cycle opens when one does.
- **v0.2.x scope** — weekly review (W52), factuality (W58D), insight ledger (W53), judge shadow (W58J), schema freeze (W-30 final destination).
- **AGENTS.md governance edits** beyond the W-29-status update at v0.1.17 ship.
- **New domains, new live sources, new MCP exposure paths** — all `Do Not Do` per AGENTS.md.

---

## Step 11 — Deliverables checklist (across the cycle)

By v0.1.17 ship:
- [ ] `PLAN.md` (your first deliverable; ships when D14 settles `PLAN_COHERENT`)
- [ ] `codex_plan_audit_prompt.md` + responses + response_responses for all D14 rounds
- [ ] `audit_findings.md` (Phase 0 close)
- [ ] `pre_implementation_gate_decision.md`
- [ ] Per-WS implementation commits (10 W-ids, atomic)
- [ ] `codex_implementation_review_prompt.md` + responses for all D15 IR rounds
- [ ] `RELEASE_PROOF.md` (first line: tier annotation per D15)
- [ ] `REPORT.md`
- [ ] AGENTS.md W29/W30 settled-decision update at ship (W-29 closed; W-30 final destination remains v0.2.3)
- [ ] `Do Not Do` cli.py-split entry retired (since v0.1.17 lifts it) or annotated "completed v0.1.17"
- [ ] AUDIT.md + CHANGELOG entries
- [ ] Ship-time freshness checklist from AGENTS.md
- [ ] PyPI publish (only after IR settles SHIP / SHIP_WITH_NOTES)

You will not finish all of this in one session. **Your immediate goal: author `PLAN.md` + `codex_plan_audit_prompt.md` cleanly, and hand them to the maintainer for D14 round-1.**

Begin.
