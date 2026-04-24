"""E2E test harness — full-journey scenarios against a fresh state DB.

E2E tests exercise multi-command sequences end-to-end, asserting that the
contract at each seam holds as the user moves through a real session.
They are the category that would have caught the 15 bugs surfaced on
2026-04-23 — see `reporting/plans/v0_1_4/README.md` for context.

Each E2E test gets an isolated (fresh DB + fresh base_dir) environment
via the `e2e_env` fixture. Tests compose by invoking `hai <subcommand>`
via ``cli.main`` in-process (no subprocess — installs can lag behind
the source under test; in-process also makes tracebacks legible and
tests run faster). Captures stdout/stderr and the returned exit code.

Assertions available:

  - exit codes per the stable taxonomy in ``core.exit_codes``
  - JSON emitted on stdout (each hai subcommand has a stable shape)
  - rows landed in the expected state tables (``E2EEnv.sql``)
  - output surfaces (``hai today``, ``hai explain --operator``) rendering
    coherently with the committed plan

Workstream E owns this harness; Workstream A / B / D each add scenarios
as their fixes land.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.state import initialize_database, open_connection


@dataclass
class E2EEnv:
    """Bundle of isolated paths + handles for a single E2E scenario."""

    db_path: Path
    base_dir: Path
    tmp_root: Path

    def sql(self, query: str, *params: Any) -> list[tuple]:
        """Run a read-only SQL query against the isolated DB. Tests assert
        on the return shape."""
        with open_connection(self.db_path) as conn:
            return list(conn.execute(query, params).fetchall())

    def sql_one(self, query: str, *params: Any) -> Optional[tuple]:
        rows = self.sql(query, *params)
        return rows[0] if rows else None

    def run_hai(
        self,
        *args: str,
        expect_exit: int = 0,
    ) -> dict[str, Any]:
        """Invoke ``hai <args>`` in-process via ``cli.main``.

        Captures stdout/stderr and asserts the returned exit code
        matches ``expect_exit``. The isolated DB path is always
        injected as ``--db-path`` unless the caller passed one already
        (keeps test bodies terse).
        """
        argv = list(args)
        if "--db-path" not in argv:
            # Only inject if the subcommand actually accepts it. Every
            # mutating hai subcommand does; read-only ones like
            # capabilities don't. Brute-force try, then retry without
            # on argparse rejection, to keep the harness dumb-simple.
            argv_with_db = [*argv, "--db-path", str(self.db_path)]
        else:
            argv_with_db = argv

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        try:
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                exit_code = cli_main(argv_with_db)
        except SystemExit as exc:
            # argparse raises SystemExit on --help / invalid args;
            # surface that as exit code.
            exit_code = int(exc.code) if isinstance(exc.code, int) else 2

        # If argparse rejected --db-path (subcommand doesn't accept it),
        # retry without the injected flag.
        stderr_text = stderr_buf.getvalue()
        if (
            exit_code == 2
            and "unrecognized arguments: --db-path" in stderr_text
            and argv_with_db is not argv
        ):
            stdout_buf = io.StringIO()
            stderr_buf = io.StringIO()
            try:
                with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                    exit_code = cli_main(argv)
            except SystemExit as exc:
                exit_code = int(exc.code) if isinstance(exc.code, int) else 2

        stdout = stdout_buf.getvalue()
        stderr = stderr_buf.getvalue()

        assert exit_code == expect_exit, (
            f"hai {' '.join(args)} exited {exit_code}, expected {expect_exit}."
            f"\nstdout: {stdout[:500]}\nstderr: {stderr[:500]}"
        )

        stdout_json: Optional[Any] = None
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
def e2e_env(tmp_path: Path) -> Iterator[E2EEnv]:
    """Fresh state DB + base_dir per test.

    The DB is initialised with the current schema head; no fixtures are
    pre-loaded. Tests that need seeded state must populate it explicitly
    via intake commands or direct SQL, to keep the test narrative
    legible.
    """
    db_path = tmp_path / "state.db"
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    initialize_database(db_path)
    yield E2EEnv(db_path=db_path, base_dir=base_dir, tmp_root=tmp_path)
