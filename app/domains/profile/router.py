from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domains.profile.schemas import (
    ProfileRead,
    ProfileUpdate,
)
from app.domains.profile.service import (
    ProfileService,
)

router = APIRouter()

Db = Annotated[
    Session,
    Depends(get_db),
]


def to_read(
    profile,
) -> ProfileRead:
    return ProfileRead(
        display_name=profile.display_name,
        timezone=profile.timezone,
        locale=profile.locale,
        about=profile.about,
        preferences=profile.preferences,
        metadata=profile.extra_metadata,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get(
    "",
    response_model=ProfileRead,
)
def get_profile(
    db: Db,
) -> ProfileRead:
    return to_read(
        ProfileService(db).get()
    )


@router.patch(
    "",
    response_model=ProfileRead,
)
def update_profile(
    payload: ProfileUpdate,
    db: Db,
) -> ProfileRead:
    return to_read(
        ProfileService(db).update(
            payload
        )
    )