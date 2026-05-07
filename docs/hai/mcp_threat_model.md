# MCP threat model — pre-Wave-3 posture

**Cycle of record.** v0.2.0 W-MCP-THREAT.

**Pre-req for.** v0.3 PLAN-audit (CP-MCP-THREAT-FORWARD,
post-v0.1.13). v0.3-v0.4 is when the project's first MCP
read-surface is currently *scheduled to land*; this doc captures
the threat posture **before** that surface is authored, so the
v0.3 PLAN can audit against a written contract rather than against
freshly-invented intuition.

**Source provenance.**

- OWASP MCP Top 10 (v0.1, beta — January 2026; lead Vandana Verma
  Sehgal): https://owasp.org/www-project-mcp-top-10/.
- CVE-2025-59536 / CVE-2026-21852 (Check Point Research,
  February 2026):
  https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/.
- AGENTS.md "Do Not Do" entry on MCP autoload — provenance:
  post-v0.1.13 strategic research §17 Sc-5 + CP-DO-NOT-DO-ADDITIONS.
- `SECURITY.md` (project root) — threat model, scope, reporting.
- `docs/hai/privacy.md` — data-handling posture.

This doc cross-references all four; if any drift, this doc is
authoritative for v0.3 audit and the others are sources of truth
for their own concerns.

---

## 1. Posture summary

**v0.2.0 ship state: zero MCP read-surface, zero MCP write-surface,
no autoload mechanism.** HAI today exposes its capability through a
local CLI (`hai`) consumed by host agents (Claude Code, Codex,
local LLMs) over shell. There is no MCP server packaged in the
distribution; there is no manifest entry that would have a host
agent auto-spawn one; there is no reachable MCP-over-network
attack surface.

The threat model here is therefore primarily **forward-looking**:
when v0.3-v0.4 introduces a read-only MCP surface (per the strategic
plan v2 §10 Wave 3 row), the posture below applies. The "currently
applies / mitigation in place / gap deferred" disposition is
recorded against that planned surface, not against today's surface.

**Settled architectural decision** (AGENTS.md "Do Not Do",
post-v0.1.13):

> Do not ship a mechanism that auto-loads MCP servers from project
> files (e.g., `.claude/settings.json` referencing a hai-managed
> MCP server). HAI runs inside Claude Code; CVE-2025-59536 /
> CVE-2026-21852 (Check Point) demonstrate the project-file
> autoload + token-exfiltration chain. **Manual install + local
> stdio is the only allowed exposure path.**

The Check Point chain is the load-bearing precedent: it
established empirically that a project-file autoload mechanism is
a token-exfiltration vector before users have any chance to grant
explicit consent. v0.3 read-surface will be packaged so that a
user must explicitly install + register the server in their host
agent's user-scoped configuration, never project-scoped.

---

## 2. The Check Point precedent (CVE-2025-59536 / CVE-2026-21852)

### Chain shape

Check Point Research disclosed (February 2026) two CVEs against
Claude Code itself — the host environment HAI runs inside —
showing how project-file-driven MCP autoload becomes a
remote-code-execution + Anthropic-API-token-exfiltration chain:

1. A malicious or compromised git repository ships a `.mcp.json`
   and/or a `.claude/settings.json` referencing an attacker-
   controlled MCP server endpoint or shell command.
2. When a developer clones the repo and opens a Claude Code
   conversation in that directory, Claude Code **initialises all
   referenced MCP servers** before the user has a meaningful
   chance to inspect them.
3. With `enableAllProjectMcpServers: true` in the project
   settings, the explicit user-approval dialog is bypassed.
4. The server runs arbitrary shell, exfiltrates the Anthropic API
   key from environment / config, and proceeds to RCE on the
   developer's host.

CVE-2025-59536 carries CVSS 8.7. Both CVEs are patched in Claude
Code 1.0.111+ (October 2025), but the **architectural lesson** is
preserved here: **project-file-driven configuration is a hostile
input boundary**, not a convenience layer. Any HAI MCP surface
must require user-scoped, manually-registered installation.

