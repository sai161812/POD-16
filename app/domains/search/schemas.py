from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class SearchResultType(StrEnum):
    PROJECT = "project"
    TASK = "task"
    NOTE = "note"
    GOAL = "goal"
    RESOURCE = "resource"


class SearchResultRead(BaseModel):
    type: SearchResultType
    id: UUID

    title: str
    snippet: str | None

    status: str | None

    updated_at: datetime


class SearchResponse(BaseModel):
    query: str
    count: int
    data: list[SearchResultRead]