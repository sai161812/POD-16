from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.domains.notes.model import Note
from app.core.query import contains_pattern

class NoteRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(
        self,
        note_id: UUID,
    ) -> Note | None:
        stmt = select(Note).where(
            Note.id == note_id,
            Note.deleted_at.is_(None),
        )

        return self.db.scalar(stmt)

    def get_deleted(
        self,
        note_id: UUID,
    ) -> Note | None:
        stmt = select(Note).where(
            Note.id == note_id,
            Note.deleted_at.is_not(None),
        )

        return self.db.scalar(stmt)

    def list(
        self,
        *,
        limit: int = 50,
        project_id: UUID | None = None,
        q: str | None = None,
    ) -> list[Note]:
        stmt = select(Note).where(
            Note.deleted_at.is_(None)
        )

        if project_id is not None:
            stmt = stmt.where(
                Note.project_id == project_id
            )

        if q:
            pattern = contains_pattern(q)

            stmt = stmt.where(
                or_(
                    Note.title.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Note.content.ilike(
                        pattern,
                        escape="\\",
                    ),
                )
            )
        stmt = (
            stmt
            .order_by(
                Note.updated_at.desc(),
                Note.id.desc(),
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt)
        )

    def add(
        self,
        note: Note,
    ) -> Note:
        self.db.add(note)

        self.db.flush()
        self.db.refresh(note)

        return note