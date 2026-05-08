# Codex Plan Audit Response — v0.1.13 PLAN.md

**Verdict:** PLAN_COHERENT_WITH_REVISIONS (revise the catalogue/count surfaces, W-CARRY register, W-Vb fixture/acceptance contract, W-FBC-2 option gate, provenance paths, W-AA/W-AE/W-LINT acceptance gates, and W-29-prep boundary-test wording before Phase 0 opens)

**Round:** 1

## Findings

### F-PLAN-01. Catalogue count excludes an in-catalogue workstream

**Q-bucket:** Q8  
**Severity:** plan-incoherence  
**Reference:** PLAN.md §1.2, lines 103-120; PLAN.md §2.C, lines 479-488  
**Argument:** PLAN.md says total scope is "16 workstreams — 4 inherited, 7 originally planned, 4 added-this-cycle, 1 pre-cycle ship" at lines 119-120. But §1.2.C lists five added-this-cycle rows: W-29-prep, W-LINT, W-AK, W-A1C7, and W-CARRY (lines 107-111), and §2.C gives W-CARRY its own per-workstream contract (lines 479-488). Counted literally, the catalogue is 17 rows: 4 inherited + 7 originally planned + 5 added + 1 pre-cycle ship. This also makes the effort roll-up fuzzy: the listed rows sum to about 22.25-33.25 days if W-CARRY's 0.5d is included, while the plan claims 22-32 days at lines 122-123 and 529-530.  
**Recommended response:** Decide whether W-CARRY is a real workstream. If yes, change the headline to 17 workstreams and update the effort range. If no, move W-CARRY out of §1.2.C/§2.C and treat CARRY_OVER.md as already-authored cycle scaffolding.

### F-PLAN-02. CARRY_OVER §2 misses two source rows it claims to dispose

**Q-bucket:** Q8  
**Severity:** provenance-gap  
**Reference:** CARRY_OVER.md §2, lines 26-34; CARRY_OVER.md acceptance check, lines 115-118; v0.1.12 CARRY_OVER.md §3, lines 47-59  
**Argument:** v0.1.13 CARRY_OVER.md says every reconciliation §6 v0.1.13+ item from v0.1.12 CARRY_OVER §3 has a row in §2 (lines 117-118). The source table has six v0.1.13 or v0.1.13-strategic-plan rows: A1+C7, A5/W-AK, C2/W-LINT, W-29-prep, L3 §6.3 strategic-plan framing edit, and W-FBC-2 (v0.1.12 CARRY_OVER lines 47-59). New §2 contains only the first four (lines 30-33). CP6/L3 and W-FBC-2 are accounted for in §1 because they also appear in RELEASE_PROOF §5, but the register's own §2 acceptance claim is false as written.  
**Recommended response:** Either add CP6/L3 and W-FBC-2 rows to CARRY_OVER §2 with "also covered by §1" notes, or revise the acceptance check to say duplicate source rows may be disposed once in §1 when RELEASE_PROOF §5 already owns them.

### F-PLAN-03. Hotfix RELEASE_PROOF path is broken in the audited tree

**Q-bucket:** Q10  
**Severity:** provenance-gap  
**Reference:** PLAN.md §1.2.D, line 117; CARRY_OVER.md §5, line 72  
**Argument:** PLAN.md and CARRY_OVER.md cite `reporting/plans/v0_1_12_1/RELEASE_PROOF.md` as an in-tree lightweight RELEASE_PROOF. In the current `cycle/v0.1.13` tree, `find reporting/plans -maxdepth 2 -type f -name RELEASE_PROOF.md` shows no `v0_1_12_1` artifact. The file exists only on `hotfix/v0.1.12.1` (`git ls-tree -r --name-only hotfix/v0.1.12.1 reporting/plans` includes it). Since the audit prompt requires current-tree cross-reference checking, the PLAN currently contains a broken path.  
**Recommended response:** Either cherry-pick the hotfix RELEASE_PROOF docs commit into the cycle branch, or change the citation to a branch-qualified reference and explicitly state that the artifact is not present in the cycle tree.

### F-PLAN-04. Runtime file paths omit the package prefix and do not exist literally

