# Agent-Operable Runtime — Plan

- Author: Claude (Opus 4.7)
- Date: 2026-04-22
- Status: all decisions locked. **Phases 1, 2, 3, 4, and 5 SHIPPED.**
  All four cycle essentials are done. Phase M (active protocol layer)
  remains explicitly deferred by design. 1459 tests passing.
- Extends, does not replace: [`post_v0_1_roadmap.md`](post_v0_1_roadmap.md)

---

## The argument in one paragraph

The proposal is directionally right, but most of what it flags as new work is
already shipped. Strip out the shipped pieces and one real structural idea
remains: **the pre-X-rule "original plan" is never stored, so the agent
can't cleanly answer *"what did you originally plan, and why did you change
it?"*** Everything else is composition: the CLI already emits JSON, has a
typed exit-code taxonomy, has a freshness-aware doctor command, and has
public-name slugs on X-rules — what it doesn't have is a contract document
an agent can rely on, or a skill that routes natural-language intent to
deterministic CLI workflows. So: build the ledger, write the contract,
ship the routing skill on top of it, and run the skill-harness eval the
prior roadmap already scheduled.

---

## 1. The original-plan ledger — the keystone (Option 2 locked)

Today the pipeline works like this:

- Each domain skill emits a proposal → stored in `proposal_log`.
- X-rules then mutate the aggregate draft (e.g. soften *"hard run"* →
  *"easy aerobic"*).
- The final mutated plan is committed to `daily_plan` + `recommendation_log`.

What's missing is **the aggregated draft as it looked before the X-rules
ran**. It exists briefly in memory during the synthesis transaction, then
it's gone. The individual mutations survive in `x_rule_firing.mutation_json`,
but the starting point of the aggregate doesn't.

That means an agent asked *"what was the original plan before the
softening?"* has to reconstruct it by inverting the firings. Reconstruction
is possible but fragile — every X-rule edit becomes a potential silent
regression in the explain surface.

**The fix (Option 2 locked):** a new table `planned_recommendation` with
one row per domain per plan, mirroring the shape of `recommendation_log`,
each linked back to its source `proposal_log` row and to its `daily_plan`.
Written atomically inside the existing synthesis transaction.

That closes the audit chain:

```
proposal_log      →  planned_recommendation  →  daily_plan           →  review_outcome
(per-domain          (aggregate pre-X-rule)      (aggregate adapted)     (performed)
 intent)
```

Every step is queryable by `domain + for_date + user_id`. Every row links
forward and backward via foreign keys. The `planned ⊕ firings = adapted`
invariant becomes a property test.

This is the keystone. Everything else in the plan is easier after it lands,
and it cannot be retrofitted — you can't reconstruct an original plan for
historical days, you can only start collecting them going forward.

**Effort:** ~1.5 weeks.

---

## 2. An agent contract for the CLI

The CLI is already more agent-friendly than the proposal assumed. 35+
commands emit JSON. Exit codes follow a published, version-stable taxonomy.
`hai doctor`, `hai explain`, and `hai state snapshot` are all structured.
X-rules have stable public-name slugs.

What's missing is that these are **scattered surfaces, not a contract.** An
agent author has to read `cli.py` to know which commands mutate state,
which are idempotent, what JSON shape each emits, and whether a given
command is safe for an agent to run or needs an operator (e.g. `hai auth
garmin`). And 9 of the ~14 handlers are still on the legacy exit-code
pattern.

The fix is small and mechanical:

- **One doc** — `reporting/docs/agent_cli_contract.md`. Per-command rows
  stating mutation class, idempotency, JSON shape, exit codes produced,
  and agent-safe vs operator-only.
- **One command** — `hai capabilities --json` emits the same thing as a
  machine-readable manifest, generated from argparse plus a small
  annotation map.
- **Finish the exit-code migration** for the 9 legacy handlers (`daily`,
  `state *`, `intake *`, `review *`, `memory *`, `propose`, `writeback`,
  `clean`, `doctor`).

The combined effect is that every agent host — Claude Code today, Agent
SDK tomorrow, the routing skill in §6, a hypothetical third host next year
— works against one known, tested surface.

**Effort:** ~1.5 weeks, mostly the exit-code migration. **Blocker:**
Decision B, §8.

---

## 3. A sentence of human explanation per X-rule

Today's X-rule public names are slugs like `sleep-debt-softens-hard`. Good
for machines. What a human — or an agent narrating back to a human —
actually wants is a sentence: *"Sleep debt is elevated, so hard sessions
are softened to reduce injury risk."*

