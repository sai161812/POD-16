from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.patch import reject_null_fields
from app.domains.rules.enums import (
    RuleDomain,
)
from app.domains.rules.evaluator import (
    apply_effects,
    rule_matches,
)
from app.domains.rules.facts import (
    FactBuilder,
)
from app.domains.rules.model import Rule
from app.domains.rules.repository import (
    RuleRepository,
)
from app.domains.rules.schemas import (
    RuleCondition,
    RuleCreate,
    RuleUpdate,
)

ALLOWED_FIELDS = {
    RuleDomain.TASK: {
        "title",
        "status",
        "priority",
        "project_id",
        "estimated_minutes",
        "due_date",
        "due_at",
        "is_overdue",
        "is_today",
        "is_blocked",
    },

    RuleDomain.PROJECT: {
        "name",
        "status",
        "priority",
        "focus_rank",
        "progress_percent",
        "target_date",
    },

    RuleDomain.GOAL: {
        "title",
        "status",
        "progress_percent",
        "target_date",
    },

    RuleDomain.RESOURCE: {
        "title",
        "resource_type",
        "status",
        "author",
        "progress_percent",
    },

    RuleDomain.SKILL: {
        "name",
        "category",
        "current_level",
        "target_level",
        "level_gap",
        "target_date",
    },
}


class RuleService:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db
        self.repo = RuleRepository(db)
        self.facts = FactBuilder(db)

    def _validate_conditions(
        self,
        domain: RuleDomain,
        conditions: list[
            RuleCondition
        ],
    ) -> None:
        allowed = ALLOWED_FIELDS[
            domain
        ]

        invalid = {
            condition.field
            for condition in conditions
            if condition.field
            not in allowed
        }

        if invalid:
            raise AppError(
                code="invalid_rule_field",
                message=(
                    "Rule contains fields "
                    "not supported by this domain."
                ),
                status_code=422,
                details={
                    "domain": domain.value,
                    "invalid_fields": sorted(
                        invalid
                    ),
                    "allowed_fields": sorted(
                        allowed
                    ),
                },
            )

    def create(
        self,
        payload: RuleCreate,
    ) -> Rule:
        self._validate_conditions(
            payload.domain,
            payload.conditions,
        )

        rule = Rule(
            name=payload.name,
            description=(
                payload.description
            ),
            domain=payload.domain,
            match_mode=(
                payload.match_mode
            ),
            conditions=[
                condition.model_dump(
                    mode="json"
                )
                for condition
                in payload.conditions
            ],
            effects=[
                effect.model_dump(
                    mode="json"
                )
                for effect
                in payload.effects
            ],
            enabled=payload.enabled,
        )

        self.repo.add(rule)

        self.db.commit()
        self.db.refresh(rule)

        return rule

    def get(
        self,
        rule_id: UUID,
    ) -> Rule:
        rule = self.repo.get(
            rule_id
        )

        if rule is None:
            raise AppError(
                code="rule_not_found",
                message="Rule not found.",
                status_code=404,
            )

        return rule

    def list(
        self,
        *,
        limit: int,
        offset: int,
        domain: RuleDomain | None,
        enabled: bool | None,
    ):
        return self.repo.list(
            limit=limit,
            offset=offset,
            domain=domain,
            enabled=enabled,
        )

    def update(
        self,
        rule_id: UUID,
        payload: RuleUpdate,
    ) -> Rule:
        rule = self.get(
            rule_id
        )

        new_domain = (
            payload.domain
            if payload.domain is not None
            else rule.domain
        )

        if payload.conditions is not None:
            conditions = (
                payload.conditions
            )
        else:
            conditions = [
                RuleCondition.model_validate(
                    item
                )
                for item
                in rule.conditions
            ]

        self._validate_conditions(
            new_domain,
            conditions,
        )

        changes = payload.model_dump(
            exclude_unset=True
        )
        reject_null_fields(
            changes,
            {
                "name",
                "domain",
                "match_mode",
                "conditions",
                "effects",
                "enabled",
            },
        )

        if "conditions" in changes:
            changes["conditions"] = [
                condition.model_dump(
                    mode="json"
                )
                for condition
                in payload.conditions
            ]

        if "effects" in changes:
            changes["effects"] = [
                effect.model_dump(
                    mode="json"
                )
                for effect
                in payload.effects
            ]

        for field, value in changes.items():
            setattr(
                rule,
                field,
                value,
            )

        self.db.commit()
        self.db.refresh(rule)

        return rule

    def delete(
        self,
        rule_id: UUID,
    ) -> None:
        rule = self.get(
            rule_id
        )

        rule.deleted_at = (
            datetime.now().astimezone()
        )

        self.db.commit()

    def restore(
        self,
        rule_id: UUID,
    ) -> Rule:
        rule = self.repo.get_deleted(
            rule_id
        )

        if rule is None:
            raise AppError(
                code="deleted_rule_not_found",
                message=(
                    "Deleted rule not found."
                ),
                status_code=404,
            )

        rule.deleted_at = None

        self.db.commit()
        self.db.refresh(rule)

        return rule

    def evaluate(
        self,
        *,
        domain: RuleDomain,
        entity_id: UUID,
    ) -> dict:
        facts = self.facts.build(
            domain,
            entity_id,
        )

        rules = (
            self.repo
            .enabled_for_domain(
                domain
            )
        )

        matched = [
            rule
            for rule in rules
            if rule_matches(
                rule,
                facts,
            )
        ]

        consequences = (
            apply_effects(
                matched
            )
        )

        return {
            "domain": domain,
            "entity_id": entity_id,
            "facts": facts,
            **consequences,
        }