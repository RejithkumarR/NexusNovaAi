# NOVA

**Neural Omni-modal Virtual Assistant** — a self-hosted general-purpose AI platform for chat, vision, audio, video, image generation, coding, agents, tools, and memory.

> NOVA 0.3 adds a local Ollama inference path, vector-search RAG hook, self-hosted API login, training endpoints, and a redesigned Flutter client.

## Architecture

```text
Flutter Mobile
    -> NOVA API
        -> Authentication
        -> Capability Router
        -> Ollama -> local NOVA model
        -> Vector DB -> retrieval context -> Ollama
        -> Training worker -> NOVA adapter/checkpoint
        -> Code Sandbox
```

NOVA does not require OpenAI, Gemini, Claude, Groq, or another hosted AI inference provider. Ollama is used only as a local model runtime on infrastructure you control.

## Ollama setup

Install and run Ollama on the same server/network as the NOVA API, then make sure your local model is available to Ollama. Configure:

```bash
NOVA_OLLAMA_BASE_URL=http://127.0.0.1:11434
NOVA_OLLAMA_MODEL=nova
NOVA_OLLAMA_TIMEOUT_SECONDS=120
```

The model name is an Ollama tag, so replace `nova` with the tag you actually use. NOVA calls Ollama's local HTTP API; no cloud AI key is required.

## Vector database / RAG

The API now has a provider-neutral vector-store adapter. Configure:

```bash
NOVA_VECTOR_DB_URL=http://127.0.0.1:YOUR_VECTOR_DB_PORT
NOVA_VECTOR_DB_API_KEY=
```

The current adapter expects a small NOVA-compatible endpoint: `POST /search` with `{"query":"...","limit":5}` and a response containing `results` with `text`, `score`, and optional `metadata`. This keeps the core NOVA API independent of the vector database vendor.

**Before production, set the adapter to the exact vector database you use.** Qdrant, Chroma, Weaviate, Milvus, pgvector, etc. have different APIs; the exact integration should be implemented once the database name/version is known.

When RAG is enabled in the mobile chat screen, NOVA retrieves relevant private context first and then sends the augmented prompt to the local Ollama model.

## Mobile application

The Flutter client now has:

- polished NOVA login screen with self-hosted branding
- secure bearer-token session storage
- dedicated Chat screen
- optional private Knowledge/RAG toggle
- dedicated Teach NOVA training screen
- CSV/XLSX/Markdown upload
- JSONL preparation
- one-tap training job launch
- sign-out
- dark, Material 3 visual design

Run it with your API URL:

```bash
flutter pub get
flutter run --dart-define=NOVA_API_URL=http://10.0.2.2:8000
```

For a physical Android device, replace `10.0.2.2` with the reachable LAN address of the NOVA API server.

## Self-hosted login

Configure these server-side values and change them before deployment:

```bash
NOVA_AUTH_USERNAME=admin
NOVA_AUTH_PASSWORD=change-me
NOVA_AUTH_SECRET=change-this-secret
NOVA_AUTH_TOKEN_TTL_MINUTES=720
```

This release provides a single-account self-hosted access gate. A multi-user database-backed identity system can be added later without changing the mobile navigation.

## Training

Training is separate from inference. Ollama serves the model; the training worker uses the existing TRL/PEFT pipeline. Configure a local/Hugging Face-compatible training checkpoint:

```bash
NOVA_TRAINING_MODEL_NAME=/models/base-model
NOVA_TRAINING_OUTPUT_DIR=artifacts/nova-adapter
NOVA_TRAINING_EPOCHS=1
```

The mobile flow is:

```text
Upload data -> Prepare JSONL -> Start training -> Adapter/checkpoint
```

After training, the resulting model/adaptor must be exported/deployed in a format supported by your Ollama model workflow before the newly trained model is served.

## Code sandbox

Build the local sandbox image:

```bash
docker build -t nova-code-sandbox:latest infra/code-sandbox
```

Python execution uses a disposable container with no network, dropped capabilities, a read-only filesystem, resource limits, and a timeout.

## Run the API

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn apps.api.main:app --reload
```

Then open `http://127.0.0.1:8000/docs`.

For the optional direct Transformers runtime, install the ML extra and configure `NOVA_MODEL_PATH`. Ollama remains the preferred inference path when `NOVA_OLLAMA_MODEL` is configured.

## Project principles

- self-hosted inference and no mandatory third-party AI APIs
- private RAG and data ownership
- open interfaces over vendor lock-in
- safe sandboxing for generated code
- reproducible evaluation before model changes
- modular inference so capabilities can scale independently
- API compatibility as the platform evolves
