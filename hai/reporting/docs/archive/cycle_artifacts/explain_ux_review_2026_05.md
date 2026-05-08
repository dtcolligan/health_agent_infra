# `hai explain` UX review — 2026-05 (v0.1.14 W-EXPLAIN-UX)

**Date.** 2026-05-01.
**Cycle.** v0.1.14 W-EXPLAIN-UX.
**Reviewer.** Maintainer-substitute reader (per PLAN.md §1.3.1
path 2 + §2.C: W-2U-GATE deferred to v0.1.15, so the v0.1.14 pass
uses the maintainer reading `hai explain` output **with a foreign-
user lens** — deliberately asking "what would a low-domain-
knowledge user (P13) not understand here?"). Foreign-user review
of the same trajectories carries forward to v0.1.15 W-2U-GATE.
**Cycle context.** JMIR AI 2024 systematic review on XAI in
clinical decision support shows explanations can *reduce* trust
when confusing. Tandfonline 2025 shows high-confidence calibrated
outputs can also *reduce* diagnostic accuracy via overreliance.
"Refusal IS the demo" only works if the refusal is legible.

## Method

Three sample state trajectories were inspected via
`hai explain --for-date <d> --user-id u_local_1` (JSON mode) on the
maintainer's local state DB after migration 023 (v0.1.14 W-PROV-1)
was applied:

- 2026-04-30 — recent day with X9 firing
  (`training-intensity-bumps-protein` adjusts nutrition target).
- 2026-04-28 — day with stable 6-domain output, no X-rules.
- 2026-04-27 — day with manual readiness intake.

For each trajectory, the maintainer read the explain output as if
they were P13 (35-year-old, no athletics background, basic English,
smartphone-native but not CLI-native — see
`verification/dogfood/personas/p13_low_domain_knowledge.py`) and
captured every place an unfamiliar term, opaque token, or
inscrutable section appeared.

**Limit of method.** A maintainer-substitute reader cannot fully
simulate genuine foreign-user confusion — the maintainer knows
what every token means and consciously has to pretend not to. The
findings below are a baseline; v0.1.15 W-2U-GATE's foreign-user
session will surface confusion modes the maintainer-substitute
missed. Items marked **carries-forward-to-v0.1.15-W-2U-GATE-foreign-
user-pass** are explicitly flagged for re-test.

## Findings

### F-EXPLAIN-01 — Token "X9" is opaque

**Severity.** P1.
**Surface.** `plan.x_rules_fired = ["X9"]` and
`x_rule_firings.phase_b[0].rule_id = "X9"`.

**P13's read.** "What's X9? Is that good or bad? Is something
wrong?"

**Diagnosis.** The token `X9` is the internal stable identifier for
the rule. The `public_name` field
(`training-intensity-bumps-protein`) is more legible but is buried
inside the firing object. JSON-mode output surfaces the opaque ID
first. Markdown rendering should lead with `public_name` and
demote `rule_id` to a sub-line.

**Remediation (v0.1.14-tractable).** None — JSON output is the
contract, and v0.1.14's W-EXPLAIN-UX scope does not change the JSON
schema. **Carries forward to v0.2.0 W52** weekly-review prose
generation (W-EXPLAIN-UX prose obligations §1).

### F-EXPLAIN-02 — `phase_a` / `phase_b` distinction is undocumented in-line

**Severity.** P1.
**Surface.** `x_rule_firings.phase_a` / `x_rule_firings.phase_b`.

**P13's read.** "What's phase A vs phase B? Why are they
different?"

**Diagnosis.** The phase distinction (Phase A = pre-skill rules
that shape the skill's input; Phase B = post-skill action_detail
adjustments) is documented in `core/synthesis_policy.py` but never
surfaced to the explain consumer. A foreign user has no way to
guess.

**Remediation.** Add a one-sentence inline help on the `phase_a` /
`phase_b` keys when surfacing in markdown mode (out of v0.1.14
scope; **carries forward to v0.2.0 W52** prose obligations §2).

### F-EXPLAIN-03 — `synthesis_meta.phase_a_count` / `phase_b_count` is jargon

**Severity.** P2.
**Surface.** `plan.synthesis_meta.phase_a_count = 0`,
`plan.synthesis_meta.phase_b_count = 1`.

**P13's read.** Skip — not parsed.

**Diagnosis.** This is operator-debug telemetry, not user-
facing. JSON-mode legitimately surfaces it; markdown-mode should
hide it behind a `--verbose` or omit it entirely.

**Remediation.** Markdown rendering filters `synthesis_meta` by
default; JSON keeps it. Out of v0.1.14 scope; **carries forward to
v0.2.0 W52** as a prose-obligation: weekly-review prose must not
expose synthesis_meta jargon.

### F-EXPLAIN-04 — `action_detail.caveat` token semantics opaque

**Severity.** P0.
**Surface.** Recommendation/proposal payloads have
`action_detail.caveat = "calorie_surplus_trend"` (and similar tokens
on other rules).

**P13's read.** "What's a calorie surplus trend? Is that bad? Is
that why it's saying maintain targets?"

**Diagnosis.** Caveat tokens are mechanical (they reference rule
firings and signal contexts). They are useful for code-side
analysis and X-rule reasoning but are **opaque to a non-expert
reader**. The token itself ("calorie_surplus_trend") is more
legible than `X9` because it's a phrase, but the relationship
between the action ("maintain_targets") and the caveat
("calorie_surplus_trend") is not explicit.

**Remediation.** v0.2.0 W52 weekly-review prose **must** translate
caveat tokens into legible English ("Your calorie intake has been
above your target for the past three days. Maintaining the target
gives you room to come back down."). This is a **v0.2.0 W52 prose
obligation** — see §"v0.2.0 W52 prose obligations" below.

### F-EXPLAIN-05 — Goal/intent surfaces aren't named in explain

**Severity.** P1.
**Surface.** `user_memory.entries` includes `primary_goal` and
`event_context` but the recommendation/proposal output doesn't
reference them.

**P13's read.** "Did the system see my goal? Is the recommendation
because of my goal or in spite of it?"

**Diagnosis.** Goal-awareness is the load-bearing trust signal for
a low-domain-knowledge user — they need to see their goal echoed
back. Today the goal is in `user_memory.entries` (a section the
reader has to find) and never cited in the rationale. The current
rationale text ("Resting HR elevated 3 days running.") is honest
but doesn't show goal awareness.

**Remediation.** v0.2.0 W52 weekly-review prose **must** open with
the user's primary_goal and explicitly reference it. **v0.2.0 W52
prose obligation.**

### F-EXPLAIN-06 — `bounded` field is jargon

**Severity.** P3.
**Surface.** `recommendations[*].bounded = true`.

**P13's read.** Skip — not parsed.

**Diagnosis.** `bounded` is the governance invariant flag (W57:
agent cannot deactivate user state without explicit user commit).
It is correctness machinery, not user-facing. Markdown should
hide it; JSON keeps it.

**Remediation.** Markdown filters `bounded`. Out of v0.1.14 scope;
defer.

### F-EXPLAIN-07 — Source-row locators (W-PROV-1) render legibly

**Severity.** Positive observation.
**Surface.** Recovery R6 firings now emit `evidence_locators` per
v0.1.14 W-PROV-1.

**P13's read.** "OK so it's looking at my resting heart rate from
the past three days." (Hypothesis; no R6 firing in current
maintainer state to test directly.)

**Observation.** The locator-list rendering shape (`{table} /
{pk-pairs} / {column}`) is self-explanatory. v0.2.0 W52 prose
should reference these directly: "Looking at your last three days
of resting heart rate readings, …" — naming the days makes the
claim auditable. **v0.2.0 W52 prose obligation.**

### F-EXPLAIN-08 — `defer_decision_insufficient_signal` is intuitive

**Severity.** Positive observation.
**Surface.** Multiple action tokens use this when signal is sparse.

**P13's read.** "OK, it doesn't have enough info — that's fine, it
should ask, not guess." (Hypothesis.)

**Observation.** This is exactly the "refusal IS the demo" lever
working. The action token is legible; the user understands the
honest deferral. v0.1.13 onboarding tone (W-AA, W-AF) primed P13
to expect refusals as the right behaviour.

## v0.2.0 W52 prose obligations

Per v0.1.14 PLAN.md §2.C, this section enumerates the
remediation items v0.2.0 W52 PLAN authoring **must** consume.
Each item is an "issue / proposed prose change / acceptance hook"
triplet.

1. **Issue:** Rule IDs (`X9` etc.) opaque to non-experts
   (F-EXPLAIN-01).
   **Proposed prose change:** Lead with `public_name` plain-English
   phrasing; demote `rule_id` to parenthetical.
   **Acceptance hook:** Weekly-review prose contains zero opaque
   `X<N>` rule-ID strings outside parentheses.

2. **Issue:** `phase_a` / `phase_b` distinction unexplained
   (F-EXPLAIN-02).
   **Proposed prose change:** Replace with "rules that shaped the
   recommendation" / "rules that adjusted the result after the
   skill ran" inline.
   **Acceptance hook:** Markdown weekly-review never exposes raw
   `phase_a` / `phase_b` keys.

3. **Issue:** `synthesis_meta` debug telemetry exposed
   (F-EXPLAIN-03).
   **Proposed prose change:** Filter `synthesis_meta` from default
   markdown rendering; keep in JSON.
   **Acceptance hook:** Markdown weekly-review never contains the
   string `synthesis_meta`.

4. **Issue:** Caveat tokens opaque (`calorie_surplus_trend` etc.)
   (F-EXPLAIN-04, **P0**).
   **Proposed prose change:** Each caveat token has a code-owned
   plain-English translation. Weekly-review prose surfaces the
   translation, not the token.
   **Acceptance hook:** No caveat-token string (e.g.
   `calorie_surplus_trend`, `resting_hr_spike_3_days_running`)
   appears in weekly-review prose; every caveat has a
   `core/explain/caveat_translations.py` entry tested for
   non-empty output.

5. **Issue:** User goal not echoed in recommendation rationale
   (F-EXPLAIN-05).
   **Proposed prose change:** Weekly-review prose opens with the
   user's `primary_goal` from user_memory and explicitly references
   it before recommendations.
   **Acceptance hook:** Weekly-review prose contains the user's
   `primary_goal` value as the first noun phrase of the body.

6. **Issue:** Source-row locators (W-PROV-1) should be referenced in
   prose, not just listed (F-EXPLAIN-07).
   **Proposed prose change:** When a claim cites locators, the prose
   names the dates / metrics: "Looking at your resting heart rate
   on April 28, 29, and 30, …" rather than dumping the locator
   table.
   **Acceptance hook:** Every claim with `evidence_locators` is
   preceded by prose that names at least one of the locator's
   pk-fields.

## Carries-forward-to-v0.1.15-W-2U-GATE-foreign-user-pass

The following items must be **re-tested against an actual foreign
user** during v0.1.15 W-2U-GATE. The maintainer-substitute pass
provides the baseline; the foreign-user pass is the empirical
evidence.

- F-EXPLAIN-01 (X9 opaque): the maintainer-substitute hypothesis is
  that `X9` is opaque. A foreign user may either confirm (more
  forceful evidence) or surface a different angle (e.g., "the
  whole `x_rule_firings` section is confusing because it's three
  levels deep").
- F-EXPLAIN-04 (caveat tokens, **P0**): the maintainer-substitute
  marked this P0 on the assumption that caveat tokens are the
  most-load-bearing legibility surface. A foreign user may
  confirm, downgrade (if they intuit the meaning), or surface a
  different P0 (e.g., the rationale text itself).
- F-EXPLAIN-05 (goal echo): the maintainer-substitute hypothesis
  is that goal echo is the load-bearing trust signal. A foreign
  user with a different goal (e.g., athletic-performance vs.
  general-health) may have a different read.
- F-EXPLAIN-07 (locator legibility): the maintainer-substitute was
  *unable* to test this directly because no R6 firing exists in
  current maintainer state. A foreign user with a triggered R6
  scenario (or a contrived test fixture during v0.1.15 W-2U-GATE)
  is needed.

The v0.1.15 W-2U-GATE foreign-user session should explicitly walk
through these four items and capture confirm / downgrade / new-
finding for each.

## Persona matrix observation (P13 added)

`verification/dogfood/personas/p13_low_domain_knowledge.py` is
registered in `ALL_PERSONAS`. P13 is matrix-only per F-PLAN-06
(no W-Vb-3 demo-replay coverage in v0.1.14; W-Vb-3 owns P2-P12
demo-replay residual exclusively). The persona stresses:

- Sparse history (12 days) — exercises R1 / sparse-coverage paths.
- Sporadic logging (~50% of days) — exercises gap-detection.
- Low-domain-knowledge framing (no athletics background) — drives
  the F-EXPLAIN-01..05 maintainer-substitute reading.

Persona-matrix re-run after P13 addition is **expected to land
13/0/0** (matrix-clean: each persona reaches `synthesized` or
expected-defer state without crashes; no demo-replay assertion
for P13 per F-PLAN-06). If P13 surfaces a finding, it adds to
this doc's findings list before v0.1.14 ships.
