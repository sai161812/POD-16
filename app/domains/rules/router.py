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
from app.domains.rules.enums import (
    RuleDomain,
)
from app.domains.rules.schemas import (
    RuleCondition,
    RuleCreate,
    RuleEffect,
    RuleEvaluationRead,
    RuleListResponse,
    RuleRead,
    RuleUpdate,
)
from app.domains.rules.service import (
    RuleService,
)

router = APIRouter()

Db = Annotated[
    Session,
    Depends(get_db),
]


def to_read(rule) -> RuleRead:
    return RuleRead(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        domain=rule.domain,
        match_mode=rule.match_mode,
        conditions=[
            RuleCondition.model_validate(
                item
            )
            for item
            in rule.conditions
        ],
        effects=[
            RuleEffect.model_validate(
                item
            )
            for item
            in rule.effects
        ],
        enabled=rule.enabled,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.post(
    "",
    response_model=RuleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_rule(
    payload: RuleCreate,
    db: Db,
) -> RuleRead:
    return to_read(
        RuleService(db).create(
            payload
        )
    )


@router.get(
    "",
    response_model=RuleListResponse,
)
def list_rules(
    db: Db,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
        ),
    ] = 50,
    offset: Annotated[
        int,
        Query(
            ge=0,
        ),
    ] = 0,
    domain: RuleDomain | None = None,
    enabled: bool | None = None,
) -> RuleListResponse:
    rules = RuleService(
        db
    ).list(
        limit=limit,
        offset=offset,
        domain=domain,
        enabled=enabled,
    )

    return RuleListResponse(
        data=[
            to_read(rule)
            for rule in rules
        ]
    )


# KEEP THIS ABOVE /{rule_id}
@router.get(
    "/evaluate/{domain}/{entity_id}",
    response_model=RuleEvaluationRead,
)
def evaluate_rules(
    domain: RuleDomain,
    entity_id: UUID,
    db: Db,
) -> RuleEvaluationRead:
    return RuleEvaluationRead(
        **RuleService(
            db
        ).evaluate(
            domain=domain,
            entity_id=entity_id,
        )
    )


@router.get(
    "/{rule_id}",
    response_model=RuleRead,
)
def get_rule(
    rule_id: UUID,
    db: Db,
) -> RuleRead:
    return to_read(
        RuleService(db).get(
            rule_id
        )
    )


@router.patch(
    "/{rule_id}",
    response_model=RuleRead,
)
def update_rule(
    rule_id: UUID,
    payload: RuleUpdate,
    db: Db,
) -> RuleRead:
    return to_read(
        RuleService(db).update(
            rule_id,
            payload,
        )
    )


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_rule(
    rule_id: UUID,
    db: Db,
) -> Response:
    RuleService(db).delete(
        rule_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/{rule_id}/restore",
    response_model=RuleRead,
)
def restore_rule(
    rule_id: UUID,
    db: Db,
) -> RuleRead:
    return to_read(
        RuleService(db).restore(
            rule_id
        )
    )