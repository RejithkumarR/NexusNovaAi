from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class NovaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NOVA_", env_file=".env", extra="ignore")

    model_path: str | None = None
    device: str = "auto"
    max_new_tokens: int = 512
    temperature: float = 0.7
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str | None = None
    ollama_timeout_seconds: int = 120
    vector_db_url: str | None = None
    vector_db_api_key: str | None = None
    vector_db_timeout_seconds: int = 10
    auth_username: str = "admin"
    auth_password: str = "change-me"
    auth_secret: str = "change-this-secret"
    auth_token_ttl_minutes: int = 720
    datasets_dir: str = "datasets/uploads"
    training_model_name: str | None = None
    training_output_dir: str = "artifacts/nova-adapter"
    training_epochs: float = 1.0
    code_timeout_seconds: int = 10
    code_memory_mb: int = 256
    code_cpu_limit: float = 1.0
    code_sandbox_image: str = "nova-code-sandbox:latest"


@lru_cache(maxsize=1)
def get_settings() -> NovaSettings:
    return NovaSettings()
