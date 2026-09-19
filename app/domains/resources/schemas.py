from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domains.resources.enums import (
    ResourceStatus,
    ResourceType,
)


class ResourceCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=240,
    )

    resource_type: ResourceType

    status: ResourceStatus = (
        ResourceStatus.SAVED
    )

    url: str | None = Field(
        default=None,
        max_length=2048,
    )

    local_path: str | None = Field(
        default=None,
        max_length=1024,
    )

    author: str | None = Field(
        default=None,
        max_length=240,
    )

    description: str | None = None

    progress_percent: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class ResourceUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=240,
    )

    resource_type: ResourceType | None = None

    status: ResourceStatus | None = None

    url: str | None = Field(
        default=None,
        max_length=2048,
    )

    local_path: str | None = Field(
        default=None,
        max_length=1024,
    )

    author: str | None = Field(
        default=None,
        max_length=240,
    )

    description: str | None = None

    progress_percent: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    metadata: dict[str, Any] | None = None


class ResourceRead(BaseModel):
    id: UUID

    title: str
    resource_type: ResourceType
    status: ResourceStatus

    url: str | None
    local_path: str | None
    author: str | None

    description: str | None

    progress_percent: int

    metadata: dict[str, Any]

    completed_at: datetime | None

    created_at: datetime
    updated_at: datetime


class ResourceListResponse(BaseModel):
    data: list[ResourceRead]


class ResourceLinkedSkillRead(BaseModel):
    id: UUID
    name: str
    slug: str
    category: str | None
    current_level: int
    target_level: int


class ResourceLinkedSkillListResponse(BaseModel):
    data: list[ResourceLinkedSkillRead]