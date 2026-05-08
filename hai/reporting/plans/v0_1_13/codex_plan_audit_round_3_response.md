# Codex Plan Audit Response — v0.1.13 PLAN.md

**Verdict:** PLAN_COHERENT_WITH_REVISIONS

**Round:** 3

## Findings

### F-PLAN-R3-01. W-Vb catalogue row still defers only P9/P11/P12

**Q-bucket:** Q8  
**Severity:** provenance-gap  
**Reference:** PLAN.md §1.2.A W-Vb row, line 92; PLAN.md §1.3, line 138; PLAN.md §2.A W-Vb, lines 193-196 and 224-226; PLAN.md §3, line 641; PLAN.md §4, line 658; CARRY_OVER.md §4, line 61  
**Argument:** Round 2 revised the W-Vb residual to the 9 non-ship-set personas (P2/P3/P6/P7/P8/P9/P10/P11/P12), and that enumeration is now consistent in PLAN §1.3, §2.A acceptance, §3 ship gate, §4 risk row, and CARRY_OVER §4. The top catalogue row still says only "P9/P11/P12 fork-deferred to v0.1.14 W-Vb-3" at line 92. That leaves the primary summary surface with the pre-round-2 residual shape.  
**Recommended response:** Revise the W-Vb §1.2 catalogue row to say the 9 non-ship-set personas (P2/P3/P6/P7/P8/P9/P10/P11/P12) are fork-deferred to v0.1.14 W-Vb-3.

### F-PLAN-R3-02. CARRY_OVER §1 still presents W-Vb as full in-cycle closure

**Q-bucket:** Q8  
**Severity:** provenance-gap  
**Reference:** CARRY_OVER.md §1, line 21; PLAN.md §1.3, line 138; PLAN.md §2.A W-Vb acceptance, lines 224-226; CARRY_OVER.md §4, line 61  
**Argument:** CARRY_OVER §1 maps the inherited W-Vb deferral to an in-cycle W-Vb row and says the cycle "authors full-shape persona DomainProposal seeds + clean-wheel build-install-subprocess test." It does not name the narrowed P1+P4+P5 ship set or point to the 9-persona W-Vb-3 residual in §4. Because CARRY_OVER §1 is the named-defer disposition surface, a reader can still read the inherited W-Vb item as full all-persona closure despite PLAN §1.3/§2.A and CARRY_OVER §4 saying v0.1.13 closes 3 of 12.  
**Recommended response:** Amend the CARRY_OVER §1 W-Vb notes to state "P1+P4+P5 in-cycle; P2/P3/P6/P7/P8/P9/P10/P11/P12 fork-deferred to v0.1.14 W-Vb-3 in §4."

### F-PLAN-R3-03. W-FBC-2 reconciliation provenance is split and the F-PLAN-R2-04 token is ambiguous

**Q-bucket:** Q8  
**Severity:** nit  
**Reference:** PLAN.md source block, lines 36-38; reporting/plans/v0_1_12/CARRY_OVER.md §3, line 59; CARRY_OVER.md §2, line 35; codex_plan_audit_response_round_2_response.md, lines 33-39  
**Argument:** PLAN.md says the v0.1.12 CARRY_OVER §3 reconciliation named-defers are A1+C7, A5/W-AK, C2/W-LINT, W-29-prep, and CP6 application, but the source table also contains W-FBC-2 at v0.1.12 CARRY_OVER line 59. The companion CARRY_OVER does account for W-FBC-2 at line 35, but it preserves the quoted source text "new W-id introduced by Codex F-PLAN-R2-04 in this cycle." In the current v0.1.13 D14 chain, F-PLAN-R2-04 is a different finding: the W-AD `cli.py` path-prefix miss. The bare token is therefore easy to misresolve when auditing this cycle's F-PLAN-R2 citations.  
**Recommended response:** Either include W-FBC-2 in the PLAN source-block list for v0.1.12 CARRY_OVER §3, or label that list as additional non-duplicate reconciliation rows. In CARRY_OVER line 35, qualify the quoted token as "v0.1.12 Codex F-PLAN-R2-04" or remove the bare finding ID from the quote.

## Open questions for maintainer

None.
