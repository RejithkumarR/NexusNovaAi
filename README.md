# NOVA

**Neural Omni-modal Virtual Assistant** — a provider-neutral general-purpose AI platform for chat, vision, audio, video, image generation, coding, agents, tools, and memory.

> NOVA 0.1 is an orchestration foundation. It intentionally separates the API, routing, model providers, and future agent/tool runtimes so individual models can be upgraded without rewriting the platform.

## Architecture

```text
Client
  -> NOVA API
      -> Capability Router
          -> Chat / Vision / Audio / Video / Image / Code
              -> Model Provider
                  -> Tools / Agents / Sandbox
```

## Current foundation

- FastAPI service with `/health` and `/v1/chat`
- Provider-neutral `NovaModel` interface
- Local deterministic `EchoModel` for smoke tests
- Multimodal capability router
- Pytest coverage for routing and orchestration
- Docker image
- GitHub Actions CI
- Optional ML dependencies for PyTorch + Transformers

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn apps.api.main:app --reload
```

Then open `http://127.0.0.1:8000/docs`.

## Roadmap

1. Replace the local provider with a configurable open-weight LLM.
2. Add vision, audio, and video provider adapters.
3. Add image and video generation adapters.
4. Build the NOVA Code agent with an isolated execution sandbox.
5. Add tool calling, web research, RAG, and long-term memory.
6. Add evaluation datasets and model fine-tuning.
7. Move toward a unified omni-modal NOVA model.

## Project principles

- Open interfaces over vendor lock-in
- Safe sandboxing for generated code
- Reproducible evaluation before model changes
- Modular inference so capabilities can scale independently
- API compatibility as the platform evolves
