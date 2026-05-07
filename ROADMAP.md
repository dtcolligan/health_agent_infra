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

- **v0.2.0 ship-prep complete (2026-05-07; PyPI publish pending D15
  IR + maintainer manual TTY gate).** Wave 2 gateway: provenance +
  weekly review + deterministic factuality. 11 W-ids closed
  (W-PROV-2, W-EVCARD-DAILY, W-EVCARD-WEEKLY, W52, W-FACT-ATOM,
  W58D, W-MCP-THREAT, W-COMP-LANDSCAPE, W-NOF1-METHOD,
  W-EXPLAIN-UX-CARRY); W-2U-GATE-2 did NOT fire (opportunistic-
  not-blocking per D16). New surface: `hai review weekly` (markdown
  + JSON, abstain branch, supersession reconciliation, data-quality
  rollup, claim-card emission, W58D gate by default). Schema head
  26 → 28 (migrations 027 daily evidence card + 028 weekly claim
  card). **Empirical: factuality corpus 100/100 vs 97/99 thresholds;
  parser precision 100% over 30-fixture corpus; persona matrix 13/13
  with 0 findings + 0 crashes.** Test surface: 2,940 passed, 4
  skipped (broader warning gate; +184 vs v0.1.18 baseline of 2,756,
  exceeded the +86 floor 2.1×).
  See [`reporting/plans/v0_2_0/RELEASE_PROOF.md`](reporting/plans/v0_2_0/RELEASE_PROOF.md).
- **v0.1.17 shipped (2026-05-05).** Maintainability + eval-substrate
  consolidation. 10 W-ids closed at 100% acceptance: W-29 cli.py
  9,927 LOC mechanical split into 1 main + 1 shared + 11 handler-group
  modules (each <2,500 LOC; manifest byte-stable); W-30 capabilities-
  manifest schema regression test (freeze itself remains v0.2.3);
  W-AH-2 scenario fixture corpus 35 → 135 across six domains +
  synthesis (100% pass-rate); W-AI-2 `hai eval review` CLI surface
  (list/show/tag/dismiss/export); W-AM-2 4 escalate-tagged adversarial
  scenarios (cumulative 6/6); W-Vb-4 12-of-12 persona closure +
  P13 matrix-only; W-B `hai intake weight` + `body_comp` table +
  migration 026; W-D arm-2 partial-day end-of-day macro projection;
  W-C-EQP migration 025 query-plan stability assertion; F-PV14-02
  `hai sync purge` surgical-cleanup CLI. Schema head 25 → 26.
  Audit chain: D14 11 → 5 → 3 → CLOSE (3 rounds, halving signature
  thrice-validated); D15 IR 6 → 1-nit (2 rounds, SHIP_WITH_NOTES
  close-in-place). Substantive tier. Test surface: 2,683 passed,
  4 skipped (+52 vs v0.1.15.1).
  See [`reporting/plans/v0_1_17/RELEASE_PROOF.md`](reporting/plans/v0_1_17/RELEASE_PROOF.md).
- **v0.1.18 ship-prep complete (2026-05-06; PyPI publish pending D15
  IR + maintainer manual TTY gate).** Onboarding-quality + intake-
  handler migration parity. 7 W-ids closed: W-OB-1 (README pivot
  ratified), W-OB-2 (`hai init` interactive default with
  `--non-interactive` + `HAI_INIT_NON_INTERACTIVE=1` opt-outs;
  release-blocker leg of substantive tier), W-OB-3 (`--guided` post-
  prompt `next_action_hint` + skip-input affordance tests), W-OB-4a
  (Phase 1 upgrade dogfood — F-OB-PRE-01 verified end-to-end),
  W-OB-4b (Phase 2 local-wheel smoke — both opt-out paths verified;
  TTY UX deferred to maintainer manual gate), W-OB-5 (`hai doctor
  next_action` across hint-emitting checks with manifest-consistency
  invariant), W-OB-7 (intake-handler migration parity — additive
  `open_connection_with_migrations` helper closing F-OB-PRE-01).
  W-OB-6 conditional did NOT fire. Schema head unchanged at 26.
  Test surface: 2,722 passed, 5 skipped (broader warning gate).
  D14 7 → 3 close-in-place (one round earlier than substantive norm).
  See [`reporting/plans/v0_1_18/RELEASE_PROOF.md`](reporting/plans/v0_1_18/RELEASE_PROOF.md).
- **v0.1.19 cancelled (2026-05-06)** per CP-2U-GATE-SPLIT
  (`reporting/plans/post_v0_1_18/CP-2U-GATE-SPLIT.md`) + AGENTS.md
  D16. Foreign-user empirical scope re-tiered to
  opportunistic-not-blocking; W-2U-INSTALL closed verbal-only by
  the post-v0.1.18 maintainer's-father session; W-2U-WEARABLE +
  W-2U-DOGFOOD (≥7d daily non-maintainer use) deferred to v0.4
  review. See [`reporting/plans/v0_1_19/README.md`](reporting/plans/v0_1_19/README.md).
- **v0.2.1 next-active (insight ledger).** W53 multi-week insight
  persistence; one schema group. **Hard deps:** v0.2.0 W52 weekly-
  review surface + W58D factuality gate, both shipped 2026-05-07.
