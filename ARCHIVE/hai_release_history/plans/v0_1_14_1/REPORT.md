# v0.1.14.1 REPORT — Hardening: Garmin-live structured-signal trap closure

**Tier (D15):** hardening.
**Date:** 2026-05-02.
**Status:** SHIPPED. Commit `856e689`. PyPI publish complete.

## 1. Why this cycle existed

A maintainer-driver Claude Code agent invoked
`hai pull --source garmin_live --live` during a routine session-start
data-freshness sweep on 2026-05-02 morning. The call hit the
documented HTTP 429 / Cloudflare 403 failure mode that AGENTS.md
"Settled Decisions" already names ("Garmin Connect is not the default
live source. Login is rate-limited and unreliable."). The maintainer's
reaction was unambiguous: this is a system trap, not a memory bug,
and it needs to close at the surface where the trap actually lives.

The trap diagnosis: `hai capabilities --json` is the agent contract.
It listed `garmin_live` as a peer of `intervals_icu` and `csv` in the
`--source` choice list, with the unreliability warning living only in
prose inside the flag's `help=` string. An agent that read the
manifest programmatically — the principal trap surface — got no
*structured* signal that one source was supported and the other was
best-effort.

## 2. What shipped

One workstream: **W-GARMIN-MANIFEST-SIGNAL.**

- New schema-additive metadata in `hai capabilities --json`:
  `flags[].choice_metadata` blocks per choice value, validated
  eagerly via a new `annotate_choice_metadata` helper. The
  `RELIABILITY_VALUES` enum currently admits `"reliable"` and
  `"unreliable"`; absence of a metadata entry is itself the signal
  (consumers default to "reliable" for plain choices).

- `hai pull` and `hai daily` `--source` flags both carry a
  `garmin_live` entry with `reliability: "unreliable"`,
  `reason: "rate-limited / Cloudflare-blocked (HTTP 429 / 403)"`,
  and `prefer_instead: "intervals_icu"`.

- Runtime breadcrumb: `_resolve_pull_source` emits a stderr warning
  exactly once when the resolved source is `garmin_live`, regardless
  of how the source was chosen (`--source`, `--live`, or any future
  resolution path). The warning catches programmatic callers who
  bypass both the manifest and the help text.

- AGENTS.md "Settled Decisions" Garmin bullet extended with a
  pointer to the structured signal so future agents reading the
  contract know to pattern-match on `choice_metadata` rather than
  parsing prose.

- 15 new tests across two new files; one existing test
  (`test_flag_entry_shape_is_stable`) updated to recognise
  `choice_metadata` as an optional schema key.

## 3. Highlights

- **The fix lives where the trap lives.** Memory-only fixes prevent
  this agent from re-tripping the trap, but every fresh agent
  session inherits a clean memory and reads the manifest. Closing
  the gap at the manifest schema fixes it for *every* future agent.

- **Purely additive surface change.** Manifest `schema_version`
  unchanged. No flag removed, no choice removed, no behavior
  break for existing `--source garmin_live` callers. Per AGENTS.md
  CP1/CP2, additive metadata fits the v0.2.x window before the
  v0.2.3 schema freeze.

- **Single-source-of-truth metadata constant.**
  `PULL_SOURCE_CHOICE_METADATA` is defined once in cli.py and
  attached to both annotation sites. Drift between `hai pull` and
  `hai daily` is structurally impossible.

- **Empirical proof of the warning at runtime.** Manual probe
  during implementation confirmed the warning fires *before* the
  network call, so it appears in the agent's transcript even when
  the upstream login subsequently fails.

## 4. Deferrals

None for this cycle. All scope items shipped.

## 5. Lessons / patterns

### 5.1 "Memory + system" double-fix pattern

The maintainer's framing was: a memory fix on the agent side is
necessary but insufficient. The trap also lives in the contract
surface. This double-fix pattern — local memory rule *plus* upstream
system change — should generalise to any future "I keep doing X
that I shouldn't" feedback. Memory keeps the *current* agent from
repeating; the system change closes the trap for *every* agent.

Two memory entries were saved during the session:

- `feedback_no_garmin_live_pull.md` — never call Garmin live;
  intervals.icu only; if recovery missing, ask for self-report or
  name the gap.
- `feedback_pull_fitness_context_on_session_intent.md` — when user
  declares a training session, pull and surface fitness context
  (HRV trend, recent activities, load trajectory, muscle-group
  conflict with yesterday) BEFORE acknowledging or moving to
  nutrition/intent commits.

### 5.2 Hardening-tier cadence works

This cycle ran from incident → PLAN.md → implementation → tests →
docs → cycle artifacts in a single session. No persona matrix, no
external Codex bug-hunt, no multi-round D14. The single-WS scope +
purely-additive surface + tight test budget made it tractable.
Substantive cycles are 2-4 weeks; hardening cycles are hours. The
D15 tier system earns its keep.

### 5.3 The capabilities manifest is the agent contract

Every cycle that touches CLI surface should ask: "would an agent
reading the manifest get the right *structured* signal here, or
only the prose in `help=`?" Help text is for humans at the
terminal. The manifest is for agents. They are different audiences
with different parsing contracts.

## 6. Ship sequence

1. ✅ PLAN.md authored.
2. ✅ Walker schema add (`annotate_choice_metadata` + `RELIABILITY_VALUES`).
3. ✅ cli.py annotation sites + `_resolve_pull_source` warning.
4. ✅ Tests written + green (15 new, 0 regressions).
5. ✅ Linters: mypy clean, bandit unchanged, ruff clean on modified files.
6. ✅ Capabilities snapshot regenerated.
7. ✅ `agent_cli_contract.md` regenerated.
8. ✅ Version 0.1.14 → 0.1.14.1.
9. ✅ CHANGELOG.md, AGENTS.md updated.
10. ✅ Codex IR skipped per D15 hardening latitude — internal sweep
    + test gates + mypy/bandit/ruff clean were the ship evidence.
11. ✅ Maintainer committed (`856e689`) and ran PyPI publish via the
    standard release toolchain.

This cycle shipped as a **hardening** cycle (D15) with an
abbreviated audit chain — single Codex IR round was not required
given the single-WS, purely-additive scope. The pattern fits the
v0.1.12.1 Cloudflare User-Agent hotfix shape: hardening tier earns
its keep on incident-driven, narrowly-scoped releases.
