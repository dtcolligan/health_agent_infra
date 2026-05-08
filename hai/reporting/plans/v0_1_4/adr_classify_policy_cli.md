# ADR — `hai classify` / `hai policy` debug CLIs

- Author: Claude (Opus 4.7) with Dom Colligan
- Decided: 2026-04-24
- Status: **ratified** — delete both commands in v0.1.4 D4.
- Tracks: v0.1.4 acceptance criterion #11.

---

## Problem

`hai classify --domain <d> --evidence-json <p>` and `hai policy
--domain <d> --evidence-json <p>` predate the per-domain
``state snapshot`` block. They evaluate recovery classify + policy
against a cleaned evidence JSON file and print the result. Both
commands are:

- Recovery-only (despite the `--domain` flag). The handler
  unconditionally calls `classify_recovery_state` / `evaluate_recovery_policy`
  and rejects any non-recovery value of `--domain` with a `USER_INPUT`
  error. Extending them to every domain would mean adding per-domain
  dispatch tables for both classify and evaluate paths — duplicating
  the logic that already lives in `core/state/snapshot.py`'s
  `build_snapshot` + `evidence_bundle` expansion.
- Redundant with ``hai state snapshot --evidence-json``, which emits
  `classified_state` + `policy_result` for every domain in one call
  from an already-cleaned evidence bundle.
- Under-tested relative to the snapshot path (no integration test
  asserts parity between `hai classify` output and the snapshot
  block; if the two drift, only one is audited).

---

## Options considered

**(a) Extend to all six domains.** Add per-domain dispatch for
classify + policy, keep the commands. Cost: ~200 lines of handler
dispatch + tests, maintenance burden mirroring the snapshot
expansion, and an entry-point into domain internals that the agent
contract doesn't need.

**(b) Delete both commands and redirect to ``hai state snapshot
--evidence-json``.** Cost: minor — scrub the two handlers + parser
blocks + their tests, add a line to the doc that mentions them.
Benefit: one source of truth for per-domain classify/policy output;
no more recovery-only surface hiding behind a `--domain` flag.

**(c) Keep them but mark recovery-only explicitly.** Cost: low.
Benefit: minimal — a debug surface that only works for one domain
is a drift hazard the moment a domain-specific bug gets investigated
for running / strength.

---

## Decision

**(b). Delete ``hai classify`` and ``hai policy``.** The snapshot
surface subsumes both commands; shipping v0.1.4 with two
recovery-only debug CLIs that look like they work for every domain
is exactly the class of agent-contract drift WS-C wanted removed.

An operator who wants the old behaviour runs:

```bash
hai state snapshot --evidence-json /path/to/clean.json \
                   --as-of 2026-04-24 --user-id u_local_1 \
                   --db-path <state.db>
```

…then reads `.recovery.classified_state` / `.recovery.policy_result`
(or any other domain's block) off the JSON.

---

## Delivery

1. Remove `cmd_classify` + `cmd_policy` handlers in `src/health_agent_infra/cli.py`.
2. Remove the `hai classify` / `hai policy` parser blocks (+ their
   `annotate_contract` calls).
3. Delete tests that exercise these commands (in
   `safety/tests/test_classify_policy_cli.py` or similar).
4. Regenerate `reporting/docs/agent_cli_contract.md`.
5. Update `intent-router/SKILL.md` if it references them (grep shows
   only passing mentions in debug sections).
6. Update `hai capabilities --json` consumers that listed these as
   always-present — the flags-contract test already uses the
   manifest as source of truth, no test churn required.

---

## Non-goals

- **No replacement debug surface.** The snapshot path is the
  replacement; adding new `hai state classify` / `hai state policy`
  subcommands would reintroduce exactly the coupling we're
  removing.
- **No backward-compat shim.** Pre-1.0 project, no external users
  depend on `hai classify`/`hai policy`. Removing cleanly is
  cheaper than maintaining a deprecated alias.