### Why this binds HAI specifically

HAI is a Python wheel that runs *inside* Claude Code (and similar
host agents). If a future cycle were tempted to ship a `.mcp.json`
template in the project root that references a hai-managed MCP
server, HAI would itself become the staging step in this exact
chain — even with Claude Code patched, a downstream fork or a
similar host that revives the autoload primitive would re-open
the wound.

The AGENTS.md "Do Not Do" entry encodes this. The v0.3 PLAN audit
must verify zero project-file-driven MCP staging in any artifact
shipped by HAI.

---

## 3. OWASP MCP Top 10 (2025) — per-category disposition

Each category below names: **(a)** the OWASP risk, **(b)** whether
it currently applies to HAI's surface (today vs. planned Wave 3
read-surface), **(c)** the mitigation if it applies, **(d)** the
gap named with destination cycle if mitigation isn't yet shipped.

### MCP01 — Token Mismanagement & Secret Exposure

- **Risk.** Hard-coded credentials, long-lived tokens, secrets in
  model memory or protocol logs.
- **Today.** **Not applicable** to MCP; HAI exposes no MCP
  surface. Adjacent concern: HAI stores intervals.icu / Garmin
  credentials locally per `core/pull/auth.py`. SECURITY.md scope
  + `core/credentials` posture covers this.
- **Wave 3.** **Applies.** A read-surface MCP server inheriting
  the user's local credentials must not log them in protocol
  traces or expose them in error messages.
- **Mitigation (Wave 3 contract).** MCP server reads credentials
  through the existing `core/pull/auth.py` boundary; never
  serialises tokens into MCP protocol responses; logs redact
  credential-shaped tokens on emit.
- **Gap.** Not yet shipped. Destination: v0.3 PLAN must
  explicitly land token-redaction tests on the read-surface.

### MCP02 — Privilege Escalation via Scope Creep

- **Risk.** Loosely defined permissions progressively expand,
  allowing agents to act beyond original scope.
- **Today.** **Not applicable** to MCP. Adjacent concern: HAI's
  W57 user-commit-only path for `intent_item` / `target` mutation
  is the analog; an LLM can `--propose` but cannot
  `--commit-active` without explicit user-driven CLI invocation.
- **Wave 3.** **Applies cautiously.** Read-only surface keeps the
  scope-creep risk minimal; the threat is whether a future
  *write* MCP surface drifts into the existing user-commit
  privileges.
- **Mitigation (Wave 3 contract).** MCP surface is **read-only**
  by design. No write-side tools exposed. Any future write tool
  must re-walk the W57 commit gate; no MCP-side bypass.
- **Gap.** Not yet shipped. Destination: v0.3 capability-manifest
  contract must enumerate every tool with a `write_path: false`
  marker; v0.4 audit pressure-tests for drift.

### MCP03 — Tool Poisoning

- **Risk.** Compromised tools / plugins inject malicious context
  to manipulate model behavior. Sub-techniques: rug pulls (post-
  trust malicious updates), schema poisoning, tool shadowing.
- **Today.** **Not applicable** to MCP. Adjacent concern: HAI's
  packaged skills are versioned with the Python wheel; the user
  installs a single artifact, not 11 separate tools that could
  be individually compromised.
- **Wave 3.** **Applies.** A future MCP surface that exposes
  hai-tool primitives could be impersonated by a co-resident
  malicious MCP server (tool shadowing).
- **Mitigation (Wave 3 contract).** MCP server is shipped inside
  the same wheel as the rest of HAI; user installs one PyPI
  artifact, not a separate connector. Server identity is verified
  by the host agent through standard MCP server-name namespacing.
  Updates ride the existing PyPI release process; the audit chain
  in `AUDIT.md` covers MCP-surface changes.
- **Gap.** No standalone HAI MCP namespace registered today.
  Destination: v0.3 PLAN names the namespace + reservation
  approach.

### MCP04 — Software Supply Chain Attacks & Dependency Tampering

- **Risk.** Compromised open-source packages, connectors, or
  model-side plug-ins introduce execution-level backdoors.
- **Today.** **Applies in general** (HAI's Python deps); does not
  apply to MCP surface (none exists). Pin discipline: `uv.lock`,
  the venv-vs-uvx separation in CLAUDE.md (mypy / bandit / build
  via uvx so the project venv stays minimal), and the
  AGENTS.md "Do Not Do" prohibition on Strava-anchored data
  paths all reduce the supply-chain blast radius.
- **Wave 3.** **Applies.** MCP server inherits HAI's existing
  Python dependency tree; no new transitive deps planned for the
  MCP layer beyond an MCP SDK pin.
- **Mitigation (Wave 3 contract).** Pin the MCP SDK at a known
  version in `pyproject.toml`; document the SBOM; never include
  a project-file-driven `.mcp.json` mechanism (CVE-2025-59536
  precedent).
- **Gap.** Wave 3 SBOM publication. Destination: v0.3 ship-time
  freshness sweep adds a `docs/hai/sbom.md` row.

### MCP05 — Command Injection & Execution

- **Risk.** AI agent constructs and executes system commands
  using untrusted input without proper validation or sanitization.
- **Today.** **Applies** at the CLI boundary, not the MCP
  boundary. Mitigations in place: `core/cli` parser-tree contract
  (every flag is typed; every value validated by argparse); D12
  coercer discipline prevents bool-shaped int silent coercion;
  intake handlers validate JSON shape before persistence;
  `core/provenance/locator.py` SQL paths use whitelist + nosec
  B608 markers (not user-supplied table names).
- **Wave 3.** **Applies.** MCP read-surface tools must not pass
  user-supplied strings into shell commands or SQL string
  concatenation.
- **Mitigation (Wave 3 contract).** All MCP tool implementations
  reuse the existing CLI handler boundaries — no new shell-out
  primitive. SQL paths use the same whitelist + parameterised-
  query pattern as `resolve_locator`.
- **Gap.** Bandit run on the MCP-surface module. Destination:
  v0.3 ship gate adds `uvx bandit -ll -r src/health_agent_infra/mcp/`
  as a release-blocker.

### MCP06 — Intent Flow Subversion (Prompt Injection)

- **Risk.** Malicious instructions embedded in context hijack
  agent operations, redirecting them toward attacker objectives.
  Injection vectors: tool descriptions, tool responses, fetched
  documents, memory entries.
- **Today.** **Applies** broadly to HAI's host-agent context
  surface. SECURITY.md "Out of scope" already names "complete
  prompt-injection defense inside third-party model providers"
  as outside HAI's control. HAI's contribution: structured CLI
  outputs the host agent ingests are *deterministic JSON*; if
  prompt-injection text leaks into that JSON it must round-trip
  through writeback validation, which rejects malformed shape.
  W57 + safety skill provide the "agent cannot deactivate user
  state" hard floor.
- **Wave 3.** **Applies acutely.** An MCP read-surface that
  returns user-narrated free text (intent prose, target prose,
  review-outcome prose) is a **direct injection conduit** —
  prose authored by the user can later be ingested by the host
  agent and influence its next action.
- **Mitigation (Wave 3 contract).** MCP read-surface returns
  structured fields, not raw prose, where possible. When prose
  is returned, it is escaped (no markdown rendering on the wire;
  no embedded tool-call shapes). The W52 weekly-review surface
  authored in v0.2.0 is already designed with W58D factuality-
  gate constraints; that gate's "qualitative atom non-factual"
  invariant becomes the MCP-surface contract too.
- **Gap.** Mechanical injection-detection on prose lanes.
  Destination: v0.4 W-INJ-MITIGATION (proposed; not yet
  scheduled).

### MCP07 — Insufficient Authentication & Authorization

- **Risk.** MCP servers / agents fail to verify identities or
  enforce access controls during interactions.
- **Today.** **Not applicable** to MCP. Adjacent concern: HAI is
  single-user by design (per SECURITY.md "Out of scope: multi-
  user installations"); the local trust model assumes a single
  operator with shell access to their own machine.
- **Wave 3.** **Applies.** MCP server must not expose write paths
  to network-reachable callers. The single-user / local-stdio
  posture limits the threat — a malicious co-resident process
  that can speak local stdio to the server is, by SECURITY.md
  scope, already past HAI's trust boundary.
- **Mitigation (Wave 3 contract).** MCP server runs over **local
  stdio only**; never network-bound. Manual install + manual
  registration in the host's user-scoped config (no project-file
  autoload — Check Point precedent). No network listener; no
  HTTP transport.
- **Gap.** None — the local-stdio-only constraint is named in
  the AGENTS.md "Do Not Do" entry already.

### MCP08 — Lack of Audit and Telemetry

- **Risk.** Limited logging and real-time alerting prevent
  detection of unauthorized actions.
- **Today.** **Applies** to HAI generally, with strong
  mitigations: every state mutation flows through the three-
  state audit chain (`proposal_log` → `planned_recommendation` →
  `daily_plan` + `recommendation_log`), reconciled by
  `hai explain`. `runtime_event_log` records command-level
  outcomes. `data_quality_daily` records freshness and coverage.
- **Wave 3.** **Applies.** MCP read-surface invocations must be
  logged at the same grain as CLI invocations, so an auditor
  reading `runtime_event_log` cannot tell which surface the
  request originated from without the MCP-source field telling
  them.
- **Mitigation (Wave 3 contract).** Every MCP tool invocation
  emits a `runtime_event_log` row with `command='mcp:<tool>'`
  and `source='mcp_local_stdio'`. Existing audit-chain probes
  in `hai explain` extend to MCP-driven mutations should any
  ever ship.
- **Gap.** Concrete `runtime_event_log` row shape for MCP origin.
  Destination: v0.3 migration adds (or reuses) the source
  enumeration to include `mcp_local_stdio`.

### MCP09 — Shadow MCP Servers

- **Risk.** Unapproved MCP deployments operate outside
  organisational governance; default credentials, permissive
  configs.
- **Today.** **Not applicable** to MCP. Adjacent concern: HAI's
  packaged-as-a-wheel posture means a "shadow HAI" is just a
  manually-installed copy with whatever creds the user typed in
  themselves.
- **Wave 3.** **Applies.** A user could run multiple HAI MCP
  servers (e.g., one per state DB) without realising both
  are reachable.
- **Mitigation (Wave 3 contract).** MCP server is single-instance
  by design — namespaced by state DB path, refuses to start a
  second instance for the same DB. `hai capabilities --json` is
  extended (per W-30 v0.2.3 schema freeze) to declare the MCP
  surface presence so external auditors can detect shadow
  instances.
- **Gap.** Concurrency check on server startup. Destination:
  v0.3 W-MCP-SINGLE-INSTANCE.

### MCP10 — Context Injection & Over-Sharing

- **Risk.** Shared / insufficiently-scoped context windows expose
  sensitive information from one task or user to another.
- **Today.** **Not applicable** to MCP; partially applicable to
  HAI's host-agent surface — anything the user pastes into a host
  agent prompt is shared with the host's provider per SECURITY.md
  "Host-agent caveat" disclosure.
- **Wave 3.** **Applies.** The MCP read-surface returns data
  derived from local SQLite — body composition, training history,
  goal prose. If that data crosses an MCP boundary into a host
  agent's session memory, the host agent then governs its
  retention.
- **Mitigation (Wave 3 contract).** MCP tool responses include
  only the data the tool was *asked for* — no implicit
  preloading of unrelated fields. The host agent's governance
  applies to whatever crosses the boundary; HAI's contract is to
  not over-share at the response level. SECURITY.md "Host-agent
  caveat" already names this disclosure obligation.
- **Gap.** Per-tool response-shape contract. Destination: v0.3
  PLAN authoring sets the per-tool minimum-disclosure shape.

---

## 4. Cross-cycle dependencies

| Concern | Destination cycle | Note |
|---|---|---|
| MCP read-surface lands | v0.3 (per strategic plan v2 §10 Wave 3) | This doc is the pre-condition for that PLAN's audit. |
| Token redaction tests on MCP responses | v0.3 (MCP01 mitigation) | Release-blocker for v0.3. |
| Capability-manifest `write_path: false` markers | v0.3 (MCP02 mitigation) | Pairs with v0.2.3 schema freeze. |
| SBOM publication | v0.3 (MCP04 mitigation) | New `docs/hai/sbom.md`. |
| Bandit on `src/health_agent_infra/mcp/` | v0.3 (MCP05 mitigation) | New ship gate. |
| Mechanical prose injection-detection | v0.4 (MCP06 mitigation) | New workstream W-INJ-MITIGATION (not yet scheduled). |
| `runtime_event_log` MCP source enumeration | v0.3 (MCP08 mitigation) | Migration delta. |
| Single-instance check on MCP startup | v0.3 (MCP09 mitigation) | New workstream W-MCP-SINGLE-INSTANCE. |
| Per-tool minimum-disclosure shape contract | v0.3 (MCP10 mitigation) | Authored at PLAN time. |

The "all gaps land at v0.3" pattern is intentional: v0.3 is where
the surface itself ships, so every applies-when-Wave-3 mitigation
is a v0.3 release-blocker. v0.4 covers second-order injection
mitigations that need empirical evidence to design.

---

## 5. What this doc does **not** do

- Does not implement any MCP surface. v0.3 territory.
- Does not change `AGENTS.md` "Do Not Do" entries — those are
  settled per post-v0.1.13 strategic research and re-affirmed
  here. The MCP autoload prohibition stays as authored.
- Does not extend SECURITY.md. SECURITY.md's "Scope of trust"
  + "What counts as a vulnerability" sections remain the
  authoritative public-facing surface.
- Does not declare the project compliant with OWASP MCP Top 10.
  Compliance presupposes a surface to audit; HAI doesn't have one
  yet. This doc maps the *posture* the surface will inherit when
  it lands.

---

## 6. Cross-references

- **`SECURITY.md`** — project-root threat model, vulnerability
  reporting, scope of trust + out-of-scope.
- **`docs/hai/privacy.md`** — data-handling posture,
  "Host-agent caveat" disclosure for HAI users running over
  Claude Code / Codex / hosted LLMs.
- **`AGENTS.md`** "Do Not Do" entries (post-v0.1.13 additions):
  the MCP autoload prohibition + the Strava-prohibition + the
  autonomous-threshold-mutation prohibition. All three are
  load-bearing for Wave-3-and-beyond posture.
- **`reporting/plans/post_v0_1_13/strategic_research_2026-05-01.md`**
  §15-§18 — the original CVE chain + OWASP analysis that
  produced the AGENTS.md additions.
- **`reporting/plans/post_v0_1_13/cycle_proposals/CP-DO-NOT-DO-ADDITIONS.md`** —
  the cycle proposal that landed the additions.
- **`reporting/plans/strategic_plan_v1.md`** §10 + post-v0.1.18
  `strategic_plan_v2.md` §7 — Wave 3 destination for MCP read-
  surface.

---

*W-MCP-THREAT closes when this doc lands + the v0.3 PLAN-audit
prerequisite is satisfied. The gap table in §4 becomes the
v0.3 cycle's MCP-related release-blocker shopping list.*
