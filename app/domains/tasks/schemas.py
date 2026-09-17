from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.tasks.enums import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)

    description: str | None = None

    status: TaskStatus = TaskStatus.TODO

    priority: TaskPriority = TaskPriority.NORMAL

    project_id: UUID | None = None

    parent_task_id: UUID | None = None

    due_date: date | None = None

    due_at: datetime | None = None

    scheduled_for: datetime | None = None

    estimated_minutes: int | None = Field(
        default=None,
        gt=0,
    )

    position: int | None = Field(
        default=None,
        ge=0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @model_validator(mode="after")
    def validate_due_mode(self):
        if self.due_date is not None and self.due_at is not None:
            raise ValueError(
                "Use either due_date or due_at, not both."
            )

        return self


class TaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=240,
    )

    description: str | None = None

    status: TaskStatus | None = None

    priority: TaskPriority | None = None

    project_id: UUID | None = None

    parent_task_id: UUID | None = None

    due_date: date | None = None

    due_at: datetime | None = None

    scheduled_for: datetime | None = None

    estimated_minutes: int | None = Field(
        default=None,
        gt=0,
    )

    position: int | None = Field(
        default=None,
        ge=0,
    )

    metadata: dict[str, Any] | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    title: str

    description: str | None

    status: TaskStatus

    priority: TaskPriority

    project_id: UUID | None

    parent_task_id: UUID | None

    due_date: date | None

    due_at: datetime | None

    scheduled_for: datetime | None

    estimated_minutes: int | None

    position: int | None

    metadata: dict[str, Any]

    completed_at: datetime | None

    created_at: datetime

    updated_at: datetime


class TaskListResponse(BaseModel):
    data: list[TaskRead]