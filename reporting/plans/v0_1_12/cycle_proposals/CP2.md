# CP2 — Lift capabilities-manifest-freeze deferral

**Cycle:** v0.1.12.
**Author:** Claude (delegated by maintainer).
**Codex round-4 verdict:** `accept`.
**Application timing:** at v0.1.12 ship, paired with CP1.
**Pairing:** CP2 + CP1 are paired changes to a single AGENTS.md
"Settled Decisions" bullet + a single "Do Not Do" bullet. See
CP1 for the joint replacement; this doc covers the capabilities-
manifest half.

---

## Rationale

Maintainer adjudication 2026-04-29 (chat): the v0.2.0 cycle
needs additive schema work for W52 weekly review (source-row
locators), W58 deterministic claim-block, and the C8
evidence-card schema (`recommendation_evidence_card.v1`). After
those additions land, freezing the manifest schema gives external
callers — including future MCP exposure per CP4 — a stable
contract.

The W30 freeze was deferred at v0.1.11 to keep additive room for
v0.2.0. Once v0.2.0 schema work completes, the freeze is the
right next step. Schedule it for v0.2.0 itself (after the
schema-add workstreams within v0.2.0 close) so that the freeze
is the last act of v0.2.0, not a separate release.

## Current AGENTS.md text (verbatim, verified on disk 2026-04-29)

Same bullets as CP1 — see CP1 for the verbatim quote of
`AGENTS.md:124-125` and `AGENTS.md:252-253`.

## Proposed delta (CP1 + CP2 jointly accepted)

Same combined replacement as CP1. See CP1 for the new "Settled
Decisions" and "Do Not Do" entries.

## Downstream contract implications

The freeze locks the manifest's top-level schema (`schema_version
= "agent_cli_contract.v1"`) and its `commands[]` row shape.

- **v0.1.12 W-FCC** adds `strength_status` enum surface to `hai
  today`. Additive — must be backwards-compatible with
  whatever shape ships at the v0.2.0 freeze.
- **v0.1.12 W-PRIV** adds `hai auth remove` subcommand to the
  manifest. Additive — same back-compat constraint.
- **v0.1.12 W-FBC** adds `--re-propose-all` flag on `hai daily`
  in capabilities. Additive — same.
- **v0.2.0 W52 + W58 schema additions** are the largest
  pre-freeze additive set. After those land, the freeze is
  applied.
- **v0.3+ MCP exposure (CP4)** consumes the frozen manifest as
  the agent-CLI contract surface. The freeze must precede the
  MCP read-surface ship; CP4's gating ensures this.

## Affected files

- `AGENTS.md` (lines 124-125 + 252-253) — paired with CP1; apply
  at v0.1.12 ship.
- `reporting/plans/tactical_plan_v0_1_x.md` — v0.2.0 row gains
  W-30 freeze workstream as the last item.
- `core/capabilities/walker.py` — v0.2.0 W-30 implementation
  adds a frozen-schema validator (no v0.1.12 change).

## Dependent cycles

- **v0.2.0** — W52 + W53 + W58 schema additions land first; W-30
  freeze workstream is the last act of the cycle.
- **v0.3+** — CP4 MCP read surface consumes the frozen manifest.

## Acceptance gate

- `accepted`: AGENTS.md edit applied at v0.1.12 ship paired with
  CP1. Tactical plan updated.
- `accepted-with-revisions`: revised text applied; AGENTS.md
  edit deferred until revisions land.
- `rejected`: AGENTS.md unchanged for the manifest-freeze
  portion. If CP1 is `accepted`, the AGENTS.md replacement text
  is adjusted to keep the manifest prohibition intact:
  ```
  - **W29 / W30 mixed.** cli.py split scheduled for v0.1.14
    conditional on v0.1.13 boundary-audit verdict. Do not freeze
    the capabilities manifest schema yet.
  ```
  v0.2.0 W-30 workstream removed from tactical plan; CP2 archived.

## Round-4 codex verdict

`accept`. Codex round-4 confirmed CP2's strike-text matches
current AGENTS.md verbatim, and the downstream contract
implications (W-FCC + W-PRIV + W-FBC additive constraints, CP4
gate dependency) are coherent.
