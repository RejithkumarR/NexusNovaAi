from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class NovaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NOVA_", env_file=".env", extra="ignore")

    model_path: str | None = None
    device: str = "auto"
    max_new_tokens: int = 512
    temperature: float = 0.7
    code_timeout_seconds: int = 10
    code_memory_mb: int = 256
    code_cpu_limit: float = 1.0
    code_sandbox_image: str = "nova-code-sandbox:latest"


@lru_cache(maxsize=1)
def get_settings() -> NovaSettings:
    return NovaSettings()
