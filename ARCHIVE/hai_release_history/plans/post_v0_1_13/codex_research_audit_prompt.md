# Codex External Audit — Strategic Research Report 2026-05-01

> **Why this round.** Claude authored a deep strategic-research report
> at `reporting/plans/post_v0_1_13/strategic_research_2026-05-01.md`
> on 2026-05-01, the day after v0.1.13 shipped. The maintainer intends
> to use it as direct input to the next v0.1.14 PLAN.md, cycle
> proposals (CP-W30-SPLIT, CP-MCP-THREAT-FORWARD, CP-2U-GATE-FIRST),
> and risk-register updates. Before that input lands, the report
> itself needs adversarial review under the same provenance and
> coherence discipline the project applies to PLAN.md and IR
> responses.
>
> **Why this isn't a D14 plan audit.** D14 audits a PLAN.md against
> the strategic plan. This audit is on a *single research artifact*
> against the strategic plan + tactical plan + the literature it
> cites. The verdict scale and Q-buckets differ; the discipline (cite
> file:line, verify before recommending, name what would change your
> mind) is the same.
>
> **You are starting fresh.** This prompt and the artifacts it cites
> are everything you need; do not assume context from a prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main (post-v0.1.13 ship) or chore/<scope>
git log --oneline -5
# expect: most recent should mention v0.1.13 ship
ls reporting/plans/post_v0_1_13/
# expect: codex_research_audit_prompt.md (this file),
#         strategic_research_2026-05-01.md (artifact under audit)
```

If any don't match, **stop and surface the discrepancy**. Ignore any
tree under `/Users/domcolligan/Documents/`.

---

## Step 1 — Read the orientation artifacts

In this order:

1. **`AGENTS.md`** — the operating contract. Pay attention to:
   - "Governance Invariants"
   - "Settled Decisions" D1-D15 — note any the report implicitly
     reopens.
   - "Do Not Do" — note any the report would extend.
   - "Patterns the cycles have validated" — provenance discipline,
     summary-surface sweep, honest partial-closure naming, audit-
     chain empirical settling shape. Apply these as you audit.
2. **`reporting/plans/strategic_plan_v1.md`** — vision; verify the
   report's framing of H1–H5, Wave structure, and v0.5+ falsification
   window.
3. **`reporting/plans/tactical_plan_v0_1_x.md`** — release-by-release
   plan. Verify the report's claims about v0.1.14 / v0.2.0 named
   scope and CP5 single-release synthesis.
4. **`reporting/plans/risks_and_open_questions.md`** — verify the
   report's risk-register claims (especially R-T-02, R-O-03, R-S-04,
   R-X-04 references in §5–§6, §17).
5. **`reporting/plans/v0_1_13/RELEASE_PROOF.md`** — verify the report's
   v0.1.13 ship claims (17 W-ids, D14 5-round, IR 3-round, tier
   substantive, named deferrals).
6. **`reporting/plans/v0_1_13/CARRY_OVER.md`** — verify the report's
   characterisation of what carries to v0.1.14.
7. **`reporting/plans/future_strategy_2026-04-29/reconciliation.md`**
   — verify the report's claims about reconciliation D1 vs CP5,
   §4 C10 source-row locators, A8 freshness checklist, etc.
8. **`reporting/plans/post_v0_1_13/strategic_research_2026-05-01.md`**
   — the artifact under audit. Read fully before forming findings.

Cross-check that everything the report cites (file paths, line
numbers, function names, exact strings) actually exists in the tree
as cited. Broken cross-references count as findings.

---

## Step 2 — The audit questions

The report makes 5 P0 recommendations, 4 P1/P2 recommendations, 4
roadmap revisions (R-1 to R-4), 4 contradiction findings, 13 open
decisions, and a candidate workstream catalogue. Audit each against
the Q-buckets below.

### Q1. Provenance discipline

Sample 10+ specific claims in the report — file:line citations,
exact-string quotes, function/class names, external paper claims.
For each, verify the source independently.

- Does §3 ("Evidence Ledger Summary") accurately reflect what the
  cited files say at the cited line ranges?
- Does §8 ("Contradictions and Stale Docs") correctly identify
  C-DRIFT-01 through C-DRIFT-04? Are any of the four false positives?
  Did the report miss other drifts?
- Do the external citations in §21 verify (paper exists at named
  venue with named author)? The report self-flags ~10% as summary-
  mediated; spot-check that flagged items.
- Are the CVE references (CVE-2025-59536/21852/6514/53109/53110)
  accurate? Are the eSentire 22%/43% percentages traceable to
  primary?

### Q2. Priority-label honesty

The report assigns P0 to W-2U-GATE, W-PROV-1, W-EXPLAIN-UX,
W-MCP-THREAT, W-BACKUP, and a doc-only second-user-exposure fix.

- Is each P0 truly P0 (blocks second-user trust, safety, governance,
  or roadmap credibility)? Or are any P1 dressed up as P0?
- Conversely, is there a P1 in the report that should be P0? (E.g.,
  W-FACT-ATOM, W-JUDGE-BIAS, W-VENDOR-CHURN, W-FRESH-EXT.)
- The report's §6 P1/P2 catalogue — does it omit a P0 the report
  should have surfaced?

### Q3. Roadmap-revision soundness

Three structural revisions are proposed:
- **R-2** moves W-30 schema-freeze out of v0.2.0 to v0.2.0.x/v0.2.1.
- **R-3** pulls W-MCP-THREAT forward from v0.3 to v0.2.0 doc-only.
- **R-1** inserts W-2U-GATE as the first v0.1.14 workstream.

For each:
- Is the design-coupling argument correct? (R-2 claims W30 has no
  coupling to W52/W58. Verify by reading W52/W58 design notes in
  tactical_plan_v0_1_x.md §6.)
- Is there a hidden coupling the report missed?
- Does the revision implicitly reopen a settled decision (D4 for
  R-2, CP4 for R-3) without proposing a formal CP?

### Q4. v0.1.14 cycle-sizing honesty

The report estimates v0.1.14 at 23-29 days (1 maintainer) with 5 new
W-ids on top of 5 named-held W-ids = 10 total.

- Compare to v0.1.10 (the ~10-W-id reference the report cites). Is
  23-29 days realistic, optimistic, or pessimistic?
- Does the report's estimate hold if W-2U-GATE surfaces a real
  blocker (the report names this as a falsifier but not as a sizing
  contingency)?
- D14 expectation: 4 rounds, ~10→5→3→0. Is that achievable on a
  cycle that adds 5 P0 W-ids to a previously-settled tactical-plan
  scope? v0.1.13 grew to 5 D14 rounds at 17 W-ids; what's the
  empirical settling shape for "pre-PLAN-revision new-W-id density"?

### Q5. v0.2.0 split soundness

The report keeps v0.2.0 as a single-release per CP5 but proposes
moving W-30 out and adding three doc-only adjuncts (W-MCP-THREAT,
W-COMP-LANDSCAPE, W-NOF1-METHOD) plus W-2U-GATE-2.

- The W52↔W58 design-coupling claim that anchored CP5 — is it cited
  correctly? (Verify from tactical_plan_v0_1_x.md:441-501.)
- Does the report's recommended v0.2.0 shape (substrate + adjuncts)
  push the cycle larger than v0.1.13 (the prior largest)?
- The 30-39-day estimate — realistic or optimistic?

### Q6. Settled-decision integrity

The report proposes additions to AGENTS.md "Do Not Do" (Strava
anchoring, MCP autoload, threshold mutation) and a framing upgrade
to README.md ("domain-pinned AgentSpec for personal health"). It
also proposes a CP6-equivalent for moving W-30.

- Are any of these *implicit* settled-decision changes that should
  be authored as formal CPs?
- Does the report quote AGENTS.md text verbatim where it proposes
  edits, or does it paraphrase?
- Are the new "Do Not Do" entries already covered by existing
  invariants? (Don't-add-Strava — is this implied by the existing
  D5? Don't-autoload-MCP — is this implied by governance invariant
  #4?)

### Q7. What the report doesn't say

- **Abort/rollback paths.** If W-PROV-1 lands but reveals the schema
  is wrong, what's the rollback path? Report doesn't say.
- **Concurrency.** Can W-2U-GATE run in parallel with W-29
  mechanical split, or does W-29 need to ship first so the second
  user installs from a stable parser shape?
- **Maintainer load.** v0.1.14 is 23-29 days + v0.2.0 is 30-39 days
  + a doc-fix sweep + a Codex audit + a CP authoring round. Is the
  cumulative maintainer-time estimate honest given the project's
  single-maintainer reality (R-O-01)?
- **What if the Codex-on-research-report pattern itself is wrong?**
  D14 was tried-and-validated for PLANs; this is the first time it's
  being applied to a strategic-research artifact. Is the precedent
  worth setting, or is it a process-overhead drift?

### Q8. External-source skepticism

The report leans on April 2026 web research for landscape and
literature claims. Spot-verify:

- The "8+ Garmin community MCPs, 6+ intervals.icu MCPs" landscape
  claim — verifiable?
- The Strava Nov 2024 ToS AI/ML prohibition — verify primary source
  (https://press.strava.com/articles/updates-to-stravas-api-agreement).
- The Apple medical-device disclosure mandate (March 2026) — verify
  this is a real regulatory action, not a misread of an MDDI piece.
- The MedHallu F1=0.625 ceiling claim — verify from the abstract or
  paper text, not from a search-summary blob.
- The OWASP MCP Top 10 (2026 beta) — does it actually exist as
  cited, and is the 10-item enumeration in the report accurate?
- The CALM 12-bias taxonomy — 12 specific biases cited; verify the
  count.

If any of these don't verify, the corresponding recommendation in
the report is unsupported and should drop.

### Q9. Hypothesis-falsification rigor

The report claims H1-H5 are "all active, none falsified at v0.1.13"
and that the May-2026 literature validates HAI's bets "more cleanly
than at any prior cycle close." Audit:

- Does the PHA paper (arXiv 2508.20148) genuinely *not* falsify H1?
  The report frames it as a "challenge but not falsification." Is
  that read defensible against the paper's actual claims?
- Does AgentSpec (arXiv 2503.18666) genuinely validate H5, or does
  it potentially commoditize HAI's contribution?
- The report recommends "domain-pinned AgentSpec for personal
  health" framing. Is that strategically sound, or does it cede
  conceptual leadership?

### Q10. Cycle-process precedent risk

This research report + audit cycle is a *new pattern* in the
project. D11 (Phase 0 bug-hunt), D14 (pre-cycle plan-audit), D15
(cycle-weight tiering) are all settled patterns that emerged from
specific cycles. If "Codex audits Claude's strategic-research
report" becomes a permanent pattern, what does that imply for the
operating discipline?

- Is the precedent worth setting, or is it ad-hoc-only?
- If it's permanent, should it become D16?
- If it's permanent, what's the cycle-weight equivalent? (Doc-only?
  Hardening? Full plan-audit-style?)

---

## Step 3 — Output shape

Write findings to
`reporting/plans/post_v0_1_13/codex_research_audit_response.md` matching
the existing convention:

```markdown
# Codex Research Audit Response — Strategic Research 2026-05-01

