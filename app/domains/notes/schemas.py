from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=240,
    )

    content: str = Field(
        min_length=1,
    )

    project_id: UUID | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class NoteUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=240,
    )

    content: str | None = Field(
        default=None,
        min_length=1,
    )

    project_id: UUID | None = None

    metadata: dict[str, Any] | None = None


class NoteRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    title: str
    content: str

    project_id: UUID | None

    metadata: dict[str, Any]

    created_at: datetime
    updated_at: datetime


class NoteListResponse(BaseModel):
    data: list[NoteRead]