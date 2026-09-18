from fastapi import APIRouter, Depends

from app.core.security import require_api_key
from app.domains.tasks.router import router as tasks_router
from app.domains.projects.router import router as projects_router
from app.domains.notes.router import (
    router as notes_router,
)

api_router = APIRouter(dependencies=[Depends(require_api_key)])
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(
    tasks_router,
    prefix="/tasks",
    tags=["tasks"],
)
api_router.include_router(
    notes_router,
    prefix="/notes",
    tags=["notes"],
)