# Roadmap

Now, next, and later. The full release-by-release plan, dependencies, risks,
and bibliography live in
[`reporting/plans/multi_release_roadmap.md`](reporting/plans/multi_release_roadmap.md).

## Now

- **v0.1.8 current.** Plan-aware feedback visibility. Intent + target +
  data-quality ledgers, code-owned review-summary tokens, `hai stats`
  outcomes/baselines/funnel/data-quality modes, config validate + diff,
  `hai daily --auto --explain`, and synthesis-skill scoring. Closed four
  audit rounds; see [AUDIT.md](AUDIT.md).
- **v0.1.9 next.** Weekly review, insight proposal ledger, and an LLM
  factuality gate with an agent-judge negotiation loop. Also carries the
  v0.1.8 backlog notes: global threshold-runtime type hardening and pytest
  unraisable warning cleanup.

## Next

- **v0.2 - visualization artifacts + BCTO.** Artifact ledger, reproducible
  chart/report commands, and Behaviour Change Technique Ontology tags on
  recommendations.
- **v0.3 - extension contracts + data-quality drift detection.** Domain and
  adapter contribution contracts, vendor algorithm drift detection,
  per-metric calibration progress, multi-source reconciliation blocks, and
  first-run UX triad (`hai init`, `hai demo`, `hai next-step --json`).
- **v0.4 - runtime portability + cryptographic provenance.** MCP server over
  governed proposal/stat surfaces, encrypted state DB, signed append-only
  audit log, and optional local-LLM pathway.
- **v0.5 - personal evidence ledger + N-of-1 substrate.** Experiment ledger
  and deterministic single-user analysis substrate. This starts the clock
  for v0.6; the estimator needs at least 90 days of accumulated triples.

## Later

- **v0.6 - personal-evidence estimator.** Reads 90+ days of v0.5 triples and
  produces per-user effect estimates with explicit uncertainty.
- **v0.7 - governed adaptation.** LLM proposes structured threshold
  mutations citing estimator output; user approves or rejects.
- **v1.0 - stable contract.** Acceptance requires at least three months of
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
v0.1.9 weekly review
    -> v0.2 artifacts/BCTO
    -> v0.3 extension contracts + data-quality drift + first-run UX
    -> v0.4 MCP/provenance
    -> v0.5 N-of-1 substrate
         -> 90+ days of accumulated triples
         -> v0.6 estimator
             -> v0.7 governed adaptation
                 -> 3+ months zero-incident
                 -> v1.0 stable contract
```

The five bets behind this sequence are in [HYPOTHESES.md](HYPOTHESES.md).
If a falsification signal fires, the affected release gets re-scoped before
it ships.
