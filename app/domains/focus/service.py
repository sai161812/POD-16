from sqlalchemy.orm import Session

from app.domains.focus.repository import (
    FocusRepository,
)
from app.domains.tasks.time import (
    local_day_bounds,
    now_local,
    today_local,
)


class FocusService:
    def __init__(self, db: Session) -> None:
        self.repo = FocusRepository(db)

    def get(self) -> dict:
        now = now_local()
        today = today_local()
        start, end = local_day_bounds()

        projects = self.repo.projects()

        project_ids = [
            project.id
            for project in projects
        ]

        tasks = self.repo.tasks(
            project_ids=project_ids,
            today=today,
            start=start,
            end=end,
        )

        task_ids = [
            task.id
            for task in tasks
        ]

        blocker_rows = self.repo.blockers(
            task_ids
        )

        blocker_map = {
            task_id: []
            for task_id in task_ids
        }

        for row in blocker_rows:
            blocker_map[
                row.task_id
            ].append(
                {
                    "id": row.dependency_id,
                    "title": row.dependency_title,
                    "status": row.dependency_status,
                    "deleted": (
                        row.dependency_deleted_at
                        is not None
                    ),
                }
            )

        task_data = []

        for task in tasks:
            due_today = (
                task.due_date == today
                or (
                    task.due_at is not None
                    and start <= task.due_at < end
                )
            )

            scheduled_today = (
                task.scheduled_for is not None
                and start
                <= task.scheduled_for
                < end
            )

            overdue = (
                (
                    task.due_date is not None
                    and task.due_date < today
                )
                or (
                    task.due_at is not None
                    and task.due_at < now
                )
            )

            blockers = blocker_map[
                task.id
            ]

            task_data.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                    "project_id": task.project_id,
                    "due_date": task.due_date,
                    "due_at": task.due_at,
                    "scheduled_for": (
                        task.scheduled_for
                    ),
                    "is_today": (
                        due_today
                        or scheduled_today
                    ),
                    "is_overdue": overdue,
                    "is_blocked": bool(
                        blockers
                    ),
                    "blocked_by": blockers,
                }
            )

        goals = self.repo.goals(
            project_ids
        )

        today_count = sum(
            item["is_today"]
            for item in task_data
        )

        overdue_count = sum(
            item["is_overdue"]
            for item in task_data
        )

        blocked_count = sum(
            item["is_blocked"]
            for item in task_data
        )

        return {
            "generated_at": now,

            "summary": {
                "focus_projects": len(projects),
                "attention_tasks": len(tasks),
                "today_tasks": today_count,
                "overdue_tasks": overdue_count,
                "blocked_tasks": blocked_count,
                "active_goals": len(goals),
            },

            "projects": [
                {
                    "id": project.id,
                    "name": project.name,
                    "slug": project.slug,
                    "status": project.status,
                    "priority": project.priority,
                    "focus_rank": (
                        project.focus_rank
                    ),
                    "progress_percent": (
                        project.progress_percent
                    ),
                    "target_date": (
                        project.target_date
                    ),
                }
                for project in projects
            ],

            "tasks": task_data,

            "goals": [
                {
                    "id": goal.id,
                    "title": goal.title,
                    "status": goal.status,
                    "progress_percent": (
                        goal.progress_percent
                    ),
                    "target_date": (
                        goal.target_date
                    ),
                }
                for goal in goals
            ],
        }