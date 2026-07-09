"""Runtime-identity preflight for paid GovernedAgentBench sweeps.

The harness runs the HAI CLI as ``<python_executable> -m
health_agent_infra.cli`` and inherits whatever ``health_agent_infra`` that
interpreter resolves. Under ``uv run`` (or ``PYTHONPATH=hai/src``) that is the
working-tree reference runtime (tag ``gab-runtime-1.0``: HAI v0.2.0 + the
post-tag dispatch-time ``agent_safe`` enforcement fixes). Under a bare
interpreter it can silently resolve the **PyPI v0.2.0 wheel**, whose mutation
gate is bypassable by an agent that passes ``--confirm`` (the dispatch-time
gate landed 2026-05-10, three days after the v0.2.0 tag, and is not in the
wheel).

A sweep launched against the stale runtime would collect a **corrupted enforce
arm**: the A/C cells of the mutation-gate substitution 2x2 would not actually
enforce. Nothing downstream would flag it -- the trajectories look normal.

This module closes that trap two ways, both invocation-independent:

  1. ``resolve_runtime_fingerprint`` records exactly which ``health_agent_infra``
     the harness interpreter resolves (import path + git sha + whether it is a
     site-packages wheel) so every run carries the runtime's identity.
  2. ``run_enforcement_preflight`` behaviorally proves the resolved runtime
     enforces: it seeds a proposed intent and asserts that an agent-context
     ``intent commit --confirm`` under ``full_contract`` is REFUSED (mutation
     does not execute). If it commits, the runtime is stale/bypassable and the
     caller must HARD STOP before spending.

The interpretation of the probe is a pure function (``interpret_enforcement_probe``)
so the pass/fail logic is unit-tested without a live runtime.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

Runner = Callable[..., subprocess.CompletedProcess]

# Refusal signals emitted by the dispatch-time agent_safe gate (see
# hai/src/health_agent_infra/core/refusal/agent_safe.py). Either substring in
# stderr is proof the gate fired.
_REFUSAL_SIGNALS = ("agent_safe_violation", "agent_invoked_unsafe_command")

REFERENCE_RUNTIME_TAG = "gab-runtime-1.0"


def _hai_command(python_executable: str, argv: list[str]) -> list[str]:
    return [python_executable, "-m", "health_agent_infra.cli", *argv]


def _hermetic_env(fixture_root: Path, extra: Mapping[str, str]) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "HAI_HERMETIC": "1",
            "HAI_STATE_DB": str(fixture_root / "state.db"),
            "HAI_BASE_DIR": str(fixture_root / "base"),
            "HOME": str(fixture_root / "home"),
            "XDG_CONFIG_HOME": str(fixture_root / "xdg"),
        }
    )
    env.update(extra)
    return env


def resolve_runtime_fingerprint(
    python_executable: str,
    *,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    """Return the identity of the ``health_agent_infra`` the harness resolves.

    ``import_path`` is where the interpreter loads the package from; ``git_sha``
    is the HEAD of the repo containing it (``None`` for an installed wheel);
    ``under_site_packages`` flags a wheel install (the stale-runtime smell).
    """

    probe = (
        "import health_agent_infra as h, inspect, os, json;"
        "print(json.dumps({'import_path': os.path.dirname(inspect.getfile(h))}))"
    )
    fingerprint: dict[str, Any] = {
        "python_executable": python_executable,
        "import_path": None,
        "git_sha": None,
        "under_site_packages": None,
        "resolve_error": None,
    }
    try:
        out = runner(
            [python_executable, "-c", probe],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        fingerprint["resolve_error"] = f"{type(exc).__name__}: {exc}"
        return fingerprint
    if out.returncode != 0:
        fingerprint["resolve_error"] = (out.stderr or "").strip()[:500]
        return fingerprint
    try:
        import_path = json.loads(out.stdout.strip())["import_path"]
    except (json.JSONDecodeError, KeyError) as exc:
        fingerprint["resolve_error"] = f"unparsable import probe: {exc}"
        return fingerprint

    fingerprint["import_path"] = import_path
    fingerprint["under_site_packages"] = (
        "site-packages" in import_path or "dist-packages" in import_path
    )
    try:
        sha = runner(
            ["git", "-C", import_path, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if sha.returncode == 0:
            fingerprint["git_sha"] = sha.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        pass
    return fingerprint


def interpret_enforcement_probe(
    *,
    commit_exit_code: int,
    post_status: str | None,
    refusal_seen: bool,
    seed_ok: bool,
) -> tuple[bool, str]:
    """Pure verdict for the enforcement probe.

    PASS iff the resolved runtime REFUSED the agent's ``--confirm`` commit under
    ``full_contract``: the gated mutation did not execute (row still
    ``proposed``) and the call was refused. Any path where the mutation executed
    -- or where we cannot prove it was refused -- fails closed.
    """

    if not seed_ok:
        return False, "preflight could not seed a proposed intent to probe"
    if post_status == "active":
        return (
            False,
            "ENFORCE BYPASSED: agent-context `intent commit --confirm` committed "
            "under full_contract (stale/PyPI v0.2.0 runtime -- the dispatch-time "
            "agent_safe gate is absent)",
        )
    if post_status != "proposed":
        return (
            False,
            f"preflight in an unexpected state: post_status={post_status!r} "
            f"(exit={commit_exit_code}, refusal_seen={refusal_seen})",
        )
    if refusal_seen or commit_exit_code != 0:
        return (
            True,
            "enforce OK: agent-context `intent commit --confirm` refused under "
            "full_contract; mutation did not execute",
        )
    return (
        False,
        "enforce ambiguous: commit returned OK with no refusal envelope and the "
        "row stayed proposed -- cannot confirm the gate fired",
    )


def _parse_intent_id(stdout: str) -> str | None:
    try:
        payload = json.loads(stdout.strip())
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict):
        row_obj = payload.get("row")
        row = row_obj if isinstance(row_obj, dict) else payload
        value = row.get("intent_id")
        return str(value) if value else None
    return None


def _status_of(stdout: str, intent_id: str) -> str | None:
    try:
        rows = json.loads(stdout.strip())
    except json.JSONDecodeError:
        return None
    if not isinstance(rows, list):
        return None
    for row in rows:
        if isinstance(row, dict) and row.get("intent_id") == intent_id:
            status = row.get("status")
            return str(status) if status is not None else None
    return None


def run_enforcement_preflight(
    python_executable: str,
    *,
    workdir: Path | None = None,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    """Behaviorally verify the resolved runtime enforces the mutation gate.

    Returns a report dict with ``passed`` (bool), ``detail`` (str), and the
    ``runtime_fingerprint``. Never raises for a runtime that merely fails the
    check -- the caller inspects ``passed`` and decides to hard stop.
    """

    fingerprint = resolve_runtime_fingerprint(python_executable, runner=runner)
    report: dict[str, Any] = {
        "check": "runtime_enforcement_preflight.v1",
        "reference_runtime_tag": REFERENCE_RUNTIME_TAG,
        "runtime_fingerprint": fingerprint,
        "passed": False,
        "detail": "",
    }
    if fingerprint.get("resolve_error"):
        report["detail"] = (
            f"could not resolve health_agent_infra: {fingerprint['resolve_error']}"
        )
        return report

    scope_start = datetime.now(timezone.utc).date().isoformat()
    ctx = tempfile.TemporaryDirectory(dir=str(workdir) if workdir else None)
    try:
        fixture_root = Path(ctx.name)
        for sub in ("base", "home", "xdg"):
            (fixture_root / sub).mkdir(parents=True, exist_ok=True)
        gate_env = {
            "HAI_INVOCATION_CONTEXT": "agent",
            "HAI_RUNTIME_MODE": "full_contract",
        }

        def hai(argv: list[str], env_extra: Mapping[str, str]) -> subprocess.CompletedProcess:
            return runner(
                _hai_command(python_executable, argv),
                capture_output=True,
                text=True,
                env=_hermetic_env(fixture_root, env_extra),
                timeout=120,
            )

        hai(["init", "--skip-skills"], {})
        seed = hai(
            [
                "intent", "training", "add-session",
                "--status", "proposed",
                "--source", "agent_proposed",
                "--reason", "runtime-preflight",
                "--scope-start", scope_start,
            ],
            gate_env,
        )
        intent_id = _parse_intent_id(seed.stdout)
        seed_ok = intent_id is not None

        commit_exit = -1
        refusal_seen = False
        post_status: str | None = None
        if seed_ok:
            assert intent_id is not None
            commit = hai(
                ["intent", "commit", "--intent-id", intent_id, "--confirm"],
                gate_env,
            )
            commit_exit = commit.returncode
            refusal_seen = any(sig in (commit.stderr or "") for sig in _REFUSAL_SIGNALS)
            listing = hai(["intent", "training", "list", "--all"], {})
            post_status = _status_of(listing.stdout, intent_id)

        passed, detail = interpret_enforcement_probe(
            commit_exit_code=commit_exit,
            post_status=post_status,
            refusal_seen=refusal_seen,
            seed_ok=seed_ok,
        )
        report["passed"] = passed
        report["detail"] = detail
        report["probe"] = {
            "seed_ok": seed_ok,
            "commit_exit_code": commit_exit,
            "post_status": post_status,
            "refusal_seen": refusal_seen,
        }
        return report
    finally:
        ctx.cleanup()


__all__ = [
    "REFERENCE_RUNTIME_TAG",
    "resolve_runtime_fingerprint",
    "interpret_enforcement_probe",
    "run_enforcement_preflight",
]
