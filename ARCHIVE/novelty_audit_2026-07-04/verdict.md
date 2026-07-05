# Novelty verdict: the conjunction survives; four PAPER.md sentences do not

Adjudicated 2026-07-04 (final synthesis pass) against every hunt and
neighbor file in this directory (hunt_0..5.md, neighbors_0..6.md) and
against primary sources directly. Verification basis, stated per item
below, is one of:

- FULL-TEXT-LOCAL: quote grepped this session from a pdftotext/HTML
  extraction cached in this directory (forge.txt, phantompolicy.txt,
  airguard.txt, symbolic_guardrails.txt, promptsdontprotect.txt,
  abstain_full.html, camel.txt, progent.txt, demm_bench.txt).
- ABSTRACT-THIS-PASS: arXiv abstract re-fetched verbatim by this
  synthesis pass (ContextCov, TeamBench, TRACE, Harness-MU,
  ConstraintRot, Verifier Tax, LogiSafetyBench, Mechanical
  Enforcement).
- SWEEP: verified by a sweep agent against primary sources but not
  re-derived here; flagged where load-bearing.

The sweep agents were a cheaper model and two sweep-level fabrications
were caught upstream (a CaMeL WebFetch that invented a factorial
design with fake verbatim quotes, and a fabricated Prompts Don't
Protect abstract with a wrong task count of 150 and a wrong 11-18pp
reduction range). No adjudication below rests on a sweep summary
alone for its load-bearing quote.

## Headline verdict

**The conjunction novelty claim SURVIVES.** No located paper runs the
crossed specify-vs-enforce 2x2 (contract-in-prompt present/withheld x
runtime-enforcement on/off, all four cells) decomposed per governance
mechanism (M4-M8), under the verifiability / goal-conflict /
capability moderators, with first-attempt scoring on the telling
axis, a deterministic offline scorer, and a released benchmark that
holds the two levers apart, together with the harness-blindness
methodological contribution. The 24 pre-identified threat entries
deduplicate to 15 distinct papers; all adjudicate at narrows_claim or
below; none reaches breaks_conjunction.

**Four sentences in PAPER.md are falsified or undercut as written and
must not appear in the draft:**

1. **"the enforced-not-told cell (verified unclaimed across the
   neighbors above)" (PAPER.md line 196). False unqualified.** FORGE
   (arXiv 2602.16708) realizes an enforced-not-told condition by
   explicit design, verified verbatim against the local full text
   (forge.txt lines 662-665): "We compare two configurations across
   all case studies: (1) non-instrumented, where agents receive
   policies as natural language instructions in their system prompts,
   and (2) instrumented, where FORGE enforces policies at runtime via
   the reference monitor. The instrumented condition does not include
   the natural language policy in the agent's prompt; the agent
   relies solely on runtime enforcement and corrective feedback." A
   second, structurally degenerate instance exists: the Prompts Don't
   Protect governed proxy (arXiv 2605.18414) filters unauthorized
   tools out of the model's context before population, with no policy
   prompt in that arm and 0% unauthorized invocation "by
   construction" (promptsdontprotect.txt, verified locally). Cell C
   is unclaimed only as a cell inside a crossed factorial, per
   mechanism, first-attempt scored, with a released deterministic
   scorer and benchmark.

2. **"AIRGuard (arXiv 2605.28914): the single closest prior"
   (PAPER.md line 153). False as an exclusivity claim.** At least
   seven verified papers now sit in the measured told-vs-enforced
   class: AIRGuard, FORGE, TeamBench, ABSTAIN, Harness-MU,
   ContextCov, Symbolic Guardrails, plus TRACE on the
   preference-compliance variant of the same lever and Mechanical
   Enforcement on the financial-governance variant. Related work must
   present a closest-prior class with per-paper distinguishing
   sentences (see neighbors.md Tier 1), never a single anointed
   neighbor. On cell coverage ABSTAIN is closer than AIRGuard (three
   of four cells vs two); on the enforced-not-told cell FORGE is
   closer; on the negative-result shape TeamBench is closer.

