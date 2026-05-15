# Codex Audit Prompt — Runtime-First Reframe

**Audit round:** 1
**Date authored:** 2026-05-09
**Audit scope:** Comprehensive review of the runtime-first reframe of
the runtime-contracts paper plan. The reframe lands in seven new or
edited files plus a memory-side decision record. This prompt asks for a
hostile, rigorous read against the rest of the repo's canonical docs
and against the HAI source.

You are operating as the project's external auditor. You have not seen
the conversation that produced this reframe. Everything you need is on
disk. Treat that as a feature: the reframe must be defensible from the
filesystem alone, not from chat history.

## 0. Why this round

A maintainer (Dom Colligan) and a planning agent (Claude) reframed the
HAI paper-readiness work over the course of one session. Two
substantive shifts landed:

1. **HAI is frozen as a product (2026-05-08).** The v0.2.0 PyPI release
   is the reference snapshot the paper and GovernedAgentBench will pin
   against. There is no v0.2.1 cycle. HAI runtime changes are now only
   permitted via the `WP-RUNTIME-FIX-NNN` template, not via a HAI
   release ladder.

2. **The headline experiment is runtime-first (2026-05-09).** The
   prompt is held constant at deployment-realistic full information in
   every condition. The runtime is the primary axis of variation. The
   `condition` enum in the benchmark schemas was split into
   `runtime_mode` × `model_class`. The pre-reframe `with_manifest` vs
   `without_manifest` ablation is dropped from the headline experiment.

The reframe was motivated by the observation that the prompt-only
ablation ("manifest yes/no") replicates a known result from BFCL,
ToolLLM, and Gorilla and produces a sandbagged-baseline critique. The
paper claim is about the runtime, so the experiment must vary the
runtime.

The maintainer wants you to find what is wrong, missing, internally
inconsistent, or under-defended in this reframe before any of the
downstream packets execute. Substantive findings are welcome and
expected. A round-1 verdict of `PLAN_COHERENT` would be surprising and
should be self-doubted; this is a substantive PLAN-class change and
the empirical settling shape (10 → 5 → 3 → 0 over 4 rounds, twice
validated in v0.1.11 and v0.1.12) almost certainly applies.

## 1. Reading list (do this in order)

You must verify file paths, function names, and exact strings against
the filesystem before citing them. Do not trust any claim made in this
prompt without checking.

### 1.1 The reframe's new and edited artifacts

Read these first. They are the artifacts under audit.

1. `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`
   (new, 2026-05-09) — the controlling 8-phase plan.
2. `research/runtime_contracts_paper/MECHANISM_INVENTORY.md` (new) —
   Phase 1 audit template with `NEEDS_INVENTORY` placeholders.
3. `benchmark/governed_agent_bench/schema/trajectory.schema.json` —
   bumped to `governed_agent_bench.trajectory.v2`.
4. `benchmark/governed_agent_bench/schema/score.schema.json` — bumped
   to v2.
5. `benchmark/governed_agent_bench/schema/task.schema.json` — bumped
   to v2; new optional `load_bearing_mechanisms` and
   `runtime_modes_in_scope` fields.
6. `benchmark/verification/tests/test_governed_agent_bench_schema_contracts.py`
   — updated to assert the new shape; passing as of 2026-05-09.
7. `benchmark/governed_agent_bench/BENCHMARK_SPEC.md` — adds
   mechanism-load-bearing coverage rule.
8. `research/runtime_contracts_paper/CLAIM_LADDER.md` — tier ladder
   restructured around runtime-first evidence.
9. `research/runtime_contracts_paper/WORK_PACKETS.md` — extended with
   ~25 reframe packets; three pre-existing packets rescoped.
10. `project/DECISIONS.md` — D-PROJ-013, D-PROJ-014, D-PROJ-015 added
    with full rationale sections.

### 1.2 Canonical project docs the reframe must not contradict

Read these to check coherence.

11. `project/FRAME.md`
12. `project/OPERATING_MODEL.md`
13. `project/HYPOTHESES.md`
14. `project/ROADMAP.md`
15. `AGENTS.md` (root)
16. `CLAUDE.md` (root, imports AGENTS.md)
17. `research/runtime_contracts_paper/PAPER_FRAME.md`
18. `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`
19. `research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md`
20. `research/runtime_contracts_paper/HAI_PAPER_READINESS_PLAN.md`
    (high-level, pre-reframe; should still be coherent)
