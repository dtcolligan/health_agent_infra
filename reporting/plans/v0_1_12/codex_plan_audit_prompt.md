# Codex External Audit — v0.1.12 PLAN.md (pre-cycle plan review)

> **Why this round.** v0.1.12 PLAN.md was authored 2026-04-29 by
> Claude as the synthesis of (a) v0.1.11 named-deferred items, (b)
> the post-v0.1.11 reconciliation between Claude's two-pass
> strategy review and Codex's three-pass strategy review
> (`reporting/plans/future_strategy_2026-04-29/reconciliation.md`),
> and (c) maintainer adjudication on the four genuine
> disagreements (D1 v0.2.0 shape, D2 cli.py timing, D3 cycle-weight
> tiers, D4 MCP exposure timing).
>
> **D14 is now a settled decision** (added at v0.1.11 ship). This
> audit is the second exercise of the pattern. Empirical norm:
> 2-4 rounds for a substantive PLAN.
>
> **Cycle position.** Pre-PLAN-open. Phase 0 bug-hunt has not
> started. No code has changed against this PLAN. The audit is on
> the *plan document itself* — its coherence, sequencing, sizing
> honesty, hidden coupling, and especially the **six cycle
> proposals (CP1-CP6)** that reverse or extend AGENTS.md "Settled
> Decisions" D-series.
>
> **What's different from the v0.1.11 audit.**
>
> 1. v0.1.11 was **audit-chain integrity** with two release-
>    blockers (W-E + W-F + W-Va). v0.1.12 has **no release-blocker
>    workstream** by design — it's a "trust repair" cycle where
>    every workstream could in principle slip again.
> 2. v0.1.12 includes a **governance-edit workstream** (W-CP)
>    that authors six cycle proposals. CP1, CP2, CP4, CP5
>    explicitly reverse AGENTS.md "Do not split cli.py" / "Do not
>    freeze the capabilities manifest schema yet" / add a new
>    MCP exposure plan / revise the v0.2.0 shape. **This is the
>    highest-leverage section of the PLAN to audit.**
> 3. v0.1.12 PLAN.md leans on the reconciliation document as a
>    primary source. The reconciliation's §8 self-flags that 4 of
>    8 round-2 research agents failed and several recommendations
>    rest on un-verified primary sources. **Be the independent
>    skeptical pass** on what Claude carried forward into the PLAN.
>
> **Maintainer rationale (2026-04-29).** D14 is settled; this is
> the standard pattern. The reconciliation was Claude-authored; an
> independent Codex pass on the resulting PLAN closes the loop.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: chore/reporting-folder-organisation OR a v0_1_12 cycle
#         branch (check with maintainer if neither)
git log --oneline -5
# expect: most recent should mention v0.1.11 ship (release: v0.1.11);
#         v0.1.12 PLAN.md edits in working tree
ls reporting/plans/v0_1_12/
# expect: PLAN.md, codex_plan_audit_prompt.md (this file)
```

If any don't match, **stop and surface the discrepancy**. Ignore
any tree under `/Users/domcolligan/Documents/`.

---

## Step 1 — Read the orientation artifacts

In order:

1. **`AGENTS.md`** — operating contract. Pay special attention to:
   - "Governance Invariants" (W57, three-state audit chain,
     review-summary bool-as-int hardening, D12 threshold-coercer
     discipline).
   - "Settled Decisions" D1-D14, **especially D11 + D14** (the
     pre-PLAN bug-hunt + pre-cycle plan-audit patterns this audit
     enacts) and **D13** (threshold-injection seam — load-bearing
     for W-D13-SYM).
   - "Do Not Do" — explicit list of currently-forbidden actions.
     **CP1 reverses "Do not split cli.py"; CP2 reverses "Do not
     freeze the capabilities manifest schema yet."** Verify the
     framing in PLAN.md is honest about *which* settled-decision
     bullet each CP reverses.
2. **`reporting/plans/strategic_plan_v1.md`** — Wave-1 thesis. Pay
   attention to **§6.3** which CP6 proposes to rephrase. Read the
   current wording before judging the proposed delta.
3. **`reporting/plans/tactical_plan_v0_1_x.md`** — Pre-reconciliation
   v0.1.12 framing was "Type-checker + security + UX polish."
   Current PLAN reframes as "carry-over closure + trust repair."
   **Is the reframe honest?** Does the tactical plan need updating
   alongside v0.1.12 ship?
4. **`reporting/plans/future_strategy_2026-04-29/reconciliation.md`**
   — the synthesis input for v0.1.12 scoping. Especially:
   - §3 (D1-D4 disagreements + recommended syntheses)
   - §4 (Codex caught these; Claude missed them)
   - §5 (Claude caught these; Codex missed them)
   - §6 (combined action list — items #1-6 are the v0.1.12 must-
     include set)
   - §8 (limitations — 4/8 round-2 research agents failed; named
     un-verified primary sources)
5. **`reporting/plans/v0_1_11/RELEASE_PROOF.md`** — §5 names the
   v0.1.11 named-deferred items. v0.1.12 PLAN's W-CARRY register
   should account for every line.
6. **`reporting/plans/v0_1_11/PLAN.md` § 1.2 + § 2.7** — the
   demo-regression gate v0.1.11 shipped (boundary-stop, isolation-
   replay) that v0.1.12 W-Vb extends to persona-replay.
7. **`reporting/plans/v0_1_12/PLAN.md`** — the artifact under
   review.

Cross-check that everything PLAN.md cites actually exists in the
tree. Broken cross-references count as findings.

---

## Step 2 — The audit questions

### Q1 — Cycle thesis coherence

v0.1.12's stated theme is **carry-over closure + trust repair** —
no release-blocker class, no feature push, governance-edit work
front and centre.

- Do the 10 workstreams add up to that theme, or has the cycle
  drifted? Specifically:
  - W-FBC (F-B-04 supersede domain-coverage drift) is presented
    as a deferred audit-chain item but its resolution involves a
    *semantic policy choice* (the PLAN picks option B with
    `--re-propose-all` override). **Is that policy choice honest
    "carry-over closure" or smuggled-in feature work that
    deserves its own cycle proposal?**
  - W-CP carries six cycle proposals. **Does the cycle thesis
    really hold if the cycle's biggest output is a
    governance-charter rewrite?** Or is there a more honest theme
    framing (e.g., "carry-over closure + governance refresh +
    trust repair")?
- The PLAN claims "no release-blocker workstream by design — every
  item could in principle slip again." Is that true? Probe at
  least:
  - W-Vb fixture-packaging fix (clean wheel install). If a user
    today does `pip install health-agent-infra` and tries `hai
    demo --persona p1`, **what happens?** If it crashes the
    install user, this might be implicitly blocker-class even
    though the PLAN doesn't label it so.
  - W-D13-SYM. If a future contributor adds a 7th-domain policy
    file and the contract test isn't in place, the silent
    bool-as-int seam reopens. Is that blocker-class for *future*
    cycles?

### Q2 — Sequencing honesty

The PLAN does not include a numbered "recommended sequence" §
like v0.1.11 did. **Is that an oversight or intentional?**

If intentional, the dependencies still exist — surface them:

- W-Vb has internal ordering: packaging fix (C3) before persona-
  loading. PLAN.md flags this in §4 (risks). Does the PLAN
  enforce the order in any other way (e.g., wheel-install test
  ordering, separate sub-W-ids)?
- W-AC depends on W-CP because the freshness sweep includes
  AGENTS.md edits the cycle proposals dictate. **Should W-AC be
  the last workstream to land, or split into W-AC-1 (current-
  state cleanup) + W-AC-2 (post-CP delta application)?**
- W-CARRY register depends on every other workstream's
  disposition being known. Should it be authored *last* in the
  cycle, or authored *first* with placeholder dispositions
  filled in as work lands?
- W-CP authoring vs. application: PLAN.md §2.10 says "AGENTS.md
  and strategic plan deltas applied at v0.1.12 ship (not at
  PLAN-author time) so a Codex revision in D14 can still reshape
  them." Is that honest, or does it leave the cycle in a half-
  applied governance state mid-cycle?

### Q3 — Effort estimate honesty

Per-workstream sizing:

- W-N-broader: 3-4 days for "47 ResourceWarning sites." The PLAN
  flags "47 is a lower bound; if audit reveals > 80, split."
  **Is 47 honest?** Probe: run `uv run pytest verification/tests
  -W error::ResourceWarning -q` against the v0.1.11 ship state
  and surface the actual count. If it's > 80, the PLAN's risk
  has already triggered and the workstream should split *now*.
- W-Vb: 3-4 days. Two coupled deliveries — packaging-path fix
  (mechanical) + persona fixture loading (new abstraction). Is
  each priced realistically? What about the wheel-install test
  cost (build wheel, install in venv, run subprocess CLI, assert
  state) — is that included in the estimate?
- W-CP: 1 day for **six cycle-proposal documents**. CP1, CP2,
  CP4, CP5 reverse settled decisions and need to argue the case;
  CP6 is a strategic-plan framing edit. **Is 1 day honest for
  governance prose at this density?**
- W-FBC: 1-2 days. Includes a semantic-policy choice + a new
  test surface. **Realistic, or hiding the design discussion
  cost?**
- Cycle total: 13-20 days. **Does the upper bound (20d) leave any
  headroom for D14 revisions surfacing follow-on work?** v0.1.11
  empirically ran 22-30 days (50-100% over original 15-20d) once
  D14 + Phase 0 findings landed.

### Q4 — Hidden coupling

The risk register (§4) names five couplings. What's missing?
Probe at minimum:

- **W-Vb × demo isolation contract.** v0.1.11 shipped a hard
  isolation contract (real DB byte-identical before/after demo
  session). v0.1.12 extends the demo to reach synthesis with
  pre-populated proposals. **Does the isolation contract still
  hold when proposals are pre-populated from packaged fixtures?
  What about scratch-DB writes during synthesis?** PLAN.md says
  "isolation contract preserved" but doesn't name the test that
  proves it.
- **W-Vb × persona harness in `verification/dogfood/`.** The
  packaged fixtures live at `src/health_agent_infra/demo/
  fixtures/`. The harness fixtures live at
  `verification/dogfood/personas/`. **Are they kept in sync, or
  do they diverge?** Drift means demo and persona-test surfaces
  describe different state.
- **W-FCC × capabilities manifest.** Surfacing the
  `strength_status` enum via `hai capabilities --json` is a
  manifest schema change. Does this conflict with CP2 (lift
  W-30 deferral, schedule freeze for v0.2.0)? If freeze is
  v0.2.0, every additive change in v0.1.12 must be back-
  compatible with whatever shape ships at the freeze.
- **W-CP × CP-self-application paradox.** CP3 adopts the four-
  tier classification, but the v0.1.12 PLAN itself already
  declares `tier: substantive` *before* CP3 is approved. **Is
  there a chicken-and-egg here?** Is the tier declaration
  conditional on CP3 ship? What if Codex rejects CP3 in this
  audit?
- **W-PRIV × CP4 (MCP exposure).** Privacy doc updates ship in
  v0.1.12. CP4 plans MCP exposure for v0.3-0.5. **Should the
  privacy doc include forward-looking language about MCP
  exposure now**, or is silence safer until the threat model
  exists?

### Q5 — Acceptance criterion bite

For each W-id, read its acceptance criterion. Is it specific
enough to fail?

Spot-check at minimum:

- W-AC: "every public doc named above reflects v0.1.11-shipped
  state." **How is this falsifiable in CI?** PLAN.md proposes
  `test_doc_freshness_assertions.py` — verify the test design
  actually catches the named C1 instances and not just any
  version drift.
- W-Vb: "`hai demo start --persona p1 --blank` reaches synthesis
  end-to-end on a clean wheel install." **Specific enough to
  fail?** Yes, but the "clean wheel install" gate needs CI
  support — does PLAN.md describe how the wheel-install test
  runs (in tmpdir? against published wheel? against
  `python -m build` output?).
- W-CP: "all six proposals authored at /cycle_proposals/CPN.md."
  **What's the bar for "authored"?** A one-paragraph proposal
  vs a multi-page argument both technically pass that gate.
  Find the right falsifier.
- W-FBC: "test exercises 3 persona scenarios; supersede
  behaviour is deterministic." **Which 3 personas? Named? Or
  any 3?** Should be named to be falsifiable.

Find any acceptance criterion that's hand-wavy and propose a
concrete falsifier.

### Q6 — Settled-decision integrity (the high-leverage Q)

This is the most consequential Q for v0.1.12. **CP1-CP6 reverse
or extend AGENTS.md "Do Not Do" / "Settled Decisions" entries.**
For each CP, audit:

- **Is the reversal honest about what it reverses?** PLAN.md
  table in §2.10 names the AGENTS.md delta. Verify each delta
  against the *current* AGENTS.md text — does the strike-text
  exist verbatim?
- **Is the rationale named?** A reversal of a settled decision
  must say *why* now, not just *what* changes. Cross-check the
  reconciliation §3 D1-D4 reasoning against the CP's claimed
  rationale.
- **Are the cascading effects mapped?** E.g., CP1 (cli.py split)
  has downstream test-surface implications (parser/capabilities
  regression test). CP2 (manifest freeze) has downstream
  external-contract implications (anything that consumes the
  manifest gets locked-in). Does the CP draft surface those?
- **CP3 (four-tier) self-application:** PLAN.md adopts the new
  classification *for v0.1.12 itself* before CP3 is approved.
  Is this a paradox or a clean precedent? (See Q4 also.)
- **CP4 (MCP exposure):** the strategic plan currently says
  nothing about MCP. The CP adds a multi-release roadmap entry.
  **Does the strategic plan §10 timeline have room?** Does
  adding MCP work shift v0.5+ work later?
- **CP5 (v0.2.0 substantial-with-shadow):** the maintainer's
  call (D1) was "substantial v0.2.0, fix bugs as they appear,"
  refined to shadow-by-default for the LLM judge. **Is the CP
  framing faithful** to that call, or has the shadow-by-default
  framing softened the substantiveness?
- **CP6 (§6.3 framing edit):** read strategic_plan_v1.md §6.3
  current wording. **Is the proposed rephrasing accurate, or
  does it understate the actual contribution?** The
  reconciliation L3 finding argued the moat is narrower than
  "publishable rule DSL" but didn't deny the rule DSL has
  some value.

Also verify that **settled decisions D11, D13, D14 are
respected** by the PLAN as currently written:

- D11 (pre-PLAN bug-hunt): PLAN.md §framing references Phase 0.
  Is the bug-hunt scope clear?
- D13 (threshold-injection seam trusted-by-design): W-D13-SYM
  closes the consumer-site asymmetry. Does PLAN.md frame this
  as *strengthening* D13 (correct) or as *replacing* it
  (incorrect)?
- D14 (pre-cycle plan-audit): this audit is the enactment.
  Verify PLAN.md's framing matches D14's documented norm
  (2-4 rounds for substantive PLANs).

### Q7 — What the plan doesn't say (absences)

Surface absences:

- Does PLAN.md document how a maintainer would **abort** the
  cycle if Phase 0 reveals an `aborts-cycle` finding?
- Does it describe what happens if **Codex rejects one or more
  CPs** in this audit? Are the dependent v0.1.13+ workstreams
  (cli.py split, manifest freeze, MCP plan) named as conditional
  on CP approval?
- Does it describe the **rollback plan** if W-N-broader audit
  reveals > 80 sites? The PLAN says "split as W-N-broader-2 →
  v0.1.13" but doesn't say what the partial v0.1.12 closes
  with — does the cycle still ship without the broader gate, or
  does ship gate degrade?
- The PLAN does not include a **Phase 0 PRE_AUDIT_PLAN.md
  outline.** v0.1.11 named the bug-hunt scope explicitly. **Is
  Phase 0 scoped tightly enough that v0.1.12 doesn't grow the
  way v0.1.11 did?**
- **Demo-flow continuity.** The PLAN says v0.1.11 boundary-stop
  transcript stays in `v0_1_11/RELEASE_PROOF` as historical
  proof. But v0.1.11's transcript was promised as a permanent
  test; does W-Vb keep that test green or replace it?

### Q8 — Reconciliation provenance and skepticism

v0.1.12 PLAN.md leans heavily on
`reporting/plans/future_strategy_2026-04-29/reconciliation.md`,
which is a Claude-authored synthesis of two parallel reviews.
The reconciliation §8 explicitly notes:

- 4 of 8 Claude round-2 research agents failed.
- Several recommendations (PHA paper specifics, calibration math,
  MCP threat model, project canonical docs) rest on un-verified
  primary sources.
- The reconciliation itself is "a synthesis with no independent
  research pass."

Audit:

- Which v0.1.12 PLAN actions rest on **on-disk-verified**
  reconciliation findings (e.g., C1 stale doc instances spot-
  verified 2026-04-29) vs **un-verified** ones?
- W-Vb's C3 packaging fix — has Claude or Codex actually
  reproduced the failure on a clean wheel install? Or is the
  bug inferred from path inspection?
- L1's D13 consumer-site asymmetry — is the four-domains-vs-two-
  domains claim accurate against current `domains/*/policy.py`?
  Spot-check it.
- C4 privacy-doc claims (the `:59` and `:116` line numbers) —
  do those line references currently exist? If the file has
  shifted, the workstream is targeting wrong lines.
- L2 W-DOMAIN-SYNC 8-registry table — Claude claimed 8
  registries enumerate the six domains. Verify the count
  against current `src/health_agent_infra/`. If the count is
  wrong, the v0.1.14 deferred workstream is mis-scoped.

Be the **independent skeptical pass** that closes the gap left
by the reconciliation's self-flagged research holes.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_12/codex_plan_audit_response.md` matching
the v0.1.11 audit-response convention:

```markdown
# Codex Plan Audit Response — v0.1.12 PLAN.md

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS |
PLAN_INCOHERENT (state which workstreams need rework before open)

**Round:** 1 / 2 / 3 / 4 (escalates if revisions warrant another pass)

## Findings

### F-PLAN-01. <short title>

**Q-bucket:** Q1 / Q2 / Q3 / Q4 / Q5 / Q6 / Q7 / Q8
**Severity:** plan-incoherence | sizing-mistake | dependency-error |
acceptance-criterion-weak | hidden-coupling | settled-decision-conflict |
absence | provenance-gap | nit
**Reference:** PLAN.md § X.Y, line N (or "absent")
**Argument:** <why this is a finding, with citations from
PLAN.md, AGENTS.md, reconciliation, or the actual codebase>
**Recommended response:** <revise PLAN.md as follows / accept
and note as known limitation / disagree with reason>

### F-PLAN-02. ...

## Open questions for maintainer

(Things Codex couldn't decide without Dom's input. Especially
relevant for CP1-CP6 where some calls are policy-shaped, not
correctness-shaped.)
```

Each finding must be triageable. Vague feedback ("the plan feels
governance-heavy") is not a finding; "CP1 strikes 'Do not split
cli.py' but the AGENTS.md text reads 'W-29 / W-30 deferred. Do
not split cli.py.' — the strike-text in PLAN §2.10 omits the
'W-29 / W-30 deferred' framing, which changes meaning" is a
finding.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle as written.
- **PLAN_COHERENT_WITH_REVISIONS** — open the cycle after named
  revisions land. Revisions list every must-fix finding.
- **PLAN_INCOHERENT** — do not open. Re-author the named
  sections before re-running this audit.

For v0.1.12 specifically: the W-CP / CP1-CP6 section is the
highest-leverage. **Verdict on CP1-CP6 individually** (accept /
revise / reject) belongs in the Open Questions section if not
in the verdict line itself.

---

## Step 5 — Out of scope

- v0.1.11 implementation (already audited, shipped to PyPI
  2026-04-28).
- Code changes against the v0.1.12 PLAN (Phase 0 hasn't
  started; no implementation yet).
- v0.1.13+ scope (named in PLAN §1.3 as deferred; not in this
  PLAN's commitments). However, **CP1-CP6 deltas that affect
  v0.1.13+ ARE in scope** because they're authored in v0.1.12
  even if effective in later cycles.
- The reconciliation document itself. v0.1.12 PLAN.md is the
  artifact; the reconciliation is input. Findings about the
  reconciliation belong in the next strategy review, not here —
  unless the PLAN cites a reconciliation claim that turns out
  to be false (which is a Q8 finding in this audit).
- The strategic plan + tactical plan content beyond §6.3
  (CP6's target). Updates to the tactical plan to reflect the
  v0.1.12 reframe are scoped under W-AC, but a structural
  rewrite of the tactical plan is not.

---

## Step 6 — Cycle pattern (this audit's place)

```
Pre-PLAN-open:
  D14 Codex plan audit ← you are here
  Maintainer response to plan audit
  PLAN.md revised if warranted
  (loop until PLAN_COHERENT — empirical 2-4 rounds for
   substantive PLANs)

Phase 0 (D11):
  Internal sweep
  Audit-chain probe
  Persona matrix
  Codex external bug-hunt audit
  → audit_findings.md consolidates

Pre-implementation gate:
  revises-scope findings may revise PLAN (loop back to D14
   if large)
  aborts-cycle findings may end the cycle

PLAN.md → opens cycle

Implementation rounds:
  Codex round 1 (post-implementation)
  Maintainer response
  ... until SHIP / SHIP_WITH_NOTES

RELEASE_PROOF.md + REPORT.md
```

Estimated audit duration: 1-2 sessions. Smaller than a code audit
because no implementation to verify. **Larger than v0.1.11's
plan audit** because CP1-CP6 require checking AGENTS.md text
exactly against proposed deltas, plus Q8 reconciliation-
provenance verification has on-disk spot-check work.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_12/codex_plan_audit_response.md` (new)
  — Codex's findings.
- `reporting/plans/v0_1_12/PLAN.md` (revisions, if warranted)
  — maintainer + Claude apply revisions in response to
  findings.
- `reporting/plans/v0_1_12/codex_plan_audit_round_2_response.md`
  + subsequent round files (if rounds escalate, per v0.1.11
  precedent).

**No code changes.** No test runs. No state mutations.

The maintainer applies any revisions; you do not edit PLAN.md
directly.
