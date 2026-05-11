# Framing v2 Orchestration — COMPLETE

**Status:** Orchestration closed.
**Closed:** 2026-05-11
**Total rounds (Phase 1):** 3 substantive (R3 + R4 + R5; R1+R2 predated this file structure)
**Total batches (Phase 2):** 6 + audit-findings-closure + final repo-wide audit
**Total framing decisions locked:** 27 (D-FRAME-001 through D-FRAME-027)

---

## One-paragraph summary

The runtime-contracts paper has a locked title, venue, scope, threat
model, mechanism inventory, predeclared roster, predeclared
thresholds, attack policy, cost ceiling, calendar binding, two
paper-killer preempts, and a 215-word cross-domain sketch. The
benchmark schemas are tightened (`claim_tier` required, T3/T4
conditional on `model_roster_hash`, 15/15 schema-contract tests
pass). 33 active docs across `research/`, `benchmark/`, `project/`,
`hai/docs/`, plus the 3 operating contracts (`AGENTS.md`, `CLAUDE.md`,
`README.md`) all carry the merged-paper framing. Pre-merge framing
survives only in clearly-marked historical provenance. Phase 1 closed
by yield exhaustion (3 consecutive SHIP_WITH_NOTES with zero
paper-§-level findings in the terminal round). Phase 2 closed
SHIP_WITH_NOTES with 5 minor/nit findings (3 fixed at closure, 2
carried to a post-Phase-2 polish pass).

---

## What this orchestration produced

### Phase 1 (research convergence)

- `framing_v2/CONVERGED.md` — locked framing summary + 27 decisions.
- `framing_v2/round_3/`, `round_4/`, `round_5/` — research artifacts
  (PROMPT, RESPONSE, AUDIT_PROMPT, AUDIT_RESPONSE, SYNTHESIS per
  round).

### Phase 2 (documentation alignment)

- `framing_v2/phase_2_doc_alignment/batches/batch_1..6_*/` — six
  per-batch directories with PROMPT.md + EDITS_SUMMARY.md.
- `framing_v2/phase_2_doc_alignment/FINAL_AUDIT_PROMPT.md` +
  `FINAL_AUDIT_RESPONSE.md` — terminal cross-repo consistency audit.
- `framing_v2/phase_2_doc_alignment/COMPLETE.md` — Phase 2 closure
  record with carry-over list.
- 33 active docs updated across 6 batches plus the audit-findings-
  closure annotation on `codex_runtime_first_reframe_audit_response.md`.

### State management

- `framing_v2/ORCHESTRATOR_STATE.md` — durable working memory with
  full locked-decisions table, open-decisions log, stop-test
  snapshots, audit verdicts, and decisions journal.

---

## The locked paper at a glance

| Aspect | Locked value |
|---|---|
| **Title** | Deterministic Software Contracts as Trusted Monitors in AI Control Protocols (D-FRAME-016) |
| **Venue** | NeurIPS 2027 main conference, May 2027 deadline (D-FRAME-008) |
| **Headline framing** | A deterministic software contract operationalizes a safety spec as the trusted monitor in an AI control protocol for bounded agent operation (D-FRAME-001) |
| **Trajectory** | Merged paper 1 + paper 2 (D-FRAME-009); paper 2 redirects to S1 fine-tuning at ICML 2028 / NeurIPS 2028 (D-FRAME-010 + D-FRAME-027) |
| **Decision gate** | Engels pilot July 2026; revert to Trajectory A if pilot fails (D-FRAME-011 + D-FRAME-018) |
| **Threat model** | Capability-failure + targeted adversarial layer (50 trajectories: 8 refusal-bypass + 8 mutation-escalation + 8 audit-tampering + 8 schema-evasion + 18 adaptive-vs-DRG-0) (D-FRAME-003 + D-FRAME-022) |
| **Mechanism inventory** | M4 validation / M5 agent_safe / M6 W57 proposal gate / M7 clinical-boundary refusal (narrow, JSON exempt) / M8 audit evidence emission (renamed) / M9-TX transaction integrity (held constant) (D-FRAME-017) |
| **Predeclared roster** | 6 Houdinis (Qwen 3B/7B/32B/72B + Haiku 3.5 retired pilot-only + Sonnet 4 with 2026-06-15 retirement) + 3 Guards (DRG-0 + Haiku 3.5 + gpt-4o-mini); successors named (D-FRAME-020) |
| **Predeclared thresholds** | AND-pass rule across 7 primary metrics + 7 zero-tolerance critical violations + ±5pp sensitivity test (D-FRAME-021) |
| **Cost ceiling** | USD 1,500 hard ceiling (D-FRAME-023) |
| **Direct competitor** | Hierarchical Summarization (D-FRAME-005); bounded empirical contrast at §7.6 on L6 only, 2-week + $200 caps (D-FRAME-024) |
| **Closest benchmark prior** | ST-WebAgentBench (Levy et al., ICML 2025); load-bearing differentiation axis = runtime-mode intervention with mechanism-isolable ablation under a held-constant prompt (D-FRAME-006 + D-FRAME-026) |
| **Paper-killer preempts** | Framing-overclaim (rhetorical) + Greenblatt DRG-artifacts (empirical); both have pre-committed structural rebuttals (D-FRAME-019) |
| **Cross-domain** | Appendix E sketch only (215 words), anti-overclaim required (D-FRAME-025) |
| **Title-drop** | "User-owned structured data" framing dropped from title (D-FRAME-012); personal wellness is instantiation, not framing (D-FRAME-013) |
| **Closed reframes** | A2 capability-elicitation (D-FRAME-014); B1 no-red-team (D-FRAME-015) — not to be reopened |

---

## What this orchestration validated as a pattern

Recorded in `AGENTS.md` "Patterns the cycles have validated" at
batch 5 closure:

- **Two-phase structure:** Phase 1 research + Phase 2 doc alignment.
- **Worker-auditor-orchestrator triad:** Codex worker (external,
  user-driven); Claude Code Agent auditor (in-session, fresh
  subagent context); Claude Code orchestrator (holds plan + state).
- **Phase 1 stop test:** three signals (decisions-list / yield /
  adversarial-review).
- **Phase 1 escape valve:** three consecutive SHIP_WITH_NOTES rounds
  with zero paper-§-level findings in the terminal round.
- **Phase 2 cadence:** batched doc-edit work with end-of-phase audit
  only, not per-batch.
- **Durable state via ORCHESTRATOR_STATE.md:** single source of
  truth across context resets and fresh sessions.
- **Empirical settling shapes:** ~3-5 substantive rounds in Phase 1;
  6 batches + final audit in Phase 2; doc-alignment is faster than
  research convergence.

---

## Outstanding carry-over (post-orchestration)

Not blocking the next substantive project step (Engels pilot July
2026). Tracked in `phase_2_doc_alignment/COMPLETE.md`:

1. **F-AUDIT-PHASE2-02 + F-AUDIT-PHASE2-04 sweep** — workshop-as-
   current language in 5 paper-lane planning files; "sensitive user-
   owned data" residuals in 4 prior-art docs.
2. **Pre-pilot artifact commits** — `prompts/deployment_full_v1.md`,
   `scorer_config.paper_v1.json`, `model_roster.md` before §7-§8
   paper-claim runs.
3. **Hermetic-mode E2E validation** — confirm resolver list (HAI_STATE_DB
   + HAI_BASE_DIR + config path + no network/auth) end-to-end before
   §7-§8 runs.
4. **Test alignment** — 2 stale assertions in
   `project/tests/test_project_reframe_docs_alignment.py`.
5. **Work-packet template completeness** — pass over WORK_PACKETS.md
   to satisfy F-CDX-RFR-R1-14 + F-CDX-RFR-R1-15 partial closures.

---

## Reading order for a fresh session

If you are a future orchestrator or researcher opening this
directory, read in this order:

1. `framing_v2/CONVERGED.md` — locked framing summary.
2. `framing_v2/ORCHESTRATOR_STATE.md` — full decisions table.
3. This file (`ORCHESTRATION_COMPLETE.md`) — what just shipped.
4. `framing_v2/phase_2_doc_alignment/COMPLETE.md` — Phase 2 details.
5. `framing_v2/phase_2_doc_alignment/FINAL_AUDIT_RESPONSE.md` — last
   audit's findings + carry-over.

The round and batch directories are full per-cycle provenance; read
them only if you need to understand how a specific decision was
reached.

---

**Phase 1 + Phase 2 done.** The repo is internally engineered for
the merged-paper framing. The next substantive step is the Engels
pilot (July 2026).
