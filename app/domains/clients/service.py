from datetime import datetime
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.domains.clients.model import ApiClient
from app.domains.clients.repository import (
    ApiClientRepository,
)
from app.domains.clients.schemas import (
    ClientCreate,
)


def hash_api_key(
    api_key: str,
) -> str:
    return sha256(
        api_key.encode("utf-8")
    ).hexdigest()


class ApiClientService:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db
        self.repo = ApiClientRepository(db)

    def create(
        self,
        payload: ClientCreate,
    ) -> tuple[ApiClient, str]:
        api_key = (
            "pod16_"
            + token_urlsafe(32)
        )

        client = ApiClient(
            name=payload.name,
            key_prefix=api_key[:18],
            token_hash=hash_api_key(
                api_key
            ),
            scopes=payload.scopes,
        )

        self.repo.add(client)

        self.db.commit()
        self.db.refresh(client)

        return client, api_key

    def list(
        self,
        *,
        limit: int,
        offset: int,
    ) -> list[ApiClient]:
        return self.repo.list(
            limit=limit,
            offset=offset,
        )
    
    def revoke(
        self,
        client_id: UUID,
    ) -> None:
        client = self.repo.get(
            client_id
        )

        if client is None:
            raise AppError(
                code="api_client_not_found",
                message="API client not found.",
                status_code=404,
            )

        if client.revoked_at is None:
            client.revoked_at = (
                datetime.now().astimezone()
            )

        self.db.commit()