# Show HN launch post — three drafts + recommendation

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
`Show HN: A local governed agent runtime for my Garmin data (Claude Code + SQLite)`

*Alt title (shorter):* `Show HN: Governed agent runtime over my own health data`

### First comment

I got tired of health apps that give me opaque recommendations I can't
audit and that phone home with data I'd rather keep local. So I built
the thing I wanted: a single-user runtime that reads my Garmin data,
runs a Claude Code agent over it, and commits recommendations to a
local SQLite file on my own machine. Nothing leaves the device.

The interesting idea for me was the **skill/code split**. Python owns
every mechanical decision — classification bands, policy rules,
atomicity, schema validation. Markdown skills (the Claude Code kind)
own *only* judgment: picking from an already-constrained action set,
composing rationale, surfacing uncertainty. Skills never change an
action; code never writes prose. That split is what makes the agent
recommendations auditable instead of hand-wavy — every rule firing
lands in a typed table you can SELECT against.

Six domains in v1: recovery, running, sleep, stress, strength, and
(macros-only) nutrition. Each has its own state projection, rule
set, and readiness skill; a synthesis pass reconciles them via
codified cross-domain rules (e.g., "if yesterday was a hard session
and HRV is suppressed, downgrade today's planned run"). `hai daily`
runs the full loop in one command. `hai explain` reconstructs the
audit chain — proposals → rule firings → final recommendation.

It's not an MLOps project, not a wearable API, not clinical. It's
infrastructure a Claude Code agent consumes. It exists because I
wanted something I could actually trust, and every design tenet —
local, deterministic tools, governed skills — is what I'd want
protected as it scales.

Install: `pipx install health-agent-infra && hai init --with-auth
--with-first-pull`, then `hai daily` tomorrow morning. Requires a
Garmin device and Claude Code today; MCP portability and additional
wearables (Apple Health, Oura, Whoop) are on the roadmap.

Source: [GITHUB_URL]

Happy to answer questions about the architecture, the skill/code
boundary, or why I think local-first agents need to look like this.

---

## Framing B — Technical architecture

### Title
`Show HN: Governed agent runtime — Claude Code + SQLite + six domain skills`

### First comment

Most "AI health" projects lean hard on model capability and very
little on constraints. Health Agent Infra is the opposite: the model
(a Claude Code agent) operates inside a deterministic frame of Python
tools, with judgment limited to composing rationale over an
already-bounded action set.

Architecture in one paragraph: a local SQLite DB holds cross-domain
state projections for six health domains (recovery, running, sleep,
stress, strength, nutrition). A morning orchestrator — `hai daily` —
pulls fresh data, cleans it, projects accepted state, snapshots the
cross-domain bundle, and emits it to a Claude Code agent. The agent
invokes per-domain skills that emit typed `DomainProposal` objects.
A synthesis pass runs codified cross-domain rules (X-rules) over the
proposals, mutating drafts atomically. Every firing lands in
`x_rule_firing`; the final plan commits transactionally with its
recommendations and scheduled reviews. `hai explain` reconstructs
the chain for any day.

The invariants that matter:
- Python code never writes prose. Markdown skills never change an
  action. The boundary is enforced by `agent-safe` CLI annotations.
- All mutations are atomic. A partial failure rolls back; there's no
  "half-applied plan" state.
- Every read surface (`hai snapshot`, `hai explain`, `hai stats`,
  `hai doctor`) is strictly read-only.
- No remote calls except to Garmin's API with the user's own
  credentials (keyring). No telemetry.

It's MIT-licensed, runs on macOS and Linux, requires Python 3.11+
and Claude Code. 1200+ tests, 28 eval scenarios, atomic audit chain
end-to-end.

Install: `pipx install health-agent-infra && hai init --with-auth
--with-first-pull`.

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
Health Agent Infra is one: six domain skills, a synthesis skill, a
writeback-protocol skill, and an intake-routing skill, all composed
over a deterministic Python runtime with atomic commits and a real
audit chain.

The pattern I found worked:
- Python tools own every mechanical decision (classification bands,
  policy rules, atomicity, schema validation).
- Markdown skills own only judgment (picking from a constrained
  action set, composing rationale, surfacing uncertainty).
- The boundary is tight and enforced. Skills never change an action;
  code never writes prose. Every CLI command is annotated agent-safe
  or interactive; the agent only calls the agent-safe surface.

I applied this to personal health data because it's a domain with
enough mechanical structure to formalize (HRV bands, training load,
sleep stages, X-rules across domains) and enough judgment to make the
skill layer pull its weight (which proposal to surface, what
uncertainty to flag, how much rationale to write). Six v1 domains,
ten cross-domain X-rules, 28 eval scenarios, full audit chain.

The artifact I'd most value feedback on: `reporting/docs/architecture.md`
and `reporting/docs/agent_cli_contract.md`. The first documents the
boundary. The second is an auto-generated manifest of every CLI
surface the agent can call, including mutation class and idempotency.
Both are where the skills pattern earns its keep or doesn't.

MIT-licensed. Claude Code + Garmin today; MCP-portable and
multi-source on the roadmap.

Install: `pipx install health-agent-infra && hai init --with-auth
--with-first-pull`.

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