3. **"they hold enforcement architecture as the manipulated variable
   and have no telling axis" (PhantomPolicy sentence, PAPER.md line
   161). Factually wrong.** Verified against the local full text
   (phantompolicy.txt lines 629-722): PhantomPolicy runs an explicit
   policy-in-prompt condition ("In addition to the execution-oriented
   baseline prompt, we ran a policy-in-prompt condition that provides
   high-level organizational policy rules in the system prompt")
   which "reduces risky-case violations from 286/300 (95.3%) to
   122/300 (40.7%), a 57% reduction" under human-reviewed labels
   (their Tables 6 and 11). A reviewer who has read PhantomPolicy's
   Section 5 catches this immediately. What still holds, verified:
   the telling condition is folded into a single ordinal axis of
   enforcement regimes (baseline / policy-in-prompt / content-DLP /
   Sentinel) and is never crossed with enforcement; Sentinel and the
   DLP baseline are always applied to traces generated under the
   baseline not-told prompt, so no enforced-and-told versus
   enforced-and-not-told contrast exists there. The conjunction is
   intact; the sentence is not.

4. **"existing enforcement is config- or LLM-based and is never
   measured against what the model would do on its own" (PAPER.md
   line 146). False as an absolute.** ContextCov (arXiv 2603.00822,
   abstract re-fetched this pass) measures exactly that: 88.3%
   constraint compliance enforced vs 67.0% prompt-only vs 50.3%
   reflection-only on SWE-bench Lite (12 repositories, 300 tasks),
   with source code and evaluation results released on GitHub.
   Verifier Tax (arXiv 2603.19328, abstract re-fetched this pass)
   also compares enforced (TRIAD-SAFETY) against unenforced
   baselines (Tool-Calling, TRIAD) on GPT-OSS-20B and GLM-4-9B.
   Qualify to "rarely, and never crossed with a per-mechanism
   factorial or verifiability and goal-conflict moderators," or
   equivalent.

**Three further wording defects (wording_fix tier, not novelty
threats):**

- ST-WebAgentBench is not "single backbone" (PAPER.md line 192): it
  evaluates three agent scaffolds (AgentWorkflowMemory,
  WorkArena-Legacy/BrowserGym, WebVoyager) with no shared backbone
  disclosed. Replace with "three agent scaffolds, in-context policies
  only, no enforcement lever" or drop the backbone clause.
- AIRGuard "one model" is true only of its Table 2 ablation
  (GPT-5.4-mini, DTAP-150 only, ASR 22% no defense, 17% prompt-only,
  4% full guard; verified against airguard.txt); the paper's main
  results (Table 1) span four backbones (Claude Haiku 4.5, Claude
  Sonnet 4.6, GPT-5.4-mini, GPT-5.3-codex). Scope the clause to the
  ablation explicitly.
- SafePyramid "policy density" (PAPER.md line 174) misnames its axis;
  the L0/L1/L2 levels vary policy reasoning complexity (single-rule
  application, cross-rule dependencies, novel policy adaptation), not
  rule density.

**The L7 fork stub must be rewritten.** Governance Decay /
ConstraintRot (arXiv 2606.22528, v1 21 Jun 2026, predating PAPER.md's
2026-07-02 sweep; abstract re-fetched verbatim this pass) already
measures the drift-causes-violation half of the phenomenon with
deterministic tool-call grading: violation rises from 0% with the
policy in full context to 30% after compaction, reaching 59% for some
models; 38% when the constraint is dropped from the summary, 0% when
it survives; a training-free Constraint Pinning mitigation restores
0% across 1,323 episodes and seven model families. No condition in
that paper involves runtime enforcement external to the agent's
context (confirmed at abstract level this pass), so it cannot claim
cell C and does not touch the 2x2. What remains open for L7 is
narrower than the current stub implies: not whether drift causes
violation (externally established) but whether independent runtime
enforcement catches the violation once drift has happened, which
ConstraintRot never tests. [FORK-L7-DRIFT: unmeasured in GAB; the
stub must name precisely this open half, cite ConstraintRot and its
concurrent sub-literature (Gamage 2026; SafeContext, per hunt_0's
full-text read, not independently re-verified), and assume no
outcome.]

