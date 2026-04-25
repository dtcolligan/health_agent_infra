# v0.1.7 — Report: where the project actually is, and what would move it most

> **Provenance.** Authored at the close of the v0.1.6 cycle (3 audit
> rounds + a 13-workstream implementation pass + Codex r3 must-fix
> follow-ups). v0.1.6 took the project from "shipped but with
> structural bugs the architecture overstated" to "the architecture
> claims the runtime actually enforces." This report is the
> maintainer-internal read of *what's still weakest* before drafting
> the v0.1.7 implementation plan.
>
> Companion: `PLAN.md` (the implementation plan) and
> `codex_audit_prompt.md` (the brief sent to Codex for review).

---

## 1. Where the project is right now (post v0.1.6)

### Shipping today (the strong parts)

- **Three real determinism boundaries** — `hai propose`,
  `hai synthesize`, `hai review record` — each with a code-enforced
  validator emitting named invariants. The audit chain across JSONL
  + SQLite is internally consistent.
- **An honest proposal-completeness gate** in `hai daily` — three
  statuses (`awaiting_proposals` / `incomplete` / `complete`); no
  more silent "1-of-N plan committed as complete."
- **No uncaught Python tracebacks from CLI surfaces** — every
  `--*-json` arg goes through `_load_json_arg`; `main()` catches
  unexpected exceptions and returns `INTERNAL`.
- **Clean local-first defaults** — `--base-dir` optional with
  `~/.health_agent` default; intervals.icu is the implicit pull
  source when configured.
- **Skill ↔ CLI drift validator** wired into CI; intent-router +
  reporting + expert-explainer + daily-plan-synthesis skills are
  all in sync with the actual parser surface.
- **Bounded local-only research surface** — `hai research topics` /
  `hai research search`; `expert-explainer` no longer has
  `Bash(python3 -c *)` as a privacy back door.
- **Schema-version gap detection** in `hai doctor` — catches DBs
  that look current by `MAX(version)` but miss lower migrations.
- **Test count: 1921 passing, 4 skipped, 0 locking broken
  behaviour.**

### Not shipping yet (the real gaps)

These are the structural weaknesses I see going into v0.1.7. Some
are deferred items from v0.1.6's plan; others are bigger ideas the
audit cycle surfaced but didn't action.

**A. Agent flow is documented end-to-end, but not orchestrated
end-to-end.** A Claude Code agent has to invoke ~10 commands to
plan a single day: `hai daily` → 6 per-domain skill calls → 6
`hai propose --domain <d>` → `hai daily` again → narrate via
`reporting`. Each step is correct in isolation; the whole loop is
heavy. The agent (and the user) carry the orchestration burden.

**B. v0.1.6 isn't on PyPI.** Everything we shipped lives in one
checkout. There is no way for a third party to `pipx install
health-agent-infra` and get the v0.1.6 surface. The release tag is
preparation for distribution, but distribution itself hasn't
happened.

**C. The agent-driven contract is implicit.** `hai daily` emits a
status + hint. The agent has to know to read `stages.gaps`, then
`stages.proposal_gate.missing`, then post per-domain proposals,
then re-run. There's no single "next action" the agent can route
on without composing several reads. An agent built on the SDK from
scratch has to re-implement the orchestration discipline the
intent-router skill encodes in prose.

**D. `hai stats` is shallow.** It reports last-sync timestamps and
a basic streak. There's no per-domain engagement signal, no
proposal-gate funnel, no review-outcome rate. Operators tuning the
runtime can't see what's working without ad-hoc SQL.

**E. Synthesis quality is not evaluated end-to-end.** The
calibration timeline says "day 90 = steady state," but there's no
fixture-based eval that simulates 90 days of inputs and asserts
the calibration claim. The skill-eval blocker note (still open
from v0.1.5) points at this.

**F. Cold-start asymmetry is documented but not designed.** Three
of six domains have a `cold_start_relaxation` rule; three don't.
v0.1.6 documented the asymmetry but didn't decide whether it's a
final design or an interim state. A per-domain decision matrix is
deferred from v0.1.6 (W14 deep).

**G. Determinism claims are partially structural.** Reproject is
"deterministic modulo projection timestamps." But there's no test
asserting two reproject runs against identical JSONL produce the
same SQLite content (excluding the named volatile columns).

**H. Synthesis-skill `allowed-tools` may block its own examples.**
Codex r2 flagged this; r3 disagreed-with-deferral if the two-pass
overlay is meant to be advertised in v0.1.6. The flag-pattern
matching semantics are unverified. Could be silently broken.

**I. `cli.py` is 6300+ lines.** Scanning it during the v0.1.6 work
showed the maintainability cost: argparse + handlers + helpers all
co-located. A per-command split would make future audits cheaper.

**J. There's no public API stability surface.** `__all__` is
disciplined in some modules and not others; nothing tests that the
exported surface doesn't change unintentionally between releases.

**K. No way to evaluate the agent's behaviour against a fixture
day.** A `hai eval` command exists, but it's deterministic-runtime
only. The agent's choices (which skill to invoke, which intake to
request, how to narrate) aren't part of the evaluation surface.

---

## 2. Maintainer's success criteria (read from behaviour)

Dom hasn't enumerated explicit success criteria. Inferring from the
last 24 hours' worth of conversation + the project artifacts:

- **The agent flow is the product.** Without the Claude Code agent
  driving it, the runtime is just a CLI. The success metric is "Dom
  can talk to his health agent and get useful answers." We hit that
  this morning.
- **Local-first, auditable, governed.** Every claim must be
  reconstructible from on-device JSONL + SQLite. No telemetry, no
  cloud, no opaque ML.
- **Honest about what it knows.** Defer over guess; cite over
  improvise; refuse over fork the audit chain.
- **AI for health.** This is a personal project that builds toward a
  credible artifact in the AI-for-health space (per Dom's
  global CLAUDE.md). The trajectory matters as much as the surface
  area.

What's NOT a success metric (per the non-goals doc + observed
preferences):
- Multi-user / cloud sync.
- Meal-level nutrition (macros only).
- Production-grade scale.
- Rich web UI.

---

## 3. Where v0.1.7 should aim

Two complementary investments. The maintainer should pick which
one to lead with; the other is a follow-on.

### Investment A — "First-class agent flow"

Make the agent's job easier by collapsing the orchestration
overhead. Concretely:

- **`hai daily --auto`** mode that, instead of stopping at the
  proposal gate, emits a denser `next_actions` payload the agent
  can route on without composing six reads.
- **`hai stats --funnel`** showing the agent's actual usage:
  how many days hit `incomplete` vs `complete`, per-domain
  proposal latency, review-outcome rate.
- **Proper PyPI release of 0.1.6** so anyone can `pipx install`
  and get the same surface.
- **Skill-eval harness completion** — close the
  `safety/evals/skill_harness_blocker.md` work so the per-domain
  skills can be scored against a fixture corpus instead of relying
  on operator-driven live transcripts.

### Investment B — "Calibrated correctness"

Tighten the audit chain + fill the structural gaps Codex r2/r3
surfaced.

- **Property-based tests for projectors** — same JSONL inputs →
  same SQLite content (modulo the documented volatile columns).
- **`hai state migrate` refuses on a gappy DB** (deferred from
  v0.1.6 W20).
- **Synthesis-skill `allowed-tools`** order-sensitivity test +
  fix.
- **Cold-start matrix decision** — extend `cold_start_relaxation`
  to all 6 domains with documented per-domain semantics, OR commit
  to the asymmetry with a written rationale + tests pinning the
  per-domain behaviour.
- **Determinism eval** — synthesise a fixture day 100 times,
  assert identical output (excluding timestamps).
- **Public API stability test** — declare `__all__` everywhere,
  add a test that the exported surface matches a checked-in
  snapshot.

### Investment C (lower priority but worth naming)

- **`cli.py` split** — into `cli/<command>.py` modules with a
  thin top-level `cli.py` that wires argparse. ~1 day of work,
  immediate maintainability win.
- **Per-meal nutrition prototype** — explicitly a non-goal in v1
  per `non_goals.md`, but worth re-evaluating now that the
  structural fixes are in.
- **MCP server** — wrap the agent-safe surface as MCP so non-Claude
  agents can drive it. Currently in the roadmap; v0.1.7 could
  scaffold without committing.

---

## 4. The proposal: lead with A, fold in the deferred-from-0.1.6 items

v0.1.7 should ship Investment A in full + the must-do P2 follow-ups
from v0.1.6 (W14 deep, W16, schema-gap migrate gate, cmd_propose
race-path test). Investment B's bigger items (property-based tests,
determinism eval) and Investment C's items go to v0.1.8+ unless
Codex argues otherwise.

The full workstream list lives in `PLAN.md`. This report establishes
the WHY; the plan describes the HOW.
