# v0.1.10 Pre-audit plan — bug hunt before scope

> **Status.** Pre-PLAN.md document. Authored 2026-04-27 in response
> to the morning-briefing dogfood session that surfaced bugs B1-B7
> against a single user shape (Dom). Before opening v0.1.10's formal
> PLAN.md, we run a structured bug hunt to ensure scope reflects
> codebase reality, not opportunistic findings.
>
> **Output.** A consolidated findings document at
> `reporting/plans/v0_1_10/audit_findings.md` that becomes the input
> to PLAN.md when the formal cycle opens.

---

## 1. Why this doc exists

The B1-B7 list in the project memory and in the v0.1.9 backlog is
**opportunistic** — what one user-flow exposed. Scoping a release
around it ships ~7 fixes and reveals 6 more next week.

A systematic hunt before the formal cycle:
- Surfaces bugs no single user-flow has tripped over yet.
- Distinguishes *classifier-assumption bugs* (which need persona
  diversity to find) from *correctness bugs* (which the existing
  unit test suite can find).
- Gives the eventual v0.1.10 PLAN.md credible scope rather than
  reactive scope.

This is the same audit-trail discipline as v0.1.8 / v0.1.9 cycles
— but the hunt phase is broader and not yet committed to a release.

---

## 2. User-set discipline

Per maintainer call (2026-04-27):

- **In scope:** recreational and technical athletes, AI-familiar,
  no medical conditions.
