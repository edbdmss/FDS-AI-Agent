from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FDS_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "FDS AI Agent"
    environment: str = "development"
    model_run_id: str = "20261119T073653Z-1d0e70df"
    database_url: SecretStr | None = None
    groq_api_key: SecretStr | None = None
    llm_model: str = "openai/gpt-oss-120b"


@lru_cache
def get_settings() -> Settings:
    return Settings()
