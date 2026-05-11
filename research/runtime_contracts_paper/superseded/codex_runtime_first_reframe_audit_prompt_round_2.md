# Codex Audit Prompt — Runtime-First Reframe, Round 2

**Audit round:** 2
**Date authored:** 2026-05-09 (evening)
**Audit scope:** Comprehensive review of the round-1 closeout. Did
the closeout actually fix the 20 round-1 findings? Did it introduce
second-order issues? Are the deferred deliverables genuinely
deferrable, or do they unblock something the plan doesn't admit?

You are operating as the project's external auditor. You did the
round-1 audit; this is the same conversation only in the sense that
both rounds reference the same disk state. You have no chat memory
of round 1. Read the response files; do not assume anything about
how the closeout was authored.

## 0. Why this round

Round 1 returned `PLAN_INCOHERENT` with 20 findings. The maintainer
adjudicated and accepted all 20; six architectural answers were
locked into `project/DECISIONS.md` D-PROJ-016 + D-PROJ-017. The
closeout produced 20 file edits + 6 new files. Test count went
5 → 13 on the schema-contract suite; both test surfaces (benchmark
verification + project alignment) are green at 21 passing.

The empirical settling shape across the project's prior PLAN-class
reviews is **10 → 5 → 3 → 0** over four rounds. Round 2 should
produce **roughly 3-5 substantive findings**. A round-2
`PLAN_COHERENT` would be a positive surprise but not impossible;
the maintainer accepted that the closeout could be honest enough to
clear in two rounds. A round-2 verdict with **more than ~8
findings** suggests the closeout introduced new issues; the
maintainer should re-read the closeout diff before responding.

The audit asks specifically about *closeout integrity* and *the
highest-risk corners of the new design*. It is not a full
re-audit; round 1's reading list and audit questions are not all
re-asked.

## 1. Reading list (do this in order)

### 1.1 Closeout artifacts (the diff you are auditing)

1. `research/runtime_contracts_paper/codex_runtime_first_reframe_audit_response.md`
   — your round-1 response, for reference.
2. `research/runtime_contracts_paper/codex_runtime_first_reframe_audit_response_response.md`
   — the maintainer's per-finding closeout. **This is the
   primary diff.** Verify each "Action" claim against the
   filesystem. If a claim is unverifiable, it is a finding.

### 1.2 Authoritative decisions and governance

3. `project/DECISIONS.md` — D-PROJ-016 (HAI freeze on disk),
   D-PROJ-017 (six architectural answers).
4. `AGENTS.md` — verify the v0.2.3 schema-freeze retirement edits
   actually retired the entries (not just commented them out)
   without breaking the rest of the Settled Decisions and Do Not
   Do sections.

### 1.3 Architectural docs the closeout rewrote

5. `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`
   (round-2 revision; Phase 2 grew, mechanism table revised, risk
   register expanded, calendar revised).
6. `research/runtime_contracts_paper/MECHANISM_INVENTORY.md`
   (rewritten with code-grounded picture, M9-TX added, hermeticity
   surface corrected).
7. `research/runtime_contracts_paper/CLAIM_LADDER.md` (Tier 5 to
   Future-A appendix, forbidden-phrasing guards strengthened).
8. `research/runtime_contracts_paper/WORK_PACKETS.md` (dependency
   graph added, `WP-DISPATCH-001` new, `WP-REFUSE-002` rewritten,
   `WP-HRN-002` rewritten, several packets expanded).

### 1.4 Schema artifacts (the v2 hardening)

9. `benchmark/governed_agent_bench/schema/trajectory.schema.json`
   v2 — verify conditional invariants (`mechanism` required when
   `step_type=mechanism_disabled`; `command` required when
   `step_type=command`; `model_identity` required for non-rule).
10. `benchmark/governed_agent_bench/schema/score.schema.json` v2 —
    verify `scorer_config_hash` required, per-metric `threshold`
    required and non-null, conditional `mechanism` for
    `mechanism_disabled_unexpected` violations.
11. `benchmark/governed_agent_bench/schema/task.schema.json` v2 —
    verify `load_bearing_mechanisms` and `runtime_modes_in_scope`
    required, `harness_allowlist` removed from the enum.
12. `benchmark/verification/tests/test_governed_agent_bench_schema_contracts.py`
    — verify the 13-test suite asserts every invariant claimed in
    the closeout. Look for invariants the test does not cover.

### 1.5 New artifacts

13. `benchmark/governed_agent_bench/prompts/deployment_full_v1.md`
    — versioned prompt template per F-CDX-RFR-R1-05.

