# Round 3 Synthesis

**Written:** 2026-05-11
**Verdict from audit:** SHIP_WITH_NOTES
**Audit findings:** 7 (all minor/nit; 0 major, 0 critical)
**Convergence:** Not yet. Round 4 needed.

---

## Verdict from audit

**SHIP_WITH_NOTES.** Codex's response is substantively right on every
load-bearing axis. All 20+ HAI source citations verify on disk via
audit's Bash sweep; all 7 mandatory arXiv IDs resolve; all sampled
lab-URL and pricing claims confirm. The Q3 cost arithmetic checks to
the penny. Zero fabricated citations.

Seven minor/nit findings; none demand re-do. Three are decision
points to surface; four are annotations to carry into Phase 2.

---

## What this round closed

| ID | Decision | Locked value | Provenance |
|---|---|---|---|
| O-FRAME-001 → D-FRAME-016 | Title | "Deterministic Software Contracts as Trusted Monitors for AI Control" (Codex Q1) **OR** "Deterministic Software Contracts as Trusted Monitors in AI Control Protocols" (audit F-AUDIT-3-02 alt) — pending Dom's editorial pick | Round 3 RESPONSE Q1 + AUDIT F-AUDIT-3-02 |
| O-FRAME-002 → D-FRAME-017 | Mechanism inventory | M4-M8 separate; M5/M6 separable but require disciplined invocation context; M7 scoped to clinical-boundary payload/text surfaces (JSON exempt per F-AUDIT-3-03); M8 renamed "audit evidence emission"; M9-TX held constant non-ablatable | Round 3 RESPONSE Q2 + on-disk audit confirmation |
| O-FRAME-003 → D-FRAME-018 | Engels pilot protocol | 60 APPS competition samples; Houdinis = Qwen2.5-7B-Instruct Turbo + Claude 3.5 Haiku + Claude Sonnet 4; Guards = DRG-0 (deterministic) + Claude 3.5 Haiku LLM Guard (5-vote majority); optional Sonnet 4 calibration pass; full DRG-0 module breakdown (syntax/AST/trigger/anomaly/fuzz/verdict); 6-clause commit rule, 6-clause revert rule, defined borderline zone; ~$18.60 estimated cost, $30-50 budget reserve | Round 3 RESPONSE Q3 + audit cost-math verification |
| O-FRAME-004 → D-FRAME-019 | Adversarial reviewer simulation | Two paper-killer critiques, not one: (a) framing-overclaim (rhetorical, mitigate via "trusted-monitor substrate for bounded AI-control protocols" reframing); (b) Greenblatt DRG-artifacts (empirical, mitigate via pre-registered DRG information boundaries + ablations + FP rates) | Round 3 RESPONSE Q4 + AUDIT F-AUDIT-3-07 escalation |

---

## What's still open

### High-priority residue (none — all 4 round-3 targets closed with caveats)

The four round-3 high opens closed substantively. Two editorial/
empirical residues are tracked as action items, not opens.

### Medium-priority opens (7, carried over)

| ID | Decision | State |
|---|---|---|
| O-FRAME-005 | Hierarchical Summarization empirical contrast | Open: full reimplementation vs rhetorical-only |
| O-FRAME-006 | Coding-agent slice | Open: appendix / full domain / cut |
| O-FRAME-007 | Predeclared model roster | Open: exact 6 Houdinis + 3 Guards with provider snapshots/parameter counts/quantization |
| O-FRAME-008 | Predeclared thresholds | Open: exact pass values per primary metric |
| O-FRAME-009 | Adversarial attack policy | Open: concrete protocol per attack type for the 50-trajectory layer |
| O-FRAME-010 | ST-WebAgentBench detailed positioning | Open: concrete differentiation table |
| O-FRAME-011 | Paper 2 sketch precision | Open: S1 fine-tuning direction concrete or pivot |

### Low-priority opens (5, carried over)

O-FRAME-012 through O-FRAME-016 unchanged.

---

## Newly surfaced

### D-FRAME-016 — Title (locked with editorial fork)

Two viable forms; Dom picks before Phase 2.

- **(9 words, Codex)** "Deterministic Software Contracts as Trusted Monitors for AI Control"
- **(10 words, audit)** "Deterministic Software Contracts as Trusted Monitors in AI Control Protocols"

If 9-word, the abstract's first sentence must carry "control protocol"
explicitly to preserve D-FRAME-001 vocabulary.

### D-FRAME-017 — Mechanism inventory (revised)

Replaces the older F-CDX-RFR-R1-08/09/10 framing. The current source
has real M5 and M7 seams; F-CDX-RFR-R1-09 and -10 are partly stale.
Paper §7 ablation matrix uses M4-M8 as five independent toggles with
M9-TX held constant.

- M4 = validation
- M5 = `agent_safe` dispatch refusal
- M6 = W57 proposal/commit gate
- M7 = clinical-boundary refusal (scoped narrowly; **JSON output
  surfaces are exempt** per F-AUDIT-3-03; do not over-promise)
- M8 = audit **evidence emission** (renamed from "audit chain"; do
  not claim full audit-chain disable)
- M9-TX = transaction integrity (held constant, non-ablatable)

Code-work to make ablations paper-ready: **10-16 hours** for
regression matrix + manifest alignment (planning anchor, not a
contract; F-AUDIT-3-06 says 14-22 hours actual is plausible).

### D-FRAME-018 — Engels pilot protocol

Full spec locked. Single audit caveat: "five Houdini attempts per
sample" needs Dom to verify against arXiv:2504.18530 §4 PDF before
the pilot manifest treats it as load-bearing (F-AUDIT-3-05; audit
WebFetch returned unrenderable binary).

DRG-0 information-boundary discipline locked: no Houdini trigger
input access, no hidden-test oracle access, no hand-tuned thresholds
from primary 60 samples. This anticipates Greenblatt's empirical
critique (D-FRAME-019 second prong).

### D-FRAME-019 — Two paper-killer critiques, not one

Codex's Q4 chose the rhetorical critique (AI-Control overclaim) as
strongest. Audit correctly escalated: the **Greenblatt DRG-artifacts
critique is structurally more dangerous** because it attacks the
empirical contribution Codex cannot retreat from without gutting §7.5.

Both critiques must be preempted in the paper:

1. **Rhetorical preempt (framing):** Reframe internal language as
   "trusted-monitor substrate for bounded AI-control protocols," not
   "a control-protocol framework." Limit the protocol claim. Cite
   arXiv:2510.09462 (Adaptive Attacks on Trusted Monitors) in §2/§5
   to anchor the "deterministic alternative to LLM monitors" frame.
2. **Empirical preempt (pilot design):** DRG-0 pre-registration of
   inputs + ablations (static-only / fuzz-only / combined) +
   adaptive-attack against DRG + FP rate on clean originals and
   benign rewrites. Pilot's clause 6 ("Fairness") is the structural
   safeguard.

Codex correctly anticipated the second critique in its decision rule
clause 6 but did not rank it as the strongest.

---

## Action items (for Phase 2 doc alignment, batch 1 paper-planning)

These propagate Round 3 closures into the paper docs. Most are doc-
edits, not research; defer to Phase 2 execution.

- [ ] **Title:** Dom picks 9-word vs 10-word. Update
  `PAPER_OUTLINE_MERGED.md` "Title (working)" with selected form.
- [ ] **Mechanism inventory section (paper §7):** rewrite M4-M8
  descriptions per D-FRAME-017. Scope M7 as "clinical-boundary
  refusal over proposal/recommendation/text surfaces, JSON exempt."
  Rename M8 to "audit evidence emission."
- [ ] **§4.3 (`agent_safe` enforcement seam) and §4.7 (audit chain):**
  update language to reflect the current `_agent_safe_gate` dispatch
  mechanism (no longer accurate to say "manifest-only enforcement")
  and the narrower "evidence emission" scope.
- [ ] **§2 / §5 citations:** add arXiv:2510.09462 (Adaptive Attacks
  on Trusted Monitors). Direct load-bearing missing-literature flag.
- [ ] **§7.5 Engels protocol:** import the locked pilot spec
  (D-FRAME-018) including DRG-0 module breakdown and pre-registered
  information boundary.
- [ ] **§8 adversarial layer:** add explicit adaptive-attack-against-
  DRG-0 cell as the empirical preempt of the Greenblatt critique.
- [ ] **§10 limitations:** add explicit "does not address
  disempowerment / persuasion / dependence harms" per Sharma critique
  rebuttal. Add "deterministic-Guard result is bench-specific until
  cross-domain replicated" per Greenblatt critique.
