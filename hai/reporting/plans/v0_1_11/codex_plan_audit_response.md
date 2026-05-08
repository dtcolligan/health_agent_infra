# Codex Plan Audit Response - v0.1.11 PLAN.md

**Verdict:** PLAN_COHERENT_WITH_REVISIONS. The cycle thesis is coherent enough
to open after revisions: W-E/W-F remain the center of gravity, and the demo
fold-ins mostly support dogfood credibility. Do not open the cycle until the
plan revises the D11 handoff, demo-mode isolation contract, W-V sequencing and
sizing, W-W read-consistency contract, capabilities touch points, and the D12
threshold note on W-B.

**Round:** 1

## Findings

### F-PLAN-01. D11 handoff is not explicit enough

**Q-bucket:** Q6 / Q7  
**Severity:** settled-decision-conflict  
**Reference:** PLAN.md lines 21-33 and 37-43; AGENTS.md lines 135-154  
**Argument:** AGENTS.md says substantive releases run a structured pre-PLAN
bug hunt before scoping PLAN.md, with findings consolidated to
`audit_findings.md`. The v0.1.11 draft introduces a plan-audit before Phase 0,
then says "Phase 0 pre-PLAN bug-hunt opens the cycle", while the same document
already fixes a 19-workstream "What this release ships" catalogue. That can be
made compatible with D11, but only if the plan says this is a pre-open draft and
that Phase 0 findings can still revise or abort scope before implementation.
Right now that gate is implicit.
**Recommended response:** Revise the cycle pattern to: draft PLAN -> Codex plan
audit -> maintainer response -> Phase 0 D11 bug hunt -> `audit_findings.md` ->
maintainer either revises PLAN.md and opens, or aborts/rescopes. Add this as a
named pre-implementation gate.

### F-PLAN-02. Demo mode isolates the DB but not the writeback/intake root

**Q-bucket:** Q4 / Q5  
**Severity:** hidden-coupling  
**Reference:** PLAN.md lines 471-488, 513-526, and 542-552  
**Argument:** W-V promises the real DB is never touched while a demo session is
active, and the test oracle is "real DB checksum stable." That misses a second
persistent surface: `resolve_base_dir()` defaults to `~/.health_agent`, and
`hai propose`, `hai intake *`, `hai review *`, and `hai daily` append JSONL
audit/intake files there. AGENTS.md treats those CLI write paths as governed
state mutation surfaces, not disposable logs. A demo can therefore leave the
real DB checksum unchanged while still polluting real proposal/intake/review
JSONL history.
**Recommended response:** Extend the marker to include a scratch `base_dir` and
make demo resolution cover both `resolve_db_path()` and `resolve_base_dir()`.
Add tests that run at least `hai intake nutrition`, `hai propose`, `hai review
schedule`, and `hai daily` in demo mode, then assert both the real DB and real
`~/.health_agent` tree are unchanged.

### F-PLAN-03. Demo marker failure modes are fail-open in the plan

**Q-bucket:** Q4  
**Severity:** hidden-coupling  
**Reference:** PLAN.md lines 485-504, 525-540, and 845-850  
**Argument:** W-V says every command checks a marker and routes to scratch DB
when present, but it does not specify what happens when the marker exists but is
corrupt, unreadable, or points at a missing scratch DB. The natural resolver
fallback is "no usable marker -> default real DB", which is the unsafe failure
mode for the feature. The refusal policy is also under-enumerated: the plan names
`hai pull` live sources and `hai auth *`, but not `hai daily --source
intervals_icu`, `hai pull --live`, `hai init --with-auth`, or `hai init
--with-first-pull`. The file list also cites `core/auth/*.py`, which does not
exist in the current tree.
**Recommended response:** Add a fail-closed rule: if a demo marker is present
but invalid, every command except `hai demo end` / `hai demo cleanup` exits
USER_INPUT without touching real state. Add an explicit command matrix for
demo-mode behavior: allowed-on-scratch, refused-because-network, refused-because
credentials/config, and cleanup-only. Add corrupt-marker and missing-scratch-DB
tests.

### F-PLAN-04. W-V is sequenced late despite being called an early resolver seam

**Q-bucket:** Q2  
**Severity:** dependency-error  
**Reference:** PLAN.md lines 554-557, 783-805, and 845-850  
**Argument:** The plan says to land W-V's DB-path resolver seam early because
other workstreams should compose against the indirection. The sequence puts W-V
at item 12, after W-X and W-Y have already changed CLI flags/doctor behavior and
after most non-audit-chain workstreams. That is not "early" for a second-highest
risk resolver seam that every command threads through.
**Recommended response:** Split W-V into W-Va and W-Vb. W-Va should land early
after the smoke-clearers: marker parsing, fail-closed resolver, scratch DB/base
dir resolution, banner, and network/credential refusal. W-Vb can land later:
persona fixtures, archive behavior, cleanup polish, and demo docs integration.
Alternatively move all of W-V before W-X/W-Y/W-W/W-S.

### F-PLAN-05. W-V is under-sized after the plan expanded it

**Q-bucket:** Q3  
**Severity:** sizing-mistake  
**Reference:** PLAN.md lines 462-552 and 800-824; demo_run_findings.md lines
297-305 and 330-351  
**Argument:** The demo findings originally sized a simpler `--demo` or env-var
scratch DB path at 2-3 days. PLAN.md expands that into a sticky `hai demo`
subcommand group, marker lifecycle, archive/cleanup behavior, every-command
resolver integration, persona fixture loading, banner injection, live-source
refusal, auth refusal, and four new test files. Once F-PLAN-02 and F-PLAN-03 are
included, 2-4 days is optimistic and the 20-27 day cycle estimate has little
headroom for W-P property-test discoveries.
**Recommended response:** Resize W-V to 4-6 days or explicitly split an MVP
from a follow-on. Add a contingency line to the total estimate: W-P correctness
findings and W-V resolver defects can push the cycle beyond 27 focused days.
State whether W-V is deferrable as a whole before implementation starts; if it
starts, a partial unsafe demo mode should block ship.

