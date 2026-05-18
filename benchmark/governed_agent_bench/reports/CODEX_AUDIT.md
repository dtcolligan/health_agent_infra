# Codex Audit: e0cb7db Range

Verdict: **PASS_WITH_FIXES**

Scope audited: `git log --reverse d12a353^..e0cb7db`, `git diff --stat d12a353^..e0cb7db`, and the code/docs/tasks touched by those commits. I did not trust commit messages or tests as evidence; I re-ran the full suites and regeneration commands, then fixed the P1 gaps in new commits:

- `f64fd2b benchmark: anchor scorer behavior in config`
- `77fb608 benchmark: run offline baseline over 28 tasks`
- `4baa4f6 benchmark: bound static isolation claims`

## Findings

| ID | Severity | File:line | Evidence | Why it matters | Fix |
|---|---|---:|---|---|---|
| F-01 | P1 | `e0cb7db:benchmark/governed_agent_bench/scorer/core.py:20` | Pre-fix scorer carried `DEFAULT_THRESHOLDS` and `CRITICAL_VIOLATIONS` in code while `scorer_config_hash()` only hashed config bytes (`e0cb7db:.../core.py:68`). `test_scorer_config_anchor` checked the hash/policy id but not behavior equality. | D-14/D-17 pre-registration was only a byte anchor, not behavior-by-construction. A reviewer could change thresholds or criticality in config without changing scorer behavior. | `f64fd2b`: `scorer/core.py` now loads thresholds and critical violation kinds from `scorer_config.paper_v1.json` (`core.py:30`, `core.py:50`); config has machine-read `scorer_behavior` (`scorer_config.paper_v1.json:17`); tests assert equality. |
| F-02 | P1 | `e0cb7db:benchmark/governed_agent_bench/scorer/core.py:283` | Pre-fix `_observed_stdout_texts` skipped any stdout that parsed as JSON (`e0cb7db:.../core.py:309`) and read `(root / ref)` without confining resolved paths (`e0cb7db:.../core.py:306`). | A prose answer that happened to be valid JSON was a false negative for clinical scanning; `stdout_ref` could also escape the observation root and affect scoring from unrelated files. | `f64fd2b`: stdout refs are resolved under `observation_root`, capped at 1 MB, and JSON is skipped only for declared JSON contract surfaces (`core.py:310`, `core.py:323`, `core.py:331`, `core.py:343`). Added regression tests for JSON-shaped prose and path escape. |
| F-03 | P1 | `e0cb7db:benchmark/governed_agent_bench/baselines/rule_baseline.py:24` | Pre-fix `TASK_IDS` listed only 10 tasks, while D-19 claimed a 28-task suite. Reproducing before fixes produced `row_count: 19` and `task_ids: "default_mvp_task_set"` in `/tmp/audit_repro/offline_repro_manifest.json`. | The default offline reproduction path did not exercise the claimed suite. This made “28 tasks” and “fully satisfying D-19” materially incomplete. | `77fb608`: rule baseline discovers the full 28-task inventory (`rule_baseline.py:24`), generic deterministic actions cover all current tasks (`rule_baseline.py:29`), and the repro manifest records concrete task ids (`reproduce_offline.py:75`). |
| F-04 | P1 | `e0cb7db:benchmark/governed_agent_bench/results/isolation_matrix.py:1` | Pre-fix static isolation wording said it evaluated/proved D-17 over hand-authored pairs; live isolation also said the static matrix “proves D-17” (`e0cb7db:.../live_isolation.py:3`). The static matrix hand-inserts `mechanism_disabled` markers and substitutes off-steps, so per-mechanism deltas are scorer canaries, not live causal proof. | The paper thesis depends on not overclaiming. Treating static oracle pairs as empirical mechanism isolation would be circular and likely fail review. | `4baa4f6`: generated matrix now declares `evidence_tier: static_oracle_pairs` and a scope note (`isolation_matrix.py:48`); SPEC/README/card now state static canary vs live-causality limits (`SPEC.md:88`, `SPEC.md:427`); live report states only M7 is live (`live_isolation.py:171`). |
| F-05 | P1 | `e0cb7db:benchmark/governed_agent_bench/results/live_isolation.py:43` | Pre-fix STATIC_ONLY reason for M5 said `rule_baseline` was not agent-classified, but HAI treats `rule_baseline` as agent-classified in `health_agent_infra.core.refusal.agent_safe` (`AGENT_CLASSIFIED_INVOCATION_CONTEXTS`). | The live-isolation limitation was surfaced, but one reason was wrong. This weakens trust in the limitation accounting. | `4baa4f6`: M5 reason now says the marker is reachable but the current scorer conflates attempted unsafe command with blocked consequence (`live_isolation.py:43`). M6 reason now names the M5-before-M6 and user-context-hook issue (`live_isolation.py:50`). |
| F-06 | P1 | `benchmark/governed_agent_bench/harness/core.py:414` | Independent benchmark mypy probe initially failed: `_trajectory_id` accepted `dict[str, Any]` but was called with `list[dict[str, Any]]`. The mandated `uvx mypy hai/src/health_agent_infra` does not type-check benchmark code. | New benchmark code had no clean type-checking signal; the existing required mypy command could not catch benchmark regressions. | `77fb608`: corrected the annotation. Post-fix `MYPYPATH=benchmark:hai/src uvx mypy --explicit-package-bases benchmark/governed_agent_bench` passes. |

No P0 remained after remediation. I found no private health rows in the 28 task JSONs. L6 prompts and off-oracle canaries intentionally contain clinical-boundary pressure; they are synthetic refusal tests, not required clinical outputs. This remains a bounded construct-validity caveat, not a D-12 private-data breach.

