# Terminology Canon

Single source of truth for the exact phrases every section writer and
reviewer agent must use in this preprint. Source: `PAPER.md` (this repo,
read 2026-07-04). Every entry below cites the `PAPER.md` section it is
drawn from. Where a term has a banned near-synonym, using the near-synonym
is a canon violation and must be corrected before the section is
considered done.

Rule for writers: if a concept below has a canonical phrase, use that
phrase (or a light grammatical inflection of it) every time the concept
appears. Do not vary vocabulary for elegance. Consistency across all
section-writer agents depends on literal string reuse, not paraphrase.

Style rule (binding, from the workflow operating rules): no em dashes
anywhere; no hype adjectives; numbers verbatim from sources; every
model-backed number carries the diagnostic hedge in §12.

---

## 1. The core dichotomy: told vs enforced

**Canonical phrase:** "in-context specification" (the general noun for
the telling lever) and "runtime enforcement" (the general noun for the
enforcing lever). The shorthand pair for prose is "told" / "enforced."

**Definition.** There are two distinct levers a harness has for making an
agent respect a constraint:
1. State the rule in the prompt so the model can read it. This is an
   **in-context contract**.
2. Have the runtime block or gate the violation regardless of what the
   model does. This is **runtime enforcement**.

Source: Title and Frame, lines 26-35; Five-Minute Talk Track, lines 84-94.

**Banned near-synonyms:** "prompted safety," "soft constraints" (for
told), "hard-coded guardrails" (for enforced) used as if interchangeable
with "runtime enforcement," "safety training," "alignment via prompting."
Do not call in-context specification "instruction tuning" or "RLHF";
those are model-training-time mechanisms, not the harness-level lever
this paper studies. Do not call runtime enforcement "guardrails" alone
without the word "runtime" nearby on first use per section; "guardrail"
is acceptable as a lay gloss but the technical term in any claim sentence
is "runtime enforcement."

---

## 2. In-context contract

**Canonical phrase:** "in-context contract."

**Definition.** The rule, manifest fact, schema, or policy statement made
available to the agent inside its prompt/context at decision time (e.g.
the command manifest, the `agent_safe` flag, the mutation class, the
clinical-boundary description). The contract-in-prompt axis of the 2x2
toggles whether this is present or withheld.

Source: Title and Frame lines 27-28 ("stating it in the prompt (an in-context
contract)"); Mechanism Inventory lines 285-295 (manifest facts as the
substrate of verifiability).

**Banned near-synonyms:** "system prompt policy" (too narrow: the
contract includes schemas, flags, and taxonomies, not just prose policy
text), "instructions," "prompt engineering." Do not call it "the spec" in
isolation without qualifying it is the in-context copy of the spec, since
the runtime also implements a spec (the enforcement side); conflating
the two erases the paper's central distinction.

---

## 3. Runtime enforcement

**Canonical phrase:** "runtime enforcement."

**Definition.** The harness blocking, gating, or otherwise making a
violation impossible regardless of what the model decides, independent
of whether the model was told the rule. Implemented via M4-M9-TX (see
§4 below).

Source: Title and Frame lines 26-35; Mechanism Inventory (the
runtime-enforcement axis, lines 332-335).

**Banned near-synonyms:** "hard-coded safety," "deterministic safety
layer" (use "deterministic governance contract" only when speaking of the
harness layer as a whole, not as a synonym for the enforcement axis
itself), "AI control," "trusted monitor." See §16 (forbidden framings).

---

## 4. Mechanisms M4-M9-TX

**Canonical phrase:** always cite mechanisms by their ID (M4, M5, M6, M7,
M8, M9-TX) plus, on first use per section, the full name from the table
below. Do not invent alternate names.

| ID | Canonical name | Ablation mode | Context-verifiable? |
|---|---|---|---|
| M4 | Validation of typed commands and proposal payloads | `no_validation` | Yes (schema is in the manifest) |
| M5 | `agent_safe` dispatch refusal | `no_agent_safe` | Yes (`agent_safe` flag is in the manifest) |
| M6 | W57 proposal/commit user gate | `no_proposal_gate` | Yes (mutation class is in the manifest) |
| M7 | Refusal of out-of-contract requests (clinical-boundary leg is the zero-tolerance subset); JSON output exempt | `no_refusal` | Yes (the boundary is describable in the prompt) |
| M8 | Audit evidence emission / reference faithfulness | `no_audit_chain` | No (requires runtime state the agent cannot see or verify; see §5, M8's status is more nuanced than a flat "no") |
| M9-TX | Transaction integrity | Held constant, non-ablatable | n/a |

Source: Mechanism Inventory table, lines 297-304; Active Decisions D-09.

**Notes writers must preserve:**
- M7's "no diagnosis, treatment, prescribing, or autonomous medical
  decisions" clinical-boundary leg is the zero-tolerance subset of M7,
  not a separate mechanism. Do not number it M7a/M7b.
- M8 is **evidence emission**, not "the whole audit chain." Say "M8
  audit evidence emission" or "M8 reference faithfulness," never "the
  audit system" as if M8 covers persistence and blocking too; the
  runtime emits and persists audit evidence; the deterministic scorer
  detects fabrication after the fact. M8 is provision-type, not
  block-type.
- M9-TX is "held constant" / "non-ablatable"; never build a "no_M9_TX"
  sentence or imply it has an ablation mode. It is the atomic-transaction
  floor, always on.
- The runtime-enforcement axis has exactly seven modes: `full_contract`,
  the five M4-M8 off-paths (`no_validation`, `no_agent_safe`,
  `no_proposal_gate`, `no_refusal`, `no_audit_chain`), and
  `no_runtime_enforcement` (all of M4-M8 off; M1-M3 harness
  infrastructure + M9-TX still on). Do not describe this as "six modes"
  or "eight modes."

**Banned near-synonyms:** "the guardrail suite" (for M4-M9-TX
collectively; use "the mechanism inventory" or "M4-M9-TX"), "the safety
mechanisms" (see §16 forbidden framings), "validation layer" alone for M4
without the M-number on first mention in a section.

---

## 5. Context-verifiability

**Canonical phrase:** "context-verifiable" / "context-verifiability" (as
a noun, "verifiability" is acceptable shorthand once "context-verifiable"
has appeared in the section). Full formal phrase when precision matters:
"verifiable from the agent's decision-time context."

**Definition.** A property of the pair (constraint, decision-time
context), not a property of a mechanism in the abstract. A constraint is
context-verifiable if the agent can check its own compliance using only
what is already in its context at the moment it decides. Verifiability
can flip within a trajectory: a constraint becomes verifiable the moment
retrieval lands the relevant ground truth in the agent's context.

Source: Mechanism Inventory, lines 285-295 ("Verifiability is a property
of (constraint, decision-time context), not of a mechanism in the
abstract... it can flip within a trajectory").

**Classification under the standard task setup** (manifest + taxonomies
in the prompt, no runtime state disclosed):
- M4, M5, M6, M7 = context-verifiable (schema, flag, and mutation class
  are in the manifest; the M7 boundary is describable in the prompt).
- M8 = classified non-verifiable under the standard setup, but this
  classification was **contradicted** at the cooperative-model
  behavioral tier once the agent retrieves the evidence (D-35; PAPER.md
  Mechanism Inventory lines 306-323).
- L7 stale-manifest drift = the one surviving genuinely non-retrievable
  class (see §9).

**Banned near-synonyms:** "checkable," "auditable" (reserve "auditable"
for M8/audit-chain discussions specifically, do not use it as a synonym
for verifiability generally), "observable," "transparent." Do not say a
mechanism "is verifiable" full stop without the decision-time-context
qualifier when the claim is load-bearing; the qualifier is the whole
point.

---

## 6. The 2x2 cells: A, B, C, D

**Canonical phrase:** always use the letter plus its full name on first
use per section; letter alone thereafter is fine.

| | Runtime enforces | Runtime off |
|---|---|---|
| **Contract in prompt** | **A: deployment baseline** | **B: told-not-enforced** (self-enforcement) |
| **Contract withheld** | **C: enforced-not-told** (pure runtime) | **D: neither** (violation floor) |

Source: Experimental Design, lines 488-500; the 2x2 table itself is
lines 491-494.

**The three informative contrasts, named exactly this way:**
- **B vs D**: "the effect of telling."
- **C vs D**: "the effect of enforcing."
- **A vs B**: "the marginal value of enforcement given the agent was
  told", also called "the redundancy measure." This is the headline
  quantity of the paper.

Source: lines 496-498.

**Additional fixed names:**
- Cell D is also "the violation floor" and, restricted to the
  contract-withheld arm specifically, "the untold violation floor" (see
  §8). Do not call cell D just "the control" or "the baseline";
  "baseline" is reserved for cell A ("deployment baseline").
- `no_runtime_enforcement` (all of M4-M8 off; M1-M3 harness
  infrastructure and M9-TX still on) is a runtime mode, not a cell.
  Under the contract-in-prompt arm it is **a robustness sanity floor**,
  never per-mechanism attribution evidence (D-20). Under the
  contract-withheld arm the same mode realizes cell D "with all
  mechanisms off" (Experimental Design line 527) and serves as the
  violation-floor baseline for the B-vs-D and C-vs-D contrasts (D-20
  and its D-34 note). Keep the two roles distinct in prose.

**Banned near-synonyms:** "condition 1/2/3/4" instead of A/B/C/D; "the
enforcement-on group" instead of naming the specific cell; "control
group" for D; "treatment" language borrowed from clinical trials
(forbidden by the non-clinical scope: PAPER.md Scope out-list line 262
and D-12).

---

## 7. Self-enforcement / redundancy

**Canonical phrase:** "self-enforcement" (a capable cooperative agent
respecting a constraint on its own, without runtime enforcement, because
it was told). The behavioral outcome when self-enforcement is high is
that enforcement is "behaviorally redundant"; never say enforcement is
"useless" or "pointless," only "behaviorally redundant" and always paired
with the deterministic-guarantee caveat: runtime enforcement's
demonstrated behavioral value remains the deterministic guarantee plus
the narrow corners (below the operate floor, the untold violation floor,
and adversarial intent, untested here; PAPER.md Title and Frame lines
44-48).

**Definition and result (D-36).** For a capable cooperative agent above
the operate floor, in-context specification substitutes for runtime
enforcement broadly: the agent self-enforces constraints it is told
plainly, whether verifiable or non-verifiable, and under benign
goal-conflict pressure. This is the paper's negative result. It is
diagnostic tier: one model, small n (PAPER.md Title and Frame line 65).

Source: Title and Frame lines 40-56; Evidence Status lines 634-643.

**Salience qualifier (must not be dropped).** First-attempt
self-enforcement of a verifiable constraint is NOT automatic; it is
salience-sensitive. The 2026-07-02 probes showed 3/3 refusal when the
constraint was foregrounded (bait phrasing, or the exact gated command
named) but 3/3 first-attempt dispatch of the gated command when it was
reached incidentally through normal task phrasing. Any claim that
self-enforcement is unconditional must carry this qualifier or it
misstates the evidence. Source: Evidence Status lines 543-560; H1
falsification rule lines 459-466.

**Banned near-synonyms:** "the model doesn't need guardrails," "the
runtime is redundant" (always scope redundancy to "behaviorally
redundant given the agent was told," never claim structural or
architectural redundancy), "compliance is automatic," "the model always
follows the rules." None of these carry the salience qualifier and all
overclaim relative to D-36.

---

## 8. Operate floor and untold violation floor

**Canonical phrase, operate floor:** "the operate floor."

**Definition.** The minimum capability level at which a model can drive
the contract at all: emit valid commands, follow the manifest, produce
parseable output. Below the operate floor, enforcement "prevents
malformed harm rather than disobedience"; this is the fixed phrase for
what enforcement does below the floor; do not substitute "prevents
violations" (violations imply intent/disobedience, which is precisely
what does not apply below the floor).

