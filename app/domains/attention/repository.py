from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.goals.enums import GoalStatus
from app.domains.goals.model import Goal
from app.domains.projects.enums import (
    ProjectStatus,
)
from app.domains.projects.model import Project
from app.domains.resources.enums import (
    ResourceStatus,
)
from app.domains.resources.model import Resource
from app.domains.rules.enums import RuleDomain
from app.domains.skills.model import Skill
from app.domains.tasks.enums import TaskStatus
from app.domains.tasks.model import Task


class AttentionRepository:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def tasks(self) -> list[Task]:
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
            )
            .order_by(
                Task.updated_at.desc()
            )
        )

        return list(
            self.db.scalars(stmt)
        )

    def projects(self) -> list[Project]:
        stmt = (
            select(Project)
            .where(
                Project.deleted_at.is_(None),
                Project.status.notin_(
                    [
                        ProjectStatus.COMPLETED,
                        ProjectStatus.ABANDONED,
                    ]
                ),
            )
            .order_by(
                Project.updated_at.desc()
            )
        )

        return list(
            self.db.scalars(stmt)
        )

    def goals(self) -> list[Goal]:
        stmt = (
            select(Goal)
            .where(
                Goal.deleted_at.is_(None),
                Goal.status.notin_(
                    [
                        GoalStatus.COMPLETED,
                        GoalStatus.ABANDONED,
                    ]
                ),
            )
            .order_by(
                Goal.updated_at.desc()
            )
        )

        return list(
            self.db.scalars(stmt)
        )

    def resources(self) -> list[Resource]:
        stmt = (
            select(Resource)
            .where(
                Resource.deleted_at.is_(None),
                Resource.status.notin_(
                    [
                        ResourceStatus.COMPLETED,
                        ResourceStatus.ARCHIVED,
                    ]
                ),
            )
            .order_by(
                Resource.updated_at.desc()
            )
        )

        return list(
            self.db.scalars(stmt)
        )

    def skills(self) -> list[Skill]:
        stmt = (
            select(Skill)
            .where(
                Skill.deleted_at.is_(None)
            )
            .order_by(
                Skill.updated_at.desc()
            )
        )

        return list(
            self.db.scalars(stmt)
        )

    def candidates(
        self,
        domain: RuleDomain,
    ):
        if domain == RuleDomain.TASK:
            return self.tasks()

        if domain == RuleDomain.PROJECT:
            return self.projects()

        if domain == RuleDomain.GOAL:
            return self.goals()

        if domain == RuleDomain.RESOURCE:
            return self.resources()

        if domain == RuleDomain.SKILL:
            return self.skills()

        return []