from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.middleware import RequestIdMiddleware

app = FastAPI(
    title="POD-16",
    version="0.1.0",
    description="Private personal programmable backend",
)

app.add_middleware(RequestIdMiddleware)
register_exception_handlers(app)

app.include_router(api_router, prefix="/v1")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
