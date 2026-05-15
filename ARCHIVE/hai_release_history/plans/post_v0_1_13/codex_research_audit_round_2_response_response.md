# Codex Research Audit — Round 2 Maintainer Response

**Round:** 2
**Codex verdict:** REPORT_SOUND_WITH_REVISIONS
**Maintainer disposition:** ACCEPT 7 / PARTIAL-ACCEPT 0 / DISAGREE 0
**Action:** apply revisions to `strategic_research_2026-05-01.md` in
place; close audit chain at round 2 unless round-3 spot-check
warrants another pass.

---

## Summary

7 findings filed. All accepted as-stated. Codex's empirical-settling
note matches the D14 "round 2 catches second-order drift" pattern:
revisions from round 1 landed in substance but did not fully
propagate to all summary surfaces. The round-2 fixes are mechanical
and localised; expected round-3 yield is 0-2 findings if a clean
mechanical sweep is applied.

The most material change is **F-RES-R2-01** (Path A still violates C6
in v0.2.1). Fix: split Path A into **four releases** (v0.2.0 W52 +
W58D / v0.2.1 W53 / v0.2.2 W58J shadow / v0.2.3 W58J promote + W-30).
Each release ships exactly one conceptual schema group, honouring
C6 cleanly. The remaining six findings are residual-revision /
provenance fixes.

---

## Per-finding disposition

### F-RES-R2-01 — Path A still violates C6 in v0.2.1

**Disposition:** ACCEPT.

**Verification:** §11 Path A v0.2.1 explicitly noted "insight ledger
+ judge log (two groups — borderline; could split further)" — that
is a self-flagged C6 violation. The original reasoning was that
Path A satisfied C6 better than Path B, but Codex correctly notes
that "satisfies for v0.2.0" ≠ "honours C6." Either Path A splits
fully into 4 releases, or the report should honestly say Path A
honours C6 only for v0.2.0.

**Decision:** **Split Path A into 4 releases.** Per-release schema
groups:

| Release | Workstreams | Schema group | Cost |
|---|---|---|---|
| **v0.2.0** | W52 + W58D + W-FACT-ATOM + 4 doc-only adjuncts | weekly-review tables + claim-block (one group) | 18-24 days |
| **v0.2.1** | W53 insight ledger | insight ledger tables (one group) | 8-12 days |
| **v0.2.2** | W58J shadow + W-JUDGE-BIAS | judge log tables (one group) | 8-12 days |
| **v0.2.3** | W58J promote to blocking + W-30 capabilities-manifest schema freeze | no new schema (flag flip + manifest pin) | 5-8 days |

This is more cycles but each is smaller and each has a single schema
group. Total v0.2.x effort: 39-56 days, similar to the single-cycle
Path B estimate (30-39 days) plus the cost of the additional D14
overhead per cycle.

**Action:**
- Revise §11 Path A table to 4 rows.
- Update §1 verdict, §9 visual roadmap diagram, §19 OQ-B, §20
  workstream catalogue, §22 caveat to reflect 4-release Path A.
- Note: Path B fallback unchanged (single v0.2.0 + W-30 hardening
  release).

### F-RES-R2-02 — v0.1.14 D14 ≤4 acceptance criterion contradicts revised sizing

**Disposition:** ACCEPT.

**Verification:** §10 "Cycle tier classification (D15)" was updated
to say "D14 expectation: 4-5 rounds." But the "Acceptance criteria
for cycle ship" subsection (which the round-1 edit didn't touch)
still says `D14 verdict PLAN_COHERENT within ≤4 rounds`. Internal
contradiction.

**Action:**
- §10 acceptance criteria line: change "≤4 rounds" to "≤5 rounds;
  if it exceeds 5, maintainer re-scopes before implementation."
- IR verdict criterion (≤3 rounds) stays — that's a separate
  empirical norm.

### F-RES-R2-03 — OWASP MCP numbering residue in §18

**Disposition:** ACCEPT.

