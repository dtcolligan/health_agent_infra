# Audit Cycle

Health Agent Infra uses structured Codex review before substantive releases.
The review is not a badge; the artifact is the value. This file indexes the
existing release-cycle audit records so they are visible from the repo root.

## v0.1.18 - 2026-05-06

Onboarding-quality + intake-handler migration parity. 7 W-ids closed:
W-OB-1 (README pivot ratified), W-OB-2 (`hai init` interactive default
with opt-outs), W-OB-3 (`--guided` post-prompt next_action_hint +
skip-input affordance tests), W-OB-4a (Phase 1 upgrade dogfood),
W-OB-4b (Phase 2 local-wheel smoke), W-OB-5 (`hai doctor next_action`
across hint-emitting checks with manifest-consistency invariant),
W-OB-7 (intake-handler migration parity — closes F-OB-PRE-01).
W-OB-6 conditional did NOT fire. **Tier:** substantive (W-OB-2
release-blocker leg).

| Round | Artifact | Result |
|---|---|---|
| Phase 0 (D11) | [`reporting/plans/v0_1_18/audit_findings.md`](reporting/plans/v0_1_18/audit_findings.md) | 4 records: F-OB-PRE-01 (revises-scope, absorbed as W-OB-7) + F-PHASE0-01..03 (informational); pre-implementation gate fired `OPEN PHASE 1` |
| D14 round 1 | [`reporting/plans/v0_1_18/codex_plan_audit_response.md`](reporting/plans/v0_1_18/codex_plan_audit_response.md) | 7 findings PLAN_COHERENT_WITH_REVISIONS |
| D14 round 2 | [`reporting/plans/v0_1_18/codex_plan_audit_round_2_response.md`](reporting/plans/v0_1_18/codex_plan_audit_round_2_response.md) | 3 findings PLAN_COHERENT_WITH_REVISIONS close-in-place; D14 closed (7 → 3 halving signature) |
| D15 IR round 1 | [`reporting/plans/v0_1_18/codex_implementation_review_response.md`](reporting/plans/v0_1_18/codex_implementation_review_response.md) | 4 findings SHIP_WITH_FIXES (F-IR-01 stale agent_cli_contract.md + F-IR-02 README pre-W-OB-2 wording + F-IR-03 missed concrete doctor checks + F-IR-04 next_action_hint correctness bug); all 4 accepted + fixed in fix-and-reland commit |
| D15 IR round 2 | [`reporting/plans/v0_1_18/codex_implementation_review_round_2_response.md`](reporting/plans/v0_1_18/codex_implementation_review_round_2_response.md) | 2 findings SHIP_WITH_FIXES (F-IR-R2-01 deep-probe `check_auth_intervals_icu` outcomes still without `next_action` + F-IR-R2-02 release-summary surface propagation gap); both accepted + fixed in fix-and-reland-2 commit |
| D15 IR round 3 | [`reporting/plans/v0_1_18/codex_implementation_review_round_3_response.md`](reporting/plans/v0_1_18/codex_implementation_review_round_3_response.md) | 1 nit-class finding SHIP_WITH_NOTES (F-IR-R3-01 R2 response_response file-count off by one); close-in-place amendment, no fix-and-reland-3. **D15 IR closed.** |
| Verification | [`reporting/plans/v0_1_18/RELEASE_PROOF.md`](reporting/plans/v0_1_18/RELEASE_PROOF.md) | 2733 pass / 5 skipped (post-IR-R2 fix-and-reland-2; R3 introduced no source/test changes); mypy + bandit clean; persona matrix 13/13 (identical to baseline); manifest snapshot regenerated for W-OB-2 `--non-interactive` flag intentional add; agent_cli_contract.md regenerated post-version-bump |

**Outcome:** v0.1.18 ships onboarding ergonomics + upgrade-path
correctness. **D15 IR closed at R3 SHIP_WITH_NOTES** (settling shape
4 → 2 → 1-nit, matching AGENTS.md empirical norm `5 → 2 → 1-nit`
twice-validated against v0.1.11 + v0.1.12 + v0.1.17). F-OB-PRE-01
(the maintainer-DB crash surfaced 2026-05-05) closed end-to-end via
the additive `open_connection_with_migrations` seam. `hai init`
default-flip makes interactive first-run friction-free without
breaking CI / agent automation. `hai doctor next_action` gives agents
a structured companion to the existing `hint` field across 9 doctor
check paths (including deep-probe outcomes). v0.1.18 W-OB-4a +
W-OB-4b are maintainer dogfood; foreign-user empirical claim stays
v0.1.19's. **PyPI publish remaining maintainer-only:** manual TTY
ship gate (RELEASE_PROOF §3) → `git push origin main` → `uvx twine
upload`.

---

## v0.1.17 - 2026-05-05

Maintainability + eval substrate consolidation. 10 W-ids closed: W-29
(cli.py 9927-LOC mechanical split), W-30 (capabilities-manifest schema
regression test), W-AH-2 (scenario corpus 35 → 135), W-AI-2
(`hai eval review` CLI), W-AM-2 (4 escalate scenarios), W-Vb-4 (12-of-12
persona closure), F-PV14-02 (`hai sync purge` surgical cleanup), W-B
(`hai intake weight` + body_comp + migration 026), W-D arm-2 (partial-
day macro projection), W-C-EQP (migration 025 query-plan stability).
**Tier:** substantive.

| Round | Artifact | Result |
|---|---|---|
| Phase 0 (D11) | [`reporting/plans/v0_1_17/audit_findings.md`](reporting/plans/v0_1_17/audit_findings.md) | 9 findings (5 nit, 4 none); pre-implementation gate fired `OPEN PHASE 1` |
| D14 round 1 | [`reporting/plans/v0_1_17/codex_plan_audit_response.md`](reporting/plans/v0_1_17/codex_plan_audit_response.md) | 11 findings PLAN_COHERENT_WITH_REVISIONS |
| D14 round 2 | [`reporting/plans/v0_1_17/codex_plan_audit_round_2_response.md`](reporting/plans/v0_1_17/codex_plan_audit_round_2_response.md) | 5 findings PLAN_COHERENT_WITH_REVISIONS (halving on track) |
| D14 round 3 | [`reporting/plans/v0_1_17/codex_plan_audit_round_3_response.md`](reporting/plans/v0_1_17/codex_plan_audit_round_3_response.md) | 3 findings PLAN_COHERENT_WITH_REVISIONS close-in-place; D14 closed |
| D15 IR round 1 | [`reporting/plans/v0_1_17/codex_implementation_review_response.md`](reporting/plans/v0_1_17/codex_implementation_review_response.md) | 6 findings SHIP_WITH_FIXES (Bandit + `_find_in_corpus` + W-D arm-2 explain + W-AH-2 vacuous-axis + wheel hygiene + paper docs unnamed) |
| D15 IR round 2 | [`reporting/plans/v0_1_17/codex_implementation_review_round_2_response.md`](reporting/plans/v0_1_17/codex_implementation_review_round_2_response.md) | 1 nit SHIP_WITH_NOTES close-in-place; IR closed |
| Verification | [`reporting/plans/v0_1_17/RELEASE_PROOF.md`](reporting/plans/v0_1_17/RELEASE_PROOF.md) | 2688 pass / 5 skipped; `hai eval run --scenario-set all` 135/135 with non-vacuous classifier-axis (post-IR-R1 F-IR-04); mypy + bandit clean; manifest byte-stable across W-29 split; wheel-content smoke green |

**Outcome:** v0.1.17 ships substantive maintainability + eval-substrate
consolidation. cli.py 9927 LOC → ~2986-LOC main + 11 handler-group
modules (each <2500 LOC). Eval scenario corpus tripled (35 → 135) at
100% pass-rate. New `hai sync purge` + `hai intake weight` + `hai eval
review` surfaces. W-D arm-2 partial-day macro projection closes the
v0.1.15 W-D arm-1 known-incomplete fix. AGENTS.md "Do Not Do"
cli.py-split clause retired; W-30 schema-freeze clause retained until
v0.2.3.

**D14 halving signature:** 11 → 5 → 3 (thrice-validated against AGENTS.md
empirical norm `10 → 5 → 3 → 0`; one round shorter than v0.1.11/v0.1.12
because v0.1.17's catalogue was largely inherited from prior release-
proofs with established source contracts).

