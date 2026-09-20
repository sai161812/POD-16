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
        offset: int,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        project_id: UUID | None,
        parent_task_id: UUID | None,
        q: str | None,
    ) -> list[Task]:
        return self.repo.list(
            limit=limit,
            offset=offset,
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

        requested_status = changes.get(
            "status",
            task.status,
        )

        if (
            requested_status
            in {
                TaskStatus.IN_PROGRESS,
                TaskStatus.COMPLETED,
            }
            and requested_status != task.status
        ):
            self._ensure_dependencies_satisfied(
                task.id
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

        if task.status != TaskStatus.COMPLETED:
            dependents = (
                self.repo
                .get_active_dependents(
                    task_id
                )
            )

            if dependents:
                raise AppError(
                    code=(
                        "task_has_active_dependents"
                    ),
                    message=(
                        "This task cannot be "
                        "deleted while active "
                        "tasks depend on it."
                    ),
                    status_code=409,
                    details={
                        "depended_on_by": [
                            {
                                "id": str(
                                    dependent.id
                                ),
                                "title": (
                                    dependent.title
                                ),
                                "status": (
                                    dependent
                                    .status
                                    .value
                                ),
                            }
                            for dependent
                            in dependents
                        ]
                    },
                )

        task.deleted_at = now_local()

        self.db.commit()

    def _validate_dependency(
        self,
        *,
        task_id: UUID,
        depends_on_task_id: UUID,
    ) -> None:
        # Both tasks must exist.
        self.get(task_id)
        self.get(depends_on_task_id)

    # A task cannot depend on itself.
        if task_id == depends_on_task_id:
            raise AppError(
                code="invalid_task_dependency",
                message="A task cannot depend on itself.",
                status_code=422,
            )

        # Prevent duplicate dependency edges.
        existing = self.repo.get_dependencies(task_id)

        if any(
            task.id == depends_on_task_id
            for task in existing
        ):
            raise AppError(
                code="task_dependency_exists",
                message="This task dependency already exists.",
                status_code=409,
        )

    # Cycle detection:
    #
    # If B wants to depend on A, walk A's dependency tree.
    # If we eventually reach B, adding B -> A would create a loop.
        stack = [depends_on_task_id]
        visited: set[UUID] = set()

        while stack:
            current_id = stack.pop()

            if current_id == task_id:
                raise AppError(
                    code="task_dependency_cycle",
                    message="This dependency would create a cycle.",
                    status_code=422,
                )

            if current_id in visited:
                continue

            visited.add(current_id)

            dependencies = self.repo.get_dependencies(
                current_id
            )

            stack.extend(
                dependency.id
                for dependency in dependencies
            )

    def add_dependency(
        self,
        *,
        task_id: UUID,
        depends_on_task_id: UUID,
    ) -> None:
        self._validate_dependency(
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
        )

        self.repo.add_dependency(
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
        )

        self.db.commit()

    def remove_dependency(
        self,
        *,
        task_id: UUID,
        depends_on_task_id: UUID,
    ) -> None:
        self.get(task_id)

        removed = self.repo.remove_dependency(
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
        )

        if not removed:
            raise AppError(
                code="task_dependency_not_found",
                message="Task dependency not found.",
                status_code=404,
            )

        self.db.commit()

    def get_dependencies(
        self,
        task_id: UUID,
    ) -> list[Task]:
        self.get(task_id)

        return self.repo.get_dependencies(task_id)

    def _get_blocking_dependencies(
        self,
        task_id: UUID,
    ) -> list[Task]:
        dependencies = self.repo.get_dependencies(
            task_id
    )

        return [
            task
            for task in dependencies
            if task.status != TaskStatus.COMPLETED
        ]

    def _ensure_dependencies_satisfied(
        self,
        task_id: UUID,
    ) -> None:
        blockers = self._get_blocking_dependencies(
            task_id
        )

        if not blockers:
            return

        raise AppError(
            code="task_dependency_not_satisfied",
            message=(
                "This task cannot be started or completed "
                "until all dependencies are completed."
            ),
            status_code=409,
            details={
                "blocked_by": [
                    {
                        "id": str(task.id),
                        "title": task.title,
                        "status": task.status.value,
                    }
                    for task in blockers
                ]
            },
        )

    def get_state(
        self,
        task_id: UUID,
    ) -> dict:
        self.get(task_id)

        blockers = self._get_blocking_dependencies(
            task_id
        )

        return {
            "is_blocked": len(blockers) > 0,
            "blocked_by": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                }
                for task in blockers
            ],
        }