### F-PLAN-06. W-W lacks a read-consistency contract

**Q-bucket:** Q4  
**Severity:** hidden-coupling  
**Reference:** PLAN.md lines 573-595, 608-623, and 636-642  
**Argument:** W-W derives gaps from "latest accepted state" plus manual intake
JSONL tails, but the plan does not say whether the read is a single snapshot or
a sequence of live reads. If a user logs `hai intake gym` or nutrition while
`hai intake gaps --from-state-snapshot` is reading, the output can mix old
accepted-state rows with new manual tails, or vice versa. The proposed shape and
source-parity tests would not catch this.
**Recommended response:** Specify that snapshot-derived gaps run inside a single
read transaction over SQLite plus an as-of/cutoff timestamp for any JSONL tail
reads. Emit `snapshot_read_at` or source ids in the JSON so the audit trail says
what state was inspected. Add a regression test that simulates a write landing
between the accepted-state read and manual-tail read and asserts deterministic
behavior.

### F-PLAN-07. Capabilities-manifest work is under-scoped and one file path is wrong

**Q-bucket:** Q1 / Q4 / Q7  
**Severity:** hidden-coupling  
**Reference:** PLAN.md lines 397-415, 698-704, and 773-774  
**Argument:** The W-S extension is probably compatible with W30: the current
manifest has no top-level `closed: true`, and row-key tests only constrain
per-command rows. But the plan under-scopes the implementation surface. The
current manifest builder is `core/capabilities/walker.py`, not
`core/cli/capabilities.py` (which is cited in W-Y and does not exist). Adding
top-level `domain_proposal_contracts`, new `hai demo` commands, W-W flags,
W-X flags, and W-Y aliases affects `build_manifest`, capability tests, generated
`reporting/docs/agent_cli_contract.md`, and probably `reporting/docs/agent_integration.md`.
The ship gate "regenerates without diff against manifest schema" is also unclear
because the schema is not frozen.
**Recommended response:** Add an explicit capabilities update list for W-S,
W-V, W-W, W-X, and W-Y: `src/health_agent_infra/core/capabilities/walker.py`,
`render.py` if markdown should mention top-level blocks, `verification/tests/test_capabilities*.py`,
`reporting/docs/agent_cli_contract.md`, and `reporting/docs/agent_integration.md`.
Reword the ship gate to "manifest JSON and generated markdown are updated and
tests prove the additive top-level block does not require freezing
`agent_cli_contract.v1`."

### F-PLAN-08. Demo fold-in success is absent from the ship gates

**Q-bucket:** Q5 / Q7  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md lines 747-750 and 754-779; demo_run_findings.md lines
337-345  
**Argument:** The plan folds all seven demo findings into v0.1.11, but the
ship gates do not require rerunning the demo that produced them. W-Z has a
strong snippet-execution criterion, but "Doc reads coherently top-to-bottom" is
subjective, and no overall gate says Dom can replay the 2026-04-28 demo without
real-state pollution, false-green doctor output, broken gaps, flag mismatch, or
orphan supersede ids.
**Recommended response:** Add a demo regression gate: run the new
`reporting/docs/demo_flow.md` commands against `hai demo start --persona ...`,
assert every snippet executes without modification, assert no live network call
is attempted unless explicitly refused, and assert real DB/base-dir checksums
are unchanged. This is the falsifier for the demo fold-ins.

### F-PLAN-09. W-F fresh-day supersede behavior is internally inconsistent

**Q-bucket:** Q5  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md lines 171-176, 190-193, and 199-200  
**Argument:** W-F says implementation may either treat `--supersede` on a fresh
day as first-version semantics or error with USER_INPUT. The proposed test then
asserts the resulting plan id is canonical, while acceptance allows "canonical
plan id (or errors clearly)." That leaves implementers free to pick a behavior
that fails the named test or to change the test later.
**Recommended response:** Choose the behavior before cycle open. If the desired
contract is forgiving first-version semantics, make the acceptance and test
assert canonical id. If the desired contract is explicit USER_INPUT, change the
test to assert no write plus the refusal message. Do not leave this as
cycle-internal discretion for a release-blocker-class path.

### F-PLAN-10. W-B adds a threshold without naming the D12 coercer/test

**Q-bucket:** Q6  
**Severity:** settled-decision-conflict  
**Reference:** PLAN.md lines 92-104 and 113-117; AGENTS.md lines 139-142;
PLAN.md lines 590-595  
**Argument:** W-B adds `r_volume_spike_min_sessions_last_28d`, a new numeric
threshold consumed by R/X-rule logic. D12 says every new threshold consumer must
use `core.config.coerce_*`; W-W correctly names `coerce_int` for its staleness
threshold, but W-B does not. Without an explicit test, this is exactly the
bool-as-int class v0.1.10 hardened against.
**Recommended response:** Add to W-B approach: resolve
`r_volume_spike_min_sessions_last_28d` with `core.config.coerce_int`. Add tests
for normal boundary values and a user override of `true`/`false` rejected as a
numeric threshold.

## Open questions for maintainer

1. Should W-V be release-blocker-class once included, or explicitly deferrable
   as a whole before implementation starts?
2. Should demo mode isolate only DB/writeback state, or also config writes,
   skills install destination, and credential/keyring surfaces?
3. Should the pre-cycle Codex plan audit become D14 after this round, and if so,
   does it run before or after the D11 bug hunt for future cycles?