**D15 IR settling signature:** 6 → 1 (within AGENTS.md empirical
`5 → 2 → 1-nit`; one round shorter than canonical 3-round shape because
R1 fixes were mechanical/contractual rather than architectural and no
second-order issue surfaced from the R1 reland).

## v0.1.15.1 - 2026-05-03

Linux keyring fall-through hotfix. CI on Linux exposed a runtime crash
where `keyring` imported successfully but raised `NoKeyringError` when
no backend was registered. The hotfix adds `keyrings.alt` as a runtime
dependency and makes `_default_backend()` degrade to `_NullBackend`
when the backend probe fails. **Tier:** hotfix.

| Round | Artifact | Result |
|---|---|---|
| Scope | [`reporting/plans/v0_1_15_1/HOTFIX_SCOPE.md`](reporting/plans/v0_1_15_1/HOTFIX_SCOPE.md) | Maintainer ratified Option B: keyring fix + two doc items + public candidate-name scrub |
| D14 / external IR | skipped | Hotfix latitude per AGENTS.md D15; single bug class |
| Verification | [`reporting/plans/v0_1_15_1/RELEASE_PROOF.md`](reporting/plans/v0_1_15_1/RELEASE_PROOF.md) | Full gates recorded: 2631 passed, 3 skipped; no schema change; CLI contract regenerated for version line |

**Outcome:** `v0.1.15.1` is the candidate package for the post-publish
foreign-user session. v0.1.16 remains the empirical-fix cycle for any
session findings.

## v0.1.15 - 2026-05-03

Foreign-user-ready package + empirical-validation framework. Six W-ids
shipped (W-GYM-SETID, F-PV14-01, W-A, W-C, W-D arm-1, W-E); W-2U-GATE
recorded session reframed from ship-gate to empirical-validation
feeding v0.1.16 per the post-IR-close publish-first pivot. Migration
head 23 → 25 (gym_set PK with exercise slug + target_type CHECK
extended with carbs_g + fat_g via recreate-and-copy). **Tier:**
substantive.

| Round | Codex response | Maintainer response |
|---|---|---|
| D14 plan-audit r1 | PLAN_COHERENT_WITH_REVISIONS, 12 findings (F-PLAN-01..12) | All AGREED + applied |
| D14 plan-audit r2 | PLAN_COHERENT_WITH_REVISIONS, 7 findings (F-PLAN-R2-01..07) | All AGREED + applied |
| D14 plan-audit r3 | PLAN_COHERENT_WITH_REVISIONS, 3 nits | Close-in-place |
| Phase 0 (D11) | 1 revises-scope (F-PHASE0-01) + 3 nits + persona matrix 13/13 clean | Option A: extend existing target table (F-PHASE0-01); D14 r4 applied |
| D14 plan-audit r4 | PLAN_COHERENT_WITH_REVISIONS, 2 close-in-place (F-R4-01 + F-R4-02) | Both AGREED + applied |
| D15 IR r1 | SHIP_WITH_FIXES, 6 findings (F-IR-01..06) | All AGREED + applied (commit 9e113b4) |
| D15 IR r2 | SHIP_WITH_FIXES, 2 findings (F-IR-R2-01 vacuous test + F-IR-R2-02 stale citations + named-defer surfacing) | Both AGREED + applied (commit 48eb3e2) |
| D15 IR r3 | SHIP_WITH_NOTES, 1 nit (F-IR-R3-01 stale source comment) | Close-in-place (commit ac2d1fe) |

**Outcome:** Shipped post-IR-close per the publish-first pivot. D14
chain settled at 12 → 7 → 3 → 2 (4 rounds, AGENTS.md halving-norm met
modulo the post-Phase-0 round-4 revision). D15 IR chain settled at
6 → 2 → 1 (AGENTS.md `5 → 2 → 1-nit` norm met at slightly higher
absolute counts driven by the cycle bundling 6 W-ids). Test surface:
2630 passed, 3 skipped (+50 vs v0.1.14.1). Mypy clean (0 errors @ 128
source files). Bandit clean (0 medium/high). Capabilities snapshot
regenerated; W-A presence-block + W-C `hai target nutrition` + new
flags additive. Release proof:
[`reporting/plans/v0_1_15/RELEASE_PROOF.md`](reporting/plans/v0_1_15/RELEASE_PROOF.md).

## v0.1.14.1 - 2026-05-02

Garmin-live unreliability surfaced as a structured signal in the
capabilities manifest. `hai capabilities --json` now exposes
`flags[].choice_metadata` with a `garmin_live → {reliability:
"unreliable", reason: ..., prefer_instead: "intervals_icu"}` block on
both `hai pull --source` and `hai daily --source`; `_resolve_pull_source`
emits a single stderr warning when the resolved source is `garmin_live`.
Single workstream (W-GARMIN-MANIFEST-SIGNAL); purely additive — manifest
`schema_version` unchanged. **Tier:** hardening.

| Round | Codex response | Maintainer response |
|---|---|---|
| Plan-audit | (skipped per D15 hardening latitude) | n/a |
| Implementation review | (skipped per D15 hardening latitude — internal sweep + test gates were the ship evidence) | n/a |

**Outcome:** Shipped as a hardening cycle without an external Codex
audit round. Test surface: 2581 passed, 3 skipped (+15 vs v0.1.14).
Broader-warning gate (`-W error::Warning`) clean. Mypy 0 errors @ 127
source files. Bandit 46 Low / 0 Medium / 0 High (unchanged from v0.1.14
baseline). Ruff clean on modified files. Capabilities snapshot
regenerated; diff is purely additive (two `choice_metadata` blocks).
Release proof:
[`reporting/plans/v0_1_14_1/RELEASE_PROOF.md`](reporting/plans/v0_1_14_1/RELEASE_PROOF.md).
Report: [`reporting/plans/v0_1_14_1/REPORT.md`](reporting/plans/v0_1_14_1/REPORT.md).

## v0.1.14 - 2026-05-01

Eval substrate + provenance + recovery path. 13 W-ids at PLAN open
(post-W-2U-GATE-defer): 8 closed, 3 partial-closed with named v0.1.15
destinations (W-AH / W-AI / W-Vb-3), 2 deferred (W-2U-GATE / W-29),
1 absorbed (W-AM into W-AI). Pre-implementation gate invoked PLAN.md
§1.3.1 path 2 to defer W-2U-GATE foreign-machine onboarding empirical
proof (no candidate on file at gate). **Tier:** substantive.

| Round | Codex response | Maintainer response |
|---|---|---|
| Plan-audit 1-4 | [`codex_plan_audit_response.md`](reporting/plans/v0_1_14/codex_plan_audit_response.md) (+ rounds 2-4; settled at PLAN_COHERENT round 4 with 12 → 7 → 3 → 1-nit → CLOSE signature; 23 cumulative findings, all ACCEPT) | rounds 1-4 |
| Implementation review 1-3 | [`codex_implementation_review_response.md`](reporting/plans/v0_1_14/codex_implementation_review_response.md) (round 1 SHIP_WITH_FIXES, 7 findings) → [`codex_implementation_review_round_2_response.md`](reporting/plans/v0_1_14/codex_implementation_review_round_2_response.md) (round 2 SHIP_WITH_FIXES, 2 findings) → [`codex_implementation_review_round_3_response.md`](reporting/plans/v0_1_14/codex_implementation_review_round_3_response.md) (round 3 SHIP_WITH_NOTES, 1 nit) | [`codex_implementation_review_round_1_response.md`](reporting/plans/v0_1_14/codex_implementation_review_round_1_response.md) → [`codex_implementation_review_round_2_response_response.md`](reporting/plans/v0_1_14/codex_implementation_review_round_2_response_response.md) → [`codex_implementation_review_round_3_response_response.md`](reporting/plans/v0_1_14/codex_implementation_review_round_3_response_response.md) |

