# Post-v0.1.13 Strategic Research — Reconciliation

**Date:** 2026-05-01
**Subject artifact:** `reporting/plans/post_v0_1_13/strategic_research_2026-05-01.md`
**Audit chain:** Codex round 1 + maintainer round-1 response + Codex round 2 + maintainer round-2 response.

---

## 1. Audit-chain settling shape

| Round | Codex verdict | Findings | Maintainer disposition |
|---|---|---|---|
| 1 | REPORT_SOUND_WITH_REVISIONS | 10 | 9 ACCEPT, 1 PARTIAL-ACCEPT, 0 DISAGREE |
| 2 | REPORT_SOUND_WITH_REVISIONS | 7 | 7 ACCEPT, 0 PARTIAL, 0 DISAGREE |
| **Cumulative** | **closed at round 2** | **17** | |

Empirical-settling shape (10 → 7 → 0-2 expected at round 3) matches
the D14 plan-audit prior. Round 2 closed without a round 3 because
the residual issues were mechanical citation errors deferred to the
v0.1.14 doc-fix sweep (W-FRESH-EXT) rather than strategic-posture
disagreements. **One more research-audit cycle is needed (per OQ-O)
before this pattern is empirical evidence rather than N=1
speculation.**

## 2. What survived the chain

The strategic posture established in the original draft survived
both rounds intact. No finding challenged:

- The five hypotheses H1-H5.
- The skill-vs-code boundary as a load-bearing invariant.
- "Refusal IS the demo" as a correctness lever (not a UX choice).
- Local-first / no telemetry / single-user SQLite as a defensible
  posture.
- The audit chain (proposal_log → planned_recommendation → daily_plan
  → recommendation_log → review_outcome) as a load-bearing primitive.
- The five P0 workstream additions (W-2U-GATE, W-PROV-1,
  W-EXPLAIN-UX, W-MCP-THREAT, W-BACKUP).
- The recommendation that v0.1.14 sequence W-2U-GATE first.

P0-6 (the sixth proposed P0 — README hosted-agent caveat) was
withdrawn because Codex F-RES-01 verified the caveat is already
present at README.md:34-38.

## 3. What changed across the chain

### 3.A — v0.1.14 sizing (F-RES-02)

The original draft enumerated only 5 inherited workstreams as the
v0.1.14 baseline. Codex correctly flagged that
`tactical_plan_v0_1_x.md:394-409` names a 9-W-id baseline (W-AH,
W-AI, W-AJ, W-AL, W-AM, W-AN as in-scope plus inherited W-29,
W-Vb-3, W-DOMAIN-SYNC). With the 5 P0/P1 additions, v0.1.14 grows to
**~14 W-ids / 32-45 days / 4-5 D14 rounds expected** (revised from
30-40 per v0.1.14 D14 F-PLAN-R2-01 + F-PLAN-R3-01). Original 23-29
day estimate was undercounted.

### 3.B — v0.2.0 split shape (F-RES-03 → F-RES-R2-01)

**Round 1** correctly named the C6 vs CP5 tension (which the
original draft missed) and proposed a 3-release Path A. **Round 2**
corrected that further: the 3-release Path A still left v0.2.1 with
two schema groups (insight ledger + judge log), violating C6. The
strict-C6 split is **4 releases**:

- v0.2.0 W52 + W58D + adjuncts (one schema group)
- v0.2.1 W53 insight ledger only (one schema group)
- v0.2.2 W58J shadow + bias panel (one schema group)
- v0.2.3 W58J flip to blocking + W-30 (no new schema)

Total v0.2.x: 39-56 days across four cycles. Path B fallback
(single-release per CP5 with new CP overriding C6) remains valid.

### 3.C — Provenance discipline (F-RES-06 → F-RES-R2-06 → deferred)

