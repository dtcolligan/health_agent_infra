# Codex Implementation Review - v0.1.13

**Verdict:** SHIP_WITH_FIXES
**Round:** 1

## Verification summary

- Tree state: started clean on `cycle/v0.1.13`; `git status --short`
  was empty. The branch is 16 commits ahead of `main`; the prompt's
  15-commit list excludes the `bdc4396` implementation-review prompt
  commit.
- Orientation read: `AGENTS.md`,
  `reporting/plans/v0_1_13/codex_implementation_review_prompt.md`,
  `PLAN.md`, `audit_findings.md`, `CARRY_OVER.md`, and the changed
  source/test/doc surfaces behind the 17 W-ids.
- Test surface:
  - `uv run pytest verification/tests -q`: 2486 passed, 3 skipped.
  - `uv run pytest verification/tests -W error::Warning -q`: 2486
    passed, 3 skipped.
  - `uv run pytest verification/tests/test_demo_persona_replay_end_to_end.py -q`:
    6 passed.
  - Targeted W-AA / W-AK / W-AG / W-LINT tests: 33 passed.
  - `uv run pytest verification/tests/test_cli_parser_capabilities_regression.py -q`:
    5 passed.
- Static gates:
  - `uvx mypy src/health_agent_infra`: no issues found in 120 source files.
  - `uvx ruff check src/health_agent_infra`: all checks passed.
  - `uvx bandit -ll -r src/health_agent_infra`: exit 0, no medium/high
    issues identified.
- Ship gates:
  - `uv run python -m verification.dogfood.runner /tmp/persona_run_ir_round1_sequential`:
    12 personas, 0 findings, 0 crashes.
  - `uv run hai capabilities --json`: exit 0 after rerun with cache
    access outside the sandbox. The sandboxed pipe attempt failed on
    uv cache permissions, not repo behavior.

## Findings

### F-IR-01. W-AG ships established-streak prose at 7 days, not the planned day-30 threshold

**Q-bucket:** Q6
**Severity:** scope-mismatch
**Reference:** `45319da`; `reporting/plans/v0_1_13/PLAN.md:111`;
`reporting/plans/v0_1_13/PLAN.md:459`;
`reporting/plans/v0_1_13/codex_implementation_review_prompt.md:364`;
`src/health_agent_infra/core/narration/render.py:257`;
`verification/tests/test_today_streak_prose.py:9`;
`verification/tests/test_today_streak_prose.py:147`

**Argument:** The PLAN defines W-AG as day-1 versus day-30+ prose:
the catalogue row says "different language for day-1 vs day-30 users",
and the workstream contract says "day-30+ (established streak,
history)." The review prompt explicitly says a threshold of ">= 7"
would be a finding. The implementation sets
`_STREAK_ESTABLISHED_THRESHOLD = 7`, and the tests lock that behavior
in with "streak_days >= 7" and "Boundary: streak == 7 should already
use established voice." That is a direct contract mismatch, even
though the current test suite is green.

**Recommended response:** fix-and-reland. Either change the renderer
and tests to the planned day-30+ threshold, or revise PLAN/CARRY_OVER
and the W-AG acceptance text before ship if 7 days is now the intended
product decision.

### F-IR-02. `hai init --guided` reports interrupted/partial guided flows as exit 0

**Q-bucket:** Q5
**Severity:** scope-mismatch
**Reference:** `03fab4f`;
`reporting/plans/v0_1_13/codex_implementation_review_prompt.md:309`;
`reporting/plans/v0_1_13/codex_implementation_review_prompt.md:313`;
`reporting/plans/v0_1_13/PLAN.md:359`;
`src/health_agent_infra/cli.py:5413`;
`src/health_agent_infra/cli.py:5631`;
`src/health_agent_infra/core/init/onboarding.py:520`;
`verification/tests/test_init_onboarding_flow.py:559`;
`verification/tests/test_init_onboarding_flow.py:568`

**Argument:** The review prompt asks this round to verify that each
guided step's failure mode surfaces a `USER_INPUT` exit code with
actionable next-step prose, and that `KeyboardInterrupt` is injected
at each step boundary. The implementation records failed steps as
`overall_status = "partial"` in the orchestrator and catches
`KeyboardInterrupt` as `{"status": "interrupted", "hint": ...}`, but
`cmd_init` always emits the JSON report and returns `exit_codes.OK`
after the guided block. The only interrupt test injects at `raise_at=2`,
not at each step boundary, and it asserts that interrupt "must exit
cleanly" rather than asserting `USER_INPUT`.

This creates a user-facing false green: an interrupted guided flow or
first-pull failure can return process exit 0 while the JSON body says
the guided flow is interrupted or partial.

