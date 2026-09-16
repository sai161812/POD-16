from fastapi import APIRouter, Depends

from app.core.security import require_api_key
from app.domains.projects.router import router as projects_router

api_router = APIRouter(dependencies=[Depends(require_api_key)])
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
