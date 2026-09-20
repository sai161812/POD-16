from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session
from app.core.patch import reject_null_fields

from app.core.errors import AppError
from app.domains.skills.model import (
    LearningSession,
    Skill,
)
from app.domains.skills.repository import (
    SkillRepository,
)
from app.domains.skills.schemas import (
    LearningSessionCreate,
    SkillCreate,
    SkillUpdate,
)


class SkillService:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db
        self.repo = SkillRepository(db)

    def create(
        self,
        payload: SkillCreate,
    ) -> Skill:
        if self.repo.get_by_slug(
            payload.slug
        ):
            raise AppError(
                code="skill_slug_conflict",
                message=(
                    "A skill with this slug already exists."
                ),
                status_code=409,
            )

        values = payload.model_dump()

        values["extra_metadata"] = (
            values.pop("metadata")
        )

        skill = Skill(**values)

        self.repo.add(skill)

        self.db.commit()
        self.db.refresh(skill)

        return skill

    def get(
        self,
        skill_id: UUID,
    ) -> Skill:
        skill = self.repo.get(
            skill_id
        )

        if skill is None:
            raise AppError(
                code="skill_not_found",
                message="Skill not found.",
                status_code=404,
            )

        return skill

    def list(
        self,
        *,
        limit: int,
        offset: int,
        category: str | None,
        q: str | None,
    ) -> list[Skill]:
        return self.repo.list(
            limit=limit,
            offset=offset,
            category=category,
            q=q,
        )

    def update(
        self,
        skill_id: UUID,
        payload: SkillUpdate,
    ) -> Skill:
        skill = self.get(
            skill_id
        )

        changes = payload.model_dump(
            exclude_unset=True
        )
        reject_null_fields(
            changes,
            {
                "name",
                "slug",
                "current_level",
                "target_level",
                "metadata",
            },
            )

        if (
            "slug" in changes
            and changes["slug"]
            != skill.slug
        ):
            if self.repo.get_by_slug(
                changes["slug"]
            ):
                raise AppError(
                    code="skill_slug_conflict",
                    message=(
                        "A skill with this slug "
                        "already exists."
                    ),
                    status_code=409,
                )

        if "metadata" in changes:
            changes["extra_metadata"] = (
                changes.pop("metadata")
            )

        current_level = changes.get(
            "current_level",
            skill.current_level,
        )

        target_level = changes.get(
            "target_level",
            skill.target_level,
        )

        if target_level < current_level:
            raise AppError(
                code="invalid_skill_levels",
                message=(
                    "target_level cannot be "
                    "below current_level."
                ),
                status_code=422,
            )

        for field, value in changes.items():
            setattr(
                skill,
                field,
                value,
            )

        self.db.commit()
        self.db.refresh(skill)

        return skill

    def delete(
        self,
        skill_id: UUID,
    ) -> None:
        skill = self.get(
            skill_id
        )

        skill.deleted_at = (
            datetime.now().astimezone()
        )

        self.db.commit()

    def restore(
        self,
        skill_id: UUID,
    ) -> Skill:
        skill = self.repo.get_deleted(
            skill_id
        )

        if skill is None:
            raise AppError(
                code="deleted_skill_not_found",
                message="Deleted skill not found.",
                status_code=404,
            )

        skill.deleted_at = None

        self.db.commit()
        self.db.refresh(skill)

        return skill

    def log_session(
        self,
        skill_id: UUID,
        payload: LearningSessionCreate,
    ) -> LearningSession:
        self.get(skill_id)

        values = payload.model_dump(
            exclude_none=True
        )

        values["extra_metadata"] = (
            values.pop(
                "metadata",
                {},
            )
        )

        session = LearningSession(
            skill_id=skill_id,
            **values,
        )

        self.repo.add_session(
            session
        )

        self.db.commit()
        self.db.refresh(session)

        return session

    def sessions(
        self,
        skill_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[LearningSession]:
        self.get(skill_id)

        return self.repo.sessions(
            skill_id,
            limit=limit,
            offset=offset,
        )

    def progress(
        self,
        skill_id: UUID,
    ) -> dict:
        skill = self.get(
            skill_id
        )

        (
            session_count,
            total_minutes,
            last_logged_at,
        ) = self.repo.progress_stats(
            skill_id
        )

        return {
            "skill_id": skill.id,
            "current_level": (
                skill.current_level
            ),
            "target_level": (
                skill.target_level
            ),
            "level_gap": max(
                skill.target_level
                - skill.current_level,
                0,
            ),
            "session_count": (
                session_count
            ),
            "total_minutes": int(
                total_minutes
            ),
            "last_logged_at": (
                last_logged_at
            ),
        }