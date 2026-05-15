# Future Strategy Review — health-agent-infra

**Date:** 2026-04-29 (round 2 — substantial expansion of round 1, same date)
**Verdict:** PLAN_STRONG_WITH_TARGETED_REVISIONS
**Author.** Claude, two-round extended research session over 13 sub-agents
(8 round-1 product/UX/research; 8 round-2 primary-source + adversarial; 4 of
the round-2 agents failed mid-stream, see § "Limitations").

> **What this is.** A two-round strategic review of the planning tree at
> `reporting/plans/`. **Round 1** produced a Top-10 recommendation set
> from broad survey research. **Round 2** subjected those recommendations
> to (a) adversarial maintainer-perspective review and (b) primary-source
> verification — papers read in full, competitor code inspected on GitHub,
> the project's actual runtime + cli.py + migrations read at depth, the
> project's own canonical docs cross-checked. Round 2 corrected several
> round-1 errors and surfaced new code-level findings round-1 did not see.
>
> **Audit-trail note.** This document is a strategic input, not a plan
> revision. Settled decisions D1-D14 in `AGENTS.md` remain in force unless
> a cycle proposal explicitly opens one. Several round-1 recommendations
> implicitly proposed reopening D4; round 2 walked most of those back.

---

## Table of contents

1. Executive summary
2. What round 1 got right
3. What round 1 got wrong (corrections)
4. New findings from round-2 primary-source inspection
5. Hypotheses (H1-H5) — refreshed verdict
6. Product / user landscape
7. Technical roadmap assessment
8. Eval strategy assessment
9. Documentation / governance assessment
10. Recommended release sequence
11. User-value map
12. Top recommendations (revised, ordered by impact)
13. Open questions for Dom
14. Limitations of this review
15. Sources

---

## 1. Executive summary

The plans are **strategically sound**. The 2026-04-27 strategic +
tactical + eval + success + risks docs collectively form a strong
governing-bet shape; v0.1.11 shipped substantively on time with the
audit cycle pattern intact (10 → 5 → 3 → 0 plan-audit convergence,
healthy halving). Apple Mulberry's Feb 2026 shelving, the EU AI Act +
Digital Omnibus regime, and the AgentSpec / Microsoft Agent
Governance Toolkit lineage have made the project's governance thesis
*more* defensible publicly, not less.

**Round 2 substantially revised round 1.** Of the round-1 Top-10:

