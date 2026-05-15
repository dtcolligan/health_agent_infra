# Phase 1 Convergence Report

> **Notice (2026-05-15):** This file is preserved as the historical
> NeurIPS 2027 main-conference framing record. For current paper scope,
> calendar, roster, cost ceiling, and empirical contribution, see
> [`PREPRINT_RESCOPE.md`](PREPRINT_RESCOPE.md). The headline frame,
> title, mechanism inventory (M4-M8 + M9-TX), lineage anchor, and
> closed reframes transfer unchanged; the Engels extension, full model
> roster, USD 1,500 ceiling, 50-trajectory adversarial layer, and
> NeurIPS 2027 main-conference deadline do not. Resolve any conflict in
> favour of `PREPRINT_RESCOPE.md`.

**Status:** Phase 1 closed.
**Closed:** 2026-05-11
**Total rounds:** 3 (R3, R4, R5; rounds 1-2 predated this orchestration
file structure)
**Convergence path:** All three stop-test signals fired AND the Phase 1
escape valve (three consecutive SHIP_WITH_NOTES rounds with zero
paper-§-level findings) triggered. Either path independently closes
Phase 1.

---

## One-page summary of the locked framing

### Paper

**Title:** *Deterministic Software Contracts as Trusted Monitors in AI
Control Protocols* (D-FRAME-016)

**Target venue:** NeurIPS 2027 main conference, May 2027 deadline.

**Merge status:** Paper 1 (runtime contract architecture +
GovernedAgentBench) merged with Paper 2 (Engels Backdoor Code
extension) into single main-conference submission (D-FRAME-009).
Paper 2 redirects to S1 fine-tuning sequel (D-FRAME-010 + D-FRAME-027).

**Decision gate:** Engels pilot July 2026 (~$18.60 cost; D-FRAME-018).
If pilot fails the 6-clause commit rule, revert to Trajectory A
(separate workshop + conference papers).

### Framing anchors

- **Headline frame:** Deterministic software contract that
  operationalizes a safety spec as the trusted monitor in an AI control
  protocol for bounded agent operation (D-FRAME-001).
- **Lineage anchor:** Triple — AI control protocols (Greenblatt 2024)
  + safety specs (OpenAI Model Spec, Anthropic Model Spec Midtraining,
  Deliberative Alignment) + LLM-monitor baselines (Constitutional
  Classifiers, Hierarchical Summarization) (D-FRAME-002).
- **Threat model:** Capability-failure + targeted adversarial layer
  (50 trajectories across 4 attack types + adaptive-vs-DRG-0)
  (D-FRAME-003 + D-FRAME-022).
- **Headline empirical:** Engels et al. 2025 Backdoor Code extension;
  deterministic Runtime Guard (DRG-0) at general Elo = 0 (D-FRAME-004).
- **Direct LLM-monitor competitor:** Hierarchical Summarization
  (Anthropic Feb 2025); bounded empirical contrast at §7.6 on L6 only,
  2-week + $200 caps (D-FRAME-005 + D-FRAME-024).
- **Closest benchmark prior:** ST-WebAgentBench (Levy et al., ICML
  2025). Load-bearing differentiation: runtime-mode intervention with
  mechanism-isolable ablation under a held-constant prompt
  (D-FRAME-006 + D-FRAME-026).
- **Benchmark framing:** Framing D — contract-as-intervention with
  measured model-scale substitution (D-FRAME-007).

### Architecture (mechanism inventory, D-FRAME-017)

Five independently ablatable mechanisms + one held-constant
non-ablatable:

- **M4** validation
- **M5** `agent_safe` dispatch refusal
- **M6** W57 proposal/commit gate
- **M7** refusal (scoped narrowly to clinical-boundary surfaces; JSON
  output exempt)
- **M8** audit evidence emission (renamed from "audit chain")
- **M9-TX** transaction integrity (held constant, non-ablatable)

### Predeclared design (D-FRAME-020/021/022/023)

