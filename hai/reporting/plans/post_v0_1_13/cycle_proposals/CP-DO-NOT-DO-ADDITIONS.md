# CP-DO-NOT-DO-ADDITIONS — Three additions to AGENTS.md "Do Not Do"

**Cycle:** v0.1.14 (or doc-only hotfix earlier).
**Author:** Claude (delegated by maintainer).
**Codex verdict:** applied at v0.1.14 D14 round 1
(PLAN_COHERENT_WITH_REVISIONS); 3 bullets applied to AGENTS.md
"Do Not Do" 2026-05-01 pre-cycle. F-PLAN-09 surfaced a missed
expansion-table sweep: strategic_plan §8.2 still listed Strava as
v0.3 importer candidate; corrected at v0.1.14 D14 round 1 to
"Hevy / MyFitnessPal only; Strava prohibited."
**Application timing:** at v0.1.14 PLAN.md authoring or as a v0.1.13.x
doc-only hotfix — adds three bullets to AGENTS.md §"Do Not Do" (lines
384-400).
**Source:** Strategic-research report 2026-05-01 §18 anti-pattern
table, §15 D-4, §17 Sc-5. Codex round-1 audit confirmed; round-2
audit did not flag.

---

## Rationale

Three anti-patterns surfaced by the post-v0.1.13 strategic research
each have:

1. A named-vendor failure mode in the public landscape.
2. No explicit prohibition in current AGENTS.md "Do Not Do" (the list
   at lines 384-400 covers nutrition, micronutrients, write paths,
   wearable sources, cli.py split, etc., but not these three).
3. Risk of being added under maintainer pressure without explicit
   prohibition.

The three additions:

### Addition 1 — Strava-anchored data path

Strava's November 2024 API agreement explicitly prohibits AI/ML use
of Strava data; intervals.icu was specifically named as a partner in
conflict.

**Source:** https://press.strava.com/articles/updates-to-stravas-api-agreement
(verify current at application time — Strava ToS may have evolved).

Adding Strava as an HAI data source — directly or as an upstream of
intervals.icu — would put HAI in violation of a vendor's published
ToS. Existing AGENTS.md D5 ("Garmin Connect is not the default live
source") covers a different concern (rate limiting); it does not
prohibit Strava.

### Addition 2 — MCP autoload from project files

CVE-2025-59536 / CVE-2026-21852 (Check Point research, 2026): Claude
Code's project-file MCP autoload was exploited to hijack
`ANTHROPIC_BASE_URL` and exfiltrate Anthropic API keys. The exploit
chain depends on a host agent auto-loading MCP-server configurations
from `.claude/settings.json` or equivalent.

**Source:** https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/

HAI runs *inside* Claude Code as the maintainer's daily-driver loop
(per AGENTS.md "Claude Code Specifics"). HAI must never ship a
mechanism that auto-loads MCP servers from a project file (e.g., a
`.claude/settings.json` that references a hai-managed MCP server, or
any future MCP exposure that uses project-file discovery).

The existing "Do not bypass the `hai` CLI for mutations" + governance
invariant #4 (local-first posture) cover related ground but do not
explicitly name MCP autoload as prohibited.

### Addition 3 — Threshold mutation without explicit user commit

Settled decision D13 (v0.1.11) describes the threshold-injection seam
as trusted-by-design *for tests*, with `core.config.load_thresholds`
validating user-TOML at the boundary. W57 governance invariant says
the agent cannot deactivate user state without explicit user commit.

The strategic research report §18 surfaces a related anti-pattern not
yet explicitly prohibited: **automatic threshold mutation by an LLM
agent without an explicit user commit step.** This is the v0.7
governed-adaptation surface in reverse — without explicit commit,
threshold drift becomes a hidden learning loop, which ROADMAP.md
"Explicitly Out Of Scope" already prohibits in spirit but not in
the AGENTS.md operating contract.

The AgentSpec literature (arXiv 2503.18666) names "deterministic
guardrails before exposed mutation surface" as the runtime-
enforcement pattern HAI's skill-vs-code boundary instantiates.

## Current AGENTS.md text (verbatim, verified on disk 2026-05-01)

`AGENTS.md:384-400`:

```
## Do Not Do

- Do not bypass the `hai` CLI for mutations.
- Do not compute bands, scores, R-rules, or X-rule firings inside a skill.
- Do not make clinical claims.
- Do not generate training or diet plans.
- Do not deactivate user-authored state without explicit user commit.
- Do not import from `skills/` inside Python runtime code.
- Do not add a write path that bypasses the three-state audit chain.
- Do not open a PR or push autonomously.
- Do not add a wearable source until the per-domain evidence contract is
  broadened.
- Do not split `cli.py` or freeze the capabilities manifest schema before
  their scheduled cycles (v0.1.14 / v0.2.0). (Origin: v0.1.12 CP1 + CP2.)
- Do not add micronutrient or food-taxonomy features.
- Do not treat raw SQLite reads as the normal inspection surface; use
  `hai today`, `hai explain`, and `hai doctor`.
```

## Proposed delta — append three bullets

After the final bullet ("Do not treat raw SQLite reads..."), append:

```
- Do not anchor a data path on Strava — directly or via an upstream
  that proxies Strava data. Strava's Nov 2024 API agreement
  prohibits AI/ML use of Strava data; intervals.icu was specifically
  named. (Origin: post-v0.1.13 strategic research §15 D-4.)
- Do not ship a mechanism that auto-loads MCP servers from project
  files (e.g., `.claude/settings.json` referencing a hai-managed MCP
  server). HAI runs inside Claude Code; CVE-2025-59536 /
  CVE-2026-21852 (Check Point) demonstrate the project-file
  autoload + token-exfiltration chain. Manual install + local stdio
  is the only allowed exposure path. (Origin: post-v0.1.13
  strategic research §17 Sc-5.)
- Do not allow automatic threshold mutation by an LLM agent without
  an explicit user-commit step. The v0.7 governed-adaptation
  surface requires user approval per recommendation; any drift
  toward "the agent retunes thresholds based on outcomes" is a
  hidden learning loop, prohibited by ROADMAP.md "Explicitly Out
  Of Scope" + W57 governance invariant. (Origin: post-v0.1.13
  strategic research §18.)
```

## Affected files

- `AGENTS.md` §"Do Not Do" — three new bullets appended.
- `reporting/plans/strategic_plan_v1.md` — optional cross-reference
  in §10 / §11 if the maintainer wants discoverability.

## Dependent cycles

- **v0.1.14**: bullets land at v0.1.14 PLAN authoring (or as a
  v0.1.13.x doc-only hotfix if the maintainer prefers).
- **v0.3+ MCP cycles**: the MCP-autoload bullet becomes load-bearing
  when MCP exposure ships at v0.4-or-v0.5.
- **v0.7 governed-adaptation**: the threshold-mutation bullet
  defines the boundary the v0.7 cycle must implement.

## Acceptance gate

- `accepted`: AGENTS.md "Do Not Do" gains the three bullets.
- `accepted-with-revisions`: bullet language tightened or merged
  with existing bullets. The three load-bearing claims (no Strava,
  no MCP autoload, no threshold mutation without commit) must each
  be explicitly preserved.
- `rejected`: AGENTS.md unchanged. CP archived. The three anti-
  patterns remain implicit prohibitions inferable from existing
  invariants but not explicitly stated. Risk: a future CP
  legitimately proposing one of these (e.g., a regulator change
  reopening Strava use) finds nothing to override.

## Round-N codex verdict

**Applied at v0.1.14 D14 round 1 (PLAN_COHERENT_WITH_REVISIONS,
2026-05-01).** 3 bullets applied to AGENTS.md "Do Not Do" 2026-05-01
pre-cycle. F-PLAN-09 surfaced a missed expansion-table sweep:
strategic_plan §8.2 still listed Strava as v0.3 importer candidate;
corrected at v0.1.14 D14 round 1 to "Hevy / MyFitnessPal only;
Strava prohibited."
