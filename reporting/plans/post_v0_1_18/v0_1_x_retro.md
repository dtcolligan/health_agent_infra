# v0.1.x Retro — What 18 Cycles Taught Us About Building Governed AI Agents

> **Status.** Authored 2026-05-06 by Claude (delegated by maintainer)
> at the close of the v0.1.x track. Companion to
> `strategic_plan_v2.md`.
>
> **Audience.** External-readable. A senior engineer, lab director,
> or portfolio reviewer who doesn't know this project should be able
> to read this cold and understand:
> 1. What the project is.
> 2. What 18 release cycles actually shipped.
> 3. Five lessons that generalise beyond this codebase.
> 4. The patterns that are now load-bearing project infrastructure.
> 5. What this maintainer learned about shipping software at this
>    rigor as a single person.
>
> **Boundary.** This doc covers operational and methodological
> learning. Strategic posture lives in `strategic_plan_v2.md`;
> per-release detail lives in `tactical_plan_v0_1_x.md`; per-cycle
> evidence lives in `reporting/plans/v0_1_*/`.

---

## Table of contents

1. What this is, in one paragraph
2. The shape of the work in numbers
3. Five lessons that generalise
4. Patterns now load-bearing
5. What this ships that competitors don't
6. What the maintainer learned about building solo at this rigor
7. What this means for the next phase

---

## 1. What this is, in one paragraph

Health Agent Infra is a **local-first agent-wrapper** for daily
personal-health decisions across six domains (recovery, running,
sleep, stress, strength, nutrition). A user talks to a host agent
in natural language; the agent invokes the local `hai` CLI; a
deterministic Python runtime owns every band, score, and rule, and
commits decisions to local SQLite + JSONL audit logs. The
contract is one line: **the agent proposes and explains; the
runtime validates and commits.** The unit of shipping is a Python
wheel + markdown skills the agent reads at runtime.

The project is its own dogfood — the maintainer (one person)
develops it through Claude Code over its own CLI. Eighteen release
cycles between 2026-04-23 and 2026-05-06 produced the v0.1.x track.
This retro names what those cycles taught us.

---

## 2. The shape of the work in numbers

Concrete v0.1.x track at the close of v0.1.18 (2026-05-06):

| Surface | Value |
|---|---|
| Release cycles shipped | 16 (v0.1.4 through v0.1.18, plus 2 hotfixes) |
| Cycles cancelled | 2 (v0.1.16, v0.1.19) |
| Time elapsed | ~2 weeks |
| Lines of code in `src/` | ~30,000 (rough; mostly Python + markdown skills) |
| `cli.py` line count | 9,927 → split across 1 main + 1 shared + 11 handler-group modules at v0.1.17, all <2,500 LOC each |
| `hai` CLI commands | 67 annotated commands |
| Schema migrations | 26 (forward-only) |
| Tests at release | 2,733 passing, 5 skipped (full suite, broader `-W error::Warning` gate, ~130s) |
| Eval scenario fixtures | 135 deterministic + 30 judge-adversarial |
| Personas | 13 archetypes (P1–P13) — full matrix run opt-in via `HAI_RUN_PERSONA_MATRIX=1` |
| Settled decisions in AGENTS.md | 16 (D1–D16) |
| Audit findings closed across v0.1.x | ~120 documented in cycle artifacts |
| Cycle proposals (CPs) accepted | ~10 across v0.1.12+ |

The project is single-maintainer + one AI collaborator (Claude
Code) + a structured second-AI reviewer (Codex) + an opt-in persona
matrix that exercises 13 synthetic users on every release. Nothing
ships without an audit trail.

---

## 3. Five lessons that generalise

Operational lessons from v0.1.x that apply to any project building
software an LLM agent will drive. Each is named at a level
abstract enough to apply outside this codebase, but grounded in
concrete v0.1.x examples.

### Lesson 1 — Audit chains *settle*; they don't *converge*

**Observation.** When a competent reviewer audits a substantive
plan or implementation, finding count drops by roughly half each
round. It does not drop to zero in one round. Twice or
thrice-validated empirical settling shapes:

