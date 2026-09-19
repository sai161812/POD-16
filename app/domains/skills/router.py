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
from app.domains.skills.schemas import (
    LearningSessionCreate,
    LearningSessionListResponse,
    LearningSessionRead,
    SkillCreate,
    SkillListResponse,
    SkillProgressRead,
    SkillRead,
    SkillUpdate,
)
from app.domains.skills.service import (
    SkillService,
)


router = APIRouter()

Db = Annotated[
    Session,
    Depends(get_db),
]


def to_read(skill) -> SkillRead:
    return SkillRead(
        id=skill.id,
        name=skill.name,
        slug=skill.slug,
        category=skill.category,
        current_level=skill.current_level,
        target_level=skill.target_level,
        target_date=skill.target_date,
        notes=skill.notes,
        metadata=skill.extra_metadata,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
    )


def session_to_read(
    session,
) -> LearningSessionRead:
    return LearningSessionRead(
        id=session.id,
        skill_id=session.skill_id,
        logged_at=session.logged_at,
        minutes=session.minutes,
        summary=session.summary,
        source=session.source,
        metadata=session.extra_metadata,
        created_at=session.created_at,
    )


@router.post(
    "",
    response_model=SkillRead,
    status_code=status.HTTP_201_CREATED,
)
def create_skill(
    payload: SkillCreate,
    db: Db,
) -> SkillRead:
    return to_read(
        SkillService(db).create(
            payload
        )
    )


@router.get(
    "",
    response_model=SkillListResponse,
)
def list_skills(
    db: Db,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 50,
    category: str | None = None,
    q: str | None = None,
) -> SkillListResponse:
    skills = SkillService(db).list(
        limit=limit,
        category=category,
        q=q,
    )

    return SkillListResponse(
        data=[
            to_read(skill)
            for skill in skills
        ]
    )


@router.get(
    "/{skill_id}",
    response_model=SkillRead,
)
def get_skill(
    skill_id: UUID,
    db: Db,
) -> SkillRead:
    return to_read(
        SkillService(db).get(
            skill_id
        )
    )


@router.patch(
    "/{skill_id}",
    response_model=SkillRead,
)
def update_skill(
    skill_id: UUID,
    payload: SkillUpdate,
    db: Db,
) -> SkillRead:
    return to_read(
        SkillService(db).update(
            skill_id,
            payload,
        )
    )


@router.delete(
    "/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_skill(
    skill_id: UUID,
    db: Db,
) -> Response:
    SkillService(db).delete(
        skill_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/{skill_id}/restore",
    response_model=SkillRead,
)
def restore_skill(
    skill_id: UUID,
    db: Db,
) -> SkillRead:
    return to_read(
        SkillService(db).restore(
            skill_id
        )
    )


@router.post(
    "/{skill_id}/sessions",
    response_model=LearningSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def log_learning_session(
    skill_id: UUID,
    payload: LearningSessionCreate,
    db: Db,
) -> LearningSessionRead:
    session = (
        SkillService(db).log_session(
            skill_id,
            payload,
        )
    )

    return session_to_read(
        session
    )


@router.get(
    "/{skill_id}/sessions",
    response_model=LearningSessionListResponse,
)
def list_learning_sessions(
    skill_id: UUID,
    db: Db,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 50,
) -> LearningSessionListResponse:
    sessions = (
        SkillService(db).sessions(
            skill_id,
            limit=limit,
        )
    )

    return LearningSessionListResponse(
        data=[
            session_to_read(session)
            for session in sessions
        ]
    )


@router.get(
    "/{skill_id}/progress",
    response_model=SkillProgressRead,
)
def get_skill_progress(
    skill_id: UUID,
    db: Db,
) -> SkillProgressRead:
    return SkillProgressRead(
        **SkillService(db).progress(
            skill_id
        )
    )