## Per-threat adjudication

Severity scale: breaks_conjunction > narrows_claim > wording_fix >
cite_only > none. The 24 pre-identified entries deduplicate: FORGE
appears four times, ContextCov three, TeamBench three, ABSTAIN three,
Prompts Don't Protect two, TRACE two, Harness-MU (implied twice via
the closest-prior-class point), AIRGuard once, PhantomPolicy once,
LogiSafetyBench once, Verifier Tax once, ConstraintRot once, CaMeL
once, Symbolic Guardrails once, Mechanical Enforcement once.

### 1. FORGE / PCAS (arXiv 2602.16708): CONFIRMED, narrows_claim (highest severity found)

FULL-TEXT-LOCAL (forge.txt). Palumbo, Choudhary, Choi, Amir,
Chalasani, Jha; v1 titled "Policy Compiler for Secure Agentic
Systems." Two configurations across three case studies
(prompt-injection information-flow defense; tau2-bench customer
service on Claude Opus 4.5, GPT-5.2, Gemini 3 Pro; MALADE
pharmacovigilance): non-instrumented (policy in the system prompt, no
monitor: cell B) and instrumented (Datalog reference monitor
enforces, policy withheld from the prompt: cell C). The most direct,
explicitly self-described enforced-not-told instance found anywhere;
falsifies the "verified unclaimed" parenthetical. Held at
narrows_claim because, each point verified against the full text: no
told-and-enforced cell A anywhere, so FORGE cannot measure the
redundancy of enforcement given specification, which is the
substitution question; no neither floor D; the instrumented arm's
corrective feedback makes its cell C a converged multi-turn
condition, not first-attempt (blocked actions return feedback, which
is in-context specification delivered late); one holistic policy per
case study, no per-mechanism inventory; no moderators;
enforcement-is-necessary framing, not substitution; no located public
code release.

### 2. PhantomPolicy (arXiv 2604.12177): CONFIRMED, narrows_claim (citation-accuracy defect)

FULL-TEXT-LOCAL (phantompolicy.txt). Wu, Gong (Atlassian). The "no
telling axis" clause in PAPER.md is falsified (headline item 3
above). The constraint-class taxonomy claim holds (eight violation
categories, their Table 1). The conjunction-relevant distinction
survives in corrected form: the telling condition exists but is never
crossed with enforcement architecture; Sentinel (92.99% accuracy vs
68.8% for content-only DLP) always runs over baseline not-told
traces. Adjudicated narrows_claim because a distinguishing sentence
is factually wrong as written, not because any cell of the 2x2 is
claimed.

### 3. ContextCov (arXiv 2603.00822): CONFIRMED, narrows_claim

ABSTRACT-THIS-PASS. Sharma, single author, submitted 2026-02-28.
88.3% constraint compliance enforced vs 67.0% prompt-only vs 50.3%
reflection-only on SWE-bench Lite (12 repositories, 300 tasks), 3.4x
lower feedback cost, source code and evaluation results released
(github.com/reSHARMA/ContextCov; earlier characterizations of it as
unreleased are wrong). Falsifies line 146 (headline item 4) and must
be promoted from PAPER.md's generic harness-engineering bucket (line
187) to the closest-prior class. Not cell C: the enforced arm
"returns immediate, reproducible violation traces, enabling
self-correction," which is enforcement plus late in-context telling,
converged rather than first-attempt. Single axis, one aggregate
compliance number, single domain, no moderators, no harness-blindness
claim.

### 4. Verifier Tax (arXiv 2603.19328): CONFIRMED, narrows_claim

