# v0.1.8 — Maintainer's Analytical Review of Codex's Audit

> **Provenance.** Authored 2026-04-25 after Codex returned the
> v0.1.8 audit response (`codex_audit_response.md`) with a
> `REVISE_BEFORE_IMPLEMENTATION` verdict. PLAN.md was revised in
> the same cycle to integrate Codex's punch list. This document is
> the maintainer's rigorous review of that audit:
>
> 1. Verification of Codex's high-stakes corrections against the
>    actual codebase (do the file:line citations resolve?).
> 2. Spot-check of the external sources Codex grounded its
>    recommendations in (are the citations real?).
> 3. Architectural points Codex raised but didn't fully develop.
> 4. Implementation considerations Codex didn't address that
>    materially affect v0.1.8 sequencing.
> 5. Risk register — what could still go wrong if this plan ships
>    as-is.
> 6. A short list of refinements to PLAN.md the maintainer would
>    apply before implementation begins.
>
> This document is the comprehensive rigorous analytical layer
> Dom asked for after reading Codex's response. It does not change
> PLAN.md; it scrutinises and supplements it.

---

## 1. Verification of Codex's high-stakes corrections

### 1.1 W39: "the runtime ignores per-user threshold overrides"

**Codex's claim:** Maintainer's W39 framing was factually wrong.
Threshold loading already exists; the missing piece is
authoring/validation/diff/audit.

**Verification.** Confirmed against the codebase:

- `src/health_agent_infra/core/config.py:441-457` defines
  `_deep_merge(base, override)` recursively merging dicts.
- `src/health_agent_infra/core/config.py:460-484`
  `load_thresholds(path)` reads the user's TOML (defaulting to
  `user_config_path()` from line 430), then returns
  `_deep_merge(DEFAULT_THRESHOLDS, user_overrides)`. So user
  overrides DO take effect on every classifier call.
- `src/health_agent_infra/cli.py:3362-3375` `cmd_config_show`
  emits `{"source_path", "source_exists", "effective_thresholds"}`
  — the merged result, not the raw user file.

**Verdict.** Codex is correct. The maintainer's original W39
framing was factually wrong. The ACTUAL gap is:

- No `hai config validate` — bad TOML or invalid threshold values
  fail at first use, not at write time.
- No `hai config diff` — user can't see "what's the user override
  vs the default" without manually grepping `DEFAULT_THRESHOLDS`.
- No `hai config set <key> <value> --reason <text>` — there's no
  in-band authoring path; users must hand-edit TOML.
- No audit trail — threshold changes don't appear in any
  `runtime_event_log` row or JSONL audit.

PLAN.md's W39 rewrite addresses all four. Accepted.

### 1.2 W37: "skills should consume raw outcomes"

**Codex's claim:** Skills computing windowed outcome counts
violates the code-vs-skill boundary; that's deterministic
arithmetic which belongs to code.

**Verification.** Confirmed against the architecture doc:

- `reporting/docs/architecture.md:121-133` lists code-owned
  responsibilities including "Deterministic arithmetic (band
  classification, scoring, signal counting)."
- `reporting/docs/architecture.md:135-142` lists skill-owned
  responsibilities — composing rationale, asking clarifying
  questions, surfacing uncertainty, joint-rationale
  reconciliation.
- `reporting/docs/architecture.md:144-146` is explicit: "Skills
  never run arithmetic the runtime already ran. A skill that
  tries to compute a band has regressed into code's territory and
  should be rewritten."

A windowed outcome classifier ("≥4 of last 7 days followed but
felt worse → emit token X") is by definition arithmetic over
historical rows. It belongs in code.

**Verdict.** Codex is correct. The maintainer's original W37
design would have introduced a code-vs-skill boundary regression.
PLAN.md's replacement (W48 — code-owned `core/review/summary.py`
builder, skills only narrate the resulting tokens) restores the
boundary correctly. Accepted.

### 1.3 The "intent + target precondition" architectural argument

**Codex's claim:** Outcomes are uninterpretable without intent +
target. A "followed but felt worse" outcome means different things
depending on what the user intended (hard session vs easy) and
what target was active.

**Reasoning.** This is Codex's most important architectural call.
Walking through a concrete scenario validates it:

- Day 1: user logs `outcome: followed=true,
  self_reported_improvement=false`.
