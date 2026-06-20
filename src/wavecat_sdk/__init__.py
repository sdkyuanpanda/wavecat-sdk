"""Wavecat SDK — connect your own OpenAI-compatible backend to wavecat.

The SDK is a small, always-on **gateway**: it presents a stable
OpenAI-compatible endpoint (``/v1/chat/completions``, ``/v1/models``,
``/health``) on localhost and forwards every request to *your* model server
(llama.cpp, vLLM, …). Point wavecat's "Custom backend" Base URL at this
gateway and it routes its heavy-model work here instead of the local 35B.

The gateway only ever sees OpenAI chat-completion payloads. It never runs
wavecat tools and never touches user data — tools always execute inside
wavecat; this process only generates tokens.
"""

from wavecat_sdk.config import Settings
from wavecat_sdk.gateway import create_app

__all__ = ["Settings", "create_app"]
__version__ = "0.1.0"