- **5 of 10** were 30-minute-consultant mistakes that fight straw-men or
  ignore settled decisions: cli.py split timing (#1 — numbers wrong),
  v0.2.0 split (#2 — breaks W52↔W58 design coupling), `hai init --demo`
  as first impression (#5 — inverts the refusal-IS-the-demo posture),
  read-only UI to v0.3 (#6 — inverts H4), and H5 reframe (#7 — fights
  a straw-man H5 that doesn't match the canonical text).
- **4 of 10** survive with revisions: W-AL push to v0.5 (clean accept),
  "second-user" rename + extension-contract anchoring (accept with
  re-anchoring), judge-adversarial fixtures (fold into W-AI, not a new
  W-id), doc simplifications (partial — historical/ subdir + cycle
  weight tiering; *not* consolidate audit transcripts).
- **1 of 10** is fine but is already in the plan: judge model
  re-benchmark before SHA-pinning (tactical plan §6.1 already says
  "Prometheus-2-7B (or comparable)").

**Round 2 also surfaced 3 code-level concerns round 1 missed:**

1. **D13 asymmetric application.** The threshold-injection seam is
   defended at load time by `_validate_threshold_types`
   (`core/config.py:766-798`), but consumer-site `coerce_*` use is
   uneven — recovery, running, sleep, and stress R-rules read
   `t["policy"][...]` directly without defensive coercers. If a future
   caller bypasses `load_thresholds`, four domains silently coerce
   bool-as-int. D13 is documented as "trusted by design" but the
   asymmetry is not.
2. **Hardcoded 6-domain enumeration tables.** ~8 registries
   (`_ACCEPTED_STATE_TABLES`, `RECOMMENDATION_SCHEMA_BY_DOMAIN`,
   `SCHEMA_VERSION_BY_DOMAIN`, `ALLOWED_ACTIONS_BY_DOMAIN`,
   `_DOMAIN_ACTION_REGISTRY`, `_DEFAULT_REVIEW_QUESTIONS`,
   `_DOMAIN_REVIEW_QUESTION_OVERRIDES`, `V1_EXPECTED_DOMAINS`)
   enumerate the six domains by name. None is the source of truth for
   the others; a forgotten registry entry on a 7th-domain expansion
   would be silent failure surface. No test asserts they stay
   synchronised.
3. **The actual moat is narrower than "publishable rule DSL".** The
   R-rule + X-rule code is *competent engineering, not novel theory* —
   any rules-engine team would arrive at structurally similar code
   within a quarter. What is genuinely defensible is (a) the audit
   chain (`proposal_log → planned_recommendation → daily_plan +
   recommendation_log → review_outcome`), (b) the skill-overlay
   invariant (`_overlay_skill_drafts` whitelists three keys, raises
   on anything else, no skill imports in runtime code), and
   (c) the Phase B write-surface guard
   (`guard_phase_b_mutation` in `core/synthesis_policy.py:1217-1264`).
   Strategic plan §6.3 ("R-rule + X-rule policy DSL is publishable
   prior art") oversells. Lead with the audit chain + skill-overlay
   seam instead — those are the moat.

**Net.** The strategic plan does not need reshaping. The tactical plan
needs ~5 targeted edits. v0.1.12 → v0.1.14 sequencing should change
slightly to schedule the cli.py split for v0.1.14 (not v0.1.13, not
"after the trip-wire fires"). The "second user" gate in v0.1.13 should
be honestly named "second developer-user". W-AL belongs in v0.5. A
small judge-adversarial fixture set should fold into W-AI. The
remaining round-1 recommendations should be discounted.

---

## 2. What round 1 got right

These hold under round-2 scrutiny and primary-source verification:

1. **The category claim is real.** Round-2 primary-source inspection
   of the five biggest open-source neighbours (Open Wearables, Pierre,
   garmy, whoop-mcp, garmin-connect-mcp) confirmed that *no* surveyed
   project mentions refusal, audit, ledger, or deterministic policy in
   its README. The vocabulary is "more tools, more sources, prettier
   prose." Apple Mulberry's Feb 2026 shelving + EU AI Act regime +
   AgentSpec / Microsoft Agent Governance Toolkit (April 2026) all
   strengthen the governance posture publicly.

2. **The audit-cycle pattern is converging well.** v0.1.11's
   plan-audit caught 18 findings across 4 rounds (10 → 5 → 3 → 0 —
   clean halving). Caught two fail-open correctness bugs at plan-time,
   not post-implementation. The maintainer's judgement to skip Phase 0
   for v0.1.11 (recorded in `RELEASE_PROOF.md § 2.6`) shows the cycle
   pattern is being exercised, not ritualised.

3. **Hypotheses H2/H3/H4 are strengthened by 2024-2026 research.**
   Local-first (H2) is on the right side of the EU AI Act + Digital
   Omnibus + 61% of Western European CIOs reprioritising local stacks.
   AgentSpec + Microsoft's April-2026 Agent Governance Toolkit make
   user-gated mutation (H3) textbook practice. PHIA + SePA +
   Single-Agent-with-Skills (H4) consistently show LLM-driving-tool
   beats end-to-end LLM as base models improve.

4. **The skill-vs-code boundary holds under code reading.** Direct
   inspection of `recovery-readiness/SKILL.md` and
   `strength-readiness/SKILL.md`: no arithmetic-shaped tokens.
   `_overlay_skill_drafts` (`core/synthesis.py:259-386`) explicitly
   whitelists three keys (`rationale`, `uncertainty`,
   `follow_up.review_question`) and raises
   `SynthesisError("skill_overlay_out_of_lane")` on anything else.
   `grep "skills" core/` returns zero matches — `synthesis.py` does
   not import from `skills/`. The boundary is enforced as a fail-loud
   invariant.

5. **Five-doc strategic split is the right shape.** Each has a
   distinct primary reader-intent the README routes to.

6. **The refusal-as-feature posture is well-aligned with 2025-2026
   adversarial literature.** The Beyond-Benchmarks medical red-team
   paper ([arxiv 2508.00923](https://arxiv.org/html/2508.00923))
   reports 94% accuracy collapse under perturbation. Vendor coaches
   confidently misclassify in real reviews
   ([TechRadar 2026 on Garmin](https://www.techradar.com/health-fitness/smartwatches/garmins-new-subscription-ai-feature-is-hilariously-bad-so-far)).
   Refusal as a first-class action is exactly where the literature
   converges.

---

## 3. What round 1 got wrong (corrections)

Round 2's adversarial agent + cli.py-quantitative agent + competitor-code
agent + runtime-code agent collectively pushed back on five round-1
recommendations. Documenting the corrections honestly:

### 3.1 Round-1 #1 — "Schedule cli.py split into v0.1.13 BEFORE W-AA-AG"

**The claim was wrong on numbers.** Round-2 git inspection of cli.py at
each tag:

| Tag | Lines | Δ |
|---|---|---|
| v0.1.7 | 6265 | — |
| v0.1.8 | 7974 | +1709 (one-off, post-audit-cycle) |
| v0.1.9 | 8239 | +265 |
| v0.1.10 | 8313 | **+74** |
| v0.1.11 | 8723 | +410 (demo-driven: W-Va + W-W + W-X) |

**Median Δ across the last 5 minor releases is +331, not +400.** The
round-1 "+400/release" framing was extrapolating across an unusual
v0.1.11 inflation (demo-isolation work) without controlling for the
one-off. v0.1.13's actual cli.py-touching scope (W-AA `hai init`
extension, W-AB renderer-mostly, W-AD distributed string edits, W-AE
mostly `core/doctor/`) is plausibly +200 to +400 lines. Realistic
v0.1.13 ship at 9050-9400, not "&gt;9700". **The 10k trip-wire fires
v0.2.x at the earliest, not v0.1.13.**

The recommendation was also tactically wrong: scheduling a 3-4 day
mechanical refactor *into* the v0.1.13 onboarding cycle co-mingles a
structural change with the project's first-external-user release.
v0.1.13's success criterion is "fresh user reaches first
recommendation in &lt;5 min," not "internal architecture cleaner."

**Corrected recommendation:** schedule the split for **v0.1.14** (the
eval-substrate cycle, 13-18 days, where cli.py touches are modest —
`hai eval run --scenario-set` is one new handler). Splitting before
v0.2.0's W52 (`hai review weekly`) and W53 (insight-ledger commands)
land saves ~1 day of merge-and-review work in v0.2.0. Treat the 10k
line count as the **abort condition** (promote to v0.1.13 if
actual v0.1.13 work pushes past 9500), not the trigger. Concrete
split shape (locked-in if scheduled): `cli/main.py` + `cli/_shared.py`
+ 11 `cli/handlers/<group>.py` files. Each &lt;2500 lines, most &lt;1000.
Effort 3-4 focused days.

### 3.2 Round-1 #2 — "Split v0.2.0 into v0.2.0 (W52) + v0.2.1 (W53 + W58)"

**The recommendation breaks the W52↔W58 design coupling.** W58 (the
factuality gate) exists *to block delivery of W52's weekly review when
it contains unsupported claims*. Shipping W52 without W58 ships an
unbounded-narration weekly summary — exactly the shape strategic plan
§6.1 + H1 reject. Tactical plan §6 names W52+W53+W58 as the v0.2.0
anchor; §9 "Risk-driven scope cuts" lists them as DO-NOT-CUT.
Splitting them inverts the dependency the design has been pointing at
since the v0.1.9 pre-cut.

The "v0.1.11 budgeted 22-30 days; v0.2.0 at 15-20 days looks low"
framing was also off: v0.1.11 *shipped under budget* (started
2026-04-28, shipped 2026-04-28 per RELEASE_PROOF). The 15-20 day
estimate for v0.2.0 is not obviously over-budget given the v0.1.11
cycle pattern.

**Corrected recommendation: REJECT round-1 #2.** If v0.2.0 over-runs,
defer the *whole release*, don't split the gate from the thing it
gates. Keep W52+W53+W58 atomic.

### 3.3 Round-1 #5 — "Make `hai init --demo` the documented first command"

**The recommendation inverts the project's strategic posture.** Three
explicit signals point the other way:

- Strategic plan §6.1 ("Lead with the governance contract, not the
  data ingest") and §6.3 ("Ship the credible artifact") both point at
  audit-chain-as-feature, not demo-flow-as-feature.
- Memory note `feedback_demo_refusal_is_the_demo` (validated
  2026-04-28): "Lean into defer/escalate/won't-fabricate moments as
  the feature, not as limitation."
- Memory note `feedback_inform_before_synthesizing`: "an informed plan
  or no plan."

A `hai init --demo` with a packaged demo agent that posts six
DomainProposals papers over what should be the actual day-1
experience (correct deferral when there's no signal). The user
*should* see "insufficient signal" everywhere on day 1, and v0.1.13
W-AG (cold-start prose) is exactly the workstream that turns that
into a feature, not a bug.

**Corrected recommendation: REJECT round-1 #5.** Fix the bare-CLI-flow
gap *honestly* — better defer prose, `hai daily` explaining what's
missing rather than `awaiting_proposals`, V0.1.13 W-AG cold-start
prose pass — not by papering over with a demo agent. The W-Va `hai
demo` command shipped in v0.1.11 is a *demoer's tool*, not a
first-impression command for an arriving user. Keep that distinction.

### 3.4 Round-1 #6 — "Move read-only UI decision-checkpoint from v0.5 to v0.3"

**The recommendation inverts H4's posture.** H4 says LLM agents
driving CLIs &gt; LLM agents reasoning end-to-end. v0.3-0.4 is MCP +
extension contracts (Wave 3) — MCP is exactly the protocol that
*substitutes* for a UI for the agent-driven access pattern. Adding a
UI decision-checkpoint at v0.3 alongside MCP work invites scope
leakage in the very release the project should be doubling down on
agent-access-as-the-surface.

Strategic plan §8.3 puts read-only UI at "v0.5+ — only if user
feedback indicates CLI-only is a hard ceiling." That conditional is
load-bearing; there is no second-user feedback yet. "Decision-checkpoint
not necessarily ship-checkpoint" is a soft-pedal — every checkpoint
the maintainer takes seriously costs cycle days.

**Corrected recommendation: REJECT round-1 #6.** Keep the read-only UI
decision at v0.5. v0.3-0.4 should ship MCP + extension contracts with
the CLI/MCP-as-surface posture intact.

### 3.5 Round-1 #7 — "Reframe H5 from user-preference to auditability + cost"

**The recommendation fights a straw-man H5.** Read H5 as actually
written:

> H5. A small set of governed ledgers + a strict code-vs-skill
> boundary scales further than a multi-agent prose-driven
> architecture.

Nowhere in the H5 evidence and falsification sections does
"user preference" appear. The falsification criterion is **internal**:
"if the project itself starts to need a multi-agent shape to ship the
next release." Google PHA's 2508.20148 user-preference data does not
falsify H5 *as written* because H5 is not a user-preference claim. It
is a *complexity-and-governance-per-unit-of-runtime-shipped-by-one-
maintainer* claim.

The round-1 reframing weakened H5 first, then proposed a fix to the
weakened version. The original is durable.

**Corrected recommendation: REJECT round-1 #7.** Keep H5 as written.
*Possibly* sharpen the falsification language with one note in the
strategic plan to clarify that academic user-preference papers don't
bear directly on H5's project-internal falsification. But do not
reframe the bet itself.

### 3.6 Round-1 was right about

- **W-AL push to v0.5** (#3). Eval-strategy §9.4 is honest that first
  measurement is post-v0.5 + 90 days. Shipping the scaffold 9-12
  months early invites bit-rot. Clean recommendation, no conflict.
- **Judge-adversarial calibration before W58 ships** (#4) — but it
  should fold into W-AI ("ground-truth methodology must produce a
  held-out judge-adversarial set"), not be a new W-AO workstream.
  Tactical plan §5.1 already lines up the work in W-AH+W-AI+W-AJ.
- **"Second-user" gate rename to "second developer-user" + multi-source
  ingest as v0.4 anchor** (#9). Surfaces a real ambiguity in tactical
  plan §4. Revise to keep v0.4's anchor as the *extension contract*
  (per strategic plan §6.1: "Adding new wearable adapters is
  undifferentiated work"), with multi-source ingest as the
  proof-of-contract.
- **Judge model re-benchmark before SHA-pinning** (#8) — already
  implicit in tactical plan §6.1's "Prometheus-2-7B (or comparable)".
  Sharpen the W-AJ scaffold acceptance criteria; not new work.
- **Doc simplifications** (#10) — accept (b) historical/ subdir,
  accept (d) cycle weight tiering, **reject (a)** consolidating
  per-round audit files (the per-round granularity is the artifact of
  D14, consolidation undermines the very record D14 produces),
  revise (c) to a single line in AGENTS.md not 6 items.

---

## 4. New findings from round-2 primary-source inspection

Round-2 read parts of the runtime that round 1 didn't touch. Three
findings have direct implications for the plan.

### 4.1 D13 asymmetric application

`core/config.py:_validate_threshold_types` (lines 766-798) is the
load-time defence: walks the merged TOML+default dict, rejects any
leaf whose type doesn't match the default, including bool-as-int via
the strict bool helper `_is_strict_bool` (line 642). This is the
well-engineered piece.

But at consumer sites, the `coerce_*` defensive helpers are applied
**unevenly**:

**Sites that use the helpers** (correct):
- `domains/strength/policy.py:127-134` — coerce_int + coerce_float
- `domains/nutrition/policy.py:127-146` — coerce_int + coerce_float
- `domains/nutrition/classify.py:102-105` — coerce_float
- `core/synthesis_policy.py` — coerce_float/coerce_int in evaluate_x2
  (line 577), x3a (line 670), x3b (line 715), x4 (line 810), x5
  (line 884), x6a (line 950), x6b (line 1009), x7 reader (line 382)

**Sites that read `t[...]` directly** (asymmetric):
- `domains/recovery/policy.py:114` —
  `threshold = t["policy"]["recovery"]["r6_resting_hr_spike_days_threshold"]`
- `domains/running/policy.py:113` —
  `threshold = t["policy"]["running"]["r_acwr_spike_min_ratio"]`
- `domains/sleep/policy.py:123-124` — `threshold_hours`,
  `threshold_nights`
- `domains/stress/policy.py:127-128` — `threshold_score`,
  `threshold_days`
- All `*/classify.py` modules read `cfg["..._min_hours"]` directly
  without coerce_*

**Implication.** If a future caller bypasses `load_thresholds` and
constructs a threshold dict in-memory with a bool, four R-rule
domains silently coerce. D13 documents this as "trusted by design"
— but the asymmetry is not. D13's exact wording (per
`v0_1_11/W_T_audit.md`): "every `evaluate_*_policy` /
`classify_*_state` entry point accepts a `thresholds:
Optional[dict]` arg, but in-memory construction + direct
pass-through is reserved for tests (trusted by design) and
intentional defensive paths."

**Recommended action.** This is a v0.1.12 small-scope addition, not a
new W-id. Either: (a) sweep the four domain policies (recovery,
running, sleep, stress) and the six classify modules to apply
`coerce_*` at every consumer site for symmetry; or (b) add a
contract test that scans for raw `t["policy"]` reads at consumer
sites and fails loudly on any new ones. Option (b) is cheaper
(~30 min); option (a) is more thorough (~half-day). Cycle time
suggests (b) is the right size.

### 4.2 Hardcoded 6-domain enumeration tables

The synthesis layer is *not* fully data-driven. ~8 registries
enumerate the six domains by name:

- `_ACCEPTED_STATE_TABLES` (`core/synthesis.py:393`)
- `RECOMMENDATION_SCHEMA_BY_DOMAIN` (`core/synthesis.py:81`)
- `SCHEMA_VERSION_BY_DOMAIN` (`core/validate.py:94`)
- `ALLOWED_ACTIONS_BY_DOMAIN` (`core/validate.py:35`)
- `_DOMAIN_ACTION_REGISTRY` (`core/synthesis_policy.py:65-86`) — only
  knows recovery/running/strength; sleep/stress/nutrition are
  silently absent (intentional, per X-rule scope, but encoded by
  *omission from a dict*)
- `_DEFAULT_REVIEW_QUESTIONS` (`core/synthesis.py:175`)
- `_DOMAIN_REVIEW_QUESTION_OVERRIDES`
- `V1_EXPECTED_DOMAINS` (`core/synthesis.py:624`)

None is the source of truth for the others. A forgotten registry
entry on a 7th-domain expansion (mental health at v0.7+ per strategic
plan §8.1) is a silent failure surface.

**Implication.** The 7th-domain extensibility story is mostly
ready (the per-domain `schemas/classify/policy` shape composes
cleanly), but the synthesis-layer registries need either (a) a
sync-test that asserts every domain in `ALLOWED_ACTIONS_BY_DOMAIN`
appears in every other registry it should, or (b) a single
domain-registry source-of-truth that other tables derive from.

**Recommended action.** Schedule **W-DOMAIN-SYNC** as a v0.1.13 or
v0.1.14 cross-cutting workstream: ~150-line Python file +
contract test that introspects all 8 registries against a single
truth table. ~half-day work. Pays off when the 7th-domain
expansion lands and would have to thread through 8 files anyway.
Even if the 7th domain never lands, the test prevents a future
intern's "I added one X-rule for nutrition but forgot the
registry entry" silent bug.

### 4.3 The actual moat — narrower than "publishable rule DSL"

Strategic plan §6.3 frames the R-rule + X-rule policy DSL as
"publishable prior art." Round-2 code reading concludes: **this is
overstated.** What the runtime actually has is competent applied
engineering — well-organised Python with stable structural conventions
(rule signature `(snapshot, proposals, thresholds) → list[XRuleFiring]`,
frozen dataclasses, two-phase split, threshold TOML override). Not a
DSL in any meaningful sense. There is no parser, no rule-table format,
no declarative grammar. A team replicating the structural moves would
reproduce them in 1-2 weeks.

What IS genuinely defensible (per code reading):

1. **The audit chain.** `proposal_log → planned_recommendation →
   daily_plan + recommendation_log → review_outcome` plus
   `x_rule_firing` rows linked atomically. The atomicity contract
   (`BEGIN EXCLUSIVE` at `synthesis.py:914`, every projector called
   with `commit_after=False`, single `conn.commit()` at line 1008,
   `conn.rollback()` on any exception, validator runs *before* `BEGIN`)
   is real and the rollback story is clean.
2. **The skill-overlay invariant.** Three whitelisted fields, fail-loud
   on anything else, no skill imports in runtime code. **This is the
   single piece most teams would *not* arrive at** — the typical reflex
   is "let the LLM emit a JSON blob and parse it." Refusing to do that
   is the moat-y move.
3. **The Phase B write-surface guard.** `guard_phase_b_mutation`
   (`core/synthesis_policy.py:1217-1264`) encodes "post-skill rules
   can only nudge action_detail" as a runtime exception, not a
   convention. Rejects any mutation touching `action`, any wrong-domain
   firing, any non-`adjust` tier. Strict.
4. **Threshold-injection load-time validation.** The bool-as-int
   rejection at `_validate_threshold_types` is industrial-grade.

**Implication.** The strategic claim should lead with **"governance
contract + audit chain + skill-overlay seam"**, not **"the rule DSL is
publishable."** The first three are the actual moat. The rule engine
is table stakes. Round-2 also recommends: lead calibration evidence
(threshold values derived from dogfood findings — v0.1.10 W-C
partial-day gate, v0.1.11 W-B sessions floor) over architecture
novelty.

**Recommended action.** Edit strategic plan §6.3 to soften the "DSL"
framing. One paragraph rewrite. Effectively a *truth-in-marketing*
pass on the strategic plan to align with what the code actually
contains — particularly important if the §6.3 publication path is
pursued at v0.6 (per strategic plan Branch 4).

---

## 5. Hypotheses (H1-H5) — refreshed verdict

| H | Status | Evidence movement (round 1 → round 2) |
|---|---|---|
| **H1** interpretability > better recs | strengthened | EU AI Act + FAIR-AI healthcare framework + Holland & Knight April 2026 compliance survey all converge on auditability + immutable audit trails as first-class HHS priorities. Apple Mulberry shelving (Feb 2026) validates publicly. Caveat: stronger as a positioning bet, less directly as a user-preference bet. |
| **H2** local-first > hosted | strengthened | EU Digital Omnibus Nov 2025; 61% Western European CIO local-stack reprioritisation; Apple silicon ML acceleration + open-weight 7B-class models adequate for judge work. |
| **H3** user-authored intent + bounded supersession | strengthened | AgentSpec (arxiv 2503.18666) + Pro2Guard (arxiv 2508.00500) + Microsoft Agent Governance Toolkit (April 2026) make user-gated mutation textbook. |
| **H4** LLM-driving-CLI > end-to-end LLM | strengthened | PHIA (Nature Comms 2025) + SePA + Single-Agent-with-Skills lineage all point this way. |
| **H5** small governed ledgers > multi-agent prose | **unchanged** (round-1 attempted reframe REJECTED) | H5 as canonically written is *not* a user-preference claim; its falsification criterion is internal ("if the project starts to need a multi-agent shape to ship"). Google PHA 2508.20148 user-preference data does not bear on H5 as written. v0.1.10 cycle (9 W-ids + 36 tests + persona harness in single session) is positive evidence. |

---

## 6. Product / user landscape

**What I found** (from round-1 web research + round-2 primary-source
GitHub inspection):

- **Apple Mulberry shelved Feb 2026** citing FDA + AI reliability
  concerns ([Bloomberg 2026-02-05](https://www.bloomberg.com/news/articles/2026-02-05/apple-is-scaling-back-plans-for-new-ai-based-health-coach-service)).
  Strongest single piece of public validation for the governance
  thesis.
- **Garmin Connect+ Active Intelligence** panned in April 2026 reviews
  as "the laziest, simplest implementation of AI"
  ([5krunner](https://the5krunner.com/2026/04/20/garmin-connect-plus-review/),
  [TechRadar](https://www.techradar.com/health-fitness/smartwatches/garmins-new-subscription-ai-feature-is-hilariously-bad-so-far)).
  Strengthens the H1 case.
- **Open-source competitive shape** (round-2 primary-source reading
  of GitHub READMEs + repo trees + sample source files):
  - **Open Wearables** (1.4k stars, v0.4.3 2026-04-14, FastAPI +
    Postgres + Celery, MCP server in `mcp/app/`) — read 5 tools in
    `mcp/app/tools/sleep.py`. Architecturally at "data + prose chat
    via MCP." `prompts.py` is *formatting* prompts, not policy.
    Roadmap promises "natural language conditions, customizable AI
    model support, embeddable widget" — no governance vocabulary.
  - **Pierre** ([Async-IO/pierre_mcp_server](https://github.com/Async-IO/pierre_mcp_server))
    — **repo returns HTTP 404 from both authed `gh api` and unauthed
    curl as of 2026-04-29.** Aggregator copy claims 25-53 MCP tools,
    Rust, OAuth 2.0 + A2A. The "150+ wearables" phrase appears only
    in promotional aggregators, not primary docs. Repo unreachable
    today is itself a maintenance signal.
  - **garmy** (56 stars, v1.0.0 June 2025, last push 2025-07-06,
    Python + SQLite + read-only MCP) — read `mcp/server.py`
    `QueryValidator`. Whitelists select/with, blocks
    insert/update/delete/etc., default LIMIT 1000. **Security
    boundary, not governance boundary.** Closest to
    health-agent-infra in *posture* but not *scope*. 9 months
    dormant.
  - **whoop-mcp / garmin-connect-mcp** — pure data wrappers, wrong
    shape entirely.
- **Vocabulary check.** I searched every primary README for the words
  refusal, audit, governance, hallucination, deterministic, policy,
  classification, ledger. **Zero hits across all five.** The OSS
  vocabulary is "more tools, more sources, more vendors, prettier
  prose" — not the governance frame.

**12-month threat estimate (revised down from round-1):**

- *Open Wearables:* 8-12% — org momentum + 1.4k stars but no governance
  signal, would need strategic pivot.
- *Pierre:* &lt;5% — repo 404 today.
- *garmy:* 5% — closest architecturally but single-author + 9-month
  dormancy.
- *whoop-mcp / garmin-connect-mcp:* &lt;2% — wrong shape.
- *An unnamed fast-mover (someone reads project's public PLANs +
  copies patterns):* 15-25% — the patterns are public; the cycle
  discipline is the moat. **This is the highest-probability threat.**

**Distribution channel — MCP vs pipx + Claude Code skills.** Round-1
identified this as a real concern; round-2 refines: the architectural
threat is overstated, but the *distribution-channel* concern is real.
MCP is the lingua franca in 2026 — Open Wearables, Pierre, garmy,
whoop-mcp, garmin-connect-mcp all ship MCP. Claude Desktop, Cursor,
Windsurf consume MCP natively; Claude Code is a wedge but not the
universe. Cost to dual-publish health-agent-infra as an MCP server:
~1k LOC mirroring the `hai` capabilities boundary, mostly thin
re-exposure of the read surface, mutation surface delegating to `hai`
CLI subprocess. **One focused release cycle.** v0.1.13 or v0.1.14
candidate.

---

## 7. Technical roadmap assessment

### 7.1 v0.1.12 → v0.2.0 sequencing — corrected

Round-2 cli.py + migration inspection shifts several recommendations:

**v0.1.12 (mostly intact).** Per round-1: keep W-Vb (deferred from
v0.1.11) + W-U + W-V + W-H2 + W-S. Round-2 adjustment: add a
**D13-symmetry sweep** (option (b) above — contract test scanning for
raw `t["policy"]` reads at consumer sites). ~30 min work; closes the
asymmetric-application surface for new code.

**v0.1.13 (narrowed — corrected).** Round-1 wanted to insert W-29
cli.py split here. Round-2 says NO: keep v0.1.13 focused on
external-user readiness (W-AA-AG). Add: rename "second user" target to
"second developer-user" honestly. Pull adapter-contract probing into
W-AE (`hai doctor --check-pull`). Bring W-AK persona expected-actions
forward from v0.1.14 (R-T-06 trip-wire — two consecutive cycles
without persona harness changes — about to fire).

**v0.1.14 (reshape).** Schedule **W-29 cli.py split** here as a
3-4-day mechanical refactor. Defer **W-AL calibration scaffold** to
v0.5. Defer **W-AM adversarial scenarios** into v0.2.0 W58 prep. Fold
**W-AO judge-adversarial fixtures** into W-AI (not a new W-id). Add
**W-DOMAIN-SYNC** half-day workstream for the 8-registry contract test.

**v0.2.0 (KEEP ATOMIC — corrected from round 1).** W52 + W53 + W58
ship together. The factuality gate (W58) exists to gate the weekly
review (W52); splitting them ships unbounded narration. Tactical plan
§6 names them as the v0.2.0 anchor; §9 lists them as DO-NOT-CUT.

**v0.3 (per plan, NOT accelerated for UI).** MCP + extension
contracts. Read-only UI decision-checkpoint stays at v0.5. Add:
**dual-publish to MCP server** as a v0.3 anchor (~1 cycle's worth of
work; mirrors `hai` capabilities boundary; offence not defence).

**v0.4-v1.0 (per plan).** No round-2 changes.

### 7.2 cli.py timing — concrete

Round-2 git inspection updates the size projection:

| Tag | Lines | Δ |
|---|---|---|
| v0.1.7 | 6265 | — |
| v0.1.8 | 7974 | +1709 (one-off) |
| v0.1.9 | 8239 | +265 |
| v0.1.10 | 8313 | **+74** |
| v0.1.11 | 8723 | +410 (demo work) |

Median Δ across last 5 minor releases: **+331/release**, not +400.

Projected sizes (median Δ):
- v0.1.12: ~9050
- v0.1.13: ~9400 (W-AA-AG mostly UX wording, not new mutation surface)
- v0.1.14: ~9400 + **(split refactor moves to module package)**
- v0.2.0: with split, into `cli/handlers/<group>.py` files at &lt;2500
  each

10k trip-wire at current trajectory fires v0.2.x at the earliest, not
v0.1.13. **W-29 split should be v0.1.14 work**, with the trip-wire as
abort condition (promote to v0.1.13 if v0.1.13's actual scope pushes
cli.py past 9500).

### 7.3 cli.py split shape (locked-in if scheduled)

```
src/health_agent_infra/cli/
    __init__.py          # re-export main for entry-point compat
    main.py              # build_parser(), main(), _demo_gate, _derive_command_id  (~2400 LoC)
    _shared.py           # _coerce_date, _coerce_dt, _load_json_arg, _emit_json    (~80 LoC)
    handlers/
        pull_clean.py    # cmd_pull, cmd_clean + projector helpers                 (~1300)
        auth.py          # 3 cmd_auth_*                                            (~200)
        writeback.py     # cmd_propose, cmd_synthesize, cmd_explain, cmd_today     (~700)
        memory.py        # 3 cmd_memory_*                                          (~280)
        review.py        # cmd_review_{schedule,record,summary}                    (~340)
        intent_target.py # 10 cmd_intent_/cmd_target_*                             (~410)
        intake.py        # 7 cmd_intake_*                                          (~1100)
        state.py         # 5 cmd_state_*                                           (~280)
        config.py        # 4 cmd_config_*                                          (~330)
        daily_init.py    # cmd_daily, cmd_init, _run_first_pull_backfill           (~750)
        doctor_stats.py  # cmd_doctor, cmd_stats + 6 _emit/_render helpers         (~840)
        capabilities.py  # cmd_capabilities, cmd_research_*, cmd_planned_*         (~100)
        demo.py          # 3 cmd_demo_*                                            (~190)
```

Effort 3-4 focused days. Hard constraint: **no handler body edited
during the move** — edits to handlers happen in separate commits
*after* the split lands. Reopening D4 needs a written cycle proposal
referencing this report's evidence.

### 7.4 Migration debt — corrected

Round-2 inspected all 22 migrations:

- 17 add-tables / 11 add-column-only / 1 reshape (004 drops 4 columns
  from accepted_recovery_state_daily) / 0 destructive replaces
- Largest: 001 (398 LoC). Smallest: 022 (16 LoC). Total: 1709 LoC.
- Existing `verification/tests/test_migrations_roundtrip.py`:
  invariant 1 — `initialize_database` from-scratch is byte-deterministic
  across two fresh files; invariant 2 — JSONL audit-trail reproject
  onto a second fresh DB produces identical recommendation_log /
  review_event / review_outcome rows.
- Per-migration probes already exist for 004, 005, 006, 009, 011,
  013/014.

**Round-2 verdict on round-1's "add per-migration round-trip test
infra" recommendation: NOT NEEDED.** v0.2.0's W52/W53 migrations are
all CREATE-TABLE (additive) — same pattern as 011/015/017/019/020/021
which shipped cleanly. The existing roundtrip pattern + a single
per-table smoke test alongside each new migration is sufficient. No
new test infrastructure needed. The "4 migrations is the largest
single-release burden" framing was correct on count but wrong on
risk: count without shape is not a concern signal.

### 7.5 Persona harness scaling — confirmed

Round-1 estimate: 12 personas × 14 days × ~10 commands/day × subprocess
overhead = ~84s. v0.2 (16 personas × 30 days) ~240s. v0.4 (20 personas
+ multi-day) approaching 10 minutes.

Round-2 confirms: keep D10 settled (full-matrix-not-in-CI). Don't try
to make subprocess-based persona harness CI-feasible at the current
shape. v0.1.12 W-Y CI-subset (2 personas) is the right discipline.

---

## 8. Eval strategy assessment

The eval surface is above field median (per
[JMIR 2025/e79217](https://www.jmir.org/2025/1/e79217); 55% of
exercise/health-coach LLM eval is low-rigor). Specific gaps the
2024-2026 literature flags + round-2 verification:

1. **Factuality-with-source-attribution as a distinct eval class.** Per
   the Springer 2025 fact-checking review and the npj Digital Medicine
   clinical-safety summarisation framework. v0.2.0 W58 partially
   addresses this for the weekly review.
2. **Robustness-under-perturbation** ([arxiv 2508.00923](https://arxiv.org/html/2508.00923)).
   The persona harness tests realistic personas, not adversarial
   perturbations of the same persona's inputs. **Separable axis.**
3. **Inter-rater reliability of the judge against a held-out
   human-graded set.** Not currently committed in the eval strategy.
   Should be a periodic pull, not a one-time scaffold. Fold into W-AI.
4. **PHI-leak adversarial probe.** Round-2 reflection: the runtime is
   local-first SQLite + no telemetry. The 86%-leakage scenario in
   arxiv 2508.00923 is for cloud-LLM contexts. **For health-agent-infra
   specifically, this concern is overstated** — the W57 governance +
   banned-token sweep + local-first posture make PHI leak a host-agent
   concern (Claude Code's data policy), not a runtime concern. Drop
   from the priority list.
5. **Demographic-cue robustness.** Same reasoning as PHI leak — for a
   *deterministic* policy code path that has no demographic cues per
   se, this concern doesn't map. For *skill prose* (which W58 partially
   covers), it does — but as a host-agent concern. Drop from priority.
6. **Prompt-injection through pull source.** Real concern: a malicious
   intervals.icu note carrying instructions could surface in skill
   prompts. Trace: pull → clean → snapshot → skill input. Mitigation:
   strip non-ASCII / sanitize user-source text in the intake layer
   before it reaches skill prompts. v0.1.13 W-AD or v0.1.14 W-AH
   candidate.
7. **Judge-adversarial fixtures** (round-1's W-AO recommendation).
   Fold into W-AI: "ground-truth methodology must produce a held-out
   judge-adversarial set." 30 weekly-review-shaped prose fragments
   with hand-labelled "supportable / unsupportable" verdicts.
   ~1-2 days as part of W-AI scope.

### 8.1 v0.2.0 factuality-gate viability

Architecture credible; model dated. **Re-benchmark before SHA-pinning**:
M-Prometheus-14B ([arxiv 2504.04953](https://arxiv.org/abs/2504.04953)),
Skywork-Reward variants, or a Llama-3.1-8B-Instruct judge with custom
factuality rubric. Tactical plan §6.1 already says "Prometheus-2-7B
(or comparable)" — round-1 just sharpened the implicit. Add to W-AJ
acceptance criteria.

### 8.2 Wave-4 substrate timing

Round-2's calibration-math agent failed mid-stream (API limits).
Round-1's analysis stands: 90 days at daily resolution = ~90
observations is **just above** the minimum to detect moderate-to-large
within-subject effects but **below** what is recommended for confidence
calibration. Split acceptance bars: "estimator runs" (90d) vs
"estimator calibrated" (likely 6+ months OR aggregated-N-of-1 across
personas). The maintainer should decide whether to commit specific N
values; the round-2 calibration agent stalled before it could refine
this.

---

## 9. Documentation / governance assessment

### 9.1 Planning tree — refined verdict

- **Five 2026-04-27 strategic docs are NOT redundant.** Each has a
  distinct primary reader-intent. Keep them.
- **Seven historical files at top level ARE bloat.**
  `multi_release_roadmap.md`, `post_v0_1_roadmap.md`,
  `agent_operable_runtime_plan.md`, `phase_0_*`, `phase_2_5_*`,
  `skill_harness_rfc.md`, `launch_notes.md` should move to
  `historical/`. **Accept**.
- **Per-cycle directories v0_1_4 → v0_1_9** could move to
  `cycles/archive/` after N=2 retention. **Accept** for v0.1.4 → v0.1.9
  when v0.1.13 opens.

### 9.2 Audit-cycle artifact sprawl — REVISED from round 1

Round-1 recommended consolidating 16 round-by-round audit files into
2 append-only logs at ship. Round-2 adversarial review pushed back:
**the per-round granularity is the artifact of D14**. Per AGENTS.md
D14:

> "round 1 caught 10 substantive findings... round 2 caught 5
> second-order contradictions from round-1 revisions... round 3 caught
> 3 stale propagation clauses from round-2 revisions."

That granularity *is* the lesson D14 captures. Consolidating undoes
the artifact that justifies the four-round pattern. **REJECT** the
consolidation recommendation. Keep round-by-round files.

What's still actionable: a **`<cycle>/INDEX.md`** with one-line
summaries of each artifact, dated. Two minutes of work per cycle;
gives a future reader the trail at a glance without losing the
granularity. **Add this to AGENTS.md "Release Cycle Expectation"**
between steps 5 and 6.

### 9.3 Audit-cycle ROI

v0.1.11 plan-audit caught 18 findings across 4 rounds, density curve
10 → 5 → 3 → 0. Clean halving. Pattern is converging. **The cost is
not the rounds — it's the artifact sprawl.** A `<cycle>/INDEX.md`
addresses the sprawl without losing the granularity.

### 9.4 Cycle weight tiering

AGENTS.md D11/D14 already say "doc-only / small-scope releases skip
both Phase 0 and the plan-audit." v0.1.11 RELEASE_PROOF.md § 2.6
exercised this informally by skipping Phase 0. Codify three explicit
classes:

- **Substantive** (D11 + D14 + 4 impl rounds, like v0.1.11)
- **Hardening** (D14 only, 1-2 impl rounds — e.g. v0.1.9)
- **Doc-only** (skip both)

State the chosen class in RELEASE_PROOF.md. **Decision criteria**:
substantive = ≥5 W-ids OR any cross-cutting work OR any new schema
column; hardening = correctness-only sweep; doc-only = README/AGENTS
edits, no code change.

### 9.5 Drift catches

Three drifts in the planning tree at v0.1.11 ship — round-1 found:

- `reporting/plans/README.md` line 95: `v0_1_11/ — ... (in flight)`
  (cycle shipped 2026-04-28).
- `v0_1_11/PLAN.md` lines 16-17: `PRE_AUDIT_PLAN.md` will be authored
  (it wasn't — Phase 0 skipped per RELEASE_PROOF.md § 2.6).
- `tactical_plan_v0_1_x.md` line 35: v0.1.11 ship target 2026-05-15
  (actual 2026-04-28).

R-O-04 ("documentation rot") trip-wire is firing. The 6-item ship-time
freshness checklist in AGENTS.md is the right shape. Round-2 adversarial
agreed but trimmed to 4 items:

```
Post-ship doc-freshness sweep (5 min, blocking on cycle close):
[ ] reporting/plans/README.md — bump Last updated, move cycle from
    "in flight" to closed list.
[ ] tactical_plan_v0_1_x.md § 2 — replace target date with actual
    ship date, add 1-line retro.
[ ] reporting/plans/v0_1_<N>/BACKLOG.md — items still open promoted
    into v0_1_<N+1>/BACKLOG.md.
[ ] AGENTS.md "Settled Decisions" — append D-N entries if cycle
    generated any.
```

Add `<cycle>/INDEX.md` (per § 9.2) as a fifth item only if the cycle
is substantive class.

---

## 10. Recommended release sequence

| Release | Status | Recommendation |
|---|---|---|
| **v0.1.12** | mostly intact | Keep W-Vb + W-U + W-V + W-H2 + W-S. **Add D13-symmetry contract test** (~30 min). Cut W-Z config docs (defer), W-Y CI persona subset (defer). |
| **v0.1.13** | reshape | **Rename gate to "second developer-user".** Pull adapter-contract probing into W-AE. Bring W-AK persona expected-actions forward from v0.1.14. *Do not insert W-29 cli.py split here* (round-1 was wrong on numbers). |
| **v0.1.14** | reshape | **Schedule W-29 cli.py split here** (3-4 day mechanical refactor; concrete shape in §7.3). Add **W-DOMAIN-SYNC** (8-registry contract test, half-day). Fold W-AO judge-adversarial fixtures into W-AI (not new W-id). **Defer W-AL** to v0.5. **Defer W-AM** into v0.2.0 W58 prep. |
| **v0.2.0** | **keep atomic** | W52 + W53 + W58 ship together. Round-1 split recommendation REJECTED — breaks W52↔W58 design coupling. Re-benchmark judge model before SHA-pinning. Lift D4 (capabilities-manifest schema freeze) here when first cryptographic commitment lands. |
| **v0.3** | per plan + MCP | Per plan + **dual-publish health-agent-infra as MCP server** (~1 cycle, mirrors `hai` capabilities boundary). Read-only UI decision-checkpoint stays at v0.5 (NOT v0.3 — round-1 was wrong). |
| **v0.4** | per plan + multi-source | Multi-source ingest (Garmin and/or Apple Health adapter) is the *gating* feature for non-developer reach; keep extension contract as the *anchor* per strategic plan §6.1. |
| **v0.5** | + W-AL | Per plan, plus W-AL calibration scaffold pulled forward from v0.1.14. Split acceptance bars: "estimator runs" (90d) vs "estimator calibrated" (6+ months). |
| **v0.6** | per plan | |
| **v0.7** | per plan | + 7th domain readiness benefits from v0.1.14 W-DOMAIN-SYNC. |
| **v1.0** | per plan | Contingent on calibration acceptance bar (per v0.5 split). |

---

## 11. User-value map

Updated based on round-2 corrections:

| Planned item | User value | Trust/safety | Engineering | Recommendation |
|---|:-:|:-:|:-:|---|
| v0.1.12 W-H2 mypy stylistic | low | low | high | Keep |
| v0.1.12 W-S state-change indicator | high | medium | low | Keep |
| v0.1.12 W-U supersession-kind | medium | high | medium | Keep |
| v0.1.12 W-V strength_status enum | medium | low | medium | Keep |
| v0.1.12 D13-symmetry contract test *(NEW)* | none | high | medium | **Add** |
| v0.1.13 W-AA `hai init` interactive | very high | medium | low | Keep |
| v0.1.13 W-AB `hai capabilities --human` | high | low | low | Keep |
| v0.1.13 W-AD error-message overhaul | high | medium | low | Keep |
| v0.1.13 W-AE `hai doctor` + adapter probe *(EXTENDED)* | high | very high | medium | Keep + extend |
| v0.1.13 W-AG cold-start prose | very high | high | low | Keep — *the* day-1 deferral feature |
| v0.1.13 W-AK persona expected-actions *(MOVED FORWARD)* | low | high | high | **Move forward** |
| v0.1.14 W-AH scenario expansion | low | high | high | Keep |
| v0.1.14 W-AJ judge harness scaffold | low | medium | high | Keep |
| v0.1.14 W-AI ground-truth methodology + **judge-adversarial fixtures** | low | very high | medium | **Extend, not new W-id** |
| v0.1.14 W-AL calibration scaffold | none | none | low | **Push to v0.5** |
| v0.1.14 W-29 cli.py split *(NEW)* | low | low | very high | **Add at v0.1.14, not v0.1.13** |
| v0.1.14 W-DOMAIN-SYNC *(NEW)* | low | high | medium | **Add — preps 7th domain** |
| v0.2.0 W52 weekly review | very high | high | medium | Keep + W58-coupled |
| v0.2.0 W53 insight ledger | high | high | medium | Keep + W58-coupled |
| v0.2.0 W58 factuality gate | low | very high | high | Keep + judge re-benchmark |
| v0.3 dual-publish MCP server *(NEW)* | medium-high | low | medium | **Add — distribution offence** |
| v0.4 multi-source ingest | very high | medium | high | Treat as gating for non-developer reach |
| v0.5 read-only UI decision-checkpoint | very high | medium | medium | Per plan (NOT moved) |

---

## 12. Top recommendations (revised, ordered by impact)

After round-2 corrections, **6 actionable** recommendations:

1. **Schedule W-29 cli.py split for v0.1.14**, not v0.1.13. 3-4 day
   mechanical refactor. Concrete split shape in §7.3 (1 main + 1
   shared + 11 handler-group files, each &lt;2500 lines). Treat the
   10k line count as abort condition, not trigger. Reopen D4 via
   cycle proposal. Land before v0.2.0 W52/W53 commands so they
   inherit the new layout.

2. **Push W-AL calibration scaffold from v0.1.14 to v0.5** (clean
   accept from round 1). Eval-strategy §9.4 already says first
   measurement is post-v0.5 + 90 days; shipping the scaffold 9-12
   months early invites bit-rot.

3. **Add D13-symmetry contract test in v0.1.12** (~30 min). Scans
   for raw `t["policy"][...]` reads at consumer sites; fails loudly
   on any new ones. Closes the asymmetric-application surface flagged
   in §4.1.

4. **Add W-DOMAIN-SYNC in v0.1.14** (~half day). Single contract test
   that introspects all 8 enumeration registries against a single
   truth table. Pays off at 7th-domain expansion (v0.7+); even without
   that, prevents future "added an X-rule but forgot the registry"
   silent bug. See §4.2.

5. **Rename v0.1.13 "second user" gate to "second developer-user".**
   Honest scoping. Treat multi-source ingest (Garmin and/or Apple
   Health adapter) as the v0.4 *gating feature for non-developer
   reach*, with extension contract as the v0.4 anchor (per strategic
   plan §6.1's "data ingest is undifferentiated work" posture).

6. **Dual-publish health-agent-infra as MCP server in v0.3** (~1
   cycle, ~1k LOC). Mirrors `hai` capabilities boundary; read surface
   thin re-exposure; mutation surface delegates to `hai` CLI
   subprocess; W57 commit path NOT exposed via MCP (LLM literally
   cannot deactivate user state through MCP). This is offence
   (distribution-channel reach), not defence — the architectural
   threat from Open Wearables / Pierre / garmy is overstated, but
   MCP-as-distribution is the durable channel in 2026.

**Plus 4 small surgical edits:**

- Edit strategic plan §6.3: soften the "publishable rule DSL" framing
  to "publishable governance contract + audit chain + skill-overlay
  seam" (per §4.3).
- Add a 4-item ship-time freshness checklist to AGENTS.md "Release
  Cycle Expectation" (per §9.5).
- Codify three explicit cycle weight classes (substantive / hardening
  / doc-only) with named criteria (per §9.4). Requires
  `RELEASE_PROOF.md` to state the chosen class.
- Move 7 historical docs (multi_release_roadmap.md, post_v0_1_roadmap.md,
  agent_operable_runtime_plan.md, phase_0_*, phase_2_5_*,
  skill_harness_rfc.md, launch_notes.md) to `reporting/plans/historical/`.
  Update README.md "Historical / superseded docs" pointer.

**Round-1 recommendations REJECTED after round-2 review:**

- ~~Round-1 #2 (split v0.2.0)~~ — breaks W52↔W58 design coupling.
- ~~Round-1 #5 (`hai init --demo` as first impression)~~ — inverts
  refusal-IS-the-demo posture.
- ~~Round-1 #6 (read-only UI to v0.3)~~ — inverts H4.
- ~~Round-1 #7 (reframe H5)~~ — fights straw-man H5.
- ~~Round-1 #10(a) (consolidate per-cycle audit transcripts)~~ —
  per-round granularity is the artifact of D14.

---

## 13. Open questions for Dom

These need maintainer judgement.

### OQ-A. Is the "second user" target in v0.1.13 a developer-user or a non-developer-user?

If developer: v0.1.13 stands modulo the rename + adapter-probe
extension. If non-developer: v0.1.13 is the wrong release; the gate
moves to v0.4 + multi-source ingest + dual-publish-MCP. Strategic
plan §10 Branch 1 + risks §OQ-07 imply this question is open.

### OQ-B. Adopt MCP-server dual-publishing as a v0.3 anchor?

Round-2 distribution-channel research is partial (the MCP-channel
agent stalled before completion). The case for MCP dual-publishing:
durable distribution channel in 2026, mirrors `hai` capabilities
cleanly, ~1 cycle work, offence-not-defence. The case against:
expands the agent-host surface from "Claude Code" to
"any-MCP-host", which slightly weakens the test surface (every host
behaves differently). Worth a scoped proposal before v0.3 PLAN.md
opens.

### OQ-C. Multi-source ingest priority — Garmin or Apple Health first at v0.4?

For non-developer-reach, Apple Health probably unlocks more users.
For technical-recreational reach, Garmin unlocks more sessions. The
order matters — the first adapter sets the per-domain
evidence-contract precedent every later adapter inherits.

### OQ-D. Capabilities-manifest schema freeze (D4) lift timing?

Round-1 recommended lifting at v0.2.x when first cryptographic
commitment (judge_model_sha + judge_score) lands. Round-2 confirms
that's the right trip-wire — earlier than v0.3-0.4 MCP per current
D4 wording.

### OQ-E. Soften strategic plan §6.3 "publishable rule DSL" framing?

Round-2 code reading concludes the rule engine is competent applied
engineering, not novel theory. The audit chain + skill-overlay
invariant + Phase B write-surface guard ARE the moat. If the §6.3
publication path is pursued at v0.6 (per strategic plan Branch 4),
which framing the publication leads with matters. Worth a maintainer
call.

### OQ-F. v0.1.10 dogfood recommendation row carry-forward (round-1 OQ-10)?

Same as round 1: data-management call. Default preserve.

---

## 14. Limitations of this review

**Round-2 had 4 of 8 agents fail mid-stream** due to API rate limits
or watchdog timeouts:

- **Google PHA paper deep-read agent** — hit rate limit before
  completing. Round-1's H5-reframe recommendation is therefore
  REJECTED based on the round-2 adversarial agent's reading of H5's
  canonical text + falsification criterion (which is project-internal,
  not user-preference). The PHA paper's actual experimental design and
  user-preference methodology are not independently verified beyond
  the round-1 web-search summary.
- **N-of-1 calibration math agent** — stalled. Round-1's "90 days =
  estimator runs but not calibrated" claim stands but is not
  refined with explicit posterior CI math. The maintainer should
  treat this as an estimation, not a derivation.
- **MCP / Claude distribution channel agent** — stalled. Round-1's
  recommendation to dual-publish MCP stands but the adoption-data
  case is not deepened. The decision should ride a scoped pre-cycle
  proposal at v0.3 with concrete adoption data of the day.
- **Project canonical-docs agent** — hit rate limit. HYPOTHESES.md /
  AUDIT.md / ROADMAP.md / x_rules.md were NOT read in this review.
  The strategic plan + tactical plan + eval-strategy + success-framework
  + risks-and-open-questions docs WERE read. If HYPOTHESES.md or
  ROADMAP.md contain text that conflicts with round-2 recommendations,
  this review didn't catch it.

**Round-2 agents that DID complete (4 of 8):**
- Adversarial review of round-1 Top-10 — STRONG; corrected 5 of 10.
- cli.py + migrations quantitative depth — corrected the lines/release
  growth claim, the 10k trip-wire timing, the migration round-trip
  test recommendation.
- Competitor substrate code depth — read primary GitHub READMEs +
  source files for 5 OSS neighbours; revised threat estimate from
  round-1's "could bolt on a policy engine in a quarter" to "the
  bolt-on is 5-6k LOC + cycle discipline none of them is practicing."
- Runtime code depth — surfaced 3 new code-level concerns (D13
  asymmetric application, hardcoded 6-domain enumeration, narrower
  moat than "publishable rule DSL").

**No primary user research with non-maintainer users** was conducted
(round 1 or round 2). Concerns about "second-user" gate, distribution
channel, and onboarding flow are informed judgement, not primary
observation.

**No code modifications.** Findings are recommendations; the cycle
pattern (D11 / D14 / Codex audit) governs which become scoped work.

**Some recommendations cross settled decisions** — D4 lift, W-29 split
scheduling, §6.3 framing edit. Those should run through the
cycle-proposal process per AGENTS.md "Settled Decisions" ("If you
think one needs revisiting, write a cycle proposal in
`reporting/plans/`").

**Round-2 surfaced 3 new code-level concerns** (§4.1-§4.3) that round
1 didn't see. There may be more — round 2 did not exhaustively read
every runtime module. A v0.1.14 or v0.1.15 fresh-eyes pass over
`core/state/projector.py` (8000+ lines), `core/explain/queries.py`,
and `core/review/summary.py` would likely surface additional
concerns.

---

## 15. Sources

### Round-2 primary sources (read in this round)

**Local repo files inspected at depth:**
- `src/health_agent_infra/cli.py` (8723 lines, 54 `cmd_*` handlers,
  `build_parser` 2175 LoC at 6427-8602)
- `src/health_agent_infra/core/synthesis.py` (1054 lines, atomicity
  contract at 914-1008, skill-overlay invariant at 259-386)
- `src/health_agent_infra/core/synthesis_policy.py` (1362 lines, 11
  X-rules, Phase B write-surface guard at 1217-1264, domain action
  registry at 65-86)
- `src/health_agent_infra/core/config.py` (load_thresholds at
  766-798, _is_strict_bool at 642, coerce_* helpers)
- `src/health_agent_infra/core/validate.py`
  (ALLOWED_ACTIONS_BY_DOMAIN at 35, SCHEMA_VERSION_BY_DOMAIN at 94)
- `src/health_agent_infra/domains/recovery/{classify,policy}.py`
  (policy.py:114 reads `t["policy"]["recovery"][...]` directly —
  D13 asymmetry)
- `src/health_agent_infra/domains/running/{classify,policy}.py`
  (policy.py:113 same pattern)
- `src/health_agent_infra/domains/sleep/{classify,policy}.py`
  (policy.py:123-124 same pattern)
- `src/health_agent_infra/domains/strength/{classify,policy}.py`
  (policy.py:127-134 USES coerce_int + coerce_float — correct shape)
- `src/health_agent_infra/domains/stress/{classify,policy}.py`
  (policy.py:127-128 reads directly)
- `src/health_agent_infra/domains/nutrition/{classify,policy}.py`
  (correct shape)
- `src/health_agent_infra/skills/recovery-readiness/SKILL.md`
- `src/health_agent_infra/skills/strength-readiness/SKILL.md`
- All 22 SQL migrations under `src/health_agent_infra/core/state/migrations/`
- `verification/tests/test_migrations_roundtrip.py`

**Git history inspection:**
- `git show v0.1.X:src/health_agent_infra/cli.py | wc -l` for tags
  v0.1.0, 0.1.2, 0.1.4, 0.1.5, 0.1.7, 0.1.8, 0.1.9, 0.1.10, 0.1.11

**Open-source competitor primary sources** (GitHub READMEs +
selected source files inspected 2026-04-29):
- [the-momentum/open-wearables](https://github.com/the-momentum/open-wearables)
  README + repo tree + `mcp/README.md` + `mcp/app/prompts.py` +
  `mcp/app/tools/sleep.py`
- [Open Wearables Feb 2026 blog](https://www.themomentum.ai/blog/talk-to-your-wearable-data-how-open-wearables-mcp-server-connects-health-metrics-to-ai-assistants)
- [bes-dev/garmy](https://github.com/bes-dev/garmy) README +
  `src/garmy/mcp/server.py` `QueryValidator`
- [Async-IO/pierre_mcp_server](https://github.com/Async-IO/pierre_mcp_server)
  — repo returned HTTP 404 from authed `gh api` and unauthed curl
  on 2026-04-29; secondary aggregator copy at
  [skywork.ai](https://skywork.ai/skypage/en/pierre-mcp-server-ai-engineers/1981519157185929216)
- [JedPattersonn/whoop-mcp](https://github.com/JedPattersonn/whoop-mcp)
- [Nicolasvegam/garmin-connect-mcp](https://github.com/Nicolasvegam/garmin-connect-mcp)

### Round-1 sources (carried forward)

#### Product / market

- [WHOOP — What's New 2026](https://www.whoop.com/us/en/thelocker/2026-whats-new/)
- [WHOOP AI Coach Review](https://exploreaitools.com/whoop-ai-coach-review/)
- [Oura Advisor introduction](https://ouraring.com/blog/oura-advisor/)
- [Oura proprietary women's-health LLM, Feb 2026](https://ouraring.com/blog/womens-health-ai-model/)
- [Oura Advisor support page (limitations)](https://support.ouraring.com/hc/en-us/articles/39512345699219-Oura-Advisor)
- [Apple scales back Mulberry — Bloomberg Feb 5 2026](https://www.bloomberg.com/news/articles/2026-02-05/apple-is-scaling-back-plans-for-new-ai-based-health-coach-service)
- [Apple shelves AI health coach — 9to5Mac](https://9to5mac.com/2026/02/05/apple-reportedly-scales-back-plans-for-ai-powered-health-coach/)
- [Fitbit personal health coach public preview](https://blog.google/products-and-platforms/devices/fitbit/personal-health-coach-public-preview/)
- [Fitbit AI coach global rollout](https://techbriefly.com/2026/02/11/google-rolls-out-fitbit-ai-coach-to-iphone-users-and-global-markets/)
- [Garmin Connect+ launch](https://www.garmin.com/en-US/newsroom/press-release/wearables-health/elevate-your-health-and-fitness-goals-with-garmin-connect/)
- [Garmin Connect+ year-on review April 2026](https://the5krunner.com/2026/04/20/garmin-connect-plus-review/)
- [Garmin Active Intelligence panned (TechRadar)](https://www.techradar.com/health-fitness/smartwatches/garmins-new-subscription-ai-feature-is-hilariously-bad-so-far)
- [Strava Athlete Intelligence GA](https://press.strava.com/articles/stravas-athlete-intelligence-translates-workout-data-into-simple-and)
- [Top Claude Code Skills 2026](https://composio.dev/content/top-claude-skills)

#### Academic

- [SePA (arxiv 2509.04752)](https://www.arxiv.org/pdf/2509.04752)
- [PHIA (Nature Comms 2025)](https://www.nature.com/articles/s41467-025-67922-y)
- [Anatomy of a PHA (arxiv 2508.20148)](https://arxiv.org/abs/2508.20148)
- [openCHA / Conversational Health Agents (PMC12228965)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12228965/)
- [JITAI mental-health meta-analysis g=0.15 (PMC12481328)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12481328/)
- [Bloom (arxiv 2510.05449)](https://arxiv.org/html/2510.05449v1)
- [GPTCoach (CHI 2025)](https://dl.acm.org/doi/10.1145/3706598.3713819)
- [AgentSpec (arxiv 2503.18666)](https://arxiv.org/abs/2503.18666)
- [Pro2Guard (arxiv 2508.00500)](https://arxiv.org/pdf/2508.00500)
- [Microsoft Agent Governance Toolkit April 2026](https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/)
- [Single-Agent-with-Skills (arxiv 2601.04748)](https://arxiv.org/pdf/2601.04748)
- [Single-agent vs multi-agent (arxiv 2604.02460)](https://arxiv.org/html/2604.02460v1)
- [Prometheus 2 (arxiv 2405.01535)](https://arxiv.org/abs/2405.01535)
- [M-Prometheus (arxiv 2504.04953)](https://arxiv.org/abs/2504.04953)
- [LLMs Cannot Reliably Judge (arxiv 2506.09443)](https://arxiv.org/html/2506.09443)
- [Beyond Benchmarks medical red-team (arxiv 2508.00923)](https://arxiv.org/html/2508.00923)
- [Declining medical safety messaging (npj DM 2025 01943)](https://www.nature.com/articles/s41746-025-01943-1)
- [JMIR exercise/health-coach LLM scoping review e79217](https://www.jmir.org/2025/1/e79217)
- [Senn N-of-1 sample size (SAGE 2019)](https://journals.sagepub.com/doi/10.1177/0962280217726801)
- [Aggregated N-of-1 (Frontiers Digital Health 2020)](https://www.frontiersin.org/journals/digital-health/articles/10.3389/fdgth.2020.00013/full)
- [Platform-of-1 Bayesian N-of-1](https://www.tandfonline.com/doi/full/10.1080/19466315.2025.2565157)

#### Governance

- [EU AI Act overview](https://artificialintelligenceact.eu/)
- [EU Digital Omnibus Nov 2025 (Jones Day)](https://www.jonesday.com/en/insights/2025/12/eu-digital-omnibus-how-eu-data-cyber-and-ai-rules-will-shift)
- [FAIR-AI healthcare framework (PMC12340025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12340025/)
- [AI Regulation compliance frontier (Holland & Knight April 2026)](https://www.hklaw.com/en/insights/publications/2026/04/ai-regulation-the-new-compliance-frontier)

### Repo-internal artifacts referenced

- `AGENTS.md` (settled decisions D1-D14)
- `reporting/plans/strategic_plan_v1.md` (5 hypotheses §3, settled
  decisions §4, scope expansion §8, decision branches §10, posture §6)
- `reporting/plans/tactical_plan_v0_1_x.md` (release sequence §1,
  per-cycle workstream catalogues §2-§6, scope cuts §9)
- `reporting/plans/eval_strategy/v1.md` (5 eval classes §2,
  calibration timing §9.4, judge approach §6)
- `reporting/plans/success_framework_v1.md` (Tier 1-3 metrics,
  anti-metrics §7)
- `reporting/plans/risks_and_open_questions.md` (R-O-04 doc rot,
  R-T-06 persona rot trip-wire firing, OQ-07 user-set archetypes)
- `reporting/plans/v0_1_11/PLAN.md`, `RELEASE_PROOF.md`, `BACKLOG.md`,
  `W_T_audit.md`
- `reporting/plans/post_v0_1_10/demo_run_findings.md`

---

*Round 1 authored 2026-04-29 by Claude across 5 parallel research
agents. Round 2 authored 2026-04-29 by Claude across 8 parallel
follow-up agents (4 completed, 4 failed mid-stream); refresh integrates
both rounds' outputs with explicit corrections of round-1 errors.
Refresh cadence: opportunistic — re-run when the strategic plan refresh
fires (post-v0.1.12 ship per strategic plan §11) or when a settled
decision is proposed for reopening.*
