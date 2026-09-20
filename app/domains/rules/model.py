from datetime import datetime
from uuid import UUID, uuid7

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID as PGUUID,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domains.rules.enums import (
    RuleDomain,
    RuleMatchMode,
)


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    domain: Mapped[RuleDomain] = mapped_column(
        Enum(
            RuleDomain,
            name="rule_domain",
            values_callable=lambda enum: [
                item.value for item in enum
            ],
        ),
        nullable=False,
        index=True,
    )

    match_mode: Mapped[
        RuleMatchMode
    ] = mapped_column(
        Enum(
            RuleMatchMode,
            name="rule_match_mode",
            values_callable=lambda enum: [
                item.value for item in enum
            ],
        ),
        nullable=False,
        default=RuleMatchMode.ALL,
    )

    conditions: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
    )

    effects: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
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

    deleted_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )