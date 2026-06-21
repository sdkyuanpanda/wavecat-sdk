# Quickstart

## 1. Install

```bash
pip install wavecat-sdk
```

Or from a clone of the repo:

```bash
pip install -e .
```

Requires Python ≥ 3.10. Pulls in `fastapi`, `uvicorn`, and `httpx`.

## 2. Start your own OpenAI-compatible server

Bring any server that speaks the OpenAI API, for example:

```bash
# llama.cpp
llama-server -m my-model.gguf --host 127.0.0.1 --port 8000 --jinja

# …or vLLM
vllm serve my-org/my-model --port 8000
```

## 3. Run the gateway in front of it

Keep it running — it should be always on:

```bash
wavecat-sdk serve --upstream http://127.0.0.1:8000/v1 --model my-model --port 8800
```

You should see:

```text
[wavecat-sdk] gateway on http://127.0.0.1:8800/v1 → upstream http://127.0.0.1:8000/v1 (as model 'my-model')
```

Verify the whole chain:

```bash
curl http://127.0.0.1:8800/health
curl http://127.0.0.1:8800/v1/models
```

## 4. Connect it in wavecat

In wavecat → **Settings → Backend**:

1. Toggle **Use a custom backend** on.
2. **Base URL**: `http://127.0.0.1:8800/v1`
3. **Model id**: whatever you passed to `--model` (or `default`).
4. **Vision-capable** — turn on only if your upstream is a vision model; otherwise
   screenshot questions stay on the local 35B.
5. **Test connection** to verify the chain, then **Save**.

Your backend serves the interactive work (chat, agent, code). Background memory
management always stays on the local model, since that requires special grammar
and other protocols. If the gateway/upstream is ever unreachable, wavecat
silently falls back to the local 35B, so turns never hard-fail.

## Compatibility notes

- **chat & code** modes use native OpenAI **tool-calling** (`tools=`), so your
  upstream must support tool calls for those. **agent** (deep-think) mode works
  on any chat-completions model.
- wavecat sends `chat_template_kwargs.enable_thinking` to toggle reasoning and
  `cache_prompt` for fresh context. The gateway drops `cache_prompt` by default;
  add `chat_template_kwargs` to `--strip-keys` if your server rejects it.