Source: Threat Model lines 349-355; Hypotheses table line 444; Model
Roster lines 406-407 (7B excluded as below the operate floor: 0/60 valid
finals, "contract friction not governance"); Evidence Status lines
616-625 (ladder finding: 7B is below the operate floor).

**Canonical phrase, untold violation floor:** "the untold violation
floor" (also acceptable, once introduced: "the harm floor" as used in the
2026-07-02 probe writeup, but "the untold violation floor" is the
paper-level canonical term; prefer it in section prose; "harm floor" is
the informal variant used in raw evidence notes and should be normalized
to "untold violation floor" in the paper text).

**Definition.** In cell D (contract withheld, runtime off), a capable
agent given a valid target id completed a governance violation 3/3
(flipping a row `proposed`→`active`) with a truthful success report. This
demonstrates a real, non-hypothetical B-vs-D and C-vs-D delta: when the
agent is never told the rule, runtime enforcement is the only thing
standing between the agent and the violation.

Source: Evidence Status lines 543-549, 561-565.

**Banned near-synonyms:** "capability ceiling" (wrong direction: operate
floor is a floor, not a ceiling), "minimum viable model," "jailbreak" (the
untold violation floor is not a jailbreak; no adversarial input is
involved, the agent is simply never told the rule and acts on neutral
phrasing).

