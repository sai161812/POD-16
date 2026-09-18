from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.domains.goals.enums import GoalStatus
from app.domains.projects.enums import (
    ProjectPriority,
    ProjectStatus,
)
from app.domains.tasks.enums import (
    TaskPriority,
    TaskStatus,
)


class FocusProjectRead(BaseModel):
    id: UUID
    name: str
    slug: str

    status: ProjectStatus
    priority: ProjectPriority

    focus_rank: int
    progress_percent: int | None

    target_date: date | None


class FocusBlockerRead(BaseModel):
    id: UUID
    title: str
    status: TaskStatus

    deleted: bool


class FocusTaskRead(BaseModel):
    id: UUID
    title: str

    status: TaskStatus
    priority: TaskPriority

    project_id: UUID | None

    due_date: date | None
    due_at: datetime | None
    scheduled_for: datetime | None

    is_today: bool
    is_overdue: bool
    is_blocked: bool

    blocked_by: list[FocusBlockerRead]


class FocusGoalRead(BaseModel):
    id: UUID
    title: str

    status: GoalStatus
    progress_percent: int

    target_date: date | None


class FocusSummaryRead(BaseModel):
    focus_projects: int
    attention_tasks: int
    today_tasks: int
    overdue_tasks: int
    blocked_tasks: int
    active_goals: int


class FocusRead(BaseModel):
    generated_at: datetime

    summary: FocusSummaryRead

    projects: list[FocusProjectRead]
    tasks: list[FocusTaskRead]
    goals: list[FocusGoalRead]