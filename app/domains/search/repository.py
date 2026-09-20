from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.query import contains_pattern
from app.domains.goals.model import Goal
from app.domains.notes.model import Note
from app.domains.projects.model import Project
from app.domains.resources.model import Resource
from app.domains.skills.model import Skill
from app.domains.tasks.model import Task


class SearchRepository:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def projects(
        self,
        query: str,
        limit: int,
    ) -> list[Project]:
        pattern = contains_pattern(
            query
        )

        stmt = (
            select(Project)
            .where(
                Project.deleted_at.is_(None),
                or_(
                    Project.name.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Project.slug.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Project.description.ilike(
                        pattern,
                        escape="\\",
                    ),
                ),
            )
            .order_by(
                Project.updated_at.desc(),
                Project.id.desc(),
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt)
        )

    def tasks(
        self,
        query: str,
        limit: int,
    ) -> list[Task]:
        pattern = contains_pattern(
            query
        )

        stmt = (
            select(Task)
            .where(
                Task.deleted_at.is_(None),
                or_(
                    Task.title.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Task.description.ilike(
                        pattern,
                        escape="\\",
                    ),
                ),
            )
            .order_by(
                Task.updated_at.desc(),
                Task.id.desc(),
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt)
        )

    def notes(
        self,
        query: str,
        limit: int,
    ) -> list[Note]:
        pattern = contains_pattern(
            query
        )

        stmt = (
            select(Note)
            .where(
                Note.deleted_at.is_(None),
                or_(
                    Note.title.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Note.content.ilike(
                        pattern,
                        escape="\\",
                    ),
                ),
            )
            .order_by(
                Note.updated_at.desc(),
                Note.id.desc(),
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt)
        )

    def goals(
        self,
        query: str,
        limit: int,
    ) -> list[Goal]:
        pattern = contains_pattern(
            query
        )

        stmt = (
            select(Goal)
            .where(
                Goal.deleted_at.is_(None),
                or_(
                    Goal.title.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Goal.description.ilike(
                        pattern,
                        escape="\\",
                    ),
                ),
            )
            .order_by(
                Goal.updated_at.desc(),
                Goal.id.desc(),
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt)
        )

    def resources(
        self,
        query: str,
        limit: int,
    ) -> list[Resource]:
        pattern = contains_pattern(
            query
        )

        stmt = (
            select(Resource)
            .where(
                Resource.deleted_at.is_(None),
                or_(
                    Resource.title.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Resource.author.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Resource.description.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Resource.url.ilike(
                        pattern,
                        escape="\\",
                    ),
                ),
            )
            .order_by(
                Resource.updated_at.desc(),
                Resource.id.desc(),
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt)
        )

    def skills(
        self,
        query: str,
        limit: int,
    ) -> list[Skill]:
        pattern = contains_pattern(
            query
        )

        stmt = (
            select(Skill)
            .where(
                Skill.deleted_at.is_(None),
                or_(
                    Skill.name.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Skill.slug.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Skill.category.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Skill.notes.ilike(
                        pattern,
                        escape="\\",
                    ),
                ),
            )
            .order_by(
                Skill.updated_at.desc(),
                Skill.id.desc(),
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt)
        )