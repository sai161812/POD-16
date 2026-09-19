from fastapi import APIRouter, Depends

from app.core.security import require_api_key
from app.domains.tasks.router import router as tasks_router
from app.domains.projects.router import router as projects_router
from app.domains.notes.router import (
    router as notes_router,
)
from app.domains.focus.router import (
    router as focus_router,
)
from app.domains.search.router import (
    router as search_router,
)
from app.domains.clients.router import (
    router as clients_router,
)
from app.domains.goals.router import (
    router as goals_router,
)
from app.domains.profile.router import (
    router as profile_router,
)
from app.domains.skills.router import (
    router as skills_router,
)
from app.domains.resources.router import (
    router as resources_router,
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
api_router.include_router(
    clients_router,
    prefix="/clients",
    tags=["clients"],
)

api_router.include_router(
    goals_router,
    prefix="/goals",
    tags=["goals"],
)
api_router.include_router(
    focus_router,
    prefix="/focus",
    tags=["focus"],
)
api_router.include_router(
    search_router,
    prefix="/search",
    tags=["search"],
)
api_router.include_router(
    profile_router,
    prefix="/profile",
    tags=["profile"],
)
api_router.include_router(
    skills_router,
    prefix="/skills",
    tags=["skills"],
)
api_router.include_router(
    resources_router,
    prefix="/resources",
    tags=["resources"],
)