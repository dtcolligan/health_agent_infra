# Show HN launch post — three drafts + recommendation

**Status:** launch draft, not current product truth. Refresh against
`reporting/docs/current_system_state.md` before reuse.

**Open Graph image.** Use [`assets/show_hn_card.png`](../../../assets/show_hn_card.png)
(1200 × 630, 1.21 MB) as the social card for whichever framing ships.
The card carries the "Health Agent Infra · Local plugin / runtime
wrapper around a personal-health agent" headline, a `hai daily`
terminal, the user-question speech bubble, and the local SQLite +
audit-chain motif. Source prompt:
[`reporting/plans/post_v0_1_15/gpt_image_prompts.md`](../../plans/post_v0_1_15/gpt_image_prompts.md)
slot 2.

The three framings from the v2 plan, each drafted as a complete Show HN
post. My recommendation is at the bottom.

A Show HN post has two parts that matter:
1. **Title** (≤80 chars, ≤8 words where possible). The single biggest
   conversion lever.
2. **First comment** (the "tell HN" that expands the title). Typically
   300–500 words. Longer is fine if it earns the attention.

Everything below is a draft in Dom's voice as best I can approximate
it. **Dom owns the final version** — even if a framing is picked
unchanged, read every sentence and replace any that doesn't sound like
something you'd say out loud.

---

## Framing A — Personal testimonial (recommended for Show HN)

### Title
`Show HN: A local health-agent runtime for my wearable data`

*Alt title (governance-led):* `Show HN: Governed agent runtime over my own health data`

### First comment

I got tired of health apps that give me opaque recommendations I can't
audit and that phone home with data I'd rather keep local. So I built
the thing I wanted: a single-user runtime where I talk to a shell-capable
agent in natural language, the agent operates a local CLI, and Python owns
the rules, state, validation, and commits. The package has no telemetry or
hosted backend; live pulls only call the source I configure.

I don't use it by memorizing commands. I tell the agent what I want, it reads
the `hai capabilities` contract, and it invokes the validated command path the
runtime exposes.

The interesting idea for me was the **skill/code split**. Python owns
every mechanical decision — classification bands, policy rules,
atomicity, schema validation. Markdown skills (the Claude Code kind)
own *only* judgment: picking from an already-constrained action set,
composing rationale, surfacing uncertainty. Skills never mutate actions;
code never improvises coaching prose. That split is what makes the agent
recommendations auditable instead of hand-wavy — every rule firing
lands in a typed table you can SELECT against.

What ships today: six domains, 14 packaged skills, 60 annotated CLI
commands, 25 SQLite migrations, 11 cross-domain X-rules, 66 packaged
eval scenario files (35 non-judge scenarios plus the adversarial judge
set), and a v0.1.15.1 release gate of
2631 passed tests. Each domain
has its own state projection, rule set, and readiness skill; synthesis
reconciles them via codified cross-domain rules. `hai daily` runs the morning
loop.
`hai explain` reconstructs the audit chain - proposals -> rule firings ->
final recommendation - from persisted rows.

It's not an MLOps project, not a wearable API, not clinical. It's
agent-native infrastructure: the user talks to the agent, the agent invokes
`hai`, and deterministic code bounds the state changes. It exists because I
wanted something I could actually trust, and every design tenet —
local, deterministic tools, governed skills — is what I'd want
protected as it scales.

Install: `pipx install health-agent-infra && hai init && hai auth
intervals-icu`, then `hai daily` tomorrow morning. Built for Claude Code
today; live pulls currently support intervals.icu as the preferred source and
Garmin Connect as best-effort, with a CSV fixture for offline runs.

Source: [GITHUB_URL]

Happy to answer questions about the architecture, the skill/code
boundary, or why I think local-first agents need to look like this.

---

## Framing B — Technical architecture

### Title
`Show HN: Governed agent runtime — Claude Code + SQLite + six domain skills`

### First comment

Most "AI health" projects lean hard on model capability and very
little on constraints. Health Agent Infra is the opposite: the user talks to
a shell-capable health agent, but the agent operates inside a deterministic
frame of Python tools, with judgment limited to composing rationale over an
already-bounded action set. Claude Code is the first compatible host, not the
product boundary.

Architecture in one paragraph: a local SQLite DB holds cross-domain
state projections for six health domains (recovery, running, sleep,
stress, strength, nutrition). A morning orchestrator — `hai daily` —
pulls fresh data, cleans it, projects accepted state, snapshots the
cross-domain bundle, and emits it to the host agent. The agent
invokes per-domain skills that emit typed `DomainProposal` objects.
A synthesis pass runs codified cross-domain rules (X-rules) over the
proposals, mutating drafts atomically. Every firing lands in
`x_rule_firing`; the final plan commits transactionally with its
recommendations and scheduled reviews. `hai explain` reconstructs
the chain for any day.

The invariants that matter:
- Python code never improvises coaching prose. Markdown skills never mutate
  actions. The boundary is enforced by `agent-safe` CLI annotations.
