# Round 5 Synthesis

**Written:** 2026-05-11
**Verdict from audit:** SHIP_WITH_NOTES
**Audit findings:** 6 (0 critical, 0 major, 2 minor, 4 nit)
**Paper-§-level findings:** 0
**Convergence:** **YES.** Phase 1 closes by yield exhaustion.

---

## Verdict from audit

**SHIP_WITH_NOTES with explicit escape-valve trigger.** Three
consecutive SHIP_WITH_NOTES rounds (R3, R4, R5) with zero paper-§-
level findings in R5. The Phase 1 escape valve per PHASE_PLAN.md §3
fires: "If three consecutive rounds return SHIP_WITH_NOTES with no
new substantive findings, declare Phase 1 done by yield exhaustion
even if signal 1 hasn't fully fired."

All primary-source claims verified — RBR arXiv:2411.01111 (Mu et
al., NeurIPS 2024), Haiku 4.5 pricing ($1/$5 per MTok), ST-
WebAgentBench 222 tasks + Completion under Policy + Risk Ratio
metric names, Deliberative Alignment latency-cost framing, MSM
agentic-OOD-generalization, cost arithmetic ($0.0575/chunk,
$0.06–0.07 simple L6, $0.29–0.30 multi-step L3/L4), L1–L7 family
mapping, and full consistency with D-FRAME-010/013/020/022 and
D-PROJ-016.

Six minor/nit findings. All editorial / citation-density /
methodology-gloss / operational-estimate. None change §2.3, §2.4,
§7.6, §10, §11, Appendix D, or Appendix E in shape.

---

## What this round closed

| ID | Decision | Locked value | Provenance |
|---|---|---|---|
| O-FRAME-005 → D-FRAME-024 | HS empirical contrast | **Bounded** at §7.6 on L6 governance/refusal (optional L5 if L6 lands early). Two-week and $200 caps. Pre-register hs_monitor_v1, prompt hashes, model id `claude-haiku-4-5-20251001`, verdict schema. Demote to §2.3 prose only if adapter misses cap. Section 7.6 renamed "Bounded Hierarchical Summarization contrast." | Round 5 RESPONSE Q1a + AUDIT verified |
| O-FRAME-006 → D-FRAME-025 | Coding-agent slice | **Appendix sketch only.** No second runtime build before this paper. Sketch must be anti-overclaiming: must not be cited as evidence in abstract, contributions, or results. 215-word draft sketch present. | Round 5 RESPONSE Q2 + D-PROJ-016 consistency |
| O-FRAME-010 → D-FRAME-026 | ST-WebAgentBench differentiation | 6-row differentiation table locked. **Load-bearing axis: "runtime-mode intervention with mechanism-isolable ablation under a held-constant prompt."** §2.3 + §2.4 prose draft provided for Phase 2 import. | Round 5 RESPONSE Q1b + AUDIT verified |
| O-FRAME-011 → D-FRAME-027 | Paper 2 sketch | **S1 fine-tuning of bounded operators on the contract.** Headline: "Trained operators reach contract-compliance at smaller scales than untrained operators." Frame as **scale substitution after a runtime floor**, not as "alignment training makes the model safe." Paper 1 setup requirements: §11 future-work paragraph; keep `fine_tuned_local` schema slot; freeze paper 1 roster/prompt/scorer/manifests; reserve GAB v2 train/val/test split; pre-register no-private-data recipe; Appendix D recipe description (future-work only). | Round 5 RESPONSE Q3 + AUDIT verified |

---

## What's still open

### High-priority residue: NONE
### Medium-priority residue: NONE

All medium opens closed.

### Low-priority opens (5, carry into Phase 2 as doc-alignment items)

