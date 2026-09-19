from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.activity.model import (
    ActivityEvent,
)


class ActivityRepository:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def add(
        self,
        event: ActivityEvent,
    ) -> ActivityEvent:
        self.db.add(event)
        self.db.flush()

        return event

    def list(
        self,
        *,
        limit: int,
        domain: str | None,
        method: str | None,
        actor_client_id: UUID | None,
        entity_id: UUID | None,
    ) -> list[ActivityEvent]:
        stmt = select(
            ActivityEvent
        )

        if domain is not None:
            stmt = stmt.where(
                ActivityEvent.domain
                == domain
            )

        if method is not None:
            stmt = stmt.where(
                ActivityEvent.method
                == method.upper()
            )

        if actor_client_id is not None:
            stmt = stmt.where(
                ActivityEvent.actor_client_id
                == actor_client_id
            )

        if entity_id is not None:
            stmt = stmt.where(
                ActivityEvent.entity_id
                == entity_id
            )

        stmt = (
            stmt
            .order_by(
                ActivityEvent.created_at.desc()
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt)
        )