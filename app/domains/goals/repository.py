from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.domains.goals.enums import GoalStatus
from app.domains.goals.model import Goal


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
            pattern = f"%{q}%"

            stmt = stmt.where(
                or_(
                    Goal.title.ilike(pattern),
                    Goal.description.ilike(pattern),
                )
            )

        stmt = (
            stmt
            .order_by(
                Goal.updated_at.desc(),
                Goal.id.desc(),
            )
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