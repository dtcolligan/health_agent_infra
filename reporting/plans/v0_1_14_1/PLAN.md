**Cycle tier (D15): hardening.**

# v0.1.14.1 PLAN — Garmin-live unreliability surfaced as structured signal

**Cycle origin.** 2026-05-02 user session. The maintainer-driver of
`hai` (a Claude Code agent) called `hai pull --source garmin_live --live`
during a routine session-start data-freshness sweep, hitting the
documented HTTP 429 / Cloudflare 403 failure mode. Maintainer reaction
was unambiguous: this is a system trap, not a memory bug, and it
needs to be closed at the surface where the trap actually lives.

**Root-cause read.** `hai capabilities --json` is the agent contract.
Today it lists `garmin_live` as a peer of `intervals_icu` and `csv` in
the `--source` choice list, with the unreliability warning living only
in prose inside the flag's `help=` string. An agent that reads the
manifest programmatically — the principal trap surface — gets no
*structured* signal that one source is supported and the other is
best-effort. The fix lives in the manifest schema, paired with a
runtime breadcrumb for callers that bypass the manifest entirely.

**Single workstream.**

## §1 W-GARMIN-MANIFEST-SIGNAL

**Goal.** Close the agent-contract trap that allowed the 2026-05-02
incident, without breaking working `--source garmin_live` setups.

**Surfaces touched.**

1. **Capabilities walker** (`core/capabilities/walker.py`):
   - New helper `annotate_choice_metadata(action, metadata: dict[str, dict[str, Any]])`
     that attaches `_choice_metadata` to the argparse `Action` object.
   - `_flag_entry` reads the attached attribute (if present) and
     includes it in the flag entry as `choice_metadata: dict[str, dict]`.
   - Validates the metadata shape eagerly (each choice key must be a
     known choice value; each value must be a dict with at least
     `reliability`).
   - Allowed `reliability` values: `"reliable"` (omittable / default
     for choices without an entry), `"unreliable"`. Add to a new
     `RELIABILITY_VALUES` frozenset alongside the existing enums.
   - Schema additive only — backwards-compatible. Manifest
     `schema_version` stays `agent_cli_contract.v1`. Per AGENTS.md
     "Capabilities-manifest schema freeze scheduled for v0.2.3 *after*
     all v0.2.x schema additions land", this kind of pre-freeze
     additive metadata is in-window.

2. **CLI annotation sites** (`cli.py`):
   - `hai pull --source` (line 6997-area): after `add_argument`, call
     `annotate_choice_metadata` with `{"garmin_live": {"reliability":
     "unreliable", "reason": "rate-limited / Cloudflare-blocked",
     "prefer_instead": "intervals_icu"}}`.
   - `hai daily --source` (line 8632-area): identical annotation
     (single source-of-truth dict imported from a module-level
     constant to avoid drift).

3. **Runtime warning** (`cli.py:_resolve_pull_source`, line 555-area):
   - When the resolved source is `"garmin_live"` (regardless of how
     it was chosen — `--source`, `--live`, or any future path), emit
     a single stderr line:
     `WARN [hai pull]: Garmin live is rate-limited and frequently fails (HTTP 429 / Cloudflare 403). intervals.icu is the supported live source. See AGENTS.md "Settled Decisions".`
   - Single site keeps both pull invocations covered (`hai pull` and
     `hai daily` both call `_resolve_pull_source`). Verify by reading
     callers.
   - Stderr only; does not change exit code, does not gate the call.

4. **Docs**:
   - `AGENTS.md` "Settled Decisions" — append one sentence to the
     existing "Garmin Connect is not the default live source" bullet,
     pointing at the new structured signal so future agents know to
     check `choice_metadata.garmin_live.reliability`.
   - `CHANGELOG.md` — new v0.1.14.1 section, hardening-tier annotation,
     one-bullet description.
   - `reporting/docs/agent_cli_contract.md` regenerated via
     `hai capabilities --markdown`.

