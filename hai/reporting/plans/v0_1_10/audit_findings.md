# v0.1.10 Audit Findings

> **Live document.** Findings consolidated from Phases A (internal sweep),
> B (audit-chain probe), C (persona matrix), D (Codex external) per
> `PRE_AUDIT_PLAN.md`. Schema per § 6 of that doc.
>
> **Status as of 2026-04-27.** Phase A in progress — pytest baseline + ruff
> + bandit + mypy complete; threshold-consumer sweep complete. Phase B
> + Phase C pending. Phase D unscheduled.

---

## Phase A — Internal sweep findings

### Baseline state

- **pytest:** 2133 passed, 2 skipped, 0 failed in 60.59s.
  - Suite is green. Skipped tests are pre-existing.
- **mypy (default):** 35 errors across 15 files, 109 source files checked.
- **ruff (default):** 24 errors (22× F401 unused imports, 2× F841 unused
  locals).
- **bandit (-ll medium):** 17 issues (16× B608 SQL string-construction,
  1× B310 url-open scheme audit).

---

### F-A-01. Untyped threshold consumers — bool-as-number bug class

**Source:** Phase A — threshold/config consumer audit.
**Severity:** type-safety / correctness.
**Blast radius:** every domain classifier + synthesis policy that reads
numeric threshold leaves. Affects nutrition, recovery, running,
strength, stress synthesis paths.
**Files / lines:**

```
src/health_agent_infra/core/synthesis_policy.py:383-385
  int() on x7_cfg.get(...) — three sites
src/health_agent_infra/core/synthesis_policy.py:569-570
  float() on extreme-deficiency cfg — two sites
src/health_agent_infra/core/synthesis_policy.py:656-657, 699
  float() on ACWR thresholds — three sites
src/health_agent_infra/core/synthesis_policy.py:792
  float() on heavy_lower_body_min_volume
src/health_agent_infra/core/synthesis_policy.py:860-861, 919, 929, 970
  int() on intensity / body_battery thresholds — five sites
src/health_agent_infra/core/pull/garmin_live.py:160-163
  int() / float() / bool() on garmin retry config — four sites
src/health_agent_infra/domains/nutrition/policy.py:125-126
  float() on R-extreme-deficiency thresholds — two sites
src/health_agent_infra/domains/nutrition/classify.py:100-103
  float() on band thresholds — four sites
```

**Description:**
v0.1.9 R2-3 + R3-1 closed bool-as-number at the validator AND runtime
resolver for `policy.review_summary` only. The same class of bug exists
across every threshold consumer. A user threshold override of `true`
or `false` in `thresholds.toml` would silently coerce to 1 / 0 because
Python's `int(True) == 1`. v0.1.9 backlog B1 named this class but
deferred fix. Total sites surfaced: ≥22.

**Triage:** **fix-now**. Centralise typed access via a shared
`core/config/coerce.py` module (option A from v0.1.9 backlog) OR
validate `DEFAULT_THRESHOLDS` leaves at `load_thresholds` time
(option B). Recommend B — closes every path without per-site changes.

---

### F-A-02. `applied_action_mutation` write-only — dead code or missing return

**Source:** Phase A — ruff F841.
**Severity:** correctness (suspicious — likely dead intent or missing wire).
**Blast radius:** synthesis Phase A action-mutation path.
**File:** `src/health_agent_infra/core/synthesis_policy.py:1259, 1268, 1276`

**Description:**
`applied_action_mutation` is initialised to `False` at line 1259 and set
to `True` in two branches (lines 1268, 1276) — block-rule application,
soften-rule application — but never read anywhere in the source tree
(verified via grep). Either:
- It was supposed to be returned from `apply_phase_a` and the wire was
  dropped, leaving a silent contract violation downstream.