**Outcome:** `SHIP_WITH_NOTES` in implementation round 3 with the
F-IR-R3-01 nit applied. Settling shape `7 → 2 → 1-nit` mirrors
v0.1.12 (`5 → 2 → 0`) + v0.1.13 (`6 → 2 → 0`); 10 cumulative IR
findings, all ACCEPT. Test surface: 2566 passed, 3 skipped (+73 vs
v0.1.13). All ship gates green: pytest broader, mypy 0 @ 127,
bandit 46 Low / 0 Med / 0 High, ruff clean, capabilities byte-stable
post-snapshot regen for the named-change-accepted W-AN + W-BACKUP +
W-PROV-1 surfaces. Release proof:
[`reporting/plans/v0_1_14/RELEASE_PROOF.md`](reporting/plans/v0_1_14/RELEASE_PROOF.md).
Report: [`reporting/plans/v0_1_14/REPORT.md`](reporting/plans/v0_1_14/REPORT.md).

## v0.1.13 - 2026-04-30

Largest cycle in the v0.1.x track at 17 workstreams. Three parallel themes:
close v0.1.12 named-deferred items (W-Vb persona-replay end-to-end ship-set,
W-N-broader 50-site sqlite3 leak fix, W-FBC-2 multi-domain F-B-04 closure,
CP6 §6.3 strategic-plan edit), ship the originally-planned onboarding scope
(W-AA `hai init --guided`, W-AB `hai capabilities --human`, W-AC README
rewrite, W-AD USER_INPUT prose, W-AE `hai doctor --deep`, W-AF README smoke,
W-AG `hai today` cold-start prose), land governance prerequisites
(W-29-prep cli.py boundary audit, W-LINT regulated-claim lint, W-AK
declarative persona expected-actions, W-A1C7 acceptance matrix). Cycle-order
inversion: IR ran *before* RELEASE_PROOF authoring. **Tier:** substantive.

| Round | Codex response | Maintainer response |
|---|---|---|
| Plan-audit 1-5 | [`codex_plan_audit_response.md`](reporting/plans/v0_1_13/codex_plan_audit_response.md) (+ rounds 2-5; settled at PLAN_COHERENT round 5 with 11 → 7 → 3 → 1-nit → 0 signature) | rounds 1-5 |
| Implementation review 1-3 | [`codex_implementation_review_response.md`](reporting/plans/v0_1_13/codex_implementation_review_response.md) (round 1 SHIP_WITH_FIXES, 6 findings) → [`codex_implementation_review_round_2_response.md`](reporting/plans/v0_1_13/codex_implementation_review_round_2_response.md) (round 2 SHIP_WITH_FIXES, 2 findings) → [`codex_implementation_review_round_3_response.md`](reporting/plans/v0_1_13/codex_implementation_review_round_3_response.md) (round 3 SHIP, 0 findings) | [`codex_implementation_review_round_1_response.md`](reporting/plans/v0_1_13/codex_implementation_review_round_1_response.md) → [`codex_implementation_review_round_2_response_response.md`](reporting/plans/v0_1_13/codex_implementation_review_round_2_response_response.md) |

**Outcome:** `SHIP` in implementation round 3. 16 of 17 W-ids closed-this-cycle;
1 partial-closure (W-Vb, P1+P4+P5 ship-set with 9-persona residual fork-deferred
to v0.1.14 W-Vb-3). Test surface: 2493 passed, 3 skipped (+109 vs v0.1.12).
Broader-warning gate (`-W error::Warning`) restored as the v0.1.13 ship target.
Release proof:
[`reporting/plans/v0_1_13/RELEASE_PROOF.md`](reporting/plans/v0_1_13/RELEASE_PROOF.md).
Report: [`reporting/plans/v0_1_13/REPORT.md`](reporting/plans/v0_1_13/REPORT.md).

## v0.1.12 - 2026-04-29

Carry-over closure + trust repair. No release-blocker workstream by design.
Ten workstreams across docs / governance / per-domain code / mypy / demo
packaging. Settled D15 (cycle-weight tiering: substantive / hardening /
doc-only / hotfix). Six cycle proposals (CP1-CP6) authored.

| Round | Codex response | Maintainer response |
|---|---|---|
| Plan-audit 1-4 | [`codex_plan_audit_response.md`](reporting/plans/v0_1_12/codex_plan_audit_response.md) (+ rounds 2-4; settled at PLAN_COHERENT round 4 with 10 → 5 → 3 → 0 signature) | rounds 1-4 |
| Implementation review 1-2 | [`codex_implementation_review_response.md`](reporting/plans/v0_1_12/codex_implementation_review_response.md) (round 1 SHIP_WITH_FIXES) → round 2 SHIP_WITH_NOTES | rounds 1-2 |

