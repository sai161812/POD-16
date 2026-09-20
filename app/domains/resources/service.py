from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.patch import reject_null_fields
from app.domains.resources.enums import (
    ResourceStatus,
)
from app.domains.resources.model import (
    Resource,
)
from app.domains.resources.repository import (
    ResourceRepository,
)
from app.domains.resources.schemas import (
    ResourceCreate,
    ResourceUpdate,
)
from app.domains.skills.repository import (
    SkillRepository,
)


class ResourceService:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db
        self.repo = ResourceRepository(db)
        self.skills = SkillRepository(db)

    def create(
        self,
        payload: ResourceCreate,
    ) -> Resource:
        values = payload.model_dump()

        values["extra_metadata"] = (
            values.pop("metadata")
        )

        if (
            values["status"]
            == ResourceStatus.COMPLETED
        ):
            values["progress_percent"] = 100
            values["completed_at"] = (
                datetime.now().astimezone()
            )

        resource = Resource(
            **values
        )

        self.repo.add(resource)

        self.db.commit()
        self.db.refresh(resource)

        return resource

    def get(
        self,
        resource_id: UUID,
    ) -> Resource:
        resource = self.repo.get(
            resource_id
        )

        if resource is None:
            raise AppError(
                code="resource_not_found",
                message="Resource not found.",
                status_code=404,
            )

        return resource

    def list(
        self,
        *,
        limit: int,
        offset: int,
        resource_type,
        status,
        q,
    ):
        return self.repo.list(
            limit=limit,
            offset=offset,
            resource_type=resource_type,
            status=status,
            q=q,
        )

    def update(
        self,
        resource_id: UUID,
        payload: ResourceUpdate,
    ) -> Resource:
        resource = self.get(
            resource_id
        )

        changes = payload.model_dump(
            exclude_unset=True
        )
        reject_null_fields(
            changes,
            {
                "title",
                "resource_type",
                "status",
                "progress_percent",
                "metadata",
            },
        )

        if "metadata" in changes:
            changes["extra_metadata"] = (
                changes.pop("metadata")
            )

        previous_status = resource.status

        for field, value in changes.items():
            setattr(
                resource,
                field,
                value,
            )

        if (
            resource.status
            == ResourceStatus.COMPLETED
        ):
            resource.progress_percent = 100

            if resource.completed_at is None:
                resource.completed_at = (
                    datetime.now().astimezone()
                )

        elif (
            previous_status
            == ResourceStatus.COMPLETED
        ):
            resource.completed_at = None

        self.db.commit()
        self.db.refresh(resource)

        return resource

    def delete(
        self,
        resource_id: UUID,
    ) -> None:
        resource = self.get(
            resource_id
        )

        resource.deleted_at = (
            datetime.now().astimezone()
        )

        self.db.commit()

    def restore(
        self,
        resource_id: UUID,
    ) -> Resource:
        resource = self.repo.get_deleted(
            resource_id
        )

        if resource is None:
            raise AppError(
                code="deleted_resource_not_found",
                message="Deleted resource not found.",
                status_code=404,
            )

        resource.deleted_at = None

        self.db.commit()
        self.db.refresh(resource)

        return resource

    def get_skills(
        self,
        resource_id: UUID,
    ):
        self.get(resource_id)

        return self.repo.get_skills(
            resource_id
        )

    def link_skill(
        self,
        *,
        resource_id: UUID,
        skill_id: UUID,
    ) -> None:
        self.get(resource_id)

        skill = self.skills.get(
            skill_id
        )

        if skill is None:
            raise AppError(
                code="skill_not_found",
                message="Skill not found.",
                status_code=404,
            )

        if self.repo.skill_link_exists(
            resource_id=resource_id,
            skill_id=skill_id,
        ):
            raise AppError(
                code="resource_skill_link_exists",
                message=(
                    "Skill is already linked "
                    "to this resource."
                ),
                status_code=409,
            )

        self.repo.add_skill_link(
            resource_id=resource_id,
            skill_id=skill_id,
        )

        self.db.commit()

    def unlink_skill(
        self,
        *,
        resource_id: UUID,
        skill_id: UUID,
    ) -> None:
        self.get(resource_id)

        removed = (
            self.repo.remove_skill_link(
                resource_id=resource_id,
                skill_id=skill_id,
            )
        )

        if not removed:
            raise AppError(
                code="resource_skill_link_not_found",
                message=(
                    "Resource-skill link "
                    "not found."
                ),
                status_code=404,
            )

        self.db.commit()