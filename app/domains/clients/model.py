from datetime import datetime
from uuid import UUID, uuid7

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import (
    ARRAY,
)
from sqlalchemy.dialects.postgresql import (
    UUID as PGUUID,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ApiClient(Base):
    __tablename__ = "api_clients"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    key_prefix: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    scopes: Mapped[list[str]] = mapped_column(
        ARRAY(String(64)),
        nullable=False,
        default=list,
    )

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )