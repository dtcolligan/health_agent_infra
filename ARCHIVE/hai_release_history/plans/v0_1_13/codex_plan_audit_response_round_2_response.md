# Codex Plan Audit Response — v0.1.13 PLAN.md

**Verdict:** PLAN_COHERENT_WITH_REVISIONS (revise the stale opening summary, W-Vb fork-defer surfaces, W-CARRY acceptance wording, W-AD path provenance, W-AE cause-class wording, W-LINT exception allowlist, and risk-cut effort math before Phase 0 opens)

**Round:** 2

## Findings

### F-PLAN-R2-01. Opening summary still describes the round-1 plan, not the revised round-2 artifact

**Q-bucket:** Q8  
**Severity:** provenance-gap  
**Reference:** PLAN.md opening block, lines 3-12 and 41-43; PLAN.md §1.2, lines 117-126  
**Argument:** The PLAN header still says the D14 chain is "not yet opened" and "this is the round-1 input" (lines 3-6), and its tier rationale still says "16 workstreams" (line 9). The same file now says total scope is 17 workstreams and 22.5-32.5 days (lines 119-126). The branch note also still says the "First commit" cherry-picked from `hotfix/v0.1.12.1` is the W-CF-UA fix (lines 41-43), while §1.2.D now correctly records both inherited commits: code+test diff `636f5d3` and RELEASE_PROOF doc `a10a238` (line 117). This is a summary-surface drift introduced by round-1 revisions.  
**Recommended response:** Update the top status/rationale/branch block for round 2: D14 opened, round-1 response applied, 17 workstreams, 22.5-32.5 days, and two hotfix-derived commits in the cycle branch.

### F-PLAN-R2-02. W-Vb-3 fork-defer names only three residual personas, but six more personas are also outside the ship set

**Q-bucket:** Q7  
**Severity:** plan-incoherence  
**Reference:** PLAN.md §1.3, line 132; PLAN.md §2.A W-Vb, lines 186-187 and 203-217; PLAN.md §3, line 620; CARRY_OVER.md §4, line 61; verification/dogfood/personas/__init__.py, lines 20-37  
**Argument:** The revised W-Vb ship set is P1+P4+P5 (PLAN lines 186-187, 203-210, and ship gate line 620). The deferral row says W-Vb-3 covers "P9/P11/P12 (the three personas not in v0.1.13's P1/P4/P5 ship-set)" (PLAN line 132), and CARRY_OVER repeats only P9/P11/P12 (line 61). But the persona matrix registers 12 personas: P1 through P12 (personas/__init__.py lines 20-37). If P1/P4/P5 are in-cycle, the non-ship-set residual is P2/P3/P6/P7/P8/P9/P10/P11/P12, not just P9/P11/P12. Also, W-Vb acceptance uses placeholder commands `p4_<slug>` and `p5_<slug>` (PLAN lines 205-208) even though the concrete current slugs are `p4_strength_only_cutter` and `p5_female_multisport` (personas/__init__.py lines 23-24).  
**Recommended response:** Either define W-Vb's universe as a six-persona demo-fixture subset and explain why P2/P3/P6/P7/P8/P10 are out of scope, or revise W-Vb-3 to defer all nine non-ship personas. Replace placeholder acceptance commands with concrete slugs.

### F-PLAN-R2-03. W-CARRY acceptance check still points every reconciliation item to §2, despite §4 owning later-cycle pass-through rows

**Q-bucket:** Q8  
**Severity:** provenance-gap  
**Reference:** CARRY_OVER.md §2, lines 26-35; CARRY_OVER.md §4, lines 55-69; CARRY_OVER.md acceptance check, lines 119-124; v0.1.12 CARRY_OVER.md §3, lines 47-59  
**Argument:** The source table in v0.1.12 CARRY_OVER §3 has v0.1.13 rows plus later-cycle pass-through rows (W-29, L2, A12, A2/W-AL, W-30, MCP plan/read-surface, W52/W53/W58) at lines 47-59. The revised v0.1.13 CARRY_OVER correctly places in-cycle rows in §2 and later-cycle rows in §4. But the acceptance check still says every reconciliation §6 v0.1.13+ item from the source has a row in "§2 above" (lines 123-124). That remains false for the rows intentionally handled in §4.  
**Recommended response:** Change the acceptance check to require disposition in §2 or §4, or rename §2 to "in-cycle reconciliation items" and make §4 part of the same acceptance condition.

