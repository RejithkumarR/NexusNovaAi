from nova.auth import issue_token, verify_token
from nova.config import get_settings
from nova.ollama_model import OllamaModel
from nova.vector_store import HttpVectorStore


def test_auth_token_round_trip():
    assert verify_token(issue_token("admin")) == "admin"


def test_ollama_model_posts_to_local_runtime(monkeypatch):
    monkeypatch.setenv("NOVA_OLLAMA_BASE_URL", "http://ollama.test")
    monkeypatch.setenv("NOVA_OLLAMA_MODEL", "nova-test")
    get_settings.cache_clear()

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": "hello from NOVA"}

    class Client:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.last = None

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, json):
            self.last = (url, json)
            return Response()

    monkeypatch.setattr("nova.ollama_model.httpx.Client", Client)
    result = OllamaModel().generate("hello", max_new_tokens=32, temperature=0.2)
    assert result.text == "hello from NOVA"
    assert result.metadata["provider"] == "ollama"
    get_settings.cache_clear()


def test_vector_store_without_url_is_disabled(monkeypatch):
    monkeypatch.delenv("NOVA_VECTOR_DB_URL", raising=False)
    get_settings.cache_clear()
    assert HttpVectorStore().search("hello") == []
    get_settings.cache_clear()
