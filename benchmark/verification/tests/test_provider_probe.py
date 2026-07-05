"""Provider ID/pricing dry-run probe tests with mocked transport."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import pytest


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.harness.fireworks import FIREWORKS_API_KEY_ENV  # noqa: E402
from governed_agent_bench.harness.together import TOGETHER_API_KEY_ENV  # noqa: E402
from governed_agent_bench.provider_probe import (  # noqa: E402
    HttpResponse,
    _assert_read_only_url,
    build_provider_probe_report,
    write_provider_probe_report,
)


NOW = datetime(2026, 6, 22, 9, 30, tzinfo=timezone.utc)


@dataclass
class FakeTransport:
    bodies: Mapping[str, str]
    calls: list[str]

    def get(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> HttpResponse:
        del headers, timeout_seconds
        self.calls.append(url)
        return HttpResponse(status_code=200, body=self.bodies[url], url=url)


def test_provider_probe_without_live_network_marks_lock_evidence_pending() -> None:
    transport = FakeTransport(bodies={}, calls=[])

    report = build_provider_probe_report(
        live=False,
        transport=transport,
        env={},
        now_utc=NOW,
    )

    assert report["verified_at_utc"] == "2026-06-22T09:30:00Z"
    assert report["overall_status"] == "not_verified_live"
    assert report["live_network_attempted"] is False
    assert report["no_model_invocation"] is True
    assert transport.calls == []
    assert {entry["provider"] for entry in report["conditions"]} == {
        "Together AI",
        "Fireworks AI",
        "Anthropic",
    }
    assert all(
        entry["model_id_status"] == "not_verified_live"
        for entry in report["conditions"]
    )


def test_provider_probe_uses_only_mocked_read_only_metadata_and_docs() -> None:
    bodies = {
        "https://api.together.xyz/v1/models": json.dumps(
            {"data": [
                {"id": "Qwen/Qwen3-235B-A22B-Instruct-2507-tput"},
                {"id": "Qwen/Qwen2.5-7B-Instruct-Turbo"},
            ]}
        ),
        "https://www.together.ai/models/qwen3-235b-a22b-instruct-2507-fp8": (
            "Qwen/Qwen3-235B-A22B-Instruct-2507-tput input 0.20 output 0.60 Qwen"
        ),
        "https://www.together.ai/models/qwen2-5-7b-instruct-turbo": (
            "Qwen/Qwen2.5-7B-Instruct-Turbo"
        ),
        "https://www.together.ai/pricing": "Qwen serverless price 0.30",
        "https://api.fireworks.ai/inference/v1/models": json.dumps(
            {"models": [{"id": "accounts/fireworks/models/qwen2p5-32b-instruct"}]}
        ),
        "https://fireworks.ai/models/fireworks/qwen2p5-32b-instruct": (
            "accounts/fireworks/models/qwen2p5-32b-instruct"
        ),
        "https://fireworks.ai/pricing": "H100 7.0 B200 deployment pricing",
        "https://docs.anthropic.com/en/docs/about-claude/models/overview": (
            "claude-sonnet-4-6"
        ),
        "https://docs.anthropic.com/en/docs/about-claude/pricing": (
            "Claude Sonnet pricing"
        ),
    }
    transport = FakeTransport(bodies=bodies, calls=[])

    report = build_provider_probe_report(
        live=True,
        transport=transport,
        env={
            TOGETHER_API_KEY_ENV: "together-secret",
            FIREWORKS_API_KEY_ENV: "fireworks-secret",
        },
        now_utc=NOW,
    )

    assert report["overall_status"] == "verified_live"
    assert report["no_model_invocation"] is True
    assert not any(
        fragment in url
        for url in transport.calls
        for fragment in ("/chat/completions", "/messages", "/generation")
    )
    by_provider = {entry["provider"]: entry for entry in report["conditions"]}
    assert by_provider["Together AI"]["model_id_status"] == "verified_metadata"
    assert by_provider["Together AI"]["pricing_status"] == "verified_docs"
    assert by_provider["Fireworks AI"]["model_id_status"] == "verified_metadata"
    assert by_provider["Fireworks AI"]["pricing_status"] == "verified_docs"
    assert by_provider["Anthropic"]["model_id_status"] == "verified_docs"
    assert by_provider["Anthropic"]["pricing_status"] == "verified_docs"
    text = json.dumps(report)
    assert "together-secret" not in text
    assert "fireworks-secret" not in text


def test_provider_probe_writes_json_and_markdown(tmp_path: Path) -> None:
    json_path = tmp_path / "provider_probe.json"
    markdown_path = tmp_path / "provider_probe.md"

    output = write_provider_probe_report(
        output_json=json_path,
        output_markdown=markdown_path,
        live=False,
        transport=FakeTransport(bodies={}, calls=[]),
        env={},
        now_utc=NOW,
    )

    assert output["json_path"] == json_path.as_posix()
    assert output["markdown_path"] == markdown_path.as_posix()
    report = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")
    assert report["schema_version"] == "governed_agent_bench.provider_probe.v1"
    assert "Provider Probe" in markdown
    assert "No model invocation" in markdown


@pytest.mark.parametrize(
    "url",
    [
        "https://api.together.xyz/v1/chat/completions",
        "https://api.anthropic.com/v1/messages",
        "https://example.invalid/v1/generation",
    ],
)
def test_provider_probe_rejects_model_invocation_endpoints(url: str) -> None:
    with pytest.raises(ValueError, match="forbidden model-invocation endpoint"):
        _assert_read_only_url(url)
