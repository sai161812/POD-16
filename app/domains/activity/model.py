from datetime import datetime
from uuid import UUID, uuid7

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
)
from sqlalchemy.dialects.postgresql import (
    UUID as PGUUID,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    actor_client_id: Mapped[
        UUID | None
    ] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "api_clients.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    actor_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    domain: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    method: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        index=True,
    )

    operation: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )

    entity_id: Mapped[
        UUID | None
    ] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    path_params: Mapped[
        dict
    ] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    request_id: Mapped[
        str | None
    ] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        index=True,
    )