Open the v0.2.0 implementation cycle. PLAN_COHERENT achieved
2026-05-07 after 4 D14 rounds settling 10 → 5 → 3 → 1nit. Phase 0
closed; D14 closed; cycle opens for Phase 2 implementation.

Goal: drive v0.2.0 from cycle-open through ship in this session if
possible. Realistic scope is 25-37 days, so a single session
likely won't complete the full cycle — end at a coherent handoff
if not. Do not truncate the audit chain to fit a session boundary.

Read in this order before doing anything:

1. `~/.claude/projects/-Users-domcolligan-health-agent-infra/memory/project_v0_2_0_cycle_handoff.md`
   (resume protocol; commit head fa8d637; first-move guidance).
2. `reporting/plans/v0_2_0/PLAN.md` (851 LOC; canonical scope; all
   4 D14 rounds' revisions inline-marked).
3. `reporting/plans/v0_2_0/audit_findings.md` (Phase 0 sweep + 13
   F-PHASE0-* findings + maintainer adjudication).
4. `reporting/plans/v0_2_0/codex_plan_audit_round_4_response_response.md`
   (D14 chain closure summary; settling shape signature).
5. AGENTS.md "Settled Decisions" + "Do Not Do" + "Patterns the
   cycles have validated".

First concrete action — DO NOT write code yet:

W-PROV-2 spike. Read `domains/running/classify.py` + the running
accepted-state table schema. Assess whether the recovery R6
conditional-emission pattern (`domains/recovery/policy.py:215-230`)
maps cleanly across the 5 dormant domains. Output: 1-page note at
`reporting/plans/v0_2_0/w_prov_2_spike.md` committed as
`chore(v0.2.0)`. Anchors the W-PROV-2 effort estimate (PLAN §2.A
says 2-4d) before any code commits. 30-60 min cost.

Then implementation per PLAN §1.3 sequencing DAG:

  Phase 1 (parallel): W-PROV-2 + 3 doc-only adjuncts
                      (W-MCP-THREAT, W-COMP-LANDSCAPE, W-NOF1-METHOD).
  Phase 2 (after W-PROV-2): W-EVCARD-DAILY (mig 027) →
                            W-EVCARD-WEEKLY (mig 028).
  Phase 3 (after carriers): W52 → W-FACT-ATOM → W58D.
  Phase 4 (opportunistic): W-2U-GATE-2 if candidate surfaces.
  Phase 5: D15 IR + RELEASE_PROOF + freshness sweep + manual TTY
           ship gate → push → twine upload.

D15 IR empirical norm: 2-3 rounds settling 5 → 2 → 1-nit.
Auto-draft each round's next prompt at round close per
feedback_auto_draft_next_round_prompt.md; don't ask permission.
Persona matrix release gate: 13/13, 0 findings, 0 crashes.

Surface a 3-5 bullet summary of v0.2.0 scope as you understand it
after the read order, then begin the W-PROV-2 spike. Surface
spike findings + commit. Then propose Phase 1 commit cadence
before writing W-PROV-2 code.

Do not unilaterally revise PLAN scope post-D14-close without an
audit trail (CP at `reporting/plans/v0_2_0/cycle_proposals/CP-N.md`
+ external review). Cycle abort triggers per PLAN §3.4 — surface
immediately if any fires; do not silently absorb.

Established patterns active: rigor over velocity for architecture
tradeoffs; run commands don't print them for git/hai mutations;
pause only for PyPI publish + destructive shared-state ops; honest
partial-closure naming if any W-id undershoots.

If the session ends before v0.2.0 ships, write a fresh
`project_v0_2_0_cycle_handoff_<date>.md` memory at session close
naming the cycle state, current commit head, and resume protocol.
Honest partial-closure naming applies — do not commit incomplete
work as if complete.
