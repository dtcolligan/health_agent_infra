# Codex Research Audit — Round 1 Maintainer Response

**Round:** 1
**Codex verdict:** REPORT_SOUND_WITH_REVISIONS
**Maintainer disposition:** ACCEPT 9 / PARTIAL-ACCEPT 1 / DISAGREE 0
**Action:** apply revisions to `strategic_research_2026-05-01.md` in place; surface the partial-accept explicitly so a round-2 audit can verify resolution.

---

## Summary

10 findings filed. 9 accepted as-stated, 1 (F-RES-03 / C6 migration cadence) accepted in substance with a narrower framing. The cumulative effect of the revisions:

- **§5 shrinks from 6 P0s to 5** (P0-6 deleted; the README hosted-agent caveat is already at README.md:34-38 — verified).
- **§10 v0.1.14 cycle estimate revises upward** from 23-29 days to 30-40 days, reflecting the full tactical-plan baseline (W-AH, W-AJ, W-AM, W-AN) which the report previously omitted. Total W-id count revises from "10 total" to ~14 total.
- **§11 v0.2.0 split engages with reconciliation C6 explicitly.** The report originally treated CP5 as having settled the question; Codex correctly noted C6 (one conceptual schema group per release) was not addressed. Revision: name two viable paths and identify which the maintainer must choose; do not silently overrule CP5 *or* C6.
- **§13 E-3 + §6 P1-2** relabel CALM thresholds as HAI-proposed acceptance gates, not literature-derived. CALM citation metadata corrected (Ye 2025 ICLR per Codex; will re-verify against primary).
- **§14 S-1 OWASP MCP Top 10 mapping** marked pending re-verification; not usable as external-narrative artifact until rebuilt from the OWASP source.
- **§3 + §18 Apple framing** softened from "regulatory mandate" to "App Store policy / compliance signal."
- **§15 + §18 Garmin MCP quantification** removes "8+" and "all" claims; strategic conclusion stays anchored to D5.
- **§2 method statement** softened from "primary sources only" to "primary sources where available; secondary flagged."
- **§3 + §21 mechanical citation errors** corrected (pyproject.toml:3 → :7; AGENTS.md:425 file-length claim removed).
- **§22 caveat / D16 framing** acknowledges Codex F-RES-10: research-audit precedent stays ad-hoc for now; no D16 proposal until ≥1 more cycle of evidence.

The revisions do not change any of the report's core P0 / P1 recommendations beyond P0-6's removal and the v0.1.14/v0.2.0 sizing/scope corrections. The strategic posture (skill-vs-code boundary, refusal IS the demo, local-first, audit chain) is unaffected.

---

## Per-finding disposition

### F-RES-01 — README hosted-agent caveat already present

**Disposition:** ACCEPT.

**Verification:** README.md:34-38 reads:

> "The package stores state locally and has no telemetry path. Pull commands only call the configured data source, currently intervals.icu or Garmin Connect. If you drive the runtime with a hosted LLM agent, any context you send to that host is governed by that host's data policy; Health Agent Infra does not control the model provider."

The report's claim ("README does not duplicate this caveat") is false on disk. P0-6 is a false positive.

**Action:**
- Delete §5 P0-6 entirely.
- Renumber §5 P0s if needed (kept as P0-1 .. P0-5).
- Update §1 executive verdict ("six things will silently break trust") to "five things."
- §10 "Recommended doc-only additions" — delete the agent-runtime exposure paragraph addition.
- §19 OQ list — no change (none of the OQs depended on P0-6).
- Self-flag this as a `provenance-failure` against the report's own discipline; the original draft cited AGENTS.md governance invariant #4 without re-verifying README state.

**Sub-finding:** privacy.md tightening could still be a P2 doc-alignment item per Codex's recommended response. Add to §6 as P2-5.

### F-RES-02 — v0.1.14 scope and sizing undercount

**Disposition:** ACCEPT.

**Verification:** tactical_plan_v0_1_x.md:394-401 lists v0.1.14 in-scope as:

| W-id | Title | Effort |
|---|---|---|
| W-AH | Scenario fixture expansion: 30+ new per-domain scenarios | 3-4 days |
| W-AI | Ground-truth labelling methodology + maintainer review tool | 2-3 days |
| W-AJ | LLM-judge harness scaffold | 2-3 days |
| W-AL | Calibration eval | 2 days |
| W-AM | Adversarial scenario fixtures | 1-2 days |
| W-AN | `hai eval run --scenario-set <set>` CLI | 1-2 days |

Plus inherited W-29, W-Vb-3, W-DOMAIN-SYNC (lines 405-409). The tactical plan's own effort estimate (line 436-437) is **15-22 days** for this inherited+in-scope set.

The report's §10 listed only W-29, W-Vb-3, W-DOMAIN-SYNC, W-AI, W-AL — missing W-AH, W-AJ, W-AM, W-AN. The "5 held W-ids" framing was wrong.

**Action:**
- Revise §10 "Current named scope" to enumerate all 9 baseline W-ids per tactical_plan_v0_1_x.md:394-409.
- Revise §10 cycle-tier discussion: actual baseline is 9, +5 P0 additions = **14 total W-ids**, not 10.
- Revise §10 cost: tactical-plan baseline is 15-22 days; +5 P0 (W-2U-GATE 2-3, W-PROV-1 3-4, W-EXPLAIN-UX 2, W-BACKUP 3-4, W-FRESH-EXT 1) = **+11-14 days**, total **26-36 days**. Round to **30-40 days** with contingency.
- Add explicit contingency clause to §10: "If W-2U-GATE surfaces a structural blocker, v0.1.14 reshapes around the fix; downstream work moves to v0.1.15."
- Revise §10 D14 expectation: not "4 rounds, 10→5→3→0 (the empirical norm)" but **"unknown / likely 5+ rounds; v0.1.13 settled at 5 rounds for 17 W-ids; v0.1.14 at 14 W-ids should expect 4-5 rounds."**
- Revise §20 v0.1.14 cycle estimate from "23-29 days" to "30-40 days."

### F-RES-03 — v0.2.0 split ignores reconciliation C6

**Disposition:** PARTIAL ACCEPT — accept the substance, narrow the framing.

**Verification:** reconciliation.md:147 reads:

> "**Migration cadence:** the store has strict gap detection. v0.2.0 should not add weekly review tables + insight ledger tables + judge log tables in one migration burst. **One conceptual schema group per release.**"

This is an *accepted consolidation* (C6 in the reconciliation taxonomy), not a disagreement. The report's §11 cited CP5 as having settled the v0.2.0 single-release shape, but CP5 (per tactical_plan:450) addressed *W52↔W58 design coupling*, not migration cadence. C6 is a separate constraint that CP5 did not engage with, and the report inherited that gap.

**Why partial accept:** CP5 was a deliberate maintainer decision; the report should not silently overrule it. But Codex is right that the report should at minimum *name* the C6 vs CP5 tension and identify the choice the maintainer must make.

**Action:**
- Revise §11 to add a "C6 vs CP5 tension" subsection.
- Name two viable paths:
  - **Path A — Honor reconciliation D1 / C6 with 3-release split.** v0.2.0 = W52 weekly review + W58 deterministic claim-block (one schema group: weekly-review tables). v0.2.1 = W53 insight ledger + W58 LLM judge shadow (one schema group: insight + judge log tables). v0.2.2 = judge promotion to blocking (no schema; flag flip + bias panel). Requires revisiting CP5.
  - **Path B — Keep CP5 single-release shape.** v0.2.0 = W52 + W53 + W58D + W58J shadow (3 schema groups). Requires authoring a new CP that explicitly overrides C6 with named reasoning (e.g., "W52 source-row locator schema is shared with W53 insight ledger and W58 claim block; splitting forces N-1 unsupported migrations").
