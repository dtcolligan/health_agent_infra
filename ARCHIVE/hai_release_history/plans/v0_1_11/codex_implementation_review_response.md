# Codex Implementation Review — v0.1.11 cycle/v0.1.11

**Verdict:** DO_NOT_SHIP. Two blocker-class findings below break release
contracts: W-E does not fingerprint the state surfaces named in PLAN.md, and
the canonical blank-demo regression flow is not runnable as written.

**Round:** 1

## Findings

### F-IR-01. W-E fingerprint misses material state-only changes

**Q-bucket:** Q1 / Q3
**Severity:** blocker
**Reference:** `reporting/plans/v0_1_11/PLAN.md:174`,
`src/health_agent_infra/core/synthesis.py:393`,
`src/health_agent_infra/core/synthesis.py:654`,
`src/health_agent_infra/cli.py:4888`,
`verification/tests/test_daily_supersede_on_state_change.py:247`
**Argument:** PLAN.md defines W-E as a state-change detector: the fingerprint
must hash nutrition intake, readiness, gym intake, clean evidence, and manual
readiness/stress, so `log nutrition A -> daily -> log nutrition B -> daily`
auto-supersedes with `_v<N>`. The implementation does not hash those state
surfaces. `_compute_state_fingerprint()` accepts only `proposals` and
`phase_a_firings`, and `run_synthesis()` calls it with exactly those two
inputs. The daily handler then reads whatever canonical proposal rows already
exist and calls `run_synthesis()`; it does not force fresh proposal rows when
underlying state changes. Therefore a material nutrition/readiness/gym change
that does not alter the existing proposal payloads or X-rule firings can return
the existing canonical plan as a no-op. The new test mutates `proposal_log`
payload JSON directly to make the fingerprint flip; that exercises the
implementation, but not the PLAN acceptance scenario.
**Recommended response:** Rework the fingerprint to include the actual
accepted-state surfaces named in W-E, or add an explicit daily-stage mechanism
that invalidates/requires fresh proposals from those state surfaces before
synthesis. Add a regression that performs the acceptance flow through runtime
state, not by editing `proposal_log`: nutrition/readiness/gym change after a
canonical plan must produce `_v2`; a true no-change re-run must preserve plan
row count and proposal links.

### F-IR-02. Canonical blank-demo flow fails before synthesis

