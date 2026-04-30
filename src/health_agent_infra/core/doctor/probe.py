"""W-X: Probe protocol for `hai doctor --deep` (Codex F-DEMO-01).

`hai doctor` reports `auth_intervals_icu: ok` whenever credentials
are present in the keyring, but says nothing about whether the
remote API still accepts them. The 2026-04-28 demo run exposed the
gap: the credential surface was green while a live wellness fetch
returned HTTP 403.

`hai doctor --deep` adds a probe call. In real mode the probe hits
the remote API (LiveProbe). In demo mode (a valid marker is active)
the probe routes to a fixture stub (FixtureProbe) — preserves the
demo moment of "doctor caught broken auth" without any network
call (per maintainer answer Q-3 on plan-audit round 2).

Contract:

- Probe.probe_intervals_icu(credentials) -> ProbeResult
- Probe.probe_garmin(credentials)        -> ProbeResult

ProbeResult fields: ok (bool), source ("live" | "fixture"),
http_status (Optional[int]), error_message (Optional[str]).

The doctor check helpers return a dict that includes a `probe`
sub-dict when `--deep` is set, with shape:
    {"ok": bool, "source": "live"|"fixture", "http_status": int|None,
     "error_message": str|None}
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol


@dataclass(frozen=True)
class ProbeResult:
    """Outcome of a single deep-probe call against a credential surface.

    ``source`` is "live" when the probe actually hit the network and
    "fixture" when a stubbed response was returned (demo mode).
    Tests assert on this field to enforce the no-network invariant
    in demo mode.

    ``error_body`` and ``outcome_class`` were added at v0.1.13 W-AE
    so the doctor row can classify a failure into one of five
    actionable buckets (OK / CAUSE_1_CLOUDFLARE_UA / CAUSE_2_CREDS /
    NETWORK / OTHER) without parsing prose. ``outcome_class`` is None
    on unclassified results (e.g. legacy fixtures).
    """

    ok: bool
    source: str  # "live" | "fixture"
    http_status: Optional[int] = None
    error_message: Optional[str] = None
    error_body: Optional[str] = None
    outcome_class: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "source": self.source,
            "http_status": self.http_status,
            "error_message": self.error_message,
            "error_body": self.error_body,
            "outcome_class": self.outcome_class,
        }


# ---------------------------------------------------------------------------
# Outcome classification (W-AE, v0.1.13)
# ---------------------------------------------------------------------------

# The five outcome classes — one success + four failure classes.
# Names referenced by `reporting/docs/intervals_icu_403_triage.md`;
# changing a token here is a breaking change for that doc.
OUTCOME_CLASSES: frozenset[str] = frozenset({
    "OK",
    "CAUSE_1_CLOUDFLARE_UA",
    "CAUSE_2_CREDS",
    "NETWORK",
    "OTHER",
})


def classify_intervals_icu_probe(
    *,
    ok: bool,
    http_status: Optional[int],
    error_body: Optional[str],
    error_message: Optional[str],
) -> str:
    """Classify a probe result into one of `OUTCOME_CLASSES`.

    Decision order (first match wins):
      1. ok=True            → ``OK``
      2. body mentions Cloudflare → ``CAUSE_1_CLOUDFLARE_UA``
         (regression detection: even with the W-CF-UA UA fix in place,
         a future Cloudflare ruleset change could re-trigger this.)
      3. HTTP 401/403       → ``CAUSE_2_CREDS``
      4. URLError-shaped (no http_status, message names a network
         primitive) → ``NETWORK``
      5. anything else      → ``OTHER``

    The Cloudflare check is body-shape-based (substring match on the
    canonical markers), not status-code-based — Cloudflare returns
    403 for both UA-blocks and (rarely) credential issues, so the
    body is the only honest discriminator.
    """

    if ok:
        return "OK"

    if error_body and _is_cloudflare_body(error_body):
        return "CAUSE_1_CLOUDFLARE_UA"

    if http_status in (401, 403):
        return "CAUSE_2_CREDS"

    if http_status is None and _looks_like_network_error(error_message):
        return "NETWORK"

    return "OTHER"


_CLOUDFLARE_BODY_MARKERS: tuple[str, ...] = (
    "cloudflare_error",
    "\"error_code\":1010",
    "browser_signature_banned",
    # Cloudflare's challenge page surface — older UA-block path.
    "Attention Required! | Cloudflare",
)


def _is_cloudflare_body(body: str) -> bool:
    """True if the response body looks Cloudflare-shaped."""

    return any(marker in body for marker in _CLOUDFLARE_BODY_MARKERS)


_NETWORK_ERROR_TOKENS: tuple[str, ...] = (
    "Connection refused",
    "Name or service not known",
    "nodename nor servname",  # macOS variant
    "timed out",
    "Network is unreachable",
    "No route to host",
    "Temporary failure in name resolution",
)


def _looks_like_network_error(error_message: Optional[str]) -> bool:
    """True if the error message names a network-layer failure."""

    if not error_message:
        return False
    return any(token in error_message for token in _NETWORK_ERROR_TOKENS)


# Per-class actionable next-step prose. Stable strings; the doctor
# render quotes them verbatim and the triage doc references them.
OUTCOME_NEXT_STEPS: dict[str, str] = {
    "OK": "Live API call succeeded.",
    "CAUSE_1_CLOUDFLARE_UA": (
        "Cloudflare bot-protection blocked the request at the edge — "
        "the credentials never reached intervals.icu. Verify the "
        "client User-Agent is not the urllib default; see "
        "`reporting/docs/intervals_icu_403_triage.md` (CAUSE_1)."
    ),
    "CAUSE_2_CREDS": (
        "intervals.icu rejected the credentials (HTTP 401/403). "
        "Re-run `hai auth intervals-icu` to refresh the API key, or "
        "verify athlete_id matches the API key's account. See "
        "`reporting/docs/intervals_icu_403_triage.md` (CAUSE_2)."
    ),
    "NETWORK": (
        "Could not reach intervals.icu (network or DNS layer). "
        "Verify connectivity, then re-run `hai doctor --deep`."
    ),
    "OTHER": (
        "Unclassified probe failure. Inspect the error body in the "
        "doctor JSON (`probe.error_body`) and consult "
        "`reporting/docs/intervals_icu_403_triage.md` (OTHER)."
    ),
}


class Probe(Protocol):
    """Probe surface for the deep-doctor checks."""

    def probe_intervals_icu(self, credentials: Any) -> ProbeResult: ...
    def probe_garmin(self, credentials: Any) -> ProbeResult: ...


class LiveProbe:
    """Real-network probe used in non-demo (real) mode.

    Reuses the existing intervals.icu adapter for a minimum-scope
    fetch. v0.1.11 W-X scope: probe intervals.icu only; Garmin
    surface gets a placeholder fixture-OK because the Garmin live
    path is rate-limited per AGENTS.md and not the recommended
    primary source.
    """

    def __init__(self, *, timeout_seconds: float = 5.0) -> None:
        self.timeout_seconds = timeout_seconds

    def probe_intervals_icu(self, credentials: Any) -> ProbeResult:
        from datetime import date, timedelta
        from health_agent_infra.core.pull.intervals_icu import (
            HttpIntervalsIcuClient,
            IntervalsIcuError,
        )

        client = HttpIntervalsIcuClient(
            credentials=credentials,
            timeout_seconds=self.timeout_seconds,
        )
        # Minimal-scope query: a single recent date. Fail fast.
        today = date.today()
        try:
            client.fetch_wellness_range(today - timedelta(days=1), today)
        except IntervalsIcuError as exc:
            msg = str(exc)
            # `IntervalsIcuError` carries http_status + body when the
            # underlying failure was an HTTPError. Falls back to None
            # for non-HTTP failures (URLError, JSON parse, etc.).
            http_status = exc.http_status
            error_body = exc.body
            outcome_class = classify_intervals_icu_probe(
                ok=False,
                http_status=http_status,
                error_body=error_body,
                error_message=msg,
            )
            return ProbeResult(
                ok=False,
                source="live",
                http_status=http_status,
                error_message=msg,
                error_body=error_body,
                outcome_class=outcome_class,
            )
        except Exception as exc:  # noqa: BLE001
            msg = f"{type(exc).__name__}: {exc}"
            outcome_class = classify_intervals_icu_probe(
                ok=False,
                http_status=None,
                error_body=None,
                error_message=msg,
            )
            return ProbeResult(
                ok=False,
                source="live",
                error_message=msg,
                outcome_class=outcome_class,
            )
        return ProbeResult(
            ok=True,
            source="live",
            http_status=200,
            outcome_class="OK",
        )

    def probe_garmin(self, credentials: Any) -> ProbeResult:
        # Garmin live login is rate-limited and unreliable per AGENTS.md
        # ("Garmin Connect is not the default live source"). v0.1.11
        # W-X does not introduce a new Garmin live probe. A future
        # workstream may add one; for now, return a "live-skipped"
        # result that surfaces honestly in the doctor row.
        return ProbeResult(
            ok=False,
            source="live",
            error_message=(
                "Garmin live probe not implemented (rate-limited per "
                "AGENTS.md; intervals.icu is the recommended live source)"
            ),
        )


class FixtureProbe:
    """Demo-mode probe — returns a fixture response without any network.

    The fixture is set per probe surface: a default 200-OK response
    when no override is supplied, or a caller-specified
    :class:`ProbeResult` when the demo persona / test wants to
    exercise a specific failure mode (e.g., a 403 to demo the
    diagnostic-trust feature).

    A hard no-network guard runs in tests via socket-monkeypatch;
    this class itself never opens a socket.
    """

    def __init__(
        self,
        *,
        intervals_icu_response: Optional[ProbeResult] = None,
        garmin_response: Optional[ProbeResult] = None,
    ) -> None:
        self._intervals_icu = intervals_icu_response or ProbeResult(
            ok=True, source="fixture", http_status=200, outcome_class="OK",
        )
        self._garmin = garmin_response or ProbeResult(
            ok=True, source="fixture", http_status=200, outcome_class="OK",
        )

    def probe_intervals_icu(self, credentials: Any) -> ProbeResult:
        return self._intervals_icu

    def probe_garmin(self, credentials: Any) -> ProbeResult:
        return self._garmin


def resolve_probe(*, demo_active: bool) -> Probe:
    """Return the probe implementation appropriate for the current mode.

    Demo mode → :class:`FixtureProbe` (default 200-OK responses).
    Real mode → :class:`LiveProbe`.

    Test-friendly override: pass an explicit ``Probe`` to
    :func:`run_deep_probes` instead of using this helper.
    """
    if demo_active:
        return FixtureProbe()
    return LiveProbe()


def run_deep_probes(
    *,
    probe: Probe,
    credential_store: Any,
) -> dict[str, ProbeResult]:
    """Run the configured probe against intervals.icu + Garmin and
    return a per-source dict of :class:`ProbeResult`.

    Skips probes when credentials are absent (the credential
    surface already returns ``warn`` in that case; the deep probe
    has nothing to probe).
    """

    out: dict[str, ProbeResult] = {}

    intervals_status = credential_store.intervals_icu_status()
    if intervals_status.get("credentials_available"):
        creds = credential_store.load_intervals_icu()
        if creds is not None:
            out["intervals_icu"] = probe.probe_intervals_icu(creds)

    garmin_status = credential_store.garmin_status()
    if garmin_status.get("credentials_available"):
        creds = credential_store.load_garmin()
        if creds is not None:
            out["garmin"] = probe.probe_garmin(creds)

    return out
