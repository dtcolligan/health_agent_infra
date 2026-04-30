# Success Framework v1 — Health Agent Infra

> **Status.** Authored 2026-04-27 by Claude in extended planning
> session. First standalone success-framework doc.
>
> **Reading intent.** When the maintainer is asking "is the project
> succeeding?" — distinct from "is the code correct?"
> (`eval_strategy/v1.md`) and "what comes next?" (`tactical_plan_v0_1_x.md`).
>
> **Refresh cadence.** Reviewed annually OR at every wave boundary
> (v0.2 → v0.3, v0.5 → v0.6, etc.).

---

## Table of contents

1. Why this doc exists
2. North-star: what success looks like
3. Tier 1 — load-bearing metrics
4. Tier 2 — supporting metrics
5. Tier 3 — diagnostic metrics
6. What this framework deliberately does NOT measure
7. Anti-metrics (things to watch for going wrong)
8. Targets at each major wave
9. How to read these metrics
10. Open questions

---

## 1. Why this doc exists

Software projects fail in two ways: shipping the wrong thing well,
and shipping the right thing badly. `eval_strategy/v1.md` covers
the second (correctness). This doc covers the first (value).

The project is N=1 today. Most success measurement frameworks
assume a user community to draw signal from. The honest framing
here:
- **Phase 1 (v0.1.x):** measure code health + maintainer-as-user
  utility. The maintainer is the only user; their daily use is the
  signal.
- **Phase 2 (v0.2 → v0.5):** measure substrate health + N-of-1
  outcome trajectories.
- **Phase 3 (v0.5 → v1.0):** measure calibration on accumulated
  outcome data.
- **Phase 4 (post-v1.0):** measure community + adoption if a
  community materialises.

This doc is honest about which phase the metrics live in. A
phase-3 metric reported in phase-1 is a vanity number.

---

## 2. North-star: what success looks like

The project succeeds if, at v1.0:

> **The maintainer (and any other user who installs it) can rely on
> `hai today` as their daily decision input across the six domains,
> trusts its abstain-when-uncertain behaviour, and uses
> `hai explain` to reconstruct any past decision when something
> surprises them.**

This is one sentence with five operative phrases. Each is a
falsifiable claim:

1. **"Rely on `hai today`"** → daily-use measurement.
2. **"Across the six domains"** → all-domain coverage, no domain
   chronically deferring.
3. **"Trusts its abstain-when-uncertain behaviour"** → defer
   action correlates with low calibration confidence; user does
   not feel deferred-out-of-laziness.
4. **"Reconstruct any past decision"** → audit-chain integrity,
   `hai explain` walks every plan cleanly.
5. **"When something surprises them"** → review-outcome surface
   captures surprise; agent learns from it.

The success framework's Tier 1 metrics map directly to these
five claims.

---

## 3. Tier 1 — load-bearing metrics

These are the metrics that, if they regress, the project is
failing on its core value proposition.

### 3.1 Daily-use frequency

**What:** Number of `hai today` runs per day, averaged over a
trailing 30-day window.

**Why it matters:** If the maintainer (the only user) isn't
running `hai today` daily, the project isn't a daily driver. If
they're running it many times a day, something is wrong (probably
state-vs-render divergence per F-B-02, B7).

**Target:**
- v0.1.x: ≥ 1.0 (at least once per day on average).
- v0.2.0+: 1.0-2.5 (daily check + occasional re-check after intake).
- v0.5+: same as v0.2.0; volatility above 2.5/day flags
  potential regression.

**Source:** `runtime_event_log` table — count `daily` events per
date.

**Phase:** 1.

### 3.2 Audit-chain reconcilability

**What:** Percentage of recent days for which
`proposal_log → planned_recommendation → daily_plan →
recommendation_log → review_outcome` reconciles cleanly via
`hai explain --plan-version all`.

**Why it matters:** The audit chain is the load-bearing governance
invariant. Any break here = a published claim the runtime can't
back up.

**Target:** 100%. Any break is a v0.1.x release-blocker.

**Source:** Audit-chain probe (Phase B in v0.1.10 PRE_AUDIT_PLAN).
Automated as part of `hai doctor` in v0.1.13 (W-AE shipped 2026-04-30).

**Phase:** 1+ (always measurable).

### 3.3 Persona matrix pass rate

**What:** Fraction of personas (P1-P12 in v0.1.11) that:
- Run without crashes.
- Produce action recommendations matching declared
  `expected_actions` (W-AK shipped at v0.1.13 with inline
  per-persona declarations on every `p<N>_<slug>.py` file
  per IR r1 F-IR-03 closure; v0.1.14 W-AH expands assertion
  coverage further).

