"""The OpenAI-compatible proxy gateway wavecat talks to.

wavecat ──/v1──► [this gateway] ──/v1──► your llama.cpp / vLLM

Three routes are exposed:

* ``POST /v1/chat/completions`` — proxy (streaming + non-streaming) to your
  upstream. The inbound body is lightly sanitized (drop wavecat/llama.cpp-only
  keys a strict server might reject; optionally rewrite the ``model`` id).
* ``GET  /v1/models``           — proxied so wavecat's reachability probe + Test
  button verify the WHOLE chain (gateway → upstream), not just the gateway.
* ``GET  /health``              — gateway liveness.

The gateway never executes tools and never sees wavecat internals — it only
relays OpenAI chat payloads (prompts, tool schemas/results-as-text, sampling
params) to and from your model.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from wavecat_sdk.config import Settings

logger = logging.getLogger("wavecat_sdk")


def _sanitize(body: dict[str, Any], settings: Settings) -> dict[str, Any]:
    """Drop unsupported top-level keys and (optionally) rewrite the model id.

    wavecat sends llama.cpp-flavored extras (e.g. ``cache_prompt``); a stricter
    OpenAI server may 400 on unknown fields, so we drop the configured
    ``strip_keys``. ``chat_template_kwargs`` is left intact by default (both
    llama.cpp and vLLM accept it) — add it to ``strip_keys`` if your server
    rejects it.
    """
    clean = {k: v for k, v in body.items() if k not in settings.strip_keys}
    if settings.model:
        clean["model"] = settings.model
    return clean


def create_app(settings: Settings) -> FastAPI:
    """Build the gateway app bound to a given upstream."""
    client = httpx.AsyncClient(timeout=settings.request_timeout)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        # Own the upstream HTTP client for the app's lifetime; close it on shutdown.
        try:
            yield
        finally:
            await client.aclose()

    app = FastAPI(title="wavecat-sdk gateway", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "upstream": settings.upstream_url}

    @app.get("/v1/models")
    async def models() -> Response:
        """Proxy the upstream model list (so a probe checks the full chain)."""
        try:
            r = await client.get(settings.upstream("/models"), headers=settings.auth_headers)
        except httpx.RequestError as exc:
            logger.warning("upstream unreachable on /v1/models: %s", exc)
            return JSONResponse({"error": f"upstream unreachable: {exc}"}, status_code=503)
        return Response(content=r.content, status_code=r.status_code, media_type="application/json")

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request) -> Response:
        """Proxy a chat completion, streaming when the client asked for it."""
        raw = await request.body()
        try:
            body = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return JSONResponse({"error": "invalid JSON body"}, status_code=400)

        body = _sanitize(body, settings)
        stream = bool(body.get("stream"))
        url = settings.upstream("/chat/completions")
        headers = {"Content-Type": "application/json", **settings.auth_headers}

        if not stream:
            try:
                r = await client.post(url, json=body, headers=headers)
            except httpx.RequestError as exc:
                logger.warning("upstream unreachable on /v1/chat/completions: %s", exc)
                return JSONResponse({"error": f"upstream unreachable: {exc}"}, status_code=503)
            return Response(
                content=r.content,
                status_code=r.status_code,
                media_type=r.headers.get("content-type", "application/json"),
            )

        async def relay() -> Any:
            # Stream the upstream SSE through unchanged so wavecat's reader sees
            # the exact OpenAI delta frames it expects.
            try:
                async with client.stream("POST", url, json=body, headers=headers) as up:
                    async for chunk in up.aiter_raw():
                        if chunk:
                            yield chunk
            except httpx.RequestError as exc:
                logger.warning("upstream unreachable mid-stream: %s", exc)
                err = {"error": {"message": f"upstream unreachable: {exc}", "type": "gateway"}}
                yield f"data: {json.dumps(err)}\n\n".encode()
                yield b"data: [DONE]\n\n"

        return StreamingResponse(relay(), media_type="text/event-stream")

    return app