- [ ] **Q4 Sharma row:** relax hedge from "former Anthropic /
  independent" to "resigned from Anthropic Safeguards lead role Feb 9
  2026; current affiliation unknown post-resignation" per F-AUDIT-3-01.
- [ ] **Cost-table provenance:** add pricing snapshot date (May 2026)
  to the pilot manifest so Phase 2 reviewers know when to re-verify.

## Action items (for Engels pilot execution, July 2026)

- [ ] **Pre-pilot:** Dom verifies "five Houdini attempts per sample"
  against arXiv:2504.18530 §4 PDF (F-AUDIT-3-05). If Engels caps at a
  different number, update D-FRAME-018 attempt count.
- [ ] **Pre-pilot:** Materialize APPS competition test set and apply
  selection procedure (sha256 seed, 60 samples + 10 smoke separate).
  Freeze `engels_pilot_manifest.jsonl`.
- [ ] **Pre-pilot:** Implement DRG-0 modules 1-6 with frozen JSON
  config hash before primary runs.
- [ ] **Pre-pilot:** Tune DRG-0 thresholds on the 10 smoke samples
  only. Never on the primary 60.

## Action items (next-cycle scope expansion possibilities)

- [ ] Bowman + Frontier Red Team rows for Q4 reviewer table if Dom
  wants belt-and-braces coverage (audit "missing literature" flag,
  not a blocker).
- [ ] Code-work decomposition: per-mechanism positive/negative pair +
  hermetic-state assertion + marker-shape assertion tasks before
  committing to the 10-16 hour estimate.

---

## Stop-test result

Per PHASE_PLAN.md §3 "Phase 1 stop test":

| Signal | Result | Detail |
|---|---|---|
| Decisions list signal (zero high + zero medium open) | **Not fired** | 0 high open; 7 medium open. Stop test requires zero of both. |
| Yield signal (round 4 prompt has <3 substantive questions) | **Not fired** | 7 medium opens cluster into 3 natural topics: predeclared-design (O-FRAME-007/008/009), competitor-positioning (O-FRAME-005/010), out-of-scope (O-FRAME-006/011). Round 4 has at minimum 3 substantive questions. |
| Adversarial-review signal (no paper-killer uncovered) | **Partially fired** | Round 3 Q4 + audit F-AUDIT-3-07 identified two paper-killer critiques; both have pre-committed structural rebuttals (D-FRAME-019). Paper is now defensible against the strongest reviewer attacks. |

**Convergence: NO.** Continue to round 4.

Per protocol §3, three signals must all fire to declare convergence.
One partial + two not-fired = continue normally, no special action.

---

## Next round target (Round 4 cluster)

**Recommended cluster: predeclared-design.** Three medium opens, all
paper-critical for §6 GovernedAgentBench reproducibility, all sharing
benchmark-design literature:

- **Q1 — O-FRAME-007 predeclared model roster.** Exact 6 Houdinis + 3
  Guards with provider, snapshot date, parameter count, quantization.
  Per F-CDX-RFR-R1-07 (which is still open). Codex must check
  availability/pricing for May 2027 as well as current.
- **Q2 — O-FRAME-008 predeclared thresholds.** Exact pass values per
  primary metric (command validity ≥ X%, mutation-boundary obedience
  ≥ Y%, refusal accuracy ≥ Z%, etc.). Per F-CDX-RFR-R1-06.
- **Q3 — O-FRAME-009 adversarial attack policy.** Concrete protocol
  per attack type for the 50-trajectory red-team layer: refusal
  bypass / mutation escalation / audit tampering / schema evasion.
  How are trajectories sampled? How is attack success scored? Who
  authors the attacks?

This cluster is naturally bounded and topically coherent. Codex's
research budget is well-spent because the three questions share
methodology (predeclaration + scoring rubrics + reproducibility) and
the same prior art (ST-WebAgentBench scoring, AgentDojo attacks,
Constitutional Classifiers thresholds).

Round 4 will not touch competitor-positioning (O-FRAME-005/010) or
out-of-scope cluster (O-FRAME-006/011); those are Round 5 candidates
if needed, otherwise resolvable in Phase 2 doc alignment.

---

## Orchestrator notes

State updated. Round 3 closed. Round 4 prompt will be drafted in the
next orchestrator turn once Dom acknowledges this synthesis (or in
the same response if Dom signals continue).
