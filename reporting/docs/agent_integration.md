# Agent Integration

How a Claude agent (or open Claude-equivalent) installs and uses
Health Agent Infra v1.

The package ships two things the agent consumes:

1. **A CLI called ``hai``** — deterministic subcommands on the
   user's PATH.
2. **Fourteen markdown skills** under ``skills/`` — six per-domain
   readiness skills, a synthesis skill, an intent-router skill
   (NL → CLI workflow mapping; consumes ``hai capabilities --json``),
   an expert-explainer skill, plus cross-cutting (strength-intake,
   merge-human-inputs, review-protocol, reporting, safety).

The agent reads skills, makes judgment calls, and invokes CLI
subcommands to move structured state. The CLI validates the
agent's output at two determinism boundaries (``hai propose`` and
``hai synthesize``).

## Install

```bash
cd /path/to/health_agent_infra
pip install -e .                # or `pip install health-agent-infra`
hai setup-skills                # copies skills to ~/.claude/skills/
hai state init                  # creates the SQLite state DB + applies migrations
```

Verify:

```bash
hai --help
ls ~/.claude/skills/
# recovery-readiness  running-readiness  sleep-quality  stress-regulation
# strength-readiness  nutrition-alignment  daily-plan-synthesis
# intent-router  expert-explainer
# strength-intake  merge-human-inputs  review-protocol  reporting  safety
```

## Claude Code

Claude Code discovers the skills automatically from
``~/.claude/skills/``. Each skill's ``allowed-tools`` frontmatter
scopes the CLI subcommands it may invoke — e.g., the
``recovery-readiness`` skill allows
``Bash(hai propose --domain recovery *)`` but nothing else.

Typical daily loop:

1. User: "Plan my day."
2. Agent invokes ``hai pull`` (or ``hai pull --live`` when a Garmin
   live-pull is configured) and any needed ``hai intake *``
   commands.
3. Agent runs ``hai clean`` + ``hai state reproject`` to refresh
   accepted state.
4. Agent reads ``hai state snapshot --as-of <date> --user-id <u>``.
5. Per domain, agent reads the domain's readiness skill + the
   snapshot's domain block, honours any ``policy_result.forced_action``
   / ``capped_confidence``, composes a ``DomainProposal``, and
   invokes ``hai propose --domain <d> --proposal-json <p>``.
6. With all six proposals in proposal_log, agent invokes ``hai
   synthesize --as-of <date> --user-id <u>``. The runtime applies
   Phase A mutations to drafts, runs Phase B, and atomically commits
   the daily_plan + x_rule_firings + N recommendations in one SQLite
   transaction. To overlay the daily-plan-synthesis skill's
   rationale prose on top, the agent uses the two-pass form:
   ``hai synthesize ... --bundle-only`` reads the bundle (read-only,
   no commit), the skill returns a drafts overlay, and a second call
   to ``hai synthesize ... --drafts-json <path>`` finishes the
   commit. ``hai daily`` ships the runtime-only path; the skill-
   overlay path is opt-in.
7. Agent uses the ``reporting`` skill to narrate the synthesised
   plan back to the user.
8. Next morning: agent records outcomes via ``hai review record
   --domain <d>``.

## Claude Agent SDK

Two supported paths:

1. **CLI subcommand dispatch** — the SDK agent shells out to
   ``hai``. Same flow as Claude Code; fully agent-agnostic.
2. **Direct Python imports** — if the SDK runs in the same Python
   environment where ``pip install -e .`` happened, the agent can
   ``from health_agent_infra.core.state.snapshot import
   build_snapshot`` and call functions directly. Skips subprocess
   overhead; couples the agent to Python.

For the SDK, skill discovery is not automatic. Either upload skills
to the Anthropic Skills API or reference them by file path in your
agent's system prompt.

## Open Claude-equivalent agents

Any agent with both:

- A shell-exec tool (for ``hai`` subcommands), AND
- A way to load markdown fragments at session start (for the
  skills)

can drive this package. The wire contract is JSON at the three
determinism boundaries.

## Determinism boundaries (three places the runtime refuses)

1. **``hai propose``** — validates a DomainProposal against
   ``core/writeback/proposal.py :: validate_proposal_dict``.
   Checked invariants: ``required_fields_present``,
   ``forbidden_fields_absent``, ``domain_supported``, ``domain_match``,
   ``schema_version``, ``action_enum``, ``confidence_enum``,
   ``bounded_true``, ``policy_decisions_present``, ``for_date_iso``.
   Violations exit 2 with a named ``invariant=<id>`` stderr tag.

2. **``hai synthesize``** — refuses with ``SynthesisError`` when
   no proposals exist for the (for_date, user_id). Rolls back the
   entire transaction on any failure inside. Phase B firings are
   passed through a write-surface guard that rejects any attempt
   to mutate ``action`` or touch a domain not registered in
   ``PHASE_B_TARGETS``.

Recommendations reach ``recommendation_log`` exclusively through
``hai synthesize``. (The legacy recovery-only ``hai writeback`` direct
path was removed in v0.1.4 D2; use ``hai propose --domain recovery`` +
``hai synthesize``.)

Nothing persists until its determinism check passes. Callers can
pattern-match on the ``invariant`` id without parsing prose.

## What an agent should NOT do

- Modify JSONL or SQLite files directly. All state mutation goes
  through ``hai``.
- Claim more than the evidence supports. Rationale in a proposal
  must reference snapshot numbers (bands, deltas, ratios).
- Use diagnostic / clinical language. The safety skill + proposal /
  recommendation validators both reject it.
- Pre-bake Phase B adjustments (e.g. X9's protein-target bump).
  That is runtime territory; the synthesis skill must not write
  an ``action_detail`` reason_token that starts with ``x9_`` or
  equivalent.
- Call ``hai`` subcommands outside the ``allowed-tools`` scope of
  whichever skill is currently active.

## MCP

No MCP server ships in v1. A future wrapper exposing CLI
subcommands as MCP tools is tracked as Phase 7 scope.

## Where tools expect paths

- ``hai pull`` reads from
  ``src/health_agent_infra/data/garmin/export/daily_summary_export.csv``
  by default (CSV fixture). ``hai pull --live`` uses keyring-stored
  Garmin credentials.
- ``hai state snapshot`` / ``hai state reproject`` default to
  ``platformdirs`` user-data path; override via ``--db-path``.
- ``hai propose`` / ``hai review`` take ``--base-dir`` for JSONL
  audit logs; the default is ``~/.local/share/hai/``.
- ``hai setup-skills`` defaults to ``~/.claude/skills/``. Override
  via ``--dest``.
- ``hai config show`` prints the effective thresholds (defaults
  merged with user overrides at ``~/.config/hai/thresholds.toml``).

## Evaluating changes

After modifying a domain classifier, policy, or skill:

```bash
hai eval run --domain recovery
hai eval run --synthesis
```

The deterministic runtime layers are scored against frozen
scenarios under ``safety/evals/scenarios/``. Skill-layer narration
is NOT scored — see ``safety/evals/skill_harness_blocker.md`` for
the deferred follow-up.
