from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.domains.search.repository import (
    SearchRepository,
)
from app.domains.search.schemas import (
    SearchResultType,
)


class SearchService:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.repo = SearchRepository(db)

    @staticmethod
    def _snippet(
        text: str | None,
        max_length: int = 240,
    ) -> str | None:
        if not text:
            return None

        cleaned = " ".join(
            text.split()
        )

        if len(cleaned) <= max_length:
            return cleaned

        return (
            cleaned[:max_length].rstrip()
            + "..."
        )

    @staticmethod
    def _rank(
        query: str,
        title: str,
        body: str | None,
    ) -> int:
        q = query.casefold()
        title_value = title.casefold()

        if title_value == q:
            return 0

        if title_value.startswith(q):
            return 1

        if q in title_value:
            return 2

        if (
            body
            and q in body.casefold()
        ):
            return 3

        return 4

    def search(
        self,
        *,
        query: str,
        limit: int,
    ) -> dict:
        query = query.strip()

        if not query:
            raise AppError(
                code="invalid_search_query",
                message=(
                    "Search query cannot be empty."
                ),
                status_code=422,
            )

        results = []

        # ---------------------------------
        # Projects
        # ---------------------------------

        projects = self.repo.projects(
            query,
            limit,
        )

        for project in projects:
            results.append(
                {
                    "type": (
                        SearchResultType.PROJECT
                    ),
                    "id": project.id,
                    "title": project.name,
                    "snippet": self._snippet(
                        project.description
                    ),
                    "status": (
                        project.status.value
                    ),
                    "updated_at": (
                        project.updated_at
                    ),
                    "_rank": self._rank(
                        query,
                        project.name,
                        project.description,
                    ),
                }
            )

        # ---------------------------------
        # Tasks
        # ---------------------------------

        tasks = self.repo.tasks(
            query,
            limit,
        )

        for task in tasks:
            results.append(
                {
                    "type": (
                        SearchResultType.TASK
                    ),
                    "id": task.id,
                    "title": task.title,
                    "snippet": self._snippet(
                        task.description
                    ),
                    "status": (
                        task.status.value
                    ),
                    "updated_at": (
                        task.updated_at
                    ),
                    "_rank": self._rank(
                        query,
                        task.title,
                        task.description,
                    ),
                }
            )

        # ---------------------------------
        # Notes
        # ---------------------------------

        notes = self.repo.notes(
            query,
            limit,
        )

        for note in notes:
            results.append(
                {
                    "type": (
                        SearchResultType.NOTE
                    ),
                    "id": note.id,
                    "title": note.title,
                    "snippet": self._snippet(
                        note.content
                    ),
                    "status": None,
                    "updated_at": (
                        note.updated_at
                    ),
                    "_rank": self._rank(
                        query,
                        note.title,
                        note.content,
                    ),
                }
            )

        # ---------------------------------
        # Goals
        # ---------------------------------

        goals = self.repo.goals(
            query,
            limit,
        )

        for goal in goals:
            results.append(
                {
                    "type": (
                        SearchResultType.GOAL
                    ),
                    "id": goal.id,
                    "title": goal.title,
                    "snippet": self._snippet(
                        goal.description
                    ),
                    "status": (
                        goal.status.value
                    ),
                    "updated_at": (
                        goal.updated_at
                    ),
                    "_rank": self._rank(
                        query,
                        goal.title,
                        goal.description,
                    ),
                }
            )

        # ---------------------------------
        # Resources
        # ---------------------------------

        resources = self.repo.resources(
            query,
            limit,
        )

        for resource in resources:
            results.append(
                {
                    "type": (
                        SearchResultType.RESOURCE
                    ),
                    "id": resource.id,
                    "title": resource.title,
                    "snippet": self._snippet(
                        resource.description
                    ),
                    "status": (
                        resource.status.value
                    ),
                    "updated_at": (
                        resource.updated_at
                    ),
                    "_rank": self._rank(
                        query,
                        resource.title,
                        resource.description,
                    ),
                }
            )
        # ---------------------------------
        # Skills
        # ---------------------------------

        skills = self.repo.skills(
        query,
        limit,
        )

        for skill in skills:
            results.append(
                {
                    "type": (
                        SearchResultType.SKILL
                    ),
                    "id": skill.id,
                    "title": skill.name,
                    "snippet": self._snippet(
                        skill.notes
                    ),
                    "status": None,
                    "updated_at": (
                        skill.updated_at
                    ),
                    "_rank": self._rank(
                        query,
                        skill.name,
                        skill.notes,
                    ),
                }
            )

        results.sort(
            key=lambda item: (
                item["_rank"],
                -item[
                    "updated_at"
                ].timestamp(),
            )
        )

        results = results[:limit]

        for item in results:
            item.pop("_rank")

        return {
            "query": query,
            "count": len(results),
            "data": results,
        }