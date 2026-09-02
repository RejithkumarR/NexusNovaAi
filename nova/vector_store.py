from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from nova.config import get_settings


@dataclass
class RetrievedChunk:
    text: str
    score: float = 0.0
    metadata: dict[str, Any] | None = None


class VectorStore(Protocol):
    def search(self, query: str, limit: int = 5) -> list[RetrievedChunk]: ...


class HttpVectorStore:
    """Adapter for a NOVA-compatible vector service.

    The service contract is intentionally small so the concrete database can be
    swapped without changing the mobile app or orchestrator. POST /search must
    accept {"query": str, "limit": int} and return {"results": [{"text": str,
    "score": number, "metadata": object}]}.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.url = (settings.vector_db_url or "").rstrip("/")
        self.timeout = settings.vector_db_timeout_seconds
        self.api_key = settings.vector_db_api_key

    def search(self, query: str, limit: int = 5) -> list[RetrievedChunk]:
        if not self.url:
            return []
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.url}/search", headers=headers, json={"query": query, "limit": limit})
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Vector DB request failed: {exc}") from exc
        results = response.json().get("results", [])
        return [RetrievedChunk(text=str(item.get("text", "")), score=float(item.get("score", 0)), metadata=item.get("metadata")) for item in results if item.get("text")]
