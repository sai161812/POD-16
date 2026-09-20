from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.projects.model import Project


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, project_id: UUID) -> Project | None:
        stmt = select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
        return self.db.scalar(stmt)

    def get_deleted(
        self,
        project_id: UUID,
    ) -> Project | None:
        stmt = select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_not(None),
      )

        return self.db.scalar(stmt)

    def get_by_slug(self, slug: str) -> Project | None:
        stmt = select(Project).where(
            Project.slug == slug,
            Project.deleted_at.is_(None),
        )
        return self.db.scalar(stmt)

    def list(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Project]:
        stmt = (
            select(Project)
           .where(
               Project.deleted_at.is_(None)
           )
            .order_by(
                Project.focus_rank.asc().nullslast(),
                Project.created_at.desc(),
                Project.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt)
        )

    def add(self, project: Project) -> Project:
        self.db.add(project)
        self.db.flush()
        self.db.refresh(project)
        return project