**Recommended response:** fix-and-reland. Map guided
`status == "interrupted"` and failed/partial guided substeps to
`USER_INPUT`, preserving the current actionable hint. Add a
parametrized boundary test for the auth, intent/target, first-pull,
and today-surface steps, or explicitly revise W-AA/W-AD if OK-with-
partial-report is the desired CLI contract.

### F-IR-03. W-AK did not add declarative `expected_actions` to the 12 persona files

**Q-bucket:** Q6
**Severity:** scope-mismatch
**Reference:** `45319da`;
`reporting/plans/v0_1_13/PLAN.md:119`;
`reporting/plans/v0_1_13/PLAN.md:587`;
`reporting/plans/v0_1_13/PLAN.md:595`;
`reporting/plans/v0_1_13/codex_implementation_review_prompt.md:369`;
`verification/dogfood/personas/base.py:169`;
`verification/dogfood/personas/base.py:183`;
`verification/tests/test_persona_expected_actions.py:12`;
`verification/dogfood/runner.py:769`;
`reporting/plans/v0_1_13/CARRY_OVER.md:46`

**Argument:** W-AK's catalogue row names
`verification/dogfood/personas/p*.py` as the files to update, the
contract says each persona declares an `expected_actions` dict in its
own file, and the prompt asks this review to verify all 12 persona
files have `expected_actions` declared. They do not: the command
`rg -n "expected_actions" verification/dogfood/personas/p*.py`
returns no matches. Instead, `PersonaSpec.__post_init__` auto-derives
`expected_actions` and `forbidden_actions` in `base.py`, and the test
docstring explicitly allows "Either declared inline OR auto-derived".

The runner assertion exists, so the behavioral guard is real. The
missing piece is the declared persona-local ground truth W-AK said it
was adding as the precondition for v0.1.14 W58 prep. CARRY_OVER also
describes this as declared on `base.py::PersonaScenario`, but the class
is `PersonaSpec` and the declarations are auto-derived, not persona-
specific.

**Recommended response:** fix-and-reland or revise-artifact. Preferred:
add explicit non-empty `expected_actions` declarations to each of the
12 persona modules, and keep the base-class fallback only as a safety
net or remove it. If auto-derivation is intentional, revise PLAN,
CARRY_OVER, and tests to say W-AK shipped derived defaults rather than
declarative per-persona declarations.

### F-IR-04. W-LINT's meta-document pragma is a file-wide opt-out outside the four-constraint exception path

**Q-bucket:** Q6
**Severity:** acceptance-weak
**Reference:** `45319da`;
`reporting/plans/v0_1_13/PLAN.md:537`;
`reporting/plans/v0_1_13/PLAN.md:540`;
`reporting/plans/v0_1_13/PLAN.md:544`;
`reporting/plans/v0_1_13/PLAN.md:649`;
`reporting/plans/v0_1_13/PLAN.md:664`;
`reporting/plans/v0_1_13/codex_implementation_review_prompt.md:374`;
`src/health_agent_infra/core/lint/regulated_claims.py:113`;
`src/health_agent_infra/core/lint/regulated_claims.py:275`;
`verification/tests/test_regulated_claim_lint.py:300`

**Argument:** The W-LINT plan narrows the exception path to four
constraints that all hold: allowlisted packaged skill
(`expert-explainer` only), provenance citation, quoted/attributed
context, and strict CLI rendering. The implementation adds
`META_DOCUMENT_PRAGMA`, and `scan_skill_text` returns `[]` immediately
for any text containing that pragma when `allow_exception` is true,
before checking the allowlist, citation, or quoted-context constraints.
The tests then require `safety`, `reporting`, and `expert-explainer` to
carry the pragma.

That may be a reasonable separate exception for scope-statement skill
files, but it is not the exception described in W-LINT. As written,
any future packaged skill can suppress the static scanner by adding a
comment string. That is the "wholesale loophole" shape the plan's risk
row was trying to prevent.

**Recommended response:** fix-and-reland. Make the meta-document path
explicitly bounded, for example by hard-coding a small meta-document
allowlist separate from the user-facing `expert-explainer` exception
and adding a negative test that an arbitrary skill with the pragma is
still scanned. Alternatively, revise W-LINT to document the separate
meta-document exception and its guardrails.

### F-IR-05. W-29-prep provenance says only `bd11be3` regenerated snapshots after freeze, but `03fab4f` did too

**Q-bucket:** Q1 / Q6
**Severity:** provenance-gap
**Reference:** `45319da`, `03fab4f`, `bd11be3`;
`reporting/plans/v0_1_13/codex_implementation_review_prompt.md:212`;
`reporting/plans/v0_1_13/codex_implementation_review_prompt.md:394`;
`reporting/plans/v0_1_13/CARRY_OVER.md:48`;
`reporting/docs/cli_boundary_table.md:15`;
`reporting/docs/cli_boundary_table.md:21`;
`verification/tests/snapshots/cli_capabilities_v0_1_13.json`;
`verification/tests/snapshots/cli_help_tree_v0_1_13.txt`

