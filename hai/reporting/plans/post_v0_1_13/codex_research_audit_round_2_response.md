# Codex Research Audit Round 2 Response — Strategic Research 2026-05-01

**Verdict:** REPORT_SOUND_WITH_REVISIONS

**Round:** 2

**Round-1 follow-through summary:** Most round-1 revisions landed in substance, but not cleanly enough to close without edits. F-RES-01, F-RES-09, and F-RES-10 landed cleanly. F-RES-02, F-RES-03, F-RES-04, F-RES-05, F-RES-07, and F-RES-08 landed partially but left residual or second-order issues. F-RES-06 fixed the two named citations, but the round-2 citation spot-check found new appendix errors. MedHallu F1=0.625 / up-to-38% abstention and JITAI g=0.15 spot-checks held.

## Findings

### F-RES-R2-01. Path A still violates C6 in v0.2.1

**Q-bucket:** R2-Q2  
**Severity:** second-order-issue  
**Reference:** `strategic_research_2026-05-01.md` §11, lines 886-895; §20, lines 1454-1471  
**Argument:** The revised report says Path A “honors C6” by splitting v0.2.0 into three releases, but its v0.2.1 still ships W53 insight ledger + W58J judge shadow + W-JUDGE-BIAS with “insight ledger + judge log (two groups — borderline; could split further)” (`strategic_research_2026-05-01.md:894`, `:1469-1471`). That does not satisfy reconciliation C6, which says “One conceptual schema group per release” (`reporting/plans/future_strategy_2026-04-29/reconciliation.md:147`). The report moved the C6 problem from v0.2.0 to v0.2.1 while still describing Path A as C6-honoring.
**Recommended response:** Either split Path A into four releases (v0.2.0 W52+W58D, v0.2.1 W53, v0.2.2 W58J shadow, v0.2.3 judge promotion + W-30) or explicitly say Path A honors C6 for v0.2.0 only and still requires a maintainer call on v0.2.1’s two schema groups. Update §1, §9 visual roadmap, §11, §19 OQ-B, §20, and §22 caveat consistently.

### F-RES-R2-02. v0.1.14 D14 acceptance criterion conflicts with revised sizing

**Q-bucket:** R2-Q1  
**Severity:** unfinished-revision  
**Reference:** `strategic_research_2026-05-01.md` §10, lines 820-848  
**Argument:** The F-RES-02 revision correctly updates v0.1.14 to 14 W-ids / 30-40 days and says to expect 4-5 D14 rounds (`strategic_research_2026-05-01.md:822-829`). But the same section still makes ship acceptance require `PLAN_COHERENT` within `<=4` rounds (`strategic_research_2026-05-01.md:844-848`). That recreates the original under-sizing problem as an impossible or misleading gate: a 5-round D14 would be expected by the revised evidence but would fail the section’s acceptance criteria.
**Recommended response:** Change the acceptance criterion to “D14 verdict `PLAN_COHERENT`; if it exceeds 5 rounds, maintainer re-scopes before implementation.” Do not hard-fail a 5-round settlement on a 14-W-id cycle.

### F-RES-R2-03. OWASP MCP numbering residue remains outside §14

**Q-bucket:** R2-Q4  
**Severity:** residual-claim  
**Reference:** `strategic_research_2026-05-01.md` §18, lines 1280 and 1289  
**Argument:** §14 correctly marks the OWASP MCP mapping pending re-verification and lists the corrected tentative enumeration (`strategic_research_2026-05-01.md:1061-1073`). Later, §18 still uses the old-style numbered claims: “OWASP MCP10 (context oversharing)” and “OWASP MCP1 + MCP7 + MCP10” (`strategic_research_2026-05-01.md:1280`, `:1289`). Under the corrected enumeration in §14, MCP10 is Tool Metadata Spoofing, not context oversharing; token relay risk is at least MCP02 Token Theft, not MCP10. This is exactly the residual numbering drift F-RES-04 was meant to prevent.
**Recommended response:** Remove numbered OWASP references from §18 until W-MCP-THREAT verifies the source. Use unnumbered labels such as “token theft, sensitive disclosure, and metadata spoofing” or cite §14’s pending-verification note.

### F-RES-R2-04. CALM correction did not propagate to OQ-K or appendix citation

