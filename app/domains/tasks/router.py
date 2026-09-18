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
from app.domains.tasks.enums import (
    TaskPriority,
    TaskStatus,
)
from app.domains.tasks.schemas import (
    TaskCreate,
    TaskListResponse,
    TaskRead,
    TaskStateRead,
    TaskUpdate,
)
from app.domains.tasks.service import TaskService


router = APIRouter()

Db = Annotated[
    Session,
    Depends(get_db),
]


def to_read(task) -> TaskRead:
    return TaskRead(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        project_id=task.project_id,
        parent_task_id=task.parent_task_id,
        due_date=task.due_date,
        due_at=task.due_at,
        scheduled_for=task.scheduled_for,
        estimated_minutes=task.estimated_minutes,
        position=task.position,
        metadata=task.extra_metadata,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def to_list_response(
    tasks,
) -> TaskListResponse:
    return TaskListResponse(
        data=[
            to_read(task)
            for task in tasks
        ]
    )


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    payload: TaskCreate,
    db: Db,
) -> TaskRead:
    return to_read(
        TaskService(db).create(payload)
    )


@router.get(
    "/today",
    response_model=TaskListResponse,
)
def today_tasks(
    db: Db,
) -> TaskListResponse:
    return to_list_response(
        TaskService(db).today()
    )


@router.get(
    "/overdue",
    response_model=TaskListResponse,
)
def overdue_tasks(
    db: Db,
) -> TaskListResponse:
    return to_list_response(
        TaskService(db).overdue()
    )


@router.get(
    "/upcoming",
    response_model=TaskListResponse,
)
def upcoming_tasks(
    db: Db,
    days: Annotated[
        int,
        Query(ge=1, le=90),
    ] = 7,
) -> TaskListResponse:
    return to_list_response(
        TaskService(db).upcoming(days)
    )


@router.get(
    "",
    response_model=TaskListResponse,
)
def list_tasks(
    db: Db,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 50,
    status_filter: Annotated[
        TaskStatus | None,
        Query(alias="status"),
    ] = None,
    priority: TaskPriority | None = None,
    project_id: UUID | None = None,
    parent_task_id: UUID | None = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
        ),
    ] = None,
) -> TaskListResponse:
    tasks = TaskService(db).list(
        limit=limit,
        status=status_filter,
        priority=priority,
        project_id=project_id,
        parent_task_id=parent_task_id,
        q=q,
    )

    return to_list_response(tasks)


@router.get(
    "/{task_id}",
    response_model=TaskRead,
)
def get_task(
    task_id: UUID,
    db: Db,
) -> TaskRead:
    return to_read(
        TaskService(db).get(task_id)
    )


@router.patch(
    "/{task_id}",
    response_model=TaskRead,
)
def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    db: Db,
) -> TaskRead:
    return to_read(
        TaskService(db).update(
            task_id,
            payload,
        )
    )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    task_id: UUID,
    db: Db,
) -> Response:
    TaskService(db).delete(task_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/{task_id}/restore",
    response_model=TaskRead,
)
def restore_task(
    task_id: UUID,
    db: Db,
) -> TaskRead:
    return to_read(
        TaskService(db).restore(task_id)
    )

@router.get(
    "/{task_id}/dependencies",
    response_model=TaskListResponse,
)
def get_task_dependencies(
    task_id: UUID,
    db: Db,
) -> TaskListResponse:
    tasks = TaskService(db).get_dependencies(
        task_id
    )

    return to_list_response(tasks)

@router.post(
    "/{task_id}/dependencies/{depends_on_task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def add_task_dependency(
    task_id: UUID,
    depends_on_task_id: UUID,
    db: Db,
) -> Response:
    TaskService(db).add_dependency(
        task_id=task_id,
        depends_on_task_id=depends_on_task_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )

@router.delete(
    "/{task_id}/dependencies/{depends_on_task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_task_dependency(
    task_id: UUID,
    depends_on_task_id: UUID,
    db: Db,
) -> Response:
    TaskService(db).remove_dependency(
        task_id=task_id,
        depends_on_task_id=depends_on_task_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )

@router.get(
    "/{task_id}/state",
    response_model=TaskStateRead,
)
def get_task_state(
    task_id: UUID,
    db: Db,
) -> TaskStateRead:
    return TaskStateRead(
        **TaskService(db).get_state(task_id)
    )