# Codex Plan Audit Response - v0.1.12 PLAN.md

**Round:** 2  
**Reviewed artifact:** `reporting/plans/v0_1_12/PLAN.md` after
`codex_plan_audit_response_round_1_response.md`  
**Verdict:** `PLAN_COHERENT_WITH_REVISIONS`

The round-1 response materially improved the PLAN: all ten findings
were accepted, CP approval semantics are now explicit, CP5 is internally
consistent, CP6 is no longer both deferred and required, Phase 0 is
scoped, and W-FBC is more honest about the missing per-domain primitive.

This is still not quite settled. The remaining issues are second-order
contradictions introduced or exposed by the revisions. None require a
strategic reset, but they should be fixed before opening Phase 0.

---

## Findings

### F-PLAN-R2-01 - W-Vb acceptance command asks for persona replay and blank replay simultaneously

**Question bucket:** Q4 hidden coupling, Q5 acceptance bite  
**Severity:** High for plan coherence; medium implementation risk

The revised PLAN repeatedly makes the clean-wheel demo proof depend on:

- `hai demo start --persona p1 --blank` seeding proposals and reaching
  synthesis (`PLAN.md:205-210`).
- The packaging test running the same command as subprocess
  (`PLAN.md:227-232`).
- The top-level ship gate requiring the same command
  (`PLAN.md:684-686`).

Current CLI semantics say the opposite. In `cmd_demo_start`,
`--blank` wins over `--persona`:

- `src/health_agent_infra/cli.py:6346-6350` sets `persona = None`
  whenever `args.blank` is true.
- `src/health_agent_infra/cli.py:8530-8537` describes `--persona` as
  forward-compatible and not yet loading a fixture.
- `src/health_agent_infra/cli.py:8540-8543` describes `--blank` as
  "Force an empty session (no persona)."

So the PLAN's acceptance command currently encodes mutually exclusive
intent: seeded persona replay and forced empty replay. That is not just
a syntax nit, because the test could be implemented to preserve current
`--blank` semantics and then fail the PLAN's own intended proof, or the
implementation could silently change the meaning of `--blank` and break
the v0.1.11 boundary-stop contract.

**Required revision:** choose one of two shapes:

1. Persona replay command is `hai demo start --persona p1`; `--blank`
   remains explicit empty-session mode.
2. If `--persona p1 --blank` is intentionally the new spelling, PLAN.md
   must say W-Vb changes `--blank` semantics, and acceptance must include
   a regression proving empty-session mode still exists under a different
   spelling.

I recommend option 1. It matches the current CLI contract and makes the
two demo modes legible.

### F-PLAN-R2-02 - W-N fallback ladder still conflicts with the top-level ship gate

**Question bucket:** Q2 sequencing honesty, Q3 effort estimate honesty,
Q5 acceptance bite  
**Severity:** High for ship-gate coherence

The W-N section now has a reasonable fallback ladder:

- Count <= 80: enforce full broader gate (`PLAN.md:296-297`).
- Count 80-150: ship a narrowed sqlite3 `ResourceWarning` gate and defer
  residual categories (`PLAN.md:298-302`).
- Count > 150: defer the broader gate and keep the v0.1.11 narrow
  `PytestUnraisableExceptionWarning` gate (`PLAN.md:303-306`).

But the global ship gate still unconditionally requires:

`uv run pytest verification/tests -W error::Warning -q`

at `PLAN.md:684`.

That command is stricter than all fallback branches except the <=80
branch, and it is not the command W-N itself says will ship in the
80-150 or >150 cases. This reintroduces the round-1 problem in a
different location: the workstream has conditional scope, but the
release gate does not.

**Required revision:** make the ship gate conditional on the W-N fork
decision. For example:

`Pytest warning gate | command chosen by W-N fallback decision exits 0;
full -W error::Warning only if the <=80 branch is selected; narrowed
sqlite3 ResourceWarning or v0.1.11 PytestUnraisableExceptionWarning gate
otherwise, with RELEASE_PROOF named-defer.`

### F-PLAN-R2-03 - W-PRIV still cites a nonexistent helper path and proposes an awkward command shape

**Question bucket:** Q3 effort estimate honesty, Q5 acceptance bite,
Q8 provenance skepticism  
**Severity:** Medium

The response says the `clear_*` helpers exist and only a CLI surface is
missing. That premise is basically right, but the revised PLAN points to
the wrong module:

- `PLAN.md:346-350` says `clear_garmin()` and
  `clear_intervals_icu()` already exist in `core/credentials.py`.
- There is no `src/health_agent_infra/core/credentials.py`.
- The actual helpers are methods in
  `src/health_agent_infra/core/pull/auth.py:171` and
  `src/health_agent_infra/core/pull/auth.py:261`.

The command shape also needs a deliberate choice. The PLAN proposes
`hai auth --remove [--source SOURCE]` (`PLAN.md:361-363`), but the
current CLI has required `auth` subcommands (`cli.py:6505-6506`) and
current children are `auth garmin`, `auth intervals-icu`, and
`auth status` (`cli.py:6508-6560`). A parent-level `--remove` option is
possible, but it works against the existing parser shape.

