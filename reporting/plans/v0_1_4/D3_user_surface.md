# D3 — User-facing narration surface

- Author: Claude (Opus 4.7)
- Status: **Draft pending Dom's review**
- Gates: Workstream B.

---

## Problem

A first-time user running `hai init --with-auth --with-first-pull` + `hai daily` on v0.1.2 sees:

1. A JSON status blob from `hai daily` (machine-readable, meant for agents).
2. A SQLite file on disk that they're *not* supposed to read directly.
3. An expectation — undocumented in the README's install quickstart — that the real product is an agent (Claude Code) invoking the `reporting` skill conversationally.

That third point is the gap. The user has no way, *from the CLI alone*, to read their plan in human language. The `reporting` skill exists and does exactly that job — but it's opt-in, agent-mediated, and only discoverable if you already know about Claude Code skill invocation.

Today (2026-04-23) Dom explicitly flagged this: "I was not told to look at [the DB] here, nor was I given the recommendations/proposals directly alongside the information which prompted them to occur." The CLI fell through to operator-debug surfaces (SQL, `hai explain --text`) rather than producing a user-readable plan, because no such command exists.

---

## Decision

**Ship `hai today` as a first-class, non-agent-mediated CLI command** that renders the canonical plan in plain prose, in the voice the `reporting` skill already specifies. The `reporting` skill continues to exist for agent-mediated conversational narration (where the agent can adapt tone, answer follow-ups, reference prior context); `hai today` is the non-conversational baseline every user can rely on.

**Change `hai daily`'s terminal output** to end with an explicit pointer: "Plan committed. Read it: `hai today`."

**Restructure the README** around a new "Reading your plan" section that makes the product's human surface visible from the install quickstart onward.

---

## `hai today` — command specification

### Signature

```
hai today [--as-of AS_OF] [--user-id USER_ID] [--format {markdown,plain,json}]
          [--domain {recovery,running,sleep,stress,strength,nutrition}]
          [--db-path DB_PATH]
```

### Semantics

- **Read-only.** Mutation class: none. Idempotent: yes.
- Reads the **canonical leaf** of the plan chain for `(for_date, user_id)` (per D1).
- Narrates all six domains by default; `--domain <X>` narrows to one.
- `--format` defaults to `markdown` on a TTY, `plain` otherwise, explicit override via flag.
- `--format json` emits the structured input the prose was rendered from (useful for agents that want to compose richer narration).
- Exit codes: `OK` when a plan exists; `USER_INPUT` when no plan exists for the date (with stderr hint: "No plan for <date>. Run `hai daily` first.").

### Output shape per domain (markdown)

```markdown
# Today, 2026-04-23 — your plan

## 🟢 Recovery — proceed with your planned session

Every recovery band is in the green: HRV 86ms is above your 14-day
baseline (84.25), resting HR 48 is below baseline (49.2), you reported
low soreness and high energy, training load is balanced. The skill
classified you as `recovered` with full coverage today.

**Confidence:** moderate. Not higher because intervals.icu doesn't
carry Garmin's `training_readiness_level`, so one cross-check wasn't
available.

**Follow-up:** I'll ask tomorrow morning whether today's session felt
appropriate for your recovery.
```

One such section per domain. Prefix emojis indicate action class:

- 🟢 proceed / maintain / prescriptive positive
- 🟡 caution / downgrade / caveat
- 🔴 rest / escalate
- ⚪ defer (insufficient signal)

For defer domains, the output explains **what the user could log to unblock a real recommendation**:

```markdown
## ⚪ Nutrition — not enough information to recommend

No structured nutrition row for today. I have breakfast logged as a
note (porridge, fruit, 2 protein yogurts) but no macro totals.

**What would unblock me:** `hai intake nutrition --calories … --protein-g
… --carbs-g … --fat-g …` when you have the day's totals.
```

### Voice

Copy-pasted verbatim from `src/health_agent_infra/skills/reporting/SKILL.md`:

- Plain, direct, first-person ("I recommend…", not "The model recommends…").
- No medical language (banned tokens enforced by shared module with the reporting skill).
- No hype, no hedging theatre. If I don't know, I say so.
- No restated raw numbers beyond what the rationale already names.
- No rule IDs (`R1`, `require_min_coverage`) — translate to intent.
- Always end with a follow-up.

A shared module `src/health_agent_infra/core/narration/voice.py` enforces these constraints via a linter-style check on output strings. The reporting skill and `hai today` both consume this module.

### Structure — top-matter + summary + per-domain + footer

```
# Top-matter (1–2 lines)
Today, <date> — your plan (<N> prescriptions, <M> defers)

# Summary (2–4 sentences)
<Overall read: "Green across the board for a quality session" /
"Mostly defers — today has thin evidence" / etc.>

# Per-domain sections
<6 sections in a stable order: recovery, sleep, running, strength,
stress, nutrition>

# Footer
Recorded as plan <daily_plan_id>. Run `hai review record` tomorrow
morning to log how today went.
```

---

## `hai daily` output change

Currently the last thing `hai daily` prints is a JSON block. Change: after the JSON, print (to stderr so the JSON stream stays pipe-clean):

```
Plan committed: plan_2026-04-23_u_local_1
Read it in plain language: hai today
```

TTY-only. If stdout isn't a TTY (e.g. piped to `jq`), skip the hint. A dedicated `--quiet` flag on `hai daily` suppresses it unconditionally.

---

## Defer review_question improvements

Today's bug: every defer rec's review_question is `"Did you decide on a session yesterday? How did it go?"` — leaking session-language into nutrition and stress.

**Each domain's skill owns its defer review_question.** Templates:

- Recovery: "Did you decide on a session yesterday? How did it go?" (unchanged — session-appropriate)
- Running: "Did you go for a run yesterday? How did it feel?"
- Sleep: "Did anything shift in your sleep last night worth noting?"
- Strength: "Did you train yesterday? Anything worth logging?"
- Stress: "How were your stress levels yesterday?"
- Nutrition: "How did yesterday's eating go? Anything worth logging as macros?"

Each domain's readiness skill's protocol section gains an explicit `review_question by defer template` entry; `hai propose` validates it's populated for defer actions; no more generic fallback.

---

## `hai explain --text` relationship

`hai explain --text` today is an **operator** report — dense, field-by-field, audit-chain-complete. It should stay that way for debug purposes. Rename to `--operator` to signal the role:

- `hai explain` → JSON (machine surface, existing default).
- `hai explain --operator` → dense text (existing `--text` behavior, renamed).
- `--text` continues to work as an alias for one release cycle with a deprecation hint.

`hai today` is the user surface; `hai explain --operator` is the debug surface. They share a common underlying structured representation (the explain bundle), render it differently.

---

## README restructure

### Current install quickstart

```bash
pipx install health-agent-infra
hai init --with-auth --with-first-pull
hai daily
hai stats
```

### New install quickstart

```bash
pipx install health-agent-infra
hai init --with-auth --with-first-pull
hai daily          # pull → clean → propose → synthesize → commit
hai today          # read today's plan in plain language
```

Followed by a new top-level section in the README:

```markdown
## Reading your plan

`hai today` is how you read what the agent recommended for you. It
narrates all six domains — recovery, sleep, running, stress, strength,
nutrition — in plain English, explaining what it recommends, why, and
what it's uncertain about.

You never need to read the SQLite database directly. If `hai today`
doesn't answer your question, `hai explain --operator` is the debug
surface.

## Recording your day

When something happens during the day — you log a gym session, eat a
big meal, feel unusually tired — the agent can't know unless you tell
it. The `hai intake …` commands are how you tell it:

    hai intake gym       # log sets/reps
    hai intake nutrition # log day totals
    hai intake stress    # log subjective stress
    hai intake readiness # log morning readiness
    hai journal add      # free-text note
    hai memory set       # goals, preferences, constraints

After any intake, rerun `hai daily` to re-synthesize. The agent will
revise today's plan automatically (see v0.1.4 re-author semantics).
```

This makes the product's human surface visible from the first screen a reader sees.

---

## Domain skills — relation to `hai today`

The six domain readiness skills (recovery-readiness, running-readiness, etc.) continue to exist and are invoked by agents (Claude Code) when the user asks domain-specific follow-ups. They do not ship output to the user directly; they produce `DomainProposal` rows that feed synthesis.

The `reporting` skill continues to exist for agent-mediated conversational narration where the user asks things like "why did you recommend this?" or "how have my sessions been going?" — the skill can answer richer questions that `hai today` can't, because it has a conversation in context.

**`hai today` is the non-agent, any-user fallback.** If you don't have Claude Code running, if you're on a server, if you're piping into TTS, if you just want to read the plan once — `hai today` is enough.

---

## Code touch-points

- `src/health_agent_infra/cli.py`:
  - New `cmd_today` handler and subparser.
  - `cmd_daily` adds the TTY-aware stderr hint.
  - `cmd_explain` adds `--operator` flag; `--text` aliased with deprecation warning.
- `src/health_agent_infra/core/narration/` — new module:
  - `voice.py` — voice-linter check (no medical language, no rule IDs, etc.); shared by `hai today` and the reporting skill.
  - `render.py` — takes the explain bundle; renders markdown / plain / json; per-domain section builders.
  - `templates.py` — defer review_question per-domain templates, action-class emoji mapping, footer templates.
- `src/health_agent_infra/skills/<domain>-readiness/SKILL.md`:
  - Each domain skill adds a `review_question by defer template` entry in its protocol.
  - Each skill's allowed-tools includes `Bash(hai today)` for quick reference in conversational flows.
- `src/health_agent_infra/core/writeback/proposal.py`:
  - Validator: if `action == defer_decision_insufficient_signal`, require a non-empty review_question override in the payload (else fall back to the domain's default from templates.py).
- `README.md`:
  - Quickstart gains `hai today`.
  - New "Reading your plan" section.
  - New "Recording your day" section.

---

## Test coverage (acceptance criteria)

1. **Snapshot test: `hai today` green day.** Seed a DB with a v3-style canonical plan where all 6 domains have real prescriptions. Run `hai today --format plain`. Assert output matches a stored fixture. Run again with no changes, assert identical.
2. **Snapshot test: `hai today` mixed day.** Seed a DB like 2026-04-23's actual session output (2 prescriptions, 4 defers). Same assertion shape.
3. **Snapshot test: `hai today` no-plan day.** Fresh DB, no plan for the date. Assert exit USER_INPUT with the "No plan for <date>. Run `hai daily` first." message.
4. **Snapshot test: `hai today --domain recovery`.** Assert single-domain output is a subset (exactly one section) of the full output.
5. **Snapshot test: `hai today --format json`.** Assert output is valid JSON with the expected structured shape.
6. **Snapshot test: `hai today` on superseded plan.** Seed v1 superseded by v2 superseded by v3. Run `hai today`. Assert output reflects v3's recommendations. Also assert `hai explain --daily-plan-id <v1> --text` (operator mode) still renders v1 correctly (per D1 retrieval changes).
7. **Voice lint test.** Seed 20 canonical narration snippets (real examples from a 2-week run). Run through `voice.py` linter. Assert no banned tokens trigger; assert no rule IDs leak.
8. **Defer question per-domain test.** Seed one defer per domain. Run `hai today`. Assert each defer's review_question is the domain-specific template, not the generic session one.
9. **`hai daily` hint test.** Run `hai daily` under a simulated TTY; assert stderr contains the `hai today` hint. Run under a non-TTY; assert hint is absent.
10. **README integrity test.** Part of the Workstream E documentation integrity check: every command in the README's quickstart exists in the capabilities manifest.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| `hai today` and the reporting skill drift apart over time | Both consume the same `core/narration/render.py`. The skill's SKILL.md explicitly names that module as its rendering source. Contract test asserts the skill's example outputs match what `hai today --format plain` would produce for the same input. |
| User finds `hai today` output too terse (or too verbose) | Output length is tuned on 5 canonical scenarios during Workstream B; iterate based on Dom's read during dogfood. Default verbosity is "medium" (today's 6-section output ≈ 1 page); add `--verbose` / `--brief` later if needed. |
| Emoji prefixes are unappealing to TTS or accessibility users | `--format plain` omits emojis; use text markers (`[PROCEED]`, `[DEFER]`) instead. Markdown mode keeps emojis. |
| Renaming `hai explain --text` to `--operator` breaks scripts | Alias is kept; deprecation warning only. Remove alias in v0.1.5 if nobody complains. |

---

## Explicit non-goals

- **No interactive TUI.** `hai today` is a one-shot read. For conversational back-and-forth, use Claude Code + skills.
- **No natural-language querying.** `hai today` renders what the plan says; it doesn't answer open-ended questions. Those go through the `reporting` skill under an agent.
- **No multi-day views.** `hai today` is today. `hai explain --daily-plan-id <id>` handles historical. A multi-day summary is v0.1.5+ (`hai week`, `hai history`, etc.).
- **No outcome-history integration.** `hai today` reads the plan, not review outcomes. The `reporting` skill handles review history in conversational context; `hai review summary` handles it for structured output.
- **No per-user customization of prose.** Voice is fixed across users; personalization is out of scope for v0.1.4.
