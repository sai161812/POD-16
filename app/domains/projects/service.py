from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.patch import reject_null_fields
from app.domains.projects.enums import ProjectStatus
from app.domains.projects.model import Project
from app.domains.projects.repository import ProjectRepository
from app.domains.projects.schemas import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectRepository(db)

    def _validate_parent_project(
        self,
        *,
        project_id: UUID | None,
        parent_project_id: UUID | None,
    ) -> None:
        if parent_project_id is None:
            return

        parent = self.repo.get(
            parent_project_id
        )

        if parent is None:
            raise AppError(
                code="parent_project_not_found",
                message="Parent project not found.",
                status_code=422,
                details={
                    "parent_project_id": str(
                        parent_project_id
                    ),
                },
            )

        if (
            project_id is not None
            and project_id == parent_project_id
        ):
            raise AppError(
                code="invalid_parent_project",
                message=(
                    "A project cannot be "
                    "its own parent."
                ),
                status_code=422,
            )

        if project_id is None:
            return

        visited: set[UUID] = set()
        current = parent

        while current is not None:
            if current.id == project_id:
                raise AppError(
                    code="project_parent_cycle",
                    message=(
                        "This parent assignment "
                        "would create a project cycle."
                    ),
                    status_code=422,
                )

            if current.id in visited:
                raise AppError(
                    code="project_parent_cycle",
                    message=(
                        "The project hierarchy "
                        "already contains a cycle."
                    ),
                    status_code=422,
                )

            visited.add(current.id)

            if current.parent_project_id is None:
                break

            current = self.repo.get(
                current.parent_project_id
            )

    def create(self, payload: ProjectCreate) -> Project:
        self._validate_parent_project(
            project_id=None,
            parent_project_id=(
                payload.parent_project_id
            ),
        )

        if self.repo.get_by_slug(payload.slug):
            raise AppError(
                code="project_slug_conflict",
                message="A project with this slug already exists.",
                status_code=409,
                details={"slug": payload.slug},
            )

        values = payload.model_dump()
        values["extra_metadata"] = values.pop("metadata")
        project = Project(**values)
        if project.status == ProjectStatus.COMPLETED:
            project.progress_percent = 100
            project.completed_at = (
                datetime.now().astimezone()
            )
            project.focus_rank = None

        try:
            self.repo.add(project)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise AppError(
                code="project_conflict",
                message="Project could not be created because of a data conflict.",
                status_code=409,
            )
        return project

    def get(self, project_id: UUID) -> Project:
        project = self.repo.get(project_id)
        if not project:
            raise AppError(
                code="project_not_found",
                message="Project not found.",
                status_code=404,
                details={"project_id": str(project_id)},
            )
        return project

    def list(
        self,
        *,
        limit: int,
        offset: int,
    ) -> list[Project]:
        return self.repo.list(
            limit=limit,
            offset=offset,
        )

    def update(self, project_id: UUID, payload: ProjectUpdate) -> Project:
        project = self.get(project_id)
        changes = payload.model_dump(exclude_unset=True)
        reject_null_fields(
            changes,
            {
                "name",
                "slug",
                "status",
                "priority",
                "metadata",
            },
        )
        if "parent_project_id" in changes:
            self._validate_parent_project(
                project_id=project.id,
                parent_project_id=changes[
                    "parent_project_id"
                ],
            )

        if "slug" in changes and changes["slug"] != project.slug:
            existing = self.repo.get_by_slug(changes["slug"])
            if existing:
                raise AppError(
                    code="project_slug_conflict",
                    message="A project with this slug already exists.",
                    status_code=409,
                )

        if "metadata" in changes:
            changes["extra_metadata"] = changes.pop("metadata")

        previous_status = project.status

        for field, value in changes.items():
            setattr(project, field, value)

        if project.status == ProjectStatus.COMPLETED:
            project.progress_percent = 100
            project.focus_rank = None

            if project.completed_at is None:
               project.completed_at = (
                   datetime.now().astimezone()
               )

        elif previous_status == ProjectStatus.COMPLETED:
           project.completed_at = None

        try:
            self.db.commit()
            self.db.refresh(project)
        except IntegrityError:
            self.db.rollback()
            raise AppError(
                code="project_conflict",
                message="Project could not be updated because of a data conflict.",
                status_code=409,
            )
        return project

    def delete(self, project_id: UUID) -> None:
        project = self.get(project_id)
        project.deleted_at = datetime.now().astimezone()
        self.db.commit()

    def restore(
        self,
        project_id: UUID,
    ) -> Project:
        project = self.repo.get_deleted(
            project_id
        )

        if project is None:
            raise AppError(
                code="deleted_project_not_found",
                message="Deleted project not found.",
                status_code=404,
                details={
                    "project_id": str(
                        project_id
                    ),
                },
            )

        project.deleted_at = None

        self.db.commit()
        self.db.refresh(project)

        return project