- The report's recommendation: **Path A** (honor C6 + reconciliation D1). Reasoning: C6's migration-cadence concern is correctness-flavored (the gap detector *will* trip if 3 schema groups land at once); CP5's design-coupling concern is sequencing-flavored (W52 needs W58D to ground its claims, but W52+W58D is one schema group already). Path A satisfies both.
- §11 cycle-size estimate: revise from "30-39 days single release" to "split per Path A reduces v0.2.0 to 18-24 days; v0.2.1 18-24 days; v0.2.2 5-8 days."
- §1 executive verdict: revise to reflect Path A as the recommended posture, with Path B as the named alternative.
- §19 OQ-B: replace "move W-30 out" with "choose Path A (3-release) or Path B (CP5 + new CP overriding C6)."

**Self-flag:** the original §11 claimed CP5 was "correct" without engaging with C6. That was over-confident. The honest framing is "CP5 addresses W52↔W58 design coupling; C6 addresses migration cadence; they are not the same constraint and the maintainer's choice between them is a real decision."

### F-RES-04 — OWASP MCP Top 10 mapping inaccurate

**Disposition:** ACCEPT.

**Verification:** Codex provides what it claims is the current OWASP MCP Top 10 list:

- MCP01 Broken Authentication/Authorization
- MCP02 Token Theft
- MCP03 Tool Poisoning
- MCP04 Excessive Permissions
- MCP05 Command Injection
- MCP06 Indirect Prompt Injection
- MCP07 Sensitive Information Disclosure
- MCP08 Rug Pulls
- MCP09 Tool Shadowing
- MCP10 Tool Metadata Spoofing

The report's §14 S-1 mapped MCP1 → token mismanagement, MCP3 → command injection, MCP5 → tool poisoning, MCP10 → context oversharing. Several of these are wrong against Codex's list.

**Caveat:** I cannot independently verify Codex's list either. Both the original mapping and Codex's correction came from web research; neither is anchored to a primary-source SHA. The honest move is to mark the mapping as pending re-verification and not use it as an external-narrative artifact until verified against the OWASP project page.

**Action:**
- Revise §14 S-1 to: "OWASP MCP Top 10 (2026 beta) reads like a checklist of HAI's existing invariants. **The detailed item-by-item mapping below is authored from secondary research; verify against https://owasp.org/www-project-mcp-top-10/ before using as external-narrative-grade artifact.**" Then list the 10 items per Codex's correction with HAI's invariant alignment for each.
- §1 executive verdict: no change (the OWASP claim was a supporting argument, not a load-bearing one).
- Add to §19 OQs: "OQ-N — Re-verify OWASP MCP Top 10 mapping before W-MCP-THREAT cites it." Default: yes; doc-fix-sweep work.

### F-RES-05 — CALM citation + judge-threshold over-claim

**Disposition:** ACCEPT.

**Verification:** Codex says CALM is "Ye et al. 2025 ICLR meta-reviewer benchmark," not "Park 2024." The original report cited "Park 2024 CALM" via the Phase 5 literature agent; that may be a different paper or a misattribution.

The numeric thresholds (position bias <5%, verbosity <10%, score-rubric-order <5%, reference-answer <5%, self-consistency ≥0.8) were authored by me as proposed acceptance gates, *informed by* the bias literature but not derived from CALM specifically. The report did not distinguish "literature-derived thresholds" from "HAI-proposed thresholds."

**Action:**
- §6 P1-2: correct CALM attribution to Ye et al. 2025 ICLR pending re-verification of the primary source.
- §13 E-3: relabel each threshold as "HAI-proposed acceptance gate (informed by the LLM-judge bias literature; not derived from a single benchmark paper)."
- §21 citations: replace "Park et al. 2024 CALM" with "Ye et al. 2025 (ICLR), CALM meta-reviewer benchmark — citation requires primary-source verification."
- W-JUDGE-BIAS workstream description in §20: keep, but acceptance criterion now reads "thresholds set per local validation, not adopted from literature."
- Self-flag as `over-claim`: the original draft conflated literature-anchored bias categories with maintainer-proposed numeric gates.

### F-RES-06 — Local citation appendix has broken line references

**Disposition:** ACCEPT.

