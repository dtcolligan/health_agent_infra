# Codex External Audit — v0.1.11 PLAN.md (pre-cycle plan review)

> **Why this round.** v0.1.11 PLAN.md was authored 2026-04-27 alongside
> the post-v0.1.10 strategic + tactical planning tree, then revised
> twice on 2026-04-28 to absorb 7 demo-run findings into the cycle.
> Scope grew from 14 to 19 workstreams; estimate from 15-20 to 20-27
> days. **Before opening the cycle, the plan goes through a Codex
> external review.** New step in the cycle pattern (compare to v0.1.10,
> where Codex reviewed implementation only).
>
> **Cycle position.** Pre-PLAN-open. Phase 0 bug-hunt has not started.
> No code has changed against this PLAN. The audit is on the *plan
> document itself* — its coherence, sequencing, sizing honesty, and
> hidden coupling. **No code changes are in scope.**
>
> **Maintainer rationale (2026-04-28).** *"I think Codex should also
> audit the plan."* — bringing external review into the planning
> phase, not just the implementation phase. May graduate to a
> permanent settled decision (D14) if the cycle finds it valuable.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main
git log --oneline -5
# expect: most recent should mention v0.1.10 ship; v0.1.11 PLAN.md edits in working tree
ls reporting/plans/v0_1_11/
# expect: PLAN.md, codex_plan_audit_prompt.md (this file)
```

If any don't match, **stop and surface the discrepancy**. Ignore any
tree under `/Users/domcolligan/Documents/`.

---

## Step 1 — Read the orientation artifacts

In order:

1. **`AGENTS.md`** — operating contract. Pay special attention to:
   - "Governance Invariants" (W57, three-state audit chain,
     review-summary bool-as-int hardening, D12 threshold-coercer
     discipline).
   - "Settled Decisions" (D1-D12, including D11 pre-PLAN bug-hunt
     pattern). Notice that this audit may seed a D14.
   - "Do Not Do" (no skill→runtime imports, no autonomous plan
     generation, no clinical claims).
2. **`reporting/plans/strategic_plan_v1.md`** — Wave-1 thesis (audit-
   chain integrity), where v0.1.11 sits in the 12-24 month vision.
3. **`reporting/plans/tactical_plan_v0_1_x.md`** § 2 — original
   v0.1.11 framing (pre-revision); compare to the current PLAN.md
   to see how much the cycle grew.
4. **`reporting/plans/v0_1_10/audit_findings.md`** — the source of
   v0.1.10's deferred items; v0.1.11 absorbs them.
5. **`reporting/plans/v0_1_10/RELEASE_PROOF.md`** — test surface
   baseline (2202 passed) the v0.1.11 ship gate references.
6. **`reporting/plans/post_v0_1_10/demo_run_findings.md`** — the
   2026-04-28 demo run that surfaced 7 findings, all now in v0.1.11.
   §§ 1-5 = findings; § 6 = routing table (the audit lever).
7. **`reporting/plans/v0_1_11/PLAN.md`** — the artifact under review.

Cross-check that everything PLAN.md cites actually exists in the
tree. Broken cross-references count as findings.

---

## Step 2 — The audit questions

### Q1 — Cycle thesis coherence

v0.1.11's stated thesis is **audit-chain integrity** (W-E + W-F are
release-blocker class), with persona expansion (W-O), property tests
(W-P), and 7 demo-finding fold-ins riding along.

- Do the 19 workstreams add up to the stated thesis, or has the
  cycle quietly become a grab-bag where the thesis is no longer the
  centre of mass?
- The release-blocker class is W-E + W-F. Does any other workstream
  *also* warrant blocker class (e.g., is W-V's DB-path resolver seam
  load-bearing enough that a regression there blocks ship)?
- Does the W-S extension (capabilities expose proposal contracts)
  conflict with the v0.1.10 settled decision W30 ("do not freeze
  the capabilities manifest schema yet")? PLAN.md claims the
  extension is additive and backwards-compatible — verify by reading
  the existing `hai capabilities --json` shape and confirm.

### Q2 — Sequencing honesty

The recommended sequence (§ 4) lists 17 numbered items spanning
"smoke-clearer (W-N, 30 min)" through "Codex round 1 audit."

- Are the dependencies right? Specifically:
  - W-V's "land the resolver seam early" claim (item #12) — does any
    earlier workstream actually need that seam?
  - W-Z's hard-dependency on W-V — does the demo-flow doc *need*
    `hai demo start` to exist, or is that a soft preference?
  - W-W's adjacency to W-E (both consume "latest accepted state") —
    is the "don't pre-engineer a shared abstraction" guidance
    realistic, or will engineers race to share by accident?
- Is the persona harness re-run (item #18) gated on every fix
  landing? Or could a partial harness re-run mid-cycle catch
  problems earlier?

### Q3 — Effort estimate honesty

Per-workstream sizing:
- W-V (`hai demo` mode): 2-4 days. Touches *every* CLI command's
  DB-path resolver, plus a new subcommand group, plus persona
  fixture loading, plus three new tests, plus auth-refusal logic
  in demo mode. **Is this under-scoped?** What would push it to
  4-5 days?
- W-W (gaps state-snapshot fallback): 1-2 days. New flag, new
  derivation path, new threshold, four new tests. **Realistic?**
- W-X / W-Y / W-Z: 0.5 day, 2 hrs, 0.5 day. **Are the small ones
  honest, or rounding-down ones that hide test-writing time?**
- Cycle total: 20-27 days, "4-5 calendar weeks." **Does the upper
  bound (27d / 5w) leave any headroom for unexpected bugs surfaced
  by W-P property tests?**

### Q4 — Hidden coupling

The risk register (§ 5) names three couplings:
- W-E schema migration risk (highest).
- W-V × W-O fixture contract coordination.
- W-W staleness threshold tuning.

What's missing? Probe at minimum:
- **W-V × demo-mode-leakage.** What happens if demo mode detection
  silently fails — could the real DB get written to mid-demo? Does
  PLAN.md prescribe a hard guard (e.g., "if marker file fails to
  parse, refuse all CLI commands until cleanup") or rely on the
  resolver to do the right thing?
- **W-W × race condition.** If a `hai intake gym` lands while
  `hai intake gaps --from-state-snapshot` is reading, do the gaps
  reflect the partial state? Is gap-detection a snapshot read or
  a live read?
- **W-S × capabilities manifest schema.** PLAN.md says the new
  `domain_proposal_contracts` block is additive. Is the manifest's
  existing schema actually open for additive extension, or does it
  have a `closed: true` flag somewhere?
- **W-V × auth refusal in demo mode.** PLAN.md says `hai auth *`
  refuses in demo mode. What about `hai memory set`? `hai intent
  archive`? Is the refusal list exhaustive, or specifically scoped
  to credential-touching commands?

### Q5 — Acceptance criterion bite

For each W-id, read its acceptance criterion:
- Is it specific enough to fail? Or is it aspirational?
- Examples to spot-check:
  - W-B: "persona matrix findings drop from 3 → ≤ 1" — measurable.
  - W-V: "real DB checksum stable across the entire session" —
    measurable.
  - W-Z: "doc reads coherently top-to-bottom" — **how is this
    falsifiable?** Better criterion would be e.g., "every command
    snippet in the doc executes without modification on a current
    `hai` install."
- Find any acceptance criterion that's hand-wavy and propose a
  concrete falsifier.

### Q6 — Settled-decision integrity

PLAN.md sits inside the AGENTS.md operating contract. Does the
proposed scope respect every settled decision D1-D12?

- **D1** (Phase 4 plans authored alongside v0.1.10) — does v0.1.11
  PLAN.md reference and respect those plans?
- **D11** (pre-PLAN bug-hunt phase) — § 1 of PLAN.md references
  Phase 0; is the bug-hunt scope clear, or does the cycle skip it?
- **D12** (every threshold consumer uses `core.config.coerce_*`) —
  W-W's new threshold (`gap_detection.snapshot_staleness_max_hours`)
  must use `coerce_int`. PLAN.md says this explicitly; verify
  against the rest of the new code paths (W-V, W-X) for any
  threshold-consumer site that's not flagged.

### Q7 — What the plan doesn't say

Surface the absences:
- Does PLAN.md document how a maintainer would **abort** the cycle
  partway through if an early finding (e.g., W-K bandit reveals a
  real SQL-injection vector) requires reshaping?
- Does it describe what success means for the **demo-finding fold-
  ins specifically** — i.e., would Dom be able to run the same
  2026-04-28 demo cleanly post-cycle?
- Are there workstreams that should explicitly include a
  capabilities-manifest update in their files-changed list? (W-V,
  W-W, W-X, W-Y all add new flags/commands.)

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_11/codex_plan_audit_response.md` matching the
v0.1.10 audit-response convention:

