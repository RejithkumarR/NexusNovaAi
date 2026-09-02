from fastapi import FastAPI
from pydantic import BaseModel

from nova.models import EchoModel
from nova.orchestrator import NovaOrchestrator
from nova.router import RequestContext

app = FastAPI(title="NOVA API", version="0.1.0")
orchestrator = NovaOrchestrator(EchoModel())


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "nova-api"}


@app.post("/v1/chat")
def chat(request: ChatRequest):
    result = orchestrator.run(RequestContext(text=request.message))
    return {
        "text": result.text,
        "capability": result.capability,
        "model": result.model,
        "metadata": result.metadata,
    }