**Verification:** §18 anti-pattern table still uses old-style numbered
references:
- "OWASP MCP10 (context oversharing)" — under verified OWASP MCP
  Top 10, MCP10 is Tool Metadata Spoofing, not context oversharing.
- "OWASP MCP1 + MCP7 + MCP10" — the actual mapping for hosted-relay
  token-distribution risks is MCP02 (Token Theft) + MCP07 (Sensitive
  Information Disclosure) + MCP10 (Tool Metadata Spoofing), and the
  whole mapping is pending re-verification per F-RES-04.

**Action:**
- §18 row "Hosted multi-user backend": replace "OWASP MCP10 (context
  oversharing)" with "OWASP-MCP-pattern: sensitive information
  disclosure across users (cf. §14 S-1 pending verification)."
- §18 row "Hosted MCP relay distributing tokens": replace "OWASP
  MCP1 + MCP7 + MCP10" with "OWASP-MCP-pattern: token theft +
  sensitive disclosure + metadata spoofing (cf. §14 S-1 pending
  verification)."

### F-RES-R2-04 — CALM correction didn't propagate to OQ-K + §21

**Disposition:** ACCEPT.

**Verification:** Codex did the primary-source check on OpenReview
ID `3GTtZFiajM` and confirmed it is **"Justice or Prejudice?
Quantifying Biases in LLM-as-a-Judge" by Jiayi Ye et al., ICLR 2025**.
That is CALM. So the round-1 attribution to "Park 2024" was wrong
across the board, not just in the body — the appendix entry and
OQ-K rationale should also be corrected.

**Action:**
- §19 OQ-K: change rationale from "CALM-grounded" to
  "bias-literature-informed; HAI-proposed thresholds validated
  locally."
- §21 external citations: replace "**CALM**, Park et al. 2024" with
  "**CALM** (Justice or Prejudice? Quantifying Biases in LLM-as-a-
  Judge), Ye et al. 2025, ICLR."
- Pending-verification flag on the CALM citation can now be removed
  (Codex confirmed primary source).

### F-RES-R2-05 — Apple "mandate" framing in appendix label

**Disposition:** ACCEPT.

**Verification:** §21 still has the bullet labeled "Apple medical-
device disclosure mandate (March 2026)" right after the source-class
note that says the link is trade press, not a regulator action.
The body text (§3, §18) was corrected; the appendix label was
missed.

**Action:**
- §21 external citations: rename "Apple medical-device disclosure
  mandate (March 2026)" to "Apple App Store medical-device-status
  disclosure policy (MDDI trade press, March 2026)."

### F-RES-R2-06 — More citation errors in §21

**Disposition:** ACCEPT.

**Verification:**
- `ARCHITECTURE.md` is 111 lines (verified `wc -l`). Citing
  `:174-199` is impossible. The actual source is
  `reporting/docs/architecture.md:174` which reads "the projector.
  Migrations 001-021 are live" — that is the migrations content I
  meant. The citation file path was wrong.
- Codex says PHA arXiv 2508.20148 names "A. Ali Heydari, Ken Gu,
  Vidya Srinivas, Hong Yu, and others," not Wang/Cosentino. I
  cannot independently verify the arXiv metadata in this session;
  trusting Codex's primary-source check.
- Codex notes the spot-check found *more than five* errors in a
  sampled set, so a full mechanical pass is warranted.

**Action:**
- §21 local citations: replace `ARCHITECTURE.md:174-199 (migrations)`
  with `reporting/docs/architecture.md:174 (migrations live; note
  the doc itself says "001-021" while migrations now run through
  022 — minor doc-staleness that is unrelated to this report)`.
- §21 external citations: replace the PHA authors line:
  - **Was:** "Anatomy of a Personal Health Agent (PHA),
    Wang/Cosentino et al. 2025"
  - **To:** "Anatomy of a Personal Health Agent (PHA), Heydari et
    al. 2025 (per Codex round-2 primary-source check)"
