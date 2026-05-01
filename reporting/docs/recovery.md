# Recovery — backup, restore, and disaster scenarios

**v0.1.14 W-BACKUP.** This is the authoritative recovery contract
for `health-agent-infra`. Local-first means **you** are responsible
for backups; HAI ships the canonical paths.

## Quick reference

| Need | Command |
|---|---|
| Save a backup | `hai backup --dest ~/hai-backups/$(date +%F).tar.gz` |
| Restore a backup | `hai restore <bundle.tar.gz>` |
| Export a unified JSONL stream | `hai export --dest /path/out.jsonl` |
| Stream JSONL to stdout | `hai export` |

## What `hai backup` writes

A versioned gzipped tarball containing:

- `manifest.json` — bundle metadata (HAI version, schema head,
  timestamp, list of included JSONL logs).
- `state.db` — the local SQLite state DB.
- `jsonl/<basename>.jsonl` — every JSONL audit log under
  `--base-dir` (default `~/.health_agent`).

The bundle is self-contained — no telemetry, no external
references. You can move it between machines, store it in cloud
backup, or check it into a private git LFS repo.

## What `hai restore` does

`hai restore <bundle.tar.gz>` reads the manifest, verifies the
bundle's `schema_version` matches the installed wheel's head, and
overwrites:

- The state DB at `$HAI_STATE_DB` / platform default.
- Every JSONL log at `$HAI_BASE_DIR` / `~/.health_agent`.

**Restore refuses on schema mismatch.** This is the load-bearing
safety check. If you backed up under wheel `v0.1.13` (schema 22)
and try to restore against an installed `v0.1.14` (schema 23):

```
hai restore: schema mismatch — bundle schema_version=22 does not
match installed wheel head=23. Restore refuses by default. Either
install a wheel matching the bundle's schema (was hai_version='0.1.13')
or restore against an empty DB and run `hai state migrate` to
bring the bundle's data forward.
```

The recovery procedure:

1. Install the matching wheel: `pipx install 'health-agent-infra==0.1.13' --force`.
2. Restore the bundle: `hai restore <bundle.tar.gz>`.
3. Upgrade: `pipx install 'health-agent-infra' --force`.
4. Run forward migrations: `hai state migrate`.

This avoids accidentally running newer-wheel migrations against a
state DB that the wheel has never seen.

## Common recovery scenarios

### Scenario 1 — corrupted state DB

Symptoms: `hai today`, `hai explain`, or `hai daily` fail with
SQLite error messages (e.g., `database disk image is malformed`).

Recovery:

1. Move the corrupted DB aside:
   `mv $HOME/.local/share/health_agent_infra/state.db{,.broken}`
2. Restore the most recent good bundle:
   `hai restore ~/hai-backups/<recent>.tar.gz`
3. Verify: `hai today`, `hai doctor` (should report green).
4. Re-run any subsequent days the bundle didn't include via
   `hai daily --as-of <YYYY-MM-DD>` per missing day.

### Scenario 2 — keyring loss (Garmin / intervals.icu credentials)

Symptoms: `hai pull` fails with auth errors.

Recovery: credentials are NOT in the backup (intentionally — they
live in the OS keyring and are user-specific). Re-add them:

- intervals.icu: `hai auth intervals-icu --interactive`
- Garmin: `hai auth garmin --interactive`

The bundle's evidence rows remain valid — only fresh pulls need
the credentials.

### Scenario 3 — intervals.icu credential rotation

Same as keyring loss — re-run `hai auth intervals-icu --interactive`.

### Scenario 4 — schema mismatch (older bundle, newer wheel)

This is the documented refusal path above. Step-by-step:

```bash
# Identify the bundle's schema:
python3 -c "import tarfile, json; t = tarfile.open('bundle.tar.gz', 'r:gz'); m = t.extractfile(t.getmember('manifest.json')); print(json.load(m))"

# Install the matching wheel:
pipx install 'health-agent-infra==<bundle hai_version>' --force

# Restore against an empty target:
HAI_STATE_DB=/tmp/restored.db hai restore bundle.tar.gz \
    --db-path /tmp/restored.db \
    --base-dir /tmp/restored-audit

# Upgrade the wheel:
pipx install 'health-agent-infra' --force

# Bring the restored DB forward:
HAI_STATE_DB=/tmp/restored.db hai state migrate \
    --db-path /tmp/restored.db

# Move into place if happy:
mv /tmp/restored.db $HOME/.local/share/health_agent_infra/state.db
mv /tmp/restored-audit ~/.health_agent  # if the existing audit dir is also stale
```

### Scenario 5 — accidental wipe of state DB

Same as Scenario 1 — restore from the most recent bundle.

If no backup exists: most state can be reconstructed from the
JSONL audit logs via `hai state reproject` (see `hai state reproject
--help`). The recommendation/review/gym/nutrition projection tables
are deterministic functions of the JSONL inputs. Computed tables
(`planned_recommendation`, `daily_plan`, `x_rule_firing`) require
re-running `hai synthesize` per affected day.

## What's NOT in the backup

- **Credentials** (Garmin / intervals.icu OS keyring entries) —
  user-specific; re-add via `hai auth`.
- **Local skill files** at `~/.claude/skills/health_agent_infra/` —
  these are installed via `hai setup-skills`, not user state.
- **Hosted-LLM-side data** (Claude transcripts, agent memory
  outside HAI's user_memory table) — HAI doesn't see this. Per
  README: "If you drive the runtime with a hosted LLM agent, any
  context you send to that host is governed by that host's data
  policy".

## Backup discipline

There is no automated backup schedule shipped with HAI. Local-first
is your responsibility. Sensible options:

- Manual: `hai backup --dest ~/hai-backups/$(date +%F).tar.gz`
  before a risky operation (migration, schema rebuild,
  experimental skill change).
- Cron: a daily `hai backup` to a rotated path (7-day rotation is
  fine for most users; the bundle is small — typically <100 MB).
- Cloud: pipe `hai export` into an encrypted cloud-backup tool.
  The export stream is plain JSONL; encrypt at rest if storing
  cloud-side.

## Verifying a bundle without restoring

```bash
python3 -c "
import tarfile, json
t = tarfile.open('bundle.tar.gz', 'r:gz')
m = t.extractfile(t.getmember('manifest.json'))
print(json.dumps(json.load(m), indent=2))
"
```

## Forward compatibility

The bundle layout version is `1` (v0.1.14 W-BACKUP). Future cycles
that change the bundle layout itself (not the SQLite schema) will
bump `bundle_format_version` and document a migration path. Schema
changes are handled by the existing `hai state migrate`
infrastructure; the bundle just carries the schema version stamp
so restore can verify compatibility.

## See also

- `hai backup --help` — current flag reference.
- `hai restore --help` — current flag reference.
- `hai export --help` — current flag reference.
- `reporting/docs/source_row_provenance.md` — v0.1.14 W-PROV-1
  source-row locator type (a separate audit-chain hardening, not
  recovery-related).
