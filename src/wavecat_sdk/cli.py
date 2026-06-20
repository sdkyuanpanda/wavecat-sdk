"""``wavecat-sdk`` command line — run the gateway.

Example::

    wavecat-sdk serve --upstream http://127.0.0.1:8000/v1 --model my-model --port 8800

Then in wavecat → Settings → Backend, enable the custom backend and set the Base
URL to ``http://127.0.0.1:8800/v1``.
"""

from __future__ import annotations

import argparse
import sys

import uvicorn

from wavecat_sdk.config import Settings, from_env
from wavecat_sdk.gateway import create_app


def _build_settings(args: argparse.Namespace) -> Settings:
    """CLI flags override the ``WAVECAT_SDK_*`` env defaults."""
    s = from_env()
    if args.upstream:
        s.upstream_url = args.upstream.rstrip("/")
    if args.upstream_key is not None:
        s.upstream_key = args.upstream_key
    if args.model is not None:
        s.model = args.model or None
    if args.host:
        s.host = args.host
    if args.port:
        s.port = args.port
    if args.strip_keys is not None:
        s.strip_keys = tuple(k.strip() for k in args.strip_keys.split(",") if k.strip())
    return s


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wavecat-sdk", description="Connect your backend to wavecat.")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Run the OpenAI-compatible gateway.")
    serve.add_argument("--upstream", help="Your model server's OpenAI root, e.g. http://127.0.0.1:8000/v1")
    serve.add_argument("--upstream-key", default=None, help="Bearer token your server expects (optional).")
    serve.add_argument("--model", default=None, help="Rewrite the inbound model id to this (optional).")
    serve.add_argument("--host", default=None, help="Gateway listen host (default 127.0.0.1).")
    serve.add_argument("--port", type=int, default=None, help="Gateway listen port (default 8800).")
    serve.add_argument(
        "--strip-keys",
        default=None,
        help="Comma-separated request-body keys to drop before forwarding (default: cache_prompt).",
    )

    args = parser.parse_args(argv)
    if args.command == "serve":
        settings = _build_settings(args)
        app = create_app(settings)
        print(
            f"[wavecat-sdk] gateway on http://{settings.host}:{settings.port}/v1 "
            f"→ upstream {settings.upstream_url}"
            + (f" (as model '{settings.model}')" if settings.model else "")
        )
        uvicorn.run(app, host=settings.host, port=settings.port, log_level="warning")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
