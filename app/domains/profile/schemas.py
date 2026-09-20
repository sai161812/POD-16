from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(
        default=None,
        max_length=120,
    )

    timezone: str | None = Field(
        default=None,
        max_length=64,
    )

    locale: str | None = Field(
        default=None,
        max_length=32,
    )

    about: str | None = None

    preferences: dict[str, Any] | None = None

    metadata: dict[str, Any] | None = None

    @field_validator("timezone")
    @classmethod
    def valid_timezone(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return value

        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError:
            raise ValueError(
                "Invalid IANA timezone."
            )

        return value


class ProfileRead(BaseModel):
    display_name: str | None

    timezone: str
    locale: str

    about: str | None

    preferences: dict[str, Any]
    metadata: dict[str, Any]

    created_at: datetime
    updated_at: datetime