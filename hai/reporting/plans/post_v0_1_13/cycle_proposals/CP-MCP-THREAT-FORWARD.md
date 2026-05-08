# CP-MCP-THREAT-FORWARD — Pull MCP threat-model authoring forward to v0.2.0

**Cycle:** v0.2.0 (PLAN authoring upcoming).
**Author:** Claude (delegated by maintainer).
**Codex verdict:** applied at v0.1.14 D14 round 1
(PLAN_COHERENT_WITH_REVISIONS); strategic_plan_v1.md Wave 3 staging
delta applied 2026-05-01 pre-cycle. F-PLAN-08 corrected the source-
list verification timing ("verify current at v0.4" → "verify
current at v0.2.0 authoring; refresh at v0.4 prereq completion").
**Application timing:** at v0.2.0 PLAN.md authoring — adds
W-MCP-THREAT as a doc-only adjunct workstream; updates
strategic_plan_v1.md Wave 3 staging language to require the threat-
model artifact *before* v0.3 PLAN-audit, not as part of v0.3
implementation.
**Source:** Strategic-research report 2026-05-01 §5 P0-4, §9 R-3,
§14 S-2. Codex round-1 audit confirmed; round-2 audit did not
flag.

---

## Rationale

CP4 (v0.1.12) staged MCP exposure as: v0.3 plans, v0.4 prereqs land,
v0.4-or-v0.5 ships read surface. The current strategic plan §10
Wave 3 row schedules **threat-model authoring as part of v0.3
design** (per CP4's `reporting/docs/mcp_threat_model.md` (new) —
authored at v0.3 design phase, completed at v0.4 prereq phase").

The 2025-2026 MCP CVE class makes "1-shot MCP integration" an
actively documented anti-pattern. Reviewed sources:

- CVE-2025-59536 / CVE-2026-21852 (Check Point — Claude Code MCP
  autoload + ANTHROPIC_BASE_URL hijack → API key exfiltration).
- CVE-2025-6514 (mcp-remote command injection via malicious
  authorization endpoint).
- CVE-2025-53109 / 53110 (Anthropic Filesystem-MCP server
  symlink-bypass + prefix-match path traversal).
- arXiv 2511.20920 — academic synthesis of MCP threat landscape.
- OWASP MCP Top 10 (2026 beta).

**The threat model is upstream of the design, not part of it.** If
v0.3 design starts with the threat model still being authored, the
v0.3 D14 plan-audit will surface what the threat model would have
surfaced — at the cost of an extra audit round per design issue.
The empirically cheap path is to author the threat model in v0.2.0
(when MCP-related schema or code work has not yet started) and let
v0.3 design consume it as input.

This is a staging change within an already-settled decision (CP4 is
not being reopened). CP4 settled the *what* and *when-to-ship*; this
CP refines the *prerequisite-authoring sequence*.

## Current strategic plan text (verify on disk before applying)

CP4 added this language to `strategic_plan_v1.md` Wave 3 (per
`reporting/plans/v0_1_12/cycle_proposals/CP4.md:65-96`):

```
**Staging within Wave 3.**
- **v0.3** — *plans* MCP server. Read-surface design only (no
  write surface). Threat-model artifact authored at
  `reporting/docs/mcp_threat_model.md`. Provenance import
  contract drafted (...).
- **v0.4** — *prereqs land*. ... Threat-model doc completes with
  mitigations for ... .
```

The proposed change moves "Threat-model artifact authored" out of
v0.3 and into v0.2.0.

## Proposed delta — strategic_plan_v1.md Wave 3 staging block

**Replace:**

> **v0.3** — *plans* MCP server. Read-surface design only (no
> write surface). Threat-model artifact authored at
> `reporting/docs/mcp_threat_model.md`. Provenance import
> contract drafted ...

**With:**

> **v0.2.0** — *threat-model artifact authored* at
> `reporting/docs/mcp_threat_model.md`, as a doc-only adjunct
> workstream (W-MCP-THREAT). Catalogues each OWASP MCP Top 10 risk
> against HAI's planned read-surface; maps to existing invariants;
> names residual risks. Cited CVEs:
> CVE-2025-59536/21852/6514/53109/53110, plus arXiv 2511.20920
> synthesis.
>
> **v0.3** — *plans* MCP server. Read-surface design only (no
> write surface). Design consumes the v0.2.0 threat-model as input.
> Provenance import contract drafted (extends agent-CLI capabilities
> manifest with provenance fields per imported row).
>
> **v0.4** — *prereqs land*. Threat-model doc completes with
> mitigations for resource audience validation, confused-deputy
> risk, token-passthrough risk, SSRF risk. Least-privilege read-
> scope model documented (per-table read scopes, no cross-table
> joins exposed). Provenance contract enforced through one full
> domain end-to-end (recovery is the smallest surface).

The remaining lines (no-write-surface-ever, security-gate
non-negotiable) are unchanged.

## Proposed delta — tactical_plan_v0_1_x.md §6 (v0.2.0 in-scope)

Add row to v0.2.0 in-scope:

```
| **W-MCP-THREAT** | Author `reporting/docs/mcp_threat_model.md` against the OWASP MCP Top 10 + 2025-2026 CVE class (doc-only) | 3 days |
```

with a note: "Per CP-MCP-THREAT-FORWARD; precedes v0.3 PLAN-audit;
does not change the v0.4-or-v0.5 ship target."

## Proposed delta — v0.2.0 PLAN.md (when authored)

W-MCP-THREAT joins v0.2.0 §2 as a doc-only adjunct alongside
W-COMP-LANDSCAPE and W-NOF1-METHOD. Acceptance: first draft of
`mcp_threat_model.md` filed; one external review pass before v0.3
PLAN.md is authored.

## Affected files

- `reporting/plans/strategic_plan_v1.md` Wave 3 staging block.
- `reporting/plans/tactical_plan_v0_1_x.md` §6 v0.2.0 row.
- `reporting/plans/v0_2_0/PLAN.md` (new at v0.2.0 PLAN authoring).
- `reporting/docs/mcp_threat_model.md` (new at v0.2.0 ship).

## Dependent cycles

- **v0.2.0**: W-MCP-THREAT ships as doc-only adjunct (3 days).
- **v0.3**: PLAN.md authoring consumes the threat-model as input.
  v0.3 PLAN-audit benefits from threat-model already in tree.
- **v0.4**: prereqs phase completes the threat-model with
  mitigations. Unchanged from CP4.
- **v0.4-or-v0.5**: ship phase. Unchanged from CP4.

## Acceptance gate

- `accepted`: v0.2.0 PLAN.md gains W-MCP-THREAT;
  strategic_plan_v1.md Wave 3 staging updated; v0.3 PLAN consumes
  the threat-model as input.
- `accepted-with-revisions`: timing or scope revised. The
  "threat-model authored before v0.3 PLAN-audit" claim is the
  load-bearing one; if revisions move authoring into v0.3, the
  cost-saving rationale evaporates.
- `rejected`: CP4 staging unchanged; threat-model authored in v0.3
  as originally scheduled. CP archived. v0.3 PLAN-audit risk
  remains.

## Round-N codex verdict

**Applied at v0.1.14 D14 round 1 (PLAN_COHERENT_WITH_REVISIONS,
2026-05-01).** strategic_plan_v1.md Wave 3 staging delta applied
2026-05-01 pre-cycle. F-PLAN-08 corrected the source-list verification
timing ("verify current at v0.4" → "verify current at v0.2.0
authoring; refresh at v0.4 prereq completion").
