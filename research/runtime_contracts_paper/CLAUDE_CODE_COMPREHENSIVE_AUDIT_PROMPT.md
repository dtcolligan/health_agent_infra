# Claude Code Comprehensive Audit Prompt

Use this prompt in Claude Code to audit Codex's runtime-contract paper
work before Dom reviews it.

```text
You are Claude Code acting as an adversarial, senior engineering and
research-artifact auditor. Your job is to find every bug, mistake,
unsupported claim, stale document, broken invariant, missing test, weak
evidence path, unsafe assumption, and governance violation in Codex's
work. Do not be polite to the work. Be precise, evidence-driven, and
skeptical.

Repository:

- Path: /Users/domcolligan/health_agent_infra
- GitHub remote: git@github.com:dtcolligan/health_agent_infra.git
- Codex pushed range to audit: a5d2fc4..HEAD
- Base commit before Codex project packet series:
  a5d2fc4 chore: migrate repo to owner lanes
- Core Codex work target before this audit prompt was added:
  6ce5f58 docs(research): add codex work inspection index
- If this prompt is committed after 6ce5f58, include the prompt and any
  inspection-index edits in the audit for accuracy, but treat the core
  implementation/research work as the packet series from a5d2fc4 through
  6ce5f58.

Hard operating rules:

1. Read AGENTS.md first and obey it.
2. Before reading or writing anything else, run:
   - pwd
   - git log -1 --oneline
   - git status --short
3. Treat any uncommitted dirty worktree changes as Dom/user-owned unless
   you can prove otherwise. Do not revert them. Do not stage them. Do
   not include them as Codex committed work unless your finding is about
   confusing inspection state.
4. Do not push, open PRs, call paid/cloud/model APIs, use private health
   data, use live credentials, use live wearable data, or run model
   inference.
5. Do not fix anything unless Dom explicitly asks for fixes. This audit
   is a review pass. Findings first.
6. Do not trust Codex's summaries. Verify claims from disk, git history,
   schemas, tests, generated artifacts, and command output.
7. Treat passing tests as weak evidence until you verify the tests cover
   the stated requirement.

Primary objective:

Audit whether Codex correctly planned and executed the runtime-contract
research project as far as it claims, while respecting the explicit Dom
judgement gate. Find all defects in:

- the plan;
- HAI runtime substrate changes;
- governed operator surface;
- GovernedAgentBench fixtures, manifests, schemas, tasks, harness,
  scorer, trajectories, rule baseline, ablations, evidence tables,
  figures, taxonomy, benchmark card, and reproducibility package;
- paper scaffolding;
- gate handling;
- repo organization and inspection surface.

First reading order:

1. AGENTS.md
2. research/runtime_contracts_paper/CODEX_WORK_INSPECTION_INDEX.md
3. research/runtime_contracts_paper/AUTONOMOUS_PROJECT_EXECUTION_PLAN.md
4. research/runtime_contracts_paper/AUTONOMOUS_GATE_HANDOFF.md
5. research/runtime_contracts_paper/MODEL_ROSTER_DECISION_BRIEF.md
6. benchmark/governed_agent_bench/BENCHMARK_CARD.md
7. benchmark/governed_agent_bench/REPRODUCIBILITY.md
8. benchmark/governed_agent_bench/README.md
9. benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md
10. benchmark/governed_agent_bench/BENCHMARK_SPEC.md

Then inspect the actual implementation and tests. Use rg/git, not only
the docs.

Commit/range audit commands:

- git log --oneline --reverse a5d2fc4..HEAD
- git diff --stat a5d2fc4..HEAD
- git diff --name-status a5d2fc4..HEAD
- git show --stat 2f0d95f
- git show --stat b81c29e
- git show --stat 58ed8c7
- git show --stat 75af33f
- git show --stat e6f21cd
- git show --stat 7b692f5
- git show --stat 6ce5f58

Audit questions. Answer each with evidence, not vibes.

Planning and governance:

- Does AUTONOMOUS_PROJECT_EXECUTION_PLAN.md actually satisfy Dom's
  requested plan requirements: definition of done, ordered phases,
  packet queue with dependencies, acceptance tests/evidence for every
  packet, Codex-autonomous vs Dom-judgement packets, stop gates,
  commit boundaries, completed-work inventory, and next executable
  packets?
- Did Codex incorrectly proceed past a Dom judgement gate at any point?
- Did Codex create or imply a model roster without Dom approval?
- Did Codex run, configure, or authorize local model inference, cloud
  model APIs, paid APIs, private data, live credentials, or live
  wearable data?
- Did any document strengthen claims beyond the committed evidence?
- Are any settled governance decisions reopened or weakened: W57,
  no clinical claims, local-first, audit chain, Strava exclusion,
  MCP autoload exclusion, threshold mutation prohibition?

HAI runtime substrate:

- Are runtime modes implemented correctly and isolated from one another?
- Do mechanism-off modes only work in hermetic benchmark conditions?
- Are mechanism_disabled markers emitted exactly where expected?
- Is agent_safe dispatch enforcement actually enforced at runtime, not
  merely documented?
- Does the refusal envelope fail closed for clinical/out-of-contract
  requests?
- Does proposal/commit separation still protect user-gated operations?
- Are audit-chain invariants preserved?
- Are there hidden bypasses around CLI mutation boundaries or direct DB
  writes?
- Did any change violate the code-vs-skill invariant?

Capabilities and operator surface:

- Does the v2 capabilities manifest honestly expose runtime modes,
  mutation classes, refusal taxonomy, exit codes, and agent_safe
  metadata?
- Are manifest snapshots frozen, reproducible, and clearly identified?
- Are stale manifest/drift cases realistic and correctly scoped?
- Are read surfaces sufficient for the benchmark tasks without raw
  SQLite inspection becoming the normal path?

Harness:

- Does the harness force structured operator actions instead of shell
  text?
- Does it construct exactly one deployment-realistic prompt path?
- Does it inject the correct manifest snapshot and prompt hash?
- Does it set runtime mode and HAI_INVOCATION_CONTEXT correctly?
- Does it execute subprocess HAI commands safely and capture stdout,
  stderr, exit code, observations, and mechanism_disabled markers?
- Does it write trajectories that match the schema?
- Does any harness path silently skip policy, validation, refusal, or
  agent_safe enforcement?
- Are invalid model outputs, malformed JSON, timeouts, and failed
  subprocesses represented as reportable outcomes?

GovernedAgentBench:

- Are fixtures synthetic and hermetic? Check that they do not contain
  private health data, live exports, names, emails, credentials, or
  copied real-user prose.
- Do all fixture builders use HAI/fixture-safe paths rather than direct
  unsafe state mutation, unless explicitly justified?
- Are frozen and stale manifests consistent with the runtime and tasks?
- Do task schemas require the fields the scorer needs?
- Do tasks cover the claimed levels and load-bearing mechanisms?
- Are hand-authored trajectories actually good/bad in the way claimed?
- Does known-good/known-bad validation test meaningful failure modes?
- Does task load-bearing coverage prove real behavioral sensitivity, or
  only satisfy a superficial enum/count check?
- Does the benchmark card overclaim intended use, model evidence, or
  generality?

Scorer:

- Is the scorer deterministic and offline?
- Are thresholds explicit, non-null, and tied to scorer_config_hash?
- Are metric definitions coherent with the benchmark spec?
- Are violations classified correctly?
- Are hallucinated commands, invalid commands, unsafe mutation, direct
  state writes, clinical claims, refusal errors, drift failures, and
  mechanism_disabled surprises caught?
- Can a bad trajectory pass because of weak matching, missing checks, or
  an overly permissive schema?
- Are scores reproducible from committed inputs?

Rule baseline and ablations:

- Does the rule baseline run through the same harness interface as a
  model condition where it matters?
- Is it clearly separated from model evidence?
- Are ablations holding the prompt constant and varying only runtime
  mode?
- Are ablation outputs actually regenerated from committed code, or are
  they stale/manual?
- Are mechanism-off results meaningful, or just artifacts of the rule
  baseline's implementation?

Evidence generation:

- Do evidence tables, figures, and taxonomy derive only from committed
  score/trajectory outputs?
- Are there hidden manual edits in generated evidence?
- Do figures/tables include enough anchors: scorer version/hash,
  prompt hash, manifest id, runtime mode, model class?
- Does the taxonomy aggregate correctly by level, mode, model, and
  mechanism?
- Are null, negative, or rule-only results represented honestly?

Reproducibility:

- Does benchmark/governed_agent_bench/reproduce_offline.py really rerun
  the offline path from scratch into a temp/output dir?
- Does it avoid default user HAI state?
- Does it avoid network, private data, credentials, live wearable
  sources, model APIs, and paid APIs?
- Does it produce stable outputs across runs?
- Are dependency/version assumptions documented?

Paper scaffolding:

- Are related-work citations real and correctly mapped to the
  prior-art matrix?
- Are there VERIFY/TODO placeholders that should block submission?
- Do methods/system sections describe what is actually committed, or
  aspirational work?
- Does any draft imply completed model experiments, model viability, or
  workshop-ready status not supported by evidence?
- Are limitations and non-use boundaries strong enough?

Model roster gate:

- Confirm benchmark/governed_agent_bench/model_roster.md does not exist.
- Confirm model_roster.schema.json is only a future format, not an
  authorization.
- Check whether the schema is too strict, too loose, inconsistent with
  trajectory/score model_class enums, or impossible to use.
- Check whether trajectories/scores require model_roster_hash for any
  tier/model condition that should require it.
- Check whether the decision brief gives Dom enough information without
  choosing models itself.

Repo organization and inspection:

- Is CODEX_WORK_INSPECTION_INDEX.md accurate?
- Does it omit important files or commits?
- Does it point to files that do not exist?
- Does it hide dirty user-owned files that materially affect review?
- Is the committed range described correctly?
- Is there a better inspection entry point or missing audit artifact?

Suggested local checks. Run as many as are reasonable. If a check is too
slow or blocked, say so and explain what coverage was lost.

- uv run pytest benchmark/verification/tests/test_model_roster_schema.py -q
- uv run pytest benchmark/verification/tests/test_operator_action_schema.py -q
- uv run pytest benchmark/verification/tests/test_harness_mvp.py -q
- uv run pytest benchmark/verification/tests/test_rule_baseline.py -q
- uv run pytest benchmark/verification/tests/test_rule_ablation.py -q
- uv run pytest benchmark/verification/tests/test_evidence_tables.py -q
- uv run pytest benchmark/verification/tests/test_result_figures.py -q
- uv run pytest benchmark/verification/tests/test_error_taxonomy.py -q
- uv run pytest benchmark/verification/tests/test_offline_repro.py -q
- uv run pytest benchmark/verification/tests -q
- uv run pytest hai/verification/tests -q
- uv run python benchmark/governed_agent_bench/reproduce_offline.py --output-dir /tmp/gab_claude_audit_repro
- test ! -e benchmark/governed_agent_bench/model_roster.md

Manual inspection requirements:

- Inspect schemas directly, not only tests.
- Inspect at least one fixture builder per fixture family.
- Inspect at least one hand-authored good and bad trajectory per claimed
  task family.
- Inspect scorer code paths for each reported metric/violation.
- Inspect generated evidence writers and their inputs.
- Inspect the exact prompt-rendering code and template hash behavior.
- Inspect HAI runtime-mode/refusal/agent_safe enforcement code and tests.

Required output format:

Start with findings, ordered by severity. Use this shape:

1. [SEVERITY: BLOCKER|HIGH|MEDIUM|LOW] Short finding title
   - Evidence: file path + line number or command output.
   - Why it matters: concrete impact on correctness, safety,
     governance, reproducibility, benchmark validity, or paper claim.
   - How to fix: minimal recommended fix or decision needed.

Then include:

- Coverage summary: what you inspected.
- Commands run and results.
- Requirements you could not verify.
- Suspected stale docs or unsupported claims.
- Any cases where Codex's own summary was misleading.
- A final verdict:
  - BLOCKED_BY_DEFECTS
  - BLOCKED_BY_DOM_GATE_ONLY
  - NEEDS_MORE_AUDIT
  - ACCEPTABLE_FOR_DOM_REVIEW_WITH_NOTES

Do not bury findings under a long narrative. If there are no findings,
say that explicitly and list residual risk. Prefer precise, actionable
bug reports over broad commentary.
```
