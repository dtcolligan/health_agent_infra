# Roadmap

Now, next, and later. **The release-by-release plan of record lives in
[`reporting/plans/tactical_plan_v0_1_x.md`](reporting/plans/tactical_plan_v0_1_x.md)**
(next 6-8 releases) and the longer-horizon strategy in
[`reporting/plans/strategic_plan_v1.md`](reporting/plans/strategic_plan_v1.md).
The earlier
[`reporting/plans/historical/multi_release_roadmap.md`](reporting/plans/historical/multi_release_roadmap.md)
is superseded as of 2026-04-27.

This file is a high-level pointer; for actual scope, read those plans.

## Now

- **v0.1.15.1 shipped (2026-05-03).** Hotfix: Linux keyring
  fall-through hardening after CI surfaced `NoKeyringError` on runners
  without a registered backend. Adds `keyrings.alt`, defensive
  `_default_backend()` fallback, README install hardening, and public
  candidate-name scrub. Schema head unchanged at 25.
  See [`reporting/plans/v0_1_15_1/RELEASE_PROOF.md`](reporting/plans/v0_1_15_1/RELEASE_PROOF.md).
- **v0.1.15 shipped (2026-05-03).** Foreign-user-ready package.
  Six W-ids (W-GYM-SETID gym set-id PK collision fix; F-PV14-01
  CSV-fixture default-deny; W-A `hai intake gaps` presence block +
  is_partial_day + target_status; W-C `hai target nutrition` 4-row
  macro convenience over the existing target table; W-D arm-1
  nutrition partial-day suppression; W-E merge-human-inputs skill
  presence-block consumption). Migration head 23 → 25. The W-2U-GATE
  recorded session reframes from ship-gate to empirical-validation
  feeding v0.1.16 per the publish-first pivot — the named foreign-user
  candidate now installs `health-agent-infra==0.1.15.1` after the Linux
  keyring hotfix. Audit chain:
  D14 12→7→3→2 (4 rounds + Phase 0 revises-scope round) + D15 IR
  6→2→1 (3 rounds, SHIP_WITH_NOTES close-in-place). Substantive tier.
  Test surface: 2631 passed, 3 skipped (+50 vs v0.1.14.1).
  See [`reporting/plans/v0_1_15/RELEASE_PROOF.md`](reporting/plans/v0_1_15/RELEASE_PROOF.md).
- **v0.1.14.1 shipped (2026-05-02).** Hardening cycle: Garmin-live
  unreliability surfaced as a structured capabilities signal. Single
  workstream (W-GARMIN-MANIFEST-SIGNAL). `hai capabilities --json`
  exposes `commands[hai pull].flags[--source].choice_metadata.garmin_live.reliability == "unreliable"`
  (plus `reason` + `prefer_instead`); `_resolve_pull_source` emits a
  stderr warning at resolution time when the resolved source is
  `garmin_live`. Purely additive — manifest `schema_version` unchanged.
  Audit chain abbreviated per D15 hardening latitude (no external
  Codex IR). Test surface: 2581 passed (+15 vs v0.1.14).
  See [`reporting/plans/v0_1_14_1/RELEASE_PROOF.md`](reporting/plans/v0_1_14_1/RELEASE_PROOF.md).
- **v0.1.14 shipped (2026-05-01).** Eval substrate + provenance +
  recovery path. 13 W-ids at PLAN open (post-W-2U-GATE-defer): 8
  closed, 3 partial-closed with named v0.1.15 destinations
  (W-AH / W-AI / W-Vb-3), 2 deferred (W-2U-GATE / W-29), 1 absorbed
  (W-AM into W-AI). Substrate-first sequencing: W-PROV-1 source-row
  locator, W-AJ judge-harness scaffold, W-AL FActScore-aware
  calibration schema — v0.2.0 W52 + W58D + v0.2.2 W58J consume these
  without re-design. Plus W-BACKUP `hai backup` / `hai restore` /
  `hai export` recovery path; W-EXPLAIN-UX maintainer-substitute
  review with 8 findings + 6 v0.2.0 W52 prose obligations + carries-
  forward-to-v0.1.15 section; W-DOMAIN-SYNC contract test;
  W-FRESH-EXT extension + F-PHASE0-01 persona-runner pre-flight
  absorption. D14 settled at round 4 with the 12 → 7 → 3 → 1-nit →
  CLOSE signature (twice-validated). IR closed at round 3
  SHIP_WITH_NOTES. Test surface: 2566 passed (+73 vs v0.1.13).
  See [`reporting/plans/v0_1_14/RELEASE_PROOF.md`](reporting/plans/v0_1_14/RELEASE_PROOF.md).
- **v0.1.13 shipped (2026-04-30).** Largest cycle in the v0.1.x track
  at 17 workstreams. Closed all v0.1.12 named-deferred items
  (W-Vb persona-replay end-to-end for P1+P4+P5 ship-set, W-N-broader
  50-site sqlite3 leak fix, W-FBC-2 multi-domain F-B-04 closure,
  CP6 §6.3 strategic-plan edit). Shipped the originally-planned
  onboarding scope (`hai init --guided`, `hai capabilities --human`,
  `hai doctor --deep`, `hai today` cold-start prose, README rewrite
  + smoke test, every USER_INPUT exit code carries actionable
  next-step prose). Landed governance prerequisites (W-29-prep
  cli.py boundary audit, W-LINT regulated-claim lint, W-AK
  declarative persona expected-actions, W-A1C7 acceptance matrix).
  See [`reporting/plans/v0_1_13/RELEASE_PROOF.md`](reporting/plans/v0_1_13/RELEASE_PROOF.md).

## Next

- **v0.1.16 — empirical post-publish validation fixes.** The named foreign-user candidate's
  recorded session runs against `health-agent-infra==0.1.15.1` from
  PyPI. PLAN.md authors after the transcript exists. Expected scope:
  P1/P2 fixes from the session, W-EXPLAIN-UX-2 (`hai explain`
  foreign-user pass), and conditional W-FPV14-SYM if asymmetric
  `--db-path` / `--base-dir` friction appears. **Ship claim:**
  empirical findings consolidated.
- **v0.1.17 — maintainability + eval consolidation.** W-29 cli.py
  mechanical split, W-30 regression prep, W-AH-2 scenario expansion,
  W-AI-2 `hai eval review`, W-AM-2 fork-deferred scenarios, W-Vb-4
  persona residuals, F-PV14-02 `hai sync purge`, W-B body-comp intake,
  W-D arm-2, and W-C-EQP query-plan assertions. **Ship claim:**
  internal correctness and maintainer-side cleanup.
- **v0.2.0 — weekly review + deterministic factuality (Path A
  release 1 of 4).** W52 weekly review with source-row locators
  (uses v0.1.14 W-PROV-1), W58D deterministic claim-block (blocking
  from day 1), W-FACT-ATOM atomic decomposition, plus 4 doc-only
  adjuncts (W-MCP-THREAT, W-COMP-LANDSCAPE, W-NOF1-METHOD,
  W-2U-GATE-2 second foreign-machine session, sequenced after the
  v0.1.15 foreign-user candidate session and v0.1.16 empirical-fix consolidation).
  One schema group per release (honors C6).
- **v0.2.1 — insight ledger (Path A release 2 of 4).** W53 only;
  one schema group.
- **v0.2.2 — LLM judge shadow-by-default (Path A release 3 of 4).**
  W58J + W-JUDGE-BIAS bias panel. One schema group.
- **v0.2.3 — judge promotion to blocking + W-30 capabilities-
  manifest schema freeze (Path A release 4 of 4).** No new schema.
- **v0.3+ — MCP staging.** v0.2.0 W-MCP-THREAT artifact (per
  CP-MCP-THREAT-FORWARD) precedes v0.3 design. v0.3 plans MCP
  server (read-surface design + provenance import contract). v0.4
  prereqs land (least-privilege scope model + threat-model
  completion). v0.4-or-v0.5 ships MCP read surface. **No write
  surface ever.** Per CP4.
- **v0.5+ — calibration substrate.** Read-only UI decision-checkpoint
  (per existing strategic plan).

## Later

- **v0.6 — personal-evidence estimator.** Reads 90+ days of v0.5 triples
  and produces per-user effect estimates with explicit uncertainty.
- **v0.7 — governed adaptation.** LLM proposes structured threshold
  mutations citing estimator output; user approves or rejects.
- **v1.0 — stable contract.** Acceptance requires at least three months of
  zero-incident operation after v0.7.

## Explicitly Out Of Scope

- Hosted multi-user product.
- Web/mobile/dashboard frontend.
- Meal-level nutrition, food taxonomy, or micronutrient inference in v1.
- Clinical claims or diagnosis-shaped language.
- Hidden learning loop or automatic threshold mutation from outcomes.

Full non-goals are in
[`reporting/docs/non_goals.md`](reporting/docs/non_goals.md).

## Dependency Chain

```text
v0.1.13 onboarding + governance prereqs (shipped 2026-04-30)
    -> v0.1.14 eval substrate + provenance + recovery path (8 W-ids closed; W-29 deferred) (shipped 2026-05-01)
        -> v0.1.14.1 hardening: garmin_live structured-signal trap (shipped 2026-05-02)
            -> v0.1.15 publish-first package (published 2026-05-03)
                -> v0.1.15.1 Linux keyring hotfix
                    -> v0.1.16 empirical fixes from the named foreign-user candidate's post-publish session
                        -> v0.1.17 maintainability + eval consolidation
                            -> v0.2.0 W52 weekly review + W58D deterministic factuality (Path A 1/4)
                                -> v0.2.1 W53 insight ledger (Path A 2/4)
                                    -> v0.2.2 W58J LLM judge shadow + W-JUDGE-BIAS panel (Path A 3/4)
                                        -> v0.2.3 W58J promote to blocking + W-30 capabilities freeze (Path A 4/4)
                                            -> v0.3 MCP plan (consumes v0.2.0 W-MCP-THREAT artifact)
                                                -> v0.4 MCP prereqs (least-privilege scope + threat-model done)
                                                    -> v0.4-or-v0.5 MCP read surface ships
                                                    -> v0.5 N-of-1 substrate (read-only UI decision-checkpoint)
                                                         -> 90+ days of accumulated triples
                                                         -> v0.6 personal-evidence estimator
                                                             -> v0.7 governed adaptation
                                                                 -> 3+ months zero-incident
                                                                 -> v1.0 stable contract
```

The Path A 4-release v0.2.x split (CP-PATH-A) honors reconciliation
C6 (one conceptual schema group per release). See
`reporting/plans/post_v0_1_13/cycle_proposals/CP-PATH-A.md` for the
full rationale.

The five bets behind this sequence are in [HYPOTHESES.md](HYPOTHESES.md).
If a falsification signal fires, the affected release gets re-scoped before
it ships.
