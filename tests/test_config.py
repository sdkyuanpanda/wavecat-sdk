"""Tests for wavecat_sdk.config.Settings and from_env()."""

from __future__ import annotations

import pytest

from wavecat_sdk.config import DEFAULT_STRIP_KEYS, Settings, from_env


def test_defaults() -> None:
    s = Settings()
    assert s.upstream_url == "http://127.0.0.1:8000/v1"
    assert s.upstream_key == ""
    assert s.model is None
    assert s.host == "127.0.0.1"
    assert s.port == 8800
    assert s.strip_keys == DEFAULT_STRIP_KEYS == ("cache_prompt",)
    assert s.request_timeout == 600.0


def test_trailing_slash_is_stripped() -> None:
    s = Settings(upstream_url="http://host:8000/v1/")
    assert s.upstream_url == "http://host:8000/v1"


def test_upstream_path_join() -> None:
    s = Settings(upstream_url="http://host:8000/v1")
    assert s.upstream("/chat/completions") == "http://host:8000/v1/chat/completions"
    assert s.upstream("models") == "http://host:8000/v1/models"


def test_auth_headers() -> None:
    assert Settings().auth_headers == {}
    assert Settings(upstream_key="secret").auth_headers == {"Authorization": "Bearer secret"}


def test_from_env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "WAVECAT_SDK_UPSTREAM",
        "WAVECAT_SDK_KEY",
        "WAVECAT_SDK_MODEL",
        "WAVECAT_SDK_HOST",
        "WAVECAT_SDK_PORT",
        "WAVECAT_SDK_STRIP_KEYS",
        "WAVECAT_SDK_TIMEOUT",
    ):
        monkeypatch.delenv(var, raising=False)
    s = from_env()
    assert s == Settings()


def test_from_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WAVECAT_SDK_UPSTREAM", "http://upstream:9000/v1")
    monkeypatch.setenv("WAVECAT_SDK_KEY", "tok")
    monkeypatch.setenv("WAVECAT_SDK_MODEL", "my-model")
    monkeypatch.setenv("WAVECAT_SDK_HOST", "0.0.0.0")
    monkeypatch.setenv("WAVECAT_SDK_PORT", "9999")
    monkeypatch.setenv("WAVECAT_SDK_STRIP_KEYS", "cache_prompt, chat_template_kwargs ,")
    monkeypatch.setenv("WAVECAT_SDK_TIMEOUT", "30")
    s = from_env()
    assert s.upstream_url == "http://upstream:9000/v1"
    assert s.upstream_key == "tok"
    assert s.model == "my-model"
    assert s.host == "0.0.0.0"
    assert s.port == 9999
    assert s.strip_keys == ("cache_prompt", "chat_template_kwargs")
    assert s.request_timeout == 30.0


def test_from_env_empty_model_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WAVECAT_SDK_MODEL", "")
    assert from_env().model is None
