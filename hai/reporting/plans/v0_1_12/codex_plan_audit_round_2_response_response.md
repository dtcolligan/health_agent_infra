# Maintainer Response — Codex Plan Audit round 2, v0.1.12 PLAN.md

**Author.** Claude (delegated by maintainer).
**Date.** 2026-04-29.
**Codex verdict.** `PLAN_COHERENT_WITH_REVISIONS`, round 2
(`reporting/plans/v0_1_12/codex_plan_audit_round_2_response.md`).

**This response.** Accepts 5 of 5 round-2 findings. Resolves
3 of 3 open questions per Codex recommendations. PLAN.md
revisions applied inline (this commit). Verified Codex's two
file-level claims (`core/credentials.py` does not exist;
`core/pull/auth.py:171/:261` confirmed) + strategic plan MCP
references at §10 Wave 3 / line 444 confirmed. Round 3 audit
can proceed.

---

## Summary

Round 2 caught the second-order issues round 1's revisions
introduced — exactly the empirical pattern AGENTS.md D14
documents (round 2 typically catches second-order contradictions
introduced by round-1 revisions). Of the five findings:

- **F-PLAN-R2-01 (W-Vb persona+blank)** is a real CLI-semantic
  contradiction; my round-1 rewrite copied the `--blank` from
  the prior version without checking that current CLI semantics
  set `persona = None` whenever `--blank` is true.
- **F-PLAN-R2-02 (W-N ship-gate vs ladder)** is a fallback that
  didn't propagate to §3. Real bug.
- **F-PLAN-R2-03 (W-PRIV path/grammar)** is a citation error I
  inherited from round-1 chat. Codex's round-1 confirmation
  named `core/credentials.py`, which does not exist; the actual
  helpers live in `core/pull/auth.py`. Verified on disk this
  round.
- **F-PLAN-R2-04 (F-B-04 not actually closed)** is the most
  consequential — the cycle theme overstates what W-FBC
  delivers. Reframed as partial-closure with multi-domain
  closure deferred to v0.1.13 W-FBC-2.
- **F-PLAN-R2-05 (CP4 MCP-row premise)** is a provenance error —
  strategic plan §10 *does* have a Wave 3 MCP row at line 444;
  it's underspecified, not absent. Verified on disk this round.

The pattern across the five: most are provenance errors I made
by trusting round-1 chat citations or my own prior framing
rather than re-verifying on disk. Internalising: when the round-
N response touches files, re-verify the file references in the
revised PLAN.

---

## Per-finding dispositions

| F-id | Disposition | PLAN.md revision |
|---|---|---|
| **F-PLAN-R2-01** (W-Vb persona+blank) | accepted, option 1 | Drop `--blank` from persona-replay command in §2.3 (description, files, tests, acceptance). `--blank` retains current "force empty session, no persona" semantics for the boundary-stop demo. §3 ship-gate row updated. |
| **F-PLAN-R2-02** (W-N ship-gate vs ladder) | accepted | §3 ship-gate row reframed: command chosen by W-N fork decision; full `-W error::Warning` only on the ≤80 branch; narrowed sqlite3 ResourceWarning or v0.1.11 narrow gate on the 80-150 / >150 branches; RELEASE_PROOF named-defer if narrowed. |
| **F-PLAN-R2-03** (W-PRIV path/grammar) | accepted | §2.7 path corrected to `core/pull/auth.py:171` and `:261` (verified). CLI grammar changed to `hai auth remove [--source garmin\|intervals-icu\|all]` (subcommand, not flag — fits existing `auth garmin` / `auth intervals-icu` / `auth status` pattern). |
| **F-PLAN-R2-04** (F-B-04 partial closure) | accepted, option 2 | §1.1 theme softened ("close-or-partial-close"). §1.2 W-FBC row clarified. §1.3 adds W-FBC-2 row for v0.1.13. §2.2 W-CARRY F-B-04 disposition reframed to partial-closure. §2.8 W-FBC reframed as design+prototype with explicit multi-domain deferral. §4 risks updated. |
| **F-PLAN-R2-05** (CP4 MCP-row premise) | accepted | §2.10 CP4 premise reframed: "current strategic plan §10 has Wave 3 MCP row at line 444 but lacks staged exposure design (read surface only), provenance import contract, least-privilege read-scope model, and threat-model gate." Proposed delta reframed as extension of the existing row, not addition of a new row. |

---

## Open question resolutions (per Codex recommendations)

**Q1. W-Vb persona-replay command.** Resolution: `hai demo
start --persona p1` (no `--blank`). Matches current CLI
contract. `--blank` retains its current force-empty semantics
for the boundary-stop demo. Acceptance: option 1 from F-PLAN-
R2-01.

**Q2. W-PRIV CLI grammar.** Resolution: `hai auth remove
[--source garmin|intervals-icu|all]`. Subcommand under the
existing `auth` namespace alongside `auth garmin / intervals-
icu / status`. The `--remove` flag form fights the parser
shape (`cli.py:6505-6506` requires `auth` subcommands).

**Q3. W-FBC F-B-04 closure scope.** Resolution: option 2 —
reclassify W-FBC as design + recovery prototype, defer full
F-B-04 closure to v0.1.13 W-FBC-2. The cycle is already 13-20
days; expanding W-FBC to multi-domain implementation + multi-
domain test coverage adds 2-3 days that don't fit cleanly.
The honest plan is to name the residual.

---

## CP1-CP6 quick-verdict response (round 2)

| CP | Codex verdict | Disposition | Action |
|---|---|---|---|
| CP1 | accept | confirmed | No further revision; ready to apply at v0.1.12 ship if PLAN_COHERENT in round 3. |
| CP2 | accept | confirmed | Same; paired with CP1. |
| CP3 | accept | confirmed | Fallback semantics explicit. |
| CP4 | accept-with-revision | accepted | Premise reframed per F-PLAN-R2-05. Security gate language unchanged (non-negotiable). |
| CP5 | accept | confirmed | Single substantial v0.2.0 with shadow-by-default flag — settled. |
| CP6 | accept | confirmed | Author-now / apply-at-v0.1.13 split — settled. |

---

## Verified during this response

- `src/health_agent_infra/core/credentials.py` does not exist
  (Codex F-PLAN-R2-03 verified).
- `src/health_agent_infra/core/pull/auth.py` line 171 contains
  `def clear_garmin(self) -> None:`; line 261 contains
  `def clear_intervals_icu(self) -> None:` — Codex citations
  exact.
- `reporting/plans/strategic_plan_v1.md:444` contains
  `### Wave 3 — MCP surface + extension contract (v0.3–v0.4,
  ~3-4 months)` — Codex F-PLAN-R2-05 citation exact. Line 632
  also references MCP exposure at v0.4.
- AGENTS.md current text for W-29/W-30 settled-decision +
  Do Not Do bullets — unchanged from round 1; no re-verify
  needed.

---

## Round-3 expectation

The PLAN.md revisions in this commit address every round-2
finding. Round 3 should be either:

- `PLAN_COHERENT` (clean) → cycle opens.
- `PLAN_COHERENT_WITH_REVISIONS` (third-order issues) → another
  round.

Empirically the v0.1.11 cycle settled at round 4; v0.1.12 has
been comparable (10 round-1 findings, 5 round-2 findings).
Round 3 should be much smaller — round 2 focused on second-
order contradictions, and the scope-reduction at F-PLAN-R2-04
(option 2 W-FBC reclassification) reduces surface area.

Out of scope for this response: code changes, test runs, CP
deltas applied to AGENTS.md / strategic plan / tactical plan.
Those apply at v0.1.12 ship per CP acceptance gates.
