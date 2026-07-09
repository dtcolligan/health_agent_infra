"""Runtime-identity preflight: the stale-runtime guard for paid sweeps.

The paid sweep must run against the reference runtime (tag gab-runtime-1.0:
HAI v0.2.0 + the post-tag dispatch-time agent_safe enforcement fixes), NOT the
shipped PyPI v0.2.0 wheel whose mutation gate is bypassable by an agent passing
--confirm. These tests pin the pass/fail logic with a fake runner so the
verdict is covered without a live runtime, plus the launcher wiring.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.runtime_preflight import (  # noqa: E402
    interpret_enforcement_probe,
    resolve_runtime_fingerprint,
    run_enforcement_preflight,
)
from governed_agent_bench.scripts import run_pilot_live  # noqa: E402


# --- pure verdict: the heart of the guard -------------------------------------

def test_enforce_refused_passes():
    ok, detail = interpret_enforcement_probe(
        commit_exit_code=1, post_status="proposed", refusal_seen=True, seed_ok=True
    )
    assert ok
    assert "enforce OK" in detail


def test_enforce_bypassed_fails():
    # The stale PyPI v0.2.0 signature: agent --confirm committed the mutation.
    ok, detail = interpret_enforcement_probe(
        commit_exit_code=0, post_status="active", refusal_seen=False, seed_ok=True
    )
    assert not ok
    assert "BYPASSED" in detail


def test_ambiguous_ok_without_refusal_fails_closed():
    # Row stayed proposed but the call returned OK with no refusal envelope:
    # we cannot prove the gate fired, so fail closed rather than spend.
    ok, detail = interpret_enforcement_probe(
        commit_exit_code=0, post_status="proposed", refusal_seen=False, seed_ok=True
    )
    assert not ok
    assert "ambiguous" in detail


def test_nonzero_exit_with_proposed_passes():
    ok, _ = interpret_enforcement_probe(
        commit_exit_code=1, post_status="proposed", refusal_seen=False, seed_ok=True
    )
    assert ok


def test_seed_failure_fails_closed():
    ok, detail = interpret_enforcement_probe(
        commit_exit_code=-1, post_status=None, refusal_seen=False, seed_ok=False
    )
    assert not ok
    assert "seed" in detail


def test_unexpected_status_fails_closed():
    ok, detail = interpret_enforcement_probe(
        commit_exit_code=0, post_status="archived", refusal_seen=False, seed_ok=True
    )
    assert not ok


# --- fingerprint resolution ---------------------------------------------------

def _completed(stdout="", stderr="", returncode=0):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def test_fingerprint_flags_site_packages_wheel():
    def runner(cmd, **kwargs):
        if "-c" in cmd:
            path = "/opt/py/lib/python3.14/site-packages/health_agent_infra"
            return _completed(stdout=json.dumps({"import_path": path}))
        return _completed(returncode=128, stderr="not a git repo")  # git rev-parse

    fp = resolve_runtime_fingerprint("python3", runner=runner)
    assert fp["under_site_packages"] is True
    assert fp["git_sha"] is None
    assert fp["resolve_error"] is None


def test_fingerprint_resolve_error_is_captured():
    def runner(cmd, **kwargs):
        return _completed(returncode=1, stderr="ModuleNotFoundError: health_agent_infra")

    fp = resolve_runtime_fingerprint("python3", runner=runner)
    assert fp["import_path"] is None
    assert "ModuleNotFoundError" in fp["resolve_error"]


# --- full preflight with a scripted runner (no live runtime) -------------------

class _FakeRuntime:
    """Scripts the sequence of hai subprocess calls the preflight issues."""

    def __init__(self, *, bypasses: bool):
        self.bypasses = bypasses
        self.intent_id = "intent_deadbeef0001"

    def __call__(self, cmd, **kwargs):
        if "-c" in cmd:  # fingerprint import probe
            return _completed(stdout=json.dumps({"import_path": "/repo/hai/src/health_agent_infra"}))
        if cmd[:2] == ["git", "-C"]:
            return _completed(stdout="0d08b62\n")
        argv = cmd[cmd.index("health_agent_infra.cli") + 1:]
        if argv[:1] == ["init"]:
            return _completed()
        if argv[:2] == ["intent", "training"] and "add-session" in argv:
            return _completed(stdout=json.dumps({"intent_id": self.intent_id, "status": "proposed"}))
        if argv[:2] == ["intent", "commit"]:
            if self.bypasses:
                return _completed(returncode=0)  # wheel: committed
            return _completed(returncode=1, stderr='{"refusal_kind": "agent_safe_violation"}')
        if argv[:2] == ["intent", "training"] and "list" in argv:
            status = "active" if self.bypasses else "proposed"
            return _completed(stdout=json.dumps([{"intent_id": self.intent_id, "status": status}]))
        return _completed()


def test_preflight_passes_on_enforcing_runtime(tmp_path):
    report = run_enforcement_preflight(
        "python3", workdir=tmp_path, runner=_FakeRuntime(bypasses=False)
    )
    assert report["passed"] is True
    assert report["probe"]["post_status"] == "proposed"
    assert report["runtime_fingerprint"]["git_sha"] == "0d08b62"


def test_preflight_fails_on_bypassable_runtime(tmp_path):
    report = run_enforcement_preflight(
        "python3", workdir=tmp_path, runner=_FakeRuntime(bypasses=True)
    )
    assert report["passed"] is False
    assert "BYPASSED" in report["detail"]
    assert report["probe"]["post_status"] == "active"


# --- launcher wiring ----------------------------------------------------------

def test_launcher_exposes_stale_runtime_exit_code():
    assert run_pilot_live.EXIT_STALE_RUNTIME == 7
    # distinct from every other exit code
    codes = [
        run_pilot_live.EXIT_OK,
        run_pilot_live.EXIT_RUN_NOT_COMPLETED,
        run_pilot_live.EXIT_MISSING_API_KEY,
        run_pilot_live.EXIT_RUN_DIR_EXISTS,
        run_pilot_live.EXIT_GIT_HEAD_FAILED,
        run_pilot_live.EXIT_CANARY_GATE_FAILED,
        run_pilot_live.EXIT_BAD_SELECTION,
        run_pilot_live.EXIT_STALE_RUNTIME,
    ]
    assert len(set(codes)) == len(codes)


def test_launcher_hard_stops_on_failed_preflight(monkeypatch, tmp_path):
    """A failed preflight returns EXIT_STALE_RUNTIME and never reaches run_ladder."""

    monkeypatch.setenv(run_pilot_live.TOGETHER_API_KEY_ENV, "dummy-key")
    monkeypatch.setattr(run_pilot_live, "DEFAULT_RUNS_ROOT", tmp_path)
    monkeypatch.setattr(run_pilot_live, "tracked_changes", lambda: [])
    monkeypatch.setattr(
        run_pilot_live,
        "run_enforcement_preflight",
        lambda _py: {
            "passed": False,
            "detail": "ENFORCE BYPASSED (test)",
            "reference_runtime_tag": "gab-runtime-1.0",
            "runtime_fingerprint": {"import_path": "x", "git_sha": None, "under_site_packages": True},
        },
    )

    def _boom(*args, **kwargs):  # run_ladder must not be reached
        raise AssertionError("run_ladder reached despite failed preflight")

    monkeypatch.setattr(run_pilot_live, "run_ladder", _boom)

    rc = run_pilot_live.main(["--ladder"])
    assert rc == run_pilot_live.EXIT_STALE_RUNTIME
    assert (tmp_path / "runtime_preflight_latest.json").exists()