- Add a §21 close-out note: "Round-2 spot-check found 2+ citation
  errors. A full mechanical pass over §21 is part of the v0.1.14
  doc-fix sweep (W-FRESH-EXT)."

### F-RES-R2-07 — "Primary external source" overclaim in §2 provenance paragraph

**Disposition:** ACCEPT.

**Verification:** §2 Phase 4 was correctly softened to "primary
sources where available; vendor statements... explicitly flagged in
§21 with a source-class label." But the §2 closing provenance
paragraph (after the 6-phase enumeration) still says: "every claim
in §5–§20 traces either to a cited file:line in the repo or to a
primary external source in §21." That is still false for MDDI,
Practical DevSecOps, Authzed, Medium, etc.

**Action:**
- §2 provenance paragraph: replace "to a primary external source in
  §21" with "to an external source listed in §21, with source class
  noted where material; explicit per-citation source-class labels
  are deferred to a v0.1.14 doc-fix sweep (W-FRESH-EXT)."

---

## Summary-surface sweep (per AGENTS.md "Summary-surface sweep on partial closure")

| Surface | Change |
|---|---|
| §1 Executive verdict | Path A is now 4-release (was 3-release); v0.2.0 split language updates |
| §2 Method | provenance paragraph softens "primary source" claim |
| §9 Visual roadmap diagram | Path A diagram shows 4 releases |
| §10 v0.1.14 acceptance | "≤4 rounds" → "≤5 rounds with re-scope clause" |
| §11 v0.2.0 split | Path A table grows to 4 rows |
| §18 Anti-pattern table | OWASP MCP numbered claims removed |
| §19 OQ-K | CALM-grounded → bias-literature-informed |
| §19 OQ-B | Path A reference updated to 4-release |
| §20 v0.2.0/v0.2.1/v0.2.2/v0.2.3 catalogue | restructured to 4 releases |
| §21 Local citations | ARCHITECTURE.md:174-199 → reporting/docs/architecture.md:174 |
| §21 External citations | PHA authors → Heydari et al.; CALM → Ye et al. 2025 ICLR; Apple title softened |
| §21 Close-out note | Mechanical pass deferred to W-FRESH-EXT |
| §22 Caveat | Path A reference matches 4-release shape |

---

## Round-3 decision

Per Codex's empirical-settling note: "expected round-3 yield should
be 0-2 findings if the maintainer applies a mechanical sweep rather
than hand-editing only the named lines."

**Maintainer choice:**

- **Option A — close at round 2 (recommended).** All 7 findings are
  ACCEPT; the revisions are mechanical and localised. Round 3 would
  be a verification-only pass with low expected yield. Cost saved:
  ~1 Codex session.
- **Option B — run round 3.** Verify the round-2 revisions land
  cleanly + spot-check the §21 mechanical pass. Yield: 0-2 findings
  expected. Maintains audit-chain discipline.

Default: **Option A**, close at round 2 by accepting the named
revisions. The empirical-settling shape for research-audit cycles is
unknown (per F-RES-10), so the discipline argument for Option B has
weight. Maintainer makes the call.

---

## What this round taught about the research-audit pattern (per F-RES-10 / OQ-O)

- **Round 1 caught 10 findings** — the original artifact had real
  provenance + sizing + framing issues.
- **Round 2 caught 7 findings** — all from incomplete propagation
  of round-1 revisions; none were strategic-posture issues.
- **The pattern matches D14 plan-audit empirical settling shape**
  (round 1 ~10, round 2 ~5-7, expected round 3 ~0-2).
- **Cost vs benefit:** the 17 cumulative findings would otherwise
  have reached PLAN.md authoring or the v0.1.14 cycle. Catching them
  at the research-artifact layer saved at least one D14 round per
  cycle they would have entered.

OQ-O's eventual retrospective (after the next strategic-research
cycle uses the pattern) should treat this as N=1 evidence that the
pattern *settles like a D14 plan-audit*, not as proof it should be
codified to D16. One more cycle of evidence is needed.
