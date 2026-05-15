# Codex External Audit — health-agent-infra (post v0.1.5)

> **How to use this prompt.** Paste it into Codex (or a similarly-capable
> code-aware model) with file-reading access to this repo. The output
> will be folded back into the v0.1.6 plan in
> `reporting/plans/v0_1_6/PLAN.md`. Keep the audit response in the same
> structure the prompt asks for so it can be diffed against the plan.

---

## Role

You are a senior systems engineer performing an **external audit** of a
local-first agent runtime. You have not seen this repo before. Your job
is to read the codebase, validate the empirical findings listed below,
find issues the maintainer missed, and produce a structured prioritised
report.

You are not implementing fixes. You are producing a report the
maintainer + the in-repo Claude agent will use to drive the v0.1.6
release.

## Project context

`health-agent-infra` (CLI: `hai`) is a **governed local agent runtime
for personal health data**. A Claude Code agent reads the user's own
Garmin / intervals.icu data, emits per-domain proposals bounded by
codified rules, and commits auditable recommendations the user reviews
the next day. Everything stays on-device in a local SQLite file.

**Architectural invariant — code-vs-skill boundary:**

- **Python (code-owned)** does the mechanical decisions: classification
  bands, R-rules / X-rules, transactional commits, projector logic,
  contract validation. No prose.
- **Markdown skills (judgment-owned)** do the rationale, uncertainty
  narration, and per-domain action selection inside a bounded enum. No
  arithmetic, no state mutation.
- **Three determinism boundaries** the runtime refuses at: `hai propose`
  (validates DomainProposal), `hai synthesize` (transactional plan
  commit), `hai review record` (typed outcome).
- Skills must never compute a band, score, or ratio. Code must never
  write prose.

**Six domains in v1:** recovery · running · sleep · stress · strength ·
nutrition. Nutrition is macros-only by design (see
`reporting/docs/non_goals.md`).

**Current version:** v0.1.5 just released (notes in
`reporting/plans/v0_1_4/release_notes.md`). v0.1.6 is the upcoming
release this audit informs.

**Where to start reading:**

- `README.md` — user-facing overview.
- `src/health_agent_infra/cli.py` — argparse tree; every subcommand
  lives here. Search `add_parser` for the surface.
- `src/health_agent_infra/core/state/` — projectors, snapshot builder,
  store. `store.py:DEFAULT_DB_PATH` is the canonical state-DB location.
- `src/health_agent_infra/domains/<d>/{classify.py, policy.py}` — per-
  domain classification bands and R-rules. Six domains; same shape.
- `src/health_agent_infra/skills/` — markdown skills installed to
  `~/.claude/skills/`. Per-domain readiness skills + intent-router +
  reporting + merge-human-inputs.
- `src/health_agent_infra/core/writeback/proposal.py` — the
  determinism boundary for `hai propose`.
- `reporting/docs/architecture.md` — the canonical pipeline + boundary
  doc.
- `reporting/docs/agent_integration.md` — the Claude Code / Agent SDK
  integration contract.
- `reporting/docs/agent_cli_contract.md` — markdown mirror of
  `hai capabilities --json`.
- `reporting/plans/v0_1_4/` — the just-shipped release's plan,
  acceptance criteria, codex handoff. Use this as the convention
  template for what plan docs look like.
- `reporting/plans/v0_1_6/PLAN.md` — the in-flight plan this audit
  augments.

## What just happened (empirical findings from a real end-to-end session)

A maintainer used the agent live for a full day on 2026-04-25 (in user
mode, not builder mode). The session did the full loop: narrate
yesterday's plan → log a strength session → record review outcome →
log nutrition → fill gaps for the prior day → generate today's plan
(synthesise across all 6 domains) → narrate today's plan. Eight items
came out the other side. Treat each as a hypothesis to validate, not a
verdict.

### Validated bugs (reproduced in-session, fixes warranted)

1. **`hai state reproject` crashes with FK constraint failure.**
   `sqlite3.IntegrityError: FOREIGN KEY constraint failed` raised at
   `core/state/projector.py:1258` on `DELETE FROM proposal_log`.
   `proposal_log` has children (`planned_recommendation` per
   `migrations/011_planned_recommendation.sql`) that aren't cascaded
   before the delete. Confirm the FK shape, propose the right fix
   (cascade, ordered deletes, or refusing-cleanly-with-opt-in-flag).