ABSTRACT-THIS-PASS. Sah, Srivastava, Sah, Jordan, submitted
2026-03-18. Compares Tool-Calling (unenforced), TRIAD, and
TRIAD-SAFETY (policy-mediated) on tau-bench Airline and Retail with
GPT-OSS-20B and GLM-4-9B; safety mediation intercepts up to 94
percent of non-compliant actions yet safe success rate stays below 5
percent in most settings, driven by Integrity Leaks (models
hallucinating user identifiers to bypass authentication); recovery
after blocked actions 21 percent to near zero. Contradicts the
literal "never measured" phrasing of line 146 and joins the
closest-prior class. No told/untold contrast (safety mediation is
architectural, not prompt-toggled), no cell C, no per-mechanism
isolation, two small open models, no released benchmark holding the
levers apart located.

### 5. Prompts Don't Protect (arXiv 2605.18414): CONFIRMED, narrows_claim

FULL-TEXT-LOCAL (promptsdontprotect.txt). Uppala, independent single
author, no venue, 18 May 2026. Three conditions on 200 adversarial
tasks: Unfiltered (UIR 48.5% Qwen 2.5 7B, 66.0% Llama 3.1 8B, 68.5%
Claude Haiku 3.5), Prompted with an explicit per-tool allowlist
(37.0%, 4.0%, 11.5%), Governed proxy (0.0% for all models). The
governed arm is structurally not-told: the proxy filters unauthorized
tools out of the model's context before population, with no policy
prompt in that arm. Degenerate as a cell C measurement: unauthorized
tools never reach context, so the 0% is true by construction and
attempted violations cannot be observed. No told-and-enforced A cell
(structurally impossible for this proxy design), single mechanism
(tool-discovery ABAC), adversarial framing, no moderators, no located
release. The 150-task / 11-18pp numbers in some upstream summaries
are fabricated; never reuse them.

### 6. TeamBench (arXiv 2605.07073): CONFIRMED, narrows_claim