**Q-bucket:** Q8  
**Severity:** provenance-gap  
**Reference:** PLAN.md §1.2.A, lines 87-88; PLAN.md §2.A W-N-broader, lines 206-217; PLAN.md §2.A W-FBC-2, lines 260-266  
**Argument:** The PLAN lists runtime paths such as `core/state/store.py`, `core/explain/queries.py`, `core/synthesis.py`, `domains/<d>/policy.py`, `evals/runner.py`, and `cli.py`. Those paths do not exist at repo root. The actual paths are under `src/health_agent_infra/`, for example `src/health_agent_infra/core/state/store.py`, `src/health_agent_infra/core/synthesis.py`, `src/health_agent_infra/evals/runner.py`, and `src/health_agent_infra/cli.py`. The W-N-broader section also says the list is "per v0.1.12 audit_findings.md" (line 206), but v0.1.12 audit_findings.md lines 60-65 records the 49+1 leak count across many CLI paths, not this concrete file list.  
**Recommended response:** Replace shorthand paths with literal repo paths, and either cite the actual source of the W-N-broader file inventory or reframe the list as an initial search surface to validate during Phase 0.

### F-PLAN-05. W-Vb fixture path plan conflicts with the shipped loader contract

**Q-bucket:** Q8  
**Severity:** dependency-error  
**Reference:** PLAN.md §1.2.A, line 86; PLAN.md §2.A W-Vb, lines 173-176; src/health_agent_infra/core/demo/fixtures.py, lines 29-52; pyproject.toml, lines 53-62  
**Argument:** PLAN.md points at `src/health_agent_infra/demo/fixtures/p*/` and per-persona directories such as `p1_dom_baseline/`, `p4_*`, and `p5_*`. The current loader expects one JSON file at `health_agent_infra/demo/fixtures/<slug>.json` (fixtures.py lines 29-52), and package data includes `demo/fixtures/*.json` only (pyproject.toml lines 53-62). The current tree contains `src/health_agent_infra/demo/fixtures/p1_dom_baseline.json`, not a per-persona directory. If v0.1.13 intends to move to directory-shaped fixtures, that is a loader/package-data migration and should be named.  
**Recommended response:** Either keep the `.json` fixture layout in W-Vb, or add an explicit loader + package-data migration subtask with acceptance tests for both editable and wheel installs.

### F-PLAN-06. W-Vb acceptance is P1-only while the catalogue claims persona replay per persona

**Q-bucket:** Q7  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §1.2.A, line 86; PLAN.md §2.A W-Vb, lines 173-180 and 189-197; PLAN.md §3, line 503; verification/dogfood/personas/__init__.py, lines 11-14 and 34-37  
**Argument:** The W-Vb catalogue row says "DomainProposal seeds across all 6 domains per persona" (line 86). The detailed contract narrows this to "start with P1, P4, P5; expand if budget allows" (lines 173-176), and the acceptance/ship gate only require `p1_dom_baseline` (lines 191-193 and 503). The persona harness has 12 personas registered (personas/__init__.py lines 34-37). This is the exact partial-closure drift shape AGENTS.md warns about: a full-scope summary row, a budget-conditional middle section, and a P1-only ship gate.  
**Recommended response:** Define the minimum ship set explicitly. If P1-only is acceptable, rename the workstream as partial W-Vb closure and defer all-persona replay. If full closure is required, make the acceptance and ship gate cover the named persona set.

### F-PLAN-07. W-FBC-2 reopens option C despite the design doc saying it is not v0.1.x scope

**Q-bucket:** Q6  
**Severity:** settled-decision-conflict  
**Reference:** PLAN.md §2.A W-FBC-2, lines 255-258; PLAN.md §4, line 519; reporting/docs/supersede_domain_coverage.md, lines 32-50 and 97-101  
**Argument:** PLAN.md says the per-domain fingerprint primitive ships "if option B or C is chosen at design" (lines 255-258), and the risks register frames "option A vs B vs C" as a deferred design choice (line 519). The design doc already names the default decision as option A (supersede means all domains re-propose) at lines 32-38. It says option B requires per-domain fingerprints and may be chosen at W-FBC-2 design (lines 42-47 and 99-101), but option C requires schema work and is "Not in scope for v0.1.x" (lines 49-50).  
**Recommended response:** Revise W-FBC-2 to treat option A as the default, option B as the only possible design fork if explicitly selected, and option C as out of v0.1.13 scope unless a new cycle proposal reopens it.

### F-PLAN-08. W-AA wall-clock SLO is not measurable as written