- **Model roster:** 6 Houdinis (Qwen2.5-3B local HF / Qwen2.5-7B-
  Instruct-Turbo Together / Qwen2.5-32B & 72B Fireworks / Haiku 3.5
  retired pilot-only / Sonnet 4 with 2026-06-15 retirement) + 3 Guards
  (DRG-0 deterministic / Haiku 3.5 retired pilot-only / gpt-4o-mini-
  2024-07-18). Successors named: claude-haiku-4-5-20251001 for new
  Haiku cells; claude-sonnet-4-6 re-anchor if §7.5 slips past
  2026-06-15.
- **Thresholds:** AND-pass rule across 7 primary metrics + 7
  zero-tolerance critical violations. Per-metric pass thresholds and
  ±5pp sensitivity tests pre-registered.
- **Attack policy:** 50 trajectories across 5 attack types (refusal
  bypass 8 / mutation escalation 8 / audit tampering 8 / schema
  evasion 8 / adaptive-vs-DRG-0 18). Adjudication: deterministic
  where possible + fixed rubric for ambiguous cases + Dom blind
  adjudication + secondary gpt-4o-mini judge.
- **Cost ceiling:** USD 1,500 hard ceiling across all model API calls
  (D-FRAME-023).

### Paper-killer preempts (D-FRAME-019)

Two paper-killer critiques identified with pre-committed structural
rebuttals:

1. **Framing-overclaim (rhetorical).** Preempt: reframe as
   "trusted-monitor substrate for bounded AI-control protocols." Cite
   arXiv:2510.09462 (Adaptive Attacks on Trusted Monitors) in §2/§5.
2. **Greenblatt DRG-artifacts (empirical).** Preempt: pre-registered
   DRG inputs + ablations + FP rates + adaptive-attack-vs-DRG-0
   trajectory type in the §8 attack policy.

### Out-of-scope (D-FRAME-025 + locked outline)

- Coding-agent reference runtime: **Appendix E sketch only.** No
  second runtime build before this paper. Sketch must not be cited
  as evidence in abstract, contributions, or results.
- Full attack-policy substitution red-team: NOT in v1.
- Clinical or medical decision-making claims: NEVER.
- Sandbagged or password-locked executor models: NOT in v1.
- Cross-domain generalization beyond personal wellness: NOT in v1
  (sketch only).

---

## Locked decisions table (27 framing decisions)

D-FRAME-001 through D-FRAME-023 + D-FRAME-024 through D-FRAME-027.
Full provenance in `framing_v2/ORCHESTRATOR_STATE.md` "Locked
decisions" table.

| ID | Topic | Closed in |
|---|---|---|
| D-FRAME-001 | Headline framing | Rounds 1-2 |
| D-FRAME-002 | Lineage anchor | Rounds 1-2 |
| D-FRAME-003 | Threat model | Rounds 1-2 |
| D-FRAME-004 | Headline empirical (Engels) | Rounds 1-2 |
| D-FRAME-005 | Direct competitor (HS) | Rounds 1-2 |
| D-FRAME-006 | Closest published prior (ST-WAB) | Rounds 1-2 |
| D-FRAME-007 | Benchmark framing | Rounds 1-2 |
| D-FRAME-008 | Target venue (NeurIPS 2027 main) | Rounds 1-2 |
| D-FRAME-009 | Trajectory (merged paper) | Rounds 1-2 |
| D-FRAME-010 | Paper 2 redirect (S1 FT) | Rounds 1-2 |
| D-FRAME-011 | Decision gate (Engels pilot July 2026) | Rounds 1-2 |
| D-FRAME-012 | Drop "user-owned structured data" from title | Rounds 1-2 |
| D-FRAME-013 | Personal wellness as instantiation | Rounds 1-2 |
| D-FRAME-014 | A2 reframe closed | Rounds 1-2 |
| D-FRAME-015 | B1 (no red-team) closed | Rounds 1-2 |
| D-FRAME-016 | Final title (10w form) | Round 3 + Dom pick |
| D-FRAME-017 | Mechanism inventory (M4-M8 + M9-TX) | Round 3 |
| D-FRAME-018 | Engels pilot protocol | Round 3 |
| D-FRAME-019 | Two paper-killer critiques | Round 3 |
| D-FRAME-020 | Predeclared model roster | Round 4 |
| D-FRAME-021 | Predeclared thresholds | Round 4 |
| D-FRAME-022 | Adversarial attack policy | Round 4 |
| D-FRAME-023 | Cost ceiling ($1,500) | Round 4 + Dom pick |
| D-FRAME-024 | Bounded HS empirical contrast | Round 5 |
| D-FRAME-025 | Coding-agent slice = Appendix E sketch | Round 5 |
| D-FRAME-026 | ST-WAB differentiation (table + load-bearing axis) | Round 5 |
| D-FRAME-027 | Paper 2 = S1 fine-tuning of bounded operators | Round 5 |

