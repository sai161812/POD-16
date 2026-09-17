from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.domains.projects.repository import ProjectRepository
from app.domains.tasks.enums import (
    TaskPriority,
    TaskStatus,
)
from app.domains.tasks.model import Task
from app.domains.tasks.repository import TaskRepository
from app.domains.tasks.schemas import (
    TaskCreate,
    TaskUpdate,
)
from app.domains.tasks.time import (
    local_day_bounds,
    now_local,
    today_local,
)


class TaskService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TaskRepository(db)
        self.projects = ProjectRepository(db)

    def _validate_project(
        self,
        project_id: UUID | None,
    ) -> None:
        if project_id is None:
            return

        if self.projects.get(project_id) is None:
            raise AppError(
                code="project_not_found",
                message="Project not found.",
                status_code=422,
                details={
                    "project_id": str(project_id),
                },
            )

    def _validate_parent_task(
        self,
        *,
        task_id: UUID | None,
        parent_task_id: UUID | None,
    ) -> None:
        if parent_task_id is None:
            return

        parent = self.repo.get(parent_task_id)

        if parent is None:
            raise AppError(
                code="parent_task_not_found",
                message="Parent task not found.",
                status_code=422,
                details={
                    "parent_task_id": str(parent_task_id),
                },
            )

        if task_id is None:
            return

        if task_id == parent_task_id:
            raise AppError(
                code="invalid_parent_task",
                message="A task cannot be its own parent.",
                status_code=422,
            )

        visited: set[UUID] = set()
        current = parent

        while current is not None:
            if current.id == task_id:
                raise AppError(
                    code="task_parent_cycle",
                    message="This parent assignment would create a task cycle.",
                    status_code=422,
                )

            if current.id in visited:
                raise AppError(
                    code="task_parent_cycle",
                    message="The task hierarchy already contains a cycle.",
                    status_code=422,
                )

            visited.add(current.id)

            if current.parent_task_id is None:
                break

            current = self.repo.get(
                current.parent_task_id
            )

    def create(
        self,
        payload: TaskCreate,
    ) -> Task:
        self._validate_project(
            payload.project_id
        )

        self._validate_parent_task(
            task_id=None,
            parent_task_id=payload.parent_task_id,
        )

        values = payload.model_dump()

        values["extra_metadata"] = values.pop(
            "metadata"
        )

        task = Task(**values)

        if task.status == TaskStatus.COMPLETED:
            task.completed_at = now_local()

        self.repo.add(task)

        self.db.commit()

        self.db.refresh(task)

        return task

    def get(
        self,
        task_id: UUID,
    ) -> Task:
        task = self.repo.get(task_id)

        if task is None:
            raise AppError(
                code="task_not_found",
                message="Task not found.",
                status_code=404,
                details={
                    "task_id": str(task_id),
                },
            )

        return task

    def list(
        self,
        *,
        limit: int,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        project_id: UUID | None,
        parent_task_id: UUID | None,
        q: str | None,
    ) -> list[Task]:
        return self.repo.list(
            limit=limit,
            status=status,
            priority=priority,
            project_id=project_id,
            parent_task_id=parent_task_id,
            q=q,
        )

    def today(self) -> list[Task]:
        start, end = local_day_bounds()

        return self.repo.today(
            today=today_local(),
            start=start,
            end=end,
        )

    def overdue(self) -> list[Task]:
        now = now_local()

        return self.repo.overdue(
            today=now.date(),
            now=now,
        )

    def upcoming(
        self,
        days: int,
    ) -> list[Task]:
        now = now_local()

        end = now + timedelta(
            days=days
        )

        return self.repo.upcoming(
            today=now.date(),
            now=now,
            end=end,
        )

    def update(
        self,
        task_id: UUID,
        payload: TaskUpdate,
    ) -> Task:
        task = self.get(task_id)

        changes = payload.model_dump(
            exclude_unset=True
        )

        if "project_id" in changes:
            self._validate_project(
                changes["project_id"]
            )

        if "parent_task_id" in changes:
            self._validate_parent_task(
                task_id=task.id,
                parent_task_id=changes[
                    "parent_task_id"
                ],
            )

        if (
            "due_date" in changes
            and changes["due_date"] is not None
        ):
            task.due_at = None

        if (
            "due_at" in changes
            and changes["due_at"] is not None
        ):
            task.due_date = None

        if "metadata" in changes:
            changes["extra_metadata"] = (
                changes.pop("metadata")
            )

        previous_status = task.status

        for field, value in changes.items():
            setattr(task, field, value)

        if (
            task.status == TaskStatus.COMPLETED
            and previous_status
            != TaskStatus.COMPLETED
        ):
            task.completed_at = now_local()

        elif (
            previous_status
            == TaskStatus.COMPLETED
            and task.status
            != TaskStatus.COMPLETED
        ):
            task.completed_at = None

        self.db.commit()

        self.db.refresh(task)

        return task

    def delete(
        self,
        task_id: UUID,
    ) -> None:
        task = self.get(task_id)

        task.deleted_at = now_local()

        self.db.commit()

    def restore(
        self,
        task_id: UUID,
    ) -> Task:
        task = self.repo.get_deleted(
            task_id
        )

        if task is None:
            raise AppError(
                code="deleted_task_not_found",
                message="Deleted task not found.",
                status_code=404,
                details={
                    "task_id": str(task_id),
                },
            )

        task.deleted_at = None

        self.db.commit()

        self.db.refresh(task)

        return task