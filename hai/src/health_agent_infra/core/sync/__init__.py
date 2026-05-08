"""Surgical operations on the sync_run_log table (F-PV14-02).

The runtime writes ``sync_run_log`` rows automatically (begin/complete/fail
lifecycle in ``core/state/store.py``); this package owns the
*operator-side* counterpart for surgical cleanup when contamination
sneaks in (e.g. fixture-pull leaks under F-PV14-01 conditions).

The contract is intentionally narrow: refuse selectors that resolve to
more than ``MAX_PURGE_ROWS`` rows, write a runtime_event_log audit row
for every committed deletion, leave dry-run mode read-only.
"""

from health_agent_infra.core.sync.purge import (
    MAX_PURGE_ROWS,
    PurgeRefusedError,
    PurgeResult,
    SyncRow,
    purge_sync_rows,
    resolve_purge_selectors,
)

__all__ = [
    "MAX_PURGE_ROWS",
    "PurgeRefusedError",
    "PurgeResult",
    "SyncRow",
    "purge_sync_rows",
    "resolve_purge_selectors",
]
