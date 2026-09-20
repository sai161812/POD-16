from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

INSECURE_BOOTSTRAP_KEYS = {
    "change-me-before-deployment",
    "change-this-before-deployment",
}


class Settings(BaseSettings):
    app_name: str = "POD-16"

    env: Literal[
        "development",
        "test",
        "production",
    ] = "development"

    database_url: str = (
        "postgresql+psycopg://"
        "pod16:pod16@localhost:5432/pod16"
    )

    bootstrap_api_key: str = (
        "change-me-before-deployment"
    )

    log_level: str = "INFO"

    timezone: str = "Asia/Kolkata"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="POD16_",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_security(
        self,
    ):
        if self.env != "production":
            return self

        if (
            self.bootstrap_api_key
            in INSECURE_BOOTSTRAP_KEYS
        ):
            raise ValueError(
                "Production cannot use the "
                "default bootstrap API key."
            )

        if len(self.bootstrap_api_key) < 32:
            raise ValueError(
                "Production bootstrap API key "
                "must be at least 32 characters."
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()