from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ActivityRead(BaseModel):
    id: UUID

    actor_client_id: UUID | None
    actor_name: str

    domain: str
    method: str
    operation: str
    path: str

    entity_id: UUID | None

    path_params: dict

    request_id: str | None

    created_at: datetime


class ActivityListResponse(BaseModel):
    data: list[ActivityRead]