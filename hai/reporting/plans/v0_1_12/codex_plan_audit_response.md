# Codex Plan Audit Response — v0.1.12 PLAN.md

**Verdict:** PLAN_COHERENT_WITH_REVISIONS

**Round:** 1

**Scope note:** I treated `reporting/plans/v0_1_12/codex_plan_audit_prompt.md`
as the controlling prompt for this audit. I did not run tests because Step 7
explicitly says "No test runs"; where Q3 asked for test execution, I used the
v0.1.11 release proof and on-disk inspection instead.

## Findings

### F-PLAN-01. CP5 contradicts the PLAN's own v0.2.x sequence

**Q-bucket:** Q6  
**Severity:** plan-incoherence  
**Reference:** PLAN.md §1.3 lines 87-90; PLAN.md §2.10 line 364  
**Argument:** The deferred-scope table says v0.2.0 contains W52 + evidence
cards + deterministic claim block, while W53 insight ledger and W58 LLM-judge
shadow mode land in v0.2.1 and W58 blocking lands in v0.2.2. CP5 then says
v0.2.0 equals W52 + W53 + W58 deterministic block + LLM-judge
shadow-by-default with a feature-flag flip to blocking. Those cannot both be
the adopted D1 shape. The reconciliation input also names a three-release split
where v0.2.0 has no LLM judge yet, v0.2.1 has W53 + judge shadow, and v0.2.2
has judge blocking (`reconciliation.md:69-75`). The PLAN status says Dom
adjudicated "substantial + LLM-judge-shadow-by-default" (`PLAN.md:11-13`), so
the document needs one canonical post-adjudication shape, not both.

**Recommended response:** Revise §1.3 and CP5 to a single D1 outcome. If Dom's
actual call is "substantial v0.2.0," then move W53 and judge shadow into the
v0.2.0 row and adjust v0.2.1/v0.2.2 accordingly. If the table is right, revise
CP5 to match it and remove "shadow-by-default" from v0.2.0.

### F-PLAN-02. W-AC and W-PRIV carry stale reconciliation premises as "confirmed on disk"

**Q-bucket:** Q8  
**Severity:** provenance-gap  
**Reference:** PLAN.md §2.1 lines 101-110; PLAN.md §2.7 lines 286-297  
**Argument:** W-AC says three concrete C1 instances were confirmed on disk.
`ROADMAP.md` is still stale (`ROADMAP.md:13` says v0.1.8 current), but the
other two cited examples no longer match the current tree. `HYPOTHESES.md`
now says the current working strategy lives in `strategic_plan_v1.md`
(`HYPOTHESES.md:8-12`), and `reporting/plans/README.md:95` is now just the
cold-session reading list while the file header says post-v0.1.11 ship
(`reporting/plans/README.md:3`, `:91-100`). W-PRIV similarly says chmod
failure semantics need a paragraph, but `reporting/docs/privacy.md:44-46`
already explains the warn-and-continue behavior. The `auth --remove` and
"forget one day" line refs still exist (`privacy.md:59-60`, `:116-120`).

**Recommended response:** Rebaseline W-AC/W-PRIV against the current tree.
Keep ROADMAP, README, AUDIT, privacy auth-removal, and privacy forgetability in
scope, but remove already-fixed or already-explained examples from the
"confirmed on disk" list.

### F-PLAN-03. CP1/CP2 strike text does not match the settled decision verbatim

**Q-bucket:** Q6  
**Severity:** settled-decision-conflict  
**Reference:** PLAN.md §2.10 lines 360-361; AGENTS.md lines 124-125 and 252-253  
**Argument:** CP1 says it will strike `Do not split cli.py`; CP2 says it will
strike `Do not freeze the capabilities manifest schema yet`. The actual settled
decision is a single combined bullet: "**W29 / W30 deferred.** Do not split
`cli.py`. Do not freeze the capabilities manifest schema yet." The Do Not Do
section also says "Do not split `cli.py` or freeze the capabilities manifest
schema in this cycle." Striking only the second sentence of the settled bullet
loses the W29/W30 deferral framing and does not specify whether the Do Not Do
cycle-scoped bullet also changes.

**Recommended response:** Each CP should quote the exact AGENTS.md text it
changes and provide the replacement D-entry and Do Not Do wording. Treat CP1
and CP2 as paired changes to D4 unless the proposal explicitly keeps them
separable.

### F-PLAN-04. W-CP approval is underspecified for proposals that reverse settled decisions

**Q-bucket:** Q5 / Q6 / Q7  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §2.10 lines 367-379; PLAN.md §5 line 442  
**Argument:** W-CP acceptance says all six proposals are authored, each lists
text deltas, and approval is implicit if the PLAN audit returns
PLAN_COHERENT and v0.1.12 ships. That makes "authored" the main falsifier for
proposals that reverse or extend settled decisions, and it gives no explicit
fallback if a CP is accepted-with-revisions or rejected. This matters because
§1.3 already schedules future work "per CP1/CP2/CP4/CP5/CP6" before the CPs
exist (`PLAN.md:82-93`), and the definition of done requires AGENTS.md,
strategic plan, and tactical plan updates per approved deltas (`PLAN.md:442`).