**Verification (mechanical):**
- pyproject.toml:7 reads `version = "0.1.13"`. Line 3 reads `build-backend = "setuptools.build_meta"`. The report's `pyproject.toml:3 (version 0.1.13)` is wrong.
- AGENTS.md:425 reads `when. Always check there before authoring a new plan doc.`  This is prose about the planning index, not a file-length citation. The report's `AGENTS.md:425 (file length)` is wrong; what was meant was "the file is 425 lines long," which is `wc -l` output, not a line-number citation.

**Action:**
- §3 evidence-ledger summary: replace `pyproject.toml:3` with `pyproject.toml:7`.
- §21 appendix: replace `pyproject.toml:3 (version 0.1.13)` with `pyproject.toml:7 (version 0.1.13)`.
- §21 appendix: replace `AGENTS.md:...:425 (file length)` with `AGENTS.md (425 lines total per wc -l).` to disambiguate.
- Run a mechanical citation pass over §21 appendix before next round; flag any other line-number mismatches.

### F-RES-07 — Method overclaims "primary sources only"

**Disposition:** ACCEPT.

**Verification:** §2 says "Primary sources only" for Phase 4 external landscape. §21 in fact lists primary papers (arXiv, Nature) alongside vendor pages (Strava press, WHOOP press, Oura cloud), trade press (MDDI, Wareable), security blogs (Check Point, OX, eSentire, Practical DevSecOps), Medium posts, and a CVE timeline blog. The "primary sources only" framing is overconfident.

**Action:**
- §2 Phase 4 line: replace "Primary sources only" with "Primary sources where available; vendor statements, trade press, and security advisories used for landscape claims and explicitly flagged."
- §21 appendix: add a one-line source-class label to each citation block — `(paper)`, `(spec)`, `(vendor statement)`, `(trade press)`, `(security advisory)`, `(product documentation)`. Apply to all external citations.
- Self-flag as `over-claim`.

### F-RES-08 — Apple medical-device source overread as regulatory action

**Disposition:** ACCEPT.