**Why it matters:** Catches classifier-assumption bugs that hide
behind the maintainer's specific user shape (single-user dogfood
limitation).

**Target:**
- v0.1.10: ≥ 0.7 (informally, given findings detector heuristics).
- v0.1.11+: ≥ 0.95 (with explicit `expected_actions`; shipped at
  v0.1.13 W-AK).
- v1.0: 1.0.

**Source:** `verification/dogfood/runner.py` `summary.json`
output.

**Phase:** 1+.

### 3.4 Confidence calibration

**What:** Per-domain correlation between
`recommendation.confidence` (low/moderate/high) and
`review_outcome.self_reported_improvement` (boolean) over
trailing 90-day window.

**Why it matters:** The agent saying `confidence: high` must
*mean something*. Otherwise, the abstention behaviour (H1) is
pretty much the only signal users can trust, and the rest is
noise.

**Target:**
- Pre-v0.5: not yet measurable.
- Post-v0.5 + 90 days substrate: high-confidence correlate ≥ 0.5;
  low-confidence correlate ≤ 0.2.
- v1.0: same plus drift detection (regression alarm if a domain
  miscalibrates over a quarter).

**Source:** `core/review/summary.py` will gain a calibration
report function; first reportable measurement is post-v0.5
substrate.

**Phase:** 3.

### 3.5 Defer rate per domain

**What:** Per-domain percentage of recommendations whose action
is `defer_decision_insufficient_signal` over a trailing 30-day
window.

**Why it matters:** Defer is a feature, not a bug — but a chronic
defer indicates either (a) data-source gaps (vendor variability)
or (b) classifier assumptions the user shape doesn't fit.

**Target:**
- v0.1.x: per-domain ≤ 0.5 (≤ half the days defer for any single
  domain). Higher rates are flagged for investigation.
- v0.2+: per-domain ≤ 0.3 for users with >30 days history.
- v1.0: per-domain ≤ 0.15 for active users.

**Anti-gaming note (v0.1.12 reconciliation C9).** A *lower* defer
rate is not better if it comes from false confidence. The
calibration-substrate work in Wave 4+ (per
`eval_strategy/v1.md`) will pair defer rate with calibration
score — a recommendation that fires confidently but turns out
wrong is worse than one that defers honestly. Do not optimise
this metric in isolation.

**Source:** Aggregate over `recommendation_log` rows.

**Phase:** 1+.

---

## 4. Tier 2 — supporting metrics

Useful diagnostic signals; informative but not load-bearing.

### 4.1 Test count

**What:** `pytest` count over time.

**Why:** Indicator of active investment in correctness.

**Target:** monotonically non-decreasing minor-to-minor. Drops
flagged for review (test deletion is occasionally correct, but
should be intentional).

### 4.2 Mypy clean baseline

**What:** Number of mypy errors (default + strict).

**Why:** Type safety hardens the runtime against silent bugs
(F-A-01 demonstrated the bool-as-int class).

**Target:**
- v0.1.10 baseline: 35 default-mode errors.
- v0.1.11 W-H1 closes 6.
- v0.1.12 W-H2 closes the remaining ~10 stylistic.
- v1.0: 0 default-mode, ≤ 5 strict-mode (with documented reasons).

### 4.3 Findings-per-cycle

**What:** New audit findings surfaced per release cycle.

**Why:** The pre-PLAN bug-hunt pattern (D11) should produce a
shrinking finding count over cycles as the codebase matures. A
sudden spike indicates either a regression or a new axis exposed
(e.g., new persona shape).

**Target:** decreasing trend. Outlier cycles get root-cause
analysis in the cycle retro.

### 4.4 Time-to-ship per cycle

**What:** Days from cycle open to cycle ship.

**Why:** Cycle inflation indicates scope creep, scope underestimation,
or a maintenance bottleneck.

**Target:**
- v0.1.10: shipped in single session (~6 hours of focused work).
- v0.1.11: target 3-4 weeks per tactical plan §2.5.
- Trend: cycles taking > 1.5× their estimate get a retro on why.

### 4.5 CHANGELOG entry quality

**What:** Subjective — does the CHANGELOG entry let a future reader
understand what shipped without reading the PR?

**Why:** Future maintainers (including future-you) read CHANGELOG
to ground decisions. Sparse entries cost time downstream.

**Target:** Per-W-id summary present, with a one-line "why" beyond
"what." Reviewed at audit-cycle time.

### 4.6 Persona harness execution time

**What:** Wall-clock time for full persona matrix run.

