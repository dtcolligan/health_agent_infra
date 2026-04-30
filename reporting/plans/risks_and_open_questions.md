# Risks + Open Questions — Health Agent Infra

> **Status.** Authored 2026-04-27 by Claude in extended planning
> session. Captures what could derail the strategic + tactical
> plans, plus questions that need maintainer judgement (not agent
> judgement).
>
> **Reading intent.** Two sections. § 2-7 = risks. § 8 = open
> questions. Read § 2-7 to understand what could go wrong; read § 8
> when about to make a decision.
>
> **Refresh cadence.** Reviewed every minor release. Resolved
> questions move to AGENTS.md "Settled Decisions"; closed risks
> note the resolution + date.

---

## Table of contents

1. How this doc works
2. Strategic risks
3. Technical risks
4. Operational risks
5. External risks
6. Compounding risks (interactions)
7. What we are NOT worried about (anti-risks)
8. Open questions for maintainer judgement
9. Risk register table (compact)

---

## 1. How this doc works

**A risk** is a thing that could happen, with non-negligible
probability, that derails the plan. Each risk has:
- **Trigger:** what would need to be true for the risk to
  materialise.
- **Impact:** what breaks if it does.
- **Likelihood:** rough estimate.
- **Mitigation:** what we're doing now or can do to reduce it.
- **Trip-wire:** the early signal we'd see if it's starting to
  happen.

**An open question** is a decision that needs the maintainer's
judgement (not an agent's). Each has:
- **Decision needed by:** milestone where deciding-no-longer-being-an-option.
- **Trade-off:** what we're choosing between.
- **Default:** what happens if no decision is made.

The doc is opinionated about likelihood (medium / high) but
honest about uncertainty. A risk listed at "low" might still be
catastrophic if it materialises — the magnitude column is
separate from probability.

---

## 2. Strategic risks

### R-S-01. The category claim turns out wrong

**Trigger:** A new entrant ships a "governed personal-health-agent
runtime" with substantially better features at lower cost (e.g.,
Anthropic, Apple, or an OSS project ships a deterministic
policy-engine + skill-judgement architecture).

**Impact:** The strategic positioning collapses. The project
becomes one-of-many in a known category, rather than the reference
implementation of an emerging one.

**Likelihood:** Low-medium. Apple Mulberry's failure (Feb 2026)
suggests big-budget entrants struggle in this space; OSS effort
to ship comparable has been thin (per 2026-04-25 comparable-OSS
survey).

**Mitigation:**
- Lead with the governance contract (strategic posture §6.1).
  The architecture moat is the load-bearing differentiator;
  add-on features are commodity.
- Publish prior art (strategic posture §6.3). Workshop / preprint
  at v0.6 review establishes priority.

**Trip-wire:** Quarterly comparable-OSS survey turns up a project
shipping the architecture pattern. v0.4 review checkpoint.

---

### R-S-02. H1 (interpretability > better recs) falsifies

**Trigger:** Per H1 falsification: Dom (after v0.5 substrate +
90 days) consistently consults underlying metrics in preference
to personal-evidence verdicts.

**Impact:** The strategic foundation shifts. Wave 4 + 5 (substrate
+ estimator + governed adaptation) become less load-bearing;
recommendation-engine investment becomes more so.

**Likelihood:** Low (multiple research lines support H1; v0.1.10
dogfood already showed honest defer outperforming confident wrong
answer). But not zero.

**Mitigation:**
- Maintain the falsification window discipline. Don't
  pre-emptively pivot.
- v0.5 retro is the natural review point.

**Trip-wire:** v0.5 retro question: "after 90 days of substrate,
do you consult `hai explain` outcomes more, or
`hai stats --raw-metrics` (or equivalent)?"

---

### R-S-03. Scope discipline failure

**Trigger:** A high-pull workstream proposed (e.g., adding a new
domain, expanding to clinical, broadening user-set) gets approved
without a formal cycle proposal.

**Impact:** AGENTS.md "settled decisions" stop being load-bearing.
Subsequent decisions reference the unilateral expansion as
precedent. Project becomes the multi-domain coaching system that
H5 explicitly bets against.

**Likelihood:** Medium (single-maintainer project; one excited
afternoon can reshape direction).

**Mitigation:**
- AGENTS.md "Settled Decisions" section explicitly lists the
  invariants.
- This doc's § 8 "open questions" captures what's *not* yet
  decided. Anything outside § 8 + AGENTS.md "settled decisions"
  is a new question that requires a cycle proposal.
