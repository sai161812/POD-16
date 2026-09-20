from sqlalchemy.orm import Session

from app.domains.attention.repository import (
    AttentionRepository,
)
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
from app.domains.rules.repository import (
    RuleRepository,
)
from app.domains.tasks.time import (
    now_local,
)


class AttentionService:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

        self.repo = AttentionRepository(
            db
        )

        self.rules = RuleRepository(
            db
        )

        self.facts = FactBuilder(
            db
        )

    @staticmethod
    def _title(
        domain: RuleDomain,
        entity,
    ) -> str:
        if domain == RuleDomain.TASK:
            return entity.title

        if domain == RuleDomain.PROJECT:
            return entity.name

        if domain == RuleDomain.GOAL:
            return entity.title

        if domain == RuleDomain.RESOURCE:
            return entity.title

        if domain == RuleDomain.SKILL:
            return entity.name

        return str(entity.id)

    def get(
        self,
        *,
        domain: RuleDomain | None,
        limit: int,
    ) -> dict:
        domains = (
            [domain]
            if domain is not None
            else list(RuleDomain)
        )

        items = []

        for current_domain in domains:
            rules = (
                self.rules
                .enabled_for_domain(
                    current_domain
                )
            )

            # No rules means there is nothing
            # to evaluate for this domain.
            if not rules:
                continue

            candidates = (
                self.repo.candidates(
                    current_domain
                )
            )

            for entity in candidates:
                facts = self.facts.build(
                    current_domain,
                    entity.id,
                )

                matched = [
                    rule
                    for rule in rules
                    if rule_matches(
                        rule,
                        facts,
                    )
                ]

                if not matched:
                    continue

                consequences = (
                    apply_effects(
                        matched
                    )
                )

                # /attention should not become
                # a dump of every matched rule.
                #
                # It includes only items that
                # actually demand attention or
                # carry a positive score.
                if (
                    not consequences[
                        "requires_attention"
                    ]
                    and consequences[
                        "score"
                    ] <= 0
                ):
                    continue

                items.append(
                    {
                        "domain": (
                            current_domain
                        ),
                        "entity_id": (
                            entity.id
                        ),
                        "title": self._title(
                            current_domain,
                            entity,
                        ),
                        "requires_attention": (
                            consequences[
                                "requires_attention"
                            ]
                        ),
                        "score": (
                            consequences[
                                "score"
                            ]
                        ),
                        "labels": (
                            consequences[
                                "labels"
                            ]
                        ),
                        "messages": (
                            consequences[
                                "messages"
                            ]
                        ),
                        "matched_rules": (
                            consequences[
                                "matched_rules"
                            ]
                        ),
                        "facts": facts,
                    }
                )

        # Attention flag first.
        # Within those groups, higher rule
        # score comes first.
        items.sort(
            key=lambda item: (
                not item[
                    "requires_attention"
                ],
                -item["score"],
                item["title"].casefold(),
            )
        )

        items = items[:limit]

        by_domain: dict[str, int] = {}

        for item in items:
            key = item[
                "domain"
            ].value

            by_domain[key] = (
                by_domain.get(
                    key,
                    0,
                )
                + 1
            )

        return {
            "generated_at": now_local(),

            "summary": {
                "total": len(items),

                "requires_attention": sum(
                    item[
                        "requires_attention"
                    ]
                    for item in items
                ),

                "positive_score_items": sum(
                    item["score"] > 0
                    for item in items
                ),

                "by_domain": by_domain,
            },

            "data": items,
        }