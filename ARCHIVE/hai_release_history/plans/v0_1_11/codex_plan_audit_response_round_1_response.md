# Maintainer Response — v0.1.11 Plan Audit Round 1

> **Authored 2026-04-28** by Claude in response to Codex's
> `codex_plan_audit_response.md` (verdict:
> `PLAN_COHERENT_WITH_REVISIONS`, 10 findings, 3 open questions
> for maintainer).
>
> **Status.** Triage complete. 9 of 10 findings → accept-with-
> revision (Claude can apply autonomously). 1 finding (F-PLAN-09)
> + all 3 open questions → maintainer decisions required before
> Round 2.

---

## 1. Triage summary

| Finding | Disposition | Owner |
|---|---|---|
| F-PLAN-01 D11 handoff gate | **Accept-with-revision** | Claude applies |
| F-PLAN-02 Demo `base_dir` isolation | **Accept-with-revision** | Claude applies |
| F-PLAN-03 Marker fail-closed + refusal matrix | **Accept-with-revision** | Claude applies |
| F-PLAN-04 W-V sequencing | **Accept-with-revision** (split into W-Va / W-Vb) | Claude applies |
| F-PLAN-05 W-V resizing | **Accept-with-revision** (4-6 days, headroom note) | Claude applies |
| F-PLAN-06 W-W read consistency | **Accept-with-revision** | Claude applies |
| F-PLAN-07 Capabilities scoping + path | **Accept-with-revision** | Claude applies |
| F-PLAN-08 Demo regression ship gate | **Accept-with-revision** | Claude applies |
| F-PLAN-09 W-F fresh-day contract | **Maintainer decision required** | Dom answers Q-A below |
| F-PLAN-10 W-B D12 coercer | **Accept-with-revision** | Claude applies |
| OQ-1 W-V release-blocker class? | **Maintainer decision required** | Dom answers Q-B below |
| OQ-2 Demo mode isolation scope | **Maintainer decision required** | Dom answers Q-C below |
| OQ-3 D14 promotion + timing | **Maintainer decision required** | Dom answers Q-D below |

---

## 2. Per-finding response

### F-PLAN-01 — D11 handoff gate

**Accept.** Codex is right that the current banner makes the plan-
audit look like a *replacement* for Phase 0, when actually Phase 0
must still be able to revise or abort scope.

**Revision applied (after maintainer signoff):** rewrite the cycle
pattern in PLAN.md as:

```
1. PLAN.md draft authored (this file).
2. Codex plan audit.                          ← review THIS file
3. Maintainer response + PLAN.md revisions.
4. Phase 0 (D11) bug hunt opens.              ← code-side investigation
   ↳ audit_findings.md consolidates findings.
5. PRE-IMPLEMENTATION GATE: maintainer reads audit_findings.md.
   ↳ If findings invalidate scope → revise PLAN.md or abort cycle.
   ↳ Otherwise → cycle opens for implementation.
6. Implementation rounds (Codex round 1, response, round 2…).
7. RELEASE_PROOF.md + REPORT.md.
```

The gate at step 5 is the explicit revisable/abortable point. Add
a named field to `audit_findings.md` schema: every Phase 0 finding
gets a `cycle_impact: "in-scope" | "revises-scope" | "aborts-cycle"`.

### F-PLAN-02 — Demo mode isolates the DB but not `base_dir`

**Accept.** This is a real correctness bug in the W-V design that
I missed. `~/.health_agent` holds `*_proposals.jsonl`,
`gym_sessions.jsonl`, `nutrition_intake.jsonl`,
`review_events.jsonl`, etc. — all governed mutation surfaces per
AGENTS.md. A demo can leave the DB checksum unchanged but pollute
the JSONL history.

**Revision applied:**

- W-V marker schema gains `scratch_base_dir`. Default:
  `/tmp/hai_demo_<ts>/health_agent_root/`.
- Resolver override covers both `resolve_db_path()` AND
  `resolve_base_dir()` (and any other persistence-root resolvers
  in the codebase — to be enumerated during implementation).
- Test additions: run `hai intake nutrition`, `hai propose`,
  `hai review schedule`, `hai daily` all in demo mode; assert real
  DB checksum + real `~/.health_agent` tree are byte-identical
  before and after.

### F-PLAN-03 — Marker fail-modes are fail-open

**Accept.** Critical. Default Python file-open fallback to real
state if marker is corrupt is exactly the failure mode the feature
must NOT have.

**Revision applied:**