- Codex audit checks scope discipline implicitly.

**Trip-wire:** A PR / commit that adds scope without referencing a
PLAN.md or BACKLOG.md item.

---

### R-S-04. Strategic bets lose their evidence anchors

**Trigger:** Research / prior-art that grounded H1-H5 gets retracted,
superseded, or reframed by new findings.

**Impact:** Hypotheses that read like load-bearing bets are now
poorly grounded. Plan readability degrades.

**Likelihood:** Medium over a 24-month horizon. Research is dynamic.

**Mitigation:**
- Annual hypothesis review (per `strategic_plan_v1.md` § 11).
- Bibliography tracked in 2026-04-25
  historical/multi_release_roadmap.md (preserved as historical doc).

**Trip-wire:** Apple Mulberry-style retraction; or a published
result that contradicts H1's "interpretability > better recs"
direction.

---

## 3. Technical risks

### R-T-01. The runtime accumulates bugs the audit cycle doesn't catch

**Trigger:** Audit cycles surface fewer findings over time —
either because the codebase is improving (good) or because the
audit pattern has gaps (bad). Distinguishing the two requires
fresh-eyes review.

**Impact:** Confidence in the runtime degrades silently. A v0.5+
estimator running on subtly wrong substrate produces
impressively-wrong calibration data.

**Likelihood:** Medium. v0.1.10 surfaced 27 findings; subsequent
cycles will find fewer. The question is whether the trajectory is
"genuinely improving" or "audit blindspot."

**Mitigation:**
- Annual fresh-eyes pass: a different LLM (Gemini, GPT-X) or
  external human reviews the entire `src/` tree without prior
  context (`tactical_plan_v0_1_x.md` § 7.5).
- Persona matrix expansion as fresh-eye proxy: each new persona
  exercises a code path the maintainer hadn't.
- Property-based testing (W-P) as orthogonal coverage to
  hand-crafted unit + scenario tests.

**Trip-wire:** Two consecutive audit cycles with zero findings
across all phases. Either celebrate or get suspicious.

---

### R-T-02. Vendor API churn breaks the data path

**Trigger:** Garmin or intervals.icu changes their API in a way
that breaks the pull adapter.

**Impact:** Daily pull fails; runtime can't get data; every
domain defers.

**Likelihood:** High over a 24-month horizon. Both vendors have
rate-limited the project before; intervals.icu's `/activities`
endpoint hadn't surfaced specific contract until recently.

**Mitigation:**
- Decoupled adapter design — only the adapter file changes when
  vendor API changes; the rest of the runtime is insulated.
- Persona harness uses synthetic data; not affected by upstream
  outage.
- CSV fixture path remains as fallback (per `hai pull
  --source csv`).

**Trip-wire:** `hai stats` shows sync_run_log failures
accumulating for an upstream source.

**Action when triggered:** Out-of-cycle hotfix release (v0.1.X.1
patch convention if needed).

---

### R-T-03. `cli.py` rot

**Trigger:** `cli.py` is 8239 lines today. Per AGENTS.md D4, splitting
is deferred. As features land, the file grows. At some
size, it becomes hard to navigate.

**Impact:** Audit-cycle review time grows; new features land
slower; bugs hide longer.

**Likelihood:** Medium. The deferral is sensible today; eventually
not.

**Mitigation:**
- D4 names the trip-wire: cli.py exceeds 10kloc OR external
  integration arrives. Either lifts the deferral.

**Trip-wire:** `wc -l src/health_agent_infra/cli.py` > 10000.

---

### R-T-04. Schema migrations get harder

**Trigger:** v0.1.11 W-E adds a `state_fingerprint` column to
`daily_plan`. Future cycles will add more columns or whole tables
(W52 review tables, W53 insight tables, W-V capabilities-manifest
extension).

**Impact:** Schema migration round-trip tests get expensive; user
DB upgrades start risking data loss.

**Likelihood:** Medium. Each individual migration is fine; the
cumulative burden grows.

**Mitigation:**
- Migration round-trip test pattern is established (per W-E
  acceptance criteria).
- Forward-only migrations (no down-migrations) keeps the test
  surface bounded.
- `hai doctor` migration check on every release.

**Trip-wire:** Migration adds a foreign-key constraint that breaks
when applied to a partially-populated DB. Specific test scenario
in `verification/tests/test_migrations.py`.

---

### R-T-05. Skill drift from runtime contract

