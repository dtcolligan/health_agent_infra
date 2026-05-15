# intervals.icu HTTP 403 Triage

When `hai pull --source intervals_icu` returns HTTP 403 (Forbidden),
the failure has at least two distinct root causes that surface
identically at the `IntervalsIcuError` boundary. The error body
shape distinguishes them. This document is the project-versioned
triage script — `hai doctor --deep` (W-AE) consumes it to surface
the actual error class to the user.

The original symptom report (F-DEMO-01) misattributed both shapes
to credential rotation; the v0.1.12.1 hotfix (W-CF-UA) fixed the
dominant cause (Cloudflare bot fingerprinting on urllib's default
User-Agent). This doc captures the calibration so the next session
doesn't repeat the misdiagnosis.

## Two distinct 403 root causes

### Cause 1 — Cloudflare User-Agent block

Cloudflare's bot protection on the intervals.icu zone returns HTTP
403 with error 1010 (`browser_signature_banned`) when urllib's
default UA `Python-urllib/3.x` is sent. The credentials never reach
the intervals.icu auth layer — Cloudflare drops the request at the
edge.

**Diagnostic tell:** error body is Cloudflare-shaped JSON, e.g.

```json
{
  "type": "https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/",
  "title": "Error 1010: Access denied",
  "status": 403,
  "detail": "The site owner has blocked access based on your browser's signature.",
  "error_code": 1010,
  "error_name": "browser_signature_banned",
  "cloudflare_error": true,
  "retryable": false
}
```

**Fix shape:** the adapter must send a non-default User-Agent. As of
v0.1.12.1, `HttpIntervalsIcuClient` sets a project-identifying UA
(`health-agent-infra/<version>`) on every request, which clears
the heuristic. The `user_agent` field is overridable for diagnostic
or compatibility purposes.

**Re-auth is not the fix for this cause.** The credentials are
fine; the request never authenticates.

### Cause 2 — Genuine credential rejection

The intervals.icu API itself rejects the credentials (revoked API
key, wrong athlete_id, account-level permission change).

**Diagnostic tell:** error body is intervals.icu-shaped — typically
401 Unauthorized OR 403 with intervals.icu's own JSON body
(structurally distinct from Cloudflare's; no `cloudflare_error`
field).

**Fix shape:** re-auth via `hai auth intervals-icu` (interactive;
prompts for API key + athlete ID).

## Triage script (programmatic probe)

Use this to determine the cause when a pull fails. Read-only;
sends one request to the athlete-profile endpoint (lighter than
wellness):

```python
import base64
import urllib.error
import urllib.request

from health_agent_infra.core.pull.auth import CredentialStore

creds = CredentialStore.default().load_intervals_icu()
if creds is None:
    print("NO_CREDS — run `hai auth intervals-icu`")
    raise SystemExit(1)

token = base64.b64encode(f"API_KEY:{creds.api_key}".encode()).decode()
url = (
    f"https://intervals.icu/api/v1/athlete/"
    f"{creds.athlete_id}/profile"
)
req = urllib.request.Request(
    url,
    headers={
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
        "User-Agent": "health-agent-infra-triage/1.0",
    },
)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        print(f"OK status={resp.status}")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    if "cloudflare_error" in body or "error_code\":1010" in body:
        print("CAUSE_1_CLOUDFLARE_UA — adapter UA is wrong / regression")
    elif e.code in (401, 403):
        print("CAUSE_2_CREDS — re-auth via `hai auth intervals-icu`")
    else:
        print(f"OTHER status={e.code} body={body[:200]}")
except urllib.error.URLError as e:
    print(f"NETWORK reason={e.reason}")
```

The probe sends a non-default User-Agent so it surfaces credential
issues distinctly from Cloudflare blocks. If you instead run the
probe with the urllib-default UA, both causes will collapse into a
single 403 and the triage fails.

## Calibration: don't recommend re-auth without the body

The v0.1.12.1 hotfix sequence had two diagnostic stages:

1. **Initial misdiagnosis** — symptom was 403, cited cause was
   "API key rotated." User pushed back ("I never rotated my key").
2. **Probe revealed Cloudflare** — the error body distinguished
   `cloudflare_error: true` from intervals.icu auth-shaped JSON.

If you see a 403 from intervals.icu in a future session, **read the
error body** before suggesting re-auth. The body shape is the
authoritative signal; the HTTP code alone is ambiguous.

## How `hai doctor --deep` consumes this

W-AE (v0.1.13 scope) extends `hai doctor` with a `--deep` mode that
performs the live-API probe above. The output classifies the
response into one of **five outcome classes (one success + four
failure classes)**:

**Success (1):**

- `OK` — pull works; credentials and adapter both healthy.

**Failure classes (4):**

- `CAUSE_1_CLOUDFLARE_UA` — adapter is sending the urllib-default
  UA (regression of v0.1.12.1 W-CF-UA fix). User cannot resolve;
  this is a code bug.
- `CAUSE_2_CREDS` — credentials present but rejected.
  Actionable: `hai auth intervals-icu`.
- `NETWORK` — DNS / TCP / TLS layer.
- `OTHER` — surface raw HTTP code + first 200 chars of body for
  reporting.

`hai doctor` (default mode, no `--deep`) does NOT make a live API
call — it reads keyring presence only, per the existing read-only
contract. `--deep` is the opt-in network surface introduced at
v0.1.11 W-X with the `Probe` protocol; W-AE adds the intervals.icu
probe class to that protocol.

## Origin

- F-DEMO-01 (v0.1.10 demo-run findings, 2026-04-28).
- W-CF-UA fix (v0.1.12.1 hotfix, 2026-04-29).
- W-AE plan (v0.1.13, this cycle).
- This doc authored 2026-04-30 in response to D14 round-1 finding
  F-PLAN-10 (W-AE acceptance cited a private memory note; moved to
  this versioned location).