| ID | Decision | Phase 2 disposition |
|---|---|---|
| O-FRAME-012 | Constitutional Classifiers head-to-head | Phase 2 batch 1: add CC citation at §7.6 metric-shape (per F-AUDIT-5-05) and §2.3 LLM-monitor baselines. Skip the empirical head-to-head; CC's published Pareto IS the comparison anchor. |
| O-FRAME-013 | Reproducibility surface | Phase 2 batch 1: codify into §6.4-6.6 and Appendix A (predeclared roster + scorer_config_hash + manifest snapshot). Already determined by D-FRAME-020/021/022. |
| O-FRAME-014 | Cross-domain extension appendix | Phase 2 batch 1: import Round 5 Q2's 215-word sketch as Appendix E body. D-FRAME-025 already determined the scope. |
| O-FRAME-015 | Scope-cut decisions pre-committed | Phase 2 batch 1: §10 limitations should explicitly name "if pilot returns null result, revert to Trajectory A" (D-FRAME-011 already locked) and "if HS adapter misses cap, demote §7.6 to §2.3 prose" (D-FRAME-024). |
| O-FRAME-016 | Threat model formalization | Phase 2 batch 1: §3 threat model imports D-FRAME-003 (capability-failure + targeted adversarial) and D-FRAME-022 attack-policy scope statement. Lock §3.1/§3.2/§3.3 prose in Phase 2. |

None of these need new research. All are doc-alignment work.

---

## Newly surfaced

### D-FRAME-024 — Bounded HS empirical contrast

Three implementation guardrails:

- **Scope:** L6 governance/refusal only (optional L5 if early).
- **Caps:** two weeks Dom-time + $200 API spend.
- **Fallback:** demote to §2.3 prose only; do not allow scope expansion.

§7.6 renames to "Bounded Hierarchical Summarization contrast." This
is editorial; Phase 2 batch 1 propagates.

### D-FRAME-025 — Coding-agent slice = Appendix E sketch

The 215-word draft from RESPONSE §Q2 is the canonical Appendix E
body. Phase 2 batch 1 imports it as-is. Anti-overclaiming language
is non-negotiable: "this paper does not demonstrate cross-domain
generalization; it specifies how the same contract interface would be
instantiated in another domain."

### D-FRAME-026 — ST-WebAgentBench differentiation locked

The 6-row table from RESPONSE §Q1b is the canonical §2.4 differentiation
artifact. Load-bearing axis: **runtime-mode intervention with
mechanism-isolable ablation under a held-constant prompt.**

### D-FRAME-027 — Paper 2 = S1 fine-tuning of bounded operators

Headline: "Trained operators reach contract-compliance at smaller
scales than untrained operators." Frame as scale-substitution-after-
runtime-floor.

Six paper-1-setup requirements:

1. §11 future-work paragraph with the headline.
2. Keep `fine_tuned_local` schema slot; do not run/imply a fine-tuned
   result in paper 1.
3. Freeze paper 1's model roster, prompt template, scorer config,
   manifest snapshots, runtime modes, threshold logic.
4. Reserve a GovernedAgentBench v2 train/validation/test split for
   fine-tuning, with explicit L7 drift and L6 refusal coverage.
5. Pre-register no-private-data recipe (synthetic fixture states
   only, LoRA/QLoRA, decoding settings, checkpoint hash, data
   provenance, model card).
6. Appendix D describes the fine-tuning recipe as future work only
   (base model, data schema, target metrics, forbidden data sources).
   No performance expectations as claims.

---

## Action items (Phase 2 doc alignment, batch 1 paper-planning)

These propagate Round 5 closures + audit minor findings into the
paper docs.

- [ ] **§7.6 rename:** "Hierarchical Summarization head-to-head" →
  "Bounded Hierarchical Summarization contrast." Import D-FRAME-024
  guardrails (L6 only, 2w + $200 caps, demote fallback). HS
  methodology framing must NOT include the "optional classifier"
  stage as a documented HS feature (F-AUDIT-5-01); soften to
  "we extend HS with an optional classifier stage" or drop entirely.
- [ ] **§7.6 metric shape:** cite Constitutional Classifiers
  (arXiv:2501.18837) as Pareto-reporting precedent (F-AUDIT-5-05).
- [ ] **§7.6 manifest reference:** correct "v2 manifest 189 KB" to
  "HAI v0.2.0 manifest snapshot at
  `benchmark/governed_agent_bench/manifests/hai_0_2_0.json` ≈ 189 KB"
  (F-AUDIT-5-02).
- [ ] **§7.6 implementation note:** widen to "16–35 hours with
  calibration iteration" or quote the two-week wall-clock cap
  instead of the 16-24h estimate (F-AUDIT-5-06).
- [ ] **§2.4 ST-WebAgentBench:** import D-FRAME-026 6-row
  differentiation table + load-bearing axis sentence.
- [ ] **§2.3 LLM-monitor baselines:** import RESPONSE §Q1b prose
  draft. Add CC citation as Pareto-reporting anchor.
