# Codex Research Audit — Round 2 Prompt

> **Why this round.** Round 1 returned REPORT_SOUND_WITH_REVISIONS
> with 10 findings (9 accepted, 1 partial-accept). Maintainer-side
> revisions applied to `strategic_research_2026-05-01.md` in place
> 2026-05-01 — ~279 lines of new content across §1, §2, §3, §5, §6,
> §10, §11, §13, §14, §15, §18, §19, §20, §21, §22. This is the
> standard D14-style "round 2 catches what round 1 introduced" pass.
>
> **Scope is narrower than round 1.** Do not re-audit the full
> report. Audit:
>   1. Did the named round-1 revisions land correctly?
>   2. Did the §11 C6 vs CP5 restructuring introduce second-order
>      issues elsewhere (cross-refs, sizing, OQs)?
>   3. Spot-check 5+ remaining citations not covered in round 1.
>   4. Are there residual OWASP-MCP / CALM / Garmin / Apple claims
>      anywhere in the report that the round-1 corrections missed?
>
> **Empirical context.** This is the first round-2 of a research-
> audit (per F-RES-10 the pattern itself is N=1). D14 plan-audit
> empirical norm at round 2 is ~5 findings (down from ~10 at round 1)
> with second-order issues from round-1 revisions as the canonical
> shape. No precedent for research-audit round 2; treat the D14
> pattern as a prior, not a target.
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
ls reporting/plans/post_v0_1_13/
# expect 4 files:
#   codex_research_audit_prompt.md            (round 1 prompt)
#   codex_research_audit_response.md          (round 1 Codex findings)
#   codex_research_audit_round_1_response.md  (round 1 maintainer response)
#   strategic_research_2026-05-01.md          (artifact, post-round-1 revisions)
#   codex_research_audit_round_2_prompt.md    (this file)
```

If any don't match, **stop and surface the discrepancy**.

---

## Step 1 — Read in this order

1. **`reporting/plans/post_v0_1_13/codex_research_audit_response.md`**
   — your round-1 findings (10 entries F-RES-01..F-RES-10).
2. **`reporting/plans/post_v0_1_13/codex_research_audit_round_1_response.md`**
   — maintainer disposition + named revisions per finding.
3. **`reporting/plans/post_v0_1_13/strategic_research_2026-05-01.md`**
   — the revised artifact. Read fully. Note that revisions are in
   place (no diff file); the document now opens with a "Round-1
   Codex audit applied 2026-05-01" callout.
4. **Spot-read sources for citation-pass:**
   - `pyproject.toml` (verify version line)
   - `README.md:34-38` (verify hosted-agent caveat exists)
   - `reporting/plans/tactical_plan_v0_1_x.md:394-437` (v0.1.14 in-scope + effort)
   - `reporting/plans/future_strategy_2026-04-29/reconciliation.md:147` (C6)
   - One additional file:line you choose at random from §21 to
     spot-verify provenance discipline.

---

## Step 2 — Round-2 audit questions

### R2-Q1. Did the round-1 revisions land correctly?

For each F-RES-01..F-RES-10, verify the maintainer-named revision is
present in the artifact and reads as intended.

- **F-RES-01 (P0-6 withdrawn):** §5 P0-6 should be marked withdrawn
  with a note citing F-RES-01. §1 should say "five things" not
  "six things." §15 S-3 should reference the README:34-38 reality.
- **F-RES-02 (v0.1.14 sizing):** §10 should enumerate 9 baseline
  W-ids + 5 P0/P1 additions = 14 total; cost should be 30-40 days
  not 23-29; §20 should match.
- **F-RES-03 (C6 vs CP5):** §11 should now name two paths (A:
  3-release per reconciliation D1; B: single-release per CP5 with
  new CP). §1 verdict, §10, §20 should reflect the choice. §19 OQ-B
  should ask the maintainer to choose.
- **F-RES-04 (OWASP MCP):** §14 S-1 should be marked pending
  re-verification; mapping should not be cited as external-narrative-
  grade. §19 should have OQ-N for re-verification.
- **F-RES-05 (CALM thresholds):** §13 E-3 thresholds should be
  labeled HAI-proposed; §6 P1-2 CALM citation should note Ye 2025
  ICLR pending verification.
- **F-RES-06 (citation errors):** §3 and §21 should now cite
  pyproject.toml:7 (not :3); AGENTS.md:425 should not be framed as
  a file-length citation.
- **F-RES-07 (primary sources):** §2 Phase 4 should soften the
  "primary only" claim; §21 should add a source-class note.
- **F-RES-08 (Apple framing):** §3 and §18 should reframe Apple as
  App Store policy / trade press, not regulator action.
- **F-RES-09 (Garmin "8+/all"):** §15 D-5, §18 should remove the
  unsourced count.
- **F-RES-10 (D16 deferral):** §22 should add the "remain ad-hoc"
  note; §19 should have OQ-O.

For any revision that didn't land or landed incorrectly, file as a
finding with severity `unfinished-revision`.

### R2-Q2. Did §11 restructuring introduce second-order issues?

§11 was the largest revision (Path A vs Path B framing replaces
"CP5 is correct"). Cross-check:

- §1 executive verdict — does it match the Path A recommendation?
- §10 v0.1.14 — does it stay neutral on Path A/B (since it doesn't
  affect v0.1.14)?
- §20 workstream catalogue — v0.2.0 is now Path A; v0.2.1 + v0.2.2
  are added; W-30 moved to v0.2.2. Are these consistent with §11?
- §19 OQ-B — does the question correctly enumerate both paths?
- "Visual: revised roadmap" diagram in §9 — does it show Path A?
- §22 caveats — does the "what would change my mind" line about
  v0.2.0 split match the new Path A/B framing?

Any inconsistency between §11 and these surfaces is a second-order
finding.

### R2-Q3. Spot-check 5+ remaining citations

Round 1 caught 2 citation errors (pyproject.toml:3, AGENTS.md:425
file-length framing). The risk: similar errors elsewhere in §21 that
round 1 didn't sample.

Pick 5 citations from §21 local-citations or external-citations and
verify on disk / against URL. Flag any mismatches as `provenance-
failure` findings. The error rate from round 1 was ~2 / N-sampled;
if round 2 spot-check finds zero, the citation appendix can be
treated as audit-grade. If 1+, recommend a full mechanical pass.

Suggested targets (pick at least 5, mix local + external):
- AGENTS.md:293-316 (summary-surface sweep pattern)
- reporting/plans/v0_1_13/RELEASE_PROOF.md:289-301 (deferrals)
- ARCHITECTURE.md:174-199 (migrations)
- reporting/plans/strategic_plan_v1.md:140-298 (H1-H5)
- HYPOTHESES.md:16-142 (H1-H5)
- (external) MedHallu paper at https://arxiv.org/abs/2502.14302 — does
  the F1=0.625 ceiling claim hold against the abstract?
- (external) JITAI 2025 meta-analysis g=0.15 at PMC12481328 — does
  the abstract match?

### R2-Q4. Residual OWASP / CALM / Garmin / Apple claims?

Round 1 corrected named instances. Search the artifact for any
residual:

- Any "OWASP MCP" reference outside §14 that still uses the original
  (incorrect) numbering?
- Any "CALM" reference outside §6 P1-2 / §13 E-3 / §21 that still
  cites Park 2024 without flag?
- Any "Garmin" reference that still includes "8+" or "all"?
- Any "Apple" reference that still uses "mandate" / "regulatory
  action" framing?

Flag residuals as `unfinished-revision`.

### R2-Q5. Empirical-settling shape

What does this audit say about the research-audit pattern's
settling shape? If round 2 finds 0-2 findings, the pattern works
roughly like a D14 plan-audit (10→5→3→0 → 0). If round 2 finds 5+
findings, the pattern needs more rounds than D14 typically takes for
research artifacts of this scope. This is data for OQ-O's eventual
retrospective.

Note your finding count and whether you'd expect round 3 to fire.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/post_v0_1_13/codex_research_audit_round_2_response.md`:

```markdown
# Codex Research Audit Round 2 Response — Strategic Research 2026-05-01

**Verdict:** REPORT_SOUND | REPORT_SOUND_WITH_REVISIONS | REPORT_FLAWED

**Round:** 2

**Round-1 follow-through summary:** <one paragraph: of the 10 round-1
findings, how many revisions landed cleanly, how many partial, how
many didn't land>

## Findings

### F-RES-R2-01. <short title>

**Q-bucket:** R2-Q1 / R2-Q2 / R2-Q3 / R2-Q4 / R2-Q5
**Severity:** unfinished-revision | second-order-issue | provenance-failure |
residual-claim | settling-shape-data | nit
**Reference:** strategic_research_2026-05-01.md § X, line N
**Argument:** <citation-grounded; what's wrong + what source it should match>
**Recommended response:** <revise as follows / accept / disagree with reason>

### F-RES-R2-02. ...

## Empirical-settling note (per R2-Q5)

<one paragraph: round-2 finding count, expected round-3 yield, recommendation
on whether to close at round 2 or continue>
```

---

## Step 4 — Verdict scale

- **REPORT_SOUND** — close the audit chain; the report is usable as
  input to v0.1.14 PLAN.md authoring + CP drafting + doc-fix sweep.
- **REPORT_SOUND_WITH_REVISIONS** — name the must-fix findings;
  maintainer applies them; round 3 verifies (or, if findings are
  trivial, maintainer closes at round 2 by accepting the named
  revisions without re-running this audit).