21. `research/runtime_contracts_paper/IMPLEMENTATION_PLAN.md`
22. `research/runtime_contracts_paper/PRIOR_ART_POSITIONING.md`
23. `research/runtime_contracts_paper/BASELINES_AND_ABLATIONS_PLAN.md`
24. `research/runtime_contracts_paper/DOC_ALIGNMENT_AUDIT.md`
25. `benchmark/governed_agent_bench/README.md`
26. `benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md`
27. `benchmark/governed_agent_bench/SCORING_SPEC.md`
28. `benchmark/governed_agent_bench/TASK_AUTHORING_GUIDE.md`
29. `README.md` (root, research-facing)
30. `hai/docs/hai_reference_runtime.md`
31. `hai/docs/runtime_contract_overview.md`
32. `hai/docs/architecture.md`
33. `hai/docs/non_goals.md`
34. `hai/docs/agent_cli_contract.md` (currently v1; v2 work pending)
35. `hai/docs/current_system_state.md`

### 1.3 HAI source surfaces relevant to mechanism isolation

The reframe assumes M4..M8 (validation, agent_safe, proposal_gate,
refusal, audit_chain) can be independently disabled. You must verify
this against actual code, not against the plan's claims.

36. `hai/src/health_agent_infra/cli.py` (root + handler-group modules
    after the v0.1.17 split)
37. `hai/src/health_agent_infra/core/` — top-level
38. `hai/src/health_agent_infra/core/synthesis.py` (proposal/commit
    seam) and `synthesis_policy.py`
39. `hai/src/health_agent_infra/core/config.py` (threshold coercion
    helpers per D12; relevant to validation seam)
40. `hai/src/health_agent_infra/skills/safety/` (current refusal
    surface — mostly skill-owned; reframe wants this in code)
41. `hai/src/health_agent_infra/domains/<d>/` for one example domain
42. Any `audit/`, `validation/`, `refusal/` dirs that exist
43. `hai/verification/tests/` — sample tests touching W57, audit
    chain, validation, agent_safe enforcement

### 1.4 Memory-side decision record (informational)

44. The reframe was recorded as a Claude memory entry at
    `<user-memory>/project_runtime_first_reframe_2026-05-09.md`. You
    cannot read this file directly; treat its existence as
    informational only. The on-disk authoritative record is
    `project/DECISIONS.md` D-PROJ-013..015.

## 2. Substantive audit questions

For each question below, return a finding (or note that no finding
applies). Do not collapse multiple findings into one entry. Findings
are cheap; missed findings are expensive.

### A. Claim-evidence integrity

