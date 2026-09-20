from uuid import UUID

from sqlalchemy import (
    or_,
    select,
)
from sqlalchemy.orm import Session

from app.core.query import contains_pattern
from app.domains.resources.enums import (
    ResourceStatus,
    ResourceType,
)
from app.domains.resources.model import (
    Resource,
    ResourceSkill,
)
from app.domains.skills.model import Skill


class ResourceRepository:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def get(
        self,
        resource_id: UUID,
    ) -> Resource | None:
        stmt = select(Resource).where(
            Resource.id == resource_id,
            Resource.deleted_at.is_(None),
        )

        return self.db.scalar(stmt)

    def get_deleted(
        self,
        resource_id: UUID,
    ) -> Resource | None:
        stmt = select(Resource).where(
            Resource.id == resource_id,
            Resource.deleted_at.is_not(None),
        )

        return self.db.scalar(stmt)

    def list(
        self,
        *,
        limit: int,
        offset: int, 
        resource_type: ResourceType | None,
        status: ResourceStatus | None,
        q: str | None,
    ) -> list[Resource]:
        stmt = select(Resource).where(
            Resource.deleted_at.is_(None)
        )

        if resource_type is not None:
            stmt = stmt.where(
                Resource.resource_type
                == resource_type
            )

        if status is not None:
            stmt = stmt.where(
                Resource.status == status
            )

        if q:
            pattern = contains_pattern(q)

            stmt = stmt.where(
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
                )
            )
        stmt = (
            stmt
            .order_by(
                Resource.updated_at.desc(),
                Resource.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        return list(
            self.db.scalars(stmt)
        )

    def add(
        self,
        resource: Resource,
    ) -> Resource:
        self.db.add(resource)
        self.db.flush()
        self.db.refresh(resource)

        return resource

    def get_skills(
        self,
        resource_id: UUID,
    ) -> list[Skill]:
        stmt = (
            select(Skill)
            .join(
                ResourceSkill,
                Skill.id
                == ResourceSkill.skill_id,
            )
            .where(
                ResourceSkill.resource_id
                == resource_id,
                Skill.deleted_at.is_(None),
            )
            .order_by(
                Skill.name.asc()
            )
        )

        return list(
            self.db.scalars(stmt)
        )

    def skill_link_exists(
        self,
        *,
        resource_id: UUID,
        skill_id: UUID,
    ) -> bool:
        link = self.db.get(
            ResourceSkill,
            (
                resource_id,
                skill_id,
            ),
        )

        return link is not None

    def add_skill_link(
        self,
        *,
        resource_id: UUID,
        skill_id: UUID,
    ) -> None:
        self.db.add(
            ResourceSkill(
                resource_id=resource_id,
                skill_id=skill_id,
            )
        )

        self.db.flush()

    def remove_skill_link(
        self,
        *,
        resource_id: UUID,
        skill_id: UUID,
    ) -> bool:
        link = self.db.get(
            ResourceSkill,
            (
                resource_id,
                skill_id,
            ),
        )

        if link is None:
            return False

        self.db.delete(link)
        self.db.flush()

        return True