### 1.6 Tombstoned active docs (verify supersession is real, not cosmetic)

14. `research/runtime_contracts_paper/PAPER_FRAME.md`
15. `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`
16. `research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md`
17. `research/runtime_contracts_paper/BASELINES_AND_ABLATIONS_PLAN.md`
18. `research/runtime_contracts_paper/IMPLEMENTATION_PLAN.md`
19. `benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md`
20. `benchmark/governed_agent_bench/baselines/README.md`
21. `project/OPERATING_MODEL.md`
22. `project/HYPOTHESES.md`
23. `project/ROADMAP.md`
24. `README.md`

### 1.7 Sampling for residual prompt-first language

25. Run a search for old condition labels and report any active
    references found:
    `local_prompt_only`, `cloud_prompt_only`, `local_manifest`,
    `cloud_manifest`, `fine_tuned_local_manifest`, `with_manifest`,
    `without_manifest`, `prompt-only baseline`,
    `manifest-grounded prompting`, `no_runtime` (without the
    `_enforcement` suffix). The round-1 closeout was supposed to
    purge these from active docs while preserving them in
    `hai/reporting/plans/` historical provenance.

### 1.8 HAI source (light sampling, not full re-audit)

26. Verify the file paths cited in the closeout's `MECHANISM_INVENTORY.md`
    actually exist (e.g., `core/validate.py`, `core/writeback/proposal.py`,
    `cli/handlers/intent.py`, `core/synthesis.py`, `core/state/store.py`,
    `core/paths.py`, `core/demo/session.py`,
    `verification/tests/contract/test_audit_chain_integrity.py`).

## 2. Round-2 audit questions

Each question expects a finding (or an explicit "no finding"). Do
not collapse multiple findings into one entry. Severity calibration
is unchanged from round 1.

### A. Closeout integrity (did the actions in the response_response file actually happen?)

A1. For each of the 20 findings, the closeout names specific Action
items. Pick five findings at random (or focus on F-02, F-09/F-10,
F-11, F-16, F-19, the architectural ones) and verify each Action
claim against the filesystem. Report any Action claim that did not
land or landed differently from what the closeout said.

A2. The closeout says "Schema-contract test grew from 5 to 13
tests. All passing." Verify by inspection of the test file. Confirm
the count and that no test is `xfail` / `skip` / commented.

A3. The closeout says supersession notes were added to 11 docs. For
each of the 11, verify the note exists *and* the doc's body content
is consistent with the note (not just a header note over an
unchanged prompt-first table).

### B. Schema conditional enforceability

B1. The trajectory schema uses Draft 2020-12 `allOf` + `if`/`then`
conditionals. Confirm the conditional structure is valid Draft
2020-12 (not Draft 7 or Draft 2019-09 syntax that was almost-but-
not-quite right). Specifically: when the `if` clause's
`required` array is missing, some validators short-circuit
differently than when it is present. The trajectory schema's
conditionals all set `"required": ["step_type"]` or
`"required": ["model_class"]` inside the `if` clause; verify this
is correct under Draft 2020-12 semantics.

B2. `model_identity` conditional says `if model_class=rule_baseline,
then NOT required, else required`. Confirm `else` semantics under
Draft 2020-12: `else` applies when the `if` clause does **not**
match. What happens when `model_class` is *missing*? (It is in the
schema's top-level `required` array, so the schema should reject
that case before reaching the conditional. Confirm.)

B3. The `score.schema.json` per-metric `threshold` requires non-null
via `"type": ["number", "boolean"]`. But Draft 2020-12 metrics with
absent `threshold` would now fail. Confirm there is no place in the
closeout that emits a metric without a threshold.

B4. The schema-contract test asserts the conditional structure
shape, but it does **not** instantiate a Draft 2020-12 validator and
test against a sample document. The test verifies the schema's
intent but not its enforceability. Is this a finding?

B5. The `harness_allowlist` removal from the task enum: confirm
the removal landed in the schema *and* in the schema-contract test
*and* there are no remaining task fixtures (currently empty) or
docs that reference `harness_allowlist` as a load-bearing
mechanism.

### C. M5/M6 separation realisability

C1. The closeout adds `WP-DISPATCH-001` (CLI-dispatch agent_safe
enforcer). The packet's design hinges on the new env var
`HAI_INVOCATION_CONTEXT` (values: `agent`, `user`, default `user`).
Trace this through: when Dom's daily-driver Claude Code session
invokes a `hai` command, what is `HAI_INVOCATION_CONTEXT` set to?
If the answer is `user` (default), then **agent_safe enforcement is
effectively off in Dom's daily loop**. Is that intended? The
closeout claims the existing maintainer daily loop is unaffected —
but the affected behaviour is exactly the agent-vs-user
classification.

C2. Phase 2 now grows by `WP-DISPATCH-001` (~2-3 weeks per the
calendar update). The packet's acceptance criteria require
isolation tests showing M5 and M6 are independently switchable.
Read the packet and assess: is `HAI_INVOCATION_CONTEXT=agent +
HAI_RUNTIME_MODE=no_agent_safe + the W57 user-gate-still-fires
test` a coherent experiment design? Specifically: under
`no_agent_safe + agent`, the dispatch refusal is bypassed; under
the same mode but with a `propose` (M4 territory), does M4 still
validate? This is the cross-mechanism isolation question.

C3. The closeout's MECHANISM_INVENTORY M5 entry says the canonical
seam (after build) is "a CLI-dispatch middleware (likely in
`cli/__init__.py` or a new `cli/dispatch/agent_safe.py`)". This is
deliberately under-specified — Phase 1 hasn't run yet. Is the under-
specification acceptable for round 2, or does it leave room for
the Phase 2 implementer to merge M5+M6 again under coupling
pressure?

### D. WP-REFUSE-002 hermetic-mode acceptance

D1. The rewritten `WP-REFUSE-002` requires `HAI_HERMETIC=1 +
HAI_STATE_DB=/tmp/<fixture>` for the `no_agent_safe` ablation test.
Confirm the test design cannot mutate user state under any
unfortunate ordering of env-var resolution. Specifically: if
`HAI_RUNTIME_MODE=no_agent_safe` is set but `HAI_HERMETIC` is unset,
what happens? The packet says "the recipe is all-or-nothing" — but
where is that enforced? `WP-HRN-001` says "Setting `HAI_HERMETIC=1`
without `HAI_STATE_DB` or `HAI_BASE_DIR` redirection fails with a
clear error." That is the inverse direction. The test that **`no_agent_safe`
without hermetic mode raises an error** is mentioned as a Tests
item; verify it is bound to runtime-side enforcement, not just
test-side.

D2. The packet says "the test invokes a representative
`agent_safe=false` command (e.g., `hai intent commit --dry-run` or
against a *fixture* intent row in a *fixture* DB)." But `--dry-run`
on `hai intent commit` may not exist as a CLI flag. Confirm by
grepping the source. If it doesn't exist, the test design has a
hole that requires a runtime fix (a `WP-RUNTIME-FIX-NNN` packet)
before `WP-REFUSE-002` can run.

### E. M9-TX held-constant invariant

E1. The closeout adds M9-TX as held-constant. The new `MECHANISM_INVENTORY.md`
M9-TX entry states "DO NOT ABLATE" and points at `core/synthesis.py`
as the canonical seam. Confirm: is there any `runtime_mode` in the
v2 enum whose semantics could accidentally disable transactions?
For example, `no_audit_chain` says "atomic state-graph writes still
happen — that is M9-TX, not part of the M8 ablation." But what
about `no_runtime_enforcement`? The mode description says "M4-M8
all off; M1-M3 + M9-TX on." Confirm the implementation guidance is
explicit enough that an implementer of `no_runtime_enforcement`
won't accidentally bypass the transaction wrapper too.

E2. The risk register's "no_runtime_enforcement performs comparably
to full_contract" risk is the empirical risk the experiment is for.
But the closeout doesn't address the *opposite* risk: what if
`no_runtime_enforcement` *catastrophically* corrupts state because
M9-TX wasn't actually preserved when M4-M8 were all off? Should
this be a separate row in the risk register?

### F. Prompt template artifact

F1. `prompts/deployment_full_v1.md` defines four substitution
variables from the manifest snapshot's top-level taxonomies. The
manifest is supposed to gain those taxonomies via Phase 3
(`WP-MAN-001..004`). Today's manifest is `agent_cli_contract.v1`
and does not have the top-level taxonomies. **Therefore the
template cannot be rendered today; it depends on Phase 3
completion.** Is this a packet-ordering issue?

F2. The template's "Stability commitment" says "Once `deployment_full_v1`
is referenced in a published trajectory or score artifact, this
file is **byte-frozen**." But the rendered prompt contains the
*manifest snapshot* embedded — meaning the rendered prompt's hash
varies by snapshot id. Two trajectories pinned to two different
manifest snapshots will record two different `prompt_template_hash`
values, even though `prompt_template_id` is the same. Is the
template-id vs rendered-hash semantics clear enough that future
implementers won't confuse them?

