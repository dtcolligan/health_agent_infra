# Codex review - docs overhaul drafts

Date: 2026-04-26
Reviewer: Codex
Scope: `reporting/plans/docs_overhaul/drafts/` plus the current root docs and release artifacts they reference.

Post-rollout note: the `drafts/` tree was a staging artifact and was removed
after the approved docs landed at the repo root. Paths below are retained as
original review evidence, not live repo links.

## Verdict

**REVISE_BEFORE_SHIP.**

The drafts are directionally strong, but several are not drop-in yet. I found blocking drift against the current CLI, the current roadmap, link targets, rollout sequencing, and privacy/no-egress wording.

## Verification performed

- `uv run pytest safety/tests --collect-only -q | tail -1` -> `2081 tests collected in 1.21s`.
- `uv run hai --version` -> `hai 0.1.8`.
- `uv run hai capabilities --markdown` -> generated contract says `52 commands; hai 0.1.8; schema agent_cli_contract.v1` and contains no `hai writeback` command (`reporting/docs/agent_cli_contract.md:58`, `reporting/docs/agent_cli_contract.md:94`, `reporting/docs/agent_cli_contract.md:108`).
- `HYPOTHESES.md` H1-H5 matches `reporting/plans/multi_release_roadmap.md` section 3 exactly after normalizing heading depth.
- `git remote -v` points at `git@github.com:dtcolligan/health_agent_infra.git`, matching the GitHub URLs in `pyproject.toml` and draft `SECURITY.md` (`pyproject.toml:35`, `reporting/plans/docs_overhaul/drafts/SECURITY.md:39`).
- `pyproject.toml` confirms version `0.1.8`, Python `>=3.11`, author name `Dom Colligan`, and MIT license file (`pyproject.toml:7`, `pyproject.toml:10`, `pyproject.toml:11`, `pyproject.toml:12`).

## BLOCKING

### B1. Privacy/no-egress wording overclaims what the repo can guarantee

The draft README says "nothing leaves your device" (`reporting/plans/docs_overhaul/drafts/README.md:10`) immediately after saying a Claude Code agent reads wearable data (`reporting/plans/docs_overhaul/drafts/README.md:21`). It also says "No exfiltration" and "no cloud calls outside the configured pull adapter" (`reporting/plans/docs_overhaul/drafts/README.md:182`, `reporting/plans/docs_overhaul/drafts/README.md:183`). Draft `SECURITY.md` says state stays on device and the runtime makes outbound calls only to pull adapters (`reporting/plans/docs_overhaul/drafts/SECURITY.md:5`, `reporting/plans/docs_overhaul/drafts/SECURITY.md:9`, `reporting/plans/docs_overhaul/drafts/SECURITY.md:10`).

That is true for the Python runtime's own storage/telemetry posture, but not for an end-to-end Claude Code or Codex session unless the host model is local or separately configured not to transmit prompt contents. The docs should distinguish "the package stores and mutates state locally; the runtime has no telemetry" from "your host LLM/provider may receive the context you give it."

Fix: replace absolute no-egress language with scoped language, and add a short host-agent caveat in `README.md` and `SECURITY.md`.

### B2. `ROADMAP.md` is stale against the canonical roadmap

The draft roadmap says v0.2 is multi-source wearables, v0.3 is skill-narration eval harness, and v0.4 is MCP wrapper (`reporting/plans/docs_overhaul/drafts/ROADMAP.md:21`, `reporting/plans/docs_overhaul/drafts/ROADMAP.md:26`, `reporting/plans/docs_overhaul/drafts/ROADMAP.md:28`). The canonical roadmap now says v0.2 is visualization artifacts + BCTO, v0.3 is extension contracts + data-quality drift detection + first-run UX, and v0.4 is runtime portability + cryptographic provenance (`reporting/plans/multi_release_roadmap.md:409`, `reporting/plans/multi_release_roadmap.md:468`, `reporting/plans/multi_release_roadmap.md:562`).

Fix: rewrite draft `ROADMAP.md` from the current `multi_release_roadmap.md` section 4, not the older README roadmap bullets.

### B3. `AUDIT.md` links are wrong for a root-level file