Round 1 caught two mechanical citation errors (pyproject.toml:3
should be :7; AGENTS.md:425 was prose, not a file-length citation).
Round 2 caught two more in a wider spot-check
(`ARCHITECTURE.md:174-199` was impossible — file is 111 lines; PHA
authors were Heydari et al. 2025, not Wang/Cosentino). Both rounds
of named errors are corrected. **A full mechanical citation pass
over §21 is deferred to v0.1.14 W-FRESH-EXT** since Codex's spot-
check rate suggests more remain. This is honest deferral, documented
in §21 close-out + §22.

### 3.D — External-source framing (F-RES-04, F-RES-05, F-RES-08, F-RES-09 → F-RES-R2-03/04/05)

Four classes of external-source claim were over-stated in the
original draft and corrected across both rounds:

- **OWASP MCP Top 10 mapping** — original draft's item-by-item
  mapping was wrong; §14 S-1 now marked pending re-verification;
  §18 numbered references replaced with unnumbered "OWASP-MCP-
  pattern" labels. Re-verification is part of W-MCP-THREAT in
  v0.2.0.
- **CALM citation** — original draft cited "Park et al. 2024";
  Codex round-2 confirmed via OpenReview ID 3GTtZFiajM that the
  canonical citation is **Ye et al. 2025, ICLR — "Justice or
  Prejudice? Quantifying Biases in LLM-as-a-Judge."** Citation
  corrected; numeric promotion thresholds relabeled as
  HAI-proposed acceptance gates rather than literature-derived.
- **Apple framing** — original draft framed the MDDI piece as a
  regulatory mandate; corrected to App Store policy / trade press
  signal. The local "no clinical claims" invariant is anchored to
  AGENTS.md governance #3 + FDA general-wellness boundary, not the
  Apple piece.
- **Garmin MCP quantification** — "8+" and "all built on
  python-garminconnect" were unsourced; removed. Strategic
  conclusion (D5 settled, intervals.icu default is correct) holds
  regardless of the count.

### 3.E — Method-statement honesty (F-RES-07 → F-RES-R2-07)

Original draft said "Primary sources only" for Phase 4 external
landscape. The actual source base mixed primary papers and specs
with vendor statements, trade press, security blogs, and CVE
timelines. Both rounds tightened: §2 Phase 4 now reads "primary
sources where available; vendor statements, trade press, and
security advisories used for landscape claims and explicitly flagged
in §21." Per-citation source-class labels are deferred to
W-FRESH-EXT.

### 3.F — Pattern precedent (F-RES-10)

Original draft did not propose D16 codification of the research-
audit pattern but implicitly normalised it. Codex correctly flagged
that promoting on N=1 evidence violates the project's settled-
decision discipline. §22 now explicitly says "remain ad-hoc until at
least one more strategic-research cycle produces evidence." OQ-O
schedules a retrospective.

## 4. Disagreements