**Recommended response:** Add per-CP acceptance gates:
`accepted | accepted-with-revisions | rejected`, exact target files, exact
delta blocks, dependent future rows, and fallback if rejected. The PLAN audit
can inform approval, but "PLAN_COHERENT" should not silently approve every CP.

### F-PLAN-05. CP6 is both deferred and required at ship

**Q-bucket:** Q2 / Q6  
**Severity:** dependency-error  
**Reference:** PLAN.md §1.3 line 93; PLAN.md §2.10 lines 365 and 377-379;
PLAN.md §5 line 442  
**Argument:** The out-of-scope table defers the L3 strategic-plan §6.3 framing
edit to a v0.1.13 strategic-plan revision. But W-CP's CP6 row says the
strategic plan §6.3 is rephrased, W-CP acceptance says AGENTS.md and strategic
plan deltas are applied at v0.1.12 ship, and the definition of done requires
strategic and tactical plan updates per CP1-CP6 approved deltas. This leaves
CP6 in two states at once: authored-now/apply-at-ship and deferred-to-v0.1.13.

**Recommended response:** Choose one. If CP6 is a v0.1.12 governance doc only,
then §5 should require "CP6 authored with future delta recorded," not strategic
plan application. If the §6.3 edit applies at v0.1.12 ship, remove the
out-of-scope deferral row.

### F-PLAN-06. W-Vb clean-wheel failure is asserted more strongly than current code supports

**Q-bucket:** Q1 / Q8  
**Severity:** provenance-gap  
**Reference:** PLAN.md §2.3 lines 181-187; pyproject.toml lines 53-62;
cli.py lines 8530-8537; core/demo/session.py lines 226-230  
**Argument:** The packaging risk is real, but the stated current failure mode
is not verified by the tree. PLAN.md says a clean `pip install
health-agent-infra` followed by `hai demo start --persona p1` fails with
`ModuleNotFoundError` because `verification/dogfood` is not packaged. Current
CLI help says the persona flag is accepted for forward compatibility but no
fixture is loaded yet, and `open_session()` only records the persona slug. I
found no runtime import from `verification.dogfood` in `src/health_agent_infra`.
The package-data list also has no `demo/fixtures/**` entry, so the future
packaged-fixture path still needs packaging metadata once added.

**Recommended response:** Rewrite the premise: current behavior is "persona
accepted but unpopulated," not confirmed `ModuleNotFoundError`. Keep the
clean-wheel test, but make it prove both that package data is included and that
`--persona p1 --blank` reaches synthesis after W-Vb.

### F-PLAN-07. W-FBC picks option B while admitting its primitive may not exist

**Q-bucket:** Q1 / Q4 / Q5  
**Severity:** dependency-error  
**Reference:** PLAN.md §2.8 lines 312-330; PLAN.md §4 lines 422-426  
**Argument:** W-FBC chooses option B: only changed-input domains re-propose,
with `--re-propose-all` as an override. The risk register then says
per-domain input fingerprints may not exist for every domain at ship. Current
state fingerprinting is global over upstream state surfaces, proposal payloads,
and Phase A firings (`core/synthesis.py:423-455`); I did not find a shipped
per-domain fingerprint primitive. If option B depends on a primitive that may
not exist across all domains, the implementation can silently become option C
or a partial policy. The new `--re-propose-all` flag is also a CLI/capabilities
surface but is not named in the file list or ship gates.

**Recommended response:** Either make W-FBC a design-first workstream with the
policy decision as acceptance, or require per-domain fingerprint support for
all six domains before option B can ship. Name the three persona scenarios and
domains in acceptance, and add `cli.py`/capabilities updates for
`--re-propose-all` if that override is in scope.

### F-PLAN-08. The W-N warning gate has no coherent split/ship fallback

**Q-bucket:** Q3 / Q7  
**Severity:** dependency-error  
**Reference:** PLAN.md §2.5 lines 245-253; PLAN.md §3 line 390;
PLAN.md §4 lines 403-406; RELEASE_PROOF.md lines 59-61  
**Argument:** v0.1.11 release proof records 47 ResourceWarning failures, so
the 47 baseline is sourced. The v0.1.12 PLAN says if the audit finds >80
sites, split W-N-broader-2 to v0.1.13. But the ship gate still requires
`uv run pytest verification/tests -W error::Warning -q` to exit 0. If the
workstream splits, the PLAN does not say whether v0.1.12 can ship with a
narrower warning gate, whether the ship gate degrades, or whether the cycle
cannot ship. The proposed `test_resource_warning_gate.py` also appears to run
the full test suite from inside the test suite, which risks recursion or at
least doubling CI runtime unless it explicitly excludes itself.

**Recommended response:** Replace the nested test with a release/CI command
gate, or specify an exclusion-safe subprocess test. Add explicit fallback:
if >80 sites, v0.1.12 either keeps the full warning gate as blocker, narrows
the gate with named residual warnings, or defers the whole W-N-broader gate.