**Verdict:** REPORT_SOUND | REPORT_SOUND_WITH_REVISIONS | REPORT_FLAWED
(state which sections / recommendations need rework before use)

**Round:** 1 / 2 / 3

## Findings

### F-RES-01. <short title>

**Q-bucket:** Q1 / Q2 / Q3 / Q4 / Q5 / Q6 / Q7 / Q8 / Q9 / Q10
**Severity:** provenance-failure | priority-mistake | roadmap-error |
sizing-mistake | settled-decision-conflict | absence | over-claim |
external-source-failure | hypothesis-overreach | precedent-risk | nit
**Reference:** strategic_research_2026-05-01.md § X, line N (or "absent")
**Argument:** <why this is a finding, with citations to the artifact
under audit AND to the source it should match>
**Recommended response:** <revise the report as follows / accept and
note as known limitation / disagree with reason>

### F-RES-02. ...

## Open questions for maintainer
```

Each finding must be triageable. "Section §5 P0-1 cites RELEASE_PROOF.md:294-297 but the actual deferral is at lines 289-301" is a finding; "section feels handwavy" is not.

---

## Step 4 — Verdict scale

- **REPORT_SOUND** — use the report directly as input to v0.1.14
  PLAN.md authoring + cycle-proposal drafting + doc-fix sweep,
  without revision.
- **REPORT_SOUND_WITH_REVISIONS** — use the report as input *after*
  named revisions land. Revisions list every must-fix finding.
  Mirrors PLAN_COHERENT_WITH_REVISIONS at D14.
- **REPORT_FLAWED** — do not use as input. Re-author the named
  sections before re-running this audit.

---

## Step 5 — Out of scope

- v0.1.13 implementation (already audited via the v0.1.13 IR chain
  and shipped).
- v0.1.14 PLAN.md (does not yet exist — its authoring is downstream
  of this audit).
- Cycle proposals (CP-W30-SPLIT etc.) — not yet authored.
- Code changes — none have been made against the report's
  recommendations.
- Strategic + tactical + risks docs beyond the deltas the report
  proposes.

---

## Step 6 — Cycle pattern (this audit's place)

This is a **new** placement in the project's operating discipline.
Best-fit characterisation:

```
Strategic-research authored ← Claude, 2026-05-01
  [research-audit] Codex review ← you are here
  Maintainer reconciliation (Claude vs Codex findings)
  Reconciliation doc → reporting/plans/post_v0_1_13/reconciliation.md
  → punch-list with named disagreements