Draft `AUDIT.md` links to `../v0_1_8/...`, `../v0_1_7/...`, `../v0_1_6/...`, and `../v0_1_9/BACKLOG.md` (`reporting/plans/docs_overhaul/drafts/AUDIT.md:21`, `reporting/plans/docs_overhaul/drafts/AUDIT.md:22`, `reporting/plans/docs_overhaul/drafts/AUDIT.md:23`, `reporting/plans/docs_overhaul/drafts/AUDIT.md:24`, `reporting/plans/docs_overhaul/drafts/AUDIT.md:30`, `reporting/plans/docs_overhaul/drafts/AUDIT.md:39`, `reporting/plans/docs_overhaul/drafts/AUDIT.md:51`). Those paths do not resolve from repo root. The real files are under `reporting/plans/v0_1_X/`.

Fix: change every audit artifact link to `reporting/plans/v0_1_X/...` before moving `AUDIT.md` to root.

### B4. New agent/security docs reintroduce retired `hai writeback`

Draft `AGENTS.md` tells agents to use `hai writeback` to persist a `TrainingRecommendation` (`reporting/plans/docs_overhaul/drafts/AGENTS.md:58`, `reporting/plans/docs_overhaul/drafts/AGENTS.md:59`) and repeats it in the do-not-do section (`reporting/plans/docs_overhaul/drafts/AGENTS.md:166`, `reporting/plans/docs_overhaul/drafts/AGENTS.md:167`). Draft `SECURITY.md` also lists `hai writeback` as a mutation boundary (`reporting/plans/docs_overhaul/drafts/SECURITY.md:13`).

`hai writeback` was retired in v0.1.4/v0.1.5, and the current generated contract has `hai propose`, `hai synthesize`, and `hai review record` as the relevant write paths (`reporting/docs/agent_cli_contract.md:94`, `reporting/docs/agent_cli_contract.md:98`, `reporting/docs/agent_cli_contract.md:108`). This is the exact kind of skill/CLI drift the project tests exist to prevent.

Fix: replace `hai writeback` with the current proposal/synthesis/review boundaries everywhere in the drafts.

### B5. Option B rollout would ship broken root links if PR-1 lands alone

The proposal recommends PR-1 as README + AGENTS + CLAUDE + REPO_MAP + `STATUS.md` deletion, with AUDIT/HYPOTHESES/CITATION in PR-2 and ROADMAP/ARCHITECTURE/SECURITY in PR-3 (`reporting/plans/docs_overhaul/PROPOSAL.md:282`, `reporting/plans/docs_overhaul/PROPOSAL.md:283`, `reporting/plans/docs_overhaul/PROPOSAL.md:285`, `reporting/plans/docs_overhaul/PROPOSAL.md:286`). But the draft README links to `AUDIT.md`, `HYPOTHESES.md`, `ARCHITECTURE.md`, `ROADMAP.md`, and `CITATION.cff` (`reporting/plans/docs_overhaul/drafts/README.md:29`, `reporting/plans/docs_overhaul/drafts/README.md:61`, `reporting/plans/docs_overhaul/drafts/README.md:62`, `reporting/plans/docs_overhaul/drafts/README.md:231`, `reporting/plans/docs_overhaul/drafts/README.md:236`, `reporting/plans/docs_overhaul/drafts/README.md:237`, `reporting/plans/docs_overhaul/drafts/README.md:238`, `reporting/plans/docs_overhaul/drafts/README.md:239`, `reporting/plans/docs_overhaul/drafts/README.md:249`). Draft `AGENTS.md` also links to root `ARCHITECTURE.md` and `AUDIT.md` (`reporting/plans/docs_overhaul/drafts/AGENTS.md:22`, `reporting/plans/docs_overhaul/drafts/AGENTS.md:28`).

Fix: either land all linked root docs in PR-1, or stage PR-1 links so they only point at files present in that PR. Do not ship an intermediate state with broken root links.

## SHOULD_FIX

### S1. `ARCHITECTURE.md` uses stale capability enum names

Draft `ARCHITECTURE.md` says `mutation_class` values are `read` / `write_state` / `write_audit` and idempotency values are `idempotent` / `idempotent_with_supersede` / `non_idempotent` (`reporting/plans/docs_overhaul/drafts/ARCHITECTURE.md:77`, `reporting/plans/docs_overhaul/drafts/ARCHITECTURE.md:78`, `reporting/plans/docs_overhaul/drafts/ARCHITECTURE.md:79`). The current generated contract uses `read-only`, `writes-state`, `writes-audit-log`, `yes`, `yes-with-supersede`, `yes-with-replace`, `no`, and `n/a` (`reporting/docs/agent_cli_contract.md:23`, `reporting/docs/agent_cli_contract.md:27`, `reporting/docs/agent_cli_contract.md:30`, `reporting/docs/agent_cli_contract.md:42`, `reporting/docs/agent_cli_contract.md:94`).