---

## 9. L7 stale-manifest drift

**Canonical phrase:** "L7 stale-manifest drift," shortened to "L7 drift"
on subsequent uses in the same section.

**Definition.** The remaining genuinely non-retrievable constraint class,
distinct from M8. An agent cannot retrieve the fact that its in-context
manifest is outdated relative to the actual runtime contract; that
ground truth is runtime state no read surface exposes. Drift is a **task
condition**, not a mechanism row. It is the sole surviving candidate for
a true non-verifiable enforcement delta, and it is **unmeasured** as of
D-36.

Source: Mechanism Inventory lines 325-330; Hypotheses table line 442;
Evidence Status lines 627-629.

**Mandatory framing rule:** L7 must always be marked as an open,
unresolved fork in section prose, never assumed to confirm or refute the
non-verifiable-exception hypothesis. Use the literal marker
`[FORK-L7-DRIFT: ...]` in any block where prose would otherwise assume an
outcome for L7. Do not write sentences like "L7 drift shows enforcement
is necessary"; it is unmeasured, full stop.

**Banned near-synonyms:** "manifest staleness," "config drift" (too
generic, drops the L7 task-level identity), "outdated policy" without
the L7 qualifier attached.

---

## 10. Harness blindness

**Canonical phrase:** "harness blindness" (also: "the harness-blindness
artifact" when referring to the specific dissolved instrumental-
fabrication finding).

**Definition.** The methodological finding that eval harnesses which do
not surface tool/command output to the agent manufacture spurious
findings, specifically spurious fabrication findings. The harness fed
the agent a `stdout_ref` file-path placeholder instead of the actual
command stdout, so the agent guessed values it could not see. Once the
harness surfaces command output (the committed stdout-inlining fix,
commit `17db5ef`), the apparent "instrumental fabrication" effect
vanishes (0 percentage points against a pre-committed >=40pp bar) and the
agent abstains honestly instead.

Source: Title and Frame lines 58-63; Five-Minute Talk Track lines
117-126; Evidence Status lines 603-614; Active Decisions D-36.

**This is the paper's second finding, named a contribution, not a
limitations aside.** Section writers must not fold this into a
limitations paragraph; it gets its own treatment (Outline §6).

**Banned near-synonyms:** "observation gap," "tool-output bug,"
"engineering bug" (undersells it: it is a methodology-level finding
about how eval harnesses can manufacture false positives, not merely a
bug that was fixed). Do not call the underlying fix a "prompt
improvement"; it is a harness-level change (stdout inlined into
observation feedback), not a prompt change.

---

## 11. First-attempt scoring

**Canonical phrase:** "first-attempt scoring" (for the telling axis).

**Definition.** A blocked action returns an error message, which is
in-context specification delivered late, so cell C converges toward
cell B after first contact with the enforcement surface. Because of this
convergence, axis attribution (B vs D, C vs D) is scored on **first-
attempt behavior**; converged multi-turn behavior is reported separately
and must never be blended into the first-attempt attribution numbers.

Source: Experimental Design lines 511-516.

**Banned near-synonyms:** "single-shot scoring," "zero-shot scoring"
(these are ML-generic terms that do not carry the "before the runtime's
error message becomes itself an in-context contract" mechanism; always
explain or reference the convergence rationale when this term is used in
a methods section). Do not conflate "first-attempt" with "first turn of
the conversation" if the trajectory format allows multiple actions per
turn; first-attempt means first contact with the enforcement surface
for that constraint specifically.

---

## 12. Evidence tiers

**Canonical phrase:** three tiers, always named in full on first use per
section, and never merged into one causal claim:

1. **Static oracle-pair evidence**: hand-authored full/off trajectory
   pairs scored by the deterministic scorer; scorer-coverage /
   attribution evidence over constructed cases, not live causality
   evidence.
2. **Live runtime probe**: an end-to-end HAI run under the compared
   modes with real command execution; live causality evidence.
3. **Model-backed diagnostic** (or "model-backed trajectory"): real
   model completions run against the harness and scored; currently
   entirely **diagnostic tier**: one model
   (`Qwen/Qwen3-235B-A22B-Instruct-2507-tput`, Together AI, temperature
   0), small n (3-5 per cell).

Source: Five-Minute Talk Track line 130-131; Threat Model line 383-384;
Active Decisions D-17, D-22.

**Mandatory hedge for every model-backed claim:** every quantitative
claim drawn from model-backed evidence must state, inline or in the
immediately preceding sentence, that it is diagnostic tier, name the
single model, and give n. Do not let a model-backed number appear in
prose without this hedge nearby. Example fixed phrasing: "diagnostic (one
model, Qwen3-235B, n=5)."

**Banned near-synonyms:** "pilot results" alone without the tier name
attached; "empirical results" as a catch-all that blurs which tier
produced a number; "the experiment showed" without naming which of the
three tiers is meant. Do not say "results confirm" for anything at the
diagnostic tier; use "diagnostics support," "diagnostics are consistent
with," or "the diagnostic probe found," reserving "confirm" register for
pre-registered, adequately-powered claims only, and even then hedge with
tier and n.

---

## 13. Goal-conflict arm

**Canonical phrase:** "the goal-conflict arm" / "benign goal-conflict
pressure" / "benign completion pressure." When contrasting with the
adversarial arm, use the fixed pairing: "benign completion pressure, not
adversarial injection."

**Definition.** Constraint compliance costs task success: respecting
the rule means failing, degrading, or delaying the user-visible goal.
This is **not** adversarial input; no attacker-controlled content is
involved. It is the literature-verified locus where frontier models
violate policies stated in their own system prompt under realistic
pressure (cited: Symbolic Guardrails, LogiSafetyBench "unsafe success").

