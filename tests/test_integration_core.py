from datetime import date


def test_core_personal_workflow(
    client,
    auth_headers,
):
    today = date.today().isoformat()

    # ----------------------------
    # Project
    # ----------------------------

    response = client.post(
        "/v1/projects",
        headers=auth_headers,
        json={
            "name": "Integration Project",
            "slug": "integration-project",
            "description": "Temporary test project",
            "status": "active",
            "priority": "high",
            "focus_rank": 1,
            "progress_percent": 50,
            "target_date": today,
            "started_at": None,
            "parent_project_id": None,
            "metadata": {
                "test": True,
            },
        },
    )

    assert response.status_code == 201

    project = response.json()
    project_id = project["id"]

    # ----------------------------
    # Goal
    # ----------------------------

    response = client.post(
        "/v1/goals",
        headers=auth_headers,
        json={
            "title": "Integration Goal",
            "description": "Temporary test goal",
            "status": "active",
            "progress_percent": 20,
            "target_date": today,
            "metadata": {
                "test": True,
            },
        },
    )

    assert response.status_code == 201

    goal_id = response.json()["id"]

    # ----------------------------
    # Goal -> Project
    # ----------------------------

    response = client.post(
        f"/v1/goals/{goal_id}/projects/{project_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    # ----------------------------
    # Note
    # ----------------------------

    response = client.post(
        "/v1/notes",
        headers=auth_headers,
        json={
            "title": "Integration Note",
            "content": (
                "Search should find this integration note."
            ),
            "project_id": project_id,
            "metadata": {
                "test": True,
            },
        },
    )

    assert response.status_code == 201

    note_id = response.json()["id"]

    # ----------------------------
    # Task A
    # ----------------------------

    response = client.post(
        "/v1/tasks",
        headers=auth_headers,
        json={
            "title": "Integration prerequisite",
            "description": "Task A",
            "status": "todo",
            "priority": "critical",
            "project_id": project_id,
            "parent_task_id": None,
            "due_date": today,
            "due_at": None,
            "scheduled_for": None,
            "estimated_minutes": 30,
            "position": 0,
            "metadata": {
                "test": True,
            },
        },
    )

    assert response.status_code == 201

    task_a_id = response.json()["id"]

    # ----------------------------
    # Task B
    # ----------------------------

    response = client.post(
        "/v1/tasks",
        headers=auth_headers,
        json={
            "title": "Integration dependent task",
            "description": "Task B",
            "status": "todo",
            "priority": "high",
            "project_id": project_id,
            "parent_task_id": None,
            "due_date": None,
            "due_at": None,
            "scheduled_for": None,
            "estimated_minutes": 30,
            "position": 1,
            "metadata": {
                "test": True,
            },
        },
    )

    assert response.status_code == 201

    task_b_id = response.json()["id"]

    # ----------------------------
    # Dependency B -> A
    # ----------------------------

    response = client.post(
        (
            f"/v1/tasks/{task_b_id}"
            f"/dependencies/{task_a_id}"
        ),
        headers=auth_headers,
    )

    assert response.status_code == 204

    # ----------------------------
    # B should be blocked
    # ----------------------------

    response = client.get(
        f"/v1/tasks/{task_b_id}/state",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["is_blocked"] is True

    # ----------------------------
    # Strict dependency enforcement
    # ----------------------------

    response = client.patch(
        f"/v1/tasks/{task_b_id}",
        headers=auth_headers,
        json={
            "status": "in_progress",
        },
    )

    assert response.status_code == 409

    assert (
        response.json()["error"]["code"]
        == "task_dependency_not_satisfied"
    )

    # ----------------------------
    # Cycle detection
    # ----------------------------

    response = client.post(
        (
            f"/v1/tasks/{task_a_id}"
            f"/dependencies/{task_b_id}"
        ),
        headers=auth_headers,
    )

    assert response.status_code == 422

    assert (
        response.json()["error"]["code"]
        == "task_dependency_cycle"
    )

    # ----------------------------
    # Complete A
    # ----------------------------

    response = client.patch(
        f"/v1/tasks/{task_a_id}",
        headers=auth_headers,
        json={
            "status": "completed",
        },
    )

    assert response.status_code == 200
    assert response.json()["completed_at"] is not None

    # ----------------------------
    # B becomes unblocked
    # ----------------------------

    response = client.get(
        f"/v1/tasks/{task_b_id}/state",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["is_blocked"] is False

    # ----------------------------
    # B can now start
    # ----------------------------

    response = client.patch(
        f"/v1/tasks/{task_b_id}",
        headers=auth_headers,
        json={
            "status": "in_progress",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"

    # ----------------------------
    # Focus
    # ----------------------------

    response = client.get(
        "/v1/focus",
        headers=auth_headers,
    )

    assert response.status_code == 200

    focus = response.json()

    assert any(
        project["id"] == project_id
        for project in focus["projects"]
    )

    assert any(
        goal["id"] == goal_id
        for goal in focus["goals"]
    )

    # ----------------------------
    # Search
    # ----------------------------

    response = client.get(
        "/v1/search",
        params={
            "q": "Integration",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["count"] >= 4

    # ----------------------------
    # Note soft deletion
    # ----------------------------

    response = client.delete(
        f"/v1/notes/{note_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = client.get(
        f"/v1/notes/{note_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404

    # ----------------------------
    # Restore note
    # ----------------------------

    response = client.post(
        f"/v1/notes/{note_id}/restore",
        headers=auth_headers,
    )

    assert response.status_code == 200