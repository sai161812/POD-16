from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.domains.projects.enums import ProjectStatus
from app.domains.projects.model import Project
from app.domains.projects.repository import ProjectRepository
from app.domains.projects.schemas import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectRepository(db)

    def create(self, payload: ProjectCreate) -> Project:
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

        for field, value in changes.items():
            setattr(project, field, value)

        if "status" in changes:
            if project.status == ProjectStatus.COMPLETED:
                project.progress_percent = 100
                project.completed_at = datetime.now().astimezone()
                project.focus_rank = None

            elif project.completed_at is not None:
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
