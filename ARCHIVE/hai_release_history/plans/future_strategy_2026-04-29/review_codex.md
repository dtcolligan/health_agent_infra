# Future Strategy Review (Codex) - health-agent-infra

**Date:** 2026-04-29
**Author:** Codex
**Scope:** Independent deep research pass over the future plans in
`reporting/plans/`, with external product, research, governance, and
open-source context.
**Note:** `reporting/plans/future_strategy_review.md` already existed
untracked in this checkout and appears to be a Claude-authored review. I
left it untouched and wrote this independent Codex review alongside it.

---

## Verdict

**PLAN_STRONG_WITH_REVISIONS**

The strategic direction is substantially right. The project should keep
positioning itself as a **local-first governed personal-health-agent
runtime**, not as another "AI health coach." The external market is
already crowded with cloud-hosted coaching UX, but it is still thin on
deterministic policy, explicit proposal boundaries, audit trails, and
local outcome loops.

The needed revisions are not a strategic pivot. They are release-sequence
and planning-system corrections:

1. Refresh v0.1.12 immediately after v0.1.11 because several deferred
   items are not named cleanly in the tactical workstream table.
2. Narrow v0.1.13's "five minutes to first recommendation" gate so it
   reflects the runtime/skill boundary and W-Vb dependency.
3. Split v0.2.0 into smaller releases; weekly review, insight ledger,
   and factuality gate are too much for one cycle.
4. Treat the LLM judge as a fallible component that needs adversarial
   evaluation and shadow-mode evidence before it can block output.
5. Tighten H4/H5 evidence wording: tool-mediated deterministic runtime
   is well supported; broad single-agent-over-multi-agent claims are not.
6. Add a planning freshness/archive pass before public onboarding work.

---

## Method

I used an initial five-track research pass, then a second deeper pass
with five specialist read-only subagents plus additional direct source
review. The second pass focused on places where the first report was too
compressed: regulatory intended-use drift, FTC/HIPAA privacy boundaries,
2026 competitive movement, judge/eval validity, first-run adoption, and
release decomposition.

The research tracks were:

- Product / market landscape: vendor coaches, athlete platforms,
  health-data MCP servers, open-source wearable stacks.
- Academic / research landscape: personal-health agents, LLM health
  coaching evals, JITAI evidence, N-of-1 methodology, LLM-as-judge.
- User needs / UX: first-run trust, second-user viability, CLI-only
  acceptability, demo path.
- Technical roadmap risk: v0.1.12 through v0.2.0 sequencing, migrations,
  eval readiness, `cli.py` growth, docs drift.
- Planning-system review: which docs are load-bearing, which are
  provenance, where freshness drift has already appeared.
- Regulatory / safety / privacy: FDA general-wellness boundary, FTC
  consumer-health privacy/claim obligations, HIPAA scoping, EU AI Act
  horizon, and agentic threat-model implications.
- Architecture / implementation sequencing: carry-over dependencies,
  migration cadence, capabilities schema pressure, eval runner shape,
  and whether weekly review / insight ledger / factuality gate can land
  in one release.

Local read set included:

- `AGENTS.md`
- `HYPOTHESES.md`
- `README.md`
- `ROADMAP.md`
- `reporting/plans/README.md`
- `reporting/plans/strategic_plan_v1.md`
- `reporting/plans/tactical_plan_v0_1_x.md`
- `reporting/plans/eval_strategy/v1.md`
- `reporting/plans/success_framework_v1.md`
- `reporting/plans/risks_and_open_questions.md`
- `reporting/plans/v0_1_11/RELEASE_PROOF.md`
- `reporting/docs/demo_flow.md`
- selected CLI and eval implementation files where roadmap claims
  depended on current code shape.

External evidence came from official vendor docs/pages, peer-reviewed or
preprint research pages, and official governance/security sources. Links
are embedded where used and collected in "Sources" at the end.

No pytest suite was run. One read-only architecture thread ran targeted
`hai eval run --synthesis`, `hai eval run --domain recovery`, and
`hai eval run --domain strength` while inspecting the eval substrate; it
reported all three passing. No code was edited.

---

## Executive Summary

The current plans are directionally strong because they build around a
real gap in the market: governed, local, auditable personal-health agent
infrastructure. WHOOP, Fitbit, Oura, Garmin, and Strava are racing to
ship coach-like UX, but their systems are cloud/vendor hosted and mostly
opaque. Open-source health-data MCP projects are making data access
easier, but most stop at exposing rows or scores to an LLM. Health Agent
Infra's best differentiation is the governed decision path: typed
proposals, deterministic policy, explicit abstention, review outcomes,
supersession, and `hai explain`.

The research landscape supports the architecture more than it weakens it.
PH-LLM and PHIA show that personal health over wearable data is now a
real research category. PHIA especially strengthens the "LLM uses tools
and code rather than reasoning over raw numbers in prose" claim. JITAI
evidence also supports the project's emphasis on outcome interpretation:
the observed intervention effect is small, and measurement/decision-rule
quality matters. AgentSpec and Microsoft Agent Governance Toolkit support
the runtime-enforcement direction.

The biggest risk is sequencing. The tactical plan still reads like a
pre-v0.1.11 document in places. v0.1.12 must absorb named v0.1.11
deferrals. v0.1.13's first-user promise is too strong unless the project
defines whether the user reaches a real recommendation, a persona demo
recommendation, or an honest `awaiting_proposals` boundary. v0.2.0 should
not ship weekly review, insight ledger, and blocking factuality judge in
one cycle.

The second risk is documentation freshness. The project has excellent
planning discipline, but the default read path now includes stale
high-signal docs. That matters because this project explicitly uses docs
as agent operating instructions. Stale public docs are not cosmetic here;
they affect agent behavior and second-user trust.

---

## Findings

### F-FS-01. The Category Claim Is Strong, But Only If Narrowly Stated

**Severity:** important
**Reference:** `reporting/plans/strategic_plan_v1.md` section 2;
external vendor landscape.

**Argument:** The project should not compete under the label "AI health
coach." That category is already occupied by:

