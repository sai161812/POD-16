from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.domains.goals.model import Goal
from app.domains.notes.model import Note
from app.domains.projects.model import Project
from app.domains.tasks.model import Task


class SearchRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def projects(
        self,
        query: str,
        limit: int,
    ) -> list[Project]:
        pattern = f"%{query}%"

        stmt = (
            select(Project)
            .where(
                Project.deleted_at.is_(None),
                or_(
                    Project.name.ilike(pattern),
                    Project.slug.ilike(pattern),
                    Project.description.ilike(pattern),
                ),
            )
            .order_by(
                Project.updated_at.desc()
            )
            .limit(limit)
        )

        return list(self.db.scalars(stmt))

    def tasks(
        self,
        query: str,
        limit: int,
    ) -> list[Task]:
        pattern = f"%{query}%"

        stmt = (
            select(Task)
            .where(
                Task.deleted_at.is_(None),
                or_(
                    Task.title.ilike(pattern),
                    Task.description.ilike(pattern),
                ),
            )
            .order_by(
                Task.updated_at.desc()
            )
            .limit(limit)
        )

        return list(self.db.scalars(stmt))

    def notes(
        self,
        query: str,
        limit: int,
    ) -> list[Note]:
        pattern = f"%{query}%"

        stmt = (
            select(Note)
            .where(
                Note.deleted_at.is_(None),
                or_(
                    Note.title.ilike(pattern),
                    Note.content.ilike(pattern),
                ),
            )
            .order_by(
                Note.updated_at.desc()
            )
            .limit(limit)
        )

        return list(self.db.scalars(stmt))

    def goals(
        self,
        query: str,
        limit: int,
    ) -> list[Goal]:
        pattern = f"%{query}%"

        stmt = (
            select(Goal)
            .where(
                Goal.deleted_at.is_(None),
                or_(
                    Goal.title.ilike(pattern),
                    Goal.description.ilike(pattern),
                ),
            )
            .order_by(
                Goal.updated_at.desc()
            )
            .limit(limit)
        )

        return list(self.db.scalars(stmt))