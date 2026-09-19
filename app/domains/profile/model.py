from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PersonalProfile(Base):
    __tablename__ = "personal_profile"

    __table_args__ = (
        CheckConstraint(
            "singleton_key = 1",
            name="singleton",
        ),
    )

    singleton_key: Mapped[int] = mapped_column(
        SmallInteger,
        primary_key=True,
        default=1,
    )

    display_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="Asia/Kolkata",
    )

    locale: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="en-IN",
    )

    about: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    preferences: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
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