A1. Does each Tier in `CLAIM_LADDER.md` v2 have evidence requirements
sufficient to support the claim's wording? Specifically: can Tier 1
("removing at least one runtime mechanism degrades at least one
primary safety metric") be honestly claimed from a single mechanism
ablation, or does it require more?

A2. Are the forbidden-language guards in each tier strict enough to
prevent the paper from sliding up the ladder when results are weaker
than written? Are there phrasings the paper might want to use that the
guards miss?

A3. Tier 3 ("runtime as floor") requires "the smallest evaluated model
under `full_contract` passes the predeclared safety thresholds." Is
this falsifiable? Could the maintainer pick thresholds and a smallest
model class such that the claim is trivially true? Is the predeclared-
thresholds discipline actually enforced anywhere on disk, or only
asserted?

A4. Tier 5 (fine-tuning) imports D-PROJ-T's deferral. Is the deferral
consistent with Tier 5 still being claimable as a workshop-floor
result, or has the workshop floor implicitly drifted up the ladder?

### B. Mechanism isolation realism

B1. Read HAI source for each of M4..M8. Verify or refute the coupling
graph in `MECHANISM_INVENTORY.md` §"Coupling Graph (provisional)". For
each arrow, cite a file path and line range as evidence.

B2. The plan rates M7 (refusal) as `aspirational` because the
runtime-owned seam does not exist yet (it must be built in Phase 2).
Is this accurate, or does runtime-side refusal already exist
partially and the plan is overstating the gap?

B3. The plan asserts that disabling M5 (`agent_safe`) and M6
(`proposal_gate`) are independently meaningful. Read the user-gated
commit path (`hai intent commit`, `hai target commit`) and the
`agent_safe=false` enforcement. Are these two mechanisms genuinely
independent, or does one functionally subsume the other?

B4. M8 (audit_chain) is consumed by `hai today`, `hai explain`, and
the W52 weekly review surface. Disabling M8 in benchmark mode must
not corrupt the user's real audit chain. Is `HAI_STATE_PATH`
redirection (`WP-HRN-002`) sufficient to guarantee this isolation, or
does the audit chain have global side effects (e.g., file paths,
environment variables, config files) the plan misses?

B5. Identify any HAI mechanism the plan fails to enumerate. Examples
to check: mutation-class enforcement (currently treated as a property
of M4 + M5); harness-allowlist enforcement (M3, held constant);
schema validation for proposal payloads (M4 sub-mechanism); state
DB transaction integrity. Should any of these be a separate
ablatable mechanism (M9..)?

### C. Experimental design integrity

C1. The plan holds the prompt constant at "deployment-realistic full
information" across all conditions. Define this rigorously. Is the
exact prompt content specified anywhere on disk, or is it under-
specified such that two future runs could differ?

C2. Is `no_runtime` itself a confounded condition? "HAI is a thin
passthrough" — does this mean the harness still parses structured
actions (M2) and still uses the allowlist (M3)? If yes, `no_runtime`
is mis-named; it should be `no_runtime_enforcement`. If no, then
mechanisms M2 and M3 are also being disabled, contaminating the
ablation. Check `HAI_PAPER_READINESS_EXECUTION.md` §"Phase 5" and the
trajectory-schema enum description.

C3. The plan drops the `local_prompt_only` and `cloud_prompt_only`
conditions from the trajectory schema. Are there places in the repo
(e.g., `RESEARCH_EVAL_STRATEGY.md`, `PROJECT_EXECUTION_PLAN.md`,
`OPERATOR_HARNESS_SPEC.md`) that still reference those condition names
or imply they will be measured?

C4. Is the model-scale claim (Tier 3 / Tier 4) realistic with the
calendar shape proposed? The plan defers fine-tuning data generation
(D-PROJ-T). Without fine-tuning, the model-scale comparison includes
only off-the-shelf models. Does the plan acknowledge that Tier 3 may
not be reachable without Tier 5?

C5. Does the plan defend against the "we just observed model-size
selection bias" attack? If the smallest evaluated model is Qwen 2.5
7B and the largest is GPT-4o, the score gap may reflect base-model
quality rather than the runtime's contribution. What predeclared
metric controls for this?

### D. Schema correctness

D1. Read the three v2 schemas. Check that:
   - The `runtime_mode` enums match byte-for-byte across
     `trajectory.schema.json` and `score.schema.json`.
   - The `model_class` enums match byte-for-byte.
   - The `mechanism` enum (in step `mechanism_disabled` and on
     score `violations`) is internally consistent.
   - All three schemas use compatible `schema_version` `const` values.

D2. The v2 task schema adds `load_bearing_mechanisms` and
`runtime_modes_in_scope` as optional fields. Should at least one of
them be required, given the mechanism-load-bearing coverage rule
in `BENCHMARK_SPEC.md`?

D3. The score schema adds `mechanism` to violations. Is this field
required when the violation `kind` is `mechanism_disabled_unexpected`,
and optional otherwise? The current schema makes it always optional.
Is that defensible?

D4. The trajectory schema adds `step_type=mechanism_disabled` to the
existing step enum. Is the `mechanism` field required when
`step_type==mechanism_disabled`, and forbidden otherwise? The schema
does not encode this conditional requirement.

D5. Are there other benchmark artifacts (README, fixtures, scorer
README) that still reference v1 schema field names?

### E. Plan coherence

E1. Read `PROJECT_EXECUTION_PLAN.md` Milestone M1. Does it still tell
a coherent story under the new plan, or does it assume the prompt-
first ordering that the reframe replaced?

E2. Read `RESEARCH_EVAL_STRATEGY.md` "Systems To Compare" table. Does
it list `local_prompt_only` and `local_manifest` as separate systems?
If yes, this contradicts D-PROJ-013/014 unless the table is reframed.

E3. Read `IMPLEMENTATION_PLAN.md` Phases 2-4. Are these phases
consistent with the eight-phase shape in the new EXECUTION doc, or
does the reader get a different story depending on which doc they
read first?

E4. Read `BASELINES_AND_ABLATIONS_PLAN.md`. Does it pre-suppose
prompt-only baselines as comparison conditions? If yes, the doc
contradicts the reframe.

E5. The `HAI_PAPER_READINESS_PLAN.md` (high-level, pre-reframe) lists
"benchmark-eligible command families" but does not yet reference
runtime modes. Is the high-level plan still coherent under the new
EXECUTION doc, or does it need its own update?

E6. The `IMPLEMENTATION_PLAN.md` Phase 4 baselines list
"local prompt-only" etc. The reframe drops these. Update or contradict?

### F. Packet boundedness

F1. Read each new WP-* packet in `WORK_PACKETS.md`. Does each have
explicit Inputs, Outputs, Allowed files, Forbidden files,
Dependencies, Acceptance criteria, Tests, Manual review needed, and
Non-goals? Note any that fail the template.

F2. Are the packet dependencies acyclic? Does any packet implicitly
depend on a later one?

F3. Is `WP-INV-001` (mechanism inventory) bounded enough that a
coding agent can complete it without making strategic decisions?
Specifically: how does the agent decide between `coupled` and
`aspirational` for an ambiguous case?

F4. Are `WP-MAN-001..006` independently executable, or do they form
a transitive dependency chain that should be merged into a single
packet? List the dependency graph.

F5. Does any new packet contradict an AGENTS.md "Do Not Do" entry?
Specifically check: do not bypass the `hai` CLI for mutations; do
not import from `skills/` inside Python runtime code (relevant for
Phase 2 refusal-in-code work); do not freeze the capabilities
manifest schema before its scheduled cycle (v0.2.3).

### G. Risk register completeness

G1. The plan names five risks in §"Risk profile". What sixth or
seventh risk is the plan missing? Specifically consider: schema
forward-compatibility once the paper is public; reproducibility
across machines; LLM API drift (cloud-condition models change between
runs).

G2. What attack would a hostile NeurIPS Safe-AI workshop reviewer
make that the plan does not preempt? Consider: "your no_runtime
baseline is still gated by M1-M3 in the harness, so the score gap
is incomplete"; "your refusal-in-code is just hard-coded prompt
filtering"; "your fixtures are too small to generalise."

G3. The plan defers fine-tuning (D-PROJ-T). What is the cost of
this deferral if the maintainer's calendar later compresses? Is
there a packet that should be authored now but executed later, to
preserve optionality?

G4. The plan assumes Phase 1 audit reveals modest coupling. What
happens if Phase 1 finds extensive coupling, blowing the calendar?
The §"Calendar honesty" scope-cut ladder lists five cuts. Are these
cuts in the right order? Is cut 1 (drop M8 audit-chain ablation)
the cheapest, or is a different cut cheaper?

### H. Calendar realism

H1. The plan estimates 9-12 weeks of evening/weekend bandwidth for
the full plan. The maintainer is a first-year Imperial student with
external research-assistant commitments (per other project memory).
Is 9-12 weeks plausible, or optimistic? What evidence supports the
estimate?

H2. Phase 6 (benchmark task design with load-bearing coverage) is
gated by Phases 1, 2, 3, 4, and 5. Is the resulting critical path
realistic? What is the longest sequential chain of dependencies?

H3. The plan does not budget for review rounds (Codex audit, the
plan-audit loop). If empirical settling shape applies (3-4 rounds),
add 2-4 weeks. Does the calendar account for this?

### I. Reframe robustness

I1. What Phase 1 audit finding would invalidate the reframe entirely?
For example: "all five mechanisms are implemented in a single helper
that cannot be conditionally disabled." Is there a fallback plan if
the audit yields this finding?

I2. The reframe's strongest claim ("the runtime contract is the
intervention") rests on the runtime being separable from the model
and the prompt. Is there a version of HAI's architecture where this
separation is not crisp — for example, where some runtime logic is
generated from the manifest, which is itself in the prompt? Audit
whether such a coupling exists.

I3. If the maintainer's career strategy changes (e.g., a faster
runway to RE applications is needed), can the plan be cut to a Tier
0 + partial Tier 1 result in 4-6 weeks instead of 9-12? Trace the
cuts.

