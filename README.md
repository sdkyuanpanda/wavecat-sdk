<p align="center">
  <img src="assets/wavecat_banner.png" alt="Banner" width="100%" />
</p>

# Wavecat Software Development Kit (SDK)
## connect your own backend :)

Run wavecat's **heavy model** on your own hardware. The SDK is a tiny, always-on
**gateway** that presents a stable OpenAI-compatible endpoint on localhost and
forwards every request to *your* model server (llama.cpp, vLLM, …). Point
wavecat at the gateway and it routes the interactive heavy work — **chat, agent,
and code** turns (plus optional screenshot Q&A) — there instead of the bundled
local 35B. Everything else (the local 4B, OCR, embeddings, and the background
memory/memex updates) keeps running on-device, unchanged.

```
wavecat ──/v1──► [wavecat-sdk gateway :8800] ──/v1──► your llama.cpp / vLLM
```

> **Minimal exposure.** The gateway only ever sees OpenAI chat-completion
> payloads — prompts, tool *schemas*, tool *results as text*, sampling params.
> It never runs a wavecat tool and never touches your memex/screen data. Tools
> always execute inside wavecat; this process just generates tokens.

---

## Install

```bash
pip install -e .          # from this repo (or `pip install wavecat-sdk` once published)
```

Requires Python ≥ 3.10. Pulls in `fastapi`, `uvicorn`, `httpx`.

## Run

First start your own OpenAI-compatible server, e.g.:

```bash
# llama.cpp
llama-server -m my-model.gguf --host 127.0.0.1 --port 8000 --jinja

# …or vLLM
vllm serve my-org/my-model --port 8000
```

Then run the gateway in front of it (keep it running — it should be always on):

```bash
wavecat-sdk serve --upstream http://127.0.0.1:8000/v1 --model my-model --port 8800
```

Flags (env equivalents in parentheses):

| Flag | Meaning |
|---|---|
| `--upstream`     | Your server's OpenAI root (`WAVECAT_SDK_UPSTREAM`). |
| `--upstream-key` | Bearer token your server needs, if any (`WAVECAT_SDK_KEY`). |
| `--model`        | Rewrite the inbound model id to this, so wavecat can send anything (`WAVECAT_SDK_MODEL`). |
| `--host`/`--port`| Where the gateway listens (`WAVECAT_SDK_HOST`/`_PORT`, default `127.0.0.1:8800`). |
| `--strip-keys`   | Comma-separated body keys to drop before forwarding (default `cache_prompt`). |

## Connect it in wavecat

In wavecat → **Settings → Backend**:

1. Toggle **Use a custom backend** on.
2. **Base URL**: `http://127.0.0.1:8800/v1`
3. **Model id**: whatever you passed to `--model` (or `default`).
4. **Vision-capable** — turn on only if your upstream is a vision model; otherwise
   screenshot questions stay on the local 35B.
5. **Test connection** to verify the chain, then **Save**.

Your backend serves the interactive work (chat, agent, code). The background
memory (memex) always stays on the local model, so you don't need to worry about
grammar / structured-output support.

If the gateway/upstream is ever unreachable, wavecat silently falls back to the
local 35B, so turns never hard-fail.

## Notes on compatibility

- **chat & code** modes use native OpenAI **tool-calling** (`tools=`), so your
  upstream must support tool calls for those. **agent** (deep-think) mode works
  on any chat-completions model.
- wavecat sends `chat_template_kwargs.enable_thinking` to toggle reasoning and
  `cache_prompt` for fresh context. The gateway drops `cache_prompt` by default;
  add `chat_template_kwargs` to `--strip-keys` if your server rejects it.

More plugins and skill add-on stuff coming soon.
