from datetime import datetime
from typing import Any
from uuid import UUID, uuid7

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID as PGUUID,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    title: Mapped[str] = mapped_column(
        String(240),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    project_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "projects.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    extra_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
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