- Without intent context: was the recommendation "rest day," and
  the user followed it but felt restless because they wanted to
  train? Or was it "hard intervals," and they did it but felt
  exhausted?
- Without target context: are they in a calorie-deficit cut
  (where "followed but felt worse" is partly expected), or
  fuelling for a race (where it's a red flag)?
- Same outcome row → opposite skill rationales depending on the
  surrounding intent + target state.

The current snapshot has `accepted_*_state_daily` (vendor +
intake-derived evidence), `proposal_log` (what was proposed),
`recommendation_log` (what was committed). It does NOT have
durable user intent (what the user planned independently of the
agent's recommendation) or active targets (what the user was
trying to achieve).

**Verdict.** The argument is sound. Outcome consumption (W48)
needs Intent (W49) + Target (W50) ledgers underneath it to
produce skill rationales the user would recognise as correct.
Accepted.

This is also the strongest argument for the maintainer's
rewriting of v0.1.8's investment ordering: W48 + W49 + W50 are
**a foundational triple** that should land together rather than
W48 first and W49/W50 in v0.1.9. The PLAN.md sequencing reflects
this (W48 → W49 → W50 in positions 3–5 of the punch list).

---

## 2. External source spot-checks

Codex grounded several recommendations in external research. The
maintainer spot-checked the highest-leverage citation:

- **Google's "Anatomy of a Personal Health Agent"** —
  `https://research.google/pubs/the-anatomy-of-a-personal-health-agent/`
  resolves to a real paper at the cited URL. Authors include
  Vidya Srinivas, Jake Garrison, Ali Heydari, Akshay Paruchuri,
  Xin Liu, John Hernandez, Yun Liu, Hamid Palangi, Ahmed
  Metwally, Ken Gu, Jiening Zhan, Kumar Ayush, Hong Yu, Amy Lee,
  Qian He, Zhihan Zhang, Isaac Galatzer-Levy, Xavi Prieto,
  Andrew Barakat, Ben Graef, Yuzhe Yang, Daniel McDuff, Brent
  Winslow, Shwetak Patel, Girish Narayanswamy, Conor Heneghan,
  Max Xu, Jacqueline Shreibati, Mark Malhotra, Orson Xu, Tim
  Althoff, Tony Faranesh, Nova Hammerquist. Citation is real.
- **Local-first software (Kleppmann)**, **JITAI design (Nahum-
  Shani et al.)**, **BCT taxonomy (Michie et al.)**, **FDA
  general wellness guidance**, **WHO AI for health**, **HL7 FHIR
  Observation/Goal/CarePlan**, **Open mHealth schemas** — these
  are well-known references in the personal-health-data and
  digital-health-intervention spaces. Codex's framing of them as
  "alignment vocabulary, not dependencies" is the right
  positioning for a v0.1.x product.
- **Open Wearables**, **QS Ledger**, **StudyMe N-of-1 trial
  research**, **Lee et al. consumer sleep tracker accuracy** —
  the maintainer didn't fetch these directly but the framing
  Codex gives them is internally consistent and aligns with
  HAI's positioning doc (`reporting/docs/personal_health_agent_positioning.md`).

**Verdict.** External grounding is real and used appropriately.
None of the citations imply that v0.1.8 should adopt an external
schema as a dependency; they all serve as vocabulary alignment
for a project that intentionally stays local-first + governed.

---

## 3. Architectural points Codex raised but didn't fully develop

### 3.1 The "ledger" framing as a unifying abstraction

Codex's audit § "Ledger architecture recommendation" lists 10
ledgers:

1. Evidence
2. Accepted State
3. Intent (new)
4. Target (new)
5. Recommendation
6. Plan (partial today)
7. Review (existing, expanded)
8. Insight (new)
9. Artifact (new)
10. Data Quality (new)

This is more than a renaming exercise — it's a unifying
abstraction. Each ledger has the same skeleton:

- Append-only canonical rows with `*_id` primary keys.
- Status enum (`proposed | active | superseded | archived`) where
  applicable.
- `created_at` + `effective_at` + `review_after` + supersession
  links where temporal evolution matters.
- Source + ingest_actor for provenance.
- A snapshot field (`snapshot.<domain>.<ledger>` or top-level)
  for skill consumption.
- A read-only CLI surface (`hai <ledger> list / show / archive`).
- An optional write CLI surface for user-authored or
  agent-proposed mutations.

If v0.1.8 ships W49 + W50 + W51 with this skeleton, the project
gains a **template** for adding future ledgers (insight, artifact)
without re-deciding shape every time. The maintainer recommends
formalising this as `reporting/docs/ledger_template.md` in the
same release as W49 + W50, so contributors can extend the project
without re-deriving the contract.

### 3.2 The "skills narrate, code computes" line is sharper than it looks

Codex's W37 → W48 rewrite is the obvious case. But W48 + W49 +
W50 + W51 raise the same question for several other surfaces:

- **W43 `hai daily --explain`** — does the explain block compute
  per-stage rationale (code), or surface code-computed rationale
  for skills to expand on (skill)? The PLAN.md text says
  "thicker JSON only, no behaviour change" — that puts it on the
  code side, but the contract isn't explicit. Recommend pinning:
  `hai daily --explain` is read-only code emission; skills do not
  participate in its content.
- **W41 / W42 skill-harness scoring** — the rubric
  ("does the rationale cite every Phase A firing?") is itself
  arithmetic. So the rubric implementation lives in code; skills
  don't self-score.
- **W46 `hai stats --funnel`** — same as W38. Code consumes
  `runtime_event_log.context_json`; skills do not narrate funnel
  output.

The boundary holds across the whole release if maintained
consistently.

### 3.3 The cold-start window interacts with the data quality ledger

Codex's W51 (Data Quality Ledger) and the v0.1.6 W14 / v0.1.7
W24 cold-start asymmetry doc partially overlap. PLAN.md's W51
spec correctly names `cold_start_window_state` as a column on
`data_quality_daily`. But there's a deeper interaction the
maintainer wants to flag:

- The cold-start matrix (`reporting/docs/cold_start_policy_matrix.md`)
  documents that recovery + sleep + nutrition correctly DEFER on
  cold-start (no relaxation rule).
- The data-quality ledger's `cold_start_window_state` column
  surfaces the same fact at the row level.
- These should not drift. If the matrix says "recovery deferes
  during cold-start," the data-quality ledger's view of recovery
  for an in-window day should match.

The maintainer recommends adding a test
(`safety/tests/test_data_quality_cold_start_consistency.py`) that
ensures: for any day where the snapshot's `recovery.cold_start =
True`, the `data_quality_daily` row for `(user, date, recovery,
*)` reports `cold_start_window_state = "in_window"`. This catches
the silent drift class where one surface is updated but the other
isn't.

### 3.4 The non-goals doc update (W57) is more than housekeeping

Codex flagged W57 as a precondition: update `non_goals.md` before
any plan-proposal language enters docs. The maintainer agrees and
wants to expand on why:

- The current `non_goals.md` says training-plan + diet-plan
  generation is forbidden.
- W49 + W50 introduce ledgers that LOOK like training-plan +
  diet-plan storage to a casual reader. The CLI is `hai intent
  training add-session` and `hai target set --type
  calories_kcal --value 2200`.
- Without an updated non-goals doc, a contributor (or future
  agent) could plausibly assume the ledgers exist to support
  agent-proposed plans, then build that surface and find out
  later that the project's positioning forbids it.

The maintainer recommends W57 lands in the same commit as W49 +
W50 — not earlier, not later — so the new ledger surfaces and the
updated non-goals appear in the same diff.

---

## 4. Implementation considerations Codex didn't address

These are operational details that affect v0.1.8 sequencing but
weren't in Codex's audit response.

### 4.1 Snapshot schema_version bump

The current snapshot bundle carries
`snapshot.schema_version = "v1"`. W48 + W49 + W50 + W51 add
fields:

- `snapshot.<domain>.review_summary` (W48)
- `snapshot.intent` (top-level, active rows at as-of date) (W49)
- `snapshot.target` (top-level, active rows at as-of date) (W50)
- `snapshot.<domain>.data_quality` (W51)

These are additive, but they ARE a contract change. Per
agent-integration discipline, agents that pinned `schema_version
= "v1"` should see the version bump and decide whether to handle
v2 fields.

**Recommendation.** Bump to `snapshot.schema_version = "v2"` in
the same release as W48 + W49 + W50 + W51, with a transition
note in `reporting/docs/agent_integration.md` saying v1 consumers
ignore the new fields gracefully but should bump their pinned
version when they're ready to consume them.

### 4.2 Migration staging discipline

W49 + W50 + W51 + W48's `[policy.review_summary]` thresholds
block all touch the migration system:

- Migration 019: `intent_item` table
- Migration 020: `target` table
- Migration 021: `data_quality_daily` table
- Migration 022: `[policy.review_summary]` defaults block (this
  is in `DEFAULT_THRESHOLDS`, not a SQL migration — but it IS a
  config schema bump)

Each SQL migration must:

- Land in numerical order (the v0.1.6 W20 / v0.1.7 W23 gap-detection
  rules enforce this; if 020 is committed before 019, the next
  `hai state migrate` refuses).
- Include a corresponding entry in
  `safety/tests/test_migrations_roundtrip.py` so its DDL is
  golden-tested.
- Be reviewable as a single file per migration (the discovery
  logic depends on the `NNN_name.sql` filename pattern).

**Recommendation.** Land migrations in order: 019 (intent) → 020
(target) → 021 (data_quality), each in its own commit, each with
its golden test addition. The commit ordering matches the
implementation ordering of W49 → W50 → W51.

### 4.3 Test infrastructure scaling

v0.1.7 ships at 1943 tests. v0.1.8 will add ~80–120 more across:

- W48: ~15 tests (token computation × {7d, 14d windows, six
  outcome shapes})
- W49: ~10 tests (intent CLI surfaces, snapshot integration,
  supersession)
- W50: ~10 tests (target CLI surfaces, same shape)
- W51: ~8 tests (data_quality computation, cold-start
  consistency)
- W38: ~6 tests (hai stats --outcomes against seeded fixtures)
- W40: ~6 tests (hai stats --baselines)
- W39 rewrite: ~10 tests (config validate / diff / set)
- W46: ~6 tests (hai stats --funnel)
- W43: ~4 tests (--explain JSON shape, behaviour-unchanged)
- W45: ~12 tests (projector replay properties)
- W41 + W42: skill-harness fixtures + scoring (~12 tests)

**Recommendation.** Before W49 + W50 land, add a fixture-factory
module at `safety/tests/_fixtures/` with helpers like
`make_intent_row(...)`, `make_target_row(...)`,
`make_outcome_chain(...)` so per-workstream tests don't reinvent
seeding. This is a ~1 day investment that saves ~3–5 days
across the rest of v0.1.8. Codex didn't call this out but it's
material.

### 4.4 Token-threshold defaults must live in `thresholds.toml`

PLAN.md's W48 spec lists tokens (`outcome_pattern_recent_negative`
etc.) but doesn't pin where their thresholds live. Per the
maintainer's note in PLAN.md § 5.4 (now superseded by the revised
PLAN.md): these thresholds are policy, not code constants.

**Recommendation.** Extend `DEFAULT_THRESHOLDS` with:

```toml
[policy.review_summary]
window_days = 7                    # rolling window for token computation
min_denominator = 3                # below this, emit insufficient_denominator
recent_negative_threshold = 4      # ≥4 followed-but-worse triggers negative token
recent_positive_threshold = 4      # ≥4 followed-and-better triggers positive token
mixed_token_lower_bound = 0.4      # |followed-improved-rate - 0.5| < this → mixed
mixed_token_upper_bound = 0.6
```

This makes all four token thresholds user-tunable via
`thresholds.toml` overlay. It also makes the v0.1.8 W39 rewrite
(config validate/diff/set) more valuable — once tokens are
user-tunable, discoverable validation matters more.

### 4.5 PyPI publish (W44) is genuinely operator-only

W44 needs `twine upload` credentials. Maintainer can prep the
build (`python -m build`, `twine check dist/*`) but the actual
upload requires PyPI account access. The release proof template
(v0.1.7 W36) covers this — captures everything operator-facing.

**Recommendation.** Plan v0.1.8 implementation work as if W44
will block briefly when the operator runs the upload. All
downstream work (W48 + W49 + W50 onward) can proceed against the
local-install version `0.1.7` and re-verify against the PyPI
build once it lands. Don't sequentially block W48 on W44.

---

## 5. Risk register

What could go wrong if v0.1.8 ships PLAN.md as-is?

| Risk | Severity | Mitigation |
|---|---|---|
| W48 + W49 + W50 land but agents don't consume them because skill SKILL.md frontmatter doesn't grant access. | **High** | Update `recovery-readiness`, `running-readiness`, `sleep-quality`, `strength-readiness`, `stress-regulation`, `nutrition-alignment` `allowed-tools` to include `Bash(hai intent list *)`, `Bash(hai target list *)` BEFORE shipping. The drift validator (W25) catches missing CLI grants but won't catch missing snapshot-field consumption. |
| Snapshot v2 transition breaks an external agent that pinned v1. | **Medium** | Document in `agent_integration.md` that v1 consumers ignore additive fields gracefully. Don't break the v1 contract — only ADD fields. |
| W49 + W50 ship without W57 (non-goals update); a contributor builds agent-proposed plans on top. | **Medium** | Land W57 in the same PR as W49. Code review enforces. |
| W48's token thresholds go in code instead of `thresholds.toml`; users can't tune sensitivity. | **Medium** | Maintainer addition: bake `[policy.review_summary]` block into `DEFAULT_THRESHOLDS` in the same commit as W48. |
| Migration ordering races (e.g. 020 lands before 019 in a feature branch) cause `hai state migrate` to refuse. | **Low** (good — that's the gap-detection rule working) | Branch hygiene; the v0.1.6 W20 + v0.1.7 W23 gap detection is the safety net. |
| Test count grows by ~100; CI duration grows materially. | **Low–Medium** | Fixture factories (point 4.3) keep per-test cost low. Profile if total CI exceeds 90s. |
| W41 (skill-harness) blocks on operator-driven live capture; doesn't ship in v0.1.8. | **Medium** | Codex's deferred-tier acceptance (`safety/evals/skill_harness_blocker.md`) covers this — recovery + one second domain is the bar, not "all skills scored." Don't slip the v0.1.8 release on it. |
| W43 (`--explain`) drifts from the read-only contract because operators want it to compute new fields. | **Low** | Tests pin the "behaviour-unchanged" assertion. Code review on every PR that touches `cmd_daily`. |

---

## 6. Refinements the maintainer would apply to PLAN.md

Concrete edits the maintainer recommends to PLAN.md before
implementation begins:

1. **Add a § 0.5 "Snapshot v2 transition note"** documenting the
   schema_version bump and the additive-only contract. Link from
   W48 + W49 + W50 + W51 specs.
2. **Add a sentence to W48** pinning the
   `[policy.review_summary]` thresholds block in
   `DEFAULT_THRESHOLDS`. Include the four threshold keys
   (`window_days`, `min_denominator`, `recent_negative_threshold`,
   `recent_positive_threshold`).
3. **Add a sentence to W49** stating that per-domain skill
   `allowed-tools` must be extended to grant `Bash(hai intent
   list *)` in the same release. Same for W50 with `Bash(hai
   target list *)`.
4. **Add a sentence to W51** stating that the
   `cold_start_window_state` column must agree with
   `cold_start_policy_matrix.md`; cite the consistency test
   recommended in § 3.3 above.
5. **Add a § 5.5 "Fixture factory precondition"** stating that
   `safety/tests/_fixtures/` lands BEFORE W49 + W50 + W51 to
   avoid per-workstream seeding boilerplate.
6. **Ship a `reporting/docs/ledger_template.md`** in the same
   release as W49 + W50 — the unifying ledger skeleton (§ 3.1
   above).

The maintainer notes that all six refinements are additive to
PLAN.md and don't change the punch-list ordering or workstream
scope. They tighten the implementation contract.

---

## 7. Final assessment

Codex's audit is rigorous, internally consistent, evidence-cited
against the codebase, and grounded in real external research.
The two most important calls are correct:

1. **W37 cannot land as drafted** — skills must not run
   arithmetic. Replace with W48.
2. **Outcomes need intent + target context to be interpretable**
   — W48 alone is insufficient; W49 + W50 are the foundational
   triple.

The maintainer's W39 framing was factually wrong; Codex's
correction stands.

The ledger architecture (10 ledgers, three new in v0.1.8) is the
right unifying abstraction. The multi-release roadmap (v0.1.8 →
v0.5+) is sensible and respects the project's local-first +
governed + auditable positioning.

Six refinements (§ 6) tighten the implementation contract without
changing scope. The maintainer recommends applying them, then
proceeding to W57 → W44 → W48 → W49 → W50 → W51 → W38 → W40 →
W39 rewrite → W46 → W43 → W41 → W42 → W45 per PLAN.md § 4
sequencing.

**Maintainer verdict on Codex's audit:** ACCEPT with the six
refinements above. Implementation can begin once those land in
PLAN.md.
