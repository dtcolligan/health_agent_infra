# Demo Plan — Post-v0.1.10

> **Status.** Scaffold authored 2026-04-28. Dom flagged "complete a
> demo" as the immediate next focus after v0.1.10 ship. This doc
> captures what's known + the open decision points. Dom should
> confirm scope before the next session executes.
>
> **Why a scaffold, not a finished plan.** The shape of "the demo"
> wasn't fully specified at session-end — there are real choices
> about audience, format, and what the demo is meant to prove. Each
> choice changes the runbook. This file marks decision points
> explicitly with **DECIDE:** so Dom can pick when he resumes.

---

## 1. Decision points to confirm

### DECIDE 1 — Audience

Who is the demo for? The shape of the demo changes hard with this:

| Audience | Implication |
|---|---|
| **Recruiters / hiring managers (AI engineering)** | Show the engineering depth: governance runtime, audit chains, three-state reconciliation, the audit-cycle pattern itself. Format: portfolio walkthrough, ~10 min. |
| **Health-tech founders / collaborators** | Show the product thesis: local-first agentic personal-health, why the runtime/skill split matters, the W57 governance invariant. Format: live walkthrough, ~15-20 min. |
| **AI-savvy individual users (potential users of `hai`)** | Show the user-facing flow: morning briefing → intake → daily plan → review. Format: one-day-in-the-life narrative, ~5-7 min. |
| **Mixed (portfolio site / public)** | Self-driving asynchronous artifact: README + recording + sample state. |

Dom's user-context memory says he cares about "AI for health" and
"credible artifacts aligned with that direction" — that points
toward audience 1 or 2. But "demo" can also mean (3) for user
acquisition. Confirm.

### DECIDE 2 — Format

| Format | Pros | Cons |
|---|---|---|
| **Live recorded walkthrough** (Loom / asciinema) | Reusable; can be sent to multiple audiences. | Requires polished execution; mistakes mean re-record. |
| **Live in-person / Zoom** | Highest signal; questions handled in real time. | Single-shot; not reusable. |
| **Static artifact** (annotated screenshots + transcript) | Deepest reading; no time pressure. | Low engagement; harder to convey "this is a working system." |
| **Script + sample dataset** (anyone runs locally) | Strongest "this is real" signal. | Highest setup cost for the viewer. |

### DECIDE 3 — What the demo proves

The product has multiple claims — pick which the demo emphasises:

- **Claim A: Governance is real.** W57 + three-state audit chain +
  R-rule / X-rule transparency means the agent's recommendations
  are reproducible and explainable.
- **Claim B: Local-first works.** State stays in the user's SQLite
  DB; no telemetry; works offline.
- **Claim C: Code-vs-skill discipline pays off.** Deterministic
  Python runtime + judgment-layer skills means no recommendation
  drifts between model moods.
- **Claim D: This is dogfooded.** Maintainer's daily loop runs on
  the project's own `hai`; the persona harness drives 8 synthetic
  user shapes through the same pipeline.
- **Claim E: The pre-PLAN bug-hunt + audit-cycle pattern produces
  shippable releases.** v0.1.10 went R1 DO_NOT_SHIP → R3
  SHIP_WITH_NOTES via 3 Codex rounds.

Different demos lead with different claims. Recruiter audience →
A + E. Founder audience → B + C + D. User audience → user-flow
narrative.

### DECIDE 4 — Demo state setup

The demo needs realistic-but-curated state. Three options:

| Option | What | Cost |
|---|---|---|
| **Use Dom's own DB** | Personal data; most authentic; privacy-sensitive. | Have to scrub identifying details. |
| **Persona-derived demo state** | Pick one of the 8 personas (P2 female marathoner has the cleanest running-action story); seed via the existing `verification.dogfood.runner`. | Already exists — minor tweaks for narrative flow. |
| **Hand-crafted demo fixture** | New state designed for the specific narrative beats. | Highest authoring cost; cleanest story. |

Recommendation: persona-derived (option 2). The harness already
produces useful action matrices and `hai today` / `hai explain`
output. Fastest path.

