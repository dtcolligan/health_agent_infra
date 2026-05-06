# Codex External Audit — v0.1.18 PLAN.md (pre-cycle plan review)

> **Why this round.** v0.1.18 PLAN.md was authored 2026-05-06 by
> Claude as the synthesis of (a) the v0.1.16-cancellation restructure
> (2026-05-04, see `v0_1_16/README.md`) which inserted v0.1.18 as a
> proactive onboarding-quality cycle before v0.1.19 foreign-user
> empirical, (b) the v0.1.18 README's provisional 6-W-id scope
> authored at the same restructure, and (c) the cycle-open absorption
> of F-OB-PRE-01 (`v0_1_18/audit_findings.md`) as a 7th W-id (W-OB-7)
> per maintainer decision 2026-05-06 (Option A: discrete fix, not
> doctor-hint-absorption).
>
> **Cycle theme.** Onboarding ergonomics + upgrade-path correctness.
> Two threads: (1) UX surfacing of the v0.1.13 W-AA mechanism
> (`hai init --guided` exists; users on TTY don't discover it),
> via README pivot + `hai init` default-flip + `hai doctor
> next_action` schema; (2) upgrade-path correctness via intake-handler
> migration parity (every `cmd_intake_*` routes through the same
> `apply_pending_migrations` seam `hai state init` already uses).
> Cross-cutting validation: maintainer self-onboard dogfood pass
> covering both clean-install AND upgrade-from-old-DB scenarios.
>
> **No CP-shape governance edits this cycle.** Unlike v0.1.12
> (CP1-CP6 reversed AGENTS.md "Do Not Do" entries), v0.1.18 proposes
> only the *closure-side* tactical-plan + current-system-state ship-
> time updates (no new D-entries; no settled-decision reversals;
> no "Do Not Do" additions). PLAN §3 enumerates them. **The audit
> lever is sequencing + sizing + acceptance bite + W-OB-4 dogfood
> honesty boundary, not governance reversals.**
>
> **D14 is a settled decision** (added at v0.1.11 ship, twice-
> validated at v0.1.11 + v0.1.12 with the `10 → 5 → 3 → 0` halving
> signature; v0.1.14 + v0.1.15 + v0.1.17 confirmed at the same shape;
> v0.1.17 settled one round earlier than the substantive norm at
> 11 → 5 → 3). Empirical norm: 2-4 rounds for a substantive PLAN.
> **v0.1.18's catalogue is small (7 W-ids) and structurally low-
> density** (most rows reference established mechanisms — the
> v0.1.13 W-AA build, the existing `apply_pending_migrations` seam,
> the v0.1.17 W-29 handler-group split). **Realistic round
> expectation 2** — author may settle one round earlier than v0.1.17.
> Don't bet on it.
>
> **What's different from the v0.1.17 audit.**
>
> 1. v0.1.17 was a 25-40-day, 10-W-id substantive cycle with W-29
>    cli.py mechanical split as the long-deferred release-blocker.
>    v0.1.18 is a 5-9-day, 6-7-W-id substantive cycle where the
>    release-blocker leg is the W-OB-2 default-flip (changing
>    existing users' first-run experience). **Q1 + Q9 below probe
>    whether the substantive-tier annotation honestly rests on the
>    release-blocker leg given days falls below threshold.**
> 2. v0.1.18 has **no foreign-user precondition by design** — that
>    remains v0.1.19's claim. PLAN §1.1 honesty boundary + §1.4 +
>    §6 explicitly name W-OB-4 as "maintainer dogfood, not foreign-
>    user transcript." **Q4 below probes whether that boundary is
>    enforced consistently across PLAN surfaces (canonical "summary-
>    surface sweep" failure mode).**
> 3. v0.1.18's W-OB-7 is a **mid-cycle absorption** (F-OB-PRE-01
>    surfaced 2026-05-05, absorbed 2026-05-06) rather than a
>    pre-existing carry-over. **Q4 + Q7 below probe whether the
>    absorption is honest (file as discrete W-id) versus a hidden
>    expansion of W-OB-4 or W-OB-5 scope.**
> 4. v0.1.18 has a **sequencing constraint that's load-bearing**:
>    W-OB-7 must land before W-OB-4 fires, otherwise W-OB-4
>    scenario 2 (upgrade) hits the F-OB-PRE-01 crash and the
>    dogfood doesn't validate W-OB-2/W-OB-3 ergonomics. **Q2 below
>    probes whether the sequencing actually holds.**
>
> **Cycle position.** Pre-PLAN-open. Phase 0 (D11) bug-hunt has
> not started. No code has changed against this PLAN. The audit
> is on the *plan document itself* — its coherence, sequencing,
> sizing honesty, hidden coupling, acceptance bite.
>
> **You are starting fresh.** This prompt and the artifacts it
> cites are everything you need; do not assume context from a
> prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main, OR cycle/v0.1.18 if branched (check with maintainer
#         if neither)
git log --oneline -5
# expect top: 9c651da (v0.1.17 ship-time freshness sweep + v0.1.18
#         F-OB-PRE-01 finding, 2026-05-05). If top is `2811669`
#         (Phase H conversational intake), you are on the stale
#         /Users/domcolligan/Documents/health_agent_infra/ tree —
#         STOP and surface.
ls reporting/plans/v0_1_18/
# expect: README.md, audit_findings.md, PLAN.md, codex_plan_audit_prompt.md
#         (this file). If PLAN.md or this prompt is missing, the
#         maintainer didn't hand off — surface and stop.
```

If any don't match, **stop and surface the discrepancy**. Ignore
any tree under `/Users/domcolligan/Documents/`. AGENTS.md "Active
repo path" preamble is durable for exactly this case.

---

## Step 1 — Read the orientation artifacts

In order:

1. **`AGENTS.md`** — operating contract. Pay attention to:
   - "Active repo path" preamble (durable per v0.1.15 W-PLAN-12).
   - "Code Vs Skill" invariant.
   - **"Governance Invariants"** — W57 still applies; W-OB-2's
     default-flip routes through the existing `--guided` flow,
     which prompts the user; W-OB-5's `next_action` is informational,
     not autonomous. Verify both respect W57 in PLAN §2.B and §2.E.
   - **"Settled Decisions" D1-D15.** Especially:
     - **D11 + D14** — pre-PLAN bug-hunt + pre-cycle plan-audit
       patterns this audit enacts.
     - **D15** — cycle-weight tiering. v0.1.18 PLAN's first line
       declares **Tier: substantive** on the W-OB-2 release-blocker
       leg. The days leg (5-9d) is **below** D15's `≥10 days`
       threshold. **Verify the tier choice is honest** — see Q9.
   - **"Do Not Do"** — note that v0.1.17 retired the cli.py-split
     entry; the current entries that v0.1.18's W-OB-2 + W-OB-5 must
     respect are: no autonomous threshold mutation, no autonomous
     intent/target deactivation (W57), no auto-loaded MCP servers.
     PLAN §2.B + §2.E should respect all three.
   - **"Patterns the cycles have validated"** — provenance discipline,
     summary-surface sweep, honest partial-closure naming, audit-chain
     empirical shape. Apply these as you audit. **W-OB-4's "maintainer
     dogfood, not foreign-user transcript" honesty boundary and W-OB-6's
     conditional shape are the two areas where these patterns most
     directly apply.**
2. **`reporting/plans/strategic_plan_v1.md`** — vision (no edits this
   cycle). Verify §10 (Wave 3) does not place a v0.2.x onboarding-
   surface claim that v0.1.18's W-OB-2 + W-OB-5 would collide with.
   PLAN §3 + §7 assert no schema additions; verify against §10.
3. **`reporting/plans/tactical_plan_v0_1_x.md` §5E** — this cycle's
   tactical row. **§5D is shipped v0.1.17; §5F is v0.1.19; §5G is
   v0.2.0.** v0.1.18 PLAN §1.4 restates the renumber narrative
   (v0.1.16-cancellation chain) — verify it matches §5D/§5E/§5F.
4. **`reporting/plans/v0_1_18/README.md`** — provisional scope
   (originally 6 W-OB-* W-ids; W-OB-7 added 2026-05-06). PLAN §1.2
   catalogue should match the README table rows; verify per-W-id
   Title + Effort + Source columns reconcile, and verify W-OB-7's
   addition is named in §1.2 + §1.4 (Chain B).
5. **`reporting/plans/v0_1_18/audit_findings.md` §F-OB-PRE-01** —
   the absorbed finding's source. PLAN §2.G must encode the
   F-OB-PRE-01 contract (every `cmd_intake_*` routes through the
   shared seam; reproducer test for the original `hai intake weight`
   crash).
6. **`reporting/plans/v0_1_17/RELEASE_PROOF.md`** — v0.1.17 closure.
   v0.1.18 lands cleanly post-W-29 (cli.py split into 11 handler-
   group modules). Verify W-OB-2 + W-OB-7's "lands in `cli/handlers/...`"
   claims match the actual post-W-29 handler module layout.
7. **`reporting/plans/v0_1_13/`** — original W-AA `hai init --guided`
   build. The mechanism this cycle re-surfaces. PLAN §2.C (W-OB-3
   prompt content review) inherits the W-AA flow shape; verify §2.C
   acceptance items don't silently change the flow shape.
8. **`reporting/plans/v0_1_19/README.md`** — downstream cycle.
   **Confirm v0.1.18 PLAN does NOT pull v0.1.19 work forward.**
   v0.1.19 owns the foreign-user empirical contract. PLAN §7
   explicitly enumerates this as out-of-scope; verify the boundary
   holds across §2 per-WS sections.
9. **`reporting/plans/v0_1_16/README.md`** — cancellation note (read
   for context on the v0.1.18 insertion chain).
10. **`reporting/plans/v0_1_18/PLAN.md`** — the artifact under review.

Cross-check that everything PLAN.md cites actually exists in the
tree at the cited path/line. Broken cross-references count as
findings (provenance discipline per AGENTS.md "Patterns the cycles
have validated").

---

## Step 2 — The audit questions

### Q1 — Cycle thesis coherence

PLAN §1.1's stated theme is **"onboarding ergonomics + upgrade-path
correctness"** with two threads (UX surfacing of W-AA mechanism;
upgrade-path correctness via intake-handler migration parity) plus
a cross-cutting validation thread (maintainer dogfood).

- **Q1.1.** Does the 7-W-id catalogue add up to that two-thread theme,
  or has scope drifted? Specifically: is W-OB-7 (intake-handler
  migration parity) cleanly inside "upgrade-path correctness" or is
  it a code-bug fix smuggled into a UX cycle?
- **Q1.2.** Are the three phases (foundation + low-risk evidence /
  default behaviour change + actionability / conditional close-out)
  coherent groupings? Is the placement of W-OB-3 in Phase 2 (after
  W-OB-4 dogfood, before W-OB-2 default-flip) honest? W-OB-3 informs
  W-OB-2 (prompt content needs to be solid before default routes
  through it); does the sequencing actually enforce that?
- **Q1.3.** PLAN §1.1 asserts the cycle is parallelizable with
  v0.2.0. Is that actually true given v0.2.0's claimed dependencies
  (per `tactical_plan_v0_1_x.md` §5G)?
- **Q1.4.** PLAN §1.1's honesty boundary names W-OB-4 as "maintainer
  dogfood, not foreign-user transcript." Does the boundary hold across
  the catalogue, or does any W-id silently claim foreign-user-shaped
  evidence?

### Q2 — Sequencing honesty

PLAN §1.3 sequences:
- Phase 1: W-OB-1 → W-OB-7 → W-OB-4
- Phase 2: W-OB-3 → W-OB-2 → W-OB-5
- Phase 3: W-OB-6 (conditional)

PLAN §1.3 names the W-OB-7 → W-OB-4 dependency as **load-bearing**
(W-OB-4 scenario 2 hits F-OB-PRE-01 crash without W-OB-7 in tree).

- **Q2.1.** Does PLAN §1.3's W-OB-7 → W-OB-4 dependency actually
  hold? §2.D acceptance item 3 names it; §2.G acceptance items 4-5
  encode the test side. Verify both surfaces enforce the sequencing
  rather than just naming it.
- **Q2.2.** PLAN §1.3 also sequences W-OB-3 → W-OB-2 → W-OB-5.
  - W-OB-3 prompt content informs W-OB-2 default-flip path content.
  - W-OB-2 default-flipped command shape informs W-OB-5 `next_action`
    string content.
  Does the sequencing actually enforce these? §2.E.2 names the
  W-OB-2 → W-OB-5 dependency. Does §2.B name the W-OB-3 → W-OB-2
  dependency? **Verify by spot-check.**
- **Q2.3.** **W-OB-1 + W-OB-7 + W-OB-4 are sequenced as Phase 1**.
  Are W-OB-1 and W-OB-7 actually independent of each other? Phase 1
  could ship them in any order if so. Verify §2.A and §2.G do not
  introduce hidden coupling.
- **Q2.4.** **W-OB-6 conditional shape.** PLAN §2.F says "if W-OB-4
  surfaces no structural finding, W-OB-6 does not fire." Is the
  trigger condition actually testable, or does it rely on subjective
  classification of W-OB-4 findings? The PLAN does not name a
  classifier — is "structural" defined sharply enough?

### Q3 — Effort estimate honesty

PLAN §5 totals **5-9 days** (per-WS arithmetic 4.5-8.5, +5%
coordination overhead).

- **Q3.1.** W-OB-2 at 1-2 days — credible for a default-flip that
  changes existing users' first-run experience and adds a new flag
  + env-var contract + 4-case test? Compare to v0.1.13 W-AA original
  build (multi-day shipping the entire `--guided` flow); v0.1.18
  W-OB-2 is *additive only* (TTY check + onboarding_readiness query
  + opt-out paths) but the surface area is small. Is 1-2d honest?
- **Q3.2.** W-OB-3 at 1-2 days — credible for "prompt content review
  informed by W-OB-4 findings"? The acceptance items don't enumerate
  specific prompts to revise; the scope is "review surfaces" listed
  prose-form. Is the work actually 1-2d, or could it grow to 3-4d
  if W-OB-4 surfaces multiple distinct UX issues?
- **Q3.3.** W-OB-7 at 0.5-1 day — credible for a shared-seam fix
  across 6 callers + 7-case regression test? §4 risk 8 names the
  scope-creep mitigation; verify the spot-check evidence cited is
  actual (PLAN §4 risk 8 says "current intake.py is 1265 LOC across
  6 well-shaped handlers" — verify by `wc -l` and grep for
  `cmd_intake_*` definitions).
- **Q3.4.** Total **5-9 days** versus v0.1.17 **25-40 days** — order
  of magnitude smaller. Is the small total actually honest, or does
  the cycle silently rely on under-counted W-OB-3 / W-OB-4 effort
  because both depend on dogfood findings the maintainer hasn't yet
  produced?

### Q4 — Hidden coupling + the dogfood honesty boundary

PLAN §1.1's honesty boundary names W-OB-4 as "maintainer dogfood,
not foreign-user transcript."

- **Q4.1.** Does that honesty boundary hold consistently across
  *every* PLAN surface that cites W-OB-4? Specifically: §1.1 theme
  paragraph, §1.2 catalogue Severity column, §1.3 sequencing, §1.4
  thesis, §2.D body, §6 ship gates, §7 out-of-scope. **Missing one
  is the canonical "summary-surface sweep" failure** per AGENTS.md
  "Patterns the cycles have validated."
- **Q4.2.** PLAN §2.D Acceptance item 3 says "scenario 2's
  `hai intake weight` invocation succeeds — the W-OB-7 fix in tree
  before W-OB-4 fires is the load-bearing precondition. If scenario
  2's intake weight invocation crashes, **the cycle does not ship**
  until W-OB-7 is rebuilt." Is this gate enforceable, or does it
  rely on the maintainer's discretion at ship time? Should §6 ship
  gates list it explicitly?
- **Q4.3.** **F-OB-PRE-01 absorption shape.** Maintainer chose
  Option A (W-OB-7 discrete fix) over Option B (W-OB-5 doctor hint
  absorption) per `audit_findings.md`. PLAN §1.4 Chain B + §9
  Provenance both name the choice. **Is the W-OB-7 contract honest,
  or does it silently leave W-OB-5 work undone that absorbing into
  W-OB-5 would have caught?** Specifically: does W-OB-5's `next_action`
  schema include a `migration-behind` case that would have surfaced
  the bug before the user invoked intake?
- **Q4.4.** **W-OB-2 + W-OB-5 sequencing risk** (PLAN §4 risk 7).
  PLAN names the risk but mitigates only by sequencing + commit
  cadence. If a W-OB-5 commit lands before W-OB-2 (e.g., implementer
  reorders for parallelization), `next_action.command` could
  reference `hai init --guided` instead of `hai init`. Is the
  sequencing enforcement strong enough?
- **Q4.5.** **W-OB-7 ↔ existing migration-application paths.**
  `apply_pending_migrations` is currently called by `hai state init`
  (`cli/handlers/state.py:273`) and possibly other paths. Does the
  W-OB-7 fix introduce a hidden interaction — e.g., if `hai daily`
  also calls `apply_pending_migrations`, does the new intake-handler
  call double-apply? Verify by reading `core/state/store.py:243`
  and `cli/handlers/state.py:239,273` against PLAN §2.G.

### Q5 — Acceptance criterion bite

PLAN §2.A through §2.G each list acceptance items. The audit's core
question: **could each item actually fail and surface the bug it's
meant to catch?**

- **Q5.1. W-OB-1 acceptance items 1-2** (sweep + cross-references).
  Is item 1 mechanically testable, or does it rely on human review?
  Item 2 names a `grep -rn "hai init"` sweep — is that a release-
  blocker if a stale reference is missed?
- **Q5.2. W-OB-2 acceptance item 3** (4-case test). Are the four
  cases (interactive+missing / interactive+complete / non-interactive
  / explicit opt-out) sufficient, or is a fifth case missing — e.g.,
  pseudo-TTY (CI runners that present TTY but don't have user input
  available)?
- **Q5.3. W-OB-3 acceptance item 2** (refusal + resume tests).
  Does case (a) "user types 'skip' at intent prompt → flow continues
  with `intent_count=0`" actually exist in the v0.1.13 W-AA flow,
  or is "skip" a UX affordance W-OB-3 is *adding*? If adding, the
  acceptance item is out of scope (W-OB-3 is content review, not
  flow change).
- **Q5.4. W-OB-4 acceptance items 1-4** (dogfood findings file +
  cycle_impact tags + sequencing precondition + finding-routing).
  Items 1-2 are observable. Item 3 enforces the W-OB-7 precondition.
  Item 4 says "no finding silently dropped" — but the PLAN does not
  name a specific gate. Is item 4 enforceable?
- **Q5.5. W-OB-5 acceptance item 2** (`next_action.command` references
  post-W-OB-2 default-flipped shape). How is this enforced? A test
  asserting `next_action.command == "hai init"` (not `"hai init
  --guided"`) post-W-OB-2 would catch sequencing slippage. Is that
  test named?
- **Q5.6. W-OB-6 conditional acceptance.** Items 1-3 are meta-acceptance
  ("if W-OB-4 surfaces / doesn't surface, W-OB-6 fires / doesn't
  fire"). Is the conditional shape itself enforceable as a ship
  gate, or does the cycle just trust the implementer to honour it?
- **Q5.7. W-OB-7 acceptance items 3-4** (regression test + reproducer).
  Item 3 covers all 6 intake commands; item 4 specifically covers
  the F-OB-PRE-01 reproducer. Does the test actually use a synthetic
  schema-25 DB that mimics the real failure mode (i.e., DB exists
  but schema head is behind), not just an empty DB?

### Q6 — Settled-decision integrity (closure-side)

PLAN §3 proposes:

1. No "Settled Decisions" edits.
2. No "Do Not Do" edits.
3. Tactical-plan §5E ship-time row update.
4. `current_system_state.md` version + command count update.
5. `CHANGELOG.md` v0.1.18 entry.
6. `AUDIT.md` v0.1.18 row.

- **Q6.1.** **Is the "no governance edits" framing honest?** v0.1.18
  changes the default behaviour of `hai init` — that's arguably a
  doctrine change worth a settled-decision entry (e.g., "default-
  flips on interactive-TTY contracts respect W57 by routing through
  prompt-based flows, not auto-authoring"). Should v0.1.18 propose
  a new D-entry?
- **Q6.2.** PLAN §3 names tactical-plan §5E + §5F updates as
  "standard ship-time freshness sweep, not a governance edit." Is
  that distinction honest, or does the sweep effectively encode
  the v0.1.18 closure-side governance shape?
- **Q6.3.** **W-OB-5 `next_action` schema.** Adding a documented
  field to the `hai doctor` output is arguably a manifest schema
  delta. PLAN §3 says "if `next_action` schema in `hai doctor`
  adds a documented field, that's a manifest schema delta worth
  naming." Should this be promoted to an explicit governance edit
  (e.g., a tactical plan note that the v0.2.3 capabilities-manifest
  schema freeze must include `next_action` in the frozen schema)?

### Q7 — What the plan doesn't say

Absences worth flagging:

- **Q7.1. W-OB-2 abort path.** What happens if the default-flip
  reveals a fundamental design issue (e.g., onboarding_readiness
  query is too slow to run on every `hai init` invocation, blocking
  startup)? PLAN §4 risk 1 names CI-breakage as the high-impact
  failure mode but doesn't name an abort path. Should it?
- **Q7.2. Cycle abort overall.** v0.1.17 PLAN had explicit abort
  paths for W-29 (the `do-not-split` verdict). Does v0.1.18 have
  an analogous abort for W-OB-2 or W-OB-7? §4 risk 9 names "cycle-
  abort path exists per AGENTS.md D11" — is that specific enough,
  or should the PLAN name explicit conditions?
- **Q7.3. Conditional WS scope.** W-OB-6's conditional shape is
  the contract. Is the trigger ("structural finding") sharply enough
  defined? The PLAN does not list examples of "structural" vs
  "non-structural" findings; should it?
- **Q7.4. Persona matrix coverage.** §6 ship gates list the 13-persona
  matrix. Does v0.1.18 add any new persona-relevant surfaces
  (e.g., the W-OB-2 default-flip changes first-run experience —
  does any persona exercise first-run)? PLAN doesn't address.
- **Q7.5. v0.1.19 reach-back.** v0.1.19's foreign-user session runs
  against the post-v0.1.18 PyPI build. If v0.1.19 surfaces a finding
  that traces back to a v0.1.18 W-OB-* design choice, what's the
  recourse? PLAN §7 names v0.1.19 as out-of-scope but doesn't name
  a v0.1.18 hotfix path.

### Q8 — Provenance / external-source skepticism

Spot-verify claims that lean on external/historical docs:

- **Q8.1.** PLAN §2.A references README.md "Install and quickstart"
  at lines 206-244. Verify by reading `README.md` against HEAD.
- **Q8.2.** PLAN §2.B claims `cmd_init` lives at
  `cli/handlers/config_init.py:420`. Verify by `grep -n "def cmd_init"
  src/health_agent_infra/cli/handlers/config_init.py`.
- **Q8.3.** PLAN §2.E claims `check_onboarding_readiness` lives at
  `core/doctor/checks.py:470` and `_render_onboarding_readiness` at
  `core/doctor/render.py:105`. Verify both.
- **Q8.4.** PLAN §2.G claims `apply_pending_migrations` lives at
  `core/state/store.py:243` and `hai state init` calls it at
  `cli/handlers/state.py:239,273`. Verify all three line numbers.
- **Q8.5.** PLAN §2.G claims six `cmd_intake_*` handlers at lines
  `gym=62, nutrition=420, stress=643, note=790, readiness=903,
  weight=1184` in `cli/handlers/intake.py`. Verify with
  `grep -n "^def cmd_intake_" src/health_agent_infra/cli/handlers/intake.py`.
- **Q8.6.** PLAN §1.4 claims `audit_findings.md` §F-OB-PRE-01 was
  added 2026-05-05. Verify file exists with the section.
- **Q8.7.** PLAN §1 honesty boundary cites
  `~/.claude/projects/-Users-domcolligan-health-agent-infra/memory/project_intake_handlers_dont_apply_migrations.md`
  as the maintainer-memory cross-reference. Verify the memory file
  exists. (Codex may not have direct access to `~/.claude/`; if not,
  flag as unverifiable rather than as a finding.)
- **Q8.8.** PLAN §4 risk 8 claims "current intake.py is 1265 LOC
  across 6 well-shaped handlers." Verify with `wc -l
  src/health_agent_infra/cli/handlers/intake.py` and the cmd_intake_*
  count via grep.
- **Q8.9.** PLAN §1 metadata cites HEAD `9c651da`. Verify with
  `git log --oneline -1`.

### Q9 — Tier annotation honesty (D15)

PLAN's first line declares **Tier: substantive** on the W-OB-2
release-blocker leg, with the days leg (5-9d) explicitly noted as
**below** the `≥10 days` threshold.

- **Q9.1.** Is the W-OB-2 release-blocker classification honest?
  W-OB-2 changes default behaviour of `hai init` (the most-touched
  install-path command). AGENTS.md D15 substantive criterion is
  "≥1 release-blocker workstream" — does W-OB-2 actually qualify,
  or is it more accurately described as a UX hardening that doesn't
  rise to release-blocker?
- **Q9.2.** PLAN proposes 0 governance/AGENTS.md edits — under D15's
  "≥3 governance edits" threshold (the third leg of the substantive
  trigger). The tier therefore rests entirely on the release-blocker
  leg. **Is the release-blocker classification load-bearing enough,
  or should the cycle be re-tiered as "hardening"?** AGENTS.md D15
  defines hardening as "correctness/security only, no governance,
  ≤1 week" with abbreviated Phase 0 + single-round D14 target. v0.1.18
  is correctness + UX + ≤1 week (5-9d) with no governance — does
  it cleanly fit hardening tier instead?
- **Q9.3.** If re-tiered to hardening, what changes? Single-round
  D14 instead of 2-3; abbreviated Phase 0; no foreign-user-shape
  ship-gate language. **Surface this trade-off explicitly so the
  maintainer can ratify or reject the tier choice.**

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_18/codex_plan_audit_response.md` matching the
existing convention:

```markdown
# Codex Plan Audit Response — v0.1.18 PLAN.md

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS |
PLAN_INCOHERENT (state which workstreams need rework before open)

**Round:** 1 / 2 / 3

## Findings

### F-PLAN-01. <short title>

**Q-bucket:** Q1 / Q2 / Q3 / Q4 / Q5 / Q6 / Q7 / Q8 / Q9
**Severity:** plan-incoherence | sizing-mistake | dependency-error |
acceptance-criterion-weak | hidden-coupling | settled-decision-conflict |
absence | provenance-gap | tier-mismatch | nit
**Reference:** PLAN.md § X.Y, line N (or "absent")
**Argument:** <why this is a finding, with citations>
**Recommended response:** <revise PLAN.md as follows / accept and
note as known limitation / disagree with reason>

### F-PLAN-02. ...

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-OB-1 | PASS / FIX / RESCOPE | ... |
| W-OB-2 | ... | ... |
| W-OB-3 | ... | ... |
| W-OB-4 | ... | ... |
| W-OB-5 | ... | ... |
| W-OB-6 | ... | ... |
| W-OB-7 | ... | ... |

## Open questions for maintainer

(Specifically rate OQ-1 through OQ-7 in PLAN §8 — agree with the
provisional default? Suggest alternative? Or is the default
already wrong-shaped?)

## Tier ratification

(Q9 specifically — substantive on release-blocker leg, hardening
on days leg + correctness shape, or other? Recommend tier and
name what changes.)

## Closure recommendation

(Verdict + named must-fix revisions list + recommended next-round
budget.)
```

Each finding must be triageable. Vague feedback is not a finding;
"PLAN.md §2.G claims `apply_pending_migrations` at `core/state/store.py:243`
but `grep -n` returns line 245" is a finding. "PLAN seems verbose"
is not.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle as written.
- **PLAN_COHERENT_WITH_REVISIONS** — open the cycle after named
  revisions land. Revisions list every must-fix finding.
- **PLAN_INCOHERENT** — do not open. Re-author the named sections
  before re-running this audit.

---

## Step 5 — Out of scope

- Prior-cycle implementation (v0.1.17 already audited and shipped).
- Code changes against this PLAN (Phase 0 hasn't started; no
  W-id has commits yet).
- v0.1.19 / v0.2.0 scope (named in tactical_plan_v0_1_x.md but
  not in this PLAN's commitments). Pulling forward is itself a
  finding.
- The strategic + tactical + eval + success + risks docs beyond
  the closure-side §3 deltas this cycle proposes.
- AGENTS.md "Active repo path" preamble (settled v0.1.15 W-PLAN-12).

---

## Step 6 — Cycle pattern (this audit's place)

```
Pre-PLAN-open:
  [D14] Codex plan audit ← you are here, round 1
  Maintainer + Claude response to plan audit
  PLAN.md revised if warranted
  (loop until PLAN_COHERENT — empirical 2-3 rounds expected for
   v0.1.18; small catalogue + low governance density)

Phase 0 (D11):
  Internal sweep
  Audit-chain probe
  Persona matrix (13 personas; W-OB-4 dogfood pass distinct from
   persona matrix)
  Codex external bug-hunt audit (optional per maintainer)
  → audit_findings.md updates beyond F-OB-PRE-01

Pre-implementation gate:
  revises-scope findings may revise PLAN (loop back to D14)
  aborts-cycle findings may end the cycle

PLAN.md → opens cycle

Implementation rounds:
  Phase 1 (W-OB-1 + W-OB-7 + W-OB-4) → atomic Phase 1 commits
  Phase 2 (W-OB-3 + W-OB-2 + W-OB-5) → atomic Phase 2 commits
  Phase 3 (W-OB-6 conditional)
  Codex implementation review (post-implementation, IR)
  ... until SHIP / SHIP_WITH_NOTES (empirical 2-3 IR rounds)

RELEASE_PROOF.md + REPORT.md → ship to PyPI as 0.1.18

v0.1.19 cycle opens — foreign-user empirical session against the
shipped v0.1.18 wheel.
```

Estimated review duration: 1-2 sessions per D14 round.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_18/codex_plan_audit_response.md` (new) —
  your findings.
- `reporting/plans/v0_1_18/PLAN.md` (revisions, if warranted) —
  maintainer + Claude apply revisions in response.
- `reporting/plans/v0_1_18/codex_plan_audit_round_N_response.md`
  (subsequent rounds, if revisions warrant another pass).

**No code changes.** No test runs. No state mutations. No
implementation against the PLAN.
