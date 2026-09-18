from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domains.goals.enums import GoalStatus
from app.domains.projects.enums import (
    ProjectPriority,
    ProjectStatus,
)


class GoalCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=240,
    )

    description: str | None = None

    status: GoalStatus = GoalStatus.ACTIVE

    progress_percent: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    target_date: date | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class GoalUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=240,
    )

    description: str | None = None

    status: GoalStatus | None = None

    progress_percent: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    target_date: date | None = None

    metadata: dict[str, Any] | None = None


class GoalRead(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: GoalStatus
    progress_percent: int
    target_date: date | None
    metadata: dict[str, Any]
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class GoalListResponse(BaseModel):
    data: list[GoalRead]    

class GoalLinkedProjectRead(BaseModel):
    id: UUID
    name: str
    slug: str
    status: ProjectStatus
    priority: ProjectPriority
    focus_rank: int | None
    progress_percent: int | None
    target_date: date | None


class GoalLinkedProjectListResponse(BaseModel):
    data: list[GoalLinkedProjectRead]