**Outcome:** `SHIP_WITH_NOTES` in implementation round 2. 8 of 10 W-ids
shipped, 2 partial-closures (W-Vb, W-FBC), 1 named-fork (W-N-broader). Test
surface: 2384 passed, 2 skipped (+37 vs v0.1.11). Release proof:
[`reporting/plans/v0_1_12/RELEASE_PROOF.md`](reporting/plans/v0_1_12/RELEASE_PROOF.md).
Report: [`reporting/plans/v0_1_12/REPORT.md`](reporting/plans/v0_1_12/REPORT.md).

A v0.1.12.1 hotfix shipped 2026-04-29 to address a Cloudflare User-Agent
block on the intervals.icu pull adapter (W-CF-UA). See
[`reporting/plans/v0_1_12_1/RELEASE_PROOF.md`](reporting/plans/v0_1_12_1/RELEASE_PROOF.md).

## v0.1.11 - 2026-04-28

Audit-cycle deferred items closed (W-B/E/F/H/K/L/N/Q/R), persona matrix
expanded 8 → 12, property-based tests for the policy DSL, demo isolation
contract shipped (boundary-stop replay). Settled D13 (threshold-injection
seam trusted-by-design) + D14 (pre-cycle Codex plan-audit pattern).

| Round | Audit prompt | Codex response | Maintainer response |
|---|---|---|---|
| Plan-audit 1-4 | [`codex_plan_audit_prompt.md`](reporting/plans/v0_1_11/codex_plan_audit_prompt.md) | [`codex_plan_audit_response.md`](reporting/plans/v0_1_11/codex_plan_audit_response.md) (+ rounds 2-4) | rounds 1-4 |
| Implementation review 1-4 | (D14-revised PLAN.md) | rounds 1-4 | rounds 1-4 |

**Outcome:** `SHIP` in implementation round 4. 19 of 20 W-ids shipped;
W-Vb named-deferred to v0.1.12. Test surface: 2347 passed, 2 skipped
(+145 vs v0.1.10). Release proof:
[`reporting/plans/v0_1_11/RELEASE_PROOF.md`](reporting/plans/v0_1_11/RELEASE_PROOF.md).

## v0.1.10 - 2026-04-27

Pre-PLAN bug-hunt phase introduced (D11), persona harness landed, mypy +
bandit correctness pass, write-surface guard. First cycle to run a
structured audit phase before plan authoring.

**Outcome:** `SHIP_WITH_NOTES`. Audit findings consolidated to
[`reporting/plans/v0_1_10/audit_findings.md`](reporting/plans/v0_1_10/audit_findings.md);
all `in-scope` findings absorbed; deferred items carry to v0.1.11. Release
proof: [`reporting/plans/v0_1_10/RELEASE_PROOF.md`](reporting/plans/v0_1_10/RELEASE_PROOF.md).

## v0.1.9 - 2026-04-26

Hardening and governance closure after parallel Codex + Claude reviews of
the v0.1.8 surface. Scope is B1-B8 only: W57 archive/commit gates,
fail-loud skill overlay, validator shape hardening, direct synthesize parity,
pull/clean provenance, safety-skill prose, and small P2 hygiene.

| Round | Audit prompt | Maintainer response |
|---|---|---|
| Implementation review | [`codex_audit_prompt.md`](reporting/plans/v0_1_9/codex_audit_prompt.md) | [`codex_implementation_review_response.md`](reporting/plans/v0_1_9/codex_implementation_review_response.md) |

**Outcome:** `SHIP_WITH_FIXES` review findings accepted and fixed. Full
suite: 2133 passed, 2 skipped. Release proof:
[`reporting/plans/v0_1_9/RELEASE_PROOF.md`](reporting/plans/v0_1_9/RELEASE_PROOF.md).

Report: [`reporting/plans/v0_1_9/REPORT.md`](reporting/plans/v0_1_9/REPORT.md).

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
