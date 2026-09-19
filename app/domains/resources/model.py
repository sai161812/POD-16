from datetime import datetime
from typing import Any
from uuid import UUID, uuid7

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID as PGUUID,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domains.resources.enums import (
    ResourceStatus,
    ResourceType,
)


class Resource(Base):
    __tablename__ = "resources"

    __table_args__ = (
        CheckConstraint(
            "progress_percent >= 0 "
            "AND progress_percent <= 100",
            name="progress_percent",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    title: Mapped[str] = mapped_column(
        String(240),
        nullable=False,
    )

    resource_type: Mapped[ResourceType] = mapped_column(
        Enum(
            ResourceType,
            name="resource_type",
            values_callable=lambda enum: [
                item.value for item in enum
            ],
        ),
        nullable=False,
        index=True,
    )

    status: Mapped[ResourceStatus] = mapped_column(
        Enum(
            ResourceStatus,
            name="resource_status",
            values_callable=lambda enum: [
                item.value for item in enum
            ],
        ),
        nullable=False,
        default=ResourceStatus.SAVED,
        index=True,
    )

    url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    local_path: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    author: Mapped[str | None] = mapped_column(
        String(240),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    progress_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    extra_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        onupdate=lambda: datetime.now().astimezone(),
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )


class ResourceSkill(Base):
    __tablename__ = "resource_skills"

    resource_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "resources.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    skill_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "skills.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )