# CP1 — Lift cli.py-split deferral

**Cycle:** v0.1.12.
**Author:** Claude (delegated by maintainer).
**Codex round-4 verdict:** `accept`.
**Application timing:** at v0.1.12 ship, paired with CP2.
**Pairing:** CP1 + CP2 are paired changes to a single AGENTS.md
"Settled Decisions" bullet + a single "Do Not Do" bullet. If
either is rejected independently, the joint bullet is partially
replaced — see "Acceptance gate" below.

---

## Rationale

Maintainer adjudication 2026-04-29 (chat): *"I am pro for
splitting the CLI.py file as soon as it becomes convenient."* The
existing W29 deferral was scoped to v0.1.11 cycle protection; it
no longer reflects intent. Schedule the split alongside a half-
day boundary audit at v0.1.13 (which has spare capacity per
tactical plan §4) and a mechanical split at v0.1.14 conditional
on the audit verdict. Either way, a parser/capabilities
regression test is mandatory — that is the cheapest insurance
against a future split silently changing CLI surface.

The reconciliation L4 finding gave a concrete shape (1 main + 1
shared + 11 handler-group files, each <2500 lines, with 10k
treated as abort-condition not trigger). v0.1.13 audit verifies
boundaries are clean; v0.1.14 mechanical split implements.

## Current AGENTS.md text (verbatim, verified on disk 2026-04-29)

**`AGENTS.md:124-125` — "Settled Decisions":**

```
- **W29 / W30 deferred.** Do not split `cli.py`. Do not freeze the
  capabilities manifest schema yet.
```

**`AGENTS.md:252-253` — "Do Not Do":**

```
- Do not split `cli.py` or freeze the capabilities manifest schema in this
  cycle.
```

## Proposed delta (CP1 + CP2 jointly accepted)

**Replace `AGENTS.md:124-125` with:**

```
- **W29 / W30 scheduled.** cli.py split scheduled for v0.1.14
  conditional on v0.1.13 boundary-audit verdict (parser /
  capabilities regression test mandatory regardless).
  Capabilities-manifest schema freeze scheduled for v0.2.0 after
  W52 / W58 schema additions land.
```

**Replace `AGENTS.md:252-253` with:**

```
- Do not split `cli.py` or freeze the capabilities manifest schema before
  their scheduled cycles (v0.1.14 / v0.2.0).
```

## Affected files

- `AGENTS.md` (lines 124-125 + 252-253) — apply at v0.1.12 ship.
- `reporting/plans/tactical_plan_v0_1_x.md` — v0.1.13 row gains
  W-29-prep workstream; v0.1.14 row gains W-29 mechanical split.

## Dependent cycles

- **v0.1.13** — W-29-prep boundary audit (~half day). Names the
  handler-group split shape; verifies <2500-lines-per-file is
  achievable; verifies parser/capabilities can be preserved.
- **v0.1.14** — W-29 mechanical split conditional on prep
  verdict. Concrete shape: 1 main + 1 shared + 11 handler-group
  files, each <2500 lines. Parser/capabilities regression test
  mandatory.

## Acceptance gate

- `accepted`: AGENTS.md edit applied at v0.1.12 ship paired with
  CP2 acceptance. Tactical plan updated.
- `accepted-with-revisions`: revised text applied; AGENTS.md
  edit deferred until revisions land.
- `rejected`: AGENTS.md unchanged for the cli.py portion. If
  CP2 is `accepted`, the AGENTS.md replacement text is adjusted
  to keep the cli.py prohibition intact:
  ```
  - **W29 / W30 mixed.** Do not split `cli.py`. Capabilities-manifest
    schema freeze scheduled for v0.2.0 after W52 / W58 schema
    additions land.
  ```
  v0.1.13 W-29-prep workstream removed from tactical plan; CP1
  archived in `reporting/plans/v0_1_12/cycle_proposals/`.

## Round-4 codex verdict

`accept`. Codex round-4 confirmed CP1's strike-text matches
current AGENTS.md verbatim and the paired CP1+CP2 framing
preserves the joint-bullet structure. No remaining contradiction.