F3. L7 drift tasks are supposed to use a stale manifest snapshot
(`hai_0_1_18_drift.json`). But the v0.1.18 manifest is at
`agent_cli_contract.v1` and does not have the v2 top-level
taxonomies that `deployment_full_v1` substitutes. **The template
cannot be rendered against the stale snapshot without adapting.**
Is this a finding? Either the L7 prompt path is different, or the
drift snapshot needs to be promoted to v2 with synthetic
taxonomies, or the template needs a backward-compat case.

### G. Tier 3 falsifiability and roster selection bias

G1. CLAIM_LADDER Tier 3 evidence: "The smallest model in the
predeclared roster, under `full_contract`, passes all primary-metric
thresholds named in `scorer_config_hash`." The maintainer could
choose a roster where the smallest model is exceptionally well-
trained for contract obedience. The "predeclared before any model
run" discipline is asserted but not on-disk-enforced. Is the
discipline hardened anywhere (e.g., Git-tag the roster, or use a
content hash like `scorer_config_hash`)?

G2. Tier 4 evidence requires "Curve-shift quantified with a
predeclared metric." But the metric itself is not defined in
`CLAIM_LADDER.md`. Is "smallest passing parameter count under
full_contract minus smallest passing under no_runtime_enforcement"
the intended metric? If so, define it. If not, what is?

G3. The model-roster artifact (`model_roster.md`) is named in the
EXECUTION doc but listed as a deferred deliverable. Is the
deferral sustainable through Phase 5, or does it need to be authored
earlier? Risk: if the maintainer authors the roster after partial
runs, the predeclared-roster discipline is broken.

### H. Hypothesis re-statement integrity

H1. `project/HYPOTHESES.md` H4 (fine-tuning, marked future-work)
was rewritten as: "A fine-tuned local operator that memorizes a
stale manifest will fail under L7 drift tasks (stale manifest
content, full runtime mode), where a fine-tuned operator that
retrieves the live manifest at task time will recover." This still
implies a comparison between *retrieving manifest* and *not
retrieving manifest* — which is the prompt-axis. Is H4's revised
wording fully consistent with D-PROJ-014, or does it sneak the
prompt axis back in for the future-work tier?

### I. Freeze + WP-RUNTIME-FIX-NNN flow

I1. D-PROJ-016 says HAI runtime defects ship via
`WP-RUNTIME-FIX-NNN` packets, not new release cycles. The closeout
says "fixes can land on the v0.2.0 line, but they are not 'v0.2.1
product work' — they are research-support runtime patches."
**Concretely:** if a Phase 2 fix lands in HAI source, does the
maintainer republish to PyPI, or does the benchmark consume HAI from
the source tree? The closeout doesn't say. The risk: a paper claim
based on benchmark runs against a source-tree HAI that diverges from
the published v0.2.0 PyPI artifact.

I2. The `WP-RUNTIME-FIX-NNN` template exists. Are there any active
references in the closeout that *invoke* it? If yes, list them — they
will become real packets soon.

### J. Doc-tombstoning depth

J1. The 11 tombstoned docs got round-2 supersession notes. For each,
verify the note plus body. Specifically:
- `BASELINES_AND_ABLATIONS_PLAN.md` had its Required Conditions
  table replaced; verify there is no old prompt-first table
  *anywhere* in the file.
- `OPERATOR_HARNESS_SPEC.md` had its Conditions table replaced and
  Model Input rewritten; verify the Trajectory Encoding section
  doesn't still reference `local_prompt_only` or related labels.
- `HYPOTHESES.md` H1 and H4 were rewritten; verify H2, H3, H5, H6
  don't have residual prompt-first language.

J2. The closeout says historical `hai/reporting/plans/` docs are
intentionally *not* tombstoned. Confirm that those historical docs
are still classified as historical (not active) by checking for any
that have been edited since the freeze.

J3. `README.md` benchmark section was updated. Confirm the rest of
the README doesn't still imply prompt-first comparison.

### K. Deferred deliverables sustainability

K1. The closeout defers `model_roster.md`, `HERMETIC_RECIPE.md`,
`WP-INV-002..N`, and the `WP-DOCS-OPS / SCAFFOLD / CARD / CONTRACT-001`
expansions. For each, identify any acceptance criterion of an
active packet that depends on the deferred deliverable. If a packet
cannot be assigned to an agent without the deferred artifact, the
deferral creates a hidden block.

