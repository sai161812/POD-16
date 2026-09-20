import re
from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)

SLUG_RE = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
)


class SkillCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=160,
    )

    slug: str = Field(
        min_length=1,
        max_length=180,
    )

    category: str | None = Field(
        default=None,
        max_length=120,
    )

    current_level: int = Field(
        default=0,
        ge=0,
        le=5,
    )

    target_level: int = Field(
        default=5,
        ge=0,
        le=5,
    )

    target_date: date | None = None

    notes: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator("slug")
    @classmethod
    def valid_slug(
        cls,
        value: str,
    ) -> str:
        if not SLUG_RE.fullmatch(value):
            raise ValueError(
                "slug must contain lowercase letters, "
                "numbers, and single hyphens"
            )

        return value

    @model_validator(mode="after")
    def valid_levels(self):
        if self.target_level < self.current_level:
            raise ValueError(
                "target_level cannot be below current_level"
            )

        return self


class SkillUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=160,
    )

    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=180,
    )

    category: str | None = Field(
        default=None,
        max_length=120,
    )

    current_level: int | None = Field(
        default=None,
        ge=0,
        le=5,
    )

    target_level: int | None = Field(
        default=None,
        ge=0,
        le=5,
    )

    target_date: date | None = None
    notes: str | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("slug")
    @classmethod
    def valid_slug(
        cls,
        value: str | None,
    ) -> str | None:
        if (
            value is not None
            and not SLUG_RE.fullmatch(value)
        ):
            raise ValueError(
                "slug must contain lowercase letters, "
                "numbers, and single hyphens"
            )

        return value


class SkillRead(BaseModel):
    id: UUID
    name: str
    slug: str
    category: str | None

    current_level: int
    target_level: int

    target_date: date | None
    notes: str | None

    metadata: dict[str, Any]

    created_at: datetime
    updated_at: datetime


class SkillListResponse(BaseModel):
    data: list[SkillRead]


class LearningSessionCreate(BaseModel):
    logged_at: datetime | None = None

    minutes: int = Field(
        gt=0,
        le=1440,
    )

    summary: str | None = None

    source: str | None = Field(
        default=None,
        max_length=200,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class LearningSessionRead(BaseModel):
    id: UUID
    skill_id: UUID

    logged_at: datetime
    minutes: int

    summary: str | None
    source: str | None

    metadata: dict[str, Any]

    created_at: datetime


class LearningSessionListResponse(BaseModel):
    data: list[LearningSessionRead]


class SkillProgressRead(BaseModel):
    skill_id: UUID

    current_level: int
    target_level: int
    level_gap: int

    session_count: int
    total_minutes: int

    last_logged_at: datetime | None