**Required revision:** cite the real helper location and choose the CLI
grammar explicitly. I recommend `hai auth remove [--source garmin|intervals-icu|all]`,
because it fits the existing required-subcommand model and avoids making
`auth` both a subcommand namespace and an action flag.

### F-PLAN-R2-04 - W-FBC says F-B-04 closes in-cycle, but acceptance only proves a one-domain prototype

**Question bucket:** Q1 thesis coherence, Q5 acceptance bite  
**Severity:** Medium

The release thesis still says v0.1.12 closes every named-deferred item,
including F-B-04 (`PLAN.md:34-37`). The catalogue also lists W-FBC as
the in-cycle F-B-04 closure (`PLAN.md:64-67`), and the carry-over table
marks F-B-04 as in-cycle at `PLAN.md:154`.

The revised W-FBC body is more cautious: it makes the workstream
design-first, defaults toward option A, and implements only a recovery
prototype (`PLAN.md:388-404`). Acceptance likewise requires only the
policy doc, the recovery prototype, and the override flag
(`PLAN.md:425-433`). The risk register says v0.1.12 "ships option A by
default (all domains re-propose) with one-domain prototype (recovery)"
(`PLAN.md:716-719`).

That may be a valid scoped implementation, but it is not clearly the
same thing as closing a six-domain domain-coverage drift finding. If
option A is selected, "all domains re-propose" should be a global
synthesis behavior and acceptance should prove at least representative
coverage beyond recovery. If only recovery is implemented, the PLAN
should stop claiming F-B-04 is closed and should name the residual
multi-domain closure explicitly.

**Required revision:** pick one:

1. Keep "F-B-04 closed in v0.1.12" and require option-A behavior to be
   implemented and tested across all six domains, with recovery only as
   the first implementation slice.
2. Reclassify W-FBC as design plus prototype, and move full F-B-04
   closure to a named v0.1.13 defer.

Given the release is already 13-20 days, option 2 is probably the more
honest plan unless Dom wants F-B-04 to be one of the heavier v0.1.12
items.

### F-PLAN-R2-05 - CP4 premise should say "underspecified MCP row," not "no MCP exposure row"

**Question bucket:** Q6 settled-decision integrity, Q8 provenance
skepticism  
**Severity:** Low

CP4 is directionally right: MCP should be staged and gated by a threat
model before any read surface ships. The revised text overstates the
current-doc premise, though:

- PLAN says strategic plan section 10 "contains no MCP exposure row"
  (`PLAN.md:552-553`).
- The strategic plan already has "Wave 3 - MCP surface + extension
  contract" (`strategic_plan_v1.md:444`) and says "at v0.4 (when MCP
  surface ships)" in the contributor-governance branch
  (`strategic_plan_v1.md:632`).

The real problem is not absence. It is that the current strategic plan
has a broad MCP surface milestone without CP4's staged read-surface
design, provenance import contract, least-privilege model, or threat
model gate.

**Required revision:** change the premise to "current strategic plan
mentions MCP surface at Wave 3/v0.4 but lacks staged exposure and
security gates." The proposed CP4 delta can otherwise stand.

---

## CP Quick Verdicts After Round 2

| CP | Round-2 verdict | Note |
|---|---|---|
| CP1 | accept | Strike-text issue fixed; paired with CP2. |
| CP2 | accept | Strike-text issue fixed; `cli.py` split remains governance proposal, not unilateral implementation. |
| CP3 | accept | Fallback if rejected is now explicit. |
| CP4 | accept-with-revision | Security gate is good; current strategic-plan premise needs wording correction. |
| CP5 | accept | Single substantial v0.2.0 with shadow-by-default W58 flag resolves the round-1 contradiction. |
| CP6 | accept | Authored in v0.1.12, applied in v0.1.13; no longer deferred-and-required. |

---

## Open Questions For Dom

1. Should W-Vb persona replay use `hai demo start --persona p1`
   without `--blank`? My recommendation: yes.
2. Should W-PRIV use `hai auth remove` rather than `hai auth --remove`?
   My recommendation: yes.
3. Is W-FBC intended to close F-B-04 fully in v0.1.12, or is a design
   doc plus recovery prototype enough? My recommendation: name the
   residual as v0.1.13 unless all-domain option-A behavior is made a
   required acceptance gate.

---

## What Would Improve The Verdict

`PLAN_COHERENT` requires:

- W-Vb commands and tests no longer combine `--persona` with `--blank`
  unless the PLAN explicitly changes the blank-session contract.
- The global pytest warning ship gate mirrors the W-N fallback branch
  selected at workstream start.
- W-PRIV cites `core/pull/auth.py` and chooses a CLI grammar compatible
  with the current `auth` subcommand structure.
- W-FBC either proves full F-B-04 closure or honestly names the residual
  closure as deferred.
- CP4's current-doc premise is corrected from "no MCP exposure row" to
  "MCP row exists but is not staged or security-gated."

No tests were run for this audit round; this was a document/source
coherence review only.
