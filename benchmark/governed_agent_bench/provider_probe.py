"""Read-only provider/model/pricing dry-run probe for pilot lock evidence."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from governed_agent_bench.harness.fireworks import (
    FIREWORKS_API_KEY_ENV,
    FIREWORKS_ON_DEMAND_GPU_HOUR_REFERENCE,
)
from governed_agent_bench.harness.together import (
    TOGETHER_API_KEY_ENV,
    TOGETHER_QWEN3_235B_PRICING,
)
from governed_agent_bench.model_roster import load_model_roster


SCHEMA_VERSION = "governed_agent_bench.provider_probe.v1"
NO_MODEL_INVOCATION_NOTE = (
    "No chat, completions, messages, generation, or inference invocation "
    "endpoint was called; this probe uses only read-only metadata or docs."
)
FORBIDDEN_ENDPOINT_FRAGMENTS = (
    "/chat/completions",
    "/completions",
    "/messages",
    "/generation",
    "/generate",
    "/responses",
)


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    body: str
    url: str


class ReadOnlyTransport(Protocol):
    def get(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> HttpResponse:
        """Return a read-only HTTP response."""


class UrlLibReadOnlyTransport:
    """Small stdlib GET transport for read-only metadata/docs requests."""

    def get(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> HttpResponse:
        _assert_read_only_url(url)
        request = urllib.request.Request(
            url,
            headers=dict(headers),
            method="GET",
        )
        try:
            # URL is HTTPS-only and read-only guarded by _assert_read_only_url.
            with urllib.request.urlopen(  # nosec B310
                request,
                timeout=timeout_seconds,
            ) as response:
                body = response.read().decode("utf-8", errors="replace")
                return HttpResponse(
                    status_code=response.status,
                    body=body,
                    url=response.url,
                )
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return HttpResponse(status_code=exc.code, body=body, url=url)


@dataclass(frozen=True)
class ProviderSpec:
    provider: str
    api_key_env: str | None
    metadata_url: str | None
    docs_urls: tuple[str, ...]
    pricing_terms: tuple[str, ...]
    pricing_snapshot: Mapping[str, Any]


PROVIDER_SPECS: dict[str, ProviderSpec] = {
    "Together AI": ProviderSpec(
        provider="Together AI",
        api_key_env=TOGETHER_API_KEY_ENV,
        metadata_url="https://api.together.xyz/v1/models",
        docs_urls=(
            "https://www.together.ai/models/qwen3-235b-a22b-instruct-2507-fp8",
            "https://www.together.ai/models/qwen2-5-7b-instruct-turbo",
            "https://www.together.ai/pricing",
        ),
        pricing_terms=("Qwen", "0.20", "0.60"),
        pricing_snapshot=TOGETHER_QWEN3_235B_PRICING,
    ),
    "Fireworks AI": ProviderSpec(
        provider="Fireworks AI",
        api_key_env=FIREWORKS_API_KEY_ENV,
        metadata_url="https://api.fireworks.ai/inference/v1/models",
        docs_urls=(
            "https://fireworks.ai/models/fireworks/qwen2p5-32b-instruct",
            "https://fireworks.ai/pricing",
        ),
        pricing_terms=("H100", "B200", "7.0"),
        pricing_snapshot={
            "billing_model": "on_demand_gpu_time",
            "billing_granularity": "gpu_second",
            "on_demand_gpu_hour_reference": FIREWORKS_ON_DEMAND_GPU_HOUR_REFERENCE,
        },
    ),
    "Anthropic": ProviderSpec(
        provider="Anthropic",
        api_key_env=None,
        metadata_url=None,
        docs_urls=(
            "https://docs.anthropic.com/en/docs/about-claude/models/overview",
            "https://docs.anthropic.com/en/docs/about-claude/pricing",
        ),
        pricing_terms=("Claude", "Sonnet"),
        pricing_snapshot={
            "pricing_source": "Anthropic public pricing docs",
            "pricing_url": "https://docs.anthropic.com/en/docs/about-claude/pricing",
            "adapter_constant_status": "not_applicable_no_anthropic_adapter_pre_lock",
        },
    ),
}


def build_provider_probe_report(
    *,
    live: bool = False,
    transport: ReadOnlyTransport | None = None,
    env: Mapping[str, str] | None = None,
    now_utc: datetime | None = None,
    timeout_seconds: float = 20.0,
) -> dict[str, Any]:
    """Build a provider ID/pricing dry-run report without model calls."""

    env_map = os.environ if env is None else env
    when = now_utc or datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    roster = load_model_roster()
    conditions = [
        condition
        for condition in roster.get("conditions", [])
        if condition.get("provider") in PROVIDER_SPECS
    ]
    http = transport or UrlLibReadOnlyTransport()
    entries = [
        _probe_condition(
            condition,
            spec=PROVIDER_SPECS[str(condition["provider"])],
            live=live,
            transport=http,
            env=env_map,
            timeout_seconds=timeout_seconds,
        )
        for condition in conditions
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "verified_at_utc": when.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "live_network_attempted": live,
        "no_model_invocation": True,
        "no_model_invocation_note": NO_MODEL_INVOCATION_NOTE,
        "forbidden_endpoint_fragments": list(FORBIDDEN_ENDPOINT_FRAGMENTS),
        "roster_file": str(roster.get("roster_file", "model_roster.md")),
        "condition_count": len(entries),
        "conditions": entries,
        "overall_status": _overall_status(entries),
    }


def write_provider_probe_report(
    *,
    output_json: Path,
    output_markdown: Path | None = None,
    live: bool = False,
    transport: ReadOnlyTransport | None = None,
    env: Mapping[str, str] | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    report = build_provider_probe_report(
        live=live,
        transport=transport,
        env=env,
        now_utc=now_utc,
    )
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path = output_markdown
    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(_markdown(report), encoding="utf-8")
    return {
        "schema_version": "governed_agent_bench.provider_probe_output.v1",
        "json_path": output_json.as_posix(),
        "markdown_path": None if markdown_path is None else markdown_path.as_posix(),
        "overall_status": report["overall_status"],
        "live_network_attempted": live,
    }


def _probe_condition(
    condition: Mapping[str, Any],
    *,
    spec: ProviderSpec,
    live: bool,
    transport: ReadOnlyTransport,
    env: Mapping[str, str],
    timeout_seconds: float,
) -> dict[str, Any]:
    model_id = str(condition["model_id"])
    metadata_result = _metadata_check(
        model_id,
        spec=spec,
        live=live,
        transport=transport,
        env=env,
        timeout_seconds=timeout_seconds,
    )
    docs_result = _docs_check(
        model_id,
        spec=spec,
        live=live,
        transport=transport,
        timeout_seconds=timeout_seconds,
    )
    return {
        "condition_id": str(condition["condition_id"]),
        "system_id": str(condition["system_id"]),
        "provider": spec.provider,
        "model_id": model_id,
        "model_id_status": _model_status(metadata_result, docs_result, live),
        "model_id_evidence": {
            "metadata": metadata_result,
            "docs": docs_result["model_docs"],
        },
        "pricing_status": _pricing_status(docs_result, live),
        "pricing_evidence": {
            "configured_pricing_snapshot": dict(spec.pricing_snapshot),
            "docs": docs_result["pricing_docs"],
        },
    }


def _metadata_check(
    model_id: str,
    *,
    spec: ProviderSpec,
    live: bool,
    transport: ReadOnlyTransport,
    env: Mapping[str, str],
    timeout_seconds: float,
) -> dict[str, Any]:
    if not live:
        return {
            "status": "not_verified_live",
            "reason": "live probe not requested",
            "metadata_url": spec.metadata_url,
        }
    if spec.metadata_url is None:
        return {
            "status": "not_available_for_provider",
            "reason": "no read-only metadata endpoint configured",
            "metadata_url": None,
        }
    _assert_read_only_url(spec.metadata_url)
    headers: dict[str, str] = {"Accept": "application/json"}
    if spec.api_key_env:
        api_key = env.get(spec.api_key_env, "").strip()
        if not api_key:
            return {
                "status": "not_verified_live",
                "reason": f"{spec.api_key_env} not present",
                "metadata_url": spec.metadata_url,
            }
        headers["Authorization"] = "Bearer <redacted>"
        actual_headers = {"Accept": "application/json", "Authorization": f"Bearer {api_key}"}
    else:
        actual_headers = headers
    try:
        response = transport.get(
            spec.metadata_url,
            headers=actual_headers,
            timeout_seconds=timeout_seconds,
        )
    except Exception as exc:  # noqa: BLE001 - status artifact records failure.
        return {
            "status": "not_verified_live",
            "reason": str(exc),
            "metadata_url": spec.metadata_url,
        }
    if response.status_code >= 400:
        return {
            "status": "not_verified_live",
            "reason": f"HTTP {response.status_code}",
            "metadata_url": spec.metadata_url,
        }
    found = _model_id_in_metadata(model_id, response.body)
    return {
        "status": "verified_metadata" if found else "not_found_in_metadata",
        "metadata_url": spec.metadata_url,
        "http_status": response.status_code,
        "model_id_found": found,
        "request_headers_recorded": headers,
    }


def _docs_check(
    model_id: str,
    *,
    spec: ProviderSpec,
    live: bool,
    transport: ReadOnlyTransport,
    timeout_seconds: float,
) -> dict[str, Any]:
    if not live:
        return {
            "model_docs": {
                "status": "not_verified_live",
                "reason": "live probe not requested",
                "urls": list(spec.docs_urls),
            },
            "pricing_docs": {
                "status": "not_verified_live",
                "reason": "live probe not requested",
                "urls": list(spec.docs_urls),
            },
        }
    model_hits = []
    pricing_hits = []
    errors = []
    for url in spec.docs_urls:
        _assert_read_only_url(url)
        try:
            response = transport.get(
                url,
                headers={"Accept": "text/html, text/plain, application/json"},
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001 - status artifact records failure.
            errors.append({"url": url, "error": str(exc)})
            continue
        if response.status_code >= 400:
            errors.append({"url": url, "error": f"HTTP {response.status_code}"})
            continue
        body = response.body
        if model_id in body or _model_id_slug(model_id) in body:
            model_hits.append(url)
        if all(term.lower() in body.lower() for term in spec.pricing_terms):
            pricing_hits.append(url)
    return {
        "model_docs": {
            "status": "verified_docs" if model_hits else "not_found_in_docs",
            "urls_checked": list(spec.docs_urls),
            "matching_urls": model_hits,
            "errors": errors,
        },
        "pricing_docs": {
            "status": "verified_docs" if pricing_hits else "not_found_in_docs",
            "urls_checked": list(spec.docs_urls),
            "matching_urls": pricing_hits,
            "expected_terms": list(spec.pricing_terms),
            "errors": errors,
        },
    }


def _model_status(
    metadata_result: Mapping[str, Any],
    docs_result: Mapping[str, Any],
    live: bool,
) -> str:
    if metadata_result["status"] == "verified_metadata":
        return "verified_metadata"
    if docs_result["model_docs"]["status"] == "verified_docs":
        return "verified_docs"
    if not live:
        return "not_verified_live"
    return "not_verified_live"


def _pricing_status(docs_result: Mapping[str, Any], live: bool) -> str:
    if docs_result["pricing_docs"]["status"] == "verified_docs":
        return "verified_docs"
    if not live:
        return "not_verified_live"
    return "not_verified_live"


def _overall_status(entries: Sequence[Mapping[str, Any]]) -> str:
    if not entries:
        return "no_roster_entries"
    if all(
        entry["model_id_status"] in {"verified_metadata", "verified_docs"}
        and entry["pricing_status"] == "verified_docs"
        for entry in entries
    ):
        return "verified_live"
    if any(
        entry["model_id_status"] in {"verified_metadata", "verified_docs"}
        or entry["pricing_status"] == "verified_docs"
        for entry in entries
    ):
        return "partially_verified_live"
    return "not_verified_live"


def _model_id_in_metadata(model_id: str, body: str) -> bool:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return model_id in body
    candidates = _metadata_candidates(payload)
    return model_id in candidates or _model_id_slug(model_id) in candidates


def _metadata_candidates(payload: Any) -> set[str]:
    candidates: set[str] = set()
    if isinstance(payload, dict):
        for key in ("id", "name", "model", "model_id"):
            value = payload.get(key)
            if isinstance(value, str):
                candidates.add(value)
        for value in payload.values():
            if isinstance(value, (dict, list)):
                candidates.update(_metadata_candidates(value))
    elif isinstance(payload, list):
        for item in payload:
            candidates.update(_metadata_candidates(item))
    return candidates


def _model_id_slug(model_id: str) -> str:
    return (
        model_id.rsplit("/", 1)[-1]
        .replace(".", "p")
        .replace("-", "_")
        .lower()
    )


def _assert_read_only_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"provider probe URL must use https: {url}")
    lower = url.lower()
    for fragment in FORBIDDEN_ENDPOINT_FRAGMENTS:
        if fragment in lower:
            raise ValueError(f"forbidden model-invocation endpoint: {url}")


def _markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Provider Probe",
        "",
        f"- Verified at UTC: `{report['verified_at_utc']}`",
        f"- Overall status: `{report['overall_status']}`",
        f"- Live network attempted: `{report['live_network_attempted']}`",
        f"- No model invocation: `{report['no_model_invocation']}`",
        "",
        "| Condition | Provider | Model status | Pricing status |",
        "|---|---|---|---|",
    ]
    for entry in report["conditions"]:
        lines.append(
            "| {condition_id} | {provider} | {model_id_status} | {pricing_status} |".format(
                **entry
            )
        )
    lines.append("")
    lines.append(str(report["no_model_invocation_note"]))
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-markdown", type=Path)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Attempt read-only metadata/docs network checks.",
    )
    args = parser.parse_args(argv)
    output = write_provider_probe_report(
        output_json=args.output_json,
        output_markdown=args.output_markdown,
        live=args.live,
    )
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
