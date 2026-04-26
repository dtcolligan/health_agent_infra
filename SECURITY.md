# Security

## Scope Of Trust

Health Agent Infra is local-first in package architecture: it stores state on
the user's device, writes to local SQLite/JSONL, and has no telemetry path.
The runtime makes outbound calls only to configured pull adapters
(intervals.icu, Garmin Connect).

Host-agent caveat: if you drive the runtime through Claude Code, Codex, or
another hosted LLM, any context you provide to that host is governed by the
host provider's data policy. Health Agent Infra controls its own runtime and
storage behavior; it cannot control a model provider's handling of prompts.

The threat model assumes:

- A trusted local user with shell access to their own machine.
- An untrusted network.
- An untrusted LLM: state mutations go through `hai propose`,
  `hai synthesize`, `hai review record`, `hai intake`, and user-gated
  `hai intent/target commit` paths.
- An untrusted future maintainer: governance invariants are tested under
  `safety/tests/`, not left as convention.

Explicitly out of scope:

- Hosted deployment or exposing `hai` as a network service.
- Multi-user installations.
- Adversarial co-resident processes that can already read the user's files.
- Complete prompt-injection defense inside third-party model providers.

Privacy details are in [`reporting/docs/privacy.md`](reporting/docs/privacy.md).

## Reporting A Vulnerability

Please do not open a public GitHub issue for security reports.

Use GitHub private vulnerability reporting:
[`github.com/dtcolligan/health_agent_infra/security/advisories/new`](https://github.com/dtcolligan/health_agent_infra/security/advisories/new).

If GitHub's tooling is unavailable, email `dtcolligan@icloud.com` with
subject `[health-agent-infra security]` and a description of the issue.

Expected response time: best-effort within 7 days for triage. This is a
single-maintainer project, so that is an upper bound rather than an SLA.

## Disclosure Timeline

- **Day 0** - Report received.
- **Day 1-7** - Triage, severity assessment, and scope confirmation.
- **Day 7-30** - Fix developed, tested, and reviewed.
- **Day 30+** - Coordinated disclosure in a release; reporter credited with
  consent.

If a vulnerability is actively exploited, the timeline compresses. If it
requires significant research, it may expand.

## What Counts As A Vulnerability

In scope:

- A way to make the runtime produce clinical or diagnosis-shaped output.
- A way to mutate user-authored intent/targets without the explicit commit
  step required by W57.
- A way to bypass the three-state audit chain.
- A package path that exfiltrates state outside configured pull adapters.
- SQL/code injection through intake, config, or pull-source responses.
- A packaged skill that bypasses the CLI and mutates the state DB directly.

Out of scope:

- A user installing a malicious modified skill themselves.
- A dependency CVE that does not reach this project's attack surface.
- A vulnerability in Claude, Codex, or another model provider.

## Past Advisories

None as of v0.1.8.