ABSTRACT-THIS-PASS. Kim, Park, Kim, Park, Schmidgall, Rahman, Park,
Breazeal, Liu, Palangi, Park, McDuff; submitted 8 May 2026. Verbatim:
"Prompt-only and sandbox-enforced teams reach statistically
indistinguishable pass rates, but prompt-only runs produce 3.6 times
more cases where the verifier attempts to edit the executor's code."
851 task templates, 931 seeded instances, deterministic grader
("Verifiers approve 49% of submissions that fail the deterministic
grader"). Published convergent evidence, in a different mechanism
domain (multi-agent Planner/Executor/Verifier role and workspace
separation, not the single-agent M4-M8 inventory), for the same
qualitative shape as this paper's negative result: outcome-level
parity between told-only and enforced with a real behavioral
difference underneath. Both arms tell the agents their roles, so no
cell C; one monolithic mechanism; no moderators. Two writing
obligations follow (constraints 6 and 7 below).

### 7. TRACE (arXiv 2606.13174): CONFIRMED, narrows_claim

ABSTRACT-THIS-PASS. Zhou, Guo, Zhuang, Wang, Huang, Liang, Chen, Gao,
Moniz, Chawla, Zhang; submitted 11 Jun 2026. Compares a Mem0
in-context memory baseline (57.5% of applicable preference checks
still violated) against user corrections compiled into runtime
checks: violations fall to 37.6% in-distribution and 2.0%
out-of-distribution on ClawArena-derived tasks, 60.5% on
MemoryArena-derived tasks. Code and deployable skill released. Domain
is user-preference compliance in a coding agent, not governance
mechanisms; the rule is always known to the agent in some form, so no
cell C; single aggregate violation rate; no moderators. Confirmed:
the phrase "complementary substrates" does not appear in the
abstract; do not quote it without full-text verification.

### 8. Harness-MU (arXiv 2606.21856): CONFIRMED, narrows_claim

ABSTRACT-THIS-PASS. Fan, Nie, Dai; submitted 20 Jun 2026. Governance
constraints "are deterministic runtime variables that should be
enforced by execution hooks rather than entrusted to the LLM";
hooks-vs-baseline delta on four frontier models on Muses-Bench
(utility improvement 0.28-0.39, instruction-following accuracy up to
48.9 percentage points). Adversarial multi-turn framing, no
factorial, no cell C, access control treated as one undifferentiated
surface. One of the reasons the "single closest prior" sentence must
die. It makes its own "first" claim, which does not collide with any
claim this paper is permitted to make.

### 9. ABSTAIN, "What Benchmarks Don't Measure" (arXiv 2606.02965): CONFIRMED, narrows_claim

FULL-TEXT-LOCAL (abstain_full.html; the Appendix B quote "receives
the same prompt as the Prompt-Only" grep-confirmed this session).
Ojewale and Venkatasubramanian, Brown, RLEval workshop. Three
conditions on 144 tool-calling scenarios across seven model families:
Baseline (no policy, no enforcement: cell D), Prompt-Only (policy in
the system prompt: cell B), Checkpoint (deterministic pre-execution
tool wrapper reusing the Prompt-Only prompt verbatim: cell A, not C).
The closest any located paper comes to the factorial: three of four
cells for one mechanism, with a three-part gap-type taxonomy
(specification / verification / authority) decomposed per gap type.
Held at narrows_claim: no cell C; a single abstention/precondition
mechanism, not a per-mechanism inventory; no moderators;
non-Checkpoint conditions scored by a GPT-4o LLM judge, not a
deterministic offline scorer; self-described preliminary work with no
located release. Supersedes hunt_3's earlier "no crossing"
characterization.

### 10. Symbolic Guardrails (arXiv 2604.15579): CONFIRMED, narrows_claim (residual gap now closed)

FULL-TEXT-LOCAL (symbolic_guardrails.txt line 665, grep-confirmed
this session): "all experimental conditions include the full policy
in the system prompt." Telling is held constant at ON in every arm,
so the design is cell B vs cell A with no cell C or D; violations are
pooled across 23-34 requirements per benchmark into one aggregate
rate, not decomposed per mechanism; the GPT-4o/GPT-5 and
adversarial/non-adversarial variants are not designed as moderators
on the telling axis. This closes the per-policy-breakdown question
earlier passes had left flagged. PAPER.md's existing sentence (line
162-164) is accurate; the full text now supplies direct textual
confirmation that the enforced-not-told cell is absent there, an
available strengthening.

### 11. Mechanical Enforcement (arXiv 2605.14744): CONFIRMED, narrows_claim (directional-tension obligation)

ABSTRACT-THIS-PASS. de la Chica Rodriguez and Marti-Gonzalez;
submitted 14 May 2026. Compares text-only governance (policy
in-context, self-interpreted) against mechanical enforcement (four
architectural primitives outside the model's interpretive loop) in a
regulated-banking decision agent: under text-only governance 27% of
deferrals carry no decision-relevant information; mechanical
enforcement reduces this by 73% and raises task accuracy from MCC
approximately 0.43 to 0.88. Confirmed two alternative configurations,
not a crossed factorial; no enforced-not-told cell; single financial
domain; decision-rationale-quality metrics, not tool-action
compliance; no located release. Does not break the design novelty,
but it points the opposite empirical direction from this paper's
headline (enforcement matters a lot there; behaviorally redundant
here for a capable cooperative agent above the operate floor).
Currently uncited in PAPER.md; a reviewer aware of both will ask why
the directions differ, and the draft must address it (constraint 14).

### 12. ConstraintRot / Governance Decay (arXiv 2606.22528): CONFIRMED, narrows_claim (scoped to the L7 stub and Lineage Anchor, not the 2x2)

ABSTRACT-THIS-PASS. Chen; v1 21 Jun 2026. Numbers as in the headline
L7 item. Confirmed this pass at abstract level: every lever concerns
whether constraint text survives in context; no external runtime
enforcement exists in any condition; the abstract does not confirm a
code or benchmark release (the released-grader and concurrent-work
details, Gamage 2026 and SafeContext, rest on hunt_0's full-text read
and must be re-verified before citing). Cannot break or narrow the
2x2 itself; narrows what remains open for the L7 fork and must enter
the Lineage Anchor. Both it (21 Jun) and TeamBench (8 May) predate
PAPER.md's 2026-07-02 sweep and were missed by it; state the sweep
date honestly if the draft mentions one.

### 13. AIRGuard (arXiv 2605.28914): DOWNGRADED to wording_fix

FULL-TEXT-LOCAL (airguard.txt; Table 2 rows grep-confirmed: no
defense ASR 22% UPR 86%, prompt-only 17% and 86%, full guard 4%).
The pre-identified threat is exactly right and no larger: "one model"
is true of the Table 2 ablation (GPT-5.4-mini, DTAP-150 only) and
false of the paper's main results (four backbones, Table 1). No
factorial, no cell C, no constraint-class analysis: all confirmed.
Scope the clause to the ablation; nothing else changes.

### 14. LogiSafetyBench (arXiv 2601.08196): DOWNGRADED to wording_fix

ABSTRACT-THIS-PASS. Song, Huang, Chen, Cong, Goebel, Ma, Khomh;
title "Evaluating Implicit Regulatory Compliance in LLM Tool
Invocation via Logic-Guided Synthesis"; 240 human-verified tasks, 13
models, no enforcement condition anywhere (prompt-only pipeline,
post-hoc LTL checking), "Unsafe Success" is its own term. The
family-dependent detail (positive scaling within the GPT-5 series,
inverse within Gemini) rests on neighbors_2's read of the results
figures. PAPER.md's compressed phrase "non-monotone and
inverse-scaling" already accommodates this; the fix binds only if
related-work prose expands the citation: render as "family-dependent,
non-monotone scaling," never a single global inverse-scaling curve.

### 15. CaMeL (arXiv 2503.18813): DOWNGRADED to cite_only (must-cite)

FULL-TEXT-LOCAL (camel.txt line 1073 grep-confirmed: "CaMeL
significantly outperforms all other defenses in terms of security").
Debenedetti et al., Google DeepMind / ETH Zurich. The pre-identified
narrows_claim severity is not supported: CaMeL never states its
security policies to the model in any condition, so disclosure is
never manipulated and there is no told cell to pair against; its one
internal ablation (CaMeL vs CaMeL no-policies) is an enforcement
on/off switch inside one architecture; it evaluates on the
pre-existing AgentDojo benchmark. It narrows no sentence the paper
needs. It is the most citable prior instance of architectural
enforcement beating prompt-only heuristic defenses in the injection
literature and is absent from PAPER.md; cite as motivating prior art
for the enforcement axis. A sweep-level WebFetch fabricated a
factorial for this paper; the fabrication is documented in hunt_3 and
must not propagate.

### Resolved to cite_only or none this cycle (previously open)

- **DEMM-Bench (arXiv 2606.20634)**: FULL-TEXT-LOCAL (demm_bench.txt,
  extraction succeeded this cycle). Benchmarks whether agent-runtime
  evidence containers suffice to reconstruct decision-level
  governance properties post hoc; no enforcement mechanism under
  test, no policy-disclosure manipulation, no live agent execution.
  **none** for the 2x2; optional cite_only for the M8 audit-evidence
  discussion ("evidence-container presence is not decision-level
  sufficiency").
- **"Stop Comparing LLM Agents Without Disclosing the Harness"
  (arXiv 2605.23950 / OpenReview qMjgplILnv)**: abstract finally
  fetched (hunt_2, this cycle). A position paper on harness-
  configuration disclosure; its "factorial" is harness-choice x
  model-choice for performance variance, not specify-vs-enforce for
  compliance. **cite_only** as a methodological parallel to the
  harness-blindness contribution. Residual-gap flag closed.

## Binding wording constraints for the S2 writer

1. Never write "the enforced-not-told cell is unclaimed" or any
   unqualified equivalent. Approved formulation: isolated
   enforced-not-told measurements exist (FORGE by explicit design;
   the Prompts Don't Protect governed proxy structurally, with the
   caveat that affordance removal makes its 0% true by construction),
   but no prior work holds that cell inside a crossed factorial
   against a told-and-enforced cell and a neither floor, decomposes
   it per governance mechanism, scores the telling axis on
   first-attempt behavior, or releases a deterministic offline scorer
   and benchmark that hold the two levers apart.

2. Never write "the single closest prior." Present a closest-prior
   class (neighbors.md Tier 1): FORGE closest on cell C, ABSTAIN
   closest on cell coverage (three of four cells, one mechanism),
   TeamBench closest on the negative-result shape, AIRGuard the
   closest security-framed prompt-vs-guard ablation, with Harness-MU,
   ContextCov, Verifier Tax, TRACE, Prompts Don't Protect, Symbolic
   Guardrails, and Mechanical Enforcement each distinguished in one
   sentence.

3. Rewrite the PhantomPolicy sentence. Approved formulation: they run
   a policy-in-prompt condition (reducing risky-case violations from
   95.3% to 40.7% under human-reviewed labels) but fold telling into
   the same single ordinal axis as enforcement architecture; no
   condition holds enforcement fixed while varying telling, so there
   is no enforced-and-told versus enforced-and-not-told comparison.
   Never repeat "no telling axis."

4. Qualify the line 146 claim. Existing enforcement work is rarely
   measured against an unenforced prompt-only baseline (ContextCov
   and Verifier Tax do exactly that), and is never crossed with a
   per-mechanism factorial or the verifiability and goal-conflict
   moderators. Do not keep "never measured against what the model
   would do on its own."

5. When citing FORGE, quote its methodology sentence verbatim
   (headline item 1) and distinguish on: no A cell, no D floor,
   corrective feedback makes its cell C converged multi-turn rather
   than first-attempt, one holistic policy per case study, no
   moderators, no located release.

6. When reporting the negative result, cite TeamBench as convergent
   published evidence of the same shape in a different mechanism
   domain; never imply the substitution pattern is unobserved in the
   literature.

7. Address TeamBench's aggregate-masking finding explicitly:
   pass-rate parity coexisted with a 3.6 times sub-metric violation
   gap, which cuts partly against this paper's own methodological
   direction (aggregate metrics can hide real enforcement value, not
   only manufacture spurious violations). State what the
   per-mechanism marker-level scoring does and does not rule out.
   This convergence does not discharge the external replication
   requirement. [FORK-H5-REPLICATION: the external non-HAI
   replication is pending; TeamBench is prior published evidence in a
   different domain and design, not a replication of this paper's
   effect; it is a candidate input to H5, flagged for Dom, and no
   prose may assume H5's outcome.]

8. Rewrite the L7 stub per the headline L7 item: cite ConstraintRot
   (and, only after full-text re-verification, its concurrent works
   Gamage 2026 and SafeContext), state that drift-causes-violation is
   externally established (0% to 30%, up to 59%), and name the
   still-open half (whether independent runtime enforcement catches
   post-drift violations). [FORK-L7-DRIFT: unmeasured in GAB; every
   sentence touching this must remain a marked stub, not an assumed
   outcome.]

9. Address the Mechanical Enforcement directional tension in the
   Discussion: their finding (mechanical enforcement raises
   governance quality and task accuracy, MCC approximately 0.43 to
   0.88, financial rationale-quality metrics) and this paper's
   finding (enforcement behaviorally redundant given specification
   for a capable cooperative agent) differ in domain, metric type
   (rationale quality vs tool-action compliance), design (paired
   alternative configurations vs crossed factorial), and pressure
   regime. Name the difference; do not leave it for a reviewer.

10. When citing ABSTAIN, state that its Checkpoint condition reuses
    the Prompt-Only prompt (cell A, not C, their Appendix B) and that
    its non-Checkpoint conditions are LLM-judge scored; supersede
    hunt_3's earlier mischaracterization.

11. When citing Prompts Don't Protect, use the corrected numbers (200
    tasks; prompted UIR 37.0/4.0/11.5% for Qwen 2.5 7B / Llama 3.1 8B
    / Claude Haiku 3.5; governed 0.0% by construction) and never the
    fabricated 150-task / 11-18pp version in some upstream summaries.

12. Correct the ST-WebAgentBench clause to "three agent scaffolds,
    in-context policies only, no enforcement lever" or drop the
    backbone clause entirely.

13. Keep AIRGuard's "one model" scoped to its ablation: the
    prompt-only vs runtime-guard ablation is one model (GPT-5.4-mini,
    DTAP-150 only, ASR 22% to 17% prompt-only to 4% full guard) while
    the main results span four backbones; say "ablation" explicitly.

14. Replace "policy density" for SafePyramid with "policy reasoning
    complexity" or the L0/L1/L2 hierarchical description. If
    LogiSafetyBench prose expands beyond the compressed list item,
    render its trend as "family-dependent, non-monotone scaling," not
    one global inverse-scaling curve.

15. Do not quote "complementary substrates" from TRACE; confirmed
    absent from its abstract.

16. Distinguish this paper's benign completion-pressure goal-conflict
    arm from adversarial framings when citing MAC-Bench (arXiv
    2606.07805), Harness-MU, Prompts Don't Protect, Open Agent
    Passport, or Anthropic's agentic-misalignment work; a reviewer
    will ask why goal conflict nulled here when adversarial pressure
    elsewhere breaks self-enforcement, and the framing difference
    must be explicit.

17. When discussing the D-36 fabrication artifact, cite
    CEF/Thanatosis (arXiv 2606.14831) and scope carefully:
    independent constraint-evasive fabrication exists under
    FSM-sealed contradictory-constraint pressure in pure prompted
    dialogue; the methodological claim is that one specific
    fabrication finding was a harness-blindness artifact, not that
    constraint-driven fabrication never occurs. "Stop Comparing LLM
    Agents Without Disclosing the Harness" (arXiv 2605.23950) is a
    citable methodological parallel (harness disclosure), not a
    competing result.

18. Standing repo constraints restated: no "first X" claims; novelty
    is the conjunction only; no additive per-mechanism attribution;
    no scaling-law claims; AI-engineering harness-governance framing,
    not AI-control, trusted-monitor, or safety-umbrella, and not
    product framing; all model-backed evidence is diagnostic tier
    (one model, Qwen3-235B-A22B-Instruct-2507 via Together AI at
    temperature 0, n=3-5 per cell) and every such claim hedges
    accordingly; static oracle-pair, live runtime-probe, and
    model-backed evidence tiers are never merged in a single claim;
    no em dashes.

## Residual coverage gaps (declare or recheck before submission)

- AgentSpec (arXiv 2503.18666) and CAAF (arXiv 2604.17025): never
  full-text verified for a hidden told/enforced crossing.
- "Silent Commitment Failure" (arXiv 2603.21415): PDF would not
  render on any pass; unconfirmed.
- "Reframing LLM Agent Security as an Agent-Human Interaction
  Problem" (arXiv 2605.24309): claims to have swept OSDI/SOSP
  proceedings; full text unrecoverable via WebFetch; re-extract with
  a direct PDF tool.
- VIGIL (arXiv 2606.26524) and AGENT-C (arXiv 2512.23738): abstracts
  cleared, but whether specification and enforcement are varied as
  crossed factors inside either was not full-text confirmed.
- ceLLMate (arXiv 2512.12594): cleared on an AI-summarized fetch
  only; low confidence.
- ConstraintRot's release status and concurrent-work citations
  (Gamage 2026, SafeContext) rest on one hunt's full-text read;
  re-verify before citing those details.
- ETCLOVG survey: confirmed via search snippets only; re-fetch before
  the related-work section locks.
- OpenReview bot-challenges prevented exhaustive enumeration of
  ICLR/ICML 2026 workshop and NeurIPS 2026 submission lists.
- Re-run the whole sweep near the 2026-09-30 submission date; two
  confirmed threats (TeamBench, 8 May 2026; ConstraintRot, 21 Jun
  2026) predate the 2026-07-02 sweep recorded in PAPER.md and were
  missed by it.

Resolved and struck from the prior residual list: Symbolic Guardrails
(full text local, always-told confirmed), DEMM-Bench (full text
local, no enforcement lever), "Stop Comparing LLM Agents Without
Disclosing the Harness" (abstract fetched, position paper,
cite_only).
