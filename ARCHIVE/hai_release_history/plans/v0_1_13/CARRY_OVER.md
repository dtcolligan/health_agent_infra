# v0.1.13 Carry-Over Register

**Date.** 2026-04-29 (authored at cycle open); **2026-04-30 (W-CARRY
disposition pass at implementation close)**.
**Authored by.** Claude (delegated by maintainer).
**Source.** `reporting/plans/v0_1_12/RELEASE_PROOF.md` §5
("Out-of-scope items deferred with documented reason") +
`reporting/plans/v0_1_12/CARRY_OVER.md` §3 (reconciliation §6
v0.1.13+ named-defers).

This register is the W-CARRY workstream deliverable per
`reporting/plans/v0_1_13/PLAN.md` §2.C. Every named-defer from
v0.1.12 + every reconciliation §6 v0.1.13+ item has a row with
disposition.

**Disposition vocabulary** (per AGENTS.md "Honest partial-closure
naming"):

- `closed-this-cycle` — workstream shipped on `cycle/v0.1.13` with
  per-row commit citation; full residual closed.
- `partial-closure → v0.1.X+1 W-X-N` — workstream shipped a named
  ship-set; the residual is fork-deferred to a destination cycle.
- `fork-deferred → v0.1.X+1 W-X` — full workstream pushed to a
  destination cycle without a v0.1.13 ship-set.

`in-cycle` (the cycle-open default) is replaced at implementation
close by one of the three terminal dispositions above. Rows still
showing `in-cycle` in this register are bugs.

---

## 1. v0.1.12 RELEASE_PROOF §5 named-defers

| Item | Disposition | W-id (this cycle) | Notes |
|---|---|---|---|
| **W-Vb persona-replay end-to-end** (proposal pre-population so `hai daily` reaches synthesis) | **partial-closure → v0.1.14 W-Vb-3** | W-Vb (v0.1.13) | **Shipped at `afffb45`.** P1+P4+P5 ship-set: flipped `apply_fixture()` to proposal-write branch + authored full-shape persona DomainProposal seeds for those 3 personas + clean-wheel build-install-subprocess test. The 9 non-ship-set personas (P2/P3/P6/P7/P8/P9/P10/P11/P12) are fork-deferred to v0.1.14 W-Vb-3 in §4 per F-PLAN-06 + F-PLAN-R2-02 + F-PLAN-R3-02. |
| **W-N-broader** (`-W error::Warning` gate fix — 49 + 1 sqlite3 connection-lifecycle leak sites) | **closed-this-cycle** | W-N-broader (v0.1.13) | **Shipped at `6ea9ea4`.** Closed 50 sqlite3 + 1 file-handle + 1 HTTPError leak sites. Broader-gate ship target restored: `pytest -W error::Warning` clean (2486 passed, 3 skipped). Per-site fix table in v0.1.13 RELEASE_PROOF §2.X at ship time. |
| **W-FBC-2** (F-B-04 recovery prototype + multi-domain runtime enforcement) | **closed-this-cycle** | W-FBC-2 (v0.1.13) | **Shipped at `bd11be3`.** Option A default per `reporting/docs/supersede_domain_coverage.md`: synthesis-side `--re-propose-all` carryover-uncertainty token enforcement on all 6 domains (recovery + running + sleep + stress + strength + nutrition). Three test files (+16 tests): P1/P5/P9 personas on recovery, parameterised multi-domain coverage, `hai today` rendering. Option B (per-domain fingerprint primitive) NOT shipped — runtime logic is domain-agnostic via `_carryover_token_for_domain()`, so the recovery prototype + multi-domain rollout sub-deliverables are one piece of code with the split living in test surface only. Option C (hybrid staleness signal) remains out-of-v0.1.x scope per F-PLAN-07. |
| **CP6 §6.3 framing edit application** | **closed-this-cycle** | CP6 application (v0.1.13) | **Shipped at `45319da` (batch 1).** Verbatim text edit per `v0_1_12/cycle_proposals/CP6.md` "Proposed delta": 4-element load-bearing-whole framing replaces 3-sentence DSL-as-moat framing at `reporting/plans/strategic_plan_v1.md` §6.3. v0.1.10-update line preserved unchanged per CP6 acceptance gate. |

## 2. Reconciliation §6 v0.1.13+ items (from v0.1.12 CARRY_OVER §3)

| Item | Disposition | W-id (this cycle) | Notes |
|---|---|---|---|
| **A1 trusted-first-value rename + C7 acceptance matrix** | **closed-this-cycle** | W-A1C7 (v0.1.13) | **Shipped at `45319da` (batch 1).** Acceptance matrix codified as contract test (`test_acceptance_matrix.py`); naming applied across docs/code. First time the workstream was fully scoped (v0.1.12 named the deferral without per-W-id contract). |
| **A5 declarative persona expected-actions** (W-AK pulled forward from v0.1.14) | **closed-this-cycle** | W-AK (v0.1.13) | **Shipped at `45319da` (batch 1) + revised at `ca0b986` (IR r1 F-IR-03 closure).** Initial implementation declared the `expected_actions` field on `verification/dogfood/personas/base.py::PersonaSpec` and auto-derived per-persona defaults in `__post_init__`; runner.py asserts actual recommendation matches. Codex IR round 1 F-IR-03 caught that the PLAN's per-persona declaration contract was satisfied by the base-class fallback only — not by inline declarations in each `p<N>_<slug>.py` file. The round-1 fix promoted the auto-derive logic to three public helpers (`established_expected_actions` / `day_one_expected_actions` / `established_forbidden_actions`) and added inline `expected_actions=` declarations to every one of the 12 packaged persona files (10 established personas use the defaults; P8 day-1 shape; P11 overrides stress to legitimately allow escalation per W-O). The base-class auto-derive remains as a safety net for future personas that forget to declare. New `test_every_persona_file_declares_expected_actions_inline` text-scan asserts each file carries the inline keyword. Precondition for v0.1.14 W58 prep is in place with the corrected per-persona ground-truth shape. |
| **C2 / W-LINT regulated-claim lint** | **closed-this-cycle** | W-LINT (v0.1.13) | **Shipped at `45319da` (batch 1).** `core/lint/regulated_claims.py` with static + runtime helpers; banned terms ("abnormal HRV", "clinical-grade", "biomarker", "risk score", "diagnose", etc); four-constraint exception path (allowlisted packaged skill + provenance citation + quoted/attributed context + CLI rendering boundary still strict); `expert-explainer` is the v0.1.13 ship-set allowlisted skill; `META_DOCUMENT_PRAGMA` carried by safety / reporting / expert-explainer. |
| **W-29-prep cli.py boundary audit** | **closed-this-cycle** | W-29-prep (v0.1.13) | **Shipped at `45319da` (batch 1).** `reporting/docs/cli_boundary_table.md` derived live from parser, not hardcoded; new `test_cli_parser_capabilities_regression.py` with byte-stability snapshots in `verification/tests/snapshots/cli_capabilities_v0_1_13.json` + `cli_help_tree_v0_1_13.txt` (frozen AFTER W-AB + W-AE intentional surface changes per F-PLAN-11). Two legitimate post-baseline snapshot regenerations, both within the W-29-prep design's intentional-drift envelope: (1) `03fab4f` for the W-AA `hai init --guided` surface; (2) `bd11be3` for the W-FBC-2 `--re-propose-all` help-text update at full closure. v0.1.14 W-29 has a clear go/no-go verdict per CP1; the mechanical split itself must not produce further snapshot drift. (Provenance corrected per v0.1.13 IR round 1 F-IR-05 — round 1 of `bd11be3`'s commit message and this row's pre-revision wording named only `bd11be3` as the post-baseline regeneration; on-disk git history confirmed `03fab4f` was the first of two.) |
| **L3 §6.3 strategic-plan framing edit (CP6)** | **closed-this-cycle** *(also covered by §1)* | CP6 application (v0.1.13) | **Shipped at `45319da` (batch 1).** Cross-reference row added at D14 round 1 per F-PLAN-02. The reconciliation source row (`v0_1_12/CARRY_OVER.md` §3 line 58) maps to the same CP6-application workstream that v0.1.12 RELEASE_PROOF §5 line names; recorded in §1 above with the canonical disposition + commit citation. Listed here too so this register's acceptance check #2 (every reconciliation §6 v0.1.13+ row disposed) is honest. |
| **W-FBC-2 (full F-B-04 multi-domain closure)** | **closed-this-cycle** *(also covered by §1)* | W-FBC-2 (v0.1.13) | **Shipped at `bd11be3`.** Cross-reference row added at D14 round 1 per F-PLAN-02. The reconciliation source row (`v0_1_12/CARRY_OVER.md` §3 line 59 — quoted "new W-id introduced by **v0.1.12 Codex F-PLAN-R2-04** in this cycle"; the bare token "F-PLAN-R2-04" in the source quote refers to the v0.1.12 D14 round-2 finding, NOT this cycle's F-PLAN-R2-04 which is the W-AD path-prefix miss — disambiguated at D14 round 3 per F-PLAN-R3-03) maps to the same W-FBC-2 workstream that v0.1.12 RELEASE_PROOF §5 names; recorded in §1 above with the canonical disposition + commit citation. Listed here too for honest acceptance-check coverage. |

## 3. Originally-planned v0.1.13 scope (tactical_plan §4.1)

These were scoped to v0.1.13 in the tactical plan authored
2026-04-27. Listed here for traceability — they're not
"carry-over" in the v0.1.12 sense, but they ARE part of v0.1.13
in-cycle scope, and a fresh agent reading the carry-over register
will look here for the full opening scope.

| Item | Disposition | W-id (this cycle) | Source |
|---|---|---|---|
| First-time-user onboarding flow | **closed-this-cycle** (`03fab4f`) | W-AA | tactical §4.1 |
| `hai capabilities --human` mode | **closed-this-cycle** (`45319da` batch 1) | W-AB | tactical §4.1 |
| README rewrite | **closed-this-cycle** (`45319da` batch 1) | W-AC | tactical §4.1 |
| Error-message quality pass | **closed-this-cycle** (`45319da` batch 1) | W-AD | tactical §4.1 |
| `hai doctor` expansion (incl. F-DEMO-01 detection prevention) | **closed-this-cycle** (`45319da` batch 1) | W-AE | tactical §4.1 + F-DEMO-01 prevention |
| README quickstart smoke test | **closed-this-cycle** (`45319da` batch 1) | W-AF | tactical §4.1 |
| `hai today` cold-start prose | **closed-this-cycle** (`45319da` batch 1) | W-AG | tactical §4.1 |

## 4. Reconciliation §6 v0.1.14+ items (named-defer pass-through)

These remain deferred to later cycles. Listed for traceability.

| Item | Defer to | Reason |
|---|---|---|
| **W-Vb-3** persona-replay extension to the 9 non-ship-set personas (P2/P3/P6/P7/P8/P9/P10/P11/P12) | v0.1.14 | fork-deferred at D14 round 1 per F-PLAN-06; scope clarified at D14 round 2 per F-PLAN-R2-02 — long-term universe is all 12 personas; v0.1.13 W-Vb closes 3 of 12 (P1+P4+P5); v0.1.14 W-Vb-3 covers the 9-persona residual (and may further partial-close). New row added 2026-04-30; expanded 2026-04-30 r2. |
| W-29 cli.py mechanical split | v0.1.14 | per CP1, conditional on W-29-prep verdict |
| L2 W-DOMAIN-SYNC scoped contract test | v0.1.14 | per Codex F-PLAN-09 |
| A12 judge-adversarial fixtures | v0.1.14 | folds into W-AI |
| A2/W-AL calibration scaffold | v0.1.14 | schema/report shape only |
| W-30 capabilities-manifest schema freeze | v0.2.0 | per CP2 |
| MCP server *plan* | v0.3 | per CP4 |
| MCP read-surface ship | v0.4 or v0.5 | per CP4 |
| W52 / W53 / W58 (weekly review + insight ledger + factuality gate) | v0.2.0 | strategic plan Wave 2 |

## 5. Pre-cycle ships absorbed in this PLAN

| Item | Where shipped | W-id (catalogue completeness) |
|---|---|---|
| **W-CF-UA** (intervals.icu Cloudflare User-Agent block fix) | **v0.1.12.1 hotfix** (branchpoint `v0.1.12` tag, three commits, lightweight RELEASE_PROOF at `reporting/plans/v0_1_12_1/RELEASE_PROOF.md`) | W-CF-UA (v0.1.13 PLAN §1.2 catalogue D — completeness only, NOT a v0.1.13 deliverable) |

The fix is also present in the `cycle/v0.1.13` branch via cherry-
pick from `hotfix/v0.1.12.1` (commit 636f5d3 carries the code +
test diff; commit a10a238 carries the lightweight RELEASE_PROOF
doc, cherry-picked in at D14 round 1 per F-PLAN-03 to make the
in-tree provenance citation honest). The hotfix branch + the cycle
branch both carry the identical code change at the file level; the
hotfix branch additionally carries the version bump (0.1.12 →
0.1.12.1) + CHANGELOG hotfix entry, neither of which propagates
into the cycle branch (cycle/v0.1.13 will eventually bump to 0.1.13).

## 6. Phase 0 (D11) findings absorbed

**Phase 0 ran 2026-04-30 at branch HEAD `57460a6`** (post-D14-r5
chain close). Pre-implementation gate fired green: 0 `aborts-cycle`,
0 `revises-scope`, 1 `in-scope`. See `audit_findings.md`.

| Finding | Cycle impact | Disposition |
|---|---|---|
| **F-PHASE0-01** (W-N-broader baseline -1 drift: 49 sites in v0.1.13 vs 50 in v0.1.12 audit) | in-scope (absorbed by W-N-broader, no PLAN.md revision) | **closed-this-cycle** at `6ea9ea4`. The 49-site authoritative file list satisfied the W-N-broader files-list contract prerequisite. Per-site fix table to land in v0.1.13 RELEASE_PROOF §2.X. |

## 7. Audit-chain integrity (cycle open)

- v0.1.12 demo isolation contract holds (validated at v0.1.12 ship;
  re-verify in Phase 0).
- 12-persona matrix at v0.1.12 ship: 0 findings, 0 crashes; re-run
  in Phase 0.
- Bandit `-ll` baseline at v0.1.12 ship: 46 Low, 0 Medium, 0 High.
  v0.1.13 target: ≤ 50 Low (D10), 0 Medium / High preserved.
- Capabilities byte-stability holds at v0.1.12 ship; will be locked
  by W-29-prep regression test in v0.1.13.

## 8. Settled-decision deltas expected at v0.1.13 ship

No new D-entries planned. CP6 (deferred application) lands as a
strategic-plan §6.3 verbatim edit; this is a wording change, not a
new settled decision. The four-element load-bearing-whole framing
is the substance.

W-29-prep produces the verdict that v0.1.14 W-29 gates on; the
verdict (split / do-not-split / split-with-revisions) is recorded
in v0.1.13 RELEASE_PROOF and may add a v0.1.14 rider in AGENTS.md
"Settled Decisions" but not a new D-entry.

---

## Acceptance check (W-CARRY)

- [x] Every line in `v0_1_12/RELEASE_PROOF.md` §5 has a disposition
  row in §1 above. **Verified 2026-04-30** — 4 source rows (W-Vb /
  W-N-broader / W-FBC-2 / CP6 application) → 4 disposition rows in
  §1, each carrying terminal disposition (`closed-this-cycle` or
  `partial-closure → v0.1.14 W-Vb-3`) and per-row commit citation.
- [x] Every reconciliation §6 v0.1.13+ item from `v0_1_12/CARRY_OVER.md`
  §3 has a row in **§2 (in-cycle items) or §4 (later-cycle pass-
  through items)**. Revised at D14 round 2 per F-PLAN-R2-03: the
  source table mixes v0.1.13 in-cycle work with explicitly-named
  v0.1.14+ defers; this register splits them across §2 + §4 by
  destination cycle, and the acceptance check now covers both.
  **Verified 2026-04-30** — 6 in-cycle reconciliation rows in §2 +
  9 fork-deferred rows in §4 cover the source table's contents.
- [x] Phase 0 findings absorbed in §6 (filled at cycle close).
  **Verified 2026-04-30** — F-PHASE0-01 closed at `6ea9ea4` via
  W-N-broader; gate fired green at HEAD `57460a6` with 0
  aborts-cycle / 0 revises-scope / 1 in-scope.
- [x] Pre-cycle ships (W-CF-UA) recorded in §5 with branchpoint +
  artifact references. **Verified 2026-04-30** — §5 cites the
  v0.1.12.1 hotfix branchpoint, the cherry-picked commits
  (`636f5d3` + `a10a238`) on this branch, and the lightweight
  RELEASE_PROOF at `reporting/plans/v0_1_12_1/RELEASE_PROOF.md`.

W-CARRY workstream deliverable: this document + acceptance checks
ticked at cycle close. **All four checks ticked 2026-04-30** by the
implementation-close disposition pass; this register is ready to
inform Codex IR round 1.

---

## 9. Summary-surface sweep — partial-closure trace

Per AGENTS.md "Summary-surface sweep on partial closure": when any
v0.1.13 workstream ships partial, every named summary surface must
move in lockstep. **One workstream shipped partial this cycle:**
**W-Vb** (P1+P4+P5 of 12 personas; 9 fork-deferred to v0.1.14
W-Vb-3). Other-cycle drift to verify at v0.1.13 RELEASE_PROOF time:

| Surface | Required state |
|---|---|
| `PLAN.md` §1.1 theme bullet | W-Vb language reflects "P1+P4+P5 ship-set" |
| `PLAN.md` §1.2 catalogue row | W-Vb row notes 9 fork-deferred personas |
| `PLAN.md` §1.3 deferral table | W-Vb-3 row pointing v0.1.14 destination |
| `PLAN.md` §2.A W-Vb contract | acceptance gates list 3 ship-set personas |
| `PLAN.md` §3 ship-gate row | demo-regression gate names ship-set personas only |
| `PLAN.md` §4 risks register | W-Vb risk row mentions partial-closure shape |
| **`RELEASE_PROOF.md` §1** | W-Vb status `partial-closure → v0.1.14 W-Vb-3`, NOT `shipped` |
| **`RELEASE_PROOF.md` §5** | W-Vb-3 line for the 9-persona residual |
| **`REPORT.md` §3 / §4 / §6** | W-Vb listed as partial-closure highlight + deferral + lesson |
| **CARRY_OVER.md** §1 + §4 | already done in this register (rows are the canonical source) |
| `ROADMAP.md` "Now" / "Next" | v0.1.14 row mentions W-Vb-3 |
| `tactical_plan_v0_1_x.md` §3.x + §4 | v0.1.14 next-cycle row reflects W-Vb-3 |
| `CHANGELOG.md` v0.1.13 entry | W-Vb partial-closure language; no implication of full closure |
| `reporting/docs/<workstream>.md` design docs | none for W-Vb (no per-WS design doc) |
| CLI help text | no impact (W-Vb is fixture/test surface, not CLI) |

The trace above is for the v0.1.13 RELEASE_PROOF / REPORT
authoring step; all CARRY_OVER-side rows are honest as of
2026-04-30.

**No other v0.1.13 workstream shipped partial.** W-FBC-2 closed
fully (option A applies to all 6 domains; the documented option-B
fork was not selected). W-N-broader closed fully (broader-gate
green). CP6 application closed fully. Every originally-planned
workstream (W-AA through W-AG) closed fully. Every reconciliation
v0.1.13+ item closed fully (W-A1C7 / W-AK / W-LINT / W-29-prep).
The 9 v0.1.14+ pass-through items in §4 are pre-existing
fork-defers, not new this cycle.