- [ ] **Appendix E:** import RESPONSE §Q2 215-word sketch. Add
  anti-overclaim header: "this appendix is not evidence that the
  HAI results generalize."
- [ ] **§11 future work + §12 conclusion:** add paper-2 headline
  paragraph ("Trained operators reach contract-compliance at smaller
  scales than untrained operators") + scale-substitution framing.
- [ ] **§11 Deliberative Alignment gloss:** if DA is cited in §11
  prose, replace "instruction-following weaknesses" with "latency
  cost and forces the model to infer the spec from labeled examples
  rather than learn it directly" (F-AUDIT-5-03).
- [ ] **Appendix D fine-tuning recipe:** add 1-paragraph future-work
  description per D-FRAME-027 requirement 6. Explicitly future-work,
  no performance claims.
- [ ] **§7.6 / Appendix coverage prose:** include L2 (setup/recovery)
  in the family-fit discussion. State it explicitly as "usable but
  not best-fit" or "out of scope for bounded contrast" (F-AUDIT-5-04).
- [ ] **§3 threat model:** lock §3.1/§3.2/§3.3 prose against
  D-FRAME-003 + D-FRAME-022 scope statement (O-FRAME-016).
- [ ] **§10 limitations:** explicit fallback clauses for pilot
  null-result revert + HS cap miss (O-FRAME-015).

## Action items (Phase 2 doc alignment, batch 2 benchmark-spec)

- [ ] **`BENCHMARK_SPEC.md`:** add L2 family description if currently
  underspecified (or confirm §44-62 is sufficient per audit's repo
  verification log).
- [ ] **GAB v2 reservation:** add a reserved-for-paper-2 section to
  BENCHMARK_SPEC.md naming the train/val/test split + L1-L7 coverage
  expectation. Do not populate (paper 2 work, not paper 1).

---

## Stop-test result

| Signal | Result | Detail |
|---|---|---|
| Decisions list signal (zero high + zero medium open) | **FIRED** | 0 high; 0 medium remaining (O-FRAME-005/006/010/011 closed; O-FRAME-007/008/009 closed in round 4; O-FRAME-017 closed by Dom 2026-05-11). 5 low-priority opens carry into Phase 2 as doc-alignment work, not research opens. |
| Yield signal (round 6 prompt has <3 substantive questions) | **FIRED** | Zero substantive opens remaining for new research. Round 6 prompt would have nothing paper-§-level to ask. |
| Adversarial-review signal (no paper-killer critique uncovered) | **FIRED** | Round 3 Q4 identified two paper-killers with pre-committed structural rebuttals (D-FRAME-019); rounds 4 and 5 surfaced no new paper-killers. Paper is defensible against the strongest reviewer attacks. |

**Convergence: YES.** All three signals fired. Phase 1 closes.

**Phase 1 escape valve:** Triggered independently. Three consecutive
SHIP_WITH_NOTES rounds (R3 / R4 / R5) with zero paper-§-level
findings in R5. Either path (full signal trigger OR escape valve)
closes Phase 1.

---

## Next: Phase 2 documentation alignment

Per PHASE_PLAN.md §3 "Phase 2 — Documentation alignment" and
ORCHESTRATOR_PROTOCOL.md §9, Phase 2 begins immediately. Worker
remains Codex; audit cadence shifts to end-of-phase only (not per
batch).

Phase 2 batches (per PHASE_PLAN.md §3):
1. **Paper planning files** (~8 files).
2. **Benchmark spec files** (~6 files).
3. **Project cold-start files** (~6 files).
4. **HAI runtime docs** (~5 files, light touch).
5. **Operating contracts** (3 files: AGENTS.md, CLAUDE.md, README.md).
6. **Historical provenance** (4 files, mark superseded).

Plus: **audit-findings-closure batch** to close
F-CDX-RFR-R1-01..11 against the merged framing.

Plus: **final repo-wide audit** dispatched once at end of Phase 2.

Calendar binding: Phase 2 target completion mid-July 2026 (before
Engels pilot window). Sufficient time given Dom's bandwidth.

---

## Orchestrator notes

`CONVERGED.md` to be written next. ORCHESTRATOR_STATE.md updates to
mark Phase 1 closed and Phase 2 ready to begin.
