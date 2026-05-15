# Phase 0 preflight capture (historical)

This directory holds the single end-to-end recovery-readiness loop
captured during the Phase 0 preflight on 2026-04-17, before the v1
multi-domain rebuild started.

It is **historical**. The runtime contracts the captures reference
(`recovery_state` shape, single-domain CLI chain, no synthesis layer)
no longer match the shipped v1 system. Do not cite these files as
current truth.

## What this proved

Phase 0 was a "delay gate" check: does the existing single-domain
flagship loop run cleanly enough that the rebuild can proceed
without first stopping to fix it? Verdict: yes — see
[`../../plans/historical/phase_0_findings.md`](../../plans/historical/phase_0_findings.md)
for the prose write-up and the gate decision.

## Where current proof lives

For the current multi-domain runtime, see
[`../flagship_loop_proof/2026-04-18-multi-domain-evals/`](../flagship_loop_proof/2026-04-18-multi-domain-evals/),
which captures all 28 deterministic eval scenarios across the six v1
domains plus synthesis.

For other pre-rebuild bundles, see
[`../archive/`](../archive/).