Pre-PLAN authoring:
  Cycle proposals authored (CP-W30-SPLIT etc.)
  AGENTS.md "Do Not Do" additions
  Mechanical doc-fix sweep (4 contradictions)

PLAN.md authoring:
  v0_1_14/PLAN.md drafted with reconciled scope
  [D14] Codex plan audit (the standard cycle)
  ... until PLAN_COHERENT
```

Estimated review duration: 1-2 sessions per round. Empirical
settling unknown — this is the first time the project has applied
the audit pattern to a research artifact rather than a PLAN.

---

## Step 7 — Files this audit may modify

- `reporting/plans/post_v0_1_13/codex_research_audit_response.md`
  (new) — your findings.
- `reporting/plans/post_v0_1_13/strategic_research_2026-05-01.md`
  (revisions, if warranted) — maintainer + Claude apply revisions
  in response.
- `reporting/plans/post_v0_1_13/codex_research_audit_round_N_response.md`
  (subsequent rounds, if revisions warrant another pass).

**No code changes.** No test runs. No state mutations. No edits to
AGENTS.md, ROADMAP.md, README.md, strategic_plan_v1.md, or
tactical_plan_v0_1_x.md from this audit — those edits are
downstream and are gated by the maintainer's reconciliation step.

---

## Reference: what good looks like

A high-quality round-1 finding catches:

- **Provenance**: a cited file:line that doesn't say what the report
  claims it says.
- **Hidden coupling**: the report claims W30 has no coupling to
  W52/W58, but tactical_plan_v0_1_x.md:XXX names a coupling.
- **Priority inversion**: the report puts W-EXPLAIN-UX at P0 when
  W-FACT-ATOM (currently P1) is the actually-load-bearing
  dependency for W58.
- **Settled-decision shadow change**: the report's "domain-pinned
  AgentSpec for personal health" framing implicitly changes how
  H5 is positioned, without naming it as a hypothesis update.
- **External-source failure**: the MedHallu F1=0.625 claim doesn't
  match the actual paper.
- **Sizing-honesty failure**: 23-29 days for v0.1.14 is incompatible
  with the project's single-maintainer reality given the cumulative
  work since 2026-04-27.

A finding that just says "section §5 feels under-developed" is not
a finding. Make it triageable: cite the report's text, cite the
source it should match, and propose the specific revision.

The report's own "Caveat" section (last paragraph) explicitly names
four things that would change Claude's mind. Treat those as
*pre-conceded falsifiers* — if you find evidence supporting any of
them, the corresponding recommendation drops automatically and
should be flagged as such.