---

## Audit verdict log

| Round | Verdict | Findings | Paper-§-level | Provenance |
|---|---|---|---|---|
| Round 3 | SHIP_WITH_NOTES | 7 (0 critical, 0 major, 5 minor, 2 nit) | 0 | `round_3/AUDIT_RESPONSE.md` |
| Round 4 | SHIP_WITH_NOTES | 7 (0 critical, 0 major, 4 minor, 3 nit) | 0 | `round_4/AUDIT_RESPONSE.md` |
| Round 5 | SHIP_WITH_NOTES | 6 (0 critical, 0 major, 2 minor, 4 nit) | 0 | `round_5/AUDIT_RESPONSE.md` |

**Three consecutive SHIP_WITH_NOTES with zero paper-§-level findings
in the terminal round = Phase 1 escape valve triggered.**

---

## Outstanding action items for Phase 2

Per the three round-synthesis files (`round_3/SYNTHESIS.md`,
`round_4/SYNTHESIS.md`, `round_5/SYNTHESIS.md`), Phase 2 inherits
~25 doc-alignment action items across the paper-planning files,
benchmark spec, project cold-start docs, HAI runtime docs (light
touch), and operating contracts.

The audit-findings-closure batch must explicitly close
F-CDX-RFR-R1-01..11 from
`research/runtime_contracts_paper/codex_runtime_first_reframe_audit_response.md`
against the locked framing.

The final repo-wide audit (dispatched once at end of Phase 2) must
verify internal consistency, terminology, version-tag freshness, and
no stale references to A2/B1 framing.

---

## Outstanding action items for Engels pilot (July 2026)

- [ ] Dom verifies "five Houdini attempts per sample" claim against
  arXiv:2504.18530 §4 PDF (F-AUDIT-3-05, pre-pilot).
- [ ] Pre-pilot: materialize APPS competition test set, apply
  selection procedure (sha256 seed, 60 samples + 10 smoke separate),
  freeze `engels_pilot_manifest.jsonl`.
- [ ] Pre-pilot: implement DRG-0 modules 1-6 with frozen JSON config
  hash before primary runs.
- [ ] Pre-pilot: tune DRG-0 thresholds on the 10 smoke samples only.
  Never on the primary 60.

---

## Calendar binding

| Date | Event | Status |
|---|---|---|
| 2026-05-11 | Phase 1 convergence | DONE |
| 2026-06-15 | Sonnet 4 retirement; §7.5 paper-claim run must complete OR re-anchor to claude-sonnet-4-6 | Open binding |
| 2026-07-15 (target) | Phase 2 doc alignment complete | Pending |
| 2026-07-20 to 2026-08-05 (target) | Engels pilot (de-risks merge) | Pending |
| 2026-08-10 (target) | Pilot decision gate | Pending |
| 2026-11 (target) | Mechanism ablations complete | Pending |
| 2027-02 (target) | Full Engels run | Pending |
| 2027-03 (target) | Red-team complete | Pending |
| 2027-03 (target) | Hierarchical Summarization bounded contrast complete | Pending |
| 2027-04 (target) | Manuscript v1 | Pending |
| 2027-05-15 (approx) | NeurIPS 2027 submission deadline | Pending |

---

## Next step

Phase 2 documentation alignment begins. The orchestrator drafts batch
1 worker prompt for the paper-planning files (~8 files) per
PHASE_PLAN.md §3 batch structure and dispatches to Codex.

Phase 2 cadence differs from Phase 1: audit is end-of-phase only,
not per batch.
