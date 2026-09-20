from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from secrets import compare_digest
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError
from app.db.session import get_db
from app.domains.clients.repository import (
    ApiClientRepository,
)

bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="POD-16 API Key",
    description=(
        "Enter your POD-16 API key "
        "as a Bearer token."
    ),
)


@dataclass(frozen=True)
class AuthContext:
    client_id: UUID | None
    name: str
    scopes: frozenset[str]
    bootstrap: bool


Db = Annotated[
    Session,
    Depends(get_db),
]

Credentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def _hash_api_key(
    api_key: str,
) -> str:
    return sha256(
        api_key.encode("utf-8")
    ).hexdigest()


def _required_scope(
    request: Request,
) -> str | None:
    path = request.url.path

    if not path.startswith("/v1/"):
        return None

    parts = path.strip("/").split("/")

    if len(parts) < 2:
        return None

    domain = parts[1]

    if domain == "clients":
        return "clients:manage"

    if request.method == "GET":
        return f"{domain}:read"

    return f"{domain}:write"


def require_api_key(
    request: Request,
    db: Db,
    credentials: Credentials,
) -> AuthContext:
    if (
        credentials is None
        or credentials.scheme.lower()
        != "bearer"
    ):
        raise AppError(
            code="unauthorized",
            message="Missing Bearer API key.",
            status_code=401,
        )

    presented_key = (
        credentials.credentials
    )

    # Bootstrap key remains the emergency /
    # administrative super-key.
    if compare_digest(
        presented_key,
        settings.bootstrap_api_key,
    ):
        context = AuthContext(
            client_id=None,
            name="bootstrap",
            scopes=frozenset({"*"}),
            bootstrap=True,
        )

        request.state.auth = context

        return context

    token_hash = _hash_api_key(
        presented_key
    )

    client = (
        ApiClientRepository(
            db
        ).get_by_token_hash(
            token_hash
        )
    )

    if client is None:
        raise AppError(
            code="unauthorized",
            message="Invalid API key.",
            status_code=401,
        )

    if client.revoked_at is not None:
        raise AppError(
            code="api_key_revoked",
            message="API key has been revoked.",
            status_code=401,
        )

    required_scope = _required_scope(
        request
    )

    scopes = set(client.scopes)

    if (
        required_scope is not None
        and "*" not in scopes
        and required_scope
        not in scopes
    ):
        raise AppError(
            code="insufficient_scope",
            message=(
                "API key does not have "
                "permission for this operation."
            ),
            status_code=403,
            details={
                "required_scope": (
                    required_scope
                )
            },
        )

    client.last_used_at = datetime.now(
        UTC
    )

    db.commit()

    context = AuthContext(
        client_id=client.id,
        name=client.name,
        scopes=frozenset(scopes),
        bootstrap=False,
    )

    request.state.auth = context

    return context