- Add fail-closed rule to W-V: if a demo marker file exists at
  `~/.health_agent/demo_session.json` but cannot be parsed, points
  at a missing scratch DB, or has a stale-but-claimed-active flag,
  every CLI command except `hai demo end` and `hai demo cleanup`
  exits USER_INPUT without touching real state. Surfaced with a
  clear error.
- Tests: corrupt marker → refusal; missing scratch DB → refusal;
  stale active marker (>72h) → refusal until cleanup.
- **Refusal matrix added to W-V** (replaces the loose `hai pull`
  + `hai auth *` enumeration):

| Behaviour | Commands |
|---|---|
| Allowed (against scratch state) | `hai today`, `hai daily --skip-pull --source csv`, `hai propose`, `hai intake *`, `hai explain`, `hai state read/snapshot`, `hai memory *`, `hai intent list`, `hai target list`, `hai stats`, `hai capabilities`, `hai doctor` (without `--deep` probe — see below), `hai demo *` |
| Refused — network | `hai pull --source intervals_icu`, `hai pull --source garmin_live`, `hai pull --live`, `hai daily --source intervals_icu`, `hai daily --source garmin_live`, `hai daily --live`, `hai doctor --deep` (needs network probe) |
| Refused — credentials/keyring | `hai auth garmin`, `hai auth intervals-icu`, `hai init --with-auth`, `hai init --with-first-pull` |
| Refused — operator/installer | `hai state init`, `hai state migrate`, `hai state reproject`, `hai setup-skills`, `hai config init`, `hai intent commit`, `hai intent archive`, `hai target commit`, `hai target archive` |
| Cleanup-only | `hai demo end`, `hai demo cleanup` |

- Fix file-list: `core/auth/*.py` does not exist; the actual
  surface is `cli.py` auth-handler branches plus
  `core/credentials.py` (or wherever the keyring helper lives —
  enumerate during implementation).

### F-PLAN-04 — W-V is sequenced too late

**Accept.** Codex's split recommendation is the cleaner path.

**Revision applied (W-V → W-Va + W-Vb):**