**Argument:** W-29-prep's written provenance says the byte-stability
snapshots were frozen after W-AB/W-AE, and that the W-FBC-2
`--re-propose-all` help-text change at `bd11be3` is the only
post-W-29-prep regeneration path. The on-disk git history disagrees:
`git log --oneline -- verification/tests/snapshots/...` shows
`45319da`, then `03fab4f`, then `bd11be3`. `git show --stat 03fab4f`
shows W-AA changed both snapshot files, adding the `hai init --guided`
surface after the W-29-prep baseline.

The final snapshots may be correct, but the freeze story is not. That
matters because v0.1.14 W-29 is supposed to use this audit as its
go/no-go provenance.

**Recommended response:** revise-artifact. Update CARRY_OVER,
`cli_boundary_table.md`, and RELEASE_PROOF when authored to name both
legitimate post-baseline snapshot changes: W-AA `--guided` at
`03fab4f` and W-FBC-2 `--re-propose-all` help text at `bd11be3`. If
the intended contract is "baseline frozen after all v0.1.13 public
surface changes", say that instead of "post-W-AB/W-AE".

### F-IR-06. README verification count is stale relative to the implemented test surface

**Q-bucket:** Q6 / Q12
**Severity:** nit
**Reference:** `45319da`; `README.md:14`; `README.md:52`;
`reporting/plans/v0_1_13/CARRY_OVER.md:37`

**Argument:** The README rewrite says `2455 passing tests` in both the
badge and the "What ships today" table. The implemented v0.1.13 test
surface is now 2486 passed, 3 skipped, which matches CARRY_OVER's
W-N-broader row and the review run. Because W-AC is already claiming
the current v0.1.13 surface, this is stale public orientation rather
than just absent RELEASE_PROOF/REPORT/CHANGELOG.

**Recommended response:** fix-and-reland or revise during ship-time
freshness sweep. Update the README count/badge to the actual final
gate result.

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-Vb | PASS | P1+P4+P5 ship-set is implemented and tested; 9-persona residual is honestly fork-deferred to v0.1.14 W-Vb-3. |
| W-N-broader | PASS | Full suite and `-W error::Warning` gate both pass at 2486 passed, 3 skipped. |
| W-FBC-2 | PASS | Option A carryover-token implementation is domain-agnostic and covered by recovery/persona and multidomain tests; no option B primitive shipped. |
| CP6 | PASS | Strategic-plan framing edit is applied and v0.1.10 update line is preserved. |
| W-AA | FIX | F-IR-02: guided partial/interrupted flows return OK and interrupt coverage is narrower than the prompt's boundary contract. |
| W-AB | PASS | `hai capabilities --human` surface and tests are present. |
| W-AC | NOTE | F-IR-06: README test count is stale. |
| W-AD | PASS | AST/source-level USER_INPUT prose test passes; W-AA needs a decision on whether interrupted guided flow is a USER_INPUT site. |
| W-AE | PASS | `doctor --deep`, onboarding readiness, outcome classes, and triage doc are present and tested. |
| W-AF | PASS | README quickstart smoke test is present and green in the full suite. |
| W-AG | FIX | F-IR-01: established-streak threshold is 7 days, not day-30+. |
| W-AK | FIX | F-IR-03: runner assertion exists, but persona-local declarations do not. |
| W-LINT | FIX | F-IR-04: pragma bypass is broader than the four-constraint exception contract. |
| W-A1C7 | PASS | Trusted-first-value language and acceptance-matrix contract test are present. |
| W-29-prep | NOTE | F-IR-05: snapshot provenance omits the W-AA post-baseline regeneration. Parser/capabilities regression test passes. |
| W-CARRY | PASS | CARRY_OVER covers the inherited and v0.1.13+ rows; W-AK wording should be revised if F-IR-03 is accepted. |
| W-CF-UA | catalogue completeness only - not v0.1.13 deliverable | Hotfix provenance is present; no new v0.1.13 implementation review finding. |

## Open questions for maintainer

1. Is W-AG's established-user threshold supposed to be day-30+ as
   planned, or did v0.1.13 intentionally lower it to day 7?
2. Should `hai init --guided` communicate partial/interrupted progress
   via exit 0 plus JSON status, or should those paths be `USER_INPUT`
   as the round prompt requires?
3. Is W-LINT's meta-document pragma intended as a second, separately
   bounded exception class? If yes, it needs an explicit allowlist and
   plan text so it is not confused with the `expert-explainer`
   exception.
