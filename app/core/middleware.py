from uuid import uuid4

from starlette.middleware.base import (
    BaseHTTPMiddleware,
)
from starlette.requests import Request
from starlette.responses import Response

MAX_REQUEST_ID_LENGTH = 128


class RequestIdMiddleware(
    BaseHTTPMiddleware
):
    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        incoming = request.headers.get(
            "X-Request-ID"
        )

        if incoming is not None:
            incoming = incoming.strip()

        if (
            not incoming
            or len(incoming)
            > MAX_REQUEST_ID_LENGTH
        ):
            request_id = str(uuid4())
        else:
            request_id = incoming

        request.state.request_id = (
            request_id
        )

        response = await call_next(
            request
        )

        response.headers[
            "X-Request-ID"
        ] = request_id

        return response