**Q-bucket:** Q4 / Q5
**Severity:** blocker
**Reference:** `reporting/plans/v0_1_11/PLAN.md:1156`,
`reporting/plans/v0_1_11/PLAN.md:1177`,
`reporting/docs/demo_flow.md:26`,
`reporting/docs/demo_flow.md:110`,
`reporting/docs/demo_flow.md:133`,
`src/health_agent_infra/core/demo/session.py:260`,
`src/health_agent_infra/cli.py:4888`
**Argument:** The ship gate says that with W-Vb deferred, W-Z § B is canonical
and every command snippet in that section executes without modification in
isolation-replay mode. It does not. `hai demo start --blank` creates scratch
directories and a marker, but it does not initialize the scratch SQLite DB.
The documented intakes then fall back to JSONL-only with "state DB projection
skipped ... Run `hai state init`", and the documented `hai daily --skip-pull
--source csv` exits USER_INPUT because `state.db` is absent. Even after adding
an init step, § B still has no proposal-authoring step; `hai daily` stops at
the proposal gate because it only reads existing proposal rows and will not
fabricate them. I verified the first failure with a scratch marker path:
`hai intake readiness ...` returned the JSONL-only warning, and
`hai daily --skip-pull --source csv` returned exit 1 with "requires an
initialized state DB".
**Recommended response:** Make the v0.1.11 canonical demo flow executable
end-to-end. Either initialize the scratch DB in `hai demo start --blank`, or
document and allow the correct scratch-safe initialization command. Then add
the missing proposal composition/posting step, or explicitly scope § B to stop
at `awaiting_proposals` and adjust the ship gate. Re-run and record the
isolation replay in RELEASE_PROOF.

### F-IR-03. W-W read-consistency contract and tests are materially incomplete

**Q-bucket:** Q2 / Q3
**Severity:** important
**Reference:** `reporting/plans/v0_1_11/PLAN.md:876`,
`reporting/plans/v0_1_11/PLAN.md:909`,
`src/health_agent_infra/core/intake/gaps.py:224`,
`src/health_agent_infra/core/intake/gaps.py:272`,
`verification/tests/test_intake_gaps_from_snapshot.py:87`
**Argument:** PLAN.md requires a 100-trial concurrency test and a JSONL
row-level consistency test that captures inode/size, reads only the captured
byte range, keeps old rows, and excludes rows appended after
`as_of_read_ts`. No `test_intake_gaps_concurrency.py` exists, and no
`test_intake_gaps_jsonl_old_rows_kept.py` exists. The implementation only
opens SQLite, runs `BEGIN IMMEDIATE`, builds a DB snapshot, and rolls back; it
does not read JSONL tails or implement the row-level byte-range filter named
in the contract. The staleness tests also use 30h/50h, not the requested
47h/48h/49h boundary, and `test_no_sync_run_history_passes_gate` codifies
"no history passes" despite the plan wording requiring a successful sync
within the last 48h.
**Recommended response:** Either narrow W-W in the plan/release proof to the
actual DB-only implementation, or implement the promised JSONL-tail
consistency path. Add the missing 100-trial concurrency test, the old-row-kept
test, and exact 47/48/49h boundary coverage before treating W-W as shipped.

### F-IR-04. W-S still hardcodes persona-harness schema versions

**Q-bucket:** Q3 / Q6
**Severity:** important
**Reference:** `reporting/plans/v0_1_11/PLAN.md:448`,
`src/health_agent_infra/core/capabilities/walker.py:521`,
`verification/dogfood/synthetic_skill.py:199`,
`verification/tests/test_persona_harness_contract.py:33`,
`verification/tests/test_capabilities_proposal_contracts.py:56`
**Argument:** W-S says the harness and capabilities manifest should share the
same primitive: `_DOMAIN_PROPOSAL_SCHEMAS` plus
`ALLOWED_ACTIONS_BY_DOMAIN`. The capabilities manifest does source schema
versions from `_DOMAIN_PROPOSAL_SCHEMAS`, but the persona harness still emits
`f"{domain}_proposal.v1"` directly. The harness contract test checks action
tokens against `ALLOWED_ACTIONS_BY_DOMAIN`, but it never checks harness schema
versions against the registry. A future schema-version bump would update the
manifest and validator-facing registry while the persona harness kept emitting
the old hardcoded string.
**Recommended response:** Have `verification/dogfood/synthetic_skill.py` read
schema versions from the same registry used by the manifest, or expose a
public runtime proposal-contract helper consumed by both. Add a test that
asserts the harness-emitted schema version for every domain equals the
registry.

### F-IR-05. D11 skip justification is weakened by bugs a real replay would catch

**Q-bucket:** Q5
**Severity:** important
**Reference:** `reporting/plans/v0_1_11/RELEASE_PROOF.md:25`,
`reporting/plans/v0_1_11/RELEASE_PROOF.md:87`,
`reporting/plans/v0_1_11/PLAN.md:1166`
**Argument:** RELEASE_PROOF argues the formal Phase 0 bug hunt was redundant
because the prior Phase 0, live demo, and four-round plan audit covered the
surface. The new demo-isolation surface was not actually covered by an
end-to-end replay: the canonical § B flow fails before synthesis. W-E also
misses the acceptance scenario because the tests mutate proposal payloads
rather than state. These are exactly the kinds of implementation-level gaps a
short Phase 0/replay gate would have caught.
**Recommended response:** After the blocker fixes, add a small transcript or
scripted command list to RELEASE_PROOF showing the actual isolation replay,
including init/proposals/synthesis/supersede/gaps/doctor, and carry this as an
explicit v0.1.12 pre-PLAN bug-hunt lesson.

### F-IR-06. W-Va cardinal isolation test does not run real CLI writes

**Q-bucket:** Q2 / Q4
**Severity:** important
**Reference:** `reporting/plans/v0_1_11/PLAN.md:675`,
`verification/tests/test_demo_isolation_surfaces.py:132`,
`verification/tests/test_demo_isolation_surfaces.py:146`,
`verification/tests/test_demo_marker_fail_closed.py:116`
**Argument:** PLAN.md asks the W-Va isolation test to run commands such as
`hai intake nutrition`, `hai propose`, `hai review schedule`, and `hai daily`
under demo mode while asserting real `state.db`, real `~/.health_agent`, and
real `thresholds.toml` remain byte-identical. The test named as the cardinal
contract only calls the resolver functions and manually writes to the returned
scratch paths. That proves the three resolvers route to scratch under a marker;
it does not prove the allowed CLI bucket lacks a direct write bypass.
**Recommended response:** Keep the resolver unit tests, but add at least one
subprocess-level isolation test that executes representative allowed commands
under an active marker and checks the real DB/base/config checksums before and
after. This can double as the executable § B replay once F-IR-02 is fixed.

