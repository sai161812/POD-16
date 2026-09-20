from typing import Any

from app.domains.rules.enums import (
    RuleEffectType,
    RuleMatchMode,
    RuleOperator,
)
from app.domains.rules.schemas import (
    RuleCondition,
    RuleEffect,
)


def _condition_matches(
    condition: RuleCondition,
    facts: dict[str, Any],
) -> bool:
    value = facts.get(
        condition.field
    )

    expected = condition.value

    operator = condition.operator

    if operator == RuleOperator.IS_NULL:
        return value is None

    if operator == RuleOperator.NOT_NULL:
        return value is not None

    if operator == RuleOperator.EQ:
        return value == expected

    if operator == RuleOperator.NE:
        return value != expected

    if operator == RuleOperator.IN:
        return value in expected

    if operator == RuleOperator.NOT_IN:
        return value not in expected

    if operator == RuleOperator.CONTAINS:
        if isinstance(value, str):
            return (
                str(expected).casefold()
                in value.casefold()
            )

        if isinstance(
            value,
            (list, tuple, set),
        ):
            return expected in value

        return False

    try:
        if operator == RuleOperator.GT:
            return value > expected

        if operator == RuleOperator.GTE:
            return value >= expected

        if operator == RuleOperator.LT:
            return value < expected

        if operator == RuleOperator.LTE:
            return value <= expected

    except TypeError:
        return False

    return False


def rule_matches(
    rule,
    facts: dict[str, Any],
) -> bool:
    conditions = [
        RuleCondition.model_validate(
            condition
        )
        for condition in rule.conditions
    ]

    matches = [
        _condition_matches(
            condition,
            facts,
        )
        for condition in conditions
    ]

    if (
        rule.match_mode
        == RuleMatchMode.ALL
    ):
        return all(matches)

    return any(matches)


def apply_effects(
    matched_rules,
) -> dict:
    requires_attention = False

    labels: list[str] = []
    messages: list[str] = []

    score = 0

    matched_data = []

    for rule in matched_rules:
        effects = [
            RuleEffect.model_validate(
                effect
            )
            for effect in rule.effects
        ]

        for effect in effects:
            if (
                effect.type
                == RuleEffectType.ATTENTION
            ):
                requires_attention = True

            elif (
                effect.type
                == RuleEffectType.LABEL
            ):
                if (
                    effect.value
                    not in labels
                ):
                    labels.append(
                        effect.value
                    )

            elif (
                effect.type
                == RuleEffectType.SCORE
            ):
                score += effect.value

            elif (
                effect.type
                == RuleEffectType.MESSAGE
            ):
                messages.append(
                    effect.value
                )

        matched_data.append(
            {
                "id": rule.id,
                "name": rule.name,
                "effects": effects,
            }
        )

    return {
        "matched_rules": matched_data,
        "requires_attention": (
            requires_attention
        ),
        "labels": labels,
        "score": score,
        "messages": messages,
    }