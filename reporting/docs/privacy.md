# Privacy and data sovereignty

Health Agent Infra is **local-first** by design. This document is an honest
account of what the runtime stores, where it lives, who can read it, and
how to inspect, export, or delete it.

The short version: every byte of your health data lives on your machine.
The runtime never phones home. The agent surfaces (Claude Code, Codex,
local LLM, MCP) read your data through the CLI; they do not have a
side-channel.

## What gets stored locally

| Thing | Where | When | Why |
|---|---|---|---|
| State DB | `$HAI_STATE_DB` (default: `~/.local/share/health_agent_infra/state.db`) | `hai state init` and every projection write | Queryable projection of accepted state, recommendations, plans, reviews |
| SQLite WAL/SHM siblings | alongside the DB file | While the DB is open in WAL mode | Required by SQLite for crash safety |
| Intake JSONL audit logs | `$base_dir/<group>.jsonl` (where `$base_dir` is the `--base-dir` you pass to `hai intake *` / `hai propose` / `hai review`) | Every successful intake / propose / review-record call | **Durable** audit boundary — DB is a derived projection that `hai state reproject` rebuilds from these |
| Pull JSONL outputs | wherever you redirect `hai pull > foo.json` | Only when you redirect | Raw upstream evidence for the day; the runtime doesn't write a default location |
| Wearable credentials | OS keychain (`hai_garmin`, `hai_intervals_icu`) | `hai auth garmin` / `hai auth intervals-icu` | Pull adapters use these to authenticate to upstream services |

Nothing else. There is no telemetry, no error reporter, no anonymous-usage
beacon. If you want to confirm: `lsof -p <hai pid>` and grep for
network connections.

## File permissions

On POSIX systems (macOS, Linux), every directory and file the runtime
creates is locked to **owner-only**:

- Directories: `0o700` (owner read/write/execute, no group, no other)
- Files: `0o600` (owner read/write, no group, no other)

This applies to:
- The state DB and its WAL/SHM/journal siblings
- Every `<group>.jsonl` audit log
- The base directories that hold them

The chmod is applied:
- On `hai state init` (DB path + parent)
- After every JSONL append
- Idempotently (re-running is a no-op)

If chmod fails (e.g. on a network mount), the runtime warns once on
stderr and continues. You'll see exactly what failed; the alternative
(refusing to write data) would be worse than the privacy gap.

On **Windows**, POSIX permissions don't apply; the runtime relies on
NTFS defaults. If you're running on Windows and concerned about other
users on the machine, store your data on an encrypted volume or apply
ACLs manually.

## Wearable credentials

`hai auth garmin` and `hai auth intervals-icu` store your credentials in
the OS keychain (macOS Keychain, GNOME Keyring, KWallet). They never
land in the state DB or any JSONL.

To remove credentials:

```bash
hai auth garmin --remove          # forget Garmin Connect creds
hai auth intervals-icu --remove   # forget intervals.icu creds
```

You can also delete them directly from your OS's keychain UI under the
service names `hai_garmin` and `hai_intervals_icu`.

## Inspecting your data

Everything is plain SQLite + plain JSONL. You can read the DB with any
SQLite browser:

```bash
sqlite3 ~/.local/share/health_agent_infra/state.db
sqlite> .tables
sqlite> SELECT * FROM recommendation_log ORDER BY for_date DESC LIMIT 5;
```

JSONL audit logs are line-delimited JSON; `cat` works fine.

Higher-level CLI surfaces:

- `hai today` — today's plan in plain prose
- `hai explain --for-date <iso> --user-id <u> --operator` — full audit
  bundle for a day (proposals, X-rule firings, recommendations, reviews)
- `hai state snapshot --as-of <iso> --user-id <u>` — current per-domain
  classified state
- `hai stats` — sync freshness, run history, recent commands

## Exporting

The state DB IS your export. Copy `state.db` to wherever you want a
backup. The JSONL audit logs are similarly portable — they're the
durable boundary; `hai state reproject --base-dir <wherever>` will
rebuild the DB from them.

There is no proprietary export format and no vendored cloud storage to
unwind.

## Deleting

To delete everything the runtime has stored:

```bash
# 1. Remove the state DB + siblings
rm -f ~/.local/share/health_agent_infra/state.db
rm -f ~/.local/share/health_agent_infra/state.db-wal
rm -f ~/.local/share/health_agent_infra/state.db-shm
rm -rf ~/.local/share/health_agent_infra

# 2. Remove your intake / writeback JSONLs (whatever --base-dir you used)
rm -rf ~/.health_agent

# 3. Remove wearable credentials
hai auth garmin --remove
hai auth intervals-icu --remove
```

That leaves no health data on your machine. The next `hai state init`
starts a fresh DB.

To delete only one day's data, query the DB directly:

```bash
sqlite3 ~/.local/share/health_agent_infra/state.db <<EOF
DELETE FROM recommendation_log WHERE for_date = '2026-04-23';
DELETE FROM proposal_log WHERE for_date = '2026-04-23';
DELETE FROM daily_plan WHERE daily_plan_id LIKE 'plan_2026-04-23_%';
EOF
```

The JSONL audit logs are append-only by design — to truly delete a day's
intake history, you'd need to remove the relevant lines manually and
then run `hai state reproject --base-dir <dir>` to rebuild the DB.
The system favours auditability over forgetability; this is a deliberate
tradeoff.

## Migrating to a new machine

```bash
# On the old machine:
cp ~/.local/share/health_agent_infra/state.db /path/to/portable/storage/
cp -r ~/.health_agent /path/to/portable/storage/

# On the new machine:
mkdir -p ~/.local/share/health_agent_infra
cp /path/to/portable/storage/state.db ~/.local/share/health_agent_infra/
cp -r /path/to/portable/storage/.health_agent ~/

# Re-authenticate to live sources (credentials don't migrate with files)
hai auth intervals-icu

# Verify
hai stats
hai doctor
```

## Packaged demo data

The `daily_summary_export.csv` fixture that ships with the package is
**synthetic**. See `src/health_agent_infra/data/garmin/export/README.md`
for provenance and the regression test in
`safety/tests/test_packaged_fixture_privacy.py` that scans for PII on
every commit.

## What we will not do

- **No telemetry.** The runtime does not send usage data anywhere.
- **No automatic cloud backup.** If you want backups, you run them
  yourself — your DB and JSONLs are plain files.
- **No third-party data sharing.** The runtime has no
  data-sharing surface to disable; it doesn't have one to begin with.
- **No agent-side persistence.** When the agent (Claude Code / Codex /
  etc.) reads your data, that's your agent's behaviour. The runtime
  doesn't know what the agent does with the JSON it returns; treat the
  agent surface as you would any local LLM tool — its memory,
  conversation logs, and integrations are your responsibility to audit.

## Reporting a privacy bug

If you find a path the runtime writes data outside the locations above,
or a fixture you suspect contains real PII, or any flow that could leak
data to a third party — open an issue. Privacy regressions get the same
treatment as safety regressions: they block release.
