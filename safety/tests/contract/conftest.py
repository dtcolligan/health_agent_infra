"""Contract test harness — structural invariants on persisted state.

A *contract* test asserts a cross-table invariant that must hold
regardless of which sequence of CLI calls produced the DB:

- Every ``proposal_ids_json`` entry on a ``daily_plan`` resolves in
  ``proposal_log``.
- Every ``recommendation_log.daily_plan_id`` resolves in
  ``daily_plan``.
- Every ``review_outcome.recommendation_id`` points to either a
  canonical-leaf recommendation OR a re-linked one that carries
  ``re_link_note`` (D1).
- Every ``proposal_log`` chain resolves to exactly one canonical
  leaf per ``(for_date, user_id, domain)``.

These are not per-command unit tests; they're end-of-day audit
checks. A fixture seeds a realistic multi-day journey via the CLI,
and every assertion runs against the final DB state. If a future
refactor breaks one of these invariants, the contract test fires
regardless of which handler drifted.

The fixture lives in this conftest.py so individual test modules
stay small + focused on one invariant.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterator, Optional

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.state import initialize_database, open_connection


@dataclass
class ContractEnv:
    """Isolated DB + base_dir for a contract scenario.

    Tests invoke ``hai <cmd>`` via ``run_hai`` to seed state exactly
    as the CLI would; the DB is then available for SQL assertions via
    ``sql`` / ``sql_one``. The pattern mirrors the e2e harness so
    audit-chain invariants are checked against CLI-produced state,
    not hand-built fixtures that might diverge from reality.
    """

    db_path: Path
    base_dir: Path
    tmp_root: Path

    def sql(self, query: str, *params: Any) -> list[tuple]:
        with open_connection(self.db_path) as conn:
            return list(conn.execute(query, params).fetchall())

    def sql_one(self, query: str, *params: Any) -> Optional[tuple]:
        rows = self.sql(query, *params)
        return rows[0] if rows else None

    def run_hai(self, *args: str, expect_exit: int = 0) -> dict[str, Any]:
        argv = list(args)
        if "--db-path" not in argv:
            argv = [*argv, "--db-path", str(self.db_path)]

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        try:
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                exit_code = cli_main(argv)
        except SystemExit as exc:
            exit_code = int(exc.code) if isinstance(exc.code, int) else 2

        # Retry without --db-path for subcommands that don't accept it.
        stderr_text = stderr_buf.getvalue()
        if exit_code == 2 and "unrecognized arguments: --db-path" in stderr_text:
            stdout_buf = io.StringIO()
            stderr_buf = io.StringIO()
            try:
                with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                    exit_code = cli_main(list(args))
            except SystemExit as exc:
                exit_code = int(exc.code) if isinstance(exc.code, int) else 2

        stdout = stdout_buf.getvalue()
        stderr = stderr_buf.getvalue()
        assert exit_code == expect_exit, (
            f"hai {' '.join(args)} exited {exit_code}, expected {expect_exit}."
            f"\nstdout: {stdout[:500]}\nstderr: {stderr[:500]}"
        )

        stdout_json = None
        if stdout.strip():
            try:
                stdout_json = json.loads(stdout)
            except json.JSONDecodeError:
                stdout_json = None
        return {
            "exit": exit_code,
            "stdout": stdout,
            "stdout_json": stdout_json,
            "stderr": stderr,
        }


@pytest.fixture
def contract_env(tmp_path: Path) -> Iterator[ContractEnv]:
    """Fresh DB + base_dir per contract test."""

    db_path = tmp_path / "state.db"
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    initialize_database(db_path)
    yield ContractEnv(db_path=db_path, base_dir=base_dir, tmp_root=tmp_path)


# ---------------------------------------------------------------------------
# Shared seeder helpers — used by multiple contract tests so the setup
# mirrors the realistic CLI sequence rather than hand-built SQL.
# ---------------------------------------------------------------------------


def seed_six_domain_daily(env: ContractEnv, *, as_of: date, user_id: str) -> dict:
    """Run `hai propose` for all six domains + `hai synthesize`.

    Returns the synthesis report payload (the dict `cmd_synthesize`
    emits on stdout). Contract tests that want audit-chain state
    should call this, then assert against the resulting DB rows.
    """

    domain_defaults = {
        "recovery":  "proceed_with_planned_session",
        "running":   "proceed_with_planned_run",
        "sleep":     "maintain_schedule",
        "strength":  "proceed_with_planned_session",
        "stress":    "maintain_routine",
        "nutrition": "maintain_targets",
    }
    schemas = {
        "recovery":  "recovery_proposal.v1",
        "running":   "running_proposal.v1",
        "sleep":     "sleep_proposal.v1",
        "strength":  "strength_proposal.v1",
        "stress":    "stress_proposal.v1",
        "nutrition": "nutrition_proposal.v1",
    }
    for domain, action in domain_defaults.items():
        payload = {
            "schema_version": schemas[domain],
            "proposal_id": f"prop_{as_of}_{user_id}_{domain}_01",
            "user_id": user_id,
            "for_date": str(as_of),
            "domain": domain,
            "action": action,
            "action_detail": None,
            "rationale": [f"{domain}_baseline"],
            "confidence": "moderate",
            "uncertainty": [],
            "policy_decisions": [
                {"rule_id": "r_baseline", "decision": "allow", "note": "ok"},
            ],
            "bounded": True,
        }
        path = env.tmp_root / f"prop_{domain}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        env.run_hai(
            "propose", "--domain", domain,
            "--proposal-json", str(path),
            "--base-dir", str(env.base_dir),
        )
    result = env.run_hai(
        "synthesize",
        "--as-of", str(as_of),
        "--user-id", user_id,
    )
    return result["stdout_json"] or {}