- **v0.1.16 cancelled (2026-05-04).** The named foreign-user candidate
  became unavailable; empirical scope renumbered to v0.1.19 (which
  itself was cancelled 2026-05-06).
  See [`reporting/plans/v0_1_16/README.md`](reporting/plans/v0_1_16/README.md).
- **v0.1.15.1 shipped (2026-05-03).** Hotfix: Linux keyring
  fall-through hardening; adds `keyrings.alt` and defensive
  `_default_backend()` fallback. Schema head unchanged at 25.
  See [`reporting/plans/v0_1_15_1/RELEASE_PROOF.md`](reporting/plans/v0_1_15_1/RELEASE_PROOF.md).
- **v0.1.15 shipped (2026-05-03).** Foreign-user-ready package.
  Six W-ids (W-GYM-SETID, F-PV14-01, W-A presence block, W-C target
  nutrition, W-D arm-1, W-E merge-human-inputs). Migration head
  23 → 25. Substantive tier. Test surface: 2,631 passed.
  See [`reporting/plans/v0_1_15/RELEASE_PROOF.md`](reporting/plans/v0_1_15/RELEASE_PROOF.md).
- **v0.1.14.1 shipped (2026-05-02).** Hardening: Garmin-live
  unreliability surfaced as a structured capabilities signal
  (W-GARMIN-MANIFEST-SIGNAL).
  See [`reporting/plans/v0_1_14_1/RELEASE_PROOF.md`](reporting/plans/v0_1_14_1/RELEASE_PROOF.md).
- **v0.1.14 shipped (2026-05-01).** Eval substrate + provenance +
  recovery path (W-PROV-1 source-row locator, W-BACKUP, W-AJ judge
  harness, W-AL calibration schema, W-EXPLAIN-UX, etc.).
  See [`reporting/plans/v0_1_14/RELEASE_PROOF.md`](reporting/plans/v0_1_14/RELEASE_PROOF.md).
- **v0.1.13 shipped (2026-04-30).** Largest cycle to date at 17 W-ids;
  guided onboarding (`hai init --guided`), `hai doctor --deep`,
  regulated-claim lint, `hai today` cold-start prose, USER_INPUT
  actionable-prose sweep.
  See [`reporting/plans/v0_1_13/RELEASE_PROOF.md`](reporting/plans/v0_1_13/RELEASE_PROOF.md).

## Next

- **v0.2.1 — insight ledger (Path A release 2 of 4).** **Next-
  active cycle.** W53 multi-week insight persistence; one schema
  group. Hard deps: v0.2.0 W52 + W-EVCARD-WEEKLY substrate, both
  shipped.
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
    -> v0.1.14 eval substrate + provenance + recovery path (shipped 2026-05-01)
        -> v0.1.14.1 hardening: garmin_live structured-signal trap (shipped 2026-05-02)
            -> v0.1.15 publish-first package (shipped 2026-05-03)
                -> v0.1.15.1 Linux keyring hotfix (shipped 2026-05-03)
                    -> [v0.1.16 CANCELLED 2026-05-04 — foreign-user candidate unavailable]
                    -> v0.1.17 maintainability + eval consolidation (shipped 2026-05-05)
                        -> v0.1.18 onboarding-quality cycle (shipped 2026-05-06)
                            -> [v0.1.19 CANCELLED 2026-05-06 — CP-2U-GATE-SPLIT (D16); foreign-user empirical re-tiered to opportunistic-not-blocking]
                            -> v0.2.0 W52 weekly review + W58D deterministic factuality (Path A 1/4)
                                -> v0.2.1 W53 insight ledger (Path A 2/4)
                                    -> v0.2.2 W58J LLM judge shadow + W-JUDGE-BIAS panel (Path A 3/4)
                                        -> v0.2.3 W58J promote to blocking + W-30 capabilities freeze (Path A 4/4)
                                            -> v0.3 MCP plan (consumes v0.2.0 W-MCP-THREAT artifact)
                                                -> v0.4 MCP prereqs (least-privilege scope + threat-model done; W-2U-WEARABLE + W-2U-DOGFOOD re-evaluation gate per D16)
                                                    -> v0.4-or-v0.5 MCP read surface ships
                                                    -> v0.5 N-of-1 substrate (read-only UI decision-checkpoint)
                                                         -> 90+ days of accumulated triples
                                                         -> v0.6 personal-evidence estimator
                                                             -> v0.7 governed adaptation
                                                                 -> 3+ months zero-incident
                                                                 -> v1.0 stable contract
```

v0.2.0 hard deps post-D16: **v0.1.14 substrate (W-PROV-1 + W-AJ
judge harness), already shipped.** Foreign-user empirical evidence
re-tiered to opportunistic-not-blocking per CP-2U-GATE-SPLIT.
v0.2.0 is parallelizable with v0.1.17/v0.1.18 maintainability work.

The Path A 4-release v0.2.x split (CP-PATH-A) honors reconciliation
C6 (one conceptual schema group per release). See
`reporting/plans/post_v0_1_13/cycle_proposals/CP-PATH-A.md` for the
full rationale.

The five bets behind this sequence are in [HYPOTHESES.md](HYPOTHESES.md).
If a falsification signal fires, the affected release gets re-scoped before
it ships.
