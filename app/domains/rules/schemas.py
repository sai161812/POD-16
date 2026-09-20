from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)

from app.domains.rules.enums import (
    RuleDomain,
    RuleEffectType,
    RuleMatchMode,
    RuleOperator,
)


class RuleCondition(BaseModel):
    field: str = Field(
        min_length=1,
        max_length=100,
    )

    operator: RuleOperator

    value: Any = None

    @model_validator(mode="after")
    def validate_value(self):
        null_operators = {
            RuleOperator.IS_NULL,
            RuleOperator.NOT_NULL,
        }

        if self.operator in null_operators:
            return self

        if self.value is None:
            raise ValueError(
                "This operator requires a value."
            )

        if (
            self.operator
            in {
                RuleOperator.IN,
                RuleOperator.NOT_IN,
            }
            and not isinstance(
                self.value,
                list,
            )
        ):
            raise ValueError(
                "in/not_in operators require "
                "a list value."
            )

        return self


class RuleEffect(BaseModel):
    type: RuleEffectType
    value: Any

    @model_validator(mode="after")
    def validate_effect(self):
        if (
            self.type
            == RuleEffectType.ATTENTION
        ):
            if self.value is not True:
                raise ValueError(
                    "attention effect value "
                    "must be true."
                )

        elif (
            self.type
            in {
                RuleEffectType.LABEL,
                RuleEffectType.MESSAGE,
            }
        ):
            if (
                not isinstance(
                    self.value,
                    str,
                )
                or not self.value.strip()
            ):
                raise ValueError(
                    "label/message must "
                    "contain text."
                )

        elif (
            self.type
            == RuleEffectType.SCORE
        ):
            if (
                isinstance(
                    self.value,
                    bool,
                )
                or not isinstance(
                    self.value,
                    int,
                )
            ):
                raise ValueError(
                    "score must be an integer."
                )

            if not -100 <= self.value <= 100:
                raise ValueError(
                    "score must be between "
                    "-100 and 100."
                )

        return self


class RuleCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=160,
    )

    description: str | None = None

    domain: RuleDomain

    match_mode: RuleMatchMode = (
        RuleMatchMode.ALL
    )

    conditions: list[
        RuleCondition
    ] = Field(
        min_length=1,
    )

    effects: list[
        RuleEffect
    ] = Field(
        min_length=1,
    )

    enabled: bool = True


class RuleUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=160,
    )

    description: str | None = None

    domain: RuleDomain | None = None

    match_mode: RuleMatchMode | None = None

    conditions: list[
        RuleCondition
    ] | None = Field(
        default=None,
        min_length=1,
    )

    effects: list[
        RuleEffect
    ] | None = Field(
        default=None,
        min_length=1,
    )

    enabled: bool | None = None


class RuleRead(BaseModel):
    id: UUID

    name: str
    description: str | None

    domain: RuleDomain
    match_mode: RuleMatchMode

    conditions: list[
        RuleCondition
    ]

    effects: list[
        RuleEffect
    ]

    enabled: bool

    created_at: datetime
    updated_at: datetime


class RuleListResponse(BaseModel):
    data: list[RuleRead]


class MatchedRuleRead(BaseModel):
    id: UUID
    name: str

    effects: list[
        RuleEffect
    ]


class RuleEvaluationRead(BaseModel):
    domain: RuleDomain

    entity_id: UUID

    facts: dict[str, Any]

    matched_rules: list[
        MatchedRuleRead
    ]

    requires_attention: bool

    labels: list[str]

    score: int

    messages: list[str]