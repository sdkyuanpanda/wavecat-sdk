"""Gateway configuration: where to listen and which upstream to forward to."""

from __future__ import annotations

import os
from dataclasses import dataclass

#: Top-level request-body keys dropped before forwarding by default. wavecat sends
#: llama.cpp-flavored extras (``cache_prompt``) that a stricter OpenAI server
#: (e.g. vLLM) may reject with a 400.
DEFAULT_STRIP_KEYS: tuple[str, ...] = ("cache_prompt",)


@dataclass
class Settings:
    """Runtime config for the gateway.

    Attributes:
        upstream_url: The OpenAI API root of YOUR model server (llama.cpp / vLLM),
            e.g. ``http://127.0.0.1:8000/v1``.
        upstream_key: Optional bearer token your server expects.
        model: If set, the inbound ``model`` field is rewritten to this before
            forwarding — so wavecat can send any model id and you decide what
            actually serves it. ``None`` passes the inbound model through.
        host / port: Where the gateway itself listens (wavecat points here).
        strip_keys: Top-level request-body keys to drop before forwarding. These
            are wavecat/llama.cpp-isms a stricter server (vLLM) may reject.
        request_timeout: Per-request upstream timeout (seconds).
    """

    upstream_url: str = "http://127.0.0.1:8000/v1"
    upstream_key: str = ""
    model: str | None = None
    host: str = "127.0.0.1"
    port: int = 8800
    strip_keys: tuple[str, ...] = DEFAULT_STRIP_KEYS
    request_timeout: float = 600.0

    def __post_init__(self) -> None:
        self.upstream_url = self.upstream_url.rstrip("/")

    def upstream(self, path: str) -> str:
        """Build a full upstream URL for an OpenAI sub-path (e.g. ``/chat/completions``)."""
        return f"{self.upstream_url}/{path.lstrip('/')}"

    @property
    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.upstream_key}"} if self.upstream_key else {}


def from_env() -> Settings:
    """Build :class:`Settings` from ``WAVECAT_SDK_*`` env vars (CLI flags override)."""
    strip = os.getenv("WAVECAT_SDK_STRIP_KEYS")
    strip_keys = tuple(k.strip() for k in strip.split(",") if k.strip()) if strip else DEFAULT_STRIP_KEYS
    return Settings(
        upstream_url=os.getenv("WAVECAT_SDK_UPSTREAM", "http://127.0.0.1:8000/v1"),
        upstream_key=os.getenv("WAVECAT_SDK_KEY", ""),
        model=os.getenv("WAVECAT_SDK_MODEL") or None,
        host=os.getenv("WAVECAT_SDK_HOST", "127.0.0.1"),
        port=int(os.getenv("WAVECAT_SDK_PORT", "8800")),
        strip_keys=strip_keys,
        request_timeout=float(os.getenv("WAVECAT_SDK_TIMEOUT", "600")),
    )
