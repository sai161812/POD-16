from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domains.attention.schemas import (
    AttentionRead,
)
from app.domains.attention.service import (
    AttentionService,
)
from app.domains.rules.enums import (
    RuleDomain,
)


router = APIRouter()

Db = Annotated[
    Session,
    Depends(get_db),
]


@router.get(
    "",
    response_model=AttentionRead,
)
def get_attention(
    db: Db,
    domain: RuleDomain | None = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=200,
        ),
    ] = 50,
) -> AttentionRead:
    return AttentionRead(
        **AttentionService(
            db
        ).get(
            domain=domain,
            limit=limit,
        )
    )