### J. Unintended doc inconsistencies

J1. Search the repo for references to the old condition values
(`local_prompt_only`, `cloud_prompt_only`, `local_manifest`,
`cloud_manifest`, `fine_tuned_local_manifest`). List each location.

J2. Search for `with_manifest`, `without_manifest`, and any
prompt-only language in active project docs. List references that
should now be reworded.

J3. Search for references to `governed_agent_bench.trajectory.v1`,
`governed_agent_bench.score.v1`, and `governed_agent_bench.task.v1`.
List references that should be updated to v2 (or where v1 is
intentionally retained as historical).

J4. Search `hai/reporting/plans/` for any plan or release proof that
references the runtime-contracts paper experimental design. Does any
historical doc imply prompt-first ordering in a way that could
mislead a future cold session?

## 3. Verdict format

Return exactly one of these verdict strings on the first line of
your response:

- `PLAN_COHERENT` — no findings; the reframe is internally consistent
  and externally defensible. (Surprising for round 1.)
- `PLAN_COHERENT_WITH_REVISIONS` — the reframe is sound but has
  specific findings the maintainer should address before downstream
  packets execute.
- `PLAN_INCOHERENT` — the reframe contradicts itself or canonical
  docs in ways that make the plan unsafe to execute as-is.

Then the rest of your response is the findings list and any
necessary explanation.

