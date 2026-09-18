from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domains.goals.enums import GoalStatus
from app.domains.goals.schemas import (
    GoalCreate,
    GoalListResponse,
    GoalRead,
    GoalUpdate,
)
from app.domains.goals.service import GoalService


router = APIRouter()

Db = Annotated[
    Session,
    Depends(get_db),
]


def to_read(goal) -> GoalRead:
    return GoalRead(
        id=goal.id,
        title=goal.title,
        description=goal.description,
        status=goal.status,
        progress_percent=goal.progress_percent,
        target_date=goal.target_date,
        metadata=goal.extra_metadata,
        completed_at=goal.completed_at,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )


@router.post(
    "",
    response_model=GoalRead,
    status_code=status.HTTP_201_CREATED,
)
def create_goal(
    payload: GoalCreate,
    db: Db,
) -> GoalRead:
    return to_read(
        GoalService(db).create(payload)
    )


@router.get(
    "",
    response_model=GoalListResponse,
)
def list_goals(
    db: Db,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 50,
    status_filter: Annotated[
        GoalStatus | None,
        Query(alias="status"),
    ] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
        ),
    ] = None,
) -> GoalListResponse:
    goals = GoalService(db).list(
        limit=limit,
        status=status_filter,
        q=q,
    )

    return GoalListResponse(
        data=[
            to_read(goal)
            for goal in goals
        ]
    )


@router.get(
    "/{goal_id}",
    response_model=GoalRead,
)
def get_goal(
    goal_id: UUID,
    db: Db,
) -> GoalRead:
    return to_read(
        GoalService(db).get(goal_id)
    )


@router.patch(
    "/{goal_id}",
    response_model=GoalRead,
)
def update_goal(
    goal_id: UUID,
    payload: GoalUpdate,
    db: Db,
) -> GoalRead:
    return to_read(
        GoalService(db).update(
            goal_id,
            payload,
        )
    )


@router.delete(
    "/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_goal(
    goal_id: UUID,
    db: Db,
) -> Response:
    GoalService(db).delete(goal_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/{goal_id}/restore",
    response_model=GoalRead,
)
def restore_goal(
    goal_id: UUID,
    db: Db,
) -> GoalRead:
    return to_read(
        GoalService(db).restore(goal_id)
    )