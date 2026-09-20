from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domains.notes.schemas import (
    NoteCreate,
    NoteListResponse,
    NoteRead,
    NoteUpdate,
)
from app.domains.notes.service import NoteService

router = APIRouter()

Db = Annotated[
    Session,
    Depends(get_db),
]


def to_read(note) -> NoteRead:
    return NoteRead(
        id=note.id,
        title=note.title,
        content=note.content,
        project_id=note.project_id,
        metadata=note.extra_metadata,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


@router.post(
    "",
    response_model=NoteRead,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    payload: NoteCreate,
    db: Db,
) -> NoteRead:
    return to_read(
        NoteService(db).create(payload)
    )


@router.get(
    "",
    response_model=NoteListResponse,
)
def list_notes(
    db: Db,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    project_id: UUID | None = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=200,
        ),
    ] = None,
) -> NoteListResponse:
    notes = NoteService(db).list(
        limit=limit,
        offset=offset,
        project_id=project_id,
        q=q,
    )

    return NoteListResponse(
        data=[
            to_read(note)
            for note in notes
        ]
    )


@router.get(
    "/{note_id}",
    response_model=NoteRead,
)
def get_note(
    note_id: UUID,
    db: Db,
) -> NoteRead:
    return to_read(
        NoteService(db).get(note_id)
    )


@router.patch(
    "/{note_id}",
    response_model=NoteRead,
)
def update_note(
    note_id: UUID,
    payload: NoteUpdate,
    db: Db,
) -> NoteRead:
    return to_read(
        NoteService(db).update(
            note_id,
            payload,
        )
    )


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_note(
    note_id: UUID,
    db: Db,
) -> Response:
    NoteService(db).delete(note_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/{note_id}/restore",
    response_model=NoteRead,
)
def restore_note(
    note_id: UUID,
    db: Db,
) -> NoteRead:
    return to_read(
        NoteService(db).restore(note_id)
    )