**Why:** If it grows unbounded, it stops being useful as a
release-time check.

**Target:**
- v0.1.10: 8 personas, ~minutes.
- v0.1.11: 12 personas, < 5 min.
- v1.0: ≤ 15 min for whatever count exists then. If it exceeds,
  parallelise or sub-set.

---

## 5. Tier 3 — diagnostic metrics

Watched but not targeted. Surface unexpected patterns.

### 5.1 Per-domain action distribution

What fraction of days resolve to `proceed_*` vs. `downgrade_*`
vs. `rest_*` vs. `defer_*` vs. `escalate_for_user_review`. Drift
in this distribution can signal calibration issues.

### 5.2 X-rule firing rate

How often each X-rule fires per 30-day window. A rule that never
fires is suspicious (dead?). A rule that always fires is also
suspicious (over-triggered?).

### 5.3 Threshold-override frequency

How many users (today: 1) have a non-default `thresholds.toml`.
Indicates whether the default thresholds are reasonable.

### 5.4 `hai explain` query rate

How often the maintainer (or any user) consults `hai explain`. A
proxy for "does the user trust enough to inspect when surprised?"
— H1 evidence.

### 5.5 Review-outcome submission rate

What fraction of recommendations get a follow-up review_outcome.
Low rates indicate the review surface is too high-friction.

---

## 6. What this framework deliberately does NOT measure

Explicit non-measurements, framed as choices:

### 6.1 Star count, GitHub clones, downloads

**Why not:** N=1 vanity metrics. The project is local-first and
single-maintainer; stars and clones don't correlate with
correctness. Reportable post-v1.0 if the project pursues
community.

### 6.2 LLM call count or token spend

**Why not:** Per H4, the agent driving the CLI is the strategic
shape. LLM call count varies with the user's host agent and prompt
patterns; not a project-controllable signal.

### 6.3 Lines of code

**Why not:** Already covered indirectly by test-count + mypy
metrics. LOC alone is misleading.

### 6.4 User satisfaction surveys

**Why not:** N=1. Maintainer satisfaction isn't generalisable.
Reportable post-v0.4 if external users land + opt in.

### 6.5 Comparison to closed-source vendor coaches

**Why not:** Different architecture, different data, different
audience. Comparable-OSS survey already covers this in the
strategic plan.

---

## 7. Anti-metrics (watch for these going wrong)

Things that, if they happen, indicate the project has drifted
from its core principles.

### 7.1 Skill arithmetic appearing

**Anti-metric:** Any skill markdown file under
`src/health_agent_infra/skills/` performs arithmetic that should
live in the runtime (computes a band, computes a score, fires an
R-rule, fires an X-rule).

**Why it matters:** Violates the code-vs-skill boundary in
AGENTS.md. The skill becomes a runtime, the runtime becomes
ornamental.

**Detection:** Manual code review of skill changes; future
linter rule.

**Target:** zero occurrences. Failure = release-blocker until
fixed.

### 7.2 Clinical claims in rationale prose

**Anti-metric:** Any rationale_text or follow_up.review_question
contains diagnosis-shaped tokens (already covered by validator
banned-token sweep — but the *intent* sneaks in via euphemism
sometimes).

**Detection:** Banned-token validator + manual eval review.

**Target:** zero. Validator failure.

### 7.3 Direct DB writes bypassing CLI

**Anti-metric:** Any code path mutates `state.db` outside `hai`
CLI invocations (per AGENTS.md governance invariant).

**Detection:** Manual review; potential code-search lint.

**Target:** zero in `src/`. Tests are exempt (they often write
test fixtures directly).

### 7.4 Confidence inflation

**Anti-metric:** Per-domain `confidence: high` rate increasing
over time without corresponding outcome calibration improvement.

**Detection:** Tier 3.1 + Tier 1.4 paired report.

**Target:** stable or decreasing high-confidence rate, increasing
calibration. Inverse pattern = miscalibration accumulating.

### 7.5 Documentation drift

**Anti-metric:** AGENTS.md, ARCHITECTURE.md, REPO_MAP.md, README.md
contain claims that are no longer true (e.g., feature X
description but feature X removed).

**Detection:** Annual review pass + post-release update discipline.

**Target:** zero stale claims. Checked at release time.

### 7.6 Audit-cycle compression

**Anti-metric:** Substantive releases skip the four-round audit
cycle (Phase 0 → PLAN → Codex → response → ship proof).

**Detection:** Release proof must reference audit rounds.

**Target:** every substantive release runs the cycle. Doc-only
releases exempt with explicit maintainer note.

---

## 8. Targets at each major wave