---

## 2. Demo structure (skeleton — fill in once decisions land)

A 10-minute demo following the morning-briefing user shape:

### Beat 1 — Setup (1 min)

- One sentence on the project: "Local governance runtime for
  agentic personal-health software."
- One sentence on why this exists: "Health agents that talk to a
  user need to make reproducible, explainable recommendations.
  This is the runtime layer that makes that possible."
- Show `hai capabilities --json` to convey "this is a real CLI
  contract."

### Beat 2 — User flow (4 min)

Pick one persona's shape and walk through:

```bash
# Show today's snapshot — what the agent sees
hai today

# Walk through one day's audit chain — proposal → recommendation →
# review
hai explain --as-of 2026-04-28
```

Highlight:
- The deterministic per-domain band classifications (R-rules).
- The cross-domain reconciliation (X-rules).
- The three-state audit chain (`proposal_log` →
  `planned_recommendation` → `daily_plan`).
- Why `hai explain` is load-bearing (you can audit *why* the agent
  said what it said).

### Beat 3 — Engineering depth (3 min)

Pick **one or two**:

- **Persona harness.** `verification.dogfood.runner /tmp/demo` —
  show 8 synthetic users, 0 crashes, 3 expected residuals.
  Demonstrates regression infrastructure.
- **D12 / load-time validation.** Show a `thresholds.toml` that
  tries to override an int with a bool. Run `hai capabilities` →
  `ConfigCoerceError` at load time. Demonstrates type-safety
  invariant + how the architectural fix beats per-consumer fixes.
- **Audit cycle.** Show `reporting/plans/v0_1_10/` — walk through
  audit_findings → PLAN → Codex prompt/response × 3 rounds →
  RELEASE_PROOF. Demonstrates the engineering process, not just
  the product.

### Beat 4 — What's next + close (2 min)

- v0.1.11 thesis: audit-chain integrity (W-E + W-F).
- Strategic plan: `strategic_plan_v1.md` 12-24 month vision.
- One-line close: "It's open-source, on PyPI, dogfooded daily."

---

## 3. Pre-demo runbook (when Dom decides to execute)

1. Confirm DECIDE 1-4 in this doc.
2. Refresh local install: `pipx install --force …
   'health-agent-infra==0.1.10'`.
3. Set up demo state (persona-derived likely):
   ```bash
   rm -rf /tmp/hai_demo_state
   uv run python -m verification.dogfood.runner /tmp/hai_demo_state
   ```
   Then export `HAI_BASE_DIR=/tmp/hai_demo_state/p2_female_marathoner`
   and `HAI_STATE_DB=$HAI_BASE_DIR/state.db` for the demo session.
4. Walk the script once end-to-end before recording.
5. Record / present.
6. Capture artifact in `reporting/artifacts/demo/<date>/`.

---

## 4. Honest risks

- **Live demo brittleness.** `hai daily` against today's date
  depends on real intervals.icu data (or CSV fixture). For demo
  reliability, freeze a date in the persona harness output and
  use that.
- **Privacy.** If using Dom's own DB, scrub names / specific
  numbers / dates that identify him before recording.
- **Over-explanation.** The audit-cycle pattern is interesting to
  engineers but can lose a non-engineering audience. Right-size
  beat 3 to the audience picked in DECIDE 1.
- **What if a beat fails live?** Have a recorded backup of each
  beat ready (especially `hai explain` which depends on a populated
  audit chain).

---

## 5. Questions for the next-session Claude

When you (Claude in the next session) pick this up:

1. Which audience did Dom pick? (DECIDE 1)
2. Which format? (DECIDE 2)
3. Which claims is the demo leading with? (DECIDE 3)
4. Persona-derived state, hand-crafted, or scrubbed-personal?
   (DECIDE 4)
5. What's the timeline pressure? (Recording today vs. polished
   over a week.)

If Dom hasn't volunteered these on session start, **ask** — don't
guess. The shape of the demo is too dependent on these for
silent assumptions to be safe.
