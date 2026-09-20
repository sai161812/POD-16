from datetime import date, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, aliased

from app.domains.goals.enums import GoalStatus
from app.domains.goals.model import (
    Goal,
    GoalProject,
)
from app.domains.projects.enums import ProjectStatus
from app.domains.projects.model import Project
from app.domains.tasks.enums import TaskStatus
from app.domains.tasks.model import (
    Task,
    TaskDependency,
)


class FocusRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def projects(self) -> list[Project]:
        stmt = (
            select(Project)
            .where(
                Project.deleted_at.is_(None),
                Project.focus_rank.is_not(None),
                Project.status.in_(
                    [
                        ProjectStatus.PLANNED,
                        ProjectStatus.ACTIVE,
                    ]
                ),
            )
            .order_by(
                Project.focus_rank.asc(),
                Project.priority.desc(),
            )
        )

        return list(self.db.scalars(stmt))

    def tasks(
        self,
        *,
        project_ids: list[UUID],
        today: date,
        start: datetime,
        end: datetime,
    ) -> list[Task]:
        attention_conditions = [
            Task.due_date <= today,
            (
                Task.due_at < end
            ),
            (
                (Task.scheduled_for >= start)
                & (Task.scheduled_for < end)
            ),
        ]

        if project_ids:
            attention_conditions.append(
                Task.project_id.in_(project_ids)
            )

        stmt = (
            select(Task)
            .where(
                Task.deleted_at.is_(None),
                Task.status.notin_(
                    [
                        TaskStatus.COMPLETED,
                        TaskStatus.CANCELLED,
                    ]
                ),
                or_(*attention_conditions),
            )
            .order_by(
                Task.priority.desc(),
                Task.due_date.asc().nullslast(),
                Task.due_at.asc().nullslast(),
                Task.scheduled_for.asc().nullslast(),
                Task.created_at.asc(),
            )
            .limit(50)
        )

        return list(self.db.scalars(stmt))

    def goals(
        self,
        project_ids: list[UUID],
    ) -> list[Goal]:
        if not project_ids:
            return []

        stmt = (
            select(Goal)
            .join(
                GoalProject,
                GoalProject.goal_id == Goal.id,
            )
            .where(
                Goal.deleted_at.is_(None),
                Goal.status == GoalStatus.ACTIVE,
                GoalProject.project_id.in_(
                    project_ids
                ),
            )
            .distinct()
            .order_by(
                Goal.target_date.asc().nullslast(),
                Goal.created_at.asc(),
            )
        )

        return list(self.db.scalars(stmt))

    def blockers(
        self,
        task_ids: list[UUID],
    ):
        if not task_ids:
            return []

        prerequisite = aliased(Task)

        stmt = (
            select(
                TaskDependency.task_id,
                prerequisite.id.label(
                    "dependency_id"
                ),
                prerequisite.title.label(
                    "dependency_title"
                ),
                prerequisite.status.label(
                    "dependency_status"
                ),
                prerequisite.deleted_at.label(
                    "dependency_deleted_at"
                ),
            )
            .join(
                prerequisite,
                prerequisite.id
                == TaskDependency.depends_on_task_id,
            )
            .where(
                TaskDependency.task_id.in_(
                    task_ids
                ),
                prerequisite.status
                != TaskStatus.COMPLETED,
            )
        )

        return self.db.execute(stmt).all()