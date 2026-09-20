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
from app.domains.resources.enums import (
    ResourceStatus,
    ResourceType,
)
from app.domains.resources.schemas import (
    ResourceCreate,
    ResourceLinkedSkillListResponse,
    ResourceLinkedSkillRead,
    ResourceListResponse,
    ResourceRead,
    ResourceUpdate,
)
from app.domains.resources.service import (
    ResourceService,
)

router = APIRouter()

Db = Annotated[
    Session,
    Depends(get_db),
]


def to_read(resource) -> ResourceRead:
    return ResourceRead(
        id=resource.id,
        title=resource.title,
        resource_type=resource.resource_type,
        status=resource.status,
        url=resource.url,
        local_path=resource.local_path,
        author=resource.author,
        description=resource.description,
        progress_percent=(
            resource.progress_percent
        ),
        metadata=resource.extra_metadata,
        completed_at=resource.completed_at,
        created_at=resource.created_at,
        updated_at=resource.updated_at,
    )


@router.post(
    "",
    response_model=ResourceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_resource(
    payload: ResourceCreate,
    db: Db,
) -> ResourceRead:
    return to_read(
        ResourceService(db).create(
            payload
        )
    )


@router.get(
    "",
    response_model=ResourceListResponse,
)
def list_resources(
    db: Db,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    resource_type: ResourceType | None = None,
    status_filter: Annotated[
        ResourceStatus | None,
        Query(alias="status"),
    ] = None,
    q: str | None = None,
) -> ResourceListResponse:
    resources = ResourceService(
        db
    ).list(
        limit=limit,
        offset=offset,
        resource_type=resource_type,
        status=status_filter,
        q=q,
    )

    return ResourceListResponse(
        data=[
            to_read(resource)
            for resource in resources
        ]
    )


@router.get(
    "/{resource_id}",
    response_model=ResourceRead,
)
def get_resource(
    resource_id: UUID,
    db: Db,
) -> ResourceRead:
    return to_read(
        ResourceService(db).get(
            resource_id
        )
    )


@router.patch(
    "/{resource_id}",
    response_model=ResourceRead,
)
def update_resource(
    resource_id: UUID,
    payload: ResourceUpdate,
    db: Db,
) -> ResourceRead:
    return to_read(
        ResourceService(db).update(
            resource_id,
            payload,
        )
    )


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_resource(
    resource_id: UUID,
    db: Db,
) -> Response:
    ResourceService(db).delete(
        resource_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/{resource_id}/restore",
    response_model=ResourceRead,
)
def restore_resource(
    resource_id: UUID,
    db: Db,
) -> ResourceRead:
    return to_read(
        ResourceService(db).restore(
            resource_id
        )
    )


@router.get(
    "/{resource_id}/skills",
    response_model=ResourceLinkedSkillListResponse,
)
def get_resource_skills(
    resource_id: UUID,
    db: Db,
) -> ResourceLinkedSkillListResponse:
    skills = ResourceService(
        db
    ).get_skills(
        resource_id
    )

    return ResourceLinkedSkillListResponse(
        data=[
            ResourceLinkedSkillRead(
                id=skill.id,
                name=skill.name,
                slug=skill.slug,
                category=skill.category,
                current_level=(
                    skill.current_level
                ),
                target_level=(
                    skill.target_level
                ),
            )
            for skill in skills
        ]
    )


@router.post(
    "/{resource_id}/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def link_resource_skill(
    resource_id: UUID,
    skill_id: UUID,
    db: Db,
) -> Response:
    ResourceService(db).link_skill(
        resource_id=resource_id,
        skill_id=skill_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.delete(
    "/{resource_id}/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlink_resource_skill(
    resource_id: UUID,
    skill_id: UUID,
    db: Db,
) -> Response:
    ResourceService(db).unlink_skill(
        resource_id=resource_id,
        skill_id=skill_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )