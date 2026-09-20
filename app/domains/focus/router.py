from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domains.focus.schemas import (
    FocusRead,
)
from app.domains.focus.service import (
    FocusService,
)

router = APIRouter()

Db = Annotated[
    Session,
    Depends(get_db),
]


@router.get(
    "",
    response_model=FocusRead,
)
def get_focus(
    db: Db,
) -> FocusRead:
    return FocusRead(
        **FocusService(db).get()
    )