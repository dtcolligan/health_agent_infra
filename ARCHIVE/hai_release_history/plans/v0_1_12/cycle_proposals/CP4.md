# CP4 — Stage and gate the existing MCP-exposure plan

**Cycle:** v0.1.12.
**Author:** Claude (delegated by maintainer).
**Codex round-4 verdict:** `accept`.
**Application timing:** at v0.1.12 ship — extends Wave 3 row at
`strategic_plan_v1.md:444` with staging + security gates.

---

## Rationale

Maintainer adjudication 2026-04-29 (chat): *"I would like to
expose the project via MCP, but only when it is ready, so I
agree with the plan."* The plan referenced was the staged
synthesis (D4) — plan at v0.3, prereqs at v0.4, ship read
surface at v0.4-or-v0.5. No write surface ever.

**Codex round 2 + 3 correction.** The strategic plan §10 already
has an MCP exposure row at Wave 3 (line 444); CP4 is not adding
a new row. The existing row lacks: (a) staged exposure design
(read surface only), (b) provenance import contract, (c) least-
privilege read-scope model, (d) threat-model gate. CP4 extends
the existing row.

The MCP commodification finding (reconciliation A6 + L5) is the
strategic premise: Open Wearables / Apple Health MCP / Pierre /
garmy commoditise data-access; the moat is governance + audit.
MCP-as-distribution is the durable channel for the *governed*
side of that commoditisation. Health Agent Infra dual-publishing
as an MCP server is offence (reach), not defence — but only if
the security surface is correct.

## Current strategic plan text (verbatim, verified on disk 2026-04-29)

**`strategic_plan_v1.md:444` — Wave 3 header:**

```
### Wave 3 — MCP surface + extension contract (v0.3–v0.4, ~3-4 months)
```

**`strategic_plan_v1.md:446-451` — Wave 3 body:**

```
**Theme.** Make the runtime accessible to second agents and second
data sources. Was v0.3 (extension contracts) + v0.4 (runtime
portability) in the 2026-04-25 roadmap. Sequence preserved.

**Evidence anchor:** Roadmap §4 v0.3 + v0.4. PHIA + Bloom integration
prior art.
```

**`strategic_plan_v1.md:632` — contributor-governance branch:**

```
**Branch:** at v0.4 (when MCP surface ships), evaluate whether to
```

(line continues; the "at v0.4 (when MCP surface ships)" reference
is preserved unchanged by CP4 — the staging adds detail to Wave
3, doesn't change v0.4 as the ship target.)

## Proposed delta — extend `strategic_plan_v1.md` Wave 3

**Insert after `:451` (after the Evidence anchor line):**

```
**Staging within Wave 3.**

- **v0.3** — *plans* MCP server. Read-surface design only (no
  write surface). Threat-model artifact authored at
  `reporting/docs/mcp_threat_model.md`. Provenance import
  contract drafted (extends the agent-CLI capabilities manifest
  with provenance fields per imported row).
- **v0.4** — *prereqs land*. Least-privilege read-scope model
  documented (per-table read scopes, no cross-table joins
  exposed). Threat-model doc completes with mitigations for
  resource audience validation, confused-deputy risk, token-
  passthrough risk, SSRF risk. Provenance contract enforced
  through one full domain end-to-end (recovery is the smallest
  surface).
- **v0.4-or-v0.5** — *ships* MCP read surface. Gated on the
  prereqs above. **No write surface ever.** All mutating CLI
  commands (`hai propose`, `hai daily`, `hai review record`,
  `hai intent commit`, `hai target commit`, all `hai intake *`)
  remain agent-CLI-only (W57 invariant preserved at the MCP
  boundary).

**Security gate (non-negotiable).** No MCP read surface ships
before the threat-model artifact, the least-privilege scope
model, and the one-domain provenance proof are all in place.
Sources for threat-model authoring (verify current at v0.4):

- <https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization>
- <https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices>
```

## Affected files

- `reporting/plans/strategic_plan_v1.md` — Wave 3 row extended
  per the delta above; apply at v0.1.12 ship.
- `reporting/plans/tactical_plan_v0_1_x.md` — v0.3 + v0.4 rows
  gain MCP staging language.
- `reporting/docs/mcp_threat_model.md` (new) — authored at
  v0.3 design phase, completed at v0.4 prereq phase.

## Dependent cycles

- **v0.3** — design phase. New W-id authored at v0.3 PLAN
  (TBD; e.g. `W-MCP-PLAN`). Threat-model artifact drafted.
- **v0.4** — prereqs land. Least-privilege model + threat-model
  completion + one-domain provenance enforcement.
- **v0.4-or-v0.5** — ship phase. MCP read surface shipped.

## Acceptance gate

- `accepted`: strategic plan §10 Wave 3 extended at v0.1.12 ship.
- `accepted-with-revisions`: revised staging applied. The
  security-gate language is **non-negotiable**: any
  `accepted-with-revisions` path must preserve the threat-model
  artifact requirement, the least-privilege scope model
  requirement, and the no-write-surface-ever invariant. Stylistic
  revisions to other parts are acceptable.
- `rejected`: strategic plan unchanged; v0.3+ MCP work uses
  whatever Wave 3 currently says (which is under-specified per
  Codex F-PLAN-R2-05). CP4 archived.

## Round-4 codex verdict

`accept`. Codex round-4 confirmed CP4 correctly extends the
existing MCP row instead of falsely treating it as absent (the
round-2 correction). Security gate language is intact.
