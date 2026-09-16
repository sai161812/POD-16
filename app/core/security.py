from secrets import compare_digest

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.errors import AppError


bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="POD-16 API Key",
    description="Enter your POD-16 API key as a Bearer token.",
)


def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(
            code="unauthorized",
            message="Missing Bearer API key.",
            status_code=401,
        )

    if not compare_digest(
        credentials.credentials,
        settings.bootstrap_api_key,
    ):
        raise AppError(
            code="unauthorized",
            message="Invalid API key.",
            status_code=401,
        )