- **W-Va** (early, ~2-3 days, item #5 in revised sequencing):
  - Marker file lifecycle (`hai demo start --persona <name>` /
    `--blank`, `hai demo end`, `hai demo cleanup`).
  - Fail-closed marker parsing.
  - DB-path + base-dir resolver override.
  - Refusal matrix enforcement.
  - Stderr banner.
  - Network/credential refusal.
  - Tests: lifecycle + fail-closed + isolation (real DB +
    base-dir checksum stable across the entire matrix).
- **W-Vb** (late, ~2-3 days, item #14 after W-O personas):
  - Persona fixture loading (depends on W-O's
    `build_demo_fixture()` contract).
  - Archive behaviour on `hai demo end`.
  - Cleanup polish (stale-session detection thresholds,
    archived-DB rotation policy).
  - Demo-doc integration (W-Z hard-deps on this).

**W-Va lands at sequencing item #5** (after smoke-clearers W-N,
W-L, W-K, W-Q), before any other workstream that touches the CLI
surface. Other workstreams compose against the indirection from
the start.

### F-PLAN-05 — W-V under-sized

**Accept.** Codex is right that 2-4 days under-counted the surface
once F-PLAN-02 + F-PLAN-03 are folded in.

**Revision applied:**

- W-Va: 2-3 days.
- W-Vb: 2-3 days.
- W-V total: **4-6 days** (was 2-4).
- New cycle estimate: **22-30 days** (was 20-27).
- **Headroom note** added to the total estimate: "W-P property
  tests may surface bugs that bloat scope; if more than 3
  correctness-class findings emerge, cycle can absorb them by
  deferring W-Vb to v0.1.12. W-Va must ship — partial unsafe demo
  mode blocks ship."
- W-Vb is **deferrable as a whole** to v0.1.12 (with named-defer
  ship gate). W-Va is **not deferrable** once W-V is in scope —
  see Q-B below for blocker-class question.

### F-PLAN-06 — W-W read consistency contract

**Accept.** Race condition I didn't address.

**Revision applied:**

- W-W approach gains: snapshot-derived gaps run inside a single
  read transaction over SQLite. JSONL tail reads are bounded by
  an `as_of` timestamp captured at transaction start. The
  resulting `Gap` objects carry a new `snapshot_read_at: <ISO-8601>`
  field for audit trail.
- Test addition: simulate a `hai intake gym` mutation landing
  between accepted-state read and JSONL tail read (achievable via
  `multiprocessing` + sleep injection in the gap-derivation path).
  Assert deterministic output: gaps reflect either the pre-write
  state OR the post-write state, never a mix.
- Update F-PLAN-08 demo regression gate to include a concurrency
  smoke-test on `hai intake gaps --from-state-snapshot`.

### F-PLAN-07 — Capabilities under-scoped + wrong path

**Accept.** Real path bug. `core/cli/capabilities.py` does not
exist; the actual builder is `core/capabilities/walker.py` with
`render.py` for markdown emission.

**Revision applied:**

- **W-S file list** corrected and extended to:
  - `src/health_agent_infra/core/capabilities/walker.py`
  - `src/health_agent_infra/core/capabilities/render.py`
  - `verification/tests/test_capabilities_*.py`
  - `reporting/docs/agent_cli_contract.md` (regenerated)
  - `reporting/docs/agent_integration.md` (touched if it
    references the manifest shape)
- **W-V, W-W, W-X, W-Y all gain a "capabilities update" line
  item** in their files-changed sections:
  - W-V: walker.py (new `hai demo` subcommand rows), render.md
    update, agent_cli_contract.md regeneration, capabilities tests.
  - W-W: walker.py (new `--from-state-snapshot` /
    `--allow-stale-snapshot` flags on `hai intake gaps`),
    capabilities tests.
  - W-X: walker.py (new `--deep` flag on `hai doctor`,
    `auth_*.probe` row schema), capabilities tests.
  - W-Y: walker.py (alias enumeration on `hai pull` /
    `hai explain`), capabilities tests.
- **Ship gate reword** (was "regenerates without diff against
  manifest schema"; now): "manifest JSON and generated markdown
  are updated; tests prove the additive `domain_proposal_contracts`
  top-level block does not require freezing `agent_cli_contract.v1`
  (W30 settled decision preserved). Manifest-as-doc regenerator
  produces deterministic output."

### F-PLAN-08 — Demo fold-in success absent from ship gates

**Accept.** Falsifier needed.

**Revision applied — new ship gate added:**

> **Demo regression gate.** Run every command snippet in the new
> `reporting/docs/demo_flow.md` against `hai demo start --persona
> p1_endurance_runner`. Assert:
> - Every snippet executes without modification.
> - No live network call attempted (CSV-only adapter active).
> - Real DB checksum + real `~/.health_agent` tree byte-identical
>   before / after.
> - `hai doctor --deep` correctly identifies broken-auth state if
>   the persona fixture stubs in a 403-returning credential
>   surface.
> - `hai intake gaps --from-state-snapshot` emits gaps with
>   `derived_from: "state_snapshot"` and `snapshot_read_at`
>   populated.
> - `hai daily --supersede` on a fresh demo-day produces a
>   canonical plan id, not `_v2`.

This is the falsifier for the demo fold-ins.

### F-PLAN-09 — W-F fresh-day supersede contract is ambiguous

**Maintainer decision required (Q-A below).**

Codex is right that I left "either silent fall-through OR
USER_INPUT" as cycle-internal discretion for a release-blocker-
class path. That's a contract decision that belongs to the
maintainer.

**My recommendation: option (b) — explicit USER_INPUT error.**

Reasoning:
- The audit-chain-integrity thesis favours explicit failures.
- `--supersede` is a load-bearing flag; passing it in error should
  be loud, not silent.
- Existing `hai propose` + `hai intent commit` patterns already
  return USER_INPUT on contract violations; consistent.
- Forgiving fall-through hides programming errors in agents that
  unconditionally pass `--supersede`.

But option (a) is defensible if you'd rather optimise for
ergonomics. **See Q-A below.**

### F-PLAN-10 — W-B missing D12 coercer

**Accept.** D12 violation. Adding the threshold without the
coercer is exactly the bool-as-int class.

**Revision applied:**

- W-B approach gains: `core.config.coerce_int` resolution for
  `r_volume_spike_min_sessions_last_28d`.
- W-B tests gain: boundary tests at 7/8/9 sessions; user-override
  of `true` / `false` rejected as numeric threshold.
- W-B DEFAULT_THRESHOLDS entry documents the coercer requirement
  inline.

---

## 3. Open questions for maintainer (4 decisions)

### Q-A. F-PLAN-09 — W-F fresh-day `--supersede` contract

When `hai daily --supersede` is invoked on a date with no
canonical plan:

- **(a) Silent first-version semantics.** Treat as if `--supersede`
  was not passed; write canonical `plan_<date>_<user_id>` cleanly.
  Forgiving but hides intent.
- **(b) Explicit USER_INPUT error.** Refuse with a clear message
  ("no canonical plan to supersede for date X"); user re-runs
  without `--supersede`. Loud, auditable, consistent with other
  contract-violation paths. **Claude's recommendation.**

### Q-B. OQ-1 — Is W-V (or W-Va specifically) release-blocker class?

Currently W-E + W-F are the only blocker-class items. With
F-PLAN-02 + F-PLAN-03 included, W-Va has the same "if half-broken,
actively destroys real user state" property.

- **(a) Yes, W-Va is blocker-class.** Demo mode that pollutes the
  real DB / base_dir is worse than no demo mode. **Claude's
  recommendation.**
- **(b) No, W-V is deferrable as a whole.** If the cycle runs hot,
  defer all of W-V to v0.1.12 (S-DEMO-02 doc + W-O persona work
  still ships).

If (a): W-Vb is still deferrable (with named-defer gate); W-Va is
not.

### Q-C. OQ-2 — Demo mode isolation scope

What additional persistence surfaces should demo mode isolate
beyond DB + `base_dir`?

| Surface | Isolate? | Notes |
|---|---|---|
| `~/.local/share/health_agent_infra/state.db` | Yes (already in W-V) | Core mutation target |
| `~/.health_agent/*.jsonl` (proposal, intake, review logs) | Yes (added per F-PLAN-02) | Governed mutation surface |
| User config (`~/Library/Application Support/hai/thresholds.toml`) | **?** | Read-mostly; demo could write a scratch override |
| Skills install dir (`~/.claude/skills/`) | No | Install-time, not runtime-mutated |
| Keyring (Garmin / intervals.icu credentials) | **Refuse, not isolate** (already in W-V) | Don't write fake creds |

**Claude's recommendation:** isolate config (write a scratch
`thresholds.toml` if the persona fixture wants to override
defaults); leave skills + keyring as already-handled. Tracks
"every governed persistence surface routes through the marker."

### Q-D. OQ-3 — Plan-audit as D14 settled decision

Should the pre-cycle Codex plan audit become a permanent D14?

- **(a) Yes, promote to D14.** Substantive PLAN.md revisions get a
  Codex plan-audit before the cycle opens. Runs **before** Phase 0
  (catches structural issues so Phase 0 can investigate against a
  coherent plan). **Claude's recommendation.**
- **(b) No, keep the v0.1.11 plan-audit as a one-off.** Re-evaluate
  after the cycle ships.
- **(c) Yes, but run it after Phase 0** (so plan-audit reviews the
  PLAN with the bug-hunt findings already integrated). Riskier
  because Phase 0 has no plan-coherence gate to reject scope
  early.

If (a): I'll author the AGENTS.md edit promoting D14, plus a brief
codification doc.

---

## 4. Net cycle impact after revisions

| Metric | Pre-audit | Post-audit |
|---|---|---|
| Workstream count | 19 | 20 (W-V → W-Va + W-Vb) |
| Estimate | 20-27 days | **22-30 days** |
| Calendar | 4-5 weeks | **4-6 weeks** |
| Release-blocker class | W-E, W-F | **W-E, W-F, W-Va** (pending Q-B) |
| Sequencing changes | — | W-Va promoted to item #5; W-Vb stays late |
| New ship gates | — | Demo regression gate (F-PLAN-08); audit-chain pre-implementation gate (F-PLAN-01) |

**Headroom note:** if W-P property tests surface >3 correctness-
class findings, cycle can absorb them by deferring W-Vb to v0.1.12
(named-defer gate). W-Va, W-E, W-F all must ship.

---

## 5. Outstanding actions

Once you decide Q-A through Q-D, Claude applies the full revision
package to PLAN.md in one pass:

1. Cycle pattern banner rewrite (F-PLAN-01).
2. W-V → W-Va + W-Vb split with refusal matrix and isolation
   contracts (F-PLAN-02, -03, -04, -05).
3. W-W read-consistency contract addition (F-PLAN-06).
4. Capabilities path corrections + per-W-id update lists
   (F-PLAN-07).
5. Demo regression ship gate (F-PLAN-08).
6. W-F fresh-day contract concretised per Q-A (F-PLAN-09).
7. W-B D12 coercer requirement (F-PLAN-10).
8. Q-B / Q-C / Q-D decisions reflected throughout.

After revisions land, request Codex round 2 audit using the same
prompt to confirm `PLAN_COHERENT`.
