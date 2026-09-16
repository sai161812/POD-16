import re
from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domains.projects.enums import ProjectPriority, ProjectStatus

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    slug: str = Field(min_length=1, max_length=180)
    description: str | None = None
    status: ProjectStatus = ProjectStatus.PLANNED
    priority: ProjectPriority = ProjectPriority.NORMAL
    focus_rank: int | None = Field(default=None, ge=1)
    progress_percent: int | None = Field(default=None, ge=0, le=100)
    target_date: date | None = None
    started_at: date | None = None
    parent_project_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str) -> str:
        if not SLUG_RE.fullmatch(value):
            raise ValueError("slug must contain lowercase letters, numbers, and single hyphens")
        return value


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    slug: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = None
    status: ProjectStatus | None = None
    priority: ProjectPriority | None = None
    focus_rank: int | None = Field(default=None, ge=1)
    progress_percent: int | None = Field(default=None, ge=0, le=100)
    target_date: date | None = None
    started_at: date | None = None
    parent_project_id: UUID | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str | None) -> str | None:
        if value is not None and not SLUG_RE.fullmatch(value):
            raise ValueError("slug must contain lowercase letters, numbers, and single hyphens")
        return value


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None
    status: ProjectStatus
    priority: ProjectPriority
    focus_rank: int | None
    progress_percent: int | None
    target_date: date | None
    started_at: date | None
    completed_at: datetime | None
    parent_project_id: UUID | None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    data: list[ProjectRead]
