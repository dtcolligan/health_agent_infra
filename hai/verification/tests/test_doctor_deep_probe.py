"""W-X: `hai doctor --deep` probe surface (Codex F-DEMO-01 + Q-3).

Tests the Probe protocol split (LiveProbe vs. FixtureProbe), the
build_report wiring, and the no-network guarantee in demo mode.
"""

from __future__ import annotations

import socket
from typing import Any

import pytest

from health_agent_infra.core.doctor.checks import (
    check_auth_garmin,
    check_auth_intervals_icu,
)
from health_agent_infra.core.doctor.probe import (
    FixtureProbe,
    LiveProbe,
    ProbeResult,
    resolve_probe,
    run_deep_probes,
)


# ---------------------------------------------------------------------------
# Stub credential store for tests
# ---------------------------------------------------------------------------


class _StubCredStore:
    def __init__(
        self,
        *,
        intervals_available: bool = True,
        garmin_available: bool = True,
    ) -> None:
        self._intervals = intervals_available
        self._garmin = garmin_available

    def intervals_icu_status(self) -> dict[str, Any]:
        return {
            "credentials_available": self._intervals,
            "keyring": {"api_key_present": self._intervals},
        }

    def garmin_status(self) -> dict[str, Any]:
        return {
            "credentials_available": self._garmin,
            "keyring": {"password_present": self._garmin},
        }

    def load_intervals_icu(self) -> Any:
        return object() if self._intervals else None

    def load_garmin(self) -> Any:
        return object() if self._garmin else None


# ---------------------------------------------------------------------------
# ProbeResult / FixtureProbe
# ---------------------------------------------------------------------------


def test_fixture_probe_default_returns_ok():
    fp = FixtureProbe()
    creds = object()
    result = fp.probe_intervals_icu(creds)
    assert result.ok is True
    assert result.source == "fixture"
    assert result.http_status == 200


def test_fixture_probe_can_stub_403():
    """The 403 stub is the demo moment for diagnostic-trust."""
    fp = FixtureProbe(
        intervals_icu_response=ProbeResult(
            ok=False,
            source="fixture",
            http_status=403,
            error_message="HTTP 403 Forbidden (stubbed)",
        ),
    )
    result = fp.probe_intervals_icu(object())
    assert result.ok is False
    assert result.source == "fixture"
    assert result.http_status == 403


def test_resolve_probe_returns_fixture_in_demo_mode():
    probe = resolve_probe(demo_active=True)
    assert isinstance(probe, FixtureProbe)


def test_resolve_probe_returns_live_in_real_mode():
    probe = resolve_probe(demo_active=False)
    assert isinstance(probe, LiveProbe)


# ---------------------------------------------------------------------------
# run_deep_probes wiring
# ---------------------------------------------------------------------------


def test_run_deep_probes_skips_when_credentials_absent():
    """No credentials → no probes attempted (the credential check
    already returns warn for that surface)."""
    store = _StubCredStore(intervals_available=False, garmin_available=False)
    probe = FixtureProbe()
    out = run_deep_probes(probe=probe, credential_store=store)
    assert out == {}


def test_run_deep_probes_runs_when_credentials_present():
    store = _StubCredStore(intervals_available=True, garmin_available=True)
    probe = FixtureProbe()
    out = run_deep_probes(probe=probe, credential_store=store)
    assert "intervals_icu" in out
    assert "garmin" in out
    assert out["intervals_icu"].source == "fixture"


# ---------------------------------------------------------------------------
# check_auth_* probe integration
# ---------------------------------------------------------------------------


def test_check_auth_intervals_no_probe_keeps_creds_only_semantics():
    """No probe_result → backwards-compatible credentials-only row."""
    store = _StubCredStore(intervals_available=True)
    out = check_auth_intervals_icu(store)
    assert out["status"] == "ok"
    assert "probe" not in out


def test_check_auth_intervals_probe_ok_attaches_sub_dict():
    store = _StubCredStore(intervals_available=True)
    pr = ProbeResult(ok=True, source="fixture", http_status=200)
    out = check_auth_intervals_icu(store, probe_result=pr)
    assert out["status"] == "ok"
    assert out["probe"]["ok"] is True
    assert out["probe"]["source"] == "fixture"
    assert out["probe"]["http_status"] == 200


def test_check_auth_intervals_probe_fail_flips_row_to_fail():
    """Codex F-DEMO-01: a present credential that the API rejects
    must surface as a doctor failure, not a green row."""
    store = _StubCredStore(intervals_available=True)
    pr = ProbeResult(
        ok=False,
        source="fixture",
        http_status=403,
        error_message="HTTP 403 Forbidden (stubbed)",
    )
    out = check_auth_intervals_icu(store, probe_result=pr)
    assert out["status"] == "fail"
    assert out["reason"]
    assert "403" in out["reason"]
    assert out["probe"]["http_status"] == 403


def test_check_auth_garmin_probe_failure_surfaces_in_row():
    """Same shape on Garmin path — failed probe → fail row."""
    store = _StubCredStore(garmin_available=True)
    pr = ProbeResult(
        ok=False,
        source="live",
        error_message="Garmin live probe not implemented",
    )
    out = check_auth_garmin(store, probe_result=pr)
    assert out["status"] == "fail"
    assert "not implemented" in out["reason"]


# ---------------------------------------------------------------------------
# Demo-mode no-network guarantee (W-Va integration)
# ---------------------------------------------------------------------------


def test_demo_mode_deep_probe_does_not_open_a_socket(
    tmp_path, monkeypatch
):
    """W-Va + W-X integration test: when a demo marker is active and
    --deep is set, the probe must not hit the network.

    Implementation enforces this via the FixtureProbe class itself
    never opening a socket. The test asserts that contract by
    monkeypatching socket.socket to raise on any open attempt.
    """
    # Activate a fake demo marker.
    marker_path = tmp_path / "marker.json"
    monkeypatch.setenv("HAI_DEMO_MARKER_PATH", str(marker_path))

    from health_agent_infra.core.demo.session import open_session
    open_session(scratch_root=tmp_path / "scratch")

    # Monkeypatch socket so any network call raises.
    real_socket = socket.socket

    def _fail_socket(*args, **kwargs):
        raise AssertionError(
            "demo-mode --deep probe attempted to open a socket"
        )

    monkeypatch.setattr(socket, "socket", _fail_socket)

    # Run the demo-mode probe via the FixtureProbe path.
    store = _StubCredStore(intervals_available=True, garmin_available=False)
    probe = resolve_probe(demo_active=True)  # FixtureProbe
    result = probe.probe_intervals_icu(store.load_intervals_icu())

    assert result.source == "fixture"
    assert result.ok is True

    # Restore (defensive — pytest fixture would do this anyway).
    monkeypatch.setattr(socket, "socket", real_socket)


# ---------------------------------------------------------------------------
# Capabilities manifest reflects --deep
# ---------------------------------------------------------------------------


def test_capabilities_lists_deep_flag_on_doctor():
    from health_agent_infra.cli import build_parser
    from health_agent_infra.core.capabilities import build_manifest

    manifest = build_manifest(build_parser())
    doctor = next(
        c for c in manifest["commands"] if c["command"] == "hai doctor"
    )
    flag_names = {f["name"] for f in doctor["flags"]}
    assert "--deep" in flag_names
