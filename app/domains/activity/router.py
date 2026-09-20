from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domains.activity.schemas import (
    ActivityListResponse,
    ActivityRead,
)
from app.domains.activity.service import (
    ActivityService,
)


router = APIRouter()

Db = Annotated[
    Session,
    Depends(get_db),
]


def to_read(
    event,
) -> ActivityRead:
    return ActivityRead(
        id=event.id,
        actor_client_id=(
            event.actor_client_id
        ),
        actor_name=event.actor_name,
        domain=event.domain,
        method=event.method,
        operation=event.operation,
        path=event.path,
        entity_id=event.entity_id,
        path_params=event.path_params,
        request_id=event.request_id,
        created_at=event.created_at,
    )


@router.get(
    "",
    response_model=ActivityListResponse,
)
def list_activity(
    db: Db,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=200,
        ),
    ] = 50,
    offset: Annotated[
        int,
        Query(
            ge=0,
        ),
    ] = 0,
    domain: str | None = None,
    method: str | None = None,
    actor_client_id: UUID | None = None,
    entity_id: UUID | None = None,
) -> ActivityListResponse:
    events = ActivityService(
        db
    ).list(
        limit=limit,
        offset=offset,
        domain=domain,
        method=method,
        actor_client_id=actor_client_id,
        entity_id=entity_id,
    )

    return ActivityListResponse(
        data=[
            to_read(event)
            for event in events
        ]
    )