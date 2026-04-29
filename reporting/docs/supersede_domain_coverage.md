# Supersede domain-coverage policy (F-B-04)

**Status:** v0.1.12 W-FBC — design + recovery prototype + override flag.
**Multi-domain closure:** deferred to v0.1.13 W-FBC-2 (named-defer per
PLAN.md §1.3 and Codex F-PLAN-R2-04).
**Author:** v0.1.12 cycle.

---

## Problem (F-B-04, deferred from v0.1.11)

When a `hai daily --supersede` re-run produces a `_v<N>` plan, which
domains carry over their existing proposals from `proposal_log` and
which re-emit?

The pre-v0.1.12 contract was implicit: synthesis read whatever was in
`proposal_log` at the moment of the supersede call, regardless of
whether the proposing skill had re-authored proposals for the domain.
A skill that re-authored only the recovery proposal between v1 and v2
would produce a v2 plan whose recovery section reflected fresh state
but whose other five sections were the original v1 proposals
re-rendered. Whether that's correct depends on whether the
state-change that triggered supersede actually invalidated the
non-recovery proposals.

There was no contract naming the policy. F-B-04 named the gap.

## Decision

**Default policy: option A (all domains re-propose).** The cleanest
semantic — supersede is a strong signal that the input state has
changed; treating every domain as needing fresh judgment costs
slightly more compute but avoids carrying stale skill-rationale
across a state delta.

Two alternatives were considered and deferred:

- **Option B** (only changed-input domains re-propose). More efficient
  — skip re-authoring for domains whose inputs didn't change. Requires
  a per-domain input fingerprint primitive that does not exist today
  (`core/synthesis.py`'s fingerprint is global per Codex F-PLAN-07).
  Building per-domain fingerprints is real work; deferred to v0.1.13
  W-FBC-2 if option B is chosen there.

- **Option C** (hybrid — staleness signal carried through
  `proposal_log`). Requires schema work. Not in scope for v0.1.x.

Option A's default disposition can be overridden per-call via the
`--re-propose-all` flag on `hai daily`. The flag is the explicit
escape hatch for an operator who wants belt-and-braces behavior even
in a runtime that has not yet enforced option A across all domains
(i.e. the v0.1.12 partial-closure state).

## v0.1.12 partial closure

This cycle delivers:

1. **This document** — names the chosen policy with rationale.
2. **The `--re-propose-all` CLI flag** on `hai daily`. Always
   accepted; capabilities-surfaced. Today the flag has *partial*
   runtime effect: the recovery domain (the one-domain prototype)
   honors it; the other five domains pass through unchanged. v0.1.13
   W-FBC-2 lifts the enforcement to all six.
3. **Recovery prototype:** when `--re-propose-all` is set and the
   recovery proposal in `proposal_log` for the target `for_date` was
   authored before the current `now` minus a threshold (default: 1
   minute, treats anything older as "carried over from a prior run"),
   synthesis emits a `recovery_proposal_carryover_under_re_propose_all`
   uncertainty token in the canonical recommendation row.
4. **Tests covering three persona scenarios**:
   - P1 (Dom baseline) — morning fresh-state supersede; flag set;
     fresh proposals authored within session; no carryover token.
   - P5 (female multi-sport) — thin-history with state delta;
     flag set; recovery proposal NOT re-authored; carryover token
     fires for recovery.
   - P9 (older female endurance) — supersede-after-intake-change
     baseline; flag absent; no carryover token regardless of
     timing (default policy stays implicit).

## Forward-compat to v0.1.13 W-FBC-2

W-FBC-2 lifts:

- Option-A enforcement to all six domains, not just recovery.
- If option B is chosen at W-FBC-2 design, the per-domain
  fingerprint primitive is the additional surface that ships there
  (the v0.1.12 fingerprint is global; per-domain requires breaking
  out the upstream state surfaces by domain).

The acceptance gate for W-FBC-2 is multi-domain coverage in the
persona matrix — every domain emits the carryover signal under the
same conditions.

## What this document is not

This is not a one-line addition to `synthesis_policy.py`. The W-E
state-fingerprint contract already determines *whether* supersede
fires. F-B-04 / W-FBC governs *what behavior the supersede produces
across domains* once it fires. The two seams are independent.

This is also not a clinical or recommendation-shape claim. The
policy is purely about whether stale rationale prose can survive a
state-change boundary. Recommendation content is downstream.
