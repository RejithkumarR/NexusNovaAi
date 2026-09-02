from __future__ import annotations

import os
import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field

from nova.auth import issue_token, verify_token
from nova.code_agent import DockerCodeSandbox
from nova.config import get_settings
from nova.dataset import DatasetIngestor, SUPPORTED
from nova.github_publisher import GitHubDatasetPublisher
from nova.models import EchoModel, NovaModel
from nova.ollama_model import OllamaModel
from nova.orchestrator import NovaOrchestrator
from nova.router import RequestContext
from nova.training import start_training
from nova.vector_store import HttpVectorStore

app = FastAPI(title="NOVA API", version="0.3.0")
settings = get_settings()

# Ollama is the preferred self-hosted inference runtime. EchoModel remains useful
# for dependency-light CI when no local model is configured.
model: NovaModel = OllamaModel() if settings.ollama_model else EchoModel()
vector_store = HttpVectorStore()
orchestrator = NovaOrchestrator(model)
sandbox = DockerCodeSandbox()


def current_user(authorization: str | None = Header(default=None)) -> str:
    token = authorization.removeprefix("Bearer ").strip() if authorization else None
    return verify_token(token)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    max_new_tokens: int | None = Field(default=None, ge=1, le=4096)
    temperature: float | None = Field(default=None, ge=0, le=2)
    use_rag: bool = True


class CodeRunRequest(BaseModel):
    language: str = "python"
    code: str = Field(min_length=1, max_length=100_000)


class TrainRequest(BaseModel):
    model_name: str | None = None
    epochs: float | None = Field(default=None, gt=0, le=100)


@app.get("/health")
def health() -> dict[str, str | bool]:
    ollama_healthy = isinstance(model, OllamaModel) and model.health()
    return {
        "status": "ok",
        "service": "nova-api",
        "model": model.name,
        "self_hosted_model": isinstance(model, OllamaModel),
        "ollama_healthy": ollama_healthy,
        "rag_configured": bool(settings.vector_db_url),
    }


@app.post("/v1/auth/login")
def login(request: LoginRequest):
    if not (secrets.compare_digest(request.username, settings.auth_username) and secrets.compare_digest(request.password, settings.auth_password)):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"access_token": issue_token(request.username), "token_type": "bearer"}


@app.post("/v1/chat")
def chat(request: ChatRequest, _: str = Depends(current_user)):
    prompt = request.message
    metadata: dict[str, object] = {"rag_used": False}
    if request.use_rag and settings.vector_db_url:
        chunks = vector_store.search(request.message, limit=5)
        if chunks:
            context = "\n\n".join(f"[{i + 1}] {chunk.text}" for i, chunk in enumerate(chunks))
            prompt = f"Use the following retrieved context when it is relevant. Do not invent facts not supported by it.\n\nContext:\n{context}\n\nUser question:\n{request.message}"
            metadata = {"rag_used": True, "retrieved_chunks": len(chunks)}
    try:
        result = orchestrator.run(
            RequestContext(text=prompt),
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "text": result.text,
        "capability": result.capability,
        "model": result.model,
        "metadata": {**result.metadata, **metadata},
    }


@app.post("/v1/datasets/upload")
async def upload_dataset(file: UploadFile = File(...), _: str = Depends(current_user)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED:
        raise HTTPException(status_code=400, detail="Supported files: .csv, .xlsx, .md")
    root = Path(settings.datasets_dir)
    root.mkdir(parents=True, exist_ok=True)
    target = root / Path(file.filename or "dataset").name
    target.write_bytes(await file.read())
    publisher = GitHubDatasetPublisher.from_environment()
    if publisher:
        publisher.publish_file(target)
    return {"status": "uploaded", "filename": target.name, "published_to_github": bool(publisher)}


@app.post("/v1/datasets/prepare")
def prepare_dataset(_: str = Depends(current_user)):
    try:
        return DatasetIngestor(Path(settings.datasets_dir)).build_jsonl()
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/train")
def train(request: TrainRequest, _: str = Depends(current_user)):
    model_name = request.model_name or settings.training_model_name or settings.model_path
    if not model_name:
        raise HTTPException(status_code=400, detail="Configure NOVA_TRAINING_MODEL_NAME or NOVA_MODEL_PATH before training")
    dataset = Path(settings.datasets_dir) / "normalized.jsonl"
    if not dataset.exists():
        raise HTTPException(status_code=400, detail="Prepare a dataset before starting training")
    try:
        return start_training(
            model_name=model_name,
            dataset_path=str(dataset),
            output_dir=settings.training_output_dir,
            num_train_epochs=request.epochs or settings.training_epochs,
        )
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/v1/code/run")
def run_code(request: CodeRunRequest, _: str = Depends(current_user)):
    if request.language.lower() != "python":
        raise HTTPException(status_code=400, detail="Only Python is enabled in this sandbox release")
    try:
        result = sandbox.run_python(request.code)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
    }
