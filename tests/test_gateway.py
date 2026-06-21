"""Tests for the wavecat_sdk gateway app, with the upstream mocked via respx."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from wavecat_sdk.config import Settings
from wavecat_sdk.gateway import _sanitize, create_app

UPSTREAM = "http://127.0.0.1:8000/v1"


@pytest.fixture
def client() -> TestClient:
    settings = Settings(upstream_url=UPSTREAM, model="rewritten-model")
    # Context manager triggers the lifespan (and closes the upstream client on exit).
    with TestClient(create_app(settings)) as c:
        yield c


def test_sanitize_drops_keys_and_rewrites_model() -> None:
    settings = Settings(model="forced", strip_keys=("cache_prompt", "extra"))
    body = {"model": "anything", "cache_prompt": True, "extra": 1, "messages": []}
    assert _sanitize(body, settings) == {"model": "forced", "messages": []}


def test_sanitize_passthrough_model_when_unset() -> None:
    settings = Settings(model=None, strip_keys=())
    body = {"model": "keep-me", "messages": []}
    assert _sanitize(body, settings) == {"model": "keep-me", "messages": []}


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "upstream": UPSTREAM}


@respx.mock
def test_models_proxied(client: TestClient) -> None:
    route = respx.get(f"{UPSTREAM}/models").mock(
        return_value=httpx.Response(200, json={"object": "list", "data": [{"id": "m"}]})
    )
    r = client.get("/v1/models")
    assert route.called
    assert r.status_code == 200
    assert r.json()["data"][0]["id"] == "m"


@respx.mock
def test_models_upstream_unreachable(client: TestClient) -> None:
    respx.get(f"{UPSTREAM}/models").mock(side_effect=httpx.ConnectError("refused"))
    r = client.get("/v1/models")
    assert r.status_code == 503
    assert "upstream unreachable" in r.json()["error"]


@respx.mock
def test_chat_completions_non_streaming(client: TestClient) -> None:
    route = respx.post(f"{UPSTREAM}/chat/completions").mock(
        return_value=httpx.Response(200, json={"id": "x", "choices": []})
    )
    r = client.post(
        "/v1/chat/completions",
        json={"model": "ignored", "cache_prompt": True, "messages": [{"role": "user", "content": "hi"}]},
    )
    assert r.status_code == 200
    assert r.json()["id"] == "x"
    # The body forwarded upstream is sanitized: cache_prompt dropped, model rewritten.
    forwarded = json.loads(route.calls.last.request.content)
    assert "cache_prompt" not in forwarded
    assert forwarded["model"] == "rewritten-model"


def test_chat_completions_invalid_json(client: TestClient) -> None:
    r = client.post("/v1/chat/completions", content=b"not json{")
    assert r.status_code == 400
    assert r.json() == {"error": "invalid JSON body"}


@respx.mock
def test_chat_completions_upstream_unreachable(client: TestClient) -> None:
    respx.post(f"{UPSTREAM}/chat/completions").mock(side_effect=httpx.ConnectError("refused"))
    r = client.post("/v1/chat/completions", json={"messages": []})
    assert r.status_code == 503
    assert "upstream unreachable" in r.json()["error"]
