# Forbidden-Claims Register

Lintable checklist for every writer and reviewer agent working the
preprint. This is a ground-truth reference file, not prose to quote
verbatim in the paper. Each entry: the rule, its source, BAD example
phrasings, and the compliant alternative. Run every drafted sentence
that touches novelty, causality, evidence, scope, or framing against
this list before it ships.

Sources: `PAPER.md` (Title and Frame, Five-Minute Talk Track,
Lineage Anchor, Scope, Mechanism Inventory, Threat Model, Hypotheses,
Experimental Design, Evidence Status, Engineering Plan, Operational
Disciplines, Active Decisions
D-03/D-12/D-17/D-20/D-21/D-26/D-34/D-36) and `AGENTS.md`
(Research Invariants, Do Not Do), plus the operating rules issued to
this workflow's agents. Line numbers cited are as of the 2026-07-04
read; re-grep if PAPER.md has moved since.

Staleness caution (2026-07-04): benchmark commit `a10e850`
(2026-07-04, "retire positive-attribution apparatus, cut to sharp
14-task suite (D-37)") changes the benchmark tree without touching
PAPER.md, whose Active Decisions still end at D-36 and whose D-19
still records the 28-task suite. The counts in this register (28
tasks in item 11; 25 static oracle pairs in item 6; 16 adversarial
trajectories in item 7) follow PAPER.md as the declared source of
truth. Re-verify these counts against PAPER.md at drafting time; do
not cite a task or trajectory count in the manuscript until PAPER.md
records the D-37 state.

---

## 1. No "first X" claims

**Rule.** Novelty is a CONJUNCTION of six elements, never a single
"first." Do not claim priority on any individual axis: the 2x2 design
including the enforced-not-told cell, per-mechanism isolation, the
three-condition substitution account, the methodological warning
(prompt-embedded-policy guardrail ablations measure self-enforcement),
the deterministic offline scorer, or the released benchmark.

**Source.** PAPER.md L195-203 ("Novelty is a CONJUNCTION, not any
single first... No 'first X' claims"); L786-789 ("Novelty is a
conjunction, not a first... forbid every 'first X'"); D-26 (L679, "no
'first X'"). AGENTS.md Do Not Do does not restate this directly but
D-26/D-34 in PAPER.md are binding project decisions.

**BAD**
- "We present the first benchmark to separate specification from
  enforcement in agent harnesses."
- "This is the first study of runtime governance in LLM agents."
- "To our knowledge, no prior work has isolated the enforced-not-told
  cell" (implies priority even when hedged this way).

**COMPLIANT**
- "The specify-vs-enforce 2x2, including the enforced-not-told cell,
  is verified unclaimed across the closest neighbors we identify
  (AIRGuard, PhantomPolicy, Symbolic Guardrails, SABER, LogiSafetyBench,
  Agent-SafetyBench, SafePyramid, Agent Behavioral Contracts,
  Life-Harness, ALIGN); the contribution is the conjunction of this
  design with per-mechanism isolation, the three-condition
  substitution account, the methodological warning, a deterministic
  offline scorer, and a released benchmark."

---

## 2. No scaling-law claim

**Rule.** The paper does not claim a clean capability-ordered
self-enforcement curve or any scaling-law result. The capability
ladder is a bounded, ladder-confounded moderator that weakly supports
an operate floor only.

**Source.** PAPER.md L133-137 ("not claiming... a clean capability
scaling law"); L238 ("No scaling-law claim"); L450 (H3: "no scaling
law"); L454 (H7 future-work-only, Engels deferred); L624
("The ladder cannot carry a scaling claim"); D-03 (L656, Engels
deferred); D-34 (L687, "recasts capability from headline substitution
claim to bounded moderator... no scaling law").

**BAD**
- "Self-enforcement improves monotonically with model capability."
- "These results establish a scaling law for runtime governance
  substitutability."
- "Larger models need enforcement less, in a smooth, predictable
  curve."

**COMPLIANT**
- "The thin, ladder-confounded capability screen (7B/9B/70B/235B)
  weakly supports an operate floor below which the model cannot drive
  the contract at all; it cannot carry a scaling claim, and
  non-monotonicity across model families is expected per SABER and
  LogiSafetyBench."

---

## 3. No AI-control / trusted-monitor / safety-umbrella framing

**Rule.** External framing is agent-harness governance
(AI-engineering). The deterministic governance contract is described
as a harness layer (ETCLOVG Governance/Verification), never as an
AI-control scheme, a trusted-monitor architecture, or under a general
"safety" umbrella.

**Source.** PAPER.md L781-785 ("External framing is agent-harness
governance (AI-engineering)... not an AI-control / trusted-monitor /
safety umbrella (D-26). Do not re-attach the AI-control framing");
D-26 (L679, "AI-control to AI-engineering... AI-control / trusted-monitor
/ safety umbrella dropped"). AGENTS.md Do Not Do (verbatim): "Do not
re-attach the AI-control / trusted-monitor / safety umbrella. External
framing is agent-harness governance (AI-engineering); the
deterministic governance contract is a harness layer (per D-26 in
`PAPER.md`)." The operating rules issued to this workflow's agents
restate the same prohibition.

**BAD**
- "This is an AI-control evaluation of trusted monitoring in agent
  deployments."
- "Our contribution sits within the AI safety umbrella of scalable
  oversight."
- "We propose a trusted-monitor architecture for agent harnesses."

**COMPLIANT**
- "We study agent-harness governance: which deterministic mechanisms
  in an agent's runtime remain necessary once the same constraints are
  stated in context, an AI-engineering question about harness design,
  not an AI-control or scalable-oversight claim."

---

## 4. No product framing

**Rule.** HAI is the pinned reference runtime instrument for the
paper, not a product. Do not describe it, or the paper's contribution,
in product-roadmap or shipped-product language.

**Source.** PAPER.md L70-71 ("do not soften to a product framing
either"); L781-785 ("Do not re-attach the AI-control framing; do not
soften to a product framing"); Operational Disciplines L790-792 ("HAI freeze is real. No
v0.2.1+ product cycles"); Scope "Out" L266 ("Any HAI v0.2.1+ product
polish"); D-26 (L679). AGENTS.md: "This repo exists to ship one
artifact: the arXiv preprint... The project is not a HAI product
roadmap. HAI is the pinned reference runtime." AGENTS.md Do Not Do:
"Do not make HAI product-roadmap changes or v0.2.1+ polish."

**BAD**
- "HAI is a production-ready personal-health assistant that
  demonstrates our governance features."
- "Users of our platform benefit from these safety guarantees."
- "This release ships a hardened v0.2.1 with new governance UX."

**COMPLIANT**
- "HAI v0.2.0 is the frozen reference runtime used to instantiate and
  measure the paper's mechanisms; it is the instrument, not the
  contribution, and is described here as a non-clinical
  personal-wellness reference implementation, not a product."

---

## 5. No additive per-mechanism attribution

**Rule.** Harness mechanisms are coupled. Per-mechanism results are
reported as marginal contribution within the fixed controller, never
summed as independent additive contributions. `no_runtime_enforcement`
is a sanity floor, not part of per-mechanism attribution evidence (see
also item 9).

**Source.** PAPER.md L386-392 ("Coupling caveat... Per-mechanism
attribution is reported as marginal contribution within this fixed
controller, not context-free causality... no additive 'M4 contributes
A plus M5 contributes B' language"). AGENTS.md Research Invariants:
"no_runtime_enforcement is a robustness sanity floor, not
per-mechanism attribution evidence."

**BAD**
- "M4 contributes 12pp of the total safety improvement, M5 contributes
  another 8pp, and M6 a further 5pp, summing to a 25pp governance
  effect."
- "Each mechanism's independent contribution adds up to explain the
  full-contract vs. no-runtime-enforcement gap."

**COMPLIANT**
- "Each mechanism's isolated `full_contract` vs. `no_X` contrast is
  reported alongside full-stack rollout evidence, within this fixed
  controller; because mechanisms are coupled, these deltas are not
  additive and do not decompose the full-contract-to-floor gap into
  independent per-mechanism shares."

---

## 6. No merging of evidence tiers

**Rule.** Static oracle-pair evidence, live runtime probes, and
model-backed trajectories are three separate evidence tiers. Never
combine them into one causal claim, and always name which tier a
result belongs to.

**Source.** PAPER.md L128-131 ("Static oracle-pair cases, live runtime
probes, and model-backed trajectories are kept as separate evidence
tiers"); L200-203 ("causal language stays conditional on this
controller, task suite, and evidence tier"); D-21 (L674, "static oracle
rows and live runtime probes must not be merged into one causal
claim"). AGENTS.md Research Invariants: "Keep static oracle-pair
evidence, live runtime probes, and model-backed trajectories clearly
separated." Operating rules for this agent: "Never merge static
oracle-pair, live runtime-probe, and model-backed evidence tiers into
one claim."

**BAD**
- "Across our evidence base, runtime enforcement prevents 90% of
  violations" (blending oracle-pair pass rates with model-backed
  trajectory counts into one number).
- "The benchmark shows X" when X is actually a hand-authored static
  oracle pair, not an observed model trajectory.

**COMPLIANT**
- "The 25 static oracle pairs confirm scorer coverage across M4-M8
  (isolation criterion, D-17); separately, the n=3-5 model-backed
  diagnostic probes on Qwen3-235B show 0 fabrication under benign goal
  conflict. These are reported as distinct evidence tiers and are not
  combined into a single pass-rate."

---

## 7. No injection-robustness claims (cited territory only)

**Rule.** The 16-trajectory adversarial layer is scorer-coverage
evidence at the appendix tier, not evidence that a model resists
prompt injection or adversarial manipulation. Injection/adversarial
robustness is cited from the existing security literature, never
claimed as a result of this paper.

**Source.** PAPER.md L366-371 ("The 16 hand-authored trajectories are
scorer-coverage evidence at the appendix tier, not model-backed
evidence that a model can be induced. Injection robustness is cited
territory... not a claim of this paper"); Scope L247-250 ("injection
robustness is cited, not claimed"); L380-384 ("Not an
adversarial-robustness proof against scheming, sandbagged, or
password-locked frontier models"). AGENTS.md Research Invariants: "The
goal-conflict arm is benign completion pressure... not adversarial
injection. Injection robustness is cited territory, not a claim of
this paper."

**BAD**
- "Our results show the runtime is robust to prompt injection."
- "The adversarial trajectories demonstrate that deterministic
  mechanisms defeat scheming or sandbagged models."
- "We prove adversarial robustness of the governed harness."

**COMPLIANT**
- "The 16 hand-authored adversarial trajectories are scorer-coverage
  canaries at the appendix tier, characterizing whether the
  mechanisms remain observable under known failure-injecting inputs.
  Injection robustness against adaptive or adversarial models is cited
  from the security literature (which already shows telling fails
  under attack), not established here."

---

## 8. No clinical or medical claims

**Rule.** HAI is a non-clinical personal-wellness reference runtime.
No diagnosis, treatment, prescribing, or autonomous medical-decision
claims anywhere in the paper. This is an explicit "Out" scope item and
a hard runtime boundary (M7).

**Source.** PAPER.md Scope "Out" L262 ("Clinical or medical
decision-making claims"); L226 ("HAI as one non-clinical
personal-wellness reference runtime"); D-12 (L665, "Non-clinical
health boundary is part of the contract, not a footer disclaimer. No
diagnosis, treatment, prescribing, or autonomous medical decisions; no
private health rows in public fixtures"); M7 mechanism (L302,
"clinical-boundary leg is the zero-tolerance subset"). AGENTS.md
Research Invariants: "The health boundary is part of the evaluated
contract: no diagnosis, treatment, prescribing, or autonomous medical
decisions." AGENTS.md Do Not Do: "Do not add wearable sources,
micronutrient/food-taxonomy features, or clinical/medical decision
claims."

**BAD**
- "The runtime diagnoses overtraining and prescribes a recovery
  protocol."
- "HAI makes autonomous medical decisions about the user's training
  load."
- "This validates the system as a clinical decision-support tool."

**COMPLIANT**
- "M7 refusal enforces the non-clinical boundary as a zero-tolerance
  runtime behavior: the harness refuses diagnosis, treatment,
  prescribing, or autonomous medical decisions rather than
  disclaiming them in prose."

---

## 9. `no_runtime_enforcement` is a sanity floor, not attribution evidence

**Rule.** The all-mechanisms-off condition is a robustness sanity
check confirming the floor exists (and, under the contract-withheld
arm, a violation-floor baseline for B-vs-D / C-vs-D contrasts). It is
never used as per-mechanism attribution evidence and never folded into
additive mechanism-contribution language (overlaps item 5; kept
separate here because it is independently named as its own
invariant).

**Source.** PAPER.md L391 ("`no_runtime_enforcement` is a sanity floor
only"); L527 ("`no_runtime_enforcement` remains a sanity floor (cell D
with all mechanisms..."); D-20 (L673, "`no_runtime_enforcement` is a
robustness sanity floor, not part of the per-mechanism H1
attribution... additionally serves as the violation-floor baseline for
the B-vs-D and C-vs-D contrasts; the sanity-floor role under the
contract-in-prompt arm is unchanged"). AGENTS.md Research Invariants:
"`no_runtime_enforcement` is a robustness sanity floor, not
per-mechanism attribution evidence."

**BAD**
- "The no_runtime_enforcement condition isolates the causal
  contribution of M4 versus M5."
- "Comparing full_contract to no_runtime_enforcement attributes the
  full effect to the five ablated mechanisms individually."

**COMPLIANT**
- "The `no_runtime_enforcement` cell (all mechanisms off) serves as a
  robustness sanity floor confirming a violation floor exists; under
  the contract-withheld arm it additionally anchors the B-vs-D and
  C-vs-D contrasts. It does not attribute effect to any individual
  mechanism."

---

## 10. Goal-conflict arm is benign pressure, not an attack

**Rule.** The goal-conflict condition is benign completion pressure
(constraint compliance costs task success), never described as an
adversarial attack, injection, or red-team probe.

**Source.** PAPER.md L357-364 ("Goal-conflict arm (benign pressure)...
It is benign completion pressure, not attack"); D-34 (L687, "Adds the
goal-conflict arm (benign completion pressure, new task variants)").
AGENTS.md Research Invariants: "The goal-conflict arm is benign
completion pressure (constraint compliance costs task success), not
adversarial injection."

**BAD**
- "We attack the model with goal-conflict prompts to test whether it
  can be induced to violate the constraint."
- "The goal-conflict arm is our adversarial red-team condition."

**COMPLIANT**
- "The goal-conflict arm applies benign completion pressure: task
  variants where respecting the constraint costs task success. This
  is distinct from the adversarial-input arm and is not an attack or
  injection condition."

---

## 11. Causal language stays conditional on this controller / task suite / tier

**Rule.** Every causal or generalizing statement must be scoped
explicitly to: this fixed controller (HAI v0.2.0), this task suite (28
tasks / GovernedAgentBench v1.0), and the evidence tier the claim
draws on. No unscoped universal claims about agents, harnesses, or
governance in general.

**Source.** PAPER.md L195-203 ("causal language stays conditional on
this controller, task suite, and evidence tier"); L786-789 ("keep
causal language conditional on this fixed controller"); L133-137 ("not
claiming universal agent safety, cross-domain generalization from a
single runtime"). Operating rules for this agent (not AGENTS.md):
"causal language conditional on this controller/task-suite/tier."

**BAD**
- "Runtime enforcement is redundant for capable agents."
- "Deterministic governance mechanisms are unnecessary once
  constraints are stated in the prompt."
- "Agents self-enforce verifiable constraints" (stated as a general
  law).

**COMPLIANT**
- "Within the HAI v0.2.0 reference runtime, on diagnostic probe tasks
  (not the locked 28-task suite; PAPER.md L736-738), for
  Qwen3-235B-A22B-Instruct-2507 at temperature 0 with n=3-5 per cell,
  specification substituted for enforcement broadly, on verifiable and
  non-verifiable constraints and under benign goal conflict (D-36);
  this is not a general claim about agents or harnesses beyond this
  controller, these tasks, and the diagnostic evidence tier."

---

## 12. Model-backed evidence is DIAGNOSTIC tier only, and must be hedged

**Rule.** All model-backed evidence in this paper comes from one model
(Qwen3-235B-A22B-Instruct-2507, Together AI, temperature 0) with small
n (3-5 per cell). Every quantitative model-backed claim must carry
this hedge explicitly, not just in a methods footnote.

**Source.** PAPER.md L65 ("All of the above is diagnostic (one model,
small n); see Evidence Status"); L538-539 ("Diagnostic results
(2026-07-02 probe battery, Qwen3-235B, temperature 0, n=3 per cell...");
L636 ("both diagnostic (one model, small n)"). Operating rules for
this agent: "All model-backed evidence is DIAGNOSTIC tier: one model
..., small n (3-5 per cell); hedge every such claim accordingly."

**BAD**
- "Models reliably self-enforce verifiable constraints" (no model,
  no-n qualifier).
- "0 fabrication events were observed" presented as a settled finding
  rather than n=5 diagnostic.

**COMPLIANT**
- "In diagnostic probing (Qwen3-235B-A22B-Instruct-2507, temperature 0,
  pre-registered n=5 per cell), zero fabrication was observed across
  all 40 reps under graded benign pressure P0-P3 (scorer-verified;
  PAPER.md Evidence Status, `runs/pilot/_probe_h2_audit/`); this is a
  small-n, single-model diagnostic result, not a settled finding
  across models."

---

## 13. Do not soften or bury the negative result

**Rule.** The paper's finding is a NEGATIVE result (in-context
specification substitutes for runtime enforcement for capable
cooperative agents above the operate floor) plus a METHODOLOGICAL
contribution (harness blindness manufactures spurious fabrication
findings). Do not reframe this as a positive result, do not
soft-pedal the null, and do not smuggle in a hidden positive claim
(e.g. implying enforcement mechanisms "still clearly matter" broadly
when the diagnostics did not support that).

**Source.** PAPER.md D-36 (L689, "The paper is a NEGATIVE result...
plus a METHODOLOGICAL contribution... No surviving positive result").
Operating rules for this agent: "The paper is a NEGATIVE result...
plus a METHODOLOGICAL contribution... Do not soften the null; do not
smuggle in a positive result."

**BAD**
- "Our governance mechanisms deliver a measurable safety improvement
  over specification alone" (implies a surviving positive effect the
  diagnostics did not support).
- Downplaying the null via hedge-stacking that leaves the reader with
  the opposite impression, e.g. "while the effect was not
  statistically detected, the mechanisms clearly still matter in
  practice."

**COMPLIANT**
- "Under diagnostic probing, neither the goal-conflict nor the
  verifiability-exception moderator showed the predicted degradation:
  specification substituted for enforcement broadly for this
  cooperative model above the operate floor. This is a negative
  result on the substitution account; the paper's contribution is
  this bounded null plus the harness-blindness methodological
  finding."

---

## 14. Open forks stay marked stubs, never resolved in prose

**Rule.** Two forks are unresolved and must be flagged with the exact
stub markers, never written as if an outcome is known.

**Source.** Operating rules for this agent: "Two open forks are
handled as marked stubs, never as prose that assumes an outcome: L7
stale-manifest drift (unmeasured; mark blocks `[FORK-L7-DRIFT: ...]`)
and the external non-HAI replication H5 (pending; mark
`[FORK-H5-REPLICATION: ...]`)." Cross-reference PAPER.md L448 (L7
drift as the "genuinely non-retrievable residual"); Scope L244-246
(external replication as "the impressive-vs-modest fork").

**BAD**
- "L7 stale-manifest drift shows enforcement is necessary" (asserting
  an unmeasured result).
- "The external replication confirms the effect generalizes beyond
  HAI" (asserting a pending result).

**COMPLIANT**
- "`[FORK-L7-DRIFT: L7 stale-manifest drift is the one unmeasured
  non-verifiable constraint class; outcome pending.]`"
- "`[FORK-H5-REPLICATION: external non-HAI replication of the
  specify-vs-enforce effect is pending; impressive-vs-modest outcome
  fork unresolved.]`"

---

## 15. No em dashes; direct academic prose; no hype adjectives

**Rule.** Style constraint, not a claims constraint, but lints the
same way: no em dashes anywhere in the manuscript; numbers verbatim
from source; no hype adjectives ("groundbreaking," "novel" used as
filler, "powerful," "unprecedented," etc. beyond the precise
conjunction-novelty claim in item 1).

**Source.** Operating rules for this agent: "Style: direct academic
prose. No em dashes anywhere. No hype adjectives. Numbers verbatim
from sources."

**BAD**
- "This groundbreaking approach—unlike anything before it—delivers
  powerful new guarantees."

**COMPLIANT**
- "This approach separates two levers that prior work has not
  factorially crossed: in-context specification and runtime
  enforcement."

---

## How to use this register (for downstream writer/reviewer agents)

1. Before drafting a section touching novelty, causality, evidence, or
   scope, re-read the relevant numbered item(s) above.
2. When reviewing a draft, grep it for the BAD-example trigger words
   ("first", "scaling", "trusted monitor", "AI control", "contributes
   A plus", "diagnos", "prescrib", "attack" near goal-conflict, "robust
   to injection", em dash character) and check each hit against the
   matching rule.
3. If a sentence's claim cannot be traced to a PAPER.md line cited
   above (or a line in Evidence Status / Hypotheses / Active
   Decisions), treat it as unsupported and either cut it or route it
   back to PAPER.md for a decision.
4. This file does not itself gate commits; it is a shared reference.
   Flag violations to Dom rather than silently rewriting scope-bearing
   claims.

---

## Audit corrections

Adversarial re-derivation audit, 2026-07-04, against PAPER.md (806
lines, current working tree), AGENTS.md, and the workflow operating
rules. All cited line numbers in items 1-15 were re-checked; the ones
not listed below were verified correct. Seven corrections applied:

1. **Header sources line.** The header listed "Active Decisions
   D-26/D-31/D-34/D-36" but the body cites D-03, D-12, D-17, D-20,
   D-21, D-26, D-34, D-36 and never cites D-31; it also omitted the
   Threat Model, Hypotheses, and Title and Frame sections that items
   4, 7, 10, and 14 actually draw on. Header rewritten to match the
   body's real citation set.
2. **Item 1 rule.** The forbidden-priority-axis enumeration dropped
   one of the six conjunction elements: the methodological warning
   (PAPER.md L195-201 lists 2x2 incl. enforced-not-told cell,
   per-mechanism isolation, three-condition substitution account,
   methodological warning, deterministic offline scorer, released
   benchmark). Added.
3. **Item 3 source.** The parenthetical claimed the AGENTS.md Do Not
   Do sentence was "repeated verbatim from the operating rules given
   to this agent"; the quote is AGENTS.md verbatim and the operating
   rules only restate the prohibition in different words. Quote
   completed with the harness-layer clause and attribution fixed.
4. **Item 4 source.** The phrase "do not soften to a product framing
   either" is at PAPER.md L70-71 (Title and Frame), not L781-785;
   Operational Disciplines L785 reads "do not soften to a product
   framing" without "either". Pointer split and both quotes made
   exact.
5. **Item 11 source.** "causal language conditional on this
   controller/task-suite/tier" was attributed to "AGENTS.md operating
   rules"; AGENTS.md contains no such sentence. Re-attributed to the
   workflow operating rules.
6. **Item 11 COMPLIANT example.** The example placed the diagnostic
   probes "within... the GovernedAgentBench 28-task suite" (they ran
   on scratchpad probe tasks explicitly "not in the locked 28-suite",
   PAPER.md L736-738) and scoped substitution to "verifiable,
   unconflicted constraints", contradicting D-36 (substitution held
   broadly; the verifiability and goal-conflict moderators nulled).
   Rewritten to match the D-36 record.
7. **Item 12 COMPLIANT example.** "0 of 5 P0-P3 fabrication events"
   misstates the H2 result. PAPER.md Evidence Status: zero fabrication
   across all 40 reps, pre-registered n=5 per cell, graded pressure
   P0-P3, scorer-verified (`runs/pilot/_probe_h2_audit/`). Rewritten
   with the numbers verbatim.

Second-pass adversarial re-derivation, 2026-07-04, independent of the
pass above. Every line number, decision ID, quote, count, and source
pointer in items 1-15 and in the correction log above was re-derived
by grep against the true file numbering of PAPER.md (unchanged since
commit 1f5afd4, 2026-07-03; identical in HEAD and working tree),
AGENTS.md, and the workflow operating rules. Verified correct:
L65, L70-71, L128-131, L133-137, L195-203, L226, L238, L244-246,
L247-250, L262, L266, L302, L357-364, L366-371, L380-384, L386-392,
L448, L450, L454, L527, L538-539, L624, L636, L736-738, L781-785,
L786-789, L790-792; decision-ID rows D-03 (L656), D-12 (L665), D-17
(L670), D-20 (L673), D-21 (L674), D-26 (L679), D-34 (L687), D-36
(L689); counts (six conjunction elements, 16 adversarial trajectories
4 each against M4 / M5+M6 / M7 / M8, 25 static isolation oracle
pairs, 28 tasks, n=3 and pre-registered n=5, 0 fabrication P0-P3
across all 40 reps, 0pp vs a 40pp bar, 7B/9B/70B/235B ladder,
Qwen3-235B-A22B-Instruct-2507 / Together AI / temperature 0); and all
AGENTS.md Research Invariants / Do Not Do / North Star quotes. One
further correction applied:

8. **First-pass preamble line count.** The preamble above stated
   PAPER.md is 807 lines; the file is 806 lines (trailing newline
   present; 806 in both HEAD and the working tree). Corrected in
   place.

Third-pass adversarial re-derivation, 2026-07-04, independent of both
passes above. Re-derived every line number in items 1-15 and in
corrections 1-8 via `grep -n` against PAPER.md (confirmed unchanged
since commit `1f5afd4`, 2026-07-03; 806 lines, trailing newline
present, so correction 8 stands), re-checked all AGENTS.md quotes
against the file verbatim, confirmed the cited artifact directories
exist under `benchmark/governed_agent_bench/runs/pilot/`
(`_probe_contract_off`, `_probe_m8*`, `_probe_h2_audit`,
`_probe_instrumental`, `_probe_ladder`), and re-verified the counts
(six conjunction elements at L195-201; 0 fabrication P0-P3 across all
40 reps at pre-registered n=5; 0pp vs the 40pp bar; 7B/9B/70B/235B).
Corrections 1-8 were verified correct as written. Two further
corrections applied:

9. **Header section list still incomplete.** Correction 1 rewrote the
   header "to match the body's real citation set" but omitted two
   PAPER.md sections the body cites: L128-131 and L133-137 (items 2,
   6, and 11) sit in Five-Minute Talk Track (section starts L73;
   Lineage Anchor starts L139), and L736-738 (item 11 COMPLIANT
   example) sits in Engineering Plan (starts L702). Both added to the
   header source list.
10. **Benchmark tree has moved ahead of PAPER.md.** Commit `a10e850`
    (2026-07-04 10:30, after PAPER.md's last update at `1f5afd4`)
    retitles the suite to 14 tasks under a D-37 that PAPER.md does not
    yet record (Active Decisions end at D-36; D-19 still says 28
    tasks; Engineering Plan L718 still says 18 seed + 16 adversarial +
    25 static isolation oracle pairs, and `trajectories/hand_authored/`
    now holds 8 files). The register's counts were correct against the
    named sources but carried no divergence flag. Staleness caution
    added to the header; items 6, 7, and 11 left tracing PAPER.md per
    the source-of-truth discipline.
