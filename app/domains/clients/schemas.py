from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


ALLOWED_SCOPES = {
    "projects:read",
    "projects:write",
    "tasks:read",
    "tasks:write",
    "notes:read",
    "notes:write",
    "goals:read",
    "goals:write",
    "focus:read",
    "search:read",
    "clients:manage",
    "profile:read",
    "profile:write",
    "skills:read",
    "skills:write",
    "resources:read",
    "resources:write",
    "activity:read",
    "rules:read",
    "rules:write",
    "*",
}


class ClientCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=120,
    )

    scopes: list[str] = Field(
        min_length=1,
    )

    @field_validator("scopes")
    @classmethod
    def validate_scopes(
        cls,
        value: list[str],
    ) -> list[str]:
        unknown = set(value) - ALLOWED_SCOPES

        if unknown:
            raise ValueError(
                "Unknown scopes: "
                + ", ".join(sorted(unknown))
            )

        return sorted(set(value))


class ClientRead(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    scopes: list[str]

    last_used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class ClientCreateResponse(ClientRead):
    api_key: str


class ClientListResponse(BaseModel):
    data: list[ClientRead]