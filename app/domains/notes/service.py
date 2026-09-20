from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.domains.notes.model import Note
from app.domains.notes.repository import NoteRepository
from app.core.patch import reject_null_fields
from app.domains.notes.schemas import (
    NoteCreate,
    NoteUpdate,
)
from app.domains.projects.repository import (
    ProjectRepository,
)


class NoteService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = NoteRepository(db)
        self.projects = ProjectRepository(db)

    def _validate_project(
        self,
        project_id: UUID | None,
    ) -> None:
        if project_id is None:
            return

        if self.projects.get(project_id) is None:
            raise AppError(
                code="project_not_found",
                message="Project not found.",
                status_code=422,
                details={
                    "project_id": str(project_id),
                },
            )

    def create(
        self,
        payload: NoteCreate,
    ) -> Note:
        self._validate_project(
            payload.project_id
        )

        values = payload.model_dump()

        values["extra_metadata"] = values.pop(
            "metadata"
        )

        note = Note(**values)

        self.repo.add(note)

        self.db.commit()
        self.db.refresh(note)

        return note

    def get(
        self,
        note_id: UUID,
    ) -> Note:
        note = self.repo.get(note_id)

        if note is None:
            raise AppError(
                code="note_not_found",
                message="Note not found.",
                status_code=404,
                details={
                    "note_id": str(note_id),
                },
            )

        return note

    def list(
        self,
        *,
        limit: int,
        offset: int,
        project_id: UUID | None,
        q: str | None,
    ) -> list[Note]:
        return self.repo.list(
            limit=limit,
            offset=offset,
            project_id=project_id,
            q=q,
        )

    def update(
        self,
        note_id: UUID,
        payload: NoteUpdate,
    ) -> Note:
        note = self.get(note_id)

        changes = payload.model_dump(
            exclude_unset=True
        )
        reject_null_fields(
            changes,
            {
                "title",
                "content",
                "metadata",
            },
        )

        if "project_id" in changes:
            self._validate_project(
                changes["project_id"]
            )

        if "metadata" in changes:
            changes["extra_metadata"] = (
                changes.pop("metadata")
            )

        for field, value in changes.items():
            setattr(note, field, value)

        self.db.commit()
        self.db.refresh(note)

        return note

    def delete(
        self,
        note_id: UUID,
    ) -> None:
        note = self.get(note_id)

        note.deleted_at = (
            datetime.now().astimezone()
        )

        self.db.commit()

    def restore(
        self,
        note_id: UUID,
    ) -> Note:
        note = self.repo.get_deleted(
            note_id
        )

        if note is None:
            raise AppError(
                code="deleted_note_not_found",
                message="Deleted note not found.",
                status_code=404,
                details={
                    "note_id": str(note_id),
                },
            )

        note.deleted_at = None

        self.db.commit()
        self.db.refresh(note)

        return note