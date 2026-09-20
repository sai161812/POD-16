from uuid import UUID
from app.core.query import contains_pattern
from sqlalchemy import (
    func,
    or_,
    select,
)
from sqlalchemy.orm import Session

from app.domains.skills.model import (
    LearningSession,
    Skill,
)


class SkillRepository:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def get(
        self,
        skill_id: UUID,
    ) -> Skill | None:
        stmt = select(Skill).where(
            Skill.id == skill_id,
            Skill.deleted_at.is_(None),
        )

        return self.db.scalar(stmt)

    def get_deleted(
        self,
        skill_id: UUID,
    ) -> Skill | None:
        stmt = select(Skill).where(
            Skill.id == skill_id,
            Skill.deleted_at.is_not(None),
        )

        return self.db.scalar(stmt)

    def get_by_slug(
        self,
        slug: str,
    ) -> Skill | None:
        stmt = select(Skill).where(
            Skill.slug == slug
        )

        return self.db.scalar(stmt)

    def list(
        self,
        *,
        limit: int,
        offset: int,
        category: str | None,
        q: str | None,
    ) -> list[Skill]:
        stmt = select(Skill).where(
            Skill.deleted_at.is_(None)
        )

        if category is not None:
            stmt = stmt.where(
                Skill.category == category
            )

        if q:
            pattern = contains_pattern(q)

            stmt = stmt.where(
                or_(
                    Skill.name.ilike(
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
                )
            )
        stmt = (
            stmt
            .order_by(
                Skill.updated_at.desc(),
                Skill.name.asc(),
                Skill.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt)
        )

    def add(
        self,
        skill: Skill,
    ) -> Skill:
        self.db.add(skill)
        self.db.flush()
        self.db.refresh(skill)

        return skill

    def add_session(
        self,
        session: LearningSession,
    ) -> LearningSession:
        self.db.add(session)
        self.db.flush()
        self.db.refresh(session)

        return session

    def sessions(
        self,
        skill_id: UUID,
        *,
        limit: int,
    ) -> list[LearningSession]:
        stmt = (
            select(LearningSession)
            .where(
                LearningSession.skill_id
                == skill_id
            )
            .order_by(
                LearningSession.logged_at.desc()
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt)
        )

    def progress_stats(
        self,
        skill_id: UUID,
    ):
        stmt = select(
            func.count(
                LearningSession.id
            ),
            func.coalesce(
                func.sum(
                    LearningSession.minutes
                ),
                0,
            ),
            func.max(
                LearningSession.logged_at
            ),
        ).where(
            LearningSession.skill_id
            == skill_id
        )

        return self.db.execute(
            stmt
        ).one()