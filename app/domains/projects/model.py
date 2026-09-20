from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid7

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domains.projects.enums import ProjectPriority, ProjectStatus


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint(
            "progress_percent IS NULL OR (progress_percent >= 0 AND progress_percent <= 100)",
            name="progress_percent_range",
        ),
        CheckConstraint(
            "focus_rank IS NULL OR focus_rank >= 1",
            name="focus_rank_positive",
        ),
        CheckConstraint(
            "parent_project_id IS NULL OR parent_project_id <> id",
            name="parent_not_self",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid7
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"),
        nullable=False,
        default=ProjectStatus.PLANNED,
        index=True,
    )
    priority: Mapped[ProjectPriority] = mapped_column(
        Enum(ProjectPriority, name="project_priority"),
        nullable=False,
        default=ProjectPriority.NORMAL,
        index=True,
    )

    focus_rank: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, index=True)
    progress_percent: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    started_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    parent_project_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
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
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