### L. Risk register completeness (round 2)

L1. The expanded risk register adds API drift, reproducibility,
audit-round budget, schema forward-compat, fixture privacy. What
risk is *still* missing? Specifically consider: (a) the maintainer's
own time / availability / external commitments (per the project's
calendar context, evening/weekend bandwidth is bounded); (b)
disagreement between the runtime-first framing and the eventual
peer-review reception.

L2. The "fixture privacy scan" mitigation in the new privacy risk
row says a scan rejects PII — but the scan is not a packet. Where
does the scan live? Is it `WP-FIX-001..006` acceptance criteria, or
a new packet that should exist?

## 3. Verdict format

Same as round 1. Return one of:

- `PLAN_COHERENT` — closeout is solid; no findings.
- `PLAN_COHERENT_WITH_REVISIONS` — substantive findings the
  maintainer should address before round-2 close.
- `PLAN_INCOHERENT` — the closeout introduced or failed to address
  blockers; round 3 cannot proceed without rework.

Verdict on first line of `codex_runtime_first_reframe_audit_response_round_2.md`.

## 4. Findings template

Use the same template as round 1. Numbering becomes `F-CDX-RFR-R2-NN`.

```
### F-CDX-RFR-R2-NN — <short title>

**Severity:** critical | major | minor | nit
**Audit question:** <e.g., A1, B3, C2>
**Where:** <file path>:<line range or anchor>
**Finding:** <one paragraph>
**Suggested fix:** <one paragraph; or `defer to maintainer`>
**Provenance check:** <what you verified on disk>
```

If a finding is a regression (something the closeout broke), tag it
with `[REGRESSION]` after the title. If it is a follow-on of an
unresolved round-1 issue, tag it `[ROUND-1 RESIDUAL]`.

## 5. Severity tags

Same calibration as round 1. A finding's severity is independent of
its difficulty to fix.

## 6. Output requirements

Write to:

```
research/runtime_contracts_paper/codex_runtime_first_reframe_audit_response_round_2.md
```

Do not edit other files. This is read-only audit; suggested fixes
are descriptions, not patches.

## 7. Provenance discipline

Same as round 1. Verify file paths, function names, line ranges,
and exact strings before citing them. The closeout's Action claims
must be checked against disk; the maintainer would rather see a
finding "the closeout claims X but disk shows Y" than a finding that
takes the closeout's claim at face value.

If you cite something you have not verified, mark the finding
`UNVERIFIED — citation only`.

## 8. Out-of-scope for this round

- Do not propose changes to `AGENTS.md` settled decisions or
  governance invariants without an explicit reframe-level finding.
  The v0.2.3 schema-freeze retirement is locked.
- Do not re-litigate the six architectural answers in
  D-PROJ-017. Those are maintainer decisions; the audit verifies
  whether they were *executed coherently*, not whether they were
  *correct*.
- Do not propose new HAI release cycles. The freeze is locked.
- Do not write the experiment results. Benchmark has not run.

## 9. Tone

Hostile but fair. The closeout was authored by the same agent that
authored the round-1 reframe and may have rationalised its way past
issues. The maintainer is paying for an external auditor's
independent read precisely because the closeout author cannot audit
itself.

## 10. Empirical settling shape

Round 2 of a substantive PLAN-class change typically produces 3-5
findings (validated v0.1.11 + v0.1.12). Calibration:

- **0-2 findings:** unusually clean; verify the audit was deep
  enough by self-checking that you actually executed §1 reading
  list and §2 audit questions. A round-2 PLAN_COHERENT for this
  reframe would be surprising but not impossible.
- **3-5 findings:** typical. Ship as `PLAN_COHERENT_WITH_REVISIONS`
  if the findings are addressable; ship as `PLAN_INCOHERENT` if
  any single finding blocks Phase 1 from starting.
- **6-8 findings:** the closeout did substantial work but missed
  meaningful corners; expect another round.
- **>8 findings:** the closeout introduced second-order issues;
  the maintainer will re-read the closeout diff before responding.

## 11. Self-check before submitting

- Did you read the closeout's response_response file in full?
- Did you sample-verify five of its Action claims against disk?
- Did you grep for residual prompt-first language?
- Did you read the v2 schemas, not just the schema-contract test?
- Did each finding have a provenance check?
- Did you avoid duplicating findings that follow from one root
  cause?

When you submit, the maintainer hands the response back to the
planning agent (Claude). Round-3 work, if any, follows the same
pattern: closeout, response_response companion, next-round prompt.
