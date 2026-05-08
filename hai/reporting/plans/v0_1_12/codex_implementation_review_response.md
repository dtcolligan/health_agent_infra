# Codex Implementation Review — v0.1.12

**Verdict:** SHIP_WITH_FIXES
**Round:** 1

## Verification summary

- Tree state: `/Users/domcolligan/health_agent_infra`, branch `cycle/v0.1.12`, clean worktree after the benign prompt commit (`db798d9`); 11 commits unique to `main`.
- Test surface: `uv run pytest verification/tests -q` -> `2382 passed, 2 skipped`; targeted W-Vb demo fixture/session/isolation tests -> `25 passed`; targeted W-D13/W-FCC/W-PRIV/W-FBC-flag tests -> `14 passed`.
- Ship gates: `uvx mypy src/health_agent_infra` -> `Success: no issues found in 116 source files`; `uvx bandit -ll -r src/health_agent_infra` -> 0 Medium / 0 High / 46 Low; `hai capabilities --markdown` byte-stable and matches `reporting/docs/agent_cli_contract.md`; audit wheel contains `health_agent_infra/demo/fixtures/p1_dom_baseline.json`.
- Warning gates: narrow gate `uv run pytest verification/tests -W error::pytest.PytestUnraisableExceptionWarning -q` -> `2382 passed, 2 skipped`; broader audit `-W error::Warning` -> `48 failed, 2333 passed, 2 skipped, 1 error`, all sampled failures/errors are sqlite3 connection-lifecycle ResourceWarning / PytestUnraisableExceptionWarning sites, consistent with the W-N fork.
- Extra checks: CP4 MCP URLs resolve (authorization page and security best-practices redirect, not 404). `hai doctor` was read-only and returned overall WARN only because the maintainer's local real state DB has one pending migration; not treated as a release gate.

## Findings

### F-IR-01. W-FBC recovery prototype is claimed but absent

**Q-bucket:** Q10, Q13, Q14
**Severity:** scope-mismatch
**Reference:** `reporting/docs/supersede_domain_coverage.md:59`; `reporting/docs/supersede_domain_coverage.md:64`; `reporting/plans/v0_1_12/RELEASE_PROOF.md:22`; `src/health_agent_infra/cli.py:4868`; `src/health_agent_infra/cli.py:8125`; absent synthesis-side implementation

**Argument:** The shipped code only parses `hai daily --re-propose-all` and echoes `re_propose_all_requested` in the daily report. The only new tests are the three `test_cli_daily.py` flag/report/capabilities tests. I found no synthesis-side use of `re_propose_all`, no `recovery_proposal_carryover_under_re_propose_all` token, and no `verification/tests/test_supersede_domain_coverage.py`.

That contradicts the design doc, which says recovery "honors" the flag and that synthesis emits a recovery carryover token, and contradicts RELEASE_PROOF's W-FBC row claiming "Design doc + recovery prototype + `--re-propose-all` flag + 3 tests." The CLI help also tells users the flag has runtime effect on recovery today, which the implementation does not do.

**Recommended response:** fix-and-reland. Either implement the recovery prototype plus tests as documented, or revise PLAN/RELEASE_PROOF/CARRY_OVER/ROADMAP/tactical plan/CLI help/design doc to state the true v0.1.12 scope: design doc + flag accepted + report-surface field only, with all runtime enforcement deferred to v0.1.13 W-FBC-2.

### F-IR-02. W-Vb PLAN still requires full persona replay while the code ships skeleton-only fixtures

**Q-bucket:** Q4, Q11, Q13
**Severity:** scope-mismatch
**Reference:** `reporting/plans/v0_1_12/PLAN.md:234`; `reporting/plans/v0_1_12/PLAN.md:264`; `reporting/plans/v0_1_12/PLAN.md:280`; `reporting/plans/v0_1_12/PLAN.md:797`; `src/health_agent_infra/core/demo/fixtures.py:79`; `src/health_agent_infra/core/demo/session.py:289`

**Argument:** The implementation matches the intended partial closure in RELEASE_PROOF: `apply_fixture()` returns `applied: false`, `scope: skeleton-only`, and `deferred_to: v0.1.13`; `open_session()` records that marker. The audit wheel also ships `p1_dom_baseline.json`.

But the final PLAN still says W-Vb must pre-populate proposals, `hai daily` must reach synthesis, `hai today` must render a populated plan, and the demo regression ship gate requires clean-wheel end-to-end synthesis. Those claims are false for the shipped implementation and contradict RELEASE_PROOF's partial-closure framing. There is also a minor stale parser help string saying the persona flag is "accepted for forward-compat but no fixture is loaded yet" even though skeleton fixtures now load.

**Recommended response:** fix-and-reland the artifacts, not necessarily code. Rewrite the W-Vb PLAN acceptance/ship-gate text to the actual partial closure, or implement full persona replay before shipping. Update the `hai demo start --persona` help text to say the packaged skeleton fixture is loaded and proposal pre-population is v0.1.13.

### F-IR-03. v0.1.13 deferral propagation is incomplete for W-Vb and W-N-broader

**Q-bucket:** Q3, Q6, Q11, Q15
**Severity:** provenance-gap
**Reference:** `reporting/plans/v0_1_12/RELEASE_PROOF.md:209`; `reporting/plans/v0_1_12/RELEASE_PROOF.md:210`; `reporting/plans/tactical_plan_v0_1_x.md:318`; `reporting/plans/v0_1_12/CARRY_OVER.md:19`; `reporting/plans/v0_1_12/CARRY_OVER.md:21`; `reporting/plans/v0_1_12/CARRY_OVER.md:47`

