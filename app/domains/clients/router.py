from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domains.clients.schemas import (
    ClientCreate,
    ClientCreateResponse,
    ClientListResponse,
    ClientRead,
)
from app.domains.clients.service import (
    ApiClientService,
)


router = APIRouter()

Db = Annotated[
    Session,
    Depends(get_db),
]


def to_read(client) -> ClientRead:
    return ClientRead(
        id=client.id,
        name=client.name,
        key_prefix=client.key_prefix,
        scopes=client.scopes,
        last_used_at=client.last_used_at,
        revoked_at=client.revoked_at,
        created_at=client.created_at,
    )


@router.post(
    "",
    response_model=ClientCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_client(
    payload: ClientCreate,
    db: Db,
) -> ClientCreateResponse:
    client, api_key = (
        ApiClientService(db).create(
            payload
        )
    )

    return ClientCreateResponse(
        **to_read(client).model_dump(),
        api_key=api_key,
    )


@router.get(
    "",
    response_model=ClientListResponse,
)
def list_clients(
    db: Db,
) -> ClientListResponse:
    clients = (
        ApiClientService(db).list()
    )

    return ClientListResponse(
        data=[
            to_read(client)
            for client in clients
        ]
    )


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_client(
    client_id: UUID,
    db: Db,
) -> Response:
    ApiClientService(db).revoke(
        client_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )