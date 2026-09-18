from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domains.search.schemas import (
    SearchResponse,
)
from app.domains.search.service import (
    SearchService,
)


router = APIRouter()

Db = Annotated[
    Session,
    Depends(get_db),
]


@router.get(
    "",
    response_model=SearchResponse,
)
def search(
    db: Db,
    q: Annotated[
        str,
        Query(
            min_length=1,
            max_length=100,
        ),
    ],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
        ),
    ] = 25,
) -> SearchResponse:
    return SearchResponse(
        **SearchService(db).search(
            query=q,
            limit=limit,
        )
    )