2. **`hai intake gaps` returns a misleading `gap_count=0` when called
   without `--evidence-json`.** The schema description says "gaps
   cannot be computed" but the JSON response carries
   `{"gap_count": 0, "gaps": []}` indistinguishable from a true zero.
   An agent or downstream caller that trusts the zero will silently do
   the wrong thing. Recommend: either error out (USER_INPUT) or add a
   `"computed": false` field to the response.

3. **`hai daily` does not actually complete the loop on its own.** It
   pulls / cleans / snapshots / detects gaps / and stops at
   `awaiting_proposals`. The agent must invoke 6 per-domain skills,
   post 6 proposals via `hai propose`, then call `hai synthesize`. The
   README's Install block (`hai daily` as one-liner) and the
   description on `hai daily` itself ("orchestrate") read as if it's
   end-to-end. Either the docs are wrong, the orchestration is missing
   a "skill-driven proposal" step, or there's an unwired auto-propose
   path. Investigate and recommend.

4. **Schema drift between intent-router skill docs and `hai review
   record` CLI.** Skill says `--completed 0|1` and per-flag fields
   work. Actual CLI takes `--completed yes|no` and requires
   `--outcome-json`. Probably analogous drift in other skills.
   Systematic check: does any other intake/agent surface have skill
   docs that diverge from the actual argparse?

### Validated friction (UX-level, README-worthy)

5. **Garmin live pull is unreliable.** Today's first `hai pull --live`
   got 429s from mobile + portal + Cloudflare in succession. We
   pivoted to `--source intervals_icu` and that worked. The README's
   Install block doesn't warn. The maintainer wants intervals.icu to
   be the default supported path going forward.

6. **`hai intake nutrition` is a daily total, not per-meal, and is not
   idempotent.** Calling it twice creates a supersede chain. We
   handled this in-session with a context note as a scratchpad until
   end-of-day. README/docs don't make this clear.

7. **Every `hai intake *` requires `--base-dir`.** New users hit this
   immediately. Worth a one-line callout in Install OR a sensible
   default that resolves like state-db does (`$HAI_BASE_DIR` env var
   or `~/.health_agent`).

8. **The `planned_session_type` string vocabulary isn't documented.**
   Free text per the merge-human-inputs skill, but downstream
   classifiers may treat unrecognised strings differently. Today's
   session used `strength_back_biceps` (composed by the agent) — fine
   for narration, but unclear whether it satisfies any downstream
   pattern match. The strength domain escalated today; partly cold-
   start, possibly partly the unrecognised session string.

### Calibration insight (informational)

9. The maintainer drafted (mid-session) a **"Calibration timeline"
   section for the README** tabulating which day-windows correspond
   to which signals being calibrated. Code-derived markers cite the
   file (`history_days < 14` in `domains/{running,strength,stress}/policy.py`,
   28-day ACWR window in `domains/running/classify.py`, 28-day strength
   `volume_ratio` in `domains/strength/classify.py`); reasoned markers
   (Day 60+, ~Day 90) extrapolate from "trend bands need ≥2 cycles."
   Validate: are the day numbers correct? Are there other threshold
   constants that should be cited? Is the framing accurate?

## Audit scope — what we want from you

Read the repo. Validate or refute each of the nine items above. Then,
with the codebase open in front of you, find the things the maintainer
*didn't* notice. Specifically:

### Mandatory checks

A. **Determinism-boundary integrity.** Re-read `hai propose`,
   `hai synthesize`, `hai review record` validators. Are the
   invariants actually enforced? Any way an agent could write garbage
   that slips through? Any precondition the validator silently skips?

B. **Skill-vs-code boundary drift.** Walk every skill in
   `src/health_agent_infra/skills/`. For each, list any place the
   skill's documented behaviour diverges from what the CLI accepts /
   the runtime computes. Schema drift like (4) above is the smell.

C. **Cold-start correctness.** The 14-day cutoff in
   `domains/{running,strength,stress}/policy.py` —
    is it consistent across the three domains? Are sleep, recovery,
    nutrition cold-start-aware in equivalent ways or do they have
    silent differences? Today's strength `volume_spike_detected`
    escalation on day 2 is mechanically expected — but is the
    `cold_start_relaxation` rule applied symmetrically?

D. **Reproject correctness.** Beyond the FK bug (1), is the projector
   actually deterministic? Same JSONL inputs → same accepted_state
   tables, every time? Any non-determinism (dict ordering, timestamp
   reads, RNG)?

E. **Migration safety.** Latest schema_version is 18 (per `hai
   doctor`). Walk recent migrations in
   `src/health_agent_infra/core/state/migrations/`. Any reversibility
   issues, any data-loss risk, any forward-compat assumptions that
   break with intervening unreleased migrations?

F. **Test coverage of the just-validated paths.** Do the 8 issues
   above have tests that should have caught them? If not, where
   should the tests live? (Don't write the tests; just locate the
   gaps.)

### Open exploration (find what we missed)

G. **Architecture review.** Anti-patterns, missing abstractions,
   premature ones, places where the code-vs-skill boundary blurs.

H. **CLI surface ergonomics.** `hai capabilities --json` is the
   contract. Are there commands that should be agent-safe but
   aren't, or vice versa? Inconsistencies in flag naming /
   semantics across the surface (e.g. `--as-of` vs `--for-date`)?

I. **Roadmap candidates.** With the v0.1.5 release behind, what's
   the highest-leverage next investment? If you saw this codebase
   for the first time, what would you build into v0.1.6 that the
   maintainer hasn't proposed?

### Non-goals — explicitly do NOT spend audit cycles on

- Rewriting README marketing copy.
- Cosmetic refactors with no behavioural impact.
- Renaming things without a structural reason.
- Adding lint configurations.
- Performance micro-optimisations on paths that aren't hot.
- Multi-user / cloud-sync / meal-level nutrition — explicit non-goals
  per `reporting/docs/non_goals.md`.

## Output format

Return a single Markdown document with this structure. Be ruthlessly
prioritised. If a section has no findings, write "No findings" — do not
pad.

```markdown
# Codex Audit — health-agent-infra v0.1.5 → v0.1.6

## Executive summary
<5–10 lines: top-3 issues by severity, top-1 architectural concern,
top-1 roadmap recommendation.>

## Findings — validated bugs
For each: status (CONFIRMED / NOT_REPRODUCED / PARTIALLY_CONFIRMED /
DEFERRED — DIDN'T_INVESTIGATE), evidence (file:line), recommended fix
(1–3 sentences), effort estimate (S/M/L), risk if unfixed (LOW / MED /
HIGH / RELEASE_BLOCKER).

### B1. hai state reproject FK constraint failure
### B2. hai intake gaps misleading zero
### B3. hai daily completion confusion
### B4. review record schema drift
<+ any new bugs you find>

## Findings — UX / friction
Same shape. Each item should land as a README change, a CLI default
change, or a new orientation doc.

### F1. Garmin live pull unreliability
### F2. Nutrition daily-total semantics not documented
### F3. --base-dir on every intake
### F4. planned_session_type vocabulary
<+ any new friction you find>

## Findings — calibration timeline validation
Confirm or correct each window in the maintainer's draft "Calibration
timeline" framing. If any day-number is wrong, give the correct one +
the file:line that implies it.

## Findings — determinism / boundary integrity (mandatory check A)
## Findings — skill-vs-code drift (mandatory check B)
## Findings — cold-start correctness (mandatory check C)
## Findings — reproject correctness (mandatory check D)
## Findings — migration safety (mandatory check E)
## Findings — test coverage gaps (mandatory check F)

## Architecture observations (open exploration G)
## CLI ergonomics observations (open exploration H)
## Roadmap recommendations (open exploration I)

## Severity-ranked punch list for v0.1.6
A flat numbered list: every actionable item from above, sorted by
priority (P0 = release-blocker, P1 = should ship, P2 = nice-to-have).
Each line: `[P0] <one-sentence problem> — <one-sentence fix> — <S/M/L>`.

## Things the maintainer's plan likely got wrong
Section for findings that contradict the maintainer's framing or the
README's claims. Be direct.

## Things the maintainer didn't ask about but should have
Last section. Issues outside the 9 listed above that you uncovered
during the audit.
```

## Tone

Be direct. The maintainer prefers terse, specific, evidence-cited
prose over hedged generalities. "Bug at `path/file.py:123` — the
condition on line 124 inverts the predicate" beats "the validation
logic appears to have an issue around line 123." Cite line numbers
whenever you can.

If you're uncertain about something, say so explicitly with the word
"uncertain" rather than burying it in soft language.

If a finding requires investigation you can't do (e.g. running the
test suite, reproducing a TLS error), say "DEFERRED — DIDN'T
INVESTIGATE" rather than guessing.

## Scope guardrail

This audit informs v0.1.6. It is not the v0.2 redesign. Recommendations
should fit within ~2–3 weeks of a single maintainer's work. Anything
larger goes in the "Roadmap recommendations" section as a *named
candidate*, not as a P0/P1 item.