Fix: copy the enum names from the generated contract or avoid listing exact enum values in the one-page architecture.

### S2. Drafts imply the synthesis skill always runs, but v0.1.8 has two synthesis paths

Draft README's agent-researcher flow implies domain skills always flow through synthesis and straight to atomic commit (`reporting/plans/docs_overhaul/drafts/README.md:55`, `reporting/plans/docs_overhaul/drafts/README.md:56`, `reporting/plans/docs_overhaul/drafts/README.md:57`). Draft `ARCHITECTURE.md` says `daily-plan-synthesis` overlays rationale as an unconditional pipeline stage (`reporting/plans/docs_overhaul/drafts/ARCHITECTURE.md:39`).

The full architecture doc says `hai daily` ships the runtime-only path today and does not orchestrate the two-pass synthesis-skill overlay; the skill-overlay path is opt-in via `hai synthesize --bundle-only` then `--drafts-json` (`reporting/docs/architecture.md:361`, `reporting/docs/architecture.md:367`, `reporting/docs/architecture.md:376`, `reporting/docs/architecture.md:379`).

Fix: show the synthesis skill as an optional overlay path, not an always-on stage.

### S3. `AGENTS.md` overstates global threshold hardening

Draft `AGENTS.md` says "threshold runtime values" are all protected against bool-as-int and that validator + runtime resolver + tests all reject them (`reporting/plans/docs_overhaul/drafts/AGENTS.md:100`, `reporting/plans/docs_overhaul/drafts/AGENTS.md:101`, `reporting/plans/docs_overhaul/drafts/AGENTS.md:102`, `reporting/plans/docs_overhaul/drafts/AGENTS.md:103`). Round 4 explicitly deferred global threshold-runtime hardening outside `policy.review_summary` to v0.1.9 (`reporting/plans/v0_1_8/codex_implementation_review_round4_response.md:41`, `reporting/plans/v0_1_8/PLAN.md:755`, `reporting/plans/v0_1_9/BACKLOG.md:12`).

Fix: narrow the invariant to `policy.review_summary` runtime values, or rephrase as "known bool-as-int bug class is closed for review-summary thresholds; global threshold access hardening is v0.1.9 backlog."

### S4. `AGENTS.md` pre-decides the pending `STATUS.md` decision

Draft `AGENTS.md` says "No STATUS.md" and tells agents not to resurrect a status file (`reporting/plans/docs_overhaul/drafts/AGENTS.md:122`, `reporting/plans/docs_overhaul/drafts/AGENTS.md:123`). But retiring `STATUS.md` is still maintainer decision Q2 in the proposal (`reporting/plans/docs_overhaul/PROPOSAL.md:208`, `reporting/plans/docs_overhaul/PROPOSAL.md:213`, `reporting/plans/docs_overhaul/PROPOSAL.md:215`).

Fix: only keep this line if Dom answers Q2 yes. If Q2 is no, rewrite it to "Keep `STATUS.md` aligned with CHANGELOG and architecture."

### S5. `AUDIT.md` release dates disagree with the changelog

Draft `AUDIT.md` labels v0.1.7 as 2026-04-24 and v0.1.6 as 2026-04-23 (`reporting/plans/docs_overhaul/drafts/AUDIT.md:33`, `reporting/plans/docs_overhaul/drafts/AUDIT.md:44`). `CHANGELOG.md` records both v0.1.7 and v0.1.6 as 2026-04-25 (`CHANGELOG.md:278`, `CHANGELOG.md:346`).

Fix: use changelog dates unless the audit doc is intentionally recording a different event date, in which case label it explicitly.

### S6. `CITATION.cff` contains an ORCID placeholder and an email not verifiable from `pyproject.toml`

Draft `CITATION.cff` has `orcid: "https://orcid.org/0000-0000-0000-0000"` (`reporting/plans/docs_overhaul/drafts/CITATION.cff:16`). The Zenodo DOI placeholder is intentional per the handoff, but a fake ORCID should not ship. The email (`reporting/plans/docs_overhaul/drafts/CITATION.cff:15`) is also not present in `pyproject.toml`, whose author record has only the name (`pyproject.toml:12`, `pyproject.toml:13`).

Fix: remove the ORCID line unless Dom provides a real ORCID. Either add the email to `pyproject.toml` or treat it as SECURITY/contact-only metadata rather than "verified against pyproject."

### S7. Audit-cycle language should distinguish expectation from history