- **REPORT_FLAWED** — do not use as input. Re-author the named
  sections before re-running this audit. (Unlikely at round 2 given
  round-1 verdict was REPORT_SOUND_WITH_REVISIONS.)

---

## Step 5 — Out of scope

- Re-auditing the report's strategic recommendations (round 1 verdict
  was REPORT_SOUND_WITH_REVISIONS; the strategic posture is not
  under re-review).
- Code changes — none have been made.
- The `codex_research_audit_round_1_response.md` itself — the
  maintainer's per-finding disposition is settled.
- v0.1.14 PLAN.md authoring (downstream).

---

## Step 6 — Cycle pattern (this audit's place)

```
Strategic-research authored ← Claude, 2026-05-01
  [research-audit r1] Codex review ← done 2026-05-01
  Maintainer round-1 response ← done 2026-05-01
  Round-1 revisions applied to artifact in place ← done 2026-05-01
  [research-audit r2] Codex review ← you are here
  Maintainer reconciliation (close at r2 or continue to r3)
  Reconciliation doc → reporting/plans/post_v0_1_13/reconciliation.md
  → punch-list with named disagreements (or empty if r2 closes clean)

Pre-PLAN authoring:
  Cycle proposals authored (CP-W30-SPLIT, CP-2U-GATE-FIRST,
    CP-MCP-THREAT-FORWARD, possibly CP-PATH-A or CP-PATH-B
    depending on OQ-B resolution)
  AGENTS.md "Do Not Do" additions
  Mechanical doc-fix sweep (4 contradictions + the 5-skill count)

PLAN.md authoring:
  v0_1_14/PLAN.md drafted with reconciled scope
  [D14] Codex plan audit (the standard cycle)
  ... until PLAN_COHERENT
```

Estimated review duration: 1 session. Round 2 is verification, not
re-analysis.

---

## Step 7 — Files this audit may modify

- `reporting/plans/post_v0_1_13/codex_research_audit_round_2_response.md`
  (new) — your findings.
- `reporting/plans/post_v0_1_13/strategic_research_2026-05-01.md`
  (revisions, if warranted) — maintainer applies revisions in
  response.
- `reporting/plans/post_v0_1_13/codex_research_audit_round_3_prompt.md`
  (only if round 3 is warranted) — drafted by Claude/maintainer
  after this round closes.

**No code changes.** No test runs. No edits to AGENTS.md, ROADMAP.md,
README.md, strategic_plan_v1.md, or tactical_plan_v0_1_x.md from
this audit — those edits are downstream.