- **Age band:** 18-50 (Mifflin-St Jeor BMR formula remains valid;
  classifiers don't need adolescent / elderly variants yet).
- **Sport mix:** running, strength, multi-sport, manual-only.
- **Out of scope:** clinical conditions, pregnancy, adolescent
  (<18), elderly (>55), chronic disease, rehab, multi-tenant.

This bounds the persona matrix and the bug surface. Expanding the
user-set is a v0.2-class scope change.

---

## 3. Hunt phases (parallelisable)

### Phase A — Internal sweep (code-side, ~1 day)

- Full pytest under verification/tests/ with `-W error::Warning` to
  surface every warning.
- `mypy --strict` on `src/health_agent_infra/` (delta vs baseline,
  not full strict-pass — incremental finding triage).
- `ruff` strict rule pass.
- `bandit` security scan on `src/`.
- `hai doctor` + `hai capabilities --json` self-consistency check
  (CLI claims match implementation).
- Threshold/config consumer audit — sweep `int(.*cfg)` /
  `float(.*cfg)` / `bool(.*cfg)` sites for the v0.1.9 carry-over
  type-hardening item B1.
- Targeted code review, three risk surfaces:
  - `core/synthesis.py` + `core/synthesis_policy.py` (B7's home)
  - `core/projection/` + `core/gap_detector` (B4's home)
  - `core/audit_chain` reconciliation reads (audit-chain integrity)

### Phase B — Audit-chain integrity probe (~half day)

Pick the most recent 3-5 historical days from the maintainer's
local DB, walk:

```
proposal_log
  → planned_recommendation
  → daily_plan
  → recommendation_log
  → review_outcome (where present)
```

Verify the chain reconciles through `hai explain` for every day.
Look for:
- Orphan recommendation_log rows (no proposal_log parent)
- Plan-id supersession chains that don't terminate cleanly
- Mismatched IDs between layers
- Reviews referencing recommendations that no longer exist
- Domain coverage gaps (proposal exists, recommendation missing
  or vice versa)

### Phase C — Persona dogfood matrix (~1-2 days)

Eight starter personas, each driven through a multi-day pipeline
in an isolated test DB. See § 4 for the matrix.

For each persona:
- Build synthetic state (intent, target, memory, history)
- Build synthetic evidence stream (HRV, sleep, activity, intake)
- Run `hai pull → clean → daily → today` for N consecutive days
- Capture: actions, bands, escalations, rationale prose, audit chain
- Classify findings as: crash, validator rejection, action mismatch,
  band miscalibration, rationale incoherence, audit chain break

### Phase D — Codex external audit (parallel, maintainer-invoked)

Standard external-audit pattern. Audit prompt at
`reporting/plans/v0_1_10/codex_audit_prompt.md`. Specific question:

> *"Identify correctness, idempotency, and data-flow bugs across
> synthesis, projection, CLI mutation paths, and audit-chain
> integrity. Bonus: find places where the runtime makes assumptions
> that wouldn't hold across the user matrix in
> `verification/dogfood/personas/`. Out of scope: features,
> performance, doc nits."*

Codex sees what Claude misses, Claude sees what Codex misses.
Findings merge into the same `audit_findings.md`.

---

## 4. Starter persona matrix

Eight personas spanning the highest-leverage axes within the
in-scope user set.

| # | Persona | Age | Sex | Body | Sport mix | Goal | Source | History | What it stresses |
|---|---|---|---|---|---|---|---|---|---|
| P1 | Dom-baseline (control) | 19 | M | 84kg / 185cm | 3 lift + 3 run | Performance + recomp | intervals.icu | 14d onboarding | Reproduces known B1-B7 |
| P2 | Female marathoner | 32 | F | 62kg / 170cm | 5× endurance running | Performance | Full Garmin | 90d | Female protein/HRV deltas, endurance-only domain |
| P3 | Older recreational | 48 | M | 78kg / 178cm | 3-4× running | Fat loss + general fitness | intervals.icu | 12mo | Age threshold edge, established history |
| P4 | Strength-only cutter | 28 | M | 95kg / 180cm | 4× strength | Fat loss | Manual-only / CSV | 60d | High BMI, no wearable, no running pulls |
| P5 | Female multi-sport | 35 | F | 64kg / 168cm | Triathlon + S&C | Performance | Mixed (Garmin + manual swim) | 6mo | Cross-train, mixed sources, female competitive |
| P6 | Sporadic recomp | 26 | M | 72kg / 175cm | 2-3× inconsistent | Recomp | Mixed | 4mo with gaps | Sporadic logging, illness/vacation gaps |
| P7 | High-volume hybrid | 41 | M | 70kg / 178cm | 6× endurance + 2× strength | Performance peak | Full Garmin | 18mo | Training-load ceiling, ACWR extremes |
| P8 | Day-1 female lifter | 23 | F | 58kg / 165cm | 3× new strength | Muscle gain | Just installed | 0d | Cold start, female + muscle gain, day-1 UX |

**Coverage:**
- Sex: 4M, 4F.
- Age: 19, 23, 26, 28, 32, 35, 41, 48.
- Goal: performance ×3, recomp ×2, fat loss ×2, muscle gain ×1.
- Sport: all-rounder, endurance-only, older endurance, strength-only,
  multi-sport, mixed, hybrid extreme, new lifter.
- Source: intervals.icu, full Garmin, manual-only, mixed (all 4).
- History: day-0, 14d, 60d, 90d, 4mo, 6mo, 12mo, 18mo.

**Deliberately excluded:** clinical edge cases, pregnancy,
adolescent (<18), elderly (>55), chronic conditions.

**P8 priority note.** P8 (day-1 fresh install) is the highest
expected bug-finding density — cold-start paths in installable
software hide bugs because developers test against existing dev
environments. Female + muscle gain doubles its discovery value.

**P1 priority note.** P1 is a regression check, not a discovery
check. Lowest expected new findings; high value for confirming
existing B1-B7 reproduce in the harness.

---

## 5. Harness shape

New directory: `verification/dogfood/`

```
verification/dogfood/
├── README.md                       # how to run, what each persona does
├── personas/
│   ├── __init__.py
│   ├── base.py                     # PersonaSpec dataclass + builder protocol
│   ├── p1_dom_baseline.py
│   ├── p2_female_marathoner.py
│   ├── ...
│   └── p8_day1_female_lifter.py
├── runner.py                       # drives pull → clean → daily → today
├── findings.py                     # captures structured per-day output
└── fixtures/
    └── (synthetic CSVs per persona, deterministic)
```

**Isolation discipline:**
- Each persona gets its own DB at `/tmp/hai_persona_<id>.db`.
- `HAI_STATE_DB` env var pins the runner to the persona DB.
- Never reads or writes the maintainer's real state DB.
- `pytest` integration via `verification/tests/test_dogfood_smoke.py`
  that imports the runner but only spot-checks (full matrix runs
  outside CI).

**Reusability:**
- Once built, the harness is permanent regression infrastructure
  under `verification/dogfood/`.
- Every release runs all 8 personas as a pre-flight check.
- New personas added when new user-set assumptions are added.

---

## 6. Findings consolidation

Output: `reporting/plans/v0_1_10/audit_findings.md`

Schema per finding:

```
### F<N>. <one-line title>

**Source:** Phase A | Phase B | Phase C-P<persona> | Phase D (Codex)
**Severity:** crash | validator-reject | action-mismatch | band-miscalibration | rationale-incoherence | audit-chain-break | correctness | idempotency | type-safety | nit
**Blast radius:** which user shapes / which domains affected
**File:** path:line if known
**Description:** what's wrong
**Reproduction:** minimal steps
**Triage:** fix-now | defer-to-v0.2 | won't-fix | needs-design-discussion
```

Triage criteria:
- **fix-now** = correctness or audit-chain integrity bugs that
  affect any in-scope persona, AND fix is bounded (<2 days work).
- **defer-to-v0.2** = correctness bugs whose fix requires schema
  or contract changes beyond the v0.1.10 scope ceiling.
- **won't-fix** = bugs in out-of-scope user shapes (e.g. age <18).
- **needs-design-discussion** = semantic ambiguity, not clearly a
  bug.

When `audit_findings.md` is consolidated, v0.1.10 PLAN.md gets
written, and the standard four-round audit cycle opens.

---

## 7. What this plan deliberately does NOT include

- **No code changes to `src/health_agent_infra/`** until PLAN.md
  is written. The hunt is read-only on the runtime.
- **No skill rewrites.** Skills are out of scope for the bug hunt
  unless a persona finding implicates a skill specifically.
- **No new domains.** Body composition surface (B3 from morning
  briefing memory) stays deferred — it's a separate cycle.
- **No CLI surface changes.** `hai capabilities --json` should
  remain stable through the hunt; capability changes wait for
  PLAN.md.

---

## 8. Sequencing

1. This doc lands.
2. Phases A and C scaffold in parallel — Phase A reads code, Phase C
   builds harness skeleton + P1 + P8 (highest-priority personas
   per § 4).
3. Phase B runs after Phase C harness skeleton is alive (uses the
   runner against maintainer's real DB in read-only mode).
4. Phase D (Codex) fires whenever the maintainer chooses — does not
   block A/B/C.
5. All findings consolidate into `audit_findings.md`.
6. PLAN.md gets written based on consolidated findings.
7. Standard v0.1.X audit/response cycle opens.

---

## 9. Time estimate

- Phase A: ~1 day
- Phase B: ~half day
- Phase C: ~1-2 days (P1 + P8 first; rest as time allows)
- Phase D: external, async
- Findings consolidation + PLAN.md: ~half day

Total: 3-5 days of focused work before v0.1.10 PLAN.md opens.

This is a meaningful pre-investment. Justified because:
- The harness is permanent regression infrastructure with reuse value.
- v0.1.10 scope based on hunt findings is more credible than
  scope based on opportunistic B1-B7.
- Skipping the hunt risks shipping v0.1.10 and discovering the
  next 7 bugs the same way we discovered the first 7.

---

## 10. Open questions

- **Synthetic vs. real-world traces.** Personas are hand-crafted.
  Bugs they surface are *classifier-assumption bugs*, not
  *real-world data-quality bugs*. Should the harness eventually
  ingest anonymised real traces (Strava public, Garmin demo)?
  Defer decision to v0.2.
- **Persona realism review.** Hand-crafted fixtures are plausible,
  not actual. A sports-medicine reviewer would catch nuances.
  Out of scope for v0.1.10 per no-clinical-claims invariant — we
  hunt for "coherent classifier output" not "clinically optimal
  recommendation."
- **Harness output volume.** 8 personas × 14-30 day pipeline runs
  × 6 domains = a lot of triage. Mitigation: structured findings
  schema (§ 6) + automated anomaly detection (cross-persona
  pattern matching) before manual review.
