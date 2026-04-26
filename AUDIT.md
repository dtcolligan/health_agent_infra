# Audit Cycle

Health Agent Infra uses structured external review before substantive
releases. The review is not a badge; the artifact is the value. This file
indexes the existing release-cycle audit records so they are visible from
the repo root.

## v0.1.8 - 2026-04-25

Plan-aware feedback visibility: intent + target + data-quality ledgers,
code-owned review-summary tokens, four new `hai stats` modes, config
validate + diff, `hai daily --auto --explain`, and synthesis-skill scoring.

| Round | Audit prompt | Codex response | Maintainer response |
|---|---|---|---|
| 1 | [`codex_audit_prompt.md`](reporting/plans/v0_1_8/codex_audit_prompt.md) | [`codex_audit_response.md`](reporting/plans/v0_1_8/codex_audit_response.md) | [`codex_implementation_review_response.md`](reporting/plans/v0_1_8/codex_implementation_review_response.md) |
| 2 | See response | [`codex_implementation_review_round2_response.md`](reporting/plans/v0_1_8/codex_implementation_review_round2_response.md) | [`codex_implementation_review_response_round2.md`](reporting/plans/v0_1_8/codex_implementation_review_response_round2.md) |
| 3 | See response | [`codex_implementation_review_round3_response.md`](reporting/plans/v0_1_8/codex_implementation_review_round3_response.md) | [`codex_implementation_review_response_round3.md`](reporting/plans/v0_1_8/codex_implementation_review_response_round3.md) |
| 4 | See response | [`codex_implementation_review_round4_response.md`](reporting/plans/v0_1_8/codex_implementation_review_round4_response.md) | [`codex_implementation_review_response_round4.md`](reporting/plans/v0_1_8/codex_implementation_review_response_round4.md) |

**Outcome:** `SHIP_WITH_NOTES` in round 4. Net: +129 tests in the
release proof, W57 deactivation hardening, and bool-as-int defence in depth
for review-summary thresholds. Deferred notes are tracked in
[`reporting/plans/v0_1_9/BACKLOG.md`](reporting/plans/v0_1_9/BACKLOG.md).
Release proof:
[`reporting/plans/v0_1_8/RELEASE_PROOF.md`](reporting/plans/v0_1_8/RELEASE_PROOF.md).

## v0.1.7 - 2026-04-25

First-class agent flow and calibrated correctness.

| Round | Audit prompt | Response |
|---|---|---|
| 1 | [`codex_audit_prompt.md`](reporting/plans/v0_1_7/codex_audit_prompt.md) | [`codex_audit_response.md`](reporting/plans/v0_1_7/codex_audit_response.md) |

**Outcome:** `SHIP`. Release proof:
[`reporting/plans/v0_1_7/RELEASE_PROOF.md`](reporting/plans/v0_1_7/RELEASE_PROOF.md).
Report: [`reporting/plans/v0_1_7/REPORT.md`](reporting/plans/v0_1_7/REPORT.md).

## v0.1.6 - 2026-04-25

Migration-drift hardening, explicit proposal replacement semantics,
intervals.icu-as-default-source, and packaged-skills install.

| Round | Audit prompt | Response |
|---|---|---|
| 1 | [`codex_audit_prompt.md`](reporting/plans/v0_1_6/codex_audit_prompt.md) | [`internal_audit_response.md`](reporting/plans/v0_1_6/internal_audit_response.md) |
| 2 | [`codex_audit_prompt_round2.md`](reporting/plans/v0_1_6/codex_audit_prompt_round2.md) | [`codex_audit_response_round2.md`](reporting/plans/v0_1_6/codex_audit_response_round2.md) |
| Implementation review | [`codex_implementation_review_prompt.md`](reporting/plans/v0_1_6/codex_implementation_review_prompt.md) | [`codex_implementation_review_response.md`](reporting/plans/v0_1_6/codex_implementation_review_response.md) |

**Outcome:** `SHIP` after maintainer-owned revision plan
[`reporting/plans/v0_1_6/codex_v0_1_6_improvement_plan.md`](reporting/plans/v0_1_6/codex_v0_1_6_improvement_plan.md).

## v0.1.4 And Earlier

Pre-formal-cycle. Audit material lives under per-release folders without a
standardized round structure. The stronger pattern stabilized across
v0.1.6-v0.1.8.

## How A Round Works

1. The maintainer drafts `PLAN.md`.
2. A fresh Codex session reviews the plan or implementation diff.
3. Findings are classified by severity and tied to file/line evidence.
4. The maintainer replies with fixes, explicit deferrals, or disagreement.
5. Review repeats until the release reaches `SHIP` or `SHIP_WITH_NOTES`.
6. `RELEASE_PROOF.md` records version, tests, generated-contract state, and
   known deferrals.

The cycle exists because this is a single-maintainer project with a
high-value invariant: the code-vs-skill boundary must not decay under
release pressure.