- It was supposed to gate a downstream action (e.g., "did Phase A
  actually mutate, so don't apply Phase B fallback") and that gate is
  missing.
- It is genuinely dead code from a refactor.

The current behaviour is silently the third option. Worth tracing whether
the intended downstream consumer exists in synthesis.py.

**Triage:** **fix-now** if intended consumer existed and was dropped;
**won't-fix** (delete the variable) if it was always dead. Needs
git-history archaeology.

---

### F-A-03. `cli.py:4389` adapter type confusion (also at line 204)

**Source:** Phase A — mypy.
**Severity:** correctness — potential runtime AttributeError on adapter
swap.
**Blast radius:** `hai pull` path when source is `intervals_icu`.
**File:** `src/health_agent_infra/cli.py:204, 4389`

**Description:**
A variable typed `GarminRecoveryReadinessAdapter` is assigned an
`IntervalsIcuAdapter` instance. mypy flags incompatible types in
assignment. If the variable is later treated through the Garmin
adapter's interface but the runtime instance is the intervals.icu
adapter, behaviour depends on duck-typed method overlap. Likely
asymmetric — could fail on Garmin-specific methods.

**Triage:** **fix-now** — type the variable as the adapter Protocol or
union, not a concrete class.

---

### F-A-04. `synthesis.py:373` `dict[str,Any] | None` assigned to non-None typed var

**Source:** Phase A — mypy.
**Severity:** correctness — None propagation risk.
**Blast radius:** synthesis path.
**File:** `src/health_agent_infra/core/synthesis.py:373`

**Description:**
mypy reports incompatible assignment: expression `dict[str, Any] | None`
assigned to variable typed `dict[str, Any]`. If the source can return
None and the consumer does not handle it, downstream `KeyError` or
`AttributeError` is possible. Worth tracing the assignment.

**Triage:** **fix-now** — narrow the type or guard None.

---

### F-A-05. `evals/runner.py:668-669` scenario-result type confusion

**Source:** Phase A — mypy.
**Severity:** correctness — suggests scoring path conflates two
distinct result types.
**Files / lines:**
- `src/health_agent_infra/evals/runner.py:668` — `SynthesisScenarioResult`
  assigned to `DomainScenarioResult`
- `src/health_agent_infra/evals/runner.py:669` — `score_synthesis_result`
  called with `DomainScenarioResult` arg (expects `SynthesisScenarioResult`)

**Description:**
The eval runner appears to have crossed wires between domain-scenario
and synthesis-scenario result types. mypy flags both an incompatible
assignment AND an incompatible call-site argument on adjacent lines.
Either (a) the type annotations are wrong but runtime works because
duck typing allows it, or (b) `score_synthesis_result` is sometimes
called with the wrong shape and produces incorrect scoring.

**Triage:** **fix-now** for mypy clean-up; **investigate** whether the
runtime path is actually mis-typed.

---

### F-A-06. `cli.py:4075, 4083` None-comparison operators

**Source:** Phase A — mypy.
**Severity:** correctness — runtime TypeError on None inputs.
**File:** `src/health_agent_infra/cli.py:4075, 4083`

**Description:**
Three errors flagged on these lines for `<=`, `>=`, `>` against
`Any | None` operands. If the input is None, comparison raises
TypeError at runtime. mypy notes "Both left and right operands are
unions" — guard or narrow.

**Triage:** **fix-now**.

---

### F-A-07. `cli.py:2957-2963` exercise taxonomy projection — None-into-required-str

**Source:** Phase A — mypy.
**Severity:** correctness — silent None propagation through to projection.
**File:** `src/health_agent_infra/cli.py:2957-2963`

**Description:**
Five mypy errors: `str | None` arguments passed to
`project_exercise_taxonomy_entry` which expects `str`. Affects
`exercise_id`, `canonical_name`, `primary_muscle_group`, `category`,
`equipment` parameters of `hai intake exercise`.

If the CLI does not validate non-None upstream of these lines, an empty
or omitted flag could push `None` into the projection layer and either
raise downstream or store NULL where the schema may not allow.

**Triage:** **fix-now** — argparse-level required validation OR
explicit non-None guard before projection call.

---

### F-A-08. `core/state/projector.py:1608` shadowed name

**Source:** Phase A — mypy.
**Severity:** maintenance / readability.
**File:** `src/health_agent_infra/core/state/projector.py:1608, 1528`

**Description:**
`days_touched` defined on line 1528 and redefined on line 1608. mypy
flags `[no-redef]`. May be intentional (different scopes) but worth
verifying — accidental shadow can mask logic bugs.

**Triage:** **needs-design-discussion** — verify whether shadow is
intentional. Not blocking.

---

### F-A-09. `core/memory/projector.py:61-62` and `cli.py:1963-1964` Literal-key abuse

**Source:** Phase A — mypy.
**Severity:** correctness / type-safety.
**Files:**
- `src/health_agent_infra/core/memory/projector.py:61-62`
- `src/health_agent_infra/cli.py:1963-1964`

**Description:**
A dict typed `dict[Literal['goal','preference','constraint','context'], int]`
is indexed with `'total'` (not in the Literal set). mypy correctly
flags this as invalid. Either the dict's type is too narrow (it should
include `'total'`), or the index is wrong. If the runtime ever inserts
a `'total'` aggregator, the type contract is broken — and downstream
consumers of `dict[str, int]` will see a missing key for any non-Literal
runtime addition.