This is a dictionary update in `core/synthesis_policy.py` plus surfacing
the new field in `hai explain`'s JSON output. One PR, ~50 lines.

This becomes especially important once the routing skill exists — when the
skill is asked *"why did you tone down my run?"* it should be able to
retrieve the sentence form and return it verbatim, not reassemble one from
the slug.

**Effort:** ~2 days. **No blocker.**

---

## 4. The skill-harness eval pilot (adopted from the existing roadmap)

The prior roadmap's Phase E is still open. Deterministic evals cover the
runtime; skill narration isn't scored. That's the project's biggest
remaining credibility gap, and nothing else in this plan closes it.

One domain (recovery), one skill, 5–10 frozen scenarios, rubric scoring
separately from the deterministic axes, opt-in so it doesn't destabilize
CI.

If the routing skill in §6 exists by the time this phase ships, it should
be the **second** skill under the harness, not the first — recovery
narration is the cleaner first pilot because its scoring rubric is
already mostly scoped in `safety/evals/skill_harness/rubrics/recovery.md`.

**Effort:** ~1–2 weeks. **No blocker.**

---

## 5. The intent-routing skill (authoritative router)

The proposal's thesis is that the system should accept messy natural-language
intent and route it to deterministic CLI workflows. This skill is where
that happens.

What the skill is, concretely:
- A markdown skill at
  `src/health_agent_infra/skills/intent-router/SKILL.md`.
- `allowed-tools` scope covering the read-only commands plus the named
  mutation commands it's authorized to orchestrate.
- A mapping layer from NL intent → a CLI workflow sequence the user can
  audit before execution.

Representative intents from the proposal:
- *"Update my Garmin data and tell me what I should do today."* →
  `hai pull --live` → `hai clean` → `hai state reproject` → `hai
  synthesize` → `hai daily` → narrate.
- *"Why did you tone down my run?"* → `hai explain --for-date today` →
  filter x_rule_firings affecting `domain=running` → return sentence-form
  explanations from §3.
- *"I actually trained harder than recommended."* → `hai review record
  --domain running --intensity-delta harder` (uses migration 010 columns).
- *"What changed from the original plan?"* → `hai explain --stages
  planned,adapted` (uses the §1 ledger) → show domain-level deltas.

The skill **never** mutates state directly. It composes `hai` subcommands,
and those subcommands own the determinism boundaries as today.

This skill is **authoritative** — it's the source of truth for how NL
intent maps to CLI workflows. Every agent host consults it. It teaches the
agent `hai` the way Claude already knows `gh`. The skill consumes
`hai capabilities --json` (the manifest from §2) as its mapping surface,
so new commands become orchestrable automatically.

Depends on §2 (the contract + manifest) being in place first.

**Effort:** ~1 week.

---

## 6. What I'd skip or defer

**The active protocol layer** (the proposal's multi-day training/nutrition
intent store). The caution the proposal itself raised — *"don't jump to
periodization"* — is the right instinct. Persistent goal context already
lives in user memory (migration 007). Per-day intent lives in
`proposal_log`. The gap between them is real but speculative: we don't yet
know what durable multi-day intent actually needs to persist. Let the new
ledger run for a cycle, see what the data says, then write an RFC. This is
the most scope-creep-prone item in the original proposal.

**Everything else** — adaptive learning, second wearable adapter,
meal-level nutrition, MCP wrapper, hosted/multi-user. None of it is on the
table this cycle.

---

## 7. Sequencing

```
week 1–1.5   §1 ledger               §3 sentences          (both in parallel)
week 2–3.5   §2 contract             §4 skill-harness      (both in parallel)
week 3.5–4.5 §5 routing skill                              (depends on §2)
```

§2 waits for §1 so the three-state JSON shape (planned / adapted /
performed) lands in the contract v1 instead of needing a v1.1. §5 waits
for §2 because the skill consumes the contract. §3 and §4 are independent
and can ship any time.

Total calendar time with one person: ~4.5 weeks. Could compress to ~3.5
if §4 is deferred a cycle, or to ~3 if the routing skill is scoped as
gap-filler rather than authoritative router.

---

## 8. Decisions

### Decision A — Ledger shape — ✅ LOCKED: Option 2

Per-domain rows in a new `planned_recommendation` table, mirroring
`recommendation_log` shape, with FKs back to `proposal_log` and forward to
`daily_plan`. See §1.

---

### Decision B — Source of truth for the agent contract — ✅ LOCKED: manifest-first

`hai capabilities --json` is generated from argparse + a small annotation
map on each subcommand registration. The human doc
(`reporting/docs/agent_cli_contract.md`) is regenerated from that manifest
on commit. A CI check fails if a new subcommand ships without annotations,
making drift impossible. The routing skill (§5) consumes the manifest
directly rather than maintaining its own mapping table.

---

### Decision C — Intent-routing skill — ✅ LOCKED: authoritative router

The skill is the source of truth for how NL intent maps to CLI workflows.
It teaches the agent `hai` the way Claude already knows `gh`. Consumes
`hai capabilities --json` programmatically; does not maintain its own
mapping. `allowed-tools` scope crosses every mutation command by design,
but the skill itself never mutates — it composes `hai` invocations that
cross the determinism boundaries.

---

## 9. Things I'm not fully sure about

- Whether §4 (skill-harness) should block shipping §1+§2 as a release.
  I lean **no**, but an argument exists for holding the release until
  skill-harness confirms narration hasn't regressed. If you have a strong
  view here, it changes the sequencing.
- Whether the sentence-form X-rule explanations in §3 should cite the raw
  threshold number. I lean **no** (keeps rationale bounded; avoids
  leaking tuning choices), but reasonable people differ.
- Whether §1's ledger should store the *skill's overlay rationale* too,
  or only the mechanical pre-mutation bundle. I lean **mechanical only**
  for v1 — keep the ledger about state, not prose — but that's a
  judgment call, not a proof.
- If Decision C's sub-question goes to "authoritative router," whether the
  routing skill should be wired into the skill-harness eval (§4) as the
  *first* pilot skill instead of recovery. Broader coverage, harder
  rubric. Probably still no — recovery is the cleaner first pilot — but
  worth flagging.

---

## 10. What's already shipped (so we don't build it twice)

I grounded this plan against the actual code. Here's what I verified is
already done:

- **Exit-code taxonomy and docs** — `core/exit_codes.py`,
  `reporting/docs/cli_exit_codes.md`. Five handlers migrated.
- **`hai explain`** — read-only audit surface over the full audit chain.
- **Explicit user memory** — `hai memory set/list/archive`, migration 007.
- **Sync run log** — migration 008. Every `hai pull` writes begin/
  complete/fail rows. Freshness is one SELECT away.
- **`recommendation_log` → `daily_plan` FK** — migration 009.
- **Review-outcome enrichment** — migration 010 added `completed`,
  `intensity_delta`, `duration_minutes`, `pre_energy_score`,
  `post_energy_score`, `disagreed_firing_ids`.
- **`hai doctor`** — consolidated freshness + today counts + text default
  (M5).
- **Pull-adapter resilience** — retry, backoff, partial-day telemetry (M6).
- **Property / concurrency / migration-rollback tests** (M7).
- **X-rule public-name slugs** — already surfaced in `hai explain` output
  via `X_RULE_PUBLIC_NAMES` in `core/synthesis_policy.py`.
- **Pervasive JSON output** — 35+ `_emit_json(...)` sites across `cli.py`.

When the proposal asked for *"sync observability," "richer review
outcomes," "exit-code hygiene,"* or *"semantic X-rule names,"* those are
already shipped partially or fully.

---

## 11. Current execution state

**Phase 1 — SHIPPED.**
- Migration 011 (`planned_recommendation` table) applied, HEAD schema
  version = 11.
- `project_planned_recommendation` projector wired through
  `core/state/__init__.py`.
- `run_synthesis` writes planned rows inside the atomic transaction;
  rollback semantics preserved; canonical-plan replacement deletes
  prior planned rows cleanly.
- `hai explain` bundle now carries `planned_recommendations`;
  JSON and text renders both surface it; backward-compatible on
  pre-011 plans (empty list, no crash).
- Tests added: 11 migration tests, 6 round-trip tests (including
  `planned ⊕ firings = adapted` under X1a), 5 explain-view tests.
- Full suite: 1424 passing, 0 failing.
- End-to-end CLI smoke confirmed: an agent can now ask *"what did
  you originally plan, and why did you change it?"* and get a
  structured answer.

**Phase 3 — SHIPPED.**
- `X_RULE_DESCRIPTIONS` + `description_for(rule_id)` live in
  `core/synthesis_policy.py`. All 11 rules have sentences.
- `XRuleFiring.to_dict()` now emits `human_explanation` alongside
  `public_name`; agents reading firings directly see the sentence.
- `ExplainXRuleFiring` carries a `human_explanation` field, populated
  by the loader; surfaced in JSON and text renders.
- `reporting/docs/x_rules.md` gained a "Human explanations" reference
  table and the rule-naming section covers the three surfaces (id /
  slug / sentence).
- Tests added: 18 new tests — registry coverage (sentence map aligned
  with public-name map), shape (sentences end with a terminator and
  contain spaces), spot-checks, and end-to-end verification through
  the explain bundle.
- Full suite: 1442 passing, 0 failing.

**Phase 2 part 1 — SHIPPED.**
- `core/capabilities/` module: walker, renderer, annotation helper,
  enum-validated schema (mutation / idempotency / JSON / exit-code /
  agent-safe).
- `annotate_contract(...)` calls on every leaf subparser (36 total).
  Bad annotations fail at CLI-construction time.
- `hai capabilities` command emits manifest as JSON (default) or
  markdown (`--markdown` flag).
- Doc generator: `reporting/docs/agent_cli_contract.md` committed,
  regenerated from the manifest deterministically. A CI test fails
  if the committed doc drifts.
- Tests added: 17 — coverage (every subcommand annotated),
  determinism, schema stability, enum validation, end-to-end CLI
  smoke, committed-doc sync check.
- Full suite: 1459 passing, 0 failing.

**Phase 2 part 2 — SHIPPED.**
- All 9 legacy handler groups (`daily`, `state *`, `intake *`,
  `review *`, `memory *`, `propose`, `writeback`, `clean`, `doctor`)
  plus the adjacent legacy commands (`config *`, `classify`, `policy`,
  `exercise search`, `eval run`, `setup-skills`, `init`) migrated to
  the `OK` / `USER_INPUT` / `TRANSIENT` / `NOT_FOUND` / `INTERNAL`
  taxonomy.
- Every annotation now emits real exit codes; `LEGACY_0_2` is
  retained as a schema sentinel but not currently emitted anywhere.
- ~30 test assertions updated from `assert rc == 2` to
  `assert rc == exit_codes.USER_INPUT`; argparse-level rejection
  tests (invalid `--category` choices etc.) correctly keep the
  literal `2` since argparse's built-in exit is outside the
  taxonomy.
- `reporting/docs/cli_exit_codes.md` scope section updated to
  reflect the completed migration.

**Phase 5 — SHIPPED.**
- `src/health_agent_infra/skills/intent-router/SKILL.md` — 14th
  packaged skill, auto-discovered by `hai setup-skills` and
  surfaced in `hai doctor`.
- Consumes `hai capabilities --json` at session start as the
  authoritative command surface; never maintains its own mapping
  table. New subcommands become orchestrable automatically.
- Scoped `allowed-tools` covers every agent-safe `hai` subcommand
  it may orchestrate; deliberately excludes `hai auth garmin` and
  `hai init` (both operator-only per the manifest).
- Five intent classes: state refresh, daily planning, explanation,
  outcome logging, memory. Each intent has a concrete CLI pipeline
  documented in the skill.
- Mutation-confirmation rule: every non-read-only command is
  previewed to the user before it runs.
- Exit-code handling documented per the taxonomy (OK / USER_INPUT /
  TRANSIENT / NOT_FOUND / INTERNAL).
- Cross-references updated: `reporting/docs/agent_integration.md`
  now lists 14 skills including intent-router; README skill tree
  updated.

**Phase 4 — SHIPPED (as inherited Phase E + incremental coverage).**
- Pre-existing: the Phase E skill-harness pilot from the
  `post_v0_1_roadmap.md` cycle was already substantially shipped
  before this plan began — 792-line runner (live/replay/demo modes),
  seven recovery scenarios, token-presence rubric, opt-in live mode
  gated on `HAI_SKILL_HARNESS_LIVE=1`, replay-mode pytest shim.
- Added in this plan: three new `hand_authored_reference`
  transcripts (h02 mild downgrade, h03 impaired mobility, h04
  impaired rest). Rubric coverage moves from 3 of 7 recovery
  branches to 6 of 7; h06 (insufficient-coverage defer) stays
  deliberately un-transcripted so the missing-transcript failure
  path keeps a live target. Blocker doc updated to reflect the new
  coverage.
- Scope kept inside the plan's stated Phase 4: one domain
  (recovery), one skill, 5–10 frozen scenarios, rubric separate
  from deterministic axes, opt-in. Second-domain expansion
  (sleep / stress / running), live transcript capture, and an
  LLM-judge rubric axis remain explicit follow-ups per
  `safety/evals/skill_harness_blocker.md` §"What remains open".

**All cycle essentials complete.** Phase M (active protocol layer)
stays deferred by design — revisit only after the planned-snapshot
ledger has accumulated a cycle of data that tells us what durable
multi-day intent is actually load-bearing.