Draft `AGENTS.md` says every release runs around four rounds of audit and "Do not skip audit rounds" (`reporting/plans/docs_overhaul/drafts/AGENTS.md:125`, `reporting/plans/docs_overhaul/drafts/AGENTS.md:127`, `reporting/plans/docs_overhaul/drafts/AGENTS.md:136`, `reporting/plans/docs_overhaul/drafts/AGENTS.md:188`). Draft `AUDIT.md` itself shows v0.1.7 had one round and v0.1.6 had a different shape (`reporting/plans/docs_overhaul/drafts/AUDIT.md:37`, `reporting/plans/docs_overhaul/drafts/AUDIT.md:49`, `reporting/plans/docs_overhaul/drafts/AUDIT.md:61`).

Fix: say "current expectation for substantive releases" or "v0.1.8 demonstrated the four-round pattern; future release cycles should preserve it unless Dom explicitly scopes a smaller doc-only release."

### S8. The README's `hai today` sample should be marked illustrative or generated from a fixture

The draft calls the athlete snippet "sample output from `hai today`" (`reporting/plans/docs_overhaul/drafts/README.md:43`). It looks plausible, and the action/slug exist in the codebase, but I did not find that exact output as a generated fixture. Since this project is selling auditability and reproducibility, example CLI output should either be real fixture output or clearly marked illustrative.

Fix: generate a fixture-backed `hai today` excerpt, or relabel it as "shape of output."

## NICE_TO_HAVE

### N1. Add a root privacy pointer

There is no missing top-tier root doc that blocks this rollout. `README.md`, `AGENTS.md`, `CLAUDE.md`, `AUDIT.md`, `HYPOTHESES.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `SECURITY.md`, and `CITATION.cff` cover the important surfaces for a solo pre-1.0 project.

Given the health-data scope, I would still add a one-line pointer from root `SECURITY.md` to `reporting/docs/privacy.md` or later promote a short root `PRIVACY.md`. This is especially useful once the no-egress wording is tightened.

### N2. The `CLAUDE.md` shim is 13 lines, not 12

The proposal repeatedly calls it a 12-line shim, but the draft is 13 lines (`reporting/plans/docs_overhaul/drafts/CLAUDE.md:1`, `reporting/plans/docs_overhaul/drafts/CLAUDE.md:13`). Not a functional issue.

### N3. Hero visual is absent from the drafts

The proposal recommends a terminal-rendered hero visual (`reporting/plans/docs_overhaul/PROPOSAL.md:152`, `reporting/plans/docs_overhaul/PROPOSAL.md:155`), but the README draft ships no visual. This is not a blocker; given the factual drift above, I would defer the visual until the text is correct.

## Framing and style assessment

- **Opening sentence:** Mostly defensible. "Instead of letting the model drive" maps to a real failure shape: raw MCP/database access or LLM-authored decisions without code-owned policy. The more precise version would be "between model output and health-data decisions" because the LLM still reads governed snapshots.
- **Audit cycle as feature:** Reasonable in shape. The README gives it one short callout (`reporting/plans/docs_overhaul/drafts/README.md:27`), and `AUDIT.md` is artifact-index-first. It does not read as an "Audited 4x" badge. The main issue is factual/link hygiene, not tone.
- **Hypotheses:** Good. H1-H5 are an exact lift from the audited roadmap section and the separate file avoids crowding the README.
- **Settled decisions:** The guardrail framing is defensible because it tells future agents to write a proposal rather than act unilaterally (`reporting/plans/docs_overhaul/drafts/AGENTS.md:108`, `reporting/plans/docs_overhaul/drafts/AGENTS.md:109`, `reporting/plans/docs_overhaul/drafts/AGENTS.md:110`). The one exception is the pending `STATUS.md` decision noted in S4.
- **Style traps:** I did not find BDFL/steering-committee theater, lowercase-name pedantry, an "Audited 4x" badge, or a defensive over-naming of Codex. The audience snippets are a deliberate Q5 decision rather than an accidental Datasette-style user-role list.

## Maintainer decisions affected

The original Q1-Q5 still stand, but Phase 2 should add blocking yes/no questions before them:

1. Should I tighten the no-egress/privacy wording before continuing?
2. Should I rewrite the root `ROADMAP.md` draft from the current canonical roadmap before rollout?
3. Should I fix `AUDIT.md` links and retired `hai writeback` references before continuing?
4. Should I adjust Option B so no PR ships broken root links?

After those, ask the original Q1-Q5, with Q2 controlling whether the `AGENTS.md` "No STATUS.md" line stays.