**Triage:** **fix-now** — broaden the Literal set OR drop the `'total'`
index in favour of a separate field.

---

### F-A-10. `cli.py:372` Literal arg type for `complete_sync`

**Source:** Phase A — mypy.
**Severity:** type-safety.
**File:** `src/health_agent_infra/cli.py:372`

**Description:**
`complete_sync(status=...)` expects `Literal['ok','partial','failed']`
but receives a `str`. If the upstream value can be other strings, this
is a real correctness issue. If it is constrained but untyped, this is
a type-safety polish item.

**Triage:** **fix-now** — narrow the upstream type or assert before call.

---

### F-A-11. `core/state/runtime_event_log.py:54` int-of-Optional

**Source:** Phase A — mypy.
**Severity:** correctness — runtime TypeError on None.
**File:** `src/health_agent_infra/core/state/runtime_event_log.py:54`

**Description:**
`int()` argument is `int | None`. If None reaches this site, runtime
TypeError. Same pattern recurs at `state/projector.py:302, 2219` and
`doctor/checks.py:276` (`fromisoformat` on `Any | None`).

**Triage:** **fix-now** for all four sites.

---

### F-A-12. `evals/runner.py:354` sorted on Any|None values

**Source:** Phase A — mypy.
**Severity:** correctness — runtime TypeError on None in sort key.
**File:** `src/health_agent_infra/evals/runner.py:354`

**Description:**
`sorted` cannot resolve `<` for `Any | None`. If the iterable can
contain None, runtime crash.

**Triage:** **fix-now** — None-strip or default before sort.

---

### F-A-13. Bandit B608: SQL string-construction across 16 sites

**Source:** Phase A — bandit -ll.
**Severity:** medium (bandit) — but most are likely false positives.
**Blast radius:** read paths in `core/explain/queries.py`,
`core/intent/store.py`, `core/memory/store.py`, `core/state/projector.py`,
`core/state/projectors/running_activity.py`, `core/state/snapshot.py`,
`core/target/store.py`, `evals/runner.py`.
**Files / lines (16):**
```
core/explain/queries.py:452, 572, 585
core/intent/store.py:239, 402
core/memory/store.py:208
core/state/projector.py:390, 617
core/state/projectors/running_activity.py:151, 162
core/state/snapshot.py:97, 348, 352
core/target/store.py:219, 360
evals/runner.py:514
```

**Description:**
All 16 are bandit B608 — string-based SQL construction. The pattern is
typically `"SELECT … WHERE x IN (" + ",".join("?"*N) + ")"` — placeholder
templating for IN clauses, then parameterised values. This is the
*correct* pattern, not actual injection — but a single
non-placeholder string-interpolation in the same shape would slip past
manual review. Worth a code review of each site to confirm no user
input ever reaches the string-construction side.

**Triage:** **investigate** each site. Likely all false positives, but
the v0.1.10 cycle should produce an explicit determination per site
+ a `# nosec B608` comment with reasoning where intentional.

---

### F-A-14. Bandit B310: intervals.icu URL scheme not whitelisted

