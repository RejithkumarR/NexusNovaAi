from __future__ import annotations

from typing import Any

import httpx

from nova.config import get_settings
from nova.models import NovaModel, NovaResponse


class OllamaModel(NovaModel):
    """NOVA model served by a local Ollama instance."""

    name = "ollama"

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_seconds

    def generate(self, prompt: str, **kwargs: Any) -> NovaResponse:
        if not self.model:
            raise RuntimeError("NOVA_OLLAMA_MODEL is not configured")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature") if kwargs.get("temperature") is not None else get_settings().temperature,
                "num_predict": kwargs.get("max_new_tokens") if kwargs.get("max_new_tokens") is not None else get_settings().max_new_tokens,
            },
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Unable to reach local Ollama at {self.base_url}: {exc}") from exc

        data = response.json()
        return NovaResponse(
            text=str(data.get("response", "")).strip(),
            capability="chat",
            model=self.model,
            metadata={"provider": "ollama", "self_hosted": True},
        )

    def health(self) -> bool:
        try:
            with httpx.Client(timeout=5) as client:
                response = client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False
