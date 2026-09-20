from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.domains.goals.model import Goal
from app.domains.projects.model import Project
from app.domains.resources.model import Resource
from app.domains.rules.enums import (
    RuleDomain,
)
from app.domains.skills.model import Skill
from app.domains.tasks.enums import (
    TaskStatus,
)
from app.domains.tasks.model import Task
from app.domains.tasks.service import (
    TaskService,
)
from app.domains.tasks.time import (
    local_day_bounds,
    now_local,
    today_local,
)


def _date_value(value):
    if value is None:
        return None

    return value.isoformat()


class FactBuilder:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def build(
        self,
        domain: RuleDomain,
        entity_id: UUID,
    ) -> dict:
        if domain == RuleDomain.TASK:
            return self._task(
                entity_id
            )

        if domain == RuleDomain.PROJECT:
            return self._project(
                entity_id
            )

        if domain == RuleDomain.GOAL:
            return self._goal(
                entity_id
            )

        if domain == RuleDomain.RESOURCE:
            return self._resource(
                entity_id
            )

        if domain == RuleDomain.SKILL:
            return self._skill(
                entity_id
            )

        raise AppError(
            code="unsupported_rule_domain",
            message="Unsupported rule domain.",
            status_code=422,
        )

    def _not_found(
        self,
        domain: RuleDomain,
        entity_id: UUID,
    ):
        raise AppError(
            code="rule_target_not_found",
            message="Rule target not found.",
            status_code=404,
            details={
                "domain": domain.value,
                "entity_id": str(
                    entity_id
                ),
            },
        )

    def _task(
        self,
        entity_id: UUID,
    ) -> dict:
        stmt = select(Task).where(
            Task.id == entity_id,
            Task.deleted_at.is_(None),
        )

        task = self.db.scalar(stmt)

        if task is None:
            self._not_found(
                RuleDomain.TASK,
                entity_id,
            )

        now = now_local()
        today = today_local()

        start, end = (
            local_day_bounds()
        )

        active = task.status not in {
            TaskStatus.COMPLETED,
            TaskStatus.CANCELLED,
        }

        is_overdue = (
            active
            and (
                (
                    task.due_date
                    is not None
                    and task.due_date
                    < today
                )
                or (
                    task.due_at
                    is not None
                    and task.due_at
                    < now
                )
            )
        )

        is_today = (
            active
            and (
                task.due_date
                == today
                or (
                    task.due_at
                    is not None
                    and start
                    <= task.due_at
                    < end
                )
                or (
                    task.scheduled_for
                    is not None
                    and start
                    <= task.scheduled_for
                    < end
                )
            )
        )

        state = TaskService(
            self.db
        ).get_state(
            task.id
        )

        return {
            "title": task.title,
            "status": task.status.value,
            "priority": task.priority.value,
            "project_id": (
                str(task.project_id)
                if task.project_id
                else None
            ),
            "estimated_minutes": (
                task.estimated_minutes
            ),
            "due_date": _date_value(
                task.due_date
            ),
            "due_at": _date_value(
                task.due_at
            ),
            "is_overdue": is_overdue,
            "is_today": is_today,
            "is_blocked": state[
                "is_blocked"
            ],
        }

    def _project(
        self,
        entity_id: UUID,
    ) -> dict:
        stmt = select(Project).where(
            Project.id == entity_id,
            Project.deleted_at.is_(None),
        )

        project = self.db.scalar(stmt)

        if project is None:
            self._not_found(
                RuleDomain.PROJECT,
                entity_id,
            )

        return {
            "name": project.name,
            "status": project.status.value,
            "priority": (
                project.priority.value
            ),
            "focus_rank": (
                project.focus_rank
            ),
            "progress_percent": (
                project.progress_percent
            ),
            "target_date": _date_value(
                project.target_date
            ),
        }

    def _goal(
        self,
        entity_id: UUID,
    ) -> dict:
        stmt = select(Goal).where(
            Goal.id == entity_id,
            Goal.deleted_at.is_(None),
        )

        goal = self.db.scalar(stmt)

        if goal is None:
            self._not_found(
                RuleDomain.GOAL,
                entity_id,
            )

        return {
            "title": goal.title,
            "status": goal.status.value,
            "progress_percent": (
                goal.progress_percent
            ),
            "target_date": _date_value(
                goal.target_date
            ),
        }

    def _resource(
        self,
        entity_id: UUID,
    ) -> dict:
        stmt = select(Resource).where(
            Resource.id == entity_id,
            Resource.deleted_at.is_(None),
        )

        resource = self.db.scalar(stmt)

        if resource is None:
            self._not_found(
                RuleDomain.RESOURCE,
                entity_id,
            )

        return {
            "title": resource.title,
            "resource_type": (
                resource.resource_type.value
            ),
            "status": (
                resource.status.value
            ),
            "author": resource.author,
            "progress_percent": (
                resource.progress_percent
            ),
        }

    def _skill(
        self,
        entity_id: UUID,
    ) -> dict:
        stmt = select(Skill).where(
            Skill.id == entity_id,
            Skill.deleted_at.is_(None),
        )

        skill = self.db.scalar(stmt)

        if skill is None:
            self._not_found(
                RuleDomain.SKILL,
                entity_id,
            )

        return {
            "name": skill.name,
            "category": skill.category,
            "current_level": (
                skill.current_level
            ),
            "target_level": (
                skill.target_level
            ),
            "level_gap": max(
                skill.target_level
                - skill.current_level,
                0,
            ),
            "target_date": _date_value(
                skill.target_date
            ),
        }