**Source:** Phase A — bandit.
**Severity:** medium (bandit), high (real concern if user input
contributes to URL construction).
**File:** `src/health_agent_infra/core/pull/intervals_icu.py:310`

**Description:**
`urllib.urlopen` (or equivalent) called without restricting allowed
schemes. If any path lets user input contribute to the URL, an
attacker could potentially route to `file://` or other schemes.
**Investigate** whether the URL is fully constructed from constants
+ trusted credentials.

**Triage:** **investigate**, then either **fix-now** (whitelist
schemes) or **document** as `# nosec B310` with reasoning.

---

### F-A-15. Ruff F401: 22 unused imports

**Source:** Phase A — ruff.
**Severity:** maintenance / nit.
**Blast radius:** trivial.
**Files (22):** see `cli.py:32, 46, 47, 72, 570, 5901`,
`core/intent/store.py:25`, `core/memory/store.py:27, 28`,
`core/review/summary.py:29`, `core/state/projector.py:37, 42, 52`,
`core/synthesis.py:45, 47, 49, 74`, `core/synthesis_policy.py:36`,
`domains/nutrition/intake.py:24`, `domains/recovery/policy.py:27`,
`domains/running/schemas.py:27 (×2)`.

**Triage:** **fix-now** — auto-fixable with `ruff check --fix`. Bulk
clean-up.

---

## Phase A summary so far

- **Real correctness concerns** (fix-now): F-A-01 (threshold type
  hardening), F-A-02 (write-only var), F-A-03 (adapter type confusion),
  F-A-04 (None propagation in synthesis), F-A-05 (eval scenario type
  confusion), F-A-06 (None comparisons), F-A-07 (exercise None-into-str),
  F-A-09 (Literal abuse), F-A-10 (Literal status arg), F-A-11
  (int-of-None pattern, 4 sites), F-A-12 (sorted on None).
- **Investigations needed**: F-A-13 (16 SQL sites), F-A-14
  (intervals.icu URL).
- **Maintenance / nits**: F-A-08 (shadowed name), F-A-15 (unused
  imports).

**Tests pass and no test regressions** — but the type-checker reveals
~15 sites where the runtime depends on values that could be None and
isn't guarded. Each is a latent crash bug waiting on a user input path
that produces None. Persona matrix (Phase C) will probably trigger
several of these.

---

## Phase B — Audit-chain integrity probe

Walked `hai explain --for-date <D> --user-id u_local_1 --plan-version all`
across 2026-04-23 through 2026-04-27.

### F-B-01. Non-sequential supersession version numbers

**Source:** Phase B — supersede chain walk.
**Severity:** audit-chain-break (governance).
**Blast radius:** every plan that has been re-synthesised more than
once in a day. Discoverable for any user who re-runs `hai daily`
multiple times after intake updates.
**Files:** `core/synthesis.py` (supersession version-increment path).

**Description:**
Walking the supersede chains:

| Date | Chain | Issue |
|---|---|---|
| 2026-04-23 | `plan_X → plan_X_v3` | **`_v2` missing** |
| 2026-04-24 | `plan_X → _v4 → _v5` | **`_v2` and `_v3` missing** |
| 2026-04-25 | single plan | OK |
| 2026-04-26 | single plan | OK |
| 2026-04-27 | single plan | But re-synth ran (see F-B-02) |

The chain head `plan_X` jumps directly to `_v3` and `_v4` — the
intermediate version IDs were either:
- Generated and then deleted (audit-chain integrity violation —
  supersedes pointers should be immutable history)
- Generated and orphaned (chain still walks via supersedes pointer
  but the orphans sit in the DB undiscoverable through `hai explain`)
- Never generated (version counter incremented without producing
  a row — counter advances on attempt, not commit)

Any of the three is a real defect. The third is most likely given
the same-day re-synth no-op observed in F-B-02.

**Repro:** `hai explain --for-date 2026-04-23 --plan-version all`
shows two plans whose IDs are `plan_2026-04-23_u_local_1` and
`plan_2026-04-23_u_local_1_v3`. There is no `_v2`.

**Triage:** **fix-now** — supersession version numbers are
audit-chain identifiers; gaps break the auditability invariant.
Either every increment must produce a row, or the version counter
must commit-coupled.