**Trigger:** A skill markdown protocol gets updated independently
of the corresponding runtime code. The skill expects a
classified_state shape that differs from what the runtime emits.

**Impact:** Recommendation prose references fields that don't
exist; user sees nonsense.

**Likelihood:** Low-medium. AGENTS.md explicitly disallows skill
arithmetic, but skill prose can still reference stale field
names.

**Mitigation:**
- Eval rubric Axis 3 marks skill-narration as
  `skipped_requires_agent_harness`. v0.2.0 W58 partly closes this
  for weekly review.
- Per-skill unit tests asserting the skill at least loads + has
  the documented frontmatter could catch some drift.

**Trip-wire:** User reports nonsense rationale prose. Or a
deliberate cycle adds a skill-vs-runtime drift check.

---

### R-T-06. Persona matrix becomes a maintenance burden

**Trigger:** Personas accumulate. Each requires fixture data,
expected behaviour declarations, periodic re-validation.

**Impact:** Adding a new persona feels expensive. Existing
personas drift from current runtime expectations. The harness
becomes ornamental rather than load-bearing.

**Likelihood:** Medium over 24-month horizon.

**Mitigation:**
- Cap persona count when marginal-yield is zero (per
  `eval_strategy/v1.md` § 7.3).
- v0.1.13 W-AK shipped explicit `expected_actions` declarations
  on every persona file (per IR r1 F-IR-03 closure), formalising
  expected behaviour as the per-persona ground-truth shape.
- Persona spec is declarative (Python dataclass), not procedural;
  cheap to author.

**Trip-wire:** Two consecutive cycles where the persona harness
runs unchanged because no one re-validated.

---

## 4. Operational risks

### R-O-01. Single-maintainer bus factor

**Trigger:** The maintainer becomes unavailable (illness, life
priorities, employment change).

**Impact:** Project stops shipping. State of the world: code is
documented, settled decisions are explicit, but no continuity.

**Likelihood:** Constant background risk; not a function of time.

**Mitigation:**
- Documentation discipline (AGENTS.md, ARCHITECTURE.md, REPO_MAP.md,
  this whole `reporting/plans/` tree).
- The four-round audit cycle pattern is documented enough that a
  successor with similar skill could pick up.
- LICENSE (MIT) means anyone can fork and continue.

**Trip-wire:** Three consecutive months without a release while
backlog work exists.

---

### R-O-02. Cycle pattern collapses

**Trigger:** A release (v0.1.11+) ships without running the
four-round audit. Once a corner is cut, subsequent cycles cite
the precedent.

**Impact:** Release-proof discipline degrades. v1.0 ships without
the operational claim it's supposed to represent.

**Likelihood:** Medium under maintainer-bandwidth pressure.

**Mitigation:**
- AGENTS.md "Release Cycle Expectation" makes the pattern
  explicit.
- `RELEASE_PROOF.md` is a hard CHANGELOG entry referent — missing
  it for a substantive release is visible.

**Trip-wire:** Substantive release without a `RELEASE_PROOF.md`.

---

### R-O-03. Maintainer dogfood diverges

**Trigger:** The maintainer stops using `hai today` daily. Either
because (a) the project no longer fits their workflow, or (b)
they're using a successor / vendor coach instead.

**Impact:** N=1 dogfood signal disappears. Bug surface that
maintainer-as-user catches goes uncovered. Persona harness has to
absorb everything.

**Likelihood:** Low if H1-H5 hold. Medium if any of H1, H4 falsify.

**Mitigation:**
- Per `success_framework_v1.md` Tier 1.1 — daily-use frequency
  is a load-bearing metric.
- Trip-wire below catches it before it becomes structural.

**Trip-wire:** 7-day rolling `hai daily` count drops below 0.5.

---

### R-O-04. Documentation rot

**Trigger:** AGENTS.md, ARCHITECTURE.md, README.md drift from
implementation. Future maintainer reads docs and gets misled.

**Impact:** Onboarding is harder. Future agent sessions start with
stale priors.

**Likelihood:** High over 24-month horizon if no discipline.

**Mitigation:**
- Per `tactical_plan_v0_1_x.md` § 7.1 — docs updated per release.
- Reading-order index (`reporting/plans/README.md`) makes
  freshness-relevant docs discoverable.
- Annual documentation audit (per success-framework anti-metric
  §7.5).

**Trip-wire:** A reader (Codex, fresh agent session) flags a
specific doc claim that's no longer true.

---

