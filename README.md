# Nexus Nova AI

**Nexus Nova AI** — a self-hosted general-purpose AI platform for chat, vision, audio, video, image generation, coding, agents, tools, training, RAG and memory.

The platform is designed around user-owned infrastructure: local Ollama inference, a private vector database, a self-hosted API, and a separate training worker. No hosted AI inference provider is required.

## Branding

Official product name: **Nexus Nova AI**

Repository: **RejithkumarR/NexusNovaAi**

The supplied Nexus Nova AI logo is the canonical mobile branding asset.

## Architecture

```text
Flutter Mobile
    -> Nexus Nova AI API
        -> Authentication
        -> Capability Router
        -> Ollama -> local model
        -> Vector DB -> retrieval context -> Ollama
        -> Training worker -> adapter/checkpoint
        -> Code Sandbox
```

## Ollama

```bash
NOVA_OLLAMA_BASE_URL=http://127.0.0.1:11434
NOVA_OLLAMA_MODEL=nova
NOVA_OLLAMA_TIMEOUT_SECONDS=120
```

Replace `nova` with the Ollama tag of your local model.

## Vector DB / RAG

Configure the private vector database with `NOVA_VECTOR_DB_URL` and the optional `NOVA_VECTOR_DB_API_KEY`. The API keeps the vector-store integration provider-neutral so the native adapter can be selected for the exact database product/version.

The mobile Chat screen provides a Knowledge / RAG toggle that retrieves private context before sending the augmented prompt to Ollama.

## Mobile

The Flutter client provides Nexus Nova AI branding, persistent login, a dedicated Chat screen, Knowledge/RAG controls, and a dedicated Teach Nexus Nova AI training screen with CSV/XLSX/Markdown upload, JSONL preparation and training launch.

Run:

```bash
flutter pub get
flutter run --dart-define=NOVA_API_URL=http://10.0.2.2:8000
```

## Training

Training is separate from inference. The TRL/PEFT worker creates adapters/checkpoints; Ollama serves a deployed model. The mobile flow is:

```text
Upload data -> Prepare JSONL -> Start training -> Deploy -> Ollama chat
```

## Code sandbox

Python code execution uses the disposable networkless Docker sandbox included in the project.

## Run API

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn apps.api.main:app --reload
```

## Principles

- self-hosted inference
- private data and RAG
- no mandatory third-party AI APIs
- safe code execution
- reproducible model evaluation
- modular local inference