**None.** Across both rounds, the maintainer accepted every Codex
finding (9 + 7 = 16 ACCEPT, 1 PARTIAL-ACCEPT in round 1 on F-RES-03
where the substance was accepted but the framing was narrowed to
"name the choice as a maintainer call" rather than "unilaterally
overrule CP5").

This is unusual relative to D14 plan-audit chains where Codex and
the maintainer typically disagree on 1-2 findings per cycle. The
reason is structural: a research artifact has lower-stakes
recommendations than a PLAN (no implementation downstream), so
provenance + framing corrections are less likely to surface
strategic-posture disagreements that would warrant push-back.

## 5. What remains open

**Maintainer decisions surfaced as OQs (§19 of the artifact):**

- **OQ-B (load-bearing):** Path A (4-release strict-C6) vs Path B
  (single-release per CP5 with new CP overriding C6)? This shapes
  v0.2.0+ scope significantly.
- **OQ-I:** Designate the 2026-04-28 demo recipient as the
  W-2U-GATE first foreign user, or different candidate?
- **OQ-J:** Adopt "domain-pinned AgentSpec for personal health"
  framing in README.md opener? Branding choice, not architecture.
- **OQ-M:** `hai support` (redacted state bundle) in v0.1.14 or
  v0.2.0?

**Maintainer decisions with proposed defaults (likely yes; will
draft CPs as proposals):**

- OQ-A (accept v0.1.14 P0 additions)
- OQ-C (pull MCP threat-model forward to v0.2.0)
- OQ-D (add P13 low-domain-knowledge persona)
- OQ-E (author competitive_landscape + n_of_1_methodology in v0.2.0)
- OQ-F (add Strava / MCP-autoload / threshold-mutation rules to AGENTS.md "Do Not Do")
- OQ-G (author mcp_threat_model.md before v0.3 PLAN.md)
- OQ-H (schedule annual hypothesis review)
- OQ-K (promote LLM judge by quantitative bias panel)
- OQ-L (accept FActScore + MedHallu vocabulary)
- OQ-N (re-verify OWASP MCP Top 10 mapping)
- OQ-O (schedule research-audit retrospective)

## 6. Next-step punch list

After this reconciliation, the work tree opens onto:

1. **Maintainer decisions on OQ-B / OQ-I / OQ-J / OQ-M** — required
   inputs to CP authoring.
2. **Mechanical doc-fix sweep (partial — applied 2026-05-01):**
   - README.md:48 — 15 → 14 skills (DONE).
   - ROADMAP.md:79-90 — Dependency Chain rewritten to current Wave
     structure (DONE).
   - privacy.md hosted-agent-exposure tightening (P2-5; deferred to
     v0.1.14 doc-fix sweep).
3. **CP drafts (authored 2026-05-01 as proposals; not applied to
   AGENTS.md until maintainer approves):**
   - `CP-2U-GATE-FIRST.md` — insert W-2U-GATE as first v0.1.14 W-id.
   - `CP-MCP-THREAT-FORWARD.md` — pull MCP threat-model authoring
     forward to v0.2.0 (precedes v0.3 PLAN-audit).
   - `CP-DO-NOT-DO-ADDITIONS.md` — three additions to AGENTS.md "Do
     Not Do" (Strava-anchored data path, MCP autoload from project
     files, threshold mutation without explicit user commit).
4. **CPs blocked on OQ-B:**
   - `CP-PATH-A.md` (if Path A) or `CP-PATH-B.md` (if Path B) —
     formalises the v0.2.0 split choice + revisits CP5/C6 tension.
   - `CP-W30-SPLIT.md` — destination depends on Path A (v0.2.3) vs
     Path B (v0.2.0.x).
5. **v0.1.14 PLAN.md authoring** with the reconciled scope (14
   W-ids, 32-45 days, ≤5 D14 rounds expected — sizing revised per
   v0.1.14 D14 F-PLAN-R2-01).
6. **D14 plan-audit on the new PLAN.md** (the standard cycle
   discipline takes over from here).

## 7. Settled-decision implications

This reconciliation does not propose any AGENTS.md edits beyond what
the CP drafts will (each CP is its own settled-decision change).
Specifically, **the research-audit pattern itself is NOT being
proposed for D16 status**. Per OQ-O, the retrospective happens after
the next strategic-research cycle uses the pattern — at which point
N=2 evidence is available and the empirical-settling shape can be
declared (or not).

## 8. Trust assessment

The chain caught 17 cumulative findings the original draft would
have carried into v0.1.14 PLAN.md authoring or cycle-proposal text.
The most material catches were:

- **Provenance**: 4 mechanical citation errors (pyproject:3 →:7;
  AGENTS.md:425 framing; ARCHITECTURE.md:174-199 impossible; PHA
  authors).
- **Sizing**: v0.1.14 undercounted by 4 W-ids / 7-11 days.
- **Framing**: 4 external-source claims softened (OWASP MCP, CALM,
  Apple, Garmin).
- **Strategic shape**: v0.2.0 split corrected from "CP5 is correct"
  to "CP5 vs C6 is a maintainer choice" to "Path A strict-C6 is
  4 releases, not 3."

The artifact is now usable as input to the v0.1.14 PLAN.md authoring
phase, conditional on the four maintainer OQs being resolved.

The audit chain itself — research artifact → 2-round Codex review →
reconciliation → CP drafts → PLAN authoring → D14 plan-audit — was
worth the investment. **Whether to codify it as D16 is a separate
decision deferred to OQ-O.**
