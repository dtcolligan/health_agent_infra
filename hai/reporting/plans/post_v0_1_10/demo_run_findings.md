# Demo-Run Findings — 2026-04-28

> **Authored 2026-04-28** by Claude after a live end-to-end demo to a
> third-party observer (a friend of Dom's). The demo exercised the
> full daily loop on Dom's real state DB: free-text intake → typed
> intake calls → six-domain proposals → synthesis → user-facing
> narration.
>
> **Purpose.** Consolidate frictions and bugs surfaced by the demo
> into a structured findings doc that feeds the next release cycle.
> Cross-references against `v0_1_11/PLAN.md` so we don't double-scope
> work already in flight.
>
> **Conventions match** `v0_1_10/audit_findings.md` so this slots
> cleanly into the cycle pattern (D11).
>
> **Demo verdict.** Friend was visibly impressed. The discipline (refuse
> to fabricate, defer when sync breaks, escalate on objective rules even
> with favourable subjective signals) read as the *feature*, not as
> limitation. That feedback validates the v0.1.10+ posture and is worth
> preserving as a settled approach for future demos.

---

## 1. What the demo run did

| Stage | Outcome |
|---|---|
| Capabilities recap to observer | Done in-character (no operator-debug voice) |
| Refusal of "give me a fitness/nutrition/supplement plan" | Done; reframed as the system's load-bearing posture |
| Fall-back to past day's plan when today's pull failed | `hai today --as-of 2026-04-27` rendered cleanly |
| Free-text intake routing | 4 typed intakes parsed cleanly: gym (12 sets), readiness, stress, nutrition (projected) |
| 6 domain proposals composed + posted | All validated by `hai propose` first time |
| Synthesis | 1 canonical plan committed (`plan_2026-04-28_u_local_1`) |
| User-facing narration | 3 prescribe / 3 defer; strength escalation surfaced as the demo's punchline |

Plan commit confirmed via `hai today --as-of 2026-04-28`. Audit chain
intact: intake → proposal → planned → committed → narrated.

---

## 2. Findings (new — not yet in v0.1.11 PLAN.md)

### F-DEMO-01. `hai doctor` reports `auth_intervals_icu: ok` while live API returns 403

**Source:** Demo run live pull stage.
**Severity:** diagnostic-trust / false-positive.
**Blast radius:** every user who relies on `hai doctor` to confirm
sync health before running `hai daily`. False-OK leaves the user
unaware that recovery + sleep + running will defer.
**Repro:**

```
hai doctor                  # → auth_intervals_icu: ok (credentials present)
hai pull --source intervals_icu --date 2026-04-28
                            # → "Intervals.icu wellness fetch failed: HTTP 403 Forbidden"
```

**Root cause hypothesis.** `core/doctor/checks.py` checks credential
*presence* in keyring; it does not perform a probe call. A revoked /
expired API key passes the doctor check but fails the actual fetch.

**Recommendation.** Extend the auth-doctor check with an optional
probe call (HEAD request or minimal-scope wellness fetch) gated behind
a `--probe` flag (default off to keep doctor cheap; on for `hai
doctor --deep`). If the probe fails, surface the HTTP status code in
the doctor output.

**Sizing.** ~half-day. New flag, single probe-helper, doctor row
extension. Test: mock 401/403 on the probe path.

**Routing.** v0.1.12 candidate. Not release-blocker class.

---

### F-DEMO-02. Proposal schemas + per-domain action enums not discoverable via `hai capabilities --json`

**Source:** Demo run proposal-composition stage. To compose 6
proposals I had to:
- read `*_proposals.jsonl` history to learn the proposal envelope shape, and
- grep `src/health_agent_infra/domains/nutrition/schemas.py` to find
  `NUTRITION_ACTION_KINDS` (which is the v1 macros-only enum).

**Severity:** agent-CLI-contract incompleteness.
**Blast radius:** every agent that composes proposals from scratch
without prior history files to mimic. Slows compose-time, encourages
"copy yesterday's shape" as the discoverability path.

**Recommendation.** Extend `hai capabilities --json` with a
per-domain block:

```json
{
  "domain_proposal_contracts": {
    "nutrition": {
      "schema_version": "nutrition_proposal.v1",
      "action_enum": ["maintain_targets", "increase_protein_intake", "increase_hydration", "reduce_calorie_deficit", "defer_decision_insufficient_signal", "escalate_for_user_review"],
      "required_fields": ["schema_version", "proposal_id", "user_id", "for_date", "domain", "action", "rationale", "confidence", "policy_decisions"]
    },
    ...
  }
}
```

Sourced from `core.validate.ALLOWED_ACTIONS_BY_DOMAIN` + the domain
schema modules. Pure read-side, no behaviour change.

**Sizing.** Half-day. Extends an existing read-only command. Test:
contract test asserting every domain in the manifest is in
`ALLOWED_ACTIONS_BY_DOMAIN` and vice versa.

**Routing.** v0.1.12 candidate. Composes well with v0.1.11 W-S
(persona harness drift guards) which already pulls from
`ALLOWED_ACTIONS_BY_DOMAIN`. Could possibly fold into W-S scope if
v0.1.11 hasn't started yet; otherwise, fresh v0.1.12 W-id.

**Note.** Per `AGENTS.md`: settled decision W30 says "do not freeze
the capabilities manifest schema yet." This finding does not freeze
the schema — it adds new optional blocks. Backwards-compatible.

---

### F-DEMO-03. CLI flag inconsistency — `--as-of` vs `--date`

**Source:** Demo run pull stage. `hai daily --as-of 2026-04-28` works;
`hai pull --as-of 2026-04-28` fails with "unrecognized arguments".
`hai pull` uses `--date` instead.

**Severity:** ergonomics nit / agent-CLI-contract polish.
**Blast radius:** every agent or user composing CLI sequences. Costs
~1 turn per encounter.

**Affected commands:**
- `hai daily` → `--as-of`
- `hai today` → `--as-of`
- `hai explain` → `--for-date`
- `hai pull` → `--date`
- `hai clean` → no civil-date flag (passthrough from evidence-json)
- `hai intake *` → `--as-of`
- `hai state read` → `--since` / `--until`

**Recommendation.** Add `--as-of` as an alias for `--date` on `hai
pull` (and rename `--for-date` on `hai explain` similarly), with the
old flag deprecated-with-warning for one cycle. Document in the
capabilities manifest that `--as-of` is the canonical civil-date flag.

**Sizing.** ~2 hours. argparse alias + deprecation warning + tests.

**Routing.** v0.1.12 candidate. Low-risk, high-frequency-friction.

---

### F-DEMO-04. `hai intake gaps` requires successful pull before it can run

**Source:** Demo run session-start protocol. The merge-human-inputs
skill's protocol step 1 calls
`hai intake gaps --evidence-json <hai clean output>`. With `hai pull`
broken (intervals.icu 403), the gap-detection chain could not run.

**Severity:** session-start protocol fragility.
**Blast radius:** every cold-start session where wearable sync is
broken or stale. Without gap-detection, the agent must improvise the
intake flow rather than running the canonical protocol.

**Root cause.** Gaps require evidence; evidence requires pull;
broken pull blocks gaps. But the state DB already has the most-recent
accepted snapshot — gaps could be derived from that as a fallback.

**Recommendation.** Add a `--from-state-snapshot` mode to
`hai intake gaps` that derives gaps from the latest
`accepted_*_state_daily` rows + manual intake jsonl tails, without
requiring fresh evidence. Keep the evidence-json mode as the
preferred path when sync is healthy.

**Sizing.** 1-2 days. Touches gap-detection logic; needs careful
mapping from accepted-state rows back to gap shapes.

**Routing.** v0.1.12 or v0.1.13 candidate. Adjacent to W-E (state-
change supersession) since both reason about state-deltas. Could be
worth considering whether they share a fingerprint primitive.

---

### F-DEMO-05. `--supersede` on a fresh day (no prior canonical) creates an unreachable plan id

**Source:** Demo run synthesis stage. First `hai daily --skip-pull
--supersede` call minted `plan_2026-04-28_u_local_1_v2` even though
no v1 existed for the day. `hai today --as-of 2026-04-28` and
`hai explain --for-date 2026-04-28` both could not find the plan
(only `hai explain --daily-plan-id <exact_id>` worked).

The next `hai daily --skip-pull` (without `--supersede`) created
`plan_2026-04-28_u_local_1` cleanly. The orphan v2 row remains.

**Severity:** audit-chain integrity / state pollution.
**Blast radius:** any caller that passes `--supersede` defensively
without first checking whether a canonical exists.

**Cross-reference.** **This is closely related to v0.1.11 W-E**
(`hai daily` re-run state-change supersession) and **W-F** (audit-
chain version-counter integrity), both already release-blocker class
in v0.1.11. **Recommend folding this into W-F scope** — the version
counter starting at `_v2` from a `_v0` baseline is the same
counter-integrity issue, just triggered via a different path.

**Recommendation.** When `--supersede` is passed but no canonical
plan exists for `(for_date, user_id)`, either:
- (a) treat as if `--supersede` was not passed (write a fresh v1), or
- (b) error out with USER_INPUT exit code and a clear message
  ("no canonical plan to supersede for date X").

Option (a) is more forgiving; option (b) is more explicit. The
former probably lines up better with how `--supersede` reads to a
caller in the wild.

Plus: a one-time cleanup pass for the existing orphan
`plan_2026-04-28_u_local_1_v2` row — either supersede-archive it via
the new canonical or document it explicitly.

**Sizing.** Inside W-F scope, ~half-day extra. Test: contrived
"supersede on fresh day" assertion.

**Routing.** **Fold into v0.1.11 W-F.** Already release-blocker
class; same code path; same release.

---

## 3. Findings already in v0.1.11 — confirmed by demo

The demo provided a fresh, real-data confirmation for three workstreams
already in `v0_1_11/PLAN.md`. Recording the demo evidence so the cycle
ships with concrete repro stories rather than only synthetic ones:

### Confirms W-B — R-volume-spike minimum-coverage gate

**Demo evidence.** Strength domain escalated `volume_ratio=4.0` against
threshold 1.5 despite favourable subjective signals (soreness=low,
energy=high, stress=1) and a perfectly-paced session (bench 90/100/100
× 8 RPE 7, all sub-failure except deliberate lateral-raise failure).
Reason: only 2 sessions in last 28 days → any session is a 4× spike.

**Why the gate matters.** A user resuming training after a quiet
period gets escalated for an entirely reasonable session, every
session, until they cross the gate threshold. This is the same shape
v0.1.10 confirmed across 6 personas — and now confirmed on Dom's real
state.

**Action.** No change to v0.1.11 W-B scope. Add this demo-run case
to the W-B test suite as a real-data fixture (sessions_last_28d=2,
sessions_last_7d=2, volume_ratio=4.0, subjective signals favourable —
expect post-fix outcome: `coverage_band: 'insufficient'` rather than
escalate).

### Confirms W-E — `hai daily` re-run state-change supersession

**Demo evidence.** First `hai daily --skip-pull --supersede` produced
the orphan `_v2` (see F-DEMO-05). Second `hai daily --skip-pull`
produced the canonical. The state did not materially change between
the two — yet `--supersede` produced a new id. This is the inverse of
the W-E goal but exposes the same mechanism.

**Action.** No change to v0.1.11 W-E scope. The state-fingerprint
primitive will incidentally fix the F-DEMO-05 path: with a fingerprint,
`--supersede` on identical state can be a true no-op instead of
producing an orphan.

### Confirms W-F — Audit-chain version-counter integrity

**Demo evidence.** F-DEMO-05 above. Counter went `_v2` from a baseline
of nothing (effectively `_v0`). Same skipped-version pattern as F-B-01.

**Action.** Fold F-DEMO-05 scope into W-F (see recommendation above).

---

## 4. Findings already in v0.1.11 — but with a wrinkle

None. Every demo-run finding either matches an existing W-id cleanly
or is a fresh v0.1.12 candidate.

---

## 5. Demo-related improvements (not bugs — strategic surface)

### S-DEMO-01. `--demo` mode (scratch DB + cleanup)

**Source.** Dom's framing at session start: *"information about himself
isn't needed to be added to the database in actuality, or it can be
removed later."* The current system has no notion of demo data. Every
intake mutates `~/.local/share/health_agent_infra/state.db`, which is
the same DB Dom runs his real life from.

For this demo, Dom's friend never gave inputs — Dom narrated his own
real day, so persistence was correct. But the next demo viewer might.
Scratch DB + auto-cleanup is the cleaner path.

**Recommendation.** Add a `HAI_DEMO_DB=/tmp/hai_demo_<timestamp>.db`
env var or `--demo` flag that:
- Routes all reads + writes to a per-session scratch DB.
- Pre-populates the scratch DB with last 14d of fixtures (from the
  CSV adapter or a synthesised persona).
- Auto-cleans on session end (or via `hai demo cleanup`).

**Sizing.** 2-3 days. Touches the DB-path resolver in every CLI
command + a fixture-loader path. Non-trivial but well-scoped.

**Routing.** v0.1.12 or v0.1.13 candidate. Strategic — useful for
demo / docs / onboarding flows.

### S-DEMO-02. Demo-flow guide doc

**Recommendation.** Add `reporting/docs/demo_flow.md` that captures
the canonical demo-run sequence: pre-flight check, capabilities
narration, refusal posture, fall-back to past day, intake-routing,
proposal composition, synthesis, narration, follow-up review.

This is the demo Dom just ran; it landed; it's worth being repeatable
without depending on the agent's session memory.

**Sizing.** ~half-day. One doc, walking through the exact happy path
with command snippets.

**Routing.** Doc-only. Could ship anytime; not gated by a code
release.

---

## 6. Routing summary — confirmed dispositions

> **Updated 2026-04-28** twice. Initial routing parked F-DEMO-04
> and S-DEMO-01 to v0.1.12. Maintainer pushed back: bugs found in
> the demo do not get parked for two cycles. After scoping Q1–Q7
> with maintainer answers, **all 7 demo findings absorb into
> v0.1.11** with ~5 days of net scope addition (within planning
> headroom for a 4-5 week cycle).

| Finding | Disposition | Cycle | Effort |
|---|---|---|---|
| F-DEMO-01 (doctor false-positive) | **New W-X in v0.1.11** | v0.1.11 | 0.5 day |
| F-DEMO-02 (capabilities expose proposal contracts) | **Fold into W-S scope** (extends existing primitive) | v0.1.11 | 0.5 day |
| F-DEMO-03 (CLI flag harmonisation) | **New W-Y in v0.1.11** | v0.1.11 | 2 hours |
| F-DEMO-04 (gaps from state snapshot) | **New W-W in v0.1.11** (`--from-state-snapshot` flag, distinguished output, 48h staleness gate, single-read-transaction concurrency contract per Codex F-PLAN-06) | v0.1.11 | 1-2 days |
| F-DEMO-05 (orphan supersede leaf) | **Fold into W-F scope** (same counter-integrity issue; USER_INPUT contract per maintainer Q-A) | v0.1.11 | 0.5 day |
| S-DEMO-01 (--demo mode) | **New W-Va + W-Vb in v0.1.11** (split per Codex F-PLAN-04; W-Va is release-blocker class with fail-closed marker + multi-resolver isolation per Codex F-PLAN-02/03; W-Vb deferrable to v0.1.12 if cycle runs hot) | v0.1.11 | 4-6 days |
| S-DEMO-02 (demo flow doc) | **New W-Z in v0.1.11** (hard-deps on W-Va + W-Vb) | v0.1.11 | 0.5 day |

**Net release impact on v0.1.11 (post Codex plan-audit round 1):**
6 new W-ids (W-Va, W-Vb, W-W, W-X, W-Y, W-Z) + W-S extension +
W-F extension + W-B D12 coercer addition. **Total ~7-10 days
extra** on the original 15-20 day estimate. New estimate:
**22-30 days** (~50-100% growth, headroom note included for
W-Vb deferral if W-P property tests bloat scope). 14 → **20
workstreams**. **Release-blocker class: W-E, W-F, W-Va.**

**v0.1.11 PLAN.md updated** in the same revision that authored
this doc.

**v0.1.12 absorbs no demo findings.** Already-planned scope
(W-H2 mypy stylistic + bandit closure + state-change UX
follow-on) stands as-is.

### Maintainer scoping answers (Q1–Q7) recorded in PLAN.md §§ 2.14–2.15

- **Q1** → explicit `--from-state-snapshot` flag on `hai intake gaps`
  (not auto-fallback). Source visibility in the audit trail beats
  cleverness.
- **Q2** → distinguished output via `derived_from: "pull_evidence"
  | "state_snapshot"` field on every gap object.
- **Q3** → 48h staleness threshold default, configurable via
  `thresholds.toml`. Override per-call via `--allow-stale-snapshot`.
- **Q4** → `hai demo start / end / cleanup` sub-commands. Sticky
  session via marker file at `~/.health_agent/demo_session.json`.
  Best UX for a 30-min demo workflow; not per-command flag friction.
- **Q5** → fixtures default to persona-pre-populated (default `p1`);
  `--blank` opens a blank-slate scratch DB.
- **Q6** → CSV adapter only in demo mode. Live wearable sources
  (`intervals_icu`, `garmin_live`) rejected with USER_INPUT.
  `hai auth *` commands refuse in demo. No network, no leak risk.
- **Q7** → auto-cleanup of stale sessions (>24h) surfaces a stderr
  note rather than auto-deleting. Explicit `hai demo cleanup`
  available. Stderr banner on every CLI invocation in demo mode.

---

## 7. What this doc is NOT

- Not a release plan. v0.1.11 PLAN.md remains authoritative. This
  feeds the v0.1.12 PLAN.md when it's authored.
- Not a Codex audit substitute. No external review here. Intended as
  the input to the next pre-PLAN bug hunt (D11).
- Not a behaviour change. Recommends scoping; ships no code.

---

## 8. Provenance

- Demo session: 2026-04-28, ~30-45 min wall clock.
- Data source: Dom's real local state DB at
  `~/.local/share/health_agent_infra/state.db`, schema_version 21.
- Plan committed during demo: `plan_2026-04-28_u_local_1`.
- Cross-referenced docs:
  - `reporting/plans/v0_1_11/PLAN.md`
  - `reporting/plans/v0_1_10/audit_findings.md` (convention match)
  - `reporting/plans/post_v0_1_10/README.md`
  - `AGENTS.md` (D11 pre-PLAN bug-hunt; W30 capabilities-schema scope)