```markdown
# Codex Plan Audit Response — v0.1.11 PLAN.md

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS |
PLAN_INCOHERENT (state which workstreams need rework before open)

**Round:** 1 / 2 / 3 (escalates if revisions warrant another pass)

## Findings

### F-PLAN-01. <short title>

**Q-bucket:** Q1 / Q2 / Q3 / Q4 / Q5 / Q6 / Q7
**Severity:** plan-incoherence | sizing-mistake | dependency-error |
acceptance-criterion-weak | hidden-coupling | settled-decision-conflict |
absence | nit
**Reference:** PLAN.md § X.Y, line N (or "absent")
**Argument:** <why this is a finding, with citations>
**Recommended response:** <revise PLAN.md as follows / accept and
note as known limitation / disagree with reason>

### F-PLAN-02. ...

## Open questions for maintainer

(Things Codex couldn't decide without Dom's input.)
```

Each finding must be triageable. Vague feedback ("the plan feels
crowded") is not a finding; "W-V at 2-4 days under-scopes the
auth-refusal contract because there are 8 mutating commands and
PLAN.md only enumerates 2" is a finding.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle as written.
- **PLAN_COHERENT_WITH_REVISIONS** — open the cycle after named
  revisions land. Revisions list every must-fix finding.
- **PLAN_INCOHERENT** — do not open. Re-author the named sections
  before re-running this audit.

---

## Step 5 — Out of scope

- v0.1.10 implementation (already audited across 3 rounds, shipped
  to PyPI).
- Code changes against the v0.1.11 PLAN (Phase 0 hasn't started).
- v0.1.12+ scope (named in tactical_plan_v0_1_x.md but not in this
  PLAN's commitments).
- The strategic + tactical + eval + success + risks docs (Phase 4
  audit at `reporting/plans/post_v0_1_10/phase_4_audit_plan.md`
  covers those separately).

---

## Step 6 — Cycle pattern (this audit's place)

```
Pre-PLAN-open:
  [NEW] Codex plan audit ← you are here
  [NEW] Maintainer response to plan audit
  [NEW] PLAN.md revised if warranted

Phase 0 (D11):
  Internal sweep
  Audit-chain probe
  Persona matrix
  Codex external bug-hunt audit
  → audit_findings.md consolidates

PLAN.md → opens cycle (post plan-audit)

Implementation rounds:
  Codex round 1 (post-implementation)
  Maintainer response
  ... until SHIP / SHIP_WITH_NOTES

RELEASE_PROOF.md + REPORT.md
```

Estimated audit duration: 1-2 sessions. Smaller than a code audit
because there's no implementation to verify, no tests to re-run.
Larger than the Phase 4 audit because PLAN.md's claims are operationally
load-bearing — a sizing miss costs the cycle real days.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_11/codex_plan_audit_response.md` (new) —
  Codex's findings.
- `reporting/plans/v0_1_11/PLAN.md` (revisions, if warranted) —
  maintainer + Claude apply revisions in response to findings.
- `reporting/plans/v0_1_11/codex_plan_audit_round2_*.md` (if a
  second round is required).

**No code changes.** No test runs. No state mutations.