**Verification:** The MDDI piece (https://www.mddionline.com/digital-health/apple-mandates-medical-device-status-for-health-apps-by-2027) is about Apple's App Store policy requiring health apps to declare medical-device status, not a regulator-issued mandate. The report framed this as "regulatory tightening" / "regulatory mine," which inflates the source.

**Action:**
- §3 external anchors: revise "Apple medical-device disclosure mandate (March 2026): clinical-drift regulation tightening, not loosening" to "Apple App Store medical-device-status disclosure policy (effective by 2027): platform-level compliance signal, not a regulator action."
- §18 anti-pattern table, "Clinical claims / diagnosis prose" row: revise "Apple medical-device disclosure mandate March 2026" to "Apple App Store medical-device-status disclosure policy."
- §21 caveat about MDDI: keep the citation but change the framing label from "regulatory mandate" to "App Store policy".
- Note that the local "no clinical claims" invariant (AGENTS.md governance #3) does not depend on the Apple source — it is anchored to FDA general-wellness guidance and the project's own non-goals. Removing the Apple overread does not weaken the recommendation.

### F-RES-09 — Garmin MCP landscape quantification unsupported

**Disposition:** ACCEPT.

**Verification:** The "8+ Garmin community MCPs" and "all built on `python-garminconnect`" claims came from the Phase 4 web research agent without a citation table. Audit-grade work would require listing each project with its dependency chain.

**Action:**
- §15 D-5: replace "8+ Garmin community MCPs all built on python-garminconnect" with "Multiple community Garmin MCPs exist (per April 2026 web search); the leading ones reuse the `python-garminconnect` SSO library, which inherits the per-account 429 rate limit. Specific project counts and dependency chains require a sourced inventory before audit-grade citation."
- §18 anti-pattern table, "60+ raw vendor-API tools" row: keep specific named projects (`Nicolasvegam/garmin-connect-mcp`, `eddmann/garmin-connect-mcp`) since those are individually verifiable; remove unsourced aggregate counts.
- The strategic recommendation (don't make Garmin Connect the default; D5 already settled) does not depend on the unsourced count.

### F-RES-10 — Don't promote research-audit to D16 yet

**Disposition:** ACCEPT.

**Verification:** Codex correctly notes that D11/D14/D15 each became settled patterns after multi-cycle evidence. This is the first time the audit pattern has been applied to a research artifact, so promoting it to D16 on N=1 evidence would violate the project's own settled-decision discipline. R-O-02 (cycle pattern collapse) and R-O-05 (releases becoming prose-heavy) are both relevant load-bearing risks.

**Action:**
- §22 ("Caveat") add a final paragraph: "This audit shape (research-artifact + Codex review + reconciliation) is being applied for the first time on this report. The pattern should remain ad-hoc until at least one more strategic-research cycle produces evidence that it catches blocking findings that would otherwise have reached PLAN.md. Not a D16 candidate at N=1."
- §19 OQs: add "OQ-O — Schedule a retrospective on the research-audit pattern after the next cycle uses it (or doesn't), before considering D16 status." Default: yes.

---

## Summary-surface sweep

The accepted revisions move multiple summary surfaces in lockstep per AGENTS.md "Summary-surface sweep on partial closure":

| Surface | Change |
|---|---|
| §1 Executive verdict | "six things" → "five things"; v0.2.0 split posture revised; v0.1.14 sizing revised |
| §2 Method | "primary sources only" → "where available; secondary flagged" |
| §3 Evidence ledger | pyproject.toml line fix; Apple framing softened; CALM citation flagged |
| §5 P0 catalogue | P0-6 removed (5 P0s remain) |
| §6 P1/P2 catalogue | CALM threshold relabel; P2-5 added (privacy.md tightening) |
| §10 v0.1.14 plan | full baseline enumerated; cost 30-40 days; D14 expectation revised |
| §11 v0.2.0 split | Path A (3-release per C6) recommended; CP5 vs C6 tension named |
| §13 Eval plan | E-3 thresholds relabeled HAI-proposed |
| §14 Security plan | OWASP mapping marked pending re-verification |
| §15 Data-source plan | "8+ / all" Garmin claims removed |
| §18 What-not-to-build | Apple framing softened |
| §19 Open decisions | OQ-B revised; OQ-N + OQ-O added |
| §20 Workstream catalogue | v0.1.14 size revised; v0.2.0 split per Path A |
| §21 Citations | source-class labels added; line-number errors fixed |
| §22 Caveat | D16 framing acknowledged |

---

## Open questions for round 2

1. **C6 vs CP5 (F-RES-03):** the report now recommends Path A (3-release) but does not unilaterally make the call. Maintainer must choose Path A vs Path B before v0.2.0 PLAN.md authoring. Round 2 audit can verify the choice was made and the corresponding revisions propagate.
2. **OWASP MCP Top 10 (F-RES-04):** the §14 S-1 mapping is now marked pending re-verification. Round 2 audit should verify primary-source check has been done and the table rebuilt.
3. **CALM primary source (F-RES-05):** "Ye 2025 ICLR" was Codex's correction; verify against ICLR 2025 program before round 2.
4. **Mechanical citation pass (F-RES-06):** the two found errors (pyproject:3, AGENTS:425) suggest others may exist. Round 2 audit should spot-check 5+ additional citations.

---

## Verdict on this response

The 9 ACCEPT findings are mechanical / provenance-flavored corrections that do not change the report's strategic recommendations — they tighten provenance and remove false positives. The 1 PARTIAL ACCEPT (F-RES-03 / C6) is the only finding that materially changes a recommendation, and even there the change is "name the choice explicitly" rather than "reverse the call."

If round 1 revisions land cleanly, the report's expected verdict on round 2 is **REPORT_SOUND** absent new findings. The empirical-settling shape for research-audit rounds is unknown (per F-RES-10), so this is best-guess.

Round 1 close-out is the next step: apply the named revisions to `strategic_research_2026-05-01.md` in place, then surface the diff to the maintainer for round-2 audit launch (or skip round 2 if the maintainer is satisfied with the round-1 fixes).
