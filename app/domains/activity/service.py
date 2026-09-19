from uuid import UUID

from sqlalchemy.orm import Session

from app.domains.activity.model import (
    ActivityEvent,
)
from app.domains.activity.repository import (
    ActivityRepository,
)


class ActivityService:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db
        self.repo = ActivityRepository(db)

    def record(
        self,
        *,
        actor_client_id: UUID | None,
        actor_name: str,
        domain: str,
        method: str,
        operation: str,
        path: str,
        entity_id: UUID | None,
        path_params: dict,
        request_id: str | None,
    ) -> ActivityEvent:
        event = ActivityEvent(
            actor_client_id=actor_client_id,
            actor_name=actor_name,
            domain=domain,
            method=method,
            operation=operation,
            path=path,
            entity_id=entity_id,
            path_params=path_params,
            request_id=request_id,
        )

        self.repo.add(event)

        return event

    def list(
        self,
        *,
        limit: int,
        domain: str | None,
        method: str | None,
        actor_client_id: UUID | None,
        entity_id: UUID | None,
    ):
        return self.repo.list(
            limit=limit,
            domain=domain,
            method=method,
            actor_client_id=actor_client_id,
            entity_id=entity_id,
        )