---

### F-B-02. Same-day `hai daily` re-run produces no supersede when state has materially changed

**Source:** Phase B + corroborates B7 from morning-briefing memory.
**Severity:** audit-chain-break + correctness.
**Blast radius:** any user who runs `hai intake nutrition --replace`
or other state-mutating commands and then re-runs `hai daily` on the
same day expecting an updated plan.
**Files:** `core/synthesis.py` (supersession decision path),
`cli.py` daily handler.

**Description:**
At 2026-04-27 17:13 UTC, after a verified state mutation (nutrition
intake superseded from 907→3266 kcal — verified in `hai state read
--domain nutrition`), I re-ran `hai pull → clean → daily → today`.
The synth output reported `superseded_prior: null` and produced the
same plan_id (`plan_2026-04-27_u_local_1`) with no version suffix.
`hai today` then rendered the **pre-mutation** rationale prose
("907 kcal / 73g protein, PARTIAL-DAY CAVEAT,
R-extreme-deficiency").

This is the exact pattern named B7 in the morning-briefing memory.
The synth path is failing to detect material state change as
grounds for supersession.

**Repro (deterministic):**
```bash
# pre: existing nutrition_intake row for today
hai intake nutrition --replace --calories X --protein-g Y --fat-g Z --carbs-g W --as-of <today>
hai state read --domain nutrition --since <today> --until <today>  # verify row updated
hai daily --as-of <today>  # observe: no supersede produced
hai today  # observe: pre-mutation prose
```

**Triage:** **fix-now**. Either:
- The synth path must check for state changes (proposal_log
  fingerprint, state-row-fingerprint) and supersede when detected.
- OR the synth path must regenerate prose unconditionally when
  re-run for an existing plan_id.
- OR the same-day re-run must be a hard error with an explicit
  `--force` / `--supersede` flag.

The current behaviour silently lies — state DB says one thing,
rendered plan says another. This is the highest-severity finding
in Phase B.

---

### F-B-03. Reviews not scheduled for 2026-04-25 and 2026-04-26

**Source:** Phase B — review reconciliation.
**Severity:** audit-chain integrity (review schedule gap).
**Blast radius:** any day where the maintainer didn't run
`hai review schedule` after `hai daily`.
**Files:** `cli.py` daily handler, `core/review/outcomes.py` schedule
path.

**Description:**
2026-04-23, 2026-04-24, 2026-04-27 each have 6 reviews scheduled
(matching 6 recs).
2026-04-25 and 2026-04-26 have 6 recs and **0 reviews**.

Either:
- Review scheduling is opt-in via `hai review schedule` and the
  maintainer didn't run it those days (probable — but the system
  should make this clear).
- Review scheduling is supposed to be automatic at `hai daily` time
  and is broken on certain days.
- The schedule ran but the rows didn't write.

