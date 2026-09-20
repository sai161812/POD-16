from enum import StrEnum


class RuleDomain(StrEnum):
    TASK = "task"
    PROJECT = "project"
    GOAL = "goal"
    RESOURCE = "resource"
    SKILL = "skill"


class RuleMatchMode(StrEnum):
    ALL = "all"
    ANY = "any"


class RuleOperator(StrEnum):
    EQ = "eq"
    NE = "ne"

    GT = "gt"
    GTE = "gte"

    LT = "lt"
    LTE = "lte"

    IN = "in"
    NOT_IN = "not_in"

    CONTAINS = "contains"

    IS_NULL = "is_null"
    NOT_NULL = "not_null"


class RuleEffectType(StrEnum):
    ATTENTION = "attention"
    LABEL = "label"
    SCORE = "score"
    MESSAGE = "message"