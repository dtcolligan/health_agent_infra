# Codex Research Audit Response — Strategic Research 2026-05-01

**Verdict:** REPORT_SOUND_WITH_REVISIONS

Use the report as input only after the named revisions below land. The core strategic direction is broadly usable, but the current artifact has three must-fix classes before it should feed v0.1.14 PLAN authoring: one false P0, undercounted release sizing, and external/source-mapping errors in the MCP and LLM-judge sections.

Sections needing rework: §2, §5 P0-6, §10, §11, §13, §14, §15, §18, §21, and the workstream catalogue estimates in §20.

**Round:** 1 / 2 / 3

## Findings

### F-RES-01. README hosted-agent caveat is already present

**Q-bucket:** Q1 / Q2  
**Severity:** priority-mistake / provenance-failure  
**Reference:** `strategic_research_2026-05-01.md` §5 P0-6, lines 412-428  
**Argument:** The report says the public README does not duplicate the AGENTS.md local-first caveat and makes a doc-only caveat fix P0. That is false on disk. `README.md:34-38` already says the package stores local state and has no telemetry path, and that if a user connects a hosted LLM agent, the context the user shares is governed by that host provider, not by HAI. This directly covers the caveat the report says is missing.  
**Recommended response:** Remove P0-6 from the P0 list and adjust the executive verdict and §10 additions accordingly. If tighter wording is still desired in `reporting/docs/privacy.md`, carry it as a P2 doc-alignment item, not a second-user trust blocker.

### F-RES-02. v0.1.14 scope and sizing undercount the plan-of-record work

**Q-bucket:** Q4  
**Severity:** sizing-mistake / roadmap-error  
**Reference:** `strategic_research_2026-05-01.md` §10, lines 730-761; §20, lines 1215-1266  
**Argument:** The report treats the current v0.1.14 scope as five held W-ids: W-29, W-Vb-3, W-DOMAIN-SYNC, W-AI, and W-AL. The tactical plan names a larger plan-of-record: W-AH scenario expansion, W-AI ground-truth methodology, W-AJ judge harness scaffold, W-AL calibration eval, W-AM adversarial fixtures, W-AN `hai eval run --scenario-set`, plus inherited W-29, W-Vb-3, and W-DOMAIN-SYNC (`reporting/plans/tactical_plan_v0_1_x.md:394-409`). Its acceptance criteria also expect scenario growth to 120+, judge harness outputs, calibration metrics, W-29 byte-stability, and W-Vb residual closure (`reporting/plans/tactical_plan_v0_1_x.md:419-432`). Adding five new W-ids on top of the real baseline yields roughly 14 workstreams, not the report's “10 total W-ids” claim. The 23-29 day estimate is therefore not evidence-led unless the report explicitly rescoping W-AH/W-AJ/W-AM/W-AN out of v0.1.14.  
**Recommended response:** Revise §10 and §20 to either name a formal CP-backed rescope of W-AH, W-AJ, W-AM, and W-AN, or recalculate v0.1.14 with all tactical-plan work included. Add explicit contingency if W-2U-GATE discovers a real second-user blocker. The D14 settling expectation should be “unknown / likely 5+ rounds” rather than implicitly reusing the 4-round norm.

### F-RES-03. v0.2.0 split ignores the reconciliation migration-cadence objection

**Q-bucket:** Q3 / Q5  
**Severity:** roadmap-error / absence  
**Reference:** `strategic_research_2026-05-01.md` §11, lines 799-831  
**Argument:** The report moves W-30 out but keeps W52, W53, W58D, and W58J in a single v0.2.0, then states CP5 is correct. That does not fully engage with the reconciliation document. The reconciliation synthesis split the work into v0.2.0 W52 + W58 deterministic unsupported-claim block, v0.2.1 W53 + W58 LLM-judge shadow, and v0.2.2 blocking after shadow evidence (`reporting/plans/future_strategy_2026-04-29/reconciliation.md:66-80`). The same reconciliation also names “one conceptual schema group per release” as accepted consolidation C6 (`reporting/plans/future_strategy_2026-04-29/reconciliation.md:146-148`). The report may disagree with that, but it currently does not name the disagreement or explain why one release can absorb multiple schema/eval concepts safely.  
**Recommended response:** Revise §11 to explicitly choose between CP5 single-release synthesis and the reconciliation C6 migration-cadence constraint. If keeping CP5, state what evidence overrides C6 and update the 30-39 day estimate. Otherwise split W53/W58J out while keeping W52/W58D together.

### F-RES-04. OWASP MCP Top 10 mapping is inaccurate

**Q-bucket:** Q8  
**Severity:** external-source-failure  
**Reference:** `strategic_research_2026-05-01.md` §14 S-1, lines 950-971  
**Argument:** The report correctly identifies OWASP MCP Top 10 as relevant, but the item mapping is wrong. The current OWASP MCP Top 10 list is MCP01 Broken Authentication/Authorization, MCP02 Token Theft, MCP03 Tool Poisoning, MCP04 Excessive Permissions, MCP05 Command Injection, MCP06 Indirect Prompt Injection, MCP07 Sensitive Information Disclosure, MCP08 Rug Pulls, MCP09 Tool Shadowing, and MCP10 Tool Metadata Spoofing. The report maps MCP1 to token mismanagement, MCP2 to excessive permissions, MCP3 to command injection, MCP5 to tool poisoning, MCP7 to weak auth, and MCP10 to context oversharing. That is not a harmless numbering issue; it would make a threat-model checklist fail provenance review.  
**Recommended response:** Rebuild §14 S-1 from the OWASP source and map each HAI control to the correct MCP item. Until fixed, do not use the MCP threat-model table as an external-narrative-grade artifact.

### F-RES-05. CALM citation and judge-threshold claims are over-stated

**Q-bucket:** Q1 / Q8  
**Severity:** external-source-failure / over-claim  
**Reference:** `strategic_research_2026-05-01.md` §6 P1-2, lines 447-459; §13 E-3, lines 913-926  
**Argument:** The report cites “Park 2024 CALM” and a 12-bias taxonomy, then lists concrete thresholds such as position-bias delta `<5%`, verbosity bias `<10%`, and self-consistency `>=0.8`. Spot-checking the cited benchmark points to CALM as an ICLR 2025 meta-reviewer benchmark by Jiayi Ye et al., not “Park 2024.” More importantly, the report does not distinguish source-backed bias categories from HAI-authored acceptance thresholds. The thresholds may be reasonable proposed gates, but they are not currently proven as CALM-derived.  
**Recommended response:** Correct the CALM citation metadata. Label every numeric threshold in §13 E-3 as a proposed HAI acceptance threshold requiring local validation, not as a literature result. Keep W-JUDGE-BIAS, but make its evidence basis honest.

### F-RES-06. Local citation appendix contains broken line references

**Q-bucket:** Q1  
**Severity:** provenance-failure  
**Reference:** `strategic_research_2026-05-01.md` §3, line 104; §21, lines 1334-1345  
**Argument:** Two sampled local citations are mechanically wrong. The report cites `pyproject.toml:3` for package version, but `version = "0.1.13"` is at `pyproject.toml:7`. The appendix cites `AGENTS.md:425 (file length)`, but `AGENTS.md:425` is ordinary prose telling agents to check the planning index before authoring new plan docs. It is not a file-length citation. The project’s own provenance discipline requires file paths, line numbers, and exact strings to be verified on disk before they feed planning artifacts (`AGENTS.md:289-291`).  
**Recommended response:** Correct these citations and run a mechanical citation pass over §21 before using the report in PLAN.md or cycle-proposal text.

### F-RES-07. Method claims “primary sources only,” but the source base is mixed

