from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "POD-16"
    env: str = "development"
    database_url: str = "postgresql+psycopg://pod16:pod16@localhost:5432/pod16"
    bootstrap_api_key: str = "change-me-before-deployment"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="POD16_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
