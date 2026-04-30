# Onboarding operator demo SLO (W-AA, v0.1.13)

**Status.** Target, not gate. v0.1.13 W-AA per F-PLAN-08 split the
onboarding correctness gate (deterministic test) from the operator
demo SLO (manual, wall-clock). This document records the SLO; the
ship-gate is `verification/tests/test_init_onboarding_flow.py`.

---

## SLO statement

A new user on broadband (≥10 Mbps), modern macOS / Linux, with
intervals.icu credentials at hand:

```
pipx install health-agent-infra
hai init --guided
```

reaches a `synthesized` daily plan in **≤5 minutes elapsed
wall-clock**.

The 5 minutes covers the full sequence:

1. `pipx install` (network-bound; ~30s with a warm wheel cache).
2. `hai init --guided` walks the seven steps:
   1. Confirm + scaffold thresholds.toml.
   2. Apply state DB migrations.
   3. Copy skills.
   4. Prompt for intervals.icu credentials.
   5. Prompt for primary training focus + daily kcal/protein/sleep
      targets; persist as `intent` + `target` rows.
   6. Run a first wellness pull via the intervals.icu adapter.
   7. Surface `hai today` (cold-start prose; no synthesized plan
      yet).
3. The agent-side seam: a host agent (Claude Code, etc.) reads the
   snapshot, posts six domain proposals via `hai propose`, and runs
   `hai synthesize`.

Step 3 is OUT of scope for `hai init`'s direct measurement — the
runtime intentionally defers proposal authoring to the agent loop
(skills propose, code synthesizes; `hai init` does not improvise
coaching prose). The 5-minute SLO assumes a willing agent on the
other end; for a maintainer driving `hai init` and then prompting
Claude Code, observed wall-clock is ~3 min.

---

## Allowed degraded states

These count as **inside** the SLO (the user is not blocked, the flow
surfaces the right next-step):

- **"still pulling — your watch may not have synced today's data
  yet"** — surfaced when the intervals.icu probe pull lands a
  partial response (e.g., today's wellness row not yet propagated).
  The user re-runs `hai today` later; this is not an SLO failure.

- **Cloudflare User-Agent challenge transient** — the v0.1.12.1
  W-CF-UA fix (User-Agent header) makes this rare, but the
  CAUSE_1_CLOUDFLARE_UA classification in `hai doctor --deep` is
  the documented recovery path. See
  `reporting/docs/intervals_icu_403_triage.md`.

- **User declines to enter intervals.icu credentials** — step 4
  records `user_skipped`; step 6 reports `skipped` with the reason
  "no intervals.icu credentials available". The user can run
  `hai auth intervals-icu` later. The `--guided` flow is idempotent
  on rerun.

- **macOS Keychain "Always Allow" prompt during first pull** — the
  user clicks once; the prompt is documented at
  `cli.py:_print_keychain_acl_hint`.

These count as **outside** the SLO (user is blocked, must wait or
escalate):

- Garmin Connect-style 429 / rate-limit transient (intervals.icu
  hits these less often, but they happen).
- intervals.icu account-level activities-endpoint disabled (the
  adapter swallows this and reports `last_pull_partial=True`; user
  can still proceed with wellness-only).
- Initial `pipx install` blocked by missing system python ≥3.11 or
  `pipx` itself missing.

---

## How this is measured

**Manual demo protocol, not a CI gate.** The maintainer or a demo
operator runs the sequence above on a fresh laptop or VM with
intervals.icu credentials at hand and times the wall-clock from
`pipx install` keystroke to first `hai today` rendering with a
synthesized plan. The number lands in:

- `reporting/plans/v0_1_X/RELEASE_PROOF.md` for the cycle that ran
  the demo.
- `reporting/plans/v0_1_X/REPORT.md` if the SLO breached or
  surfaced a regression.

**Why manual, not CI?** The SLO is bounded by network latency (pipx
download, intervals.icu API), Keychain ACL prompts (macOS-only), and
agent loop responsiveness (model-dependent). Any of these would make
a CI gate flaky-by-design. The deterministic ship-gate
(`test_init_onboarding_flow.py`) covers the mechanical contract; this
SLO covers the felt experience.

---

## Risk register reference

PLAN.md §4 risk row:

> "W-AA onboarding wall-clock SLO conflict between deterministic gate
> + operator SLO" — likelihood low, impact governance / UX. Mitigation:
> SLO split per F-PLAN-08 — deterministic test gate (stubbed) is the
> ship-gate; operator wall-clock SLO is a documented target with
> "still pulling" allowed degraded state, recorded here and not a CI
> gate.

This document satisfies that mitigation.

---

## Provenance

- **Authored.** 2026-04-30 (v0.1.13 W-AA implementation cycle).
- **Source.** `reporting/plans/v0_1_13/PLAN.md` §2.B W-AA acceptance
  + ship gates row "Onboarding operator demo SLO".
- **Companion gate.** `verification/tests/test_init_onboarding_flow.py`.
