# CLI exit codes

The ``hai`` CLI exits with a small set of codes that classify failures
by cause. An agent or shell caller can react programmatically without
parsing stderr: retry on ``TRANSIENT``, surface ``NOT_FOUND`` to the
user, stop and reconsider on ``USER_INPUT`` or ``INTERNAL``.

The constants live in
``src/health_agent_infra/core/exit_codes.py``. Import them rather than
writing literal integers.

## Codes

| Code | Constant       | Meaning |
|-----:|----------------|---------|
| 0    | ``OK``         | Command completed as intended. |
| 1    | ``USER_INPUT`` | The invocation was wrong: missing / conflicting flags, unreadable user-supplied JSON, missing credentials the caller was expected to provide, or a state precondition the caller controls (e.g. ``hai state init`` hasn't been run yet). |
| 2    | ``TRANSIENT``  | An external dependency failed in a way a retry might fix: vendor 5xx, rate limit, network blip. |
| 3    | ``NOT_FOUND``  | The target identifier is well-formed but the runtime has no record of it. Today the only producer is an unknown ``daily_plan_id`` passed to ``hai explain``. |
| 4    | ``INTERNAL``   | A runtime invariant tripped that should not be reachable from normal inputs. Indicates a bug, not caller error. |

## Why TRANSIENT stays at 2

Before the taxonomy, every non-zero exit was ``2``. Callers that
treated any non-zero code as "retry" worked fine for vendor blips and
continued to work when we introduced distinct codes — because we kept
``TRANSIENT`` at ``2`` and pushed user-input errors *down* to ``1``.
Shifting ``TRANSIENT`` to a new code would have silently broken those
retry loops without a clean signal to the caller. ``1`` was free, so
``USER_INPUT`` got it.

## Scope

M1 migrated the five CLI handlers with the highest operational value
(the pull → synthesize → explain path, plus credential setup). Every
other handler still returns the legacy ``0 / 2``; those will migrate
in follow-up PRs.

| Handler | Migrated in M1? | Codes produced |
|---|:---:|---|
| ``hai pull``           | ✅ | ``OK``, ``USER_INPUT`` (no creds), ``TRANSIENT`` (adapter 5xx) |
| ``hai auth garmin``    | ✅ | ``OK``, ``USER_INPUT`` |
| ``hai auth status``    | ✅ | ``OK`` |
| ``hai synthesize``     | ✅ | ``OK``, ``USER_INPUT``, ``INTERNAL`` (write-surface violation) |
| ``hai explain``        | ✅ | ``OK``, ``USER_INPUT``, ``NOT_FOUND`` |
| ``hai daily``          | ❌ | legacy ``0 / 2`` |
| ``hai state *``        | ❌ | legacy ``0 / 2`` |
| ``hai intake *``       | ❌ | legacy ``0 / 2`` |
| ``hai review *``       | ❌ | legacy ``0 / 2`` |
| ``hai memory *``       | ❌ | legacy ``0 / 2`` |
| ``hai propose``        | ❌ | legacy ``0 / 2`` |
| ``hai writeback``      | ❌ | legacy ``0 / 2`` |
| ``hai clean``          | ❌ | legacy ``0 / 2`` |
| ``hai doctor``         | ❌ | legacy ``0 / 2`` |

## Usage — Python

```python
from health_agent_infra.core import exit_codes

# Inside a subcommand:
if not db_path.exists():
    print("run `hai state init` first", file=sys.stderr)
    return exit_codes.USER_INPUT
```

## Usage — shell

```bash
hai pull --live --date "$(date -I)"
case $? in
  0) echo "ok" ;;
  1) echo "invocation error — fix flags and retry" ;;
  2) echo "transient — back off and retry"; sleep 30; exec "$0" "$@" ;;
  3) echo "target not found" ;;
  4) echo "internal error — file a bug" ;;
esac
```

## Stability contract

- Numeric values of ``OK`` / ``USER_INPUT`` / ``TRANSIENT`` / ``NOT_FOUND`` /
  ``INTERNAL`` are frozen. Changing one is a breaking change.
- New codes may be added to the taxonomy; they will take the next free
  integer.
- A migrated handler may be narrowed (fewer codes produced) but never
  broadened silently — if a handler starts producing a new code, this
  doc's scope table is updated in the same PR.
- A legacy handler (``❌`` above) makes no promise beyond "``0`` on
  success, non-zero otherwise" until it migrates.
