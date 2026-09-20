from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domains.rules.enums import (
    RuleDomain,
)
from app.domains.rules.schemas import (
    MatchedRuleRead,
)


class AttentionItemRead(BaseModel):
    domain: RuleDomain

    entity_id: UUID

    title: str

    requires_attention: bool

    score: int

    labels: list[str]

    messages: list[str]

    matched_rules: list[
        MatchedRuleRead
    ]

    facts: dict


class AttentionSummaryRead(BaseModel):
    total: int

    requires_attention: int

    positive_score_items: int

    by_domain: dict[str, int]


class AttentionRead(BaseModel):
    generated_at: datetime

    summary: AttentionSummaryRead

    data: list[
        AttentionItemRead
    ]