# v0.1.11 backlog

> **Status.** Backlog tracks items deferred from v0.1.10 + items
> scoped out of v0.1.11 PLAN.md. When v0.1.11 ships, items still
> open here roll forward into the next cycle's backlog.

---

## Items deferred from v0.1.10 PLAN.md

### Release-blocker-class items (audit-chain integrity)

These two were originally in v0.1.10 scope, did not land cleanly,
and were deferred per Codex implementation review round 1 + the
2026-04-28 rescope (`v0_1_10/PLAN.md` § 1.2). v0.1.11 is the
audit-chain integrity release; they gate v0.1.11 ship.

#### W-E — `hai daily` re-run state-change detection
**Source.** `v0_1_10/audit_findings.md` § F-B-02 + memory B7 +
Codex round 1 review F-CDX-IR-04.
**Severity.** audit-chain / correctness — release-blocker-class.

When the user re-logs intake the same day, `hai daily` should
produce a superseded `_v<N>` plan with refreshed rationale prose
and proposal-log rows. Today the rationale prose stays stale.

**Proposed approach.** State-fingerprint-based supersession:
hash the inputs (nutrition_intake / readiness / gym intake / clean
evidence) before synthesis. Match → no-op. Mismatch → produce
`_v<N>` with fresh proposal_log rows.

**Why deferred from v0.1.10.** Synthesis-path semantics; needed
design discussion. Doing it under release pressure was the wrong
shape. v0.1.11 PLAN.md scopes the design upfront.

**Proposed cycle:** v0.1.11 (release-blocker-class).

#### W-F — Audit-chain version-counter integrity
**Source.** `v0_1_10/audit_findings.md` § F-B-01 + Codex round 1
review F-CDX-IR-04.
**Severity.** audit-chain integrity — release-blocker-class.

A `_v0 → _v3` jump (skipping `_v2`) was observed during the audit-
chain probe. Hypothesis: the version counter increments on attempt
rather than on commit; partial writes leave gaps.

**Proposed approach.** Read the supersession path; localise the
increment site; ensure it advances only after successful commit.
Add a contract test that asserts every supersede produces
sequential versions.

**Why deferred from v0.1.10.** Investigative — root cause not yet
localised. Needed time to read the path carefully.

**Proposed cycle:** v0.1.11 (release-blocker-class).

### W-H2 — Mypy stylistic-class fixes
**Source.** `v0_1_10/PLAN.md` § 1.2 + tactical plan § 3.
**Severity.** type-safety / nit.

Approximately 10 mypy errors remaining after v0.1.11 W-H1. These
are stylistic-class: Literal abuse, redefinition warnings,
scenario-result type confusion. Lower correctness impact than W-H1.

**Proposed cycle:** v0.1.12 (per tactical plan § 3).

### F-B-04 — Domain coverage drift across supersession
**Source.** `v0_1_10/audit_findings.md` § F-B-04.
**Severity.** audit-chain semantic / interpretation.

A supersede that adds entirely new domain proposals (2026-04-24
chain went 2 domains → 6 domains) breaks the "supersession =
correction of same proposals" semantic. Possible fixes: require
domain-coverage stability across supersession, OR add a
`supersession_kind` field, OR document the current "whole-plan
replacement" semantic.

**Proposed cycle:** v0.1.12 W-U (per tactical plan § 3).

### F-CDX-IR-05 — Running-rollup provenance completeness
**Source.** `v0_1_10/codex_implementation_review_response.md`
§ F-CDX-IR-05.
**Severity.** correctness / provenance — concern (Codex's own
classification).

`aggregate_activities_to_daily_rollup` computes `total_duration_s`
and `session_count`, but `project_accepted_running_state_daily`
hardcodes both to `None` and stamps
`derivation_path="garmin_daily"` even for historical rows derived
from `running_activity`. The persona regression check confirmed
P2/P7 improved (running domain now produces actions instead of
universal defer), but provenance + rollup completeness is weaker
than the W-D-ext claim implied.

**Proposed approach.** Plumb `total_duration_s`, `session_count`,
and a derivation-path enum (`activity_rollup` vs `garmin_daily`)
through the projector. Add a test that asserts derivation_path
matches the upstream source.

**Proposed cycle:** v0.1.11 W-R (alongside the audit-chain work,
since it touches the projection layer and the provenance string is
a downstream `hai explain` audit field). See `v0_1_11/PLAN.md`
§ 2.11.