### F-PLAN-R2-04. F-PLAN-04 path-prefix sweep missed W-AD's `cli.py` references

**Q-bucket:** Q8  
**Severity:** provenance-gap  
**Reference:** PLAN.md §1.2.B W-AD row, line 98; PLAN.md §2.B W-AD, lines 390-397  
**Argument:** The round-1 response says runtime paths were prefixed with `src/health_agent_infra/`. Most were, but W-AD still cites `cli.py` in the catalogue row and contract section (lines 98, 390, 396). The actual path is `src/health_agent_infra/cli.py`, as used elsewhere in the revised PLAN. This is exactly the path-prefix completeness risk the round-1 response asked round 2 to grep for.  
**Recommended response:** Replace the remaining W-AD `cli.py` references with `src/health_agent_infra/cli.py`.

### F-PLAN-R2-05. W-AE says "four cause classes" but lists five outcomes

**Q-bucket:** Q5  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §2.B W-AE, lines 422-428; reporting/docs/intervals_icu_403_triage.md, lines 127-141; maintainer response lines 224-226  
**Argument:** PLAN.md says `hai doctor --deep` classifies intervals.icu responses into "one of the four cause classes" (lines 422-425), then lists `OK`, `CAUSE_1_CLOUDFLARE_UA`, `CAUSE_2_CREDS`, `NETWORK`, and `OTHER` (lines 427-428): five outcomes. The new triage doc also lists the same five outcomes at lines 127-141. The maintainer response introduced the same mismatch when it said "four cause classes" and then listed five labels.  
**Recommended response:** Decide whether the contract is "five outcomes" or "four failure classes plus OK", then update PLAN.md, the maintainer response convention if copied forward, and the triage doc wording consistently.

### F-PLAN-R2-06. W-LINT exception allowlist names a non-existent `research` skill

**Q-bucket:** Q8  
**Severity:** provenance-gap  
**Reference:** PLAN.md §2.C W-LINT, lines 526-534; absent `src/health_agent_infra/skills/research/SKILL.md`; existing `src/health_agent_infra/core/research/` package  
**Argument:** W-LINT says the emitting skill must be in a hard-coded allowlist, initially `research` and `expert-explainer` (lines 526-529). There is an `expert-explainer` packaged skill, but no packaged `research` skill under `src/health_agent_infra/skills/`. There is a code-owned `src/health_agent_infra/core/research/` registry and `hai research` CLI surface, but the same W-LINT section says CLI rendering paths never get the exception (line 529). So one allowlist entry is either a wrong skill name or a contradictory reference to a CLI/core surface.  
**Recommended response:** Replace `research` with the actual packaged skill name intended to receive the exception, or explicitly define a non-skill research-source exception while preserving the "CLI never gets the exception" rule.

### F-PLAN-R2-07. Risk-cut effort range does not match the named cuts

**Q-bucket:** Q9  
**Severity:** sizing-mistake  
**Reference:** PLAN.md §1.2 effort rows, lines 97, 100, 109, and 125; PLAN.md §4, line 643; PLAN.md §5, lines 649-655  
**Argument:** Total effort is now 22.5-32.5 days (lines 125 and 649-652). The named cuts are W-AC (1-2d, line 97), W-AF (1d, line 100), and W-AK (1d, line 109), and the risks register correctly says cutting W-AC + W-AF first saves 2-3d and cutting W-AK second saves 1d (line 643), for 3-4d total. But §5 says the same cuts drop effort to 18.5-25.5d (lines 654-655), which implies 4-7d of savings. If only those three W-ids are cut, the resulting range is 19.5-28.5d.  
**Recommended response:** Recalculate §5 from the named cuts, or name the additional cuts needed to reach 18.5-25.5d.

## Open questions for maintainer

1. Is W-Vb's intended long-term demo-fixture universe all 12 personas, or only the P1/P4/P5/P9/P11/P12 subset?
2. Should W-LINT's exception allowlist contain only packaged skill names, or can it reference code-owned research surfaces too?
