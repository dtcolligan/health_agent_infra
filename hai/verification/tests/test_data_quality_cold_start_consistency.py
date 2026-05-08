"""W51 maintainer refinement § 3.3 — cold-start consistency.

For any day where ``snapshot.<domain>.cold_start = True``, the
``data_quality_daily`` row for ``(user, date, domain, *)`` MUST report
``cold_start_window_state = "in_window"``. Catches silent drift between
``cold_start_policy_matrix.md`` and the W51 projection.

The test runs over every v1 domain. It seeds a brand-new DB (no
history), runs ``build_snapshot``, projects the data-quality rows,
and asserts the consistency invariant per domain.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from health_agent_infra.core.data_quality import (
    DOMAINS,
    project_data_quality_for_date,
    read_data_quality_rows,
)
from health_agent_infra.core.state import (
    build_snapshot,
    initialize_database,
    open_connection,
)


USER = "u_test"
AS_OF = date(2026, 4, 24)


def test_cold_start_window_state_matches_snapshot_cold_start_per_domain(
    tmp_path: Path,
):
    db = tmp_path / "state.db"
    initialize_database(db)

    conn = open_connection(db)
    try:
        snap = build_snapshot(
            conn,
            as_of_date=AS_OF,
            user_id=USER,
            now_local=datetime(2026, 4, 24, 23, 45),
        )
        project_data_quality_for_date(conn, snapshot=snap)
        rows = read_data_quality_rows(
            conn, user_id=USER, since_date=AS_OF, until_date=AS_OF,
        )
    finally:
        conn.close()

    rows_by_domain: dict[str, list[dict]] = {}
    for row in rows:
        rows_by_domain.setdefault(row["domain"], []).append(row)

    for domain in DOMAINS:
        cold = bool(snap[domain].get("cold_start", False))
        domain_rows = rows_by_domain.get(domain, [])
        assert domain_rows, (
            f"data_quality_daily missing rows for domain={domain}"
        )
        for row in domain_rows:
            if cold:
                assert row["cold_start_window_state"] == "in_window", (
                    f"cold-start mismatch for {domain} on {AS_OF}: "
                    f"snapshot.cold_start=True but "
                    f"data_quality_daily.cold_start_window_state="
                    f"{row['cold_start_window_state']!r}"
                )
            else:
                assert row["cold_start_window_state"] == "post_cold_start", (
                    f"cold-start mismatch for {domain} on {AS_OF}: "
                    f"snapshot.cold_start=False but "
                    f"data_quality_daily.cold_start_window_state="
                    f"{row['cold_start_window_state']!r}"
                )
