import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_development_allows_placeholder_key():
    settings = Settings(
        _env_file=None,
        env="development",
        bootstrap_api_key=(
            "change-me-before-deployment"
        ),
    )

    assert settings.env == "development"


def test_production_rejects_default_key():
    with pytest.raises(
        ValidationError
    ):
        Settings(
            _env_file=None,
            env="production",
            bootstrap_api_key=(
                "change-me-before-deployment"
            ),
        )


def test_production_rejects_short_key():
    with pytest.raises(
        ValidationError
    ):
        Settings(
            _env_file=None,
            env="production",
            bootstrap_api_key=(
                "short-production-key"
            ),
        )


def test_production_accepts_strong_key():
    settings = Settings(
        _env_file=None,
        env="production",
        bootstrap_api_key=(
            "pod16-production-key-"
            "0123456789abcdef0123456789"
        ),
    )

    assert settings.env == "production"