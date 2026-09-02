from dataclasses import dataclass
from typing import Any


@dataclass
class NovaResponse:
    text: str
    capability: str
    model: str
    metadata: dict[str, Any]


class NovaModel:
    """Provider-neutral model interface used by the NOVA orchestrator."""

    name = "base"

    def generate(self, prompt: str, **kwargs: Any) -> NovaResponse:
        raise NotImplementedError


class EchoModel(NovaModel):
    """Deterministic local provider for development and API smoke tests."""

    name = "echo"

    def generate(self, prompt: str, **kwargs: Any) -> NovaResponse:
        return NovaResponse(
            text=f"NOVA development response: {prompt}",
            capability="chat",
            model=self.name,
            metadata={"provider": "local"},
        )
