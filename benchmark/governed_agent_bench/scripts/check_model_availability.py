"""Preflight: check that Together model ids are actually serverless-invocable.

The Together `/v1/models` catalog lists pricing even for dedicated-only models,
so a nonzero price does NOT imply serverless availability. The only reliable
signal is a live minimal call: a serverless model returns HTTP 200, a
dedicated-only model returns HTTP 400 with a "non-serverless" error. Run this
before any model-backed sweep so a roster is not silently populated with ids
that cannot run.

Usage:
    TOGETHER_API_KEY=... python -m governed_agent_bench.scripts.check_model_availability \
        Qwen/Qwen3-235B-A22B-Instruct-2507-tput meta-llama/Llama-3.3-70B-Instruct-Turbo

Exit code 0 if every id is serverless, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

TOGETHER_API_KEY_ENV = "TOGETHER_API_KEY"
_ENDPOINT = "https://api.together.xyz/v1/chat/completions"


def classify(model_id: str, api_key: str, *, timeout: float = 30.0) -> tuple[str, str]:
    """Return (verdict, detail) for one model id via a minimal live call."""

    payload = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 4,
        "temperature": 0,
    }).encode("utf-8")
    request = urllib.request.Request(
        _ENDPOINT,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "gab-availability-check/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            if resp.status == 200:
                return "SERVERLESS", "ok"
            return "ERROR", f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            message = (json.loads(body).get("error") or {}).get("message", "") or ""
        except json.JSONDecodeError:
            message = body
        if "non-serverless" in message:
            return "DEDICATED-ONLY", message[:100]
        if "only supports streaming" in message:
            return "STREAMING-ONLY", message[:100]
        return "ERROR", f"HTTP {exc.code}: {message[:100]}"
    except (urllib.error.URLError, TimeoutError) as exc:
        return "ERROR", str(exc)[:100]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_ids", nargs="+", help="Together model ids to check")
    args = parser.parse_args(argv)

    api_key = os.environ.get(TOGETHER_API_KEY_ENV, "").strip()
    if not api_key:
        sys.stderr.write(f"ERROR: {TOGETHER_API_KEY_ENV} is not set.\n")
        return 2

    all_ok = True
    for model_id in args.model_ids:
        verdict, detail = classify(model_id, api_key)
        if verdict != "SERVERLESS":
            all_ok = False
        print(f"{verdict:16s} {model_id}  ({detail})")
    if not all_ok:
        sys.stderr.write(
            "\nAt least one id is not serverless-invocable. The catalog "
            "'serverless' flag is unreliable; use this live check.\n"
        )
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