## Per-Commit Assessment

| Commit | Claim | Actual assessment |
|---|---|---|
| `d12a353` | Option C scorer plus D-14..D-21 pre-registration. | Implemented stdout-only clinical scan, marker attribution, `mechanism_disabled_unexpected`, schema scaffolding, and config hash. Overclaimed config anchoring because thresholds/criticality stayed in code. JSON skip was too broad and path handling was unsafe. |
| `e96dabb` | Scaled oracle-pair structure plus first DR-5 task. | Added task/oracle structure toward coverage. Directionally correct, but the coverage proof was still hand-authored static oracle evidence, not live attribution. |
| `e294862` | M5 and M7 reach >=3 tasks. | Added tasks/oracles that raise counts. Construct is static canary coverage; M5 live reason later proved inaccurate. |
| `5376641` | M6 and M8 reach >=3 tasks. | Added tasks/oracles for proposal gate and audit chain. M8 deltas are largely driven by hand-authored command substitutions, so attribution must be bounded as static sensitivity. |
| `395ae2e` | no_runtime_enforcement sanity-floor coverage. | Added two composite tasks and tests. Correctly framed by D-20 as sanity floor, not per-mechanism H1 attribution. |
| `6d54f29` | D-17 isolation matrix plus >=3 oracle pairs/mechanism. | Produced deterministic static matrix with 25 rows by the end of the range. The generator was useful, but wording implied proof stronger than hand-authored pairs support. |
| `4600958` | schema_invalid completes the 11-kind taxonomy. | Added proposal-payload validation and metric wiring. No crash found in normal path; `schema_invalid` is non-critical and gates `schema_validity`. Remaining robustness risk is acceptable after full tests. |
| `2c59a5a` | Completeness oracles for two straggler tasks. | Filled oracle gaps. Same static-oracle limitation applies. |
| `e75dacc` | Reach 28 tasks, fully satisfying D-19. | Task files reached 28 and validated, but default offline repro/rule baseline still ran only 10 tasks. Fixed in `77fb608`. |
| `e0cb7db` | Live-HAI D-17 isolation probe. | Added a real hermetic M7/refusal probe. The limitation that M4/M5/M6/M8 are static-only is now explicit; original M5 reason was inaccurate and fixed. |

## Reproduction Evidence

Pre-fix independent runs:

- `uv run pytest hai/verification/tests -q` -> `2999 passed, 4 skipped`.
- `PYTHONPATH=benchmark uv run pytest -q benchmark/verification/tests` -> `122 passed`.
- `uvx mypy hai/src/health_agent_infra` -> clean, but did not cover benchmark code.
- `uvx bandit -ll -r hai/src/health_agent_infra benchmark/governed_agent_bench` -> no medium/high issues.
- `reproduce_offline.py --output-dir /tmp/audit_repro` -> passed but only `row_count: 19`, exposing F-03.
- `isolation_matrix.py --output-dir /tmp/audit_iso` -> `row_count: 25`, `all_isolated: true`.
- `live_isolation.py --output-dir /tmp/audit_live` -> `live_count: 1`, `static_only: [agent_safe, audit_chain, proposal_gate, validation]`.
- `uv run hai doctor` -> completed with `overall: [WARN] warn`; warnings were local state/readiness staleness, not benchmark failures.

Post-remediation targeted runs:

- `PYTHONPATH=benchmark uv run pytest -q benchmark/verification/tests/test_scorer_mechanism_disabled.py` -> `11 passed`.
- `PYTHONPATH=benchmark uv run pytest -q benchmark/verification/tests/test_rule_baseline.py benchmark/verification/tests/test_rule_ablation.py benchmark/verification/tests/test_offline_repro.py` -> `5 passed`.
- `PYTHONPATH=benchmark uv run pytest -q benchmark/verification/tests/test_isolation_matrix.py benchmark/verification/tests/test_live_isolation.py benchmark/verification/tests/test_task_load_bearing_coverage.py` -> `6 passed`.
- `MYPYPATH=benchmark:hai/src uvx mypy --explicit-package-bases benchmark/governed_agent_bench` -> clean.
- `uvx ruff check ...` over changed benchmark files/tests -> clean.

Final full-suite verification after remediation:

- `uv run pytest hai/verification/tests -q` -> `2999 passed, 4 skipped`.
- `PYTHONPATH=benchmark uv run pytest -q benchmark/verification/tests` -> `124 passed`.
- `uvx mypy hai/src/health_agent_infra` -> clean.
- `MYPYPATH=benchmark:hai/src uvx mypy --explicit-package-bases benchmark/governed_agent_bench` -> clean.
- `uvx bandit -ll -r hai/src/health_agent_infra benchmark/governed_agent_bench` -> no medium/high findings under the `-ll` gate.
- `PYTHONPATH=benchmark uv run python benchmark/governed_agent_bench/reproduce_offline.py --output-dir /tmp/audit_repro` -> `row_count: 67`, `violation_count: 0`, `model_calls: false`, 28 task ids, 7 runtime modes.
- `PYTHONPATH=benchmark uv run python benchmark/governed_agent_bench/results/isolation_matrix.py --output-dir /tmp/audit_iso` -> `row_count: 25`, `all_isolated: true`, `model_calls: false`.
- `PYTHONPATH=benchmark uv run python benchmark/governed_agent_bench/results/live_isolation.py --output-dir /tmp/audit_live` -> `live_count: 1`, `all_live_isolated: true`, `static_only: [agent_safe, audit_chain, proposal_gate, validation]`.
- `uv run hai doctor` -> completed with `overall: [WARN] warn`; warnings were local source/readiness/intake state, not benchmark or package failures.