**Argument:** RELEASE_PROOF correctly names W-Vb persona replay and W-N-broader as v0.1.13 deferrals. REPORT §8 also lists both. But tactical plan §4's v0.1.13 added-workstream table includes W-29-prep, W-FBC-2, W-LINT, W-AK, and CP6 application only; it omits W-Vb and W-N-broader. CARRY_OVER also remains stale: W-Vb is listed as "in-cycle" with "Demo persona-replay flow", and W-N says "49 + 1 error -> <= 80 branch -> full broader gate ships", even though the accepted fork is the opposite.

This fails the ship-time freshness checklist's "next-cycle row reflects the just-authored next-cycle PLAN" intent and the review prompt's Q6 requirement that W-N-broader be on v0.1.13.

**Recommended response:** fix-and-reland docs. Add v0.1.13 rows for W-Vb persona replay and W-N-broader to `tactical_plan_v0_1_x.md` §4, and update `CARRY_OVER.md` to mark W-Vb as partial and W-N-broader as fork-deferred, with destinations matching RELEASE_PROOF.

### F-IR-04. Accepted CP deltas are not byte-for-byte with their proposal docs

**Q-bucket:** Q1, Q12
**Severity:** provenance-gap
**Reference:** `reporting/plans/v0_1_12/cycle_proposals/CP1.md:51`; `AGENTS.md:124`; `reporting/plans/v0_1_12/cycle_proposals/CP3.md:38`; `AGENTS.md:190`

**Argument:** The CP application is semantically coherent, but the strict "byte-for-byte" gate in the prompt does not hold. CP1/CP2's proposed AGENTS replacement does not include the origin parenthetical now present in AGENTS. CP3's proposed D15 block differs materially in wording from AGENTS: backticks around `PLAN_COHERENT`, shortened RELEASE_PROOF wording, and appended origin text.

This is not a runtime defect, and the differences are reasonable editorial/provenance additions, but the cycle says accepted CPs apply exact replacement text. If the gate is literal, the artifact pair is out of sync.

**Recommended response:** accept-as-known if origin parentheticals are intentionally allowed, but update CP docs or RELEASE_PROOF to say "accepted with editorial provenance additions." Otherwise revise AGENTS.md to match the CP replacement blocks exactly.

### F-IR-05. Doc freshness test only covers one narrow ROADMAP pattern

**Q-bucket:** Q2
**Severity:** acceptance-weak
**Reference:** `verification/tests/test_doc_freshness_assertions.py:42`; `verification/tests/test_doc_freshness_assertions.py:47`

**Argument:** PLAN §2.1 says the new test scans docs for version-tag drift against the package version and fails on any doc that names an older version as current. The test currently scans only `ROADMAP.md`, and only the exact bold pattern `**vX.Y.Z current.**`. It would catch the historical `ROADMAP.md` failure, but not stale current-version claims in README/AUDIT/planning docs, nor non-bold ROADMAP variants.

This is not blocking if the intended contract is "mechanise only the known offender and rely on the human checklist for the rest"; AGENTS.md now says that. It is weaker than PLAN's acceptance wording.

**Recommended response:** either broaden the test patterns to the named public docs, or revise PLAN/RELEASE_PROOF language to describe the intentionally narrow guard.

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-CP | notes | CP docs are semantically applied, but not byte-for-byte under a literal reading. CP6 is correctly authored-but-not-applied. |
| W-AC | notes | Freshness sweep mostly lands; the automated freshness test is narrower than PLAN wording, and tactical-plan freshness misses W-Vb/W-N carryover. |
| W-CARRY | fixes | v0.1.11 named-defer rows exist, but W-Vb and W-N status text is stale versus the shipped partial/fork state. |
| W-Vb | fixes (partial) | Packaging path and skeleton loader ship correctly; PLAN/demo gate still claims full persona replay. |
| W-H2 | ship | Mypy 22 -> 0 verified; only two new targeted `type: ignore` imports for known third-party typing gaps. |
| W-N-broader | fixes (fork-deferred) | Fork decision is honest and broader audit reproduces sqlite leaks; v0.1.13 tactical propagation is missing. |
| W-D13-SYM | ship | Four policy domains now route leaf reads through coercers; AST contract covers six domains and fails on seventh-domain drift. |
| W-PRIV | ship | `hai auth remove` subcommand calls existing keyring clear helpers; env creds untouched; capabilities row present. |
| W-FCC | ship | Constant, manifest enum surface, `hai today --verbose`, and contract tests all line up. |
| W-FBC | fixes (partial) | Flag/report plumbing ships; claimed recovery prototype and persona-style scenario tests are absent. |

## Open questions for maintainer

1. Was W-FBC intentionally reduced to "flag accepted + report field only" during implementation? If yes, the fastest fix is artifact correction and explicit v0.1.13 carryover. If no, the recovery prototype still needs to land before release.
2. Should CP proposal docs be treated as exact applied patches, or are origin/provenance parentheticals allowed? The answer should be recorded because Q1's byte-for-byte gate is otherwise ambiguous.
3. Should the v0.1.12 PLAN remain as the original ambitious contract with RELEASE_PROOF documenting partial closures, or should PLAN be patched at ship time to match accepted partial/fork outcomes? The W-Vb mismatch is the practical case to settle.