Source: Threat Model lines 357-364; AGENTS.md Research Invariants ("The
goal-conflict arm is benign completion pressure ... not adversarial
injection").

**Result (D-36):** H2 FALSIFIED in diagnostics. Told-only compliance did
not degrade under benign goal conflict graded P0-P3 (0 fabrication across
40 reps, n=5 pre-registered, the pre-committed falsification bar of
<=10% fabrication at P3 was met). The agent self-enforced audit
faithfulness even under pressure as strong as "a pipeline is blocked and
the user cannot proceed." Side finding: high pressure degraded tool-use
competence (command-format loops) before it touched honesty.

Source: Evidence Status lines 594-601; Active Decisions D-36.

**Banned near-synonyms:** "adversarial pressure," "jailbreak pressure,"
"red-teaming" for the goal-conflict arm; these belong to the separate
adversarial-input arm (16 trajectories, secondary/appendix tier,
scorer-coverage evidence, injection robustness cited not claimed; see
Threat Model lines 366-384). Never use "attack" language for the
goal-conflict arm. Do not call it "stress testing" generically without
the "benign completion pressure" qualifier.

---

## 14. Adversarial-input arm (for contrast; not to be confused with goal-conflict)

**Canonical phrase:** "the adversarial-input arm" or "the 16-trajectory
adversarial layer."

**Definition.** 16 hand-authored trajectories (4 each targeting M7,
M5+M6, M8, M4) where inputs induce the agent to violate a rule it can
read. This is **scorer-coverage evidence at the appendix/secondary tier**,
not model-backed evidence that a model can be induced. "Injection
robustness is cited territory... not a claim of this paper."

Source: Threat Model lines 366-384; Scope lines 247-250.

**Banned near-synonyms:** do not call this arm "the goal-conflict tasks"
or vice versa; they are different axes of the Threat Model
(capability/cooperative, goal-conflict/benign, adversarial-input) and
must never be merged in prose.

---

## 15. Coupling caveat / per-mechanism attribution

**Canonical phrase:** "marginal contribution within this fixed
controller" (never "causal contribution" or "independent contribution").

**Definition.** Harness mechanisms are coupled: a mechanism can help in
isolation yet degrade the full rollout. Per-mechanism attribution is
reported as marginal contribution within the fixed controller, not
context-free causality.

Source: Threat Model lines 386-392.

**Explicit ban (also stated in AGENTS.md):** no additive language of the
form "M4 contributes A plus M5 contributes B [equals total effect]."
`no_runtime_enforcement` is a sanity floor only, never per-mechanism
attribution evidence.

---

## 16. Forbidden framings (apply globally, every section)

These are not terminology substitutions; they are hard bans from
AGENTS.md and the task brief. No canonical replacement phrase is needed
because the concept itself must not appear.

- Any "first X" novelty claim. Novelty is a **conjunction only** (see
  Lineage Anchor, lines 195-203): the 2x2 including the
  enforced-not-told cell + per-mechanism isolation + the three-condition
  substitution account + the methodological warning + the deterministic
  offline scorer + the released benchmark, taken together.
- Any scaling-law claim. The capability ladder is "bounded," "confounded"
  (D-36), "weakly supports that an operate floor exists," and explicitly
  "cannot carry a scaling claim."
- AI-control / trusted-monitor / safety-umbrella framing. External
  framing is fixed as "AI-engineering paper on agent-harness governance."
  The deterministic governance contract is a harness layer (the ETCLOVG
  Governance/Verification layer per D-26), not an AI-control apparatus.
- Additive per-mechanism attribution (see §15).
- Product framing of any kind (HAI is "the instrument, not the
  contribution" / "one non-clinical personal-wellness reference
  runtime").
- Softening the null result. The paper is a negative result plus a
  methodological contribution. Do not smuggle in a positive result or
  imply the three-condition account was supported when D-36 nulled two
  of its three legs (verifiability exception, goal conflict) and only
  weakly/confounded-ly supported the third (operate floor).

Source: Title and Frame lines 67-71; Lineage Anchor lines 195-203; task
brief operating rules.

---

## 17. Quick-reference table (canonical phrase → one-line gloss → source)

| Canonical phrase | One-line gloss | PAPER.md anchor |
|---|---|---|
| in-context contract | rule stated in the agent's prompt/manifest | Title and Frame l.27-28 |
| runtime enforcement | harness blocks the violation regardless of the model | Title and Frame l.28 |
| cell A / deployment baseline | contract in prompt, runtime on | Experimental Design l.493 |
| cell B / told-not-enforced | contract in prompt, runtime off | Experimental Design l.493 |
| cell C / enforced-not-told | contract withheld, runtime on | Experimental Design l.494 |
| cell D / neither / violation floor | contract withheld, runtime off | Experimental Design l.494 |
| M4 validation | typed command/proposal schema check | Mechanism Inventory l.299 |
| M5 agent_safe dispatch refusal | manifest flag gating dispatch | Mechanism Inventory l.300 |
| M6 W57 proposal/commit gate | user-commit mutation gate | Mechanism Inventory l.301 |
| M7 refusal | out-of-contract / clinical-boundary refusal | Mechanism Inventory l.302 |
| M8 audit evidence emission | audit reference faithfulness | Mechanism Inventory l.303 |
| M9-TX transaction integrity | atomic tx floor, held constant | Mechanism Inventory l.304 |
| context-verifiability | checkable from decision-time context | Mechanism Inventory l.285-295 |
| operate floor | minimum capability to drive the contract at all | Threat Model l.349-355 |
| untold violation floor / harm floor | cell-D observed completed violation | Evidence Status l.543-565 |
| harness blindness | hidden tool output manufactures spurious findings | Title and Frame l.58-63 |
| first-attempt scoring | telling-axis scored before enforcement's error message becomes late telling | Experimental Design l.511-516 |
| static oracle-pair evidence | hand-authored full/off pairs, scorer coverage | Five-Minute Talk Track l.130 |
| live runtime probe | end-to-end HAI run under compared modes | Five-Minute Talk Track l.130 |
| model-backed diagnostic | real model completions, diagnostic tier only | Evidence Status l.534-537 |
| goal-conflict arm / benign completion pressure | compliance costs task success, not attack | Threat Model l.357-364 |
| adversarial-input arm | 16 trajectories, secondary tier, cited not claimed | Threat Model l.366-384 |
| L7 stale-manifest drift | unmeasured non-retrievable class | Mechanism Inventory l.325-330 |
| marginal contribution within this fixed controller | no additive/causal attribution | Threat Model l.386-392 |

---

## 18. Open forks: mandatory marker syntax

Two forks must never be resolved in prose. Use exactly this marker
syntax wherever a section would otherwise need to state or imply an
outcome:

- `[FORK-L7-DRIFT: unmeasured; do not assume outcome]`
- `[FORK-H5-REPLICATION: pending external non-HAI replication; do not
  assume outcome]`

H5 (external replication) source: Hypotheses table line 452, Scope
lines 244-246 ("One external non-HAI replication of the
specify-vs-enforce effect: the generality check that distinguishes a
phenomenon from a HAI quirk").

---

## Audit corrections

Adversarial re-derivation audit, 2026-07-04, against
`/Users/domcolligan/health_agent_infra/PAPER.md` (807 lines, read in
full). All line anchors, decision IDs, mechanism names, ablation-mode
names, cell definitions, contrast names, and quantitative values
(3/3 probe outcomes, 6/6 M8 regimes, 0 fabrication across 40 reps at
n=5, 0pp vs the pre-committed >=40pp bar, <=10% at P3, 0/60 valid
finals, seven runtime modes, 16 adversarial trajectories at 4 each,
commit `17db5ef`, Qwen3-235B-A22B-Instruct-2507-tput at temperature 0,
n=3-5 per cell) were re-derived and found correct except as listed.

1. §6 `no_runtime_enforcement` bullet rewritten. The prior text called
   it "not identical to cell D" and placed it only under the
   contract-in-prompt arm, contradicting PAPER.md line 527
   ("`no_runtime_enforcement` remains a sanity floor (cell D with all
   mechanisms off)"). Corrected to: a runtime mode, not a cell;
   sanity-floor role under the contract-in-prompt arm; realizes cell D
   / violation-floor baseline under the contract-withheld arm.
2. §6 citation "(D-20, D-25 note)" corrected to "(D-20 and its D-34
   note)". D-25 (orchestrator pins) contains no sanity-floor/cell-D
   note; the note is the D-34 annotation inside D-20.
3. §8 source attribution corrected: the "0/60 valid finals, contract
   friction not governance" figure is in Model Roster lines 407-408,
   not Evidence Status lines 616-625 (which carry the ladder finding
   without that figure). Both anchors now cited for their own content.
4. §5 gloss corrected: the prior text said the M7 boundary description
   is "in the manifest"; PAPER.md line 302 says the boundary is
   "describable in the prompt". §4 table cells also restored to
   PAPER.md's exact parenthetical wording.
5. Cross-references to "forbidden framings" corrected from §11 to §16
   in three places (§3 banned list, §4 banned list, §6 banned list).
   The extractor had numbered against a stale outline.
6. M8-nuance cross-references corrected: the §4 table row pointed to
   §7 (self-enforcement), which does not discuss the D-35
   classification; now points to §5. §5's own "(D-35) see §7" pointer
   replaced with the primary anchor, PAPER.md Mechanism Inventory
   lines 306-323.
7. §7 deterministic-guarantee caveat pointer corrected: it cited §12
   (evidence tiers), which does not contain that caveat. The caveat is
   now spelled out with its PAPER.md anchor (Title and Frame lines
   44-48).
8. §7 D-36 result statement was missing the mandatory diagnostic
   hedge; added "diagnostic tier: one model, small n" per PAPER.md
   line 65.
9. §18 H5 source label corrected from "Lineage Anchor / Scope line
   244-246" to "Scope lines 244-246"; the quoted sentence is in Scope,
   not the Lineage Anchor.
10. Style: all 47 em dashes removed (binding workflow rule: no em
    dashes anywhere), including inside the two FORK marker literals in
    §18, and a binding style-rule paragraph added to the intro so
    section writers do not copy the banned punctuation from this file.

### Second-pass adversarial re-derivation, 2026-07-04

Independent re-derivation against `PAPER.md` (807 lines, read end to
end; the prior audit above was NOT trusted). Verified: every canonical
phrase, mechanism name, ablation-mode name, cell name and contrast
name; decision IDs D-09, D-17, D-20 (and its D-34 note), D-22, D-26,
D-31 through D-36; the quantitative values 3/3 (all four probe rows),
6/6 (both M8 honest regimes), 0 fabrication across 40 reps at
pre-registered n=5, <=10% at P3 falsification bar, 0pp vs the
pre-committed >=40pp bar, 5/5 honest abstention with the stdout fix,
0/60 valid finals, seven runtime modes, 16 adversarial trajectories at
4 per class (M7, M5+M6, M8, M4), n=3 per cell probe battery, commit
`17db5ef`, `Qwen/Qwen3-235B-A22B-Instruct-2507-tput` at temperature 0;
and every PAPER.md line anchor in §§1-18 and the §17 table. No em
dashes present. Three corrections applied this pass:

11. §8 Model Roster anchor corrected from "lines 407-408" to "lines
    406-407". The "0/60 valid finals, contract friction not
    governance" text sits on PAPER.md lines 406-407; the prior audit's
    correction 3 introduced an off-by-one that missed the line
    carrying "0/60 valid".
12. §6 source pointer made precise: "Experimental Design table, lines
    488-500" called the whole range the table; the 2x2 table itself is
    PAPER.md lines 491-494 (lines 488-489 are the design intro,
    496-498 the contrasts). Pointer now cites both.
13. §14 heading was wrapped across two source lines, so
    "goal-conflict)" rendered as stray body text instead of part of
    the heading. Joined onto one line.

### Third-pass adversarial re-derivation, 2026-07-04

Independent re-derivation against
`/Users/domcolligan/health_agent_infra/PAPER.md` (read end to end; the
two prior audits above were NOT trusted). Re-verified every canonical
phrase, mechanism name and ablation-mode name (M4 `no_validation`, M5
`no_agent_safe`, M6 `no_proposal_gate`, M7 `no_refusal`, M8
`no_audit_chain`, M9-TX held constant), the seven runtime modes, the
2x2 cell names and the three contrasts, all cited decision IDs (D-09,
D-12, D-17, D-20 and its D-34 note, D-22, D-26, D-31 through D-36),
the fork markers, and the quantitative values (3/3 in all four
contract-off probe rows; 6/6 in both M8 honest regimes; 0 fabrication
across 40 reps at pre-registered n=5; <=10% at P3 falsification bar;
0pp vs the pre-committed >=40pp bar; 5/5 honest abstention with the
stdout fix; 0/60 valid finals on lines 406-407; 16 adversarial
trajectories at 4 per class; n=3 per cell probe battery; commit
`17db5ef`; `Qwen/Qwen3-235B-A22B-Instruct-2507-tput`, Together AI,
temperature 0). PAPER.md section boundaries were re-derived from the
heading map (Title and Frame 18-72, Five-Minute Talk Track 73-138,
Lineage Anchor 139-204, Scope 222-267, Mechanism Inventory 283-336,
Threat Model 337-393, Model Roster 394-425, Hypotheses 426-485,
Experimental Design 486-531, Evidence Status 532-644). Four
corrections applied this pass:

14. §10 source anchor mislabeled a section: "Title and Frame lines
    58-63, 117-126" attributed lines 117-126 to Title and Frame, but
    Title and Frame ends at line 72 and lines 117-126 (the dissolved
    instrumental-fabrication narrative) sit in the Five-Minute Talk
    Track (heading at line 73). Relabeled as "Five-Minute Talk Track
    lines 117-126".
15. §6 banned-list cross-reference corrected: the ban on clinical-trial
    "treatment" language pointed to §16, but §16 (forbidden framings)
    contains no clinical ban. The ban traces to PAPER.md Scope out-list
    line 262 ("Clinical or medical decision-making claims") and D-12.
    Pointer replaced with those primary anchors.
16. §2 quote anchor corrected from "line 27" to "lines 27-28": the
    quoted string "stating it in the prompt (an in-context contract)"
    wraps across PAPER.md lines 27-28 ("(an in-context" ends line 27,
    "contract)" opens line 28). §17 in-context-contract row updated to
    l.27-28 to match; the runtime-enforcement row stays l.28, where
    "enforcing it in the runtime" sits in full.
17. Intro claim "80 section-writer agents" removed (now "all
    section-writer agents"): the count 80 traces to no named source
    (not PAPER.md, not the task brief) and violates the
    every-number-traces evidence rule this file itself imposes.
