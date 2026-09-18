from datetime import date, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.domains.tasks.enums import TaskPriority, TaskStatus
from app.domains.tasks.model import Task, TaskDependency


class TaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, task_id: UUID) -> Task | None:
        stmt = select(Task).where(
            Task.id == task_id,
            Task.deleted_at.is_(None),
        )

        return self.db.scalar(stmt)

    def get_deleted(self, task_id: UUID) -> Task | None:
        stmt = select(Task).where(
            Task.id == task_id,
            Task.deleted_at.is_not(None),
        )

        return self.db.scalar(stmt)

    def list(
        self,
        *,
        limit: int = 50,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        project_id: UUID | None = None,
        parent_task_id: UUID | None = None,
        q: str | None = None,
    ) -> list[Task]:
        stmt = select(Task).where(
            Task.deleted_at.is_(None)
        )

        if status is not None:
            stmt = stmt.where(
                Task.status == status
            )

        if priority is not None:
            stmt = stmt.where(
                Task.priority == priority
            )

        if project_id is not None:
            stmt = stmt.where(
                Task.project_id == project_id
            )

        if parent_task_id is not None:
            stmt = stmt.where(
                Task.parent_task_id == parent_task_id
            )

        if q:
            pattern = f"%{q}%"

            stmt = stmt.where(
                or_(
                    Task.title.ilike(pattern),
                    Task.description.ilike(pattern),
                )
            )

        stmt = (
            stmt
            .order_by(
                Task.position.asc().nullslast(),
                Task.created_at.desc(),
                Task.id.desc(),
            )
            .limit(limit)
        )

        return list(self.db.scalars(stmt))

    def today(
        self,
        *,
        today: date,
        start: datetime,
        end: datetime,
    ) -> list[Task]:
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
                or_(
                    Task.due_date == today,
                    (
                        (Task.due_at >= start)
                        & (Task.due_at < end)
                    ),
                    (
                        (Task.scheduled_for >= start)
                        & (Task.scheduled_for < end)
                    ),
                ),
            )
            .order_by(
                Task.priority.desc(),
                Task.due_at.asc().nullslast(),
                Task.position.asc().nullslast(),
                Task.created_at.asc(),
            )
        )

        return list(self.db.scalars(stmt))

    def get_dependencies(
        self,
        task_id: UUID,
    ) -> list[Task]:
        stmt = (
            select(Task)
            .join(
                TaskDependency,
                Task.id == TaskDependency.depends_on_task_id,
            )
            .where(
                TaskDependency.task_id == task_id,
            )
            .order_by(Task.created_at.asc())
        )

        return list(self.db.scalars(stmt))


    def add_dependency(
        self,
        *,
        task_id: UUID,
        depends_on_task_id: UUID,
    ) -> TaskDependency:
        dependency = TaskDependency(
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
        )

        self.db.add(dependency)
        self.db.flush()

        return dependency


    def remove_dependency(
        self,
        *,

        task_id: UUID,
        depends_on_task_id: UUID,
    ) -> bool:
        dependency = self.db.get(
            TaskDependency,
            (task_id, depends_on_task_id),
        )

        if dependency is None:
            return False

        self.db.delete(dependency)
        self.db.flush()

        return True

    def overdue(
        self,
        *,
        today: date,
        now: datetime,
    ) -> list[Task]:
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
                or_(
                    Task.due_date < today,
                    Task.due_at < now,
                ),
            )
            .order_by(
                Task.due_date.asc().nullslast(),
                Task.due_at.asc().nullslast(),
                Task.priority.desc(),
            )
        )

        return list(self.db.scalars(stmt))

    def upcoming(
        self,
        *,
        today: date,
        now: datetime,
        end: datetime,
    ) -> list[Task]:
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
                or_(
                    (
                        (Task.due_date > today)
                        & (Task.due_date <= end.date())
                    ),
                    (
                        (Task.due_at > now)
                        & (Task.due_at <= end)
                    ),
                    (
                        (Task.scheduled_for > now)
                        & (Task.scheduled_for <= end)
                    ),
                ),
            )
            .order_by(
                Task.due_date.asc().nullslast(),
                Task.due_at.asc().nullslast(),
                Task.scheduled_for.asc().nullslast(),
            )
        )

        return list(self.db.scalars(stmt))

    def add(self, task: Task) -> Task:
        self.db.add(task)
        self.db.flush()
        self.db.refresh(task)

        return task