from typing import Any

from app.core.errors import AppError


def reject_null_fields(
    changes: dict[str, Any],
    fields: set[str],
) -> None:
    invalid = sorted(
        field
        for field in fields
        if (
            field in changes
            and changes[field] is None
        )
    )

    if not invalid:
        return

    raise AppError(
        code="null_not_allowed",
        message=(
            "One or more fields cannot "
            "be set to null."
        ),
        status_code=422,
        details={
            "fields": invalid,
        },
    )