**Q-bucket:** Q5  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §2.B W-AA, lines 307-316; PLAN.md §4, line 521; PLAN.md §3, line 504  
**Argument:** W-AA acceptance requires a fresh user to run `pipx install health-agent-infra && hai init` and reach a `synthesized` daily plan in under 5 minutes (lines 309-311), and the ship gate repeats the same SLO (line 504). The only named test stubs prompt input (lines 314-316), so it does not measure install time, hardware, network, keyring prompts, or intervals.icu latency. The risk register then says that if intervals.icu is slow, the UX should surface "still pulling" rather than fail the SLO (line 521), which contradicts the requirement to reach a synthesized plan within the SLO.  
**Recommended response:** Split this into a deterministic testable acceptance gate and an operator demo SLO. Define cache state, hardware/network assumptions, live-vs-stubbed intervals.icu behavior, and whether "still pulling" is an allowed degraded state or an SLO failure.

### F-PLAN-09. W-LINT exception path lacks a non-loophole acceptance gate

**Q-bucket:** Q7  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §2.C W-LINT, lines 435-441; PLAN.md §3, line 506; PLAN.md §4, line 520  
**Argument:** W-LINT allows a documented exception class for research/expert-explainer content quoting regulated terms with provenance citations (lines 439-441), and the risks register relies on that exception path (line 520). But the ship gate only says `test_regulated_claim_lint` is green and there are 0 packaged-skill violations (line 506). Nothing requires a negative test proving exceptions are allowlisted, citation-bound, and unavailable to ordinary skill/CLI prose. Without that, the exception can become a broad bypass of the no-clinical-claims invariant.  
**Recommended response:** Add acceptance criteria and tests for the exception path: allowlisted surface only, citation required, quoted-term context only, and ordinary user-facing prose still blocked.

### F-PLAN-10. W-AE depends on a triage script that is not in the repo

**Q-bucket:** Q8  
**Severity:** provenance-gap  
**Reference:** PLAN.md §2.B W-AE, lines 372-375  
**Argument:** W-AE acceptance says `hai doctor --deep` surfaces error classes "per the triage script in `reference_doctor_intervals_icu_false_positive.md`" (lines 372-375). `find . -name 'reference_doctor_intervals_icu_false_positive.md'` finds no such file in the repo. The hotfix RELEASE_PROOF on `hotfix/v0.1.12.1` describes this as a `~/.claude/.../memory/` note, not a versioned project artifact. That makes W-AE acceptance depend on private, non-repo context, violating the prompt's fresh-session/no-assumed-context rule.  
**Recommended response:** Move the triage script/spec into the repo, likely under `reporting/docs/` or `verification/fixtures/`, and cite that path from W-AE.

### F-PLAN-11. W-29-prep boundary scope is stale and underspecified against planned CLI changes

**Q-bucket:** Q4  
**Severity:** hidden-coupling  
**Reference:** PLAN.md §2.C W-29-prep, lines 407-415; PLAN.md §2.B W-AB, lines 318-325; PLAN.md §3, line 501; src/health_agent_infra/cli.py, lines 6511-6521 and 8625-8647; src/health_agent_infra/evals/cli.py, lines 84-90  
**Argument:** W-29-prep acceptance says the boundary table covers "all 22 subcommands" (line 414). The current parser has 24 top-level `sub.add_parser(...)` registrations in `cli.py` and also registers `hai eval` through `src/health_agent_infra/evals/cli.py` lines 84-90, so 22 is already stale before implementation. The same workstream requires byte-equality on `hai capabilities --json` (lines 407-409 and ship gate line 501), while W-AB adds a new `hai capabilities --human` mode (lines 318-325). The current capabilities parser has only `--markdown` and `--json` flags (cli.py lines 8625-8647), so W-AB is a legitimate CLI/capabilities surface change that could make an unscoped byte-equality assertion fail for the wrong reason.  
**Recommended response:** Make W-29-prep derive command count from the parser/capabilities manifest, and define the byte-stability baseline as "stable after intentional v0.1.13 surface changes" rather than "unchanged from pre-cycle." Add a sequencing note that W-AB/W-AE surface changes land before the W-29-prep snapshot is frozen.

## Open questions for maintainer

1. Should W-CARRY be counted as a v0.1.13 workstream, or treated as cycle scaffolding already created at PLAN open?
2. Is W-Vb expected to ship full replay for all 12 personas, the P1/P4/P5 subset, or P1 only?
3. For W-FBC-2, is option B genuinely still on the table, or should v0.1.13 implement the already-documented option-A default only?
4. Should the v0.1.12.1 RELEASE_PROOF be cherry-picked into `cycle/v0.1.13`, or should v0.1.13 cite the hotfix branch/tag as an external artifact?
