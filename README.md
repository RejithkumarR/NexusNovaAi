# NOVA

**Neural Omni-modal Virtual Assistant** — a self-hosted general-purpose AI platform for chat, vision, audio, video, image generation, coding, agents, tools, and memory.

> NOVA 0.2 adds the first real self-hosted model runtime and an isolated code execution path. No hosted AI inference provider is required.

## Architecture

```text
Client
  -> NOVA API
      -> Capability Router
          -> NOVA Local Model / Multimodal Providers
              -> Tools / Agents / Code Sandbox
```

## Current foundation

- FastAPI service with `/health` and `/v1/chat`
- Provider-neutral `NovaModel` interface
- Self-hosted Transformers runtime loading a local checkpoint only
- Local deterministic `EchoModel` for dependency-light CI smoke tests
- Multimodal capability router
- `/v1/code/run` for Python execution inside a networkless Docker sandbox
- Pytest coverage for routing, local-model configuration, and sandbox contracts
- Optional ML dependencies for PyTorch + Transformers
- GitHub Actions CI

## Self-hosted model

Production NOVA deployments must point `NOVA_MODEL_PATH` at a model directory already present on the server. The runtime uses `local_files_only=True`, so it does not call a hosted model inference API or silently download model weights.

Install the ML runtime:

```bash
pip install -e '.[ml]'
```

Configure the model:

```bash
# Linux/macOS
export NOVA_MODEL_PATH=/models/nova

# Windows PowerShell
$env:NOVA_MODEL_PATH='D:\models\nova'
```

The checkpoint should contain the tokenizer and model files expected by Hugging Face Transformers. Chat-capable tokenizers should include their chat template; NOVA uses it when available.

## Code agent sandbox

Build the local sandbox image:

```bash
docker build -t nova-code-sandbox:latest infra/code-sandbox
```

The API currently enables Python only. Execution uses a disposable container with no network, dropped Linux capabilities, a read-only filesystem, PID/memory/CPU limits, and a timeout.

Example request:

```json
{
  "language": "python",
  "code": "print('hello NOVA')"
}
```

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn apps.api.main:app --reload
```

Then open `http://127.0.0.1:8000/docs`.

For actual local-model inference, install the ML extra and set `NOVA_MODEL_PATH` before starting the API.

## Roadmap

1. Add local vision, audio, video, and image-generation runtimes.
2. Connect the NOVA Code agent to model tool-calling without automatically executing untrusted output.
3. Add tool calling, RAG, web research, and long-term memory.
4. Add evaluation datasets and repeatable model fine-tuning.
5. Train NOVA-specific adapters/checkpoints from the project dataset pipeline.
6. Move toward a unified omni-modal NOVA model trained and served on NOVA infrastructure.

## Project principles

- Self-hosted inference and no mandatory third-party AI APIs
- Open interfaces over vendor lock-in
- Safe sandboxing for generated code
- Reproducible evaluation before model changes
- Modular inference so capabilities can scale independently
- API compatibility as the platform evolves
