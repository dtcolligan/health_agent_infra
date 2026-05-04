# v0.1.18 cycle — workspace

**Status:** scoped, not yet open. PLAN.md authored when the cycle
opens after v0.1.17 closes.

**Tier (anticipated):** substantive (multi-surface change touching
CLI default behaviour, README, and packaged skills). Full Phase 0
D11 bug-hunt + multi-round D14 plan-audit.

**Provenance.** Created 2026-05-04 as part of the v0.1.16-cancellation
restructure. The maintainer's directive: do v0.1.17 (maintainability
+ eval substrate) first, then close the onboarding gap proactively
(this cycle), then run a real foreign-user empirical pass (v0.1.19),
then v0.2.0.

The thesis: **the infrastructure for easy onboarding already shipped
in v0.1.13 (`hai init --guided`, `hai doctor onboarding_readiness`),
but the maintainer's own state DB still shows
`onboarding_readiness: WARN: missing intent` (`intent_count: 0`).**
That means the gap is in surfacing/discoverability/UX, not in
mechanism. This cycle closes that gap before exposing it to a foreign
user — pivoting now avoids burning the v0.1.19 foreign-user session
on issues we already know about.

## Scope (provisional, to be finalised in PLAN.md)

| W-id | Title | Effort | Source |
|---|---|---|---|
| **W-OB-1** | README quickstart pivot to `hai init --guided`; drop the now-redundant manual `hai auth intervals-icu` step | 0.5d | maintainer 2026-05-04 directive |
| **W-OB-2** | `hai init` default-flip: when stdin is a TTY and `onboarding_readiness` reports missing fields, auto-promote to `--guided`. Non-interactive callers opt out via `--non-interactive` flag or `HAI_INIT_NON_INTERACTIVE=1` env var. (Lands cleanly post-v0.1.17 W-29 cli.py split into the `init` handler-group module.) | 1-2d | maintainer 2026-05-04 directive + own-DB `intent_count=0` evidence |
| **W-OB-3** | `--guided` prompt content review — intent prompt stickiness, target prompts, refusal-to-answer paths. Decisions: what's required vs optional, what defaults are sane, what the post-prompt summary surfaces | 1-2d | own-DB evidence; UX judgment call |
| **W-OB-4** | Self-onboard dogfood pass — maintainer installs `health-agent-infra` from PyPI on a clean `pipx` environment with no existing state, walks the README cold, files findings | 1d | substitutes for v0.1.16's missing foreign-user transcript |
| **W-OB-5** | `hai doctor onboarding_readiness` actionability: hint text + machine-parsable `next_action` field for agent consumers; capabilities manifest update | 0.5d | downstream from W-OB-1/2/3 — once the path is clean, doctor's hint should cite the right command |
| **W-OB-6** *(conditional)* | If W-OB-4 self-onboard surfaces a structural finding (not just prompt content), absorb here unless severity routes to a hotfix | bounded by W-OB-4 | conditional |

**Total (estimated):** 5-6 W-ids, **3-7 days**, substantive tier.

## Sequencing (provisional)

**Phase 1 — README + dogfood (low-risk, surfaces evidence):**
1. W-OB-1 (README pivot — partly pre-staged on main as a low-risk
   in-flight delta authored 2026-05-04 alongside this scaffold).
2. W-OB-4 (self-onboard dogfood pass on PyPI — outputs become W-OB-3
   input).

**Phase 2 — Default behaviour change:**
3. W-OB-2 (`hai init` default-flip; CI parser/capabilities regression
   test must hold).
4. W-OB-3 (prompt content review — informed by W-OB-4 findings).

**Phase 3 — Diagnostics polish:**
5. W-OB-5 (`hai doctor` actionability).
6. W-OB-6 if applicable.

## Hard dependencies

- **v0.1.17 must close** so W-29 cli.py split is in tree before
  W-OB-2 (default-flip touches the `hai init` argparse handler;
  pre-split would create merge conflicts; post-split lands cleanly
  in the appropriate handler-group module).
- **PyPI `health-agent-infra` (current at start of cycle) must be
  installable cleanly via `pipx install`** for W-OB-4 dogfood to be
  meaningful.

## What's explicitly OUT of scope for v0.1.18

- **No new domains** or domain-policy changes.
- **No schema additions** (v0.2.x territory).
- **No new live-data sources.**
- **No autonomous onboarding actions.** `--guided` default-flip
  respects W57: prompts the user, doesn't auto-author intent rows
  from defaults.
- **No body-comp surface** (W-B is in v0.1.17 scope; if it slips,
  do not absorb here).
- **No foreign-user empirical work** — that's v0.1.19's claim.

## First actions for the cycle session (when it opens)

1. Confirm v0.1.17 closed (RELEASE_PROOF.md + REPORT.md present).
2. Re-read this README.
3. Run `hai init --guided` cold on a clean throwaway environment as
   a pre-PLAN bug-hunt input (informs W-OB-3 + W-OB-4).
4. Author `PLAN.md`. First line: tier annotation.
5. Copy `_templates/codex_plan_audit_prompt.template.md` and
   customise.
6. Hand to maintainer for D14 round-1.

## Cross-references

- `reporting/plans/v0_1_19/README.md` — the post-onboarding foreign-
  user empirical cycle this one is meant to make productive.
- `reporting/plans/v0_1_17/README.md` — the precursor maintainability
  cycle.
- `reporting/plans/v0_1_16/README.md` — cancellation note for the
  former empirical slot.
- AGENTS.md "Settled Decisions" — v0.1.16 cancellation chain.
- `reporting/plans/v0_1_13/` — original W-AA `hai init --guided`
  build (the mechanism this cycle re-surfaces).
- README.md "Install and quickstart" — W-OB-1 target.
