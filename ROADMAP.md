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

- **v0.1.13 shipped (2026-04-30).** Largest cycle in the v0.1.x track
  at 17 workstreams. Closed all v0.1.12 named-deferred items
  (W-Vb persona-replay end-to-end for P1+P4+P5 ship-set, W-N-broader
  50-site sqlite3 leak fix, W-FBC-2 multi-domain F-B-04 closure with
  per-domain carryover-uncertainty token, CP6 §6.3 strategic-plan
  edit). Shipped the originally-planned onboarding scope (`hai init
  --guided`, `hai capabilities --human`, `hai doctor --deep`,
  `hai today` cold-start prose, README rewrite + smoke test, every
  USER_INPUT exit code carries actionable next-step prose). Landed
  governance prerequisites (W-29-prep cli.py boundary audit,
  W-LINT regulated-claim lint, W-AK declarative persona
  expected-actions, W-A1C7 acceptance matrix). D14 settled at
  round 5 with the 11 → 7 → 3 → 1-nit → 0 signature; Codex IR
  closed at round 3 with 6 → 2 → 0 (cleaner than the empirical
  norm). See
  [`reporting/plans/v0_1_13/RELEASE_PROOF.md`](reporting/plans/v0_1_13/RELEASE_PROOF.md).
- **v0.1.14 open (D14 PLAN_COHERENT closed at round 4 2026-05-01;
  Phase 0 (D11) gate fired green 2026-05-01;
  W-2U-GATE deferred to v0.1.15 at pre-implementation gate per
  PLAN.md §1.3.1 path 2 — 13 W-ids post-defer).** Eval substrate
  (W-AH/W-AI/W-AJ/W-AL/W-AM/W-AN) + inherited W-29 / W-Vb-3 /
  W-DOMAIN-SYNC + 4 P0/P1 additions from post-v0.1.13 strategic
  research (W-PROV-1 source-row locator, W-EXPLAIN-UX `hai explain`
  UX review with maintainer-substitute reader, W-BACKUP
  backup/restore/export, W-FRESH-EXT doc-freshness extension +
  persona-runner demo-session pre-flight). W-PROV-1 sequenced first
  post-defer.

## Next

- **v0.1.14 open — eval substrate + cli.py split + W-Vb-3 + 4 P0/P1
  additions (13 W-ids post-defer, 30-43 days).** Detailed scope in
  `reporting/plans/tactical_plan_v0_1_x.md` §5; PLAN +
  `pre_implementation_gate_decision.md` under
  `reporting/plans/v0_1_14/`.
- **v0.1.15 — W-2U-GATE foreign-machine onboarding empirical proof
  (carry-forward from v0.1.14 pre-implementation gate defer) +
  scope TBD.** Cycle authoring after v0.1.14 ship.
- **v0.2.0 — weekly review + deterministic factuality (Path A
  release 1 of 4).** W52 weekly review with source-row locators
  (uses v0.1.14 W-PROV-1), W58D deterministic claim-block (blocking
  from day 1), W-FACT-ATOM atomic decomposition, plus 4 doc-only
  adjuncts (W-MCP-THREAT, W-COMP-LANDSCAPE, W-NOF1-METHOD,
  W-2U-GATE-2). One schema group per release (honors C6).
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
    -> v0.1.14 eval substrate + cli.py split + W-Vb-3 + 5 P0/P1 additions (14 W-ids)
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
