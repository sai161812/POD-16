from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.domains.goals.enums import GoalStatus
from app.domains.goals.model import Goal
from app.domains.goals.repository import (
    GoalRepository,
)
from app.domains.goals.schemas import (
    GoalCreate,
    GoalUpdate,
)
from app.domains.projects.repository import (
    ProjectRepository,
)

class GoalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = GoalRepository(db)
        self.projects = ProjectRepository(db)

    def create(
        self,
        payload: GoalCreate,
    ) -> Goal:
        values = payload.model_dump()

        values["extra_metadata"] = values.pop(
            "metadata"
        )

        if (
            values["status"]
            == GoalStatus.COMPLETED
        ):
            values["progress_percent"] = 100
            values["completed_at"] = (
                datetime.now().astimezone()
            )

        goal = Goal(**values)

        self.repo.add(goal)

        self.db.commit()
        self.db.refresh(goal)

        return goal

    def get(
        self,
        goal_id: UUID,
    ) -> Goal:
        goal = self.repo.get(goal_id)

        if goal is None:
            raise AppError(
                code="goal_not_found",
                message="Goal not found.",
                status_code=404,
                details={
                    "goal_id": str(goal_id),
                },
            )

        return goal

    def list(
        self,
        *,
        limit: int,
        status: GoalStatus | None,
        q: str | None,
    ) -> list[Goal]:
        return self.repo.list(
            limit=limit,
            status=status,
            q=q,
        )

    def update(
        self,
        goal_id: UUID,
        payload: GoalUpdate,
    ) -> Goal:
        goal = self.get(goal_id)

        changes = payload.model_dump(
            exclude_unset=True
        )

        if "metadata" in changes:
            changes["extra_metadata"] = (
                changes.pop("metadata")
            )

        previous_status = goal.status

        for field, value in changes.items():
            setattr(goal, field, value)

        if (
            goal.status == GoalStatus.COMPLETED
            and previous_status
            != GoalStatus.COMPLETED
        ):
            goal.progress_percent = 100
            goal.completed_at = (
                datetime.now().astimezone()
            )

        elif (
            previous_status
            == GoalStatus.COMPLETED
            and goal.status
            != GoalStatus.COMPLETED
        ):
            goal.completed_at = None

        self.db.commit()
        self.db.refresh(goal)

        return goal

    def delete(
        self,
        goal_id: UUID,
    ) -> None:
        goal = self.get(goal_id)

        goal.deleted_at = (
            datetime.now().astimezone()
        )

        self.db.commit()

    def restore(
        self,
        goal_id: UUID,
    ) -> Goal:
        goal = self.repo.get_deleted(
            goal_id
        )

        if goal is None:
            raise AppError(
                code="deleted_goal_not_found",
                message="Deleted goal not found.",
                status_code=404,
                details={
                    "goal_id": str(goal_id),
                },
            )

        goal.deleted_at = None

        self.db.commit()
        self.db.refresh(goal)

        return goal

    def get_projects(
        self,
        goal_id: UUID,
    ):
        self.get(goal_id)

        return self.repo.get_projects(goal_id)


    def link_project(
        self,
        *,
        goal_id: UUID,
        project_id: UUID,
    ) -> None:
        self.get(goal_id)

        project = self.projects.get(project_id)

        if project is None:
            raise AppError(
                code="project_not_found",
                message="Project not found.",
                status_code=404,
                details={
                    "project_id": str(project_id),
                },
            )

        if self.repo.project_link_exists(
            goal_id=goal_id,
            project_id=project_id,
        ):
            raise AppError(
                code="goal_project_link_exists",
                message="Project is already linked to this goal.",
                status_code=409,
            )

        self.repo.add_project_link(
            goal_id=goal_id,
            project_id=project_id,
        )

        self.db.commit()


    def unlink_project(
        self,
        *,
        goal_id: UUID,
        project_id: UUID,
    ) -> None:
        self.get(goal_id)

        removed = self.repo.remove_project_link(
            goal_id=goal_id,
            project_id=project_id,
        )

        if not removed:
            raise AppError(
                code="goal_project_link_not_found",
                message="Goal-project link not found.",
                status_code=404,
            )

        self.db.commit()