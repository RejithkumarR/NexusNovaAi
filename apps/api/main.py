from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from nova.code_agent import DockerCodeSandbox
from nova.config import get_settings
from nova.local_model import LocalTransformerModel
from nova.models import EchoModel, NovaModel
from nova.orchestrator import NovaOrchestrator
from nova.router import RequestContext

app = FastAPI(title="NOVA API", version="0.2.0")
settings = get_settings()

# CI/development remains dependency-light when no local checkpoint is configured.
# Production/self-hosted deployments should always set NOVA_MODEL_PATH.
model: NovaModel = LocalTransformerModel() if settings.model_path else EchoModel()
orchestrator = NovaOrchestrator(model)
sandbox = DockerCodeSandbox()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    max_new_tokens: int | None = Field(default=None, ge=1, le=4096)
    temperature: float | None = Field(default=None, ge=0, le=2)


class CodeRunRequest(BaseModel):
    language: str = "python"
    code: str = Field(min_length=1, max_length=100_000)


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "nova-api",
        "model": model.name,
        "self_hosted_model": isinstance(model, LocalTransformerModel),
    }


@app.post("/v1/chat")
def chat(request: ChatRequest):
    try:
        result = orchestrator.run(
            RequestContext(text=request.message),
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "text": result.text,
        "capability": result.capability,
        "model": result.model,
        "metadata": result.metadata,
    }


@app.post("/v1/code/run")
def run_code(request: CodeRunRequest):
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
