from collections.abc import Generator
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.security import (
    AuthContext,
    require_api_key,
)
from app.db.session import get_db
from app.domains.activity.service import (
    ActivityService,
)


MUTATING_METHODS = {
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
}


def _domain_from_request(
    request: Request,
) -> str:
    parts = (
        request.url.path
        .strip("/")
        .split("/")
    )

    if (
        len(parts) >= 2
        and parts[0] == "v1"
    ):
        return parts[1]

    return "unknown"


def _entity_id_from_params(
    path_params: dict,
) -> UUID | None:
    for key, value in path_params.items():
        if not key.endswith("_id"):
            continue

        try:
            return UUID(str(value))
        except (ValueError, TypeError):
            continue

    return None


def _operation_path(
    request: Request,
    domain: str,
) -> str:
    route_object = request.scope.get(
        "route"
    )

    local_path = getattr(
        route_object,
        "path",
        "",
    )

    # The dependency is attached to the
    # parent /v1 router, while FastAPI may
    # expose only the child router's path
    # here, e.g.:
    #
    # ""                -> /v1/projects
    # "/{project_id}"   -> /v1/projects/{project_id}
    #
    # Reconstruct the full stable route
    # template for audit history.

    base = f"/v1/{domain}"

    if not local_path:
        return base

    if not local_path.startswith("/"):
        local_path = "/" + local_path

    return base + local_path


def audit_request(
    request: Request,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(
        require_api_key
    ),
) -> Generator[None]:
    try:
        yield

    except Exception:
        # Failed business operations are
        # not recorded as successful events.
        raise

    else:
        if (
            request.method
            not in MUTATING_METHODS
        ):
            return

        domain = _domain_from_request(
            request
        )

        operation_path = (
            _operation_path(
                request,
                domain,
            )
        )

        path_params = {
            key: str(value)
            for key, value
            in request.path_params.items()
        }

        entity_id = (
            _entity_id_from_params(
                request.path_params
            )
        )

        ActivityService(db).record(
            actor_client_id=(
                auth.client_id
            ),
            actor_name=auth.name,
            domain=domain,
            method=request.method,
            operation=(
                f"{request.method} "
                f"{operation_path}"
            ),
            path=request.url.path,
            entity_id=entity_id,
            path_params=path_params,
            request_id=getattr(
                request.state,
                "request_id",
                None,
            ),
        )

        db.commit()