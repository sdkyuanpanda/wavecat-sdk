# Configuration

The gateway is configured with CLI flags, environment variables, or both. **CLI
flags override the `WAVECAT_SDK_*` environment defaults.**

| Flag | Env var | Default | Meaning |
|---|---|---|---|
| `--upstream` | `WAVECAT_SDK_UPSTREAM` | `http://127.0.0.1:8000/v1` | Your model server's OpenAI root. |
| `--upstream-key` | `WAVECAT_SDK_KEY` | *(none)* | Bearer token your server expects, if any. |
| `--model` | `WAVECAT_SDK_MODEL` | *(passthrough)* | Rewrite the inbound `model` id to this, so wavecat can send anything. |
| `--host` | `WAVECAT_SDK_HOST` | `127.0.0.1` | Host the gateway listens on. |
| `--port` | `WAVECAT_SDK_PORT` | `8800` | Port the gateway listens on. |
| `--strip-keys` | `WAVECAT_SDK_STRIP_KEYS` | `cache_prompt` | Comma-separated request-body keys to drop before forwarding. |
| *(n/a)* | `WAVECAT_SDK_TIMEOUT` | `600` | Per-request upstream timeout, in seconds. |

## Why `--strip-keys`?

wavecat sends a few llama.cpp-flavored extras (e.g. `cache_prompt`) that a
stricter OpenAI server such as vLLM may reject with a `400`. The gateway drops
the configured keys before forwarding. `chat_template_kwargs` is left intact by
default (both llama.cpp and vLLM accept it) — add it to `--strip-keys` if your
server rejects it:

```bash
wavecat-sdk serve --upstream http://127.0.0.1:8000/v1 \
  --strip-keys "cache_prompt,chat_template_kwargs"
```

## Environment-only example

```bash
export WAVECAT_SDK_UPSTREAM=http://gpu-box:8000/v1
export WAVECAT_SDK_KEY=sk-your-token
export WAVECAT_SDK_MODEL=my-model
wavecat-sdk serve
```

## Programmatic use

`create_app` returns a standard FastAPI app you can run with any ASGI server, or
mount inside a larger application:

```python
import uvicorn
from wavecat_sdk import Settings, create_app

settings = Settings(
    upstream_url="http://127.0.0.1:8000/v1",
    model="my-model",
    port=8800,
)
app = create_app(settings)

if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port)
```

See the [API reference](reference.md) for the full `Settings` surface.
