from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.clients.model import ApiClient


class ApiClientRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(
        self,
        client_id: UUID,
    ) -> ApiClient | None:
        return self.db.get(
            ApiClient,
            client_id,
        )

    def get_by_token_hash(
        self,
        token_hash: str,
    ) -> ApiClient | None:
        stmt = select(ApiClient).where(
            ApiClient.token_hash == token_hash
        )

        return self.db.scalar(stmt)

    def list(self) -> list[ApiClient]:
        stmt = select(ApiClient).order_by(
            ApiClient.created_at.desc()
        )

        return list(
            self.db.scalars(stmt)
        )

    def add(
        self,
        client: ApiClient,
    ) -> ApiClient:
        self.db.add(client)
        self.db.flush()
        self.db.refresh(client)

        return client