- **Plan-audit (D14):** 10 → 5 → 3 → 0 findings (v0.1.11 + v0.1.12),
  11 → 5 → 3 (v0.1.17, one round shorter), 7 → 3 (v0.1.18, halving
  close-in-place at 2 rounds).
- **Implementation review (D15 IR):** 5 → 2 → 1-nit (v0.1.11 +
  v0.1.12), 6 → 1 (v0.1.17, mechanical), 4 → 2 → 1-nit (v0.1.18).

**Why.** Round 1 catches first-order issues — what's wrong on the
face of it. Round 2 catches second-order issues introduced by
round-1 fixes ("you said you'd update X to fix Y; X is updated but
Y still references the old behaviour in three other places").
Round 3 catches third-order propagation ("the round-2 fix to Z
revealed Z is cited by W which is now stale"). The pattern is
recursive; pretending it isn't means shipping with the round-3
issues uncaught.

**Application.** Budget audit rounds against the empirical norm.
For substantive plans: 2–4 rounds. For substantive implementations:
2–3 rounds. **A "one-shot" estimate on a substantive plan is
wrong.** Round 2 always finds something round 1 introduced.

If round N has *more* findings than round N-1, the previous
response introduced second-order issues — re-read your own diff.

### Lesson 2 — Two-LLM disagreement is productive when you don't collapse it

**Observation.** v0.1.x ran every substantive cycle with Claude
authoring artifacts and Codex reviewing them. The maintainer's
explicit instruction (in `~/.claude/CLAUDE.md`): *"Dom is comfortable
having Claude and Codex disagree. Do not collapse toward consensus.
Use disagreement to sharpen the plan."*

That posture caught at least three classes of bug across v0.1.x
that single-AI review wouldn't have:

- **v0.1.12 D14 round 1** — Codex caught Claude citing
  `core/credentials.py:171` for a helper that actually lived at
  `core/pull/auth.py:171`. Wrong file path in a load-bearing audit
  prompt.
- **v0.1.12 D14 round 2** — Codex caught "strategic plan §10
  contains no MCP exposure row" when it had a Wave 3 row at line
  444. Wrong cited absence.
- **v0.1.12 IR round 1** — Codex caught W-FBC RELEASE_PROOF claiming
  "recovery prototype shipped" when only the flag plumbing landed.
  Overclaim of completion.

**Why.** Two LLMs trained at different times on different data
develop different blind spots. A bug that looks invisible to one
often looks obvious to the other. Collapsing toward consensus
removes the signal.

**Application.** Run an adversarial reviewer that doesn't share
your training distribution. When the reviewer disagrees with you,
**treat the disagreement as evidence**, not as friction. Resolve
disagreements through file:line citation, not through
authority-of-the-recent-author.

This is also a hedge against single-vendor risk. If Anthropic or
OpenAI changes their model behaviour mid-project, the second
reviewer catches the regression.

### Lesson 3 — Persona-driven regression beats single-user dogfood

**Observation.** v0.1.10 introduced an 8-persona regression harness
(P1 through P8 archetypes — recreational lifter, returning-to-
running, stressed knowledge worker, etc.). v0.1.11 expanded to 12.
v0.1.14 added P13 for low-domain-knowledge readers. The harness
runs synthetic users through the full pipeline.

In v0.1.10 alone, the persona matrix surfaced 6 bugs the single-user
maintainer dogfood had not exposed across multiple weeks:

- F-C-01: classifier assumption that broke on a triathlete persona.
- F-C-02: nutrition partial-day handling that broke on a
  weekend-skip pattern.
- F-C-03: per-activity rollup never invoked for intervals.icu users
  (every such user defaulted to "running deferred — insufficient
  signal" regardless of activity log richness).
- F-C-04: stress-policy edge case on elevated-baseline persona.
- F-C-05: strength_status enum surface gap.
- F-C-08: synthesis-policy R-rule firing on a persona shape the
  maintainer didn't fit.

**Why.** Single-user dogfood, even when the user is the maintainer,
exercises a narrow band of the input space. The maintainer's
training pattern, sleep pattern, and recovery shape don't span
the user-space the runtime claims to support. Synthetic personas
fill the gap mechanically.

**Application.** Ship a persona-driven regression harness *before*
shipping to a second user. Each persona is cheap to author
(declarative dataclass at `verification/dogfood/personas/p<N>_<slug>.py`).
Each one exercises a code path the maintainer hadn't.

This generalises beyond personal-health software: any product with
a "user" abstraction has a similar single-user-dogfood blind spot.

### Lesson 4 — Empirical-by-design cycles can't be built on synthetic evidence

**Observation.** v0.1.x cancelled two cycles:

- **v0.1.16** — scoped as "the bugs the post-publish foreign-user
  session surfaces." Cancelled 2026-05-04 when the named candidate
  became unavailable. PLAN.md was deliberately not authored ahead
  of cycle open because the scope was empirical.
- **v0.1.19** — renumbered from v0.1.16's empirical scope.
  Cancelled 2026-05-06 when the maintainer's candidate-supply
  criteria proved too narrow to satisfy on the v0.2.0 timeline.

Both cycles were doctrinally well-formed (maintainer paused rather
than fabricating evidence). Both cycles slipped because the
empirical contract was over-specified.

**Why.** Empirical-by-design cycles depend on a real-world
precondition that engineering effort can't manufacture. If you
ship the cycle anyway, the closure claim is fabricated; if you
don't, the cycle slips.

**Application.** For empirical cycles:
1. Author a cancellation README precedent ahead of time so the
   cancellation path is known.
2. Split monolithic empirical gates into multiple claims with
   different supply costs (this is what CP-2U-GATE-SPLIT did
   today — split W-2U-GATE into W-2U-INSTALL + W-2U-WEARABLE +
   W-2U-DOGFOOD, only one gating).
3. Re-tier deferred gates to opportunistic-not-blocking with a
   named re-evaluation milestone, not "later" or "indefinite."

**The uncomfortable truth this surfaces:** sometimes the only
honest move is to cancel a cycle. That's discipline, not weakness.
Twice across v0.1.x, the maintainer cancelled rather than ship
synthetic evidence. The audit chain remained trustworthy as a
result.

### Lesson 5 — Honest partial-closure naming saves audit rounds

**Observation.** When a workstream undershoots, naming the residual
with destination cycle in every artifact is cheaper than dressing
up partial work as full delivery. The audit chain catches the
mismatch every time; the only difference is whether you save a
round by being honest first.

v0.1.x convention (now codified in `AGENTS.md` "Patterns the
cycles have validated"):

- `in-cycle (W-X here)` → `partial-closure → v0.1.X+1 W-X-2`
- `full broader gate ships` → `fork-deferred → v0.1.X+1 W-X`

**Examples.**
- v0.1.12 W-Vb shipped only the workstream's structural surface;
  the broader empirical gate was named `fork-deferred → v0.1.13
  W-Vb-3` and tracked.
- v0.1.12 W-FBC shipped flag plumbing only; the recovery prototype
  itself was named partial-closure.
- v0.1.12 W-N-broader shipped the v0.1.11 narrow gate unchanged;
  broader-gate fix was fork-deferred to v0.1.13.

**Why.** Audit rounds catch overclaim mechanically. Codex round 2
of any substantive cycle will compare RELEASE_PROOF claims against
the actual diff and surface a finding for every claim that
overshoots. Saving that round means naming residuals upfront.

**Application.** When closing partial work, name *what undershot*,
*by how much*, *where the residual lives*, and *which cycle picks
it up*. Don't compress. Don't dress up. Don't defer without
destination.

This generalises to any version-controlled work: **the diff is the
ground truth.** If the diff doesn't support the claim, the claim
is wrong, not the diff.

---

## 4. Patterns now load-bearing

Operational machinery shipped across v0.1.x that future cycles
depend on. Each is now a named settled decision in AGENTS.md.

### D11 — Pre-PLAN bug-hunt (v0.1.10)

Before scoping a substantive PLAN.md, run a structured hunt:
internal sweep + audit-chain probe + persona matrix + Codex
external audit. Findings consolidate to `audit_findings.md` with
`cycle_impact` tags (`revises-scope`, `aborts-cycle`,
`informational`).

**Concrete example:** v0.1.18 Phase 0 surfaced F-OB-PRE-01 (intake
crash on schema-behind DB) as `revises-scope`; the cycle absorbed
the fix as W-OB-7 instead of slipping it.

### D14 — Pre-cycle plan-audit (v0.1.11)

Before Phase 0 opens, Codex reviews PLAN.md against
`codex_plan_audit_prompt.md` and returns one of `PLAN_COHERENT` /
`PLAN_COHERENT_WITH_REVISIONS` / `PLAN_INCOHERENT`. Maintainer
responds; PLAN.md revises until verdict is positive. Multi-round
normal.

**Concrete example:** v0.1.11 D14 round 1 caught 10 substantive
findings (including 2 fail-open correctness bugs and a wrong file
path) before any code changed. Round 2 caught 5 second-order
contradictions. Round 3 caught 3 stale propagation clauses. Round
4 verdict was `PLAN_COHERENT`. **Empirically, 4 rounds was the
full settling time for a substantive PLAN.md.**

### D15 IR cycle (v0.1.8 stabilised)

After implementation, Codex reviews against
`codex_implementation_review_prompt.md` and returns `SHIP` /
`SHIP_WITH_NOTES` / `SHIP_WITH_FIXES`. Multi-round; same settling
shape pattern as D14.

**Concrete example:** v0.1.18 IR round 1 caught 4 findings
(F-IR-01 stale `agent_cli_contract.md` + F-IR-02 README pre-W-OB-2
wording + F-IR-03 missed concrete doctor checks + F-IR-04
`next_action_hint` correctness bug). All 4 accepted + fixed in a
fix-and-reland commit. Round 2 caught 2 follow-on findings.
Round 3 caught 1 nit. **Settled at 4 → 2 → 1-nit, matching
empirical norm.**

### D15 cycle-weight tiering (v0.1.12)

Substantive / hardening / doc-only / hotfix. RELEASE_PROOF.md
declares the chosen tier as the first line of the document. Each
tier has different audit-cycle obligations:

- **Substantive** — full Phase 0 + multi-round D14.
- **Hardening** — abbreviated Phase 0; single-round D14 target.
- **Doc-only** — may skip Phase 0 + D14.
- **Hotfix** — may skip Phase 0 + D14; lightweight RELEASE_PROOF.

This prevents small cycles from being implicitly forced through
the substantive machinery.

**Concrete example:** v0.1.14.1 declared `tier: hardening` and
shipped a single workstream (W-GARMIN-MANIFEST-SIGNAL) without
external Codex IR. v0.1.18 declared `tier: substantive` and ran
the full audit chain. Both were correct calls; the tiering made
the difference legible.

### D16 — W-2U-GATE split (post-v0.1.18, today)

Foreign-user empirical evidence is three gates, not one:
W-2U-INSTALL (closed verbal-only by today's father session),
W-2U-WEARABLE (deferred to v0.4 review), W-2U-DOGFOOD (≥7d daily
non-maintainer use, deferred to v0.4 review). v0.2.0 hard-dep on
foreign-user empirical dropped.

Origin: today's chat. The foreign-user gate had slipped four times
(v0.1.14 → v0.1.15 → v0.1.16 cancelled → v0.1.19 cancelled). The
slip pattern surfaced the over-specification. CP-2U-GATE-SPLIT
formalises the split.

---

## 5. What this ships that the surveyed competitive landscape doesn't

Cross-checked against the comparable-OSS survey carried forward
from `historical/multi_release_roadmap.md` (2026-04-25):

### 5.1 Deterministic policy engine separated from LLM judgment

R-rule layer (per-domain forced-action / capped-confidence rules)
+ X-rule layer (cross-domain Phase A mutations) implemented in
code. Skill-level invariants enforce that neither runs in prose.
v0.1.10 D12 closed the bool-as-int silent-coercion class durably.

No surveyed competitor (Quantified Self trackers, athlete analytics
platforms, MCP servers, vendor coaches, multi-agent personal-
health frameworks) ships this separation.

### 5.2 Domain-typed Proposals with explicit safety/abstain semantics

`defer_decision_insufficient_signal` is a first-class action enum
value in every domain. Abstention is a runtime-enforced behaviour,
not an option. v0.1.18's father session demonstrated this works
empirically — a wearable-less user got coherent output because the
abstain path is honest.

### 5.3 Three-state writeback + review-outcome loop

`proposal_log → planned_recommendation → daily_plan +
recommendation_log → review_outcome` reconciles end-to-end. D1
re-author semantics handle the supersession case. `hai explain`
walks every plan cleanly.

Every comparable MCP server exposes raw data. None persist a
user-confirmed outcome and link it back to the originating
recommendation, much less re-link across superseded plans.

### 5.4 Capabilities manifest as agent contract

`hai capabilities --json` exposes 67 commands with mutation
classes, `agent_safe` flags, idempotency, exit-code semantics.
Byte-stable across the v0.1.17 cli.py mechanical split. v0.1.14.1
added structured `choice_metadata.reliability` fields for vendor
unreliability signals.

This is what makes the project's CLI legible to *another agent*
rather than just to a human reading help text.

### 5.5 Persona-driven regression infrastructure

13 synthetic archetypes exercised on every release (opt-in matrix
run; declarative dataclass per persona). v0.1.13 W-AK shipped
explicit `expected_actions` declarations on every persona file,
formalising expected behaviour as the per-persona ground-truth
shape.

No surveyed competitor ships persona-driven regression testing for
their decision layer at this scale.

### 5.6 Methodology contributions (new in v0.1.x)

- **D11 + D14 + D15 audit-cycle pattern.** Pre-PLAN bug-hunt +
  pre-cycle plan-audit + multi-round IR with empirically-validated
  settling shapes (10 → 5 → 3 → 0 plan-audit; 5 → 2 → 1-nit IR).
  This pattern is publishable prior art.
- **Two-LLM adversarial review discipline.** Maintainer-instructed
  non-collapse-toward-consensus posture between Claude (author)
  and Codex (reviewer).

---

## 6. What the maintainer learned about building solo at this rigor

Honest reflection. Naming what worked, what slipped, what's still
uncertain.

### What worked

**Audit-chain discipline as continuity infrastructure.** Eighteen
cycles of file-and-line evidence, structured Codex review, named
deferrals, and empirically-validated settling shapes mean that any
future maintainer (or AI session) can pick up the project cold and
reconstruct *why* every settled decision is settled. The
documentation discipline isn't bureaucracy; it's the
single-maintainer project's hedge against bus factor.

**Two-AI collaboration with a third human in the loop.** The
maintainer is the deciding human. Claude and Codex don't agree
unilaterally; they surface evidence, the human adjudicates. This
is the shape that scales — neither AI is forced to pretend
authority they don't have.

**Cancelling cycles when the empirical evidence wasn't there.**
Twice in v0.1.x, the maintainer cancelled a cycle rather than
fabricate evidence. v0.1.16 + v0.1.19 cancellations are the
strongest evidence that the project's discipline is real, not
performed.

**Velocity at rigor.** Ten cycles shipped in nine days
(v0.1.10–v0.1.18) without a single substantive release skipping
the four-round audit. The pattern doesn't slow shipping; it
clarifies it.

### What slipped

**The foreign-user gate slipped four times.** v0.1.14 → v0.1.15 →
v0.1.16 (cancelled) → v0.1.19 (cancelled). The gate was real, but
the criteria were over-specified. CP-2U-GATE-SPLIT (today)
formalises the lesson. **Cost: ~3 weeks of cycle-shape thrash.**
**Worth it:** the lesson now lives in AGENTS.md as D16.

**Some risks documented in v1's `risks_and_open_questions.md` were
already obsolete by the time the doc was authored.** R-T-03
("cli.py rot") had a trip-wire `wc -l > 10000`; v0.1.17 closed it
with a clean split before the trip-wire fired. The risks doc was
authored 2026-04-27; v1 of the strategic plan was authored the same
day; both reflect a snapshot of the project that was already
shifting.

**The strategic plan's refresh cadence rule (v1 §11) was overdue.**
v1 said "next refresh: post-v0.1.12 ship." v0.1.12 shipped
2026-04-29; the actual strategic refresh (this doc + v2) ships
2026-05-06, six cycles past the scheduled review. The cadence rule
worked as a tripwire — the maintainer noticed the drift before
v0.2.0 PLAN had to cite a stale strategic plan.

### What's still uncertain

**v0.5 N-of-1 substrate hasn't started.** The strongest claim the
project will ever make — that personal evidence accumulated over
≥90 days produces calibration data — depends on a substrate that
v0.1.x didn't begin. v0.2.0 W52 weekly review is the first piece
of substrate scaffolding. The estimator that reads it (v0.6) is
the project's central bet on H1.

**Foreign-user wearable-bearing + multi-day evidence is missing.**
The W-2U-WEARABLE + W-2U-DOGFOOD gates deferred to v0.4 review per
D16. The project hasn't yet had a non-maintainer use the full
pipeline daily for ≥7 consecutive days. That's the gap most
likely to surface unknown-unknowns.

**The MCP read-surface (Wave 3) hasn't been threat-modelled yet.**
W-MCP-THREAT scoped for v0.2.0 as a doc-only adjunct. Until that
artifact exists, the v0.3+ MCP design is constrained by what
hasn't been identified.

### What this maintainer demonstrated

Not for the maintainer's benefit. For an external reader of this
retro evaluating whether the project is what it claims to be.

- **Long-range technical thesis** with falsifiable bets stated up
  front (H1–H5; falsification criteria named per bet).
- **Audit discipline** that absorbs adversarial review without
  collapsing — twice-validated settling shapes, named residuals,
  cancellations rather than overclaim.
- **Taste for system boundaries** — code-vs-skill, agent-vs-runtime,
  install-vs-wearable-vs-dogfood gate splits.
- **Capacity to coordinate two AI agents and synthesise results**
  while keeping decision authority human. Eighteen cycles of
  Claude-Codex disagreement without consensus collapse.
- **Willingness to cancel cycles, retire claims, and restructure
  scope** rather than ship synthetic evidence.

These are the discipline elements. The project is a demonstration
that they hold under volume.

---

## 7. What this means for the next phase

v0.1.x shipped the **trust-the-runtime** phase. v0.2+ ships the
**trust-the-runtime-across-time** phase: weekly reviews, insight
ledgers, factuality gates, eventual N-of-1 substrate.

The v0.1.x methodology contributions are durable. The audit-cycle
pattern doesn't change between v0.1 and v0.2. The persona matrix
expands but doesn't restructure. The capabilities manifest schema
freezes at v0.2.3 but the contract shape stays.

**What does change:** v0.2+ work increasingly depends on
accumulated calendar time (≥90d substrate gates from v0.5 and v0.7
onward). Velocity at rigor isn't the constraint anymore;
calendar-driven evidence accumulation is.

The v0.1.x retro is therefore the high-velocity portion of the
project's life. v0.2-v0.4 will ship at similar discipline but
slower cadence; v0.5-v0.6 will be substrate-driven; v0.7-v1.0 will
be stability-proof-driven. The shape changes; the discipline doesn't.

**The five lessons in §3 are the durable contribution.** They
generalise to any project building software an LLM agent will
drive at production rigor.

---

*Authored: 2026-05-06 by Claude in extended planning session.
Companion to `strategic_plan_v2.md`. Not subject to refresh
cadence — this is a snapshot of the v0.1.x track at its close.
Future tracks (v0.2.x retro, v0.3.x retro, etc.) author their own.*