- All mutations are atomic. A partial failure rolls back; there's no
  "half-applied plan" state.
- Every read surface (`hai state snapshot`, `hai explain`, `hai stats`,
  `hai doctor`) is strictly read-only.
- No package telemetry or hosted backend. Live pulls call only the configured
  source (intervals.icu or best-effort Garmin Connect) with the user's own
  credentials in the OS keyring.

It's MIT-licensed, runs on macOS and Linux, requires Python 3.11+,
and is currently packaged around Claude Code as the first compatible
agent surface. Current shape: 60 annotated CLI commands, 14 packaged
skills, 2631 passing release-gate tests, 66 packaged eval scenario files,
atomic audit chain end-to-end.

Install: `pipx install health-agent-infra && hai init && hai auth
intervals-icu`.

Source: [GITHUB_URL]

Feedback especially welcome on the skill/code boundary — whether
that split is the right level of constraint, or whether it's too
rigid for the judgment-heavy parts.

---

## Framing C — Reference implementation (recommended for Claude Code audiences)

### Title
`Show HN: Reference implementation of Anthropic's skills pattern (multi-domain health)`

### First comment

Anthropic's skills pattern — markdown instructions that a Claude Code
agent invokes alongside deterministic tools — is elegant in the
abstract but scarce in the wild as a non-trivial end-to-end example.
Health Agent Infra is one: six domain skills, a synthesis skill, an
intent-router skill, an expert-explainer skill, and cross-cutting intake /
review / reporting / safety skills, all composed over a deterministic Python
runtime with atomic commits and a real audit chain.

The pattern I found worked:
- Python tools own every mechanical decision (classification bands,
  policy rules, atomicity, schema validation).
- Markdown skills own only judgment (picking from a constrained
  action set, composing rationale, surfacing uncertainty).
- The boundary is tight and enforced. Skills never mutate actions;
  code never improvises coaching prose. Every CLI command is annotated agent-safe
  or interactive; the agent only calls the agent-safe surface.

I applied this to personal health data because it's a domain with
enough mechanical structure to formalize (HRV bands, training load,
sleep stages, X-rules across domains) and enough judgment to make the
skill layer pull its weight (which proposal to surface, what
uncertainty to flag, how much rationale to write). Six v1 domains,
11 cross-domain X-rules, 66 packaged eval scenario files, full audit chain.

The artifact I'd most value feedback on: `reporting/docs/architecture.md`
and `reporting/docs/agent_cli_contract.md`. The first documents the
boundary. The second is an auto-generated manifest of every CLI
surface the agent can call, including mutation class and idempotency.
Both are where the skills pattern earns its keep or doesn't.

MIT-licensed. Claude Code today; intervals.icu is the preferred live source,
Garmin Connect is best-effort, and MCP portability / broader source support
are on the roadmap.

Install: `pipx install health-agent-infra && hai init && hai auth
intervals-icu`.

Source: [GITHUB_URL]

---

## Recommendation

**Pick Framing A for the HN launch.**

Reasoning:
- HN front-page conversion skews heavily on the *human story* in the
  first two sentences. "I got tired of X so I built Y" is an evergreen
  HN structure that beats "here is a reference implementation of Z"
  on raw upvote rate.
- The governance pitch (Framing B) is correct but generic — many
  projects claim auditability. Doesn't differentiate in a skim.
- The reference-implementation framing (Framing C) is better for a
  narrower audience (Claude Code forums, r/Anthropic) because it
  flags "interesting to people thinking about agent architecture."
  On HN generally it undersells — positions the project as an
  example of someone else's idea.

**If the primary channel changes to Claude Code communities** (Discord,
internal forums, r/Anthropic): switch to Framing C. It lands harder
with the skills-pattern-curious audience and doesn't have to compete
for HN's attention budget.

**If posting to r/QuantifiedSelf or r/selfhosted**: use Framing A's
body but change the title to lead with the wearable + local-first
angle rather than the AI angle. QS readers have high tolerance for
technical depth but will bounce off "AI" framing that feels
promotional.

## What Dom owns

- **The opening two sentences of Framing A.** They need to sound
  exactly like you'd write them, not like me approximating you. If
  any of my phrasing is even slightly off, rewrite it — the
  first-person hook only works when the voice is real.
- **The "Happy to answer questions about..." closing.** Pick the
  topics you actually want to discuss. That shapes who engages.
- **The timing.** HN is best Tue–Thu, 8–10am PT. Don't post right
  before a long meeting — the first hour is when engagement is
  load-bearing and you want to be responsive.
- **`[GITHUB_URL]`** — replace with the public repo URL before
  posting. Verify the install command works end-to-end on a fresh
  machine right before submission.

## What I'd NOT do

- Cross-post simultaneously to HN and Reddit. One shot per venue;
  preserve the novelty for each.
- Ask friends to upvote. HN detects rings; a well-written post earns
  its placement or it doesn't.
- Respond defensively to criticism. If someone says "this is just X,"
  acknowledge the overlap and state what's different in one sentence.
  The people reading the thread are your real audience; the
  commenter has already decided.