**Q-bucket:** Q1 / Q8  
**Severity:** provenance-failure / over-claim  
**Reference:** `strategic_research_2026-05-01.md` §2, lines 78-80; §21, lines 1377-1424  
**Argument:** The method says external landscape research used “Primary sources only.” The appendix is more accurate: it includes primary papers/specs where available, but also vendor/product pages, trade press, security blogs, a Medium post, and timeline posts. That mixed source base is acceptable for landscape scanning, but the method overclaims. It also makes weaker claims look stronger than they are, especially Apple policy, MCP vulnerability summaries, and product-surface comparisons.  
**Recommended response:** Revise §2 to say “primary sources and source-of-record material where available; secondary sources flagged when used.” Add a source-class label to external citations: paper/spec, vendor statement, security advisory, product documentation, or secondary/trade press.

### F-RES-08. Apple medical-device source is overread as regulatory action

**Q-bucket:** Q8  
**Severity:** external-source-failure / over-claim  
**Reference:** `strategic_research_2026-05-01.md` §3, lines 164-165; §18, line 1152  
**Argument:** The report treats the Apple health-app medical-device disclosure story as evidence of regulatory tightening around clinical drift. The source checked is an MDDI trade-press article about Apple App Store disclosure requirements for health apps by 2027, not a regulator mandating clinical-device classification. The local no-clinical-claims boundary is already strongly supported by AGENTS.md and non-goals; this external source should not carry more weight than it has.  
**Recommended response:** Reword this as an App Store policy/compliance signal, not a regulatory action. Keep the “no clinical claims” recommendation anchored to local settled decisions and formal non-goals.

### F-RES-09. Garmin MCP landscape quantification is unsupported

**Q-bucket:** Q8  
**Severity:** external-source-failure / over-claim  
**Reference:** `strategic_research_2026-05-01.md` §15 D-5, lines 1038-1042; §18, line 1157  
**Argument:** The report claims “8+ Garmin community MCPs” and says they are all built on `python-garminconnect`. The appendix does not provide a sourced table or citations sufficient for that count or the “all” claim. A few Garmin MCP projects are readily discoverable, but the quantified claim is not currently audit-grade. The recommendation not to default to Garmin Connect does not need this overclaim; AGENTS.md already says Garmin Connect is not the default live source because login is rate-limited and unreliable (`AGENTS.md:130-131`).  
**Recommended response:** Remove “8+” and “all,” or add a sourced mini-table with project, source, adapter dependency, and last activity. Keep the strategic conclusion anchored to the settled Garmin decision.

### F-RES-10. Research-audit precedent should remain ad hoc for now

**Q-bucket:** Q10 / Q7  
**Severity:** precedent-risk  
**Reference:** absent from `strategic_research_2026-05-01.md`  
**Argument:** This audit placement is useful, but the project should not automatically promote it to D16 yet. D11, D14, and D15 became settled patterns after repeated cycle evidence. This is the first research-artifact audit, and the risk register already warns about cycle pattern collapse (`reporting/plans/risks_and_open_questions.md:339-356`) and releases becoming prose-heavy (`reporting/plans/risks_and_open_questions.md:403-420`). Making every strategic research memo pass through a full audit would increase single-maintainer load without an empirical settling shape.  
**Recommended response:** Treat this as an ad hoc hardening audit for a high-impact post-v0.1.13 artifact. Do not add a D16 rule unless at least one more research-audit round catches blocking findings that would otherwise have reached PLAN.md.

## Open questions for maintainer

1. Should the next reconciliation accept CP5 single-release v0.2.0 despite reconciliation C6, or should W53/W58J move to v0.2.1 while W52/W58D stay in v0.2.0?
2. Is v0.1.14 allowed to rescope W-AH, W-AJ, W-AM, and W-AN, or must the report’s added P0s be additive to the full tactical-plan baseline?
3. Should P0 status require “blocks second-user trust before any external user tries the package,” or can doc-only public-surface alignment be P0 when the risk is already covered elsewhere?
4. Should this research-audit pattern remain one-off, or should a lightweight “strategic research hardening” tier be added after evidence from another cycle?