Compact view of what each wave's "good" looks like across the Tier
1 metrics.

| Wave | Daily-use | Audit reconcile | Persona pass | Calibration | Defer rate |
|---|---|---|---|---|---|
| **Wave 1 (v0.1.10–v0.1.13)** | ≥ 1.0/day | 100% | ≥ 95% pass | n/a | per-domain ≤ 0.5 |
| **Wave 2 (v0.2)** | 1.0-2.5/day | 100% | 100% pass | n/a | per-domain ≤ 0.3 |
| **Wave 3 (v0.3-v0.4)** | same | 100% | 100% pass | scaffold ready | same |
| **Wave 4 (v0.5-v0.6)** | same | 100% | 100% pass | first reportable measurement at v0.5 + 90d | per-domain ≤ 0.2 |
| **Wave 5 (v0.7-v1.0)** | same | 100% | 100% pass | high-conf > 0.5 correl, low-conf < 0.2 | per-domain ≤ 0.15 |

Anti-metric watch (§7) is live across all waves.

---

## 9. How to read these metrics

### 9.1 What good looks like

A healthy project month, pre-v0.2:
- `hai today` runs every day.
- Persona matrix passes on every release.
- Audit-chain reconciles cleanly.
- Defer rate per domain stays under 50%.
- One-to-three audit findings per release cycle, decreasing trend.
- Mypy delta zero or improving.
- CHANGELOG entries explain "why" not just "what."

### 9.2 What concerning looks like

- `hai today` skipped for 3+ consecutive days → daily-driver claim
  is wobbling.
- Audit-chain has any orphan or version-skip → governance
  invariant breached.
- Persona matrix regressions → fix before next ship.
- Defer rate spike for a domain → either a vendor data-source
  outage (likely) or a classifier regression (investigate).

### 9.3 What clearly bad looks like

- Anti-metric §7.1, 7.2, 7.3, 7.6 violations.
- Cycle ships without RELEASE_PROOF.md.
- Maintainer reports "I don't trust this anymore" — qualitative
  but operative.

---

## 10. Open questions

### Q1. Should we instrument `hai today` runs for self-reporting?

**Default:** No telemetry. Local-first, no network calls. Daily-use
frequency is computed from `runtime_event_log` (already local).

But — should the project ship a maintainer-only opt-in summary
that emits Tier 1 metrics weekly? Convenience vs. surface area.

**Decision needed by:** v0.2.0 review.

### Q2. How do we measure "trust" objectively?

**Status:** "Maintainer trusts the runtime" is a qualitative
self-report.

**Question:** Is there a derivable proxy? E.g., what fraction of
recommendations does the maintainer follow? What fraction do they
override via review_outcome?

**Default:** add a "followed recommendation" boolean to
review_outcome (already exists per AGENTS.md governance
invariant 6 — `followed_recommendation` is a typed field). Use
this as the trust proxy.

### Q3. When does the framework graduate to community measurement?

**Status:** Phase 1 (N=1) measurements are honest. Phase 4
(community) metrics need community.

**Question:** What signal indicates community has formed? PyPI
downloads from non-maintainer IPs? GitHub stars? Pull requests
from non-maintainer accounts?

**Default:** the trigger is qualitative — a sustained pattern of
external interest. Could be downloads, stars, issues, PRs, or
external mentions. The maintainer makes the call at a v0.4+ review.

### Q4. Should the framework include code-quality metrics?

**Status:** Mypy + ruff + bandit covered as Tier 2.

**Question:** Should test coverage percentage, cyclomatic
complexity, etc. be tracked?

**Default:** No, per "lines of code" exclusion (§6.3). They're
indirect signals already covered by Tier 2 metrics.

---

## 11. Provenance + evolution

**Authored:** 2026-04-27 by Claude in extended planning session.

**Sources:**
- `reporting/plans/strategic_plan_v1.md` § 9 (v1.0 ship criteria).
- `reporting/plans/eval_strategy/v1.md` (calibration eval shape).
- `reporting/plans/v0_1_10/audit_findings.md` (deferred work
  surface).
- AGENTS.md governance invariants 1-6.
- 2026-04-25 historical/multi_release_roadmap.md (H1 falsification
  framing).

**Refresh:** annually OR at every wave boundary. Tier 1 metrics
reviewed every minor release.

**Boundary:** this doc covers project value. It does not cover
test correctness (`eval_strategy/v1.md`) or release execution
(`tactical_plan_v0_1_x.md`).

---

*Last reviewed: 2026-04-27 by Claude. Next review: post-v0.2.0 ship
or Q1 2027 — whichever comes first.*