**Q-bucket:** R2-Q1 / R2-Q4  
**Severity:** unfinished-revision / residual-claim  
**Reference:** `strategic_research_2026-05-01.md` §19, lines 1334-1335; §21, lines 1564-1569 and 1585  
**Argument:** §6 and §13 now correctly say CALM is Ye et al. 2025 ICLR pending verification and that numeric thresholds are HAI-proposed (`strategic_research_2026-05-01.md:464-475`, `:1011-1024`). But §19 still says OQ-K defaults to “CALM-grounded” (`strategic_research_2026-05-01.md:1334-1335`), and §21 still lists “CALM, Park et al. 2024” (`strategic_research_2026-05-01.md:1585`). The primary-source spot-check verifies the OpenReview ID `3GTtZFiajM` is “Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge” by Jiayi Ye et al., ICLR 2025, and it identifies 12 biases. The remaining “Park 2024” and “CALM-grounded” wording should not survive into PLAN input.
**Recommended response:** Replace the appendix citation with “Ye et al. 2025, ICLR, Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge / CALM.” Change OQ-K’s default rationale to “yes; bias-literature-informed, with HAI-proposed thresholds validated locally.”

### F-RES-R2-05. Apple “mandate” framing remains in appendix

**Q-bucket:** R2-Q4  
**Severity:** unfinished-revision / residual-claim  
**Reference:** `strategic_research_2026-05-01.md` §21, lines 1571-1573 and 1610  
**Argument:** The body now frames Apple correctly as App Store policy / trade press, not regulator action (`strategic_research_2026-05-01.md:186-190`, `:1283`). But the external citation list still labels the link “Apple medical-device disclosure mandate (March 2026)” (`strategic_research_2026-05-01.md:1610`) immediately after a note saying it is not a regulator-issued mandate (`strategic_research_2026-05-01.md:1571-1573`). The residual title will be copied into downstream docs unless fixed.
**Recommended response:** Rename the citation to “Apple App Store medical-device-status disclosure policy (MDDI trade press, March 2026).”

### F-RES-R2-06. Citation appendix still has audit-blocking metadata errors

**Q-bucket:** R2-Q3  
**Severity:** provenance-failure  
**Reference:** `strategic_research_2026-05-01.md` §21, lines 1513-1514 and 1575  
**Argument:** The named F-RES-06 fixes landed for `pyproject.toml:7` and the AGENTS.md file-length framing, but the round-2 citation spot-check found two more hard errors. First, §21 cites `ARCHITECTURE.md:174-199 (migrations)` (`strategic_research_2026-05-01.md:1513-1514`), but `ARCHITECTURE.md` is only 111 lines long; the citation likely meant `reporting/docs/architecture.md` or another migration doc. Second, the PHA citation lists “Wang/Cosentino et al. 2025” (`strategic_research_2026-05-01.md:1575`), but the arXiv 2508.20148 metadata names A. Ali Heydari, Ken Gu, Vidya Srinivas, Hong Yu, and others. This spot-check sampled more than five citations and found new errors, so the appendix is not audit-grade yet.
**Recommended response:** Run a full mechanical citation pass over §21 before closing. Fix `ARCHITECTURE.md:174-199` to the correct file or remove it, and correct PHA author metadata to Heydari et al. 2025.

### F-RES-R2-07. “Primary external source” overclaim remains in method

**Q-bucket:** R2-Q1  
**Severity:** unfinished-revision  
**Reference:** `strategic_research_2026-05-01.md` §2, lines 91-107; §21, lines 1555-1562  
**Argument:** The Phase 4 method was softened correctly at lines 91-95, and §21 now admits the external source base mixes papers, specs, vendor statements, trade press, security blogs, and timelines (`strategic_research_2026-05-01.md:1555-1562`). But the provenance paragraph still says every claim traces to a file:line or “to a primary external source in §21” (`strategic_research_2026-05-01.md:105-107`). That is still false for MDDI, Practical DevSecOps, Authzed, Medium, product pages, and several vendor announcements.
**Recommended response:** Replace “primary external source” with “external source listed in §21, with source class and confidence noted where material.” If explicit per-citation source-class labels will be deferred, say so in §2 rather than implying they already exist.

## Empirical-settling note (per R2-Q5)

Round 2 found 7 findings: 4 unfinished/residual revision issues, 2 second-order/provenance issues, and 1 method wording residue. This is not a 10→0 close; it is closer to the D14 “round 2 catches second-order drift” pattern, though the errors are mostly mechanical and localised. A round 3 is warranted after revisions, but it should be short: verify §11 Path A/C6 propagation, residual OWASP/CALM/Apple strings, and the full §21 citation pass. Expected round-3 yield should be 0-2 findings if the maintainer applies a mechanical sweep rather than hand-editing only the named lines.