**Tests.**

| File | Assertion |
|---|---|
| `verification/tests/test_cli_parser_capabilities_regression.py` | Capabilities snapshot for `hai pull` and `hai daily` carries `choice_metadata.garmin_live.reliability == "unreliable"` on the `--source` flag. (Existing snapshot test extended; baseline regenerated as part of cycle.) |
| `verification/tests/test_capabilities_choice_metadata.py` (new) | (a) `annotate_choice_metadata` rejects unknown reliability values; (b) rejects metadata for choices not in the action's `choices`; (c) `_flag_entry` round-trips the metadata into the manifest. |
| `verification/tests/test_pull_garmin_live_warning.py` (new) | `_resolve_pull_source` emits the warning to stderr exactly once when source resolves to `"garmin_live"`; emits nothing when source is `"intervals_icu"` or `"csv"`. |

**Out-of-scope (explicitly).**

- No hard gate / opt-in flag. `hai pull --source garmin_live` continues
  to attempt the call after the warning.
- No removal of `garmin_live` as a `--source` choice.
- No retry-policy change. The garminconnect library failure mode is
  upstream.
- No new `reliability` value beyond `"reliable"` / `"unreliable"`.
  If we ever need `"deprecated"` or `"requires-confirm"` it lands in a
  later cycle as an additive enum extension.
- No `--source` choice metadata for sites other than `hai pull` and
  `hai daily`. Other commands' `--source` flags (e.g.
  `hai intake nutrition --source`) carry semantically different
  values (`user_authored`, `agent_proposed`) and are unrelated to
  pull-source reliability.

## §2 Quality gates

| Gate | Target |
|---|---|
| Pytest narrow | ≥ 2566 (v0.1.14 baseline + new tests) |
| Pytest broader (`-W error::Warning`) | clean |
| Mypy | 0 errors |
| Bandit -ll | 0 Med/High |
| Ruff | clean |
| `hai capabilities --json` | parses; `schema_version` unchanged; `choice_metadata` field present on `hai pull` + `hai daily` rows |
| `hai capabilities --markdown` | regenerated; diff is additive only |

## §3 Audit shape

Per D15 hardening tier:

- **Phase 0 (D11):** abbreviated — internal sweep only. No persona
  matrix. No external bug-hunt. The trap is already characterised by
  the 2026-05-02 incident transcript; no exploration needed.
- **D14 plan-audit:** target single-round `PLAN_COHERENT`. If round 1
  surfaces second-order issues, escalate to round 2 — but the surface
  is small enough (one workstream, ~50 LoC across walker + cli +
  tests) that one round should suffice.
- **Implementation review:** target single-round `SHIP` or
  `SHIP_WITH_NOTES` nit-only. Same scope-tightness rationale.
- **Ship-time freshness checklist** (AGENTS.md): apply.

## §4 Ship gate

Cycle ships when ALL of:

1. Test surface green at the gates above.
2. `hai capabilities --json` regenerated and committed; agents reading
   the manifest can pattern-match on `choice_metadata.garmin_live.reliability`.
3. Stderr warning fires in a manual probe (`uv run hai pull --source garmin_live`)
   even when the call subsequently fails.
4. CHANGELOG + AGENTS.md updated.
5. Codex IR returns `SHIP` or `SHIP_WITH_NOTES`.
6. Maintainer commits version bump and runs `twine upload`.

## §5 Carry-over

None. Single workstream, single goal, ship-or-revert.

## §6 Why now (vs queueing for v0.1.15)

The maintainer's own daily-driver agent loop tripped this trap in a
real session. Leaving the manifest signal absent through a full
v0.1.15 cycle (substantive, multi-WS, weeks-out) means every fresh
agent session continues to risk the same call. A scoped hardening
cycle ships in <24h with a tight audit shape. The change is purely
additive at the schema level, so there is no compatibility cost to
moving fast.