### R-O-05. Releases become prose-heavy

**Trigger:** Each release adds a doc; doc-load grows; readers
drown.

**Impact:** Future maintainer / reader can't find what they need.
Plans become aspirational rather than operative.

**Likelihood:** Medium with planning discipline; high without.

**Mitigation:**
- Reading-order index must stay current.
- Each new doc has a clear refresh cadence + boundary section.
- This doc itself is a meta-mitigation: it captures the meta-
  question of "is the planning system working?"

**Trip-wire:** Maintainer reports inability to find a known piece
of information in the planning tree.

---

## 5. External risks

### R-X-01. Regulatory shift forces server-side audit

**Trigger:** A regulator (FDA, EMA, UK MHRA, EU AI Act
implementation) requires server-side audit of any AI making
health-adjacent recommendations.

**Impact:** Per H2 falsification, the local-first architecture is
the wrong shape. The project either changes architecture (massive
re-shape) or restricts its scope (no longer "personal health
agent" — closer to "personal training tracker").

**Likelihood:** Low-medium over 24 months. UK MHRA + EU MDR
existing definitions exclude wellness apps; new regs would have
to specifically capture wellness AI.

**Mitigation:**
- Wellness-only positioning maintained (no clinical claims, no
  diagnosis). Establishes the regulatory boundary.
- Per H2 falsification window — if regulator forces this, project
  either pivots or scopes down.

**Trip-wire:** A regulatory body publishes guidance specifically
addressing wellness-AI agents.

---

### R-X-02. Local LLM hardware regression

**Trigger:** Apple silicon (or comparable) regresses on local LLM
inference performance — e.g., a future generation deprioritises ML
acceleration; or Anthropic / Meta stop releasing open-weight models
in the size class needed.

**Impact:** Per H2 falsification, local-first beats hosted only if
hardware can run a useful judgment LLM. If hardware regresses, the
v0.5+ local-LLM judge bet becomes unreachable.

**Likelihood:** Low. Apple has invested in M-series ML acceleration;
open-weight models are an active research direction.

**Mitigation:**
- Cloud Anthropic API is the fallback (current state).
- Decision to ship local-default at v0.5 is gated on hardware
  benchmarks being adequate at that time.

**Trip-wire:** A hardware generation drops Apple Neural Engine or
equivalent.

---

### R-X-03. Wearable ecosystem shrinks

**Trigger:** Garmin / Apple / Whoop consolidate or change their
data-sharing policies. Wearable diversity that the project assumes
collapses.

**Impact:** The "data ingest is commodity" claim weakens. The
project's audience shrinks if their primary wearable becomes
opaque.

**Likelihood:** Low-medium. Apple Health remains generous on
read-access; Garmin Connect is rate-limited but functional;
Whoop sells data access via API.

**Mitigation:**
- Multiple-source design — pull adapters are pluggable. Loss of
  one source doesn't kill the pipeline.
- Manual intake surface (`hai intake gym|nutrition|stress|note|
  readiness`) is always available.

**Trip-wire:** A vendor revokes API access without a transition
period.

---

### R-X-04. Anthropic / Claude Code direction change

**Trigger:** Claude Code (the maintainer's primary daily-driver
host agent) changes its skill / hook / MCP architecture in a way
that breaks the project's integration.

**Impact:** The project's primary user-facing surface degrades
until adaptation.

**Likelihood:** Medium over 24 months. Anthropic moves fast on
agent infrastructure.

**Mitigation:**
- The project's strategic surface is the CLI (per H4), not the
  Claude Code integration. CLI works against any host agent.
- Claude Code skill format is markdown — portable across hosts.

**Trip-wire:** Claude Code release-notes flag a breaking change.

---

## 6. Compounding risks (interactions)

Risks that aren't catastrophic alone but combine badly.

### R-C-01. Vendor API churn × scope creep

If R-T-02 (vendor churn) lands during a release that's already
over scope, the maintainer faces "ship the over-scoped release
with broken pull, OR delay the release to fix the adapter."
Either is bad.

**Mitigation:** keep release scope tight. Don't ship a release
without validating the pull path against the current vendor API
state.

### R-C-02. Single-maintainer × cycle pattern collapse × doc rot

If R-O-01 (bus factor) lands while R-O-02 (cycle collapse) and
R-O-04 (doc rot) are accumulating, the project becomes a one-shot
artifact rather than a living system.

**Mitigation:** the planning discipline encoded in this whole
`reporting/plans/` tree is the meta-mitigation. Documentation
that actually maintains the project's continuity capability.

### R-C-03. Persona harness rot × calibration eval scaffolding

If R-T-06 (persona harness becomes ornamental) lands before v0.5
substrate accumulates calibration data, both eval surfaces are
weak simultaneously. The bug-finding signal goes dark.

**Mitigation:** persona harness must stay live through Wave 4.
v0.1.13 W-AK shipped per-persona inline `expected_actions`
declarations, making expectation rot detectable at harness run.

---

## 7. What we are NOT worried about (anti-risks)

Explicit non-risks — things that, if they materialise, are fine.

### Not worried: GitHub stars / community size

Per `success_framework_v1.md` § 6.1. The project succeeds at N=1.
External adoption is bonus.

### Not worried: Cloud compute cost

The project is local-first; runtime cost is the maintainer's
laptop. Hosted-component absence means no infrastructure spend.

### Not worried: Competing wearable coaches gaining mind-share

Per H4 + strategic posture §6.1 — the project's moat is the
governance contract, not a vendor-coach killer. Vendor coaches
expanding doesn't shrink the project's strategic surface.

### Not worried: PyPI availability

The package can be distributed via GitHub releases if PyPI
becomes unavailable. Wheel build is local.

### Not worried: macOS-only platform risk

Linux support is in CI; Windows isn't but the maintainer doesn't
use Windows. Platform expansion is a v0.4+ item if it matters.

---

## 8. Open questions for maintainer judgement

These are questions where my (Claude's) judgement is insufficient.
The maintainer makes the call, ideally at the milestone listed.

### OQ-01. Do we publish workshop / preprint at v0.6?

**Decision needed by:** v0.6 review (post-estimator ship,
2027-Q1-Q2 in optimistic case).

**Trade-off:** ~2 weeks of maintainer time for a credibility
artifact that draws contributors + cites + employer signal.
Versus shipping v0.7 sooner.

**Default:** No. The publication is a portfolio bonus, not a
project requirement.

### OQ-02. Do we open the project to external contributors?

**Decision needed by:** v0.4 review.

**Trade-off:** Contributor leverage (more domain skills, more
adapters) versus review-burden + governance risk. AGENTS.md is
meant to absorb new agents; it's not designed to absorb new
humans with arbitrary opinions about the design.

**Default:** No until v0.4. Revisit when MCP surface ships.

### OQ-03. Do we add a hosted thin-wrapper service?

**Decision needed by:** v1.0 review.

**Trade-off:** Easier onboarding (auth pass-through, cross-device
sync) versus violating H2 (local-first wins for daily-driver use
case).

**Default:** No. Hosted is conditional on a specific user-research
signal, not a default.

### OQ-04. Do we add any of the speculative new domains?

**Decision needed by:** Per-domain (mental health: v0.6 review;
cycling-specific: v0.4 review; rehab: not before v1.0).

**Trade-off:** Per `strategic_plan_v1.md` § 8.1.

**Default:** Per the table in strategic plan § 8.1.

### OQ-05. Do we add Whoop / Oura / Apple Health adapters?

**Decision needed by:** v0.4 review (extension contract release).

**Trade-off:** Adapter-cost vs. user-set expansion. Apple Health
is the most strategic given it's downstream of everything else.

**Default:** Apple Health at v0.4. Whoop / Oura conditional on
demand.

### OQ-06. Do we expose the persona harness to end-users?

**Decision needed by:** v0.5 review.

**Trade-off:** Letting end-users author personas is a powerful
self-eval surface but expands the API surface.

**Default:** No until v0.5. The harness stays maintainer-internal
for now.

### OQ-07. What user-set archetypes does v0.2+ add?

**Decision needed by:** v0.2 review.

**Trade-off:** Per `strategic_plan_v1.md` § 8.5 — older
recreational, female cyclists, etc. Each archetype expansion
requires persona authorship + threshold review.

**Default:** Add 50-65 age band when first non-maintainer user
provides feedback indicating gaps.

### OQ-08. Do we ship a Claude.ai connector / Anthropic API skill?

**Decision needed by:** v0.4 review.

**Trade-off:** Distribution leverage (most natural path given
maintainer's primary loop is Claude Code) versus dependency on
Anthropic-specific surfaces.

**Default:** Yes at v0.4 or v0.5. Pairs with MCP surface.

### OQ-09. Do we ship a local-LLM judge at v0.2 or defer?

**Decision needed by:** v0.2.0 PLAN.md.

**Trade-off:** Local-first integrity at v0.2 (judge runs locally)
versus shipping speed (cloud Anthropic API as judge gets to ship
faster).

**Default:** Local per D8 (settled 2026-04-25). Reconsider only
if hardware budget falls below the model's requirements at
release time.

### OQ-10. How do we handle the v0.1.10 recommendation that's already issued by the agent during dogfood — does it carry forward into v0.1.11+ history?

**Decision needed by:** Anytime — it's a data-management question.

**Trade-off:** Cleaning up state.db before v0.1.11 ship vs.
preserving the audit chain across version boundaries.

**Default:** Preserve. The audit chain across release boundaries
is part of what makes the runtime governable. Don't truncate
history at version bumps.

---

## 9. Risk register table (compact)

| ID | Risk | Likelihood | Impact | Mitigation in place | Trip-wire |
|---|---|---|---|---|---|
| **R-S-01** | Category claim wrong | Low-medium | Strategic | Lead-with-governance posture | Comparable-OSS survey result |
| **R-S-02** | H1 falsifies | Low | Strategic foundation | Falsification window discipline | v0.5 retro |
| **R-S-03** | Scope discipline failure | Medium | Settled decisions degrade | AGENTS.md + cycle proposal requirement | Unilateral scope expansion in commit |
| **R-S-04** | Strategic bets lose evidence | Medium | Plan readability | Annual hypothesis review | Research retraction |
| **R-T-01** | Audit cycle blindspots | Medium | Quality regression hidden | Annual fresh-eyes pass + property tests | 2 cycles with 0 findings |
| **R-T-02** | Vendor API churn | High | Daily pull breaks | Decoupled adapter design | sync_run_log failures |
| **R-T-03** | cli.py rot | Medium | Audit time grows | D4 trip-wire defined | wc -l > 10000 |
| **R-T-04** | Schema migrations harder | Medium | Migration risk | Forward-only + round-trip tests | FK constraint failure |
| **R-T-05** | Skill drift from runtime | Low-medium | Nonsense prose | W58 (partial) + per-skill load tests | User reports prose nonsense |
| **R-T-06** | Persona harness rot | Medium | Eval surface weakens | W-AK formalises expectations | 2 cycles unchanged |
| **R-O-01** | Bus factor | Constant background | Project stalls | Documentation discipline | 3 months no release |
| **R-O-02** | Cycle pattern collapses | Medium | Release-proof degrades | AGENTS.md + RELEASE_PROOF.md | Substantive release without proof |
| **R-O-03** | Maintainer dogfood diverges | Low | N=1 signal disappears | Tier 1 daily-use metric | < 0.5/day for 7 days |
| **R-O-04** | Documentation rot | High over 24mo | Onboarding harder | Per-release update + reading index | Stale claim flagged |
| **R-O-05** | Releases become prose-heavy | Medium | Plans aspirational | Reading-order index | Maintainer can't find info |
| **R-X-01** | Regulatory shift | Low-medium | Architecture wrong | Wellness-only positioning | Wellness-AI guidance |
| **R-X-02** | Local LLM hardware regression | Low | Local-first bet weakens | Cloud fallback | M-series ML deprioritised |
| **R-X-03** | Wearable ecosystem shrinks | Low-medium | Audience shrinks | Multiple-source design | Vendor revokes API |
| **R-X-04** | Claude Code direction change | Medium | Integration degrades | CLI is portable | Breaking change announced |

---

## 10. Provenance + evolution

**Authored:** 2026-04-27 by Claude in extended planning session.

**Sources:**
- `reporting/plans/strategic_plan_v1.md` (hypotheses, settled
  decisions, branches).
- `reporting/plans/tactical_plan_v0_1_x.md` (operational risks).
- `reporting/plans/eval_strategy/v1.md` (eval-surface risks).
- `reporting/plans/success_framework_v1.md` (anti-metrics §7
  cross-reference).
- AGENTS.md governance invariants.

**Refresh:** every minor release. Resolved questions move to
AGENTS.md "Settled Decisions"; closed risks note resolution +
date.

**Boundary:** this doc covers what could go wrong + decisions
needed. Does not cover correctness (`eval_strategy/v1.md`),
project value (`success_framework_v1.md`), or per-release
execution (`tactical_plan_v0_1_x.md`).

---

*Last reviewed: 2026-04-27 by Claude. Next review: post-v0.1.11
ship.*
