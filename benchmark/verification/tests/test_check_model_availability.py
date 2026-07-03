"""Offline tests for the serverless-availability preflight (WP-B).

The real check makes a live Together call; here we mock the HTTP layer so the
verdict logic (200 -> serverless, 400 non-serverless -> dedicated-only) is
tested without network.
"""

from __future__ import annotations

import io
import json
import urllib.error

import pytest

from governed_agent_bench.scripts import check_model_availability as cma


class _FakeResp:
    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self) -> "_FakeResp":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def _http_error(code: int, message: str) -> urllib.error.HTTPError:
    body = json.dumps({"error": {"message": message}}).encode("utf-8")
    return urllib.error.HTTPError(
        url="x", code=code, msg="err", hdrs=None, fp=io.BytesIO(body)
    )


def test_serverless_model_is_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cma.urllib.request, "urlopen", lambda *a, **k: _FakeResp(200))
    assert cma.classify("some/model", "key")[0] == "SERVERLESS"


def test_dedicated_only_is_flagged(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*a: object, **k: object) -> None:
        raise _http_error(400, "Unable to access non-serverless model some/model.")

    monkeypatch.setattr(cma.urllib.request, "urlopen", _raise)
    verdict, _ = cma.classify("some/model", "key")
    assert verdict == "DEDICATED-ONLY"


def test_streaming_only_is_flagged(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*a: object, **k: object) -> None:
        raise _http_error(400, 'This model only supports streaming. Set "stream": true.')

    monkeypatch.setattr(cma.urllib.request, "urlopen", _raise)
    assert cma.classify("some/model", "key")[0] == "STREAMING-ONLY"


def test_main_exit_code_reflects_availability(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("TOGETHER_API_KEY", "key")
    monkeypatch.setattr(
        cma, "classify", lambda mid, key, **k:
        ("SERVERLESS", "ok") if "good" in mid else ("DEDICATED-ONLY", "no")
    )
    assert cma.main(["good/model"]) == 0
    assert cma.main(["bad/model"]) == 1
    assert cma.main(["good/model", "bad/model"]) == 1