### F-CDX-IR-06 — Persona harness drift guards
**Source.** `v0_1_10/codex_implementation_review_response.md`
§ F-CDX-IR-06.
**Severity.** harness ergonomics — nit (Codex's own classification).

`verification/dogfood/synthetic_skill.py` hardcodes
`_DOMAIN_DEFAULT_ACTION`, `_STATUS_TO_ACTION`, and
`schema_version=f"{domain}_proposal.v1"`. The current values are
valid (Codex checked against `ALLOWED_ACTIONS_BY_DOMAIN`), and
schema drift would surface as `hai propose` failure. But the
harness doesn't import or test against the runtime contract
directly, so drift is detected only as noisy persona setup
failures after the fact.

**Proposed approach.** Replace hardcoded mappings with imports
from `core/validate.ALLOWED_ACTIONS_BY_DOMAIN` + the actual
proposal schema registry. Add a contract test that asserts the
harness's mappings cover every domain in the runtime.

**Proposed cycle:** v0.1.11 W-S. See `v0_1_11/PLAN.md` § 2.12.

### F-CDX-IR-R3-N1 — In-memory threshold injection bypasses load-time validation
**Source.** `v0_1_10/codex_implementation_review_round3_response.md`
note 1. Verdict was SHIP_WITH_NOTES; this was a documentation
note, not a release blocker.
**Severity.** trusted-seam audit — concern.

`load_thresholds()` validates the user-TOML boundary, but
`evaluate_nutrition_policy(thresholds=...)`,
`evaluate_recovery_policy(...)`, the synthesis primitives, and
the per-domain classify/policy modules all accept a
`thresholds: Optional[dict[str, Any]]` argument that bypasses
`_validate_threshold_types` when a caller constructs the dict
in-memory. Today this is a trusted seam used by tests and by
the production path that always flows from `load_thresholds()`.

**Proposed approach (W-T).**

1. Audit every call site of `evaluate_*` and per-domain
   `classify/policy` functions that passes a non-`None`
   `thresholds` argument. Categorise:
   - Production-flow caller → already validated transitively.
   - Test caller → trusted, no action needed.
   - Other (migrations, ad-hoc scripts, future paths) →
     surface for design discussion.
2. If any non-test, non-production-flow site exists, choose:
   - (a) Make `_validate_threshold_types` robust to partial
     defaults so it can run at every internal entry point.
   - (b) Wrap each entry point with a thin
     "load-or-pass-through-validated" helper.
   - (c) Document the trust boundary explicitly in the
     function docstring and accept the seam.
3. If only production + test callers exist (the likely outcome),
   document the seam in `core/config.py` module docstring +
   AGENTS.md "Settled Decisions" so the trust boundary is
   load-bearing knowledge, not implicit.

**Proposed cycle:** v0.1.11 W-T. Adds to the audit-cycle scope
without expanding the release thesis (audit-chain integrity is
the headline; this is a small additional sweep).

### F-C-05 — strength_status enum surfaceability
**Source.** `v0_1_10/audit_findings.md` § F-C-05.
**Severity.** documentation / API surface.

The runtime emits status values like `overreaching` without a
discoverable enum surface. Skill authors have to spelunk the code
or learn from running examples. Add per-domain status enum to
the capabilities manifest.

**Proposed cycle:** v0.1.12 W-V (per tactical plan § 3).

---

## Items deferred per strategic / scope discipline

### W52 / W53 / W58 — Weekly review + insight ledger + factuality gate
**Source.** Strategic plan § 7 Wave 2 + 2026-04-25 multi_release_roadmap.md.
**Status.** v0.2.0 wave per strategic plan. Not v0.1.x scope.

### W29 — `cli.py` split
**Source.** AGENTS.md § "Settled Decisions".
**Status.** Deferred per D4. Revisit when cli.py exceeds 10kloc OR
when external integration arrives.

### W30 — Capabilities manifest schema freeze
**Source.** AGENTS.md § "Settled Decisions".
**Status.** Deferred per D4. Revisit when first external consumer
lands.

---

## How this file evolves

- Items deferred from a closing PLAN.md land here with reason.
- When v0.1.11 ships and v0.1.12 PLAN.md opens, items here are
  re-triaged: in-scope for v0.1.12, deferred to v0.2+, or won't-fix.
- Items cut from v0.1.11 stay here with a "deferred to v0.1.12"
  note; do not silently delete them.

---

## v0.1.10 retro hook

(Populated post-v0.1.10 ship — not yet committed. Retro section
captures: what worked in v0.1.10, what didn't, what to keep, what
to change next cycle.)

**To capture:**
- Pre-PLAN bug-hunt pattern was high-yield (27 findings vs. ~7 from
  opportunistic). Keep.
- Persona harness build took most of the cycle's time. Future
  cycles benefit from existing harness; this was one-time cost.
- W-D-ext (running aggregator wiring) was a 30-line glue change
  that fixed the load-bearing bug. Lesson: search for
  implemented-but-never-wired code before assuming a feature is
  missing.
