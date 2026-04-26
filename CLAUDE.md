@AGENTS.md

## Claude Code Specifics

- This is the maintainer's daily-driver loop. Skills under
  `src/health_agent_infra/skills/` are also user-installed at
  `~/.claude/skills/` via `hai setup-skills`. Edit the packaged copy, not the
  installed copy.
- Path-scoped rules live in `.claude/rules/` when present.
- For mutating CLI calls during a session, prefer plan mode first.
- The `intent-router` skill is the authoritative natural-language-to-`hai`
  mapper; invoke it rather than composing mutation commands from intuition.