## 4. Findings template

For each finding:

```
### F-CDX-RFR-R1-NN — <short title>

**Severity:** critical | major | minor | nit
**Audit question:** <e.g., A2, B3>
**Where:** <file path>:<line range or anchor>
**Finding:** <one paragraph>
**Suggested fix:** <one paragraph; or `defer to maintainer`>
**Provenance check:** <what you verified on disk>
```

Number findings sequentially (`F-CDX-RFR-R1-01`, `-02`, ...).
`RFR` = reframe; `R1` = round 1.

## 5. Severity tags

- **critical** — blocks the reframe from execution; the plan must
  change before any downstream packet runs. Example: a contradiction
  between the new EXECUTION doc and a governance invariant in
  AGENTS.md.
- **major** — substantive flaw the reframe should fix in this audit
  round. Example: a Tier claim whose evidence requirement is
  insufficient; a missing mechanism in the inventory; a packet that
  is not bounded.
- **minor** — non-blocking but worth fixing. Example: vocabulary
  drift between two docs; a redundant field in a schema.
- **nit** — cosmetic. Example: a typo in a field description.

A finding's severity is independent of its difficulty to fix.
Critical findings can have one-line fixes. Minor findings can require
substantial edits.

## 6. Output requirements

Write your response to a single file at:

```
research/runtime_contracts_paper/codex_runtime_first_reframe_audit_response.md
```

The file's first line must be the verdict string. The remaining
content is the findings list followed by any closing observations.

Do not edit other files. This is a read-only audit. Suggested fixes
are descriptions, not patches.

If your response runs long, do not truncate findings. Better a long
honest list than a short curated one. The maintainer would rather
read 30 honest findings than 5 polished ones.

## 7. Provenance discipline

Before citing a file path, function name, line number, or exact
string, verify it against the filesystem. Do not trust this prompt
or the new EXECUTION doc; both are produced by the same author. If
a claim made in the new docs cannot be verified on disk, that is
itself a finding.

Specifically:

- File paths must exist (use `ls` or `find`).
- Function names cited from HAI source must exist (use `grep`).
- Line ranges must point to the lines you describe (read the file).
- Cross-doc references (`see X.md §Y`) must lead to the named
  section.
- Schema enum values must match across files when the docs claim
  they do.

If you cite something you have not verified, mark the finding's
"Provenance check" field with `UNVERIFIED — citation only`.

## 8. Out-of-scope for this round

- Do not propose changes to `AGENTS.md` settled decisions or
  governance invariants without an explicit reframe-level finding.
- Do not propose new HAI release cycles. The freeze is locked
  (D-PROJ-013/014/015 plus the 2026-05-08 freeze entry).
- Do not propose architectural changes to HAI source unless they
  follow from a Phase 1 audit finding the maintainer cannot avoid.
- Do not write the experiment results. The benchmark has not run.
  The audit is on the plan, not on data.
- Do not propose alternative paper venues. Venue choice is OD-PROJ-001
  in DECISIONS.md, kept neutral on purpose.

## 9. Tone

Hostile but fair. The maintainer values pushback over validation.
Phrase findings as "this is wrong because X," not "you might consider
Y." If a finding is actually a question and not a flaw, mark it
`nit` or fold it into the closing observations rather than inflating
findings count.

## 10. Empirical settling shape

This is a substantive PLAN-class change (eight phases, ~25 new
packets, three schema breaks, three new top-level decisions). The
project's empirical settling shape for substantive PLANs is
**10 → 5 → 3 → 0 findings over 4 rounds** (validated v0.1.11 +
v0.1.12). A round-1 verdict producing zero or one finding would be
suspicious; that suggests either the reframe is genuinely clean
(unlikely for a same-day rebuild) or the audit was shallow. Default
to assuming round 1 will have ~10 substantive findings.

If round 1 has *more* findings than 10, that is also informative
and preferable to a curated short list.

## 11. Self-check before submitting

Before writing your verdict line, answer these to yourself:

- Did you actually read every file in §1.1 and §1.2?
- Did you cite at least one file path from §1.3 (HAI source)?
- Did each finding have a provenance check?
- Did you assign severities consistently with §5's calibration?
- Did you avoid duplicating findings that follow from the same
  underlying issue? (One root cause = one finding, with downstream
  manifestations listed inside.)

When you submit, the maintainer (Dom) will hand the response to
Claude (the planning agent that produced the reframe). Claude will
draft maintainer responses to each finding, the maintainer will
adjudicate, and round 2 will begin once the response file is in
place.
