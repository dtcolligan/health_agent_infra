# Codex Implementation Review - v0.1.13

**Verdict:** SHIP_WITH_FIXES
**Round:** 2

## Verification summary

- Tree state: started clean on `cycle/v0.1.13`; `git status --short`
  was empty. HEAD is `ca0b986` (`v0.1.13 IR r1: fixes for F-IR-01..06
  (SHIP_WITH_FIXES -> SHIP-ready)`).
- Review scope: round-1 findings in
  `codex_implementation_review_response.md`, maintainer response in
  `codex_implementation_review_round_1_response.md`, and the fix diff
  introduced by `ca0b986`.
- Focused fix tests:
  `uv run pytest verification/tests/test_init_onboarding_flow.py verification/tests/test_persona_expected_actions.py verification/tests/test_regulated_claim_lint.py verification/tests/test_today_streak_prose.py verification/tests/test_user_input_messages_actionable.py -q`
  passed: 42 passed.
- Regression/ship tests:
  - `uv run pytest verification/tests -q`: 2493 passed, 3 skipped.
  - `uv run pytest verification/tests -W error::Warning -q`: 2493
    passed, 3 skipped.
  - `uv run pytest verification/tests/test_cli_parser_capabilities_regression.py -q`:
    5 passed.
  - `uv run pytest verification/tests/test_demo_persona_replay_end_to_end.py -q`:
    6 passed.
  - `uv run python -m verification.dogfood.runner /tmp/persona_run_ir_round2`:
    12 personas, 0 findings, 0 crashes.
- Static gates:
  - `uvx mypy src/health_agent_infra`: no issues found in 120 source files.
  - `uvx bandit -ll -r src/health_agent_infra`: exit 0, no medium/high
    issues identified.
  - `uvx ruff check src/health_agent_infra`: **failed** with 3 F541
    findings in `src/health_agent_infra/cli.py`.

## Findings

### F-IR-R2-01. Round-1 W-AA fix breaks the ruff ship gate

**Q-bucket:** Q5 / Q10
**Severity:** acceptance-weak
**Reference:** `ca0b986`;
`src/health_agent_infra/cli.py:5447`;
`src/health_agent_infra/cli.py:5448`;
`src/health_agent_infra/cli.py:5449`

**Argument:** The behavioral W-AA/W-AD fix works, but the static gate
does not. `uvx ruff check src/health_agent_infra` fails on three F541
diagnostics:

- `src/health_agent_infra/cli.py:5447`: f-string without placeholders.
- `src/health_agent_infra/cli.py:5448`: f-string without placeholders.
- `src/health_agent_infra/cli.py:5449`: f-string without placeholders.

All three are the new `guided onboarding partially failed` stderr
strings added for F-IR-02's W-AD interlock. This is a classic
second-order fix bug: the exit-code/prose behavior is now covered, but
the source no longer passes the release static gate.

**Recommended response:** fix-and-reland. Remove the unnecessary `f`
prefixes on those three literal string fragments, then rerun
`uvx ruff check src/health_agent_infra` plus the focused W-AA/W-AD tests.

### F-IR-R2-02. Round-1 artifact updates left current summary surfaces stale

**Q-bucket:** Q6 / Q11 / Q12
**Severity:** provenance-gap
**Reference:** `ca0b986`;
`README.md:14`;
`README.md:52`;
`reporting/plans/v0_1_13/CARRY_OVER.md:46`;
`verification/dogfood/personas/base.py:97`;
`verification/dogfood/personas/base.py:253`;
`verification/dogfood/personas/p1_dom_baseline.py:54`;
`verification/dogfood/personas/p8_day1_female_lifter.py:53`;
`verification/dogfood/personas/p11_elevated_stress_hybrid.py:70`;
`reporting/plans/v0_1_13/codex_implementation_review_round_1_response.md:171`;
`reporting/plans/v0_1_13/codex_implementation_review_round_1_response.md:176`

**Argument:** Two round-1 artifact surfaces still describe the pre- or
mid-fix state rather than the current branch.

First, F-IR-06 was accepted as stale README verification count. The
round-1 response says the current post-fix suite is 2493 passed, 3
skipped, and even says it is "updating to 2493", but the applied
README lines still say `2486` in both the badge and "What ships today"
table. The assertion that the +7 round-1 tests are "invisible at the
README level until the next ship" is not coherent with this branch's
ship surface: those tests are now part of the v0.1.13 release candidate
before RELEASE_PROOF/REPORT/CHANGELOG are authored.

Second, the W-AK CARRY_OVER row still says `expected_actions` are
declared on `verification/dogfood/personas/base.py::PersonaScenario`
and auto-derived from `ALLOWED_ACTIONS_BY_DOMAIN`. After the F-IR-03
fix, the class on disk is `PersonaSpec`, the public helpers live in
`base.py`, and the shipped persona files now carry inline
`expected_actions=` declarations. There is no `PersonaScenario` class
on disk. The row should name the actual shipped shape rather than the
round-1-finding shape.

**Recommended response:** revise-artifact. Update README to the current
verified branch count (`2493 passing tests`) unless another test delta
lands first. Update CARRY_OVER's W-AK row to say the 12 `p*.py` persona
files declare inline `expected_actions=` via the public helper baselines
in `base.py`, with `PersonaSpec.__post_init__` retained only as a
safety-net fallback.

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-Vb | PASS | Demo replay ship-set still passes; persona matrix is clean. |
| W-N-broader | PASS | Full warning gate passes at 2493 passed, 3 skipped. |
| W-FBC-2 | PASS | No round-2 issue found in the carryover-token implementation or parser/capabilities regression. |
| CP6 | PASS | No round-2 issue found. |
| W-AA | FIX | F-IR-R2-01: behavior fixed, but the added stderr string fails ruff. |
| W-AB | PASS | No round-2 issue found. |
| W-AC | NOTE | F-IR-R2-02: README count still stale after round-1 fix. |
| W-AD | FIX | Same as W-AA: W-AD stderr prose exists, but static gate fails on its f-string literals. |
| W-AE | PASS | No round-2 issue found. |
| W-AF | PASS | Quickstart smoke remains covered by the full suite. |
| W-AG | PASS | Threshold is now 30 with 30/29 boundary tests. |
| W-AK | NOTE | Code/test fix landed; CARRY_OVER row still describes the old auto-derived/base.py shape. |
| W-LINT | PASS | Meta-document pragma is now bounded by `META_DOCUMENT_ALLOWLIST`; focused tests pass. |
| W-A1C7 | PASS | No round-2 issue found. |
| W-29-prep | PASS | Parser/capabilities regression passes; snapshot provenance is corrected for W-AA and W-FBC-2. |
| W-CARRY | NOTE | F-IR-R2-02: W-AK row needs artifact correction. |
| W-CF-UA | catalogue completeness only - not v0.1.13 deliverable | No round-2 issue found. |

## Open questions for maintainer

None. The required fixes are mechanical: remove three `f` prefixes,
update the README count to the current gate result, and correct the
W-AK CARRY_OVER row.