- WHOOP Coach, where WHOOP reports recommendation-seeking as a major use
  case and frames Coach as personalized coaching over proprietary member
  data: [OpenAI WHOOP case study](https://openai.com/index/whoop/).
- Fitbit Personal Health Coach, which already has onboarding
  conversation, weekly plans, Today-tab moments, Ask Coach, sleep, health,
  and fitness surfaces: [Fitbit public preview](https://blog.google/products-and-platforms/devices/fitbit/personal-health-coach-public-preview/).
- Oura Advisor, which provides personalized sleep/resilience/activity
  advice, memories, interaction style, and cloud-hosted data processing:
  [Oura Advisor](https://support.ouraring.com/hc/en-us/articles/39512345699219-Oura-Advisor).
- Garmin Connect+ Active Intelligence and Strava Athlete Intelligence,
  which cover AI insights and post-activity summaries.

The defensible category is the one the strategic plan already names:
**governed personal-health-agent runtime**. The runtime, audit chain,
typed proposal surface, and local-first posture are the moat, not the
coach phrasing.

**Recommended response:** Keep public positioning aggressively narrow:
"local-first governed runtime for personal-health agents." Avoid "AI
coach" as the top-line label except when explaining what host agents can
build on top.

---

### F-FS-02. v0.1.12 Scope Is Stale After v0.1.11

**Severity:** important
**Reference:** `reporting/plans/tactical_plan_v0_1_x.md:257`;
`reporting/plans/v0_1_11/RELEASE_PROOF.md:291`.

**Argument:** v0.1.11 explicitly deferred W-Vb, W-H2, W-N broader gate,
F-A-04/F-A-05, F-B-04, F-C-05, and W52/W53/W58. The v0.1.12 tactical
table names W-H2, W-U/F-B-04, W-V/F-C-05, and related polish, but it
does not name W-Vb or W-N. Yet its acceptance says "All v0.1.10/v0.1.11
deferred items closed."

That is a hidden planning contradiction. The next cycle can accidentally
claim it closed all carry-over while omitting demo polish and the broader
unclosed-resource warning cleanup.

**Recommended response:** Before implementation starts for v0.1.12,
refresh the tactical table or v0.1.12 PLAN so every v0.1.11 deferral has
one of:

- included W-id,
- explicitly deferred again with reason,
- declared obsolete with proof.

Do this before D14/D11 so the audit passes review the right scope.

---

### F-FS-03. The v0.1.13 "Five Minutes To First Recommendation" Gate Is Too Ambiguous

**Severity:** important
**Reference:** `reporting/plans/tactical_plan_v0_1_x.md:285`;
`src/health_agent_infra/cli.py:4735`;
`reporting/docs/demo_flow.md:14`.

**Argument:** The tactical plan says v0.1.13 should get a fresh
intervals.icu user from install to first recommendation in under five
minutes. That is a good product target, but it is not yet precise enough
for this architecture.

Current `hai daily` explicitly stops at `awaiting_proposals` when the
agent has not posted DomainProposal rows. That is correct by design.
The v0.1.11 blank demo also intentionally stops at the runtime/skill
boundary; `hai today` has no populated plan unless proposals are seeded.

So "first recommendation" can mean three different things:

1. First real recommendation from a host-agent-mediated flow.
2. First demo recommendation from a pre-populated persona fixture.
3. First honest boundary explanation: "I need proposals next."

Those are very different acceptance gates. A strict human-only CLI path
to real recommendations implies new proposal-authoring UX or a bundled
host-agent demo. A persona demo implies W-Vb. A boundary explanation is
trustworthy but not a recommendation.

**Recommended response:** Reword the v0.1.13 gate as:

- "Under five minutes from install to trusted first value."

Then define two separate acceptance paths:

- **Demo path:** `hai demo start --persona ...`, `hai today`, `hai
  explain` show a complete synthetic plan without real-state mutation.
- **Real path:** fresh intervals.icu setup reaches either a real plan via
  host-agent proposal posting, or a clear `awaiting_proposals` state with
  one actionable next step.

Do not invite a second user until the chosen path passes on a clean
machine with no maintainer context.

---

### F-FS-04. v0.2.0 Is Overloaded

**Severity:** important
**Reference:** `reporting/plans/tactical_plan_v0_1_x.md:364`.

**Argument:** v0.2.0 bundles:

- W52 weekly review aggregation,
- W53 insight proposal ledger and new tables,
- W58 LLM-judge factuality gate with blocking behavior.

That is too much schema, CLI, eval, and model-risk surface for one cycle.
Each component is independently valuable, but together they create a
release where a weekly review bug, migration bug, insight-ledger design
mistake, or judge false positive can block the whole milestone.

The plan itself says v0.1.14 exists to make W58 a "wire-up release," but
W58 is not just a wire-up. It introduces model selection, pinned model
identity, rubric validity, failure modes, claim extraction, negotiation
loop, logging, and user-facing blocking behavior.

**Recommended response:** Split v0.2.x:

- **v0.2.0:** deterministic weekly review only. No new insight ledger
  unless strictly necessary. No blocking judge.
- **v0.2.1:** insight proposal ledger and insight review path.
- **v0.2.2:** factuality judge in shadow mode first, then blocking only
  after adversarial and regression evidence is clean.

If the project wants v0.2.0 to remain a semantic milestone, make weekly
review the milestone.

---

### F-FS-05. W58 Needs A Judge-Evaluation Plan Before It Can Block Output

**Severity:** important
**Reference:** `reporting/plans/eval_strategy/v1.md`;
`reporting/plans/tactical_plan_v0_1_x.md:380`.

**Argument:** LLM-as-judge is useful, but it is not a deterministic
oracle. The plan currently frames W58 as a factuality gate that blocks
delivery when one unsupported quantitative claim is found. That might be
the right end-state, but not the first shipped shape.

Research supports both sides:

- Prometheus 2 supports custom evaluator criteria and improves open
  evaluator alignment: [Prometheus 2](https://aclanthology.org/2024.emnlp-main.248/).
- FActScore-style decomposition supports checking atomic claims against
  sources: [FActScore](https://arxiv.org/abs/2305.14251).
- Robustness and bias work shows LLM judges are prompt-sensitive and
  attackable, so a single judge score should not be treated as ground
  truth without regression and adversarial evidence.

The project's own eval strategy says daily skill prose is currently
unscored and adversarial eval is only partial. That is not enough support
for a blocking judge in a high-trust health context.

**Recommended response:** Change W58 acceptance to a staged gate:

1. Deterministic claim extraction for quantitative claims.
2. Source mapping to underlying state rows.
3. Judge shadow mode that logs score, rationale, model SHA, prompt
   version, and false-positive/false-negative review.
4. Dedicated adversarial weekly-review fixtures.
5. Blocking mode only after a release with acceptable shadow-mode
   performance.

For initial blocking, prefer deterministic unsupported-claim checks over
free-form judge disapproval.

---

### F-FS-06. W-AL Calibration Eval Is Premature As A Correlation Metric

**Severity:** important
**Reference:** `reporting/plans/tactical_plan_v0_1_x.md:344`;
`reporting/plans/eval_strategy/v1.md` section 3.4.

**Argument:** The tactical plan puts "Calibration eval - confidence vs.
ground truth correlation" in v0.1.14. But the eval strategy correctly
says outcome/calibration is not built and requires future weekly review
and outcome triples. With N=1 and no accumulated review substrate, a
correlation report risks becoming fake precision.

**Recommended response:** Keep v0.1.14 W-AL, but narrow it to:

- schema/interface for future calibration examples,
- report shape,
- missing-data behavior,
- synthetic fixture sanity checks,
- no real correlation claim until enough review-outcome triples exist.

Move real calibration reporting to v0.5+ after the N-of-1 substrate has
enough history.

---

### F-FS-07. H4 Is Strengthened, But Some Evidence Wording Should Be Corrected

**Severity:** important
**Reference:** `HYPOTHESES.md` H4; `reporting/plans/strategic_plan_v1.md`
H4.

**Argument:** H4's core claim is strong: LLM agents should drive
deterministic tools/CLIs instead of reasoning end-to-end over health
state. PHIA is strong support here. It shows an LLM agent using code
generation and retrieval over wearable data outperforms baselines on
objective numerical queries and open-ended reasoning, while the paper
also says behavior-change outcomes were not proven:
[PHIA Nature Communications](https://www.nature.com/articles/s41467-025-67922-y).

However, the local hypothesis text says PHIA shows "a single agent with
a code-execution tool matches a three-agent specialist team on equal
token budgets." I did not verify that claim in the PHIA page. The PHIA
paper as opened here compares against numerical reasoning and code
generation baselines, not the exact "three-agent equal token budget"
claim.

**Recommended response:** Refresh H4 evidence text before the next
public strategy refresh. The supported claim is enough:

- Tool/code-mediated agents are materially better for precise wearable
  data reasoning than raw text reasoning.
- The project's CLI/capability-manifest shape is consistent with that
  direction.

Avoid relying on an over-specific PHIA-vs-multi-agent statement unless
the exact paper section is cited.

---

### F-FS-08. H5 Should Be Narrowed Around Auditability, Not Anti-Multi-Agent Architecture

**Severity:** important
**Reference:** `HYPOTHESES.md` H5; Google Personal Health Agent.

**Argument:** H5 is directionally right if it says:

> A governed runtime with append-only ledgers and a code-vs-skill
> boundary is more auditable and reproducible per unit complexity than a
> prose-driven multi-agent coaching system.

It is weaker if it implies multi-agent health assistants are broadly the
wrong shape. Google's Personal Health Agent research explicitly proposes
specialist subagents for data science, health domain expertise, and
coaching, with substantial expert and end-user evaluation:
[Google Research PHA](https://research.google/pubs/the-anatomy-of-a-personal-health-agent/).

That does not invalidate Health Agent Infra. It clarifies the wedge:
the project is not trying to beat Google on consumer health assistant
breadth. It is trying to provide a governed, local, reproducible runtime
where policy and mutation are inspectable.

**Recommended response:** Revise H5 wording at the next strategic
refresh:

- Keep "small governed ledgers + strict code-vs-skill boundary."
- Drop broad anti-multi-agent implication.
- Say multi-agent orchestration may be fine above the runtime, but the
  mutation substrate should stay deterministic, audited, and local.

---

### F-FS-09. Open Wearables And MCP Projects Commoditize Data Access Faster Than The Plan Assumes

**Severity:** important
**Reference:** `reporting/plans/strategic_plan_v1.md` section 2;
external OSS landscape.

**Argument:** The strategic plan already names Health MCP servers as
neighbors. The pace now matters. Open Wearables is not just a raw MCP
server; it claims self-hosted wearable ingestion, open health scoring,
AI reasoning tools, coaching profiles, and MCP access:
[Open Wearables](https://openwearables.io/). Other projects expose
Garmin, Apple Health, Withings, and broader health data to Claude or
MCP-compatible clients.

This creates pressure on Health Agent Infra's lower layers:

- wearable ingestion,
- normalized health metrics,
- scores,
- basic "AI recommendation from scores" demos.

Those can become commodity. Health Agent Infra should not spend its
scarce roadmap budget trying to out-integrate every aggregator unless
the governance loop requires it.

**Recommended response:** Treat data-access breadth as partner/interoperability
surface, not the main moat. Prioritize:

- import/export contracts,
- provenance preservation when data enters from external MCP/API layers,
- policy/audit/outcome loop,
- `hai explain` over imported evidence,
- clear adapter strategy for Open Wearables-style sources once external
  integration is in scope.

---

### F-FS-10. Public/Default Docs Are Already Stale Enough To Affect Trust

**Severity:** important
**Reference:** `reporting/plans/README.md:95`; `README.md:43`;
`ROADMAP.md:3`; `HYPOTHESES.md` header.

**Argument:** The planning system is impressive, but the public/default
read path has drift:

- `reporting/plans/README.md` still labels v0.1.11 as "in flight."
- `README.md` says 52 commands, 21 migrations, and 2135 tests, while
  v0.1.11 shipped more commands/migrations/tests.
- `ROADMAP.md` still points readers to the superseded
  `multi_release_roadmap.md` and calls v0.1.8 current.
- `HYPOTHESES.md` says the superseded roadmap is "the working document,"
  contradicting AGENTS.md and the planning README.

This matters because agents are instructed to read these docs as
operating context. Drift here is not cosmetic.

**Recommended response:** Add a post-ship freshness gate before v0.1.12
or as W-AC/W-Z prep:

- update `reporting/plans/README.md`,
- update `README.md` and `ROADMAP.md`,
- update `AUDIT.md`,
- fix `HYPOTHESES.md` provenance text,
- update architecture/state docs for migration 022,
- add a checklist to AGENTS.md requiring this sweep after each
  substantive release.

---

### F-FS-11. The Planning Tree Needs Archival Compression Before It Scales Further

**Severity:** important
**Reference:** `reporting/plans/README.md:106`;
`reporting/plans/v0_1_11/` artifact count.

**Argument:** D14 and D11 are working. v0.1.11's multi-round plan audit
caught real contradictions before implementation. The risk is not the
audit pattern; it is artifact sprawl and provenance living in the
default path.

The planning README already marks many root docs historical. They should
not remain visually equivalent to live strategy docs. Per-cycle audit
round files also become hard to scan after ship.

**Recommended response:** Keep the planning system, but compress it:

- Add `reporting/plans/historical/` and move historical root planning
  docs there.
- After ship, consolidate plan-audit rounds into `plan_audit_log.md` and
  implementation-review rounds into `implementation_review_log.md`.
- Keep `PLAN.md`, `RELEASE_PROOF.md`, `BACKLOG.md`, and named
  investigative docs as the per-cycle canonical set.
- Make source-of-truth transitions explicit:
  - before implementation: `PLAN.md`,
  - after ship: `RELEASE_PROOF.md`,
  - after rollover: next cycle PLAN/BACKLOG.

---

### F-FS-12. `cli.py` Will Hit The D4 Trip-Wire During Risky Feature Work

**Severity:** important
**Reference:** `src/health_agent_infra/cli.py` line count: 8723;
`reporting/plans/risks_and_open_questions.md` R-T-03.

**Argument:** `cli.py` is 8723 lines and carries 55 annotated commands.
The settled D4 decision says do not split until the file exceeds 10k
lines or external integration arrives. That was sensible earlier. But
v0.1.13 and v0.2.0 add exactly the kind of code that makes late splitting
expensive: onboarding, doctor expansion, eval CLI, weekly review, insight
ledger, judge integration.

Waiting until the trip-wire fires may force the split in the same cycle
as user-facing onboarding or schema-heavy weekly review.

**Recommended response:** Do not violate D4. Instead, schedule a D4
re-evaluation workstream before v0.2.0:

- measure command groups,
- identify low-risk extraction boundaries,
- define manifest-preserving parser registration tests,
- decide whether to split before external integration.

If no split happens, at least add a parser/capabilities regression test
that makes a future split safer.

---

### F-FS-13. Persona Assertions Need To Become Declarative Before The Judge Work

**Severity:** important
**Reference:** `reporting/plans/eval_strategy/v1.md` section 4.1;
`reporting/plans/tactical_plan_v0_1_x.md:343`.

**Argument:** The persona harness is a major strength. But current
persona findings are still partly heuristic, while v0.1.14 expects
per-persona expected behavior across all 12 personas and 6 domains.
At the same time, W58 judge work depends on knowing what "correct" looks
like.

The tactical plan also has a count mismatch: eval strategy says current
scenario count is 28, while tactical acceptance says current "~50 ->
120+." That should be normalized before v0.1.14.

**Recommended response:** Before LLM judge integration:

- add a declarative expected-action table per persona,
- add a scenario manifest with authoritative counts,
- separate "expected deterministic action" from "acceptable prose
  rationale",
- make persona expected actions a review artifact in release proof.

---

## Hypothesis Review

| Hypothesis | Codex Assessment | Recommended Adjustment |
|---|---|---|
| H1: interpretability/outcomes beat marginally better recommendations | Strengthened. JITAI evidence shows small average effects and calls for clearer decision rules; N-of-1 thinking fits the future review loop. | Keep. Make outcome interpretation and weekly review the product wedge. |
| H2: local-first beats hosted daily runtime | Strengthened on privacy/control, unproven on adoption. Vendor coaches prove users accept cloud UX when it is polished. | Keep, but pair local-first with a very smooth demo/onboarding path. |
| H3: user-authored intent/targets + bounded supersession | Strengthened. Agent governance and approval-workflow research supports runtime boundaries. | Keep. Make approval fatigue a future falsification metric. |
| H4: LLM agents driving deterministic CLI/tools beat end-to-end reasoning | Strongly strengthened. PHIA, AgentSpec, and governance-toolkit patterns all support tools, code, and policy enforcement. | Keep, but refresh over-specific evidence wording. |
| H5: governed ledgers + code-vs-skill scales beyond multi-agent prose | Mixed. Auditability claim is strong; anti-multi-agent claim is weaker due Google PHA and broader multi-agent health research. | Narrow to auditability, reproducibility, and mutation-governance per unit complexity. |

---

## Product/User Research Synthesis

Users in this category appear to want five things:

1. **Action, not dashboards.** WHOOP reports recommendation-seeking as
   a large share of Coach usage. Fitbit and Oura have moved beyond raw
   metrics toward "what should I do?" surfaces.
2. **Contextual personalization.** Goals, readiness, sleep, injuries,
   schedule, equipment, travel, and preferences are front-and-center in
   Fitbit, WHOOP, and Oura UX.
3. **Trust and control.** Local-first/no telemetry is a real wedge for
   technical users, but it only helps if setup is trustworthy and docs
   are current.
4. **Cross-source data.** Open Wearables, Apple Health MCP, Garmin MCP,
   and Nori HealthMCP all show demand for using multiple health data
   sources with AI assistants.
5. **Less generic prose.** Market critique increasingly says AI fitness
   summaries repeat charts. Health Agent Infra should win by showing
   why a decision happened and whether it helped, not by producing
   warmer prose.

Recommended first external-user persona:

- Technical recreational athlete.
- Already uses intervals.icu or can provide a CSV export.
- Comfortable with Claude Code or another host agent.
- Cares about privacy and auditability.
- Will tolerate CLI if the daily path is natural-language first.

Do not optimize the next three releases for nontechnical consumers. The
gap from current CLI to consumer mobile UX is too large, and the
strategic plan already defers web/mobile until evidence proves it is
needed.

---

## Recommended Roadmap Revision

### v0.1.12 - Carry-over closure and trust repair

Keep the hardening theme, but make carry-over explicit.

Recommended scope:

- W-Vb demo persona fixture loading and cleanup polish, unless explicitly
  deferred again.
- W-H2 mypy stylistic baseline.
- W-N broader warning cleanup or documented re-deferral.
- W-U / F-B-04 and W-V / F-C-05.
- Capabilities drift/schema checks.
- Planning/public-doc freshness sweep.
- Minimal `cli.py` growth watch.

Suggested acceptance additions:

- Every v0.1.11 deferred item has final disposition.
- Public/default docs no longer point to superseded planning authority.
- Demo persona path exists or W-Vb is deliberately moved with a named
  reason.

### v0.1.13 - Onboarding and first value

Keep the release, but rewrite the success gate.

Recommended scope:

- intervals.icu-first `hai init`,
- `hai capabilities --human`,
- actionable USER_INPUT messages,
- `hai doctor --deep` onboarding readiness,
- public README quickstart smoke,
- day-1 vs day-30 `hai today` copy,
- clean-machine second-user rehearsal.

Acceptance should be:

- Under five minutes to trusted first value.
- Demo persona path produces `hai today` + `hai explain`.
- Real intervals.icu path reaches either a plan through host-agent
  proposal posting or an honest next-action boundary.

### v0.1.14 - Eval substrate, not judge confidence theatre

Recommended scope:

- scenario expansion,
- declarative persona expected actions,
- adversarial fixtures,
- judge harness scaffold,
- ground-truth review tool,
- calibration report shape only.

Acceptance should avoid real calibration claims until outcome history
exists.

### v0.2.0 - Deterministic weekly review

Recommended scope:

- W52 only, unless the insight ledger is strictly required.
- Byte-stable weekly output over fixture weeks.
- Source-row links for every quantitative claim.
- No blocking LLM judge yet.

### v0.2.1 - Insight ledger

Recommended scope:

- W53 schema, migration, CLI, explain integration, review workflow.
- Legacy-upgrade fixture tests.
- Provenance and supersession behavior.

### v0.2.2 - Factuality gate shadow mode, then blocking

Recommended scope:

- W58 claim extraction,
- model/prompt pinning,
- adversarial weekly-review fixture set,
- shadow-mode judge logging,
- false-positive review,
- blocking mode only after evidence.

### v0.3+

Revisit external integration and MCP once:

- docs are fresh,
- weekly review exists,
- import/provenance contract is clear,
- Open Wearables/MCP interop has been explicitly evaluated.

---

## Planning-System Recommendations

1. **Add a post-ship freshness checklist to AGENTS.md.**
   Include README, ROADMAP, AUDIT, planning README, tactical plan,
   HYPOTHESES, architecture/state docs, changelog, and unresolved backlog
   rollover.

2. **Move historical root planning docs to `reporting/plans/historical/`.**
   Keep provenance, but remove them from the default scan path.

3. **Consolidate audit transcripts after ship.**
   Use `plan_audit_log.md` and `implementation_review_log.md`, preserving
   individual details but making the cycle directory readable.

4. **Make cycle weight explicit.**
   Substantive releases get D14 + D11 + implementation audits.
   Hardening releases get targeted D14/D11 depending on scope.
   Doc-only releases get a freshness checklist.
   Hotfixes get targeted proof.

5. **Maintain a source-of-truth table.**
   For every major planning doc, list when it is authoritative and when it
   becomes provenance.

6. **Add a "citation freshness" task for hypothesis refreshes.**
   HYPOTHESES includes several specific research/product claims. Before
   public launch, verify every claim still maps to a live source and avoid
   post-dated or ambiguous citations.

---

## Deep Research Addendum - Second Pass

The first pass was directionally right but too compressed. This addendum
turns the research into an explicit source-to-roadmap argument.

### A. Strategic Position After External Research

The project's future should be stated as:

> Health Agent Infra is a local-first governed runtime for personal
> health agents. It does not try to be the highest-polish consumer coach
> or the broadest wearable aggregator. It owns the decision substrate:
> typed proposals, deterministic policy, provenance, abstention,
> supersession, review outcomes, and explainability.

That narrower claim matters because the market is moving quickly in
adjacent layers:

| Layer | 2026 external movement | Consequence for HAI |
|---|---|---|
| Wearable ingestion | Open Wearables, Nori HealthMCP, Terra, ROOK, Thryve, Apple Health MCP, Garmin MCP, `garmy` | Do not compete mainly on source count. Keep adapters pluggable and preserve provenance. |
| Health scores | Vendor readiness/recovery/strain/sleep scores; Open Wearables open scoring | Do not make "open score math" the main story. It is useful, not sufficient. |
| Coaching UX | Fitbit, WHOOP, Oura, Garmin, Strava, Nori | Expect users to demand daily and weekly action, memory, check-ins, and cross-source context. |
| Governance | Mostly vendor privacy controls, disclaimers, opt-in memories, and cloud processing | HAI's wedge remains stronger: deterministic audit chain and local mutation boundary. |
| Agent tooling | MCP servers and agent-governance toolkits are becoming normal | HAI should eventually expose controlled agent tools, but only after a threat-model gate. |

The best strategy is not to outrun vendors on consumer UX. It is to be
the trusted local substrate that can sit under a host agent, a future MCP
surface, or a second-user workflow while retaining auditability.

### B. Regulatory And Safety Deep Dive

This is not legal advice, but the planning docs should treat regulated
claim drift as a product risk, not just a wording issue.

The FDA general-wellness policy is the strongest public boundary for the
current posture. FDA's page says software intended for maintaining or
encouraging a healthy lifestyle and unrelated to diagnosis, cure,
mitigation, prevention, or treatment of a disease or condition is not a
device under section 520(o)(1)(B) of the FD&C Act:
[FDA General Wellness guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/general-wellness-policy-low-risk-devices).
That supports the project's non-goals, but only if public docs,
recommendations, weekly reviews, and insight names avoid clinical
intended-use language.

The current "no diagnosis" rule is necessary but incomplete. A future
weekly review could cross the boundary without saying "diagnosis" if it
uses language such as:

- "abnormal HRV,"
- "clinical-grade recovery marker,"
- "risk score,"
- "detects overtraining syndrome,"
- "prevents injury,"
- "monitor diabetes,"
- "manage anxiety,"
- "protein deficiency,"
- "biomarker."

The safer wording is:

- "above your recent baseline,"
- "below your own target,"
- "logged signal,"
- "insufficient signal,"
- "training-adjustment support,"
- "wellness support,"
- "consider reducing intensity,"
- "review with a qualified professional if concerned."

The FTC privacy source adds a separate issue. FTC guidance says the FTC
Act can apply to companies that collect, use, or share health information
even when they are not HIPAA-covered, and warns against misleading
claims about health data practices:
[FTC health information guidance](https://www.ftc.gov/business-guidance/resources/collecting-using-or-sharing-consumer-health-information-look-hipaa-ftc-act-health-breach).
For HAI, the immediate implication is not "become HIPAA software." It is
"be precise." "The runtime has no telemetry path" is defensible.
"Your health data never leaves your machine" is only true if the user is
not driving HAI through a hosted agent or connector that receives CLI
output.

The privacy doc already contains the right core distinction:
`reporting/docs/privacy.md:8` says the runtime never phones home but the
agent surfaces have their own policies. That distinction should move into
README/onboarding before v0.1.13 external users. It should also appear in
demo docs, because the project is explicitly dogfooding Claude Code over
health data.

Recommended regulatory/safety changes:

1. Add a deterministic regulated-claim lint in v0.1.12 or v0.1.13.
   It should cover public docs, packaged skills, recommendation prose,
   weekly-review prose once it exists, and insight labels.
2. Add a privacy-claims release-proof checklist: every public privacy
   claim should distinguish local runtime egress from host-agent egress.
3. Add an intended-use statement to onboarding: adult recreational
   wellness/training support; not diagnosis, treatment, prevention,
   disease management, symptom triage, emergency support, clinician
   workflow, or medical-device use.
4. Treat CGM, labs, medical records, rehab, mental health, minors, and
   clinical-condition support as hard-deferred pending a specific
   regulatory/privacy memo.
5. Before any MCP/connector surface, add an agentic threat model covering
   least privilege, prompt injection, memory poisoning, tool misuse,
   rate limits, audit logs, and raw SQLite exclusion.

### C. Privacy Product Gap

The current privacy architecture is good for a local developer tool, but
the product controls are not yet second-user-ready.

Existing strengths:

- runtime has no telemetry path,
- state is local SQLite plus JSONL logs,
- credentials live in the OS keychain,
- state mutations route through `hai`,
- demo isolation prevents real-state pollution,
- privacy bugs block release per `reporting/docs/privacy.md`.

Current gaps to plan:

- `reporting/docs/privacy.md:59` still says there is no `hai auth
  --remove` command in v0.1.8.
- `reporting/docs/privacy.md:116` says there is no first-class
  "forget one day" command.
- chmod failure warns and continues; that is pragmatic, but public docs
  should say what risk remains on network/shared filesystems.
- Windows relies on NTFS defaults and does not yet have equivalent
  operational guidance.
- hosted-agent/provider egress warnings are present but easy to miss.

Recommended product sequencing:

- v0.1.12/v0.1.13: update privacy docs to current version and add a
  first-run hosted-agent notice.
- v0.1.13: add or explicitly defer credential revoke UX.
- v0.1.13/v0.1.14: add export/backup/restore guidance for second users.
- v0.2.x: design forget/delete carefully because append-only auditability
  and user deletion rights are in tension.

Do not block v0.1.12 on perfect deletion semantics. Do block broader
external onboarding on stale privacy docs and missing hosted-agent
disclosure.

### D. Academic Evidence Deep Dive

The academic evidence supports the architecture, but only when the claims
are modest.

#### H1: Outcome interpretation is a better wedge than "better recs"

Strengthened.

JITAI and ecological momentary intervention evidence generally shows
small average effects. That makes recommendation novelty a weak
standalone differentiator. HAI's stronger claim is that an auditable
outcome loop can answer:

- what was recommended,
- why it was recommended,
- whether the user followed it,
- what happened next,
- what uncertainty remains.

This maps cleanly to the existing three-state audit chain and future
weekly review work.

#### H2: Local-first daily runtime is strategically coherent

Mostly unchanged.

The strongest research systems are cloud-scale or hosted. They do not
prove a local runtime will match consumer UX. But they do support the
idea that sensitive longitudinal health data needs explicit governance,
data minimization, and explainability. The local-first runtime remains
the right technical bet for the current target user.

#### H3: User-authored intent/targets with bounded mutation

Strengthened with a caveat.

Agent governance literature and runtime policy toolkits support explicit
approval and policy enforcement. N-of-1 platforms such as StudyMe/StudyU
support user-configured experiments. But the current evidence does not
prove that agent-proposed user-owned target mutations improve outcomes.
That should remain a hypothesis, not a claim.

#### H4: Deterministic tools beat raw LLM reasoning for health data

Strengthened, but wording needs correction.

PHIA strongly supports tool/code-mediated analysis over raw LLM
reasoning for wearable-data questions. Google PHA complicates a simple
"single-agent beats multi-agent" story: orchestration can work when
heavily evaluated and resourced. The safer H4 claim is:

> Health-data reasoning should be grounded in deterministic tools and
> source rows. Multi-agent orchestration may exist above the runtime, but
> mutable state and policy decisions should stay code-owned and audited.

#### H5: Ledgers and code/skill boundary scale trust

Strengthened for governance, weakened for broad anti-multi-agent claims.

The project should stop implying that multi-agent health assistants are
inherently the wrong architecture. The correct claim is that HAI offers
better reproducibility and mutation governance per unit complexity.

### E. Evaluation And Judge Architecture

The largest roadmap correction is W58. A factuality gate must start with
deterministic claim support, not an LLM judge.

Recommended W58 architecture:

1. **Claim extraction.**
   Split generated weekly-review prose into atomic claims. Mark claim
   type: quantitative, temporal, comparative, causal, recommendation,
   uncertainty, clinical/safety, preference/memory.

2. **Deterministic source mapping.**
   For quantitative, temporal, and comparative claims, require source-row
   locators. Examples:
   - "RHR was 12% above baseline" maps to accepted readiness rows plus
     baseline calculation inputs.
   - "You completed 4 of 5 planned sessions" maps to planned/review rows.
   - "Protein was below target three days" maps to nutrition intake rows
     and target rows.

3. **Hard deterministic blocks first.**
   Block when a quantitative/comparative claim lacks source rows or
   contradicts source rows. This is safer than asking an LLM to decide
   factuality from prose alone.

4. **LLM judge as residual prose support.**
   Use the judge for ambiguous unsupported reasoning, causal framing,
   overconfident tone, and missing uncertainty. Log model id, prompt
   version, rubric version, output, and reviewer disposition.

5. **Shadow mode first.**
   Run W58 in shadow mode for at least one release. Review false
   positives and false negatives before blocking judge-only findings.

6. **Adversarial fixtures.**
   Include injected user-note content, phantom metrics, stale-source
   claims, verbosity bias, fluent unsupported causal claims, prompt
   variants, and model-swap checks.

7. **Separate regulated-claim lint.**
   Even a factually supported claim can be unsafe or over-regulated. "HRV
   was below baseline" may be supported; "this indicates illness" is a
   separate intended-use problem.

This architecture draws from FActScore's atomic-fact framing, Prometheus
style rubric evaluation, and LLM-as-judge robustness concerns. It also
fits the repo's philosophy: code owns deterministic checks; skills and
judges handle prose/uncertainty only after code has bounded the state.

### F. Calibration And N-of-1 Evidence

The current success framework correctly says phase-3 calibration should
not be reported during phase 1. The tactical plan should therefore avoid
turning W-AL into a fake correlation metric in v0.1.14.

For v0.1.14, acceptable calibration work:

- define future schema,
- define report shape,
- define missing-data behavior,
- produce synthetic fixtures,
- verify confidence labels round-trip,
- define minimum-N gates.

Do not claim real calibration until the project has enough review-outcome
triples. Even then, simple correlation is a weak metric because:

- confidence is ordinal unless mapped to probabilities,
- self-reported improvement is not objective ground truth,
- followed/not-followed confounds outcome,
- domains have different base rates,
- adherence and surprise matter,
- N=1 histories are noisy.

Better future metrics:

- reliability bins by confidence label,
- Wilson or Bayesian intervals,
- Brier/ECE only if confidence becomes probabilistic,
- stratification by domain and action class,
- followed/not-followed separation,
- adverse/surprise labels,
- defer precision and defer user-satisfaction,
- minimum history length before any display.

N-of-1 should be treated as "personal evidence substrate," not proof of
general effectiveness. A real N-of-1 experiment requires an explicit
hypothesis, intervention/control schedule, primary outcome, carryover or
washout assumptions, missing-data rule, stop/safety rule, and provenance.

### G. Competitive Landscape Deep Dive

The market no longer splits neatly into "opaque vendor coaches" and
"raw MCP rows." There is now a middle layer:

- Open Wearables claims self-hosted unified wearable ingestion, open
  scoring, AI reasoning, coaching profiles, and MCP:
  [Open Wearables](https://openwearables.io/).
- Nori HealthMCP connects Apple Health, labs, Oura, Garmin, WHOOP, and
  more to AI assistants:
  [Nori HealthMCP](https://nori.ai/health-mcp).
- Fitbit is pushing a Gemini-backed coach with weekly plans, Today-tab
  insights, Ask Coach, schedule adjustment, plan memory, and broad health
  questions:
  [Fitbit public preview](https://blog.google/products-and-platforms/devices/fitbit/personal-health-coach-public-preview/).
- Oura Advisor exposes memory, personalization, cloud processing, and
  a disclaimer that unexpected responses can occur:
  [Oura Advisor](https://support.ouraring.com/hc/en-us/articles/39512345699219-Oura-Advisor).

This changes the roadmap in two ways.

First, ingestion breadth should not be the main bet. Apple Health and
Health Connect matter, but only after HAI knows how to preserve
provenance, missingness, conflict, and source freshness across imports.

Second, "evidence cards" should move earlier. A user comparing HAI to
Fitbit/WHOOP/Oura will not be impressed by a worse-looking daily plan.
They may be impressed by a plan that says:

- source rows used,
- last sync,
- stale/partial flags,
- rule fired,
- classified state,
- confidence/abstain reason,
- prior outcome link,
- user intent/target link,
- whether this is observation, association, hypothesis, or experiment.

Evidence cards are a product feature, but they are also the bridge
between governance and user-perceived trust.

### H. User Adoption Deep Dive

The next user should not be a general consumer. The plausible second user
is:

- technical,
- privacy-sensitive,
- already using intervals.icu or able to import/export data,
- comfortable with Claude Code/Codex/Claude Desktop-like tools,
- willing to inspect `hai explain`,
- motivated by endurance/strength/recovery decisions,
- patient with a local CLI if the boundaries are honest.

The v0.1.13 target should therefore be "trusted first value," not "first
recommendation" unless the host-agent proposal flow is explicitly part of
the path.

Recommended v0.1.13 first-run acceptance matrix:

| Path | Required result | Why it matters |
|---|---|---|
| Blank demo | Reaches `awaiting_proposals`; `hai today` honestly says no plan | Proves runtime boundary without fake proposals |
| Persona demo | `hai today` renders a synthetic plan and `hai explain` reconciles it | Shows the product value without real data |
| Real intervals.icu setup | Auth + doctor + first pull + snapshot + clear proposal boundary or agent-posted proposals | Shows second-user feasibility |
| Host-agent flow | Agent reads capabilities, posts valid proposals, synthesis commits, user can explain | Proves actual product loop |
| Failure path | Missing credentials, malformed config, no proposals, stale source all produce actionable USER_INPUT | Prevents first-run dead ends |

Do not measure v0.1.13 success by a raw CLI user reaching a real daily
plan unless the project also ships a proposal-authoring path. That would
contradict the code-vs-skill boundary.

### I. Technical Roadmap Deep Dive

The architecture is strong, but the next several releases have hidden
dependencies that should be made explicit.

#### v0.1.12 hidden dependencies

v0.1.12 should open with a carry-over register from v0.1.11:

- W-Vb demo persona fixture loading/archive,
- W-H2 mypy stylistic baseline,
- W-N broad ResourceWarning cleanup,
- W-U supersession semantic kind,
- W-V capabilities status enum,
- W-S/related `hai today` state-change UX,
- F-B-04/F-C-05 disposition,
- migration round-trip fixture template.

If any of these are deferred again, the PLAN should say so before D14.

#### Demo fixture packaging

W-Vb should not import from `verification/dogfood` at runtime. Dogfood
personas are not packaged runtime data. Put demo fixture data under a
packaged module/resource path, or create a runtime fixture loader with
tests proving wheel availability.

#### Supersession kind before weekly rollups

W-U should land before weekly review and `hai today` supersession UX.
The current state-fingerprint supersession is correct, but weekly review
will need to distinguish user supersede, auto state-change supersede,
legacy NULL-fingerprint supersede, and possibly future review-triggered
supersede.

#### Eval substrate before judge

v0.1.14 should be a deterministic eval substrate release:

- scenario manifest,
- authoritative scenario counts,
- eval batch/list CLI,
- persona expected-action table,
- expected deterministic action vs acceptable prose split,
- ground-truth review tool,
- judge harness scaffold,
- adversarial fixtures.

Only after that should W58 start.

#### CLI tripwire

`cli.py` is already 8723 lines with 55 commands. D4 says not to split
casually, and that remains right. But v0.1.13/v0.2.x will likely hit the
10k line tripwire during high-risk feature work. The safer plan is a D4
re-evaluation workstream before v0.2:

- keep `build_parser()` behavior stable,
- add parser/capabilities regression tests,
- extract command registration by group only if it can be done without
  behavior churn,
- do not combine CLI splitting with onboarding or weekly review logic.

#### Migration cadence

v0.2.0 should not add weekly review tables, insight ledger tables, judge
logs, and source locators in one migration burst. The store already has
strict gap detection and transactional migration application; preserve
that discipline by adding one conceptual schema group per release.

### J. Revised Release Sequence

This is the second-pass release sequence I would use as the planning
baseline.

#### v0.1.12 - Carry-over closure, doc freshness, trust hardening

Goal: close v0.1.11 carry-over and repair public/default trust before a
second user sees the project.

Must include or explicitly defer:

- W-Vb demo persona fixture loading/archive,
- W-H2 mypy stylistic baseline,
- W-N broad ResourceWarning cleanup,
- W-U supersession kind,
- W-V status enum in capabilities,
- `hai today` state-change UX,
- public doc freshness sweep,
- privacy/intended-use wording sweep,
- regulated-claim lint design or first implementation,
- migration round-trip test template.

Acceptance:

- every v0.1.11 deferral has disposition,
- README/ROADMAP/planning README/AUDIT no longer contradict current
  release state,
- privacy docs distinguish runtime no-telemetry from hosted-agent
  provider handling,
- no public doc points to superseded roadmap as active authority.

#### v0.1.13 - Second-user onboarding and trusted first value

Goal: make one clean-machine second-user path work.

Scope:

- intervals.icu-first onboarding,
- fresh-home smoke script,
- `hai capabilities --human` or equivalent human-readable orientation,
- actionable USER_INPUT for common first-run failures,
- demo persona path if W-Vb landed,
- explicit host-agent proposal path,
- first-run privacy/intended-use notice,
- second-user quickstart aligned with real command behavior.

Acceptance:

- clean machine reaches trusted first value in under five minutes,
- "trusted first value" is one of: persona plan + explain, real plan via
  host-agent proposals, or honest boundary plus exact next step,
- no quickstart relies on maintainer-only hidden state,
- no public doc promises populated `hai today` from blank state.

#### v0.1.14 - Deterministic eval substrate

Goal: make evaluation ready for weekly review and judge work.

Scope:

- scenario manifest and count normalization,
- batch/list eval CLI,
- declarative persona expected actions,
- persona release-proof table,
- health-coach prose rubric as offline label target,
- adversarial missingness/source/conflict scenarios,
- calibration schema/report shape only,
- no real calibration claim.

Acceptance:

- scenario counts are generated or single-sourced,
- persona expected actions are reviewed artifacts,
- deterministic action correctness is separated from prose quality,
- calibration output clearly says insufficient real data when applicable.

#### v0.2.0 - Deterministic weekly review

Goal: ship weekly review without insight ledger or blocking judge.

Scope:

- W52 weekly aggregation,
- stable week fixture tests,
- source-row locators for quantitative claims,
- source freshness/missingness display,
- evidence-card primitives,
- no insight ledger unless unavoidable,
- no blocking LLM judge.

Acceptance:

- weekly review is byte-stable over fixtures,
- every quantitative claim maps to source rows,
- stale/partial data is surfaced,
- `hai explain` can reconstruct weekly-review inputs.

#### v0.2.1 - Insight ledger

Goal: add durable insight memory after weekly review is stable.

Scope:

- W53 schema/migrations,
- `insight_proposal` and `insight`,
- explicit claim type: observation, association, hypothesis,
  experiment_result,
- promotion/rejection workflow,
- explain integration,
- supersession/provenance behavior,
- memory-poisoning tests.

Acceptance:

- insights cannot silently mutate future state without explicit policy,
- causal claims require experiment substrate or are rejected/downgraded,
- rejected insights remain auditable,
- imported/user-note prompt injection cannot create durable insight
  without validation.

#### v0.2.2 - Factuality gate shadow mode

Goal: collect evidence before blocking.

Scope:

- W58 claim extraction,
- deterministic quantitative claim support,
- LLM judge shadow logs,
- model/prompt/rubric pinning,
- adversarial judge fixtures,
- false-positive/false-negative review workflow.

Acceptance:

- deterministic unsupported quantitative claims can block,
- judge-only findings are logged but not yet blocking,
- release proof includes shadow-mode error analysis.

#### v0.2.3 - Blocking factuality gate

Goal: block unsupported weekly-review claims only after shadow evidence.

Scope:

- blocking for deterministic unsupported claims,
- optional blocking for judge-only claims only if shadow evidence supports
  it,
- override/review path,
- regression suite.

Acceptance:

- no unsupported quantitative weekly-review claim can ship,
- judge false positives are below an agreed threshold,
- user-facing block messages are actionable.

#### v0.3+ - External integration/MCP

Goal: expose HAI to broader agent/data ecosystems after the core loop is
trustworthy.

Prerequisites:

- weekly review stable,
- insight ledger governed,
- agentic threat model complete,
- no raw SQLite tool surface,
- source provenance import contract,
- Open Wearables/Nori/Apple Health feasibility assessed,
- privacy and intended-use docs current.

### K. Planning Docs That Should Change Next

Concrete edits I would make before or during the v0.1.12 planning
refresh:

1. `reporting/plans/tactical_plan_v0_1_x.md`
   - Mark v0.1.11 shipped.
   - Add W-Vb and W-N broad cleanup to v0.1.12 disposition.
   - Replace v0.2.0 monolith with v0.2.0/v0.2.1/v0.2.2/v0.2.3.
   - Change v0.1.13 target from "first recommendation" to "trusted first
     value" unless the proposal-authoring path is explicit.

2. `reporting/plans/eval_strategy/v1.md`
   - Normalize scenario counts.
   - Add persona expected-action manifest.
   - Move real calibration to post-v0.5 or minimum-N gate.
   - Add judge adversarial fixtures and deterministic claim-source checks.

3. `reporting/plans/success_framework_v1.md`
   - Fix daily-use metric naming: if the source is runtime events, state
     exactly which command/event is counted.
   - Keep "phase-3 metrics reported in phase 1 are vanity" as a hard
     guard.
   - Add defer-rate anti-gaming note: lower defer rate is not better if
     it comes from false confidence.

4. `reporting/plans/risks_and_open_questions.md`
   - Add claim/intended-use drift as nearer-term risk than server-side
     audit mandates.
   - Add durable insight-memory poisoning.
   - Add judge false-positive/false-negative risk.
   - Add `cli.py` tripwire timing risk.
   - Add data-source conflict/missingness risk.

5. `HYPOTHESES.md`
   - Stop calling the superseded roadmap the working document.
   - Correct PHIA/PHA wording and dates.
   - Soften "validated by dogfood" to "N=1 support signal."
   - Reframe H5 away from broad anti-multi-agent claims.

6. `README.md`, `ROADMAP.md`, `AUDIT.md`, `reporting/plans/README.md`
   - Update version, command count, migration count, test count, and
     current roadmap pointers.
   - Prefer generated snippets for counts, or remove volatile counts
     from public copy.

7. `reporting/docs/privacy.md`
   - Update stale v0.1.8 wording.
   - Add credential revoke/delete/export/backup current state.
   - Add hosted-agent/provider egress notice in the first screen.

8. `reporting/docs/architecture.md`
   - Update migrations 001-021 to include migration 022 and any newer
     schema state.
   - State where weekly review/insight/judge tables will live if adopted.

### L. Source-To-Roadmap Traceability

This table captures the strongest evidence links.

| Evidence | Source | Roadmap consequence |
|---|---|---|
| General wellness software boundary excludes diagnosis/treatment/prevention/disease management | FDA general-wellness guidance | Add intended-use wording and regulated-claim lint before public onboarding. |
| FTC Act can apply to non-HIPAA health data practices and privacy promises | FTC health information guidance | Make local-first privacy copy precise; add hosted-agent egress disclosure. |
| Open Wearables offers self-hosted ingestion, open scores, AI reasoning, MCP | Open Wearables | Treat data access as commodity/interop, not moat. |
| Nori HealthMCP connects multiple health sources to AI assistants | Nori HealthMCP | Expect MCP-style cross-source access; preserve HAI's governance wedge. |
| Fitbit coach ships weekly plans, Today insights, Ask Coach, memory/adjustment | Google Fitbit public preview | Users will expect daily/weekly action; HAI must lead with evidence/trust rather than UX polish. |
| Oura Advisor uses cloud processing, memory, deletion controls, and warns of unexpected responses | Oura Advisor help | HAI can differentiate on local audit, but needs equally clear memory/delete controls. |
| PHIA/PHA support tool-mediated health analysis but not broad outcome proof | Nature/Google PHA sources | Keep deterministic runtime claim; avoid overclaiming effectiveness. |
| LLM judges are useful but biased/prompt-sensitive | FActScore/Prometheus/RobustJudge/judge-bias papers | Stage W58: deterministic support first, shadow judge second, blocking later. |
| Success framework says phase-3 metrics in phase 1 are vanity | Local `success_framework_v1.md` | Move real calibration out of v0.1.14; keep only schema/report shape. |
| `hai daily` stops at `awaiting_proposals` without proposals | Local `cli.py` and demo docs | Reword v0.1.13 to "trusted first value"; do not promise blank-state plan. |

### M. Final Strategic Call

The future plans are strongest when they resist three temptations:

1. **Do not chase ingestion breadth.**
   Integrate, import, and preserve provenance, but do not define success
   as more sources than Open Wearables/Terra/ROOK/Thryve.

2. **Do not ship a broad coach.**
   Consumer coaches already have better UX. HAI's job is to make a host
   agent trustworthy, explainable, and bounded.

3. **Do not rush judge/weekly/insight into one milestone.**
   Weekly review is the right next product leap, but the insight ledger
   and factuality gate change the system's memory and safety profile.
   Split them.

If the next plan refresh makes those three corrections, the project has
a coherent path from maintainer dogfood to second-user local runtime to
weekly outcome interpretation and eventually N-of-1 personal evidence.

---

## Deep Research Addendum - Third Pass

The third pass turns the strategy into concrete planning artifacts. It
adds five things that were not detailed enough in the second pass:

1. an evidence-card design,
2. a v0.1.12 PLAN skeleton,
3. a regulated-claim lint taxonomy,
4. a v0.1.13 second-user onboarding acceptance suite,
5. a reconciliation of the Claude and Codex strategy reviews.

### A. Evidence Cards As The Product Trust Primitive

Evidence cards should become the bridge between today's `hai explain`
and the future weekly-review source-grounding requirement.

The rule:

> Evidence cards are code-owned deterministic audit artifacts. Skills
> may narrate them, but skills must not author, mutate, or repair them.

The current substrate is already close. Synthesis already writes
`daily_plan`, `recommendation_log`, `x_rule_firing`, and
`planned_recommendation` atomically. `hai explain` already reconstructs
the audit chain read-only. Snapshot already carries missingness, data
quality, source freshness, review summary, intent, and targets.

Recommended daily card shape:

```json
{
  "schema_version": "recommendation_evidence_card.v1",
  "card_id": "ecard_<daily_plan_id>_<domain>",
  "scope": "daily_recommendation",
  "user_id": "u_local_1",
  "for_date": "YYYY-MM-DD",
  "domain": "running",
  "daily_plan_id": "plan_...",
  "recommendation_id": "rec_...",
  "planned_id": "planned_...",
  "proposal_id": "proposal_...",
  "decision": {
    "planned_action": "proceed_with_planned_run",
    "final_action": "downgrade_to_easy_aerobic",
    "confidence": "moderate",
    "action_changed": true,
    "changed_by_firing_ids": [12],
    "abstain_or_defer_reason": null
  },
  "evidence": {
    "classified_state": {"coverage_band": "partial"},
    "policy_decisions": [],
    "x_rule_firings": [],
    "active_intent_ids": [],
    "active_target_ids": []
  },
  "source_quality": {
    "coverage_band": "partial",
    "missingness": {
      "token": "partial:sleep_hours",
      "kind": "partial",
      "fields": ["sleep_hours"]
    },
    "freshness": [
      {
        "source": "intervals_icu",
        "last_successful_sync_at": "2026-04-29T06:00:00Z",
        "staleness_hours": 3.5,
        "status": "fresh"
      }
    ],
    "cold_start_window_state": "in_window",
    "source_unavailable": false,
    "user_input_pending": false,
    "suspicious_discontinuity": false
  },
  "provenance": {
    "accepted_state_rows": [],
    "raw_source_refs": [],
    "proposal_log": [],
    "planned_recommendation": [],
    "recommendation_log": [],
    "x_rule_firing": [],
    "data_quality_daily": []
  },
  "conflicts": [],
  "review": {
    "review_event_id": "review_...",
    "latest_outcome_id": null,
    "status": "pending"
  }
}
```

Persistence should be a new table, not a blob inside
`recommendation_log.payload_json`:

```sql
CREATE TABLE recommendation_evidence_card (
    card_id TEXT PRIMARY KEY,
    daily_plan_id TEXT NOT NULL REFERENCES daily_plan(daily_plan_id),
    recommendation_id TEXT NOT NULL REFERENCES recommendation_log(recommendation_id),
    planned_id TEXT REFERENCES planned_recommendation(planned_id),
    proposal_id TEXT REFERENCES proposal_log(proposal_id),
    user_id TEXT NOT NULL,
    for_date TEXT NOT NULL,
    domain TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    source TEXT NOT NULL,
    ingest_actor TEXT NOT NULL,
    agent_version TEXT
);
```

Write cards inside the same synthesis transaction after
`recommendation_log` and `planned_recommendation` rows exist. If any
card insert fails, the plan commit rolls back. This keeps cards at the
same trust level as the rest of the audit chain.

The card should link the existing chain:

```text
proposal_log
  -> planned_recommendation
  -> daily_plan + x_rule_firing + recommendation_log
  -> review_event
  -> review_outcome
```

For source provenance, parse accepted-state `derived_from` fields into
structured locators rather than exposing only raw JSON strings. Start
with conservative locators:

- accepted-state table + primary key/date/user/domain,
- raw source row id where available,
- JSONL file + offset where applicable,
- `proposal_log.proposal_id`,
- `planned_recommendation.planned_id`,
- `recommendation_log.recommendation_id`,
- `x_rule_firing.firing_id`,
- `review_outcome.outcome_id`.

Conflict vocabulary should start narrow:

- `source_quality_conflict`: stale, partial, absent, unavailable,
  pending user input,
- `x_rule_conflict`: user later marked `disagreed_firing_ids`,
- `source_signal_conflict`: only when a deterministic detector exists.

Do not invent conflict prose from vibes.

Surfaces:

- `hai explain --json`: top-level `evidence_cards`.
- `hai explain --operator`: evidence card under each final
  recommendation.
- `hai today`: default stays uncluttered; add `--evidence
  compact|full|none` only when product need is clear.
- `hai today --format json`: include compact `evidence_card_summary`.
- Future `hai review weekly`: use weekly claim cards, not daily
  recommendation cards, for quantitative/comparative weekly claims.

Test gates:

- migration table/index/legacy-plan degradation tests,
- synthesis writes exactly one card per committed recommendation,
- rollback proves no card survives a failed synthesis,
- explain JSON/text render cards and remain read-only,
- `hai today --evidence compact` snapshot tests,
- data-quality matrix: present, partial, unavailable, pending, stale,
  negative/backfill freshness,
- review outcome with `disagreed_firing_ids` appears on the card,
- weekly fixture gate: every quantitative weekly claim has at least one
  locator.

Roadmap placement: evidence cards should land before or with
deterministic weekly review. If capacity is tight, ship only source
locators and compact cards in v0.2.0, then expand operator rendering in
v0.2.1.

### B. Concrete v0.1.12 PLAN Skeleton

The stale tactical table should not be copied as-is. v0.1.11 already
used W-S through W-Z, so v0.1.12 should allocate fresh W-ids, likely
W-AA onward.

Theme:

> Carry-over closure, doc freshness, and trust hardening before
> second-user onboarding.

Suggested workstreams:

| W-id | Workstream | Depends on | Acceptance |
|---|---|---|---|
| W-AA | W-Vb demo persona fixtures + archive/cleanup | v0.1.11 W-Va/W-Z/W-X/W-W/W-F | `hai demo start --persona ...` loads packaged fixtures, reaches seeded proposals/full synthesis, `hai today` renders, same-day correction creates `_v2`, no network, real state byte-identical, archive outside real base dir |
| W-AB | W-H2 mypy stylistic + F-A-04/F-A-05 | none | `uvx mypy src/health_agent_infra` has zero errors, or remaining strict-only exceptions are documented in `mypy_strict_baseline.md` |
| W-AC | W-N broad ResourceWarning cleanup | none | `uv run pytest verification/tests -W error::ResourceWarning -W error::pytest.PytestUnraisableExceptionWarning -q` clean, or wider warnings explicitly named |
| W-AD | F-B-04 supersession semantic kind | v0.1.11 W-E/W-F | Migration distinguishes auto state-change, explicit correction, domain-coverage-change, and legacy/unknown in DB plus `hai explain` |
| W-AE | `hai today` state-change/review UX | W-AD | JSON/plain/markdown surfaces auto-updated plan state and optional no-scheduled-review note without mutation |
| W-AF | F-C-05 status enum surfaceability | W-AG | `hai capabilities --json` exposes per-domain status/classified enum surfaces, sourced from runtime constants |
| W-AG | Capabilities drift/additive-shape guard | W-AF | Deterministic JSON/markdown; additive blocks validated; no frozen manifest schema, preserving W30 |
| W-AH | Public/default docs freshness sweep | v0.1.11 ship facts | README, ROADMAP, AUDIT, planning README, HYPOTHESES, architecture docs no longer contradict v0.1.11; reconcile 2347 vs 2356 test-count drift |
| W-AI | Privacy/intended-use wording sweep | W-AH | Docs distinguish runtime no-telemetry from hosted-agent egress; intended use says adult recreational wellness/training, not clinical use |
| W-AJ | Regulated-claim lint v1 | W-AI | Deterministic lint scans public docs + packaged skills for diagnosis/treatment/prevention/medical-device claims with allowlisted disclaimers |
| W-AK | Migration round-trip template | before/with W-AD | Old DB fixture applies through head, reruns idempotently, verifies migration 022 plus v0.1.12 migrations |
| W-AL | D4 `cli.py` growth watch | none | Record line/command count, add/scope parser and capabilities regression guard; no split unless D4 re-evaluation approves |

Cycle gates:

- Run D14 first. v0.1.12 is substantive; do not reuse the v0.1.11
  D11-skip exception.
- Run D11 Phase 0 after D14, with a demo-flow rehearsal as a
  pre-implementation acceptance scenario.
- Ship gate: `uv run pytest verification/tests -q`, warning gate,
  mypy gate, ruff, bandit, capabilities deterministic/additive gate,
  wheel/sdist if package data or migrations changed, full persona matrix
  as release proof rather than CI.

Explicit deferrals:

- W52/W53/W58 split to v0.2.x.
- JSONL tail row-level filtering unless a v0.1.12 JSONL tail consumer
  is added.
- Old tactical W-T gym docs, W-X stats polish, W-Y CI persona subset,
  and exhaustive threshold/persona docs unless Phase 0 promotes them.
- `cli.py` split and manifest schema freeze unless D4/W30 are explicitly
  re-opened.
- CGM, labs, medical records, rehab, minors, mental health,
  clinical-condition support, web/mobile, and MCP/connector surfaces.

### C. Regulated-Claim Lint Taxonomy

The repo already enforces narrow R2 diagnosis-shaped tokens through
`core.validate` and `core.narration.voice`. That should evolve into a
surface-aware deterministic lint layer, not another skill instruction.

Suggested module shape:

```text
src/health_agent_infra/core/safety/regulated_claim_lint.py
verification/tests/fixtures/regulated_claim_lint/cases.yml
verification/tests/test_regulated_claim_lint.py
```

Taxonomy:

| ID | Block or flag | Allowed replacement |
|---|---|---|
| `RCL-DX` | diagnosis/disease claims: `diagnose`, `disease`, `disorder`, `condition`, `infection`, `illness`, `sick`, `overtraining syndrome`, disease names when asserting state | "above baseline", "logged signal", "insufficient signal", "if concerned, ask a clinician" |
| `RCL-TREAT` | treatment/prevention: `treat`, `cure`, `prevent injury`, `manage diabetes/anxiety`, `mitigate disease`, `therapy protocol` | "reduce intensity", "training-adjustment support", "wellness support" |
| `RCL-CLIN` | clinical-grade claims: `clinical-grade`, `biomarker`, `risk score`, `screening`, `triage`, `abnormal`, `pathological`, `clearance` | "training signal", "confidence/coverage", "recent baseline" |
| `RCL-MEDSUPP` | medication/supplement advice: start/stop/change dose, magnesium/iron/vitamin dosing | refusal plus clinician/RD referral |
| `RCL-NUTRIENT` | nutrient deficiency or micronutrient status claims | "protein below your own target"; "micronutrients unavailable at source" |
| `RCL-PLAN` | autonomous regimen: `prescribe`, `training plan`, `diet plan`, `meal plan`, `macro split`, `periodization`, `rehab protocol` | user-authored intent/targets; bounded enum nudges |
| `RCL-CAUSE` | unsupported causality: `HRV is low because`, `this will fix`, `will improve recovery`, `caused by stress` | "co-occurred", "associated in your log", "conservative adjustment" |
| `RCL-PRIVACY` | privacy overclaim: "health data never leaves your machine" without hosted-agent qualifier; HIPAA certified/secure/compliant claims | "runtime has no telemetry path"; "host agent/provider policy still applies" |
| `RCL-EMERGENCY` | triage/minimization: "not urgent", "safe to train" around chest pain, collapse, suicidal ideation, severe shortness of breath | stop workflow; emergency/clinician referral |
| `RCL-AGENTIC` | prompt/tool safety: durable insight from user note alone, obeying note instructions, web/cloud send, direct SQLite mutation | source-row provenance, CLI-only mutation, least privilege |
| `RCL-DEBUG` | user-facing rule leakage: `R1`, `X9`, raw policy slugs in prose | translate to user-facing rationale; allow in `hai explain --operator` |

Surface policy:

- `block`: recommendation payloads, `hai today`, reporting prose,
  weekly review, insight titles/labels.
- `warn`: README, docs, privacy/onboarding copy.
- `allow-with-annotation`: safety docs, non-goal examples, tests,
  regulatory quotes.

Allow annotations should require a reason, for example:

```text
lint:allow RCL-DX reason="forbidden example in safety docs"
```

False-positive requirements:

- whole-word and phrase-aware matching,
- `condition` must not match `conditional`,
- code identifiers such as `protein_sufficiency_band` must not trip
  deficiency lint,
- historical planning docs should be advisory-only unless promoted to
  active public docs.

Minimum fixture cases:

- banned: "This detects overtraining syndrome."
- banned: "Your HRV is an abnormal biomarker."
- banned: "Protein deficiency drove the downgrade."
- banned: "This prevents injury."
- banned: "Your data never leaves your machine."
- allowed: "RHR was above your recent baseline for three days."
- allowed: "Protein was below your own target."
- allowed: "Micronutrients are unavailable at source."
- allowed: "The runtime has no telemetry path; hosted agents may
  receive context you give them."

Roadmap placement:

- v0.1.12: first lint implementation for active docs and packaged skills.
- v0.1.13: make lint part of public onboarding/README acceptance.
- v0.2.0: weekly-review prose must pass lint plus source-row mapping.
- v0.2.1: validate `insight_proposal.title`, `insight.label`, and claim
  type before promotion.
- W58 remains factuality support, not a substitute for intended-use
  lint.

### D. v0.1.13 Second-User Onboarding Acceptance Suite

The gate should be:

> Under five minutes to trusted first value for a second developer-user.

It should not be:

> CLI-only first real recommendation from blank state.

Current behavior correctly stops at `awaiting_proposals` until proposals
exist. That is a feature, not a bug. v0.1.13 should prove four separate
paths.

Suggested planning/test files:

```text
reporting/plans/v0_1_13/SECOND_USER_ONBOARDING_ACCEPTANCE.md
reporting/plans/v0_1_13/second_user_rehearsal.md
verification/scripts/smoke_v013_blank_demo.py
verification/scripts/smoke_v013_persona_demo.py
verification/scripts/smoke_v013_real_intervals.py
verification/scripts/smoke_v013_host_agent_loop.py
verification/tests/test_v013_onboarding_user_input.py
verification/tests/test_v013_public_docs_promises.py
verification/tests/test_v013_second_user_smokes.py
verification/tests/fixtures/v013_onboarding/host_agent_proposals/
verification/dogfood/personas/p13_second_user_intervals_recreational.py
```

Acceptance paths:

| Path | Commands | Expected result |
|---|---|---|
| Blank demo | `hai demo start --blank`; `hai doctor --deep --json`; refused `hai auth intervals-icu`; refused `hai pull --source intervals_icu`; `hai daily --skip-pull --source csv --auto --explain`; `hai today`; `hai demo end` | Doctor uses fixture probe; auth/pull exit USER_INPUT; daily exits OK with `overall_status=awaiting_proposals`; synthesize skipped; today exits USER_INPUT with no plan |
| Persona demo | `hai demo start --persona p13_second_user_intervals_recreational`; `hai daily --skip-pull --source csv --auto --explain`; `hai today --format json`; `hai explain --as-of <fixture_date> --user-id u_local_1` | Complete synthetic plan with no network or real-state mutation; six proposals, six recommendations, six review events; today/explain OK |
| Real intervals.icu | opt-in only when `HAI_INTERVALS_ATHLETE_ID` and `HAI_INTERVALS_API_KEY` are present; isolated `hai init`; noninteractive `hai auth intervals-icu`; `hai doctor --deep --json`; `hai daily --source intervals_icu --auto --explain` | Doctor live probe OK; daily may stop at `awaiting_proposals` only if it emits one actionable next step; do not require `hai today` unless proposals are posted |
| Host-agent loop | run daily to `awaiting_proposals`; read `hai capabilities --json` and `hai state snapshot`; generate/post six valid proposals from fixtures; rerun daily; run today/explain | Final daily complete; `hai explain` reconciles proposal -> planned -> daily_plan -> recommendation chain |

USER_INPUT regression tests should pin:

- missing state DB on `daily` and `today`,
- `hai pull --source intervals_icu` without credentials,
- missing env var for `hai auth intervals-icu --api-key-env`,
- demo-active auth/network refusals,
- invalid `--domains`,
- malformed proposal JSON,
- domain/action mismatch proposal,
- same-day nutrition duplicate without `--replace`,
- noninteractive `intent commit` / `target commit` without confirm,
- fresh-day `--supersede` after proposals but before canonical plan.

Doc promises to avoid:

- CLI-only first real recommendation from blank demo,
- populated `hai today` after blank demo,
- "your data never leaves your machine" without hosted-agent caveat,
- `hai init --with-auth --with-first-pull` as intervals.icu unless it
  is changed,
- doctor is all green on fresh installs,
- demo uses live intervals.icu,
- meal-level/micronutrient nutrition,
- Garmin as default live source.

Second-user persona:

```text
p13_second_user_intervals_recreational
adult technical recreational athlete
already uses intervals.icu
comfortable with Claude Code or equivalent host agent
privacy/auditability motivated
not Dom-shaped
34F, 64 kg, 168 cm
3 runs + 2 strength sessions/week
performance plus recomposition goal
target 2200 kcal / 120 g protein
typical HRV 48 ms, RHR 58, sleep 7.2 h
today easy_z2, soreness moderate, energy moderate, stress 3
```

This persona should pass onboarding without clinical language and should
produce six-domain coverage once proposals are posted.

### E. External Integration Checkpoints

Apple Health, Health Connect, and MCP should be framed as future
checkpoints, not silent adapter tasks.

Apple's HealthKit privacy docs emphasize fine-grained user permission
per data type, clear use descriptions, no advertising use of HealthKit
data, no sale to data brokers, no disclosure to third parties without
express permission, and a coherent privacy policy:
[Apple HealthKit privacy](https://developer.apple.com/documentation/healthkit/protecting-user-privacy).

Health Connect docs emphasize platform availability, declared data use,
Play Console approval for data types, and user permission:
[Health Connect data types](https://developer.android.com/health-and-fitness/guides/health-connect/plan/data-types).

MCP authorization/security docs make clear that MCP is not just a tool
transport. For sensitive user data, authorization, token handling,
resource indicators, and security best practices matter:
[MCP authorization](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization),
[MCP security best practices](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices).

Roadmap implication:

- v0.3 should include a read-only UI decision checkpoint, not a UI
  commitment.
- v0.3 should include an MCP threat-model checkpoint before any MCP
  server/tool surface.
- v0.4 can treat multi-source ingest as the non-developer reach anchor,
  but only after permission, provenance, source freshness, and privacy
  copy are designed.
- W30 manifest-freeze should be reconsidered when W58 introduces
  source hashes, judge model identity, prompt/rubric versions, or other
  cryptographic-like commitments, not only when MCP arrives.

### F. Claude/Codex Reconciliation Deltas

The Claude and Codex strategy reports agree on the important direction:
the plan is strong, v0.2.0 is overloaded, v0.1.13's first-value gate
needs narrowing, W58 must be staged, W-AL real calibration is premature,
H5 should be reframed, and public docs are stale enough to affect trust.

Useful Claude deltas folded into this report:

- `cli.py`: add parser/capabilities regression tests now; run D4
  re-evaluation early; split before onboarding only if genuinely
  mechanical and approved.
- W-AL: no real metric before v0.5; v0.1.14 may only define no-op report
  shape and minimum-N gates.
- v0.1.13: call the first target user a second developer-user.
- v0.3: add read-only UI decision checkpoint.
- v0.4: treat multi-source ingest as a likely non-developer reach
  anchor, not a near-term v0.1.x task.
- W58/adversarial eval: include PHI-leak, demographic-cue, and medical
  jailbreak robustness probes alongside prompt injection, source
  conflict, and judge-bias fixtures.
- First-run trust: keep `hai doctor --deep` credential probing and
  adapter false-OK behavior in the onboarding trust surface.

Combined top actions:

1. Open v0.1.12 with a carry-over register and fresh W-ids.
2. Do the public/default doc freshness sweep before external onboarding.
3. Add privacy/intended-use discipline and regulated-claim lint.
4. Reword v0.1.13 to "trusted first value" for a second developer-user.
5. Ship W-Vb as packaged persona demo fixtures, not runtime imports from
   `verification/dogfood`.
6. Run D4 re-evaluation and add parser/capabilities regression tests.
7. Make v0.1.14 a deterministic eval-substrate release.
8. Split v0.2.x into weekly review, insight ledger, factuality shadow,
   and blocking gate.
9. Redesign W58 around source locators and deterministic unsupported
   claim blocks before LLM judgment.
10. Add v0.3/v0.4 checkpoints for read-only UI, MCP threat model, and
    multi-source ingest.

---

## Sources

Product and market:

- [OpenAI / WHOOP case study](https://openai.com/index/whoop/)
- [WHOOP Coach launch](https://www.whoop.com/hr/en/thelocker/whoop-unveils-the-new-whoop-coach-powered-by-openai/)
- [Fitbit Personal Health Coach public preview](https://blog.google/products-and-platforms/devices/fitbit/personal-health-coach-public-preview/)
- [Fitbit Public Preview help](https://support.google.com/fitbit/answer/16678124)
- [Oura Advisor help](https://support.ouraring.com/hc/en-us/articles/39512345699219-Oura-Advisor)
- [Garmin Active Intelligence support](https://support.garmin.com/en-US/?faq=kWi5DoaMPZ4VCJBA0lFWP7)
- [Strava Athlete Intelligence support](https://support.strava.com/hc/en-us/articles/26786795557005-Athlete-Intelligence-on-Strava)
- [Open Wearables](https://openwearables.io/)
- [Nori HealthMCP](https://nori.health/health-mcp)
- [Garmin MCP server](https://github.com/Taxuspt/garmin_mcp)
- [Apple Health MCP server](https://github.com/neiltron/apple-health-mcp)
- [garmy](https://github.com/bes-dev/garmy)
- [Terra wearable API](https://tryterra.co/)
- [ROOK wearable API](https://www.tryrook.io/)
- [Thryve health data API](https://www.thryve.health/)

Research:

- [PH-LLM, Nature Medicine 2025](https://www.nature.com/articles/s41591-025-03888-0)
- [PHIA, Nature Communications 2026](https://www.nature.com/articles/s41467-025-67922-y)
- [Google Research: The Anatomy of a Personal Health Agent](https://research.google/pubs/the-anatomy-of-a-personal-health-agent/)
- [The Anatomy of a Personal Health Agent, arXiv](https://arxiv.org/abs/2508.20148)
- [SePA](https://arxiv.org/abs/2509.04752)
- [Bloom](https://arxiv.org/abs/2510.05449)
- [JITAI/EMI meta-analysis, BMJ Mental Health / PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12481328/)
- [StudyMe N-of-1 trials](https://link.springer.com/article/10.1186/s13063-022-06893-7)
- [LLM exercise and health coaching evaluation review, JMIR 2025](https://www.jmir.org/2025/1/e79217)
- [AgentSpec paper page](https://huggingface.co/papers/2503.18666)
- [Prometheus 2, ACL Anthology](https://aclanthology.org/2024.emnlp-main.248/)
- [FActScore](https://arxiv.org/abs/2305.14251)
- [LLM-as-judge bias](https://arxiv.org/abs/2306.05685)
- [RobustJudge paper page](https://papers.cool/arxiv/2506.09443)
- [LLM confidence calibration](https://www.nature.com/articles/s44355-026-00053-3)

Governance and regulation:

- [Microsoft Agent Governance Toolkit](https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/)
- [EU AI Act official overview](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)
- [EU AI Act Service Desk timeline](https://ai-act-service-desk.ec.europa.eu/en/ai-act/eu-ai-act-implementation-timeline)
- [FDA General Wellness guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/general-wellness-policy-low-risk-devices)
- [FDA device software/mobile medical apps](https://www.fda.gov/medical-devices/digital-health-center-excellence/device-software-functions-including-mobile-medical-applications)
- [FDA AI in Software as a Medical Device](https://www.fda.gov/medical-devices/software-medical-device-samd/artificial-intelligence-software-medical-device)
- [FDA AI-enabled medical devices list](https://www.fda.gov/medical-devices/software-medical-device-samd/artificial-intelligence-enabled-medical-devices)
- [FTC consumer health information guidance](https://www.ftc.gov/business-guidance/resources/collecting-using-or-sharing-consumer-health-information-look-hipaa-ftc-act-health-breach)
- [FTC Health Breach Notification Rule guide](https://www.ftc.gov/business-guidance/resources/complying-ftcs-health-breach-notification-rule-0)
- [FTC Health Products Compliance Guidance](https://www.ftc.gov/business-guidance/resources/health-products-compliance-guidance)
- [HHS HIPAA health apps/API guidance](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/access-right-health-apps-apis/index.html)
- [OWASP Agentic AI threats and mitigations](https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/)
- [OWASP Agentic Skills Top 10](https://owasp.org/www-project-agentic-skills-top-10/)
- [Apple HealthKit privacy](https://developer.apple.com/documentation/healthkit/protecting-user-privacy)
- [Health Connect data types and declaration](https://developer.android.com/health-and-fitness/guides/health-connect/plan/data-types)
- [Model Context Protocol authorization](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)
- [Model Context Protocol security best practices](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices)

---

## Bottom Line

The future plans should not be thrown out. They should be tightened.

The best next move is a planning-refresh cycle before v0.1.12:

- roll every v0.1.11 deferral into the tactical plan with disposition,
- repair stale public/default docs,
- add privacy/intended-use wording discipline,
- narrow v0.1.13 from "first recommendation" to "trusted first value,"
- split v0.2.0 into weekly review, insight ledger, judge shadow mode,
  and judge blocking releases,
- make deterministic claim-source verification precede LLM judgment,
- add evidence cards as the trust bridge between `hai explain` and
  weekly review,
- define v0.1.13's acceptance suite around blank demo, persona demo,
  real intervals.icu, host-agent loop, and USER_INPUT failures,
- refresh H4/H5 evidence wording.

After that, the strategic shape remains strong: local-first governed
runtime, deterministic policy, explicit proposal boundaries, honest
abstention, evidence cards, weekly outcome interpretation, durable
insights only after validation, and eventually N-of-1 personal evidence.
