from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.query import contains_pattern
from app.domains.goals.enums import GoalStatus
from app.domains.goals.model import Goal, GoalProject
from app.domains.projects.model import Project


class GoalRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(
        self,
        goal_id: UUID,
    ) -> Goal | None:
        stmt = select(Goal).where(
            Goal.id == goal_id,
            Goal.deleted_at.is_(None),
        )

        return self.db.scalar(stmt)

    def get_deleted(
        self,
        goal_id: UUID,
    ) -> Goal | None:
        stmt = select(Goal).where(
            Goal.id == goal_id,
            Goal.deleted_at.is_not(None),
        )

        return self.db.scalar(stmt)

    def list(
        self,
        *,
        limit: int,
        offset: int,
        status: GoalStatus | None,
        q: str | None,
    ) -> list[Goal]:
        stmt = select(Goal).where(
            Goal.deleted_at.is_(None)
        )

        if status is not None:
            stmt = stmt.where(
                Goal.status == status
            )

        if q:
            pattern = contains_pattern(q)

            stmt = stmt.where(
                or_(
                    Goal.title.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Goal.description.ilike(
                        pattern,
                        escape="\\",
                    ),
                )
            )

        stmt = (
            stmt
            .order_by(
                Goal.updated_at.desc(),
                Goal.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt)
        )

    def add(
        self,
        goal: Goal,
    ) -> Goal:
        self.db.add(goal)
        self.db.flush()
        self.db.refresh(goal)

        return goal

    def get_projects(
        self,
        goal_id: UUID,
    ) -> list[Project]:
        stmt = (
            select(Project)
            .join(
                GoalProject,
                GoalProject.project_id == Project.id,
           )
            .where(
                GoalProject.goal_id == goal_id,
                Project.deleted_at.is_(None),
           )
            .order_by(
                Project.focus_rank.asc().nullslast(),
                Project.created_at.desc(),
            )
        )

        return list(self.db.scalars(stmt))


    def project_link_exists(
        self,
        *,
        goal_id: UUID,
        project_id: UUID,
    ) -> bool:
        link = self.db.get(
            GoalProject,
            (goal_id, project_id),
        )

        return link is not None


    def add_project_link(
        self,
        *,
        goal_id: UUID,
        project_id: UUID,
    ) -> GoalProject:
        link = GoalProject(
            goal_id=goal_id,
            project_id=project_id,
        )

        self.db.add(link)
        self.db.flush()

        return link


    def remove_project_link(
        self,
        *,
        goal_id: UUID,
        project_id: UUID,
    ) -> bool:
        link = self.db.get(
            GoalProject,
            (goal_id, project_id),
        )

        if link is None:
            return False

        self.db.delete(link)
        self.db.flush()

        return True