If review scheduling is intended-automatic on `hai daily`, this is
a regression. If intended-manual, the user-facing surface should
make it discoverable (e.g., `hai today` should mention "no review
scheduled — run `hai review schedule`").

**Triage:** **investigate** first. Then **fix-now** if regression,
**document + UX fix** if intended-manual.

---

### F-B-04. Domain coverage changes mid-chain (proposals 2 → 6)

**Source:** Phase B — chain walk for 2026-04-24.
**Severity:** audit-chain semantic / interpretation.
**Blast radius:** plans whose v0 was generated with sparse
evidence and a later version generated with fuller evidence.
**Files:** `core/synthesis.py` (proposal completeness gate).

**Description:**
2026-04-24 chain walk:
- v0: 2 proposals, 2 planned_recs, 2 recs
- v4: 2 proposals (same as v0)
- v5: 6 proposals (full domain coverage)

A supersede that adds 4 entirely new domain proposals is not just
"correcting" the same proposal set — it is producing a structurally
different plan. The schema does not distinguish "supersession of
the same proposals with corrected values" from "supersession with
new domain coverage." The audit interpretation is ambiguous:
did the agent fix v4's nutrition recommendation in v5, or replace
v4 entirely with a different plan?

The maintainer's audit cycle relies on "every recommendation has a
supersede chain pointing to its predecessor in semantic continuity."
A 2 → 6 jump breaks that interpretation.

**Triage:** **needs-design-discussion**. Possible fixes:
- Require domain-coverage stability across supersession (block
  the supersede if domain set changed; force a fresh plan_id).
- Or: add a `supersession_kind` field
  (`refine` | `extend_coverage` | `replace`) to make the semantic
  explicit.
- Or: document the current "supersession = whole-plan replacement"
  semantic and make `hai explain` render it that way.

---

## Phase B summary

Phase B surfaced 4 findings, three of them audit-chain integrity
issues:
- **F-B-01** non-sequential version numbers (likely orphan/skip
  in version-counter logic)
- **F-B-02** confirms B7 — same-day re-run silently fails to
  supersede on state change
- **F-B-03** review scheduling gap (investigate before classifying)
- **F-B-04** domain-coverage drift across supersession (semantic
  ambiguity)

F-B-01 and F-B-02 alone are reason to expand v0.1.10 scope. They
break the load-bearing audit invariant in AGENTS.md governance.

---

## Phase C — Persona matrix

Built `verification/dogfood/` harness with 8 personas (P1-P8) per
`PRE_AUDIT_PLAN.md` § 4. Drove every persona through the full pipeline
(state init → memory + targets + intake seeding → pull → clean →
state snapshot → synthetic skill posts proposals → daily → today →
explain). Strict isolation per persona via `/tmp/hai_dogfood_run/<id>/state.db`.

### Cross-persona action matrix (final run, 2026-04-27)

```
persona                       recovery     running  sleep        strength     stress       nutrition
p1_dom_baseline               proceed      defer    maintain     ESCALATE     maintain     maintain
p2_female_marathoner          proceed      defer    maintain     defer        maintain     maintain
p3_older_recreational         proceed      defer    maintain     defer        maintain     maintain
p4_strength_only_cutter       defer        defer    defer        ESCALATE     maintain     maintain
p5_female_multisport          proceed      defer    maintain     ESCALATE     maintain     maintain
p6_sporadic_recomp            proceed      defer    maintain     ESCALATE     maintain     maintain
p7_high_volume_hybrid         proceed      defer    maintain     ESCALATE     maintain     maintain
p8_day1_female_lifter         defer        defer    defer        defer        maintain     defer
```

Crashes during harness build (now resolved with payload fixes, but
tracked as runtime findings since the production code expected
fields that user-facing flows don't always provide):

---

### F-C-01. `running_activity` projector requires `user_id` via direct dict access

**Source:** Phase C — harness payload mismatch.
**Severity:** correctness (KeyError + transaction rollback).
**Blast radius:** any pull adapter or synthetic flow that emits an
activity dict missing `user_id`.
**File:** `src/health_agent_infra/core/state/projectors/running_activity.py:105`

**Description:**
`project_activity` reads `activity["user_id"]` via direct subscript
(line 105), not `.get()`. If an activity dict from any future adapter
or test path lacks `user_id`, clean projection raises `KeyError:
'user_id'`, the entire clean transaction rolls back, and stdout still
emits the cleaned-evidence JSON — but state DB is empty.

The harness reproduced this when synthetic activities omitted
`user_id` (only `as_of_date`, `activity_type`, etc.). The intervals.icu
adapter does pass `user_id` because the upstream `IntervalsIcuActivity.
as_dict()` always includes it; but the contract is implicit, not
enforced by validation.

**Reproduction:**
```python
activity = {
    "activity_id": "test_001",
    "activity_type": "Run",
    "as_of_date": "2026-04-27",
    "distance_m": 5000,
    "elapsed_time_s": 1800,
    # user_id deliberately omitted
}
project_activity(conn, activity=activity)  # KeyError: 'user_id'
```

**Triage:** **fix-now**. Either `.get()` with explicit `if not user_id:
raise ValidationError(...)`, or a Pydantic-style schema validator at
the projector entry that produces a clear contract violation rather
than a `KeyError`. Same hardening pattern used elsewhere for clean
inputs.

---

### F-C-02. `running_activity` projector requires `raw_json` via direct dict access

**Source:** Phase C — second harness payload mismatch.
**Severity:** correctness (same class as F-C-01).
**File:** `src/health_agent_infra/core/state/projectors/running_activity.py`

**Description:**
After fixing F-C-01 (added `user_id` to synthetic activities), clean
projection rolled back again with `KeyError: 'raw_json'`. Same direct
dict access pattern. Other fields read via `.get()` are safe; only
`activity_id`, `user_id`, and `raw_json` use direct `[]`. Any of the
three missing produces a hard rollback.

**Triage:** **fix-now**. Bundle with F-C-01 — apply the same
validation pattern to the full set of required keys.

---

### F-C-03. Running domain treats users as `cold_start: True` even with `running_activity` rows present

**Source:** Phase C — snapshot inspection across P1, P2, P3, P7.
**Severity:** band-miscalibration / semantic — produces "defer
running" universally.
**Blast radius:** **every user with intervals.icu running activities
but no daily-summary `distance_m` populated**. Confirms the
maintainer's own state — `hai today` defers running every day.
**Files:** `src/health_agent_infra/core/state/projector.py:409` —
`project_accepted_running_state_daily`.

**Description:**
Every persona that has logged run activities (P1: 1 run, P2: 3
runs, P3: 2 runs, P7: 3 runs) appears in the snapshot's
`running.activities_history` list — but the running domain shows
`cold_start: True`, `history_days: 0`, `running_readiness_status:
'unknown'`, and produces `defer_decision_insufficient_signal` for
every persona regardless of how rich their activity history is.

Root cause: `project_accepted_running_state_daily` reads
`raw_row.get("distance_m")`, `moderate_intensity_min`,
`vigorous_intensity_min` from the **daily summary row only**.
Per-activity rows in `running_activity` are never aggregated into
`accepted_running_state_daily`. The running classifier reads the
daily-state table; activities never reach it.

The maintainer's recurring "Running deferred — no run found" output
across many days is a symptom of this same bug. Earlier audit cycles
treated it as missing data; the persona harness shows it as a real
projection-layer gap.

**Reproduction:**
1. Build a state DB with `running_activity` rows but no
   `accepted_running_state_daily` rows.
2. Run `hai state snapshot` and `hai daily`.
3. Observe `running.cold_start: True`, `defer_decision_insufficient_signal`.

**Triage:** **fix-now** (high impact). Either:
- Add an aggregator that pulls `running_activity` totals into
  `accepted_running_state_daily` per as_of_date.
- Or change the classifier to read from `running_activity` directly
  when the daily-state row is missing or zero.

Either way, the system currently has a documented load-bearing gap
where the running domain effectively never produces a useful
recommendation for users on intervals.icu.

---

### F-C-04. R-volume-spike (B2) reproduces across 6 of 8 personas

**Source:** Phase C — strength escalation across diverse personas.
**Severity:** band-miscalibration.
**Blast radius:** every user with logged strength history short of
the rule's volume-spike threshold's implicit baseline.
**Files:** `src/health_agent_infra/core/synthesis_policy.py` (X-rule),
`src/health_agent_infra/domains/strength/policy.py`.

**Description:**
B2 in the morning-briefing memory was discovered against Dom's 14-day
onboarding. The persona harness shows this rule fires across SIX
personas: P1 (19M, 14d, 3×/wk), P4 (28M, 60d, 4×/wk), P5 (35F, 180d,
2×/wk), P6 (26M, 120d, 2×/wk), P7 (41M, 540d, 2×/wk). Even P7 with
18 months of history triggers because his 7-day vs 28-day session
ratio + the volume-spike threshold combine without a coverage gate
that requires N sessions in the lookback window.

This is not "thin history" — the rule fires for any user whose
recent training pattern sits above the static threshold relative to
their averaged baseline. The escalation produces
`escalate_for_user_review` on what is, for these personas, completely
ordinary training.

**Triage:** **fix-now**. Add a minimum-coverage gate to R-volume-spike
(e.g., require `sessions_last_28d >= 8` before the rule can fire),
OR change the rule to fire on absolute volume thresholds rather than
ratios.

---

### F-C-05. P4 strength_status `overreaching` is not in the action enum mapping

**Source:** Phase C — synthetic skill mapping audit.
**Severity:** action-mismatch / nit (skill stand-in).
**Blast radius:** harness only — this is a finding *about* the
synthetic skill, not the runtime.
**Files:** `verification/dogfood/synthetic_skill.py`.

**Description:**
P4's classified_state produced `strength_status: 'overreaching'`. The
synthetic skill's `_STATUS_TO_ACTION` table didn't include this value,
so it fell back to `proceed_with_planned_session` — which the
synthesizer's X-rule then forced to `escalate_for_user_review`. The
final answer was correct (escalation) but the intermediate path was
luck — a different domain might mishandle an unknown status by
producing a `won't-validate` action.

This signals that **the runtime's classifier emits status values
without a discoverable enum surface** — there is no `hai
capabilities --json` field that lists "valid `strength_status`
values." The skill author has to either spelunk the code or learn
each value from running examples.

**Triage:** **needs-design-discussion**. Either:
- Add per-domain status enum to the capabilities manifest (small
  schema change, broad benefit).
- Or document the status enum surface in the per-domain skill
  docstrings.

---

### F-C-06. Cross-persona universal stress = `maintain_routine`

**Source:** Phase C — observation.
**Severity:** nit / informational.

**Description:**
Every persona returned `stress: maintain_routine`. This is not a bug —
the synthetic stress score (1-3 across personas) is uniformly
"manageable" — but it's a coverage gap in the persona matrix. We did
not include a persona with elevated stress signals (manual_stress
high, body_battery low). Future expansion of the matrix should add
one.

**Triage:** **won't-fix** (matrix expansion item, not a runtime bug).

---

### F-C-07. Day-1 fresh install (P8) produces clean output

**Source:** Phase C — observation.
**Severity:** informational (positive).

**Description:**
P8 (zero-history fresh install, female muscle gain) produces clean
output: 5 domains defer cleanly, stress maintains routine (manual
score logged at 2). No crashes, no validator rejections, no
unexpected actions. The day-1 cold-start path works as designed.

This was the highest-expected-bug-yield persona in the matrix; it
turned out to be the cleanest. Worth knowing — the cold-start path
is well-protected.

**Triage:** no action.

---

### F-C-08. `hai intake gym` requires `exercise_name` not `exercise` in `--session-json` payload

**Source:** Phase C — harness validation error.
**Severity:** type-safety / documentation.
**Files:** `src/health_agent_infra/cli.py` (intake gym handler),
`src/health_agent_infra/domains/strength/intake.py`.

**Description:**
The `--session-json` flag accepts a JSON file with a `sets:[...]`
array. Each set's "exercise" field is named `exercise_name` in the
schema, but `hai intake gym --help` shows `--exercise` as the
per-set flag (singular without `_name`). A user reading help output
would write `"exercise": "Bench"` and get rejected with `intake gym
rejected: sets[0] missing required key: 'exercise_name'`.

Inconsistent naming between the CLI flag and the JSON payload is
a usability cliff — either the CLI flag should be `--exercise-name`
(matching schema) or the JSON should accept `exercise` as an alias.

**Triage:** **fix-now**. Cleanest fix: accept both `exercise` and
`exercise_name` keys in the JSON payload, with explicit documentation.

---

## Phase C summary

Persona harness is now operational permanent regression infrastructure
under `verification/dogfood/`. Final run: 8 personas, 0 crashes, 3
findings flagged by the auto-detector + 5 additional findings
surfaced during build (F-C-01 through F-C-08).

**Highest-value findings:**
- **F-C-03** — running domain doesn't aggregate per-activity rows into
  daily state. Affects every intervals.icu user.
- **F-C-04** — B2 confirmed across 6 personas; not a "thin history"
  edge case but a systematic miscalibration.
- **F-C-01 + F-C-02** — projector direct dict access without
  validation; future adapter integration risk.

---

## Phase D — Codex external audit

_Status: prompt drafted, awaiting maintainer invocation._
