from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domains.projects.schemas import (
    ProjectCreate,
    ProjectListResponse,
    ProjectRead,
    ProjectUpdate,
)
from app.domains.projects.service import ProjectService

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]


def to_read(project) -> ProjectRead:
    return ProjectRead(
        id=project.id,
        name=project.name,
        slug=project.slug,
        description=project.description,
        status=project.status,
        priority=project.priority,
        focus_rank=project.focus_rank,
        progress_percent=project.progress_percent,
        target_date=project.target_date,
        started_at=project.started_at,
        completed_at=project.completed_at,
        parent_project_id=project.parent_project_id,
        metadata=project.extra_metadata,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Db) -> ProjectRead:
    return to_read(ProjectService(db).create(payload))


@router.get("", response_model=ProjectListResponse)
def list_projects(
    db: Db,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ProjectListResponse:
    projects = ProjectService(db).list(limit=limit)
    return ProjectListResponse(data=[to_read(project) for project in projects])


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: UUID, db: Db) -> ProjectRead:
    return to_read(ProjectService(db).get(project_id))


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: UUID, payload: ProjectUpdate, db: Db) -> ProjectRead:
    return to_read(ProjectService(db).update(project_id, payload))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, db: Db) -> Response:
    ProjectService(db).delete(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post(
    "/{project_id}/restore",
    response_model=ProjectRead,
)
def restore_project(
    project_id: UUID,
    db: Db,
) -> ProjectRead:
    return to_read(
        ProjectService(db).restore(
            project_id
        )
    )