### F-PLAN-09. W-DOMAIN-SYNC's "8 registries enumerate six domains" premise is not exact

**Q-bucket:** Q8  
**Severity:** provenance-gap  
**Reference:** PLAN.md §1.3 line 84; reconciliation.md line 162;
synthesis_policy.py lines 65-86  
**Argument:** The reconciliation claim is useful but over-broad. Some named
tables are six-domain registries (`RECOMMENDATION_SCHEMA_BY_DOMAIN`,
`_ACCEPTED_STATE_TABLES`, `V1_EXPECTED_DOMAINS`,
`ALLOWED_ACTIONS_BY_DOMAIN`, `SCHEMA_VERSION_BY_DOMAIN`). Others are action
or override maps, not domain registries (`_DEFAULT_REVIEW_QUESTIONS`,
`_DOMAIN_REVIEW_QUESTION_OVERRIDES`). `_DOMAIN_ACTION_REGISTRY` currently
lists only recovery, running, and strength because those are the Phase A
hard-action domains. A future sync test that expects every registry to
enumerate all six domains would fail the intended shape or force meaningless
sleep/stress/nutrition entries.

**Recommended response:** Re-scope the deferred W-DOMAIN-SYNC row to "single
truth table plus expected subset registries." The contract should assert which
registries must be six-domain complete and which are intentionally sparse.

### F-PLAN-10. Phase 0 is named but not scoped

**Q-bucket:** Q7  
**Severity:** absence  
**Reference:** PLAN.md lines 20-23 and 436-439; AGENTS.md lines 135-138 and
191-202  
**Argument:** PLAN.md correctly says Phase 0 happens after D14 and that
`aborts-cycle` findings may end the cycle. It does not define the v0.1.12
Phase 0 bug-hunt shape. AGENTS.md D11 requires a structured hunt: internal
sweep, audit-chain probe, persona matrix, and Codex external audit, with
findings consolidated to `audit_findings.md`. v0.1.12 is governance-heavy and
trust-repair-oriented, so an unscoped Phase 0 is likely to expand after D14 or
miss the exact trust surfaces the cycle claims to repair.

**Recommended response:** Add a short Phase 0 outline before opening the cycle:
named probes, expected artifact (`audit_findings.md`), cycle-impact tags, and
what constitutes an abort/revise signal for W-Vb, W-FBC, W-N-broader, and
W-CP.

## Open questions for maintainer

1. **CP5:** Is Dom's D1 adjudication "single substantial v0.2.0 with W52,
   W53, deterministic claim block, and LLM judge shadow-by-default," or the
   three-release sequence currently in §1.3? The PLAN must choose one.
2. **CP3:** If CP3 is revised or rejected, should v0.1.12 still label itself
   "substantive" under the pre-existing D11/D14 language? I think yes, but the
   CP3 ship gate should have a fallback.
3. **W-PRIV:** Is `hai auth --remove` in v0.1.12 scope or not? The auth
   store already has `clear_garmin()` and `clear_intervals_icu()` helpers, but
   the CLI surface does not expose them. The PLAN should decide, not leave it
   optional.
4. **CP4:** The staged MCP plan is directionally sound, but official MCP docs
   make the threat-model gate non-optional: the authorization spec requires
   resource audience validation, and the security guide calls out
   confused-deputy, token-passthrough, and SSRF risks. Should CP4 explicitly
   require a least-privilege read-scope model before any read surface ships?
   Sources: <https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization>
   and <https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices>.

## CP1-CP6 quick verdicts

| CP | Verdict | Reason |
|---|---|---|
| CP1 | revise | Right direction, but strike text must quote the combined W29/W30 settled decision and Do Not Do delta exactly. |
| CP2 | revise | Same strike-text issue; also needs manifest-freeze downstream contract implications. |
| CP3 | accept-with-revision | Four tiers are fine, but v0.1.12 needs a fallback tier declaration if CP3 changes. |
| CP4 | accept-with-revision | Staged MCP is coherent; add explicit security/threat-model acceptance. |
| CP5 | revise | Internally contradictory v0.2.0/v0.2.1/v0.2.2 sequencing. |
| CP6 | revise | Decide whether §6.3 edit applies at v0.1.12 ship or is deferred to v0.1.13. |

## Verified During Audit

- Step 0 matched the expected tree: current directory
  `/Users/domcolligan/health_agent_infra`, branch
  `chore/reporting-folder-organisation`, recent log includes
  `release: v0.1.11`, and `reporting/plans/v0_1_12/` contains `PLAN.md`
  plus this prompt.
- L1 D13 asymmetry is accurate: recovery, running, sleep, and stress policy
  files read raw `t["policy"][...]`; strength and nutrition use
  `coerce_*` helpers.
- C4 line numbers partially still exist: privacy lines 59 and 116 are valid;
  chmod semantics are already documented at lines 44-46.
- C3 is a real packaging design concern, but the current observed failure mode
  should be restated as unimplemented persona loading rather than a confirmed
  clean-wheel `ModuleNotFoundError`.
