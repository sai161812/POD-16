from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.rules.enums import (
    RuleDomain,
)
from app.domains.rules.model import Rule


class RuleRepository:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def get(
        self,
        rule_id: UUID,
    ) -> Rule | None:
        stmt = select(Rule).where(
            Rule.id == rule_id,
            Rule.deleted_at.is_(None),
        )

        return self.db.scalar(stmt)

    def get_deleted(
        self,
        rule_id: UUID,
    ) -> Rule | None:
        stmt = select(Rule).where(
            Rule.id == rule_id,
            Rule.deleted_at.is_not(None),
        )

        return self.db.scalar(stmt)

    def list(
        self,
        *,
        limit: int,
        offset: int,
        domain: RuleDomain | None,
        enabled: bool | None,
    ) -> list[Rule]:
        stmt = select(Rule).where(
            Rule.deleted_at.is_(None)
        )

        if domain is not None:
            stmt = stmt.where(
                Rule.domain == domain
            )

        if enabled is not None:
            stmt = stmt.where(
                Rule.enabled == enabled
            )

        stmt = (
            stmt
            .order_by(
                Rule.created_at.asc(),
                Rule.id.asc(),
            )
            .limit(limit)
            .offset(offset)
        )

        return list(
            self.db.scalars(stmt)
        )

    def enabled_for_domain(
        self,
        domain: RuleDomain,
    ) -> list[Rule]:
        stmt = (
            select(Rule)
            .where(
                Rule.deleted_at.is_(None),
                Rule.enabled.is_(True),
                Rule.domain == domain,
            )
            .order_by(
                Rule.created_at.asc()
            )
        )

        return list(
            self.db.scalars(stmt)
        )

    def add(
        self,
        rule: Rule,
    ) -> Rule:
        self.db.add(rule)
        self.db.flush()
        self.db.refresh(rule)

        return rule